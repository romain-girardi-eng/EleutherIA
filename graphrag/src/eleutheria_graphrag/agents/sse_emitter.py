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
