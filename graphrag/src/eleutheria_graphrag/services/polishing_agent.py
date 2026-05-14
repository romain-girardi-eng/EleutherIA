"""
Polishing Agent — doctoral-chapter pass.

Runs after the MethodologyAgent has either approved a draft or exhausted
its re-synth budget. The polisher rewrites the Markdown draft into a
doctoral chapter (Intro → State of the question → Sources → Analysis →
Counter-evidence → Conclusion), tightens academic register, and enforces
section structure.

The polisher never invents Greek or Latin text, never alters citation
ids or quotes, and never silently drops upstream editorial markers
(``[ED: …]``).

Matching opencode agent: ``.opencode/agent/polishing.md``.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from eleutheria_graphrag.models.methodology import (
    MethodologyFlag,
    PolishingResult,
)

if TYPE_CHECKING:
    from eleutheria_graphrag.services.llm_service import LLMService

logger = logging.getLogger(__name__)


REQUIRED_SECTIONS: tuple[str, ...] = (
    "Introduction",
    "State of the question",
    "Primary sources",
    "Analysis",
    "Counter-evidence and discussion",
    "Conclusion",
)


POLISHING_PROMPT = """\
You are the polishing agent for the EleutherIA scholarly pipeline. The draft \
below has passed citation verification and methodology audit. Raise it to a \
doctoral-chapter standard.

Hard rules:
- Never invent Greek or Latin text. Do not "restore" what an ancient author \
"must have said".
- Never change a passage_id, cts_urn, or quoted text inside a footnote.
- Never silently drop editorial markers — any [ED: ...] markers in the input \
must appear verbatim in the output.
- Output the rewritten Markdown only — no preamble, no JSON, no postscript.

Apply six checks:

a. ACADEMIC REGISTER. Replace first-person ("I argue", "I show") with \
impersonal third-person or passive. Remove "kind of", "sort of", "basically", \
"pretty much". Standardize Greek transliteration to Bobzien conventions \
(prohairesis, hekousion, eph' hēmin, synkatathesis). On first occurrence of \
a Greek term, give original-script + transliteration + English gloss; on \
subsequent occurrences, italicized transliteration alone is enough. Italicize \
Latin titles.

b. DOCTORAL CHAPTER STRUCTURE. The output must have six top-level sections \
in this order, marked with `## `:
  1. Introduction
  2. State of the question
  3. Primary sources
  4. Analysis
  5. Counter-evidence and discussion
  6. Conclusion
If a section is missing, add the heading and route existing content into it. \
If a section is empty (e.g., no counter-evidence was found), insert a \
one-sentence stub naming the absence.

c. FOOTNOTE DENSITY. Target ≥ 3 footnotes per main paragraph, mixing primary \
and secondary sources. If a primary citation lacks an edition, append \
"[ED: edition not specified in draft]". If a translation lacks a translator, \
append "[ED: translation provenance not specified]". Do not invent editions.

d. TRANSITIONS. Each section opens with a one-sentence transition naming the \
previous section's conclusion and the current section's task. Subsection \
headings are descriptive, not numeric ("Chrysippus on perfect and auxiliary \
causes", not "Argument 1").

e. PARAGRAPH SHAPE. Every paragraph should follow claim → evidence → \
analysis → micro-conclusion. If a paragraph stops at evidence, add a \
one-sentence micro-conclusion.

f. LENGTH BALANCE. No section under 100 words or over 800 words without \
justification. Analysis is normally the largest section; Introduction and \
Conclusion the smallest.

----- DRAFT (Markdown, methodology-approved) -----
{draft}
{flags_block}
-----

Return the rewritten Markdown only. The six top-level section headings must \
appear in order."""


PolishingCallback = Callable[[dict[str, Any]], Awaitable[None]] | None


class PolishingAgent:
    """Doctoral-chapter polishing pass over a methodology-approved draft.

    Args:
        llm: LLM service for the rewrite call.
        on_event: Optional async callback emitting a
            ``polishing_pass_complete`` event with the number of sections
            the polisher restructured or added.
    """

    def __init__(
        self,
        llm: LLMService,
        *,
        on_event: PolishingCallback = None,
    ) -> None:
        self._llm = llm
        self._on_event = on_event

    # ------------------------------------------------------------------ API

    async def polish(
        self,
        draft_markdown: str,
        *,
        carry_over_flags: list[MethodologyFlag] | None = None,
    ) -> PolishingResult:
        """Rewrite the draft into doctoral-chapter Markdown."""
        before_section_count = _count_required_sections(draft_markdown)

        flags_block = _format_flags_block(carry_over_flags or [])
        prompt = POLISHING_PROMPT.format(
            draft=draft_markdown[:14_000],
            flags_block=flags_block,
        )

        try:
            polished = await self._llm.generate(
                prompt,
                temperature=0.2,
                max_tokens=6_000,
            )
        except Exception:
            logger.warning(
                "Polishing LLM call failed — returning draft unchanged",
                exc_info=True,
            )
            return PolishingResult(
                markdown=draft_markdown,
                sections_modified=0,
                unresolved_flags_carried=len(carry_over_flags or []),
            )

        polished_md = _strip_fences(polished)
        polished_md = _ensure_carried_flags(polished_md, carry_over_flags or [])

        after_section_count = _count_required_sections(polished_md)
        sections_modified = max(0, after_section_count - before_section_count)

        # If the polisher actually rewrote the body, count that too.
        if sections_modified == 0 and polished_md.strip() != draft_markdown.strip():
            sections_modified = after_section_count

        result = PolishingResult(
            markdown=polished_md,
            sections_modified=sections_modified,
            unresolved_flags_carried=len(carry_over_flags or []),
        )
        await self._emit_complete(result)
        return result

    # ------------------------------------------------------------------ helpers

    async def _emit_complete(self, result: PolishingResult) -> None:
        if self._on_event is None:
            return
        try:
            await self._on_event(
                {
                    "type": "polishing_pass_complete",
                    "sections_modified": result.sections_modified,
                }
            )
        except Exception:
            logger.warning("polishing on_event callback failed", exc_info=True)


# ---------------------------------------------------------------------------
# module-level helpers (pure, easy to unit-test)
# ---------------------------------------------------------------------------


def _count_required_sections(markdown: str) -> int:
    """Count how many of the six required section headings appear in the draft."""
    if not markdown:
        return 0
    found = 0
    for section in REQUIRED_SECTIONS:
        # Match `## <section>` at start of line, case-insensitive, allowing
        # trailing words ("Counter-evidence and discussion" exactly, but
        # also "## Counter-evidence" alone should count for the same slot).
        head = section.split(" and ")[0] if " and " in section else section
        pattern = re.compile(
            rf"(?im)^\#{{1,3}}\s+{re.escape(head)}\b",
        )
        if pattern.search(markdown):
            found += 1
    return found


def missing_required_sections(markdown: str) -> list[str]:
    """Return required section names that are NOT yet in the draft."""
    missing: list[str] = []
    for section in REQUIRED_SECTIONS:
        head = section.split(" and ")[0] if " and " in section else section
        pattern = re.compile(rf"(?im)^\#{{1,3}}\s+{re.escape(head)}\b")
        if not pattern.search(markdown):
            missing.append(section)
    return missing


def _strip_fences(text: str) -> str:
    """Strip ```markdown fences if the LLM wrapped its output in one."""
    if not text:
        return ""
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:markdown|md)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned


def _format_flags_block(flags: list[MethodologyFlag]) -> str:
    if not flags:
        return ""
    lines: list[str] = [
        "",
        "----- METHODOLOGY EDITORIAL MARKERS (must be carried into output) -----",
    ]
    for flag in flags:
        lines.append(
            f"- [ED: methodology was unable to resolve flag — "
            f"{flag.type} ({flag.severity}): {flag.issue}]"
        )
    return "\n".join(lines)


def _ensure_carried_flags(
    polished_md: str, flags: list[MethodologyFlag]
) -> str:
    """Append any flags the polisher dropped as a trailing editorial block."""
    if not flags:
        return polished_md
    missing: list[MethodologyFlag] = []
    for flag in flags:
        marker_signature = f"{flag.type} ({flag.severity}): {flag.issue}"
        if marker_signature not in polished_md:
            missing.append(flag)
    if not missing:
        return polished_md
    trailer = ["", "<!-- editorial markers carried from methodology pass -->"]
    for flag in missing:
        trailer.append(
            f"[ED: methodology was unable to resolve flag — "
            f"{flag.type} ({flag.severity}): {flag.issue}]"
        )
    return polished_md.rstrip() + "\n\n" + "\n".join(trailer) + "\n"
