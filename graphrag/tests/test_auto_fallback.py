"""Tests for auto-fallback: VectorStrategy -> SQLStrategy when vector returns empty."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from eleutheria_graphrag.services.retrieval_strategy import SQLStrategy, VectorStrategy


@pytest.mark.asyncio
async def test_vector_strategy_returns_empty_on_embed_failure():
    """VectorStrategy gracefully returns empty when embed_fn raises."""
    mock_deps = MagicMock()

    async def failing_embed(_deps: MagicMock, _query: str) -> list[float]:
        raise Exception("429 spending cap exceeded")

    vector = VectorStrategy(embed_fn=failing_embed)
    seeds, anchors = await vector.discover_seeds(["Stoic fate"], mock_deps)
    assert seeds == []
    assert anchors == []


@pytest.mark.asyncio
async def test_sql_strategy_finds_seeds_after_vector_failure():
    """In auto mode, if VectorStrategy returns empty, SQLStrategy can still find seeds."""
    mock_deps = MagicMock()
    mock_deps.db = AsyncMock()
    mock_deps.db.fetch = AsyncMock(side_effect=[
        # Step 1: label match
        [{"node_id": "concept_fate"}],
        # Step 1: fetch_citations
        [
            {"passage_id": "p1", "kg_node_id": "concept_fate", "confidence": 0.9},
            {"passage_id": "p2", "kg_node_id": "concept_fate", "confidence": 0.8},
            {"passage_id": "p3", "kg_node_id": "concept_fate", "confidence": 0.7},
            {"passage_id": "p4", "kg_node_id": "concept_fate", "confidence": 0.6},
        ],
    ])
    mock_deps.outgoing_edges = {}
    mock_deps.incoming_edges = {}
    mock_deps.search = None

    sql = SQLStrategy(min_bundles=1)
    seeds, anchors = await sql.discover_seeds(["Stoic fate"], mock_deps)
    assert "concept_fate" in seeds
    assert len(anchors) >= 1


@pytest.mark.asyncio
async def test_auto_fallback_sequence():
    """Full auto-fallback: VectorStrategy fails, then SQLStrategy succeeds."""
    mock_deps = MagicMock()

    # Vector strategy with failing embed
    async def failing_embed(_deps: MagicMock, _query: str) -> list[float]:
        raise Exception("429 spending cap exceeded")

    vector = VectorStrategy(embed_fn=failing_embed)
    seeds, _ = await vector.discover_seeds(["Stoic fate"], mock_deps)
    assert seeds == [], "VectorStrategy should return empty on embed failure"

    # Now try SQL fallback
    mock_deps.db = AsyncMock()
    mock_deps.db.fetch = AsyncMock(side_effect=[
        [{"node_id": "concept_fate"}, {"node_id": "concept_determinism"}],
        [
            {"passage_id": "p1", "kg_node_id": "concept_fate", "confidence": 0.9},
            {"passage_id": "p2", "kg_node_id": "concept_fate", "confidence": 0.8},
            {"passage_id": "p3", "kg_node_id": "concept_determinism", "confidence": 0.7},
            {"passage_id": "p4", "kg_node_id": "concept_determinism", "confidence": 0.6},
        ],
    ])
    mock_deps.outgoing_edges = {}
    mock_deps.incoming_edges = {}
    mock_deps.search = None

    sql = SQLStrategy(min_bundles=2)
    seeds2, anchors2 = await sql.discover_seeds(["Stoic fate"], mock_deps)
    assert "concept_fate" in seeds2
    assert "concept_determinism" in seeds2
    assert len(anchors2) >= 2
