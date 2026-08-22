"""
FastAPI routes for ancient works and passages.

Provides REST endpoints for browsing the ancient texts corpus.
"""

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from eleutheria_database.models.works import AncientWork, Passage
from eleutheria_database.services.db import DatabaseService
from eleutheria_database.services.hybrid_search import fts_fragments

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


def derive_translation_source(
    has_translation: bool, translation_type: str | None
) -> str | None:
    """Label translation provenance from the _en node's metadata.

    ``translation_type`` is set by the provenance audit ('machine' for AI
    batches). Absent metadata means provenance is unverified — label it
    'unknown', never assume a scholarly source.
    """
    if not has_translation:
        return None
    if translation_type == "machine":
        return "ai_generated"
    if translation_type:
        return translation_type
    return "unknown"


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


@router.get("/works/{work_id}/passages")
async def list_passages(
    work_id: UUID,
    db: Annotated[DatabaseService, Depends(get_db)],
    book: str | None = Query(None, description="Filter by book"),
    chapter: str | None = Query(None, description="Filter by chapter"),
    include_translations: bool = Query(
        False, description="Include KG translation nodes"
    ),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> dict:
    """
    List passages for a specific work.

    Returns ``{"passages": [...], "total": N, "work_id": ...}`` — the
    contract the frontend readers (useLazyPassages) paginate against.
    When include_translations=true, joins KG translation nodes via
    passage_citation → kg_node translation_of edges.
    """
    conditions = ["p.work_id = $1"]
    params: list = [work_id]
    param_count = 1

    if book:
        param_count += 1
        conditions.append(f"p.book = ${param_count}")
        params.append(book)

    if chapter:
        param_count += 1
        conditions.append(f"p.chapter = ${param_count}")
        params.append(chapter)

    where_clause = " AND ".join(conditions)

    param_count += 1
    limit_param = param_count
    param_count += 1
    offset_param = param_count
    params.extend([limit, offset])

    if include_translations:
        sql = f"""
        SELECT
            p.*,
            tn.description AS translation_text,
            CASE
                WHEN tn.node_id IS NOT NULL THEN 'en'
                ELSE NULL
            END AS translation_language,
            tn.node_id AS translation_node_id,
            tn.metadata->>'translation_type' AS translation_type,
            COALESCE(kg_count.cnt, 0) AS kg_node_count
        FROM free_will.passages p
        LEFT JOIN free_will.passage_citations pc
            ON p.passage_id = pc.passage_id
            AND pc.citation_type = 'snapshot_passage_node'
        LEFT JOIN free_will.kg_edges te
            ON te.source_id = pc.kg_node_id || '_en'
            AND te.relation = 'translation_of'
        LEFT JOIN free_will.kg_nodes tn
            ON tn.node_id = te.source_id
        LEFT JOIN LATERAL (
            SELECT COUNT(DISTINCT pc2.kg_node_id) AS cnt
            FROM free_will.passage_citations pc2
            WHERE pc2.passage_id = p.passage_id
        ) kg_count ON true
        WHERE {where_clause}
        ORDER BY p.sequence_number
        LIMIT ${limit_param} OFFSET ${offset_param}
        """
    else:
        sql = f"""
        SELECT p.*
        FROM free_will.passages p
        WHERE {where_clause}
        ORDER BY p.sequence_number
        LIMIT ${limit_param} OFFSET ${offset_param}
        """

    rows = await db.fetch(sql, *params)
    if include_translations:
        for row in rows:
            row["translation_source"] = derive_translation_source(
                row.get("translation_node_id") is not None,
                row.get("translation_type"),
            )

    count_row = await db.fetchrow(
        f"SELECT COUNT(*) AS total FROM free_will.passages p WHERE {where_clause}",
        *params[: len(params) - 2],
    )
    total = count_row["total"] if count_row else len(rows)

    return {
        "passages": rows,
        "total": total,
        "work_id": str(work_id),
        "offset": offset,
        "limit": limit,
    }


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
    match_cond, rank_expr = await fts_fragments(db, "$1")
    conditions = [match_cond]
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
        {rank_expr} as rank,
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
