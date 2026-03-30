"""
Scholarly Agent facade wrapping the long-context pydantic-graph pipeline.
"""

from __future__ import annotations

import json
import logging
import re
from collections.abc import AsyncIterator
from typing import Any

from pydantic_graph import Graph

from eleutheria_graphrag.agents.dependencies import Deps
from eleutheria_graphrag.agents.graph_nodes import (
    BuildResearchNotebook,
    ClassifyQueryType,
    DiscoverCorpus,
    DraftClaimLedger,
    EvidenceSufficiency,
    ExpandEvidenceBundles,
    ExpandQuery,
    PlanReading,
    ProgrammaticVerify,
    RenderGroundedAnswer,
    SeekCounterEvidence,
    TreeNavigateWorks,
)
from eleutheria_graphrag.agents.state import RAGState, ScholarlyAnswer

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.;·?!])\s+")
logger = logging.getLogger(__name__)

scholarly_graph = Graph(
    nodes=[
        ClassifyQueryType,
        ExpandQuery,
        DiscoverCorpus,
        BuildResearchNotebook,
        PlanReading,
        TreeNavigateWorks,
        ExpandEvidenceBundles,
        SeekCounterEvidence,
        EvidenceSufficiency,
        DraftClaimLedger,
        RenderGroundedAnswer,
        ProgrammaticVerify,
    ],
)


class ScholarlyAgent:
    """High-level facade over the structured long-context GraphRAG pipeline."""

    def __init__(self, deps: Deps) -> None:
        self.deps = deps

    async def query(
        self,
        question: str,
        *,
        max_iterations: int = 5,
        selected_model: str = "gemini-3.1-pro",
        retrieval_mode: str = "auto",
    ) -> ScholarlyAnswer:
        state = RAGState(
            question=question,
            max_iterations=max_iterations,
            selected_model=selected_model,
            retrieval_mode=retrieval_mode,
        )
        result = await scholarly_graph.run(
            ClassifyQueryType(),
            state=state,
            deps=self.deps,
        )
        return result.output

    async def query_dict(
        self,
        question: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
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
                "query_type": getattr(answer.query_type, "value", answer.query_type),
                "quality_badge": answer.quality_badge,
                "grounding_policy": answer.grounding_policy.value,
                "claim_ledger_size": len(answer.claim_ledger),
            },
        }

    async def query_stream(
        self,
        question: str,
        *,
        max_iterations: int = 5,
    ) -> AsyncIterator[str]:
        answer = await self.query(question, max_iterations=max_iterations)
        text = answer.answer
        paragraphs = re.split(r"\n\n+", text)
        for i, para in enumerate(paragraphs):
            if i > 0:
                yield "\n\n"
            if len(para) <= 500:
                yield para
            else:
                sentences = _SENTENCE_SPLIT_RE.split(para)
                buffer = ""
                for sent in sentences:
                    if buffer and len(buffer) + len(sent) + 1 > 500:
                        yield buffer
                        buffer = sent
                    else:
                        buffer = f"{buffer} {sent}" if buffer else sent
                if buffer:
                    yield buffer

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
                "query_type": getattr(answer.query_type, "value", answer.query_type),
                "quality_badge": answer.quality_badge,
                "grounding_policy": answer.grounding_policy.value,
                "claim_ledger_size": len(answer.claim_ledger),
            },
        }
        yield json.dumps({"type": "complete", "data": complete_data}, default=str)
