"""Tests for get_node_detail tool."""

import pytest

from eleutheria_graphrag.agents.tools.get_node_detail import GetNodeDetailTool


@pytest.mark.asyncio
async def test_returns_full_detail(mock_deps):
    mock_deps.db.fetchval.return_value = 5

    tool = GetNodeDetailTool(mock_deps)
    result = await tool.execute({"node_id": "person_origen"})

    assert result.label == "Origen of Alexandria"
    assert result.type == "person"
    assert result.period == "Roman Imperial"
    assert "free will" in result.description
    assert result.neighbor_count > 0  # Has outgoing + incoming edges
    assert result.passage_count == 5


@pytest.mark.asyncio
async def test_not_found(mock_deps):
    tool = GetNodeDetailTool(mock_deps)
    result = await tool.execute({"node_id": "nonexistent_node"})

    assert result.label == "(not found)"
    assert "not found" in result.description


@pytest.mark.asyncio
async def test_db_error_returns_zero_passages(mock_deps):
    mock_deps.db.fetchval.side_effect = Exception("DB error")

    tool = GetNodeDetailTool(mock_deps)
    result = await tool.execute({"node_id": "person_plato"})

    assert result.passage_count == 0
    assert result.label == "Plato"
