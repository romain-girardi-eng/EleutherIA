"""Tests for query expansion in the long-context pipeline."""

import pytest

from eleutheria_graphrag.agents.legacy_fsm_nodes import DiscoverCorpus, ExpandQuery
from eleutheria_graphrag.agents.pipeline_config import PipelineConfig, QueryType
from eleutheria_graphrag.agents.state import RAGState

from .conftest import make_ctx, make_deps


class TestExpandQuery:
    @pytest.mark.asyncio
    async def test_routes_into_unified_discovery(self):
        deps = make_deps(
            llm_response='{"expanded_query": "Stoic fate heimarmene", "greek_terms": [], "latin_terms": [], "philosophers": ["Chrysippus"], "concepts": ["fate"], "schools": ["Stoicism"], "periods": ["Hellenistic"]}'
        )
        state = RAGState(question="What did the Stoics believe about fate?")
        state.query_type = QueryType.GLOBAL_ABSTRACT
        ctx = make_ctx(state, deps)

        node = ExpandQuery()
        result = await node.run(ctx)

        assert isinstance(result, DiscoverCorpus)
        assert state.expanded_query == "Stoic fate heimarmene"
        assert "Chrysippus" in state.expansion_terms.philosophers

    @pytest.mark.asyncio
    async def test_falls_back_to_static_expansion(self):
        deps = make_deps(llm_response="not valid json")
        state = RAGState(question="What is Stoic fate (heimarmene)?")
        state.query_type = QueryType.GLOBAL_ABSTRACT
        ctx = make_ctx(state, deps)

        node = ExpandQuery()
        result = await node.run(ctx)

        assert isinstance(result, DiscoverCorpus)
        assert state.expanded_query == state.question
        assert state.expansion_terms.concepts == ["fate"]

    @pytest.mark.asyncio
    async def test_respects_disabled_expansion(self):
        deps = make_deps()
        state = RAGState(question="What is Stoic fate?")
        state.query_type = QueryType.GLOBAL_ABSTRACT
        state.pipeline_config = PipelineConfig(use_expansion=False)
        ctx = make_ctx(state, deps)

        node = ExpandQuery()
        result = await node.run(ctx)

        assert isinstance(result, DiscoverCorpus)
        assert state.expanded_query == state.question
        deps.llm.generate.assert_not_called()
