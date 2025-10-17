#!/usr/bin/env python3
"""
Search API Routes
Endpoints for full-text, lemmatic, semantic, and hybrid search
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class SearchQuery(BaseModel):
    """Search query model"""
    query: str
    limit: Optional[int] = 10
    enable_fulltext: Optional[bool] = True
    enable_lemmatic: Optional[bool] = True
    enable_semantic: Optional[bool] = True


@router.post("/hybrid")
async def hybrid_search(search_query: SearchQuery, request: Request):
    """
    Perform hybrid search combining full-text, lemmatic, and semantic search
    Uses Reciprocal Rank Fusion (RRF) to merge results
    """
    try:
        from services.hybrid_search import HybridSearchService

        # Get services from app state
        db = request.app.state.db
        qdrant = request.app.state.qdrant

        # Create hybrid search service
        search_service = HybridSearchService(db, qdrant)

        # Perform hybrid search
        results = await search_service.hybrid_search(
            query=search_query.query,
            limit=search_query.limit,
            enable_fulltext=search_query.enable_fulltext,
            enable_lemmatic=search_query.enable_lemmatic,
            enable_semantic=search_query.enable_semantic
        )

        return results

    except Exception as e:
        logger.error(f"Error in hybrid search: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fulltext")
async def fulltext_search(search_query: SearchQuery, request: Request):
    """Full-text search using PostgreSQL"""
    try:
        from services.hybrid_search import HybridSearchService

        db = request.app.state.db
        qdrant = request.app.state.qdrant
        search_service = HybridSearchService(db, qdrant)

        results = await search_service.fulltext_search(
            query=search_query.query,
            limit=search_query.limit
        )

        return {
            'results': results,
            'total': len(results)
        }

    except Exception as e:
        logger.error(f"Error in fulltext search: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/lemmatic")
async def lemmatic_search(search_query: SearchQuery, request: Request):
    """Lemmatic search using existing lemmas"""
    try:
        from services.hybrid_search import HybridSearchService

        db = request.app.state.db
        qdrant = request.app.state.qdrant
        search_service = HybridSearchService(db, qdrant)

        results = await search_service.lemmatic_search(
            query=search_query.query,
            limit=search_query.limit
        )

        return {
            'results': results,
            'total': len(results)
        }

    except Exception as e:
        logger.error(f"Error in lemmatic search: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/semantic")
async def semantic_search(search_query: SearchQuery, request: Request):
    """Semantic search using Qdrant vector similarity"""
    try:
        from services.hybrid_search import HybridSearchService

        db = request.app.state.db
        qdrant = request.app.state.qdrant
        search_service = HybridSearchService(db, qdrant)

        results = await search_service.semantic_search(
            query=search_query.query,
            limit=search_query.limit
        )

        return {
            'results': results,
            'total': len(results)
        }

    except Exception as e:
        logger.error(f"Error in semantic search: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/kg")
async def search_knowledge_graph(search_query: SearchQuery, request: Request):
    """Search Knowledge Graph nodes using semantic search"""
    try:
        from services.hybrid_search import HybridSearchService

        db = request.app.state.db
        qdrant = request.app.state.qdrant
        search_service = HybridSearchService(db, qdrant)

        results = await search_service.search_knowledge_graph(
            query=search_query.query,
            limit=search_query.limit
        )

        return {
            'results': results,
            'total': len(results)
        }

    except Exception as e:
        logger.error(f"Error searching knowledge graph: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
