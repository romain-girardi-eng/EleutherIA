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
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from backend.dependencies import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["works-extras"])

# Additional routers mounted at different prefixes in main.py
texts_router = APIRouter(tags=["texts"])
text_router = APIRouter(tags=["text"])
citations_router = APIRouter(tags=["citations"])
embeddings_router = APIRouter(tags=["embeddings"])


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
        format_passage(r, is_target=(r["sequence_number"] == seq))
        for r in context_rows
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
            results.append({
                "id": node_id,
                "text": best["text_content"],
                "author": best["author"] or "",
                "work": best["work"] or "",
                "passage_ref": best["canonical_ref"],
                "confidence": float(best["confidence"]) if best["confidence"] else None,
            })
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
                results.append({
                    "id": node_id,
                    "text": (node["description"] or "")[:500],
                    "author": "",
                    "work": "",
                    "passage_ref": node["label"],
                    "confidence": None,
                })

    return results


# =============================================================================
# /api/embeddings — Stubs (Qdrant-dependent, not available on Railway)
# =============================================================================


@embeddings_router.get("/semantic-space")
async def get_semantic_space() -> dict[str, Any]:
    """Stub: Embedding visualization not available in Railway deployment."""
    return {
        "nodes": [],
        "error": "Embedding visualization not available in Railway deployment",
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
