"""
Citation Verifier v2 — adversarial post-synthesis audit.

Replaces the disabled v1 verifier (false-positive issues per project memory).
The contract is different by design:

* v1 was a soft confirmation pass on the synthesizer's own evidence cache. It
  asked "does the evidence text we already have support the claim?" — which
  fails silently when the synthesizer pulled the wrong passage in the first
  place.
* **v2 is adversarial.** For every (claim, citation_id) pair it re-fetches
  the passage *fresh* from the corpus (the synthesizer's text is never
  trusted), reads the verbatim content, and returns one of four statuses:
  ``VERIFIED`` / ``WEAK`` / ``REJECTED`` / ``MISSING``. The matching opencode
  agent (.opencode/agent/citation-verifier.md) carries the same instructions
  when this runs as an opencode subagent.

Concurrency is capped via ``asyncio.Semaphore`` to avoid hammering the LLM
provider. The verifier degrades gracefully: if its own LLM call fails after
retries, the citation is marked ``WEAK`` (never silently passed) so a human
or a downstream pass can re-examine it.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import uuid
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from eleutheria_graphrag.models.verification import (
    CitationCheck,
    CitationStatus,
    DraftClaim,
    SynthesizedDraft,
    VerificationReport,
)

if TYPE_CHECKING:
    from eleutheria_graphrag.agents.sse_emitter import SSEEmitter
    from eleutheria_graphrag.services.llm_service import LLMService

logger = logging.getLogger(__name__)

# Adversarial verification prompt — note the framing ("find why this is bad").
VERIFY_PROMPT = """\
You are an ADVERSARIAL citation auditor for ancient philosophy. Your job is \
NOT to confirm citations — it is to find reasons to REJECT them. The \
synthesizer is downstream; you must not trust its account of the passage.

Claim being audited:
{claim}

Verbatim passage as fetched fresh from the corpus (passage_id={citation_id}):
\"\"\"
{passage_text}
\"\"\"

Decide one of four statuses:

- VERIFIED: the passage explicitly supports the claim. A specific clause \
asserts what the claim asserts.
- WEAK: the passage is on the same topic and consistent with the claim, but \
does not explicitly assert it. The synthesizer extrapolated.
- REJECTED: the passage does not support the claim, contradicts it, or is \
about a different author/topic than the claim attributes.
- MISSING: the passage is empty, unintelligible, or otherwise unusable.

Bias: when in doubt between VERIFIED and WEAK, choose WEAK. When in doubt \
between WEAK and REJECTED, choose REJECTED. False approvals defeat the \
verifier; false rejections merely send the draft back for a better citation.

For REJECTED or WEAK, you MUST supply a verbatim quote from the passage above \
showing the mismatch, in the ``evidence_quote`` field (NOT inside \
``reasoning``). No quote, no rejection.

Output format — CRITICAL. Respond with ONLY a single strict JSON object. No \
markdown fence, no prose before or after. Inside the ``reasoning`` string, do \
NOT use double-quote characters: write any quoted phrase with single quotes \
('like this'). Put the verbatim passage quote in ``evidence_quote`` only.

{{"status": "VERIFIED" | "WEAK" | "REJECTED" | "MISSING",
  "reasoning": "<one sentence, no double-quote characters inside>",
  "evidence_quote": "<verbatim passage quote for WEAK/REJECTED, else empty>",
  "suggested_action": "<optional remediation, or empty string>"}}"""

# How many verifier calls may run in parallel against the LLM.
DEFAULT_CONCURRENCY = 10
# How many times we retry a verifier LLM call before giving up and marking WEAK.
DEFAULT_RETRIES = 3
# Max passage chars sent to the LLM (long passages get truncated, but the
# *verbatim* prefix is preserved so the LLM can still quote it).
PASSAGE_TRUNCATE_CHARS = 4000

# Strict server-side JSON schema for the verdict. On Fireworks/Kimi this is
# enforced as ``response_format={"type": "json_schema", ...}`` so the model is
# constrained to a valid verdict object instead of free-running a meta-monologue
# (F1 root cause: kimi-k2p7-code rambling instead of emitting JSON). On providers
# that only support ``json_object`` the LLMService degrades gracefully; the
# tolerant parser is the second line of defence.
VERDICT_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "enum": ["VERIFIED", "WEAK", "REJECTED", "MISSING"],
        },
        "reasoning": {"type": "string"},
        "evidence_quote": {"type": "string"},
        "suggested_action": {"type": "string"},
    },
    "required": ["status", "reasoning"],
}

# Env knob: an explicit model for the verifier call (e.g. a reasoning model that
# returns parseable verdicts — ``accounts/fireworks/models/deepseek-v4-pro``).
# Unset → the LLMService default provider chain (unchanged behaviour). Read at
# call time so deployments can flip it without a code change.
_VERIFIER_MODEL_ENV = "ELEUTHERIA_VERIFIER_MODEL"

# A claim payload that is just a bare node label ("Susanne Bobzien",
# "Robert F. Dobbin, 121") is NOT auditable: there is no assertion to test
# against the passage, only a name. Feeding it to the adversarial auditor is what
# produced the "Wait, the claim is just 'Susanne Bobzien'?" monologue (F1c). We
# detect it deterministically and FAIL CLOSED instead of calling the LLM.
_BARE_LABEL_MAX_WORDS = 6
_CLAIM_VERB_RE = re.compile(
    r"\b(?:is|are|was|were|be|been|being|holds?|held|argues?|argued|claims?|"
    r"claimed|asserts?|asserted|maintains?|maintained|denies?|denied|says?|"
    r"said|states?|stated|contends?|defends?|rejects?|distinguishes?|"
    r"believes?|thinks?|shows?|implies|entails?|means?|has|have|had|"
    r"requires?|presupposes?|originat\w+|reads?|interprets?)\b",
    re.IGNORECASE,
)


# A bare label looks like a proper name (Title-Case tokens, optionally with
# initials) possibly trailed by a bare page/line number — exactly the
# ``citation.label`` fallback the synthesis path leaks ("Susanne Bobzien",
# "Robert F. Dobbin, 121"). It is NOT a generic short string ("Claim.", "c0").
_PROPER_NAME_RE = re.compile(r"[A-Z][a-zA-Z.''-]+")
_NAME_PLUS_NUMBER_RE = re.compile(r"^[A-Z].*?,?\s*\d+\s*$")


def _is_bare_label_claim(claim: str) -> bool:
    """True when ``claim`` is a bare label/name, not an auditable assertion.

    Deterministic, zero-fabrication. A real claim predicates something (it
    carries a verb). The degenerate input the synthesis path leaks is the bare
    ``citation.label``: a proper name, or a name + page number, with no verb —
    "Susanne Bobzien", "Robert F. Dobbin, 121". We flag ONLY that shape so a
    short test stub or a verbless noun-phrase claim is left to the auditor.
    """
    stripped = (claim or "").strip()
    if not stripped:
        return True
    if _CLAIM_VERB_RE.search(stripped):
        return False
    words = re.findall(r"\w+", stripped)
    if not words or len(words) > _BARE_LABEL_MAX_WORDS:
        return False
    # name + trailing page/line number ("Robert F. Dobbin, 121")
    if _NAME_PLUS_NUMBER_RE.match(stripped):
        return True
    # ≥2 Title-Case tokens and (nearly) every word capitalised → a proper name
    proper = _PROPER_NAME_RE.findall(stripped)
    alpha_words = [w for w in words if w[:1].isalpha()]
    return len(proper) >= 2 and len(proper) >= len(alpha_words)


PassageFetcher = Callable[[str], Awaitable[dict[str, Any] | None]]
"""Async callable: ``citation_id -> {text, label, urn, ...} | None``.

A ``None`` return (or empty ``text``) means MISSING. Implementations must
re-fetch each call — caching defeats the v2 contract.
"""


def build_db_passage_fetcher(
    db: Any,
    *,
    schema: str | None = None,
    node_lookup: dict[str, dict[str, Any]] | None = None,
) -> PassageFetcher:
    """Production :data:`PassageFetcher`: one fresh SELECT per call.

    Resolution order per the v2 contract (no caching, never trust the
    synthesizer's text):

    1. ``passages`` table by ``passage_id`` (passage citations);
    2. ``kg_nodes`` table by ``node_id`` (node citations — the description is
       the canonical claimable text for metadata-grounded claims);
    3. optional ``node_lookup`` snapshot as last resort when the DB is
       unreachable, so offline runs degrade to WEAK/REJECTED verdicts on real
       text instead of marking every citation MISSING.

    The passages arm only runs when ``citation_id`` parses as a UUID — the
    comparison is then ``passage_id = $1::uuid`` (index scan). Node-shaped
    ids skip the passages arm entirely instead of forcing the old
    ``passage_id::text = $1`` seq scan over 69k rows.
    """
    resolved_schema = schema or os.getenv("ELEUTHERIA_DB_SCHEMA", "free_will")

    async def fetch(citation_id: str) -> dict[str, Any] | None:
        rows: list[dict[str, Any]] = []
        passage_uuid = _try_parse_uuid(citation_id)
        if passage_uuid is not None:
            try:
                rows = await db.fetch(
                    f"""
                    SELECT
                        p.passage_id::text AS passage_id,
                        p.text_content,
                        p.canonical_ref,
                        w.title,
                        w.author
                    FROM {resolved_schema}.passages p
                    LEFT JOIN {resolved_schema}.ancient_works w
                        ON p.work_id = w.work_id
                    WHERE p.passage_id = $1::uuid
                    """,
                    str(passage_uuid),
                )
            except Exception:
                logger.debug(
                    "Fresh passage fetch failed for %s", citation_id, exc_info=True
                )
        if rows:
            row = rows[0]
            return {
                "text": row.get("text_content") or "",
                "label": row.get("canonical_ref") or citation_id,
                "work_title": row.get("title"),
                "author": row.get("author"),
                "source": "passages",
            }

        try:
            rows = await db.fetch(
                f"""
                SELECT node_id, label, description
                FROM {resolved_schema}.kg_nodes
                WHERE node_id = $1
                """,
                citation_id,
            )
        except Exception:
            logger.debug(
                "Fresh kg_node fetch failed for %s", citation_id, exc_info=True
            )
            rows = []
        if rows:
            row = rows[0]
            return {
                "text": row.get("description") or "",
                "label": row.get("label") or citation_id,
                "source": "kg_nodes",
            }

        if node_lookup:
            node = node_lookup.get(citation_id)
            if node:
                return {
                    "text": str(node.get("description") or ""),
                    "label": str(node.get("label") or citation_id),
                    "source": "kg_snapshot",
                }
        return None

    return fetch


class CitationVerifierV2:
    """Adversarial citation verifier.

    Args:
        llm: LLM service used for the verification calls (low temperature).
        passage_fetcher: Async callable that re-fetches a passage by id. The
            verifier intentionally takes this as a dependency so it is not
            coupled to the DB layer — production wires it to a fresh DB
            query, tests inject a mock.
        emitter: Optional SSE emitter. When supplied, emits one
            ``citation_verified`` event per check (matches the frontend
            protocol in ``frontend/src/types/agent-events.ts``).
        concurrency: Max parallel verifier LLM calls.
        retries: Per-citation LLM retries before falling back to WEAK.
        warn_threshold: Fraction of failed citations that triggers a warning
            in the aggregate report.
        abort_threshold: Fraction of failed citations that triggers
            ``aborted=True`` (orchestrator should discard the draft).
    """

    def __init__(
        self,
        llm: LLMService,
        passage_fetcher: PassageFetcher,
        *,
        emitter: SSEEmitter | None = None,
        concurrency: int = DEFAULT_CONCURRENCY,
        retries: int = DEFAULT_RETRIES,
        warn_threshold: float = 0.20,
        abort_threshold: float = 0.50,
        verifier_model: str | None = None,
    ) -> None:
        self._llm = llm
        self._fetch = passage_fetcher
        self._emitter = emitter
        self._semaphore = asyncio.Semaphore(max(1, concurrency))
        self._retries = max(1, retries)
        self._warn_threshold = warn_threshold
        self._abort_threshold = abort_threshold
        # Explicit > env > default-chain. A reasoning model that returns
        # parseable verdicts (e.g. deepseek-v4-pro) can be pinned here without
        # touching the shared LLMService provider chain.
        self._verifier_model = verifier_model or os.getenv(_VERIFIER_MODEL_ENV) or None

    # ------------------------------------------------------------------ API

    async def verify_draft(self, draft: SynthesizedDraft) -> VerificationReport:
        """Verify every claim/citation pair in ``draft`` in parallel."""
        if not draft.claims:
            return VerificationReport.from_checks(
                [],
                warn_threshold=self._warn_threshold,
                abort_threshold=self._abort_threshold,
            )

        tasks = [
            asyncio.create_task(self._verify_with_semaphore(claim))
            for claim in draft.claims
        ]
        checks: list[CitationCheck] = list(await asyncio.gather(*tasks))

        report = VerificationReport.from_checks(
            checks,
            warn_threshold=self._warn_threshold,
            abort_threshold=self._abort_threshold,
        )
        logger.info(
            "CitationVerifierV2: %d total | %d verified | %d weak | %d rejected | %d missing",
            report.total,
            report.verified,
            report.weak,
            report.rejected,
            report.missing,
        )
        return report

    async def verify_one(self, claim: str, passage_id: str) -> CitationCheck:
        """Single-shot helper (also used by tests). Re-fetches the passage."""
        return await self._verify_one(
            DraftClaim(claim=claim, citation_id=passage_id, citation_kind="passage")
        )

    # -------------------------------------------------------------- internals

    async def _verify_with_semaphore(self, claim: DraftClaim) -> CitationCheck:
        async with self._semaphore:
            return await self._verify_one(claim)

    async def _verify_one(self, claim: DraftClaim) -> CitationCheck:
        # 0) Guard the auditor input itself (F1c). A bare node label
        # ("Susanne Bobzien", "Robert F. Dobbin, 121") is not an auditable
        # claim — there is no assertion to test. Fail CLOSED (WEAK, flagged as a
        # verifier issue, never a clean VERIFIED) instead of feeding the
        # adversarial model a name it can only ramble about.
        if _is_bare_label_claim(claim.claim):
            logger.warning(
                "Verifier received a bare-label claim for %s (%r) — not an "
                "auditable claim+passage pair; failing closed to WEAK.",
                claim.citation_id,
                (claim.claim or "")[:120],
            )
            check = CitationCheck(
                citation_id=claim.citation_id,
                status=CitationStatus.WEAK,
                reasoning=(
                    "Verifier could not audit: the claim payload was a bare "
                    "label/name, not a claim+passage pair. Citation left "
                    "UNVERIFIED pending a real claim sentence."
                ),
                claim=claim.claim,
                passage_excerpt="",
                suggested_action="supply the claim sentence for this citation",
                parse_error=True,
            )
            await self._emit(check)
            return check

        # 1) Re-fetch — no caching, no trust of upstream paraphrase.
        try:
            fetched = await self._fetch(claim.citation_id)
        except Exception:
            logger.warning(
                "Passage fetch raised for %s — marking MISSING",
                claim.citation_id,
                exc_info=True,
            )
            fetched = None

        if not fetched or not (fetched.get("text") or "").strip():
            check = CitationCheck(
                citation_id=claim.citation_id,
                status=CitationStatus.MISSING,
                reasoning="Passage could not be re-fetched from the corpus.",
                claim=claim.claim,
                passage_excerpt="",
                suggested_action="remove citation",
            )
            await self._emit(check)
            return check

        passage_text = str(fetched.get("text", "")).strip()
        truncated = passage_text[:PASSAGE_TRUNCATE_CHARS]

        # 2) Ask the LLM to find why the citation is bad (adversarial framing).
        verdict = await self._ask_llm(claim.claim, claim.citation_id, truncated)

        status = verdict["status"]
        check = CitationCheck(
            citation_id=claim.citation_id,
            status=status,
            reasoning=verdict["reasoning"],
            claim=claim.claim,
            passage_excerpt=truncated,
            suggested_action=verdict.get("suggested_action") or None,
            parse_error=bool(verdict.get("parse_error", False)),
        )
        await self._emit(check)
        return check

    async def _ask_llm(
        self,
        claim: str,
        citation_id: str,
        passage_text: str,
    ) -> dict[str, Any]:
        prompt = VERIFY_PROMPT.format(
            claim=claim,
            citation_id=citation_id,
            passage_text=passage_text,
        )

        last_error: Exception | None = None
        last_raw: str | None = None
        for attempt in range(1, self._retries + 1):
            try:
                raw = await self._llm.generate(
                    prompt,
                    temperature=0.1,
                    # Reasoning models need headroom to emit reasoning AND the
                    # verdict object; 400 truncated the JSON on the rambling
                    # path. The schema keeps the visible output tight.
                    max_tokens=700,
                    response_mime_type="application/json",
                    response_json_schema=VERDICT_JSON_SCHEMA,
                    model_override=self._verifier_model,
                )
                last_raw = raw
                parsed = _parse_verdict(raw)
                if parsed is not None:
                    return parsed
                last_error = ValueError("verifier LLM returned unparseable JSON")
                # A parse failure is NOT a verdict — log the raw output so the
                # format drift is debuggable instead of vanishing into a WEAK.
                logger.warning(
                    "Verifier could not parse LLM output for %s (attempt %d/%d). "
                    "Raw output: %r",
                    citation_id,
                    attempt,
                    self._retries,
                    (raw or "")[:1000],
                )
            except Exception as exc:  # noqa: BLE001 — third-party LLM client
                last_error = exc
                logger.debug(
                    "Verifier LLM attempt %d/%d failed: %s",
                    attempt,
                    self._retries,
                    exc,
                )

        # Genuine failure after retries. Default to WEAK (adversarial bias:
        # never silently pass), but flag it as a verifier error, not a real
        # "consistent-but-not-asserted" WEAK verdict, so it can be distinguished
        # downstream and in benchmarks.
        logger.warning(
            "Verifier unable to assess citation %s after %d attempts (%s) — "
            "falling back to WEAK. Last raw output: %r",
            citation_id,
            self._retries,
            last_error,
            (last_raw or "")[:1000],
        )
        return {
            "status": CitationStatus.WEAK,
            "reasoning": (
                "Verifier unable to assess: LLM call failed or returned "
                "unparseable output after retries."
            ),
            "suggested_action": "manual review",
            "parse_error": True,
        }

    async def _emit(self, check: CitationCheck) -> None:
        if self._emitter is None:
            return
        try:
            await self._emitter.emit_citation_verified(
                passage_id=check.citation_id,
                status=check.status.value,
                verified=check.is_passing,
                reason=check.reasoning,
            )
        except AttributeError:
            # Older emitter (no emit_citation_verified). Don't crash the
            # pipeline over a telemetry-only call.
            logger.debug("SSE emitter lacks emit_citation_verified — skipping")
        except Exception:
            logger.warning(
                "SSE emit failed for citation %s — continuing",
                check.citation_id,
                exc_info=True,
            )


# --------------------------------------------------------------------- helpers


def _try_parse_uuid(value: str) -> uuid.UUID | None:
    """Parse ``value`` as a UUID, or ``None`` for node-shaped ids."""
    try:
        return uuid.UUID(value)
    except (ValueError, AttributeError, TypeError):  # fmt: skip
        return None


_VALID_STATUSES = {s.value for s in CitationStatus}

# Field-name variants the model drifts to, mapped to our canonical fields.
_STATUS_KEYS = ("status", "verdict", "judgment", "judgement", "result", "label")
_REASONING_KEYS = ("reasoning", "rationale", "reason", "explanation", "justification")
_QUOTE_KEYS = ("evidence_quote", "quote", "verbatim_quote", "evidence", "passage_quote")
_ACTION_KEYS = ("suggested_action", "action", "remediation", "suggestion")

# Loose status-token map (handles the model answering with a bare word or a
# near-synonym instead of the exact enum value).
_STATUS_ALIASES = {
    "VERIFIED": "VERIFIED",
    "VERIFY": "VERIFIED",
    "SUPPORTED": "VERIFIED",
    "PASS": "VERIFIED",
    "WEAK": "WEAK",
    "PARTIAL": "WEAK",
    "CONSISTENT": "WEAK",
    "REJECTED": "REJECTED",
    "REJECT": "REJECTED",
    "UNSUPPORTED": "REJECTED",
    "CONTRADICTED": "REJECTED",
    "FAIL": "REJECTED",
    "MISSING": "MISSING",
    "EMPTY": "MISSING",
    "UNUSABLE": "MISSING",
}


def _iter_json_objects(text: str) -> list[str]:
    """Return every top-level balanced ``{...}`` block, in source order.

    Brace counting that respects JSON string literals, so a quote containing
    ``{`` / ``}`` does not corrupt the boundaries. A reasoning model emits a
    meta-monologue (often with stray braces) and only THEN the real verdict
    object; returning all candidates lets the caller prefer the LAST one that
    actually parses to a verdict (F1: reasoning-then-JSON).
    """
    blocks: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        if text[i] != "{":
            i += 1
            continue
        start = i
        depth = 0
        in_string = False
        escape = False
        closed = False
        while i < n:
            ch = text[i]
            if in_string:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_string = False
            elif ch == '"':
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    blocks.append(text[start : i + 1])
                    i += 1
                    closed = True
                    break
            i += 1
        if not closed:
            # Unbalanced tail (truncated final object) — keep it so the repair
            # pass below still gets a shot at it, then stop.
            blocks.append(text[start:])
            break
    return blocks


def _extract_first_json_object(text: str) -> str | None:
    """Return the first balanced ``{...}`` block (brace-counting, string-aware).

    A greedy ``\\{.*\\}`` regex grabs from the first ``{`` to the *last* ``}``,
    which swallows trailing prose and any second object. Brace counting that
    respects JSON string literals returns exactly the first object.
    """
    blocks = _iter_json_objects(text)
    return blocks[0] if blocks else None


def _strip_trailing_commas(text: str) -> str:
    """Remove trailing commas before ``}`` / ``]`` (a very common LLM slip)."""
    return re.sub(r",(\s*[}\]])", r"\1", text)


def _repair_inner_quotes(block: str) -> str:
    """Best-effort repair of unescaped double-quotes *inside* string values.

    The single biggest source of unparseable verdicts: the model embeds a
    verbatim ``"quote"`` inside the ``reasoning`` value, producing
    ``"reasoning": "... says "x" ..."``. We walk the JSON char-by-char and,
    once inside a string value, escape any ``"`` that is not the genuine
    closing quote (i.e. not followed by ``:``, ``,`` or a closing brace).
    """
    out: list[str] = []
    in_string = False
    escape = False
    i = 0
    n = len(block)
    while i < n:
        ch = block[i]
        if not in_string:
            out.append(ch)
            if ch == '"':
                in_string = True
            i += 1
            continue
        if escape:
            out.append(ch)
            escape = False
            i += 1
            continue
        if ch == "\\":
            out.append(ch)
            escape = True
            i += 1
            continue
        if ch == '"':
            # Is this the real closing quote? Peek past whitespace.
            j = i + 1
            while j < n and block[j] in " \t\r\n":
                j += 1
            nxt = block[j] if j < n else ""
            if nxt in (":", ",", "}", "]", ""):
                out.append(ch)
                in_string = False
            else:
                # Stray inner quote — escape it.
                out.append('\\"')
            i += 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def _loads_tolerant(block: str) -> Any | None:
    """Try increasingly aggressive repairs to parse ``block`` as JSON."""
    for candidate in (
        block,
        _strip_trailing_commas(block),
        _strip_trailing_commas(_repair_inner_quotes(block)),
    ):
        try:
            return json.loads(candidate)
        except (json.JSONDecodeError, ValueError):  # fmt: skip
            continue
    return None


def _first_present(obj: dict[str, Any], keys: tuple[str, ...]) -> Any:
    """Return the first value among ``keys`` (case-insensitive) present in ``obj``."""
    lowered = {str(k).lower(): v for k, v in obj.items()}
    for key in keys:
        if key in lowered:
            return lowered[key]
    return None


def _coerce_status(value: Any) -> str | None:
    """Map a raw status value to a canonical enum value, or ``None``."""
    token = str(value or "").strip().upper()
    if token in _VALID_STATUSES:
        return token
    if token in _STATUS_ALIASES:
        return _STATUS_ALIASES[token]
    # Sometimes the model answers with a sentence; pick the first known token.
    for word in re.findall(r"[A-Z]+", token):
        if word in _VALID_STATUSES:
            return word
        if word in _STATUS_ALIASES:
            return _STATUS_ALIASES[word]
    return None


def _verdict_from_block(block: str) -> dict[str, Any] | None:
    """Parse ONE balanced ``{...}`` block into a verdict dict, or ``None``."""
    obj = _loads_tolerant(block)
    if not isinstance(obj, dict):
        return None

    status_canonical = _coerce_status(_first_present(obj, _STATUS_KEYS))
    if status_canonical is None:
        return None

    reasoning = str(_first_present(obj, _REASONING_KEYS) or "").strip()
    quote = str(_first_present(obj, _QUOTE_KEYS) or "").strip()
    # Fold the evidence quote back into reasoning so downstream consumers (which
    # expect the verbatim quote in `reasoning` for WEAK/REJECTED) keep working.
    if quote and quote not in reasoning:
        reasoning = f'{reasoning} "{quote}"'.strip() if reasoning else f'"{quote}"'

    action_raw = _first_present(obj, _ACTION_KEYS)
    suggested_action = (
        action_raw.strip() or None if isinstance(action_raw, str) else None
    )

    return {
        "status": CitationStatus(status_canonical),
        "reasoning": reasoning,
        "suggested_action": suggested_action,
    }


# A leading meta-monologue (the reasoning/code model's failure mode) is "prose"
# when there is a substantial run of words before the first JSON object.
_PROSE_PREFIX_MIN_CHARS = 80


def _parse_verdict(raw: str) -> dict[str, Any] | None:
    """Extract the JSON verdict from the LLM response. Returns ``None`` on failure.

    Resilient to: ```` ```json ```` fences, prose before/after the object, a
    trailing second object, trailing commas, status field-name variants
    (``verdict``/``result``/...), unescaped double-quotes embedded inside string
    values (the G2 benchmark killer), AND a reasoning-then-JSON response where a
    non-reasoning code model rambles a meta-monologue and only THEN emits the
    real verdict object (F1).

    Selection rule (honours both failure shapes):

    * if the response *opens* with the JSON (no substantial leading prose), take
      the FIRST parseable verdict — guards against ``{verdict}{noise}``;
    * if a meta-monologue precedes the first object, take the LAST parseable
      verdict — the rambling model's real answer is at the end.
    """
    if not raw:
        return None
    text = raw.strip()
    # Strip markdown fences anywhere (opening ```json / ``` and closing ```).
    text = re.sub(r"```(?:json|JSON)?", "", text)
    text = text.strip()

    blocks = _iter_json_objects(text)
    if not blocks:
        return None

    parsed = [(b, _verdict_from_block(b)) for b in blocks]
    valid = [(b, v) for b, v in parsed if v is not None]
    if not valid:
        return None

    first_block = valid[0][0]
    prefix = text[: text.find(first_block)]
    # A short prefix (fence remnants, "Here is the verdict:") keeps the FIRST
    # object; a long meta-monologue flips to the LAST parseable verdict.
    if len(prefix.strip()) >= _PROSE_PREFIX_MIN_CHARS:
        return valid[-1][1]
    return valid[0][1]
