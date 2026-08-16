"""The curated per-answer subgraph shipped in ``reasoning_path.subgraph``.

Before this existed the right panel only received flat id lists, so the
"curated knowledge graph for each answer" was a retrieval dump with no debate
structure. These tests pin the two guarantees that make it real: it is built
from the assembled ControversyMap + the KG nodes retrieval actually activated,
and it stays inside the legibility caps.
"""

from __future__ import annotations

from eleutheria_graphrag.agents.answer_subgraph import (
    MAX_SUBGRAPH_EDGES,
    MAX_SUBGRAPH_NODES,
    build_answer_subgraph,
    serialize_controversy_map,
)
from eleutheria_graphrag.agents.state import (
    ControversyFrame,
    ControversyMap,
    DialecticalLink,
    FrameCompleteness,
    GroundedPosition,
    PassageRef,
)


def _map() -> ControversyMap:
    """One fault line: two positions that clash over one contested passage."""
    frame = ControversyFrame(
        frame_id="f1",
        debate_node_id="debate_fate",
        title="Is assent up to us?",
        period="Hellenistic",
        positions=[
            GroundedPosition(
                position_id="p_bobzien",
                holder="Bobzien",
                holder_node_id="person_bobzien",
                holder_type="modern_scholar",
                claim="Chrysippus has no notion of freedom of decision.",
                primary_support=["passage_1"],
            ),
            GroundedPosition(
                position_id="p_frede",
                holder="Frede",
                holder_node_id="person_frede",
                holder_type="modern_scholar",
                claim="A notion of will emerges in Epictetus.",
                primary_support=["passage_1"],
            ),
        ],
        links=[
            DialecticalLink(
                relation="opposes",
                from_id="p_frede",
                to_id="p_bobzien",
                gloss="on the Stoic notion of will",
            )
        ],
        contested_passages=[
            PassageRef(
                passage_id="passage_1",
                author="Epictetus",
                work="Discourses",
                canonical_ref="1.1.7",
                original_text="…",
            ),
            PassageRef(
                passage_id="passage_2",
                author="Cicero",
                work="De fato",
                canonical_ref="40",
            ),
        ],
        completeness=FrameCompleteness(incident_edge_count=3),
    )
    return ControversyMap(question_frame="q", frames=[frame])


def _node_lookup() -> dict[str, dict[str, str]]:
    return {
        "person_bobzien": {"label": "Susanne Bobzien", "type": "person"},
        "person_frede": {"label": "Michael Frede", "type": "person"},
        "concept_eph_hemin": {"label": "ἐφ' ἡμῖν", "type": "concept"},
        "person_chrysippus": {"label": "Chrysippus", "type": "person"},
    }


class TestSerializeControversyMap:
    def test_none_map_is_inert(self):
        assert serialize_controversy_map(None) is None
        assert serialize_controversy_map(ControversyMap()) is None

    def test_skeleton_keeps_structure_and_drops_text(self):
        skeleton = serialize_controversy_map(_map())
        assert skeleton is not None
        frame = skeleton["frames"][0]
        assert frame["frame_id"] == "f1"
        assert frame["incident_edge_count"] == 3
        assert [p["holder"] for p in frame["positions"]] == ["Bobzien", "Frede"]
        assert frame["links"][0]["relation"] == "opposes"
        assert [p["passage_id"] for p in frame["passages"]] == [
            "passage_1",
            "passage_2",
        ]
        # The untruncated ancient text NEVER rides on this seam.
        assert "original_text" not in frame["passages"][0]


class TestBuildAnswerSubgraph:
    def test_builds_frames_positions_passages_and_kg_nodes(self):
        subgraph = build_answer_subgraph(
            skeleton=serialize_controversy_map(_map()),
            seed_ids=["concept_eph_hemin"],
            context_ids=["person_chrysippus"],
            activated=[
                {"id": "person_chrysippus", "label": "Chrysippus", "type": "person"}
            ],
            node_lookup=_node_lookup(),
            outgoing_edges={
                "person_bobzien": [
                    {"target": "concept_eph_hemin", "relation": "discusses"}
                ],
                "concept_eph_hemin": [
                    {"target": "not_retrieved", "relation": "related_to"}
                ],
            },
        )

        by_id = {n["id"]: n for n in subgraph["nodes"]}
        assert by_id["frame:f1"]["type"] == "debate"
        assert by_id["frame:f1"]["label"] == "Is assent up to us?"
        assert by_id["pos:p_bobzien"]["label"] == "Bobzien"
        assert by_id["pos:p_bobzien"]["ref"] == "person_bobzien"
        assert by_id["passage_1"]["type"] == "passage"
        assert by_id["passage_1"]["label"] == "Epictetus 1.1.7"
        assert by_id["concept_eph_hemin"]["label"] == "ἐφ' ἡμῖν"
        assert by_id["concept_eph_hemin"]["origin"] == "seed"

        edges = {(e["source"], e["target"], e["relation"]) for e in subgraph["edges"]}
        assert ("frame:f1", "pos:p_bobzien", "has_position") in edges
        # The map's own dialectical link survives with its relation label.
        assert ("pos:p_frede", "pos:p_bobzien", "opposes") in edges
        assert ("pos:p_bobzien", "passage_1", "grounded_in") in edges
        # A contested passage no position claims still hangs off its frame.
        assert ("frame:f1", "passage_2", "contested_passage") in edges
        # Real KG adjacency between included nodes, via the position's holder.
        assert ("pos:p_bobzien", "concept_eph_hemin", "discusses") in edges
        # …but never an edge to a node retrieval did not touch.
        assert all(e["target"] != "not_retrieved" for e in subgraph["edges"])

        stats = subgraph["stats"]
        assert stats["frame_count"] == 1
        assert stats["position_count"] == 2
        assert stats["passage_count"] == 2
        assert stats["kg_node_count"] == 2
        assert stats["node_count"] == len(subgraph["nodes"])
        assert stats["edge_count"] == len(subgraph["edges"])
        assert stats["truncated"] is False

    def test_activated_labels_used_when_node_is_not_in_the_snapshot(self):
        subgraph = build_answer_subgraph(
            skeleton=None,
            seed_ids=[],
            context_ids=[],
            activated=[
                {"id": "concept_new", "label": "New concept", "type": "concept"}
            ],
            node_lookup={},
        )
        assert subgraph["nodes"][0]["label"] == "New concept"
        assert subgraph["stats"]["frame_count"] == 0

    def test_kg_only_answer_still_yields_a_graph(self):
        subgraph = build_answer_subgraph(
            skeleton=None,
            seed_ids=["person_bobzien"],
            context_ids=["concept_eph_hemin"],
            node_lookup=_node_lookup(),
            outgoing_edges={
                "person_bobzien": [
                    {"target": "concept_eph_hemin", "relation": "discusses"}
                ]
            },
        )
        assert [n["id"] for n in subgraph["nodes"]] == [
            "person_bobzien",
            "concept_eph_hemin",
        ]
        assert subgraph["nodes"][0]["root"] is True
        assert subgraph["edges"] == [
            {
                "source": "person_bobzien",
                "target": "concept_eph_hemin",
                "relation": "discusses",
            }
        ]

    def test_caps_hold_and_are_reported(self):
        lookup = {
            f"n{i}": {"label": f"Node {i}", "type": "concept"} for i in range(300)
        }
        edges = {
            f"n{i}": [{"target": f"n{j}", "relation": "related_to"} for j in range(300)]
            for i in range(300)
        }
        subgraph = build_answer_subgraph(
            skeleton=None,
            seed_ids=[f"n{i}" for i in range(300)],
            context_ids=[],
            node_lookup=lookup,
            outgoing_edges=edges,
        )
        assert len(subgraph["nodes"]) == MAX_SUBGRAPH_NODES
        assert len(subgraph["edges"]) == MAX_SUBGRAPH_EDGES
        assert subgraph["stats"]["truncated"] is True
        assert subgraph["stats"]["candidate_nodes"] > MAX_SUBGRAPH_NODES

    def test_frames_win_the_node_budget_over_bulk_kg_nodes(self):
        """Best-first: the debate structure survives a tight cap, not the tail."""
        lookup = {f"n{i}": {"label": f"Node {i}", "type": "concept"} for i in range(50)}
        subgraph = build_answer_subgraph(
            skeleton=serialize_controversy_map(_map()),
            seed_ids=[f"n{i}" for i in range(50)],
            context_ids=[],
            node_lookup=lookup,
            max_nodes=6,
        )
        ids = [n["id"] for n in subgraph["nodes"]]
        assert ids[:5] == [
            "frame:f1",
            "pos:p_bobzien",
            "pos:p_frede",
            "passage_1",
            "passage_2",
        ]
        assert len(ids) == 6


class TestAgentSeam:
    """``_make_answer`` is where the map skeleton joins the answer metadata."""

    def test_make_answer_publishes_the_skeleton(self):
        from eleutheria_graphrag.agents.graph_nodes import _make_answer
        from eleutheria_graphrag.agents.state import RAGState

        state = RAGState(question="q", raw_answer="a")
        assert "controversy_skeleton" not in _make_answer(state).metadata

        state.controversy_map = _map()
        answer = _make_answer(state)
        assert answer.metadata["controversy_skeleton"]["frames"][0]["frame_id"] == "f1"


class TestNoRawIdsRender:
    """A raw node id must never reach the panel as a label (GOAL-8 deleak)."""

    def test_unresolvable_kg_node_is_dropped(self):
        subgraph = build_answer_subgraph(
            skeleton=None,
            seed_ids=["person_bobzien", "concept_unknown_to_the_snapshot"],
            context_ids=[],
            node_lookup=_node_lookup(),
        )
        assert [n["id"] for n in subgraph["nodes"]] == ["person_bobzien"]
