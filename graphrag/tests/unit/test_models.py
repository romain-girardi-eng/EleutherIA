"""Tests for GraphRAG models."""

import pytest
from pydantic import ValidationError

from eleutheria_graphrag.models.query import Citation, QueryRequest, QueryResponse


class TestQueryRequest:
    """Tests for QueryRequest model."""

    def test_valid_request(self):
        """Test valid query request."""
        request = QueryRequest(question="What is Stoic fate?")
        assert request.question == "What is Stoic fate?"
        assert request.semantic_k == 10
        assert request.graph_depth == 2
        assert request.stream is False

    def test_custom_params(self):
        """Test request with custom parameters."""
        request = QueryRequest(
            question="What is Stoic fate?",
            semantic_k=20,
            graph_depth=3,
            max_context_nodes=50,
            include_passages=False,
            stream=True,
        )
        assert request.semantic_k == 20
        assert request.graph_depth == 3
        assert request.include_passages is False
        assert request.stream is True

    def test_question_too_short(self):
        """Test that short questions are rejected."""
        with pytest.raises(ValidationError):
            QueryRequest(question="Hi")

    def test_semantic_k_bounds(self):
        """Test semantic_k bounds."""
        with pytest.raises(ValidationError):
            QueryRequest(question="Valid question", semantic_k=0)

        with pytest.raises(ValidationError):
            QueryRequest(question="Valid question", semantic_k=100)


class TestCitation:
    """Tests for Citation model."""

    def test_node_citation(self):
        """Test node citation."""
        citation = Citation(
            ref="1",
            type="node",
            id="chrysippus",
            label="Chrysippus",
        )
        assert citation.type == "node"
        assert citation.confidence is None

    def test_passage_citation(self):
        """Test passage citation with confidence."""
        citation = Citation(
            ref="P1",
            type="passage",
            id="abc-123",
            label="Chrysippus, On Fate 3.191",
            confidence=0.95,
        )
        assert citation.type == "passage"
        assert citation.confidence == 0.95

    def test_confidence_bounds(self):
        """Test confidence bounds."""
        with pytest.raises(ValidationError):
            Citation(
                ref="1",
                type="node",
                id="test",
                label="Test",
                confidence=1.5,
            )


class TestQueryResponse:
    """Tests for QueryResponse model."""

    def test_minimal_response(self):
        """Test minimal response."""
        response = QueryResponse(
            answer="The Stoics believed...",
            question="What is Stoic fate?",
        )
        assert response.answer == "The Stoics believed..."
        assert response.citations == []
        assert response.passages_used == 0

    def test_full_response(self):
        """Test response with all fields."""
        response = QueryResponse(
            answer="The Stoics believed... [1]",
            question="What is Stoic fate?",
            citations=[
                Citation(ref="1", type="node", id="fate", label="Fate")
            ],
            seed_nodes=["fate", "stoicism"],
            context_nodes=["fate", "stoicism", "chrysippus"],
            passages_used=5,
            metadata={"processing_time": 1.5},
        )
        assert len(response.citations) == 1
        assert response.seed_nodes == ["fate", "stoicism"]
        assert response.passages_used == 5
