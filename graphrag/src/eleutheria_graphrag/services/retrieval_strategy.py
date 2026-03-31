"""Retrieval strategies for the DiscoverCorpus FSM node."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any, Protocol

logger = logging.getLogger(__name__)


class RetrievalStrategy(Protocol):
    """Interface for corpus discovery — returns seed node IDs and passage anchor IDs."""

    async def discover_seeds(
        self,
        queries: list[str],
        deps: Any,
        node_limit: int = 100,
    ) -> tuple[list[str], list[str]]:
        """Returns (seed_node_ids, passage_anchor_ids)."""
        ...


EmbedFn = Callable[[Any, str], Awaitable[list[float]]]


class VectorStrategy:
    """Embed queries via Gemini, search Qdrant for seed nodes."""

    def __init__(self, embed_fn: EmbedFn) -> None:
        self._embed = embed_fn

    async def discover_seeds(
        self,
        queries: list[str],
        deps: Any,
        node_limit: int = 100,
    ) -> tuple[list[str], list[str]]:
        seed_ids: list[str] = []
        limit_per_query = max(8, node_limit // max(1, len(queries)))

        for query in queries:
            try:
                embedding = await self._embed(deps, query)
                hits = await deps.qdrant.search_nodes(embedding, limit=limit_per_query)
            except Exception:
                logger.warning("VectorStrategy failed for query %r", query, exc_info=True)
                continue

            for hit in hits:
                node_id = hit.id if hasattr(hit, "id") else str(hit)
                if node_id not in seed_ids:
                    seed_ids.append(node_id)

        passage_anchors = seed_ids[:12]
        return seed_ids, passage_anchors


DB_SCHEMA = "free_will"


def _dedup(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


class SQLStrategy:
    """SQL-only retrieval with 4-step escalation. No Qdrant or embedding calls."""

    def __init__(self, min_bundles: int = 4) -> None:
        self._min_bundles = min_bundles

    async def discover_seeds(
        self,
        queries: list[str],
        deps: Any,
        node_limit: int = 100,  # noqa: ARG002 — protocol compliance
    ) -> tuple[list[str], list[str]]:
        seed_ids: list[str] = []
        passage_anchor_ids: list[str] = []

        # Step 1: Direct passage_citations via kg_nodes label/description match
        matched_node_ids = await self._step1_label_match(queries, deps)
        if matched_node_ids:
            citations = await self._fetch_citations(matched_node_ids, deps)
            seed_ids.extend(matched_node_ids)
            passage_anchor_ids.extend(c["kg_node_id"] for c in citations)

            # 1-hop graph expansion from in-memory edges
            expanded = self._expand_1hop(matched_node_ids, deps)
            seed_ids.extend(nid for nid in expanded if nid not in seed_ids)

        if len(passage_anchor_ids) >= self._min_bundles:
            return _dedup(seed_ids), _dedup(passage_anchor_ids[:12])

        # Step 2: HybridSearch (FTS + lemmatic)
        if deps.search is not None:
            hybrid_ids = await self._step2_hybrid_search(queries, deps)
            seed_ids.extend(nid for nid in hybrid_ids if nid not in seed_ids)
            passage_anchor_ids.extend(nid for nid in hybrid_ids if nid not in passage_anchor_ids)

        if len(passage_anchor_ids) >= self._min_bundles:
            return _dedup(seed_ids), _dedup(passage_anchor_ids[:12])

        # Steps 2bis + 3 are handled by FSM's TreeNavigateWorks + ExpandEvidenceBundles
        return _dedup(seed_ids), _dedup(passage_anchor_ids[:12])

    async def _step1_label_match(self, queries: list[str], deps: Any) -> list[str]:
        """Find kg_nodes matching query terms. Prioritizes label matches over description."""
        seen: set[str] = set()
        patterns: list[str] = []
        for q in queries:
            for term in q.split():
                low = term.lower()
                if len(term) >= 3 and low not in seen:
                    seen.add(low)
                    patterns.append(f"%{term}%")
        if not patterns:
            return []
        patterns = patterns[:30]

        placeholders = ", ".join(f"${i + 1}" for i in range(len(patterns)))

        # Tier 1: Label matches — prioritize person/work nodes, then others.
        # Use a scoring approach: label match on person/work = highest priority.
        sql = f"""
            SELECT node_id, type,
                   CASE WHEN type IN ('person', 'work') THEN 2 ELSE 1 END AS priority
            FROM {DB_SCHEMA}.kg_nodes
            WHERE label ILIKE ANY(ARRAY[{placeholders}])
            ORDER BY priority DESC, length(label) ASC
            LIMIT 50
        """
        try:
            label_rows = await deps.db.fetch(sql, *patterns)
        except Exception:
            logger.warning("SQLStrategy step1 label match failed", exc_info=True)
            label_rows = []

        result_ids = [r["node_id"] for r in label_rows]

        # Tier 2: Only search descriptions if label matches are insufficient.
        # Skip short generic terms to avoid matching everything.
        if len(result_ids) < self._min_bundles:
            long_patterns = [p for p in patterns if len(p) > 7]  # %term% where term > 5 chars
            if long_patterns:
                desc_ph = ", ".join(f"${i + 1}" for i in range(len(long_patterns)))
                desc_sql = f"""
                    SELECT DISTINCT node_id
                    FROM {DB_SCHEMA}.kg_nodes
                    WHERE description ILIKE ANY(ARRAY[{desc_ph}])
                      AND type IN ('person', 'work', 'concept', 'argument', 'school')
                    LIMIT 30
                """
                try:
                    desc_rows = await deps.db.fetch(desc_sql, *long_patterns)
                    for r in desc_rows:
                        if r["node_id"] not in result_ids:
                            result_ids.append(r["node_id"])
                except Exception:
                    logger.warning("SQLStrategy step1 description match failed", exc_info=True)

        return result_ids

    async def _fetch_citations(self, node_ids: list[str], deps: Any) -> list[dict[str, Any]]:
        """Fetch passage_citations for given node IDs, ordered by confidence."""
        if not node_ids:
            return []

        # Use individual $1, $2, ... placeholders for pgbouncer compatibility.
        placeholders = ", ".join(f"${i + 1}" for i in range(len(node_ids)))
        sql = f"""
            SELECT passage_id, kg_node_id, confidence
            FROM {DB_SCHEMA}.passage_citations
            WHERE kg_node_id = ANY(ARRAY[{placeholders}])
            ORDER BY confidence DESC
            LIMIT 100
        """
        try:
            return await deps.db.fetch(sql, *node_ids)
        except Exception:
            logger.warning("SQLStrategy fetch_citations failed", exc_info=True)
            return []

    def _expand_1hop(self, node_ids: list[str], deps: Any) -> list[str]:
        """Expand seed nodes by 1 hop using in-memory edge dicts."""
        expanded: list[str] = []
        outgoing = getattr(deps, "outgoing_edges", {})
        incoming = getattr(deps, "incoming_edges", {})
        for nid in node_ids:
            for edge in outgoing.get(nid, []):
                target = edge.get("target") or edge.get("target_id", "")
                if target and target not in expanded:
                    expanded.append(target)
            for edge in incoming.get(nid, []):
                source = edge.get("source") or edge.get("source_id", "")
                if source and source not in expanded:
                    expanded.append(source)
        return expanded[:50]

    async def _step2_hybrid_search(self, queries: list[str], deps: Any) -> list[str]:
        """Use HybridSearchService for FTS + lemmatic search."""
        all_ids: list[str] = []
        for query in queries[:3]:
            try:
                results = await deps.search.hybrid_search(query, limit=30)
                for r in results:
                    pid = r.get("passage_id") or r.get("id")
                    if pid and pid not in all_ids:
                        all_ids.append(pid)
            except Exception:
                logger.warning("SQLStrategy step2 hybrid_search failed for %r", query, exc_info=True)
        return all_ids
