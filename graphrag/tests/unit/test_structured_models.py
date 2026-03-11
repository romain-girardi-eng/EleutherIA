"""Tests for Pydantic AI structured output models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from eleutheria_graphrag.agents.pipeline_config import QueryType
from eleutheria_graphrag.agents.structured_models import (
    ClassificationResult,
    CRAGValidation,
    ExpansionTerms,
    GreekTerm,
    LatinTerm,
    LLMRerankResult,
    RerankItem,
    SelectedNode,
    SelfRAGEvaluation,
    SufficiencyAssessment,
    TreeNavigationResult,
)


class TestClassificationResult:
    def test_valid(self):
        r = ClassificationResult(
            query_type=QueryType.SPECIFIC_ENTITY,
            confidence=0.95,
            reason="Single entity lookup",
        )
        assert r.query_type == QueryType.SPECIFIC_ENTITY
        assert r.confidence == 0.95

    def test_confidence_bounds(self):
        with pytest.raises(ValidationError):
            ClassificationResult(
                query_type=QueryType.MULTI_HOP, confidence=1.5, reason="x"
            )

    def test_confidence_negative(self):
        with pytest.raises(ValidationError):
            ClassificationResult(
                query_type=QueryType.MULTI_HOP, confidence=-0.1, reason="x"
            )


class TestExpansionTerms:
    def test_defaults(self):
        e = ExpansionTerms()
        assert e.greek_terms == []
        assert e.philosophers == []

    def test_with_terms(self):
        e = ExpansionTerms(
            greek_terms=[
                GreekTerm(
                    greek="εἱμαρμένη",
                    transliteration="heimarmenē",
                    translation="fate",
                )
            ],
            latin_terms=[LatinTerm(latin="fatum", translation="fate")],
            philosophers=["Chrysippus"],
        )
        assert len(e.greek_terms) == 1
        assert e.greek_terms[0].transliteration == "heimarmenē"


class TestCRAGValidation:
    def test_valid(self):
        c = CRAGValidation(
            relevance=80,
            completeness=70,
            confidence=75,
            missing=["Chrysippus quote"],
            suggestions=["search De Fato"],
        )
        assert c.confidence == 75

    def test_score_bounds(self):
        with pytest.raises(ValidationError):
            CRAGValidation(
                relevance=101, completeness=50, confidence=50,
            )

    def test_score_negative(self):
        with pytest.raises(ValidationError):
            CRAGValidation(
                relevance=-1, completeness=50, confidence=50,
            )


class TestSelfRAGEvaluation:
    def test_valid(self):
        s = SelfRAGEvaluation(
            relevance=85, grounding=90, completeness=75, confidence=83,
            caveats=["Limited Epicurean sources"],
            improvements=["Add Lucretius references"],
        )
        assert s.grounding == 90

    def test_default_lists(self):
        s = SelfRAGEvaluation(
            relevance=80, grounding=80, completeness=80, confidence=80,
        )
        assert s.caveats == []
        assert s.improvements == []


class TestSufficiencyAssessment:
    def test_sufficient(self):
        s = SufficiencyAssessment(
            score=0.8, sufficient=True, reason="Enough primary sources",
        )
        assert s.sufficient is True
        assert s.refinement is None

    def test_insufficient_with_refinement(self):
        s = SufficiencyAssessment(
            score=0.3, sufficient=False,
            reason="Missing Chrysippus",
            refinement="Chrysippus fate argument De Fato",
        )
        assert s.refinement is not None

    def test_score_bounds(self):
        with pytest.raises(ValidationError):
            SufficiencyAssessment(score=1.5, sufficient=True, reason="x")


class TestLLMRerankResult:
    def test_valid(self):
        r = LLMRerankResult(rankings=[
            RerankItem(id=1, score=85, reason="Direct argument about fate"),
            RerankItem(id=2, score=60, reason="Tangentially relevant"),
        ])
        assert len(r.rankings) == 2
        assert r.rankings[0].score == 85

    def test_score_bounds(self):
        with pytest.raises(ValidationError):
            RerankItem(id=1, score=101, reason="x")


class TestTreeNavigationResult:
    def test_valid(self):
        t = TreeNavigationResult(
            selected_nodes=[
                SelectedNode(
                    work_id="de_fato",
                    node_id="df_003",
                    reason="Contains Master Argument",
                    priority=1,
                ),
            ],
            reasoning="De Fato Book II directly addresses this.",
        )
        assert t.selected_nodes[0].priority == 1

    def test_priority_bounds(self):
        with pytest.raises(ValidationError):
            SelectedNode(
                work_id="x", node_id="y", reason="z", priority=4,
            )
