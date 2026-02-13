"""
Shared dependency injection for all backend services.

Holds singleton instances of DatabaseService, QdrantService, LLMService,
GraphRAGService, KGAnalytics, KGCache, RerankerService, and CitationVerifier
— initialized once at startup and shared across all routes.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from eleutheria_database.services.db import DatabaseService
from eleutheria_database.services.hybrid_search import HybridSearchService
from eleutheria_graphrag.services.graphrag_service import GraphRAGService
from eleutheria_graphrag.services.llm_service import LLMService, ModelProvider
from eleutheria_kg.services.analytics import KGAnalytics
from eleutheria_kg.services.cache import KGCache
from eleutheria_kg.services.qdrant import QdrantService

logger = logging.getLogger(__name__)


@dataclass
class Services:
    """Container for all shared service instances."""

    db: DatabaseService = field(default_factory=DatabaseService)
    qdrant: QdrantService = field(default_factory=QdrantService)
    llm: LLMService = field(
        default_factory=lambda: LLMService(preferred_provider=ModelProvider.GEMINI)
    )
    analytics: KGAnalytics = field(default_factory=KGAnalytics)
    cache: KGCache = field(default_factory=lambda: KGCache(default_ttl=300))
    search: HybridSearchService | None = None
    graphrag: GraphRAGService | None = None

    async def initialize(self) -> None:
        """Connect to all external services and build derived services."""
        # 1. Database
        await self.db.connect()

        # 2. Qdrant
        await self.qdrant.connect()

        # 3. Hybrid search (wraps db)
        self.search = HybridSearchService(self.db)

        # 4. Load KG data into analytics
        kg_data = await self._load_kg_data()
        self.analytics.set_data(kg_data)

        # 5. Optional: Cross-encoder reranker
        reranker = self._init_reranker()

        # 6. Citation verifier
        verifier = self._init_verifier()

        # 7. GraphRAG (wraps db + qdrant + llm + new services)
        self.graphrag = GraphRAGService(
            db_service=self.db,
            qdrant_service=self.qdrant,
            llm_service=self.llm,
            analytics=self.analytics,
            search_service=self.search,
            reranker=reranker,
            verifier=verifier,
        )
        await self.graphrag.load_kg()

    async def _load_kg_data(self) -> dict[str, Any]:
        """Load KG nodes and edges from the database."""
        nodes = await self.db.fetch("""
            SELECT
                node_id as id, label, type, description,
                period, school, role, metadata
            FROM free_will.kg_nodes
        """)
        edges = await self.db.fetch("""
            SELECT
                source_id as source, target_id as target,
                relation, description, weight
            FROM free_will.kg_edges
        """)
        return {"nodes": nodes, "edges": edges}

    def _init_reranker(self) -> Any:
        """Initialize the cross-encoder reranker (optional, CPU-based)."""
        try:
            from eleutheria_graphrag.services.reranker import RerankerService

            reranker = RerankerService()
            logger.info("RerankerService initialized")
            return reranker
        except ImportError:
            logger.info("sentence-transformers not installed, reranker disabled")
            return None

    def _init_verifier(self) -> Any:
        """Initialize the citation verifier."""
        try:
            from eleutheria_graphrag.services.citation_verifier import (
                CitationVerifier,
            )

            verifier = CitationVerifier(llm=self.llm, db=self.db)
            logger.info("CitationVerifier initialized")
            return verifier
        except ImportError:
            logger.info("CitationVerifier import failed, disabled")
            return None

    async def shutdown(self) -> None:
        """Gracefully close all connections."""
        if self.graphrag:
            await self.graphrag.close()
        await self.qdrant.close()
        await self.db.close()


# Global singleton — set during app lifespan
services: Services | None = None


def get_services() -> Services:
    """Get the global Services instance (raises if not initialized)."""
    if services is None:
        raise RuntimeError("Services not initialized — app lifespan did not run")
    return services


def get_db() -> DatabaseService:
    return get_services().db


def get_qdrant() -> QdrantService:
    return get_services().qdrant


def get_search() -> HybridSearchService:
    svc = get_services()
    if svc.search is None:
        raise RuntimeError("HybridSearchService not initialized")
    return svc.search


def get_graphrag() -> GraphRAGService:
    svc = get_services()
    if svc.graphrag is None:
        raise RuntimeError("GraphRAGService not initialized")
    return svc.graphrag


def get_analytics() -> KGAnalytics:
    return get_services().analytics


def get_cache() -> KGCache:
    return get_services().cache


def get_llm() -> LLMService:
    return get_services().llm
