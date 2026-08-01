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
import re
from collections import defaultdict
from typing import Any

from eleutheria_database.services.db import DatabaseService

logger = logging.getLogger(__name__)

_ALLOWED_PASSAGE_ROLES = {"original", "translation", "paraphrase"}
_PASSAGE_ROLE_ENV = "ELEUTHERIA_PASSAGE_ROLE_FILTER"

# Word tokenizer covering Latin-1 accents, basic Greek (U+0370-03FF, i.e.
# α-ω) and polytonic Greek Extended (U+1F00-1FFF).
_TERM_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ\u0370-\u03FF\u1F00-\u1FFF]+")
_GREEK_CHAR_RE = re.compile(r"[\u0370-\u03FF\u1F00-\u1FFF]")

# The 'simple' text-search config has no stopword list, so plainto_tsquery
# ANDs question words together and natural questions fall off a zero-result
# cliff. These are stripped before the OR-ed retry.
_QUERY_STOPWORDS = frozenset(
    {
        "a",
        "about",
        "according",
        "after",
        "against",
        "all",
        "also",
        "an",
        "and",
        "any",
        "are",
        "as",
        "at",
        "be",
        "because",
        "been",
        "between",
        "but",
        "by",
        "can",
        "did",
        "do",
        "does",
        "for",
        "from",
        "had",
        "has",
        "have",
        "how",
        "in",
        "into",
        "is",
        "it",
        "its",
        "may",
        "not",
        "of",
        "on",
        "or",
        "que",
        "quel",
        "quelle",
        "so",
        "some",
        "such",
        "than",
        "that",
        "the",
        "their",
        "them",
        "then",
        "there",
        "these",
        "they",
        "this",
        "those",
        "to",
        "was",
        "were",
        "what",
        "when",
        "where",
        "which",
        "who",
        "why",
        "with",
        "would",
        "καί",
        "και",
        "δέ",
        "δε",
        "τό",
        "το",
        "τά",
        "τα",
        "ὁ",
        "ἡ",
        "τε",
        "μέν",
        "μεν",
        "γάρ",
        "γαρ",
    }
)


def _content_terms(query: str) -> list[str]:
    """Tokenize ``query`` into de-duplicated, stopword-free content terms.

    Only word characters survive tokenization, so the result is always safe
    to join into a ``to_tsquery`` expression (which is still passed as a
    bound parameter, never interpolated into SQL).
    """
    terms: list[str] = []
    seen: set[str] = set()
    for token in _TERM_RE.findall(query or ""):
        lowered = token.lower()
        if len(lowered) < 2 or lowered in _QUERY_STOPWORDS or lowered in seen:
            continue
        seen.add(lowered)
        terms.append(lowered)
    return terms


def or_tsquery_string(query: str) -> str | None:
    """Build an OR-ed ``to_tsquery`` input (``a | b | c``) from ``query``.

    Returns ``None`` when nothing usable remains, in which case the caller
    should skip the retry.
    """
    terms = _content_terms(query)
    if not terms:
        return None
    return " | ".join(terms)


# Upper bound on the number of per-lemma containment probes in one query.
_MAX_LEMMA_PROBES = 8


def _lemma_candidates(lemma: str) -> list[str]:
    """Split ``lemma`` into the lemma forms to probe against ``morphology``.

    A bare dictionary form is returned verbatim (the historical behaviour).
    A natural-language query is tokenized, so each word is probed on its own —
    the stored morphology holds per-word lemmas and could never contain a
    whole sentence. Tokens are Greek/Latin-script words by construction; a
    query with none (digits, punctuation only) yields an empty list and the
    caller skips the leg.
    """
    tokens = _TERM_RE.findall(lemma or "")
    if not tokens:
        return []
    if len(tokens) == 1:
        return tokens[:1]

    candidates: list[str] = []
    seen: set[str] = set()
    for token in tokens:
        lowered = token.lower()
        if len(lowered) < 3 or lowered in _QUERY_STOPWORDS or lowered in seen:
            continue
        seen.add(lowered)
        candidates.append(token)
        if len(candidates) >= _MAX_LEMMA_PROBES:
            break
    return candidates


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


_ALLOWED_TSQUERY_FNS = {"plainto_tsquery", "to_tsquery"}


def _legacy_fts_fragments(
    query_param: str, tsquery_fn: str = "plainto_tsquery"
) -> tuple[str, str]:
    tsq = f"{tsquery_fn}('simple', {query_param})"
    return (
        f"to_tsvector('simple', p.text_content) @@ {tsq}",
        f"ts_rank(to_tsvector('simple', p.text_content), {tsq})",
    )


async def fts_fragments_ex(
    db: DatabaseService, query_param: str, tsquery_fn: str = "plainto_tsquery"
) -> tuple[str, str]:
    """Return ``(match_condition, rank_expression)`` for a chosen tsquery parser.

    ``tsquery_fn`` selects the query parser: ``plainto_tsquery`` (all terms
    ANDed) or ``to_tsquery`` (caller supplies an operator string such as
    ``a | b | c`` as the *bound parameter*). It is validated against a closed
    allowlist before being inlined into SQL.

    Once migration ``20260610_02_unify_fts_simple_unaccent.sql`` has run
    (detected via ``free_will.f_unaccent``), queries hit the stored
    'simple'+unaccent ``search_vector`` column and its GIN index. Before
    the migration the legacy runtime ``to_tsvector('simple', ...)``
    expression is kept, so code and migration can deploy in either order.
    Probe failures are not cached.
    """
    global _UNACCENT_AVAILABLE
    if tsquery_fn not in _ALLOWED_TSQUERY_FNS:
        tsquery_fn = "plainto_tsquery"
    if _UNACCENT_AVAILABLE is None:
        try:
            row = await db.fetchrow(_F_UNACCENT_PROBE)
            _UNACCENT_AVAILABLE = bool(row and row["available"])
        except Exception:
            logger.warning("f_unaccent capability probe failed", exc_info=True)
            return _legacy_fts_fragments(query_param, tsquery_fn)
    if _UNACCENT_AVAILABLE:
        tsq = f"{tsquery_fn}('simple', free_will.f_unaccent({query_param}))"
        return (
            f"p.search_vector @@ {tsq}",
            f"ts_rank(p.search_vector, {tsq})",
        )
    return _legacy_fts_fragments(query_param, tsquery_fn)


async def fts_fragments(db: DatabaseService, query_param: str) -> tuple[str, str]:
    """Return ``(match_condition, rank_expression)`` for the FTS leg.

    Backward-compatible wrapper around :func:`fts_fragments_ex`.
    """
    return await fts_fragments_ex(db, query_param)


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
            results = await self._fulltext_rows(query, limit, "plainto_tsquery")
            if not results:
                # plainto_tsquery ANDs every token, and the 'simple' config has
                # no stopword list — natural questions therefore hit a
                # zero-result cliff. Retry with the content terms OR-ed.
                or_query = or_tsquery_string(query)
                if or_query and or_query != query.strip().lower():
                    results = await self._fulltext_rows(or_query, limit, "to_tsquery")
            return results

        except Exception as e:
            logger.error(f"Error in fulltext_search: {e}")
            return []

    async def _fulltext_rows(
        self, query_text: str, limit: int, tsquery_fn: str
    ) -> list[dict[str, Any]]:
        """Run one FTS pass. ``query_text`` is always a bound parameter."""
        if tsquery_fn not in _ALLOWED_TSQUERY_FNS:
            tsquery_fn = "plainto_tsquery"
        match_cond, rank_expr = await fts_fragments_ex(self.db, "$1", tsquery_fn)
        headline_tsq = f"{tsquery_fn}('simple', $1)"
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
                {headline_tsq},
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

        results = await self.db.fetch(sql, query_text, limit)
        return [dict(r) for r in results]

    async def lemmatic_search(
        self, lemma: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        """
        Search for passages whose morphology carries any of the query lemmas.

        ``lemma`` may be a single dictionary form ('ἐγώ', 'sum') or a whole
        natural-language query. It is tokenized into words and each token is
        probed separately against the ``morphology`` JSONB array — probing the
        untokenized string could never match a stored per-word lemma.

        Args:
            lemma: Dictionary form, or a query to tokenize into lemmas
            limit: Maximum results to return

        Returns:
            List of passages containing at least one of the lemmas
        """
        try:
            lemmas = _lemma_candidates(lemma)
            if not lemmas:
                return []

            # One containment probe per lemma, OR-ed. Each lemma is a bound
            # parameter — never interpolated into the SQL string.
            probes = " OR ".join(
                "p.morphology @> "
                f"jsonb_build_array(jsonb_build_object('l', ${i}::text))"
                for i in range(1, len(lemmas) + 1)
            )
            limit_param = f"${len(lemmas) + 1}"
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
            WHERE ({probes})
              AND {passage_role_condition("p")}
            ORDER BY p.work_id, p.sequence_number
            LIMIT {limit_param}
            """

            results = await self.db.fetch(sql, *lemmas, limit)
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
                results = await self._author_rows(
                    author, query, limit, role_cond, "plainto_tsquery"
                )
                if not results:
                    # Same zero-result cliff as fulltext_search: retry with the
                    # content terms OR-ed instead of ANDed.
                    or_query = or_tsquery_string(query)
                    if or_query and or_query != query.strip().lower():
                        results = await self._author_rows(
                            author, or_query, limit, role_cond, "to_tsquery"
                        )
                return results

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
            rows = await self.db.fetch(sql, author, limit)
            return [dict(r) for r in rows]

        except Exception as e:
            logger.error(f"Error in search_by_author: {e}")
            return []

    async def _author_rows(
        self,
        author: str,
        query_text: str,
        limit: int,
        role_cond: str,
        tsquery_fn: str,
    ) -> list[dict[str, Any]]:
        """Run one author-scoped FTS pass. Both inputs are bound parameters."""
        if tsquery_fn not in _ALLOWED_TSQUERY_FNS:
            tsquery_fn = "plainto_tsquery"
        match_cond, rank_expr = await fts_fragments_ex(self.db, "$2", tsquery_fn)
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
        rows = await self.db.fetch(sql, author, query_text, limit)
        return [dict(r) for r in rows]

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
