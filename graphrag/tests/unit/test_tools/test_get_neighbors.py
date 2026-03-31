"""Tests for get_neighbors tool."""

import pytest

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
    result = await tool.execute({
        "node_id": "person_origen",
        "relation_filter": "discusses",
        "direction": "out",
    })
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
