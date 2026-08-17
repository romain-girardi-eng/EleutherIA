"""The real-KG per-answer subgraph shipped in ``reasoning_path.subgraph``.

The answer map may select and arrange KG nodes, but it must not mint a parallel
``frame:*`` / ``pos:*`` graph. These tests pin that every non-question id comes
from the loaded snapshot and that runtime-only structure is disclosed.
"""

from __future__ import annotations

from copy import deepcopy

import pytest

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
        "debate_fate": {"label": "Is assent up to us?", "type": "debate"},
        "person_bobzien": {"label": "Susanne Bobzien", "type": "person"},
        "person_frede": {"label": "Michael Frede", "type": "person"},
        "passage_1": {"label": "Epictetus, Discourses 1.1.7", "type": "passage"},
        "passage_2": {"label": "Cicero, De fato 40", "type": "passage"},
        "concept_eph_hemin": {"label": "ἐφ' ἡμῖν", "type": "concept"},
        "person_chrysippus": {"label": "Chrysippus", "type": "person"},
    }


@pytest.fixture
def kg_snapshot_fixture() -> dict[str, dict[str, str]]:
    """A minimal loaded-snapshot index used by the serialisation assertions."""
    return _node_lookup()


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
    def test_builds_real_debates_holders_passages_and_kg_nodes(self):
        subgraph = build_answer_subgraph(
            skeleton=serialize_controversy_map(_map()),
            question="Did Chrysippus have a notion of free will?",
            seed_ids=["concept_eph_hemin"],
            context_ids=["person_chrysippus"],
            activated=[
                {"id": "person_chrysippus", "label": "Chrysippus", "type": "person"}
            ],
            node_lookup=_node_lookup(),
            outgoing_edges={
                "person_frede": [
                    {
                        "edge_id": "edge-frede-debate",
                        "target": "debate_fate",
                        "relation": "responds_to",
                    },
                    {
                        "edge_id": "edge-frede-bobzien",
                        "target": "person_bobzien",
                        "relation": "opposes",
                    },
                ],
                "person_bobzien": [
                    {
                        "edge_id": "edge-bobzien-concept",
                        "target": "concept_eph_hemin",
                        "relation": "discusses",
                    },
                    {
                        "edge_id": "edge-bobzien-passage",
                        "target": "passage_1",
                        "relation": "grounded_in",
                    },
                ],
                "debate_fate": [
                    {
                        "edge_id": "edge-debate-passage",
                        "target": "passage_2",
                        "relation": "contributes_to",
                    }
                ],
                "concept_eph_hemin": [
                    {"target": "not_retrieved", "relation": "related_to"}
                ],
            },
        )

        by_id = {n["id"]: n for n in subgraph["nodes"]}
        assert by_id["question"]["type"] == "question"
        assert by_id["question"]["synthetic"] is True
        assert by_id["debate_fate"]["type"] == "debate"
        assert by_id["debate_fate"]["label"] == "Is assent up to us?"
        assert by_id["person_bobzien"]["label"] == "Susanne Bobzien"
        assert by_id["person_bobzien"]["type"] == "person"
        assert by_id["passage_1"]["type"] == "passage"
        assert by_id["passage_1"]["label"] == "Epictetus, Discourses 1.1.7"
        assert by_id["concept_eph_hemin"]["label"] == "ἐφ' ἡμῖν"
        assert by_id["concept_eph_hemin"]["origin"] == "seed"
        assert not any(node_id.startswith(("frame:", "pos:")) for node_id in by_id)

        edges = {(e["source"], e["target"], e["relation"]) for e in subgraph["edges"]}
        assert ("question", "debate_fate", "frames_question") in edges
        assert ("debate_fate", "person_bobzien", "has_position") in edges
        # The real KG dialectical edge wins over the projected map link.
        assert ("person_frede", "person_bobzien", "opposes") in edges
        assert ("person_bobzien", "passage_1", "grounded_in") in edges
        assert ("debate_fate", "passage_2", "contributes_to") in edges
        assert ("person_bobzien", "concept_eph_hemin", "discusses") in edges
        # …but never an edge to a node retrieval did not touch.
        assert all(e["target"] != "not_retrieved" for e in subgraph["edges"])

        by_edge = {
            (edge["source"], edge["target"], edge["relation"]): edge
            for edge in subgraph["edges"]
        }
        assert by_edge[("person_frede", "person_bobzien", "opposes")]["origin"] == "kg"
        assert by_edge[("question", "debate_fate", "frames_question")]["origin"] == "runtime_inference"
        assert by_edge[("debate_fate", "person_bobzien", "has_position")]["origin"] == "runtime_inference"

        stats = subgraph["stats"]
        assert stats["frame_count"] == 1
        assert stats["position_count"] == 2
        assert stats["passage_count"] == 2
        assert stats["kg_node_count"] == 2
        assert stats["node_count"] == len(subgraph["nodes"])
        assert stats["edge_count"] == len(subgraph["edges"])
        assert stats["truncated"] is False

    def test_activated_node_missing_from_snapshot_is_dropped(self):
        subgraph = build_answer_subgraph(
            skeleton=None,
            seed_ids=[],
            context_ids=[],
            activated=[
                {"id": "concept_new", "label": "New concept", "type": "concept"}
            ],
            node_lookup={},
        )
        assert subgraph["nodes"] == [
            {
                "id": "question",
                "label": "Question",
                "type": "question",
                "origin": "question_anchor",
                "score": 1.0,
                "root": True,
                "synthetic": True,
            }
        ]
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
            "question",
            "person_bobzien",
            "concept_eph_hemin",
        ]
        assert subgraph["nodes"][1]["root"] is True
        assert subgraph["edges"] == [
            {
                "source": "person_bobzien",
                "target": "concept_eph_hemin",
                "relation": "discusses",
                "origin": "kg",
            },
            {
                "source": "question",
                "target": "person_bobzien",
                "relation": "retrieved_for_question",
                "origin": "runtime_inference",
            },
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
        lookup = {
            **_node_lookup(),
            **{
                f"n{i}": {"label": f"Node {i}", "type": "concept"}
                for i in range(50)
            },
        }
        subgraph = build_answer_subgraph(
            skeleton=serialize_controversy_map(_map()),
            seed_ids=[f"n{i}" for i in range(50)],
            context_ids=[],
            node_lookup=lookup,
            max_nodes=6,
        )
        ids = [n["id"] for n in subgraph["nodes"]]
        assert ids == [
            "question",
            "debate_fate",
            "person_bobzien",
            "person_frede",
            "passage_1",
            "passage_2",
        ]

    def test_lexical_fallback_mints_no_frame_and_deduplicates_holder(self):
        skeleton = serialize_controversy_map(_map())
        assert skeleton is not None
        skeleton["frames"][0]["debate_node_id"] = None
        second = deepcopy(skeleton["frames"][0])
        second["frame_id"] = "f2"
        second["positions"] = [deepcopy(second["positions"][0])]
        second["links"] = []
        second["passages"] = []
        skeleton["frames"].append(second)

        subgraph = build_answer_subgraph(
            skeleton=skeleton,
            question="What is up to us?",
            node_lookup=_node_lookup(),
            outgoing_edges={
                "person_frede": [
                    {"target": "person_bobzien", "relation": "opposes"}
                ]
            },
        )

        ids = [node["id"] for node in subgraph["nodes"]]
        assert ids.count("person_bobzien") == 1
        assert "debate_fate" not in ids
        assert not any(node_id.startswith("frame:") for node_id in ids)
        assert {
            (edge["source"], edge["target"], edge["origin"])
            for edge in subgraph["edges"]
            if edge["source"] == "question"
        } == {
            ("question", "person_bobzien", "runtime_inference"),
            ("question", "person_frede", "runtime_inference"),
        }

    def test_every_non_question_node_exists_in_snapshot_fixture(
        self,
        kg_snapshot_fixture: dict[str, dict[str, str]],
    ):
        subgraph = build_answer_subgraph(
            skeleton=serialize_controversy_map(_map()),
            question="Is assent up to us?",
            seed_ids=["concept_eph_hemin", "missing_seed"],
            context_ids=["person_chrysippus", "missing_context"],
            activated=[
                {"id": "person_frede", "label": "Michael Frede"},
                {"id": "runtime_only", "label": "Runtime-only node"},
            ],
            node_lookup=kg_snapshot_fixture,
        )

        assert all(
            node["id"] == "question" or node["id"] in kg_snapshot_fixture
            for node in subgraph["nodes"]
        )


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
        assert [n["id"] for n in subgraph["nodes"]] == [
            "question",
            "person_bobzien",
        ]
