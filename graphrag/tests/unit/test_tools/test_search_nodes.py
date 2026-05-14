"""Tests for search_nodes tool."""

import pytest

from eleutheria_graphrag.agents.tools.search_nodes import SearchNodesTool


@pytest.mark.asyncio
async def test_exact_label_match(mock_deps):
    tool = SearchNodesTool(mock_deps)
    result = await tool.execute({"query": "Origen of Alexandria"})
    assert result.total_found >= 1
    assert result.nodes[0].node_id == "person_origen"
    assert result.nodes[0].score > 0.8


@pytest.mark.asyncio
async def test_partial_label_match(mock_deps):
    tool = SearchNodesTool(mock_deps)
    result = await tool.execute({"query": "Origen"})
    assert result.total_found >= 1
    # Origen should be top result
    ids = [n.node_id for n in result.nodes]
    assert "person_origen" in ids


@pytest.mark.asyncio
async def test_type_filter(mock_deps):
    tool = SearchNodesTool(mock_deps)
    result = await tool.execute({"query": "fate", "type_filter": "concept"})
    for node in result.nodes:
        assert node.type == "concept"


@pytest.mark.asyncio
async def test_period_filter(mock_deps):
    tool = SearchNodesTool(mock_deps)
    result = await tool.execute(
        {"query": "philosopher", "period_filter": "Hellenistic"}
    )
    for node in result.nodes:
        assert node.period == "Hellenistic"


@pytest.mark.asyncio
async def test_no_results(mock_deps):
    tool = SearchNodesTool(mock_deps)
    result = await tool.execute({"query": "xyznonexistent"})
    assert result.total_found == 0
    assert result.nodes == []


@pytest.mark.asyncio
async def test_description_truncated(mock_deps):
    tool = SearchNodesTool(mock_deps)
    result = await tool.execute({"query": "Plato"})
    for node in result.nodes:
        assert len(node.description) <= 200


@pytest.mark.asyncio
async def test_limit_respected(mock_deps):
    tool = SearchNodesTool(mock_deps)
    result = await tool.execute({"query": "a", "limit": 2})
    assert len(result.nodes) <= 2


@pytest.mark.asyncio
async def test_tool_protocol(mock_deps):
    tool = SearchNodesTool(mock_deps)
    assert tool.name == "search_nodes"
    assert isinstance(tool.description, str)
    assert "query" in tool.parameters_schema["properties"]
