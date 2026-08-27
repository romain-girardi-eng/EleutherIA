"""Single publication verdict for GraphRAG answers: block or withhold.

The citation auditor, the streaming boundary, and both answer caches must make
the same decision.  Keeping that decision here prevents a rejected draft from
being withheld by one path but replayed by another.

Two classes of failure are handled differently:

* **Safety-class failures block the whole answer** — the content gate did not
  pass, the citation audit never ran or crashed (verifier exception, provider
  outage, zero auditable citations), unattested ancient text reached the prose
  unenforced, or the per-citation verdict record needed for withholding is
  missing.  Nothing is published.
* **Per-citation verdicts withhold sentences.**  A ``WEAK`` / ``REJECTED`` /
  ``MISSING`` / verifier-error verdict removes the sentences carrying that
  citation from the published prose (replaced by a bracketed marker), drops the
  citation from the public list and downgrades its ledger items to
  ``INSUFFICIENT`` with the reason.  Everything ``VERIFIED`` is published.

This module deliberately distinguishes *internal draft* from *publishable
answer*.  Callers may keep an internal draft for diagnostics
(``withhold_prose=False``), but withholding is applied before the draft
crosses the public ``GraphRAGService``/SSE boundary.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from eleutheria_graphrag.agents.state import (
    Citation,
    ClaimLedgerItem,
    ClaimStatus,
    ScholarlyAnswer,
)

POLICY = "content_gate_and_sentence_withholding_v2"

#: Placeholder left where a sentence was withheld — same convention as the
#: ``*[removed: unverified ancient text]*`` marker of the text verifier.
WITHHELD_SENTENCE_MARKER = "*[withheld: citation not verified]*"

BADGE_HIGH = "High"
BADGE_PARTIAL = "Partial"
BADGE_BLOCKED = "Blocked"

#: Reason keys used for withheld citations (``withholding.reasons`` counts).
REASON_WEAK = "weak"
REASON_REJECTED = "rejected"
REASON_MISSING = "missing"
REASON_VERIFIER_ERROR = "verifier_error"
REASON_UNAUDITED = "unaudited"

_STATUS_REASONS = {
    "WEAK": REASON_WEAK,
    "REJECTED": REASON_REJECTED,
    "MISSING": REASON_MISSING,
}

_BRACKET_RE = re.compile(r"\[([^\]]*)\]")
_PURE_REF_LIST_RE = re.compile(r"^\s*P?\d+(?:\s*[,;]\s*P?\d+)*\s*$")
_REF_TOKEN_RE = re.compile(r"P?\d+")
_MARKER_BODY_RE = re.compile(r"^(?:P|edge|passage)_?(?P<body>.+)$", re.DOTALL)
# Sentence boundary inside one line: terminal punctuation, whitespace, then an
# opening character.  The separator is captured so it survives re-assembly.
_SENTENCE_SEP_RE = re.compile(
    r"((?:(?<=[.!?;·])|(?<=[.!?;·][)»”\"']))\s+)(?=[A-ZΑ-Ω«“\"'(\[*_])"
)
_LINE_PREFIX_RE = re.compile(r"^(\s*(?:[-*+]|\d+[.)])\s+|\s*#+\s+)")
_WS_RE = re.compile(r"\s+")


@dataclass(frozen=True, slots=True)
class PublicationDecision:
    """Deterministic answer-publication decision.

    ``reasons`` are the safety-class (blocking) reasons.  ``withheld`` maps
    citation ids to the withholding reason derived from the recorded per-
    citation verdicts.  ``verdict_record`` is True when the audit recorded the
    ids it verified, so citations without a verdict can be told apart from
    verified ones at apply time.
    """

    publishable: bool
    reasons: tuple[str, ...]
    withheld: dict[str, str] = field(default_factory=dict)
    verdict_record: bool = False
    audit_warning: str | None = None

    @property
    def status(self) -> str:
        if not self.publishable:
            return "blocked"
        return "partial" if self.withheld else "passed"

    def as_metadata(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "publishable": self.publishable,
            "reasons": list(self.reasons),
            "policy": POLICY,
        }


@dataclass(frozen=True, slots=True)
class WithholdingOutcome:
    """Result of removing withheld sentences from a prose text."""

    text: str
    withheld_sentences: int
    published_sentences: int


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _integer(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except TypeError, ValueError:
        return default


def _str_list(value: Any) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, str | bytes):
        return []
    return [str(item) for item in value if item is not None]


def _reason_for_verdict(entry: Mapping[str, Any]) -> str:
    if bool(entry.get("parse_error")):
        return REASON_VERIFIER_ERROR
    status = str(entry.get("status") or "").upper()
    return _STATUS_REASONS.get(status, REASON_REJECTED)


def evaluate_publication(
    metadata: Mapping[str, Any] | None,
) -> PublicationDecision:
    """Evaluate the final content gate and the citation audit.

    Blocking (safety-class) invariants:

    * the synthesis is authoritative (not a degraded structural rendering);
    * the post-revision content gate ran and passed (or was explicitly marked
      not applicable for the legacy non-dialectical renderer);
    * the citation verifier ran to completion — a verifier exception, an
      unavailable verifier, or an audit aborted before any verdict blocks;
    * there was at least one auditable citation;
    * a partial audit is only tolerated when the audit recorded which
      citations it verified, so the rest can be withheld sentence by sentence;
    * per-citation failures are only tolerated when the audit recorded them
      by id (``failed_citations``); bare counts cannot be applied honestly;
    * unverified ancient text never reaches the prose unenforced.

    Every ``WEAK`` / ``REJECTED`` / ``MISSING`` / verifier-error verdict is
    returned in ``withheld`` for sentence-level withholding instead of
    blocking the answer.
    """

    data = _mapping(metadata)
    reasons: list[str] = []

    synthesis = _mapping(data.get("scholar_synthesis"))
    if synthesis and (
        synthesis.get("degraded") or str(synthesis.get("status") or "") != "ok"
    ):
        reasons.append("scholar_synthesis_not_authoritative")

    content = _mapping(data.get("content_gate"))
    content_status = str(content.get("status") or "")
    if content_status not in {"passed", "not_applicable"}:
        reasons.append("content_gate_not_passed")

    audit = _mapping(data.get("citation_verifier_v2"))
    audit_status = str(audit.get("status") or "")
    if audit_status not in {"passed", "failed"}:
        # The audit never completed: not configured, disabled, skipped, or
        # crashed.  There are no verdicts to withhold by.
        reasons.append("citation_audit_not_passed")
    if audit_status == "error" or bool(audit.get("infrastructure_failure")):
        reasons.append("citation_audit_infrastructure_failure")

    total_citations = _integer(audit.get("total_citations"), -1)
    audited = _integer(
        audit.get("audited_citations", audit.get("sampled", audit.get("total"))),
        -1,
    )
    report_total = _integer(audit.get("total"), -1)
    verified = _integer(audit.get("verified"), 0)
    weak = _integer(audit.get("weak"), 0)
    rejected = _integer(audit.get("rejected"), 0)
    missing = _integer(audit.get("missing"), 0)
    parse_errors = _integer(audit.get("parse_errors"), 0)
    aborted = bool(audit.get("aborted"))

    verdict_record = "verified_citations" in audit
    failed_entries = [
        entry
        for entry in (audit.get("failed_citations") or [])
        if isinstance(entry, Mapping) and entry.get("citation_id")
    ]

    audit_completed = audit_status in {"passed", "failed"}
    if total_citations <= 0:
        reasons.append("no_auditable_citations")
    elif (
        audit_completed
        and (audited != total_citations or report_total != total_citations)
        and not verdict_record
    ):
        # Without the verified-id record an unaudited citation cannot be told
        # apart from a verified one, so the partial audit cannot be applied.
        reasons.append("citation_audit_partial")

    if aborted and audited <= 0:
        # Aborted before a single verdict: nothing to withhold by.  An abort on
        # the rejection-rate threshold (audited > 0) is applied per sentence.
        reasons.append("citation_audit_aborted")

    failing_count = weak + rejected + missing + parse_errors
    non_verified = max(audited, 0) - verified if audited > 0 else 0
    if (failing_count > 0 or non_verified > 0) and not failed_entries:
        reasons.append("citation_verdicts_unrecorded")

    text_verification = _mapping(data.get("text_verification"))
    if (
        text_verification
        and _integer(text_verification.get("unverified"), 0) > 0
        and not bool(text_verification.get("enforced"))
    ):
        reasons.append("unverified_ancient_text_present")

    withheld: dict[str, str] = {}
    for entry in failed_entries:
        cid = str(entry["citation_id"])
        # A citation audited more than once keeps its harshest reason.
        reason = _reason_for_verdict(entry)
        current = withheld.get(cid)
        if current is None or _severity(reason) > _severity(current):
            withheld[cid] = reason

    warning = audit.get("warning")
    audit_warning = str(warning) if warning else None

    # Stable, de-duplicated order makes metadata and tests reproducible.
    unique_reasons = tuple(dict.fromkeys(reasons))
    return PublicationDecision(
        publishable=not unique_reasons,
        reasons=unique_reasons,
        withheld=withheld,
        verdict_record=verdict_record,
        audit_warning=audit_warning,
    )


def is_publishable(metadata: Mapping[str, Any] | None) -> bool:
    """Whether a result may cross a public boundary or enter a cache.

    An applied gate record is authoritative: it also carries verdicts that
    only exist after application (``all_sentences_withheld``).  Without one
    the metadata is evaluated afresh.
    """

    data = _mapping(metadata)
    gate = _mapping(data.get("publication_gate"))
    if gate.get("policy") == POLICY and gate.get("applied"):
        return bool(gate.get("publishable"))
    return evaluate_publication(data).publishable


def _severity(reason: str) -> int:
    order = (
        REASON_UNAUDITED,
        REASON_VERIFIER_ERROR,
        REASON_WEAK,
        REASON_MISSING,
        REASON_REJECTED,
    )
    return order.index(reason) if reason in order else 0


# ---------------------------------------------------------------------------
# Sentence-level withholding
# ---------------------------------------------------------------------------


def _normalise(text: str) -> str:
    return _WS_RE.sub(" ", text).strip()


def _sentence_cites(
    sentence: str,
    *,
    refs: frozenset[str],
    ids: frozenset[str],
) -> bool:
    """Whether ``sentence`` carries an inline marker for a withheld citation.

    Handles the legacy renderer's ``[P1]`` / ``[1, P2]`` reference lists (matched
    against ``Citation.ref``) and the dialectical ``[passage_<id>: …]`` /
    ``[P_<id>: …]`` markers (matched against the citation id).
    """
    for match in _BRACKET_RE.finditer(sentence):
        block = match.group(1)
        stripped = block.strip()
        if not stripped:
            continue
        if stripped in ids or stripped in refs:
            return True
        if _PURE_REF_LIST_RE.match(block):
            for token in _REF_TOKEN_RE.findall(block):
                if token in refs or token in ids:
                    return True
            continue
        marker = _MARKER_BODY_RE.match(stripped)
        if marker is None:
            continue
        ref_id = marker.group("body").split(":", 1)[0].strip().lstrip("_")
        if ref_id and (ref_id in ids or ref_id in refs):
            return True
    return False


def _sentence_matches_claim(sentence: str, claims: Sequence[str]) -> bool:
    norm = _normalise(sentence)
    if not norm:
        return False
    for claim in claims:
        if norm == claim:
            return True
        if len(norm) >= 20 and norm in claim:
            return True
    return False


def _is_blockquote(line: str) -> bool:
    return line.lstrip().startswith(">")


def withhold_sentences(
    text: str,
    *,
    refs: Iterable[str] = (),
    ids: Iterable[str] = (),
    claims: Iterable[str] = (),
) -> WithholdingOutcome:
    """Remove every sentence citing a withheld citation from ``text``.

    A sentence is withheld when it carries an inline marker for one of
    ``refs``/``ids`` or when it is (part of) one of the withheld ledger
    ``claims``.  Withheld sentences are replaced by
    :data:`WITHHELD_SENTENCE_MARKER`; consecutive markers collapse into one.
    A blockquote block (contiguous ``>`` lines) stands or falls as a whole:
    an original and its translation are never separated.  List bullets and
    headings keep their prefix.  Text that is not withheld is preserved
    byte-for-byte.
    """

    ref_set = frozenset(r for r in refs if r)
    id_set = frozenset(i for i in ids if i)
    claim_set = tuple(dict.fromkeys(_normalise(c) for c in claims if _normalise(c)))
    if not ref_set and not id_set and not claim_set:
        return WithholdingOutcome(text, 0, _count_sentences(text))

    def hit(sentence: str) -> bool:
        return _sentence_cites(
            sentence, refs=ref_set, ids=id_set
        ) or _sentence_matches_claim(sentence, claim_set)

    lines = text.split("\n")
    out_lines: list[str] = []
    withheld = 0
    published = 0

    index = 0
    while index < len(lines):
        line = lines[index]
        if _is_blockquote(line):
            block_end = index
            while block_end + 1 < len(lines) and _is_blockquote(lines[block_end + 1]):
                block_end += 1
            block = lines[index : block_end + 1]
            block_sentences = [
                sentence
                for block_line in block
                for sentence in _split_line(block_line.lstrip()[1:])[0::2]
                if sentence.strip()
            ]
            if any(hit(sentence) for sentence in block_sentences):
                out_lines.append(WITHHELD_SENTENCE_MARKER)
                withheld += 1
            else:
                out_lines.extend(block)
                published += len(block_sentences)
            index = block_end + 1
            continue

        prefix_match = _LINE_PREFIX_RE.match(line)
        prefix = prefix_match.group(1) if prefix_match else ""
        body = line[len(prefix) :]
        parts = _split_line(body)
        rebuilt: list[str] = []
        for position, part in enumerate(parts):
            if position % 2 == 1:
                rebuilt.append(part)
                continue
            if not part.strip():
                rebuilt.append(part)
                continue
            if hit(part):
                rebuilt.append(WITHHELD_SENTENCE_MARKER)
                withheld += 1
            else:
                rebuilt.append(part)
                published += 1
        out_lines.append(prefix + _collapse_markers(rebuilt))
        index += 1

    return WithholdingOutcome("\n".join(out_lines), withheld, published)


def _split_line(body: str) -> list[str]:
    """Split one line into ``[sentence, sep, sentence, sep, ...]``."""
    return _SENTENCE_SEP_RE.split(body)


def _collapse_markers(parts: list[str]) -> str:
    """Re-assemble parts, collapsing runs of markers into a single marker."""
    result: list[str] = []
    pending_sep = ""
    last_was_marker = False
    for position, part in enumerate(parts):
        if position % 2 == 1:
            pending_sep = part
            continue
        if part == WITHHELD_SENTENCE_MARKER and last_was_marker:
            continue
        if result:
            result.append(pending_sep)
        result.append(part)
        pending_sep = ""
        last_was_marker = part == WITHHELD_SENTENCE_MARKER
    return "".join(result)


def _count_sentences(text: str) -> int:
    count = 0
    for line in text.split("\n"):
        if _is_blockquote(line):
            line = line.lstrip()[1:]
        else:
            prefix_match = _LINE_PREFIX_RE.match(line)
            if prefix_match:
                line = line[len(prefix_match.group(1)) :]
        count += sum(1 for part in _split_line(line)[0::2] if part.strip())
    return count


# ---------------------------------------------------------------------------
# Applying the verdict (shared core for model and mapping forms)
# ---------------------------------------------------------------------------


def _ledger_cites(evidence_ids: Sequence[str], citation_id: str) -> bool:
    suffix = f"::{citation_id}"
    return any(eid == citation_id or eid.endswith(suffix) for eid in evidence_ids)


def _ledger_reason(evidence_ids: Sequence[str], withheld: Mapping[str, str]) -> str:
    best: str | None = None
    for cid, reason in withheld.items():
        if _ledger_cites(evidence_ids, cid) and (
            best is None or _severity(reason) > _severity(best)
        ):
            best = reason
    return best or ""


@dataclass(slots=True)
class _Plan:
    decision: PublicationDecision
    withheld: dict[str, str]
    refs: set[str]
    reasons: dict[str, int]
    withheld_citations: list[dict[str, Any]]


def _plan(
    decision: PublicationDecision,
    citations: Sequence[Mapping[str, Any]],
    audit: Mapping[str, Any],
) -> _Plan:
    """Extend the decision's withheld set with unaudited citations."""
    withheld = dict(decision.withheld)
    if decision.verdict_record:
        verified_ids = set(_str_list(audit.get("verified_citations")))
        for citation in citations:
            cid = str(citation.get("id") or "")
            if cid and cid not in verified_ids and cid not in withheld:
                withheld[cid] = REASON_UNAUDITED
    refs: set[str] = set()
    withheld_citations: list[dict[str, Any]] = []
    for citation in citations:
        cid = str(citation.get("id") or "")
        if cid in withheld:
            ref = str(citation.get("ref") or "")
            if ref:
                refs.add(ref)
            withheld_citations.append(
                {"citation_id": cid, "ref": ref, "reason": withheld[cid]}
            )
    reasons: dict[str, int] = {}
    for reason in withheld.values():
        reasons[reason] = reasons.get(reason, 0) + 1
    return _Plan(
        decision, withheld, refs, dict(sorted(reasons.items())), withheld_citations
    )


def _withholding_metadata(
    plan: _Plan, outcome: WithholdingOutcome | None
) -> dict[str, Any]:
    return {
        "withheld_sentences": outcome.withheld_sentences if outcome else 0,
        "published_sentences": outcome.published_sentences if outcome else 0,
        "withheld_citations": plan.withheld_citations,
        "reasons": plan.reasons,
        "audit_warning": plan.decision.audit_warning,
    }


def _gate_metadata(
    decision: PublicationDecision,
    plan: _Plan,
    outcome: WithholdingOutcome | None,
    *,
    applied: bool,
) -> dict[str, Any]:
    status = decision.status
    if decision.publishable and (
        plan.withheld or (outcome and outcome.withheld_sentences)
    ):
        status = "partial"
    return {
        **decision.as_metadata(),
        "status": status,
        "applied": applied,
        "withholding": _withholding_metadata(plan, outcome),
    }


def _already_applied(metadata: Mapping[str, Any]) -> bool:
    gate = _mapping(metadata.get("publication_gate"))
    return bool(gate.get("applied")) and gate.get("policy") == POLICY


def annotate_publication_decision(
    answer: ScholarlyAnswer,
    *,
    withhold_prose: bool,
) -> ScholarlyAnswer:
    """Attach the shared verdict and, at a public boundary, apply it.

    ``withhold_prose=False`` keeps the internal draft for diagnostics: the
    verdict is recorded in ``metadata.publication_gate`` and a blocked draft
    has its citations marked unverified and supported claims downgraded, but
    the prose is untouched and ``applied`` stays False.

    ``withhold_prose=True`` publishes: a blocked draft loses prose, citations
    and ledger; otherwise sentences citing withheld citations are removed,
    those citations are dropped from the public list, their ledger items are
    downgraded to ``INSUFFICIENT`` with the reason, and the quality badge
    becomes ``High`` (nothing withheld) or ``Partial``.  Applying twice is a
    no-op.
    """

    if withhold_prose and _already_applied(answer.metadata):
        return answer

    decision = evaluate_publication(answer.metadata)
    audit = _mapping(answer.metadata.get("citation_verifier_v2"))
    plan = _plan(decision, [c.model_dump() for c in answer.citations], audit)

    if not decision.publishable:
        return _annotate_blocked(answer, decision, plan, withhold_prose=withhold_prose)

    if not withhold_prose:
        metadata = {
            **answer.metadata,
            "publication_gate": _gate_metadata(decision, plan, None, applied=False),
        }
        return answer.model_copy(update={"metadata": metadata})

    outcome = withhold_sentences(
        answer.answer,
        refs=plan.refs,
        ids=plan.withheld,
        claims=[
            item.claim
            for item in answer.claim_ledger
            if _ledger_reason(list(item.evidence_ids), plan.withheld)
        ],
    )
    if plan.withheld and outcome.published_sentences == 0:
        decision = PublicationDecision(
            publishable=False,
            reasons=(*decision.reasons, "all_sentences_withheld"),
            withheld=decision.withheld,
            verdict_record=decision.verdict_record,
            audit_warning=decision.audit_warning,
        )
        return _annotate_blocked(answer, decision, plan, withhold_prose=True)

    citations = [c for c in answer.citations if c.id not in plan.withheld]
    ledger = [_downgrade_item(item, plan.withheld) for item in answer.claim_ledger]
    metadata = {
        **answer.metadata,
        "publication_gate": _gate_metadata(decision, plan, outcome, applied=True),
    }
    return answer.model_copy(
        update={
            "answer": outcome.text,
            "citations": citations,
            "claim_ledger": ledger,
            "metadata": metadata,
            "quality_badge": BADGE_PARTIAL if plan.withheld else BADGE_HIGH,
            "insufficient_evidence": False,
        }
    )


def _downgrade_item(
    item: ClaimLedgerItem, withheld: Mapping[str, str]
) -> ClaimLedgerItem:
    reason = _ledger_reason(list(item.evidence_ids), withheld)
    if not reason:
        return item
    return item.model_copy(
        update={
            "status": ClaimStatus.INSUFFICIENT,
            "status_reason": f"withheld: {reason}",
        }
    )


def _annotate_blocked(
    answer: ScholarlyAnswer,
    decision: PublicationDecision,
    plan: _Plan,
    *,
    withhold_prose: bool,
) -> ScholarlyAnswer:
    metadata = {
        **answer.metadata,
        "publication_gate": _gate_metadata(
            decision, plan, None, applied=withhold_prose
        ),
    }
    reason = ", ".join(decision.reasons) or "publication gate blocked"
    unverified_citations: list[Citation] = [
        citation.model_copy(
            update={
                "verified": False,
                "verification_note": citation.verification_note
                or f"[WITHHELD] {reason}",
            }
        )
        for citation in answer.citations
    ]
    downgraded_ledger = [
        item.model_copy(
            update={
                "status": ClaimStatus.INSUFFICIENT,
                "status_reason": f"blocked: {reason}",
            }
        )
        if item.status is ClaimStatus.SUPPORTED
        else item
        for item in answer.claim_ledger
    ]
    updates: dict[str, Any] = {
        "metadata": metadata,
        "citations": unverified_citations,
        "claim_ledger": downgraded_ledger,
        "quality_badge": BADGE_BLOCKED,
        "insufficient_evidence": True,
    }
    if withhold_prose:
        updates.update(
            {
                "answer": "",
                "citations": [],
                "claim_ledger": [],
                "passages_used": 0,
            }
        )
    return answer.model_copy(update=updates)


def apply_publication_verdict(result: Mapping[str, Any]) -> dict[str, Any]:
    """Public-boundary equivalent for ``GraphRAGService.query_dict`` results.

    Same verdict, same withholding, same metadata as
    :func:`annotate_publication_decision` with ``withhold_prose=True``, on the
    plain-dict shape that crosses the service boundary and the answer caches.
    Idempotent: a result that already carries an applied verdict is returned
    unchanged.
    """

    output = dict(result)
    metadata = _mapping(output.get("metadata"))
    if _already_applied(metadata):
        output["metadata"] = metadata
        return output

    decision = evaluate_publication(metadata)
    audit = _mapping(metadata.get("citation_verifier_v2"))
    citations = [
        _mapping(c) for c in (output.get("citations") or []) if isinstance(c, Mapping)
    ]
    ledger = [
        _mapping(c)
        for c in (output.get("claim_ledger") or [])
        if isinstance(c, Mapping)
    ]
    plan = _plan(decision, citations, audit)

    if decision.publishable:
        outcome = withhold_sentences(
            str(output.get("answer") or ""),
            refs=plan.refs,
            ids=plan.withheld,
            claims=[
                str(item.get("claim") or "")
                for item in ledger
                if _ledger_reason(_str_list(item.get("evidence_ids")), plan.withheld)
            ],
        )
        if plan.withheld and outcome.published_sentences == 0:
            decision = PublicationDecision(
                publishable=False,
                reasons=(*decision.reasons, "all_sentences_withheld"),
                withheld=decision.withheld,
                verdict_record=decision.verdict_record,
                audit_warning=decision.audit_warning,
            )
        else:
            published_ledger = []
            for item in ledger:
                reason = _ledger_reason(
                    _str_list(item.get("evidence_ids")), plan.withheld
                )
                if reason:
                    item = {
                        **item,
                        "status": ClaimStatus.INSUFFICIENT.value,
                        "status_reason": f"withheld: {reason}",
                    }
                published_ledger.append(item)
            badge = BADGE_PARTIAL if plan.withheld else BADGE_HIGH
            output.update(
                {
                    "answer": outcome.text,
                    "citations": [
                        c
                        for c in citations
                        if str(c.get("id") or "") not in plan.withheld
                    ],
                    "claim_ledger": published_ledger,
                    "insufficient_evidence": False,
                    "metadata": {
                        **metadata,
                        "quality_badge": badge,
                        "publication_gate": _gate_metadata(
                            decision, plan, outcome, applied=True
                        ),
                    },
                }
            )
            if "polished_markdown" in output and output["polished_markdown"]:
                polished = withhold_sentences(
                    str(output["polished_markdown"]),
                    refs=plan.refs,
                    ids=plan.withheld,
                )
                output["polished_markdown"] = polished.text
            return output

    output.update(
        {
            "answer": "",
            "citations": [],
            "claim_ledger": [],
            "passages_used": 0,
            "polished_markdown": "",
            "insufficient_evidence": True,
            "metadata": {
                **metadata,
                "quality_badge": BADGE_BLOCKED,
                "publication_gate": _gate_metadata(decision, plan, None, applied=True),
            },
        }
    )
    return output


def withhold_mapping_if_needed(result: Mapping[str, Any]) -> dict[str, Any]:
    """Backward-compatible alias of :func:`apply_publication_verdict`."""

    return apply_publication_verdict(result)


__all__ = [
    "BADGE_BLOCKED",
    "BADGE_HIGH",
    "BADGE_PARTIAL",
    "POLICY",
    "WITHHELD_SENTENCE_MARKER",
    "PublicationDecision",
    "WithholdingOutcome",
    "annotate_publication_decision",
    "apply_publication_verdict",
    "evaluate_publication",
    "is_publishable",
    "withhold_mapping_if_needed",
    "withhold_sentences",
]
