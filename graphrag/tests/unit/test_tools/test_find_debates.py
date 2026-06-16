"""Tests for the Scholar-RAG find_debates tool (G6 M1).

Builds a small in-memory KG mirroring the real trigger-graph shape (debate /
controversy / position nodes + dialectical edges) so the vectorless ranking,
period filtering, participant surfacing, and opposing-pair extraction are
exercised against realistic structures.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest

from eleutheria_graphrag.agents.dependencies import Deps
from eleutheria_graphrag.agents.tools.find_debates import FindDebatesTool


def _deps() -> Deps:
    node_lookup: dict[str, dict[str, Any]] = {
        "debate_discovery_of_will": {
            "id": "debate_discovery_of_will",
            "label": 'The "Discovery of the Will" Debate',
            "type": "debate",
            "description": "When did a notion of the will emerge in ancient thought?",
            "period": "Contemporary",
        },
        "debate_stoic_compatibilism": {
            "id": "debate_stoic_compatibilism",
            "label": "Stoic Compatibilism and Fate",
            "type": "debate",
            "description": "Whether the Stoics reconciled fate with responsibility.",
            "period": "Hellenistic",
        },
        "controversy_luther_erasmus": {
            "id": "controversy_luther_erasmus",
            "label": "Luther vs. Erasmus Debate on Free Will",
            "type": "controversy",
            "description": "Reformation dispute over the bondage of the will.",
            "period": "Renaissance",
        },
        "debate_unrelated": {
            "id": "debate_unrelated",
            "label": "Atomic Swerve and Cosmology",
            "type": "debate",
            "description": "A debate about Epicurean physics with no overlap.",
            "period": "Hellenistic",
        },
        "scholar_position_frede": {
            "id": "scholar_position_frede",
            "label": "Frede: will originates in Epictetus",
            "type": "position",
            "description": "The notion of will originates with Epictetus.",
            "period": "Contemporary",
        },
        "person_frede": {
            "id": "person_frede",
            "label": "Michael Frede",
            "type": "person",
        },
        "person_dihle": {
            "id": "person_dihle",
            "label": "Albrecht Dihle",
            "type": "person",
        },
        "passage_alex_fat_12": {
            "id": "passage_alex_fat_12",
            "label": "Alexander, De Fato 12",
            "type": "passage",
        },
    }

    outgoing_edges: dict[str, list[dict[str, Any]]] = {
        "debate_discovery_of_will": [
            {
                "source": "debate_discovery_of_will",
                "target": "scholar_position_frede",
                "relation": "has_position",
            },
        ],
        "scholar_position_frede": [
            {
                "source": "scholar_position_frede",
                "target": "scholar_position_dihle",
                "relation": "opposes",
            },
        ],
    }
    incoming_edges: dict[str, list[dict[str, Any]]] = {
        "debate_discovery_of_will": [
            {
                "source": "person_frede",
                "target": "debate_discovery_of_will",
                "relation": "participates_in",
            },
            {
                "source": "person_dihle",
                "target": "debate_discovery_of_will",
                "relation": "participates_in",
            },
            {
                "source": "passage_alex_fat_12",
                "target": "debate_discovery_of_will",
                "relation": "contributes_to",
            },
        ],
    }
    return Deps(
        db=AsyncMock(),
        llm=AsyncMock(),
        node_lookup=node_lookup,
        outgoing_edges=outgoing_edges,
        incoming_edges=incoming_edges,
        pagerank_scores={},
    )


@pytest.mark.asyncio
async def test_finds_debate_by_topic() -> None:
    tool = FindDebatesTool(_deps())
    result = await tool.execute({"topic": "discovery of the will"})
    ids = [d.debate_id for d in result.debates]
    assert "debate_discovery_of_will" in ids


@pytest.mark.asyncio
async def test_only_debate_position_types_returned() -> None:
    """Persons and passages are never returned — only debate/controversy/position."""
    tool = FindDebatesTool(_deps())
    result = await tool.execute({"topic": "will free fate"})
    types = {d.type for d in result.debates}
    assert types <= {"debate", "controversy", "position"}
    ids = [d.debate_id for d in result.debates]
    assert "person_frede" not in ids
    assert "passage_alex_fat_12" not in ids


@pytest.mark.asyncio
async def test_most_contested_first() -> None:
    """The debate with the highest incident dialectical degree ranks first."""
    tool = FindDebatesTool(_deps())
    result = await tool.execute({"topic": "will"})
    # discovery_of_will has has_position + 2 participants + contributes_to = degree 4.
    top = result.debates[0]
    assert top.debate_id == "debate_discovery_of_will"
    assert top.degree >= 3


@pytest.mark.asyncio
async def test_participant_and_opposing_pairs_surfaced() -> None:
    tool = FindDebatesTool(_deps())
    result = await tool.execute({"topic": "discovery of the will"})
    debate = next(
        d for d in result.debates if d.debate_id == "debate_discovery_of_will"
    )
    assert "person_frede" in debate.participant_ids
    assert "person_dihle" in debate.participant_ids
    assert debate.grounded_passage_count == 1


@pytest.mark.asyncio
async def test_period_filter_excludes_modern_disputes() -> None:
    """An antiquity-scoped query drops the Reformation controversy."""
    tool = FindDebatesTool(_deps())
    result = await tool.execute(
        {"topic": "will free", "period_filter": ["Hellenistic", "Contemporary"]}
    )
    ids = [d.debate_id for d in result.debates]
    assert "controversy_luther_erasmus" not in ids


@pytest.mark.asyncio
async def test_zero_degree_zero_lex_node_excluded() -> None:
    """A debate with neither lexical overlap nor contestedness is dropped.

    Per ARCHITECTURE §2.2 the ranking is ``lex + 0.15*degree`` over a LEFT JOIN,
    so a highly-contested node can still surface on a non-matching topic (degree
    alone). What must NOT surface is a node that is both lexically irrelevant AND
    has zero incident dialectical degree.
    """
    tool = FindDebatesTool(_deps())
    result = await tool.execute({"topic": "phylogenetics zebrafish"})
    ids = [d.debate_id for d in result.debates]
    # debate_unrelated has zero overlap with the topic and zero dialectical degree.
    assert "debate_unrelated" not in ids


@pytest.mark.asyncio
async def test_limit_respected() -> None:
    tool = FindDebatesTool(_deps())
    result = await tool.execute({"topic": "will free fate", "limit": 1})
    assert len(result.debates) <= 1
