"""Pydantic AI structured output models for all JSON-returning LLM calls.

Each model is used as the ``result_type`` for a ``pydantic_ai.Agent``,
providing automatic validation and retry on malformed LLM output.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from eleutheria_graphrag.agents.pipeline_config import QueryType

# ---------------------------------------------------------------------------
# ClassifyQueryType
# ---------------------------------------------------------------------------


class ClassificationResult(BaseModel):
    """Structured output for query classification."""

    query_type: QueryType
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str


# ---------------------------------------------------------------------------
# ExpandQuery
# ---------------------------------------------------------------------------


class GreekTerm(BaseModel):
    greek: str
    transliteration: str
    translation: str


class LatinTerm(BaseModel):
    latin: str
    translation: str


class ExpansionTerms(BaseModel):
    """Structured output for philological query expansion."""

    greek_terms: list[GreekTerm] = Field(default_factory=list)
    latin_terms: list[LatinTerm] = Field(default_factory=list)
    philosophers: list[str] = Field(default_factory=list)
    concepts: list[str] = Field(default_factory=list)
    schools: list[str] = Field(default_factory=list)
    periods: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# EvaluateSufficiency
# ---------------------------------------------------------------------------


class SufficiencyAssessment(BaseModel):
    """Structured output for evidence sufficiency evaluation."""

    score: float = Field(ge=0.0, le=1.0)
    sufficient: bool
    reason: str
    refinement: str | None = None


# ---------------------------------------------------------------------------
# TreeReasoningRetrieve
# ---------------------------------------------------------------------------


class SelectedNode(BaseModel):
    work_id: str
    node_id: str
    reason: str
    priority: int = Field(ge=1, le=3)


class TreeNavigationResult(BaseModel):
    """Structured output for tree reasoning navigation."""

    selected_nodes: list[SelectedNode]
    reasoning: str


# ---------------------------------------------------------------------------
# CRAGValidate
# ---------------------------------------------------------------------------


class CRAGValidation(BaseModel):
    """Structured output for CRAG retrieval validation."""

    relevance: int = Field(ge=0, le=100)
    completeness: int = Field(ge=0, le=100)
    confidence: int = Field(ge=0, le=100)
    missing: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# DualRerank (LLM stage)
# ---------------------------------------------------------------------------


class RerankItem(BaseModel):
    id: int
    score: int = Field(ge=0, le=100)
    reason: str


class LLMRerankResult(BaseModel):
    """Structured output for LLM scholarly reranking."""

    rankings: list[RerankItem]


# ---------------------------------------------------------------------------
# SelfRAGEvaluate
# ---------------------------------------------------------------------------


class SelfRAGEvaluation(BaseModel):
    """Structured output for post-generation quality evaluation."""

    relevance: int = Field(ge=0, le=100)
    grounding: int = Field(ge=0, le=100)
    completeness: int = Field(ge=0, le=100)
    confidence: int = Field(ge=0, le=100)
    caveats: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)
