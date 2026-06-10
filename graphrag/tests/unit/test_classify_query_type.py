"""Tests for ClassifyQueryType FSM node."""

import pytest

from eleutheria_graphrag.agents.graph_nodes import ClassifyQueryType
from eleutheria_graphrag.agents.legacy_fsm_nodes import ExpandQuery
from eleutheria_graphrag.agents.pipeline_config import QueryType
from eleutheria_graphrag.agents.state import QueryComplexity, RAGState

from .conftest import make_ctx, make_deps


class TestClassifyQueryType:
    @pytest.mark.asyncio
    async def test_classifies_specific_entity(self):
        deps = make_deps(
            llm_response='{"query_type": "specific_entity", "complexity": "simple", "reason": "single entity"}'
        )
        state = RAGState(question="Who was Chrysippus?")
        ctx = make_ctx(state, deps)

        node = ClassifyQueryType()
        result = await node.run(ctx)

        assert isinstance(result, ExpandQuery)
        assert state.query_type == QueryType.SPECIFIC_ENTITY
        assert state.complexity == QueryComplexity.SIMPLE

    @pytest.mark.asyncio
    async def test_classifies_global_abstract(self):
        deps = make_deps(
            llm_response='{"query_type": "global_abstract", "complexity": "medium", "reason": "abstract"}'
        )
        state = RAGState(question="What did Stoics believe about fate?")
        ctx = make_ctx(state, deps)

        node = ClassifyQueryType()
        result = await node.run(ctx)

        assert isinstance(result, ExpandQuery)
        assert state.query_type == QueryType.GLOBAL_ABSTRACT
        assert state.complexity == QueryComplexity.MEDIUM

    @pytest.mark.asyncio
    async def test_classifies_multi_hop(self):
        deps = make_deps(
            llm_response='{"query_type": "multi_hop", "complexity": "complex", "reason": "multi-hop"}'
        )
        state = RAGState(
            question="How did Stoic fate evolve from Chrysippus to Epictetus?"
        )
        ctx = make_ctx(state, deps)

        node = ClassifyQueryType()
        result = await node.run(ctx)

        assert isinstance(result, ExpandQuery)
        assert state.query_type == QueryType.MULTI_HOP
        assert state.complexity == QueryComplexity.COMPLEX

    @pytest.mark.asyncio
    async def test_fallback_on_llm_failure(self):
        """LLM failure should fall back to keyword heuristics."""
        deps = make_deps(llm_response="not valid json at all")
        state = RAGState(question="Who was Chrysippus?")
        ctx = make_ctx(state, deps)

        node = ClassifyQueryType()
        result = await node.run(ctx)

        assert isinstance(result, ExpandQuery)
        # Keyword heuristic for "Who was" → specific_entity
        assert state.query_type == QueryType.SPECIFIC_ENTITY

    @pytest.mark.asyncio
    async def test_fallback_comparative_keyword(self):
        """'compare' keyword should trigger comparative classification."""
        deps = make_deps(llm_response="not valid json")
        state = RAGState(question="Compare Stoic and Epicurean views on fate")
        ctx = make_ctx(state, deps)

        node = ClassifyQueryType()
        result = await node.run(ctx)

        assert isinstance(result, ExpandQuery)
        assert state.query_type == QueryType.COMPARATIVE

    @pytest.mark.asyncio
    async def test_pipeline_config_set(self):
        """ClassifyQueryType must set a PipelineConfig matching the query type."""
        deps = make_deps(
            llm_response='{"query_type": "specific_entity", "complexity": "simple", "reason": "x"}'
        )
        state = RAGState(question="Who was Epictetus?")
        ctx = make_ctx(state, deps)

        node = ClassifyQueryType()
        await node.run(ctx)

        assert state.pipeline_config is not None
        # specific_entity disables reranking-free defaults — sanity check a field
        assert state.pipeline_config.use_tree_reasoning is True

    @pytest.mark.asyncio
    async def test_metadata_populated(self):
        deps = make_deps(
            llm_response='{"query_type": "comparative", "complexity": "complex", "reason": "compare"}'
        )
        state = RAGState(question="Compare Stoic and Epicurean views on fate")
        ctx = make_ctx(state, deps)

        node = ClassifyQueryType()
        await node.run(ctx)

        assert "query_type" in state.metadata
        assert state.metadata["query_type"] == "comparative"
