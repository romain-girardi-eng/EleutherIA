"""Tests for SelfRAGEvaluate and RefineSynthesis FSM nodes.

SelfRAGEvaluation model fields: relevance, grounding, completeness, confidence (all int 0-100)
Quality badge: confidence >= 80 → High, >= 60 → Medium, < 60 → Low
Refine trigger: confidence < 60 AND self_rag_iterations < max_self_rag_iterations
"""

import pytest
from pydantic_graph import End

from eleutheria_graphrag.agents.graph_nodes import (
    RefineSynthesis,
    SelfRAGEvaluate,
    VerifyCitations,
)
from eleutheria_graphrag.agents.pipeline_config import PipelineConfig
from eleutheria_graphrag.agents.state import (
    Citation,
    Evidence,
    RAGState,
    ScholarlyAnswer,
)

from .conftest import make_ctx, make_deps


# SelfRAGEvaluation JSON with all required fields (relevance, grounding, completeness, confidence)
_SELF_RAG_HIGH = '{"relevance": 90, "grounding": 92, "completeness": 88, "confidence": 90, "caveats": [], "improvements": []}'
_SELF_RAG_MEDIUM = '{"relevance": 68, "grounding": 70, "completeness": 65, "confidence": 68, "caveats": [], "improvements": []}'
_SELF_RAG_LOW = '{"relevance": 45, "grounding": 50, "completeness": 40, "confidence": 45, "caveats": ["lacks citations"], "improvements": ["add more sources"]}'


class TestSelfRAGEvaluate:
    @pytest.mark.asyncio
    async def test_passthrough_when_disabled(self):
        """SelfRAGEvaluate returns End immediately when use_self_rag=False."""
        deps = make_deps()
        state = RAGState(question="test")
        state.raw_answer = "Test answer."
        state.pipeline_config = PipelineConfig(use_self_rag=False)
        ctx = make_ctx(state, deps)

        node = SelfRAGEvaluate()
        result = await node.run(ctx)

        assert isinstance(result, End)
        deps.llm.generate.assert_not_called()

    @pytest.mark.asyncio
    async def test_high_quality_returns_end(self):
        """High-confidence (>=80) evaluation returns End with 'High' badge."""
        deps = make_deps(llm_response=_SELF_RAG_HIGH)
        state = RAGState(question="Who was Chrysippus?")
        state.raw_answer = "Chrysippus was the third head of the Stoic school [1]."
        state.citations = [Citation(ref="1", type="node", id="n1", label="Chrysippus")]
        ctx = make_ctx(state, deps)

        node = SelfRAGEvaluate()
        result = await node.run(ctx)

        assert isinstance(result, End)
        answer: ScholarlyAnswer = result.data
        assert answer.quality_badge == "High"

    @pytest.mark.asyncio
    async def test_medium_quality_returns_end(self):
        """Medium confidence (60-79) assigns 'Medium' badge and returns End."""
        deps = make_deps(llm_response=_SELF_RAG_MEDIUM)
        state = RAGState(question="test")
        state.raw_answer = "The Stoics believed..."
        ctx = make_ctx(state, deps)

        node = SelfRAGEvaluate()
        result = await node.run(ctx)

        assert isinstance(result, End)
        assert result.data.quality_badge == "Medium"

    @pytest.mark.asyncio
    async def test_low_quality_triggers_refine(self):
        """Low confidence (<60) triggers RefineSynthesis when iterations remain."""
        deps = make_deps(llm_response=_SELF_RAG_LOW)
        state = RAGState(question="test")
        state.raw_answer = "Incomplete answer..."
        state.self_rag_iterations = 0
        state.max_self_rag_iterations = 2
        ctx = make_ctx(state, deps)

        node = SelfRAGEvaluate()
        result = await node.run(ctx)

        assert isinstance(result, RefineSynthesis)
        assert state.quality_badge == "Low"

    @pytest.mark.asyncio
    async def test_max_iterations_stops_refinement(self):
        """At max iterations, return End even with low confidence."""
        deps = make_deps(llm_response=_SELF_RAG_LOW)
        state = RAGState(question="test")
        state.raw_answer = "Incomplete answer..."
        state.self_rag_iterations = 2
        state.max_self_rag_iterations = 2
        ctx = make_ctx(state, deps)

        node = SelfRAGEvaluate()
        result = await node.run(ctx)

        assert isinstance(result, End)

    @pytest.mark.asyncio
    async def test_fallback_on_llm_failure(self):
        """LLM failure in SelfRAGEvaluate returns End gracefully."""
        deps = make_deps(llm_response="not valid json")
        state = RAGState(question="test")
        state.raw_answer = "Some answer."
        ctx = make_ctx(state, deps)

        node = SelfRAGEvaluate()
        result = await node.run(ctx)

        assert isinstance(result, End)

    @pytest.mark.asyncio
    async def test_answer_fields_populated(self):
        """Final ScholarlyAnswer includes quality_badge and self_rag_evaluation."""
        deps = make_deps(llm_response=_SELF_RAG_HIGH)
        state = RAGState(question="Who was Chrysippus?")
        state.raw_answer = "Chrysippus [1]."
        state.citations = [Citation(ref="1", type="node", id="n1", label="Chrysippus")]
        ctx = make_ctx(state, deps)

        node = SelfRAGEvaluate()
        result = await node.run(ctx)

        assert isinstance(result, End)
        answer: ScholarlyAnswer = result.data
        assert answer.self_rag_evaluation is not None
        assert answer.self_rag_evaluation.confidence == 90


class TestRefineSynthesis:
    @pytest.mark.asyncio
    async def test_refines_answer(self):
        """RefineSynthesis generates a new answer and returns VerifyCitations."""
        deps = make_deps(llm_response="Refined: Chrysippus was a key Stoic philosopher [1].")
        state = RAGState(question="Who was Chrysippus?")
        state.raw_answer = "Original incomplete answer."
        state.primary_evidence = [Evidence(id="n1", label="Chrysippus", type="Person")]
        ctx = make_ctx(state, deps)

        node = RefineSynthesis()
        result = await node.run(ctx)

        assert isinstance(result, VerifyCitations)
        assert state.raw_answer == "Refined: Chrysippus was a key Stoic philosopher [1]."

    @pytest.mark.asyncio
    async def test_increments_self_rag_iteration(self):
        """RefineSynthesis must increment self_rag_iterations."""
        deps = make_deps(llm_response="Refined answer.")
        state = RAGState(question="test")
        state.raw_answer = "Original."
        state.self_rag_iterations = 0
        ctx = make_ctx(state, deps)

        node = RefineSynthesis()
        await node.run(ctx)

        assert state.self_rag_iterations == 1

    @pytest.mark.asyncio
    async def test_uses_evaluation_feedback(self):
        """RefineSynthesis includes evaluation caveats/improvements in prompt."""
        from eleutheria_graphrag.agents.structured_models import SelfRAGEvaluation

        deps = make_deps(llm_response="Improved answer with more citations [1] [P1].")
        state = RAGState(question="test")
        state.raw_answer = "Brief answer."
        state.self_rag_evaluation = SelfRAGEvaluation(
            relevance=45,
            grounding=50,
            completeness=40,
            confidence=45,
            caveats=["lacks primary sources"],
            improvements=["add SVF citations"],
        )
        ctx = make_ctx(state, deps)

        node = RefineSynthesis()
        result = await node.run(ctx)

        assert isinstance(result, VerifyCitations)
        deps.llm.generate.assert_called_once()
