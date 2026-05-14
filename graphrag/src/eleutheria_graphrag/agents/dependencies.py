"""
Dependency injection container for the agentic RAG pipeline.

Wraps all external services (DB, LLM, analytics, search, reranker,
citation verifier) into a single Deps dataclass that pydantic-graph nodes
receive via GraphRunContext.deps.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from eleutheria_database.services.db import DatabaseService
    from eleutheria_database.services.hybrid_search import HybridSearchService
    from eleutheria_graphrag.services.citation_verifier import CitationVerifier
    from eleutheria_graphrag.services.citation_verifier_v2 import CitationVerifierV2
    from eleutheria_graphrag.services.llm_service import LLMService
    from eleutheria_graphrag.services.reranker import RerankerService
    from eleutheria_graphrag.services.weighted_traversal import WeightedTraversal
    from eleutheria_kg.services.analytics import KGAnalytics


@dataclass
class Deps:
    """All services required by the agentic RAG pipeline.

    Injected into pydantic-graph nodes via ``GraphRunContext.deps``.
    """

    # Core services (required)
    db: DatabaseService
    llm: LLMService

    # Analytics — used for PageRank / centrality in weighted traversal
    analytics: KGAnalytics | None = None

    # Hybrid search (fulltext + lemmatic + RRF)
    search: HybridSearchService | None = None

    # Weighted graph traversal service
    traversal: WeightedTraversal | None = None

    # Cross-encoder reranker
    reranker: RerankerService | None = None

    # Citation verification — v1 (disabled by default, kept for compatibility).
    verifier: CitationVerifier | None = None

    # Adversarial post-synthesis citation auditor — see
    # ``services/citation_verifier_v2.py``. Optional; when set, the scholarly
    # agent runs it after the synthesizer produces a draft.
    verifier_v2: CitationVerifierV2 | None = None

    # LLM-based scholarly reranker
    llm_reranker: Any | None = None  # LLMRerankerService

    # Tree index service (PageIndex-inspired)
    tree_index: Any | None = None  # TreeIndexService

    # Retrieval strategy (SQL or Snapshot)
    retrieval_strategy: Any | None = None  # RetrievalStrategy

    # Pre-loaded KG data (nodes, edges, lookup indices)
    kg_data: dict[str, Any] = field(default_factory=dict)
    node_lookup: dict[str, dict[str, Any]] = field(default_factory=dict)
    outgoing_edges: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    incoming_edges: dict[str, list[dict[str, Any]]] = field(default_factory=dict)

    # Pre-computed centrality scores (PageRank)
    pagerank_scores: dict[str, float] = field(default_factory=dict)

    # Optional pointer to the live RAGState, attached by graph nodes
    # before invoking retrieval so the strategy layer can record
    # ontology-aware inferred edges into ``state.inferred_edges``.
    # Phase D activation — not part of the dependency contract.
    state: Any | None = None
