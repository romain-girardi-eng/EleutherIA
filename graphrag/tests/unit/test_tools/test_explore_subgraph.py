"""Tests for explore_subgraph tool (PPR-based exploration)."""

import pytest

from eleutheria_graphrag.agents.tools.explore_subgraph import ExploreSubgraphTool


@pytest.mark.asyncio
async def test_finds_connected_nodes(mock_deps):
    tool = ExploreSubgraphTool(mock_deps)
    result = await tool.execute(
        {
            "seed_node_ids": ["person_origen"],
            "top_k": 10,
        }
    )

    # Should find nodes connected to Origen
    ids = [n.node_id for n in result.nodes]
    # Origen's direct connections should appear
    assert (
        "concept_autexousion" in ids
        or "work_de_principiis" in ids
        or "school_middle_platonism" in ids
    )
    # Seeds should be excluded from results
    assert "person_origen" not in ids
    assert result.seed_count == 1


@pytest.mark.asyncio
async def test_multiple_seeds(mock_deps):
    tool = ExploreSubgraphTool(mock_deps)
    result = await tool.execute(
        {
            "seed_node_ids": ["person_origen", "person_plato"],
            "top_k": 10,
        }
    )

    assert result.seed_count == 2
    ids = [n.node_id for n in result.nodes]
    # Neither seed should be in results
    assert "person_origen" not in ids
    assert "person_plato" not in ids
    # Should find shared connections
    assert len(result.nodes) > 0


@pytest.mark.asyncio
async def test_invalid_seeds(mock_deps):
    tool = ExploreSubgraphTool(mock_deps)
    result = await tool.execute(
        {
            "seed_node_ids": ["nonexistent_1", "nonexistent_2"],
        }
    )

    assert result.seed_count == 0
    assert result.nodes == []


@pytest.mark.asyncio
async def test_excludes_passage_nodes(mock_deps):
    # Add a passage node to the KG
    mock_deps.node_lookup["passage_test"] = {
        "id": "passage_test",
        "label": "Test passage",
        "type": "passage",
        "description": "Some text",
        "period": None,
        "school": None,
        "metadata": {},
    }
    mock_deps.outgoing_edges.setdefault("person_origen", []).append(
        {
            "source": "person_origen",
            "target": "passage_test",
            "relation": "evidenced_by",
            "weight": 1.0,
            "metadata": {},
            "description": "",
        }
    )

    tool = ExploreSubgraphTool(mock_deps)
    result = await tool.execute(
        {
            "seed_node_ids": ["person_origen"],
            "top_k": 20,
        }
    )

    ids = [n.node_id for n in result.nodes]
    assert "passage_test" not in ids


@pytest.mark.asyncio
async def test_top_k_limit(mock_deps):
    tool = ExploreSubgraphTool(mock_deps)
    result = await tool.execute(
        {
            "seed_node_ids": ["person_origen"],
            "top_k": 5,  # Minimum is 5
        }
    )

    assert len(result.nodes) <= 5


@pytest.mark.asyncio
async def test_distance_from_seed(mock_deps):
    tool = ExploreSubgraphTool(mock_deps)
    result = await tool.execute(
        {
            "seed_node_ids": ["person_origen"],
            "top_k": 20,
        }
    )

    for node in result.nodes:
        assert node.distance_from_seed >= 1
