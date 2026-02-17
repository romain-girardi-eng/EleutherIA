"""Tests for CRAGValidate FSM node."""

from unittest.mock import AsyncMock, patch

import pytest

from eleutheria_graphrag.agents.graph_nodes import CRAGValidate, DualRerank
from eleutheria_graphrag.agents.pipeline_config import PipelineConfig
from eleutheria_graphrag.agents.state import Evidence, EvidenceLayer, RAGState

from .conftest import make_ctx, make_deps


class TestCRAGValidate:
    @pytest.mark.asyncio
    async def test_passthrough_when_disabled(self):
        """CRAGValidate should pass through when use_crag=False."""
        deps = make_deps()
        state = RAGState(question="test")
        state.pipeline_config = PipelineConfig(use_crag=False)
        ctx = make_ctx(state, deps)

        node = CRAGValidate()
        result = await node.run(ctx)

        assert isinstance(result, DualRerank)
        deps.llm.generate.assert_not_called()

    @pytest.mark.asyncio
    async def test_proceeds_on_high_confidence(self):
        """High CRAG confidence should proceed to DualRerank without secondary retrieval."""
        deps = make_deps(
            llm_response='{"relevance": 85, "completeness": 80, "confidence": 82, "reasoning": "good"}'
        )
        state = RAGState(question="Who was Chrysippus?")
        state.primary_evidence = [Evidence(id="n1", label="Chrysippus", type="Person")]
        ctx = make_ctx(state, deps)

        node = CRAGValidate()
        result = await node.run(ctx)

        assert isinstance(result, DualRerank)
        assert state.crag_validation is not None
        assert state.crag_validation.confidence == 82
        assert state.insufficient_evidence is False

    @pytest.mark.asyncio
    async def test_insufficiency_gate(self):
        """Low confidence (<30) with few sources triggers insufficiency gate."""
        deps = make_deps(
            llm_response='{"relevance": 20, "completeness": 15, "confidence": 20, "reasoning": "poor coverage"}'
        )
        state = RAGState(question="obscure topic")
        state.primary_evidence = [Evidence(id="n1", label="X", type="Person")]  # only 1
        ctx = make_ctx(state, deps)

        node = CRAGValidate()
        result = await node.run(ctx)

        assert isinstance(result, DualRerank)
        assert state.insufficient_evidence is True

    @pytest.mark.asyncio
    async def test_secondary_retrieval_on_low_confidence(self):
        """Confidence 30-60 should trigger secondary retrieval."""
        deps = make_deps(
            llm_response='{"relevance": 50, "completeness": 45, "confidence": 45, "missing": ["Epicurus"], "suggestions": ["epicurean fate"], "reasoning": "incomplete"}',
            search_results=[{"id": "epicurus", "score": 0.8}],
        )
        state = RAGState(question="Compare Stoic and Epicurean fate")
        state.primary_evidence = [
            Evidence(id="n1", label="Chrysippus", type="Person"),
            Evidence(id="n2", label="Fate", type="Concept"),
            Evidence(id="n3", label="Stoic school", type="School"),
        ]
        ctx = make_ctx(state, deps)

        node = CRAGValidate()
        with patch(
            "eleutheria_graphrag.agents.graph_nodes._get_embedding",
            new_callable=AsyncMock,
            return_value=[0.1] * 768,
        ):
            result = await node.run(ctx)

        assert isinstance(result, DualRerank)
        # Secondary retrieval should have added epicurus
        all_ids = ctx.state.all_node_ids()
        # At least 3 original nodes still present
        assert "n1" in all_ids

    @pytest.mark.asyncio
    async def test_fallback_on_llm_failure(self):
        """LLM failure in CRAG should proceed to DualRerank without crashing."""
        deps = make_deps(llm_response="not valid json")
        state = RAGState(question="test")
        ctx = make_ctx(state, deps)

        node = CRAGValidate()
        result = await node.run(ctx)

        assert isinstance(result, DualRerank)
        assert state.crag_validation is None  # not set on failure
