"""
RAG pipeline state and shared models for the scholarly agent.

The agent keeps an explicit research notebook, adaptive retrieval budgets,
evidence bundles, and a claim ledger so that retrieval, reasoning, and
grounding stay inspectable end-to-end.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


def _default_model_window() -> int:
    """Synthesis context window used to size the per-layer packing budgets.

    Defaults to the full 1M-token Gemini window. The public/streaming path can
    shrink this via ``ELEUTHERIA_SYNTH_CONTEXT_TOKENS`` so that
    ``_build_context_pack`` packs fewer evidence bundles into the render prompt
    — profiling showed the unbounded 552k-token passage budget (up to 200
    bundles) feeds a large synthesis prompt. Capping it trims synthesis +
    verification latency on cold queries without dropping the agent's
    highest-scored evidence (bundles are packed best-first). Values below 8192
    are ignored.
    """
    raw = os.getenv("ELEUTHERIA_SYNTH_CONTEXT_TOKENS")
    if raw:
        try:
            value = int(raw)
        except ValueError:
            return 1_000_000
        if value >= 8192:
            return value
    return 1_000_000


class QueryComplexity(StrEnum):
    """Classification tier for adaptive query routing."""

    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


class EvidenceSource(StrEnum):
    """Where a piece of evidence originated."""

    SEMANTIC_SEARCH = "semantic_search"
    GRAPH_TRAVERSAL = "graph_traversal"
    HYBRID_SEARCH = "hybrid_search"
    PASSAGE_CITATION = "passage_citation"
    DIRECT_LOOKUP = "direct_lookup"
    CRAG_SECONDARY = "crag_secondary"
    TREE_REASONING = "tree_reasoning"


class EvidenceLayer(StrEnum):
    """Primary (ancient) vs secondary (modern) source layer."""

    PRIMARY = "primary"
    SECONDARY = "secondary"


# Relations that encode scholarly disagreement / dialectical structure.
# When a ``get_neighbors`` / ``explore_subgraph`` result carries one of these,
# the collector retains BOTH endpoints + the relation + direction as a
# ``DialecticalEdge`` (Scholar-RAG M0b). These are the fault-line edges the old
# pipeline dropped at ingestion (the literal "0 edges used" bug, failure-map F1).
DIALECTICAL_RELATIONS: frozenset[str] = frozenset(
    {
        "opposes",
        "critiques",
        "responds_to",
        "refutes",
        "contrasts_with",
        "agrees_with",
        "supports",
        "participates_in",
        "contributes_to",
        "has_position",
        "advanced_in",
        "engages_with",
        "interprets",
    }
)


class DialecticalEdge(BaseModel):
    """A retained dialectical (disagreement-bearing) edge between two KG nodes.

    Unlike the bare ``Evidence`` the collector kept before, this preserves the
    full relational triple — both endpoints, the ``relation``, and the
    ``direction`` — so the synthesis layer can narrate "A --opposes--> B" fault
    lines instead of being structurally edge-blind. Scholar-RAG M0b.
    """

    source_id: str
    relation: str
    target_id: str
    direction: str = ""  # "outgoing" | "incoming" | "" (already canonicalised)
    weight: float | None = None
    source_label: str = ""
    target_label: str = ""
    source_type: str = ""
    target_type: str = ""


def scholar_rag_enabled() -> bool:
    """Whether the Scholar-RAG (G6) path is active.

    Gated by ``ELEUTHERIA_SCHOLAR_RAG`` (default OFF). The new debate-first
    tools, planner, dossier, and dialectical synthesis are only *consumed* when
    this is true; the additive state fields and tool definitions are inert until
    a consumer reads them, so the existing default pipeline is unaffected.
    """
    raw = os.getenv("ELEUTHERIA_SCHOLAR_RAG", "")
    return raw.strip().lower() in {"1", "true", "yes", "on"}


# ── Scholar-RAG controversy dossier (ARCHITECTURE §3.1) ──────────────────────
# The typed intermediate object the M1 tools populate and M3 assembles into a
# ``ControversyMap``. Defined here (additive, inert without a consumer) so the
# debate tools and their tests share one canonical shape. Star-tolerant flat
# links, raw incident-edge ordering — NO strength scalar (amputation 1).


class AnswerShape(StrEnum):
    """The six scholarly answer shapes (+ factual short-circuit)."""

    SURVEY_OF_DEBATES = "survey_of_debates"
    CONCEPT_GENEALOGY = "concept_genealogy"
    TRANSMISSION_TRACE = "transmission_trace"
    POSITION_COMPARISON = "position_comparison"
    PRIMARY_TEXT_EXEGESIS = "primary_text_exegesis"
    DOXOGRAPHICAL_SYNTHESIS = "doxographical_synthesis"
    FACTUAL_LOOKUP = "factual_lookup"


class GraphPattern(BaseModel):
    """One graph-entry pattern in a ResearchPlan DAG (ARCHITECTURE §1).

    A typed, inspectable retrieval program — the named ``edge_program`` is the
    audit surface the plan can be diffed against the graph before retrieval
    runs. NOT a fixed list of section titles.
    """

    intent: str = ""  # "find fault lines in discovery-of-will debate"
    entry: str = "debate"  # debate|concept|person|passage|school|position
    seed_query: str = ""  # lexical/lemmatic seed to locate entry nodes
    edge_program: list[str] = Field(default_factory=list)  # ordered relations to walk
    depth: int = 2
    want_bilingual: bool = True


class ResearchPlan(BaseModel):
    """The typed retrieval program emitted by PlanResearch (ARCHITECTURE §1).

    One primary + optional secondary shape, a small DAG of GraphPatterns
    (executed in topological order), and an ADAPTIVE answer skeleton that the
    synthesiser may override — never a hard template.
    """

    primary_shape: AnswerShape = AnswerShape.SURVEY_OF_DEBATES
    secondary_shape: AnswerShape | None = None
    patterns: list[GraphPattern] = Field(default_factory=list)  # 3-6 patterns
    answer_skeleton: list[str] = Field(default_factory=list)  # HINTS, never a template
    budget_tier: str = "standard"  # quick|standard|deep
    rationale: str = ""  # why this shape (audit surface)


class PassageRef(BaseModel):
    """A contested primary passage, original + English, fully untruncated."""

    passage_id: str
    work: str = ""
    author: str = ""
    canonical_ref: str = ""
    cts_urn: str | None = None
    original_text: str = ""  # FULL, untruncated, polytonic diacritics preserved
    english_text: str | None = None  # _en counterpart via has_translation
    language: str = ""


class GroundedPosition(BaseModel):
    """A scholarly position, ALWAYS a holder's claim — never asserted as truth."""

    position_id: str
    holder: str = ""
    holder_node_id: str = ""
    holder_type: str = "modern_scholar"  # modern_scholar | ancient_author | school
    claim: str = ""
    publication: str | None = None
    publication_node_id: str | None = None
    page_grounding: str | None = None  # present in metadata, else None (never invented)
    primary_support: list[str] = Field(default_factory=list)  # PassageRef ids


class DialecticalLink(BaseModel):
    """FLAT and STAR-TOLERANT — not pro/con tagging (ARCHITECTURE §3.1)."""

    relation: str
    from_id: str
    to_id: str
    from_holder: str = ""
    to_holder: str = ""
    gloss: str | None = None


class FrameCompleteness(BaseModel):
    """Boolean + raw-count completeness signals — no score, no float."""

    has_two_sides: bool = False  # ≥1 position with ≥1 attacker
    has_orphan_attack: bool = False  # attacker, no surfaced defender ⇒ expand
    has_primary_grounding: bool = False  # ≥1 contested passage
    incident_edge_count: int = 0  # raw count — drives ordering (NO score)


class ControversyFrame(BaseModel):
    """One scholarly fault line: positions, the flat links, contested texts."""

    frame_id: str
    debate_node_id: str | None = None
    title: str = ""
    period: str = ""
    positions: list[GroundedPosition] = Field(default_factory=list)
    links: list[DialecticalLink] = Field(default_factory=list)
    contested_passages: list[PassageRef] = Field(default_factory=list)
    completeness: FrameCompleteness = Field(default_factory=FrameCompleteness)
    used_fallback: bool = False  # empty-debate-node fallback fired


class ControversyMap(BaseModel):
    """The tri-purpose dossier (ARCHITECTURE §3.1): retrieval target, synthesis
    context, and verification oracle in one typed object.

    A list of ``ControversyFrame``s ordered by raw ``incident_edge_count`` (NO
    score, NO DF-QuAD, NO base_strength/contestedness float — amputation 1) plus
    a pool of standalone exegesis passages and a record of planner patterns that
    retrieval under-filled (the completeness critic's denominator substrate).
    """

    question_frame: str = ""
    shape: AnswerShape = AnswerShape.SURVEY_OF_DEBATES
    frames: list[ControversyFrame] = Field(default_factory=list)
    exegesis_units: list[PassageRef] = Field(default_factory=list)
    coverage_gaps: list[str] = Field(default_factory=list)
    provenance: dict[str, PassageRef] = Field(default_factory=dict)

    def order_frames(self) -> None:
        """Sort frames by raw incident dialectical-edge count, desc (no score)."""
        self.frames.sort(key=lambda f: f.completeness.incident_edge_count, reverse=True)


class GroundingPolicy(StrEnum):
    """Policy for which evidence types may support a claim."""

    MIXED_EVIDENCE = "mixed_evidence"
    PASSAGE_FIRST = "passage_first"


class ClaimStatus(StrEnum):
    """Support status for a drafted claim."""

    SUPPORTED = "supported"
    INSUFFICIENT = "insufficient"
    # Scholar-RAG: a cite-as-you-write marker that does NOT resolve to a map id
    # (a hallucinated id) — emitted UNVERIFIED for the M5 referee to hard-reject.
    UNVERIFIED = "unverified"


class RetrievalBudget(BaseModel):
    """Token budgets for long-context packing and adaptive retrieval."""

    model_window: int = Field(default_factory=_default_model_window, ge=8192)
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
    """Atomic, evidence-linked claim produced before prose rendering.

    The optional ``proof_chain`` field carries the OWL-RL derivation when
    the claim depends on an inferred (non-asserted) fact. Each chain
    entry is shaped like
    ``{"rule", "premises": [[s, p, o], ...], "conclusion": [s, p, o], "confidence"}``,
    matching :func:`eleutheria_kg.semantic.proof.serialize_proof_chain`.
    Absent for directly-asserted claims (backward-compatible default).
    """

    claim: str
    evidence_ids: list[str] = Field(default_factory=list)
    facet_id: str | None = None
    evidence_class: str = "direct_text"
    quote_original: str | None = None
    quote_translation: str | None = None
    support_type: str = "passage"
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    status: ClaimStatus = ClaimStatus.SUPPORTED
    proof_chain: list[dict[str, Any]] | None = Field(
        default=None,
        description=(
            "Optional OWL-RL derivation when the claim relies on an inferred "
            "triple. Each step: rule, premises (list of [s, p, o]), "
            "conclusion ([s, p, o]), confidence. None for asserted claims."
        ),
    )


class ContextPack(BaseModel):
    """Packed long-context payload broken into semantic layers."""

    kg_metadata: list[str] = Field(default_factory=list)
    section_summaries: list[str] = Field(default_factory=list)
    passage_bundles: list[EvidenceBundle] = Field(default_factory=list)
    prompt_context: str = ""
    token_estimate: int = Field(0, ge=0)
    bundle_refs: dict[str, str] = Field(default_factory=dict)
    node_refs: dict[str, str] = Field(default_factory=dict)
    # Scholar-RAG M3: the ``## Controversy Frames`` layer. The serialised frames
    # give the synthesis prompt a first-class edge slot (failure-map F2 fix).
    # Populated only when ELEUTHERIA_SCHOLAR_RAG is on; empty/inert by default.
    controversy_frames: list[ControversyFrame] = Field(default_factory=list)


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
class ReasoningStep:
    """One step of the FSM reasoning trace."""

    node_name: str
    timestamp_ms: int
    duration_ms: int
    model: str | None
    prompt_summary: str
    full_prompt_tokens: int
    raw_output: str
    thinking: str | None
    parsed_result: dict[str, Any] | None
    skipped: bool
    skip_reason: str | None


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

    # Dialectical (disagreement-bearing) edges retained at ingestion so the
    # synthesis layer can narrate real fault lines. Populated by
    # EvidenceCollector.populate_state from get_neighbors / explore_subgraph
    # results whose relation ∈ DIALECTICAL_RELATIONS. Scholar-RAG M0b — the
    # fix for the "0 edges used" root cause (failure-map F1). Empty by default.
    dialectical_edges: list[DialecticalEdge] = field(default_factory=list)

    # Scholar-RAG M2: the typed retrieval program (question -> answer shape).
    # Set by PlanResearch only when ELEUTHERIA_SCHOLAR_RAG is on; None by default
    # so the legacy facet picker stays the default path.
    research_plan: ResearchPlan | None = None

    # Scholar-RAG M3: the assembled controversy dossier (frames + exegesis +
    # coverage gaps). Set by the M3 assembler under the flag; None by default.
    controversy_map: ControversyMap | None = None

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
    reasoning_trace: list[ReasoningStep] = field(default_factory=list)
    retrieval_mode: str = "auto"  # "auto" | "vector" | "sql"
    selected_model: str = "gemini-3.1-pro"

    # Triples derived via the ontology-aware retrieval layer (Phase D).
    # Each entry is (subject_node_id, relation, object_node_id) — the
    # *conclusion* of a single-step inverseOf inference whose premise is
    # the asserted reverse edge in ``deps.outgoing_edges`` /
    # ``deps.incoming_edges``. Consumed by ``DraftClaimLedger`` to attach
    # a proof chain when a supporting edge is inferred rather than
    # directly asserted.
    inferred_edges: set[tuple[str, str, str]] = field(default_factory=set)

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
