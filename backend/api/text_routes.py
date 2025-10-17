#!/usr/bin/env python3
"""
Text API Routes
Endpoints for accessing the 289 ancient texts
"""

from fastapi import APIRouter, HTTPException, Request
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/list")
async def list_texts(
    category: Optional[str] = None,
    author: Optional[str] = None,
    language: Optional[str] = None,
    request: Request = None
):
    """List all texts with optional filtering"""
    try:
        db = request.app.state.db

        # Build query
        conditions = []
        params = []
        param_count = 1

        if category:
            conditions.append(f"category = ${param_count}")
            params.append(category)
            param_count += 1

        if author:
            conditions.append(f"author ILIKE ${param_count}")
            params.append(f"%{author}%")
            param_count += 1

        if language:
            conditions.append(f"language = ${param_count}")
            params.append(language)
            param_count += 1

        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

        sql = f"""
        SELECT id, title, author, category, language, text_length,
               date_created, kg_work_id
        FROM free_will.texts
        {where_clause}
        ORDER BY title
        """

        texts = await db.fetch(sql, *params)

        return {
            'texts': texts,
            'total': len(texts)
        }

    except Exception as e:
        logger.error(f"Error listing texts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{text_id}")
async def get_text(text_id: str, request: Request):
    """Get full text content"""
    try:
        db = request.app.state.db

        sql = """
        SELECT id, title, author, category, language, text_length,
               raw_text, normalized_text, tei_xml, lemmas,
               date_created, kg_work_id, metadata
        FROM free_will.texts
        WHERE id = $1
        """

        text = await db.fetchrow(sql, text_id)

        if not text:
            raise HTTPException(status_code=404, detail=f"Text {text_id} not found")

        return text

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting text: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{text_id}/structure")
async def get_text_structure(text_id: str, request: Request):
    """Get hierarchical structure of a text"""
    try:
        db = request.app.state.db

        sql = """
        SELECT id, parent_id, type, subtype, n, full_reference, heading,
               char_position, char_length
        FROM free_will.text_divisions
        WHERE text_id = $1
        ORDER BY char_position
        """

        divisions = await db.fetch(sql, text_id)

        return {
            'text_id': text_id,
            'divisions': divisions,
            'total': len(divisions)
        }

    except Exception as e:
        logger.error(f"Error getting text structure: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/overview")
async def get_text_stats(request: Request):
    """Get overview statistics for all texts"""
    try:
        db = request.app.state.db

        sql = """
        SELECT
            COUNT(*) as total_texts,
            COUNT(DISTINCT author) as unique_authors,
            COUNT(DISTINCT category) as categories,
            COUNT(CASE WHEN language = 'grc' THEN 1 END) as greek_texts,
            COUNT(CASE WHEN language = 'lat' THEN 1 END) as latin_texts,
            COUNT(CASE WHEN lemmas IS NOT NULL THEN 1 END) as texts_with_lemmas,
            COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) as texts_with_embeddings,
            SUM(text_length) as total_characters
        FROM free_will.texts
        """

        stats = await db.fetchrow(sql)

        return stats

    except Exception as e:
        logger.error(f"Error getting text stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
