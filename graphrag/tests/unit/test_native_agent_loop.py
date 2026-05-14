"""Tests for the OpenAI-style native tool-calling agent loop."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest

from eleutheria_graphrag.agents.dependencies import Deps
from eleutheria_graphrag.agents.react_loop import (
    AgentLoop,
    NativeAgentLoop,
    build_agent_loop,
)
from eleutheria_graphrag.agents.sse_emitter import NullEmitter
from eleutheria_graphrag.agents.state import QueryComplexity, RAGState
from eleutheria_graphrag.agents.tools import build_tool_registry


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
