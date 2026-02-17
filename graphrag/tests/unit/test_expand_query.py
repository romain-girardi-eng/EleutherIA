"""Tests for ExpandQuery FSM node."""

import pytest

from eleutheria_graphrag.agents.graph_nodes import (
    DecomposeQuery,
    DirectKGLookup,
    ExpandQuery,
    HybridRetrieve,
)
from eleutheria_graphrag.agents.pipeline_config import QueryType
from eleutheria_graphrag.agents.state import RAGState

from .conftest import make_ctx, make_deps


class TestExpandQuery:
    @pytest.mark.asyncio
    async def test_routes_specific_entity_to_direct_kg(self):
        """specific_entity → DirectKGLookup."""
        deps = make_deps(
            llm_response='{"expanded_query": "Chrysippus (Chrysippos)", "greek_terms": [], "latin_terms": [], "related_philosophers": ["Chrysippus"], "related_concepts": []}'
        )
        state = RAGState(question="Who was Chrysippus?")
        state.query_type = QueryType.SPECIFIC_ENTITY
        ctx = make_ctx(state, deps)

        node = ExpandQuery()
        result = await node.run(ctx)

        assert isinstance(result, DirectKGLookup)

    @pytest.mark.asyncio
    async def test_routes_global_abstract_to_hybrid(self):
        """global_abstract → HybridRetrieve."""
        deps = make_deps(
            llm_response='{"expanded_query": "Stoic fate", "greek_terms": [], "latin_terms": [], "related_philosophers": [], "related_concepts": ["fate"]}'
        )
        state = RAGState(question="What is Stoic fate?")
        state.query_type = QueryType.GLOBAL_ABSTRACT
        ctx = make_ctx(state, deps)

        node = ExpandQuery()
        result = await node.run(ctx)

        assert isinstance(result, HybridRetrieve)

    @pytest.mark.asyncio
    async def test_routes_multi_hop_to_decompose(self):
        """multi_hop → DecomposeQuery."""
        deps = make_deps(
            llm_response='{"expanded_query": "Stoic fate evolution", "greek_terms": [], "latin_terms": [], "related_philosophers": [], "related_concepts": []}'
        )
        state = RAGState(question="How did Stoic fate evolve?")
        state.query_type = QueryType.MULTI_HOP
        ctx = make_ctx(state, deps)

        node = ExpandQuery()
        result = await node.run(ctx)

        assert isinstance(result, DecomposeQuery)

    @pytest.mark.asyncio
    async def test_routes_temporal_to_decompose(self):
        """temporal → DecomposeQuery."""
        deps = make_deps(llm_response="not json")  # fallback
        state = RAGState(question="When did Stoic ideas change?")
        state.query_type = QueryType.TEMPORAL
        ctx = make_ctx(state, deps)

        node = ExpandQuery()
        result = await node.run(ctx)

        assert isinstance(result, DecomposeQuery)

    @pytest.mark.asyncio
    async def test_routes_comparative_to_hybrid(self):
        """comparative → HybridRetrieve."""
        deps = make_deps(llm_response="not json")  # fallback
        state = RAGState(question="Compare Stoic and Epicurean fate")
        state.query_type = QueryType.COMPARATIVE
        ctx = make_ctx(state, deps)

        node = ExpandQuery()
        result = await node.run(ctx)

        assert isinstance(result, HybridRetrieve)

    @pytest.mark.asyncio
    async def test_sets_expanded_query(self):
        """Successful LLM expansion should set state.expanded_query."""
        deps = make_deps(
            llm_response='{"expanded_query": "Chrysippus (Chrysippos, Stoic)", "greek_terms": [{"greek": "Χρύσιππος", "transliteration": "Chrysippos", "meaning": "Chrysippus"}], "latin_terms": [], "related_philosophers": ["Chrysippus"], "related_concepts": []}'
        )
        state = RAGState(question="Who was Chrysippus?")
        state.query_type = QueryType.SPECIFIC_ENTITY
        ctx = make_ctx(state, deps)

        node = ExpandQuery()
        await node.run(ctx)

        assert "Chrysippus" in state.expanded_query or "Chrysippos" in state.expanded_query

    @pytest.mark.asyncio
    async def test_static_fallback_on_llm_failure(self):
        """LLM expansion failure should fall back to static dict gracefully."""
        deps = make_deps(llm_response="not valid json")
        state = RAGState(question="What is Stoic fate (heimarmenē)?")
        state.query_type = QueryType.GLOBAL_ABSTRACT
        ctx = make_ctx(state, deps)

        node = ExpandQuery()
        result = await node.run(ctx)

        # Should still route correctly even after fallback
        assert isinstance(result, HybridRetrieve)
        # expanded_query should still be set (to original or expanded)
        assert len(state.expanded_query) > 0

    @pytest.mark.asyncio
    async def test_expansion_disabled(self):
        """When use_expansion=False, expanded_query equals original question."""
        from eleutheria_graphrag.agents.pipeline_config import PipelineConfig
        deps = make_deps()
        state = RAGState(question="What is Stoic fate?")
        state.query_type = QueryType.GLOBAL_ABSTRACT
        state.pipeline_config = PipelineConfig(use_expansion=False)
        ctx = make_ctx(state, deps)

        node = ExpandQuery()
        await node.run(ctx)

        assert state.expanded_query == "What is Stoic fate?"
        # LLM should NOT have been called for expansion
        deps.llm.generate.assert_not_called()
