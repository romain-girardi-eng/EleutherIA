"""
RAG pipeline state — accumulated context, evidence, and citations.

This state flows through the pydantic-graph FSM, accumulating evidence
from primary sources, secondary scholarship, and passage citations
as nodes execute and retrieve information.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


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
    HYDE_SEARCH = "hyde_search"  # NEW: hypothetical document embedding search
    CRAG_SECONDARY = "crag_secondary"  # NEW: CRAG-triggered secondary retrieval
    TREE_REASONING = "tree_reasoning"  # NEW: PageIndex-inspired tree navigation


class EvidenceLayer(str, Enum):
    """Primary (ancient) vs secondary (modern) source layer."""

    PRIMARY = "primary"
    SECONDARY = "secondary"


# ---------------------------------------------------------------------------
# Evidence & Citation models
# ---------------------------------------------------------------------------


class Evidence(BaseModel):
    """A single piece of retrieved evidence (KG node or passage)."""

    id: str = Field(..., description="Node ID or passage ID")
    label: str = Field("", description="Human-readable label")
    type: str = Field("", description="Node type (Person, Concept, etc.) or 'passage'")
    layer: EvidenceLayer = Field(EvidenceLayer.PRIMARY)
    source: EvidenceSource = Field(EvidenceSource.SEMANTIC_SEARCH)
    description: str = Field("", description="Node description or passage text")
    score: float = Field(0.0, description="Relevance score (0-1)")

    # Passage-specific fields
    passage_id: str | None = Field(
        None, description="Database passage_id if applicable"
    )
    cts_urn: str | None = Field(None, description="CTS URN for ancient texts")
    canonical_ref: str | None = Field(None, description="Canonical reference string")
    author: str | None = None
    work_title: str | None = None
    text_content: str | None = Field(None, description="Full passage text from DB")
    confidence: float | None = Field(None, ge=0.0, le=1.0)

    # KG-specific fields
    period: str | None = None
    school: str | None = None
    role: str | None = None

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict)


class Citation(BaseModel):
    """A verified citation linking an answer claim to its evidence."""

    ref: str = Field(..., description="Reference marker in the answer (e.g. '1', 'P2')")
    type: str = Field(..., description="'node' or 'passage'")
    id: str = Field(..., description="Node or passage ID")
    label: str = Field(..., description="Display label")
    layer: EvidenceLayer = Field(EvidenceLayer.PRIMARY)
    confidence: float | None = Field(None, ge=0.0, le=1.0)
    verified: bool = Field(
        False, description="Whether citation was verified against DB"
    )
    verification_note: str | None = Field(
        None, description="Verification result detail"
    )


class ScholarlyAnswer(BaseModel):
    """Final output of the agentic RAG pipeline."""

    answer: str = Field(..., description="Generated scholarly answer")
    question: str = Field(..., description="Original question")
    complexity: QueryComplexity = Field(QueryComplexity.MEDIUM)
    query_type: Any = Field(
        default="temporal", description="NEW: 5-type query classification"
    )  # QueryType
    citations: list[Citation] = Field(default_factory=list)
    seed_nodes: list[str] = Field(default_factory=list)
    context_nodes: list[str] = Field(default_factory=list)
    passages_used: int = Field(0, ge=0)
    iterations: int = Field(1, description="Number of retrieval iterations used")
    sub_queries: list[str] = Field(default_factory=list)
    quality_badge: str = Field("", description="NEW: High / Medium / Low")
    self_rag_evaluation: Any = Field(None, description="NEW: SelfRAGEvaluation | None")
    crag_validation: Any = Field(None, description="NEW: CRAGValidation | None")
    insufficient_evidence: bool = Field(
        False, description="NEW: evidence insufficiency flag"
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Mutable pipeline state (flows through the FSM graph)
# ---------------------------------------------------------------------------


@dataclass
class RAGState:
    """Mutable state accumulating through the pydantic-graph FSM."""

    # Input
    question: str = ""
    sub_queries: list[str] = field(default_factory=list)
    complexity: QueryComplexity = QueryComplexity.MEDIUM

    # --- Classification (NEW) ---
    query_type: Any = None  # QueryType — set in __post_init__
    pipeline_config: Any = None  # PipelineConfig — set in __post_init__

    # --- Query expansion (NEW) ---
    expanded_query: str | None = None
    expansion_terms: Any = None  # ExpansionTerms | None

    # Retrieved evidence, separated by layer
    primary_evidence: list[Evidence] = field(default_factory=list)
    secondary_evidence: list[Evidence] = field(default_factory=list)

    # Seed nodes from initial semantic search
    seed_node_ids: list[str] = field(default_factory=list)

    # All context node IDs seen
    context_node_ids: list[str] = field(default_factory=list)

    # Built context string for LLM
    accumulated_context: str = ""

    # Generated answer (before verification)
    raw_answer: str = ""

    # Verified citations
    citations: list[Citation] = field(default_factory=list)

    # Sufficiency tracking
    sufficiency_score: float = 0.0
    iteration: int = 0
    max_iterations: int = 5

    # Passages fetched
    passages_used: int = 0

    # --- CRAG validation (NEW) ---
    crag_validation: Any = None  # CRAGValidation | None
    insufficient_evidence: bool = False

    # --- Self-RAG (NEW) ---
    self_rag_evaluation: Any = None  # SelfRAGEvaluation | None
    self_rag_iterations: int = 0
    max_self_rag_iterations: int = 2
    quality_badge: str = ""  # "High" / "Medium" / "Low"

    # Metadata for debugging / logging
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Set defaults that require import (avoids circular imports)."""
        if self.query_type is None:
            from eleutheria_graphrag.agents.pipeline_config import QueryType

            self.query_type = QueryType.TEMPORAL
        if self.pipeline_config is None:
            from eleutheria_graphrag.agents.pipeline_config import PipelineConfig

            self.pipeline_config = PipelineConfig()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

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
