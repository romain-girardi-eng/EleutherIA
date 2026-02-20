"""
Scholarly Agent — high-level facade wrapping the pydantic-graph FSM.

Provides ``query()`` and ``query_stream()`` entry points that are
API-compatible with the old ``GraphRAGService`` interface, making it
a drop-in replacement for the routes layer.

Node graph (17 nodes):
----------------------
ClassifyQueryType
 ↓
ExpandQuery
 ├─ specific_entity / global_abstract → DirectKGLookup
 ├─ multi_hop / comparative / temporal → HybridRetrieve
 └─ (complex)                          → DecomposeQuery
         ↓
DirectKGLookup / HybridRetrieve → TreeReasoningRetrieve
DecomposeQuery → SearchPrimarySources → EvaluateSufficiency
                                          ├─ insufficient → SearchPrimarySources (loop)
                                          └─ sufficient   → TreeReasoningRetrieve
SearchSecondarySources (reached from FetchPassagesAndLayer for comparative/global_abstract)
         ↓
TreeReasoningRetrieve → CRAGValidate → DualRerank → FetchPassagesAndLayer
         ↓
Synthesize / SynthesizeWithHierarchy → VerifyCitations → SelfRAGEvaluate
         ├─ quality ≥ threshold → End
         └─ quality <  threshold → RefineSynthesis → VerifyCitations (loop)
"""

from __future__ import annotations

import json
import logging
import textwrap
from collections.abc import AsyncIterator
from typing import Any

from pydantic_graph import Graph

from eleutheria_graphrag.agents.dependencies import Deps
from eleutheria_graphrag.agents.graph_nodes import (
    ClassifyComplexity,
    ClassifyQueryType,
    CRAGValidate,
    DecomposeQuery,
    DirectKGLookup,
    DualRerank,
    EvaluateSufficiency,
    ExpandQuery,
    FetchPassagesAndLayer,
    HybridRetrieve,
    RefineSynthesis,
    SearchPrimarySources,
    SearchSecondarySources,
    SelfRAGEvaluate,
    Synthesize,
    SynthesizeWithHierarchy,
    TreeReasoningRetrieve,
    VerifyCitations,
)
from eleutheria_graphrag.agents.state import RAGState, ScholarlyAnswer

logger = logging.getLogger(__name__)

# Build the pydantic-graph with all 17 node types
scholarly_graph = Graph(
    nodes=[
        # New classification / expansion nodes
        ClassifyQueryType,
        ExpandQuery,
        # Retrieval nodes
        DirectKGLookup,
        HybridRetrieve,
        DecomposeQuery,
        SearchPrimarySources,
        EvaluateSufficiency,
        SearchSecondarySources,
        # Tree reasoning + CRAG + dual reranking
        TreeReasoningRetrieve,
        CRAGValidate,
        DualRerank,
        FetchPassagesAndLayer,
        # Synthesis nodes
        Synthesize,
        SynthesizeWithHierarchy,
        # Post-generation quality nodes
        VerifyCitations,
        SelfRAGEvaluate,
        RefineSynthesis,
        # Legacy complexity classifier (kept for backwards-compat)
        ClassifyComplexity,
    ],
)


class ScholarlyAgent:
    """High-level agent wrapping the pydantic-graph FSM.

    Constructed with a ``Deps`` instance and provides both synchronous
    (non-streaming) and streaming query interfaces.
    """

    def __init__(self, deps: Deps) -> None:
        self.deps = deps

    async def query(
        self,
        question: str,
        *,
        max_iterations: int = 5,
    ) -> ScholarlyAnswer:
        """Execute the full agentic RAG pipeline.

        Args:
            question: The scholarly question to answer.
            max_iterations: Maximum retrieval loops for complex queries.

        Returns:
            A ``ScholarlyAnswer`` with the answer, citations, and metadata.
        """
        state = RAGState(question=question, max_iterations=max_iterations)

        result = await scholarly_graph.run(
            ClassifyQueryType(),  # New entry point (replaces ClassifyComplexity)
            state=state,
            deps=self.deps,
        )

        return result.output

    async def query_dict(
        self,
        question: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Query returning a plain dict (backwards-compatible with old API)."""
        answer = await self.query(question, **kwargs)
        return {
            "answer": answer.answer,
            "question": answer.question,
            "citations": [c.model_dump() for c in answer.citations],
            "seed_nodes": answer.seed_nodes,
            "context_nodes": answer.context_nodes,
            "passages_used": answer.passages_used,
            "llm_model": self.deps.llm.last_model_used,
            "llm_provider": self.deps.llm.last_provider_used,
            "metadata": {
                **answer.metadata,
                "complexity": answer.complexity.value,
                "iterations": answer.iterations,
                "sub_queries": answer.sub_queries,
                "query_type": answer.query_type,
                "quality_badge": answer.quality_badge,
            },
        }

    async def query_stream(
        self,
        question: str,
        *,
        max_iterations: int = 5,
    ) -> AsyncIterator[str]:
        """Execute the pipeline with streaming LLM output.

        Stages 1-N (retrieval, traversal, etc.) run to completion,
        then the synthesis stage streams tokens.

        For now this runs the full pipeline then streams the answer.
        Future: integrate true streaming into the synthesis nodes.
        """
        answer = await self.query(question, max_iterations=max_iterations)
        # Chunk at word boundaries to preserve UTF-8 multi-byte characters
        text = answer.answer
        for chunk in textwrap.wrap(text, width=200, break_on_hyphens=False):
            yield chunk
        # Yield a final complete event with full metadata (JSON-encoded)
        def _safe_default(obj: Any) -> Any:
            """Fallback serializer for non-JSON-serializable objects."""
            return str(obj)

        complete_data = {
            "answer": answer.answer,
            "question": answer.question,
            "citations": [c.model_dump() for c in answer.citations],
            "seed_nodes": answer.seed_nodes,
            "context_nodes": answer.context_nodes,
            "passages_used": answer.passages_used,
            "llm_model": self.deps.llm.last_model_used,
            "llm_provider": self.deps.llm.last_provider_used,
            "metadata": {
                **answer.metadata,
                "complexity": answer.complexity.value,
                "iterations": answer.iterations,
                "sub_queries": answer.sub_queries,
                "query_type": answer.query_type,
                "quality_badge": answer.quality_badge,
            },
        }
        yield json.dumps(
            {"type": "complete", "data": complete_data},
            default=_safe_default,
        )
