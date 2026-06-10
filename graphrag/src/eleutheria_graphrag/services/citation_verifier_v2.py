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

For REJECTED or WEAK, your ``reasoning`` MUST include a verbatim quote \
(in double quotes) from the passage above showing the mismatch. No quote, no \
rejection.

Respond with ONLY a JSON object, no markdown fence, no prose:
{{"status": "VERIFIED" | "WEAK" | "REJECTED" | "MISSING",
  "reasoning": "<one sentence>",
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
        for attempt in range(1, self._retries + 1):
            try:
                raw = await self._llm.generate(
                    prompt,
                    temperature=0.1,
                    max_tokens=400,
                )
                parsed = _parse_verdict(raw)
                if parsed is not None:
                    return parsed
                last_error = ValueError("verifier LLM returned unparseable JSON")
            except Exception as exc:  # noqa: BLE001 — third-party LLM client
                last_error = exc
                logger.debug(
                    "Verifier LLM attempt %d/%d failed: %s",
                    attempt,
                    self._retries,
                    exc,
                )

        logger.warning(
            "Verifier unable to assess citation %s after %d attempts (%s) — "
            "falling back to WEAK",
            citation_id,
            self._retries,
            last_error,
        )
        return {
            "status": CitationStatus.WEAK,
            "reasoning": "Verifier unable to assess: LLM call failed after retries.",
            "suggested_action": "manual review",
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
    except ValueError, AttributeError, TypeError:
        return None


_JSON_BLOCK_RE = re.compile(r"\{[\s\S]*\}")
_VALID_STATUSES = {s.value for s in CitationStatus}


def _parse_verdict(raw: str) -> dict[str, Any] | None:
    """Extract the JSON verdict from the LLM response. Returns ``None`` on failure."""
    if not raw:
        return None
    text = raw.strip()
    # Strip optional ```json fences.
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    match = _JSON_BLOCK_RE.search(text)
    if not match:
        return None
    try:
        obj = json.loads(match.group())
    except json.JSONDecodeError:
        return None
    if not isinstance(obj, dict):
        return None

    status_raw = str(obj.get("status", "")).strip().upper()
    if status_raw not in _VALID_STATUSES:
        return None

    reasoning = str(obj.get("reasoning", "")).strip()
    suggested_action = obj.get("suggested_action")
    if isinstance(suggested_action, str):
        suggested_action = suggested_action.strip() or None
    else:
        suggested_action = None

    return {
        "status": CitationStatus(status_raw),
        "reasoning": reasoning,
        "suggested_action": suggested_action,
    }
