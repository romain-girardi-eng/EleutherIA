"""
GraphRAG Service — thin wrapper preserving the original API contract.

Delegates all real work to the agentic pipeline (``ScholarlyAgent``)
while keeping the same ``query()`` / ``query_stream()`` signatures
so that routes and external callers need no changes.
"""

from __future__ import annotations

import logging
import warnings
from collections.abc import AsyncIterator
from typing import Any

from eleutheria_graphrag.agents.dependencies import Deps
from eleutheria_graphrag.agents.scholarly_agent import ScholarlyAgent
from eleutheria_graphrag.services.llm_service import LLMService, ModelProvider

logger = logging.getLogger(__name__)


class GraphRAGService:
    """
    GraphRAG service — API-compatible wrapper around the agentic pipeline.

    Usage::

        graphrag = GraphRAGService(db_service, qdrant_service)
        await graphrag.load_kg()
        result = await graphrag.query("What did Stoics believe about fate?")
        print(result["answer"])
    """

    def __init__(
        self,
        db_service: Any,
        qdrant_service: Any,
        llm_service: LLMService | None = None,
        analytics: Any | None = None,
        search_service: Any | None = None,
        reranker: Any | None = None,
        verifier: Any | None = None,
    ) -> None:
        self.db = db_service
        self.qdrant = qdrant_service
        self.llm = llm_service or LLMService(preferred_provider=ModelProvider.KIMI)
        self._analytics = analytics
        self._search = search_service
        self._reranker = reranker
        self._verifier = verifier

        # KG data (populated by load_kg)
        self.kg_data: dict[str, Any] | None = None
        self.node_lookup: dict[str, dict[str, Any]] = {}
        self.outgoing_edges: dict[str, list[dict[str, Any]]] = {}
        self.incoming_edges: dict[str, list[dict[str, Any]]] = {}
        self._kg_loaded = False

        # Agent (created after KG is loaded)
        self._agent: ScholarlyAgent | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def load_kg(self) -> None:
        """Load knowledge graph from database and build agent."""
        if self._kg_loaded:
            return

        logger.info("Loading knowledge graph from database...")

        nodes = await self.db.fetch("""
            SELECT
                node_id as id, label, type, description,
                period, school, role, metadata
            FROM free_will.kg_nodes
        """)

        edges = await self.db.fetch("""
            SELECT
                source_id as source, target_id as target,
                relation, description, weight
            FROM free_will.kg_edges
        """)

        self.kg_data = {"nodes": nodes, "edges": edges}

        # Build lookup indices
        self.node_lookup = {node["id"]: node for node in nodes}

        for edge in edges:
            source = edge["source"]
            target = edge["target"]

            if source not in self.outgoing_edges:
                self.outgoing_edges[source] = []
            self.outgoing_edges[source].append(edge)

            if target not in self.incoming_edges:
                self.incoming_edges[target] = []
            self.incoming_edges[target].append(edge)

        # Pre-compute PageRank if analytics is available
        pagerank_scores: dict[str, float] = {}
        if self._analytics:
            try:
                self._analytics.set_data(self.kg_data)
                pagerank_scores = self._analytics.calculate_centrality(
                    metric="pagerank",
                )
            except Exception:
                logger.warning("PageRank computation failed, continuing without")

        # Build weighted traversal service if analytics available
        traversal = None
        if pagerank_scores:
            from eleutheria_graphrag.services.weighted_traversal import (
                WeightedTraversal,
            )

            traversal = WeightedTraversal(
                node_lookup=self.node_lookup,
                outgoing_edges=self.outgoing_edges,
                incoming_edges=self.incoming_edges,
                pagerank_scores=pagerank_scores,
            )

        # Construct dependency container
        deps = Deps(
            db=self.db,
            qdrant=self.qdrant,
            llm=self.llm,
            analytics=self._analytics,
            search=self._search,
            traversal=traversal,
            reranker=self._reranker,
            verifier=self._verifier,
            kg_data=self.kg_data,
            node_lookup=self.node_lookup,
            outgoing_edges=self.outgoing_edges,
            incoming_edges=self.incoming_edges,
            pagerank_scores=pagerank_scores,
        )

        self._agent = ScholarlyAgent(deps)
        self._kg_loaded = True
        logger.info(f"Loaded {len(nodes)} nodes and {len(edges)} edges")

    def _ensure_agent(self) -> ScholarlyAgent:
        """Return the agent or raise a clear error."""
        if self._agent is None:
            raise RuntimeError("ScholarlyAgent not initialized — call load_kg() first")
        return self._agent

    # ------------------------------------------------------------------
    # Query (non-streaming)
    # ------------------------------------------------------------------

    async def query(
        self,
        question: str,
        semantic_k: int = 10,
        graph_depth: int = 2,
        max_context_nodes: int = 30,
        include_passages: bool = True,
    ) -> dict[str, Any]:
        """Execute agentic GraphRAG query pipeline.

        Args:
            question: User question
            semantic_k: Deprecated — ignored by agentic pipeline.
            graph_depth: Deprecated — ignored by agentic pipeline.
            max_context_nodes: Deprecated — ignored by agentic pipeline.
            include_passages: Deprecated — ignored by agentic pipeline.

        Returns:
            Dictionary with answer, citations, and metadata.
        """
        if not self._kg_loaded:
            await self.load_kg()

        # Warn if callers pass non-default legacy parameters
        if semantic_k != 10 or graph_depth != 2 or max_context_nodes != 30:
            warnings.warn(
                "Parameters semantic_k, graph_depth, and max_context_nodes "
                "are deprecated and ignored by the agentic pipeline.",
                DeprecationWarning,
                stacklevel=2,
            )

        agent = self._ensure_agent()
        return await agent.query_dict(question)

    # ------------------------------------------------------------------
    # Query (streaming)
    # ------------------------------------------------------------------

    async def query_stream(
        self,
        question: str,
        semantic_k: int = 10,
        graph_depth: int = 2,
        max_context_nodes: int = 30,
    ) -> AsyncIterator[str]:
        """Execute GraphRAG query with streaming response."""
        if not self._kg_loaded:
            await self.load_kg()

        agent = self._ensure_agent()
        async for chunk in agent.query_stream(question):
            yield chunk

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    async def close(self) -> None:
        """Close resources."""
        await self.llm.close()
