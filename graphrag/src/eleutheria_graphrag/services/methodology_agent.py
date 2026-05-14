"""
Methodology Agent — anti-anachronism + source-criticism patrol.

Runs after CitationVerifierV2 in deep mode. Inspects the verified draft
for four classes of methodological failure (anachronism, source criticism,
scholarly consensus, period appropriateness) and emits structured flags.

If any flag has ``severity="blocker"``, the orchestrator loops back to the
synthesizer for a v3 pass with the flags inline. The loop is capped at
``MAX_RESYNTH_ITERATIONS`` (default 2). After the cap, remaining flags
are forwarded inline to the polishing agent as ``[ED: …]`` markers.

The matching opencode agent (.opencode/agent/methodology.md) carries the
same instructions and is used when this runs as an opencode subagent.
"""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from eleutheria_graphrag.models.methodology import (
    MethodologyFlag,
    MethodologyReport,
)

if TYPE_CHECKING:
    from eleutheria_graphrag.services.llm_service import LLMService

logger = logging.getLogger(__name__)


MAX_RESYNTH_ITERATIONS = 2
"""Hard cap on synthesizer re-passes triggered by methodology blockers."""


METHODOLOGY_PROMPT = """\
You are the methodology auditor for the EleutherIA scholarly pipeline on \
ancient philosophy (free will, fate, moral responsibility, 6th c. BCE - \
6th c. CE plus modern reception). The citation verifier has already passed \
this draft. Your job is to catch CONCEPTUAL errors before polishing.

Run all four checks every time:

a. ANACHRONISM. Flag every un-hedged use of "free will" for a pre-Christian \
author (Aristotle has hekousion/prohairesis; Stoics have eph' hēmin/\
synkatathesis; the modern concept is post-ancient per Bobzien 1998/2014, \
debated by Frede 2011 and Dihle 1982). Flag every un-hedged \
"libertarian"/"compatibilist"/"incompatibilist"/"soft determinism"/\
"hard determinism" used of an ancient author (Kane 1985+ taxonomy). Flag \
every projection of a faculty "will" onto Aristotle (Dihle 1982 argues the \
faculty psychology of will is Patristic + Augustinian). Flag every "determinism" \
used univocally across Stoic/Atomist/theological/astral cases.

b. SOURCE CRITICISM. Flag claims that conflate direct attestation, testimonium, \
doxographical fragment, and modern paraphrase. "Chrysippus argued ..." when \
we only have Aulus Gellius is sloppy. Correct: "Chrysippus is reported by \
Aulus Gellius (Noctes Atticae VII.2.6-13 = SVF II.1000) to have argued ...".

c. SCHOLARLY CONSENSUS. For each substantive claim, decide if it is consensus, \
disputed, or outlier. Canonical disputed case: "Did ancient philosophy have a \
concept of free will?" — Frede yes, Bobzien no, Dihle later still. Picking one \
side without naming the others is a blocker.

d. PERIOD APPROPRIATENESS. Flag Stoic doctrines assigned to Aristotle and vice \
versa, Middle Platonism conflated with Neoplatonism, Augustinian categories \
projected onto pre-Augustinian Patristic authors, rabbinic conflated with \
Hellenistic Jewish thought.

Severity scale:
- blocker: the claim as written is wrong (anachronism stated as fact, scholarly \
debate elided, misattribution). Cannot ship.
- major: defensible but methodologically loose (un-hedged modern term, missing \
source-criticism layer). Forwarded to polishing as [ED: ...] marker.
- minor: stylistic methodology drift. Forwarded to polishing as [ED: ...] marker.

approved_for_polishing is false whenever any flag is a blocker. Otherwise true.

----- DRAFT UNDER AUDIT -----
{draft}

----- CLAIM LEDGER (for claim_id anchors) -----
{claim_ledger}
-----------------------------

Respond with ONLY a JSON object, no markdown fence, no prose:

{{
  "methodology_flags": [
    {{
      "type": "anachronism" | "source_criticism" | "scholarly_consensus" | "period_appropriateness",
      "claim_id_or_excerpt": "<claim id or short verbatim quote>",
      "issue": "<one sentence>",
      "scholarly_basis": "<one or two sentences citing real scholars>",
      "suggested_revision": "<one sentence rewriting the claim correctly>",
      "severity": "blocker" | "major" | "minor"
    }}
  ],
  "approved_for_polishing": true | false
}}

If the draft is methodologically clean, return an empty flags array and \
approved_for_polishing=true. Never invent scholars; if you cannot name a real \
authority for a disputed-consensus call, downgrade to major and say so."""


# Async callback: ``(event_dict) -> None``. Used for SSE streaming.
MethodologyCallback = Callable[[dict[str, Any]], Awaitable[None]] | None


# What the draft input looks like to the agent. The orchestrator builds it
# from the verified synthesizer output.
DraftInput = dict[str, Any]


class MethodologyAgent:
    """Methodology auditor for a citation-verified draft.

    Args:
        llm: LLM service for the audit call (low temperature, JSON-only).
        on_event: Optional async callback for SSE events
            (``methodology_flagged`` per flag, ``methodology_approved`` once
            no blockers remain).
        max_iterations: Hard cap on the synthesizer re-pass loop.
    """

    def __init__(
        self,
        llm: LLMService,
        *,
        on_event: MethodologyCallback = None,
        max_iterations: int = MAX_RESYNTH_ITERATIONS,
    ) -> None:
        self._llm = llm
        self._on_event = on_event
        self._max_iterations = max(1, max_iterations)

    # ------------------------------------------------------------------ API

    async def audit(self, draft: DraftInput) -> MethodologyReport:
        """Run one methodology pass over the verified draft."""
        draft_text = self._coerce_draft_text(draft)
        ledger_text = self._coerce_ledger_text(draft)

        prompt = METHODOLOGY_PROMPT.format(
            draft=draft_text[:12_000],
            claim_ledger=ledger_text[:4_000],
        )

        try:
            raw = await self._llm.generate(
                prompt,
                temperature=0.2,
                max_tokens=2_000,
            )
        except Exception:
            logger.warning(
                "Methodology LLM call failed — returning empty report",
                exc_info=True,
            )
            return MethodologyReport(
                methodology_flags=[], approved_for_polishing=True
            )

        report = self._parse_report(raw)

        # Emit one event per flag for live UI streaming.
        for flag in report.methodology_flags:
            await self._emit_flag(flag)

        if report.approved_for_polishing:
            await self._emit_approved()

        return report

    async def run_with_resynth_loop(
        self,
        initial_draft: DraftInput,
        resynthesize: Callable[
            [DraftInput, list[MethodologyFlag]], Awaitable[DraftInput]
        ],
    ) -> tuple[DraftInput, MethodologyReport]:
        """Run audit + (up to ``max_iterations`` - 1) re-synth passes.

        ``resynthesize`` is an async callable supplied by the orchestrator
        that takes ``(current_draft, blockers)`` and returns a new draft.

        Returns the final ``(draft, report)``. If blockers remain after the
        cap, they are still in ``report.methodology_flags`` so the polishing
        agent can carry them inline as editorial markers.
        """
        draft = initial_draft
        report = await self.audit(draft)
        iterations = 1
        while (
            report.blockers
            and iterations < self._max_iterations
        ):
            try:
                draft = await resynthesize(draft, report.blockers)
            except Exception:
                logger.warning(
                    "Re-synthesis failed at iteration %d — accepting current draft",
                    iterations,
                    exc_info=True,
                )
                break
            iterations += 1
            report = await self.audit(draft)
        return draft, report

    # ------------------------------------------------------------------ helpers

    @staticmethod
    def _coerce_draft_text(draft: DraftInput) -> str:
        """Pull the prose draft out of the orchestrator's result dict."""
        if not isinstance(draft, dict):
            return str(draft)
        for key in ("polished_markdown", "answer", "draft", "synthesized_text"):
            value = draft.get(key)
            if isinstance(value, str) and value.strip():
                return value
        return ""

    @staticmethod
    def _coerce_ledger_text(draft: DraftInput) -> str:
        """Render the claim ledger (if any) as a compact text block."""
        if not isinstance(draft, dict):
            return ""
        ledger = draft.get("claim_ledger") or []
        if not ledger:
            return "(no claim ledger; use verbatim quotes for claim_id_or_excerpt)"
        lines: list[str] = []
        for idx, entry in enumerate(ledger):
            if isinstance(entry, dict):
                claim = entry.get("claim") or entry.get("claim_text") or ""
            else:
                claim = getattr(entry, "claim", None) or getattr(
                    entry, "claim_text", ""
                )
            if not claim:
                continue
            lines.append(f"  c{idx + 1}: {str(claim)[:280]}")
        return "\n".join(lines) or "(empty ledger)"

    @staticmethod
    def _parse_report(raw: str) -> MethodologyReport:
        """Parse the LLM JSON output. Fail closed (empty, approved)."""
        if not raw:
            return MethodologyReport(
                methodology_flags=[], approved_for_polishing=True
            )
        text = raw.strip()
        # Strip optional ```json fences.
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            logger.warning("Methodology output not parseable; defaulting to empty")
            return MethodologyReport(
                methodology_flags=[], approved_for_polishing=True
            )
        try:
            payload = json.loads(match.group())
        except json.JSONDecodeError:
            logger.warning("Methodology JSON decode failed; defaulting to empty")
            return MethodologyReport(
                methodology_flags=[], approved_for_polishing=True
            )
        if not isinstance(payload, dict):
            return MethodologyReport(
                methodology_flags=[], approved_for_polishing=True
            )

        raw_flags = payload.get("methodology_flags") or []
        flags: list[MethodologyFlag] = []
        for item in raw_flags:
            if not isinstance(item, dict):
                continue
            flag_type = item.get("type")
            severity = item.get("severity")
            if flag_type not in (
                "anachronism",
                "source_criticism",
                "scholarly_consensus",
                "period_appropriateness",
            ):
                continue
            if severity not in ("blocker", "major", "minor"):
                continue
            claim_or_excerpt = str(item.get("claim_id_or_excerpt", "")).strip()
            issue = str(item.get("issue", "")).strip()
            suggested = str(item.get("suggested_revision", "")).strip()
            if not (claim_or_excerpt and issue and suggested):
                continue
            flags.append(
                MethodologyFlag(
                    type=flag_type,
                    claim_id_or_excerpt=claim_or_excerpt,
                    issue=issue,
                    scholarly_basis=str(item.get("scholarly_basis", "")).strip(),
                    suggested_revision=suggested,
                    severity=severity,
                )
            )

        # Derive approved_for_polishing from the flag list to avoid LLM
        # inconsistency (it sometimes returns approved=true with blockers).
        has_blocker = any(f.severity == "blocker" for f in flags)
        return MethodologyReport(
            methodology_flags=flags,
            approved_for_polishing=not has_blocker,
        )

    async def _emit_flag(self, flag: MethodologyFlag) -> None:
        if self._on_event is None:
            return
        try:
            await self._on_event(
                {
                    "type": "methodology_flagged",
                    "flag_type": flag.type,
                    "severity": flag.severity,
                    "issue": flag.issue,
                    "suggested_revision": flag.suggested_revision,
                }
            )
        except Exception:
            logger.warning(
                "methodology on_event callback failed", exc_info=True
            )

    async def _emit_approved(self) -> None:
        if self._on_event is None:
            return
        try:
            await self._on_event({"type": "methodology_approved"})
        except Exception:
            logger.warning(
                "methodology on_event callback failed", exc_info=True
            )


# ---------------------------------------------------------------------------
# Helpers for formatting flags back into the synthesizer prompt
# ---------------------------------------------------------------------------


def format_blockers_for_synthesizer(blockers: list[MethodologyFlag]) -> str:
    """Render blocker flags as a prompt block for synthesizer v3."""
    if not blockers:
        return ""
    lines: list[str] = [
        "## METHODOLOGY FLAGS (must be resolved before re-submission)",
        "",
        "The methodology auditor has flagged the following blocking issues. ",
        "For each, revise the draft so that the issue is fixed AND the ",
        "scholarly basis is acknowledged in the prose (or a hedge added).",
        "",
    ]
    for i, flag in enumerate(blockers, start=1):
        lines.append(f"### Flag {i} — {flag.type} (blocker)")
        lines.append(f"- Anchor: {flag.claim_id_or_excerpt}")
        lines.append(f"- Issue: {flag.issue}")
        if flag.scholarly_basis:
            lines.append(f"- Scholarly basis: {flag.scholarly_basis}")
        lines.append(f"- Suggested revision: {flag.suggested_revision}")
        lines.append("")
    return "\n".join(lines)


def format_non_blockers_as_editorial_markers(
    non_blockers: list[MethodologyFlag],
) -> str:
    """Render non-blocker flags as inline ``[ED: ...]`` markers for polishing."""
    if not non_blockers:
        return ""
    lines: list[str] = ["", "<!-- methodology editorial markers -->", ""]
    for flag in non_blockers:
        lines.append(
            f"[ED: methodology was unable to resolve flag — "
            f"{flag.type} ({flag.severity}): {flag.issue}]"
        )
    return "\n".join(lines)
