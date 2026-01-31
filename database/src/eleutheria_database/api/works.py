"""
FastAPI routes for ancient works and passages.

Provides REST endpoints for browsing the ancient texts corpus.
"""

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from eleutheria_database.models.works import AncientWork, Passage
from eleutheria_database.services.db import DatabaseService

router = APIRouter(tags=["works"])

# Dependency for database service (to be injected by main app)
_db_service: DatabaseService | None = None


def set_db_service(db: DatabaseService) -> None:
    """Set the database service instance for dependency injection."""
    global _db_service
    _db_service = db


async def get_db() -> DatabaseService:
    """Get the database service."""
    if _db_service is None:
        raise RuntimeError("Database service not initialized")
    return _db_service


@router.get("/works", response_model=list[AncientWork])
async def list_works(
    db: Annotated[DatabaseService, Depends(get_db)],
    language: str | None = Query(
        None, description="Filter by language (grc, lat, eng)"
    ),
    author: str | None = Query(None, description="Filter by author (partial match)"),
    school: str | None = Query(None, description="Filter by philosophical school"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> list[dict]:
    """
    List ancient works with optional filtering.

    Returns paginated list of works with metadata.
    """
    conditions: list[str] = []
    params: list[Any] = []
    param_count = 0

    if language:
        param_count += 1
        conditions.append(f"language = ${param_count}")
        params.append(language)

    if author:
        param_count += 1
        conditions.append(f"author ILIKE '%' || ${param_count} || '%'")
        params.append(author)

    if school:
        param_count += 1
        conditions.append(f"school ILIKE '%' || ${param_count} || '%'")
        params.append(school)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    param_count += 1
    limit_param = param_count
    param_count += 1
    offset_param = param_count
    params.extend([limit, offset])

    sql = f"""
    SELECT *
    FROM free_will.ancient_works
    {where_clause}
    ORDER BY author, title
    LIMIT ${limit_param} OFFSET ${offset_param}
    """

    return await db.fetch(sql, *params)


@router.get("/works/{work_id}", response_model=AncientWork)
async def get_work(
    work_id: UUID,
    db: Annotated[DatabaseService, Depends(get_db)],
) -> dict:
    """Get a specific ancient work by ID."""
    result = await db.fetchrow(
        "SELECT * FROM free_will.ancient_works WHERE work_id = $1",
        work_id,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Work not found")
    return result


@router.get("/works/{work_id}/passages", response_model=list[Passage])
async def list_passages(
    work_id: UUID,
    db: Annotated[DatabaseService, Depends(get_db)],
    book: str | None = Query(None, description="Filter by book"),
    chapter: str | None = Query(None, description="Filter by chapter"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> list[dict]:
    """
    List passages for a specific work.

    Returns paginated passages in sequence order.
    """
    conditions = ["work_id = $1"]
    params: list = [work_id]
    param_count = 1

    if book:
        param_count += 1
        conditions.append(f"book = ${param_count}")
        params.append(book)

    if chapter:
        param_count += 1
        conditions.append(f"chapter = ${param_count}")
        params.append(chapter)

    where_clause = " AND ".join(conditions)

    param_count += 1
    limit_param = param_count
    param_count += 1
    offset_param = param_count
    params.extend([limit, offset])

    sql = f"""
    SELECT *
    FROM free_will.passages
    WHERE {where_clause}
    ORDER BY sequence_number
    LIMIT ${limit_param} OFFSET ${offset_param}
    """

    return await db.fetch(sql, *params)


@router.get("/passages/{passage_id}", response_model=Passage)
async def get_passage(
    passage_id: UUID,
    db: Annotated[DatabaseService, Depends(get_db)],
) -> dict:
    """Get a specific passage by ID."""
    result = await db.fetchrow(
        "SELECT * FROM free_will.passages WHERE passage_id = $1",
        passage_id,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Passage not found")
    return result


@router.get("/search")
async def search_passages(
    db: Annotated[DatabaseService, Depends(get_db)],
    q: str = Query(..., min_length=2, description="Search query"),
    language: str | None = Query(None, description="Filter by language"),
    author: str | None = Query(None, description="Filter by author"),
    limit: int = Query(50, ge=1, le=200),
) -> list[dict]:
    """
    Full-text search across passages.

    Returns passages matching the query with highlighted snippets.
    """
    conditions = [
        "to_tsvector('simple', p.text_content) @@ plainto_tsquery('simple', $1)"
    ]
    params: list = [q]
    param_count = 1

    if language:
        param_count += 1
        conditions.append(f"w.language = ${param_count}")
        params.append(language)

    if author:
        param_count += 1
        conditions.append(f"w.author ILIKE '%' || ${param_count} || '%'")
        params.append(author)

    where_clause = " AND ".join(conditions)

    param_count += 1
    limit_param = param_count
    params.append(limit)

    sql = f"""
    SELECT
        p.passage_id,
        p.work_id,
        p.canonical_ref,
        p.text_content,
        w.title,
        w.author,
        w.language,
        ts_rank(
            to_tsvector('simple', p.text_content),
            plainto_tsquery('simple', $1)
        ) as rank,
        ts_headline(
            'simple',
            p.text_content,
            plainto_tsquery('simple', $1),
            'MaxWords=50, MinWords=20'
        ) as snippet
    FROM free_will.passages p
    JOIN free_will.ancient_works w ON p.work_id = w.work_id
    WHERE {where_clause}
    ORDER BY rank DESC
    LIMIT ${limit_param}
    """

    return await db.fetch(sql, *params)


@router.get("/statistics")
async def get_statistics(
    db: Annotated[DatabaseService, Depends(get_db)],
) -> dict:
    """Get corpus statistics."""
    works_stats = await db.fetchrow("SELECT * FROM free_will.works_statistics")
    passages_stats = await db.fetchrow("SELECT * FROM free_will.passages_statistics")

    return {
        "works": dict(works_stats) if works_stats else {},
        "passages": dict(passages_stats) if passages_stats else {},
    }
