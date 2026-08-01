"""Tests for explore_subgraph tool (PPR-based exploration)."""

from typing import Any
from unittest.mock import AsyncMock

import pytest

from eleutheria_graphrag.agents.dependencies import Deps
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


@pytest.mark.asyncio
async def test_db_fallback_when_in_memory_graph_cold():
    """When `node_lookup` is empty (no in-memory graph warmed), the tool
    must fall back to the bounded Postgres k-hop CTE per seed instead of
    always reporting zero results.
    """

    def _node(node_id: str, node_type: str = "concept") -> dict[str, Any]:
        return {
            "id": node_id,
            "label": node_id,
            "type": node_type,
            "description": None,
            "period": None,
            "school": None,
            "metadata": {},
        }

    async def _fake_fetch(query: str, *args: Any) -> list[dict[str, Any]]:
        if "WITH RECURSIVE khop" in query:
            return [{"node_id": "concept_fate", "hop": 1}]
        if "FROM free_will.kg_nodes" in query:
            # `all_ids` param is args[0] for the ANY($1) queries.
            ids = args[0]
            return [_node(i) for i in ids if i in {"person_origen", "concept_fate"}]
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

    tool = ExploreSubgraphTool(cold_deps)
    result = await tool.execute({"seed_node_ids": ["person_origen"], "top_k": 10})

    assert result.seed_count == 1
    ids = [n.node_id for n in result.nodes]
    assert ids == ["concept_fate"]
    assert "person_origen" not in ids


@pytest.mark.asyncio
async def test_db_fallback_no_db_returns_empty():
    cold_deps = Deps(db=None, llm=AsyncMock())  # type: ignore[arg-type]
    tool = ExploreSubgraphTool(cold_deps)
    result = await tool.execute({"seed_node_ids": ["person_origen"]})
    assert result.nodes == []
    assert result.seed_count == 0
