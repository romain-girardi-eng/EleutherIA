"""
Scholarly Agent facade — orchestrates the GraphRAG pipeline.

Supports three modes via ELEUTHERIA_AGENT_MODE (or a per-request ``pipeline``):
  - "react" (default): ReAct agent loop with tools, then synthesis + tail
  - "lead": lead researcher — facets -> parallel sub-agents -> dossiers ->
    the lead writes -> the same verification tail (``agents/lead_researcher``)
  - "fsm": Original 12-node pydantic-graph pipeline
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
import re
import time as _time_mod
from collections.abc import AsyncIterator, Mapping, Sequence
from typing import Any, Literal, NamedTuple, cast

from pydantic_graph import GraphBuilder

from eleutheria_graphrag.agents.dependencies import Deps
from eleutheria_graphrag.agents.dialectical_synthesis import (
    build_provenance_ledger,
    deterministic_map_hedge,
    evaluate_content_gate,
    passes_content_gate,
    scholar_render_max_tokens,
    scholar_synthesis_timeout,
    synthesize_degraded,
    synthesize_dialectical,
    synthesize_dialectical_stream,
)
from eleutheria_graphrag.agents.graph_nodes import (
    SYSTEM_PROMPT,
    ClassifyQueryType,
    DraftClaimLedger,
    ProgrammaticVerify,
    RenderGroundedAnswer,
    _append_reasoning_step,
    _build_context_pack,
    _classify_render_quality,
    _dialectical_citations,
    _render_answer_fallback,
    _trace_stage,
    assess_evidence_sufficiency,
    build_render_prompt,
    truncate_text,
)
from eleutheria_graphrag.agents.legacy_fsm_nodes import (
    BuildResearchNotebook,
    DiscoverCorpus,
    EvidenceSufficiency,
    ExpandEvidenceBundles,
    ExpandQuery,
    PlanReading,
    SeekCounterEvidence,
    TreeNavigateWorks,
)
from eleutheria_graphrag.agents.publication_gate import (
    _claim_was_withheld,
    _normalise,
    annotate_publication_decision,
)
from eleutheria_graphrag.agents.state import (
    Citation,
    ClaimLedgerItem,
    ClaimStatus,
    Evidence,
    PassageRef,
    RAGState,
    ScholarlyAnswer,
    scholar_rag_enabled,
)
from eleutheria_graphrag.agents.text_verifier import (
    REATTRIBUTION_NOTE,
    Reattribution,
)
from eleutheria_graphrag.models.counter_evidence import (
    ClaimUnit,
    CounterEvidenceReport,
)
from eleutheria_graphrag.models.counter_evidence import (
    SynthesizedDraft as CounterEvidenceDraft,
)
from eleutheria_graphrag.models.verification import (
    CitationCheck,
    CitationStatus,
    CompanionRef,
    DraftClaim,
    SynthesizedDraft,
    VerificationReport,
)
from eleutheria_graphrag.public_payload import public_payload
from eleutheria_graphrag.services.claim_clause import (
    cited_sentences,
    extract_claim_clause,
    paragraph_context,
)
from eleutheria_graphrag.services.llm_service import CLIENT_LLM_ERROR_MESSAGE

_GREEK_CHAR_RE = re.compile(r"[\u0370-\u03FF\u1F00-\u1FFF]")
logger = logging.getLogger(__name__)

# Lossless prose-streaming chunker. Splits at paragraph (``\n\n``) then sentence
# (``. ``) boundaries WITHOUT discarding the boundary whitespace, so the
# concatenation of the yielded chunks is BYTE-FOR-BYTE the input prose. The
# earlier ``re.split(r"\n\n+")`` + ``_SENTENCE_SPLIT_RE.split`` chunkers dropped
# the inter-paragraph/inter-sentence separators at chunk boundaries, silently
# corrupting (and at the buffer-flush boundary mangling) the streamed answer.
# A capturing split keeps every delimiter; greedy packing keeps chunks ~<=500
# chars without ever losing a character.
_PROSE_SEGMENT_RE = re.compile(r"(\n{2,}|(?<=[.;\u00B7?!])\s+)")
_PROSE_CHUNK_TARGET = 500


def _lossless_prose_chunks(text: str, target: int = _PROSE_CHUNK_TARGET) -> list[str]:
    """Chunk ``text`` for streaming so ``"".join(chunks) == text`` exactly.

    Tokens (content + the following separator) are packed greedily up to
    ``target`` chars; an oversized single token is emitted whole rather than
    split mid-word. Empty input yields no chunks.
    """
    if not text:
        return []
    parts = _PROSE_SEGMENT_RE.split(text)
    # ``parts`` alternates content / captured-separator / content / \u2026 . Re-pair
    # each content piece with the separator that followed it so no character is
    # ever dropped between tokens.
    tokens: list[str] = []
    for i in range(0, len(parts), 2):
        content = parts[i]
        sep = parts[i + 1] if i + 1 < len(parts) else ""
        token = content + sep
        if token:
            tokens.append(token)
    chunks: list[str] = []
    buffer = ""
    for token in tokens:
        if buffer and len(buffer) + len(token) > target:
            chunks.append(buffer)
            buffer = token
        else:
            buffer += token
    if buffer:
        chunks.append(buffer)
    return chunks


# SSE frame types of the provisional-answer protocol (see docs/reference/API.md).
# Prose that has not yet passed the content gate, the ancient-text verifier and
# the citation audit only ever crosses the wire as ``answer_provisional``; the
# gated text is released by ``answer_final`` and the plain ``answer_chunk``
# frames that follow it.
ANSWER_PROVISIONAL_EVENT = "answer_provisional"
ANSWER_FINAL_EVENT = "answer_final"
ANSWER_CHUNK_EVENT = "answer_chunk"


class RenderProse(str):
    """Provenance marker for prose yielded by the render generators.

    ``_stream_render``, ``_stream_dialectical`` and ``_stream_map_hedge`` put
    two kinds of value on their channel: JSON control frames they build
    themselves (plain ``str``) and prose that originates from the model or a
    deterministic fallback (this type). The tag is applied at the yield site,
    so the consumer dispatches on the object's *type* and never on its text —
    a draft that happens to begin with valid typed-event JSON (a forged
    ``answer_final`` or ``complete``) is still a draft, and is wrapped as
    ``answer_provisional`` like every other un-audited chunk.

    A ``str`` subclass so the byte-for-byte prose contract of the generators
    (``"".join(chunks) == state.raw_answer``) is unchanged.
    """

    __slots__ = ()


# The only control frames the render generators are allowed to put on the wire
# themselves. Anything else that reaches ``_stream_react`` from the render as a
# plain string is dropped, never forwarded: control types of the publication
# protocol (``answer_final``, ``answer_chunk``, ``complete``, …) are emitted by
# the publication tail alone, after the verdict.
_RENDER_CONTROL_EVENT_TYPES: frozenset[str] = frozenset(
    {"status", "synthesis_reasoning"}
)


def _render_control_frame(event: object) -> str | None:
    """Return ``event`` iff it is a render-owned control frame, else ``None``.

    Provenance first: a ``RenderProse`` value is prose and is never a control
    frame, whatever it looks like. A plain string must then parse as a JSON
    object whose ``type`` is in the render whitelist. A frame that fails either
    check is not forwarded (fail closed) and is logged.
    """
    if isinstance(event, RenderProse) or not isinstance(event, str):
        return None
    try:
        parsed = json.loads(event)
    except json.JSONDecodeError:
        logger.warning("Dropping non-JSON control frame from the render stream")
        return None
    event_type = parsed.get("type") if isinstance(parsed, dict) else None
    if event_type not in _RENDER_CONTROL_EVENT_TYPES:
        logger.warning(
            "Dropping render-stream frame with non-whitelisted type %r", event_type
        )
        return None
    return event


def _answer_chunk_frame(chunk: str) -> str:
    """Wrap a chunk of GATED prose as a typed ``answer_chunk`` SSE frame.

    The publication tail emits the released text as typed frames rather than
    raw strings so the route never has to classify protocol-path text by
    inspecting it: gated prose that happens to begin with valid typed-event
    JSON (a forged ``complete``) stays prose on the wire — it can never be
    mistaken for a terminal frame, reach the answer cache, or finalize the
    trace.
    """
    return json.dumps({"type": ANSWER_CHUNK_EVENT, "data": chunk})


def _provisional_frame(chunk: str) -> str:
    """Wrap un-audited prose as a typed ``answer_provisional`` SSE frame.

    The route forwards typed frames verbatim on their own channel, so this text
    never enters the ``answer_chunk`` prose path, the partial-answer trace, or
    the answer cache. ``provisional: true`` is carried explicitly so a consumer
    cannot mistake the draft for the verified answer.
    """
    return json.dumps(
        {"type": ANSWER_PROVISIONAL_EVENT, "data": chunk, "provisional": True}
    )


def _answer_final_frame(answer: ScholarlyAnswer) -> str:
    """The verdict frame: gated prose, citations, badge and withholding info.

    Emitted once, after the content gate + text verifier + citation audit have
    ruled and the shared verdict has been APPLIED to ``answer`` (see
    ``annotate_publication_decision(withhold_prose=True)``), and BEFORE the
    plain ``answer_chunk`` / ``complete`` frames. The frame reads
    ``metadata.publication_gate`` — the same record the sync facade and the
    answer caches publish — so the three boundaries cannot drift. A blocked
    run carries an empty ``answer`` with ``withheld: true`` and the
    machine-readable reasons; a partial run carries the prose with its
    withheld sentences already removed and ``withholding`` says what went. The
    client replaces its provisional preview atomically in every outcome.
    """
    gate = answer.metadata.get("publication_gate") or {}
    publishable = bool(gate.get("publishable"))
    return json.dumps(
        {
            "type": ANSWER_FINAL_EVENT,
            "provisional": False,
            "data": {
                "answer": answer.answer if publishable else "",
                "withheld": not publishable,
                "status": gate.get("status")
                or ("passed" if publishable else "blocked"),
                "reasons": list(gate.get("reasons") or []),
                "withholding": gate.get("withholding") or {},
                "quality_badge": answer.quality_badge,
                "citations": public_payload([c.model_dump() for c in answer.citations]),
                "claim_ledger": public_payload(
                    {"claim_ledger": [c.model_dump() for c in answer.claim_ledger]}
                )["claim_ledger"],
                "publication_gate": gate or None,
            },
        },
        default=str,
    )


def _claim_from_ledger(
    ledger: list[ClaimLedgerItem],
    citation_id: str,
) -> str | None:
    """The ledger claim sentence citing ``citation_id``, or ``None``.

    The dialectical path stores the full sentence carrying each inline
    ``[passage_<id>: …]`` marker in the claim ledger (``build_provenance_ledger``),
    so this recovers a real auditable claim where the literal-``[ref]`` lookup
    cannot find one. First match wins; empty claims are skipped.
    """
    if not ledger or not citation_id:
        return None
    for item in ledger:
        if not item.claim or not item.claim.strip():
            continue
        if _ledger_item_cites(list(item.evidence_ids), citation_id):
            return item.claim.strip()
    return None


_VERIFIER_V2_DEFAULT_MAX_CLAIMS = 160


def _verifier_v2_max_claims() -> int:
    """Per-query audit ceiling for the v2 verifier (0 disables it).

    Publication now requires full citation coverage.  The former default of 8
    made every longer answer necessarily unauditable, and 64 still fell short
    of a dense answer: a benchmark answer carrying 84 citations had 20 of them
    withheld as "unaudited" for no reason but the cap (production already ran
    with ``ELEUTHERIA_VERIFIER_V2_MAX_CLAIMS=160``).  160 covers the answer
    envelope actually observed, while an explicit lower operator cap remains
    fail-closed (the resulting partial audit cannot pass the publication
    gate).
    """

    raw = os.getenv(
        "ELEUTHERIA_VERIFIER_V2_MAX_CLAIMS",
        str(_VERIFIER_V2_DEFAULT_MAX_CLAIMS),
    )
    try:
        value = int(raw)
    except ValueError:
        return _VERIFIER_V2_DEFAULT_MAX_CLAIMS
    return max(0, value)


_CITATION_AUDIT_DEFAULT_MAX_WAIT_S = 900.0


def _citation_audit_max_wait() -> float:
    """Wall-clock ceiling (seconds) for the streamed citation audit.

    The audit now judges every (sentence, citation) pair, with companion
    sources and a bounded tool loop per pair: on a long answer that is well
    over a hundred judge calls. The former 180 s heartbeat ceiling abandoned
    such audits mid-way, which the publication gate then reported as
    ``no_auditable_citations`` and blocked the whole answer. 900 s covers the
    audited pairs at the default concurrency; operators may lower it with
    ``ELEUTHERIA_CITATION_AUDIT_MAX_WAIT_S`` (an abandoned audit still fails
    closed).
    """

    raw = os.getenv(
        "ELEUTHERIA_CITATION_AUDIT_MAX_WAIT_S",
        str(_CITATION_AUDIT_DEFAULT_MAX_WAIT_S),
    )
    try:
        value = float(raw)
    except ValueError:
        return _CITATION_AUDIT_DEFAULT_MAX_WAIT_S
    return value if value > 0 else _CITATION_AUDIT_DEFAULT_MAX_WAIT_S


class _AuditPair(NamedTuple):
    """One (sentence, citation) pair of the answer, the unit of audit.

    ``claim`` is the sentence carrying the citation's marker (the anchor the
    judge's proposition is cut from); ``sentence_index`` is its position in
    the answer's sentence sequence (see ``claim_clause.enumerate_sentences``).
    A citation with no inline marker gets one fallback pair with
    ``sentence_index=None`` whose ``claim`` is its ledger sentence or, last,
    its label; ``clause`` is the proposition the marker is attached to.
    """

    citation: Citation
    claim: str
    sentence_index: int | None
    clause: str = ""


def _citation_index(answer: ScholarlyAnswer) -> dict[str, Citation]:
    by_key: dict[str, Citation] = {}
    for citation in answer.citations:
        for key in _citation_keys(citation):
            by_key.setdefault(key, citation)
    return by_key


def _enumerate_audit_pairs(answer: ScholarlyAnswer) -> list[_AuditPair]:
    """Every (sentence, citation) pair of ``answer``, in document order.

    A citation cited in four sentences yields four pairs — each use is
    judged on its own proposition, and a verdict on one use never speaks
    for the others. Within a sentence the pairs follow the citation list.
    A citation absent from the prose (ledger-only, or a label fallback)
    yields one pair with no sentence index, audited as a whole.
    """
    by_key = _citation_index(answer)
    pairs: list[_AuditPair] = []
    covered: set[str] = set()
    for index, sentence, tokens in cited_sentences(answer.answer, known=by_key.keys()):
        seen_here: set[str] = set()
        present = set(tokens)
        for citation in answer.citations:
            if citation.id in seen_here or not (_citation_keys(citation) & present):
                continue
            seen_here.add(citation.id)
            covered.add(citation.id)
            clause = extract_claim_clause(
                sentence, keys=_citation_keys(citation), known=by_key.keys()
            ).clause
            pairs.append(_AuditPair(citation, sentence, index, clause))
    for citation in answer.citations:
        if citation.id in covered:
            continue
        covered.add(citation.id)
        claim_text = (
            _claim_from_ledger(answer.claim_ledger, citation.id) or citation.label
        )
        pairs.append(_AuditPair(citation, claim_text, None, claim_text))
    return pairs


def _order_audit_pairs(pairs: list[_AuditPair]) -> list[_AuditPair]:
    """Order pairs by risk, so a cap cuts the least risky ones.

    Three tiers: pairs whose proposition quotes ancient Greek (fabricated
    ancient text is the worst failure mode); then one pair per citation so
    every citation gets at least one look; then the rest. Inside a tier,
    ascending citation confidence (unknown sorts last as 1.0), then document
    order.
    """
    position = {id(pair): index for index, pair in enumerate(pairs)}

    def rank(pair: _AuditPair) -> tuple[float, int]:
        citation = pair.citation
        confidence = citation.confidence if citation.confidence is not None else 1.0
        return (confidence, position[id(pair)])

    greek = sorted(
        (p for p in pairs if _GREEK_CHAR_RE.search(p.clause or p.claim)), key=rank
    )
    covered = {p.citation.id for p in greek}
    first_look: list[_AuditPair] = []
    rest: list[_AuditPair] = []
    for pair in sorted(
        (p for p in pairs if not _GREEK_CHAR_RE.search(p.clause or p.claim)), key=rank
    ):
        if pair.citation.id in covered:
            rest.append(pair)
        else:
            covered.add(pair.citation.id)
            first_look.append(pair)
    return greek + first_look + rest


def _sample_citations_for_verification(
    answer: ScholarlyAnswer,
    max_claims: int,
) -> list[_AuditPair]:
    """The highest-risk (sentence, citation) pairs, capped at ``max_claims``.

    See :func:`_enumerate_audit_pairs` for the pairs and
    :func:`_order_audit_pairs` for the risk order. Pairs beyond the cap go
    unaudited and are withheld as such (fail-closed) — the caller records
    how many.
    """
    return _order_audit_pairs(_enumerate_audit_pairs(answer))[:max_claims]


def _citation_keys(citation: Citation) -> set[str]:
    return {key for key in (citation.ref, citation.id) if key}


def _draft_claim_for(
    answer: ScholarlyAnswer,
    citation: Citation,
    claim_text: str,
    *,
    sentence_index: int | None = None,
) -> DraftClaim:
    """Build the judge's input for one (sentence, citation) pair: the
    proposition the marker is attached to, the full sentence and paragraph
    as context, and the sentence's other citations as companions (their
    evidence is fetched by the verifier). The sentence (``claim_text``) stays
    the anchor; ``sentence_index`` keys the pair."""
    by_key = _citation_index(answer)
    clause = extract_claim_clause(
        claim_text, keys=_citation_keys(citation), known=by_key.keys()
    )
    companions: list[CompanionRef] = []
    seen = {citation.id}
    for token in clause.companion_tokens:
        other = by_key.get(token)
        if other is None or other.id in seen:
            continue
        seen.add(other.id)
        companions.append(
            CompanionRef(
                citation_id=other.id,
                marker=other.ref or token,
                label=other.label,
                citation_kind="passage" if other.type == "passage" else "node",
            )
        )
    return DraftClaim(
        claim=clause.clause,
        sentence=clause.sentence,
        context=paragraph_context(answer.answer, clause.sentence),
        companions=companions,
        citation_id=citation.id,
        citation_kind="passage" if citation.type == "passage" else "node",
        sentence_index=sentence_index,
    )


_STATUS_SEVERITY = {
    CitationStatus.VERIFIED: 0,
    CitationStatus.WEAK: 1,
    CitationStatus.MISSING: 2,
    CitationStatus.REJECTED: 3,
}


def _harshest(checks: list[CitationCheck]) -> CitationCheck:
    """The most severe verdict among ``checks`` (first one on ties)."""
    return max(checks, key=lambda c: _STATUS_SEVERITY.get(c.status, 0))


class _PairAudit:
    """The pair-level reading of a verification report.

    Verdicts are keyed by ``(citation_id, sentence_index)``. A check whose
    key matches no draft claim (a verdict without a sentence index) is
    attributed to the claim of its citation when that citation was audited
    once — the legacy one-verdict-per-id shape.
    """

    def __init__(
        self,
        claims: list[DraftClaim],
        checks: list[CitationCheck],
        unaudited: list[_AuditPair],
    ) -> None:
        by_key = {claim.pair_key: claim for claim in claims}
        by_id: dict[str, list[DraftClaim]] = {}
        for claim in claims:
            by_id.setdefault(claim.citation_id, []).append(claim)
        self.checks = checks
        self.unaudited = unaudited
        self.claim_for: dict[int, DraftClaim | None] = {}
        self.checks_by_id: dict[str, list[CitationCheck]] = {}
        for check in checks:
            claim = by_key.get(check.pair_key)
            if claim is None and check.sentence_index is None:
                candidates = by_id.get(check.citation_id) or []
                claim = candidates[0] if len(candidates) == 1 else None
            self.claim_for[id(check)] = claim
            self.checks_by_id.setdefault(check.citation_id, []).append(check)

    # ---- per pair

    def sentence_index(self, check: CitationCheck) -> int | None:
        claim = self.claim_for.get(id(check))
        return claim.sentence_index if claim is not None else check.sentence_index

    def sentence(self, check: CitationCheck) -> str:
        claim = self.claim_for.get(id(check))
        if claim is not None and claim.sentence:
            return claim.sentence
        return check.sentence or check.claim

    def pair_record(self, check: CitationCheck) -> dict[str, Any]:
        return {
            "sentence_index": self.sentence_index(check),
            "sentence": self.sentence(check),
            "clause": check.claim,
            "status": check.status.value,
            "reasoning": check.reasoning,
            "parse_error": bool(check.parse_error),
            "evidence_kind": check.evidence_kind,
        }

    # ---- per citation id

    def verified_pairs(self, cid: str) -> list[CitationCheck]:
        return [c for c in self.checks_by_id.get(cid, []) if c.is_passing]

    def failing_pairs(self, cid: str) -> list[CitationCheck]:
        return [c for c in self.checks_by_id.get(cid, []) if not c.is_passing]

    @property
    def audited_ids(self) -> list[str]:
        return list(self.checks_by_id)

    @property
    def verified_ids(self) -> list[str]:
        """Ids whose every audited pair is VERIFIED."""
        return [cid for cid in self.checks_by_id if not self.failing_pairs(cid)]

    @property
    def fully_failing_ids(self) -> set[str]:
        """Ids without a single verified pair: withheld as a whole."""
        return {cid for cid in self.checks_by_id if not self.verified_pairs(cid)}

    def id_status(self, cid: str) -> CitationStatus:
        return _harshest(self.checks_by_id[cid]).status

    def id_counts(self) -> dict[str, int]:
        counts = {"verified": 0, "weak": 0, "rejected": 0, "missing": 0}
        for cid in self.checks_by_id:
            counts[self.id_status(cid).value.lower()] += 1
        return counts

    def pair_counts(self) -> dict[str, int]:
        counts = {
            "total": len(self.checks) + len(self.unaudited),
            "audited": len(self.checks),
            "verified": 0,
            "weak": 0,
            "rejected": 0,
            "missing": 0,
            "unaudited": len(self.unaudited),
        }
        for check in self.checks:
            counts[check.status.value.lower()] += 1
        return counts

    def failed_citations(self) -> list[dict[str, Any]]:
        """One entry per id with a failing pair: the harshest verdict at the
        top (the legacy shape), the failing pairs listed beneath, and how
        many pairs of the id were verified — the publication gate withholds
        by pair when at least one was."""
        entries: list[dict[str, Any]] = []
        for cid in self.checks_by_id:
            failing = self.failing_pairs(cid)
            if not failing:
                continue
            harshest = _harshest(failing)
            entries.append(
                {
                    "citation_id": cid,
                    "status": harshest.status.value,
                    "claim": harshest.claim,
                    "reasoning": harshest.reasoning,
                    "parse_error": bool(harshest.parse_error),
                    "evidence_kind": harshest.evidence_kind,
                    "verified_pairs": len(self.verified_pairs(cid)),
                    "pairs": [self.pair_record(check) for check in failing],
                }
            )
        return entries

    def unaudited_pairs(self) -> list[dict[str, Any]]:
        return [
            {
                "citation_id": pair.citation.id,
                "sentence_index": pair.sentence_index,
                "sentence": pair.claim if pair.sentence_index is not None else "",
                "clause": pair.clause,
            }
            for pair in self.unaudited
        ]

    def failing_sentences(self) -> tuple[str, ...]:
        """Normalised sentences of the failing pairs of partially verified
        ids — the sentences the gate will withhold."""
        texts: list[str] = []
        for cid in self.checks_by_id:
            if cid in self.fully_failing_ids:
                continue
            for check in self.failing_pairs(cid):
                if self.sentence_index(check) is not None:
                    texts.append(_normalise(self.sentence(check)))
        return tuple(texts)


def _aggregate_tool_calls(checks: list[CitationCheck]) -> dict[str, Any]:
    """Cost/latency visibility for the judge's fetch-on-demand loop."""
    by_tool: dict[str, int] = {}
    total = hits = errors = 0
    with_calls = 0
    for check in checks:
        calls = check.tool_calls or []
        if calls:
            with_calls += 1
        for call in calls:
            total += 1
            name = str(call.get("tool") or "?")
            by_tool[name] = by_tool.get(name, 0) + 1
            hits += 1 if call.get("hit") else 0
            errors += 1 if call.get("error") else 0
    return {
        "total": total,
        "hits": hits,
        "errors": errors,
        "by_tool": by_tool,
        "citations_with_tool_calls": with_calls,
    }


def _ledger_item_cites(evidence_ids: list[str], citation_id: str) -> bool:
    """Whether a ledger item's evidence includes ``citation_id``.

    Ledger evidence ids are bundle ids (``{work_id}::{passage_id}``) or KG
    node ids, while v2 verdicts are keyed by passage/node id — match both the
    exact id and the bundle-id suffix form (best-effort, never false on an
    exact hit).
    """
    suffix = f"::{citation_id}"
    return any(eid == citation_id or eid.endswith(suffix) for eid in evidence_ids)


def _text_verifier_enabled() -> bool:
    """Deterministic ancient-text verifier gate (default ON — report-only)."""
    raw = os.getenv("ELEUTHERIA_TEXT_VERIFIER", "true").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def _reranker_enabled() -> bool:
    """Cross-encoder reranker gate (default OFF — model weights not vendored)."""
    raw = os.getenv("ELEUTHERIA_RERANKER", "false").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _stream_render_max_tokens() -> int:
    """Completion-token ceiling for the streamed public-path render.

    Profiling put cold-query *synthesis* (claim ledger + render) at ~169 s, the
    single largest stage. The render streams up to 16 k completion tokens of a
    doctoral-length answer from a heavy reasoning model; generation time scales
    with that ceiling. Capping it for the public/streaming path is the highest-
    leverage synthesis latency lever — a structured, fully-cited answer fits
    comfortably in ~7 k tokens. Override with ``ELEUTHERIA_RENDER_MAX_TOKENS``;
    defaults to 8000 (down from 16000) for the streaming path. Values are
    clamped to [2000, 16000].
    """
    raw = os.getenv("ELEUTHERIA_RENDER_MAX_TOKENS", "8000")
    try:
        value = int(raw)
    except ValueError:
        return 8000
    return max(2000, min(16000, value))


def _dialectical_heartbeat_ceiling() -> float:
    """Heartbeat ``max_wait`` ceiling for the Scholar-RAG dialectical synthesis.

    The heartbeat wrapper cancels its wrapped task once this elapses. For the
    dialectical synthesis that task is the slow thinking-model LLM call, whose
    own HTTP timeout is ``scholar_synthesis_timeout()`` (default 360 s). The
    heartbeat ceiling MUST sit ABOVE that timeout — otherwise it would cancel a
    healthy-but-slow synthesis BEFORE the LLM call can return, dropping the
    pipeline into the legacy facet-template fallback (the worst outcome). We add
    a margin for ledger build + prose chunking so the LLM timeout is always the
    binding deadline, never the heartbeat. Flag-OFF paths keep the 240 s default.
    """
    return scholar_synthesis_timeout() + 45.0


def _sufficiency_continuation_budget() -> int:
    """Max bounded continuation rounds after an insufficient verdict (0 or 1)."""
    raw = os.getenv("ELEUTHERIA_SUFFICIENCY_CONTINUATIONS", "1")
    try:
        value = int(raw)
    except ValueError:
        return 1
    return max(0, min(1, value))


def _sufficiency_extra_calls() -> int:
    """Tool-call budget granted to the single continuation round."""
    raw = os.getenv("ELEUTHERIA_SUFFICIENCY_EXTRA_CALLS", "3")
    try:
        value = int(raw)
    except ValueError:
        return 3
    return max(1, min(5, value))


def counter_report_to_ledger_items(
    report: CounterEvidenceReport,
    *,
    max_items: int = 8,
) -> list[ClaimLedgerItem]:
    """Convert hunter testimonia into claim-ledger entries.

    ``contradiction`` findings become ``support_type='contradicts'``; every
    other dimension (qualification, alternative, scholar_critique, …) becomes
    ``support_type='qualifies'``. Testimonia without a validated passage or
    node id are skipped — a ledger entry must be anchorable. Quote fields are
    deliberately left empty: hunter excerpts are tool-result snippets, not
    verified ancient quotations.
    """
    items: list[ClaimLedgerItem] = []
    seen: set[tuple[str, tuple[str, ...]]] = set()
    for finding in report.per_claim_findings:
        for testimony in finding.opposing_testimonia:
            evidence_ids = [
                eid for eid in (testimony.passage_id, testimony.source_node_id) if eid
            ]
            if not evidence_ids:
                continue
            claim = f"Counter-evidence ({testimony.type}): {testimony.source}"
            if testimony.brief_reasoning:
                claim = f"{claim} — {testimony.brief_reasoning}"
            key = (claim, tuple(evidence_ids))
            if key in seen:
                continue
            seen.add(key)
            items.append(
                ClaimLedgerItem(
                    claim=claim,
                    evidence_ids=evidence_ids,
                    evidence_class="counter_evidence",
                    support_type=(
                        "contradicts"
                        if testimony.type == "contradiction"
                        else "qualifies"
                    ),
                    confidence=0.7 if testimony.force == "strong" else 0.5,
                    status=ClaimStatus.SUPPORTED,
                )
            )
            if len(items) >= max_items:
                return items
    return items


# ── Research journal: the leads the pipeline OPENED and then DROPPED ─────────
#
# The timeline already narrates what worked. What it never showed is the other
# half of real research: the hypotheses formed and then abandoned. These helpers
# read REAL pipeline state — nothing is inferred, nothing is narrated that the
# run did not actually do — and turn it into ``research_note`` SSE frames:
#
#   dead_end       a lead that was followed and returned nothing
#   abandoned      a line of inquiry opened and then dropped
#   rejected_claim a drafted claim the grounding gate refused to keep
#   gap            something the pipeline's own critic said was missing
#
# A flood is worse than silence: the whole run is capped at
# ``_RESEARCH_NOTE_CAP`` frames, and each source is individually capped.
#
# The journal is written FOR A RESEARCHER, so it speaks the graph's own
# vocabulary, never the pipeline's: node ids are resolved to their KG labels
# and internal machinery (tool names, gate nicknames, mode names, scores) stays
# out of the summary. A lead that cannot be named in the reader's language is
# dropped rather than shown as an opaque identifier (the deleak rule).

#: Hard ceiling on ``research_note`` frames per run.
_RESEARCH_NOTE_CAP = 10

#: Per-source ceilings — one noisy source must not eat the whole budget.
_MAX_DEAD_END_TOOLS = 4
_MAX_COVERAGE_GAPS = 3
_MAX_REJECTED_CLAIMS = 4

ResearchNoteKind = Literal["abandoned", "dead_end", "rejected_claim", "gap"]


class ResearchJournal:
    """Budgeted serialiser for ``research_note`` SSE frames.

    Holds the per-run cap so every emission site can stay a one-liner. Returns
    the JSON string to yield, or ``None`` once the budget is spent.
    """

    def __init__(self, cap: int = _RESEARCH_NOTE_CAP) -> None:
        self.remaining = max(0, cap)

    def note(
        self,
        kind: ResearchNoteKind,
        summary: str,
        *,
        stage: str,
        detail: str | None = None,
    ) -> str | None:
        summary = (summary or "").strip()
        if not summary or self.remaining <= 0:
            return None
        self.remaining -= 1
        data: dict[str, Any] = {"kind": kind, "summary": summary, "stage": stage}
        if detail:
            data["detail"] = detail.strip()[:400]
        return json.dumps({"type": "research_note", "data": data}, default=str)


def _trim(text: str, limit: int) -> str:
    """One-line, length-bounded rendering of a state string."""
    flat = " ".join((text or "").split())
    return flat if len(flat) <= limit else flat[: limit - 1].rstrip() + "…"


#: Read-only view of the KG used to turn ids into the names a reader knows.
NodeLookup = Mapping[str, Mapping[str, Any]]

#: Tools whose "lead" argument is a node id, not a human-readable query.
_NODE_ID_TOOLS = frozenset(
    {
        "get_node_detail",
        "get_neighbors",
        "explore_subgraph",
        "infer_transitive",
        "build_controversy_frame",
    }
)

#: An identifier-shaped token (``pub_furst_2022_wege_freiheit``, ``debate_fate_1``).
_NODE_ID_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)+")

#: Machine vocabulary that must never reach the reader: raw identifiers, tool
#: names, gate nicknames, pipeline mode names. Text still carrying any of it is
#: dropped rather than shown half-translated.
_MACHINE_TALK_RE = re.compile(
    r"_[a-z0-9]{3,}|\bllm\b|heuristic|\bfallback\b|sufficiency|\btsquery\b",
    re.IGNORECASE,
)


def _reads_as_machine(text: str) -> bool:
    """True when a string still carries pipeline-internal vocabulary."""
    return bool(_MACHINE_TALK_RE.search(text or ""))


def _node_label(node_id: str, node_lookup: NodeLookup | None) -> str:
    """The KG label for an id, or ``""`` when the graph cannot name it.

    Mirrors the subgraph builder's resolution (``_kg_node_payload``) but never
    falls back to the id itself: an unnameable node is skipped, not printed.
    """
    if not node_id or not isinstance(node_lookup, Mapping):
        return ""
    meta = node_lookup.get(node_id)
    if not isinstance(meta, Mapping):
        return ""
    label = str(meta.get("label") or "").strip()
    if not label or label == node_id or _reads_as_machine(label):
        return ""
    return _trim(label, 90)


def _first_named_node(text: str, node_lookup: NodeLookup | None) -> str:
    """Label of the first id-shaped token in ``text`` the KG can name."""
    for token in _NODE_ID_TOKEN_RE.findall(text or ""):
        label = _node_label(token, node_lookup)
        if label:
            return label
    return ""


def _ingested_node_ids(state: RAGState) -> set[str]:
    """Every node id this run actually pulled into evidence.

    Defence in depth for the dead-end rule: whatever a counter says, a node
    whose content reached the synthesis was read, not dropped.
    """
    ids = set(state.seed_node_ids) | set(state.context_node_ids)
    ids.update(ev.id for ev in state.all_evidence() if ev.id)
    return ids


def dead_end_tool_notes(
    state: RAGState, node_lookup: NodeLookup | None = None
) -> list[dict[str, str]]:
    """Leads the ReAct loop followed that came back with nothing.

    ``ResearchToolCall.detail_count`` is the number of nodes + passages the
    collector actually ingested from that call, so ``0`` is the literal "this
    lead produced no evidence" record — a successful node read counts 1 and is
    therefore never narrated as a dead end. A lead the reader cannot be shown
    (no query, or a node id the graph cannot name) is skipped rather than
    printed raw.
    """
    ingested = _ingested_node_ids(state)
    notes: list[dict[str, str]] = []
    seen: set[str] = set()
    for call in state.research_notebook.tool_calls:
        if call.detail_count > 0:
            continue
        raw_lead = _trim(call.query or "", 120)
        if not raw_lead or raw_lead in ingested:
            # Its content reached the evidence: read, not dropped.
            continue
        by_id = call.tool_name in _NODE_ID_TOOLS or bool(
            _NODE_ID_TOKEN_RE.fullmatch(raw_lead)
        )
        lead = (
            _node_label(raw_lead, node_lookup)
            if by_id
            else ("" if _reads_as_machine(raw_lead) else raw_lead)
        )
        if not lead or lead.lower() in seen:
            continue
        seen.add(lead.lower())
        summary = (
            f'Looked up "{lead}" — the entry added no usable evidence, so the '
            "lead was set aside."
            if by_id
            else f'Searched for "{lead}" — nothing came back, so the lead was '
            "set aside."
        )
        notes.append(
            {
                "kind": "dead_end",
                "summary": summary,
                "detail": _trim(call.rationale or "", 200),
            }
        )
        if len(notes) >= _MAX_DEAD_END_TOOLS:
            break
    return notes


def _debate_gap_summary(gap: str, node_lookup: NodeLookup | None) -> str:
    """Reader-facing sentence for one abandoned debate seed.

    The assembler records its gaps in its own words ("build_controversy_frame
    on debate_fate_1 returned no frame"). Only the debate it names survives
    into the journal, under its KG label; an unnameable seed is dropped.
    """
    text = _trim(gap, 200)
    label = _first_named_node(text, node_lookup)
    if not label:
        return ""
    if "under-filled" in text.lower() or "no positions" in text.lower():
        return (
            f'The debate "{label}" was set aside — nothing was found to fill it '
            "out, neither positions nor the disagreements between them."
        )
    return (
        f'The debate "{label}" was set aside — no usable account of the '
        "disagreement could be built from it."
    )


def controversy_gap_notes(
    state: RAGState, node_lookup: NodeLookup | None = None
) -> list[dict[str, str]]:
    """Debate seeds the controversy-map assembly opened and then abandoned.

    ``coverage_gaps`` are written by the assembler at the exact point a seed is
    ``continue``-d out of the map (no frame returned, or an under-filled frame),
    so each one names a real abandoned line of inquiry.
    """
    meta = state.metadata.get("controversy_map")
    notes: list[dict[str, str]] = []
    gaps = state.metadata.get("controversy_map_gaps")
    if isinstance(gaps, list):
        for gap in gaps:
            summary = _debate_gap_summary(str(gap), node_lookup)
            if summary:
                notes.append({"kind": "abandoned", "summary": summary, "detail": ""})
            if len(notes) >= _MAX_COVERAGE_GAPS:
                break
    if isinstance(meta, dict) and meta.get("status") == "degraded":
        notes.append(
            {
                "kind": "abandoned",
                "summary": (
                    "The controversy-map approach was abandoned: assembly "
                    "produced no usable debate frames, so the run fell back to "
                    "the non-dialectical evidence synthesis."
                ),
                "detail": _trim(str(meta.get("reason") or ""), 200),
            }
        )
    return notes


def sufficiency_gap_notes(state: RAGState) -> list[dict[str, str]]:
    """What the pipeline's own evidence critic said was still missing.

    The reader is told what happened to the research, in plain words. The
    numeric verdict belongs in ``detail``; the critic's own reason is quoted
    only when it is written in the reader's language (an internal marker such
    as the heuristic fallback's is dropped, never paraphrased into a claim the
    critic did not make).
    """
    check = state.metadata.get("sufficiency_check")
    if not isinstance(check, dict) or check.get("sufficient"):
        return []
    summary = (
        "The evidence gathered so far looked too thin, so one more retrieval "
        "round was run."
        if check.get("continued")
        else "The evidence gathered so far looked too thin, but there was no "
        "retrieval round left to run."
    )
    reason = _trim(str(check.get("reason") or ""), 220)
    if reason and not _reads_as_machine(reason):
        summary = f"{summary} What was missing: {reason.rstrip('.')}."
    detail_bits: list[str] = []
    score = check.get("score")
    if isinstance(score, int | float):
        detail_bits.append(f"Evidence-sufficiency score {float(score):.2f}.")
    refinement = _trim(str(check.get("refinement") or ""), 180)
    if refinement:
        detail_bits.append(f"Suggested refinement: {refinement}")
    return [{"kind": "gap", "summary": summary, "detail": " ".join(detail_bits)}]


def counter_evidence_notes(state: RAGState) -> list[dict[str, str]]:
    """The adversarial hunt that went looking for objections and found none."""
    hunt = state.metadata.get("counter_evidence_hunt")
    if not isinstance(hunt, dict):
        return []
    status = hunt.get("status")
    if status == "skipped":
        reason = _trim(str(hunt.get("reason") or ""), 160)
        if not reason or _reads_as_machine(reason):
            reason = "there was nothing in place to audit"
        return [
            {
                "kind": "abandoned",
                "summary": (
                    "The search for evidence against the working hypotheses was "
                    f"abandoned before it ran — {reason.rstrip('.')}."
                ),
                "detail": "",
            }
        ]
    if status != "ok" or hunt.get("total_testimonia"):
        return []
    audited = hunt.get("claims_audited")
    scope = (
        f"{audited} working hypothes{'is' if audited == 1 else 'es'}"
        if isinstance(audited, int) and audited > 0
        else "the working hypotheses"
    )
    return [
        {
            "kind": "dead_end",
            "summary": (
                f"Hunted for evidence against {scope} and found none — no "
                "opposing testimony entered the answer."
            ),
            "detail": "",
        }
    ]


def _serialise_notes(
    journal: ResearchJournal, notes: list[dict[str, str]], stage: str
) -> list[str]:
    """Serialise a batch of notes into ``research_note`` SSE frames."""
    frames: list[str] = []
    for note in notes:
        frame = journal.note(
            cast("ResearchNoteKind", note["kind"]),
            note["summary"],
            stage=stage,
            detail=note.get("detail") or None,
        )
        if frame:
            frames.append(frame)
    return frames


def rejected_claim_notes(state: RAGState) -> list[dict[str, str]]:
    """Drafted claims the grounding gate refused to keep.

    ``INSUFFICIENT`` = the claim was written but its evidence did not hold up;
    ``UNVERIFIED`` = it cited a marker that resolves to nothing in the map (the
    hallucinated-id signature). Both are hypotheses the pipeline dropped.
    """
    reasons = {
        ClaimStatus.INSUFFICIENT: "its evidence did not hold up",
        ClaimStatus.UNVERIFIED: "its citation resolved to no source in the map",
    }
    notes: list[dict[str, str]] = []
    for item in state.claim_ledger:
        reason = reasons.get(item.status)
        if reason is None:
            continue
        claim = _trim(item.claim, 160)
        if not claim or _reads_as_machine(claim):
            # A claim still carrying internal markers is not shown raw.
            continue
        notes.append(
            {
                "kind": "rejected_claim",
                "summary": f'Claim dropped — {reason}: "{claim}"',
                "detail": (
                    f"{len(item.evidence_ids)} evidence reference(s), "
                    f"confidence {item.confidence:.2f}"
                ),
            }
        )
        if len(notes) >= _MAX_REJECTED_CLAIMS:
            break
    return notes


def _collect_evidence_texts(state: RAGState) -> list[str]:
    """All texts retrieved for this query — the text verifier's whitelist.

    Ancient text the agent actually read (bundle originals/translations,
    evidence descriptions and passage texts) is legitimate to quote, so it
    must never be flagged or re-checked against the DB.
    """
    texts: list[str] = []
    bundles = list(state.evidence_bundles)
    if state.context_pack and state.context_pack.passage_bundles:
        bundles.extend(state.context_pack.passage_bundles)
    for bundle in bundles:
        for text in (bundle.original_text, bundle.translation_text):
            if text:
                texts.append(text)
    for evidence in state.all_evidence():
        for text in (evidence.description, evidence.text_content):
            if text:
                texts.append(text)
    return texts


def _register_reattributed_provenance(
    state: RAGState, reattributed: Sequence[Reattribution]
) -> None:
    """Make re-attributed passages resolvable by the dialectical rebuild.

    ``_apply_final_content_gate`` rebuilds the ledger and citations from the
    prose markers against the ControversyMap; a ``[passage_<id>]`` marker the
    text verifier inserted must resolve there (and pass its verbatim-quote
    gate, which it does: the span is verbatim in that passage) or the rescued
    quotation would be dropped again as an unresolved id.
    """
    cmap = getattr(state, "controversy_map", None)
    if cmap is None:
        return
    for item in reattributed:
        locus = item.locus
        cmap.provenance.setdefault(
            locus.passage_id,
            PassageRef(
                passage_id=locus.passage_id,
                work=locus.title,
                author=locus.author,
                canonical_ref=locus.canonical_ref,
                cts_urn=locus.cts_urn,
                original_text=locus.text_content,
            ),
        )


def _reattributed_ids(answer: ScholarlyAnswer) -> set[str]:
    verification = answer.metadata.get("text_verification") or {}
    return {str(cid) for cid in verification.get("reattributed_citation_ids") or []}


def _mark_verifier_v2_unavailable(
    answer: ScholarlyAnswer,
    *,
    status: str,
    reason: str,
) -> ScholarlyAnswer:
    """Fail closed when the mandatory citation audit did not complete."""

    citations = [
        citation.model_copy(
            update={
                "verified": False,
                "verification_note": f"[{status.upper()}] citation audit unavailable",
            }
        )
        for citation in answer.citations
    ]
    ledger = [
        item.model_copy(update={"status": ClaimStatus.INSUFFICIENT})
        if item.status is ClaimStatus.SUPPORTED
        else item
        for item in answer.claim_ledger
    ]
    return answer.model_copy(
        update={
            "citations": citations,
            "claim_ledger": ledger,
            "metadata": {
                **answer.metadata,
                "citation_verifier_v2": {
                    "status": status,
                    "reason": reason[:300],
                    "total_citations": len(answer.citations),
                    "audited_citations": 0,
                    "total": 0,
                    "verified": 0,
                    "weak": 0,
                    "rejected": 0,
                    "missing": 0,
                    "parse_errors": 0,
                    "aborted": True,
                    # A crashed audit is an infrastructure failure: the
                    # publication gate blocks the whole answer instead of
                    # withholding sentences it has no verdicts for.
                    "infrastructure_failure": status == "error",
                },
            },
        }
    )


def _mark_verifier_v2_error(answer: ScholarlyAnswer, exc: Exception) -> ScholarlyAnswer:
    """Machine-readable, fail-closed signal when the v2 audit crashes."""

    return _mark_verifier_v2_unavailable(
        answer,
        status="error",
        reason=f"{type(exc).__name__}: {exc}",
    )


def _apply_final_content_gate(
    answer: ScholarlyAnswer,
    state: RAGState,
) -> ScholarlyAnswer:
    """Run the dialectical content gate after the final possible revision.

    A referee revision changes the prose.  Rebuild its provenance ledger and
    citations before evaluating the gate, otherwise a revised sentence can ride
    on the pre-revision ledger.  Non-dialectical renders are explicitly marked
    ``not_applicable``; they remain subject to the mandatory citation audit.
    """

    cmap = state.controversy_map
    if state.metadata.get("render_answer_mode") != "dialectical" or cmap is None:
        gate = {
            "status": "not_applicable",
            "passed": True,
            "reason": "non_dialectical_render",
        }
        state.metadata["content_gate"] = gate
        return answer.model_copy(
            update={"metadata": {**answer.metadata, "content_gate": gate}}
        )

    # The answer may have been revised after ProgrammaticVerify.  Make the
    # post-revision prose the only source of truth for ledger and citations.
    state.raw_answer = answer.answer
    state.claim_ledger = build_provenance_ledger(answer.answer, cmap)
    reattributed = _reattributed_ids(answer)
    state.citations = [
        citation.model_copy(update={"verification_note": REATTRIBUTION_NOTE})
        if citation.id in reattributed
        else citation
        for citation in _dialectical_citations(state)
    ]
    # The SUBSTANCE gate: enough markers must RESOLVE through the map (an
    # invented id never counts) and ≥1 primary passage must ground the prose.
    # An invoked fault line is recorded, not required — see
    # ``dialectical_synthesis.evaluate_content_gate``.
    verdict = evaluate_content_gate(answer.answer, cmap, ledger=state.claim_ledger)
    gate = {
        "status": "passed" if verdict.passed else "failed",
        "passed": verdict.passed,
        "reason": verdict.reason,
        "ledger_size": len(state.claim_ledger),
        **verdict.as_record(),
    }
    if verdict.warnings:
        logger.warning(
            "Content gate %s with warnings %s (resolved %d/%d markers, min %d)",
            gate["status"],
            ",".join(verdict.warnings),
            verdict.resolved_markers,
            verdict.total_markers,
            verdict.min_resolved,
        )
    state.metadata["content_gate"] = gate
    return answer.model_copy(
        update={
            "citations": list(state.citations),
            "claim_ledger": list(state.claim_ledger),
            "metadata": {**answer.metadata, "content_gate": gate},
        }
    )


def _build_scholar_diagnostics(state: RAGState) -> dict[str, Any]:
    """Per-query structured diagnostics for the scholar-RAG synthesis (F6).

    Prod drops INFO logs, so the ``ControversyMap assembled: …`` line never
    surfaces live. This packs the same grounding signals into a plain dict that
    rides on ``state.metadata['scholar_diagnostics']`` and therefore onto the
    SSE ``complete.metadata`` — visible WITHOUT changing the prod log level.

    Reads the ControversyMap (``state.controversy_map``) object directly — it
    is OWNED by ``controversy_map.py`` (another stream); we only read it here.
    Pure/deterministic, never raises (a diagnostics failure must not break a
    real answer); degrades to an ``error`` shape on the rare malformed map.

    Shape::

        {
            "frames": int,                       # contested fault lines
            "author_histogram": {author: count}, # contested-passage authors
            "passages_with_quotable_greek": int, # original_text holds polytonic
            "ancient_sources": int,              # distinct ancient passages
            "synthesis_model_used": str,         # model that wrote the prose
            "synthesis_status": str,             # ok|degraded|deterministic_map|…
            "kimi_fallback_fired": bool,         # 2nd-rung content model wrote it
            "deterministic_hedge_fired": bool,   # map serialised w/o any LLM
        }
    """
    try:
        cmap = getattr(state, "controversy_map", None)
        frames = list(getattr(cmap, "frames", []) or []) if cmap is not None else []

        # Contested-passage author histogram + quotable-Greek + ancient count,
        # deduplicated by passage_id across all frames (a passage shared by two
        # frames is ONE primary source, not two).
        seen_ids: set[str] = set()
        author_histogram: dict[str, int] = {}
        quotable_greek = 0
        ancient_sources = 0
        for frame in frames:
            for pref in getattr(frame, "contested_passages", []) or []:
                pid = str(getattr(pref, "passage_id", "") or "")
                if pid and pid in seen_ids:
                    continue
                if pid:
                    seen_ids.add(pid)
                ancient_sources += 1
                author = (getattr(pref, "author", "") or "?").strip() or "?"
                author_histogram[author] = author_histogram.get(author, 0) + 1
                if _GREEK_CHAR_RE.search(getattr(pref, "original_text", "") or ""):
                    quotable_greek += 1

        synthesis = state.metadata.get("scholar_synthesis")
        synthesis = synthesis if isinstance(synthesis, dict) else {}
        status = str(synthesis.get("status") or "")
        model_used = str(synthesis.get("model_used") or "")
        # The 2nd synthesis rung is a kimi CONTENT model; the deterministic map
        # hedge runs WITHOUT any LLM (status='deterministic_map'). Both are
        # quality-floor signals an operator must see without log access.
        kimi_fallback_fired = "kimi" in model_used.lower()
        deterministic_hedge_fired = status == "deterministic_map"

        return {
            "frames": len(frames),
            "author_histogram": author_histogram,
            "passages_with_quotable_greek": quotable_greek,
            "ancient_sources": ancient_sources,
            "synthesis_model_used": model_used,
            "synthesis_status": status,
            "kimi_fallback_fired": kimi_fallback_fired,
            "deterministic_hedge_fired": deterministic_hedge_fired,
        }
    except Exception as exc:  # noqa: BLE001 - diagnostics must never break answers
        logger.warning("scholar diagnostics assembly failed", exc_info=True)
        return {"error": f"{type(exc).__name__}: {exc}"[:200]}


AGENT_MODE = os.getenv("ELEUTHERIA_AGENT_MODE", "react")

#: Selectable pipelines. ``react`` (default) and ``fsm`` are the historical
#: modes; ``lead`` is the lead-researcher pipeline (facet decomposition ->
#: parallel sub-agents -> distilled dossiers -> the lead writes -> the same
#: verification tail). Selected per request (``pipeline``) or via
#: ``ELEUTHERIA_AGENT_MODE``; both are read at request time so an A/B can
#: flip them without a restart.
PIPELINES: frozenset[str] = frozenset({"react", "fsm", "lead"})


def resolve_pipeline(*overrides: str | None) -> str:
    """The pipeline for a request: the first explicit override, else the env.

    Unknown values fall back to ``react`` rather than raising — the API layer
    validates user input before it gets here.
    """
    for candidate in overrides:
        value = (candidate or "").strip().lower()
        if value in PIPELINES:
            return value
    env = (os.getenv("ELEUTHERIA_AGENT_MODE") or AGENT_MODE or "react").strip().lower()
    return env if env in PIPELINES else "react"


# FSM graph (kept for fsm mode and as fallback). GraphBuilder.node adapts the
# existing BaseNode classes while moving graph construction and execution onto the
# supported builder API.
_scholarly_graph_builder = GraphBuilder(
    state_type=RAGState,
    deps_type=Deps,
    input_type=ClassifyQueryType,
    output_type=ScholarlyAnswer,
)
_scholarly_graph_builder.add(
    _scholarly_graph_builder.edge_from(_scholarly_graph_builder.start_node).to(
        ClassifyQueryType
    )
)
for _node in (
    ClassifyQueryType,
    ExpandQuery,
    DiscoverCorpus,
    BuildResearchNotebook,
    PlanReading,
    TreeNavigateWorks,
    ExpandEvidenceBundles,
    SeekCounterEvidence,
    EvidenceSufficiency,
    DraftClaimLedger,
    RenderGroundedAnswer,
    ProgrammaticVerify,
):
    _scholarly_graph_builder.add(_scholarly_graph_builder.node(_node))
scholarly_graph = _scholarly_graph_builder.build()


class ScholarlyAgent:
    """High-level facade over the GraphRAG pipeline.

    In 'fsm' mode, runs the full pydantic-graph FSM.
    In 'react' mode, runs: ClassifyQueryType → AgentLoop → Synthesis.
    """

    def __init__(self, deps: Deps) -> None:
        self.deps = deps
        self._tool_registry: Any | None = None

    @property
    def _tools_by_name(self) -> Any:
        """Lazily built tool registry for sub-agents (hunter, bibliography).

        ``GraphRAGService`` duck-types this as a ``.get(name)`` mapping when
        wiring the CounterEvidenceHunter and BibliographyBuilder toolsets.
        Built on first access so test doubles with mock ``Deps`` never pay
        (or crash on) registry construction. Returns ``{}`` when the
        registry cannot be built — callers already degrade on missing tools.
        """
        if self._tool_registry is None:
            try:
                from eleutheria_graphrag.agents.tools import build_tool_registry

                self._tool_registry = build_tool_registry(self.deps)
            except Exception:
                logger.warning("Tool registry construction failed", exc_info=True)
                return {}
        return self._tool_registry

    async def query(
        self,
        question: str,
        *,
        max_iterations: int = 5,
        selected_model: str = "gemini-3.1-pro",
        retrieval_mode: str = "auto",
        agent_mode: str | None = None,
        hunt_counter_evidence: bool = False,
        pipeline: str | None = None,
        subagent_model: str | None = None,
    ) -> ScholarlyAnswer:
        mode = resolve_pipeline(pipeline, agent_mode)

        state = RAGState(
            question=question,
            max_iterations=max_iterations,
            selected_model=selected_model,
            retrieval_mode=retrieval_mode,
        )
        if hunt_counter_evidence:
            state.metadata["hunt_counter_evidence"] = True

        if mode == "react":
            internal = await self._run_react(state)
        elif mode == "lead":
            internal = await self._run_lead(state, subagent_model=subagent_model)
        else:
            # The legacy graph ends at ProgrammaticVerify, which is not a
            # publication verdict: run its draft through the SAME
            # verification + publication tail as the FSM stream, so the sync
            # and streaming facades reach one verdict for one draft.
            internal = await self._publish_fsm_draft(await self._run_fsm(state), state)
        # Both pipelines retain their draft for diagnostics. The public
        # ScholarlyAgent facade is itself a publication boundary and applies
        # the same verdict whatever the mode (idempotent on an applied one).
        return annotate_publication_decision(internal, withhold_prose=True)

    async def _publish_fsm_draft(
        self, answer: ScholarlyAnswer, state: RAGState
    ) -> ScholarlyAnswer:
        """Run the shared verification tail on an FSM draft, without a wire.

        Drains the status / audit frames ``_verify_for_publication`` emits for
        the stream and returns the gated answer it produced.
        """
        holder: dict[str, Any] = {}
        async for _frame in self._verify_for_publication(
            answer, state, journal=ResearchJournal(), result_into=holder
        ):
            pass
        return cast(ScholarlyAnswer, holder["answer"])

    async def _run_lead(
        self, state: RAGState, *, subagent_model: str | None = None
    ) -> ScholarlyAnswer:
        """Run the lead-researcher pipeline (see ``agents/lead_researcher``).

        Facet decomposition -> parallel bounded sub-agents -> distilled
        dossiers -> merge -> the lead writes through the existing synthesis ->
        the SAME verification tail (``_verify_for_publication``, drained).
        """
        from eleutheria_graphrag.agents.lead_researcher import run_lead

        return await run_lead(self, state, subagent_model=subagent_model)

    async def _run_fsm(self, state: RAGState) -> ScholarlyAnswer:
        """Run the original pydantic-graph FSM pipeline."""
        return await scholarly_graph.run(
            state=state,
            deps=self.deps,
            inputs=ClassifyQueryType(),
        )

    async def _run_react(self, state: RAGState) -> ScholarlyAnswer:
        """Run the new ReAct agent pipeline.

        Phase 1: ClassifyQueryType (deterministic)
        Phase 2: AgentLoop (ReAct with tools)
        Phase 3: DraftClaimLedger → RenderGroundedAnswer → ProgrammaticVerify
        """
        from pydantic_graph import End, GraphRunContext

        from eleutheria_graphrag.agents.react_loop import build_agent_loop
        from eleutheria_graphrag.agents.sse_emitter import NullEmitter
        from eleutheria_graphrag.agents.tools import build_tool_registry

        # Phase 1: Classify query type
        classify_node = ClassifyQueryType()
        ctx = GraphRunContext(state=state, deps=self.deps)
        await classify_node.run(ctx)
        logger.info(
            "Query classified: type=%s, complexity=%s",
            state.query_type,
            state.complexity,
        )

        # Phase 2: Agent loop (native tool-calling or legacy text mode)
        tools = build_tool_registry(self.deps)
        emitter = NullEmitter()
        agent = build_agent_loop(
            deps=self.deps,
            state=state,
            tools=tools,
            emitter=emitter,
        )
        await agent.run()
        logger.info(
            "Agent loop completed: %d calls, %d evidence, %d bundles",
            agent.calls_made,
            len(agent.evidence.primary_evidence)
            + len(agent.evidence.secondary_evidence),
            len(agent.evidence.evidence_bundles),
        )

        # Phase 2.4: Scholar-RAG (G6) controversy-map assembly. Flag-gated and
        # deterministic — runs the planner + assemble_controversy_map BEFORE the
        # context pack is (re)built, so the ## Controversy Frames layer fires and
        # synthesis routes dialectically instead of to the facet template. Inert
        # (and the legacy path byte-for-byte unchanged) when the flag is off.
        if scholar_rag_enabled():
            await self._assemble_controversy_map(state, tools)

        # Phase 2.5: post-loop quality gate — optional cross-encoder rerank,
        # evidence-sufficiency check with one bounded continuation round, and
        # (deep mode) the counter-evidence hunt whose findings feed the ledger.
        counter_items = await self._post_loop_quality_phase(state, agent)

        # Phase 3: Synthesis (reuse existing FSM nodes)
        # Run DraftClaimLedger → RenderGroundedAnswer → ProgrammaticVerify
        draft_node = DraftClaimLedger()
        ctx = GraphRunContext(state=state, deps=self.deps)
        await draft_node.run(ctx)
        self._merge_counter_ledger_items(state, counter_items)

        # M4 cutover: when Scholar-RAG is on and a ControversyMap assembled, the
        # FINAL ANSWER PROSE comes from dialectical synthesis over the map — NOT
        # the facet template. The DraftClaimLedger facet ledger is overwritten by
        # the prose-derived provenance ledger. On failure / empty prose we fall
        # back to the legacy RenderGroundedAnswer render (flag-OFF is untouched).
        dialectical_prose: str | None = None
        if self._scholar_render_active(state):
            dialectical_prose = await self._synthesize_dialectical(state)
        if dialectical_prose is None:
            render_node = RenderGroundedAnswer()
            ctx = GraphRunContext(state=state, deps=self.deps)
            await render_node.run(ctx)

        # F6: structured per-query grounding diagnostics on state.metadata so
        # they ride onto the SSE complete.metadata — visible in prod (which
        # drops INFO logs). _make_answer copies state.metadata onto the answer.
        state.metadata["scholar_diagnostics"] = _build_scholar_diagnostics(state)

        verify_node = ProgrammaticVerify()
        ctx = GraphRunContext(state=state, deps=self.deps)
        result = await verify_node.run(ctx)

        # ProgrammaticVerify returns End(output=ScholarlyAnswer)
        if isinstance(result, End):
            answer = result.data
        else:
            from eleutheria_graphrag.agents.graph_nodes import _make_answer

            answer = _make_answer(state)

        # Phase 3.5: Programmatic passage injection
        # If the LLM failed to include quotation blocks, inject them deterministically
        answer = self._inject_passage_quotations(answer, state)

        # Phase 4: deterministic ancient-text verification. Whitelist-first
        # (evidence gathered for this query passes without a DB query), then
        # a bounded DB probe. Report-only unless
        # ELEUTHERIA_TEXT_VERIFIER_ENFORCE is set.
        if _text_verifier_enabled():
            answer = await self._verify_ancient_text(answer, state)

        # Phase 4.6: referee pass (env-gated, bounded). Runs AFTER the text gate
        # so the referee reads what the reader will see; a revised answer is
        # re-gated inside the stage. Never raises, never empties the answer.
        answer, _referee_note = await self._referee_answer(answer, state)

        # Phase 4.7: the content gate MUST inspect the final prose, including a
        # possible referee revision.  It also rebuilds dialectical provenance so
        # the citation auditor never evaluates a stale pre-revision ledger.
        answer = _apply_final_content_gate(answer, state)

        # Phase 5: Adversarial citation verifier (v2). Optional — only runs
        # when ``deps.verifier_v2`` is wired. Publication is fail-closed: an
        # unavailable/crashed audit blocks the whole answer, while every
        # non-VERIFIED verdict withholds the sentences citing it. The public
        # boundaries (ScholarlyAgent.query, GraphRAGService, SSE) apply that
        # verdict through ``publication_gate``.
        content_passed = answer.metadata.get("content_gate", {}).get("passed") is True
        if not content_passed:
            answer = _mark_verifier_v2_unavailable(
                answer,
                status="skipped_content_gate",
                reason="citation audit skipped because final content gate failed",
            )
        elif self.deps.verifier_v2 is not None:
            try:
                answer, _report = await self._run_citation_verifier_v2(answer)
            except Exception as exc:
                logger.warning(
                    "CitationVerifierV2 failed — blocking publication",
                    exc_info=True,
                )
                answer = _mark_verifier_v2_error(answer, exc)
        else:
            answer = _mark_verifier_v2_unavailable(
                answer,
                status="unavailable",
                reason="CitationVerifierV2 is not configured",
            )

        return annotate_publication_decision(answer, withhold_prose=False)

    # ------------------------------------------------------------------
    # Scholar-RAG (G6) controversy-map assembly (flag-gated)
    # ------------------------------------------------------------------

    async def _assemble_controversy_map(self, state: RAGState, tools: Any) -> bool:
        """Deterministically populate ``state.controversy_map`` (Scholar-RAG seam).

        Runs the PlanResearch planner to pick an answer shape, then drives the
        documented ``assemble_controversy_map`` orchestration (find_debates ->
        build_controversy_frame over the surfaced fault lines). This is the
        wiring that makes the flag-ON path end-to-end: the context-pack
        ``## Controversy Frames`` layer (``graph_nodes.py`` seam) only fires
        when ``state.controversy_map is not None``, which routes synthesis to
        the dialectical path instead of the facet template.

        Driven deterministically off the planned debates — NOT off the ReAct
        agent's improvised tool calls — so the seam is reliable. Returns True
        when a non-empty map (≥1 frame) was assembled; on an empty map or any
        error, ``state.controversy_map`` is left ``None`` and the caller falls
        back to the legacy path gracefully (with a prose-stated degraded note).
        """
        from eleutheria_graphrag.agents.controversy_map import (
            assemble_controversy_map,
        )
        from eleutheria_graphrag.agents.plan_research import plan_research

        find_tool = tools.get("find_debates")
        build_tool = tools.get("build_controversy_frame")
        if find_tool is None or build_tool is None:
            logger.warning(
                "Scholar-RAG on but find_debates/build_controversy_frame "
                "unavailable — falling back to legacy synthesis"
            )
            state.metadata["controversy_map"] = {
                "status": "skipped",
                "reason": "relational tools unavailable",
            }
            return False

        try:
            plan = await plan_research(state.question, self.deps.llm)
            state.research_plan = plan
            cmap = await assemble_controversy_map(
                state.question,
                find_tool,
                build_tool,
                shape=plan.primary_shape,
            )
        except Exception as exc:
            logger.warning(
                "Controversy-map assembly failed (%s) — falling back to legacy "
                "synthesis",
                exc,
                exc_info=True,
            )
            state.metadata["controversy_map"] = {
                "status": "error",
                "reason": f"{type(exc).__name__}: {exc}"[:300],
            }
            return False

        meta = {
            "shape": plan.primary_shape.value,
            "frames": len(cmap.frames),
            "coverage_gaps": len(cmap.coverage_gaps),
            "provenance_passages": len(cmap.provenance),
        }
        # Keep the gap TEXTS (not just the count) on state: each one names a
        # debate seed the assembler opened and then dropped, and the degraded
        # branch below leaves ``state.controversy_map`` None, which would
        # otherwise lose them. Read back by ``controversy_gap_notes``.
        state.metadata["controversy_map_gaps"] = list(cmap.coverage_gaps)
        if not cmap.frames:
            # Empty map: do NOT route to the dialectical layer. Leave
            # controversy_map None so the seam stays inert and the legacy
            # path runs, but record the degraded note (prose-stated downstream).
            logger.info(
                "Controversy-map assembly yielded 0 frames — legacy synthesis "
                "(coverage_gaps=%d)",
                len(cmap.coverage_gaps),
            )
            state.metadata["controversy_map"] = {
                "status": "degraded",
                "reason": "assembly yielded 0 frames",
                **meta,
            }
            state.research_notebook.competing_hypotheses.append(
                "[degraded: no controversy frames assembled — answer falls back "
                "to the non-dialectical evidence synthesis]"
            )
            return False

        state.controversy_map = cmap
        # These are texts actually loaded by map assembly, independently of
        # which sources the model eventually cites. Keep retrieval observable.
        state.metadata["retrieved_passages"] = list(
            dict.fromkeys(
                [
                    *state.metadata.get("retrieved_passages", []),
                    *(
                        p.passage_id
                        for f in cmap.frames
                        for p in f.contested_passages
                        if p.original_text or p.english_text
                    ),
                    *(
                        p.passage_id
                        for p in cmap.exegesis_units
                        if p.original_text or p.english_text
                    ),
                ]
            )
        )
        state.metadata["controversy_map"] = {"status": "ok", **meta}
        _trace_stage(state, "controversy_map", meta)
        return True

    # ------------------------------------------------------------------
    # Dialectical synthesis (Scholar-RAG M4 cutover — flag-gated render)
    # ------------------------------------------------------------------

    def _scholar_render_active(self, state: RAGState) -> bool:
        """The dialectical render is THE render path iff the flag is on AND a
        ControversyMap actually assembled (``state.controversy_map`` populated).

        Both must hold; otherwise the legacy facet-template render runs
        byte-for-byte unchanged (flag-OFF and flag-ON-but-empty-map both keep
        the legacy path)."""
        return scholar_rag_enabled() and state.controversy_map is not None

    async def _synthesize_dialectical(
        self,
        state: RAGState,
        *,
        on_reasoning: Any | None = None,
    ) -> str | None:
        """Produce the final answer prose from ``state.controversy_map`` via
        :func:`synthesize_dialectical` (M4 cutover), writing it into the same
        seam the legacy render uses: ``state.raw_answer`` + ``state.claim_ledger``.

        The prose IS the source of truth; the provenance ledger is reconstructed
        from it (``build_provenance_ledger``) and replaces the pre-built
        ``DraftClaimLedger`` facet ledger so the verifier and the UI reference
        map index the dialectical answer, not the discarded template scaffolding.

        When ``on_reasoning`` is supplied (the streaming path), the thinking
        model's ``reasoning_content`` is streamed LIVE through it via
        :func:`synthesize_dialectical_stream` (each reasoning delta is awaited on
        the callback, which emits a ``synthesis_reasoning`` SSE event). The
        reasoning text NEVER enters the answer. With ``on_reasoning=None`` (the
        non-streaming path) the blocking :func:`synthesize_dialectical` runs,
        byte-for-byte unchanged.

        On success returns the synthesis prose. If the full synthesis genuinely
        fails or returns empty (e.g. every fallback rung errored), it does NOT
        drop to the facet template: a SAFETY-BELT still-dialectical
        :func:`synthesize_degraded` hedge over the same ControversyMap is
        attempted, and only if THAT also fails is ``None`` returned (the caller's
        legacy render is then the absolute last resort). Never raises into the
        pipeline."""
        cmap = state.controversy_map
        if cmap is None:  # defensive — caller already gated on this
            return None
        max_tokens = scholar_render_max_tokens(
            getattr(getattr(state, "research_plan", None), "budget_tier", None)
            or "standard"
        )
        try:
            if on_reasoning is not None:
                result = await synthesize_dialectical_stream(
                    state,
                    cmap,
                    self.deps.llm,
                    on_reasoning=on_reasoning,
                    max_tokens=max_tokens,
                )
            else:
                result = await synthesize_dialectical(
                    state,
                    cmap,
                    self.deps.llm,
                    max_tokens=max_tokens,
                )
        except Exception:  # noqa: BLE001 - never crash the pipeline on synthesis
            logger.warning(
                "Dialectical synthesis raised; trying degraded hedge", exc_info=True
            )
            return await self._synthesize_degraded_fallback(state, cmap, "raised")

        prose = (result.prose or "").strip()
        if not prose:
            return await self._synthesize_degraded_fallback(state, cmap, "empty")

        state.raw_answer = prose
        # The ledger is a BYPRODUCT of the prose (reverses the legacy
        # DraftClaimLedger->prose dependency): index the inline markers back to
        # the map so the verifier + UI reference map reflect the dialectical
        # answer, not the discarded facet scaffolding.
        ledger = result.ledger or build_provenance_ledger(prose, cmap)
        if ledger:
            state.claim_ledger = ledger
        state.metadata["render_answer_mode"] = "dialectical"
        state.metadata["scholar_synthesis"] = {
            "status": "ok",
            "model_used": result.model_used,
            "ledger_size": len(ledger),
            "degraded": result.degraded,
        }
        # The thinking model's chain-of-thought (reasoning_content) is a trace
        # artefact ONLY — never part of the answer. Surface it on the metadata so
        # the SSE reasoning channel can show it, truncated to stay low-risk.
        if result.reasoning_trace:
            state.metadata["scholar_synthesis_reasoning"] = truncate_text(
                result.reasoning_trace, 4000
            )
        _trace_stage(
            state,
            "dialectical_synthesis",
            {
                "mode": "dialectical",
                "model_used": result.model_used,
                "ledger_size": len(ledger),
                "raw_excerpt": truncate_text(prose, 2000),
            },
        )
        return prose

    async def _synthesize_degraded_fallback(
        self, state: RAGState, cmap: Any, reason: str
    ) -> str | None:
        """SAFETY BELT: when the full dialectical synthesis fails/empties, emit a
        minimal STILL-DIALECTICAL hedge over the same ControversyMap rather than
        dropping to the legacy facet template (the "frames the issue as" string).

        :func:`synthesize_degraded` reasons over whatever frames assembled and
        states its coverage limit in prose — never a node-paste, never a
        template. On success it lands in the same render seam (``raw_answer`` +
        a prose-derived ledger) and is marked ``render_answer_mode=dialectical``
        so the caller does NOT run ``RenderGroundedAnswer``. Returns ``None`` only
        if even the hedge fails (then the legacy render is the last resort).
        Never raises into the pipeline."""
        try:
            prose = (await synthesize_degraded(cmap, self.deps.llm) or "").strip()
        except Exception:  # noqa: BLE001 - never crash the pipeline on the hedge
            logger.warning(
                "Degraded dialectical hedge raised; trying deterministic map hedge",
                exc_info=True,
            )
            prose = ""

        # FINAL GUARANTEE: when even the LLM hedge empties (e.g. all Fireworks
        # rungs 429 and Gemini 429s too), a POPULATED controversy map must STILL
        # yield a real answer — never fall through to the legacy Gemini path that
        # 429s and shows the bare "insufficient evidence" sentence. Serialise the
        # contending positions + grounded passages into prose deterministically.
        hedge_mode = "degraded"
        if not prose:
            try:
                prose = (deterministic_map_hedge(cmap) or "").strip()
            except Exception:  # noqa: BLE001 - the floor must never raise
                logger.warning("Deterministic map hedge raised", exc_info=True)
                prose = ""
            if prose:
                hedge_mode = "deterministic_map"

        if not prose:
            # Only a genuinely empty map (no frames/positions/passages) reaches
            # here — there is nothing to render, so the legacy path is correct.
            state.metadata["scholar_synthesis"] = {
                "status": "failed",
                "reason": reason,
            }
            return None

        state.raw_answer = prose
        ledger = build_provenance_ledger(prose, cmap)
        if ledger:
            state.claim_ledger = ledger
        # Still the dialectical render path — NOT the facet template — so the
        # caller skips RenderGroundedAnswer. Marked degraded for observability.
        state.metadata["render_answer_mode"] = "dialectical"
        state.metadata["scholar_synthesis"] = {
            "status": hedge_mode,
            "reason": reason,
            "ledger_size": len(ledger),
            "degraded": True,
        }
        _trace_stage(
            state,
            "dialectical_synthesis",
            {
                "mode": f"dialectical_{hedge_mode}",
                "reason": reason,
                "ledger_size": len(ledger),
                "raw_excerpt": truncate_text(prose, 2000),
            },
        )
        return prose

    # ------------------------------------------------------------------
    # Post-loop quality gate (react paths)
    # ------------------------------------------------------------------

    async def _post_loop_quality_phase(
        self, state: RAGState, agent: Any
    ) -> list[ClaimLedgerItem]:
        """Quality machinery between the agent loop and DraftClaimLedger.

        1. Optional cross-encoder rerank (ELEUTHERIA_RERANKER, default off).
        2. Evidence-sufficiency check; when insufficient, at most one bounded
           continuation round of the agent loop (env-capped).
        3. Deep mode: CounterEvidenceHunter run against the working
           hypotheses; findings land in the research notebook (ledger prompt
           input) and are returned as ready-made ledger items for merging
           after DraftClaimLedger.

        Every step degrades to a no-op on error — this phase must never take
        down a query that the legacy pipeline would have answered.
        """
        await self._maybe_rerank_bundles(state)
        if not state.context_pack.prompt_context:
            state.context_pack = _build_context_pack(state)
            state.accumulated_context = state.context_pack.prompt_context

        try:
            continued = await self._maybe_continue_for_sufficiency(state, agent)
        except Exception:
            logger.warning("Sufficiency continuation failed", exc_info=True)
            continued = False
        if continued:
            # The continuation round repopulated evidence and reset the
            # context pack — rerank the new bundle set and rebuild the pack.
            await self._maybe_rerank_bundles(state)
            state.context_pack = _build_context_pack(state)
            state.accumulated_context = state.context_pack.prompt_context

        counter_items: list[ClaimLedgerItem] = []
        if state.metadata.get("hunt_counter_evidence"):
            try:
                counter_items = await self._hunt_counter_evidence_pre_ledger(state)
            except Exception as exc:
                logger.warning("Pre-ledger counter-evidence hunt failed: %s", exc)
                state.metadata["counter_evidence_hunt"] = {
                    "status": "error",
                    "reason": f"{type(exc).__name__}: {exc}"[:300],
                }
        return counter_items

    async def _maybe_rerank_bundles(self, state: RAGState) -> None:
        """Score evidence bundles with the cross-encoder (env-gated, lazy).

        Writes ``rerank_score`` into each bundle's metadata; the score is
        consumed by ``_bundle_score`` when ``_build_context_pack`` orders
        bundles for packing. Degrades cleanly: any failure (model absent,
        download error, prediction error) leaves the original order intact.
        """
        if (
            not _reranker_enabled()
            or self.deps.reranker is None
            or not state.evidence_bundles
        ):
            return
        try:
            proxies = [
                Evidence(
                    id=bundle.bundle_id,
                    label=bundle.work_title or bundle.bundle_id,
                    type="passage",
                    text_content="\n".join(
                        text
                        for text in (bundle.original_text, bundle.translation_text)
                        if text
                    ),
                )
                for bundle in state.evidence_bundles
            ]
            ranked = await self.deps.reranker.rerank(
                state.question,
                proxies,
                top_k=len(proxies),
                score_threshold=-1e9,
            )
            scores = {item.id: item.score for item in ranked}
            applied = 0
            for bundle in state.evidence_bundles:
                if bundle.bundle_id in scores:
                    bundle.metadata["rerank_score"] = scores[bundle.bundle_id]
                    applied += 1
            state.metadata["reranker"] = {"applied": True, "scored": applied}
        except Exception:
            logger.warning(
                "Cross-encoder rerank failed — keeping retrieval order",
                exc_info=True,
            )
            state.metadata["reranker"] = {"applied": False, "error": True}

    async def _maybe_continue_for_sufficiency(
        self, state: RAGState, agent: Any
    ) -> bool:
        """Run the sufficiency check; grant at most one continuation round.

        The check itself (heuristic + LLM) is the extracted core of the FSM
        ``EvidenceSufficiency`` node. When the verdict is insufficient and the
        env-capped budget allows, the agent loop is re-run once with the
        sufficiency feedback injected as a tool-result-style block appended to
        the user question (the loop rebuilds its conversation from
        ``state.question`` on each run, so this is the injection point that
        both the legacy and native loops honour). The round is bounded by
        shrinking the loop's own call budget. Returns True when a
        continuation round actually ran.
        """
        score, sufficient, reason, refinement = await assess_evidence_sufficiency(
            state, self.deps
        )
        # Record the critic's verdict whatever it is — an "insufficient" verdict
        # names a real gap in the answer, and the research journal surfaces it
        # even when no continuation round could be granted.
        check: dict[str, Any] = {
            "score": round(float(score), 4),
            "sufficient": bool(sufficient),
            "reason": reason,
            "refinement": refinement,
            "continued": False,
        }
        state.metadata["sufficiency_check"] = check
        if sufficient:
            return False
        budget = _sufficiency_continuation_budget()
        already = int(state.metadata.get("sufficiency_continuations", 0))
        if budget < 1 or already >= budget:
            return False
        if not hasattr(agent, "run"):
            return False
        state.metadata["sufficiency_continuations"] = already + 1
        check["continued"] = True

        feedback_lines = [
            "TOOL RESULT — evidence_sufficiency_check:",
            f"verdict=insufficient score={score:.2f}",
            f"reason: {reason}",
        ]
        if refinement:
            feedback_lines.append(f"suggested refinement: {refinement}")
            state.sub_queries = [refinement]
        feedback_lines.append(
            "Fill the evidence gap with a few targeted tool calls, then finish."
        )
        feedback = "\n".join(feedback_lines)

        extra = _sufficiency_extra_calls()
        # Bound the continuation round on either loop implementation.
        if hasattr(agent, "budget") and isinstance(
            getattr(agent, "calls_made", None), int
        ):
            agent.budget = agent.calls_made + extra
        if hasattr(agent, "max_iterations"):
            agent.max_iterations = extra

        original_question = state.question
        state.question = f"{original_question}\n\n{feedback}"
        try:
            await agent.run()
        except Exception:
            logger.warning(
                "Sufficiency continuation round failed — keeping prior evidence",
                exc_info=True,
            )
        finally:
            state.question = original_question
        logger.info(
            "Sufficiency continuation ran (score=%.2f): %s",
            score,
            reason,
        )
        return True

    def _build_counter_evidence_hunter(self) -> Any | None:
        """Wire a CounterEvidenceHunter to this agent's tool registry."""
        from eleutheria_graphrag.services.counter_evidence_hunter import (
            CounterEvidenceHunter,
            MCPToolset,
        )

        tools = self._tools_by_name
        search_tool = tools.get("search_passages")
        subgraph_tool = tools.get("explore_subgraph")
        if search_tool is None or subgraph_tool is None:
            return None
        toolset = MCPToolset(
            search_passages=search_tool,
            explore_subgraph=subgraph_tool,
            get_neighbors=tools.get("get_neighbors"),
            get_node_detail=tools.get("get_node_detail"),
            # The dead `query_scholarly_consensus` ref always resolved to None.
            # Repoint it to the Scholar-RAG `find_debates` tool (present only when
            # ELEUTHERIA_SCHOLAR_RAG is on; None otherwise — unchanged default).
            query_scholarly_consensus=tools.get("find_debates"),
        )
        return CounterEvidenceHunter(llm=self.deps.llm, tools=toolset)

    @staticmethod
    def _pre_ledger_claim_units(state: RAGState) -> list[ClaimUnit]:
        """Hunt anchors before a ledger exists: working hypotheses + seeds."""
        seeds = list(state.seed_node_ids[:5])
        hypotheses = [
            h.strip()
            for h in state.research_notebook.competing_hypotheses[:3]
            if h and h.strip()
        ]
        if not hypotheses:
            question = state.question.strip()
            hypotheses = [question] if question else []
        return [
            ClaimUnit(
                claim_id=f"pre{idx + 1}",
                claim_text=hypothesis[:400],
                seed_node_ids=seeds,
            )
            for idx, hypothesis in enumerate(hypotheses)
        ]

    async def _hunt_counter_evidence_pre_ledger(
        self, state: RAGState
    ) -> list[ClaimLedgerItem]:
        """Deep mode: adversarial hunt before the claim ledger is drafted.

        Findings are appended to the research notebook (so the ledger and
        render prompts see them) and converted into counter-evidence ledger
        items that the caller merges after ``DraftClaimLedger`` runs.
        """
        hunter = self._build_counter_evidence_hunter()
        if hunter is None:
            state.metadata["counter_evidence_hunt"] = {
                "status": "skipped",
                "reason": "agent tools unavailable",
            }
            return []
        claims = self._pre_ledger_claim_units(state)
        if not claims:
            state.metadata["counter_evidence_hunt"] = {
                "status": "skipped",
                "reason": "no hypotheses to audit",
            }
            return []
        report: CounterEvidenceReport = await hunter.hunt(
            CounterEvidenceDraft(answer=state.question, claims=claims)
        )
        notebook = state.research_notebook
        for finding in report.per_claim_findings:
            for testimony in finding.opposing_testimonia[:4]:
                note = (
                    f"{testimony.source}: {testimony.brief_reasoning or testimony.type}"
                )
                if note not in notebook.counter_evidence:
                    notebook.counter_evidence.append(note)
        items = counter_report_to_ledger_items(report)
        state.metadata["counter_evidence_hunt"] = {
            "status": "ok",
            "claims_audited": len(claims),
            "total_testimonia": report.total_testimonia,
            "ledger_items": len(items),
            "aggregate_summary": report.aggregate_summary,
        }
        _trace_stage(
            state,
            "counter_evidence_hunt",
            {
                "mode": "pre_ledger",
                "claims_audited": len(claims),
                "total_testimonia": report.total_testimonia,
                "ledger_items": len(items),
            },
        )
        return items

    @staticmethod
    def _merge_counter_ledger_items(
        state: RAGState, counter_items: list[ClaimLedgerItem]
    ) -> None:
        """Append hunter-derived counter-evidence claims to the drafted ledger."""
        if not counter_items:
            return
        state.claim_ledger = list(state.claim_ledger) + counter_items
        state.research_notebook.claim_ledger = state.claim_ledger
        state.metadata["counter_evidence_ledger_items"] = len(counter_items)

    async def _run_citation_verifier_v2(
        self, answer: ScholarlyAnswer
    ) -> tuple[ScholarlyAnswer, VerificationReport | None]:
        """Run the v2 adversarial verifier and attach its report to the answer.

        Returns the (possibly updated) answer and the verification report so
        the streaming path can emit per-citation SSE events from the checks.
        """
        verifier = self.deps.verifier_v2
        if verifier is None:
            return (
                _mark_verifier_v2_unavailable(
                    answer,
                    status="unavailable",
                    reason="CitationVerifierV2 is not configured",
                ),
                None,
            )
        if not answer.citations:
            return (
                _mark_verifier_v2_unavailable(
                    answer,
                    status="failed",
                    reason="answer has no auditable citations",
                ),
                None,
            )
        max_claims = _verifier_v2_max_claims()
        if max_claims == 0:
            return (
                _mark_verifier_v2_unavailable(
                    answer,
                    status="disabled",
                    reason="ELEUTHERIA_VERIFIER_V2_MAX_CLAIMS=0",
                ),
                None,
            )

        # Enumerate every (sentence, citation) pair, order by risk and cut at
        # the per-query budget. Pairs beyond the cap go unaudited: they stay
        # withheld (fail-closed) and are counted in the record.
        ordered = _order_audit_pairs(_enumerate_audit_pairs(answer))
        sampled = ordered[:max_claims]
        unaudited = ordered[max_claims:]
        claims = [
            _draft_claim_for(
                answer, pair.citation, pair.claim, sentence_index=pair.sentence_index
            )
            for pair in sampled
        ]

        draft = SynthesizedDraft(
            question=answer.question,
            answer_text=answer.answer,
            claims=claims,
        )
        report = await verifier.verify_draft(draft)
        audit = _PairAudit(claims, report.checks, unaudited)

        # Merge per-citation verdicts back into Citation.verified for the
        # frontend: a citation is verified when every audited pair of it is;
        # the note carries its harshest verdict. The publication gate
        # withholds the sentence of each failing pair at the public boundary.
        updated_citations = []
        for citation in answer.citations:
            checks = audit.checks_by_id.get(citation.id)
            if not checks:
                updated_citations.append(citation)
                continue
            harshest = _harshest(checks)
            updated_citations.append(
                citation.model_copy(
                    update={
                        "verified": all(c.is_passing for c in checks),
                        "verification_note": (
                            f"[{harshest.status.value}] {harshest.reasoning}"
                        ),
                    }
                )
            )

        # Every verdict other than VERIFIED downgrades the affected ledger
        # claim: a claim citing an id without a single verified pair, or a
        # claim whose own sentence carries a failing pair. WEAK is not
        # permission to publish an assertion: it means the cited source does
        # not support it.
        failing_ids = {cid for cid in audit.audited_ids if audit.failing_pairs(cid)}
        updated_ledger = answer.claim_ledger
        if failing_ids:
            from eleutheria_graphrag.agents.state import ClaimStatus

            fully_failing = audit.fully_failing_ids
            failing_sentences = audit.failing_sentences()

            def downgraded(item: ClaimLedgerItem) -> bool:
                cited = {
                    cid
                    for cid in failing_ids
                    if _ledger_item_cites(item.evidence_ids, cid)
                }
                if not cited:
                    return False
                if cited & fully_failing:
                    return True
                return _claim_was_withheld(item.claim, failing_sentences)

            updated_ledger = [
                item.model_copy(update={"status": ClaimStatus.INSUFFICIENT})
                if downgraded(item)
                else item
                for item in answer.claim_ledger
            ]

        pairs = audit.pair_counts()
        id_counts = audit.id_counts()
        audited = min(len(audit.audited_ids), len(answer.citations))
        full_coverage = audited == len(answer.citations) and pairs["unaudited"] == 0

        # Honest grounding: verified/audited over the audited pairs replaces
        # the ref-resolution ratio computed by ProgrammaticVerify. The score
        # only covers the audited pairs, so its coverage is always recorded
        # alongside it — a 100 over a partial sample must never read as
        # "every claim verified".
        evaluation = answer.self_rag_evaluation
        grounding_meta: dict[str, Any] | None = None
        if evaluation is not None and pairs["audited"]:
            grounding = int(round(100 * pairs["verified"] / pairs["audited"]))
            grounding_meta = {
                "score": grounding,
                "method": "verifier_v2_sample",
                "audited_citations": audited,
                "total_citations": len(answer.citations),
                "audited_pairs": pairs["audited"],
                "total_pairs": pairs["total"],
                "coverage": (
                    "full"
                    if full_coverage
                    else f"partial: {audited}/{len(answer.citations)} audited"
                ),
            }
            try:
                evaluation = evaluation.model_copy(update={"grounding": grounding})
            except AttributeError:
                logger.debug("self_rag_evaluation has no model_copy — skipping")

        parse_errors = sum(
            1
            for cid in audit.audited_ids
            if any(c.parse_error for c in audit.checks_by_id[cid])
        )
        audit_passed = (
            full_coverage
            and pairs["verified"] == pairs["audited"]
            and not any(c.parse_error for c in report.checks)
            and not report.aborted
        )

        updated = answer.model_copy(
            update={
                "citations": updated_citations,
                "claim_ledger": updated_ledger,
                "self_rag_evaluation": evaluation,
                "metadata": {
                    **answer.metadata,
                    "retrieved_node_ids": list(
                        dict.fromkeys(
                            [
                                *answer.seed_nodes,
                                *answer.context_nodes,
                            ]
                        )
                    ),
                    **({"grounding": grounding_meta} if grounding_meta else {}),
                    "citation_verifier_v2": {
                        "status": "passed" if audit_passed else "failed",
                        # Id-level counts (legacy shape): an id is verified
                        # when every audited pair of it is, and carries its
                        # harshest verdict otherwise. Pair-level counts live
                        # under ``pairs``.
                        "total": len(audit.audited_ids),
                        "sampled": len(claims),
                        "max_claims": max_claims,
                        "audited_citations": audited,
                        "total_citations": len(answer.citations),
                        "verified": id_counts["verified"],
                        "weak": id_counts["weak"],
                        "rejected": id_counts["rejected"],
                        "missing": id_counts["missing"],
                        "parse_errors": parse_errors,
                        "rejection_rate": report.rejection_rate,
                        "flagged_for_rewrite": list(
                            dict.fromkeys(report.flagged_for_rewrite)
                        ),
                        "warning": report.warning,
                        "aborted": report.aborted,
                        # The unit of audit is the (sentence, citation) pair:
                        # how many there were, how many were judged, with
                        # which verdicts, and how many the cap left unjudged
                        # (withheld as unaudited).
                        "pairs": pairs,
                        # Ids the audit cleared on every audited pair. The
                        # publication gate keeps exactly these in the public
                        # list, plus any id with at least one verified pair;
                        # an id absent from both lists went unaudited and is
                        # withheld as such.
                        "verified_citations": audit.verified_ids,
                        # Verification report for every id with a failing
                        # pair — the honest record of what was withheld and
                        # why: the harshest verdict at the top, the failing
                        # pairs (sentence index, sentence, clause) beneath,
                        # and ``verified_pairs`` so the gate withholds by
                        # sentence when other uses of the id were verified.
                        # ``parse_error`` separates a verifier failure from a
                        # genuine adversarial WEAK.
                        "failed_citations": audit.failed_citations(),
                        # Pairs the cap left unjudged: withheld sentence by
                        # sentence (or the whole citation, when none of its
                        # pairs was judged).
                        "unaudited_pairs": audit.unaudited_pairs(),
                        # Evidence layer each verdict was reached against —
                        # "passage" (verbatim corpus text / reviewed page) or
                        # "node" (the graph's curated statement of a scholar's
                        # argument or position). A node-verified citation is
                        # published like any other, but readers of the record
                        # can tell the two layers apart.
                        "evidence_kinds": {
                            check.citation_id: check.evidence_kind
                            for check in report.checks
                        },
                        # Judge context: how many propositions were isolated
                        # inside a multi-source sentence, how many companion
                        # sources were shown, and every fetch-on-demand call
                        # (aggregate; per-check detail lives on the report).
                        "clauses_isolated": sum(
                            1 for check in report.checks if check.sentence
                        ),
                        "companions": {
                            "total": sum(
                                len(check.companion_ids) for check in report.checks
                            ),
                            "citations_with_companions": sum(
                                1 for check in report.checks if check.companion_ids
                            ),
                        },
                        "tool_calls": _aggregate_tool_calls(report.checks),
                    },
                },
            }
        )
        return updated, report

    async def _stream_citation_audit(
        self,
        answer: ScholarlyAnswer,
        result_into: dict[str, Any],
    ) -> AsyncIterator[str]:
        """Streaming wrapper for the v2 audit (used by ``_stream_react``).

        Runs the verifier under the SSE heartbeat (the audit is one wave of
        LLM calls, 10-60 s on a full sample), emits one ``citation_verified``
        event per check, then a ``citation_audit`` stage_complete. The merged
        answer lands in ``result_into['answer']``. Any audit failure is recorded
        as a blocking verdict; the public streaming boundary withholds the draft.
        """
        stage_started = _time_mod.perf_counter()
        report: VerificationReport | None = None
        holder: dict[str, Any] = {}
        try:
            async for hb in self._await_with_heartbeat(
                self._run_citation_verifier_v2(answer),
                label="Auditing citations",
                stage_id="citation_audit",
                max_wait=_citation_audit_max_wait(),
                result_into=holder,
            ):
                yield hb
            verified_answer, report = holder.get("value", (answer, None))
            result_into["answer"] = verified_answer
        except Exception as exc:
            logger.warning(
                "CitationVerifierV2 failed in stream — blocking publication",
                exc_info=True,
            )
            result_into["answer"] = _mark_verifier_v2_error(answer, exc)

        if report is not None:
            for check in report.checks:
                yield json.dumps(
                    {
                        "type": "citation_verified",
                        "passage_id": check.citation_id,
                        "sentence_index": check.sentence_index,
                        "verified": check.is_passing,
                        "status": check.status.value,
                        "reason": check.reasoning,
                    }
                )

        audit_ms = int((_time_mod.perf_counter() - stage_started) * 1000)
        yield json.dumps(
            {
                "type": "stage_complete",
                "stage": "citation_audit",
                "duration_ms": audit_ms,
                "metadata": (
                    {
                        "total": report.total,
                        "verified": report.verified,
                        "weak": report.weak,
                        "rejected": report.rejected,
                        "missing": report.missing,
                    }
                    if report is not None
                    else {"status": "error", "publishable": False}
                ),
            }
        )

    @staticmethod
    def _inject_passage_quotations(
        answer: ScholarlyAnswer, state: Any
    ) -> ScholarlyAnswer:
        """Programmatic injection of passage quotations when the LLM omits them.

        If the rendered answer has fewer than 2 blockquote sections with Greek/Latin
        text, we append a "Primary Textual Evidence" section with the best evidence
        bundles — original text + translation, properly attributed.

        This is 100% deterministic — no LLM calls.
        """
        import re as _re

        # Scholar-RAG M4 (F10): the dialectical answer quotes contested primary
        # text INLINE from the ControversyMap; post-hoc bundle dumping would bolt
        # legacy node-pasted passages onto it. Skip injection entirely on this path.
        if state.metadata.get("render_answer_mode") == "dialectical":
            return answer

        text = answer.answer
        # Count existing Greek blockquotes (lines starting with > containing Greek chars)
        greek_quote_count = len(
            _re.findall(
                r"^>\s*.*[\u0370-\u03FF\u1F00-\u1FFF]",
                text,
                _re.MULTILINE,
            )
        )

        if greek_quote_count >= 2:
            return answer  # LLM already included quotations

        bundles = state.evidence_bundles
        if not bundles:
            return answer

        # Build quotation blocks from the best evidence bundles
        sections: list[str] = []
        seen_works: set[str] = set()

        for bundle in bundles:
            if not bundle.original_text or len(bundle.original_text.strip()) < 20:
                continue
            work_key = bundle.work_title or bundle.work_id
            if work_key in seen_works:
                continue
            seen_works.add(work_key)

            # Build the quotation block
            author = bundle.author or "Unknown"
            ref = bundle.canonical_ref or ""
            title = bundle.work_title or "Unknown work"
            original = bundle.original_text.strip()
            # Truncate very long passages
            if len(original) > 600:
                original = original[:600] + "..."

            block = f"> {original} ({author}, *{title}* {ref})"

            if bundle.translation_text:
                trans = bundle.translation_text.strip()
                if len(trans) > 600:
                    trans = trans[:600] + "..."
                block += f'\n> "{trans}"'

            ref_marker = ""
            if (
                bundle.bundle_id
                and state.context_pack
                and state.context_pack.bundle_refs
            ):
                ref_marker = state.context_pack.bundle_refs.get(bundle.bundle_id, "")
                if ref_marker:
                    ref_marker = f" [{ref_marker}]"

            block += ref_marker
            sections.append(block)

            if len(sections) >= 5:
                break

        if not sections:
            return answer

        # Append the primary sources section
        injection = "\n\n## Primary Textual Evidence\n\n" + "\n\n".join(sections)
        new_text = text.rstrip() + injection

        return answer.model_copy(
            update={
                "answer": new_text,
                "metadata": {
                    **answer.metadata,
                    "passage_injection": {
                        "injected": len(sections),
                        "reason": f"LLM produced only {greek_quote_count} Greek quotation(s), minimum is 2",
                    },
                },
            }
        )

    async def _verify_ancient_text(
        self, answer: ScholarlyAnswer, state: RAGState
    ) -> ScholarlyAnswer:
        """Deterministic post-render check: ancient text must come from evidence.

        Whitelist-first: spans already present in this query's evidence
        bundles/descriptions pass with no DB query. The rest goes through a
        bounded anchor-token DB probe (accent/sigma/punctuation-insensitive
        comparison in Python). Report-only by default — outcomes land in
        ``metadata.text_verification``; prose is only altered when
        ``ELEUTHERIA_TEXT_VERIFIER_ENFORCE`` is truthy. Degrades gracefully:
        any internal error leaves the answer untouched.
        """
        from eleutheria_graphrag.agents.text_verifier import (
            enforce_answer,
            enforcement_enabled,
            reattribute_unverified_spans,
            verify_ancient_text,
        )

        try:
            evidence_texts = _collect_evidence_texts(state)
            result = await verify_ancient_text(
                answer.answer,
                self.deps.db,
                evidence_texts=evidence_texts,
            )
            text = answer.answer
            citations = list(answer.citations)
            # Before deleting anything: a span verbatim in exactly one corpus
            # locus is kept and cited to that passage instead (its reference
            # was wrong or the bounded probe missed it); a list of attested
            # technical terms or a short attested phrase is kept without a
            # citation — never Greek that is not verbatim-attested. Enforce
            # mode only: report-only leaves the prose untouched by contract.
            if enforcement_enabled() and not result.all_verified:
                rescued = await reattribute_unverified_spans(
                    text,
                    result,
                    self.deps.db,
                    citations=citations,
                    evidence_texts=evidence_texts,
                )
                text = rescued.text
                citations.extend(rescued.citations)
                _register_reattributed_provenance(state, rescued.reattributed)
            enforce = enforcement_enabled() and not result.all_verified
            new_text = enforce_answer(text, result) if enforce else text
            answer = answer.model_copy(
                update={
                    "answer": new_text,
                    "citations": citations,
                    "metadata": {
                        **answer.metadata,
                        "text_verification": {
                            **result.to_metadata(),
                            "enforced": enforce,
                            # Citation ids the deterministic verifier vouches
                            # for (span verbatim in that passage): the
                            # publication gate must not withhold them as
                            # unaudited when the v2 sample skipped them.
                            "reattributed_citation_ids": [
                                c.id
                                for c in citations
                                if c.verification_note == REATTRIBUTION_NOTE
                            ],
                        },
                    },
                }
            )
            if not result.all_verified:
                logger.warning(
                    "Text verification: %d verified, %d unverified (enforce=%s)",
                    len(result.verified_spans),
                    len(result.unverified_spans),
                    enforce,
                )
        except Exception:
            logger.warning("Text verification failed", exc_info=True)

        return answer

    # ------------------------------------------------------------------
    # Referee stage — the institutionalized audit (env-gated, bounded)
    # ------------------------------------------------------------------

    async def _referee_answer(
        self, answer: ScholarlyAnswer, state: RAGState
    ) -> tuple[ScholarlyAnswer, dict[str, str] | None]:
        """ONE referee pass over the finished answer, plus at most ONE revision.

        THE SEAM: this runs AFTER the deterministic ancient-text gate
        (:meth:`_verify_ancient_text`), so the referee reads exactly the prose the
        reader will see — enforcement marks and all — and BEFORE the structured
        citation frames, so a revised answer is the one that ships.

        Bounded by construction: one referee call (90 s), at most one revision
        call (240 s). Every failure path — stage off, empty prose, timeout,
        transport error, malformed JSON, a truncated revision — keeps the
        ORIGINAL answer and logs a warning. When a revision IS accepted, the
        text gate runs again on it, because a revision is still model output.

        Returns ``(answer, note)`` where ``note`` is a research-journal entry
        describing what the referee asked for, or ``None`` when there is nothing
        to report.
        """
        from eleutheria_graphrag.agents.dialectical_synthesis import (
            apply_referee_revisions,
            referee_enabled,
            run_referee,
            scholar_render_max_tokens,
        )

        if not referee_enabled():
            return answer, None
        prose = (answer.answer or "").strip()
        if not prose:
            return answer, None

        meta: dict[str, Any] = {"status": "unavailable"}
        note: dict[str, str] | None = None
        try:
            plan = getattr(state, "research_plan", None)
            budget_tier = getattr(plan, "budget_tier", None) or "standard"
            verdict = await run_referee(
                state.question,
                prose,
                self.deps.llm,
                cmap=getattr(state, "controversy_map", None),
            )
            if verdict is None:
                logger.warning(
                    "Referee stage unavailable — keeping the original answer"
                )
            elif verdict.passes:
                meta = {
                    "status": "passed",
                    "model": verdict.model_used,
                    "revisions_requested": 0,
                }
            else:
                meta = {
                    "status": "revision_failed",
                    "model": verdict.model_used,
                    "revisions_requested": len(verdict.revisions),
                    "issues": [r.issue for r in verdict.revisions],
                }
                revised = await apply_referee_revisions(
                    state.question,
                    prose,
                    verdict.revisions,
                    self.deps.llm,
                    max_tokens=scholar_render_max_tokens(budget_tier),
                )
                if revised:
                    candidate = answer.model_copy(update={"answer": revised})
                    # A revision is still model output: re-run the gate on it.
                    if _text_verifier_enabled():
                        candidate = await self._verify_ancient_text(candidate, state)

                    # A referee may improve the prose while accidentally
                    # dropping or rewriting the inline provenance markers.  Do
                    # not let that strictly-worse revision replace an original
                    # answer that still satisfies the dialectical content gate.
                    # This is especially important for fast utility heads,
                    # which are good critics but less reliable at preserving a
                    # long answer's exact marker grammar.
                    cmap = getattr(state, "controversy_map", None)
                    revision_keeps_grounding = (
                        state.metadata.get("render_answer_mode") != "dialectical"
                        or cmap is None
                        or passes_content_gate(candidate.answer, cmap)
                    )
                    if revision_keeps_grounding:
                        answer = candidate
                        meta["status"] = "revised"
                        meta["revised_chars"] = len(candidate.answer)
                        meta["original_chars"] = len(prose)
                    else:
                        logger.warning(
                            "Referee revision failed the final content gate; "
                            "keeping the original grounded answer"
                        )
                        meta["status"] = "revision_rejected_content_gate"
                        meta["revised_chars"] = len(candidate.answer)
                        meta["original_chars"] = len(prose)
                note = {
                    "kind": "gap",
                    "summary": verdict.summary,
                    "detail": " | ".join(
                        r.instruction for r in verdict.revisions if r.instruction
                    ),
                }
        except Exception:  # noqa: BLE001 — the referee must never empty an answer
            logger.warning("Referee stage failed", exc_info=True)
            meta = {"status": "error"}

        state.metadata["referee"] = meta
        answer = answer.model_copy(
            update={"metadata": {**answer.metadata, "referee": meta}}
        )
        return answer, note

    async def query_dict(
        self,
        question: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        answer = await self.query(question, **kwargs)
        return self._public_answer_payload(answer)

    async def query_stream(
        self,
        question: str,
        *,
        max_iterations: int = 5,
        selected_model: str = "gemini-3.1-pro",
        retrieval_mode: str = "auto",
        agent_mode: str | None = None,
        hunt_counter_evidence: bool = False,
        pipeline: str | None = None,
        subagent_model: str | None = None,
    ) -> AsyncIterator[str]:
        mode = resolve_pipeline(pipeline, agent_mode)

        if mode == "react":
            async for event_json in self._stream_react(
                question,
                max_iterations=max_iterations,
                selected_model=selected_model,
                retrieval_mode=retrieval_mode,
                hunt_counter_evidence=hunt_counter_evidence,
            ):
                yield event_json
            return

        if mode == "lead":
            from eleutheria_graphrag.agents.lead_researcher import stream_lead

            async for event_json in stream_lead(
                self,
                question,
                max_iterations=max_iterations,
                selected_model=selected_model,
                retrieval_mode=retrieval_mode,
                hunt_counter_evidence=hunt_counter_evidence,
                subagent_model=subagent_model,
            ):
                yield event_json
            return

        # FSM fallback: the legacy graph runs whole (no live prose), then its
        # answer goes through the SAME verification + publication tail as the
        # agentic stream. The FSM graph ends at the legacy ProgrammaticVerify,
        # which is not a publication verdict: without this tail the FSM stream
        # would emit ungated answer_chunk prose with no answer_final.
        state = RAGState(
            question=question,
            max_iterations=max_iterations,
            selected_model=selected_model,
            retrieval_mode=retrieval_mode,
        )
        if hunt_counter_evidence:
            state.metadata["hunt_counter_evidence"] = True
        yield json.dumps(
            {
                "type": "status",
                "message": "Running research pipeline...",
                "data": {"step": 0},
            }
        )
        answer = await self._run_fsm(state)
        async for ev in self._stream_publication_tail(
            answer, state, journal=ResearchJournal()
        ):
            yield ev

    async def _stream_react(
        self,
        question: str,
        *,
        max_iterations: int = 5,
        selected_model: str = "gemini-3.1-pro",
        retrieval_mode: str = "auto",
        hunt_counter_evidence: bool = False,
    ) -> AsyncIterator[str]:
        """Stream ReAct agent events as JSON strings.

        Emits agent_thinking, tool_start, tool_result events in real time,
        then the final answer as answer_chunk + complete events. Per-stage
        ``stage_complete`` events are emitted at each phase boundary so the
        frontend AgentTrace pane can render a latency stack.
        """
        import asyncio
        import time as _time

        from pydantic_graph import End, GraphRunContext

        from eleutheria_graphrag.agents.react_loop import build_agent_loop
        from eleutheria_graphrag.agents.sse_emitter import SSEEmitter
        from eleutheria_graphrag.agents.tools import build_tool_registry

        state = RAGState(
            question=question,
            max_iterations=max_iterations,
            selected_model=selected_model,
            retrieval_mode=retrieval_mode,
        )
        if hunt_counter_evidence:
            state.metadata["hunt_counter_evidence"] = True

        # Abandoned-lead journal: budgeted across the WHOLE run so the four
        # emission points below cannot flood the timeline between them. The KG
        # lookup is what lets the notes name nodes the way the reader does.
        journal = ResearchJournal()
        kg_labels = getattr(self.deps, "node_lookup", None)
        if not isinstance(kg_labels, Mapping):
            kg_labels = None

        def _notes(notes: list[dict[str, str]], stage: str) -> list[str]:
            """Serialise a batch of notes into ``research_note`` SSE frames."""
            return _serialise_notes(journal, notes, stage)

        # Phase 1: Classify
        stage_started = _time.perf_counter()
        yield json.dumps(
            {"type": "status", "message": "Classifying query...", "data": {"step": 0}}
        )
        classify_node = ClassifyQueryType()
        ctx = GraphRunContext(state=state, deps=self.deps)
        await classify_node.run(ctx)
        classify_ms = int((_time.perf_counter() - stage_started) * 1000)
        yield json.dumps(
            {
                "type": "status",
                "message": f"Query classified: {state.complexity.value}",
                "data": {"step": 1},
            }
        )
        yield json.dumps(
            {
                "type": "stage_complete",
                "stage": "classify",
                "duration_ms": classify_ms,
                "metadata": {"complexity": state.complexity.value},
            }
        )

        # Phase 2: Agent loop with real-time SSE
        stage_started = _time.perf_counter()
        queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()
        emitter = SSEEmitter(queue)
        tools = build_tool_registry(self.deps)

        agent = build_agent_loop(
            deps=self.deps,
            state=state,
            tools=tools,
            emitter=emitter,
        )

        # Run agent in background task, yield events as they arrive
        agent_task = asyncio.create_task(self._run_agent_and_close(agent, emitter))

        tool_calls_observed = 0
        while True:
            event = await queue.get()
            if event is None:
                break  # Agent finished
            if isinstance(event, dict) and event.get("type") in {
                "tool_start",
                "tool_call",
            }:
                tool_calls_observed += 1
            yield json.dumps(event, default=str)

        # Wait for agent task to complete (should already be done)
        await agent_task

        agent_loop_ms = int((_time.perf_counter() - stage_started) * 1000)
        yield json.dumps(
            {
                "type": "stage_complete",
                "stage": "agent_loop",
                "duration_ms": agent_loop_ms,
                "metadata": {"tool_calls": tool_calls_observed},
            }
        )

        # Journal: searches the loop ran that returned nothing.
        for frame in _notes(dead_end_tool_notes(state, kg_labels), "agent_loop"):
            yield frame

        # Phase 2.4: Scholar-RAG (G6) controversy-map assembly. Flag-gated,
        # deterministic, and run BEFORE the quality gate rebuilds the context
        # pack — populating state.controversy_map is what makes the synthesis
        # seam route to the dialectical layer instead of the facet template.
        # Inert (zero extra work, no SSE noise) when the flag is off.
        if scholar_rag_enabled():
            cm_started = _time.perf_counter()
            cm_holder: dict[str, Any] = {}
            try:
                async for hb in self._await_with_heartbeat(
                    self._assemble_controversy_map(state, tools),
                    label="Assembling controversy map",
                    stage_id="controversy_map",
                    interval=8.0,
                    max_wait=120.0,
                    result_into=cm_holder,
                ):
                    yield hb
            except Exception:
                logger.warning(
                    "Controversy-map assembly failed in stream", exc_info=True
                )
            cm_ms = int((_time.perf_counter() - cm_started) * 1000)
            yield json.dumps(
                {
                    "type": "stage_complete",
                    "stage": "controversy_map",
                    "duration_ms": cm_ms,
                    "metadata": state.metadata.get(
                        "controversy_map", {"status": "skipped"}
                    ),
                }
            )

            # Journal: debate seeds opened by the assembler, then dropped.
            for frame in _notes(
                controversy_gap_notes(state, kg_labels), "controversy_map"
            ):
                yield frame

        # Phase 2.5: post-loop quality gate (rerank, sufficiency continuation,
        # deep-mode counter-evidence hunt). The SSE emitter was closed when the
        # agent task finished, so a possible continuation round runs against a
        # NullEmitter; progress is surfaced via the heartbeat wrapper instead.
        stage_started = _time.perf_counter()
        from eleutheria_graphrag.agents.sse_emitter import NullEmitter as _NullEmitter

        agent.emitter = _NullEmitter()
        quality_holder: dict[str, Any] = {}
        counter_items: list[ClaimLedgerItem] = []
        try:
            async for hb in self._await_with_heartbeat(
                self._post_loop_quality_phase(state, agent),
                label="Running quality checks",
                stage_id="quality_gate",
                result_into=quality_holder,
            ):
                yield hb
            counter_items = quality_holder.get("value") or []
        except Exception:
            logger.warning("Post-loop quality phase failed in stream", exc_info=True)
        quality_ms = int((_time.perf_counter() - stage_started) * 1000)
        yield json.dumps(
            {
                "type": "stage_complete",
                "stage": "quality_gate",
                "duration_ms": quality_ms,
                "metadata": {
                    "sufficiency_score": round(state.sufficiency_score, 4),
                    "continuations": state.metadata.get("sufficiency_continuations", 0),
                    "reranker": state.metadata.get("reranker", {"applied": False}),
                    "counter_evidence_items": len(counter_items),
                },
            }
        )

        # Journal: what the evidence critic said was missing, and an
        # adversarial hunt that came back empty.
        for frame in _notes(sufficiency_gap_notes(state), "quality_gate"):
            yield frame
        for frame in _notes(counter_evidence_notes(state), "quality_gate"):
            yield frame

        # Phase 3: Synthesis (two LLM calls — draft claim ledger then render
        # answer). Each one can run for 30-90 s on a doctoral-grade query;
        # without intermediate SSE traffic the Cloudflare tunnel drops the
        # connection at ~100 s of silence and the client never sees a
        # `complete` event. We wrap every long await with a heartbeat that
        # emits a status SSE every 10 s, both to keep the wire warm and to
        # show real progress in the UI.
        stage_started = _time.perf_counter()
        yield json.dumps(
            {
                "type": "status",
                "message": "Synthesizing answer...",
                "data": {"step": 99},
            }
        )

        ctx = GraphRunContext(state=state, deps=self.deps)
        async for hb in self._await_with_heartbeat(
            DraftClaimLedger().run(ctx),
            label="Drafting claim ledger",
            stage_id="draft_claim_ledger",
            max_wait=180.0,
        ):
            yield hb
        self._merge_counter_ledger_items(state, counter_items)

        # Journal: claims the ledger drafted and the grounding gate refused.
        for frame in _notes(rejected_claim_notes(state), "claim_ledger"):
            yield frame

        # Generate under the existing heartbeat/reasoning stream. Raw prose is
        # forwarded LIVE, but only as typed ``answer_provisional`` frames: the
        # draft has not yet met the content gate, the ancient-text verifier or
        # the citation audit, and the wire says so on every frame. An
        # unverified draft never crosses ``answer_chunk``; the gated text is
        # released below by ``answer_final`` once the verdict is in.
        # Dispatch is by PROVENANCE (the ``RenderProse`` tag set at the yield
        # site), never by inspecting the text: model output that begins with
        # valid typed-event JSON is still un-audited prose and is wrapped as
        # provisional. Plain strings must be render-owned control frames
        # (whitelisted type) or they are dropped.
        async for ev in self._stream_render(state):
            if isinstance(ev, RenderProse):
                if ev:
                    yield _provisional_frame(str(ev))
                continue
            control = _render_control_frame(ev)
            if control is not None:
                yield control
        state.metadata["prose_provisional_until_verified"] = True

        synthesis_ms = int((_time.perf_counter() - stage_started) * 1000)
        yield json.dumps(
            {
                "type": "stage_complete",
                "stage": "synthesis",
                "duration_ms": synthesis_ms,
            }
        )

        # F6: structured per-query grounding diagnostics. Set on state.metadata
        # (which _make_answer copies onto answer.metadata) BEFORE the
        # citations_preview / complete frames so both carry it, AND surface it
        # on its OWN trace event so it is visible even if the connection is cut
        # before the terminal complete. Prod drops INFO logs; this does not.
        diagnostics = _build_scholar_diagnostics(state)
        state.metadata["scholar_diagnostics"] = diagnostics
        yield json.dumps({"type": "scholar_diagnostics", "data": diagnostics})

        # TERMINAL-FRAME GUARANTEE: this is the last long await before the
        # citations_preview / complete frames. _await_with_heartbeat re-raises
        # whatever the wrapped task raised, and an unguarded raise here left the
        # client with prose and NO structured citations and no terminal frame.
        # Every stage below is best-effort; _make_answer(state) always yields
        # something renderable from the state we already have.
        stage_started = _time.perf_counter()
        verify_node = ProgrammaticVerify()
        ctx = GraphRunContext(state=state, deps=self.deps)
        verify_result_holder: dict[str, Any] = {}
        verify_error: Exception | None = None
        try:
            async for hb in self._await_with_heartbeat(
                verify_node.run(ctx),
                label="Verifying citations",
                stage_id="verify",
                interval=8.0,
                max_wait=120.0,
                result_into=verify_result_holder,
            ):
                yield hb
        except Exception as exc:  # noqa: BLE001 — never strand the client
            verify_error = exc
            logger.warning("Citation verification stage failed", exc_info=True)
        result = verify_result_holder.get("value")
        verify_ms = int((_time.perf_counter() - stage_started) * 1000)
        yield json.dumps(
            {
                "type": "stage_complete",
                "stage": "verify",
                "duration_ms": verify_ms,
                "failed": verify_error is not None,
            }
        )

        from eleutheria_graphrag.agents.graph_nodes import _make_answer

        answer = result.data if isinstance(result, End) else _make_answer(state)

        # Everything from here on is the SHARED verification + publication
        # tail (also run by the FSM stream): answer_final, then the gated
        # answer_chunk / complete frames.
        async for ev in self._stream_publication_tail(answer, state, journal=journal):
            yield ev

    async def _stream_publication_tail(
        self,
        answer: ScholarlyAnswer,
        state: RAGState,
        *,
        journal: ResearchJournal,
    ) -> AsyncIterator[str]:
        """The shared verification + publication tail of every streaming path.

        Takes the answer as ``ProgrammaticVerify`` left it, runs the shared
        verification (:meth:`_verify_for_publication`) and the single
        fail-closed publication verdict, emits the ``answer_final`` frame and
        only then the plain ``answer_chunk`` / ``complete`` frames — prose
        that has not been through this tail never crosses as an answer.  Both
        the agentic (``_stream_react``) and the FSM (``query_stream``
        fallback) streams end here, and the sync FSM facade
        (``query`` → ``_publish_fsm_draft``) runs the same verification, so
        the three cannot drift.
        """
        holder: dict[str, Any] = {}
        async for frame in self._verify_for_publication(
            answer, state, journal=journal, result_into=holder
        ):
            yield frame
        answer = cast(ScholarlyAnswer, holder["answer"])
        gate = answer.metadata.get("publication_gate") or {}
        publishable = bool(gate.get("publishable"))
        for frame in self._publication_gate_frames(answer):
            yield frame

        # The verdict frame: the client replaces its provisional preview with
        # the gated text (or the withholding notice) atomically, before the
        # plain answer_chunk / complete frames that keep older consumers whole.
        yield _answer_final_frame(answer)

        # Release prose only after the shared publication verdict passes. A
        # blocked run still gets a terminal frame, with an empty answer/citation
        # payload and machine-readable reasons; a partial run streams the
        # withheld prose.
        async for chunk in self._chunk_answer(
            answer,
            stream_prose=publishable,
        ):
            yield chunk

    async def _verify_for_publication(
        self,
        answer: ScholarlyAnswer,
        state: RAGState,
        *,
        journal: ResearchJournal,
        result_into: dict[str, Any],
    ) -> AsyncIterator[str]:
        """The ONE post-draft verification tail, for the stream and the facade.

        Runs, in order: passage injection, the ancient-text verifier, the
        referee, the FINAL content gate, the citation-verifier-v2 audit, then
        the single fail-closed publication verdict (applied).  Yields the
        status / heartbeat / audit frames the stream puts on the wire; the
        gated answer lands in ``result_into["answer"]``.  The sync facade
        drains the frames and keeps the answer, so a draft gets the same
        verdict whether it is queried or streamed.
        """
        # Phase 3.5: Programmatic passage injection
        with contextlib.suppress(Exception):
            answer = self._inject_passage_quotations(answer, state)

        # Phase 4: deterministic ancient-text verification (whitelist-first,
        # report-only unless ELEUTHERIA_TEXT_VERIFIER_ENFORCE is set).
        if _text_verifier_enabled():
            try:
                answer = await self._verify_ancient_text(answer, state)
            except Exception:  # noqa: BLE001 — report-only stage
                logger.warning("Ancient-text verification failed", exc_info=True)

        # Phase 4.6: referee pass (env-gated, bounded). Placed AFTER the text
        # gate — the referee must read exactly what the reader will see — and
        # BEFORE `citations_preview`, so a revised answer is the one that ships
        # on both terminal frames. The prose streamed only as provisional
        # frames; the FE replaces that preview with the answer_final payload.
        from eleutheria_graphrag.agents.dialectical_synthesis import (
            referee_enabled,
            referee_timeout,
            revision_timeout,
        )

        if referee_enabled():
            referee_holder: dict[str, Any] = {}
            try:
                async for hb in self._await_with_heartbeat(
                    self._referee_answer(answer, state),
                    label="Referee review",
                    stage_id="referee",
                    interval=8.0,
                    max_wait=referee_timeout() + revision_timeout() + 30.0,
                    result_into=referee_holder,
                ):
                    yield hb
            except Exception:  # noqa: BLE001 — the referee must never eat `complete`
                logger.warning("Referee stage failed", exc_info=True)
            refereed = referee_holder.get("value")
            if refereed is not None:
                answer, referee_note = refereed
                if referee_note:
                    for frame in _serialise_notes(journal, [referee_note], "referee"):
                        yield frame

        # Phase 4.7: run the content gate on the FINAL prose, after any referee
        # revision, and rebuild dialectical provenance from that exact prose.
        # The former pre-audit citations_preview exposed an unaudited answer and
        # is deliberately gone; status heartbeats keep the wire alive instead.
        answer = _apply_final_content_gate(answer, state)

        # A degraded synthesis must SAY SO on the wire: the prose is a
        # structural rendering of the evidence, not a weighed scholarly answer.
        synthesis_meta = state.metadata.get("scholar_synthesis")
        if isinstance(synthesis_meta, dict) and (
            synthesis_meta.get("degraded") or synthesis_meta.get("status") != "ok"
        ):
            yield json.dumps(
                {
                    "type": "status",
                    "message": (
                        "The synthesis model was unavailable on this run; the "
                        "answer is a structural rendering of the assembled "
                        "evidence."
                    ),
                    "data": {
                        "step": 99,
                        "stage": "degraded",
                        "reason": synthesis_meta.get("reason"),
                        "synthesis_status": synthesis_meta.get("status"),
                    },
                }
            )

        # Phase 5: adversarial audit. A content-gate failure or a missing /
        # crashed verifier blocks the answer; a non-VERIFIED verdict withholds
        # the sentences citing it.
        content_passed = answer.metadata.get("content_gate", {}).get("passed") is True
        if not content_passed:
            answer = _mark_verifier_v2_unavailable(
                answer,
                status="skipped_content_gate",
                reason="citation audit skipped because final content gate failed",
            )
        elif self.deps.verifier_v2 is not None:
            audit_holder: dict[str, Any] = {}
            try:
                async for ev in self._stream_citation_audit(answer, audit_holder):
                    yield ev
            except Exception as exc:  # noqa: BLE001 — convert to blocking metadata
                logger.warning("Citation audit stage failed", exc_info=True)
                audit_holder["answer"] = _mark_verifier_v2_error(answer, exc)
            answer = audit_holder.get("answer", answer)
        else:
            answer = _mark_verifier_v2_unavailable(
                answer,
                status="unavailable",
                reason="CitationVerifierV2 is not configured",
            )

        # A public boundary (the SSE terminal frame, the sync facade): apply
        # the shared verdict (block, or withhold sentence by sentence) exactly
        # as the answer caches do.
        result_into["answer"] = annotate_publication_decision(
            answer, withhold_prose=True
        )

    async def _await_with_heartbeat(
        self,
        coro: Any,
        *,
        label: str,
        stage_id: str,
        interval: float = 10.0,
        max_wait: float = 180.0,
        result_into: dict[str, Any] | None = None,
    ) -> AsyncIterator[str]:
        """Run ``coro`` while yielding ``status`` SSE strings every ``interval`` s.

        Cloudflare tunnel idles out an SSE connection after ~100 s of
        silence, which used to drop doctoral-grade queries mid-synthesis.
        Wrapping the long awaits here keeps a steady drip of frames on the
        wire and surfaces real progress (elapsed seconds) to the UI.

        ``max_wait`` is a hard ceiling on the wrapped task: once it elapses the
        task is cancelled and the generator returns WITHOUT setting
        ``result_into['value']`` (the caller then falls back). This is the
        critical safety net — a synthesis-phase LLM call that hangs (no token,
        no error) would otherwise keep this loop emitting ``status`` heartbeats
        forever, so the stream never reached ``citations_preview`` / ``complete``
        and the UI showed prose with zero structured citations. Bounding the
        wait lets the pipeline finish and emit those terminal frames.

        The coroutine's return value, if any, is stashed in
        ``result_into['value']`` for the caller (avoids re-running the
        coroutine just to get its result).
        """
        task = asyncio.create_task(coro)
        started = _time_mod.monotonic()
        # First-frame ping: clients see we entered this stage immediately.
        yield json.dumps(
            {
                "type": "status",
                "message": f"{label}…",
                "data": {"step": 99, "stage": stage_id, "elapsed_s": 0},
            }
        )
        timed_out = False
        try:
            while not task.done():
                try:
                    await asyncio.wait_for(asyncio.shield(task), timeout=interval)
                except TimeoutError:
                    elapsed = _time_mod.monotonic() - started
                    if elapsed >= max_wait:
                        timed_out = True
                        break
                    yield json.dumps(
                        {
                            "type": "status",
                            "message": f"{label}… ({int(elapsed)}s)",
                            "data": {
                                "step": 99,
                                "stage": stage_id,
                                "elapsed_s": int(elapsed),
                            },
                        }
                    )
        except Exception:
            # Cancel only if still running; let exception surface below.
            if not task.done():
                task.cancel()
            raise
        if timed_out:
            # Abandon the stuck task and let the caller fall back. Cancelling
            # frees the request rather than leaking a runaway coroutine.
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await task
            logger.warning(
                "Heartbeat-wrapped task %s exceeded max_wait=%.0fs; abandoning "
                "and falling back",
                stage_id,
                max_wait,
            )
            return
        try:
            value = task.result()
        except Exception:
            logger.exception("Heartbeat-wrapped task %s failed", stage_id)
            raise
        if result_into is not None:
            result_into["value"] = value

    async def _stream_map_hedge(
        self, state: RAGState, holder: dict[str, Any]
    ) -> AsyncIterator[str]:
        """FINAL GUARANTEE for the streaming seam: emit a deterministic, non-empty
        map-derived hedge as answer_chunks when the streaming synthesis failed /
        timed out / emptied.

        A POPULATED controversy map must ALWAYS yield a real answer — never fall
        through to the legacy Gemini render that 429s and shows the bare
        "insufficient evidence" sentence. Serialises the contending positions +
        their grounded passages into prose (no LLM call), lands it in
        ``state.raw_answer`` + a prose-derived ledger, and chunks it losslessly.
        Sets ``holder['ok']`` True iff a real hedge was produced; an empty map
        leaves it falsy so the legacy render runs (nothing to render anyway)."""
        cmap = getattr(state, "controversy_map", None)
        if cmap is None:
            holder["ok"] = False
            return
        prose = ""
        try:
            prose = (deterministic_map_hedge(cmap) or "").strip()
        except Exception:  # noqa: BLE001 - the floor must never raise
            logger.warning("Deterministic map hedge raised", exc_info=True)
            prose = ""
        if not prose:
            holder["ok"] = False
            return

        state.raw_answer = prose
        ledger = build_provenance_ledger(prose, cmap)
        if ledger:
            state.claim_ledger = ledger
        state.metadata["render_streamed"] = True
        state.metadata["render_answer_mode"] = "dialectical"
        state.metadata["scholar_synthesis"] = {
            "status": "deterministic_map",
            "ledger_size": len(ledger),
            "degraded": True,
        }
        for chunk in _lossless_prose_chunks(prose):
            yield RenderProse(chunk)
        _append_reasoning_step(
            state,
            "DialecticalSynthesis",
            "deterministic_map_hedge",
            "",
            0,
            prose,
            parsed_result={"streamed": True, "render_mode": "dialectical_hedge"},
        )
        holder["ok"] = True

    async def _stream_dialectical(
        self,
        state: RAGState,
        *,
        holder: dict[str, Any],
        interval: float = 10.0,
        max_wait: float | None = None,
    ) -> AsyncIterator[str]:
        """Stream the dialectical answer for the Scholar-RAG render seam (M4).

        The synthesis runs on a TRUE thinking model whose ``reasoning_content``
        now streams LIVE: we drive it via ``synthesize_dialectical_stream`` (the
        segmented LLM stream) on a background task, push each reasoning delta onto
        a queue as a ``synthesis_reasoning`` SSE event, and drain that queue here
        WHILE the slow (~5–10 min) synthesis runs — so the right-panel AGENT
        REASONING workspace fills live instead of freezing on "Rendering…". The
        reasoning text travels on its OWN channel and NEVER enters the answer.
        When the synthesis finishes, its clean ``content`` prose is chunked into
        raw ``answer_chunk`` strings (the route wraps each as an ``answer_chunk``
        event, identical to ``_stream_render``). The prose lands in
        ``state.raw_answer`` and the prose-derived provenance ledger in
        ``state.claim_ledger`` (set inside ``_synthesize_dialectical``).

        Sets ``holder['ok'] = True`` iff dialectical prose was produced and
        streamed; otherwise leaves it falsy so the caller falls through to the
        legacy streamed render. Never raises into the pipeline.

        ``max_wait`` defaults to ``_dialectical_heartbeat_ceiling()`` (the
        synthesis HTTP timeout + margin) so the ceiling NEVER cancels a
        healthy-but-slow thinking-model synthesis before its own LLM timeout —
        which would drop us into the legacy facet-template fallback.
        """
        if max_wait is None:
            max_wait = _dialectical_heartbeat_ceiling()

        # Reasoning deltas arrive on a queue from the synthesis task's callback;
        # the drain loop below interleaves them with idle ``status`` heartbeats
        # (so the SSE wire stays warm even while the model is still thinking).
        reasoning_queue: asyncio.Queue[str] = asyncio.Queue()

        async def _on_reasoning(delta: str) -> None:
            await reasoning_queue.put(delta)

        result_holder: dict[str, Any] = {}

        async def _run() -> None:
            result_holder["value"] = await self._synthesize_dialectical(
                state, on_reasoning=_on_reasoning
            )

        synth_task = asyncio.create_task(_run())
        started = _time_mod.monotonic()
        # First-frame ping so the UI enters the synthesis stage immediately.
        yield json.dumps(
            {
                "type": "status",
                "message": "Synthesizing dialectical answer…",
                "data": {
                    "step": 99,
                    "stage": "dialectical_synthesis",
                    "elapsed_s": 0,
                },
            }
        )
        timed_out = False
        try:
            while not synth_task.done():
                try:
                    delta = await asyncio.wait_for(
                        reasoning_queue.get(), timeout=interval
                    )
                    # LIVE reasoning on its OWN channel — NEVER an answer_chunk.
                    yield json.dumps(
                        {
                            "type": "synthesis_reasoning",
                            "data": {
                                "reasoning": delta,
                                "stage": "Reasoning over the controversy map",
                            },
                        }
                    )
                except TimeoutError:
                    elapsed = _time_mod.monotonic() - started
                    if elapsed >= max_wait:
                        timed_out = True
                        break
                    yield json.dumps(
                        {
                            "type": "status",
                            "message": (
                                f"Synthesizing dialectical answer… ({int(elapsed)}s)"
                            ),
                            "data": {
                                "step": 99,
                                "stage": "dialectical_synthesis",
                                "elapsed_s": int(elapsed),
                            },
                        }
                    )
        except Exception:
            logger.warning(
                "Dialectical synthesis stream failed; deterministic map hedge",
                exc_info=True,
            )
            if not synth_task.done():
                synth_task.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await synth_task
            async for ev in self._stream_map_hedge(state, holder):
                yield ev
            return

        # Drain any reasoning deltas that landed after the task finished but
        # before the loop noticed (so no live thought is silently dropped).
        while not reasoning_queue.empty():
            delta = reasoning_queue.get_nowait()
            yield json.dumps(
                {
                    "type": "synthesis_reasoning",
                    "data": {
                        "reasoning": delta,
                        "stage": "Reasoning over the controversy map",
                    },
                }
            )

        if timed_out:
            synth_task.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await synth_task
            logger.warning(
                "Dialectical synthesis exceeded max_wait=%.0fs; deterministic "
                "map hedge",
                max_wait,
            )
            async for ev in self._stream_map_hedge(state, holder):
                yield ev
            return

        try:
            synth_task.result()  # surface any task exception
        except Exception:
            logger.warning(
                "Dialectical synthesis task raised; deterministic map hedge",
                exc_info=True,
            )
            async for ev in self._stream_map_hedge(state, holder):
                yield ev
            return

        prose = result_holder.get("value")
        if not prose:
            async for ev in self._stream_map_hedge(state, holder):
                yield ev
            return

        state.metadata["render_streamed"] = True
        # Chunk the finished prose LOSSLESSLY: paragraph-first, then sentence
        # boundaries, preserving every separator so the concatenation of the
        # emitted answer_chunks is byte-for-byte the full prose (the old
        # split-and-rejoin chunker dropped inter-paragraph/inter-sentence
        # whitespace, which truncated/mangled the streamed answer). Each chunk is
        # tagged ``RenderProse`` (un-audited prose, by provenance).
        for chunk in _lossless_prose_chunks(prose):
            yield RenderProse(chunk)

        _append_reasoning_step(
            state,
            "DialecticalSynthesis",
            self.deps.llm.last_model_used or state.selected_model,
            "",
            0,
            prose,
            parsed_result={"streamed": True, "render_mode": "dialectical"},
        )
        holder["ok"] = True

    async def _stream_render(
        self, state: RAGState, *, interval: float = 10.0, max_wait: float = 240.0
    ) -> AsyncIterator[str]:
        """Stream the grounded-answer render token-by-token.

        Replaces the blocking ``RenderGroundedAnswer`` LLM call in the
        streaming pipeline. Emitting prose as it is generated (a) keeps the SSE
        wire warm with real content so a proxy/tunnel request-duration cap
        cannot sever the connection mid-render and leave the user with nothing,
        (b) lets the answer render live, and (c) means a partial answer
        survives any drop (the FE keeps any >200-char stream). Idle heartbeats
        cover the pre-first-token "thinking" gap of reasoning models. After the
        stream we classify the draft and fall back if it is empty/inadequate,
        mirroring ``RenderGroundedAnswer``'s tail. The expand-retry and polish
        passes are intentionally skipped here to cut synthesis latency.

        Yields prose tagged ``RenderProse`` (un-audited, by provenance — the
        agentic path wraps it as ``answer_provisional`` until the verdict)
        interleaved with plain-string JSON ``status`` heartbeats.
        """
        # First-frame ping so the UI enters the render stage immediately.
        yield json.dumps(
            {
                "type": "status",
                "message": "Rendering grounded answer…",
                "data": {"step": 99, "stage": "render_grounded_answer", "elapsed_s": 0},
            }
        )

        # M4 cutover: when Scholar-RAG is on and a ControversyMap assembled, the
        # streamed prose comes from dialectical synthesis over the map — NOT the
        # facet template. synthesize_dialectical is whole (one LLM call), so we
        # run it under a heartbeat then chunk its result into answer_chunk events.
        # On failure / empty prose we fall through to the legacy streamed render.
        if self._scholar_render_active(state):
            dx_holder: dict[str, Any] = {}
            async for ev in self._stream_dialectical(
                state, holder=dx_holder, interval=interval
            ):
                yield ev
            if dx_holder.get("ok"):
                return
            # else: synthesis failed/empty → fall through to the legacy render.

        payload = build_render_prompt(state)

        if payload["mode"] == "deterministic_quote":
            state.raw_answer = payload["answer"]
            state.metadata["render_answer_mode"] = "deterministic_quote"
            state.metadata["render_streamed"] = True
            if state.raw_answer:
                yield RenderProse(state.raw_answer)
            _trace_stage(
                state,
                "render_grounded_answer",
                {
                    "mode": "deterministic_quote",
                    "streamed": True,
                    "raw_excerpt": truncate_text(state.raw_answer, 2000),
                },
            )
            return

        prompt = payload["prompt"]
        model_api_id = payload["model_api_id"]
        render_max_tokens = _stream_render_max_tokens()

        # Bridge the llm.stream() async-gen onto a queue so we can interleave
        # idle heartbeats while the model is still "thinking" (no token yet).
        queue: asyncio.Queue[tuple[str, Any]] = asyncio.Queue()

        async def _pump() -> None:
            try:
                async for piece in self.deps.llm.stream(
                    prompt,
                    system_prompt=SYSTEM_PROMPT,
                    temperature=0.2,
                    max_tokens=render_max_tokens,
                    model_override=model_api_id,
                ):
                    await queue.put(("chunk", piece))
                await queue.put(("done", None))
            except Exception as exc:  # noqa: BLE001
                await queue.put(("error", exc))

        pump_task = asyncio.create_task(_pump())
        started = _time_mod.monotonic()
        chunks: list[str] = []
        stream_error: Exception | None = None
        try:
            while True:
                try:
                    kind, value = await asyncio.wait_for(queue.get(), timeout=interval)
                except TimeoutError:
                    elapsed = int(_time_mod.monotonic() - started)
                    # Hard ceiling: a stalled LLM stream (no token, no done/error)
                    # would otherwise spin this loop forever emitting heartbeats,
                    # so the pipeline never reached citations_preview/complete.
                    # Bail with whatever prose we have; the tail below falls back
                    # to a deterministic render when chunks are empty/inadequate.
                    if elapsed >= max_wait:
                        logger.warning(
                            "Streaming render exceeded max_wait=%.0fs after %d "
                            "chars; abandoning stream and falling back",
                            max_wait,
                            len("".join(chunks)),
                        )
                        break
                    yield json.dumps(
                        {
                            "type": "status",
                            "message": f"Rendering grounded answer… ({elapsed}s)",
                            "data": {
                                "step": 99,
                                "stage": "render_grounded_answer",
                                "elapsed_s": elapsed,
                            },
                        }
                    )
                    continue
                if kind == "chunk":
                    if value:
                        chunks.append(value)
                        # Model prose, tagged by provenance: the agentic path
                        # wraps it as answer_provisional until the verdict.
                        yield RenderProse(value)
                elif kind == "done":
                    break
                else:  # "error"
                    stream_error = value
                    break
        finally:
            if not pump_task.done():
                pump_task.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await pump_task

        if stream_error is not None:
            logger.warning(
                "Streaming render failed after %d chars: %s",
                len("".join(chunks)),
                stream_error,
            )

        rendered = "".join(chunks).strip()
        band, _shape = _classify_render_quality(state, rendered)
        fallback_answer = _render_answer_fallback(state)
        if not rendered or band == "inadequate":
            rendered = fallback_answer
            band = "inadequate"
        state.raw_answer = rendered

        if rendered == fallback_answer:
            state.metadata["render_answer_mode"] = "fallback"
            state.metadata["pipeline_degraded"] = True
        elif band == "strict":
            state.metadata["render_answer_mode"] = "llm"
        else:
            state.metadata["render_answer_mode"] = "llm_short"
        state.metadata["render_streamed"] = True

        _append_reasoning_step(
            state,
            "RenderGroundedAnswer",
            self.deps.llm.last_model_used or state.selected_model,
            prompt[:200],
            len(prompt) // 4,
            rendered,
            skipped=bool(stream_error is not None and not chunks),
            skip_reason=(
                f"stream error: {type(stream_error).__name__}"
                if stream_error is not None
                else None
            ),
            parsed_result={"streamed": True, "render_band": band},
        )
        _trace_stage(
            state,
            "render_grounded_answer",
            {
                "mode": state.metadata["render_answer_mode"],
                "streamed": True,
                "render_band": band,
                "raw_excerpt": truncate_text(state.raw_answer, 2000),
                "stream_error": (
                    f"{type(stream_error).__name__}: {stream_error}"
                    if stream_error is not None
                    else None
                ),
            },
        )

    @staticmethod
    async def _run_agent_and_close(agent: Any, emitter: Any) -> None:
        """Run the agent loop and close the emitter when done."""
        try:
            await agent.run()
        except Exception:
            # Never put the raw exception on the wire: it can carry credentials
            # (httpx embeds the request URL) and provider internals.
            logger.error("Agent loop error", exc_info=True)
            await emitter.emit_error(CLIENT_LLM_ERROR_MESSAGE)
            # A provider outage is an execution failure, not a source finding.
            # Stop before map assembly/synthesis can produce a misleading fallback.
            raise RuntimeError(CLIENT_LLM_ERROR_MESSAGE) from None
        finally:
            await emitter.close()

    @staticmethod
    def _publication_gate_frames(answer: ScholarlyAnswer) -> list[str]:
        """``verification_warning`` frame for a blocked or partial verdict.

        Shared by the ReAct terminal frame and the FSM streaming fallback so
        both boundaries announce the same machine-readable verdict.
        """
        gate = answer.metadata.get("publication_gate") or {}
        if not gate or gate.get("status") == "passed":
            return []
        return [
            json.dumps(
                {
                    "type": "verification_warning",
                    "data": {
                        "stage": "publication_gate",
                        "status": "partial" if gate.get("publishable") else "blocked",
                        "reasons": list(gate.get("reasons") or []),
                        "withholding": gate.get("withholding") or {},
                    },
                }
            )
        ]

    async def _chunk_answer(
        self, answer: ScholarlyAnswer, *, stream_prose: bool = True
    ) -> AsyncIterator[str]:
        """Chunk a ScholarlyAnswer into typed answer_chunk + complete SSE events.

        Only ever called with GATED prose (after the publication verdict).
        When ``stream_prose`` is False the prose chunks are skipped and only
        the ``complete`` event is emitted — a withheld run.
        """
        if stream_prose:
            # Lossless chunking: the concatenation of the emitted chunk payloads
            # equals ``answer.answer`` byte-for-byte (no dropped separators).
            # Typed frames, never raw strings — see ``_answer_chunk_frame``.
            for chunk in _lossless_prose_chunks(answer.answer):
                yield _answer_chunk_frame(chunk)

        yield self._build_complete_event(answer, event_type="complete")

    def _build_complete_event(
        self, answer: ScholarlyAnswer, *, event_type: str = "complete"
    ) -> str:
        """Serialize a ScholarlyAnswer into a `complete`-shaped SSE frame.

        Shared by `_chunk_answer` (terminal `complete` event) and the early
        `citations_preview` frame emitted before the verifier-v2 audit so both
        carry an identical structured-citation payload (no schema drift). The
        route transforms either frame into the frontend GraphRAGResponse shape.
        """
        return json.dumps(
            {"type": event_type, "data": self._public_answer_payload(answer)},
            default=str,
        )

    def _public_answer_payload(self, answer: ScholarlyAnswer) -> dict[str, Any]:
        """One public projection for synchronous, preview and terminal responses."""
        complete_data = public_payload(
            {
                "answer": answer.answer,
                "question": answer.question,
                "citations": [c.model_dump() for c in answer.citations],
                "seed_nodes": answer.seed_nodes,
                "context_nodes": answer.context_nodes,
                "passages_used": answer.passages_used,
                # Typed claim-ledger entries — the SSE route forwards these to
                # the frontend, the answer cache and the share page (mirror of
                # query_dict; without this the streaming path always ships []).
                "claim_ledger": [c.model_dump() for c in answer.claim_ledger],
                "llm_model": self.deps.llm.last_model_used,
                "llm_provider": self.deps.llm.last_provider_used,
                "metadata": {
                    **answer.metadata,
                    "complexity": answer.complexity.value,
                    "iterations": answer.iterations,
                    "sub_queries": answer.sub_queries,
                    "query_type": getattr(
                        answer.query_type, "value", answer.query_type
                    ),
                    "quality_badge": answer.quality_badge,
                    "grounding_policy": answer.grounding_policy.value,
                    "claim_ledger_size": len(answer.claim_ledger),
                },
            }
        )
        complete_data["metadata"]["claim_ledger_size"] = len(
            complete_data["claim_ledger"]
        )
        return complete_data
