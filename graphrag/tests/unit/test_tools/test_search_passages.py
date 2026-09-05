"""Scoped retrieval must not discard a work's exact conventional locus."""

from unittest.mock import AsyncMock

import pytest

from eleutheria_graphrag.agents.tools.search_passages import SearchPassagesTool


@pytest.mark.asyncio
async def test_kg_work_filter_searches_its_canonical_locus_without_global_post_filter(
    mock_deps,
):
    mock_deps.search = AsyncMock()
    row = {
        "passage_id": "p1",
        "title": "De fato",
        "author": "Cicero",
        "canonical_ref": "Fat. 41",
        "language": "lat",
        "text_content": "Causarum enim aliae sunt perfectae et principales.",
    }
    mock_deps.db.fetch.return_value = [row]
    result = await SearchPassagesTool(mock_deps).execute(
        {"query": "41", "work_filter": "work_cicero"}
    )
    assert [p.passage_id for p in result.passages] == ["p1"]
    mock_deps.search.hybrid_search.assert_not_called()
    sql, *args = mock_deps.db.fetch.call_args.args
    assert "p.canonical_ref ILIKE $1" in sql
    assert "w.kg_work_id = $3" in sql
    assert args == ["%41%", 5, "work_cicero"]


@pytest.mark.asyncio
async def test_empty_hybrid_result_continues_to_corpus_search(mock_deps):
    mock_deps.search = AsyncMock()
    mock_deps.search.hybrid_search.return_value = []
    mock_deps.db.fetch.return_value = []
    await SearchPassagesTool(mock_deps).execute({"query": "perfectae"})
    mock_deps.db.fetch.assert_awaited_once()
