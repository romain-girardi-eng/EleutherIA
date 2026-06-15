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
    ) -> None:
        self._llm = llm
        self._fetch = passage_fetcher
        self._emitter = emitter
        self._semaphore = asyncio.Semaphore(max(1, concurrency))
        self._retries = max(1, retries)
        self._warn_threshold = warn_threshold
        self._abort_threshold = abort_threshold

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
                    max_tokens=400,
                    response_mime_type="application/json",
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


def _extract_first_json_object(text: str) -> str | None:
    """Return the first balanced ``{...}`` block (brace-counting, string-aware).

    A greedy ``\\{.*\\}`` regex grabs from the first ``{`` to the *last* ``}``,
    which swallows trailing prose and any second object. Brace counting that
    respects JSON string literals returns exactly the first object.
    """
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    # Unbalanced (truncated). Return the tail from the first brace so the
    # repair pass below still gets a shot at it.
    return text[start:]


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
        except json.JSONDecodeError, ValueError:
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


def _parse_verdict(raw: str) -> dict[str, Any] | None:
    """Extract the JSON verdict from the LLM response. Returns ``None`` on failure.

    Resilient to: ```` ```json ```` fences, prose before/after the object, a
    trailing second object, trailing commas, status field-name variants
    (``verdict``/``result``/...), and unescaped double-quotes embedded inside
    string values (the dominant real-world failure — see G2 benchmark).
    """
    if not raw:
        return None
    text = raw.strip()
    # Strip markdown fences anywhere (opening ```json / ``` and closing ```).
    text = re.sub(r"```(?:json|JSON)?", "", text)
    text = text.strip()

    block = _extract_first_json_object(text)
    if not block:
        return None

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
