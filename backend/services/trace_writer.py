"""TraceWriter — persistent audit trail for deep-mode GraphRAG queries.

A single :class:`TraceWriter` instance buffers the agent tree, tool calls,
verifier / counter-evidence / methodology / polishing reports and timing
totals in memory, then flushes them to ``free_will.query_traces`` via the
shared :class:`DatabaseService`.

The writer is intentionally tolerant of missing data — partial traces are
better than no traces — and degrades to a no-op when the DB is unavailable
(snapshot mode, tests without a real Postgres). The orchestrator and the
opencode SSE proxy both share a single instance per query identified by
``trace_id``.

Threading note: every public method is a coroutine. Sub-agents that emit
events concurrently must hold the writer's lock when mutating the tree;
``record_*`` methods do so transparently.
"""

from __future__ import annotations

import contextvars
import json
import logging
import time
import uuid
from asyncio import Lock
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from eleutheria_database.services.db import DatabaseService
from eleutheria_graphrag.services.llm_pricing import (
    TokenUsage,
    estimate_cost_usd,
)

logger = logging.getLogger(__name__)

# Per-task active writer. Any code running inside an asyncio task that was
# started under an SSE handler reads this to find the right TraceWriter
# (LLMService dispatches token usage observations here). ContextVar isolates
# concurrent queries cleanly: each top-level task gets its own copy.
active_trace_writer: contextvars.ContextVar[TraceWriter | None] = (
    contextvars.ContextVar("active_trace_writer", default=None)
)


def _now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _now_dt() -> datetime:
    """UTC-aware datetime — what asyncpg needs for ``timestamptz`` columns."""
    return datetime.now(UTC)


def _iso_to_dt(iso: str | None) -> datetime | None:
    if not iso:
        return None
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError:
        return None


def _coerce_uuid(value: str) -> uuid.UUID | None:
    try:
        return uuid.UUID(value)
    except (TypeError, ValueError, AttributeError) as _exc:
        del _exc
        return None


class TraceWriter:
    """Captures and persists the full audit trail of a single query.

    Lifecycle::

        writer = TraceWriter(db, trace_id, query="...", user_id=user_id, mode="deep")
        await writer.start()
        await writer.record_agent_invocation(agent_id, parent_agent_id=None)
        await writer.record_tool_call(agent_id, tool="x", args={}, result_summary="...")
        await writer.record_subagent_complete(agent_id, success=True)
        await writer.set_report("methodology_report", {...})
        await writer.finalize(final_answer="...", citations=[...])

    Every mutation records a wall-clock timestamp; ``finalize`` writes a
    single row (UPSERT) carrying the full agent tree as JSONB.
    """

    def __init__(
        self,
        db: DatabaseService,
        trace_id: str,
        *,
        query: str,
        user_id: str | None = None,
        mode: str = "deep",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self._db = db
        self.trace_id = trace_id
        self.query = query
        self.user_id = user_id
        self.mode = mode
        self.metadata: dict[str, Any] = metadata or {}

        self._started_at = _now_iso()
        self._completed_at: str | None = None
        self._t0 = time.perf_counter()
        self._tool_call_count = 0
        self._lock = Lock()

        # The root of the agent tree. Sub-agents nest under their parents
        # by `parent_agent_id`. Tools are appended to the owning agent's
        # `tools_called` list.
        self._tree_index: dict[str, dict[str, Any]] = {}
        self._root_agents: list[dict[str, Any]] = []

        self._reports: dict[str, Any] = {
            "citation_verifier_report": None,
            "counter_evidence_report": None,
            "methodology_report": None,
            "polishing_report": None,
        }

        # Token / cost ledger. Maintained alongside the agent tree so the
        # frontend can show a live "$0.034 · 12,348 tok" badge as the deep
        # pipeline runs. ``by_agent`` and ``by_model`` are rolled up on every
        # call; ``provider_usage`` keeps a per-provider split for finance.
        self._total_tokens: int = 0
        self._total_cost_usd: float = 0.0
        self._usage_by_agent: dict[str, dict[str, float]] = {}
        self._usage_by_model: dict[str, dict[str, float]] = {}
        self._usage_by_provider: dict[str, dict[str, float]] = {}
        self._stage_metrics: list[dict[str, Any]] = []
        self._stage_usage_tokens = 0
        self._stage_usage_cost_usd = 0.0

    # ---------- public API ----------

    async def start(self) -> None:
        """Insert the initial empty row so partial views can be served."""
        await self._upsert(initial=True)

    async def record_agent_invocation(
        self,
        agent_id: str,
        *,
        parent_agent_id: str | None = None,
        subagent_index: int | None = None,
    ) -> None:
        """Register a new agent (orchestrator or sub-agent) starting up."""
        async with self._lock:
            node: dict[str, Any] = {
                "agent_id": agent_id,
                "parent_agent_id": parent_agent_id,
                "started_at": _now_iso(),
                "completed_at": None,
                "success": None,
                "tokens_used": None,
                "subagent_index": subagent_index,
                "tools_called": [],
                "subagents": [],
            }
            self._tree_index[agent_id] = node
            parent = self._tree_index.get(parent_agent_id) if parent_agent_id else None
            if parent is not None:
                parent["subagents"].append(node)
            else:
                self._root_agents.append(node)

    async def record_tool_call(
        self,
        agent_id: str,
        *,
        tool: str,
        args: dict[str, Any],
        result_summary: str,
        duration_ms: int | None = None,
    ) -> None:
        """Append a tool invocation to the owning agent's tool list."""
        async with self._lock:
            self._tool_call_count += 1
            entry: dict[str, Any] = {
                "tool": tool,
                "args": args,
                "result_summary": result_summary,
                "duration_ms": duration_ms,
                "at": _now_iso(),
            }
            node = self._tree_index.get(agent_id)
            if node is not None:
                node["tools_called"].append(entry)
            else:
                # Tool fired before the agent was registered — stash it on
                # a synthetic "orphan" branch rather than dropping silently.
                self._tree_index.setdefault(
                    "_orphan",
                    {
                        "agent_id": "_orphan",
                        "parent_agent_id": None,
                        "started_at": _now_iso(),
                        "completed_at": None,
                        "success": None,
                        "tools_called": [],
                        "subagents": [],
                    },
                )
                self._tree_index["_orphan"]["tools_called"].append(entry)

    async def record_subagent_complete(
        self,
        agent_id: str,
        *,
        success: bool,
        tokens_used: int | None = None,
    ) -> None:
        """Mark an agent as finished, success/failure, optional token count."""
        async with self._lock:
            node = self._tree_index.get(agent_id)
            if node is None:
                return
            node["completed_at"] = _now_iso()
            node["success"] = success
            node["tokens_used"] = tokens_used

    async def record_token_usage(
        self,
        agent_id: str | None,
        usage: TokenUsage,
    ) -> None:
        """Aggregate a single :class:`TokenUsage` observation.

        Updates running totals (overall + per-agent + per-model + per-provider)
        and bubbles ``tokens_used`` / ``cost_usd`` onto the owning agent's
        tree node so the AgentTrace view can render per-sub-agent rows
        without a second join.
        """
        async with self._lock:
            agent_key = agent_id or usage.agent_id or "_unknown"
            self._total_tokens += usage.total_tokens
            self._total_cost_usd = round(
                self._total_cost_usd + usage.estimated_cost_usd, 6
            )

            agent_row = self._usage_by_agent.setdefault(
                agent_key,
                {"tokens": 0.0, "cost_usd": 0.0, "calls": 0.0},
            )
            agent_row["tokens"] += usage.total_tokens
            agent_row["cost_usd"] = round(
                agent_row["cost_usd"] + usage.estimated_cost_usd, 6
            )
            agent_row["calls"] += 1

            model_row = self._usage_by_model.setdefault(
                usage.model or "unknown",
                {"tokens": 0.0, "cost_usd": 0.0, "calls": 0.0},
            )
            model_row["tokens"] += usage.total_tokens
            model_row["cost_usd"] = round(
                model_row["cost_usd"] + usage.estimated_cost_usd, 6
            )
            model_row["calls"] += 1

            provider_row = self._usage_by_provider.setdefault(
                usage.provider or "unknown",
                {
                    "prompt_tokens": 0.0,
                    "completion_tokens": 0.0,
                    "total_tokens": 0.0,
                    "cost_usd": 0.0,
                    "calls": 0.0,
                },
            )
            provider_row["prompt_tokens"] += usage.prompt_tokens
            provider_row["completion_tokens"] += usage.completion_tokens
            provider_row["total_tokens"] += usage.total_tokens
            provider_row["cost_usd"] = round(
                provider_row["cost_usd"] + usage.estimated_cost_usd, 6
            )
            provider_row["calls"] += 1

            node = self._tree_index.get(agent_key)
            if node is not None:
                node_tokens = node.get("tokens_used") or 0
                node["tokens_used"] = int(node_tokens) + usage.total_tokens
                node_cost = float(node.get("cost_usd") or 0.0)
                node["cost_usd"] = round(node_cost + usage.estimated_cost_usd, 6)
                node["model"] = usage.model
                node["provider"] = usage.provider

    def get_running_totals(self) -> dict[str, Any]:
        """Snapshot of the running ledger — safe to call without the lock."""
        return {
            "total_tokens": int(self._total_tokens),
            "total_cost_usd": round(self._total_cost_usd, 6),
            "by_agent": {k: dict(v) for k, v in self._usage_by_agent.items()},
            "by_model": {k: dict(v) for k, v in self._usage_by_model.items()},
            "by_provider": {k: dict(v) for k, v in self._usage_by_provider.items()},
        }

    @staticmethod
    def estimate_cost(
        *, provider: str, prompt_tokens: int, completion_tokens: int
    ) -> float:
        """Convenience proxy for the pricing helper."""
        return estimate_cost_usd(
            provider=provider,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )

    async def set_report(self, key: str, value: Any) -> None:
        """Set one of the four post-synthesis report fields."""
        if key not in self._reports:
            raise ValueError(f"unknown report key: {key}")
        async with self._lock:
            self._reports[key] = value

    async def record_stage_metric(
        self,
        stage: str,
        duration_ms: int | float,
        *,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        """Record the same stage boundary emitted to the SSE client.

        Token and cost attribution is the delta observed since the preceding
        boundary. This keeps stage accounting on the provider-reported usage
        ledger instead of estimating it independently.
        """
        if not stage or not isinstance(duration_ms, (int, float)):
            return
        async with self._lock:
            tokens = self._total_tokens - self._stage_usage_tokens
            cost_usd = round(
                self._total_cost_usd - self._stage_usage_cost_usd,
                6,
            )
            metric: dict[str, Any] = {
                "stage": stage,
                "ms": max(0, int(duration_ms)),
                "tokens": max(0, tokens),
                "cost_usd": max(0.0, cost_usd),
            }
            if metadata:
                metric["metadata"] = dict(metadata)
            self._stage_metrics.append(metric)
            self._stage_usage_tokens = self._total_tokens
            self._stage_usage_cost_usd = self._total_cost_usd

    async def record_pipeline_outputs(self, output: Mapping[str, Any]) -> None:
        """Map real pipeline outputs onto trace reports and provenance."""
        raw_metadata = output.get("metadata")
        pipeline_metadata = (
            dict(raw_metadata) if isinstance(raw_metadata, Mapping) else {}
        )
        report_sources = {
            "citation_verifier_report": (
                output.get("citation_verifier_report"),
                pipeline_metadata.get("citation_verifier_v2"),
            ),
            "counter_evidence_report": (
                output.get("counter_evidence_report"),
                pipeline_metadata.get("counter_evidence"),
                pipeline_metadata.get("counter_evidence_hunt"),
            ),
            "methodology_report": (
                output.get("methodology_report"),
                pipeline_metadata.get("methodology"),
            ),
            "polishing_report": (
                output.get("polishing_report"),
                pipeline_metadata.get("polishing"),
            ),
        }
        answer_metadata_keys = (
            "citation_verifier_v2",
            "grounding",
            "quality_badge",
            "text_verification",
            "grounding_policy",
            "publication_gate",
        )

        async with self._lock:
            for report_key, candidates in report_sources.items():
                value = next((item for item in candidates if item is not None), None)
                if value is not None:
                    self._reports[report_key] = value

            answer_metadata = {
                key: pipeline_metadata[key]
                for key in answer_metadata_keys
                if pipeline_metadata.get(key) is not None
            }
            if answer_metadata:
                existing = self.metadata.get("answer_metadata")
                self.metadata["answer_metadata"] = {
                    **(dict(existing) if isinstance(existing, Mapping) else {}),
                    **answer_metadata,
                }
            claim_ledger = output.get("claim_ledger")
            if isinstance(claim_ledger, list) and claim_ledger:
                self.metadata["claim_ledger"] = claim_ledger

    async def finalize(
        self,
        *,
        final_answer: str,
        citations: list[dict[str, Any]] | None = None,
        success: bool = True,
    ) -> None:
        """Write the terminal state of the trace to Postgres."""
        async with self._lock:
            self._completed_at = _now_iso()
            # If the root orchestrator was never explicitly completed, do it
            # now so the UI doesn't show a perpetually-running root node.
            for node in self._tree_index.values():
                if node.get("completed_at") is None:
                    node["completed_at"] = self._completed_at
                    node["success"] = (
                        node.get("success")
                        if node.get("success") is not None
                        else success
                    )

        total_latency_ms = int((time.perf_counter() - self._t0) * 1000)
        await self._upsert(
            final_answer=final_answer,
            citations=citations or [],
            total_latency_ms=total_latency_ms,
        )

        # Best-effort: derive topic_tags so the galerie filter chips work.
        # Never fail a query because the tagger choked.
        try:
            from backend.services.topic_tagger import TopicTagger

            await TopicTagger(self._db).tag_and_persist(self.trace_id)
        except Exception:  # noqa: BLE001
            logger.exception("topic tagging failed for %s — non-fatal", self.trace_id)

    # ---------- persistence ----------

    async def _upsert(
        self,
        *,
        initial: bool = False,
        final_answer: str | None = None,
        citations: list[dict[str, Any]] | None = None,
        total_latency_ms: int | None = None,
    ) -> None:
        if not self._db.is_connected():
            if initial:
                logger.debug(
                    "TraceWriter: DB not connected; skipping persistence for %s",
                    self.trace_id,
                )
            return

        trace_uuid = _coerce_uuid(self.trace_id)
        if trace_uuid is None:
            # opencode session_ids are not UUIDs ("ses_abc123"); derive a
            # deterministic v5 UUID so we always have a primary key but a
            # human can still trace it back.
            trace_uuid = uuid.uuid5(
                uuid.NAMESPACE_URL, f"eleutheria:trace:{self.trace_id}"
            )
            self.metadata.setdefault("source_trace_id", self.trace_id)

        user_uuid = _coerce_uuid(self.user_id) if self.user_id else None

        agent_tree = {
            "root_agents": self._root_agents,
        }

        totals = self.get_running_totals()
        token_breakdown = {
            "by_agent": totals["by_agent"],
            "by_model": totals["by_model"],
        }
        provider_usage = totals["by_provider"]
        persisted_metadata = dict(self.metadata)
        if self._stage_metrics:
            persisted_metadata["stage_metrics"] = [
                dict(metric) for metric in self._stage_metrics
            ]

        # Stamp the trace with the KG version it was produced against — but
        # only on finalize. The initial INSERT happens before the agent has
        # touched the KG, so the version we'd read could already be stale by
        # the time the synthesis runs; deferring to finalize keeps the
        # `cached_at_kg_version` honest for the reproducibility certificate.
        current_kg_version: int | None = None
        if not initial:
            try:
                current_kg_version = (
                    await self._db.fetchval(
                        "SELECT version FROM free_will.kg_version WHERE id = 1"
                    )
                ) or 0
            except Exception:  # noqa: BLE001
                logger.debug(
                    "TraceWriter: kg_version lookup failed; leaving column"
                    " untouched on UPSERT",
                    exc_info=True,
                )
                current_kg_version = None

        try:
            await self._db.execute(
                """
                INSERT INTO free_will.query_traces (
                    trace_id, user_id, query, started_at, completed_at, mode,
                    agent_tree,
                    citation_verifier_report,
                    counter_evidence_report,
                    methodology_report,
                    polishing_report,
                    final_answer_text,
                    final_answer_citations,
                    total_latency_ms,
                    total_tool_calls,
                    metadata,
                    total_tokens,
                    total_cost_usd,
                    token_breakdown,
                    provider_usage,
                    kg_version_at_creation,
                    is_public
                )
                VALUES (
                    $1, $2, $3, $4::timestamptz, $5::timestamptz, $6,
                    $7::jsonb, $8::jsonb, $9::jsonb, $10::jsonb, $11::jsonb,
                    $12, $13::jsonb, $14, $15, $16::jsonb,
                    $17, $18, $19::jsonb, $20::jsonb,
                    COALESCE($21::bigint, 0),
                    false
                )
                ON CONFLICT (trace_id) DO UPDATE SET
                    completed_at = COALESCE(EXCLUDED.completed_at, query_traces.completed_at),
                    agent_tree = EXCLUDED.agent_tree,
                    citation_verifier_report = EXCLUDED.citation_verifier_report,
                    counter_evidence_report = EXCLUDED.counter_evidence_report,
                    methodology_report = EXCLUDED.methodology_report,
                    polishing_report = EXCLUDED.polishing_report,
                    final_answer_text = COALESCE(EXCLUDED.final_answer_text, query_traces.final_answer_text),
                    final_answer_citations = COALESCE(EXCLUDED.final_answer_citations, query_traces.final_answer_citations),
                    total_latency_ms = COALESCE(EXCLUDED.total_latency_ms, query_traces.total_latency_ms),
                    total_tool_calls = EXCLUDED.total_tool_calls,
                    metadata = EXCLUDED.metadata,
                    total_tokens = EXCLUDED.total_tokens,
                    total_cost_usd = EXCLUDED.total_cost_usd,
                    token_breakdown = EXCLUDED.token_breakdown,
                    provider_usage = EXCLUDED.provider_usage,
                    kg_version_at_creation = CASE
                        WHEN $21::bigint IS NOT NULL THEN EXCLUDED.kg_version_at_creation
                        ELSE query_traces.kg_version_at_creation
                    END
                """,
                trace_uuid,
                user_uuid,
                self.query,
                _iso_to_dt(self._started_at),
                _iso_to_dt(self._completed_at),
                self.mode,
                json.dumps(agent_tree, default=str),
                json.dumps(self._reports["citation_verifier_report"], default=str)
                if self._reports["citation_verifier_report"] is not None
                else None,
                json.dumps(self._reports["counter_evidence_report"], default=str)
                if self._reports["counter_evidence_report"] is not None
                else None,
                json.dumps(self._reports["methodology_report"], default=str)
                if self._reports["methodology_report"] is not None
                else None,
                json.dumps(self._reports["polishing_report"], default=str)
                if self._reports["polishing_report"] is not None
                else None,
                final_answer,
                json.dumps(citations or [], default=str)
                if citations is not None
                else None,
                total_latency_ms,
                self._tool_call_count,
                json.dumps(persisted_metadata, default=str),
                int(totals["total_tokens"]),
                float(totals["total_cost_usd"]),
                json.dumps(token_breakdown, default=str),
                json.dumps(provider_usage, default=str),
                current_kg_version,
            )
        except Exception:  # noqa: BLE001 — never fail the query because of audit
            logger.exception("TraceWriter: failed to persist trace %s", self.trace_id)
