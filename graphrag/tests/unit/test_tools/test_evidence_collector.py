"""Tests for EvidenceCollector."""

import pytest

from eleutheria_graphrag.agents.evidence_collector import EvidenceCollector
from eleutheria_graphrag.agents.state import RAGState
from eleutheria_graphrag.agents.tools.get_neighbors import GetNeighborsResult, EdgeSummary
from eleutheria_graphrag.agents.tools.search_nodes import SearchNodesResult, NodeSummary
from eleutheria_graphrag.agents.tools.read_passages import ReadPassagesResult, PassageSummary


def test_ingest_search_nodes():
    collector = EvidenceCollector()
    result = SearchNodesResult(
        nodes=[
            NodeSummary(
                node_id="person_origen",
                label="Origen",
                type="person",
                description="Theologian",
                score=0.9,
            ),
        ],
        total_found=1,
    )

    collector.ingest("search_nodes", {"query": "Origen"}, result)

    assert "person_origen" in collector.seen_node_ids
    assert len(collector.primary_evidence) == 1
    assert collector.primary_evidence[0].id == "person_origen"
    assert "person_origen" in collector.seed_node_ids


def test_ingest_get_neighbors():
    collector = EvidenceCollector()
    result = GetNeighborsResult(
        center_node="person_origen",
        center_label="Origen",
        edges=[
            EdgeSummary(
                edge_node_id="concept_autexousion",
                label="Autexousion",
                type="concept",
                relation="discusses",
                direction="outgoing",
            ),
        ],
    )

    collector.ingest("get_neighbors", {"node_id": "person_origen"}, result)

    assert "concept_autexousion" in collector.seen_node_ids
    assert len(collector.secondary_evidence) == 1
    assert "concept_autexousion" in collector.context_node_ids


def test_ingest_passages():
    collector = EvidenceCollector()
    result = ReadPassagesResult(
        node_id="person_origen",
        node_label="Origen",
        passages=[
            PassageSummary(
                passage_id="p1",
                work_title="De Principiis",
                author="Origen",
                canonical_ref="III.1.1",
                text_content="Περὶ αὐτεξουσίου",
                confidence=0.95,
            ),
        ],
    )

    collector.ingest("read_passages", {"node_id": "person_origen"}, result)

    assert "p1" in collector.seen_passage_ids
    assert len(collector.evidence_bundles) == 1
    assert collector.evidence_bundles[0].work_title == "De Principiis"
    assert collector.evidence_bundles[0].original_text == "Περὶ αὐτεξουσίου"


def test_deduplication():
    collector = EvidenceCollector()

    # Ingest same node twice
    result1 = SearchNodesResult(
        nodes=[NodeSummary(node_id="n1", label="Node 1", type="concept", description="A concept", score=0.9)],
        total_found=1,
    )
    result2 = GetNeighborsResult(
        center_node="x",
        center_label="X",
        edges=[EdgeSummary(edge_node_id="n1", label="Node 1", type="concept", relation="discusses", direction="outgoing")],
    )

    collector.ingest("search_nodes", {}, result1)
    collector.ingest("get_neighbors", {}, result2)

    # Should only appear once
    assert len(collector.primary_evidence) == 1
    assert len(collector.secondary_evidence) == 0  # Deduplicated


def test_populate_state():
    collector = EvidenceCollector()

    # Add some evidence
    collector.ingest("search_nodes", {}, SearchNodesResult(
        nodes=[NodeSummary(node_id="n1", label="Node", type="person", description="A person", score=0.9)],
        total_found=1,
    ))
    collector.ingest("read_passages", {}, ReadPassagesResult(
        node_id="n1",
        node_label="Node",
        passages=[PassageSummary(passage_id="p1", work_title="Work", text_content="Text", confidence=0.9)],
    ))
    collector.record_call("search_nodes", {"query": "test"}, "testing", "1 node found", node_count=1)

    state = RAGState(question="Test question")
    collector.populate_state(state)

    assert len(state.primary_evidence) == 1
    assert len(state.evidence_bundles) == 1
    assert state.passages_used == 1
    # context_pack is left empty — DraftClaimLedger builds it from state
    assert state.context_pack.prompt_context == ""
    assert len(state.research_notebook.tool_calls) == 1
