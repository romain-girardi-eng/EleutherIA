"""
Shared dependency injection for all backend services.

Holds singleton instances of DatabaseService, LLMService, GraphRAGService,
KGAnalytics, KGCache, RerankerService, and CitationVerifier — initialized
once at startup and shared across all routes.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any

from eleutheria_database.services.db import DatabaseService
from eleutheria_database.services.hybrid_search import HybridSearchService
from eleutheria_graphrag.services.graphrag_service import GraphRAGService
from eleutheria_graphrag.services.llm_service import LLMService, ModelProvider
from eleutheria_kg.services.analytics import KGAnalytics
from eleutheria_kg.services.cache import KGCache
from eleutheria_kg.services.snapshot import (
    load_kg_snapshot,
    materialize_inverse_edges,
    snapshot_available,
)

from backend.services.credentials import CredentialsBridge, get_credentials_bridge

logger = logging.getLogger(__name__)


def _env_flag(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _preferred_provider() -> ModelProvider:
    raw = (
        os.getenv("LLM_PREFERRED_PROVIDER", ModelProvider.CODEX.value)
        .strip()
        .lower()
    )
    try:
        return ModelProvider(raw)
    except ValueError:
        logger.warning("Unknown LLM_PREFERRED_PROVIDER=%s, falling back to codex", raw)
        return ModelProvider.CODEX


@dataclass
class Services:
    """Container for all shared service instances."""

    db: DatabaseService = field(default_factory=DatabaseService)
    credentials: CredentialsBridge = field(default_factory=get_credentials_bridge)
    llm: LLMService = field(
        default_factory=lambda: LLMService(preferred_provider=_preferred_provider())
    )
    analytics: KGAnalytics = field(default_factory=KGAnalytics)
    cache: KGCache = field(default_factory=lambda: KGCache(default_ttl=300))
    search: HybridSearchService | None = None
    graphrag: GraphRAGService | None = None
    kg_source: str = "unknown"

    async def initialize(self) -> None:
        """Connect to all external services and build derived services."""
        # 0. Resolve LLM provider keys via the credentials bridge. When
        # EXTERNAL_INTEGRATION is off (default for local dev), the bridge
        # transparently falls back to environment variables — so behaviour
        # is unchanged unless the platform is wired up.
        codex_key = await self.credentials.get_llm_key("codex")
        claude_key = await self.credentials.get_llm_key("claude")
        gemini_key = await self.credentials.get_llm_key("gemini")
        self.llm = LLMService(
            preferred_provider=_preferred_provider(),
            codex_api_key=codex_key,
            claude_api_key=claude_key,
            gemini_api_key=gemini_key,
        )

        # 1. Database. If a KG snapshot is available, the backend can still
        # serve KG/GraphRAG routes while PostgreSQL is being restored.
        database_required = _env_flag("DATABASE_REQUIRED", not snapshot_available())
        try:
            await self.db.connect()
        except Exception:
            if database_required:
                raise
            logger.warning("PostgreSQL unavailable - continuing with KG snapshot only")

        # 2. Hybrid search (wraps db)
        self.search = HybridSearchService(self.db) if self.db.is_connected() else None

        # 3. Load KG data into analytics
        kg_data = await self._load_kg_data()
        self.analytics.set_data(kg_data)

        # 4. Optional: Cross-encoder reranker
        reranker = self._init_reranker()

        # 5. Citation verifier
        verifier = self._init_verifier()

        # 6. GraphRAG (wraps db + llm + new services)
        self.graphrag = GraphRAGService(
            db_service=self.db,
            llm_service=self.llm,
            analytics=self.analytics,
            search_service=self.search,
            reranker=reranker,
            verifier=verifier,
            kg_data=kg_data,
        )
        await self.graphrag.load_kg()

    async def _load_kg_data(self) -> dict[str, Any]:
        """Load KG nodes and edges from DB, falling back to local snapshot."""
        if self.db.is_connected():
            try:
                nodes = await self.db.fetch("""
                    SELECT
                        node_id as id,
                        label,
                        type,
                        description,
                        period,
                        COALESCE(metadata->>'school', metadata->>'school_affiliation') as school,
                        COALESCE(metadata->>'role', metadata->>'scholarly_role') as role,
                        metadata,
                        metadata->>'date' as date,
                        metadata->>'birth' as birth,
                        metadata->>'death' as death,
                        metadata->>'floruit' as floruit,
                        metadata->>'approximate_dates' as approximate_dates,
                        metadata->>'scholarly_role' as scholarly_role
                    FROM free_will.kg_nodes
                """)
                edges = await self.db.fetch("""
                    SELECT
                        source_id as source,
                        target_id as target,
                        relation,
                        metadata->>'description' as description,
                        CASE
                            WHEN COALESCE(metadata->>'weight', '') ~ '^[0-9]+(\\.[0-9]+)?$'
                                THEN (metadata->>'weight')::double precision
                            ELSE 1.0
                        END as weight,
                        metadata
                    FROM free_will.kg_edges
                """)
                self.kg_source = "database"
                return {"nodes": nodes, "edges": materialize_inverse_edges(edges)}
            except Exception:
                logger.exception("Failed to load KG from PostgreSQL")
                if not snapshot_available():
                    raise

        kg_data = load_kg_snapshot()
        self.kg_source = "snapshot"
        return kg_data

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
