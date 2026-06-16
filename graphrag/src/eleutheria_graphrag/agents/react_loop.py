"""
ReAct agent loop for scholarly graph retrieval.

Replaces the fixed FSM middle section (ExpandQuery → EvidenceSufficiency)
with a free-form tool-calling loop where the LLM reasons about what to
retrieve and when to stop.

Two execution modes are supported, selected by the env variable
``LLM_TOOL_CALLING_MODE``:

- ``native`` (default): OpenAI-style function/tool-calling via
  ``LLMService.generate_with_tools``. Robust against text-parsing failures
  with Kimi K2.6 and other modern chat models. This is the production path.
- ``text``: legacy text-parsing ReAct prompt — kept as a feature-flagged
  fallback while the native path is under observation.

Inspired by: IRCoT (ACL 2023), ToG 2.0 (ICLR 2024), DoG (AAAI 2025),
CRAG (ICLR 2024), HippoRAG (NeurIPS 2024).
"""

from __future__ import annotations

import json
import logging
import os
import time
import uuid
from typing import Any

from eleutheria_graphrag.agents.dependencies import Deps
from eleutheria_graphrag.agents.evidence_collector import EvidenceCollector
from eleutheria_graphrag.agents.graph_helpers import parse_json, resolve_model_api_id
from eleutheria_graphrag.agents.prompts import (
    BUDGET_WARNING,
    FORMAT_RETRY,
    format_system_prompt,
    format_user_prompt,
    kg_scale_summary,
)
from eleutheria_graphrag.agents.sse_emitter import SSEEmitter
from eleutheria_graphrag.agents.state import QueryComplexity, RAGState
from eleutheria_graphrag.agents.tool_schemas import build_tool_function_schemas
from eleutheria_graphrag.agents.tools import ToolRegistry

logger = logging.getLogger(__name__)


def _tool_calling_mode() -> str:
    """Return the active tool-calling mode (``"native"`` or ``"text"``)."""
    return (os.getenv("LLM_TOOL_CALLING_MODE", "native") or "native").lower()


def _max_iterations() -> int:
    """Safety belt on the native tool-calling loop.

    The cap exists only to defend against pathological LLM behavior (a model
    that keeps requesting tool calls forever). Well-behaved agents emit a
    SYNTHESIZE signal and exit on their own well before this number.

    Default raised to 30 — the previous value (12) was forcing premature
    synthesis on doctoral-grade queries that legitimately need 15+ tool
    calls (cross-period KG traversal + multi-source close reading).
    """
    try:
        return int(os.getenv("MAX_ITERATIONS", "30"))
    except ValueError:
        return 30


# Budget per complexity tier (optimized for speed — fewer but smarter calls)
_BUDGETS: dict[QueryComplexity, int] = {
    QueryComplexity.SIMPLE: 4,
    QueryComplexity.MEDIUM: 7,
    QueryComplexity.COMPLEX: 10,
}

# Hard ceiling on TOTAL tool calls (not LLM turns) for the native loop.
#
# ``MAX_ITERATIONS`` caps LLM turns, but a single turn can request many
# parallel ``tool_calls`` — Gemini routinely batches 4-7 per turn. With a 30
# turn cap that is 120-210 sequential tool executions, which profiling showed
# is the dominant cold-query cost (agent_loop = 86-167 s of the ~280 s total,
# 126-218 tool calls). The per-turn iteration cap alone does NOT bound this.
#
# These ceilings stop dispatching once the loop has gathered enough evidence,
# which is what keeps a cold query inside the Cloudflare connection window.
# They are deliberately generous relative to ``_BUDGETS`` (which the legacy
# text loop uses as a turn budget) so doctoral-grade multi-source reads still
# complete, while pathological 200-call runs are cut off. Override with
# ``MAX_TOOL_CALLS`` to force a single ceiling for all tiers.
_TOOL_CALL_BUDGETS: dict[QueryComplexity, int] = {
    QueryComplexity.SIMPLE: 12,
    QueryComplexity.MEDIUM: 20,
    QueryComplexity.COMPLEX: 30,
}


def _tool_call_budget(complexity: QueryComplexity) -> int:
    """Total-tool-call ceiling for the native loop (env-overridable).

    ``MAX_TOOL_CALLS`` sets a single ceiling across all tiers; otherwise the
    per-complexity defaults apply. Returns a large number when explicitly
    disabled (``MAX_TOOL_CALLS=0``) so the loop falls back to the iteration cap.
    """
    raw = os.getenv("MAX_TOOL_CALLS")
    if raw is not None:
        try:
            value = int(raw)
        except ValueError:
            value = 0
        if value > 0:
            return value
        if value == 0:
            return 1_000_000  # disabled — iteration cap is the only belt
    return _TOOL_CALL_BUDGETS.get(complexity, 20)


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
        # Legacy loop never produces an inline final answer — the FSM Phase 3
        # nodes synthesize it. Kept for API parity with NativeAgentLoop.
        self.final_answer: str | None = None

    async def run(self) -> None:
        """Execute the ReAct loop."""
        # Initialize conversation
        self.messages = [
            _system_msg(
                format_system_prompt(
                    budget=self.budget,
                    remaining=self.budget,
                    tool_descriptions=self.tools.tool_descriptions(),
                    kg_data=self.deps.kg_data,
                )
            ),
            _user_msg(
                format_user_prompt(
                    question=self.state.question,
                    context=self._build_query_context(),
                )
            ),
        ]

        self.emitter.set_budget(self.budget)

        while self.calls_made < self.budget:
            remaining = self.budget - self.calls_made
            self.emitter.set_calls_made(self.calls_made)

            # Budget warning at N-2
            if remaining == 2:
                self.messages.append(
                    _system_msg(BUDGET_WARNING.format(remaining=remaining))
                )

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
            int((time.monotonic() - t0) * 1000)

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
            await self.emitter.emit_tool_start(action.tool, action.args, action.reason)

            t0 = time.monotonic()
            try:
                result = await self.tools[action.tool].execute(action.args)
                result_dict = result.model_dump()
                self.evidence.ingest(action.tool, action.args, result)
                error = False
            except Exception as e:
                logger.warning("Tool %s failed: %s", action.tool, e, exc_info=True)
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
    except (json.JSONDecodeError, ValueError) as _exc:
        del _exc
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

    if tool == "infer_transitive":
        nodes = result.get("derived_nodes", [])
        relation = result.get("relation", "?")
        start = result.get("start_label") or result.get("start_node_id") or "?"
        suffix = " (truncated)" if result.get("truncated") else ""
        return f"Inferred {len(nodes)} {relation} nodes from {start}{suffix}"

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
    elif tool == "infer_transitive":
        nodes = len(result.get("derived_nodes", []))
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
        return f"Found {result.get('total_found', len(nodes))} nodes:\n" + "\n".join(
            lines
        )

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

    if tool == "infer_transitive":
        nodes = result.get("derived_nodes", [])
        lines = [
            f"- {n.get('node_id', '?')}: {n.get('label', '?')} [{n.get('type', '?')}] "
            f"(distance={n.get('distance', '?')}, derivation={', '.join(n.get('derivation') or [])})"
            + (f" inferred={n.get('inferred_edge')}" if n.get("inferred_edge") else "")
            for n in nodes[:50]
        ]
        suffix = "\n- [truncated]" if result.get("truncated") else ""
        return (
            f"Inferred via {result.get('relation', '?')} from "
            f"{result.get('start_label') or result.get('start_node_id', '?')} "
            f"({len(nodes)} nodes):\n" + "\n".join(lines) + suffix
        )

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


# ───────────────────────────────────────────────────────────────────────────
# Native tool-calling path (OpenAI-style ``tools=`` + ``tool_calls``)
# ───────────────────────────────────────────────────────────────────────────


NATIVE_SYSTEM_PROMPT_TEMPLATE = """\
You are a scholarly research agent specializing in ancient philosophy. You have \
access to {kg_scale} covering philosophical debates on free will, \
fate, and moral responsibility from the 6th century BCE to the 6th century CE.

## Your Mission
Gather the textual evidence for a deeply grounded scholarly answer. A separate \
synthesis stage will write the final answer from the evidence you retrieve — \
your job is retrieval coverage, not prose. Quality standards:
- ALWAYS read passages — do not rely on node descriptions alone.
- Verify attributions before treating a passage as evidence.
- NEVER fabricate ancient text. If you cannot find a passage, say so.

## How to Work
1. Search for the philosophers, concepts, or works mentioned in the question.
2. Explore the neighborhood with get_neighbors (omit relation_filter first).
3. Read primary texts with read_passages on every relevant work or argument node.
   At least 3-5 passages per philosopher discussed.
4. Use search_passages for Greek/Latin terms (αὐτεξούσιον, εἱμαρμένη, \
liberum arbitrium, ἐφ᾿ ἡμῖν).
5. Stop calling tools once you have enough textual evidence.

## Output Format
Use the provided tools to gather evidence. Everything a tool returns is \
recorded automatically for the downstream synthesis stage; your final plain \
message is NOT shown to the user. When you are done retrieving, reply with a \
single assistant message (no tool call) containing a structured evidence \
inventory in Markdown:
- **Evidence found** — each relevant passage/node with its reference \
(e.g. "De Princ. III.1.5") and one line on what it establishes.
- **Coverage gaps** — authors, works, or sub-questions you could not ground \
in retrieved passages (state "none" if fully covered).
Do not write the scholarly answer itself and do not quote long passages — \
synthesis happens downstream from the recorded evidence.
"""


# ───────────────────────────────────────────────────────────────────────────
# Scholar-RAG (G6) debate-first system prompt — used only when
# ELEUTHERIA_SCHOLAR_RAG is on. The default NATIVE_SYSTEM_PROMPT_TEMPLATE above is
# left untouched so the existing pipeline is byte-for-byte unchanged.
# ───────────────────────────────────────────────────────────────────────────

SCHOLAR_RAG_SYSTEM_PROMPT_TEMPLATE = """\
You are a scholarly research agent specializing in ancient philosophy, with \
access to {kg_scale} covering debates on free will, fate, and moral \
responsibility from the 6th century BCE to the 6th century CE.

This knowledge graph encodes scholarly **disagreement** as edges (`opposes`, \
`critiques`, `responds_to`, `refutes`, `contrasts_with`). The pipeline has \
ALREADY surfaced the live fault lines for this question (the controversy map is \
assembled deterministically by a separate stage). **Your job is to GROUND them** \
— deepen the evidence behind each contested position — so the synthesis stage \
can write a dialectical answer.

## How to Work — grounding-first
1. Do NOT try to enumerate the debates yourself; that map already exists. \
Instead, strengthen its grounding: for each position or contested claim implied \
by the question, find the holder's publication/page and the primary passage that \
anchors it.
2. Use `search_nodes` / `get_neighbors` / `get_node_detail` to locate scholarly \
positions, arguments, and the `opposes`/`critiques`/`responds_to` edges between \
them, then `search_passages` / `read_passages` to retrieve the contested primary \
text (original + English).
3. A position is reportable only if you can name its *holder* and its *grounding* \
(publication + primary passage). For every position, retrieve that grounding \
before reporting it.
4. Always fetch the `_en` translation alongside the original; `read_passages` \
pairs them automatically. Read deep (full bilingual) only on demand — never \
truncate at a tool boundary.

## Hard rules
- NEVER write a position without its holder and page.
- NEVER paraphrase a position you have not located via an edge.
- NEVER assert a modern label ('libertarian', 'compatibilism', 'the will') as \
historical fact — these belong only inside an attributed scholarly position.
- NEVER fabricate ancient text. If you cannot find a passage, say so.

## Output Format
Everything a tool returns is recorded automatically for downstream synthesis; \
your final plain message is NOT shown to the user. When done retrieving, reply \
with a single assistant message (no tool call) containing a Markdown evidence \
inventory:
- **Fault lines found** — each debate with its two sides + the opposing edge.
- **Grounding** — per position, its publication/page + primary passage reference.
- **Coverage gaps** — fault lines or positions you could not ground (state \
"none" if fully covered).
Do not write the scholarly answer itself; synthesis happens downstream.
"""


def _native_system_prompt(deps: Deps) -> str:
    """Build the native-loop system prompt with truthful KG counts.

    Switches to the debate-first Scholar-RAG variant when
    ``ELEUTHERIA_SCHOLAR_RAG`` is on (default OFF → unchanged behaviour).
    """
    from eleutheria_graphrag.agents.state import scholar_rag_enabled

    template = (
        SCHOLAR_RAG_SYSTEM_PROMPT_TEMPLATE
        if scholar_rag_enabled()
        else NATIVE_SYSTEM_PROMPT_TEMPLATE
    )
    return template.format(kg_scale=kg_scale_summary(deps.kg_data))


class _NativeAgentLoopBase:
    """Shared scaffolding between the native and text-parsing loops."""

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
        self.calls_made = 0
        self.final_answer: str | None = None


class NativeAgentLoop(_NativeAgentLoopBase):
    """OpenAI-style tool-calling agent loop.

    Each iteration:
        1. Send the running message list + the tool schemas to the LLM.
        2. If the assistant returns ``tool_calls``: execute them, append the
           tool results to messages, loop.
        3. If the assistant returns plain ``content``: retrieval is done. The
           text (a structured evidence inventory per the system prompt) is
           stored on ``final_answer`` for diagnostics (REPL, logs); the
           user-facing answer is synthesized downstream by
           ``DraftClaimLedger -> RenderGroundedAnswer`` from the evidence
           recorded in ``EvidenceCollector``.

    The loop is hard-capped at ``MAX_ITERATIONS`` to defend against models that
    refuse to stop calling tools.
    """

    def __init__(
        self,
        deps: Deps,
        state: RAGState,
        tools: ToolRegistry,
        emitter: SSEEmitter,
    ) -> None:
        super().__init__(deps, state, tools, emitter)
        self.max_iterations = _max_iterations()
        # Hard ceiling on total tool calls (not LLM turns) — the real defence
        # against the 126-218-call cold-query blowups profiling surfaced. See
        # ``_tool_call_budget`` for the rationale.
        self.max_tool_calls = _tool_call_budget(state.complexity)
        self.tool_schemas = build_tool_function_schemas(tools)
        self.messages: list[dict[str, Any]] = []
        self._activated_node_ids: set[str] = set()

    async def run(self) -> None:
        """Execute the native tool-calling loop."""
        trace_id = uuid.uuid4().hex
        self.messages = [
            {"role": "system", "content": _native_system_prompt(self.deps)},
            {
                "role": "user",
                "content": format_user_prompt(
                    question=self.state.question,
                    context=_build_query_context(self.state),
                ),
            },
        ]

        await self.emitter.emit_agent_start(
            agent="eleutheria",
            query=self.state.question,
            trace_id=trace_id,
        )
        self.emitter.set_budget(self.max_iterations)

        for iteration in range(self.max_iterations):
            self.emitter.set_calls_made(self.calls_made)

            try:
                message = await self.deps.llm.generate_with_tools(
                    messages=self.messages,
                    tools=self.tool_schemas,
                    tool_choice="auto",
                    temperature=0.1,
                    max_tokens=2048,
                    model_override=resolve_model_api_id(self.state),
                )
            except Exception as exc:  # pragma: no cover — surfaced to client
                logger.error(
                    "LLM tool-calling failed at iteration %d: %s",
                    iteration,
                    exc,
                    exc_info=True,
                )
                await self.emitter.emit_error(f"LLM error: {exc}")
                break

            tool_calls = message.get("tool_calls") or []
            content = message.get("content")

            # No tool calls — final answer (or empty).
            if not tool_calls:
                self.final_answer = content or ""
                await self.emitter.emit_thinking(
                    "Agent completed retrieval; synthesizing answer."
                )
                logger.info(
                    "Native agent finished after %d tool calls",
                    self.calls_made,
                )
                break

            # Persist the assistant turn so the model sees its own tool calls.
            self.messages.append(_assistant_with_tool_calls(content, tool_calls))

            for call in tool_calls:
                if self.calls_made >= self.max_tool_calls:
                    # Budget hit mid-turn: the model echoed tool_calls we must
                    # answer (an unanswered tool_call id breaks the next
                    # request), so reply with a terminal stub instead of
                    # executing — no DB/LLM work, just a "budget reached" note.
                    self._answer_unexecuted_call(call)
                    continue
                await self._dispatch_tool_call(call)

            if self.calls_made >= self.max_tool_calls:
                await self.emitter.emit_thinking(
                    f"Tool-call budget of {self.max_tool_calls} reached; "
                    "proceeding to synthesis."
                )
                logger.info(
                    "Native agent loop hit tool-call budget=%d after %d calls",
                    self.max_tool_calls,
                    self.calls_made,
                )
                break
        else:
            await self.emitter.emit_thinking(
                f"Iteration cap of {self.max_iterations} reached; forcing synthesis."
            )
            logger.warning(
                "Native agent loop hit MAX_ITERATIONS=%d", self.max_iterations
            )

        # Transfer evidence to RAGState for synthesis phase.
        self.evidence.populate_state(self.state)
        self.state.iteration = self.calls_made

    def _answer_unexecuted_call(self, call: dict[str, Any]) -> None:
        """Stub-answer a ``tool_calls`` entry we declined to run (budget hit).

        Every assistant ``tool_call`` must be answered by a matching ``role:
        tool`` message or the next request 400s. When the tool-call budget is
        reached mid-turn we still record a (cheap, no-op) result so the message
        history stays well-formed for the final break.
        """
        call_id = (
            call.get("id") if isinstance(call, dict) else None
        ) or uuid.uuid4().hex
        self.messages.append(
            _tool_result_msg(
                call_id,
                json.dumps({"skipped": "tool-call budget reached; synthesizing"}),
            )
        )

    async def _dispatch_tool_call(self, call: dict[str, Any]) -> None:
        """Execute a single ``tool_calls`` entry and append its result."""
        call_id = call.get("id") or uuid.uuid4().hex
        fn = (call.get("function") or {}) if isinstance(call, dict) else {}
        tool_name = fn.get("name") or ""
        raw_args = fn.get("arguments") or "{}"

        # Arguments come back as a JSON string.
        try:
            args = json.loads(raw_args) if isinstance(raw_args, str) else dict(raw_args)
        except json.JSONDecodeError:
            logger.warning(
                "Tool %s: invalid JSON args %r — skipping", tool_name, raw_args
            )
            self.messages.append(
                _tool_result_msg(
                    call_id,
                    json.dumps({"error": "invalid tool arguments"}),
                )
            )
            return

        if tool_name not in self.tools:
            self.messages.append(
                _tool_result_msg(
                    call_id,
                    json.dumps({"error": f"unknown tool {tool_name}"}),
                )
            )
            return

        await self.emitter.emit_tool_call(
            agent="eleutheria",
            tool=tool_name,
            args=args,
            call_id=call_id,
        )
        # Keep the legacy event so older frontends still light up.
        await self.emitter.emit_tool_start(tool_name, args, reason="")

        t0 = time.monotonic()
        try:
            result_model = await self.tools[tool_name].execute(args)
            result_dict = result_model.model_dump()
            self.evidence.ingest(tool_name, args, result_model)
            error = False
        except Exception as exc:
            logger.warning("Tool %s failed: %s", tool_name, exc, exc_info=True)
            result_dict = {"error": str(exc)}
            error = True
        duration_ms = int((time.monotonic() - t0) * 1000)

        summary = _summarize_result(tool_name, result_dict, error)
        node_count, passage_count = _count_results(tool_name, result_dict)
        nodes_touched = _touched_node_ids(tool_name, result_dict)
        passages_touched = _touched_passage_ids(tool_name, result_dict)

        await self.emitter.emit_tool_call_result(
            tool_call_id=call_id,
            result_summary=summary,
            nodes_touched=nodes_touched,
            passages_touched=passages_touched,
            duration_ms=duration_ms,
        )
        # Legacy event mirror.
        await self.emitter.emit_tool_result(
            tool_name,
            summary,
            duration_ms=duration_ms,
            node_count=node_count,
            passage_count=passage_count,
        )

        await self._emit_node_and_citation_events(tool_name, result_dict, nodes_touched)

        self.evidence.record_call(
            tool_name=tool_name,
            args=args,
            reason="",
            result_summary=summary,
            node_count=node_count,
            passage_count=passage_count,
            duration_ms=duration_ms,
        )
        self.calls_made += 1

        # Append summarized tool result so model context stays bounded.
        compact = _summarize_for_context(tool_name, result_dict)
        self.messages.append(_tool_result_msg(call_id, compact))

    async def _emit_node_and_citation_events(
        self,
        tool: str,
        result: dict[str, Any],
        nodes_touched: list[str],
    ) -> None:
        """Emit ``kg_node_activated`` + ``citation_found`` for nice UI updates."""
        for node_id in nodes_touched:
            if node_id in self._activated_node_ids:
                continue
            self._activated_node_ids.add(node_id)
            node = self.deps.node_lookup.get(node_id, {})
            await self.emitter.emit_kg_node_activated(
                node_id=node_id,
                label=str(node.get("label") or node_id),
                node_type=str(node.get("type") or "concept"),
                period=node.get("period"),
            )

        if tool in ("read_passages", "search_passages"):
            for passage in result.get("passages", []):
                excerpt = (passage.get("text_content") or "")[:400]
                if not excerpt:
                    continue
                pid = str(
                    passage.get("passage_id")
                    or passage.get("id")
                    or passage.get("canonical_ref")
                    or ""
                )
                if not pid:
                    continue
                node_ids = [
                    str(n) for n in (passage.get("kg_node_ids") or nodes_touched) if n
                ]
                await self.emitter.emit_citation_found(
                    passage_id=pid,
                    excerpt=excerpt,
                    node_ids=node_ids,
                    confidence=float(passage.get("confidence") or 0.7),
                    cts_urn=passage.get("cts_urn"),
                    work_label=passage.get("work_title"),
                )


def _assistant_with_tool_calls(
    content: str | None, tool_calls: list[dict[str, Any]]
) -> dict[str, Any]:
    """Build the assistant message we echo back so the model sees its own calls."""
    msg: dict[str, Any] = {"role": "assistant", "tool_calls": tool_calls}
    if content:
        msg["content"] = content
    else:
        msg["content"] = None
    return msg


def _tool_result_msg(tool_call_id: str, content: str) -> dict[str, Any]:
    """Build a ``role: tool`` message linked to the originating call."""
    return {
        "role": "tool",
        "tool_call_id": tool_call_id,
        "content": content,
    }


def _build_query_context(state: RAGState) -> str:
    parts: list[str] = []
    if state.query_type:
        parts.append(f"Query type: {state.query_type}")
    if state.complexity:
        parts.append(f"Complexity: {state.complexity.value}")
    if state.expanded_query:
        parts.append(f"Expanded query: {state.expanded_query}")
    return "\n".join(parts)


def _touched_node_ids(tool: str, result: dict[str, Any]) -> list[str]:
    if tool in ("search_nodes", "explore_subgraph"):
        return [
            str(n.get("node_id")) for n in result.get("nodes", []) if n.get("node_id")
        ]
    if tool == "get_neighbors":
        return [
            str(e.get("edge_node_id"))
            for e in result.get("edges", [])
            if e.get("edge_node_id")
        ]
    if tool == "get_node_detail":
        nid = result.get("node_id")
        return [str(nid)] if nid else []
    if tool == "infer_transitive":
        ids = [
            str(n.get("node_id"))
            for n in result.get("derived_nodes", [])
            if n.get("node_id")
        ]
        start_id = result.get("start_node_id")
        if start_id:
            ids.insert(0, str(start_id))
        return list(dict.fromkeys(ids))
    return []


def _touched_passage_ids(tool: str, result: dict[str, Any]) -> list[str]:
    if tool in ("read_passages", "search_passages"):
        return [
            str(p.get("passage_id") or p.get("id") or "")
            for p in result.get("passages", [])
            if p.get("passage_id") or p.get("id")
        ]
    return []


# ───────────────────────────────────────────────────────────────────────────
# Mode-selecting alias
# ───────────────────────────────────────────────────────────────────────────


def build_agent_loop(
    deps: Deps,
    state: RAGState,
    tools: ToolRegistry,
    emitter: SSEEmitter,
) -> Any:
    """Construct the agent loop matching ``LLM_TOOL_CALLING_MODE``.

    Returns an object exposing ``run()``, ``calls_made``, ``evidence``, and
    ``final_answer`` (the native path) or a legacy ``AgentLoop``.
    """
    mode = _tool_calling_mode()
    if mode == "text":
        logger.info("Using legacy text-parsing AgentLoop (LLM_TOOL_CALLING_MODE=text)")
        return AgentLoop(deps=deps, state=state, tools=tools, emitter=emitter)
    return NativeAgentLoop(deps=deps, state=state, tools=tools, emitter=emitter)
