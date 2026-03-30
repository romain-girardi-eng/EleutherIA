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
        """Find kg_nodes whose label or description matches query terms."""
        patterns: list[str] = []
        for q in queries:
            for term in q.split():
                if len(term) >= 3:
                    patterns.append(f"%{term}%")
        if not patterns:
            return []

        sql = f"""
            SELECT DISTINCT node_id
            FROM {DB_SCHEMA}.kg_nodes
            WHERE label ILIKE ANY($1::text[]) OR description ILIKE ANY($1::text[])
            LIMIT 200
        """
        try:
            rows = await deps.db.fetch(sql, patterns)
            return [r["node_id"] for r in rows]
        except Exception:
            logger.warning("SQLStrategy step1 label match failed", exc_info=True)
            return []

    async def _fetch_citations(self, node_ids: list[str], deps: Any) -> list[dict[str, Any]]:
        """Fetch passage_citations for given node IDs, ordered by confidence."""
        sql = f"""
            SELECT passage_id, kg_node_id, confidence
            FROM {DB_SCHEMA}.passage_citations
            WHERE kg_node_id = ANY($1::text[])
            ORDER BY confidence DESC
            LIMIT 100
        """
        try:
            return await deps.db.fetch(sql, node_ids)
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
