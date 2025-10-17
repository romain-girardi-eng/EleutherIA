#!/usr/bin/env python3
"""
Ancient Free Will Database - FastAPI Backend
Main application entry point
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from contextlib import asynccontextmanager

from api import kg_routes, search_routes, graphrag_routes, text_routes, auth
from services.db import DatabaseService
from services.qdrant_service import QdrantService
from services.llm_service import LLMService, ModelProvider

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global services
db_service: DatabaseService = None
qdrant_service: QdrantService = None
llm_service: LLMService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown"""
    global db_service, qdrant_service, llm_service

    # Startup
    logger.info("🚀 Starting Ancient Free Will Database API")

    try:
        # Initialize database service
        db_service = DatabaseService()
        await db_service.connect()
        logger.info("✅ Connected to PostgreSQL")

        # Initialize Qdrant service
        qdrant_service = QdrantService()
        await qdrant_service.connect()
        logger.info("✅ Connected to Qdrant")

        # Initialize LLM service (prefer Ollama, fallback to Gemini)
        llm_service = LLMService(preferred_provider=ModelProvider.OLLAMA)
        health_status = await llm_service.health_check()
        
        available_providers = []
        if health_status["ollama"]["available"]:
            available_providers.append("Ollama (Mistral 7B)")
        if health_status["gemini"]["available"]:
            available_providers.append("Gemini 2.0 Flash")
        
        logger.info(f"✅ LLM Service initialized - Available: {', '.join(available_providers)}")

        # Store in app state
        app.state.db = db_service
        app.state.qdrant = qdrant_service
        app.state.llm = llm_service

        logger.info("✅ API ready to serve requests")

        yield

    finally:
        # Shutdown
        logger.info("🛑 Shutting down Ancient Free Will Database API")

        if db_service:
            await db_service.close()
            logger.info("✅ Disconnected from PostgreSQL")

        if qdrant_service:
            await qdrant_service.close()
            logger.info("✅ Disconnected from Qdrant")


# Create FastAPI app
app = FastAPI(
    title="Ancient Free Will Database API",
    description="Comprehensive API for the EleutherIA Ancient Free Will Database",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(kg_routes.router, prefix="/api/kg", tags=["Knowledge Graph"])
app.include_router(search_routes.router, prefix="/api/search", tags=["Search"])
app.include_router(graphrag_routes.router, prefix="/api/graphrag", tags=["GraphRAG"])
app.include_router(text_routes.router, prefix="/api/texts", tags=["Texts"])
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])


# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected" if db_service and db_service.is_connected() else "disconnected",
        "qdrant": "connected" if qdrant_service and qdrant_service.is_connected() else "disconnected"
    }


# Root endpoint
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Ancient Free Will Database API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
