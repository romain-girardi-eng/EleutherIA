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

import asyncio
import base64
import binascii
import json
import logging
import re
import time
import uuid
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Annotated, Any, Literal

from eleutheria_database.services.db import DatabaseService
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.dependencies import get_db, get_graphrag

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


# Canonical passages (reception map) -----------------------------------------


class CanonicalPassageItem(BaseModel):
    passage_id: str
    label: str
    citation_count: int
    distinct_answer_count: int
    canonical_ref: str | None
    language: str | None
    work_title: str | None
    author: str | None
    period: str | None
    preview_text: str | None
    preview_slugs: list[str]


class CanonicalPassagesResponse(BaseModel):
    items: list[CanonicalPassageItem]
    total: int


class CitingAnswer(BaseModel):
    slug: str
    query: str
    excerpt: str
    citation_count: int
    created_at: datetime


class CanonicalPassageDetail(CanonicalPassageItem):
    full_text: str | None
    citing_answers: list[CitingAnswer]


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
        except (json.JSONDecodeError, ValueError) as _exc:
            del _exc
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


# ---------------------------------------------------------------------------
# Canonical passages — reception map of the corpus
# ---------------------------------------------------------------------------


_CITING_ANSWERS_CAP = 50
_CANONICAL_LIMIT_CAP = 200


def _preview_slugs(value: Any) -> list[str]:
    """Decode the comma/json-encoded preview slugs returned by SQL."""
    decoded = _maybe_json(value)
    if isinstance(decoded, list):
        return [s for s in decoded if isinstance(s, str)]
    if isinstance(value, list):
        return [s for s in value if isinstance(s, str)]
    return []


@router.get("/canonical-passages", response_model=CanonicalPassagesResponse)
async def list_canonical_passages(
    db: Annotated[DatabaseService, Depends(get_db)],
    limit: int = Query(50, ge=1, le=_CANONICAL_LIMIT_CAP),
    period: str | None = None,
    author: str | None = None,
) -> CanonicalPassagesResponse:
    """Most-cited passages across all public GraphRAG answers.

    Aggregates ``query_traces.final_answer_citations`` (jsonb array). A
    passage that has been called upon by many distinct scholarly answers is
    a ``locus classicus`` — we rank by ``distinct_answer_count`` first, then
    raw ``citation_count`` as a tiebreaker. Optional ``period`` / ``author``
    filters apply to the joined ``ancient_works`` row (ILIKE).
    """
    period_param = period if period else None
    author_param = author if author else None

    sql = """
        WITH cited AS (
            SELECT
                cit->>'id'    AS passage_id,
                cit->>'label' AS label,
                qt.share_slug
            FROM free_will.query_traces qt,
                 jsonb_array_elements(qt.final_answer_citations) AS cit
            WHERE qt.is_public = true
              AND qt.final_answer_text IS NOT NULL
              AND length(qt.final_answer_text) >= $4
              AND cit->>'type' = 'passage'
              AND cit->>'id' IS NOT NULL
        ),
        aggregated AS (
            SELECT
                passage_id,
                min(label) AS label,
                count(*) AS citation_count,
                count(DISTINCT share_slug) AS distinct_answer_count,
                array_agg(DISTINCT share_slug) AS answer_slugs
            FROM cited
            GROUP BY passage_id
        )
        SELECT
            a.passage_id,
            a.label,
            a.citation_count,
            a.distinct_answer_count,
            (a.answer_slugs)[1:5] AS preview_slugs,
            p.text_content,
            p.canonical_ref,
            w.language,
            w.title  AS work_title,
            w.author AS author_label,
            w.period
        FROM aggregated a
        LEFT JOIN free_will.passages p
               ON p.passage_id::text = a.passage_id
        LEFT JOIN free_will.ancient_works w
               ON w.work_id = p.work_id
        WHERE ($1::text IS NULL OR w.period ILIKE $1)
          AND ($2::text IS NULL OR w.author ILIKE $2)
        ORDER BY a.distinct_answer_count DESC,
                 a.citation_count DESC,
                 a.passage_id
        LIMIT $3
    """

    rows = await db.fetch(sql, period_param, author_param, limit, _MIN_ANSWER_LEN)

    items: list[CanonicalPassageItem] = []
    for row in rows:
        text_content = row.get("text_content")
        preview = _excerpt(text_content) if text_content else None
        items.append(
            CanonicalPassageItem(
                passage_id=str(row["passage_id"]),
                label=row.get("label") or row.get("canonical_ref") or "",
                citation_count=int(row.get("citation_count") or 0),
                distinct_answer_count=int(row.get("distinct_answer_count") or 0),
                canonical_ref=row.get("canonical_ref"),
                language=row.get("language"),
                work_title=row.get("work_title"),
                author=row.get("author_label"),
                period=row.get("period"),
                preview_text=preview,
                preview_slugs=_preview_slugs(row.get("preview_slugs")),
            )
        )

    # Total: how many distinct passages match the same filter set
    count_sql = """
        WITH cited AS (
            SELECT DISTINCT cit->>'id' AS passage_id
            FROM free_will.query_traces qt,
                 jsonb_array_elements(qt.final_answer_citations) AS cit
            WHERE qt.is_public = true
              AND qt.final_answer_text IS NOT NULL
              AND length(qt.final_answer_text) >= $3
              AND cit->>'type' = 'passage'
              AND cit->>'id' IS NOT NULL
        )
        SELECT count(*) AS total
        FROM cited c
        LEFT JOIN free_will.passages p
               ON p.passage_id::text = c.passage_id
        LEFT JOIN free_will.ancient_works w
               ON w.work_id = p.work_id
        WHERE ($1::text IS NULL OR w.period ILIKE $1)
          AND ($2::text IS NULL OR w.author ILIKE $2)
    """
    total_row = await db.fetchrow(
        count_sql, period_param, author_param, _MIN_ANSWER_LEN
    )
    total = int((total_row or {}).get("total") or 0)

    return CanonicalPassagesResponse(items=items, total=total)


@router.get(
    "/canonical-passages/{passage_id}",
    response_model=CanonicalPassageDetail,
)
async def get_canonical_passage(
    passage_id: str,
    db: Annotated[DatabaseService, Depends(get_db)],
) -> CanonicalPassageDetail:
    """Reverse-index: full passage text + every public answer citing it."""
    aggregate_sql = """
        WITH cited AS (
            SELECT
                cit->>'id'    AS passage_id,
                cit->>'label' AS label,
                qt.share_slug
            FROM free_will.query_traces qt,
                 jsonb_array_elements(qt.final_answer_citations) AS cit
            WHERE qt.is_public = true
              AND qt.final_answer_text IS NOT NULL
              AND length(qt.final_answer_text) >= $2
              AND cit->>'type' = 'passage'
              AND cit->>'id' = $1
        )
        SELECT
            $1 AS passage_id,
            min(c.label) AS label,
            count(*) AS citation_count,
            count(DISTINCT c.share_slug) AS distinct_answer_count,
            (array_agg(DISTINCT c.share_slug))[1:5] AS preview_slugs,
            p.text_content,
            p.canonical_ref,
            w.language,
            w.title  AS work_title,
            w.author AS author_label,
            w.period
        FROM cited c
        LEFT JOIN free_will.passages p
               ON p.passage_id::text = $1
        LEFT JOIN free_will.ancient_works w
               ON w.work_id = p.work_id
        GROUP BY p.text_content, p.canonical_ref, w.language,
                 w.title, w.author, w.period
    """
    aggregate = await db.fetchrow(aggregate_sql, passage_id, _MIN_ANSWER_LEN)

    if not aggregate or not (aggregate.get("citation_count") or 0):
        raise HTTPException(status_code=404, detail="Passage not cited")

    # Per-answer counts + queries + excerpts
    citing_sql = """
        WITH per_trace AS (
            SELECT
                qt.share_slug,
                qt.query,
                qt.final_answer_text,
                qt.started_at,
                (
                    SELECT count(*)
                    FROM jsonb_array_elements(qt.final_answer_citations) AS cit
                    WHERE cit->>'id' = $1
                      AND cit->>'type' = 'passage'
                ) AS cnt
            FROM free_will.query_traces qt
            WHERE qt.is_public = true
              AND qt.final_answer_text IS NOT NULL
              AND length(qt.final_answer_text) >= $2
              AND EXISTS (
                  SELECT 1
                  FROM jsonb_array_elements(qt.final_answer_citations) AS cit
                  WHERE cit->>'id' = $1
                    AND cit->>'type' = 'passage'
              )
        )
        SELECT share_slug, query, final_answer_text, started_at, cnt
        FROM per_trace
        ORDER BY cnt DESC, started_at DESC, share_slug DESC
        LIMIT $3
    """
    citing_rows = await db.fetch(
        citing_sql, passage_id, _MIN_ANSWER_LEN, _CITING_ANSWERS_CAP
    )

    citing_answers: list[CitingAnswer] = []
    for row in citing_rows:
        answer_text = row.get("final_answer_text") or ""
        citing_answers.append(
            CitingAnswer(
                slug=row["share_slug"],
                query=row.get("query") or "",
                excerpt=_excerpt(answer_text),
                citation_count=int(row.get("cnt") or 0),
                created_at=row["started_at"],
            )
        )

    text_content = aggregate.get("text_content")
    preview = _excerpt(text_content) if text_content else None

    return CanonicalPassageDetail(
        passage_id=passage_id,
        label=aggregate.get("label") or aggregate.get("canonical_ref") or "",
        citation_count=int(aggregate.get("citation_count") or 0),
        distinct_answer_count=int(aggregate.get("distinct_answer_count") or 0),
        canonical_ref=aggregate.get("canonical_ref"),
        language=aggregate.get("language"),
        work_title=aggregate.get("work_title"),
        author=aggregate.get("author_label"),
        period=aggregate.get("period"),
        preview_text=preview,
        preview_slugs=_preview_slugs(aggregate.get("preview_slugs")),
        full_text=text_content,
        citing_answers=citing_answers,
    )


# ---------------------------------------------------------------------------
# Reproducibility — per-slug certificate + on-demand reverification
# ---------------------------------------------------------------------------


_PASSAGE_REF_RE = re.compile(r"P-[A-Za-z0-9_\-]+")


class ReproducibilityStatus(BaseModel):
    slug: str
    cached_at_kg_version: int
    current_kg_version: int
    kg_advanced_by: int
    status: Literal["unchanged", "kg_advanced", "stale_unknown"]
    cached_at: datetime
    current_kg_updated_at: datetime


class ReverifyResponse(BaseModel):
    slug: str
    original_trace_id: str
    new_trace_id: str
    char_count_diff: int
    citation_diff: dict[str, list[str]]
    similarity: float
    kg_advanced_by: int
    new_answer_excerpt: str


def _extract_passage_refs(
    answer_text: str, citations: list[dict[str, Any]]
) -> set[str]:
    """Collect every passage reference (P-…) used in an answer.

    Pulls from two sources: explicit ``passage_id`` fields on the citations
    list (authoritative when present) and inline ``P-…`` tokens in the
    answer body (resilient against malformed citation objects)."""
    refs: set[str] = set()
    for citation in citations:
        if not isinstance(citation, dict):
            continue
        pid = citation.get("passage_id") or citation.get("id")
        if isinstance(pid, str) and pid:
            refs.add(pid)
    refs.update(_PASSAGE_REF_RE.findall(answer_text or ""))
    return refs


def _jaccard_word_similarity(a: str, b: str) -> float:
    """Cheap, dependency-free similarity over normalized word sets.

    sklearn is not a hard backend dep, so we use word-level Jaccard. It is
    monotonic in the same direction as TF-IDF cosine for our use case
    (high-overlap drafts produced by the same pipeline) and good enough to
    answer "is this answer materially different?" — which is all the
    reproducibility certificate claims."""
    if not a and not b:
        return 1.0
    tokens_a = {t for t in re.findall(r"\w+", a.lower()) if len(t) > 1}
    tokens_b = {t for t in re.findall(r"\w+", b.lower()) if len(t) > 1}
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = len(tokens_a & tokens_b)
    union = len(tokens_a | tokens_b)
    return intersection / union if union else 0.0


async def _load_trace_for_slug(db: DatabaseService, slug: str) -> dict[str, Any]:
    """Fetch the canonical trace row for a public slug or raise 404.

    Mirrors the visibility rules of ``get_query`` so the reproducibility
    surface is consistent: public + non-stub answers only."""
    row = await db.fetchrow(
        """
        SELECT
            trace_id,
            share_slug,
            query,
            final_answer_text,
            final_answer_citations,
            metadata,
            kg_version_at_creation,
            is_public,
            started_at,
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
    return dict(row)


@router.get(
    "/queries/{slug}/reproducibility",
    response_model=ReproducibilityStatus,
)
async def reproducibility_status(
    slug: str,
    db: Annotated[DatabaseService, Depends(get_db)],
) -> ReproducibilityStatus:
    """Reproducibility certificate for a cached Q&A.

    Compares the KG version a trace was produced against with the live
    version, surfacing the delta so the FE can render a "stale by N
    edits" badge and offer the reverify CTA."""
    row = await _load_trace_for_slug(db, slug)
    cached_version = int(row.get("kg_version_at_creation") or 0)

    version_row = await db.fetchrow(
        "SELECT version, updated_at FROM free_will.kg_version WHERE id = 1"
    )
    if version_row is None:
        # No kg_version row at all (fresh DB) — treat the cached trace as
        # the only authority we have. Delta = 0.
        current_version = 0
        current_updated_at = row["started_at"]
    else:
        current_version = int(version_row.get("version") or 0)
        current_updated_at = version_row.get("updated_at") or row["started_at"]

    if cached_version == 0:
        status: Literal["unchanged", "kg_advanced", "stale_unknown"] = "stale_unknown"
    elif cached_version == current_version:
        status = "unchanged"
    else:
        status = "kg_advanced"

    return ReproducibilityStatus(
        slug=slug,
        cached_at_kg_version=cached_version,
        current_kg_version=current_version,
        kg_advanced_by=max(0, current_version - cached_version)
        if cached_version > 0
        else 0,
        status=status,
        cached_at=row["started_at"],
        current_kg_updated_at=current_updated_at,
    )


async def _run_reverification(
    *,
    db: DatabaseService,
    graphrag: Any,
    slug: str,
    row: dict[str, Any],
    progress_queue: asyncio.Queue[dict[str, Any]],
) -> ReverifyResponse:
    """Drive a fresh pipeline run for the given slug and compute the diff.

    Runs synchronously inside the SSE producer task. Emits ``progress``
    payloads onto ``progress_queue`` at well-known stage boundaries so the
    FE can render a busy indicator without depending on a streaming
    answer body."""
    started = time.perf_counter()

    async def _emit(stage: str) -> None:
        await progress_queue.put(
            {
                "stage": stage,
                "elapsed_s": round(time.perf_counter() - started, 2),
            }
        )

    metadata = _maybe_json(row.get("metadata")) or {}
    selected_model = _model_from_metadata(metadata) or "gemini-3.1-pro"
    retrieval_mode = (
        metadata.get("retrieval_mode")
        if isinstance(metadata, dict)
        and isinstance(metadata.get("retrieval_mode"), str)
        else "auto"
    )

    original_answer = row.get("final_answer_text") or ""
    original_citations = _citations_list(row.get("final_answer_citations"))
    original_refs = _extract_passage_refs(original_answer, original_citations)
    original_kg_version = int(row.get("kg_version_at_creation") or 0)

    await _emit("starting")

    # Re-run the agentic pipeline live. We deliberately call ``query()``
    # (not ``query_stream``) — the DB-level answer cache only sits in front
    # of the stream endpoint, so this path is naturally cache-free, and
    # we don't need partial tokens here, just the final answer.
    await _emit("retrieval")
    result = await graphrag.query(
        question=row.get("query") or "",
        selected_model=selected_model,
        retrieval_mode=retrieval_mode,
    )
    await _emit("synthesis_complete")

    new_answer = (result or {}).get("answer", "") if isinstance(result, dict) else ""
    new_citations_raw = (
        ((result or {}).get("passage_citations") if isinstance(result, dict) else None)
        or ((result or {}).get("citations") if isinstance(result, dict) else None)
        or []
    )
    new_citations = [c for c in new_citations_raw if isinstance(c, dict)]
    new_refs = _extract_passage_refs(new_answer, new_citations)

    citation_diff = {
        "added": sorted(new_refs - original_refs),
        "removed": sorted(original_refs - new_refs),
    }
    char_diff = len(new_answer) - len(original_answer)
    similarity = _jaccard_word_similarity(original_answer, new_answer)

    # Persist the rerun as a separate trace row so the diff is auditable.
    # The TraceWriter spawned by ``query_stream`` is what normally does
    # this, but we're calling the non-streaming path; fall back to a
    # lightweight direct insert.
    new_trace_id = uuid.uuid4()
    try:
        current_version = (
            await db.fetchval("SELECT version FROM free_will.kg_version WHERE id = 1")
        ) or 0
    except Exception:  # noqa: BLE001
        current_version = 0

    reverify_metadata = {
        "endpoint": "community.reverify",
        "reverify_of_slug": slug,
        "reverify_of_trace_id": str(row.get("trace_id")),
        "model": selected_model,
        "retrieval_mode": retrieval_mode,
    }
    try:
        await db.execute(
            """
            INSERT INTO free_will.query_traces (
                trace_id, query, started_at, completed_at, mode,
                final_answer_text, final_answer_citations,
                metadata, kg_version_at_creation, is_public
            ) VALUES (
                $1, $2, now(), now(), $3,
                $4, $5::jsonb,
                $6::jsonb, $7::bigint, false
            )
            ON CONFLICT (trace_id) DO NOTHING
            """,
            new_trace_id,
            row.get("query") or "",
            "react",
            new_answer,
            json.dumps(new_citations, default=str),
            json.dumps(reverify_metadata, default=str),
            int(current_version),
        )
    except Exception:  # noqa: BLE001 — never fail the API on audit-write trouble
        logger.exception("reverify: failed to persist rerun trace for slug %s", slug)

    excerpt = new_answer[:400]
    kg_advanced_by = (
        max(0, int(current_version) - original_kg_version)
        if original_kg_version > 0
        else 0
    )

    return ReverifyResponse(
        slug=slug,
        original_trace_id=str(row.get("trace_id")),
        new_trace_id=str(new_trace_id),
        char_count_diff=char_diff,
        citation_diff=citation_diff,
        similarity=round(similarity, 4),
        kg_advanced_by=kg_advanced_by,
        new_answer_excerpt=excerpt,
    )


@router.post("/queries/{slug}/reverify")
async def reverify_query(
    slug: str,
    db: Annotated[DatabaseService, Depends(get_db)],
    graphrag: Annotated[Any, Depends(get_graphrag)],
) -> StreamingResponse:
    """Re-run a cached Q&A against the live KG and stream the diff.

    The full pipeline takes ~7 minutes; this endpoint streams Server-Sent
    Events so the FE can render progress.

    SSE event types:
      * ``progress`` — ``{stage, elapsed_s}`` heartbeats during retrieval
        and synthesis.
      * ``complete`` — terminal event carrying a ``ReverifyResponse``.
      * ``error``   — terminal event with an ``error`` string.
    """
    row = await _load_trace_for_slug(db, slug)

    progress_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
    _SENTINEL: dict[str, Any] = {"__done__": True}

    async def _producer() -> ReverifyResponse | Exception:
        try:
            response = await _run_reverification(
                db=db,
                graphrag=graphrag,
                slug=slug,
                row=row,
                progress_queue=progress_queue,
            )
            await progress_queue.put(_SENTINEL)
            return response
        except Exception as exc:  # noqa: BLE001
            logger.exception("reverify: pipeline failed for slug %s", slug)
            await progress_queue.put(_SENTINEL)
            return exc

    async def _event_stream() -> AsyncIterator[str]:
        producer_task = asyncio.create_task(_producer())
        try:
            while True:
                item = await progress_queue.get()
                if item is _SENTINEL:
                    break
                yield (
                    "event: progress\n"
                    f"data: {json.dumps({'type': 'progress', 'data': item})}\n\n"
                )
            outcome = await producer_task
            if isinstance(outcome, Exception):
                yield (
                    "event: error\n"
                    f"data: {json.dumps({'type': 'error', 'error': str(outcome)})}\n\n"
                )
            else:
                payload = outcome.model_dump(mode="json")
                yield (
                    "event: complete\n"
                    f"data: {json.dumps({'type': 'complete', 'data': payload}, default=str)}\n\n"
                )
        finally:
            if not producer_task.done():
                producer_task.cancel()

    return StreamingResponse(
        _event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
