"""Tests for the Scholar-RAG M2 planner (question -> AnswerShape).

Covers the deterministic heuristic shape classifier (the trigger lands on
``survey_of_debates``; "when did Chrysippus die" short-circuits to
``factual_lookup``), the typed pattern-DAG emission, and the LLM path with a
graceful heuristic fallback on malformed output.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from eleutheria_graphrag.agents.plan_research import (
    GraphInventory,
    build_inventory_header,
    classify_shape_heuristic,
    plan_from_shape,
    plan_research,
)
from eleutheria_graphrag.agents.state import AnswerShape

# ── heuristic shape classification ───────────────────────────────────────────


def test_trigger_question_routes_to_survey_of_debates() -> None:
    shape = classify_shape_heuristic(
        "What are the big open debates today about free will in antiquity?"
    )
    assert shape == AnswerShape.SURVEY_OF_DEBATES


def test_ambiguous_question_defaults_to_survey() -> None:
    assert (
        classify_shape_heuristic("Tell me about free will in the Stoics")
        == AnswerShape.SURVEY_OF_DEBATES
    )


def test_factual_question_short_circuits() -> None:
    assert (
        classify_shape_heuristic("When did Chrysippus die?")
        == AnswerShape.FACTUAL_LOOKUP
    )


def test_genealogy_cue() -> None:
    assert (
        classify_shape_heuristic("What is the origin of the notion of the will?")
        == AnswerShape.CONCEPT_GENEALOGY
    )


def test_comparison_cue() -> None:
    assert (
        classify_shape_heuristic("Frede vs Dihle on the emergence of the will")
        == AnswerShape.POSITION_COMPARISON
    )


def test_transmission_cue() -> None:
    assert (
        classify_shape_heuristic("Did Origen know Alexander's anti-fatalist works?")
        == AnswerShape.TRANSMISSION_TRACE
    )


def test_doxography_cue() -> None:
    assert (
        classify_shape_heuristic("What did the Stoics hold about fate?")
        == AnswerShape.DOXOGRAPHICAL_SYNTHESIS
    )


def test_exegesis_cue_with_locus() -> None:
    assert (
        classify_shape_heuristic("What does Cicero De Fato 41 say about the swerve?")
        == AnswerShape.PRIMARY_TEXT_EXEGESIS
    )


# ── typed pattern DAG ────────────────────────────────────────────────────────


def test_survey_plan_emits_debate_first_pattern() -> None:
    plan = plan_from_shape("open debates about fate", AnswerShape.SURVEY_OF_DEBATES)
    assert plan.primary_shape == AnswerShape.SURVEY_OF_DEBATES
    assert plan.patterns, "survey plan must carry graph patterns"
    first = plan.patterns[0]
    assert first.entry == "debate"
    # The audit surface: the named edge_program walks the disagreement layer.
    assert "opposes" in first.edge_program
    # deep tier for a cross-period survey.
    assert plan.budget_tier == "deep"
    # answer_skeleton is a HINT list, not a fixed template.
    assert plan.answer_skeleton


def test_factual_plan_has_no_traversal_program() -> None:
    plan = plan_from_shape("when did Chrysippus die", AnswerShape.FACTUAL_LOOKUP)
    assert plan.budget_tier == "quick"
    assert plan.patterns[0].edge_program == []
    assert plan.patterns[0].depth == 0


def test_secondary_shape_appends_patterns() -> None:
    plan = plan_from_shape(
        "origin of the will and the live debate about it",
        AnswerShape.CONCEPT_GENEALOGY,
        AnswerShape.SURVEY_OF_DEBATES,
    )
    entries = {p.entry for p in plan.patterns}
    assert "concept" in entries
    assert "debate" in entries


# ── inventory header ─────────────────────────────────────────────────────────


def test_inventory_header_surfaces_disagreement_layer() -> None:
    header = build_inventory_header(
        GraphInventory(
            debate_node_count=33,
            opposes_edge_count=11,
            critiques_edge_count=244,
            position_node_count=18,
        )
    )
    assert "33 debate" in header
    assert "11 `opposes`" in header
    assert "244 `critiques`" in header


# ── LLM path + fallback ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_llm_path_parses_shape() -> None:
    llm = AsyncMock()
    llm.generate.return_value = (
        '{"primary_shape": "transmission_trace", '
        '"secondary_shape": null, "rationale": "source question"}'
    )
    plan = await plan_research("how did the argument reach Origen?", llm)
    assert plan.primary_shape == AnswerShape.TRANSMISSION_TRACE
    assert plan.rationale == "source question"


@pytest.mark.asyncio
async def test_llm_path_handles_code_fence() -> None:
    llm = AsyncMock()
    llm.generate.return_value = (
        '```json\n{"primary_shape": "position_comparison", '
        '"secondary_shape": null, "rationale": "x vs y"}\n```'
    )
    plan = await plan_research("Frede vs Dihle", llm)
    assert plan.primary_shape == AnswerShape.POSITION_COMPARISON


@pytest.mark.asyncio
async def test_llm_garbage_falls_back_to_heuristic() -> None:
    llm = AsyncMock()
    llm.generate.return_value = "not json at all"
    plan = await plan_research("What are the open debates about free will?", llm)
    # Heuristic recovers the survey shape; never raises.
    assert plan.primary_shape == AnswerShape.SURVEY_OF_DEBATES
    assert "heuristic" in plan.rationale.lower()


@pytest.mark.asyncio
async def test_no_llm_uses_heuristic() -> None:
    plan = await plan_research("when did Chrysippus die?", llm=None)
    assert plan.primary_shape == AnswerShape.FACTUAL_LOOKUP
