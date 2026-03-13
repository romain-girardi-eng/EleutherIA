"""Structured output models for JSON-returning LLM calls."""

from __future__ import annotations

from pydantic import BaseModel, Field

from eleutheria_graphrag.agents.pipeline_config import QueryType
from eleutheria_graphrag.agents.state import ClaimStatus, ResearchFacet


class ClassificationResult(BaseModel):
    """Structured output for query classification."""

    query_type: QueryType
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str
    complexity: str | None = None


class GreekTerm(BaseModel):
    greek: str
    transliteration: str
    translation: str


class LatinTerm(BaseModel):
    latin: str
    translation: str


class ExpansionTerms(BaseModel):
    """Structured output for philological query expansion."""

    expanded_query: str | None = None
    greek_terms: list[GreekTerm] = Field(default_factory=list)
    latin_terms: list[LatinTerm] = Field(default_factory=list)
    philosophers: list[str] = Field(default_factory=list)
    concepts: list[str] = Field(default_factory=list)
    schools: list[str] = Field(default_factory=list)
    periods: list[str] = Field(default_factory=list)


class ResearchFrame(BaseModel):
    """Notebook framing for a research-style pipeline."""

    question_frame: str
    facets: list[ResearchFacet] = Field(default_factory=list)
    sub_questions: list[str] = Field(default_factory=list)
    competing_hypotheses: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)


class SelectedNode(BaseModel):
    work_id: str
    node_id: str
    title: str | None = None
    path: str | None = None
    reason: str
    priority: int = Field(ge=1, le=3)


class TreeNavigationResult(BaseModel):
    """Structured output for recursive work-tree navigation."""

    selected_nodes: list[SelectedNode]
    reasoning: str


class ReadingPlanResult(BaseModel):
    """Structured output for the work/facet reading planner."""

    work_titles: list[str] = Field(default_factory=list)
    facet_ids: list[str] = Field(default_factory=list)
    rationale: str = ""


class SufficiencyAssessment(BaseModel):
    """Structured output for evidence sufficiency evaluation."""

    score: float = Field(ge=0.0, le=1.0)
    sufficient: bool
    reason: str
    refinement: str | None = None


class CRAGValidation(BaseModel):
    """Legacy validation payload kept for backwards-compatible metadata."""

    relevance: int = Field(ge=0, le=100)
    completeness: int = Field(ge=0, le=100)
    confidence: int = Field(ge=0, le=100)
    missing: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)


class RerankItem(BaseModel):
    id: int
    score: int = Field(ge=0, le=100)
    reason: str


class LLMRerankResult(BaseModel):
    """Legacy reranker payload kept for optional compatibility."""

    rankings: list[RerankItem]


class SelfRAGEvaluation(BaseModel):
    """Legacy post-generation evaluation payload kept for compatibility."""

    relevance: int = Field(ge=0, le=100)
    grounding: int = Field(ge=0, le=100)
    completeness: int = Field(ge=0, le=100)
    confidence: int = Field(ge=0, le=100)
    caveats: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)


class CounterEvidenceResult(BaseModel):
    """Structured output for bundle-level counter-evidence selection."""

    bundle_ids: list[str] = Field(default_factory=list)
    rationale: str = ""


class ClaimLedgerDraftItem(BaseModel):
    """Structured output for the pre-answer claim ledger."""

    claim: str
    evidence_ids: list[str] = Field(default_factory=list)
    facet_id: str | None = None
    evidence_class: str = "direct_text"
    quote_original: str | None = None
    quote_translation: str | None = None
    support_type: str = "passage"
    confidence: float = Field(ge=0.0, le=1.0)
    status: ClaimStatus = ClaimStatus.SUPPORTED


class ClaimLedgerDraft(BaseModel):
    """Structured claim ledger used before answer rendering."""

    claims: list[ClaimLedgerDraftItem] = Field(default_factory=list)
