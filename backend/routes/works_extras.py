"""
Works compatibility routes — endpoints the frontend calls that aren't
in the database package's works router.
"""

import logging
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.dependencies import get_db
from eleutheria_database.services.db import DatabaseService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["works-extras"])


@router.get("/search")
async def search_works(
    db: Annotated[DatabaseService, Depends(get_db)],
    query: str = Query(..., min_length=1),
    author: str | None = Query(None),
    language: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
) -> list[dict[str, Any]]:
    """Search works by title, author, or text content."""
    conditions = [
        """(
            w.title ILIKE '%' || $1 || '%'
            OR w.author ILIKE '%' || $1 || '%'
            OR w.canonical_id ILIKE '%' || $1 || '%'
        )"""
    ]
    params: list[Any] = [query]
    idx = 1

    if author:
        idx += 1
        conditions.append(f"w.author ILIKE '%' || ${idx} || '%'")
        params.append(author)

    if language:
        idx += 1
        conditions.append(f"w.language = ${idx}")
        params.append(language)

    idx += 1
    params.append(limit)

    where = " AND ".join(conditions)

    sql = f"""
    SELECT
        w.work_id, w.canonical_id, w.title, w.author,
        w.language, w.period, w.school, w.date_composed,
        w.source, w.total_words
    FROM free_will.ancient_works w
    WHERE {where}
    ORDER BY w.author, w.title
    LIMIT ${idx}
    """

    return await db.fetch(sql, *params)


@router.get("/stats")
async def get_works_stats(
    db: Annotated[DatabaseService, Depends(get_db)],
) -> dict[str, Any]:
    """Get corpus statistics for works and passages."""
    works_stats = await db.fetchrow("SELECT * FROM free_will.works_statistics")
    passages_stats = await db.fetchrow("SELECT * FROM free_will.passages_statistics")

    return {
        "works": dict(works_stats) if works_stats else {},
        "passages": dict(passages_stats) if passages_stats else {},
    }


@router.get("/{work_id}/kg-nodes")
async def get_work_kg_nodes(
    work_id: UUID,
    db: Annotated[DatabaseService, Depends(get_db)],
) -> list[dict[str, Any]]:
    """Get KG nodes linked to a specific work via passage citations."""
    rows = await db.fetch(
        """
        SELECT DISTINCT
            n.node_id, n.label, n.type, n.description,
            n.period, n.school
        FROM free_will.passages p
        JOIN free_will.passage_citations pc ON p.passage_id = pc.passage_id
        JOIN free_will.kg_nodes n ON pc.kg_node_id = n.node_id
        WHERE p.work_id = $1
        ORDER BY n.label
        """,
        work_id,
    )
    return [dict(r) for r in rows]
