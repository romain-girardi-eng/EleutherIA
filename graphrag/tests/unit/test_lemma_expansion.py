"""Unit tests for LemmaExpander."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from eleutheria_graphrag.services.lemma_expansion import LemmaExpander


@pytest.mark.asyncio
async def test_expand_returns_tokens_plus_llm_lemmas() -> None:
    llm = AsyncMock()
    llm.generate = AsyncMock(
        return_value='{"lemmas": ["hekousi", "prohaires", "voluntary"]}'
    )
    expander = LemmaExpander(llm=llm)

    result = await expander.expand("voluntary action in Aristotle", max_lemmas=8)

    # Original tokens preserved
    assert "voluntary" in [r.lower() for r in result]
    assert "Aristotle" in result
    # LLM-derived lemmas added
    assert "hekousi" in result
    assert "prohaires" in result
    llm.generate.assert_awaited_once()


@pytest.mark.asyncio
async def test_expand_dedups_case_insensitively() -> None:
    llm = AsyncMock()
    # LLM returns "voluntary" — also in the query — should not duplicate.
    llm.generate = AsyncMock(
        return_value='{"lemmas": ["VOLUNTARY", "hekousi", "hekousi"]}'
    )
    expander = LemmaExpander(llm=llm)

    result = await expander.expand("voluntary action", max_lemmas=8)
    lowered = [r.lower() for r in result]
    assert lowered.count("voluntary") == 1
    assert lowered.count("hekousi") == 1


@pytest.mark.asyncio
async def test_expand_caches_per_query() -> None:
    llm = AsyncMock()
    llm.generate = AsyncMock(return_value='{"lemmas": ["fat"]}')
    expander = LemmaExpander(llm=llm)

    await expander.expand("Stoic fate")
    await expander.expand("Stoic fate")
    # Second call must be served from cache.
    assert llm.generate.await_count == 1


@pytest.mark.asyncio
async def test_expand_handles_llm_failure_gracefully() -> None:
    llm = AsyncMock()
    llm.generate = AsyncMock(side_effect=RuntimeError("LLM down"))
    expander = LemmaExpander(llm=llm)

    result = await expander.expand("voluntary action", max_lemmas=8)
    # Falls back to original tokens.
    assert "voluntary" in result
    assert "action" in result


@pytest.mark.asyncio
async def test_expand_handles_malformed_json() -> None:
    llm = AsyncMock()
    llm.generate = AsyncMock(return_value="not json at all")
    expander = LemmaExpander(llm=llm)

    result = await expander.expand("voluntary action", max_lemmas=8)
    assert "voluntary" in result
    assert "action" in result


@pytest.mark.asyncio
async def test_expand_respects_max_lemmas() -> None:
    llm = AsyncMock()
    llm.generate = AsyncMock(
        return_value='{"lemmas": ["a1", "a2", "a3", "a4", "a5", "a6", "a7", "a8", "a9"]}'
    )
    expander = LemmaExpander(llm=llm)

    result = await expander.expand("fate", max_lemmas=3)
    # Up to 3 LLM lemmas, but original token(s) also included.
    llm_added = [r for r in result if r.startswith("a")]
    assert len(llm_added) <= 3


@pytest.mark.asyncio
async def test_expand_empty_query_returns_empty() -> None:
    llm = AsyncMock()
    expander = LemmaExpander(llm=llm)
    assert await expander.expand("") == []
    assert await expander.expand("   ") == []
    llm.generate.assert_not_awaited()
