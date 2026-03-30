# graphrag/tests/test_retrieval_strategy.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from eleutheria_graphrag.services.retrieval_strategy import (
    VectorStrategy,
    SQLStrategy,
    RetrievalStrategy,
)


@pytest.mark.asyncio
async def test_vector_strategy_calls_qdrant():
    """VectorStrategy embeds queries and searches Qdrant."""
    mock_deps = MagicMock()
    mock_deps.qdrant.search_nodes = AsyncMock(return_value=[
        MagicMock(id="node_1", score=0.9, payload={"type": "concept"}),
        MagicMock(id="node_2", score=0.8, payload={"type": "person"}),
    ])

    async def mock_embed(deps, query):
        return [0.1] * 3072

    strategy = VectorStrategy(embed_fn=mock_embed)
    seeds, anchors = await strategy.discover_seeds(
        queries=["Stoic fate"],
        deps=mock_deps,
        node_limit=20,
    )
    assert "node_1" in seeds
    assert "node_2" in seeds
    mock_deps.qdrant.search_nodes.assert_called_once()


@pytest.mark.asyncio
async def test_vector_strategy_handles_qdrant_failure():
    """VectorStrategy returns empty on Qdrant failure."""
    mock_deps = MagicMock()
    mock_deps.qdrant.search_nodes = AsyncMock(side_effect=ConnectionError("Qdrant down"))

    async def mock_embed(deps, query):
        return [0.1] * 3072

    strategy = VectorStrategy(embed_fn=mock_embed)
    seeds, anchors = await strategy.discover_seeds(
        queries=["Stoic fate"],
        deps=mock_deps,
        node_limit=20,
    )
    assert seeds == []
    assert anchors == []


@pytest.mark.asyncio
async def test_vector_strategy_handles_embedding_failure():
    """VectorStrategy returns empty when embedding fails (e.g., Gemini 429)."""
    mock_deps = MagicMock()

    async def mock_embed_fail(deps, query):
        raise Exception("429 Too Many Requests")

    strategy = VectorStrategy(embed_fn=mock_embed_fail)
    seeds, anchors = await strategy.discover_seeds(
        queries=["Stoic fate"],
        deps=mock_deps,
        node_limit=20,
    )
    assert seeds == []
    assert anchors == []
