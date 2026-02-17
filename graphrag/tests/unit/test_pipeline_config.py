"""Tests for query type taxonomy and adaptive pipeline configuration."""

from __future__ import annotations

import pytest

from eleutheria_graphrag.agents.pipeline_config import (
    PIPELINE_CONFIGS,
    PipelineConfig,
    QueryType,
    get_pipeline_config,
    query_type_to_complexity,
)
from eleutheria_graphrag.agents.state import QueryComplexity


class TestQueryType:
    def test_all_values(self):
        assert len(QueryType) == 5

    def test_specific_entity(self):
        assert QueryType("specific_entity") == QueryType.SPECIFIC_ENTITY

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            QueryType("invalid_type")


class TestPipelineConfig:
    def test_defaults(self):
        config = PipelineConfig()
        assert config.use_hyde is True
        assert config.use_crag is True
        assert config.use_reranking is True
        assert config.use_self_rag is True
        assert config.use_expansion is True
        assert config.use_tree_reasoning is False

    def test_specific_entity_config(self):
        config = get_pipeline_config(QueryType.SPECIFIC_ENTITY)
        assert config.use_hyde is False
        assert config.use_crag is True
        assert config.use_tree_reasoning is False

    def test_global_abstract_config(self):
        config = get_pipeline_config(QueryType.GLOBAL_ABSTRACT)
        assert config.use_hyde is True
        assert config.use_expansion is False
        assert config.use_tree_reasoning is False

    def test_multi_hop_config(self):
        config = get_pipeline_config(QueryType.MULTI_HOP)
        assert config.use_hyde is False
        assert config.use_reranking is False
        assert config.use_tree_reasoning is True

    def test_comparative_config(self):
        config = get_pipeline_config(QueryType.COMPARATIVE)
        assert config.use_hyde is True
        assert config.use_tree_reasoning is True
        assert config.use_expansion is True

    def test_temporal_config(self):
        config = get_pipeline_config(QueryType.TEMPORAL)
        # Default — all on
        assert config.use_hyde is True
        assert config.use_tree_reasoning is True

    def test_all_query_types_have_config(self):
        for qt in QueryType:
            config = get_pipeline_config(qt)
            assert isinstance(config, PipelineConfig)


class TestQueryTypeToComplexity:
    def test_specific_entity_is_simple(self):
        assert query_type_to_complexity(QueryType.SPECIFIC_ENTITY) == QueryComplexity.SIMPLE

    def test_global_abstract_is_medium(self):
        assert query_type_to_complexity(QueryType.GLOBAL_ABSTRACT) == QueryComplexity.MEDIUM

    def test_multi_hop_is_complex(self):
        assert query_type_to_complexity(QueryType.MULTI_HOP) == QueryComplexity.COMPLEX

    def test_comparative_is_complex(self):
        assert query_type_to_complexity(QueryType.COMPARATIVE) == QueryComplexity.COMPLEX

    def test_temporal_is_complex(self):
        assert query_type_to_complexity(QueryType.TEMPORAL) == QueryComplexity.COMPLEX
