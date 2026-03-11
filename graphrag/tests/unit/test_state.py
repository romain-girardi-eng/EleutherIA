"""Tests for RAG pipeline state models."""

import pytest
from pydantic import ValidationError

from eleutheria_graphrag.agents.pipeline_config import PipelineConfig, QueryType
from eleutheria_graphrag.agents.state import (
    Citation,
    Evidence,
    EvidenceLayer,
    EvidenceSource,
    QueryComplexity,
    RAGState,
    ScholarlyAnswer,
)
from eleutheria_graphrag.agents.structured_models import (
    CRAGValidation,
)


class TestQueryComplexity:
    """Tests for QueryComplexity enum."""

    def test_values(self):
        assert QueryComplexity.SIMPLE.value == "simple"
        assert QueryComplexity.MEDIUM.value == "medium"
        assert QueryComplexity.COMPLEX.value == "complex"

    def test_from_string(self):
        assert QueryComplexity("simple") == QueryComplexity.SIMPLE
        assert QueryComplexity("complex") == QueryComplexity.COMPLEX

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            QueryComplexity("unknown")


class TestEvidenceSource:
    """Tests for EvidenceSource enum."""

    def test_all_sources(self):
        assert len(EvidenceSource) == 8  # 5 original + 3 new (hyde, crag_secondary, tree_reasoning)
        assert EvidenceSource.SEMANTIC_SEARCH.value == "semantic_search"
        assert EvidenceSource.GRAPH_TRAVERSAL.value == "graph_traversal"
        assert EvidenceSource.PASSAGE_CITATION.value == "passage_citation"


class TestEvidence:
    """Tests for Evidence Pydantic model."""

    def test_minimal(self):
        ev = Evidence(id="node_1")
        assert ev.id == "node_1"
        assert ev.label == ""
        assert ev.score == 0.0
        assert ev.layer == EvidenceLayer.PRIMARY

    def test_full_node(self):
        ev = Evidence(
            id="chrysippus_1",
            label="Chrysippus",
            type="Person",
            layer=EvidenceLayer.PRIMARY,
            source=EvidenceSource.SEMANTIC_SEARCH,
            description="Stoic philosopher",
            score=0.95,
            period="Hellenistic",
            school="Stoicism",
        )
        assert ev.type == "Person"
        assert ev.score == 0.95

    def test_passage_fields(self):
        ev = Evidence(
            id="p_42",
            label="SVF 2.912",
            type="passage",
            passage_id="42",
            canonical_ref="SVF 2.912",
            author="Chrysippus",
            work_title="On Fate",
            text_content="Some ancient text here",
            confidence=0.85,
        )
        assert ev.passage_id == "42"
        assert ev.confidence == 0.85

    def test_confidence_bounds(self):
        with pytest.raises(ValidationError):
            Evidence(id="x", confidence=1.5)
        with pytest.raises(ValidationError):
            Evidence(id="x", confidence=-0.1)


class TestCitation:
    """Tests for Citation Pydantic model."""

    def test_node_citation(self):
        c = Citation(ref="1", type="node", id="n1", label="Chrysippus")
        assert c.verified is False
        assert c.layer == EvidenceLayer.PRIMARY

    def test_passage_citation(self):
        c = Citation(
            ref="P1",
            type="passage",
            id="p42",
            label="SVF 2.912",
            confidence=0.9,
            verified=True,
            verification_note="Claim supported",
        )
        assert c.verified is True
        assert c.verification_note == "Claim supported"


class TestScholarlyAnswer:
    """Tests for ScholarlyAnswer output model."""

    def test_defaults(self):
        ans = ScholarlyAnswer(answer="Test answer", question="Test question")
        assert ans.complexity == QueryComplexity.MEDIUM
        assert ans.citations == []
        assert ans.passages_used == 0
        assert ans.iterations == 1

    def test_full_answer(self):
        ans = ScholarlyAnswer(
            answer="The Stoics believed...",
            question="What about fate?",
            complexity=QueryComplexity.COMPLEX,
            citations=[
                Citation(ref="1", type="node", id="n1", label="Chrysippus")
            ],
            seed_nodes=["n1", "n2"],
            context_nodes=["n1", "n2", "n3"],
            passages_used=3,
            iterations=2,
            sub_queries=["sub1", "sub2"],
        )
        assert len(ans.citations) == 1
        assert ans.iterations == 2

    def test_serialization(self):
        ans = ScholarlyAnswer(answer="a", question="q")
        d = ans.model_dump()
        assert "answer" in d
        assert "complexity" in d


class TestRAGState:
    """Tests for mutable RAGState dataclass."""

    def test_defaults(self):
        state = RAGState()
        assert state.question == ""
        assert state.complexity == QueryComplexity.MEDIUM
        assert state.iteration == 0
        assert state.max_iterations == 5
        assert state.primary_evidence == []
        assert state.secondary_evidence == []

    def test_all_evidence(self):
        state = RAGState()
        state.primary_evidence = [
            Evidence(id="p1"),
            Evidence(id="p2"),
        ]
        state.secondary_evidence = [
            Evidence(id="s1"),
        ]
        assert len(state.all_evidence()) == 3

    def test_primary_node_ids(self):
        state = RAGState()
        state.primary_evidence = [
            Evidence(id="a"),
            Evidence(id="b"),
            Evidence(id="a"),  # duplicate
        ]
        ids = state.primary_node_ids()
        assert ids == {"a", "b"}

    def test_all_node_ids(self):
        state = RAGState()
        state.primary_evidence = [Evidence(id="p1")]
        state.secondary_evidence = [Evidence(id="s1"), Evidence(id="p1")]
        assert state.all_node_ids() == {"p1", "s1"}

    def test_mutability(self):
        state = RAGState(question="test")
        state.complexity = QueryComplexity.COMPLEX
        state.iteration = 3
        state.raw_answer = "The answer is..."
        assert state.complexity == QueryComplexity.COMPLEX
        assert state.iteration == 3


class TestQueryTypeInState:
    def test_all_values(self):
        assert len(QueryType) == 5


class TestEvidenceSourceNew:
    def test_hyde_search(self):
        assert EvidenceSource.HYDE_SEARCH == "hyde_search"

    def test_crag_secondary(self):
        assert EvidenceSource.CRAG_SECONDARY == "crag_secondary"

    def test_tree_reasoning(self):
        assert EvidenceSource.TREE_REASONING == "tree_reasoning"

    def test_total_sources(self):
        assert len(EvidenceSource) == 8


class TestRAGStateNewFields:
    def test_query_type_default(self):
        s = RAGState()
        assert s.query_type == QueryType.TEMPORAL

    def test_pipeline_config_default(self):
        s = RAGState()
        assert isinstance(s.pipeline_config, PipelineConfig)
        assert s.pipeline_config.use_hyde is True

    def test_expanded_query(self):
        s = RAGState(expanded_query="fate (heimarmenē, Chrysippus)")
        assert "heimarmenē" in s.expanded_query

    def test_crag_validation(self):
        s = RAGState()
        assert s.crag_validation is None
        s.crag_validation = CRAGValidation(
            relevance=80, completeness=70, confidence=75,
        )
        assert s.crag_validation.confidence == 75

    def test_self_rag_fields(self):
        s = RAGState()
        assert s.self_rag_evaluation is None
        assert s.self_rag_iterations == 0
        assert s.max_self_rag_iterations == 2
        assert s.quality_badge == ""

    def test_insufficient_evidence(self):
        s = RAGState()
        assert s.insufficient_evidence is False


class TestScholarlyAnswerNewFields:
    def test_query_type(self):
        a = ScholarlyAnswer(answer="test", question="test")
        assert a.query_type == "temporal"

    def test_quality_badge(self):
        a = ScholarlyAnswer(
            answer="test", question="test", quality_badge="High",
        )
        assert a.quality_badge == "High"

    def test_insufficient_evidence(self):
        a = ScholarlyAnswer(
            answer="test", question="test", insufficient_evidence=True,
        )
        assert a.insufficient_evidence is True

    def test_serialization_new_fields(self):
        a = ScholarlyAnswer(
            answer="test", question="test",
            query_type=QueryType.COMPARATIVE,
            quality_badge="Medium",
        )
        d = a.model_dump()
        assert d["query_type"] == QueryType.COMPARATIVE
        assert d["quality_badge"] == "Medium"
