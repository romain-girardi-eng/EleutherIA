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


# ---------------------------------------------- integrity_status gating
# Greek fixture is imported verbatim from test_programmatic_verify_quotes
# (itself audit-derived from data/eval/must_not_appear.jsonl) — never
# composed by hand.


def _flagged_node(description: str) -> dict:
    return {
        "id": "argument_flagged_x1",
        "label": "Flagged fabrication argument",
        "type": "argument",
        "description": description,
        "period": "Roman Imperial",
        "school": None,
        "metadata": {"integrity_status": "greek_unverified"},
    }


@pytest.mark.asyncio
async def test_integrity_flagged_description_is_blanked(mock_deps):
    from ..test_programmatic_verify_quotes import FOREIGN_GREEK

    mock_deps.node_lookup["argument_flagged_x1"] = _flagged_node(
        f"Fabricated quotation pending fix: {FOREIGN_GREEK}"
    )
    tool = SearchNodesTool(mock_deps)
    result = await tool.execute({"query": "Flagged fabrication argument"})

    hit = next(n for n in result.nodes if n.node_id == "argument_flagged_x1")
    # Node stays findable/traversable, but its description is not citable.
    assert hit.label == "Flagged fabrication argument"
    assert hit.description == ""


@pytest.mark.asyncio
async def test_flagged_node_cannot_whitelist_its_own_greek(mock_deps):
    """End-to-end react-path regression: a flagged node retrieved via
    search_nodes must NOT put its (fabricated) Greek into the text
    verifier's evidence whitelist."""
    from eleutheria_graphrag.agents.evidence_collector import EvidenceCollector
    from eleutheria_graphrag.agents.scholarly_agent import _collect_evidence_texts
    from eleutheria_graphrag.agents.state import RAGState

    from ..test_programmatic_verify_quotes import FOREIGN_GREEK

    mock_deps.node_lookup["argument_flagged_x1"] = _flagged_node(
        f"Fabricated quotation pending fix: {FOREIGN_GREEK}"
    )
    tool = SearchNodesTool(mock_deps)
    result = await tool.execute({"query": "Flagged fabrication argument"})

    collector = EvidenceCollector()
    collector.ingest("search_nodes", {}, result)
    state = RAGState(question="q")
    collector.populate_state(state)

    texts = _collect_evidence_texts(state)
    assert all(FOREIGN_GREEK not in text for text in texts)
