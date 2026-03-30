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


@pytest.mark.asyncio
async def test_sql_strategy_step1_passage_citations():
    """Step 1: finds seeds via kg_nodes label match + passage_citations."""
    mock_deps = MagicMock()
    mock_deps.db = AsyncMock()
    mock_deps.db.fetch = AsyncMock(side_effect=[
        [{"node_id": "concept_fate"}, {"node_id": "person_chrysippus"}],
        [
            {"passage_id": "p1", "kg_node_id": "concept_fate", "confidence": 0.9},
            {"passage_id": "p2", "kg_node_id": "concept_fate", "confidence": 0.8},
            {"passage_id": "p3", "kg_node_id": "person_chrysippus", "confidence": 0.85},
            {"passage_id": "p4", "kg_node_id": "person_chrysippus", "confidence": 0.7},
        ],
    ])
    mock_deps.outgoing_edges = {"concept_fate": [{"target": "concept_determinism", "relation": "related_to"}]}
    mock_deps.incoming_edges = {}
    mock_deps.search = None

    strategy = SQLStrategy(min_bundles=4)
    seeds, anchors = await strategy.discover_seeds(
        queries=["Stoic fate"],
        deps=mock_deps,
        node_limit=100,
    )
    assert "concept_fate" in seeds
    assert "person_chrysippus" in seeds
    assert "concept_determinism" in seeds  # 1-hop expansion
    assert len(anchors) >= 2


@pytest.mark.asyncio
async def test_sql_strategy_escalates_to_step2():
    """When step 1 finds < min_bundles, escalates to HybridSearch."""
    mock_deps = MagicMock()
    mock_deps.db = AsyncMock()
    mock_deps.db.fetch = AsyncMock(side_effect=[
        [{"node_id": "concept_fate"}],
        [{"passage_id": "p1", "kg_node_id": "concept_fate", "confidence": 0.9}],
    ])
    mock_deps.outgoing_edges = {}
    mock_deps.incoming_edges = {}
    mock_search = AsyncMock()
    mock_search.hybrid_search = AsyncMock(return_value=[
        {"passage_id": "p2", "work_id": "w1", "text_content": "about fate..."},
        {"passage_id": "p3", "work_id": "w1", "text_content": "heimarmene..."},
        {"passage_id": "p4", "work_id": "w2", "text_content": "Chrysippus argues..."},
    ])
    mock_deps.search = mock_search

    strategy = SQLStrategy(min_bundles=4)
    seeds, anchors = await strategy.discover_seeds(
        queries=["Stoic fate"],
        deps=mock_deps,
        node_limit=100,
    )
    mock_search.hybrid_search.assert_called()
    assert len(anchors) >= 1


@pytest.mark.asyncio
async def test_sql_strategy_returns_empty_gracefully():
    """SQLStrategy returns empty lists when nothing matches."""
    mock_deps = MagicMock()
    mock_deps.db = AsyncMock()
    mock_deps.db.fetch = AsyncMock(return_value=[])
    mock_deps.outgoing_edges = {}
    mock_deps.incoming_edges = {}
    mock_deps.search = None

    strategy = SQLStrategy(min_bundles=4)
    seeds, anchors = await strategy.discover_seeds(
        queries=["nonexistent topic xyz"],
        deps=mock_deps,
        node_limit=100,
    )
    assert seeds == []
    assert anchors == []
