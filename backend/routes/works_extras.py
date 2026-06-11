"""
Works compatibility routes — endpoints the frontend calls that aren't
in the database package's works router.

Includes:
- Works search & stats (mounted at /api/works)
- Passage context (mounted at /api/texts)
- Citation passage lookup (mounted at /api/text)
- Batch citation fetch (mounted at /api/citations)
- Embedding stubs (mounted at /api/embeddings)
"""

import logging
from typing import Annotated, Any
from uuid import UUID

from eleutheria_database.services.db import DatabaseService
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from backend.dependencies import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["works-extras"])

# Additional routers mounted at different prefixes in main.py
texts_router = APIRouter(tags=["texts"])
text_router = APIRouter(tags=["text"])
citations_router = APIRouter(tags=["citations"])
embeddings_router = APIRouter(tags=["embeddings"])


@router.get("")
@router.get("/")
async def list_works_compat(
    db: Annotated[DatabaseService, Depends(get_db)],
    language: str | None = Query(None),
    author: str | None = Query(None),
    period: str | None = Query(None),
    source: str | None = Query(None),
    search: str | None = Query(None),
    sort_by: str = Query("author"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    """List ancient works in the shape expected by the frontend.

    The installable database package exposes ``GET /api/works`` as a raw list.
    The frontend has long consumed a paginated object, so this compatibility
    route is mounted before the package router and keeps the public `/texts`
    page from failing when it expects `works` and `total` keys.
    """
    conditions: list[str] = []
    params: list[Any] = []
    idx = 0

    def add_param(value: Any) -> str:
        nonlocal idx
        idx += 1
        params.append(value)
        return f"${idx}"

    if language:
        conditions.append(f"w.language = {add_param(language)}")
    if author:
        conditions.append(f"w.author ILIKE '%' || {add_param(author)} || '%'")
    if period:
        conditions.append(f"w.period ILIKE '%' || {add_param(period)} || '%'")
    if source:
        conditions.append(f"w.source ILIKE '%' || {add_param(source)} || '%'")
    if search:
        placeholder = add_param(search)
        conditions.append(
            f"""(
                w.title ILIKE '%' || {placeholder} || '%'
                OR w.author ILIKE '%' || {placeholder} || '%'
                OR w.canonical_id ILIKE '%' || {placeholder} || '%'
            )"""
        )

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    sort_sql = {
        "title": "w.title ASC, w.author ASC",
        "author": "w.author ASC, w.title ASC",
        "period": "w.period ASC NULLS LAST, w.author ASC, w.title ASC",
        "language": "w.language ASC, w.author ASC, w.title ASC",
        "most_passages": "w.total_divisions DESC NULLS LAST, w.author ASC, w.title ASC",
        "most_cited": "w.total_divisions DESC NULLS LAST, w.author ASC, w.title ASC",
        "featured": "w.total_divisions DESC NULLS LAST, w.author ASC, w.title ASC",
    }.get(sort_by, "w.author ASC, w.title ASC")

    count_sql = f"""
    SELECT count(*)::int AS total
    FROM free_will.ancient_works w
    {where_clause}
    """
    count_row = await db.fetchrow(count_sql, *params)

    limit_placeholder = add_param(limit)
    offset_placeholder = add_param(offset)
    list_sql = f"""
    SELECT *
    FROM free_will.ancient_works w
    {where_clause}
    ORDER BY {sort_sql}
    LIMIT {limit_placeholder} OFFSET {offset_placeholder}
    """
    rows = await db.fetch(list_sql, *params)

    return {
        "works": [dict(row) for row in rows],
        "total": int(count_row["total"]) if count_row else 0,
        "offset": offset,
        "limit": limit,
    }


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
    citations = await db.fetchrow(
        "SELECT COUNT(*) AS total FROM free_will.passage_citations"
    )

    return {
        "works": dict(works_stats) if works_stats else {},
        "passages": dict(passages_stats) if passages_stats else {},
        "total_citations": citations["total"] if citations else 0,
    }


@router.get("/{work_id}/section")
async def get_work_section(
    work_id: str,
    db: Annotated[DatabaseService, Depends(get_db)],
    around: str = Query(
        ..., description="Anchor passage_id (UUID) or passage KG node_id"
    ),
    before: int = Query(1, ge=0, le=20),
    after: int = Query(1, ge=0, le=20),
) -> dict[str, Any]:
    """Return N passages before + the anchor + N passages after.

    ``around`` may be a passages.passage_id UUID or a passage KG node_id;
    the latter is resolved through ``passage_citations``. Passages are
    ordered by ``sequence_number`` within the work.
    """
    # Resolve work_id (UUID or canonical_id)
    work: dict[str, Any] | None = None
    if len(work_id) == 36 and work_id.count("-") == 4:
        work = await db.fetchrow(
            "SELECT work_id, title, canonical_id FROM free_will.ancient_works WHERE work_id = $1::uuid",
            work_id,
        )
    if work is None:
        work = await db.fetchrow(
            "SELECT work_id, title, canonical_id FROM free_will.ancient_works WHERE canonical_id = $1 OR kg_work_id = $1",
            work_id,
        )
    if work is None:
        raise HTTPException(status_code=404, detail="Work not found")

    # Resolve target passage
    is_uuid = len(around) == 36 and around.count("-") == 4
    target = None
    if is_uuid:
        target = await db.fetchrow(
            "SELECT passage_id, sequence_number, canonical_ref, text_content, cts_urn "
            "FROM free_will.passages WHERE passage_id = $1::uuid AND work_id = $2",
            around,
            work["work_id"],
        )
    if target is None:
        target = await db.fetchrow(
            """
            SELECT p.passage_id, p.sequence_number, p.canonical_ref, p.text_content, p.cts_urn
            FROM free_will.passage_citations pc
            JOIN free_will.passages p ON pc.passage_id = p.passage_id
            WHERE pc.kg_node_id = $1 AND p.work_id = $2
            LIMIT 1
            """,
            around,
            work["work_id"],
        )
    if target is None:
        raise HTTPException(status_code=404, detail="Anchor passage not found in work")

    seq = target["sequence_number"]
    rows = await db.fetch(
        """
        SELECT passage_id, sequence_number, canonical_ref, text_content, cts_urn
        FROM free_will.passages
        WHERE work_id = $1 AND sequence_number BETWEEN $2 AND $3
        ORDER BY sequence_number
        """,
        work["work_id"],
        seq - before,
        seq + after,
    )

    # Try to load English translations via passage_citations + _en KG nodes.
    en_lookup: dict[str, str] = {}
    if rows:
        ids = [str(r["passage_id"]) for r in rows]
        en_rows = await db.fetch(
            """
            SELECT pc.passage_id, n.description
            FROM free_will.passage_citations pc
            JOIN free_will.kg_nodes n ON n.node_id = pc.kg_node_id || '_en'
            WHERE pc.passage_id = ANY($1::uuid[])
            """,
            ids,
        )
        for r in en_rows:
            en_lookup[str(r["passage_id"])] = r["description"]

    def _shape(row: dict[str, Any]) -> dict[str, Any]:
        pid = str(row["passage_id"])
        return {
            "passage_id": pid,
            "label": row.get("canonical_ref"),
            "cts_urn": row.get("cts_urn"),
            "sequence_number": row.get("sequence_number"),
            "text_content_original": row.get("text_content"),
            "text_content_english": en_lookup.get(pid),
        }

    before_items: list[dict[str, Any]] = []
    after_items: list[dict[str, Any]] = []
    target_shape: dict[str, Any] | None = None
    for r in rows:
        shaped = _shape(r)
        if r["sequence_number"] < seq:
            before_items.append(shaped)
        elif r["sequence_number"] > seq:
            after_items.append(shaped)
        else:
            target_shape = shaped

    if target_shape is None:
        target_shape = _shape(target)

    section_label = target.get("canonical_ref")
    # Strip the most-specific component for the section label (e.g.
    # "EN III.1, 1110a4-6" → "EN III.1") so the UI can show a clean header.
    if section_label and "," in section_label:
        section_label = section_label.split(",", 1)[0].strip()

    return {
        "target_passage_id": str(target["passage_id"]),
        "before": before_items,
        "target": target_shape,
        "after": after_items,
        "section_label": section_label,
        "work_title": work.get("title"),
        "work_canonical_id": work.get("canonical_id"),
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


# =============================================================================
# /api/texts — Passage context endpoint
# =============================================================================


@texts_router.get("/passage/{passage_id}/context")
async def get_passage_context(
    passage_id: str,
    db: Annotated[DatabaseService, Depends(get_db)],
    window: int = Query(5, ge=1, le=20),
) -> dict[str, Any]:
    """Get a passage with surrounding context (N passages before/after)."""
    # First, get the target passage with its work info
    target = await db.fetchrow(
        """
        SELECT
            p.passage_id, p.text_content, p.canonical_ref,
            p.cts_urn, p.book, p.chapter, p.section,
            p.sequence_number, p.work_id,
            w.title AS work_title, w.author, w.language
        FROM free_will.passages p
        JOIN free_will.ancient_works w ON p.work_id = w.work_id
        WHERE p.passage_id::text = $1
        """,
        passage_id,
    )

    # If not found by UUID, try matching by kg_node_id in passage_citations
    if not target:
        target = await db.fetchrow(
            """
            SELECT
                p.passage_id, p.text_content, p.canonical_ref,
                p.cts_urn, p.book, p.chapter, p.section,
                p.sequence_number, p.work_id,
                w.title AS work_title, w.author, w.language
            FROM free_will.passage_citations pc
            JOIN free_will.passages p ON pc.passage_id = p.passage_id
            JOIN free_will.ancient_works w ON p.work_id = w.work_id
            WHERE pc.kg_node_id = $1
            LIMIT 1
            """,
            passage_id,
        )

    if not target:
        return {
            "target": None,
            "passages": [],
            "workId": "",
            "totalPassagesInWork": 0,
        }

    work_id = target["work_id"]
    seq = target["sequence_number"]

    # Get surrounding passages within the same work
    context_rows = await db.fetch(
        """
        SELECT
            p.passage_id, p.text_content, p.canonical_ref,
            p.cts_urn, p.book, p.chapter, p.section,
            p.sequence_number
        FROM free_will.passages p
        WHERE p.work_id = $1
          AND p.sequence_number BETWEEN $2 AND $3
        ORDER BY p.sequence_number
        """,
        work_id,
        seq - window,
        seq + window,
    )

    # Get total passages in work
    total = await db.fetchval(
        "SELECT COUNT(*) FROM free_will.passages WHERE work_id = $1",
        work_id,
    )

    def format_passage(row: Any, is_target: bool = False) -> dict[str, Any]:
        return {
            "passageId": str(row["passage_id"]),
            "textContent": row["text_content"],
            "canonicalRef": row["canonical_ref"],
            "author": target["author"] or "",
            "workTitle": target["work_title"] or "",
            "language": target["language"] or "grc",
            "ctsUrn": row.get("cts_urn"),
            "book": row.get("book"),
            "chapter": row.get("chapter"),
            "section": row.get("section"),
            "sequenceNumber": row["sequence_number"],
            "isTarget": is_target,
        }

    passages = [
        format_passage(r, is_target=(r["sequence_number"] == seq)) for r in context_rows
    ]

    target_formatted = format_passage(target, is_target=True)

    return {
        "target": target_formatted,
        "passages": passages,
        "workId": str(work_id),
        "totalPassagesInWork": int(total or 0),
    }


# =============================================================================
# /api/text — Citation passage lookup
# =============================================================================


class CitationPassageRequest(BaseModel):
    citation: str = Field(..., min_length=1)


@text_router.post("/citation-passage")
async def get_citation_passage(
    body: CitationPassageRequest,
    db: Annotated[DatabaseService, Depends(get_db)],
) -> dict[str, Any]:
    """Find a passage matching a citation reference string."""
    citation = body.citation.strip()

    # Try exact match on canonical_ref first
    row = await db.fetchrow(
        """
        SELECT
            p.passage_id, p.text_content, p.canonical_ref,
            p.cts_urn, w.title, w.author, w.language
        FROM free_will.passages p
        JOIN free_will.ancient_works w ON p.work_id = w.work_id
        WHERE p.canonical_ref ILIKE $1
        LIMIT 1
        """,
        citation,
    )

    # Try partial match on canonical_ref
    if not row:
        row = await db.fetchrow(
            """
            SELECT
                p.passage_id, p.text_content, p.canonical_ref,
                p.cts_urn, w.title, w.author, w.language
            FROM free_will.passages p
            JOIN free_will.ancient_works w ON p.work_id = w.work_id
            WHERE p.canonical_ref ILIKE '%' || $1 || '%'
            LIMIT 1
            """,
            citation,
        )

    # Try text search as fallback
    if not row:
        row = await db.fetchrow(
            """
            SELECT
                p.passage_id, p.text_content, p.canonical_ref,
                p.cts_urn, w.title, w.author, w.language
            FROM free_will.passages p
            JOIN free_will.ancient_works w ON p.work_id = w.work_id
            WHERE p.search_vector @@ plainto_tsquery('english', $1)
            ORDER BY ts_rank(p.search_vector, plainto_tsquery('english', $1)) DESC
            LIMIT 1
            """,
            citation,
        )

    if not row:
        return {
            "citation": citation,
            "original": None,
            "originalLanguage": None,
            "translation": None,
            "note": "No matching passage found",
        }

    lang = row["language"] or "grc"

    return {
        "citation": citation,
        "original": row["text_content"],
        "originalLanguage": lang,
        "translation": None,  # Translation requires separate table/service
        "text_id": str(row["passage_id"]),
        "title": row["title"],
        "author": row["author"],
    }


# =============================================================================
# /api/citations — Batch citation fetch
# =============================================================================


class BatchCitationsRequest(BaseModel):
    ids: list[str] = Field(..., min_length=1)


@citations_router.post("/batch")
async def batch_fetch_citations(
    body: BatchCitationsRequest,
    db: Annotated[DatabaseService, Depends(get_db)],
) -> list[dict[str, Any]]:
    """Batch fetch citation data for a list of KG node IDs."""
    results: list[dict[str, Any]] = []

    # Query each ID individually (statement_cache_size=0 compatible)
    for node_id in body.ids[:50]:  # Cap at 50 to prevent abuse
        rows = await db.fetch(
            """
            SELECT
                pc.kg_node_id,
                p.passage_id, p.text_content, p.canonical_ref,
                w.title AS work, w.author,
                pc.confidence
            FROM free_will.passage_citations pc
            JOIN free_will.passages p ON pc.passage_id = p.passage_id
            JOIN free_will.ancient_works w ON p.work_id = w.work_id
            WHERE pc.kg_node_id = $1
            ORDER BY pc.confidence DESC NULLS LAST
            LIMIT 3
            """,
            node_id,
        )

        if rows:
            # Use the highest-confidence passage
            best = rows[0]
            results.append(
                {
                    "id": node_id,
                    "text": best["text_content"],
                    "author": best["author"] or "",
                    "work": best["work"] or "",
                    "passage_ref": best["canonical_ref"],
                    "confidence": float(best["confidence"])
                    if best["confidence"]
                    else None,
                }
            )
        else:
            # Try to find the node label from kg_nodes
            node = await db.fetchrow(
                """
                SELECT label, type, description
                FROM free_will.kg_nodes
                WHERE node_id = $1
                """,
                node_id,
            )
            if node:
                results.append(
                    {
                        "id": node_id,
                        "text": (node["description"] or "")[:500],
                        "author": "",
                        "work": "",
                        "passage_ref": node["label"],
                        "confidence": None,
                    }
                )

    return results


# =============================================================================
# /api/embeddings — Retired stubs (vectorless architecture as of 2026-05-14)
# =============================================================================
# Kept for frontend backwards-compat; returns empty payload + retirement notice.


@embeddings_router.get("/semantic-space")
async def get_semantic_space() -> dict[str, Any]:
    """Retired: vector embedding visualization removed in the vectorless rewrite."""
    return {
        "nodes": [],
        "error": "Embedding visualization retired in the vectorless architecture",
    }


class VisualizeRequest(BaseModel):
    text: str = Field(..., min_length=1)


@embeddings_router.post("/visualize")
async def visualize_embedding(body: VisualizeRequest) -> dict[str, Any]:
    """Stub: Embedding visualization not available in Railway deployment."""
    return {
        "embedding": [],
        "position_3d": {"x": 0, "y": 0, "z": 0},
        "cluster": "Unknown",
        "cluster_color": "#666666",
        "similar_nodes": [],
        "error": "Embedding visualization not available in Railway deployment",
    }
