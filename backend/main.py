"""
EleutherIA Main Application — FastAPI orchestrator.

Creates the FastAPI app, initializes all services during lifespan,
mounts package routers, and adds cross-cutting middleware/routes.
"""

import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

# Package routers
from eleutheria_database.api.works import router as works_router
from eleutheria_database.api.works import set_db_service
from eleutheria_graphrag.api.routes import router as graphrag_router
from eleutheria_graphrag.api.routes import set_service as set_graphrag_service
from eleutheria_kg.api.routes import router as kg_router
from eleutheria_kg.api.routes import set_services as set_kg_services
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import backend.dependencies as deps
from backend.dependencies import Services

# Backend-specific routers
from backend.routes.auth import router as auth_router
from backend.routes.conversations import router as conversations_router
from backend.routes.graphrag_extras import router as graphrag_extras_router
from backend.routes.kg_extras import router as kg_extras_router
from backend.routes.lemma import router as lemma_router
from backend.routes.search import router as search_router
from backend.routes.works_extras import (
    citations_router,
    embeddings_router,
    text_router,
    texts_router,
)
from backend.routes.works_extras import (
    router as works_extras_router,
)

logger = logging.getLogger(__name__)


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
    set_kg_services(svc.analytics, svc.cache)
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
    app = FastAPI(
        title="EleutherIA",
        description="FAIR-compliant knowledge graph for ancient philosophical debates on free will",
        version="2.0.0",
        lifespan=lifespan,
    )

    # CORS
    allowed_origins = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://localhost:3000,http://localhost",
    ).split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_origin_regex=r"https://.*\.eleutheria\.pages\.dev|https://visual-pulpit.*\.vercel\.app|https://free-will\.app|https://.*\.up\.railway\.app",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ---------- Mount routers ----------

    # Works extras (must be before works_router so /search and /stats match before /{work_id})
    app.include_router(works_extras_router, prefix="/api/works")

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
    app.include_router(kg_extras_router, prefix="/api/kg")

    # Migration compatibility routers (endpoints called by frontend)
    app.include_router(texts_router, prefix="/api/texts")
    app.include_router(text_router, prefix="/api/text")
    app.include_router(citations_router, prefix="/api/citations")
    app.include_router(embeddings_router, prefix="/api/embeddings")

    # ---------- Health endpoint ----------

    @app.get("/api/health")
    async def health() -> dict[str, Any]:
        """Composite health check across all services."""
        svc = deps.services
        if svc is None:
            return {"status": "starting", "database": "unknown", "graphrag": "not_ready", "kg_nodes": 0}

        try:
            db_ok = svc.db.is_connected()
        except Exception:
            db_ok = False

        graphrag_ok = getattr(svc.graphrag, "_kg_loaded", False) if svc.graphrag else False
        kg_nodes = len(svc.analytics.kg_data.get("nodes", [])) if svc.analytics else 0
        core_ready = graphrag_ok and kg_nodes > 0

        return {
            "status": "healthy" if db_ok else "degraded" if core_ready else "unhealthy",
            "database": "connected" if db_ok else "disconnected",
            "graphrag": "ready" if graphrag_ok else "not_ready",
            "kg_nodes": kg_nodes,
            "kg_source": getattr(svc, "kg_source", "unknown"),
        }

    return app


# The app instance uvicorn will import
app = create_app()
