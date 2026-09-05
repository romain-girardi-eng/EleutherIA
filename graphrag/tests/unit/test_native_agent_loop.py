"""Tests for the OpenAI-style native tool-calling agent loop."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock

import pytest
from pydantic import BaseModel

from eleutheria_graphrag.agents.dependencies import Deps
from eleutheria_graphrag.agents.react_loop import (
    AgentLoop,
    NativeAgentLoop,
    build_agent_loop,
)
from eleutheria_graphrag.agents.sse_emitter import NullEmitter
from eleutheria_graphrag.agents.state import QueryComplexity, RAGState
from eleutheria_graphrag.agents.tools import ToolRegistry, build_tool_registry


def _make_deps() -> Deps:
    db = AsyncMock()
    llm = AsyncMock()
    llm.last_model_used = "kimi-k2p6"
    llm.last_provider_used = "fireworks"
    return Deps(
        db=db,
        llm=llm,
        node_lookup={
            "person_origen": {
                "id": "person_origen",
                "label": "Origen",
                "type": "person",
                "description": "Early Christian theologian",
                "period": "Roman Imperial",
                "school": None,
                "metadata": {},
            },
        },
        outgoing_edges={},
        incoming_edges={},
        pagerank_scores={},
    )


class _ProbeResult(BaseModel):
    marker: str


class _ConcurrentProbe:
    def __init__(self) -> None:
        self.active = 0
        self.max_active = 0


class _ProbeTool:
    description = "Concurrency probe"
    parameters_schema = {
        "type": "object",
        "properties": {"delay": {"type": "number"}},
    }

    def __init__(self, name: str, probe: _ConcurrentProbe) -> None:
        self.name = name
        self.probe = probe

    async def execute(self, args: dict) -> _ProbeResult:
        self.probe.active += 1
        self.probe.max_active = max(self.probe.max_active, self.probe.active)
        try:
            await asyncio.sleep(float(args.get("delay", 0.02)))
            return _ProbeResult(marker=self.name)
        finally:
            self.probe.active -= 1


@pytest.mark.asyncio
async def test_native_loop_finishes_on_plain_content() -> None:
    """If the model returns content with no tool_calls, that's the final answer."""
    deps = _make_deps()
    deps.llm.generate_with_tools = AsyncMock(
        return_value={"role": "assistant", "content": "The answer is 42."}
    )

    state = RAGState(question="What?", complexity=QueryComplexity.SIMPLE)
    tools = build_tool_registry(deps)
    loop = NativeAgentLoop(deps=deps, state=state, tools=tools, emitter=NullEmitter())

    await loop.run()

    assert loop.final_answer == "The answer is 42."
    assert loop.calls_made == 0
    deps.llm.generate_with_tools.assert_awaited_once()


@pytest.mark.asyncio
async def test_native_loop_dispatches_tool_calls() -> None:
    """A tool_call response should be executed and looped back as role=tool."""
    deps = _make_deps()
    deps.llm.generate_with_tools = AsyncMock(
        side_effect=[
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_1",
                        "type": "function",
                        "function": {
                            "name": "search_nodes",
                            "arguments": json.dumps({"query": "Origen"}),
                        },
                    }
                ],
            },
            {"role": "assistant", "content": "Found him."},
        ]
    )

    state = RAGState(question="Who is Origen?", complexity=QueryComplexity.SIMPLE)
    tools = build_tool_registry(deps)
    loop = NativeAgentLoop(deps=deps, state=state, tools=tools, emitter=NullEmitter())

    await loop.run()

    assert loop.calls_made == 1
    assert loop.final_answer == "Found him."
    # Two LLM calls: initial + after tool result.
    assert deps.llm.generate_with_tools.await_count == 2
    # The message history should now include a role=tool entry tied to call_1.
    tool_msgs = [m for m in loop.messages if m.get("role") == "tool"]
    assert any(m.get("tool_call_id") == "call_1" for m in tool_msgs)


@pytest.mark.asyncio
async def test_native_loop_invalid_json_args_is_recovered() -> None:
    """If the model emits non-JSON arguments we surface an error to it and keep going."""
    deps = _make_deps()
    deps.llm.generate_with_tools = AsyncMock(
        side_effect=[
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_bad",
                        "type": "function",
                        "function": {
                            "name": "search_nodes",
                            "arguments": "not-json",
                        },
                    }
                ],
            },
            {"role": "assistant", "content": "Recovered."},
        ]
    )

    state = RAGState(question="x", complexity=QueryComplexity.SIMPLE)
    tools = build_tool_registry(deps)
    loop = NativeAgentLoop(deps=deps, state=state, tools=tools, emitter=NullEmitter())

    await loop.run()
    assert loop.final_answer == "Recovered."
    # No successful tool calls counted.
    assert loop.calls_made == 0


@pytest.mark.asyncio
async def test_native_loop_unknown_tool() -> None:
    """Calling an unknown tool yields an error result, loop continues."""
    deps = _make_deps()
    deps.llm.generate_with_tools = AsyncMock(
        side_effect=[
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_x",
                        "type": "function",
                        "function": {
                            "name": "no_such_tool",
                            "arguments": "{}",
                        },
                    }
                ],
            },
            {"role": "assistant", "content": "fine"},
        ]
    )

    state = RAGState(question="x", complexity=QueryComplexity.SIMPLE)
    tools = build_tool_registry(deps)
    loop = NativeAgentLoop(deps=deps, state=state, tools=tools, emitter=NullEmitter())
    await loop.run()
    assert loop.final_answer == "fine"


@pytest.mark.asyncio
async def test_native_loop_iteration_cap(monkeypatch: pytest.MonkeyPatch) -> None:
    """Hard cap at MAX_ITERATIONS even when the model keeps calling tools."""
    monkeypatch.setenv("MAX_ITERATIONS", "3")
    # Disable the tool-call budget so this test isolates the iteration cap.
    monkeypatch.setenv("MAX_TOOL_CALLS", "0")
    deps = _make_deps()

    forever_call = {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": "x",
                "type": "function",
                "function": {
                    "name": "search_nodes",
                    "arguments": json.dumps({"query": "anything"}),
                },
            }
        ],
    }
    deps.llm.generate_with_tools = AsyncMock(return_value=forever_call)

    state = RAGState(question="loop", complexity=QueryComplexity.SIMPLE)
    tools = build_tool_registry(deps)
    loop = NativeAgentLoop(deps=deps, state=state, tools=tools, emitter=NullEmitter())

    await loop.run()
    # 3 iterations × 1 tool call each
    assert loop.calls_made == 3


@pytest.mark.asyncio
async def test_native_loop_tool_call_budget_caps_parallel_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Latency cap: TOTAL tool calls are bounded even with parallel batches.

    Regression for the cold-query blowup — a model that batches several
    ``tool_calls`` per turn (Gemini does) under the 30-turn iteration cap could
    run 126-218 sequential tool executions (86-167 s). The total-tool-call
    budget must stop the loop well before that, regardless of how many calls a
    single turn requests.
    """
    # Generous iteration cap, tight tool-call ceiling — the ceiling must win.
    monkeypatch.setenv("MAX_ITERATIONS", "30")
    monkeypatch.setenv("MAX_TOOL_CALLS", "5")
    deps = _make_deps()

    # Every turn asks for 4 parallel tool calls and never stops on its own.
    def _batch(i: int) -> dict:
        return {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": f"call_{i}_{j}",
                    "type": "function",
                    "function": {
                        "name": "search_nodes",
                        "arguments": json.dumps({"query": "anything"}),
                    },
                }
                for j in range(4)
            ],
        }

    deps.llm.generate_with_tools = AsyncMock(side_effect=[_batch(i) for i in range(20)])

    state = RAGState(question="loop", complexity=QueryComplexity.MEDIUM)
    tools = build_tool_registry(deps)
    loop = NativeAgentLoop(deps=deps, state=state, tools=tools, emitter=NullEmitter())

    await loop.run()

    # Budget is 5: turn 1 executes 4, turn 2 executes 1 then stops. Never the
    # 30×4 = 120 the unbounded loop would have run.
    assert loop.calls_made == 5
    assert loop.max_tool_calls == 5
    # The loop broke long before the iteration cap (only 2 LLM turns needed).
    assert deps.llm.generate_with_tools.await_count == 2


@pytest.mark.asyncio
async def test_native_loop_executes_one_turn_concurrently_but_commits_in_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MAX_PARALLEL_TOOL_CALLS", "2")
    deps = _make_deps()
    deps.llm.generate_with_tools = AsyncMock(
        side_effect=[
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_slow",
                        "type": "function",
                        "function": {
                            "name": "probe_slow",
                            "arguments": json.dumps({"delay": 0.06}),
                        },
                    },
                    {
                        "id": "call_fast",
                        "type": "function",
                        "function": {
                            "name": "probe_fast",
                            "arguments": json.dumps({"delay": 0.01}),
                        },
                    },
                ],
            },
            {"role": "assistant", "content": "done"},
        ]
    )
    probe = _ConcurrentProbe()
    tools = ToolRegistry()
    tools.register(_ProbeTool("probe_slow", probe))
    tools.register(_ProbeTool("probe_fast", probe))
    state = RAGState(question="parallel", complexity=QueryComplexity.SIMPLE)
    loop = NativeAgentLoop(deps=deps, state=state, tools=tools, emitter=NullEmitter())

    await loop.run()

    assert probe.max_active == 2
    assert loop.calls_made == 2
    assert [
        message["tool_call_id"]
        for message in loop.messages
        if message.get("role") == "tool"
    ] == ["call_slow", "call_fast"]
    batch = state.metadata["tool_batch_metrics"][0]
    assert batch["requested"] == batch["executed"] == 2
    assert batch["concurrency_limit"] == 2
    assert batch["sequential_tool_ms"] >= batch["wall_ms"]


def test_build_agent_loop_text_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_TOOL_CALLING_MODE", "text")
    deps = _make_deps()
    tools = build_tool_registry(deps)
    state = RAGState(question="x", complexity=QueryComplexity.SIMPLE)
    loop = build_agent_loop(deps=deps, state=state, tools=tools, emitter=NullEmitter())
    assert isinstance(loop, AgentLoop)


def test_build_agent_loop_native_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_TOOL_CALLING_MODE", "native")
    deps = _make_deps()
    tools = build_tool_registry(deps)
    state = RAGState(question="x", complexity=QueryComplexity.SIMPLE)
    loop = build_agent_loop(deps=deps, state=state, tools=tools, emitter=NullEmitter())
    assert isinstance(loop, NativeAgentLoop)


@pytest.mark.asyncio
async def test_provider_failure_closes_stream_and_prevents_synthesis():
    from eleutheria_graphrag.agents.scholarly_agent import ScholarlyAgent
    from eleutheria_graphrag.agents.sse_emitter import SSEEmitter

    deps = _make_deps()
    deps.llm.generate_with_tools = AsyncMock(
        side_effect=RuntimeError("private provider credential detail")
    )
    state = RAGState(question="What?", complexity=QueryComplexity.SIMPLE)
    queue = asyncio.Queue()
    emitter = SSEEmitter(queue)
    loop = NativeAgentLoop(
        deps=deps, state=state, tools=build_tool_registry(deps), emitter=emitter
    )
    with pytest.raises(RuntimeError) as failure:
        await ScholarlyAgent._run_agent_and_close(loop, emitter)
    assert "private provider" not in str(failure.value)
    frames = []
    while not queue.empty():
        frames.append(queue.get_nowait())
    assert frames[-1] is None
    assert any(frame and frame.get("type") == "error" for frame in frames)
    assert "private provider" not in json.dumps(frames)
    assert loop.calls_made == 0
