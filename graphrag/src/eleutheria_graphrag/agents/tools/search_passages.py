"""search_passages tool — full-text search across the passage corpus."""

from __future__ import annotations

import logging
import os
from typing import Any

from pydantic import BaseModel, Field

from eleutheria_graphrag.agents.dependencies import Deps

logger = logging.getLogger(__name__)

DB_SCHEMA = os.getenv("ELEUTHERIA_DB_SCHEMA", "free_will")


class PassageHit(BaseModel):
    passage_id: str
    work_title: str = ""
    author: str | None = None
    canonical_ref: str | None = None
    language: str | None = None
    text_content: str = Field(default="", description="Up to 800 chars")
    score: float = 0.0


class SearchPassagesResult(BaseModel):
    passages: list[PassageHit]
    total_found: int


class SearchPassagesTool:
    """Full-text search across the ancient text corpus."""

    def __init__(self, deps: Deps) -> None:
        self._deps = deps

    @property
    def name(self) -> str:
        return "search_passages"

    @property
    def description(self) -> str:
        return (
            "Search the full corpus of ancient texts by keyword. "
            "Combines full-text search and lemmatic search (for Greek/Latin lemmas). "
            "Use this when you need to find specific textual evidence without going "
            "through the knowledge graph, or to search within a specific work."
        )

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search text (supports Greek/Latin)"},
                "work_filter": {
                    "type": "string",
                    "description": "Filter by work_id to search within a specific work",
                },
                "limit": {"type": "integer", "default": 5, "minimum": 1, "maximum": 10},
            },
            "required": ["query"],
        }

    async def execute(self, args: dict[str, Any]) -> SearchPassagesResult:
        query = args["query"]
        work_filter = args.get("work_filter")
        limit = min(max(args.get("limit", 5), 1), 10)

        passages: list[PassageHit] = []

        # Try HybridSearchService first
        if self._deps.search:
            try:
                results = await self._deps.search.hybrid_search(
                    query=query,
                    limit=limit * 3,  # Fetch extra for post-filtering
                )
                for row in results:
                    if work_filter:
                        if row.get("work_id") != work_filter:
                            continue
                    passages.append(PassageHit(
                        passage_id=str(row.get("passage_id") or row.get("id", "")),
                        work_title=row.get("title", ""),
                        author=row.get("author"),
                        canonical_ref=row.get("canonical_ref"),
                        language=row.get("language"),
                        text_content=(row.get("text_content") or "")[:800],
                        score=row.get("rank", 0.0),
                    ))
                    if len(passages) >= limit:
                        break

                return SearchPassagesResult(
                    passages=passages,
                    total_found=len(results),
                )
            except Exception:
                logger.warning("HybridSearch failed, falling back to SQL", exc_info=True)

        # Fallback: ILIKE search (works across Greek/Latin/English)
        work_clause = ""
        params: list[Any] = [f"%{query}%", limit]
        if work_filter:
            # Match by kg_work_id, canonical_id, or work_id UUID
            work_clause = "AND (w.kg_work_id = $3 OR w.canonical_id = $3 OR w.work_id::text = $3 OR w.title ILIKE ('%' || $3 || '%'))"
            params.append(work_filter)

        sql = f"""
            SELECT
                p.passage_id::text,
                w.title,
                w.author,
                p.canonical_ref,
                w.language,
                p.text_content,
                1.0 AS rank
            FROM {DB_SCHEMA}.passages p
            JOIN {DB_SCHEMA}.ancient_works w ON w.work_id = p.work_id
            WHERE p.text_content ILIKE $1
            {work_clause}
            ORDER BY p.sequence_number
            LIMIT $2
        """

        try:
            rows = await self._deps.db.fetch(sql, *params)
        except Exception:
            logger.warning("SQL fallback failed in search_passages", exc_info=True)
            rows = []

        passages = [
            PassageHit(
                passage_id=row["passage_id"],
                work_title=row.get("title", ""),
                author=row.get("author"),
                canonical_ref=row.get("canonical_ref"),
                language=row.get("language"),
                text_content=(row.get("text_content") or "")[:800],
                score=row.get("rank", 0.0),
            )
            for row in rows
        ]

        return SearchPassagesResult(
            passages=passages,
            total_found=len(passages),
        )
