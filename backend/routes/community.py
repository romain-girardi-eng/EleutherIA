"""
Public community Q&A gallery for past GraphRAG queries.

Two read endpoints, no authentication required:

* ``GET /api/graphrag/community/queries``           — paginated list, filterable
* ``GET /api/graphrag/community/queries/{slug}``    — one full answer + citations

Backed by ``free_will.query_traces`` (see migration
``20260515_06_query_traces_public.sql``). Rows are eligible for the gallery
when ``is_public = true`` AND the final answer is at least 1 000 characters
long (filters out error stubs and aborted runs).
"""

from __future__ import annotations

import base64
import binascii
import json
import logging
import re
from datetime import datetime
from typing import Annotated, Any, Literal

from eleutheria_database.services.db import DatabaseService
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from backend.dependencies import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/graphrag/community", tags=["community"])


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class CommunityListItem(BaseModel):
    slug: str
    query: str
    excerpt: str
    citation_count: int
    section_count: int
    quote_count: int
    model: str | None
    total_cost_usd: float
    total_tokens: int
    created_at: datetime
    topic_tags: list[str]


class CommunityListResponse(BaseModel):
    items: list[CommunityListItem]
    next_cursor: str | None = None


class CommunityDetailResponse(BaseModel):
    slug: str
    trace_id: str
    query: str
    answer: str
    passage_citations: list[dict[str, Any]]
    sources: list[dict[str, Any]]
    reasoning_path: dict[str, Any] | None
    model: str | None
    total_cost_usd: float
    total_tokens: int
    created_at: datetime
    topic_tags: list[str]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


_MIN_ANSWER_LEN = 1000
_EXCERPT_LEN = 240


def _excerpt(text: str, limit: int = _EXCERPT_LEN) -> str:
    """First ``limit`` chars of ``text``, trimmed at a word boundary."""
    if not text:
        return ""
    clean = text.strip()
    if len(clean) <= limit:
        return clean
    sliced = clean[:limit]
    cut = sliced.rsplit(" ", 1)[0]
    return (cut or sliced).rstrip() + "…"


_SECTION_RE = re.compile(r"^### ", re.MULTILINE)
_QUOTE_RE = re.compile(r"^> ", re.MULTILINE)


def _count_sections(text: str) -> int:
    return len(_SECTION_RE.findall(text or ""))


def _count_quotes(text: str) -> int:
    return len(_QUOTE_RE.findall(text or ""))


def _model_from_metadata(metadata: dict[str, Any] | None) -> str | None:
    """Extract the model name from metadata / provider_usage."""
    if not isinstance(metadata, dict):
        return None
    value = metadata.get("model")
    return value if isinstance(value, str) else None


def _maybe_json(value: Any) -> Any:
    """asyncpg sometimes returns jsonb columns as already-decoded objects, but
    when the driver hands back a raw string we still want to decode it."""
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str) and value:
        try:
            return json.loads(value)
        except json.JSONDecodeError, ValueError:
            return None
    return None


def _encode_cursor(started_at: datetime, slug: str) -> str:
    payload = f"{started_at.isoformat()}|{slug}"
    return base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii")


def _decode_cursor(cursor: str) -> tuple[datetime, str]:
    try:
        decoded = base64.urlsafe_b64decode(cursor.encode("ascii")).decode("utf-8")
        iso_part, slug_part = decoded.split("|", 1)
        return datetime.fromisoformat(iso_part), slug_part
    except (binascii.Error, ValueError, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=400, detail="Invalid cursor") from exc


def _citations_list(value: Any) -> list[dict[str, Any]]:
    decoded = _maybe_json(value)
    if isinstance(decoded, list):
        return [c for c in decoded if isinstance(c, dict)]
    return []


def _sources_from_metadata(metadata: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(metadata, dict):
        return []
    sources = metadata.get("sources")
    if isinstance(sources, list):
        return [s for s in sources if isinstance(s, dict)]
    return []


def _reasoning_from_metadata(
    metadata: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if not isinstance(metadata, dict):
        return None
    reasoning = metadata.get("reasoning_path")
    if isinstance(reasoning, dict):
        return reasoning
    return None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("/queries", response_model=CommunityListResponse)
async def list_queries(
    db: Annotated[DatabaseService, Depends(get_db)],
    sort: Literal["recent", "popular"] = "recent",
    period: str | None = None,
    philosopher: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = None,
) -> CommunityListResponse:
    """List public queries, sorted by ``recent`` or ``popular``.

    * ``period`` and ``philosopher`` both match ``topic_tags @> ARRAY[?]``.
    * ``cursor`` is the ``next_cursor`` returned by the previous page; only
      meaningful for ``sort=recent``.
    """
    conditions = [
        "is_public = true",
        "final_answer_text IS NOT NULL",
        "length(final_answer_text) >= $1",
    ]
    params: list[Any] = [_MIN_ANSWER_LEN]

    if period:
        params.append([period])
        conditions.append(f"topic_tags @> ${len(params)}")
    if philosopher:
        params.append([philosopher])
        conditions.append(f"topic_tags @> ${len(params)}")

    if cursor and sort == "recent":
        cursor_dt, cursor_slug = _decode_cursor(cursor)
        params.append(cursor_dt)
        params.append(cursor_slug)
        conditions.append(
            f"(started_at, share_slug) < (${len(params) - 1}, ${len(params)})"
        )

    if sort == "popular":
        order_clause = (
            "ORDER BY coalesce(jsonb_array_length(final_answer_citations), 0) DESC, "
            "started_at DESC, share_slug DESC"
        )
    else:
        order_clause = "ORDER BY started_at DESC, share_slug DESC"

    params.append(limit + 1)
    sql = f"""
        SELECT
            share_slug,
            query,
            final_answer_text,
            final_answer_citations,
            metadata,
            total_cost_usd,
            total_tokens,
            started_at,
            topic_tags
        FROM free_will.query_traces
        WHERE {" AND ".join(conditions)}
        {order_clause}
        LIMIT ${len(params)}
    """

    rows = await db.fetch(sql, *params)

    has_more = len(rows) > limit
    visible = rows[:limit]

    items: list[CommunityListItem] = []
    for row in visible:
        answer = row.get("final_answer_text") or ""
        citations = _citations_list(row.get("final_answer_citations"))
        metadata = _maybe_json(row.get("metadata")) or {}
        items.append(
            CommunityListItem(
                slug=row["share_slug"],
                query=row.get("query") or "",
                excerpt=_excerpt(answer),
                citation_count=len(citations),
                section_count=_count_sections(answer),
                quote_count=_count_quotes(answer),
                model=_model_from_metadata(metadata),
                total_cost_usd=float(row.get("total_cost_usd") or 0.0),
                total_tokens=int(row.get("total_tokens") or 0),
                created_at=row["started_at"],
                topic_tags=list(row.get("topic_tags") or []),
            )
        )

    next_cursor: str | None = None
    if has_more and sort == "recent" and visible:
        last = visible[-1]
        next_cursor = _encode_cursor(last["started_at"], last["share_slug"])

    return CommunityListResponse(items=items, next_cursor=next_cursor)


@router.get("/queries/{slug}", response_model=CommunityDetailResponse)
async def get_query(
    slug: str,
    db: Annotated[DatabaseService, Depends(get_db)],
) -> CommunityDetailResponse:
    """Return the full answer + citations for a public query by its slug."""
    row = await db.fetchrow(
        """
        SELECT
            trace_id,
            share_slug,
            query,
            final_answer_text,
            final_answer_citations,
            metadata,
            total_cost_usd,
            total_tokens,
            started_at,
            topic_tags,
            is_public,
            length(final_answer_text) AS answer_length
        FROM free_will.query_traces
        WHERE share_slug = $1
        """,
        slug,
    )

    if not row or not row.get("is_public"):
        raise HTTPException(status_code=404, detail="Query not found")
    if not row.get("final_answer_text"):
        raise HTTPException(status_code=404, detail="Query not found")
    if (row.get("answer_length") or 0) < _MIN_ANSWER_LEN:
        raise HTTPException(status_code=404, detail="Query not found")

    metadata = _maybe_json(row.get("metadata")) or {}

    return CommunityDetailResponse(
        slug=row["share_slug"],
        trace_id=str(row["trace_id"]),
        query=row.get("query") or "",
        answer=row.get("final_answer_text") or "",
        passage_citations=_citations_list(row.get("final_answer_citations")),
        sources=_sources_from_metadata(metadata),
        reasoning_path=_reasoning_from_metadata(metadata),
        model=_model_from_metadata(metadata),
        total_cost_usd=float(row.get("total_cost_usd") or 0.0),
        total_tokens=int(row.get("total_tokens") or 0),
        created_at=row["started_at"],
        topic_tags=list(row.get("topic_tags") or []),
    )
