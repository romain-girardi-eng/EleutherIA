"""
Pydantic models for GraphRAG queries and responses.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class QueryRequest(BaseModel):
    """Request model for GraphRAG query."""

    model_config = ConfigDict(from_attributes=True)

    question: str = Field(..., min_length=3, description="User question")
    semantic_k: int = Field(10, ge=1, le=50, description="Semantic search results")
    graph_depth: int = Field(2, ge=1, le=4, description="Graph traversal depth")
    max_context_nodes: int = Field(30, ge=5, le=100, description="Max nodes in context")
    include_passages: bool = Field(True, description="Include ancient passages")
    stream: bool = Field(False, description="Enable streaming response")
    mode: str = Field(
        "fast",
        description=(
            "Pipeline depth: 'fast' (single-pass) or 'deep' (two-pass "
            "adversarial counter-evidence hunt + methodology/polishing)."
        ),
        pattern="^(fast|deep)$",
    )


class Citation(BaseModel):
    """A citation reference in the answer."""

    model_config = ConfigDict(from_attributes=True)

    ref: str = Field(..., description="Reference marker (e.g., '1', 'P2')")
    type: str = Field(..., description="Citation type: 'node' or 'passage'")
    id: str = Field(..., description="Node or passage ID")
    label: str = Field(..., description="Display label")
    confidence: float | None = Field(
        None, ge=0.0, le=1.0, description="Citation confidence"
    )


class SourceCitationMetadata(BaseModel):
    """Metadata for a source citation, aligned with TS SourceCitation.metadata."""

    model_config = ConfigDict(from_attributes=True)

    school: str | None = Field(
        None, description="Philosophical school (e.g., Stoic, Epicurean)"
    )
    period: str | None = Field(
        None, description="Historical period (e.g., Hellenistic, Imperial)"
    )
    author: str | None = Field(None, description="Ancient author name")
    confidence: float = Field(
        0.0, ge=0.0, le=1.0, description="Source confidence score"
    )


class SourceCitation(BaseModel):
    """A structured source citation aligned with the TS SourceCitation interface."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Unique citation index")
    node_id: str = Field(..., description="Knowledge graph node ID")
    node_label: str = Field(..., description="Display label for the node")
    node_type: str = Field(
        ..., description="Node type (e.g., philosopher, concept, argument)"
    )
    content: str = Field(..., description="Cited content or description")
    url: str | None = Field(None, description="Optional URL to source material")
    metadata: SourceCitationMetadata = Field(
        default_factory=SourceCitationMetadata, description="Citation metadata"
    )


class EvidenceMapEntry(BaseModel):
    """An entry in the evidence map, aligned with the TS EvidenceMap value type."""

    model_config = ConfigDict(from_attributes=True)

    node_id: str = Field(..., description="Knowledge graph node ID")
    node_path: list[str] | None = Field(None, description="Traversal path to this node")
    confidence: float = Field(
        0.0, ge=0.0, le=1.0, description="Evidence confidence score"
    )
    type: str = Field(
        ..., description="Evidence type (e.g., direct, inferred, contextual)"
    )


class QualityMetrics(BaseModel):
    """Quality metrics for the generated answer, aligned with TS qualityMetrics."""

    model_config = ConfigDict(from_attributes=True)

    completeness: float = Field(
        0.0, ge=0.0, le=1.0, description="Answer completeness score"
    )
    accuracy: float = Field(0.0, ge=0.0, le=1.0, description="Answer accuracy score")
    clarity: float = Field(0.0, ge=0.0, le=1.0, description="Answer clarity score")


class ClaimLedgerEntry(BaseModel):
    """Public-facing claim with optional OWL-RL proof chain.

    The ``proof_chain`` field carries the derivation when the claim
    depends on an inferred (non-asserted) triple, surfaced by the
    ontology-aware retrieval layer. ``None`` for directly-asserted
    claims (Phase D activation).
    """

    model_config = ConfigDict(from_attributes=True)

    claim: str = Field(..., description="The claim text")
    evidence_ids: list[str] = Field(
        default_factory=list, description="Evidence node / bundle IDs"
    )
    support_type: str = Field("passage", description="passage | metadata | derived")
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    status: str = Field("supported", description="supported | insufficient")
    proof_chain: list[dict[str, Any]] | None = Field(
        None,
        description=(
            "OWL-RL derivation steps when the claim relies on an inferred "
            "triple. Each step: rule, premises ([[s,p,o], ...]), conclusion "
            "([s,p,o]), confidence. None when directly asserted."
        ),
    )


class QueryResponse(BaseModel):
    """Response model for GraphRAG query, aligned with the TS AgenticAnswer interface."""

    model_config = ConfigDict(from_attributes=True)

    answer: str = Field(..., description="Generated answer")
    question: str = Field(..., description="Original question")
    confidence: float = Field(
        0.0, ge=0.0, le=1.0, description="Overall answer confidence"
    )
    citations: list[Citation] = Field(
        default_factory=list, description="Extracted citations"
    )
    sources: list[SourceCitation] = Field(
        default_factory=list, description="Structured source citations"
    )
    evidence_map: dict[str, EvidenceMapEntry] = Field(
        default_factory=dict, description="Evidence map keyed by claim or node ID"
    )
    quality_metrics: QualityMetrics | None = Field(
        None, description="Quality metrics for the answer"
    )
    seed_nodes: list[str] = Field(
        default_factory=list, description="Semantic search seed nodes"
    )
    context_nodes: list[str] = Field(
        default_factory=list, description="All context nodes"
    )
    passages_used: int = Field(0, ge=0, description="Number of passages in context")
    claim_ledger: list[ClaimLedgerEntry] = Field(
        default_factory=list,
        description=(
            "Atomic, evidence-linked claims. Entries derived from inferred "
            "(inverseOf / transitivity) edges carry a ``proof_chain``."
        ),
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
