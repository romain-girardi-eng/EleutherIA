"""Tests for the BibliographyBuilder sub-agent."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from eleutheria_graphrag.models.bibliography import (
    AnnotatedBibliography,
    BibliographyEntry,
)
from eleutheria_graphrag.models.counter_evidence import (
    ClaimUnit,
    SynthesizedDraft,
)
from eleutheria_graphrag.services.bibliography_builder import (
    BibliographyBuilder,
    BibliographyToolset,
    render_bibliography_markdown,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _llm_returning(payload: Any) -> MagicMock:
    llm = MagicMock()
    if isinstance(payload, str):
        llm.generate = AsyncMock(return_value=payload)
    else:
        llm.generate = AsyncMock(return_value=json.dumps(payload))
    return llm


def _tool_returning(value: Any) -> MagicMock:
    tool = MagicMock()
    tool.execute = AsyncMock(return_value=value)
    return tool


def _toolset(
    neighbor_responses: dict[str, list[dict[str, Any]]] | None = None,
    detail_responses: dict[str, dict[str, Any]] | None = None,
) -> BibliographyToolset:
    """Build a tool bundle that returns scripted responses per node_id."""
    neighbor_responses = neighbor_responses or {}
    detail_responses = detail_responses or {}

    async def neighbors_exec(args: dict[str, Any]) -> dict[str, Any]:
        node_id = args.get("node_id", "")
        return {"edges": neighbor_responses.get(node_id, [])}

    async def detail_exec(args: dict[str, Any]) -> dict[str, Any]:
        node_id = args.get("node_id", "")
        return detail_responses.get(
            node_id,
            {
                "node_id": node_id,
                "label": f"label-{node_id}",
                "type": "unknown",
                "description": "",
                "metadata": {},
            },
        )

    neighbors_tool = MagicMock()
    neighbors_tool.execute = AsyncMock(side_effect=neighbors_exec)
    detail_tool = MagicMock()
    detail_tool.execute = AsyncMock(side_effect=detail_exec)
    return BibliographyToolset(
        get_node_detail=detail_tool, get_neighbors=neighbors_tool
    )


def _draft(
    answer: str = "Draft answer.",
    seed_ids: list[str] | None = None,
) -> SynthesizedDraft:
    return SynthesizedDraft(
        answer=answer,
        claims=[
            ClaimUnit(
                claim_id="c1",
                claim_text="Sample claim.",
                seed_node_ids=seed_ids or ["concept_eph_hemin"],
            )
        ],
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestBibliographyBuilder:
    @pytest.mark.asyncio
    async def test_no_seeds_returns_empty_bibliography(self) -> None:
        draft = SynthesizedDraft(answer="x", claims=[])
        llm = _llm_returning("{}")
        toolset = _toolset()
        builder = BibliographyBuilder(llm=llm, tools=toolset)
        bibliography = await builder.build(draft)
        assert isinstance(bibliography, AnnotatedBibliography)
        assert bibliography.total_entries == 0
        llm.generate.assert_not_called()

    @pytest.mark.asyncio
    async def test_walks_wrote_about_edges_for_scholar_layer(self) -> None:
        # Setup: concept node has an incoming wrote_about edge from a scholar
        neighbors = {
            "concept_eph_hemin": [
                {
                    "source": "scholar_bobzien",
                    "target": "scholar_bobzien",
                    "relation": "wrote_about",
                    "target_type": "modern_scholar",
                    "label": "Bobzien",
                }
            ],
            "scholar_bobzien": [],
        }
        details = {
            "scholar_bobzien": {
                "node_id": "scholar_bobzien",
                "label": "Susanne Bobzien",
                "type": "modern_scholar",
                "description": "Stoic determinism scholar",
                "metadata": {
                    "full_citation": "Bobzien, S. 1998. Determinism and Freedom in Stoic Philosophy. Oxford: Clarendon.",
                    "key_works": ["Determinism and Freedom 1998"],
                },
            },
        }
        llm = _llm_returning(
            {
                "primary_sources": [],
                "secondary_literature": [
                    {
                        "node_id": "scholar_bobzien",
                        "citation": "Bobzien, S. 1998. Determinism and Freedom in Stoic Philosophy. Oxford: Clarendon.",
                        "relevance_score": 0.9,
                        "in_answer_citations": ["c1"],
                        "annotation": "Standard reference on Stoic compatibilism.",
                    }
                ],
                "supplementary_reading": [],
            }
        )
        builder = BibliographyBuilder(llm=llm, tools=_toolset(neighbors, details))
        bibliography = await builder.build(_draft())
        assert len(bibliography.secondary_literature) == 1
        entry = bibliography.secondary_literature[0]
        assert entry.node_id == "scholar_bobzien"
        assert entry.relevance_score == pytest.approx(0.9)
        assert entry.in_answer_citations == ["c1"]
        assert entry.tier == "secondary_literature"

    @pytest.mark.asyncio
    async def test_classifies_primary_vs_scholar_vs_supplementary(self) -> None:
        neighbors = {
            "concept_eph_hemin": [
                {
                    "target": "work_de_fato",
                    "relation": "part_of",
                    "target_type": "work",
                },
                {
                    "target": "scholar_frede",
                    "relation": "wrote_about",
                    "target_type": "modern_scholar",
                },
                {
                    "target": "concept_voluntas",
                    "relation": "qualifies",
                    "target_type": "concept",
                },
            ],
        }
        details = {
            "work_de_fato": {
                "node_id": "work_de_fato",
                "label": "De Fato",
                "type": "work",
                "description": "Cicero, De Fato",
                "metadata": {
                    "full_citation": "Cicero, M. T. De Fato. Ed. R. W. Sharples 1991."
                },
            },
            "scholar_frede": {
                "node_id": "scholar_frede",
                "label": "Michael Frede",
                "type": "modern_scholar",
                "description": "Free Will historian",
                "metadata": {"full_citation": "Frede, M. 2011. A Free Will."},
            },
            "concept_voluntas": {
                "node_id": "concept_voluntas",
                "label": "voluntas",
                "type": "concept",
                "description": "Augustinian will",
                "metadata": {},
            },
        }
        llm = _llm_returning(
            {
                "primary_sources": [
                    {
                        "node_id": "work_de_fato",
                        "citation": "Cicero, M. T. De Fato. Ed. R. W. Sharples 1991.",
                        "relevance_score": 1.0,
                        "in_answer_citations": ["c1"],
                        "annotation": "Primary source.",
                    }
                ],
                "secondary_literature": [
                    {
                        "node_id": "scholar_frede",
                        "citation": "Frede, M. 2011. A Free Will.",
                        "relevance_score": 0.8,
                        "in_answer_citations": [],
                        "annotation": "Secondary.",
                    }
                ],
                "supplementary_reading": [
                    {
                        "node_id": "concept_voluntas",
                        "citation": "voluntas (concept node)",
                        "relevance_score": 0.3,
                        "in_answer_citations": [],
                        "annotation": "Adjacent.",
                    }
                ],
            }
        )
        builder = BibliographyBuilder(llm=llm, tools=_toolset(neighbors, details))
        bibliography = await builder.build(_draft())
        assert len(bibliography.primary_sources) == 1
        assert len(bibliography.secondary_literature) == 1
        assert len(bibliography.supplementary_reading) == 1

    @pytest.mark.asyncio
    async def test_rejects_hallucinated_node_ids(self) -> None:
        """The LLM may invent node_ids; the builder must reject them."""
        neighbors = {
            "concept_eph_hemin": [
                {
                    "target": "scholar_real",
                    "relation": "wrote_about",
                    "target_type": "modern_scholar",
                }
            ]
        }
        details = {
            "scholar_real": {
                "node_id": "scholar_real",
                "label": "Real Scholar",
                "type": "modern_scholar",
                "description": "",
                "metadata": {"full_citation": "Real, A. 2020."},
            }
        }
        llm = _llm_returning(
            {
                "primary_sources": [],
                "secondary_literature": [
                    {
                        "node_id": "scholar_fabricated",
                        "citation": "Made up.",
                        "relevance_score": 1.0,
                        "in_answer_citations": [],
                        "annotation": "Fake.",
                    },
                    {
                        "node_id": "scholar_real",
                        "citation": "Real, A. 2020.",
                        "relevance_score": 0.5,
                        "in_answer_citations": [],
                        "annotation": "OK.",
                    },
                ],
                "supplementary_reading": [],
            }
        )
        builder = BibliographyBuilder(llm=llm, tools=_toolset(neighbors, details))
        bibliography = await builder.build(_draft())
        assert len(bibliography.secondary_literature) == 1
        assert bibliography.secondary_literature[0].node_id == "scholar_real"

    @pytest.mark.asyncio
    async def test_caps_entries_at_max(self) -> None:
        # Build 15 neighbours, request cap of 5
        neighbors = {
            "concept_x": [
                {
                    "target": f"scholar_{i}",
                    "relation": "wrote_about",
                    "target_type": "modern_scholar",
                }
                for i in range(15)
            ]
        }
        details = {
            f"scholar_{i}": {
                "node_id": f"scholar_{i}",
                "label": f"Scholar {i}",
                "type": "modern_scholar",
                "description": "",
                "metadata": {"full_citation": f"Scholar {i}, 2020."},
            }
            for i in range(15)
        }
        llm = _llm_returning(
            {
                "primary_sources": [],
                "secondary_literature": [
                    {
                        "node_id": f"scholar_{i}",
                        "citation": f"Scholar {i}, 2020.",
                        "relevance_score": 1.0 - i * 0.05,
                        "in_answer_citations": [],
                        "annotation": "...",
                    }
                    for i in range(15)
                ],
                "supplementary_reading": [],
            }
        )
        draft = SynthesizedDraft(
            answer="x",
            claims=[
                ClaimUnit(
                    claim_id="c1",
                    claim_text="claim",
                    seed_node_ids=["concept_x"],
                )
            ],
        )
        builder = BibliographyBuilder(
            llm=llm, tools=_toolset(neighbors, details), max_entries=5
        )
        bibliography = await builder.build(draft, max_entries=5)
        assert bibliography.total_entries <= 5

    @pytest.mark.asyncio
    async def test_emits_bibliography_entry_events(self) -> None:
        neighbors = {
            "concept_eph_hemin": [
                {
                    "target": "scholar_bobzien",
                    "relation": "wrote_about",
                    "target_type": "modern_scholar",
                }
            ]
        }
        details = {
            "scholar_bobzien": {
                "node_id": "scholar_bobzien",
                "label": "Bobzien",
                "type": "modern_scholar",
                "description": "",
                "metadata": {"full_citation": "Bobzien 1998."},
            }
        }
        llm = _llm_returning(
            {
                "primary_sources": [],
                "secondary_literature": [
                    {
                        "node_id": "scholar_bobzien",
                        "citation": "Bobzien 1998.",
                        "relevance_score": 0.9,
                        "in_answer_citations": ["c1"],
                        "annotation": "Standard ref.",
                    }
                ],
                "supplementary_reading": [],
            }
        )

        events: list[dict[str, Any]] = []

        async def on_event(evt: dict[str, Any]) -> None:
            events.append(evt)

        builder = BibliographyBuilder(
            llm=llm,
            tools=_toolset(neighbors, details),
            on_event=on_event,
        )
        await builder.build(_draft())
        types = [e["type"] for e in events]
        assert "bibliography_entry" in types
        assert "bibliography_built" in types
        built = next(e for e in events if e["type"] == "bibliography_built")
        assert built["total_entries"] == 1
        assert built["secondary_count"] == 1

    @pytest.mark.asyncio
    async def test_handles_invalid_llm_json_gracefully(self) -> None:
        neighbors = {"concept_x": []}
        llm = _llm_returning("not json at all")
        builder = BibliographyBuilder(llm=llm, tools=_toolset(neighbors, {}))
        bibliography = await builder.build(
            SynthesizedDraft(
                answer="x",
                claims=[
                    ClaimUnit(
                        claim_id="c1",
                        claim_text="claim",
                        seed_node_ids=["concept_x"],
                    )
                ],
            )
        )
        assert bibliography.total_entries == 0

    @pytest.mark.asyncio
    async def test_render_bibliography_markdown_three_tiers(self) -> None:
        bibliography = AnnotatedBibliography(
            primary_sources=[
                BibliographyEntry(
                    node_id="w1",
                    citation="Cicero, De Fato",
                    relevance_score=1.0,
                    in_answer_citations=["c1"],
                    annotation="Primary.",
                    tier="primary_sources",
                )
            ],
            secondary_literature=[
                BibliographyEntry(
                    node_id="s1",
                    citation="Bobzien 1998",
                    relevance_score=0.9,
                    in_answer_citations=[],
                    annotation="Secondary.",
                    tier="secondary_literature",
                )
            ],
            supplementary_reading=[
                BibliographyEntry(
                    node_id="x1",
                    citation="Other",
                    relevance_score=0.3,
                    in_answer_citations=[],
                    annotation="Aux.",
                    tier="supplementary_reading",
                )
            ],
        )
        md = render_bibliography_markdown(bibliography)
        assert "## Annotated Bibliography" in md
        assert "### Primary Sources" in md
        assert "### Secondary Literature" in md
        assert "### Supplementary Reading" in md
        assert "Cicero, De Fato" in md
        assert "Bobzien 1998" in md
        # claim anchor for primary
        assert "supports c1" in md

    @pytest.mark.asyncio
    async def test_render_bibliography_markdown_empty(self) -> None:
        assert render_bibliography_markdown(AnnotatedBibliography()) == ""

    @pytest.mark.asyncio
    async def test_relevance_score_clamped_to_unit_interval(self) -> None:
        neighbors = {
            "concept_x": [
                {
                    "target": "scholar_x",
                    "relation": "wrote_about",
                    "target_type": "modern_scholar",
                }
            ]
        }
        details = {
            "scholar_x": {
                "node_id": "scholar_x",
                "label": "X",
                "type": "modern_scholar",
                "description": "",
                "metadata": {"full_citation": "X 2020."},
            }
        }
        llm = _llm_returning(
            {
                "primary_sources": [],
                "secondary_literature": [
                    {
                        "node_id": "scholar_x",
                        "citation": "X 2020.",
                        "relevance_score": 2.5,
                        "in_answer_citations": [],
                        "annotation": "out of range.",
                    }
                ],
                "supplementary_reading": [],
            }
        )
        builder = BibliographyBuilder(llm=llm, tools=_toolset(neighbors, details))
        draft = SynthesizedDraft(
            answer="x",
            claims=[
                ClaimUnit(
                    claim_id="c1",
                    claim_text="c",
                    seed_node_ids=["concept_x"],
                )
            ],
        )
        bibliography = await builder.build(draft)
        assert bibliography.secondary_literature[0].relevance_score == 1.0
