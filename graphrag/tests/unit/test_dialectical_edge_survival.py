"""Scholar-RAG M0b — dialectical edges survive ingestion into RAGState.

Regression guard for failure-map F1 (the "0 edges used" root cause):
``EvidenceCollector._ingest_get_neighbors`` used to keep only ``edge_node_id``
and drop ``relation`` + ``direction`` entirely, so ``opposes`` / ``critiques`` /
``responds_to`` never reached the synthesis layer. These tests prove that a
``get_neighbors`` (and a future edge-bearing ``explore_subgraph``) result now
populates ``RAGState.dialectical_edges`` with both endpoints + relation +
direction, and that non-dialectical relations are ignored.
"""

from __future__ import annotations

from eleutheria_graphrag.agents.evidence_collector import EvidenceCollector
from eleutheria_graphrag.agents.state import (
    DIALECTICAL_RELATIONS,
    DialecticalEdge,
    RAGState,
)
from eleutheria_graphrag.agents.tools.get_neighbors import (
    EdgeSummary,
    GetNeighborsResult,
)


def _state() -> RAGState:
    state = RAGState()
    state.question = "test"
    return state


def test_dialectical_edges_default_empty() -> None:
    assert RAGState().dialectical_edges == []


def test_get_neighbors_outgoing_edge_survives() -> None:
    """An outgoing dialectical edge keeps center as source, neighbor as target."""
    collector = EvidenceCollector()
    result = GetNeighborsResult(
        center_node="scholar_position_frede_will_originates_epictetus",
        center_label="Frede: will originates in Epictetus",
        edges=[
            EdgeSummary(
                edge_node_id="scholar_position_dihle_will_christian_innovation",
                label="Dihle: will is a Christian innovation",
                type="position",
                relation="opposes",
                direction="outgoing",
                weight=1.0,
            ),
        ],
    )
    collector.ingest("get_neighbors", {}, result)

    state = _state()
    collector.populate_state(state)

    assert len(state.dialectical_edges) == 1
    edge = state.dialectical_edges[0]
    assert isinstance(edge, DialecticalEdge)
    assert edge.source_id == "scholar_position_frede_will_originates_epictetus"
    assert edge.relation == "opposes"
    assert edge.target_id == "scholar_position_dihle_will_christian_innovation"
    assert edge.direction == "outgoing"
    assert edge.target_label == "Dihle: will is a Christian innovation"
    assert edge.target_type == "position"
    assert edge.weight == 1.0


def test_get_neighbors_incoming_edge_is_canonicalised() -> None:
    """An incoming dialectical edge flips source/target to match KG orientation."""
    collector = EvidenceCollector()
    result = GetNeighborsResult(
        center_node="scholar_position_frede_will_originates_epictetus",
        center_label="Frede",
        edges=[
            EdgeSummary(
                edge_node_id="scholarly_argument_irwin_greek_concept_of_the_will_0",
                label="Irwin: Aristotle may already have the will",
                type="scholarly_argument",
                relation="opposes",
                direction="incoming",
                weight=1.0,
            ),
        ],
    )
    collector.ingest("get_neighbors", {}, result)

    state = _state()
    collector.populate_state(state)

    assert len(state.dialectical_edges) == 1
    edge = state.dialectical_edges[0]
    # Incoming => the neighbor is the source, center is the target.
    assert edge.source_id == "scholarly_argument_irwin_greek_concept_of_the_will_0"
    assert edge.target_id == "scholar_position_frede_will_originates_epictetus"
    assert edge.direction == "incoming"


def test_non_dialectical_relation_is_not_retained() -> None:
    """``authored_by`` is not a fault-line relation — it must not be retained."""
    collector = EvidenceCollector()
    result = GetNeighborsResult(
        center_node="pub_dihle_1982_theory_of_will",
        center_label="Dihle 1982",
        edges=[
            EdgeSummary(
                edge_node_id="scholar_albrecht_dihle",
                label="Albrecht Dihle",
                type="scholar",
                relation="authored_by",
                direction="outgoing",
            ),
        ],
    )
    collector.ingest("get_neighbors", {}, result)

    state = _state()
    collector.populate_state(state)

    assert state.dialectical_edges == []
    # The neighbor node still survives as ordinary evidence.
    assert "scholar_albrecht_dihle" in state.context_node_ids


def test_duplicate_dialectical_edges_collapse() -> None:
    collector = EvidenceCollector()
    edge_summary = EdgeSummary(
        edge_node_id="b",
        label="B",
        type="position",
        relation="critiques",
        direction="outgoing",
    )
    for _ in range(3):
        collector.ingest(
            "get_neighbors",
            {},
            GetNeighborsResult(center_node="a", center_label="A", edges=[edge_summary]),
        )
    state = _state()
    collector.populate_state(state)
    assert len(state.dialectical_edges) == 1


def test_explore_subgraph_edge_list_is_retained_when_present() -> None:
    """Future-proofing: an edge-bearing subgraph result also feeds the store.

    ``ExploreSubgraphResult`` carries only ``nodes`` today, so we ingest a raw
    dict (the shape a future edge-bearing result would dump) to prove the
    retention path is wired and does not regress to dropping edges.
    """
    collector = EvidenceCollector()
    collector._ingest_explore_subgraph(
        {
            "nodes": [
                {"node_id": "x", "label": "X", "type": "debate"},
                {"node_id": "y", "label": "Y", "type": "position"},
            ],
            "edges": [
                {"source": "x", "target": "y", "relation": "responds_to"},
                {"source": "x", "target": "y", "relation": "discusses"},  # dropped
            ],
        }
    )
    state = _state()
    collector.populate_state(state)
    assert len(state.dialectical_edges) == 1
    assert state.dialectical_edges[0].relation == "responds_to"
    assert state.dialectical_edges[0].source_type == "debate"


def test_all_spec_relations_are_recognised() -> None:
    """The retained set matches the ARCHITECTURE §2.1 DIALECTICAL_RELATIONS."""
    expected = {
        "opposes",
        "critiques",
        "responds_to",
        "refutes",
        "contrasts_with",
        "agrees_with",
        "supports",
        "participates_in",
        "contributes_to",
        "has_position",
        "advanced_in",
        "engages_with",
        "interprets",
    }
    assert set(DIALECTICAL_RELATIONS) == expected
