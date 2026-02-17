"""
Agentic GraphRAG — Pydantic AI agent framework for scholarly Q&A.

Replaces the single-pass pipeline with an adaptive multi-step agent graph
that decomposes queries, retrieves hierarchically, and verifies citations.
"""

from eleutheria_graphrag.agents.dependencies import Deps
from eleutheria_graphrag.agents.scholarly_agent import ScholarlyAgent
from eleutheria_graphrag.agents.state import (
    Citation,
    Evidence,
    QueryComplexity,
    RAGState,
    ScholarlyAnswer,
)

__all__ = [
    "Citation",
    "Deps",
    "Evidence",
    "QueryComplexity",
    "RAGState",
    "ScholarlyAgent",
    "ScholarlyAnswer",
]
