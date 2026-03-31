"""
ReAct agent loop for scholarly graph retrieval.

Replaces the fixed FSM middle section (ExpandQuery → EvidenceSufficiency)
with a free-form tool-calling loop where the LLM reasons about what to
retrieve and when to stop.

Inspired by: IRCoT (ACL 2023), ToG 2.0 (ICLR 2024), DoG (AAAI 2025),
CRAG (ICLR 2024), HippoRAG (NeurIPS 2024).
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from eleutheria_graphrag.agents.dependencies import Deps
from eleutheria_graphrag.agents.evidence_collector import EvidenceCollector
from eleutheria_graphrag.agents.graph_helpers import parse_json, resolve_model_api_id
from eleutheria_graphrag.agents.prompts import (
    BUDGET_WARNING,
    FORMAT_RETRY,
    format_system_prompt,
    format_user_prompt,
)
from eleutheria_graphrag.agents.sse_emitter import SSEEmitter
from eleutheria_graphrag.agents.state import QueryComplexity, RAGState
from eleutheria_graphrag.agents.tools import ToolRegistry

logger = logging.getLogger(__name__)

# Budget per complexity tier (optimized for speed — fewer but smarter calls)
_BUDGETS: dict[QueryComplexity, int] = {
    QueryComplexity.SIMPLE: 4,
    QueryComplexity.MEDIUM: 7,
    QueryComplexity.COMPLEX: 10,
}

# Max parse failures before aborting
_MAX_PARSE_FAILURES = 3


class AgentAction:
    """Parsed action from LLM output."""

    __slots__ = ("type", "tool", "args", "reason", "summary")

    def __init__(
        self,
        action_type: str,
        tool: str = "",
        args: dict[str, Any] | None = None,
        reason: str = "",
        summary: str = "",
    ) -> None:
        self.type = action_type  # "tool_call" or "synthesize"
        self.tool = tool
        self.args = args or {}
        self.reason = reason
        self.summary = summary


class AgentLoop:
    """ReAct loop: LLM reasons → calls tools → accumulates evidence.

    The loop runs until either:
    - The agent says SYNTHESIZE (sufficient evidence gathered)
    - The budget is exhausted (forced synthesis)
    - A fatal error occurs
    """

    def __init__(
        self,
        deps: Deps,
        state: RAGState,
        tools: ToolRegistry,
        emitter: SSEEmitter,
    ) -> None:
        self.deps = deps
        self.state = state
        self.tools = tools
        self.emitter = emitter
        self.evidence = EvidenceCollector()
        self.messages: list[dict[str, str]] = []
        self.budget = _BUDGETS.get(state.complexity, 15)
        self.calls_made = 0
        self._parse_failures = 0

    async def run(self) -> None:
        """Execute the ReAct loop."""
        # Initialize conversation
        self.messages = [
            _system_msg(format_system_prompt(
                budget=self.budget,
                remaining=self.budget,
                tool_descriptions=self.tools.tool_descriptions(),
            )),
            _user_msg(format_user_prompt(
                question=self.state.question,
                context=self._build_query_context(),
            )),
        ]

        self.emitter.set_budget(self.budget)

        while self.calls_made < self.budget:
            remaining = self.budget - self.calls_made
            self.emitter.set_calls_made(self.calls_made)

            # Budget warning at N-2
            if remaining == 2:
                self.messages.append(_system_msg(
                    BUDGET_WARNING.format(remaining=remaining)
                ))

            # Call LLM
            t0 = time.monotonic()
            try:
                raw = await self.deps.llm.generate(
                    prompt=_format_conversation(self.messages),
                    temperature=0.1,
                    max_tokens=1024,
                    model_override=resolve_model_api_id(self.state),
                )
            except Exception as e:
                logger.error("LLM call failed in agent loop: %s", e, exc_info=True)
                await self.emitter.emit_error(f"LLM error: {e}")
                break
            llm_ms = int((time.monotonic() - t0) * 1000)

            # Parse action
            action = _parse_action(raw, self.tools)

            if action is None:
                self._parse_failures += 1
                logger.warning(
                    "Parse failure #%d: %s",
                    self._parse_failures,
                    raw[:200],
                )
                if self._parse_failures >= _MAX_PARSE_FAILURES:
                    logger.error("Too many parse failures, aborting agent loop")
                    await self.emitter.emit_thinking(
                        "Unable to parse tool calls. Proceeding to synthesis."
                    )
                    break
                self.messages.append(_assistant_msg(raw))
                self.messages.append(_system_msg(FORMAT_RETRY))
                continue

            # Reset parse failure counter on success
            self._parse_failures = 0

            if action.type == "synthesize":
                await self.emitter.emit_thinking(action.summary)
                logger.info(
                    "Agent chose to SYNTHESIZE after %d calls: %s",
                    self.calls_made,
                    action.summary[:100],
                )
                break

            # Execute tool
            await self.emitter.emit_tool_start(
                action.tool, action.args, action.reason
            )

            t0 = time.monotonic()
            try:
                result = await self.tools[action.tool].execute(action.args)
                result_dict = result.model_dump()
                self.evidence.ingest(action.tool, action.args, result)
                error = False
            except Exception as e:
                logger.warning(
                    "Tool %s failed: %s", action.tool, e, exc_info=True
                )
                result_dict = {"error": str(e)}
                error = True
            tool_ms = int((time.monotonic() - t0) * 1000)

            # Summarize result for LLM context and SSE
            summary = _summarize_result(action.tool, result_dict, error)
            node_count, passage_count = _count_results(action.tool, result_dict)

            await self.emitter.emit_tool_result(
                action.tool,
                summary,
                duration_ms=tool_ms,
                node_count=node_count,
                passage_count=passage_count,
            )

            # Record in evidence collector audit trail
            self.evidence.record_call(
                tool_name=action.tool,
                args=action.args,
                reason=action.reason,
                result_summary=summary,
                node_count=node_count,
                passage_count=passage_count,
                duration_ms=tool_ms,
            )

            # Append to conversation (summarized, not full result)
            self.messages.append(_assistant_msg(raw))
            context_result = _summarize_for_context(action.tool, result_dict)
            self.messages.append(_tool_msg(context_result))
            self.calls_made += 1

            # Context compression: summarize old tool results
            if len(self.messages) > 14:
                _compress_old_results(self.messages)

        # Budget exhausted
        if self.calls_made >= self.budget:
            await self.emitter.emit_thinking(
                f"Budget exhausted ({self.budget} calls). Proceeding to synthesis."
            )
            logger.info("Agent budget exhausted after %d calls", self.calls_made)

        # Transfer evidence to RAGState for synthesis phase
        self.evidence.populate_state(self.state)
        self.state.iteration = self.calls_made

    def _build_query_context(self) -> str:
        """Build additional context from query classification."""
        parts: list[str] = []
        if self.state.query_type:
            parts.append(f"Query type: {self.state.query_type}")
        if self.state.complexity:
            parts.append(f"Complexity: {self.state.complexity.value}")
        if self.state.expanded_query:
            parts.append(f"Expanded query: {self.state.expanded_query}")
        return "\n".join(parts)


def _parse_action(raw: str, tools: ToolRegistry) -> AgentAction | None:
    """Parse LLM output into an AgentAction."""
    try:
        parsed = parse_json(raw)
    except (json.JSONDecodeError, ValueError):
        return None

    if not isinstance(parsed, dict):
        return None

    # Check for SYNTHESIZE
    if parsed.get("action") == "SYNTHESIZE":
        return AgentAction(
            action_type="synthesize",
            summary=str(parsed.get("summary", "")),
        )

    # Check for tool call
    tool_name = parsed.get("tool")
    if not tool_name or tool_name not in tools:
        return None

    args = parsed.get("args")
    if not isinstance(args, dict):
        return None

    return AgentAction(
        action_type="tool_call",
        tool=tool_name,
        args=args,
        reason=str(parsed.get("reason", "")),
    )


def _summarize_result(tool: str, result: dict[str, Any], error: bool) -> str:
    """One-line summary for SSE streaming."""
    if error:
        return f"Error: {result.get('error', 'unknown')}"

    if tool == "search_nodes":
        nodes = result.get("nodes", [])
        if not nodes:
            return "No nodes found"
        labels = [n.get("label", "?") for n in nodes[:3]]
        total = result.get("total_found", len(nodes))
        return f"Found {total} nodes: {', '.join(labels)}" + (
            "..." if total > 3 else ""
        )

    if tool == "get_neighbors":
        edges = result.get("edges", [])
        if not edges:
            return "No neighbors found"
        return f"{len(edges)} connections from {result.get('center_label', '?')}"

    if tool in ("read_passages", "search_passages"):
        passages = result.get("passages", [])
        if not passages:
            return "No passages found"
        return f"{len(passages)} passages loaded"

    if tool == "get_node_detail":
        return f"{result.get('label', '?')} ({result.get('type', '?')}): {result.get('neighbor_count', 0)} neighbors, {result.get('passage_count', 0)} passages"

    if tool == "read_work_section":
        sections = result.get("sections", [])
        return f"{len(sections)} sections in {result.get('work_title', '?')}"

    if tool == "explore_subgraph":
        nodes = result.get("nodes", [])
        return f"Subgraph: {len(nodes)} relevant nodes from {result.get('seed_count', 0)} seeds"

    return "OK"


def _count_results(tool: str, result: dict[str, Any]) -> tuple[int, int]:
    """Count nodes and passages in a result."""
    nodes = 0
    passages = 0
    if tool in ("search_nodes", "explore_subgraph"):
        nodes = len(result.get("nodes", []))
    elif tool == "get_neighbors":
        nodes = len(result.get("edges", []))
    elif tool in ("read_passages", "search_passages"):
        passages = len(result.get("passages", []))
    elif tool == "read_work_section":
        nodes = len(result.get("sections", []))
    return nodes, passages


def _summarize_for_context(tool: str, result: dict[str, Any]) -> str:
    """Summarize tool result for the LLM conversation context.

    Returns a concise version: node lists show id+label+type only,
    passage text is truncated to 400 chars. Full data is in EvidenceCollector.
    """
    if tool == "search_nodes":
        nodes = result.get("nodes", [])
        lines = [
            f"- {n.get('node_id', '?')}: {n.get('label', '?')} [{n.get('type', '?')}] "
            f"(score={n.get('score', 0):.2f})"
            + (f" — {n.get('description', '')[:100]}" if n.get("description") else "")
            for n in nodes
        ]
        return f"Found {result.get('total_found', len(nodes))} nodes:\n" + "\n".join(lines)

    if tool == "get_neighbors":
        edges = result.get("edges", [])
        lines = [
            f"- {e.get('direction', '?')} {e.get('relation', '?')} → "
            f"{e.get('edge_node_id', '?')}: {e.get('label', '?')} [{e.get('type', '?')}]"
            for e in edges
        ]
        return f"Neighbors of {result.get('center_label', '?')}:\n" + "\n".join(lines)

    if tool in ("read_passages", "search_passages"):
        passages = result.get("passages", [])
        lines = []
        for p in passages:
            text = (p.get("text_content") or "")[:400]
            ref = p.get("canonical_ref") or ""
            work = p.get("work_title") or ""
            lines.append(f"- [{ref}] {work}: {text}")
        return f"{len(passages)} passages:\n" + "\n".join(lines)

    if tool == "get_node_detail":
        desc = (result.get("description") or "")[:500]
        return (
            f"Node: {result.get('label', '?')} [{result.get('type', '?')}]\n"
            f"Period: {result.get('period', '?')}, School: {result.get('school', '?')}\n"
            f"Neighbors: {result.get('neighbor_count', 0)}, Passages: {result.get('passage_count', 0)}\n"
            f"Description: {desc}"
        )

    if tool == "read_work_section":
        sections = result.get("sections", [])
        lines = [
            f"- {s.get('title', '?')} ({s.get('passage_count', 0)} passages)"
            + (" [has subsections]" if s.get("has_subsections") else "")
            for s in sections
        ]
        return f"Sections of {result.get('work_title', '?')}:\n" + "\n".join(lines)

    if tool == "explore_subgraph":
        nodes = result.get("nodes", [])
        lines = [
            f"- {n.get('node_id', '?')}: {n.get('label', '?')} [{n.get('type', '?')}] "
            f"(ppr={n.get('ppr_score', 0):.4f}, dist={n.get('distance_from_seed', '?')})"
            for n in nodes
        ]
        return f"Subgraph ({len(nodes)} nodes):\n" + "\n".join(lines)

    return json.dumps(result, default=str, ensure_ascii=False)[:500]


def _compress_old_results(messages: list[dict[str, str]]) -> None:
    """Compress older tool results to one-line summaries.

    Keeps the system prompt, user prompt, and last 6 messages intact.
    Compresses tool results in the middle section.
    """
    # Keep: [system, user, ..., last_6]
    if len(messages) <= 8:
        return

    # Find tool messages in the middle (skip first 2 and last 6)
    boundary = len(messages) - 6
    for i in range(2, boundary):
        msg = messages[i]
        if msg.get("role") == "tool" and len(msg.get("content", "")) > 200:
            # Compress to first line only
            content = msg["content"]
            first_line = content.split("\n")[0]
            messages[i] = _tool_msg(first_line + " [compressed]")


def _format_conversation(messages: list[dict[str, str]]) -> str:
    """Format conversation history for the LLM.

    Concatenates messages with role prefixes. The LLM service expects
    a single string prompt (not a chat messages array).
    """
    parts: list[str] = []
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        if role == "system":
            parts.append(content)
        elif role == "user":
            parts.append(f"\n\nUser: {content}")
        elif role == "assistant":
            parts.append(f"\n\nAssistant: {content}")
        elif role == "tool":
            parts.append(f"\n\nTool result:\n{content}")
    return "".join(parts)


def _system_msg(content: str) -> dict[str, str]:
    return {"role": "system", "content": content}


def _user_msg(content: str) -> dict[str, str]:
    return {"role": "user", "content": content}


def _assistant_msg(content: str) -> dict[str, str]:
    return {"role": "assistant", "content": content}


def _tool_msg(content: str) -> dict[str, str]:
    return {"role": "tool", "content": content}
