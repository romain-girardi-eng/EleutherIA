"""
Search routes — hybrid, fulltext, lemmatic, semantic, autocomplete, KG search.

Wraps the existing HybridSearchService from the database package and adds
semantic search via Qdrant and lemma autocomplete.
"""

import logging
from typing import Annotated, Any

from eleutheria_database.services.db import DatabaseService
from eleutheria_database.services.hybrid_search import HybridSearchService
from eleutheria_kg.services.qdrant import QdrantService
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from backend.dependencies import get_db, get_qdrant, get_search

logger = logging.getLogger(__name__)

router = APIRouter(tags=["search"])


# ---------- Request/Response models ----------

class SearchBody(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(50, ge=1, le=200)


class HybridSearchBody(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(50, ge=1, le=200)
    enable_fulltext: bool = True
    enable_lemmatic: bool = True
    enable_semantic: bool = True
    enable_ai_enhancements: bool = False


class SemanticSearchBody(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(10, ge=1, le=100)
    collection: str = "text_embeddings"


# ---------- Routes ----------

@router.post("/hybrid")
async def hybrid_search(
    body: HybridSearchBody,
    search: Annotated[HybridSearchService, Depends(get_search)],
    qdrant: Annotated[QdrantService, Depends(get_qdrant)],
) -> dict[str, Any]:
    """
    Multi-mode hybrid search combining fulltext, lemmatic, and semantic results
    via Reciprocal Rank Fusion (RRF).
    """
    results_lists: list[list[dict[str, Any]]] = []
    modes_used: list[str] = []

    # Full-text search
    if body.enable_fulltext:
        ft = await search.fulltext_search(body.query, body.limit)
        if ft:
            results_lists.append(ft)
            modes_used.append("fulltext")

    # Lemmatic search
    if body.enable_lemmatic:
        lm = await search.lemmatic_search(body.query, body.limit)
        if lm:
            results_lists.append(lm)
            modes_used.append("lemmatic")

    # Semantic search
    used_semantic = False
    if body.enable_semantic:
        try:
            embedding = await _get_embedding(body.query)
            sem_results = await qdrant.search_texts(embedding, limit=body.limit)
            if sem_results:
                # Normalize keys to match fulltext output
                normalized = []
                for r in sem_results:
                    normalized.append({
                        "id": r.get("passage_id") or r.get("id"),
                        "passage_id": r.get("passage_id"),
                        "work_id": r.get("work_id"),
                        "title": r.get("title", ""),
                        "author": r.get("author", ""),
                        "text_content": r.get("text_content", ""),
                        "canonical_ref": r.get("canonical_ref", ""),
                        "language": r.get("language", ""),
                        "source": "semantic",
                        "score": r.get("score", 0),
                    })
                results_lists.append(normalized)
                modes_used.append("semantic")
                used_semantic = True
        except Exception:
            logger.debug("Semantic search unavailable, falling back to text-based modes", exc_info=True)

    if not results_lists:
        return {
            "combined_results": [],
            "query": body.query,
            "totalResults": 0,
            "usedSemantic": False,
            "modes_used": [],
        }

    combined = search.reciprocal_rank_fusion(results_lists)[:body.limit]

    return {
        "combined_results": combined,
        "query": body.query,
        "totalResults": len(combined),
        "usedSemantic": used_semantic,
        "used_rrf": len(results_lists) > 1,
        "modes_used": modes_used,
    }


@router.post("/fulltext")
async def fulltext_search(
    body: SearchBody,
    search: Annotated[HybridSearchService, Depends(get_search)],
) -> dict[str, Any]:
    """Full-text search using PostgreSQL ts_rank."""
    results = await search.fulltext_search(body.query, body.limit)
    return {"results": results, "query": body.query, "count": len(results)}


@router.post("/lemmatic")
async def lemmatic_search(
    body: SearchBody,
    search: Annotated[HybridSearchService, Depends(get_search)],
) -> dict[str, Any]:
    """Lemmatic search on pre-indexed morphology data."""
    results = await search.lemmatic_search(body.query, body.limit)
    return {"results": results, "query": body.query, "count": len(results)}


@router.post("/semantic")
async def semantic_search(
    body: SemanticSearchBody,
    qdrant: Annotated[QdrantService, Depends(get_qdrant)],
) -> dict[str, Any]:
    """Semantic (vector) search via Qdrant."""
    embedding = await _get_embedding(body.query)
    results = await qdrant.search_texts(embedding, limit=body.limit)
    return {"results": results, "query": body.query, "count": len(results)}


@router.get("/autocomplete/lemmas")
async def autocomplete_lemmas(
    db: Annotated[DatabaseService, Depends(get_db)],
    q: str = Query(..., min_length=1, description="Search prefix"),
    lang: str | None = Query(None, description="Filter by language (grc, lat)"),
    limit: int = Query(20, ge=1, le=100),
    min_count: int = Query(1, ge=1),
    fuzzy: bool = Query(False),
) -> dict[str, Any]:
    """
    Lemma autocomplete with Latin-to-Greek transliteration support.

    Queries the OGA tokens table for lemma suggestions matching the prefix.
    """
    # Determine if query uses Latin characters (transliteration mode)
    is_latin = all(ord(c) < 880 for c in q if c.isalpha())
    mode = "latin-to-greek" if is_latin else "direct"

    conditions = []
    params: list[Any] = []
    param_idx = 0

    if fuzzy:
        param_idx += 1
        conditions.append(f"t.lemma ILIKE '%' || ${param_idx} || '%'")
        params.append(q)
    elif is_latin:
        # Latin-to-Greek: transliterate common patterns and search
        greek_prefix = _latin_to_greek(q)
        param_idx += 1
        conditions.append(f"t.lemma ILIKE ${param_idx} || '%'")
        params.append(greek_prefix)
    else:
        param_idx += 1
        conditions.append(f"t.lemma ILIKE ${param_idx} || '%'")
        params.append(q)

    if lang:
        param_idx += 1
        conditions.append(f"w.language = ${param_idx}")
        params.append(lang)

    param_idx += 1
    min_count_param = param_idx
    params.append(min_count)

    param_idx += 1
    limit_param = param_idx
    params.append(limit)

    where = " AND ".join(conditions)

    sql = f"""
    SELECT
        t.lemma,
        t.pos,
        w.language,
        COUNT(*) as count,
        COUNT(DISTINCT t.work_id) as passage_count
    FROM free_will.oga_tokens t
    JOIN free_will.ancient_works w ON t.work_id = w.work_id
    WHERE {where}
      AND t.lemma IS NOT NULL
    GROUP BY t.lemma, t.pos, w.language
    HAVING COUNT(*) >= ${min_count_param}
    ORDER BY COUNT(*) DESC
    LIMIT ${limit_param}
    """

    rows = await db.fetch(sql, *params)

    suggestions = []
    for r in rows:
        lemma = r["lemma"]
        suggestions.append({
            "lemma": lemma,
            "lemma_latin": _greek_to_latin(lemma) if r.get("language") == "grc" else lemma,
            "language": r.get("language", ""),
            "pos": r.get("pos", ""),
            "count": r.get("count", 0),
            "passage_count": r.get("passage_count", 0),
            "forms": [],
        })

    return {
        "suggestions": suggestions,
        "query": q,
        "mode": mode,
        "fuzzy": fuzzy,
    }


@router.post("/kg")
async def search_kg(
    body: SearchBody,
    qdrant: Annotated[QdrantService, Depends(get_qdrant)],
) -> dict[str, Any]:
    """Search KG nodes by vector similarity."""
    embedding = await _get_embedding(body.query)
    results = await qdrant.search_nodes(embedding, limit=body.limit)
    return {"results": results, "query": body.query, "count": len(results)}


# ---------- Helpers ----------

_LATIN_TO_GREEK_MAP = str.maketrans({
    "a": "\u03b1", "b": "\u03b2", "g": "\u03b3", "d": "\u03b4",
    "e": "\u03b5", "z": "\u03b6", "h": "\u03b7", "q": "\u03b8",
    "i": "\u03b9", "k": "\u03ba", "l": "\u03bb", "m": "\u03bc",
    "n": "\u03bd", "x": "\u03be", "o": "\u03bf", "p": "\u03c0",
    "r": "\u03c1", "s": "\u03c3", "t": "\u03c4", "u": "\u03c5",
    "f": "\u03c6", "c": "\u03c7", "y": "\u03c8", "w": "\u03c9",
})

_GREEK_TO_LATIN_MAP = {v: k for k, v in _LATIN_TO_GREEK_MAP.items() if isinstance(v, str)}


def _latin_to_greek(text: str) -> str:
    """Basic Latin-to-Greek transliteration (Beta Code style)."""
    return text.lower().translate(_LATIN_TO_GREEK_MAP)


def _greek_to_latin(text: str) -> str:
    """Basic Greek-to-Latin transliteration."""
    return "".join(_GREEK_TO_LATIN_MAP.get(c, c) for c in text.lower())


async def _get_embedding(text: str) -> list[float]:
    """Get embedding for text using Gemini."""
    import os

    import google.generativeai as genai

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY required for semantic search")

    genai.configure(api_key=api_key)
    model = os.getenv("GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-001")
    result = genai.embed_content(
        model=model,
        content=text,
        task_type="retrieval_query",
    )
    return result["embedding"]
