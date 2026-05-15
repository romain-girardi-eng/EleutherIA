"""
SSEEmitter — streams agent loop events as Server-Sent Events.

Each tool call and agent reasoning step is emitted as a typed SSE event,
allowing the frontend to display the agent's exploration in real time.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)


class SSEEmitter:
    """Emits agent loop events to an asyncio.Queue for SSE streaming."""

    def __init__(self, queue: asyncio.Queue[dict[str, Any] | None]) -> None:
        self._queue = queue
        self._step = 0
        self._budget = 0
        self._calls_made = 0

    def set_budget(self, budget: int) -> None:
        self._budget = budget

    def set_calls_made(self, calls_made: int) -> None:
        self._calls_made = calls_made

    async def emit_status(self, message: str) -> None:
        """Emit a general status message (Phase 1 or Phase 3)."""
        self._step += 1
        await self._queue.put(
            {
                "type": "status",
                "message": message,
                "data": {"step": self._step},
            }
        )

    async def emit_thinking(self, thinking: str) -> None:
        """Emit agent reasoning/thinking text."""
        self._step += 1
        await self._queue.put(
            {
                "type": "agent_thinking",
                "data": {
                    "thinking": thinking,
                    "step": self._step,
                    "remaining": self._budget - self._calls_made,
                },
            }
        )

    async def emit_tool_start(
        self, tool: str, args: dict[str, Any], reason: str
    ) -> None:
        """Emit that a tool call is starting."""
        await self._queue.put(
            {
                "type": "tool_start",
                "data": {
                    "tool": tool,
                    "args": _sanitize_args(args),
                    "reason": reason,
                    "step": self._step,
                },
            }
        )

    async def emit_tool_result(
        self,
        tool: str,
        summary: str,
        *,
        duration_ms: int = 0,
        node_count: int = 0,
        passage_count: int = 0,
    ) -> None:
        """Emit a tool call result summary."""
        await self._queue.put(
            {
                "type": "tool_result",
                "data": {
                    "tool": tool,
                    "summary": summary,
                    "duration_ms": duration_ms,
                    "node_count": node_count,
                    "passage_count": passage_count,
                    "step": self._step,
                },
            }
        )

    async def emit_answer_chunk(self, chunk: str) -> None:
        """Emit a chunk of the final answer."""
        await self._queue.put(
            {
                "type": "answer_chunk",
                "data": chunk,
            }
        )

    async def emit_complete(self, data: dict[str, Any]) -> None:
        """Emit the final complete response."""
        await self._queue.put(
            {
                "type": "complete",
                "data": data,
            }
        )

    async def emit_error(self, message: str) -> None:
        """Emit an error event."""
        await self._queue.put(
            {
                "type": "error",
                "message": message,
            }
        )

    async def emit_agent_start(self, agent: str, query: str, trace_id: str) -> None:
        """Frontend-protocol: signal that an agent has started a query."""
        await self._queue.put(
            {
                "type": "agent_start",
                "agent": agent,
                "query": query,
                "trace_id": trace_id,
            }
        )

    async def emit_tool_call(
        self,
        agent: str,
        tool: str,
        args: dict[str, Any],
        call_id: str,
    ) -> None:
        """Frontend-protocol ``tool_call`` event (paired later with tool_result)."""
        await self._queue.put(
            {
                "type": "tool_call",
                "agent": agent,
                "tool": tool,
                "args": _sanitize_args(args),
                "id": call_id,
            }
        )

    async def emit_tool_call_result(
        self,
        tool_call_id: str,
        result_summary: str,
        *,
        nodes_touched: list[str] | None = None,
        passages_touched: list[str] | None = None,
        duration_ms: int | None = None,
    ) -> None:
        """Frontend-protocol ``tool_result`` (matches the ``tool_call`` id)."""
        payload: dict[str, Any] = {
            "type": "tool_result",
            "tool_call_id": tool_call_id,
            "result_summary": result_summary,
        }
        if nodes_touched:
            payload["nodes_touched"] = nodes_touched
        if passages_touched:
            payload["passages_touched"] = passages_touched
        if duration_ms is not None:
            payload["duration_ms"] = duration_ms
        await self._queue.put(payload)

    async def emit_citation_found(
        self,
        *,
        passage_id: str,
        excerpt: str,
        node_ids: list[str],
        confidence: float,
        cts_urn: str | None = None,
        work_label: str | None = None,
    ) -> None:
        """Frontend-protocol ``citation_found`` event."""
        payload: dict[str, Any] = {
            "type": "citation_found",
            "passage_id": passage_id,
            "excerpt": excerpt,
            "node_ids": node_ids,
            "confidence": confidence,
        }
        if cts_urn:
            payload["cts_urn"] = cts_urn
        if work_label:
            payload["work_label"] = work_label
        await self._queue.put(payload)

    async def emit_kg_node_activated(
        self,
        *,
        node_id: str,
        label: str,
        node_type: str,
        period: str | None = None,
    ) -> None:
        """Frontend-protocol ``kg_node_activated`` event."""
        payload: dict[str, Any] = {
            "type": "kg_node_activated",
            "node_id": node_id,
            "label": label,
            "node_type": node_type,
        }
        if period:
            payload["period"] = period
        await self._queue.put(payload)

    async def emit_citation_verified(
        self,
        *,
        passage_id: str,
        verified: bool,
        status: str | None = None,
        reason: str | None = None,
    ) -> None:
        """Frontend-protocol ``citation_verified`` event.

        ``status`` carries the four-way verdict (VERIFIED/WEAK/REJECTED/MISSING)
        from the adversarial v2 verifier; ``verified`` is the boolean projection
        kept for backwards compatibility with the original event shape.
        """
        payload: dict[str, Any] = {
            "type": "citation_verified",
            "passage_id": passage_id,
            "verified": verified,
        }
        if status:
            payload["status"] = status
        if reason:
            payload["reason"] = reason
        await self._queue.put(payload)

    async def emit_verification_warning(
        self,
        *,
        message: str,
        rejection_rate: float,
        aborted: bool,
    ) -> None:
        """Emitted when the v2 verifier flags a high rejection rate.

        Not part of the original SSE protocol — projects as an ``error`` event
        when ``aborted`` is True (downstream UI already handles it), and as a
        ``status`` event otherwise.
        """
        if aborted:
            await self._queue.put(
                {
                    "type": "error",
                    "agent": "citation-verifier",
                    "message": message,
                    "rejection_rate": rejection_rate,
                    "aborted": True,
                }
            )
        else:
            await self._queue.put(
                {
                    "type": "status",
                    "message": message,
                    "data": {
                        "agent": "citation-verifier",
                        "rejection_rate": rejection_rate,
                    },
                }
            )

    async def emit_final_answer(
        self,
        answer: str,
        citations: list[dict[str, Any]],
        trace_id: str,
    ) -> None:
        """Frontend-protocol ``final_answer`` event."""
        await self._queue.put(
            {
                "type": "final_answer",
                "answer": answer,
                "citations": citations,
                "trace_id": trace_id,
            }
        )

    async def emit_stage_complete(
        self,
        stage: str,
        duration_ms: int,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Emit a ``stage_complete`` event with per-stage latency (Wave 7).

        Stages: ``classify``, ``retrieve``, ``agent_loop``, ``synthesis``,
        ``verify``, ``polish``. The frontend AgentTrace pane stacks these
        into a latency bar so the user sees where time is spent.
        """
        payload: dict[str, Any] = {
            "type": "stage_complete",
            "stage": stage,
            "duration_ms": duration_ms,
        }
        if metadata:
            payload["metadata"] = metadata
        await self._queue.put(payload)

    async def close(self) -> None:
        """Signal end of stream."""
        await self._queue.put(None)


class NullEmitter(SSEEmitter):
    """No-op emitter for non-streaming use (e.g., POST /query)."""

    def __init__(self) -> None:
        # Use a dummy queue that we never read from
        super().__init__(asyncio.Queue())

    async def emit_status(self, message: str) -> None:
        pass

    async def emit_thinking(self, thinking: str) -> None:
        pass

    async def emit_tool_start(
        self, tool: str, args: dict[str, Any], reason: str
    ) -> None:
        pass

    async def emit_tool_result(self, tool: str, summary: str, **kwargs: Any) -> None:
        pass

    async def emit_answer_chunk(self, chunk: str) -> None:
        pass

    async def emit_complete(self, data: dict[str, Any]) -> None:
        pass

    async def emit_error(self, message: str) -> None:
        pass

    async def emit_agent_start(self, agent: str, query: str, trace_id: str) -> None:
        pass

    async def emit_tool_call(
        self, agent: str, tool: str, args: dict[str, Any], call_id: str
    ) -> None:
        pass

    async def emit_tool_call_result(
        self,
        tool_call_id: str,
        result_summary: str,
        *,
        nodes_touched: list[str] | None = None,
        passages_touched: list[str] | None = None,
        duration_ms: int | None = None,
    ) -> None:
        pass

    async def emit_citation_found(
        self,
        *,
        passage_id: str,
        excerpt: str,
        node_ids: list[str],
        confidence: float,
        cts_urn: str | None = None,
        work_label: str | None = None,
    ) -> None:
        pass

    async def emit_kg_node_activated(
        self,
        *,
        node_id: str,
        label: str,
        node_type: str,
        period: str | None = None,
    ) -> None:
        pass

    async def emit_citation_verified(
        self,
        *,
        passage_id: str,
        verified: bool,
        status: str | None = None,
        reason: str | None = None,
    ) -> None:
        pass

    async def emit_verification_warning(
        self,
        *,
        message: str,
        rejection_rate: float,
        aborted: bool,
    ) -> None:
        pass

    async def emit_final_answer(
        self, answer: str, citations: list[dict[str, Any]], trace_id: str
    ) -> None:
        pass

    async def emit_stage_complete(
        self,
        stage: str,
        duration_ms: int,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        pass

    async def close(self) -> None:
        pass


def _sanitize_args(args: dict[str, Any]) -> dict[str, Any]:
    """Sanitize tool args for SSE output (truncate long values)."""
    clean: dict[str, Any] = {}
    for key, value in args.items():
        if isinstance(value, str) and len(value) > 200:
            clean[key] = value[:200] + "..."
        elif isinstance(value, list) and len(value) > 10:
            clean[key] = value[:10]
        else:
            clean[key] = value
    return clean
