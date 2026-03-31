"""Tests for read_passages tool."""

import pytest

from eleutheria_graphrag.agents.tools.read_passages import ReadPassagesTool


@pytest.mark.asyncio
async def test_reads_passages_for_node(mock_deps):
    mock_deps.db.fetch.return_value = [
        {
            "passage_id": "p1",
            "title": "De Principiis",
            "author": "Origen",
            "canonical_ref": "III.1.1",
            "language": "grc",
            "text_content": "Περὶ αὐτεξουσίου...",
            "confidence": 0.95,
        },
        {
            "passage_id": "p2",
            "title": "De Principiis",
            "author": "Origen",
            "canonical_ref": "III.1.2",
            "language": "grc",
            "text_content": "Text about free will...",
            "confidence": 0.85,
        },
    ]

    tool = ReadPassagesTool(mock_deps)
    result = await tool.execute({"node_id": "person_origen", "limit": 5})

    assert result.node_label == "Origen of Alexandria"
    assert len(result.passages) == 2
    assert result.passages[0].confidence == 0.95
    assert result.passages[0].canonical_ref == "III.1.1"
    mock_deps.db.fetch.assert_called_once()


@pytest.mark.asyncio
async def test_empty_result_on_db_error(mock_deps):
    mock_deps.db.fetch.side_effect = Exception("DB connection failed")

    tool = ReadPassagesTool(mock_deps)
    result = await tool.execute({"node_id": "person_origen"})

    assert result.passages == []


@pytest.mark.asyncio
async def test_text_truncated_to_800(mock_deps):
    mock_deps.db.fetch.return_value = [
        {
            "passage_id": "p1",
            "title": "Long work",
            "author": "Author",
            "canonical_ref": "1.1",
            "language": "grc",
            "text_content": "x" * 2000,
            "confidence": 0.9,
        },
    ]

    tool = ReadPassagesTool(mock_deps)
    result = await tool.execute({"node_id": "test"})

    assert len(result.passages[0].text_content) <= 800


@pytest.mark.asyncio
async def test_tool_protocol(mock_deps):
    tool = ReadPassagesTool(mock_deps)
    assert tool.name == "read_passages"
    assert "node_id" in tool.parameters_schema["properties"]
