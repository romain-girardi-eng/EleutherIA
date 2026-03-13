"""
RAG pipeline state and shared models for the scholarly agent.

The agent keeps an explicit research notebook, adaptive retrieval budgets,
evidence bundles, and a claim ledger so that retrieval, reasoning, and
grounding stay inspectable end-to-end.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class QueryComplexity(str, Enum):
    """Classification tier for adaptive query routing."""

    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


class EvidenceSource(str, Enum):
    """Where a piece of evidence originated."""

    SEMANTIC_SEARCH = "semantic_search"
    GRAPH_TRAVERSAL = "graph_traversal"
    HYBRID_SEARCH = "hybrid_search"
    PASSAGE_CITATION = "passage_citation"
    DIRECT_LOOKUP = "direct_lookup"
    HYDE_SEARCH = "hyde_search"
    CRAG_SECONDARY = "crag_secondary"
    TREE_REASONING = "tree_reasoning"


class EvidenceLayer(str, Enum):
    """Primary (ancient) vs secondary (modern) source layer."""

    PRIMARY = "primary"
    SECONDARY = "secondary"


class GroundingPolicy(str, Enum):
    """Policy for which evidence types may support a claim."""

    MIXED_EVIDENCE = "mixed_evidence"
    PASSAGE_FIRST = "passage_first"


class ClaimStatus(str, Enum):
    """Support status for a drafted claim."""

    SUPPORTED = "supported"
    INSUFFICIENT = "insufficient"


class RetrievalBudget(BaseModel):
    """Token budgets for long-context packing and adaptive retrieval."""

    model_window: int = Field(1_000_000, ge=8192)
    reserved_ratio: float = Field(0.15, ge=0.05, le=0.5)
    layer_ratios: dict[str, float] = Field(
        default_factory=lambda: {
            "passage_bundles": 0.65,
            "section_summaries": 0.20,
            "kg_metadata": 0.15,
        }
    )
    degradation_order: list[str] = Field(
        default_factory=lambda: [
            "kg_metadata",
            "section_summaries",
            "passage_bundles",
        ]
    )

    def available_context_tokens(self) -> int:
        """Return the usable prompt budget after reserving output space."""
        return int(self.model_window * (1.0 - self.reserved_ratio))

    def layer_budget(self, layer: str) -> int:
        """Tokens available for a specific context layer."""
        return int(self.available_context_tokens() * self.layer_ratios.get(layer, 0.0))

    def node_search_limit(self) -> int:
        """Adaptive node search target based on metadata budget."""
        return max(20, min(200, self.layer_budget("kg_metadata") // 160))

    def traversal_node_limit(self) -> int:
        """Adaptive traversal breadth based on metadata budget."""
        return max(30, min(300, self.layer_budget("kg_metadata") // 100))

    def candidate_work_limit(self) -> int:
        """Adaptive candidate work budget for tree navigation."""
        return max(5, min(50, self.layer_budget("section_summaries") // 1200))

    def section_summary_limit(self) -> int:
        """Adaptive section summary count before passage expansion."""
        return max(8, min(120, self.layer_budget("section_summaries") // 350))

    def passage_bundle_limit(self) -> int:
        """Adaptive passage bundle count before final packing."""
        return max(4, min(200, self.layer_budget("passage_bundles") // 650))

    @staticmethod
    def estimate_tokens(value: str | Any) -> int:
        """Cheap token estimate good enough for prompt packing decisions."""
        if value is None:
            return 0
        if not isinstance(value, str):
            value = str(value)
        return max(1, (len(value) + 3) // 4)


class Evidence(BaseModel):
    """A single piece of retrieved evidence (KG node or passage)."""

    id: str = Field(..., description="Node ID or passage ID")
    label: str = Field("", description="Human-readable label")
    type: str = Field("", description="Node type (Person, Concept, etc.) or 'passage'")
    layer: EvidenceLayer = Field(EvidenceLayer.PRIMARY)
    source: EvidenceSource = Field(EvidenceSource.SEMANTIC_SEARCH)
    description: str = Field("", description="Node description or passage text")
    score: float = Field(0.0, description="Relevance score (0-1)")

    passage_id: str | None = Field(
        None, description="Database passage_id if applicable"
    )
    cts_urn: str | None = Field(None, description="CTS URN for ancient texts")
    canonical_ref: str | None = Field(None, description="Canonical reference string")
    author: str | None = None
    work_id: str | None = None
    work_title: str | None = None
    language: str | None = None
    text_content: str | None = Field(None, description="Full passage text from DB")
    confidence: float | None = Field(None, ge=0.0, le=1.0)

    period: str | None = None
    school: str | None = None
    role: str | None = None

    metadata: dict[str, Any] = Field(default_factory=dict)


class EvidenceBundle(BaseModel):
    """Canonical proof unit used in long-context packing and answering."""

    bundle_id: str
    work_id: str
    work_title: str
    author: str | None = None
    section_path: str = ""
    canonical_ref: str | None = None
    original_passage_id: str
    translation_passage_id: str | None = None
    original_text: str
    translation_text: str | None = None
    language: str | None = None
    token_estimate: int = Field(0, ge=0)
    evidence_role: str = "primary_support"
    source: EvidenceSource = EvidenceSource.TREE_REASONING
    node_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ResearchFacet(BaseModel):
    """Facet used to mimic a scholar's reading plan for broad queries."""

    facet_id: str
    title: str
    question: str
    keywords: list[str] = Field(default_factory=list)
    required_support: str = "passage"
    priority: int = Field(1, ge=1, le=5)


class ReadingNote(BaseModel):
    """Notebook note captured before the final synthesis pass."""

    note_id: str
    thesis: str
    work_id: str | None = None
    section_path: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)
    counterpoint: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class ResearchToolCall(BaseModel):
    """Structured record of an internal retrieval/reading tool invocation."""

    tool_call_id: str
    tool_name: str
    stage_id: str
    status: str = "complete"
    query: str | None = None
    rationale: str | None = None
    work_id: str | None = None
    work_title: str | None = None
    section_path: str | None = None
    selected_ids: list[str] = Field(default_factory=list)
    detail_count: int = Field(0, ge=0)
    details: dict[str, Any] = Field(default_factory=dict)


class ReadingDecision(BaseModel):
    """Explicit decision taken while planning or reading the corpus."""

    decision_id: str
    stage_id: str
    decision_type: str
    title: str
    rationale: str = ""
    facet_id: str | None = None
    selected_ids: list[str] = Field(default_factory=list)
    rejected_ids: list[str] = Field(default_factory=list)
    supporting_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ClaimLedgerItem(BaseModel):
    """Atomic, evidence-linked claim produced before prose rendering."""

    claim: str
    evidence_ids: list[str] = Field(default_factory=list)
    facet_id: str | None = None
    evidence_class: str = "direct_text"
    quote_original: str | None = None
    quote_translation: str | None = None
    support_type: str = "passage"
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    status: ClaimStatus = ClaimStatus.SUPPORTED


class ContextPack(BaseModel):
    """Packed long-context payload broken into semantic layers."""

    kg_metadata: list[str] = Field(default_factory=list)
    section_summaries: list[str] = Field(default_factory=list)
    passage_bundles: list[EvidenceBundle] = Field(default_factory=list)
    prompt_context: str = ""
    token_estimate: int = Field(0, ge=0)
    bundle_refs: dict[str, str] = Field(default_factory=dict)
    node_refs: dict[str, str] = Field(default_factory=dict)


class ResearchNotebook(BaseModel):
    """Traceable notebook for research-style reasoning."""

    question_frame: str = ""
    facets: list[ResearchFacet] = Field(default_factory=list)
    corpus_scope: list[str] = Field(default_factory=list)
    work_priorities: list[str] = Field(default_factory=list)
    reading_notes: list[ReadingNote] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    competing_hypotheses: list[str] = Field(default_factory=list)
    counter_evidence: list[str] = Field(default_factory=list)
    tool_calls: list[ResearchToolCall] = Field(default_factory=list)
    reading_decisions: list[ReadingDecision] = Field(default_factory=list)
    claim_ledger: list[ClaimLedgerItem] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)


class DossierFacet(BaseModel):
    """Facet-level slice of the final scholarly dossier."""

    facet_id: str
    title: str
    question: str
    summary: str = ""
    primary_bundle_ids: list[str] = Field(default_factory=list)
    testimony_bundle_ids: list[str] = Field(default_factory=list)
    counter_bundle_ids: list[str] = Field(default_factory=list)
    metadata_ids: list[str] = Field(default_factory=list)
    note_ids: list[str] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)


class ScholarlyDossier(BaseModel):
    """Structured dossier feeding the claim-ledger and final synthesis passes."""

    question_frame: str = ""
    facets: list[DossierFacet] = Field(default_factory=list)
    primary_bundle_ids: list[str] = Field(default_factory=list)
    testimony_bundle_ids: list[str] = Field(default_factory=list)
    counter_bundle_ids: list[str] = Field(default_factory=list)
    metadata_ids: list[str] = Field(default_factory=list)
    interpretive_notes: list[str] = Field(default_factory=list)
    insufficiency_notes: list[str] = Field(default_factory=list)


class Citation(BaseModel):
    """A verified citation linking an answer claim to its evidence."""

    ref: str = Field(..., description="Reference marker in the answer")
    type: str = Field(..., description="'node' or 'passage'")
    id: str = Field(..., description="Node or passage ID")
    label: str = Field(..., description="Display label")
    layer: EvidenceLayer = Field(EvidenceLayer.PRIMARY)
    confidence: float | None = Field(None, ge=0.0, le=1.0)
    verified: bool = Field(False)
    verification_note: str | None = None


class ScholarlyAnswer(BaseModel):
    """Final output of the agentic RAG pipeline."""

    answer: str
    question: str
    complexity: QueryComplexity = Field(QueryComplexity.MEDIUM)
    query_type: Any = Field(default="temporal")
    citations: list[Citation] = Field(default_factory=list)
    seed_nodes: list[str] = Field(default_factory=list)
    context_nodes: list[str] = Field(default_factory=list)
    passages_used: int = Field(0, ge=0)
    iterations: int = Field(1)
    sub_queries: list[str] = Field(default_factory=list)
    quality_badge: str = ""
    self_rag_evaluation: Any = None
    crag_validation: Any = None
    insufficient_evidence: bool = False
    grounding_policy: GroundingPolicy = GroundingPolicy.MIXED_EVIDENCE
    claim_ledger: list[ClaimLedgerItem] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


@dataclass
class RAGState:
    """Mutable state accumulating through the pydantic-graph FSM."""

    question: str = ""
    sub_queries: list[str] = field(default_factory=list)
    complexity: QueryComplexity = QueryComplexity.MEDIUM

    query_type: Any = None
    pipeline_config: Any = None

    expanded_query: str | None = None
    expansion_terms: Any = None

    primary_evidence: list[Evidence] = field(default_factory=list)
    secondary_evidence: list[Evidence] = field(default_factory=list)
    evidence_bundles: list[EvidenceBundle] = field(default_factory=list)

    seed_node_ids: list[str] = field(default_factory=list)
    context_node_ids: list[str] = field(default_factory=list)

    accumulated_context: str = ""
    context_pack: ContextPack = field(default_factory=ContextPack)

    raw_answer: str = ""
    citations: list[Citation] = field(default_factory=list)

    sufficiency_score: float = 0.0
    iteration: int = 0
    max_iterations: int = 5
    passages_used: int = 0

    crag_validation: Any = None
    insufficient_evidence: bool = False

    self_rag_evaluation: Any = None
    self_rag_iterations: int = 0
    max_self_rag_iterations: int = 2
    quality_badge: str = ""

    grounding_policy: GroundingPolicy = GroundingPolicy.MIXED_EVIDENCE
    retrieval_budget: RetrievalBudget = field(default_factory=RetrievalBudget)
    research_notebook: ResearchNotebook = field(default_factory=ResearchNotebook)
    scholarly_dossier: ScholarlyDossier = field(default_factory=ScholarlyDossier)
    claim_ledger: list[ClaimLedgerItem] = field(default_factory=list)

    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.query_type is None:
            from eleutheria_graphrag.agents.pipeline_config import QueryType

            self.query_type = QueryType.TEMPORAL
        if self.pipeline_config is None:
            from eleutheria_graphrag.agents.pipeline_config import PipelineConfig

            self.pipeline_config = PipelineConfig()

    def all_evidence(self) -> list[Evidence]:
        """Return primary + secondary evidence combined."""
        return self.primary_evidence + self.secondary_evidence

    def primary_node_ids(self) -> set[str]:
        """IDs of all primary evidence items."""
        return {e.id for e in self.primary_evidence}

    def secondary_node_ids(self) -> set[str]:
        """IDs of all secondary evidence items."""
        return {e.id for e in self.secondary_evidence}

    def all_node_ids(self) -> set[str]:
        """All unique evidence IDs."""
        return self.primary_node_ids() | self.secondary_node_ids()

    def bundle_ids(self) -> set[str]:
        """All current evidence bundle identifiers."""
        return {bundle.bundle_id for bundle in self.evidence_bundles}
