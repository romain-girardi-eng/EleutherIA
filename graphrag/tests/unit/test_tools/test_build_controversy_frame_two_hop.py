"""Regression tests for GOAL-7 / WORKSTREAM A — two-hop primary grounding.

ROOT CAUSE (verified against prod): frame seed/position nodes (e.g. the
prohairesis ``scholarly_argument_*`` nodes) carry 0 DIRECT passage edges. Their
primary passages sit one concept hop further:

    argument --discusses/employs--> concept_prohairesis_* --evidenced_by--> passage_epict_*

The old ``_contested_passages`` walked only 1 hop, so the 705 Epictetus passages
silently dropped at frame build and synthesis never saw the Greek. These tests
mirror that exact chain and assert the recovered passages now surface AND that
the fan-out caps hold.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest

from eleutheria_graphrag.agents.dependencies import Deps
from eleutheria_graphrag.agents.tools.build_controversy_frame import (
    BuildControversyFrameTool,
)


def _two_hop_deps(*, n_passages: int = 20) -> Deps:
    """KG fixture mirroring the real prohairesis chain.

    A position node with 0 direct passage edges -> a concept bridge
    (``discusses``) -> ``n_passages`` Epictetus passages (``evidenced_by``),
    one of which carries verbatim Greek.
    """
    node_lookup: dict[str, dict[str, Any]] = {
        "scholarly_argument_dobbin_1991_prohairesis_is_man": {
            "id": "scholarly_argument_dobbin_1991_prohairesis_is_man",
            "label": "Dobbin: prohairesis is the self in Epictetus",
            "type": "argument",
            "description": "Dobbin reads prohairesis as the defining faculty.",
            "period": "Contemporary",
            "metadata": {"scholar_id": "scholar_robert_dobbin"},
        },
        "scholar_robert_dobbin": {
            "id": "scholar_robert_dobbin",
            "label": "Robert Dobbin",
            "type": "person",
            "period": "Contemporary",
        },
        # The concept BRIDGE — has NO direct edge to the position; reachable
        # only via the argument's `discusses` edge.
        "concept_prohairesis_deliberate_choice_aristotle_c3d4e5f6": {
            "id": "concept_prohairesis_deliberate_choice_aristotle_c3d4e5f6",
            "label": "Prohairesis (Προαίρεσις) — Deliberate Choice",
            "type": "concept",
            "description": "The faculty of choice.",
            "metadata": {},
        },
    }
    # The Greek-bearing Epictetus passage (verbatim, polytonic).
    node_lookup["passage_epict_1"] = {
        "id": "passage_epict_1",
        "label": "Epictetus, Discourses 1.1",
        "type": "passage",
        "description": "τῶν ὄντων τὰ μέν ἐστιν ἐφ' ἡμῖν, τὰ δὲ οὐκ ἐφ' ἡμῖν",
        "metadata": {
            "author": "Epictetus",
            "canonical_ref": "Discourses 1.1",
            "language": "grc",
            "cts_urn": "urn:cts:greekLit:tlg0557.tlg002:1.1",
        },
    }
    for i in range(2, n_passages + 1):
        node_lookup[f"passage_epict_{i}"] = {
            "id": f"passage_epict_{i}",
            "label": f"Epictetus, Discourses fragment {i}",
            "type": "passage",
            "description": f"ἐφ' ἡμῖν fragment {i}",
            "metadata": {
                "author": "Epictetus",
                "canonical_ref": f"Discourses {i}",
                "language": "grc",
            },
        }

    outgoing_edges: dict[str, list[dict[str, Any]]] = {
        # hop 1: position -> concept bridge (no passage here).
        "scholarly_argument_dobbin_1991_prohairesis_is_man": [
            {
                "source": "scholarly_argument_dobbin_1991_prohairesis_is_man",
                "target": "concept_prohairesis_deliberate_choice_aristotle_c3d4e5f6",
                "relation": "discusses",
            },
        ],
        # hop 2: concept bridge -> Epictetus passages (evidenced_by).
        "concept_prohairesis_deliberate_choice_aristotle_c3d4e5f6": [
            {
                "source": "concept_prohairesis_deliberate_choice_aristotle_c3d4e5f6",
                "target": f"passage_epict_{i}",
                "relation": "evidenced_by",
            }
            for i in range(1, n_passages + 1)
        ],
    }
    incoming_edges: dict[str, list[dict[str, Any]]] = {}
    return Deps(
        db=AsyncMock(),
        llm=AsyncMock(),
        node_lookup=node_lookup,
        outgoing_edges=outgoing_edges,
        incoming_edges=incoming_edges,
        pagerank_scores={},
    )


def _is_ascii(text: str) -> bool:
    return all(ord(ch) < 128 for ch in text)


@pytest.mark.asyncio
async def test_two_hop_recovers_epictetus_greek_passage() -> None:
    """The frame now carries ≥1 Epictetus PassageRef whose text is Greek."""
    tool = BuildControversyFrameTool(_two_hop_deps())
    out = await tool.execute(
        {"seed_id": "scholarly_argument_dobbin_1991_prohairesis_is_man"}
    )
    epict = [
        p
        for p in out.frame.contested_passages
        if p.passage_id.startswith("passage_epict_")
    ]
    assert epict, "two-hop walk surfaced no Epictetus passages (1-hop regression)"
    # At least one carries verbatim Greek (non-ASCII original text).
    assert any(p.original_text and not _is_ascii(p.original_text) for p in epict)
    # The canonical Discourses 1.1 line, with its real Greek, must be present.
    first = next(p for p in epict if p.passage_id == "passage_epict_1")
    assert "ἐφ' ἡμῖν" in first.original_text
    assert first.author == "Epictetus"


@pytest.mark.asyncio
async def test_two_hop_respects_max_passages_cap() -> None:
    """Even with 20 reachable passages, the limit bounds the result."""
    tool = BuildControversyFrameTool(_two_hop_deps(n_passages=20))
    out = await tool.execute(
        {
            "seed_id": "scholarly_argument_dobbin_1991_prohairesis_is_man",
            "max_passages": 4,
        }
    )
    assert len(out.frame.contested_passages) <= 4


@pytest.mark.asyncio
async def test_via_concepts_caps_bridge_fanout() -> None:
    """Helper walks at most _MAX_BRIDGE_NODES bridges and ≤limit passages."""
    deps = _two_hop_deps(n_passages=30)
    # Add many concept bridges off the position; each fans out to passages.
    extra_bridges: list[dict[str, str]] = []
    for b in range(20):
        bid = f"concept_extra_{b}"
        deps.node_lookup[bid] = {"id": bid, "type": "concept", "label": bid}
        extra_bridges.append(
            {
                "source": "scholarly_argument_dobbin_1991_prohairesis_is_man",
                "target": bid,
                "relation": "discusses",
            }
        )
        deps.outgoing_edges[bid] = [
            {"source": bid, "target": f"passage_epict_{i}", "relation": "evidenced_by"}
            for i in range(1, 6)
        ]
    deps.outgoing_edges["scholarly_argument_dobbin_1991_prohairesis_is_man"].extend(
        extra_bridges
    )
    tool = BuildControversyFrameTool(deps)
    # Limit total passages to 7; helper must never exceed it.
    result = tool._passage_ids_via_concepts(
        "scholarly_argument_dobbin_1991_prohairesis_is_man", 7
    )
    assert len(result) <= 7
    assert len(set(result)) == len(result)  # deduped + ordered
