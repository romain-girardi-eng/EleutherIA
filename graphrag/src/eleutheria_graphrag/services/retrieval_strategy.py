"""Retrieval strategies for the DiscoverCorpus FSM node."""

from __future__ import annotations

import logging
from typing import Any, Protocol, Callable, Awaitable

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


class SQLStrategy:
    """SQL-only retrieval: passage_citations + HybridSearch + canonical works."""

    async def discover_seeds(
        self,
        queries: list[str],
        deps: Any,
        node_limit: int = 100,
    ) -> tuple[list[str], list[str]]:
        # Implemented in Task 4
        raise NotImplementedError("SQLStrategy — see Task 4")
