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

import json
import logging
import time
import uuid
from asyncio import Lock
from datetime import UTC, datetime
from typing import Any

from eleutheria_database.services.db import DatabaseService

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _coerce_uuid(value: str) -> uuid.UUID | None:
    try:
        return uuid.UUID(value)
    except TypeError, ValueError, AttributeError:
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

    async def set_report(self, key: str, value: Any) -> None:
        """Set one of the four post-synthesis report fields."""
        if key not in self._reports:
            raise ValueError(f"unknown report key: {key}")
        async with self._lock:
            self._reports[key] = value

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
                    metadata
                )
                VALUES (
                    $1, $2, $3, $4::timestamptz, $5::timestamptz, $6,
                    $7::jsonb, $8::jsonb, $9::jsonb, $10::jsonb, $11::jsonb,
                    $12, $13::jsonb, $14, $15, $16::jsonb
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
                    metadata = EXCLUDED.metadata
                """,
                trace_uuid,
                user_uuid,
                self.query,
                self._started_at,
                self._completed_at,
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
                json.dumps(self.metadata, default=str),
            )
        except Exception:  # noqa: BLE001 — never fail the query because of audit
            logger.exception("TraceWriter: failed to persist trace %s", self.trace_id)
