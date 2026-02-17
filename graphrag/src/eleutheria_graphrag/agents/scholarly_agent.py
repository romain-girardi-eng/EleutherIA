"""
Scholarly Agent — high-level facade wrapping the pydantic-graph FSM.

Provides ``query()`` and ``query_stream()`` entry points that are
API-compatible with the old ``GraphRAGService`` interface, making it
a drop-in replacement for the routes layer.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from typing import Any

from pydantic_graph import Graph

from eleutheria_graphrag.agents.dependencies import Deps
from eleutheria_graphrag.agents.graph_nodes import (
    ClassifyComplexity,
    DecomposeQuery,
    DirectKGLookup,
    EvaluateSufficiency,
    HybridRetrieve,
    SearchPrimarySources,
    SearchSecondarySources,
    Synthesize,
    SynthesizeWithHierarchy,
    VerifyCitations,
)
from eleutheria_graphrag.agents.state import RAGState, ScholarlyAnswer

logger = logging.getLogger(__name__)

# Build the pydantic-graph with all node types
scholarly_graph = Graph(
    nodes=[
        ClassifyComplexity,
        DirectKGLookup,
        HybridRetrieve,
        DecomposeQuery,
        SearchPrimarySources,
        EvaluateSufficiency,
        SearchSecondarySources,
        Synthesize,
        SynthesizeWithHierarchy,
        VerifyCitations,
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
            ClassifyComplexity(),
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
            "metadata": {
                **answer.metadata,
                "complexity": answer.complexity.value,
                "iterations": answer.iterations,
                "sub_queries": answer.sub_queries,
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
        # Yield the answer in chunks to preserve SSE contract
        chunk_size = 80
        text = answer.answer
        for i in range(0, len(text), chunk_size):
            yield text[i : i + chunk_size]
