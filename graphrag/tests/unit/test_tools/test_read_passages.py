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
async def test_text_kept_in_full(mock_deps):
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

    assert len(result.passages[0].text_content) == 2000


@pytest.mark.asyncio
async def test_tool_protocol(mock_deps):
    tool = ReadPassagesTool(mock_deps)
    assert tool.name == "read_passages"
    assert "node_id" in tool.parameters_schema["properties"]


_PASSAGE_ROW = {
    "passage_id": "p1",
    "title": "De Principiis",
    "author": "Origen",
    "canonical_ref": "III.1.1",
    "language": "grc",
    "text_content": "Περὶ αὐτεξουσίου...",
    "confidence": 0.95,
}


@pytest.mark.asyncio
async def test_machine_translation_provenance_exposed(mock_deps):
    mock_deps.db.fetch.return_value = [dict(_PASSAGE_ROW)]
    mock_deps.node_lookup["person_origen_en"] = {
        "id": "person_origen_en",
        "label": "Origen of Alexandria (English)",
        "type": "passage",
        "description": "English rendering of the passage.",
        "metadata": {"language": "eng", "translation_type": "machine"},
    }

    tool = ReadPassagesTool(mock_deps)
    result = await tool.execute({"node_id": "person_origen", "limit": 1})

    passage = result.passages[0]
    assert passage.translation == "English rendering of the passage."
    assert passage.translation_type == "machine"
    assert passage.translation_ai_generated is True


@pytest.mark.asyncio
async def test_translation_without_provenance_is_unknown_not_scholarly(mock_deps):
    mock_deps.db.fetch.return_value = [dict(_PASSAGE_ROW)]
    mock_deps.node_lookup["person_origen_en"] = {
        "id": "person_origen_en",
        "label": "Origen of Alexandria (English)",
        "type": "passage",
        "description": "English rendering of the passage.",
        "metadata": {"language": "eng"},
    }

    tool = ReadPassagesTool(mock_deps)
    result = await tool.execute({"node_id": "person_origen", "limit": 1})

    passage = result.passages[0]
    assert passage.translation == "English rendering of the passage."
    assert passage.translation_type is None
    assert passage.translation_ai_generated is None


@pytest.mark.asyncio
async def test_no_translation_means_no_provenance_fields(mock_deps):
    mock_deps.db.fetch.return_value = [dict(_PASSAGE_ROW)]

    tool = ReadPassagesTool(mock_deps)
    result = await tool.execute({"node_id": "person_origen", "limit": 1})

    passage = result.passages[0]
    assert passage.translation is None
    assert passage.translation_type is None
    assert passage.translation_ai_generated is None


@pytest.mark.asyncio
async def test_snapshot_translation_carries_provenance(mock_deps):
    mock_deps.db.fetch.return_value = [dict(_PASSAGE_ROW)]
    mock_deps.node_lookup["passage_dp_31"] = {
        "id": "passage_dp_31",
        "label": "De Principiis III.1",
        "type": "passage",
        "description": "Περὶ αὐτεξουσίου...",
        "metadata": {"language": "grc", "passage_id": "p1"},
    }
    mock_deps.node_lookup["passage_dp_31_en"] = {
        "id": "passage_dp_31_en",
        "label": "De Principiis III.1 (English)",
        "type": "passage",
        "description": "English rendering of the passage.",
        "metadata": {"language": "eng", "translation_type": "machine"},
    }
    mock_deps.incoming_edges["passage_dp_31"] = [
        {
            "source": "passage_dp_31_en",
            "target": "passage_dp_31",
            "relation": "translation_of",
            "weight": 1.0,
            "metadata": {},
            "description": "",
        },
    ]

    tool = ReadPassagesTool(mock_deps)
    result = await tool.execute({"node_id": "person_origen", "limit": 1})

    passage = result.passages[0]
    assert passage.translation == "English rendering of the passage."
    assert passage.translation_type == "machine"
    assert passage.translation_ai_generated is True
