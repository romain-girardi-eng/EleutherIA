"""Tests for the Polishing Agent sub-agent."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from eleutheria_graphrag.models.methodology import MethodologyFlag
from eleutheria_graphrag.services.polishing_agent import (
    PolishingAgent,
    _count_required_sections,
    missing_required_sections,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_llm(payload: str | list[str]) -> MagicMock:
    llm = MagicMock()
    if isinstance(payload, list):
        llm.generate = AsyncMock(side_effect=payload)
    else:
        llm.generate = AsyncMock(return_value=payload)
    return llm


MESSY_DRAFT = """\
# Stoic determinism

In this paper I argue that the Stoics were basically compatibilists. \
Chrysippus kind of talks about fate as a sort of cause. I show that this \
view holds up.

Cicero (De Fato) says fate is causal.

Frede disagrees with me but I think he's wrong.
"""

CLEAN_DOCTORAL_OUTPUT = """\
## Introduction

The question of whether the early Stoa held what modern scholars term \
compatibilism is the subject of a longstanding debate.

## State of the question

Bobzien (1998) and Frede (2011) take opposing positions on the matter.

## Primary sources

The principal source is Cicero, *De Fato* (Yon ed., Budé 1933).

## Analysis

Chrysippus is reported by Cicero to have distinguished perfect from \
auxiliary causes (Cicero, *De Fato* 41).

## Counter-evidence and discussion

Frede 2011 disputes this reading. Bobzien 1998 argues against it.

## Conclusion

The argument is best read as compatibilist in a qualified sense.
"""


# ---------------------------------------------------------------------------
# Tests — register normalization
# ---------------------------------------------------------------------------


class TestPolishingRegisterAndStructure:
    @pytest.mark.asyncio
    async def test_polisher_calls_llm_with_draft(self) -> None:
        """The polisher must send the draft into the LLM and surface the result."""
        llm = _make_llm(CLEAN_DOCTORAL_OUTPUT)
        agent = PolishingAgent(llm)
        result = await agent.polish(MESSY_DRAFT)
        assert "## Introduction" in result.markdown
        assert "## Analysis" in result.markdown
        # The polisher should have been invoked exactly once.
        llm.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_polishing_returns_unchanged_on_llm_failure(self) -> None:
        """If the LLM raises, the polisher returns the draft as-is."""
        llm = MagicMock()
        llm.generate = AsyncMock(side_effect=RuntimeError("LLM down"))
        agent = PolishingAgent(llm)
        result = await agent.polish(MESSY_DRAFT)
        assert result.markdown == MESSY_DRAFT
        assert result.sections_modified == 0

    @pytest.mark.asyncio
    async def test_polishing_strips_markdown_fences(self) -> None:
        """If the LLM wraps output in ```markdown fences, the polisher strips them."""
        fenced = "```markdown\n" + CLEAN_DOCTORAL_OUTPUT + "\n```"
        agent = PolishingAgent(_make_llm(fenced))
        result = await agent.polish(MESSY_DRAFT)
        assert not result.markdown.startswith("```")
        assert not result.markdown.rstrip().endswith("```")
        assert "## Introduction" in result.markdown


# ---------------------------------------------------------------------------
# Tests — section structure enforcement
# ---------------------------------------------------------------------------


class TestPolishingSectionStructure:
    def test_count_required_sections_full(self) -> None:
        """All six required sections should be detected."""
        assert _count_required_sections(CLEAN_DOCTORAL_OUTPUT) == 6

    def test_count_required_sections_partial(self) -> None:
        """A partial doctoral chapter counts what's actually present."""
        partial = "## Introduction\nfoo\n## Analysis\nbar"
        assert _count_required_sections(partial) == 2

    def test_count_required_sections_messy_draft(self) -> None:
        """The original messy draft has zero of the required headings."""
        assert _count_required_sections(MESSY_DRAFT) == 0

    def test_missing_sections_reported(self) -> None:
        """`missing_required_sections` should list all six on an empty draft."""
        missing = missing_required_sections("")
        assert len(missing) == 6
        assert "Introduction" in missing
        assert "Conclusion" in missing

    def test_missing_sections_empty_when_complete(self) -> None:
        """A complete doctoral chapter has no missing sections."""
        assert missing_required_sections(CLEAN_DOCTORAL_OUTPUT) == []

    @pytest.mark.asyncio
    async def test_polishing_flags_section_count_diff(self) -> None:
        """The polisher's sections_modified count reflects the structural gain."""
        agent = PolishingAgent(_make_llm(CLEAN_DOCTORAL_OUTPUT))
        result = await agent.polish(MESSY_DRAFT)
        # Messy draft had 0 required sections; output has 6.
        assert result.sections_modified == 6


# ---------------------------------------------------------------------------
# Tests — editorial-marker carry-over
# ---------------------------------------------------------------------------


class TestPolishingEditorialMarkers:
    @pytest.mark.asyncio
    async def test_dropped_flags_appended_to_output(self) -> None:
        """If the polisher drops an [ED:] marker, the agent appends it back."""
        # The LLM strips the marker — the agent must re-append.
        llm_output = CLEAN_DOCTORAL_OUTPUT  # no [ED: …] in this output
        agent = PolishingAgent(_make_llm(llm_output))

        flag = MethodologyFlag(
            type="anachronism",
            claim_id_or_excerpt="c1",
            issue="un-hedged 'free will'",
            scholarly_basis="Bobzien 1998",
            suggested_revision="use hekousion",
            severity="major",
        )
        result = await agent.polish(MESSY_DRAFT, carry_over_flags=[flag])
        assert "[ED: methodology was unable to resolve flag" in result.markdown
        assert "anachronism (major): un-hedged 'free will'" in result.markdown
        assert result.unresolved_flags_carried == 1

    @pytest.mark.asyncio
    async def test_preserved_flags_not_duplicated(self) -> None:
        """If the polisher already kept the marker, the agent doesn't add it again."""
        marker = (
            "[ED: methodology was unable to resolve flag — "
            "anachronism (major): un-hedged 'free will']"
        )
        llm_output = CLEAN_DOCTORAL_OUTPUT + "\n\n" + marker
        agent = PolishingAgent(_make_llm(llm_output))

        flag = MethodologyFlag(
            type="anachronism",
            claim_id_or_excerpt="c1",
            issue="un-hedged 'free will'",
            scholarly_basis="Bobzien 1998",
            suggested_revision="use hekousion",
            severity="major",
        )
        result = await agent.polish(MESSY_DRAFT, carry_over_flags=[flag])
        # Marker appears exactly once.
        assert result.markdown.count("[ED: methodology was unable to resolve flag") == 1


# ---------------------------------------------------------------------------
# Tests — SSE event emission
# ---------------------------------------------------------------------------


class TestPolishingEventEmission:
    @pytest.mark.asyncio
    async def test_completion_event_emitted(self) -> None:
        """One ``polishing_pass_complete`` event must fire after polishing."""
        events: list[dict[str, Any]] = []

        async def _on_event(event: dict[str, Any]) -> None:
            events.append(event)

        agent = PolishingAgent(_make_llm(CLEAN_DOCTORAL_OUTPUT), on_event=_on_event)
        result = await agent.polish(MESSY_DRAFT)
        completion_events = [
            e for e in events if e["type"] == "polishing_pass_complete"
        ]
        assert len(completion_events) == 1
        assert completion_events[0]["sections_modified"] == result.sections_modified
