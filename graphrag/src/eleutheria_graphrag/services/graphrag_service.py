"""
GraphRAG Service — thin wrapper preserving the original API contract.

Delegates all real work to the agentic pipeline (``ScholarlyAgent``)
while keeping the same ``query()`` / ``query_stream()`` signatures
so that routes and external callers need no changes.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
import uuid
import warnings
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

from eleutheria_graphrag.agents.dependencies import Deps
from eleutheria_graphrag.agents.scholarly_agent import ScholarlyAgent
from eleutheria_graphrag.services.lemma_expansion import LemmaExpander
from eleutheria_graphrag.services.llm_reranker import LLMRerankerService
from eleutheria_graphrag.services.llm_service import LLMService, ModelProvider
from eleutheria_graphrag.services.retrieval_strategy import (
    SnapshotStrategy,
    SQLStrategy,
)
from eleutheria_graphrag.services.snapshot_retrieval import db_is_connected
from eleutheria_graphrag.services.tree_index import TreeIndexService
from eleutheria_graphrag.services.weighted_traversal import WeightedTraversal
from eleutheria_kg.services.snapshot import load_kg_snapshot

logger = logging.getLogger(__name__)


def _normalize_json_mapping(value: Any) -> dict[str, Any]:
    """Return a dict for JSON/JSONB fields regardless of driver behaviour."""
    if isinstance(value, dict):
        return value
    if not value:
        return {}
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _preferred_provider() -> ModelProvider:
    raw = (
        os.getenv("LLM_PREFERRED_PROVIDER", ModelProvider.OPENROUTER.value)
        .strip()
        .lower()
    )
    try:
        return ModelProvider(raw)
    except ValueError:
        logger.warning("Unknown LLM_PREFERRED_PROVIDER=%s, falling back to gemini", raw)
        return ModelProvider.GEMINI


@dataclass
class Turn:
    question: str
    answer: str
    citations: list[dict[str, Any]]
    reasoning_trace: list[Any]
    evidence_node_ids: list[str]


@dataclass
class ConversationThread:
    thread_id: str
    model: str
    retrieval_mode: str
    turns: list[Turn] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)


class ThreadManager:
    def __init__(self, ttl_seconds: int = 1800) -> None:
        self._threads: dict[str, ConversationThread] = {}
        self._ttl = ttl_seconds

    def create_thread(self, model: str, retrieval_mode: str) -> ConversationThread:
        self.cleanup_expired()
        thread = ConversationThread(
            thread_id=str(uuid.uuid4()),
            model=model,
            retrieval_mode=retrieval_mode,
        )
        self._threads[thread.thread_id] = thread
        return thread

    def get_thread(self, thread_id: str) -> ConversationThread | None:
        thread = self._threads.get(thread_id)
        if thread is None:
            return None
        if time.time() - thread.last_accessed > self._ttl:
            del self._threads[thread_id]
            return None
        return thread

    def touch(self, thread_id: str) -> None:
        thread = self._threads.get(thread_id)
        if thread:
            thread.last_accessed = time.time()

    def cleanup_expired(self) -> None:
        now = time.time()
        expired = [
            tid for tid, t in self._threads.items() if now - t.last_accessed > self._ttl
        ]
        for tid in expired:
            del self._threads[tid]


class ResponseCache:
    """Simple TTL cache for GraphRAG responses."""

    def __init__(self, ttl_seconds: int = 600, max_entries: int = 100) -> None:
        self._cache: dict[str, tuple[float, dict[str, Any]]] = {}
        self._ttl = ttl_seconds
        self._max = max_entries

    def _key(self, question: str, model: str, mode: str) -> str:
        raw = f"{question.strip().lower()}::{model}::{mode}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def get(self, question: str, model: str, mode: str) -> dict[str, Any] | None:
        key = self._key(question, model, mode)
        entry = self._cache.get(key)
        if entry is None:
            return None
        ts, result = entry
        if time.time() - ts > self._ttl:
            del self._cache[key]
            return None
        return result

    def put(self, question: str, model: str, mode: str, result: dict[str, Any]) -> None:
        if len(self._cache) >= self._max:
            oldest_key = min(self._cache, key=lambda k: self._cache[k][0])
            del self._cache[oldest_key]
        key = self._key(question, model, mode)
        self._cache[key] = (time.time(), result)


class GraphRAGService:
    """
    GraphRAG service — API-compatible wrapper around the agentic pipeline.

    Usage::

        graphrag = GraphRAGService(db_service)
        await graphrag.load_kg()
        result = await graphrag.query("What did Stoics believe about fate?")
        print(result["answer"])
    """

    def __init__(
        self,
        db_service: Any,
        llm_service: LLMService | None = None,
        analytics: Any | None = None,
        search_service: Any | None = None,
        reranker: Any | None = None,
        verifier: Any | None = None,
        kg_data: dict[str, Any] | None = None,
    ) -> None:
        self.db = db_service
        self.llm = llm_service or LLMService(preferred_provider=_preferred_provider())
        self._analytics = analytics
        self._search = search_service
        self._reranker = reranker
        self._verifier = verifier

        # Response cache
        self._response_cache = ResponseCache()

        # KG data (populated by load_kg)
        self.kg_data: dict[str, Any] | None = kg_data
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
        """Load knowledge graph from database or snapshot and build agent."""
        if self._kg_loaded:
            return

        if self.kg_data and self.kg_data.get("nodes") is not None:
            logger.info("Loading knowledge graph from provided data...")
            raw_kg = self.kg_data
        elif db_is_connected(self.db):
            logger.info("Loading knowledge graph from database...")
            raw_kg = await self._load_kg_from_db()
        else:
            logger.warning("Database unavailable; loading knowledge graph snapshot")
            raw_kg = load_kg_snapshot()

        nodes, edges = self._normalize_kg_data(raw_kg)

        self.kg_data = {"nodes": nodes, "edges": edges}

        # Build lookup indices
        self.node_lookup = {node["id"]: node for node in nodes}
        self.outgoing_edges = {}
        self.incoming_edges = {}

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

        traversal = WeightedTraversal(
            node_lookup=self.node_lookup,
            outgoing_edges=self.outgoing_edges,
            incoming_edges=self.incoming_edges,
            pagerank_scores=pagerank_scores,
        )
        tree_index = TreeIndexService(db=self.db) if db_is_connected(self.db) else None
        llm_reranker = LLMRerankerService(llm=self.llm)

        # Vectorless retrieval: SQL strategy with LLM lemma expansion when the
        # database is reachable; snapshot strategy as the offline fallback.
        lemma_expander = LemmaExpander(llm=self.llm)
        retrieval_strategy: Any
        if db_is_connected(self.db):
            retrieval_strategy = SQLStrategy(
                min_bundles=4, lemma_expander=lemma_expander
            )
        else:
            retrieval_strategy = SnapshotStrategy(min_passages=4)

        # Construct dependency container
        deps = Deps(
            db=self.db,
            llm=self.llm,
            analytics=self._analytics,
            search=self._search,
            traversal=traversal,
            reranker=self._reranker,
            verifier=self._verifier,
            llm_reranker=llm_reranker,
            tree_index=tree_index,
            retrieval_strategy=retrieval_strategy,
            kg_data=self.kg_data,
            node_lookup=self.node_lookup,
            outgoing_edges=self.outgoing_edges,
            incoming_edges=self.incoming_edges,
            pagerank_scores=pagerank_scores,
        )

        self._agent = ScholarlyAgent(deps)
        self._kg_loaded = True
        logger.info(f"Loaded {len(nodes)} nodes and {len(edges)} edges")

    async def _load_kg_from_db(self) -> dict[str, list[dict[str, Any]]]:
        nodes = await self.db.fetch("""
            SELECT
                node_id as id,
                label,
                type,
                description,
                period,
                COALESCE(metadata->>'school', metadata->>'school_affiliation') as school,
                COALESCE(metadata->>'role', metadata->>'scholarly_role') as role,
                metadata,
                metadata->>'date' as date,
                metadata->>'birth' as birth,
                metadata->>'death' as death,
                metadata->>'floruit' as floruit,
                metadata->>'approximate_dates' as approximate_dates,
                metadata->>'scholarly_role' as scholarly_role
            FROM free_will.kg_nodes
        """)

        edges = await self.db.fetch("""
            SELECT
                source_id as source,
                target_id as target,
                relation,
                metadata->>'description' as description,
                CASE
                    WHEN COALESCE(metadata->>'weight', '') ~ '^[0-9]+(\\.[0-9]+)?$'
                        THEN (metadata->>'weight')::double precision
                    ELSE 1.0
                END as weight,
                metadata
            FROM free_will.kg_edges
        """)
        return {"nodes": nodes, "edges": edges}

    def _normalize_kg_data(
        self,
        kg_data: dict[str, Any],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        nodes = [
            {
                **node,
                "id": str(node.get("id") or node.get("node_id") or ""),
                "metadata": _normalize_json_mapping(node.get("metadata")),
            }
            for node in kg_data.get("nodes", [])
            if node.get("id") or node.get("node_id")
        ]

        edges: list[dict[str, Any]] = []
        for edge in kg_data.get("edges", []):
            metadata = _normalize_json_mapping(edge.get("metadata"))
            weight = edge.get("weight", metadata.get("weight", 1.0))
            try:
                normalized_weight = float(weight)
            except (TypeError, ValueError):
                normalized_weight = 1.0
            source = str(edge.get("source") or edge.get("source_id") or "")
            target = str(edge.get("target") or edge.get("target_id") or "")
            if not source or not target:
                continue
            edges.append(
                {
                    **edge,
                    "source": source,
                    "target": target,
                    "relation": edge.get("relation") or "",
                    "description": edge.get("description") or metadata.get("description"),
                    "weight": normalized_weight,
                    "metadata": metadata,
                }
            )

        return nodes, edges

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
        selected_model: str = "gemini-3.1-pro",
        retrieval_mode: str = "auto",
    ) -> dict[str, Any]:
        """Execute agentic GraphRAG query pipeline.

        Args:
            question: User question
            semantic_k: Deprecated — ignored by agentic pipeline.
            graph_depth: Deprecated — ignored by agentic pipeline.
            max_context_nodes: Deprecated — ignored by agentic pipeline.
            include_passages: Deprecated — ignored by agentic pipeline.
            selected_model: Model key from model_registry (e.g. "claude-sonnet-4.6").
            retrieval_mode: "auto", "vector", or "sql".

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

        cached = self._response_cache.get(question, selected_model, retrieval_mode)
        if cached is not None:
            return {**cached, "cached": True}

        agent = self._ensure_agent()
        result = await agent.query_dict(
            question,
            selected_model=selected_model,
            retrieval_mode=retrieval_mode,
        )
        self._response_cache.put(question, selected_model, retrieval_mode, result)
        return result

    # ------------------------------------------------------------------
    # Query (streaming)
    # ------------------------------------------------------------------

    async def query_stream(
        self,
        question: str,
        semantic_k: int = 10,
        graph_depth: int = 2,
        max_context_nodes: int = 30,
        selected_model: str = "gemini-3.1-pro",
        retrieval_mode: str = "auto",
    ) -> AsyncIterator[str]:
        """Execute GraphRAG query with streaming response."""
        if not self._kg_loaded:
            await self.load_kg()

        agent = self._ensure_agent()
        async for chunk in agent.query_stream(
            question,
            selected_model=selected_model,
            retrieval_mode=retrieval_mode,
        ):
            yield chunk

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    async def close(self) -> None:
        """Close resources."""
        await self.llm.close()
