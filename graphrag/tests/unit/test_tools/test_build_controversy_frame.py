"""Tests for the Scholar-RAG build_controversy_frame tool (G6 M1).

Two paths are covered against a KG mirroring the real trigger graph:

1. **Frame population** — a position seed with direct ``opposes`` edges yields a
   ControversyFrame with grounded positions (holder + publication + page),
   dialectical links, and bilingual contested passages.
2. **Empty-debate fallback** — the two real empty debate nodes
   (``debate_origins_notion_of_will_modern_paradigm``,
   ``debate_carneadean_antiastrology_tradition``) carry no direct fault-line
   edge; the lexical-participant + argument-cluster fallback recovers Frede⟂Dihle
   and Amand⟂Ramelli respectively.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest

from eleutheria_graphrag.agents.dependencies import Deps
from eleutheria_graphrag.agents.tools.build_controversy_frame import (
    BuildControversyFrameTool,
)


def _deps() -> Deps:
    node_lookup: dict[str, dict[str, Any]] = {
        # ── direct-edge frame: Frede position with opposes edges ──────────
        "scholar_position_frede_will_originates_epictetus": {
            "id": "scholar_position_frede_will_originates_epictetus",
            "label": "Frede: will originates in Epictetus",
            "type": "position",
            "description": "The notion of will originates with the Stoic Epictetus.",
            "period": "Contemporary",
            "metadata": {
                "stance": "The notion of free will originates with Epictetus.",
                "scholar_id": "scholar_frede_michael",
                "key_work_reference": "Frede 2011, A Free Will",
                "pages": "pp. 153-174",
            },
        },
        "scholar_position_dihle_will_christian_innovation": {
            "id": "scholar_position_dihle_will_christian_innovation",
            "label": "Dihle: will is a Christian innovation",
            "type": "position",
            "description": "A discrete concept of will is a Christian innovation.",
            "period": "Contemporary",
            "metadata": {
                "stance": "The will is a Christian innovation crystallised in Augustine.",
                "scholar_id": "scholar_albrecht_dihle",
                "key_work_reference": "Dihle 1982, Theory of Will",
            },
        },
        "scholar_position_bobzien_no_free_will_problem_ancients": {
            "id": "scholar_position_bobzien_no_free_will_problem_ancients",
            "label": "Bobzien: no free-will problem in the ancients",
            "type": "position",
            "description": "There is no free-will problem in the ancients.",
            "period": "Contemporary",
            "metadata": {"scholar_id": "scholar_bobzien_susanne"},
        },
        "scholar_frede_michael": {
            "id": "scholar_frede_michael",
            "label": "Michael Frede",
            "type": "person",
            "period": "Contemporary",
        },
        "scholar_albrecht_dihle": {
            "id": "scholar_albrecht_dihle",
            "label": "Albrecht Dihle",
            "type": "person",
            "period": "Contemporary",
        },
        "scholar_bobzien_susanne": {
            "id": "scholar_bobzien_susanne",
            "label": "Susanne Bobzien",
            "type": "person",
            "period": "Contemporary",
        },
        "passage_alex_fat_12": {
            "id": "passage_alex_fat_12",
            "label": "Alexander, De Fato 12",
            "type": "passage",
            "description": "Ἀναιρουμένου δὲ ὡς ἐδείχθη τοῦ βουλεύσασθαι",
            "metadata": {
                "author": "Alexander of Aphrodisias",
                "canonical_ref": "De Fato 12",
                "language": "grc",
            },
        },
        "passage_alex_fat_12_en": {
            "id": "passage_alex_fat_12_en",
            "label": "Alexander, De Fato 12 (English)",
            "type": "passage",
            "description": "Since deliberation is abolished on their account",
            "metadata": {"language": "eng"},
        },
        # ── empty debate 1: discovery-of-will (no direct fault-line edge) ──
        "debate_origins_notion_of_will_modern_paradigm": {
            "id": "debate_origins_notion_of_will_modern_paradigm",
            "label": "Origins of the Notion of Will: Frede and Dihle",
            "type": "debate",
            "description": "Frede dates the will to Epictetus; Dihle to Augustine.",
            "period": "Contemporary",
        },
        # ── empty debate 2: carneadean (participants only, opposes on args) ─
        "debate_carneadean_antiastrology_tradition": {
            "id": "debate_carneadean_antiastrology_tradition",
            "label": "The Carneadean Anti-Astrology Tradition",
            "type": "debate",
            "description": "Did Amand or Ramelli correctly trace the Carneadean argument?",
            "period": "Cross-period",
        },
        "scholarly_argument_amand_carneades": {
            "id": "scholarly_argument_amand_carneades",
            "label": "Amand: Carneades developed the moral argumentation",
            "type": "argument",
            "description": "Amand de Mendieta on the Carneadean anti-fatalist argument.",
            "metadata": {},
        },
        "scholarly_argument_ramelli_origen": {
            "id": "scholarly_argument_ramelli_origen",
            "label": "Ramelli: Origen knew Alexander's anti-fatalist works",
            "type": "argument",
            "description": "Ramelli on Origen's knowledge of the Carneadean tradition.",
            "metadata": {},
        },
    }

    outgoing_edges: dict[str, list[dict[str, Any]]] = {
        "scholar_position_frede_will_originates_epictetus": [
            {
                "source": "scholar_position_frede_will_originates_epictetus",
                "target": "scholar_position_dihle_will_christian_innovation",
                "relation": "opposes",
            },
            {
                "source": "scholar_position_frede_will_originates_epictetus",
                "target": "scholar_position_bobzien_no_free_will_problem_ancients",
                "relation": "opposes",
            },
        ],
        "scholarly_argument_amand_carneades": [
            {
                "source": "scholarly_argument_amand_carneades",
                "target": "scholarly_argument_ramelli_origen",
                "relation": "opposes",
            },
        ],
    }
    incoming_edges: dict[str, list[dict[str, Any]]] = {
        "scholar_position_dihle_will_christian_innovation": [
            {
                "source": "scholar_position_frede_will_originates_epictetus",
                "target": "scholar_position_dihle_will_christian_innovation",
                "relation": "opposes",
            },
        ],
        "scholar_position_bobzien_no_free_will_problem_ancients": [
            {
                "source": "scholar_position_frede_will_originates_epictetus",
                "target": "scholar_position_bobzien_no_free_will_problem_ancients",
                "relation": "opposes",
            },
        ],
        "scholar_position_frede_will_originates_epictetus": [
            {
                "source": "passage_alex_fat_12",
                "target": "scholar_position_frede_will_originates_epictetus",
                "relation": "evidenced_by",
            },
        ],
        "passage_alex_fat_12": [
            {
                "source": "passage_alex_fat_12_en",
                "target": "passage_alex_fat_12",
                "relation": "translation_of",
            },
        ],
        "scholarly_argument_ramelli_origen": [
            {
                "source": "scholarly_argument_amand_carneades",
                "target": "scholarly_argument_ramelli_origen",
                "relation": "opposes",
            },
        ],
        "debate_carneadean_antiastrology_tradition": [
            {
                "source": "person_carneades",
                "target": "debate_carneadean_antiastrology_tradition",
                "relation": "participates_in",
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


# ── frame population (direct-edge path) ──────────────────────────────────


@pytest.mark.asyncio
async def test_position_seed_assembles_frame() -> None:
    tool = BuildControversyFrameTool(_deps())
    out = await tool.execute(
        {"seed_id": "scholar_position_frede_will_originates_epictetus"}
    )
    frame = out.frame
    assert not out.used_fallback
    pids = {p.position_id for p in frame.positions}
    assert "scholar_position_frede_will_originates_epictetus" in pids
    assert "scholar_position_dihle_will_christian_innovation" in pids
    # Two opposes links recorded.
    relations = {(link.from_id, link.relation, link.to_id) for link in frame.links}
    assert (
        "scholar_position_frede_will_originates_epictetus",
        "opposes",
        "scholar_position_dihle_will_christian_innovation",
    ) in relations
    assert len(frame.links) == 2


@pytest.mark.asyncio
async def test_positions_are_grounded_with_holder_and_page() -> None:
    tool = BuildControversyFrameTool(_deps())
    out = await tool.execute(
        {"seed_id": "scholar_position_frede_will_originates_epictetus"}
    )
    frede = next(
        p
        for p in out.frame.positions
        if p.position_id == "scholar_position_frede_will_originates_epictetus"
    )
    assert frede.holder == "Michael Frede"
    assert frede.holder_node_id == "scholar_frede_michael"
    assert frede.holder_type == "modern_scholar"
    assert frede.publication == "Frede 2011, A Free Will"
    assert frede.page_grounding == "pp. 153-174"  # read off metadata, not invented


@pytest.mark.asyncio
async def test_page_grounding_absent_is_none() -> None:
    """No page in metadata => None, never a fabricated locus."""
    tool = BuildControversyFrameTool(_deps())
    out = await tool.execute(
        {"seed_id": "scholar_position_frede_will_originates_epictetus"}
    )
    dihle = next(
        p
        for p in out.frame.positions
        if p.position_id == "scholar_position_dihle_will_christian_innovation"
    )
    assert dihle.page_grounding is None


@pytest.mark.asyncio
async def test_contested_passage_paired_with_english() -> None:
    tool = BuildControversyFrameTool(_deps())
    out = await tool.execute(
        {"seed_id": "scholar_position_frede_will_originates_epictetus"}
    )
    assert out.frame.contested_passages
    pref = out.frame.contested_passages[0]
    assert pref.passage_id == "passage_alex_fat_12"
    assert "βουλεύσασθαι" in pref.original_text
    assert pref.english_text == "Since deliberation is abolished on their account"


@pytest.mark.asyncio
async def test_completeness_signals_no_score() -> None:
    tool = BuildControversyFrameTool(_deps())
    out = await tool.execute(
        {"seed_id": "scholar_position_frede_will_originates_epictetus"}
    )
    c = out.frame.completeness
    assert c.has_two_sides is True
    assert c.has_primary_grounding is True
    assert c.incident_edge_count == 2
    # raw count only — there is no strength/contestedness float anywhere.
    assert not hasattr(c, "base_strength")
    assert not hasattr(c, "contestedness")


# ── empty-debate fallback ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_empty_debate_uses_fallback_and_recovers_frede_dihle() -> None:
    tool = BuildControversyFrameTool(_deps())
    out = await tool.execute(
        {"seed_id": "debate_origins_notion_of_will_modern_paradigm"}
    )
    assert out.used_fallback is True
    assert out.frame.used_fallback is True
    pids = {p.position_id for p in out.frame.positions}
    # Lexical match on "Frede"/"Dihle" recovers the position nodes, then their
    # opposes edges surface as links.
    assert "scholar_position_frede_will_originates_epictetus" in pids
    assert "scholar_position_dihle_will_christian_innovation" in pids
    link_endpoints = {link.from_id for link in out.frame.links} | {
        link.to_id for link in out.frame.links
    }
    assert "scholar_position_dihle_will_christian_innovation" in link_endpoints


@pytest.mark.asyncio
async def test_empty_debate_recovers_amand_ramelli_via_argument_cluster() -> None:
    tool = BuildControversyFrameTool(_deps())
    out = await tool.execute({"seed_id": "debate_carneadean_antiastrology_tradition"})
    assert out.used_fallback is True
    endpoints = {link.from_id for link in out.frame.links} | {
        link.to_id for link in out.frame.links
    }
    assert any("amand" in e for e in endpoints), endpoints
    assert any("ramelli" in e for e in endpoints), endpoints


@pytest.mark.asyncio
async def test_unknown_seed_returns_empty_frame() -> None:
    tool = BuildControversyFrameTool(_deps())
    out = await tool.execute({"seed_id": "does_not_exist"})
    assert out.frame.positions == []
    assert out.frame.links == []
    assert "not found" in out.note


@pytest.mark.asyncio
async def test_links_are_deduplicated() -> None:
    """Frede's opposes edge appears on both endpoints' adjacency — kept once."""
    tool = BuildControversyFrameTool(_deps())
    out = await tool.execute(
        {"seed_id": "scholar_position_frede_will_originates_epictetus"}
    )
    keys = [(link.from_id, link.relation, link.to_id) for link in out.frame.links]
    assert len(keys) == len(set(keys))


@pytest.mark.asyncio
async def test_same_thesis_component_counts_as_one_richest_witness() -> None:
    deps = _deps()
    original = "scholar_position_frede_will_originates_epictetus"
    richest = "scholarly_argument_frede_rich_formulation"
    deps.node_lookup[richest] = {
        "id": richest,
        "label": "Frede: richly grounded formulation",
        "type": "argument",
        "description": "A detailed, atomic formulation of the Epictetus thesis. " * 8,
        "metadata": {
            "stance": "The notion of will originates with Epictetus.",
            "scholar_id": "scholar_frede_michael",
            "page_range": "pp. 153-174",
            "citation_verdict": "verified",
            "citation_verified": True,
            "verified_reference": "Frede 2011, pp. 153-174",
        },
    }
    same_edge = {
        "edge_id": "same-frede-runtime-test",
        "source": original,
        "target": richest,
        "relation": "same_thesis_as",
    }
    deps.outgoing_edges.setdefault(original, []).append(same_edge)
    deps.incoming_edges.setdefault(richest, []).append(same_edge)

    frame = (
        await BuildControversyFrameTool(deps).execute({"seed_id": original})
    ).frame
    ids = {position.position_id for position in frame.positions}
    assert richest in ids
    assert original not in ids
    representative = next(p for p in frame.positions if p.position_id == richest)
    assert representative.same_thesis_formulation_count == 2
    assert set(representative.same_thesis_formulation_ids) == {original, richest}
    assert any(link.from_id == richest for link in frame.links)


@pytest.mark.asyncio
async def test_flagged_passage_is_discovery_only_not_contested_evidence() -> None:
    deps = _deps()
    passage = deps.node_lookup["passage_alex_fat_12"]
    passage["metadata"]["needs_locus_mapping"] = True

    frame = (
        await BuildControversyFrameTool(deps).execute(
            {"seed_id": "scholar_position_frede_will_originates_epictetus"}
        )
    ).frame
    assert frame.contested_passages == []
    assert [item.passage_id for item in frame.flagged_passages] == [
        "passage_alex_fat_12"
    ]
    assert frame.flagged_passages[0].original_text == ""
    assert frame.completeness.has_primary_grounding is False


# ── page + verbatim-quote resolvers (the scholar-quote feature) ──────────────


def test_resolve_page_reads_page_range() -> None:
    """``page_range`` is what the enrichment waves wrote (1162 nodes) — its
    omission silently dropped the page from ~99% of serialized positions."""
    assert BuildControversyFrameTool._resolve_page({"page_range": "34-35"}) == "34-35"


def test_resolve_page_priority_keeps_page_grounding_first() -> None:
    md = {"page_grounding": "p. 12", "page_range": "34-35"}
    assert BuildControversyFrameTool._resolve_page(md) == "p. 12"


def test_resolve_quotation_reads_quote_verbatim() -> None:
    md = {"quote_verbatim": "  the scholar's own words  "}
    assert (
        BuildControversyFrameTool._resolve_quotation(md) == "the scholar's own words"
    )


def test_resolve_quotation_absent_or_blank_is_none() -> None:
    assert BuildControversyFrameTool._resolve_quotation({}) is None
    assert BuildControversyFrameTool._resolve_quotation({"quote_verbatim": "  "}) is None
    assert BuildControversyFrameTool._resolve_quotation({"quote_verbatim": 42}) is None
