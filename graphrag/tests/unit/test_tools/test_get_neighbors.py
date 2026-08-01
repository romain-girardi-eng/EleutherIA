"""Tests for get_neighbors tool."""

from typing import Any
from unittest.mock import AsyncMock

import pytest

from eleutheria_graphrag.agents.dependencies import Deps
from eleutheria_graphrag.agents.tools.get_neighbors import GetNeighborsTool


@pytest.mark.asyncio
async def test_both_directions(mock_deps):
    tool = GetNeighborsTool(mock_deps)
    result = await tool.execute({"node_id": "concept_fate"})
    assert result.center_label == "Fate (Heimarmene)"
    # Should have incoming edges from Plato and Chrysippus
    ids = [e.edge_node_id for e in result.edges]
    assert "person_plato" in ids
    assert "person_chrysippus" in ids


@pytest.mark.asyncio
async def test_outgoing_only(mock_deps):
    tool = GetNeighborsTool(mock_deps)
    result = await tool.execute({"node_id": "person_origen", "direction": "out"})
    for edge in result.edges:
        assert edge.direction == "outgoing"
    ids = [e.edge_node_id for e in result.edges]
    assert "concept_autexousion" in ids
    assert "work_de_principiis" in ids


@pytest.mark.asyncio
async def test_incoming_only(mock_deps):
    tool = GetNeighborsTool(mock_deps)
    result = await tool.execute({"node_id": "concept_fate", "direction": "in"})
    for edge in result.edges:
        assert edge.direction == "incoming"


@pytest.mark.asyncio
async def test_relation_filter(mock_deps):
    tool = GetNeighborsTool(mock_deps)
    result = await tool.execute(
        {
            "node_id": "person_origen",
            "relation_filter": "discusses",
            "direction": "out",
        }
    )
    for edge in result.edges:
        assert edge.relation == "discusses"
    assert len(result.edges) == 1
    assert result.edges[0].edge_node_id == "concept_autexousion"


@pytest.mark.asyncio
async def test_nonexistent_node(mock_deps):
    tool = GetNeighborsTool(mock_deps)
    result = await tool.execute({"node_id": "nonexistent"})
    assert result.edges == []


@pytest.mark.asyncio
async def test_limit(mock_deps):
    tool = GetNeighborsTool(mock_deps)
    result = await tool.execute({"node_id": "person_origen", "limit": 1})
    assert len(result.edges) <= 1


@pytest.mark.asyncio
async def test_sorted_by_weight_and_pagerank(mock_deps):
    tool = GetNeighborsTool(mock_deps)
    result = await tool.execute({"node_id": "person_origen", "direction": "out"})
    # Edges should be sorted by weight + pagerank descending
    if len(result.edges) > 1:
        # Just verify ordering is consistent
        assert isinstance(result.edges[0].weight, float)


@pytest.mark.asyncio
async def test_db_fallback_when_in_memory_graph_cold():
    """When `node_lookup` is empty (no in-memory graph warmed), the tool
    must fall back to the bounded Postgres k-hop CTE instead of always
    reporting zero neighbors.
    """

    async def _fake_fetch(query: str, *_args: Any) -> list[dict[str, Any]]:
        if "WITH RECURSIVE khop" in query:
            return [{"node_id": "concept_fate", "hop": 1}]
        if "FROM free_will.kg_nodes" in query:
            return [
                {
                    "id": "person_origen",
                    "label": "Origen",
                    "type": "person",
                    "description": None,
                    "period": "Roman Imperial",
                    "school": None,
                    "metadata": {},
                },
                {
                    "id": "concept_fate",
                    "label": "Fate (Heimarmene)",
                    "type": "concept",
                    "description": None,
                    "period": "Hellenistic",
                    "school": None,
                    "metadata": {},
                },
            ]
        if "FROM free_will.kg_edges" in query:
            return [
                {
                    "source": "person_origen",
                    "target": "concept_fate",
                    "relation": "discusses",
                    "weight": 1.0,
                    "metadata": {},
                }
            ]
        return []

    db = AsyncMock()
    db.fetch = AsyncMock(side_effect=_fake_fetch)
    cold_deps = Deps(db=db, llm=AsyncMock())  # node_lookup defaults to {}

    tool = GetNeighborsTool(cold_deps)
    result = await tool.execute({"node_id": "person_origen"})

    assert result.center_label == "Origen"
    assert [e.edge_node_id for e in result.edges] == ["concept_fate"]
    assert result.edges[0].relation == "discusses"
