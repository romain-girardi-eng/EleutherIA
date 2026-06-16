"""Regression: PRIMARY-PASSAGE SURFACING — author round-robin under a tight cap.

ROOT CAUSE (verified on prod DB): the 2-hop concept bridge reaches a MIX of
``passage_alex_*``, ``passage_arist_*`` AND ``passage_epict_*`` nodes. The old
``_contested_passages`` / ``_passage_ids_via_concepts`` SORTED candidate passage
ids ALPHABETICALLY and then capped at the limit. ``passage_alex_*`` and
``passage_arist_*`` sort BEFORE ``passage_epict_*``, so the capped slots filled
entirely with Alexander + Aristotle passages and ZERO Epictetus survived into the
frame — synthesis never saw the relevant author's Greek.

The fix orders candidates by AUTHOR ROUND-ROBIN (relevance-ranked by the frame
holders), so every author gets representation and the holder's own author
(Epictetus, here) surfaces even under a tight cap. These tests reproduce that
exact alex/arist/epict mix and assert at least one ``passage_epict_*`` survives.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest

from eleutheria_graphrag.agents.dependencies import Deps
from eleutheria_graphrag.agents.tools.build_controversy_frame import (
    BuildControversyFrameTool,
)

_POSITION_ID = "scholarly_argument_dobbin_1991_prohairesis_is_man"
_CONCEPT_ID = "concept_prohairesis_deliberate_choice_aristotle_c3d4e5f6"


def _mixed_author_deps(*, per_author: int = 8) -> Deps:
    """KG fixture: position -> concept bridge -> mix of alex/arist/epict passages.

    The holder is a modern scholar (Dobbin) whose argument is ABOUT Epictetus
    (the claim text names Epictetus). The concept bridge fans out to
    ``per_author`` passages for each of Alexander, Aristotle, Epictetus. Their
    ids sort alex < arist < epict alphabetically — the exact ordering that used
    to starve Epictetus under a low cap.
    """
    node_lookup: dict[str, dict[str, Any]] = {
        _POSITION_ID: {
            "id": _POSITION_ID,
            "label": "Dobbin: prohairesis is the self in Epictetus",
            "type": "argument",
            "description": (
                "Dobbin reads prohairesis as the defining faculty of the self "
                "in Epictetus, contrasting it with the Aristotelian usage."
            ),
            "period": "Contemporary",
            "metadata": {"scholar_id": "scholar_robert_dobbin"},
        },
        "scholar_robert_dobbin": {
            "id": "scholar_robert_dobbin",
            "label": "Robert Dobbin",
            "type": "person",
            "period": "Contemporary",
        },
        _CONCEPT_ID: {
            "id": _CONCEPT_ID,
            "label": "Prohairesis (Προαίρεσις) — Deliberate Choice",
            "type": "concept",
            "description": "The faculty of choice.",
            "metadata": {},
        },
    }

    bridge_passage_edges: list[dict[str, str]] = []
    # Greek-bearing passages for three authors; ids sort alex < arist < epict.
    specimens = {
        "alex": ("Alexander of Aphrodisias", "De Fato"),
        "arist": ("Aristotle", "Nicomachean Ethics"),
        "epict": ("Epictetus", "Discourses"),
    }
    for token, (author, work) in specimens.items():
        for i in range(1, per_author + 1):
            pid = f"passage_{token}_{i}"
            node_lookup[pid] = {
                "id": pid,
                "label": f"{author}, {work} fragment {i}",
                "type": "passage",
                "description": "τῶν ὄντων τὰ μέν ἐστιν ἐφ' ἡμῖν",
                "metadata": {
                    "author": author,
                    "canonical_ref": f"{work} {i}",
                    "language": "grc",
                },
            }
            bridge_passage_edges.append(
                {"source": _CONCEPT_ID, "target": pid, "relation": "evidenced_by"}
            )

    outgoing_edges: dict[str, list[dict[str, Any]]] = {
        _POSITION_ID: [
            {
                "source": _POSITION_ID,
                "target": _CONCEPT_ID,
                "relation": "discusses",
            }
        ],
        _CONCEPT_ID: bridge_passage_edges,
    }
    return Deps(
        db=AsyncMock(),
        llm=AsyncMock(),
        node_lookup=node_lookup,
        outgoing_edges=outgoing_edges,
        incoming_edges={},
        pagerank_scores={},
    )


@pytest.mark.asyncio
async def test_capped_frame_contains_epictetus_despite_alpha_first_others() -> None:
    """Under a tight cap, ≥1 passage_epict_* survives (was 0 with alpha sort)."""
    tool = BuildControversyFrameTool(_mixed_author_deps(per_author=8))
    out = await tool.execute({"seed_id": _POSITION_ID, "max_passages": 6})

    ids = [p.passage_id for p in out.frame.contested_passages]
    assert len(ids) <= 6
    epict = [pid for pid in ids if pid.startswith("passage_epict_")]
    assert epict, (
        "alpha-sort regression: capped frame surfaced only "
        f"alex/arist passages, zero Epictetus — got {ids}"
    )


@pytest.mark.asyncio
async def test_round_robin_gives_multiple_authors_representation() -> None:
    """The cap is shared across authors, not monopolised by the alpha-first."""
    tool = BuildControversyFrameTool(_mixed_author_deps(per_author=8))
    out = await tool.execute({"seed_id": _POSITION_ID, "max_passages": 6})

    prefixes = {
        p.passage_id.split("_")[1]  # alex / arist / epict
        for p in out.frame.contested_passages
        if p.passage_id.startswith("passage_")
    }
    assert len(prefixes) >= 2, f"only one author represented: {prefixes}"
    # With 6 slots and 3 authors, perfect round-robin yields all three.
    assert prefixes == {"alex", "arist", "epict"}


@pytest.mark.asyncio
async def test_holder_author_ranks_first_under_minimal_cap() -> None:
    """Relevance rank: with only 1 slot, the holder's author (Epictetus) wins."""
    tool = BuildControversyFrameTool(_mixed_author_deps(per_author=8))
    out = await tool.execute({"seed_id": _POSITION_ID, "max_passages": 1})

    ids = [p.passage_id for p in out.frame.contested_passages]
    assert len(ids) == 1
    assert ids[0].startswith("passage_epict_"), (
        f"Epictetus question did not rank Epictetus passage first: {ids}"
    )
