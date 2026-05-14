"""Dependency container for the MCP server.

Builds the same ``Deps`` object the in-process ReAct agent uses, so the
tool wrappers can stay thin. The container is a singleton — one
asyncpg pool, one in-memory KG snapshot — shared across every MCP
client connection.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

from eleutheria_graphrag.agents.dependencies import Deps

logger = logging.getLogger(__name__)


def _build_kg_indices(
    kg_data: dict[str, Any],
) -> tuple[
    dict[str, dict[str, Any]],
    dict[str, list[dict[str, Any]]],
    dict[str, list[dict[str, Any]]],
]:
    """Build node lookup + outgoing/incoming edge indices."""
    node_lookup: dict[str, dict[str, Any]] = {}
    for node in kg_data.get("nodes", []) or []:
        nid = node.get("id") or node.get("node_id")
        if not nid:
            continue
        node_lookup[nid] = dict(node)

    outgoing: dict[str, list[dict[str, Any]]] = {}
    incoming: dict[str, list[dict[str, Any]]] = {}
    for edge in kg_data.get("edges", []) or []:
        src = edge.get("source") or edge.get("source_id")
        tgt = edge.get("target") or edge.get("target_id")
        if not src or not tgt:
            continue
        normalized = {
            "source": src,
            "target": tgt,
            "relation": edge.get("relation", ""),
            "weight": edge.get("weight", 1.0),
            "metadata": edge.get("metadata", {}),
        }
        outgoing.setdefault(src, []).append(normalized)
        incoming.setdefault(tgt, []).append(normalized)

    return node_lookup, outgoing, incoming


class DepsContainer:
    """Singleton holder for MCP server dependencies."""

    def __init__(self) -> None:
        self._deps: Deps | None = None
        self._lock = asyncio.Lock()

    async def get(self) -> Deps:
        if self._deps is not None:
            return self._deps
        async with self._lock:
            if self._deps is not None:
                return self._deps
            self._deps = await self._build()
            return self._deps

    async def _build(self) -> Deps:
        """Load KG snapshot + connect to Postgres if available."""
        # Imports are local so unit tests can stub the container without
        # pulling the full eleutheria stack.
        from eleutheria_database.services.db import DatabaseService
        from eleutheria_kg.services.analytics import KGAnalytics
        from eleutheria_kg.services.snapshot import (
            load_kg_snapshot,
            snapshot_available,
        )

        db = DatabaseService()
        try:
            await db.connect()
            logger.info("MCP server: Postgres connection established")
        except Exception:
            logger.warning(
                "MCP server: Postgres unavailable, falling back to snapshot",
                exc_info=True,
            )

        kg_data: dict[str, Any] = {}
        if db.is_connected():
            try:
                nodes = await db.fetch(
                    """
                    SELECT
                        node_id as id,
                        label,
                        type,
                        description,
                        period,
                        COALESCE(metadata->>'school', metadata->>'school_affiliation') as school,
                        metadata
                    FROM free_will.kg_nodes
                    """
                )
                edges = await db.fetch(
                    """
                    SELECT
                        source_id as source,
                        target_id as target,
                        relation,
                        metadata
                    FROM free_will.kg_edges
                    """
                )
                kg_data = {"nodes": nodes, "edges": edges}
            except Exception:
                logger.exception("MCP server: KG load from Postgres failed")

        if not kg_data and snapshot_available():
            kg_data = load_kg_snapshot()

        node_lookup, outgoing, incoming = _build_kg_indices(kg_data)

        analytics: KGAnalytics | None = None
        pagerank_scores: dict[str, float] = {}
        try:
            analytics = KGAnalytics()
            analytics.set_data(kg_data)
            pagerank_scores = analytics.compute_pagerank() or {}
        except Exception:
            logger.warning("MCP server: PageRank skipped", exc_info=True)

        search = None
        if db.is_connected():
            try:
                from eleutheria_database.services.hybrid_search import (
                    HybridSearchService,
                )

                search = HybridSearchService(db)
            except Exception:
                logger.warning("MCP server: HybridSearchService unavailable", exc_info=True)

        tree_index = None
        try:
            from eleutheria_graphrag.services.tree_index import TreeIndexService

            tree_index = TreeIndexService(db) if db.is_connected() else None
        except Exception:
            logger.debug("MCP server: TreeIndexService unavailable", exc_info=True)

        llm = _build_minimal_llm()

        return Deps(
            db=db,
            llm=llm,
            analytics=analytics,
            search=search,
            tree_index=tree_index,
            kg_data=kg_data,
            node_lookup=node_lookup,
            outgoing_edges=outgoing,
            incoming_edges=incoming,
            pagerank_scores=pagerank_scores,
        )

    async def shutdown(self) -> None:
        if self._deps is None:
            return
        try:
            await self._deps.db.close()
        except Exception:
            logger.debug("MCP server: db close failed", exc_info=True)
        self._deps = None


def _build_minimal_llm() -> Any:
    """Build an LLM service. The wrapped tools don't call the LLM directly,
    but ``Deps`` requires a non-None llm. We construct one with whatever
    keys exist in the environment and let it stay idle.
    """
    try:
        from eleutheria_graphrag.services.llm_service import LLMService

        return LLMService()
    except Exception:
        logger.warning("MCP server: LLMService init failed (idle stub used)", exc_info=True)

        class _IdleLLM:
            async def generate(self, *_: Any, **__: Any) -> str:
                raise RuntimeError("LLM not configured in MCP server context")

        return _IdleLLM()


_container = DepsContainer()


async def get_deps() -> Deps:
    return await _container.get()


async def shutdown_deps() -> None:
    await _container.shutdown()


def override_container(container: DepsContainer) -> None:
    """Test hook to swap the singleton."""
    global _container
    _container = container


def reset_container() -> None:
    """Test hook to reset to a fresh container."""
    global _container
    _container = DepsContainer()


# Optional: log the KG snapshot dir at startup so misconfig is visible.
logger.debug(
    "MCP server deps init — KG_SNAPSHOT_DIR=%s",
    os.getenv("ELEUTHERIA_KG_SNAPSHOT_DIR", "data/kg"),
)
