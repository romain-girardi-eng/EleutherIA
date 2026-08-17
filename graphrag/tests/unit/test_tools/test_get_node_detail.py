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


# ---------------------------------------------- integrity_status gating


@pytest.mark.asyncio
async def test_integrity_flagged_description_is_withheld(mock_deps):
    # Greek fixture imported verbatim (audit-derived) — never composed.
    from ..test_programmatic_verify_quotes import FOREIGN_GREEK

    mock_deps.db.fetchval.return_value = 0
    mock_deps.node_lookup["passage_flagged_x2"] = {
        "id": "passage_flagged_x2",
        "label": "Flagged passage",
        "type": "passage",
        "description": f"Fabricated: {FOREIGN_GREEK}",
        "period": "Roman Imperial",
        "school": None,
        "metadata": {"integrity_status": "fabrication_confirmed_pending_fix"},
    }
    tool = GetNodeDetailTool(mock_deps)
    result = await tool.execute({"node_id": "passage_flagged_x2"})

    assert result.label == "Flagged passage"  # node stays inspectable
    assert result.description == ""
    # The agent can still see WHY the description is withheld.
    assert result.metadata.get("integrity_status") == (
        "fabrication_confirmed_pending_fix"
    )


@pytest.mark.asyncio
async def test_flagged_detail_does_not_reach_evidence(mock_deps):
    from eleutheria_graphrag.agents.evidence_collector import EvidenceCollector

    from ..test_programmatic_verify_quotes import FOREIGN_GREEK

    mock_deps.db.fetchval.return_value = 0
    mock_deps.node_lookup["passage_flagged_x2"] = {
        "id": "passage_flagged_x2",
        "label": "Flagged passage",
        "type": "passage",
        "description": f"Fabricated: {FOREIGN_GREEK}",
        "period": "Roman Imperial",
        "school": None,
        "metadata": {"integrity_status": "greek_unverified"},
    }
    tool = GetNodeDetailTool(mock_deps)
    result = await tool.execute({"node_id": "passage_flagged_x2"})

    collector = EvidenceCollector()
    collector.ingest("get_node_detail", {}, result)

    assert collector.primary_evidence == []
    assert collector.secondary_evidence[0].description == ""
    assert collector.secondary_evidence[0].evidence_tier == "discoverable_only"
