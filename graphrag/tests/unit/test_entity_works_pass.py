"""Named-entity works pass: canonical work/publication nodes must be seeded.

Audit finding: an Augustine question ("How does De libero arbitrio relate to his
later anti-Pelagian doctrine of grace?") never retrieved
``work_ad_simplicianum``, ``work_augustine_retractationes`` (which carries the
Retract. I.9.3-6 loci on DLA) or ``pub_wetzel_1992_augustine_limits_virtue``,
though all three are in the graph: the loop grazes the densely-linked argument
clusters and never reaches the sparsely-linked work/publication layer.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest

from eleutheria_graphrag.agents.dependencies import Deps
from eleutheria_graphrag.agents.evidence_collector import EvidenceCollector
from eleutheria_graphrag.agents.plan_research import extract_named_entities
from eleutheria_graphrag.agents.react_loop import (
    NativeAgentLoop,
    entity_works_pass,
    seed_entity_works,
)
from eleutheria_graphrag.agents.sse_emitter import NullEmitter
from eleutheria_graphrag.agents.state import QueryComplexity, RAGState
from eleutheria_graphrag.agents.tools import build_tool_registry

AUGUSTINE_QUESTION = (
    "How does De libero arbitrio relate to his later anti-Pelagian doctrine of grace?"
)
NO_WORK_QUESTION = "How does grace relate to freedom of choice?"


def _node(
    node_id: str,
    label: str,
    node_type: str,
    *,
    author: str | None = None,
    alternative_names: list[str] | None = None,
    description: str = "",
) -> dict[str, object]:
    return {
        "id": node_id,
        "node_id": node_id,
        "label": label,
        "type": node_type,
        "description": description,
        "period": None,
        "school": None,
        "alternative_names": alternative_names or [],
        "metadata": {"author": author} if author else {},
    }


def _node_lookup() -> dict[str, dict[str, object]]:
    """A miniature of the real graph: works + publications + noisy neighbours."""
    nodes = [
        _node(
            "work_augustine_de_libero_arbitrio",
            "Augustine, De Libero Arbitrio (On the Free Choice of the Will)",
            "work",
            author="Augustine of Hippo",
        ),
        _node(
            "work_ad_simplicianum",
            "Ad Simplicianum (To Simplician)",
            "work",
            author="Augustine of Hippo",
        ),
        # No author field at all — reachable via the (French-spelled) label, and
        # ranked up by its own description naming the work the question names.
        _node(
            "work_augustine_retractationes",
            "Augustin, Retractationes",
            "work",
            alternative_names=["Retractationum libri II", "Augustine, Retractations"],
            description=(
                "Retract. I.9.3-6 — critical reflection on De libero arbitrio "
                "(388-395), where Augustine qualifies his youthful argument."
            ),
        ),
        _node(
            "pub_wetzel_1992_augustine_limits_virtue",
            "Wetzel 1992 — Augustine and the Limits of Virtue",
            "publication",
            author="James Wetzel",
        ),
        # Densely-linked argument cluster the loop already finds on its own.
        _node(
            "argument_frede_2011_alexander_libertarian_dead_end",
            "Alexander's libertarian construction as a dead end",
            "argument",
        ),
        _node("person_augustine", "Augustine of Hippo", "person"),
        # Same title, different author — a legitimate direct hit, not a bug.
        _node(
            "work_methodius_de_libero_arbitrio",
            "Methodius, De Libero Arbitrio",
            "work",
            author="Methodius of Olympus",
        ),
        # Unrelated: must never be pulled in.
        _node("work_cicero_de_fato", "Cicero, De Fato", "work", author="Cicero"),
    ]
    return {n["id"]: n for n in nodes}  # type: ignore[index,misc]


def _edge(source: str, target: str, relation: str) -> dict[str, object]:
    return {"source": source, "target": target, "relation": relation, "weight": 1.0}


def _edges() -> tuple[dict[str, list[dict[str, object]]], ...]:
    """``De libero arbitrio --extends--> Ad Simplicianum`` + the author node."""
    edges = [
        _edge("work_augustine_de_libero_arbitrio", "work_ad_simplicianum", "extends"),
        _edge("work_augustine_de_libero_arbitrio", "person_augustine", "authored_by"),
        _edge("work_augustine_retractationes", "person_augustine", "authored_by"),
        _edge(
            "pub_wetzel_1992_augustine_limits_virtue", "person_augustine", "discusses"
        ),
    ]
    outgoing: dict[str, list[dict[str, object]]] = {}
    incoming: dict[str, list[dict[str, object]]] = {}
    for edge in edges:
        outgoing.setdefault(str(edge["source"]), []).append(edge)
        incoming.setdefault(str(edge["target"]), []).append(edge)
    return outgoing, incoming


def _make_deps(*, with_edges: bool = True) -> Deps:
    llm = AsyncMock()
    llm.last_model_used = "gemini-3.1-pro"
    llm.last_provider_used = "gemini"
    outgoing, incoming = _edges() if with_edges else ({}, {})
    return Deps(
        db=AsyncMock(),
        llm=llm,
        node_lookup=_node_lookup(),  # type: ignore[arg-type]
        outgoing_edges=outgoing,
        incoming_edges=incoming,
        pagerank_scores={},
    )


# ── entity extraction ────────────────────────────────────────────────────────


def test_extract_named_entities_finds_latin_title() -> None:
    """The title run stops at the first English word, not at the sentence end."""
    assert extract_named_entities(AUGUSTINE_QUESTION)[0] == "De libero arbitrio"


def test_extract_named_entities_splits_author_from_title() -> None:
    entities = extract_named_entities(
        "How does Augustine's De libero arbitrio relate to his later doctrine?"
    )
    assert "Augustine" in entities
    assert "De libero arbitrio" in entities


def test_extract_named_entities_empty_when_nothing_named() -> None:
    assert extract_named_entities(NO_WORK_QUESTION) == []


# ── the works pass ───────────────────────────────────────────────────────────


def test_works_pass_surfaces_the_missed_canonical_nodes() -> None:
    """The three nodes the audit query missed must all be returned."""
    hits = entity_works_pass(_make_deps(), AUGUSTINE_QUESTION)
    found = {h.node_id for h in hits}

    assert "work_augustine_de_libero_arbitrio" in found  # direct title match
    assert "work_ad_simplicianum" in found  # via author expansion
    assert "work_augustine_retractationes" in found  # via label ("Augustin")
    assert "pub_wetzel_1992_augustine_limits_virtue" in found  # publication layer


def test_works_pass_ranks_the_named_title_first() -> None:
    hits = entity_works_pass(_make_deps(), AUGUSTINE_QUESTION)
    assert hits[0].node_id == "work_augustine_de_libero_arbitrio"
    # A node whose own text names the title outranks the author's other works.
    scores = {h.node_id: h.score for h in hits}
    assert scores["work_augustine_retractationes"] > scores["work_ad_simplicianum"]


def test_works_pass_uses_the_edge_layer_when_names_do_not_match() -> None:
    """``Ad Simplicianum`` is reachable only as a graph neighbour of the title."""
    deps = _make_deps()
    deps.node_lookup["work_ad_simplicianum"]["metadata"] = {}  # no author string
    found = {h.node_id for h in entity_works_pass(deps, AUGUSTINE_QUESTION)}
    assert "work_ad_simplicianum" in found


def test_works_pass_survives_a_graph_without_edges() -> None:
    found = {
        h.node_id
        for h in entity_works_pass(_make_deps(with_edges=False), AUGUSTINE_QUESTION)
    }
    assert "work_ad_simplicianum" in found  # author-string fallback tier


def test_works_pass_is_restricted_to_the_work_publication_layer() -> None:
    hits = entity_works_pass(_make_deps(), AUGUSTINE_QUESTION)
    assert hits, "expected hits for a question naming a work"
    assert all(h.type in {"work", "publication", "source_collection"} for h in hits)
    found = {h.node_id for h in hits}
    assert "person_augustine" not in found
    assert "argument_frede_2011_alexander_libertarian_dead_end" not in found
    assert "work_cicero_de_fato" not in found


def test_works_pass_is_a_noop_when_no_work_is_named() -> None:
    assert entity_works_pass(_make_deps(), NO_WORK_QUESTION) == []


def test_works_pass_respects_its_limit() -> None:
    hits = entity_works_pass(_make_deps(), AUGUSTINE_QUESTION, limit=2)
    assert len(hits) == 2


def test_works_pass_survives_stringified_metadata() -> None:
    """Snapshot rows sometimes carry metadata/alt-names as JSON strings."""
    deps = _make_deps()
    node = deps.node_lookup["work_ad_simplicianum"]
    node["metadata"] = json.dumps(node["metadata"])
    node["alternative_names"] = json.dumps([])
    found = {h.node_id for h in entity_works_pass(deps, AUGUSTINE_QUESTION)}
    assert "work_ad_simplicianum" in found


# ── seeding into the loop ────────────────────────────────────────────────────


def test_seed_entity_works_seeds_evidence_and_context() -> None:
    deps = _make_deps()
    state = RAGState(question=AUGUSTINE_QUESTION, complexity=QueryComplexity.COMPLEX)
    evidence = EvidenceCollector()

    block = seed_entity_works(deps, state, evidence)

    assert "work_ad_simplicianum" in block
    assert "work_ad_simplicianum" in evidence.seed_node_ids
    assert "work_ad_simplicianum" in state.metadata["entity_works_pass"]


def test_seed_entity_works_noop_returns_empty_block() -> None:
    deps = _make_deps()
    state = RAGState(question=NO_WORK_QUESTION, complexity=QueryComplexity.MEDIUM)
    evidence = EvidenceCollector()

    assert seed_entity_works(deps, state, evidence) == ""
    assert evidence.seed_node_ids == []
    assert "entity_works_pass" not in state.metadata


@pytest.mark.asyncio
async def test_native_loop_starts_aware_of_the_named_works() -> None:
    """Iteration 0 must already name the works, and they must reach the state."""
    deps = _make_deps()
    deps.llm.generate_with_tools = AsyncMock(
        return_value={"role": "assistant", "content": "done"}
    )
    state = RAGState(question=AUGUSTINE_QUESTION, complexity=QueryComplexity.COMPLEX)
    loop = NativeAgentLoop(
        deps=deps,
        state=state,
        tools=build_tool_registry(deps),
        emitter=NullEmitter(),
    )

    await loop.run()

    opening_user_msg = loop.messages[1]["content"]
    assert "work_ad_simplicianum" in opening_user_msg
    assert "work_augustine_retractationes" in opening_user_msg
    # No tool call was made: the pass is free.
    assert loop.calls_made == 0
    assert "work_ad_simplicianum" in state.seed_node_ids
