"""
Hybrid Search Service - Full-text and lemmatic search on ancient texts.

This service provides database-level search functionality:
- Full-text search using PostgreSQL GIN indexes
- Lemmatic search on pre-indexed lemma data
- Reciprocal Rank Fusion (RRF) for combining results

The legacy vector leg has been retired; GraphRAG now uses the vectorless
SQL/tree/lemma retrieval strategy in the graphrag package.
"""

import logging
import os
from collections import defaultdict
from typing import Any

from eleutheria_database.services.db import DatabaseService

logger = logging.getLogger(__name__)

_ALLOWED_PASSAGE_ROLES = {"original", "translation", "paraphrase"}
_PASSAGE_ROLE_ENV = "ELEUTHERIA_PASSAGE_ROLE_FILTER"

# Capability cache for the post-migration FTS fast path (module-level so the
# probe runs once per process across all consumers). None = not probed yet.
_UNACCENT_AVAILABLE: bool | None = None
_F_UNACCENT_PROBE = (
    "SELECT to_regprocedure('free_will.f_unaccent(text)') IS NOT NULL AS available"
)


def passage_role_condition(alias: str = "p") -> str:
    """SQL predicate restricting primary-text retrieval to one passage role.

    Defaults to ``original`` so translation/paraphrase stub rows never feed
    ancient-text evidence. Override with ``ELEUTHERIA_PASSAGE_ROLE_FILTER``
    (a role name, or ``all`` to disable). Validated against a closed
    allowlist before being inlined into SQL.
    """
    role = os.environ.get(_PASSAGE_ROLE_ENV, "original").strip().lower()
    if role in {"", "all", "any", "off"}:
        return "TRUE"
    if role not in _ALLOWED_PASSAGE_ROLES:
        role = "original"
    return f"{alias}.passage_role = '{role}'"


def _legacy_fts_fragments(query_param: str) -> tuple[str, str]:
    tsq = f"plainto_tsquery('simple', {query_param})"
    return (
        f"to_tsvector('simple', p.text_content) @@ {tsq}",
        f"ts_rank(to_tsvector('simple', p.text_content), {tsq})",
    )


async def fts_fragments(db: DatabaseService, query_param: str) -> tuple[str, str]:
    """Return ``(match_condition, rank_expression)`` for the FTS leg.

    Once migration ``20260610_02_unify_fts_simple_unaccent.sql`` has run
    (detected via ``free_will.f_unaccent``), queries hit the stored
    'simple'+unaccent ``search_vector`` column and its GIN index. Before
    the migration the legacy runtime ``to_tsvector('simple', ...)``
    expression is kept, so code and migration can deploy in either order.
    Probe failures are not cached.
    """
    global _UNACCENT_AVAILABLE
    if _UNACCENT_AVAILABLE is None:
        try:
            row = await db.fetchrow(_F_UNACCENT_PROBE)
            _UNACCENT_AVAILABLE = bool(row and row["available"])
        except Exception:
            logger.warning("f_unaccent capability probe failed", exc_info=True)
            return _legacy_fts_fragments(query_param)
    if _UNACCENT_AVAILABLE:
        tsq = f"plainto_tsquery('simple', free_will.f_unaccent({query_param}))"
        return (
            f"p.search_vector @@ {tsq}",
            f"ts_rank(p.search_vector, {tsq})",
        )
    return _legacy_fts_fragments(query_param)


class HybridSearchService:
    """
    Database-level hybrid search combining full-text and lemmatic search.

    Uses Reciprocal Rank Fusion (RRF) to merge results from multiple
    search modes into a unified ranking.
    """

    def __init__(self, db_service: DatabaseService) -> None:
        self.db = db_service

    async def fulltext_search(
        self, query: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        """
        Full-text search using PostgreSQL ts_rank on passages table.

        Args:
            query: Search query text
            limit: Maximum results to return

        Returns:
            List of passage results with rank scores and highlighted snippets
        """
        try:
            match_cond, rank_expr = await fts_fragments(self.db, "$1")
            sql = f"""
            SELECT
                p.passage_id::text as id,
                p.passage_id::text as passage_id,
                w.work_id::text as work_id,
                w.title,
                w.author,
                w.period as category,
                w.language,
                p.canonical_ref,
                p.book,
                p.chapter,
                p.section,
                p.text_content,
                {rank_expr} as rank,
                ts_headline(
                    'simple',
                    p.text_content,
                    plainto_tsquery('simple', $1),
                    'MaxWords=50, MinWords=20, HighlightAll=true'
                ) as snippet,
                'fulltext' as source
            FROM free_will.passages p
            JOIN free_will.ancient_works w ON p.work_id = w.work_id
            WHERE {match_cond}
              AND {passage_role_condition("p")}
            ORDER BY rank DESC
            LIMIT $2
            """

            results = await self.db.fetch(sql, query, limit)
            return [dict(r) for r in results]

        except Exception as e:
            logger.error(f"Error in fulltext_search: {e}")
            return []

    async def lemmatic_search(
        self, lemma: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        """
        Search for passages containing a specific lemma.

        Searches the morphology JSONB column for lemma matches.

        Args:
            lemma: Dictionary form to search for (e.g., 'ἐγώ', 'sum')
            limit: Maximum results to return

        Returns:
            List of passages containing the lemma
        """
        try:
            sql = f"""
            SELECT
                p.passage_id::text as id,
                p.passage_id::text as passage_id,
                w.work_id::text as work_id,
                w.title,
                w.author,
                w.period as category,
                w.language,
                p.canonical_ref,
                p.text_content,
                'lemmatic' as source
            FROM free_will.passages p
            JOIN free_will.ancient_works w ON p.work_id = w.work_id
            WHERE p.morphology @> $1::jsonb
              AND {passage_role_condition("p")}
            LIMIT $2
            """

            # Search for lemma in JSONB morphology array
            lemma_pattern = f'[{{"l": "{lemma}"}}]'
            results = await self.db.fetch(sql, lemma_pattern, limit)
            return [dict(r) for r in results]

        except Exception as e:
            logger.error(f"Error in lemmatic_search: {e}")
            return []

    async def search_by_author(
        self, author: str, query: str | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        """
        Search passages by author, optionally filtered by text query.

        Args:
            author: Author name (partial match supported)
            query: Optional text search within author's works
            limit: Maximum results to return

        Returns:
            List of matching passages
        """
        try:
            role_cond = passage_role_condition("p")
            if query:
                match_cond, rank_expr = await fts_fragments(self.db, "$2")
                sql = f"""
                SELECT
                    p.passage_id::text as id,
                    p.passage_id::text as passage_id,
                    w.work_id::text as work_id,
                    w.title,
                    w.author,
                    w.language,
                    p.canonical_ref,
                    p.text_content,
                    {rank_expr} as rank
                FROM free_will.passages p
                JOIN free_will.ancient_works w ON p.work_id = w.work_id
                WHERE w.author ILIKE '%' || $1 || '%'
                  AND {match_cond}
                  AND {role_cond}
                ORDER BY rank DESC
                LIMIT $3
                """
                results = await self.db.fetch(sql, author, query, limit)
            else:
                sql = f"""
                SELECT
                    p.passage_id::text as id,
                    p.passage_id::text as passage_id,
                    w.work_id::text as work_id,
                    w.title,
                    w.author,
                    w.language,
                    p.canonical_ref,
                    p.text_content
                FROM free_will.passages p
                JOIN free_will.ancient_works w ON p.work_id = w.work_id
                WHERE w.author ILIKE '%' || $1 || '%'
                  AND {role_cond}
                ORDER BY p.sequence_number
                LIMIT $2
                """
                results = await self.db.fetch(sql, author, limit)

            return [dict(r) for r in results]

        except Exception as e:
            logger.error(f"Error in search_by_author: {e}")
            return []

    def reciprocal_rank_fusion(
        self,
        results_lists: list[list[dict[str, Any]]],
        id_key: str = "id",
        k: int = 60,
    ) -> list[dict[str, Any]]:
        """
        Combine multiple ranked lists using Reciprocal Rank Fusion (RRF).

        RRF formula: score(d) = sum(1 / (k + rank_i(d)))
        where rank_i(d) is the rank of document d in result list i.

        Args:
            results_lists: List of ranked result lists to merge
            id_key: Key to use for document identity
            k: RRF constant (default 60, per original paper)

        Returns:
            Merged and re-ranked results
        """
        scores: defaultdict[Any, float] = defaultdict(float)
        items: dict[Any, dict[str, Any]] = {}

        # Calculate RRF scores
        for results in results_lists:
            for rank, item in enumerate(results, start=1):
                item_id = item[id_key]
                scores[item_id] += 1 / (k + rank)

                # Store the item (use first occurrence)
                if item_id not in items:
                    items[item_id] = item
                # Merge sources for items appearing in multiple lists
                elif "source" in item:
                    current_source = items[item_id].get("source", "")
                    new_source = item["source"]
                    if new_source not in current_source:
                        items[item_id]["source"] = f"{current_source}, {new_source}"

        # Sort by RRF score
        sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        # Build final results with scores
        results = []
        for item_id, score in sorted_items:
            item = items[item_id].copy()
            item["rrf_score"] = score
            results.append(item)

        return results

    async def hybrid_search(
        self,
        query: str,
        limit: int = 50,
        include_fulltext: bool = True,
        include_lemmatic: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Execute hybrid search combining multiple search modes.

        Args:
            query: Search query
            limit: Maximum results per search mode
            include_fulltext: Whether to include full-text search
            include_lemmatic: Whether to include lemmatic search

        Returns:
            RRF-merged results from all enabled search modes
        """
        results_lists = []

        if include_fulltext:
            fulltext_results = await self.fulltext_search(query, limit)
            if fulltext_results:
                results_lists.append(fulltext_results)

        if include_lemmatic:
            lemmatic_results = await self.lemmatic_search(query, limit)
            if lemmatic_results:
                results_lists.append(lemmatic_results)

        if not results_lists:
            return []

        return self.reciprocal_rank_fusion(results_lists)[:limit]
