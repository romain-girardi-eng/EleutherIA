"""
EleutherIA Main Application — FastAPI orchestrator.

Creates the FastAPI app, initializes all services during lifespan,
mounts package routers, and adds cross-cutting middleware/routes.
"""

import logging
import os
import re
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

# Package routers
from eleutheria_database.api.works import router as works_router
from eleutheria_database.api.works import set_db_service
from eleutheria_graphrag.api.routes import router as graphrag_router
from eleutheria_graphrag.api.routes import set_service as set_graphrag_service
from eleutheria_kg.api.routes import apply_release_headers
from eleutheria_kg.api.routes import router as kg_router
from eleutheria_kg.api.routes import set_services as set_kg_services
from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

import backend.dependencies as deps
from backend.dependencies import Services

# Backend-specific routers
from backend.routes.audit import router as audit_router
from backend.routes.auth import router as auth_router
from backend.routes.community import router as community_router
from backend.routes.contributions import router as contributions_router
from backend.routes.conversations import router as conversations_router
from backend.routes.feedback import router as feedback_router
from backend.routes.graphrag_extras import router as graphrag_extras_router
from backend.routes.kg_extras import router as kg_extras_router
from backend.routes.lemma import router as lemma_router
from backend.routes.opencode_proxy import router as opencode_router
from backend.routes.passages import router as passages_router
from backend.routes.projects import router as projects_router
from backend.routes.search import router as search_router
from backend.routes.share import public_router as share_public_router
from backend.routes.share import router as share_router
from backend.routes.works_extras import (
    citations_router,
    embeddings_router,
    text_router,
    texts_router,
)
from backend.routes.works_extras import (
    router as works_extras_router,
)
from backend.services.rate_limit import LLMRateLimitMiddleware

# Application-wide logging: without an explicit config the root logger stays at
# WARNING and every logger.info diagnostic in the pipeline (provider routing,
# synthesis budget tiers, cache decisions) is silently dropped. LOG_LEVEL is
# already part of the deploy contract; honor it. basicConfig is a no-op when a
# runner (e.g. pytest) configured handlers first, so tests are unaffected.
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)

# Structural placeholder detection: any secret that is too short to resist
# brute force, or that reads like one of the repo's own example values, must
# never reach production — accepting one would let anyone with the repo forge
# JWTs and sign in as any user.
_MIN_JWT_SECRET_LENGTH = 32
_PLACEHOLDER_JWT_PATTERN = re.compile(r"change|placeholder|generate|secret", re.I)


def _assert_jwt_secret_configured() -> None:
    """Refuse to boot when JWT_SECRET_KEY is unset, too short, or placeholder-like.

    Runs at import time (before uvicorn binds a port) so misconfiguration
    surfaces as a hard, loud failure during deploy rather than silently
    accepting forgeable tokens.
    """
    secret = os.getenv("JWT_SECRET_KEY", "").strip()
    if len(secret) < _MIN_JWT_SECRET_LENGTH or _PLACEHOLDER_JWT_PATTERN.search(secret):
        raise RuntimeError(
            "JWT_SECRET_KEY is unset, shorter than "
            f"{_MIN_JWT_SECRET_LENGTH} characters, or looks like a placeholder. "
            'Generate a strong key with `python -c "import secrets; '
            'print(secrets.token_hex(64))"` and set it in the environment '
            "before starting the API."
        )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan: initialize all services on startup, close on shutdown."""
    logger.info("Starting EleutherIA backend...")

    # Initialize shared services
    svc = Services()
    deps.services = svc

    try:
        await svc.initialize()
    except Exception:
        logger.exception("Failed to initialize services")
        raise

    # Inject services into package routers
    set_db_service(svc.db)
    set_kg_services(svc.analytics, svc.cache, svc.db)
    set_graphrag_service(svc.graphrag)

    logger.info("All services initialized — backend ready")
    yield

    # Shutdown
    logger.info("Shutting down EleutherIA backend...")
    await svc.shutdown()
    deps.services = None
    logger.info("Backend shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    _assert_jwt_secret_configured()
    app = FastAPI(
        title="EleutherIA",
        description="FAIR-compliant knowledge graph for ancient philosophical debates on free will",
        version="2.0.0",
        lifespan=lifespan,
    )

    # Compact workspace JSON is deliberately field-thin, but repeated edge
    # keys still make the uncompressed release ~12 MB. Origin compression
    # brings the current complete graph below the 2 MB transfer budget. The
    # Starlette middleware excludes `text/event-stream`, so GraphRAG SSE keeps
    # its low-latency flush semantics.
    app.add_middleware(GZipMiddleware, minimum_size=1024, compresslevel=6)

    # Per-IP throttle on the LLM-invoking endpoints only (admission control;
    # SSE streams are never wrapped). Added before CORS so CORS stays
    # outermost and 429 responses carry CORS headers for the browser FE.
    # See backend/services/rate_limit.py.
    app.add_middleware(LLMRateLimitMiddleware)

    # CORS
    allowed_origins = [
        origin.strip()
        for origin in os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost:5173,http://localhost:3000,http://localhost",
        ).split(",")
        if origin.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_origin_regex=r"https://([a-z0-9-]+\.)?free-will\.app",
        allow_credentials=False,
        allow_methods=["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Accept"],
    )

    # ---------- Mount routers ----------

    # Works extras (must be before works_router so /search and /stats match before /{work_id})
    app.include_router(works_extras_router, prefix="/api/works")

    # Passages detail endpoint — must be mounted BEFORE the database package's
    # works router which exposes a competing /passages/{passage_id} route that
    # only accepts UUIDs. Our version accepts UUIDs *and* KG node_ids.
    app.include_router(passages_router, prefix="/api/passages")

    # Package routers (from the 3 installable packages)
    app.include_router(works_router, prefix="/api")
    app.include_router(kg_router, prefix="/api/kg")
    app.include_router(graphrag_router, prefix="/api/graphrag")

    # Backend-specific routers (cross-cutting concerns)
    app.include_router(search_router, prefix="/api/search")
    app.include_router(auth_router, prefix="/api/auth")
    app.include_router(conversations_router, prefix="/api/graphrag/conversations")
    app.include_router(lemma_router, prefix="/api/lemma")
    app.include_router(graphrag_extras_router, prefix="/api/graphrag")
    app.include_router(audit_router, prefix="/api/graphrag")
    app.include_router(kg_extras_router, prefix="/api/kg")
    app.include_router(opencode_router, prefix="/api/opencode")
    app.include_router(share_router, prefix="/api/graphrag")
    app.include_router(share_public_router)
    app.include_router(community_router)
    app.include_router(contributions_router)
    app.include_router(projects_router)
    app.include_router(feedback_router)

    # Migration compatibility routers (endpoints called by frontend)
    app.include_router(texts_router, prefix="/api/texts")
    app.include_router(text_router, prefix="/api/text")
    app.include_router(citations_router, prefix="/api/citations")
    app.include_router(embeddings_router, prefix="/api/embeddings")

    # ---------- Health endpoint ----------

    @app.get("/api/health")
    async def health(
        response: Response,
        expected_release_id: str | None = Query(None, max_length=160),
    ) -> dict[str, Any]:
        """Composite health check across all services."""
        svc = deps.services
        if svc is None:
            if expected_release_id is not None:
                raise HTTPException(
                    status_code=503,
                    detail={
                        "code": "kg_release_unavailable",
                        "requested_release_id": expected_release_id,
                    },
                )
            return {
                "status": "starting",
                "database": "unknown",
                "graphrag": "not_ready",
                "kg_nodes": 0,
            }

        release = (
            svc.analytics.get_release_metadata() if svc.analytics is not None else None
        )
        if release is None:
            if expected_release_id is not None:
                raise HTTPException(
                    status_code=503,
                    detail={
                        "code": "kg_release_unavailable",
                        "requested_release_id": expected_release_id,
                    },
                )
        else:
            served_release_id = str(release["release_id"])
            if (
                expected_release_id is not None
                and expected_release_id != served_release_id
            ):
                raise HTTPException(
                    status_code=409,
                    detail={
                        "code": "kg_release_mismatch",
                        "requested_release_id": expected_release_id,
                        "served_release_id": served_release_id,
                    },
                )
            apply_release_headers(response, release)

        try:
            db_ok = svc.db.is_connected()
        except Exception:
            db_ok = False

        graphrag_ok = (
            getattr(svc.graphrag, "_kg_loaded", False) if svc.graphrag else False
        )
        # Prefer LIVE DB count over the in-memory snapshot — analytics is loaded
        # once at startup and would otherwise drift between deploys without a pod
        # restart. The COUNT(*) on free_will.kg_nodes is cheap (~5ms).
        kg_nodes = 0
        if db_ok:
            try:
                row = await svc.db.fetchrow(
                    "SELECT count(*)::int AS n FROM free_will.kg_nodes"
                )
                if row:
                    kg_nodes = int(row["n"])
            except Exception:
                kg_nodes = (
                    len(svc.analytics.kg_data.get("nodes", [])) if svc.analytics else 0
                )
        else:
            kg_nodes = (
                len(svc.analytics.kg_data.get("nodes", [])) if svc.analytics else 0
            )
        core_ready = graphrag_ok and kg_nodes > 0

        return {
            "status": "healthy" if db_ok else "degraded" if core_ready else "unhealthy",
            "database": "connected" if db_ok else "disconnected",
            "graphrag": "ready" if graphrag_ok else "not_ready",
            "kg_nodes": kg_nodes,
            "kg_source": getattr(svc, "kg_source", "unknown"),
            "release_id": str(release["release_id"]) if release else None,
            "served_total_nodes": release["served_total_nodes"] if release else 0,
            "served_total_edges": release["served_total_edges"] if release else 0,
        }

    return app


# The app instance uvicorn will import
app = create_app()
