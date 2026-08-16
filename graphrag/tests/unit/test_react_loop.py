"""Tests for the ReAct agent loop."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from eleutheria_graphrag.agents.dependencies import Deps
from eleutheria_graphrag.agents.react_loop import (
    AgentLoop,
    _compress_old_results,
    _count_results,
    _parse_action,
    _summarize_result,
    _touched_node_ids,
)
from eleutheria_graphrag.agents.sse_emitter import NullEmitter
from eleutheria_graphrag.agents.state import QueryComplexity, RAGState
from eleutheria_graphrag.agents.tools import ToolRegistry

# ── Fixtures ──────────────────────────────────────────────────────────────


def _make_deps() -> Deps:
    """Minimal mock deps for agent loop tests."""
    db = AsyncMock()
    llm = AsyncMock()
    llm.last_model_used = "gemini-3.1-pro"
    llm.last_provider_used = "gemini"
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
        outgoing_edges={
            "person_origen": [
                {
                    "source": "person_origen",
                    "target": "concept_fw",
                    "relation": "discusses",
                    "weight": 1.0,
                    "metadata": {},
                    "description": "",
                },
            ],
        },
        incoming_edges={},
        pagerank_scores={"person_origen": 0.1},
    )


def _make_tool_registry(deps: Deps) -> ToolRegistry:
    """Build a real tool registry from deps."""
    from eleutheria_graphrag.agents.tools import build_tool_registry

    return build_tool_registry(deps)


# ── _parse_action tests ──────────────────────────────────────────────────


class TestParseAction:
    def test_parse_tool_call(self):
        registry = ToolRegistry()
        # Register a dummy tool
        tool = MagicMock()
        tool.name = "search_nodes"
        registry.register(tool)

        raw = json.dumps(
            {
                "tool": "search_nodes",
                "args": {"query": "Origen"},
                "reason": "Find the philosopher",
            }
        )
        action = _parse_action(raw, registry)
        assert action is not None
        assert action.type == "tool_call"
        assert action.tool == "search_nodes"
        assert action.args == {"query": "Origen"}
        assert action.reason == "Find the philosopher"

    def test_parse_synthesize(self):
        registry = ToolRegistry()
        raw = json.dumps(
            {
                "action": "SYNTHESIZE",
                "summary": "Found Origen and his works",
            }
        )
        action = _parse_action(raw, registry)
        assert action is not None
        assert action.type == "synthesize"
        assert action.summary == "Found Origen and his works"

    def test_parse_with_markdown_fences(self):
        registry = ToolRegistry()
        tool = MagicMock()
        tool.name = "search_nodes"
        registry.register(tool)

        raw = '```json\n{"tool": "search_nodes", "args": {"query": "Plato"}}\n```'
        action = _parse_action(raw, registry)
        assert action is not None
        assert action.tool == "search_nodes"

    def test_parse_invalid_json(self):
        registry = ToolRegistry()
        action = _parse_action("This is not JSON", registry)
        assert action is None

    def test_parse_unknown_tool(self):
        registry = ToolRegistry()
        raw = json.dumps({"tool": "nonexistent", "args": {}})
        action = _parse_action(raw, registry)
        assert action is None

    def test_parse_missing_args(self):
        registry = ToolRegistry()
        tool = MagicMock()
        tool.name = "search_nodes"
        registry.register(tool)

        raw = json.dumps({"tool": "search_nodes"})
        action = _parse_action(raw, registry)
        assert action is None


# ── _summarize_result tests ──────────────────────────────────────────────


class TestSummarizeResult:
    def test_search_nodes(self):
        result = {
            "nodes": [
                {"label": "Origen", "node_id": "n1"},
                {"label": "Plato", "node_id": "n2"},
            ],
            "total_found": 5,
        }
        s = _summarize_result("search_nodes", result, False)
        assert "5 nodes" in s
        assert "Origen" in s

    def test_empty_search(self):
        s = _summarize_result("search_nodes", {"nodes": [], "total_found": 0}, False)
        assert "No nodes" in s

    def test_error(self):
        s = _summarize_result("search_nodes", {"error": "DB down"}, True)
        assert "Error" in s
        assert "DB down" in s

    def test_infer_transitive(self):
        result = {
            "start_node_id": "work_republic",
            "start_label": "Republic",
            "relation": "authored_by",
            "derived_nodes": [{"node_id": "person_plato", "label": "Plato"}],
        }
        s = _summarize_result("infer_transitive", result, False)
        assert "Inferred 1 authored_by nodes" in s
        assert _count_results("infer_transitive", result) == (1, 0)
        assert _touched_node_ids("infer_transitive", result) == [
            "work_republic",
            "person_plato",
        ]


# ── A node read is evidence, never a dead end ─────────────────────────────
#
# ``_count_results`` feeds ``ResearchToolCall.detail_count``, which the research
# journal reads as "did this lead produce anything?". A missing branch here made
# every successful ``get_node_detail`` count 0, and the journal told the reader
# that a publication it had actually read (Fürst 2022) came back empty.


class TestNodeReadCounts:
    def _detail(self, **overrides) -> dict:
        result = {
            "node_id": "pub_furst_2022_wege_freiheit",
            "label": "Fürst, Wege zur Freiheit",
            "type": "publication",
            "description": "Origen's doctrine of freedom.",
            "neighbor_count": 4,
            "passage_count": 0,
            "found": True,
        }
        result.update(overrides)
        return result

    def test_a_successful_read_counts_as_one_node(self):
        assert _count_results("get_node_detail", self._detail()) == (1, 0)

    def test_a_read_with_no_linked_passages_still_counts(self):
        result = self._detail(neighbor_count=0, passage_count=0)
        assert _count_results("get_node_detail", result)[0] == 1

    def test_a_missing_node_counts_nothing(self):
        result = self._detail(label="(not found)", found=False)
        assert _count_results("get_node_detail", result) == (0, 0)
        assert _touched_node_ids("get_node_detail", result) == []

    def test_a_failed_call_counts_nothing(self):
        assert _count_results("get_node_detail", {"error": "DB down"}) == (0, 0)

    def test_a_read_activates_its_node(self):
        assert _touched_node_ids("get_node_detail", self._detail()) == [
            "pub_furst_2022_wege_freiheit"
        ]


class TestNodeReadReachesEvidence:
    """The collector's own record of the read must agree with the counter."""

    def _collector_after(self, result: dict):
        from eleutheria_graphrag.agents.evidence_collector import EvidenceCollector
        from eleutheria_graphrag.agents.tools.get_node_detail import NodeDetail

        collector = EvidenceCollector()
        detail = NodeDetail(**result)
        collector.ingest("get_node_detail", {"node_id": detail.node_id}, detail)
        nodes, passages = _count_results("get_node_detail", detail.model_dump())
        collector.record_call(
            tool_name="get_node_detail",
            args={"node_id": detail.node_id},
            reason="checking the modern reception",
            result_summary="",
            node_count=nodes,
            passage_count=passages,
        )
        return collector

    def test_a_read_node_is_ingested_and_counted(self):
        collector = self._collector_after(
            {
                "node_id": "pub_furst_2022_wege_freiheit",
                "label": "Fürst, Wege zur Freiheit",
                "type": "publication",
                "description": "Origen's doctrine of freedom.",
            }
        )
        state = RAGState(question="q")
        collector.populate_state(state)

        assert [ev.id for ev in state.primary_evidence] == [
            "pub_furst_2022_wege_freiheit"
        ]
        assert state.research_notebook.tool_calls[0].detail_count == 1

    def test_a_missing_node_enters_neither_evidence_nor_the_count(self):
        collector = self._collector_after(
            {
                "node_id": "pub_not_a_real_id",
                "label": "(not found)",
                "type": "",
                "description": "Node 'pub_not_a_real_id' not found in the "
                "knowledge graph.",
                "found": False,
            }
        )
        state = RAGState(question="q")
        collector.populate_state(state)

        assert state.primary_evidence == []
        assert state.research_notebook.tool_calls[0].detail_count == 0


# ── _compress_old_results tests ──────────────────────────────────────────


class TestCompressOldResults:
    def test_compresses_old_tool_results(self):
        messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "Question"},
            {"role": "assistant", "content": '{"tool": "search_nodes"}'},
            {"role": "tool", "content": "A " * 300},  # Long result
            {"role": "assistant", "content": '{"tool": "get_neighbors"}'},
            {"role": "tool", "content": "B " * 300},  # Long result
            # Last 6 messages
            {"role": "assistant", "content": "recent1"},
            {"role": "tool", "content": "recent2"},
            {"role": "assistant", "content": "recent3"},
            {"role": "tool", "content": "recent4"},
            {"role": "assistant", "content": "recent5"},
            {"role": "tool", "content": "recent6"},
        ]
        _compress_old_results(messages)

        # Old tool results should be compressed
        assert "[compressed]" in messages[3]["content"]
        assert "[compressed]" in messages[5]["content"]
        # Recent messages should be untouched
        assert messages[-1]["content"] == "recent6"

    def test_no_compression_when_short(self):
        messages = [
            {"role": "system", "content": "S"},
            {"role": "user", "content": "Q"},
            {"role": "assistant", "content": "A"},
            {"role": "tool", "content": "Short"},
        ]
        _compress_old_results(messages)
        assert messages[3]["content"] == "Short"


# ── AgentLoop integration tests ──────────────────────────────────────────


class TestAgentLoop:
    @pytest.mark.asyncio
    async def test_synthesize_after_one_call(self):
        deps = _make_deps()
        # Script: first call returns a search, second returns SYNTHESIZE
        deps.llm.generate = AsyncMock(
            side_effect=[
                json.dumps(
                    {
                        "tool": "search_nodes",
                        "args": {"query": "Origen"},
                        "reason": "Find philosopher",
                    }
                ),
                json.dumps({"action": "SYNTHESIZE", "summary": "Found Origen"}),
            ]
        )

        state = RAGState(question="Who is Origen?", complexity=QueryComplexity.SIMPLE)
        tools = _make_tool_registry(deps)
        emitter = NullEmitter()

        loop = AgentLoop(deps=deps, state=state, tools=tools, emitter=emitter)
        await loop.run()

        assert loop.calls_made == 1
        assert len(loop.evidence.primary_evidence) >= 1
        # State should be populated
        assert len(state.primary_evidence) >= 1

    @pytest.mark.asyncio
    async def test_budget_exhaustion(self):
        deps = _make_deps()
        # Always return tool calls, never SYNTHESIZE
        deps.llm.generate = AsyncMock(
            return_value=json.dumps(
                {
                    "tool": "search_nodes",
                    "args": {"query": "test"},
                    "reason": "keep going",
                }
            )
        )

        state = RAGState(question="Test", complexity=QueryComplexity.SIMPLE)
        tools = _make_tool_registry(deps)
        emitter = NullEmitter()

        loop = AgentLoop(deps=deps, state=state, tools=tools, emitter=emitter)
        await loop.run()

        # Should stop at budget (SIMPLE = 5)
        assert loop.calls_made == 4  # SIMPLE budget = 4

    @pytest.mark.asyncio
    async def test_parse_failure_recovery(self):
        deps = _make_deps()
        deps.llm.generate = AsyncMock(
            side_effect=[
                "This is not JSON",  # Parse failure 1
                "Still not JSON",  # Parse failure 2
                json.dumps({"action": "SYNTHESIZE", "summary": "recovered"}),  # OK
            ]
        )

        state = RAGState(question="Test", complexity=QueryComplexity.SIMPLE)
        tools = _make_tool_registry(deps)
        emitter = NullEmitter()

        loop = AgentLoop(deps=deps, state=state, tools=tools, emitter=emitter)
        await loop.run()

        # Should have recovered and synthesized
        assert loop.calls_made == 0  # No successful tool calls
        assert loop._parse_failures == 0  # Reset after success

    @pytest.mark.asyncio
    async def test_parse_failure_abort(self):
        deps = _make_deps()
        deps.llm.generate = AsyncMock(return_value="garbage")

        state = RAGState(question="Test", complexity=QueryComplexity.SIMPLE)
        tools = _make_tool_registry(deps)
        emitter = NullEmitter()

        loop = AgentLoop(deps=deps, state=state, tools=tools, emitter=emitter)
        await loop.run()

        # Should abort after MAX_PARSE_FAILURES (3)
        assert loop._parse_failures >= 3

    @pytest.mark.asyncio
    async def test_llm_error_stops_loop(self):
        deps = _make_deps()
        deps.llm.generate = AsyncMock(side_effect=Exception("API error"))

        state = RAGState(question="Test", complexity=QueryComplexity.SIMPLE)
        tools = _make_tool_registry(deps)
        emitter = NullEmitter()

        loop = AgentLoop(deps=deps, state=state, tools=tools, emitter=emitter)
        await loop.run()

        assert loop.calls_made == 0

    @pytest.mark.asyncio
    async def test_evidence_collector_populated(self):
        deps = _make_deps()
        deps.llm.generate = AsyncMock(
            side_effect=[
                json.dumps(
                    {
                        "tool": "search_nodes",
                        "args": {"query": "Origen"},
                        "reason": "find",
                    }
                ),
                json.dumps(
                    {
                        "tool": "get_neighbors",
                        "args": {"node_id": "person_origen"},
                        "reason": "explore",
                    }
                ),
                json.dumps({"action": "SYNTHESIZE", "summary": "done"}),
            ]
        )

        state = RAGState(question="Test", complexity=QueryComplexity.MEDIUM)
        tools = _make_tool_registry(deps)
        emitter = NullEmitter()

        loop = AgentLoop(deps=deps, state=state, tools=tools, emitter=emitter)
        await loop.run()

        assert loop.calls_made == 2
        assert len(loop.evidence.tool_calls) == 2
        # State should have evidence from both calls
        assert len(state.primary_evidence) > 0 or len(state.secondary_evidence) > 0
