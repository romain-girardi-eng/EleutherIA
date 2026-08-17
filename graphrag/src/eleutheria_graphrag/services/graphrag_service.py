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
from eleutheria_graphrag.models.counter_evidence import (
    ClaimUnit,
    CounterEvidenceReport,
    SynthesizedDraft,
)
from eleutheria_graphrag.models.methodology import MethodologyFlag
from eleutheria_graphrag.services.bibliography_builder import (
    BibliographyBuilder,
    BibliographyToolset,
    render_bibliography_markdown,
)
from eleutheria_graphrag.services.citation_verifier_v2 import (
    CitationVerifierV2,
    build_db_passage_fetcher,
)
from eleutheria_graphrag.services.counter_evidence_hunter import (
    CounterEvidenceHunter,
    MCPToolset,
    format_report_for_synthesizer,
)
from eleutheria_graphrag.services.lemma_expansion import LemmaExpander
from eleutheria_graphrag.services.llm_reranker import LLMRerankerService
from eleutheria_graphrag.services.llm_service import LLMService, ModelProvider
from eleutheria_graphrag.services.methodology_agent import (
    MethodologyAgent,
    format_blockers_for_synthesizer,
    format_non_blockers_as_editorial_markers,
)
from eleutheria_graphrag.services.polishing_agent import PolishingAgent
from eleutheria_graphrag.services.retrieval_strategy import (
    SnapshotStrategy,
    SQLStrategy,
)
from eleutheria_graphrag.services.snapshot_retrieval import db_is_connected
from eleutheria_graphrag.services.tree_index import TreeIndexService
from eleutheria_graphrag.services.weighted_traversal import WeightedTraversal
from eleutheria_kg.services.snapshot import load_kg_snapshot, materialize_inverse_edges

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


def _env_flag(name: str, *, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _preferred_provider() -> ModelProvider:
    raw = os.getenv("LLM_PREFERRED_PROVIDER", ModelProvider.CODEX.value).strip().lower()
    try:
        return ModelProvider(raw)
    except ValueError:
        logger.warning("Unknown LLM_PREFERRED_PROVIDER=%s, falling back to codex", raw)
        return ModelProvider.CODEX


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

    def _key(self, question: str, model: str, mode: str, *, deep: bool = False) -> str:
        # ``deep`` (hunt_counter_evidence / mode='deep') changes the answer
        # materially — deep and fast responses must never share a cache slot.
        raw = f"{question.strip().lower()}::{model}::{mode}::deep={int(deep)}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def get(
        self, question: str, model: str, mode: str, *, deep: bool = False
    ) -> dict[str, Any] | None:
        key = self._key(question, model, mode, deep=deep)
        entry = self._cache.get(key)
        if entry is None:
            return None
        ts, result = entry
        if time.time() - ts > self._ttl:
            del self._cache[key]
            return None
        return result

    def put(
        self,
        question: str,
        model: str,
        mode: str,
        result: dict[str, Any],
        *,
        deep: bool = False,
    ) -> None:
        if len(self._cache) >= self._max:
            oldest_key = min(self._cache, key=lambda k: self._cache[k][0])
            del self._cache[oldest_key]
        key = self._key(question, model, mode, deep=deep)
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

        # Cross-encoder reranker: only constructed when explicitly enabled
        # (model weights are not vendored — first use downloads/loads them
        # lazily inside RerankerService). Default off to keep prod startup
        # and per-query latency unchanged.
        if self._reranker is None and _env_flag("ELEUTHERIA_RERANKER", default=False):
            try:
                from eleutheria_graphrag.services.reranker import RerankerService

                self._reranker = RerankerService()
                logger.info("Cross-encoder reranker enabled (ELEUTHERIA_RERANKER)")
            except Exception:
                logger.warning(
                    "ELEUTHERIA_RERANKER set but RerankerService unavailable",
                    exc_info=True,
                )

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

        # Adversarial post-synthesis citation auditor (v2). Default ON: the
        # per-query cost is capped by ELEUTHERIA_VERIFIER_V2_MAX_CLAIMS
        # (default 8) sampled claims, each a single small low-temperature LLM
        # call, all dispatched within the verifier's concurrency cap of 10 —
        # one parallel wave per query. Set ELEUTHERIA_VERIFIER_V2=false to
        # disable.
        verifier_v2: CitationVerifierV2 | None = None
        if _env_flag("ELEUTHERIA_VERIFIER_V2", default=True):
            verifier_v2 = CitationVerifierV2(
                llm=self.llm,
                passage_fetcher=build_db_passage_fetcher(
                    self.db,
                    node_lookup=self.node_lookup,
                ),
            )

        # Construct dependency container
        deps = Deps(
            db=self.db,
            llm=self.llm,
            analytics=self._analytics,
            search=self._search,
            traversal=traversal,
            reranker=self._reranker,
            verifier=self._verifier,
            verifier_v2=verifier_v2,
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
            except (TypeError, ValueError) as _exc:
                del _exc
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
                    "description": edge.get("description")
                    or metadata.get("description"),
                    "weight": normalized_weight,
                    "metadata": metadata,
                }
            )

        return nodes, materialize_inverse_edges(edges)

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
        hunt_counter_evidence: bool = False,
    ) -> dict[str, Any]:
        """Execute agentic GraphRAG query pipeline.

        Args:
            question: User question
            semantic_k: Deprecated — ignored by agentic pipeline.
            graph_depth: Deprecated — ignored by agentic pipeline.
            max_context_nodes: Deprecated — ignored by agentic pipeline.
            include_passages: Deprecated — ignored by agentic pipeline.
            selected_model: Model key from model_registry (e.g. "claude-sonnet-5").
            retrieval_mode: "auto", "sql", or legacy "vector" alias.

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

        cached = self._response_cache.get(
            question,
            selected_model,
            retrieval_mode,
            deep=hunt_counter_evidence,
        )
        if cached is not None:
            return {**cached, "cached": True}

        agent = self._ensure_agent()
        result = await agent.query_dict(
            question,
            selected_model=selected_model,
            retrieval_mode=retrieval_mode,
            hunt_counter_evidence=hunt_counter_evidence,
        )

        # Two-pass adversarial loop (mode=deep / thesis-grade queries).
        # Off by default to keep fast queries fast.
        if hunt_counter_evidence:
            try:
                report = await self._run_counter_evidence_hunt(result, question)
                if report.total_testimonia > 0:
                    revised = await self._resynthesize_with_counter_evidence(
                        agent=agent,
                        question=question,
                        v1_result=result,
                        report=report,
                        selected_model=selected_model,
                        retrieval_mode=retrieval_mode,
                    )
                    result = revised
                result.setdefault("metadata", {})["counter_evidence"] = (
                    report.model_dump()
                )
            except Exception as exc:
                logger.warning("Counter-evidence hunt failed: %s", exc, exc_info=True)
                result.setdefault("metadata", {})["counter_evidence_error"] = str(exc)

            # Methodology + Polishing — thesis-grade pass.
            # Runs only in deep mode (gated on hunt_counter_evidence).
            try:
                result = await self._run_methodology_and_polishing(
                    agent=agent,
                    question=question,
                    result=result,
                    selected_model=selected_model,
                    retrieval_mode=retrieval_mode,
                )
            except Exception as exc:
                logger.warning(
                    "Methodology + Polishing pass failed: %s", exc, exc_info=True
                )
                result.setdefault("metadata", {})["methodology_polishing_error"] = str(
                    exc
                )

        self._response_cache.put(
            question,
            selected_model,
            retrieval_mode,
            result,
            deep=hunt_counter_evidence,
        )
        return result

    # ------------------------------------------------------------------
    # Counter-evidence two-pass loop
    # ------------------------------------------------------------------

    def _build_counter_evidence_hunter(
        self,
        on_finding: Any | None = None,
    ) -> CounterEvidenceHunter | None:
        """Construct a CounterEvidenceHunter wired to the agent's tools."""
        agent = self._agent
        if agent is None:
            return None
        tools_by_name = getattr(agent, "_tools_by_name", None) or {}
        search_tool = tools_by_name.get("search_passages")
        subgraph_tool = tools_by_name.get("explore_subgraph")
        if search_tool is None or subgraph_tool is None:
            return None
        toolset = MCPToolset(
            search_passages=search_tool,
            explore_subgraph=subgraph_tool,
            get_neighbors=tools_by_name.get("get_neighbors"),
            get_node_detail=tools_by_name.get("get_node_detail"),
            query_scholarly_consensus=tools_by_name.get("query_scholarly_consensus"),
        )
        return CounterEvidenceHunter(
            llm=self.llm,
            tools=toolset,
            on_finding=on_finding,
        )

    @staticmethod
    def _extract_claims_from_result(
        result: dict[str, Any],
    ) -> list[ClaimUnit]:
        """Build ClaimUnits from the synthesizer's claim_ledger (or fallback)."""
        ledger = result.get("claim_ledger") or []
        claims: list[ClaimUnit] = []
        for idx, entry in enumerate(ledger):
            if isinstance(entry, dict):
                claim_text = entry.get("claim", "")
                evidence_ids = list(entry.get("evidence_ids") or [])
            else:
                claim_text = getattr(entry, "claim", "")
                evidence_ids = list(getattr(entry, "evidence_ids", []) or [])
            if not claim_text:
                continue
            claims.append(
                ClaimUnit(
                    claim_id=f"c{idx + 1}",
                    claim_text=claim_text,
                    seed_node_ids=evidence_ids[:5],
                    keywords=[],
                )
            )
        # Fallback: synthesize one coarse claim from the answer if no ledger.
        if not claims:
            answer = (result.get("answer") or "").strip()
            if answer:
                claims.append(
                    ClaimUnit(
                        claim_id="c1",
                        claim_text=answer[:400],
                        seed_node_ids=list(result.get("seed_nodes") or [])[:5],
                    )
                )
        return claims

    async def _run_counter_evidence_hunt(
        self,
        v1_result: dict[str, Any],
        question: str,
    ) -> CounterEvidenceReport:
        hunter = self._build_counter_evidence_hunter()
        if hunter is None:
            return CounterEvidenceReport(
                per_claim_findings=[],
                aggregate_summary="Hunter unavailable: agent tools not initialized.",
            )
        claims = self._extract_claims_from_result(v1_result)
        draft = SynthesizedDraft(
            answer=v1_result.get("answer", ""),
            claims=claims,
        )
        return await hunter.hunt(draft)

    async def _resynthesize_with_counter_evidence(
        self,
        *,
        agent: ScholarlyAgent,
        question: str,
        v1_result: dict[str, Any],
        report: CounterEvidenceReport,
        selected_model: str,
        retrieval_mode: str,
    ) -> dict[str, Any]:
        """Feed the counter-evidence report back to the synthesizer for v2."""
        counter_block = format_report_for_synthesizer(report)
        v2_query = (
            f"{question}\n\n"
            f"FIRST DRAFT (engage with the counter-evidence below):\n"
            f"{(v1_result.get('answer') or '')[:4000]}\n\n"
            f"{counter_block}"
        )
        # If the agent exposes an explicit re-synthesis hook, use it. Otherwise
        # fall back to a fresh query — the prompt itself carries the brief.
        resynth = getattr(type(agent), "resynthesize", None)
        if resynth is not None and callable(resynth):
            return await agent.resynthesize(  # type: ignore[no-any-return]
                question=question,
                v1_result=v1_result,
                counter_evidence=counter_block,
                selected_model=selected_model,
                retrieval_mode=retrieval_mode,
            )
        return await agent.query_dict(
            v2_query,
            selected_model=selected_model,
            retrieval_mode=retrieval_mode,
        )

    # ------------------------------------------------------------------
    # Methodology + Polishing (deep-mode thesis-grade pass)
    # ------------------------------------------------------------------

    async def _run_methodology_and_polishing(
        self,
        *,
        agent: ScholarlyAgent,
        question: str,
        result: dict[str, Any],
        selected_model: str,
        retrieval_mode: str,
    ) -> dict[str, Any]:
        """Audit + polish a citation-verified draft.

        Methodology agent runs first. Any ``blocker`` flags drive a synthesizer
        v3 re-pass (loop capped inside ``MethodologyAgent``). Non-blocker
        flags are forwarded inline to the polishing agent as
        ``[ED: …]`` markers. The polished Markdown lands in
        ``result["polished_markdown"]`` and the methodology report in
        ``result["metadata"]["methodology"]``.
        """
        methodology = MethodologyAgent(self.llm, db=self.db)
        polisher = PolishingAgent(self.llm)

        async def _resynth(
            current_draft: dict[str, Any],
            blockers: list[MethodologyFlag],
        ) -> dict[str, Any]:
            block = format_blockers_for_synthesizer(blockers)
            current_answer = (current_draft.get("answer") or "")[:6000]
            v3_query = (
                f"{question}\n\n"
                f"PREVIOUS DRAFT (revise to resolve the methodology blockers below):\n"
                f"{current_answer}\n\n"
                f"{block}"
            )
            return await agent.query_dict(
                v3_query,
                selected_model=selected_model,
                retrieval_mode=retrieval_mode,
            )

        revised_draft, report = await methodology.run_with_resynth_loop(
            initial_draft=result,
            resynthesize=_resynth,
        )
        # Merge revised draft over result (preserve metadata + counter-evidence)
        merged: dict[str, Any] = {**result, **revised_draft}
        merged.setdefault("metadata", {})["methodology"] = report.model_dump()

        # Bibliography pass — runs AFTER Synthesizer v2 (already done) and
        # BEFORE Polishing. Walks the KG from the citation-verified draft's
        # cited nodes and emits a 3-tier annotated bibliography.
        try:
            bibliography = await self._build_bibliography(merged, question)
        except Exception:
            logger.warning(
                "BibliographyBuilder failed — continuing without",
                exc_info=True,
            )
            bibliography = None
        if bibliography is not None:
            merged["bibliography"] = bibliography.model_dump()

        # Carry non-blocker flags into polishing as inline editorial markers
        non_blockers = report.non_blockers
        draft_md = str(merged.get("answer") or "")
        if non_blockers:
            draft_md = draft_md + format_non_blockers_as_editorial_markers(non_blockers)
        # Append the bibliography to the draft before polishing so the
        # polisher can fold it into the final Markdown.
        if bibliography is not None and bibliography.total_entries > 0:
            draft_md = draft_md + render_bibliography_markdown(bibliography)

        polished = await polisher.polish(draft_md, carry_over_flags=non_blockers)
        merged["polished_markdown"] = polished.markdown
        merged["metadata"]["polishing"] = polished.model_dump(exclude={"markdown"})
        return merged

    async def _build_bibliography(self, draft: dict[str, Any], question: str) -> Any:
        """Run the BibliographyBuilder on a citation-verified draft."""
        agent = self._agent
        if agent is None:
            return None
        tools_by_name = getattr(agent, "_tools_by_name", None) or {}
        get_node_detail = tools_by_name.get("get_node_detail")
        get_neighbors = tools_by_name.get("get_neighbors")
        if get_node_detail is None or get_neighbors is None:
            return None
        toolset = BibliographyToolset(
            get_node_detail=get_node_detail,
            get_neighbors=get_neighbors,
            explore_subgraph=tools_by_name.get("explore_subgraph"),
        )
        builder = BibliographyBuilder(llm=self.llm, tools=toolset)
        claims = self._extract_claims_from_result(draft)
        synthesized = SynthesizedDraft(
            answer=draft.get("answer", ""),
            claims=claims,
        )
        return await builder.build(synthesized)

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
        hunt_counter_evidence: bool = False,
    ) -> AsyncIterator[str]:
        """Execute GraphRAG query with streaming response.

        ``hunt_counter_evidence`` (mode='deep' upstream) runs the
        CounterEvidenceHunter inside the react pipeline after evidence
        collection and before the claim ledger is drafted.
        """
        if not self._kg_loaded:
            await self.load_kg()

        agent = self._ensure_agent()
        async for chunk in agent.query_stream(
            question,
            selected_model=selected_model,
            retrieval_mode=retrieval_mode,
            hunt_counter_evidence=hunt_counter_evidence,
        ):
            yield chunk

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    async def close(self) -> None:
        """Close resources."""
        await self.llm.close()
