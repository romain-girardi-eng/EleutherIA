"""Query type taxonomy and adaptive pipeline configuration.

Each query type maps to a PipelineConfig that selectively enables/disables
augmentation stages (CRAG, reranking, Self-RAG, expansion, tree reasoning).
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel

from eleutheria_graphrag.agents.state import QueryComplexity


class QueryType(str, Enum):
    """Five-type query taxonomy for adaptive pipeline routing."""

    SPECIFIC_ENTITY = "specific_entity"
    GLOBAL_ABSTRACT = "global_abstract"
    MULTI_HOP = "multi_hop"
    COMPARATIVE = "comparative"
    TEMPORAL = "temporal"


class PipelineConfig(BaseModel):
    """Feature flags controlling which augmentation stages are active."""

    use_crag: bool = True
    use_reranking: bool = True
    use_self_rag: bool = True
    use_expansion: bool = True
    use_tree_reasoning: bool = False


PIPELINE_CONFIGS: dict[QueryType, PipelineConfig] = {
    QueryType.SPECIFIC_ENTITY: PipelineConfig(
        use_crag=True,
        use_reranking=True,
        use_self_rag=True,
        use_expansion=True,
        use_tree_reasoning=True,
    ),
    QueryType.GLOBAL_ABSTRACT: PipelineConfig(
        use_crag=True,
        use_reranking=True,
        use_self_rag=True,
        use_expansion=True,
        use_tree_reasoning=True,
    ),
    QueryType.MULTI_HOP: PipelineConfig(
        use_crag=True,
        use_reranking=False,
        use_self_rag=True,
        use_expansion=True,
        use_tree_reasoning=True,
    ),
    QueryType.COMPARATIVE: PipelineConfig(
        use_crag=True,
        use_reranking=True,
        use_self_rag=True,
        use_expansion=True,
        use_tree_reasoning=True,
    ),
    QueryType.TEMPORAL: PipelineConfig(
        use_crag=True,
        use_reranking=True,
        use_self_rag=True,
        use_expansion=True,
        use_tree_reasoning=True,
    ),
}


def get_pipeline_config(query_type: QueryType) -> PipelineConfig:
    """Get the pipeline config for a given query type."""
    return PIPELINE_CONFIGS[query_type]


_COMPLEXITY_MAP: dict[QueryType, QueryComplexity] = {
    QueryType.SPECIFIC_ENTITY: QueryComplexity.SIMPLE,
    QueryType.GLOBAL_ABSTRACT: QueryComplexity.MEDIUM,
    QueryType.MULTI_HOP: QueryComplexity.COMPLEX,
    QueryType.COMPARATIVE: QueryComplexity.COMPLEX,
    QueryType.TEMPORAL: QueryComplexity.COMPLEX,
}


def query_type_to_complexity(query_type: QueryType) -> QueryComplexity:
    """Map query type to backwards-compatible complexity tier."""
    return _COMPLEXITY_MAP[query_type]
