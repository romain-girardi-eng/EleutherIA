"""Deterministic graph seed on the ReAct path.

Before this step, the ReAct loop only expanded the graph when the model chose
to call ``explore_subgraph``; two runs of the same question could start from
different evidence. The seed step runs the retrieval strategy + a bounded
``WeightedTraversal`` before turn 0 and pushes the result through the same
``EvidenceCollector`` paths the tools use.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any
from unittest.mock import AsyncMock

import pytest

from eleutheria_graphrag.agents.dependencies import Deps
from eleutheria_graphrag.agents.evidence_collector import EvidenceCollector
from eleutheria_graphrag.agents.graph_seed import (
    GRAPH_SEED_BUDGET_ENV,
    GRAPH_SEED_ENV,
    seed_graph_context,
)
from eleutheria_graphrag.agents.react_loop import NativeAgentLoop
from eleutheria_graphrag.agents.sse_emitter import NullEmitter
from eleutheria_graphrag.agents.state import QueryComplexity, RAGState
from eleutheria_graphrag.agents.tools import ToolRegistry, build_tool_registry
from eleutheria_graphrag.agents.tools.explore_subgraph import ExploreSubgraphTool
from eleutheria_graphrag.agents.tools.read_passages import (
    PassageSummary,
    ReadPassagesResult,
)
from eleutheria_graphrag.services.weighted_traversal import WeightedTraversal

QUESTION = "How does Origen ground moral responsibility?"


def _node(node_id: str, label: str, node_type: str, **metadata: Any) -> dict[str, Any]:
    return {
        "id": node_id,
        "node_id": node_id,
        "label": label,
        "type": node_type,
        "description": f"{label} description",
        "period": None,
        "school": None,
        "metadata": metadata,
    }


def _graph() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Origen --argues_for--> autexousion --influences--> De principiis
    Origen --related_to--> theodicy argument --refutes--> [blocked node]
    De principiis --contains--> passage (skipped by the subgraph ingest)."""
    nodes = {
        "person_origen": _node("person_origen", "Origen", "person"),
        "concept_autexousion": _node("concept_autexousion", "Autexousion", "concept"),
        "work_de_principiis": _node("work_de_principiis", "De principiis", "work"),
        "argument_theodicy": _node(
            "argument_theodicy", "Theodicy argument", "argument"
        ),
        "argument_blocked": _node(
            "argument_blocked", "Blocked argument", "argument", citation_blocked=True
        ),
        "passage_1": _node("passage_1", "Princ. III.1.1", "passage"),
        "person_unrelated": _node("person_unrelated", "Zeno", "person"),
    }
    edges = [
        ("person_origen", "concept_autexousion", "argues_for", 1.0),
        ("concept_autexousion", "work_de_principiis", "influences", 1.0),
        ("person_origen", "argument_theodicy", "related_to", 1.0),
        ("argument_theodicy", "argument_blocked", "refutes", 1.0),
        ("work_de_principiis", "passage_1", "contains", 1.0),
    ]
    outgoing: dict[str, list[dict[str, Any]]] = {}
    incoming: dict[str, list[dict[str, Any]]] = {}
    for source, target, relation, weight in edges:
        edge = {
            "source": source,
            "target": target,
            "relation": relation,
            "weight": weight,
        }
        outgoing.setdefault(source, []).append(edge)
        incoming.setdefault(target, []).append(edge)
    return nodes, outgoing, incoming


class _StubStrategy:
    def __init__(self, seeds: list[str], *, delay: float = 0.0) -> None:
        self.seeds = seeds
        self.delay = delay
        self.calls = 0

    async def discover_seeds(
        self,
        queries: list[str],  # noqa: ARG002 — protocol signature
        deps: Any,  # noqa: ARG002
        node_limit: int = 100,  # noqa: ARG002
    ) -> tuple[list[str], list[str]]:
        self.calls += 1
        if self.delay:
            await asyncio.sleep(self.delay)
        return list(self.seeds), []


class _RaisingStrategy:
    async def discover_seeds(
        self,
        queries: list[str],  # noqa: ARG002 — protocol signature
        deps: Any,  # noqa: ARG002
        node_limit: int = 100,  # noqa: ARG002
    ) -> tuple[list[str], list[str]]:
        raise RuntimeError("db down")


class _StubReadPassages:
    """One passage per node, keyed by node id — deterministic and DB-free."""

    name = "read_passages"
    description = "stub"
    parameters_schema: dict[str, Any] = {"type": "object", "properties": {}}

    def __init__(self) -> None:
        self.calls: list[str] = []

    async def execute(self, args: dict[str, Any]) -> ReadPassagesResult:
        node_id = args["node_id"]
        self.calls.append(node_id)
        return ReadPassagesResult(
            node_id=node_id,
            node_label=node_id,
            passages=[
                PassageSummary(
                    passage_id=f"p_{node_id}",
                    work_title="De principiis",
                    author="Origen",
                    canonical_ref="III.1.1",
                    language="grc",
                    text_content="text",
                    confidence=1.0,
                )
            ],
        )


def _make_deps(strategy: Any | None) -> Deps:
    nodes, outgoing, incoming = _graph()
    llm = AsyncMock()
    llm.last_model_used = "kimi-k2p6"
    llm.last_provider_used = "fireworks"
    llm.generate_with_tools = AsyncMock(
        return_value={"role": "assistant", "content": "done"}
    )
    return Deps(
        db=AsyncMock(),
        llm=llm,
        traversal=WeightedTraversal(nodes, outgoing, incoming),
        retrieval_strategy=strategy,
        node_lookup=nodes,
        outgoing_edges=outgoing,
        incoming_edges=incoming,
        pagerank_scores={},
    )


def _tools(deps: Deps) -> tuple[ToolRegistry, _StubReadPassages]:
    tools = build_tool_registry(deps)
    reader = _StubReadPassages()
    tools.register(reader)  # type: ignore[arg-type]
    return tools, reader


def _state() -> RAGState:
    return RAGState(question=QUESTION, complexity=QueryComplexity.SIMPLE)


def _ids(evidence: list[Any]) -> list[str]:
    return [e.id for e in evidence]


# ── the step runs on the react path ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_graph_seed_runs_before_the_first_llm_turn(monkeypatch) -> None:
    monkeypatch.delenv(GRAPH_SEED_ENV, raising=False)
    strategy = _StubStrategy(["person_origen"])
    deps = _make_deps(strategy)
    tools, reader = _tools(deps)
    state = _state()

    loop = NativeAgentLoop(deps=deps, state=state, tools=tools, emitter=NullEmitter())
    await loop.run()

    assert strategy.calls == 1
    report = state.metadata["graph_seed"]
    assert report["status"] == "ok"
    assert report["seed_nodes"] == ["person_origen"]
    # Reachable neighbourhood, in traversal order: argumentative edge first.
    assert report["expanded_nodes"] == [
        "concept_autexousion",
        "argument_theodicy",
        "work_de_principiis",
    ]
    # Blocked and passage nodes are traversed but never enter the evidence.
    assert "argument_blocked" not in report["expanded_nodes"]
    assert "passage_1" not in report["expanded_nodes"]
    assert report["edges_followed"] == 5
    assert report["truncated"] is False
    assert report["ms"] >= 0
    assert report["passages"] == 4

    # Evidence reached the state the synthesis phase reads.
    assert state.seed_node_ids == ["person_origen"]
    assert set(report["expanded_nodes"]) <= set(state.context_node_ids)
    assert "person_origen" in _ids(state.primary_evidence)
    assert {b.original_passage_id for b in state.evidence_bundles} == {
        "p_person_origen",
        "p_concept_autexousion",
        "p_argument_theodicy",
        "p_work_de_principiis",
    }
    assert reader.calls == [
        "person_origen",
        "concept_autexousion",
        "argument_theodicy",
        "work_de_principiis",
    ]
    # The LLM saw the seeded neighbourhood in the turn-0 prompt, no tool call needed.
    prompt = loop.messages[1]["content"]
    assert "Graph neighbourhood already seeded" in prompt
    assert "concept_autexousion" in prompt
    assert loop.calls_made == 0
    assert loop.final_answer == "done"


@pytest.mark.asyncio
async def test_graph_seed_falls_back_to_snapshot_scoring_without_a_strategy(
    monkeypatch,
) -> None:
    monkeypatch.delenv(GRAPH_SEED_ENV, raising=False)
    deps = _make_deps(None)
    tools, _reader = _tools(deps)
    state = _state()

    await seed_graph_context(deps, state, EvidenceCollector(), tools)

    report = state.metadata["graph_seed"]
    assert report["status"] == "ok"
    assert "person_origen" in report["seed_nodes"]
    assert "person_unrelated" not in report["seed_nodes"]


@pytest.mark.asyncio
async def test_graph_seed_seeds_from_the_entity_works_pass_too(monkeypatch) -> None:
    """Nodes already seeded before the step are traversal seeds, not duplicates."""
    monkeypatch.delenv(GRAPH_SEED_ENV, raising=False)
    deps = _make_deps(_StubStrategy([]))
    tools, _reader = _tools(deps)
    state = _state()
    evidence = EvidenceCollector()
    evidence.seen_node_ids.add("person_origen")
    evidence.seed_node_ids.append("person_origen")

    context = await seed_graph_context(deps, state, evidence, tools)

    report = state.metadata["graph_seed"]
    assert report["seed_nodes"] == ["person_origen"]
    assert report["expanded_nodes"]
    assert evidence.seed_node_ids == ["person_origen"]
    # The prompt block lists only what the step added, not the works block again.
    assert "person_origen —" not in context
    assert "concept_autexousion" in context


# ── flag off ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.parametrize("value", ["false", "0", "off", "no", " FALSE "])
async def test_graph_seed_is_skipped_when_the_flag_is_off(monkeypatch, value) -> None:
    monkeypatch.setenv(GRAPH_SEED_ENV, value)
    strategy = _StubStrategy(["person_origen"])
    deps = _make_deps(strategy)
    tools, reader = _tools(deps)
    state = _state()

    loop = NativeAgentLoop(deps=deps, state=state, tools=tools, emitter=NullEmitter())
    await loop.run()

    assert strategy.calls == 0
    assert reader.calls == []
    assert state.metadata["graph_seed"] == {
        "status": "disabled",
        "seed_nodes": [],
        "expanded_nodes": [],
        "edges_followed": 0,
        "ms": 0,
        "truncated": False,
        "passages": 0,
    }
    assert state.primary_evidence == []
    assert state.secondary_evidence == []
    assert "Graph neighbourhood" not in loop.messages[1]["content"]
    assert loop.final_answer == "done"


# ── budget ──────────────────────────────────────────────────────────────────


def test_traversal_deadline_in_the_past_returns_seeds_only() -> None:
    nodes, outgoing, incoming = _graph()
    traversal = WeightedTraversal(nodes, outgoing, incoming)

    result = traversal.expand_with_stats(
        ["person_origen"], deadline=time.monotonic() - 1.0
    )

    assert result.visited == {"person_origen"}
    assert result.order == ["person_origen"]
    assert result.edges_followed == 0
    assert result.truncated is True
    assert result.deadline_hit is True


def test_traversal_node_cap_reports_truncation() -> None:
    nodes, outgoing, incoming = _graph()
    traversal = WeightedTraversal(nodes, outgoing, incoming)

    capped = traversal.expand_with_stats(["person_origen"], max_nodes=2)
    full = traversal.expand_with_stats(["person_origen"], max_nodes=30)

    # The cap is checked per popped node (historical behaviour), so the first
    # node's neighbours are admitted together; the frontier is then abandoned.
    assert capped.visited == {
        "person_origen",
        "concept_autexousion",
        "argument_theodicy",
    }
    assert capped.truncated is True
    assert capped.deadline_hit is False
    assert full.truncated is False
    assert full.visited == {
        "person_origen",
        "concept_autexousion",
        "work_de_principiis",
        "argument_theodicy",
        "argument_blocked",
        "passage_1",
    }
    # ``expand`` keeps its historical contract.
    assert traversal.expand(["person_origen"]) == full.visited


@pytest.mark.asyncio
async def test_graph_seed_respects_the_wall_clock_budget(monkeypatch) -> None:
    monkeypatch.delenv(GRAPH_SEED_ENV, raising=False)
    monkeypatch.setenv(GRAPH_SEED_BUDGET_ENV, "50")
    strategy = _StubStrategy(["person_origen"], delay=0.5)
    deps = _make_deps(strategy)
    tools, reader = _tools(deps)
    state = _state()
    evidence = EvidenceCollector()
    evidence.seen_node_ids.add("person_origen")
    evidence.seed_node_ids.append("person_origen")

    started = time.monotonic()
    await seed_graph_context(deps, state, evidence, tools)
    elapsed = time.monotonic() - started

    assert elapsed < 0.4, "the slow discovery must be cut by the budget"
    report = state.metadata["graph_seed"]
    assert report["truncated"] is True
    assert report["status"] == "ok"
    # Seeds already in hand still went through the traversal (deadline passed,
    # so only the seeds themselves), and no passage read started.
    assert report["seed_nodes"] == ["person_origen"]
    assert report["expanded_nodes"] == []
    assert reader.calls == []
    assert any(
        err.startswith("graph_seed: seed discovery timed out")
        for err in state.metadata["retrieval_errors"]
    )


# ── idempotence with the LLM tools ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_graph_seed_and_tool_calls_never_duplicate_evidence(
    monkeypatch,
) -> None:
    monkeypatch.delenv(GRAPH_SEED_ENV, raising=False)
    deps = _make_deps(_StubStrategy(["person_origen"]))
    tools, reader = _tools(deps)
    state = _state()
    evidence = EvidenceCollector()

    await seed_graph_context(deps, state, evidence, tools)
    nodes_after_seed = len(evidence.primary_evidence) + len(evidence.secondary_evidence)
    bundles_after_seed = len(evidence.evidence_bundles)
    assert nodes_after_seed == 4
    assert bundles_after_seed == 4

    # The model later explores the same neighbourhood and re-reads a passage.
    subgraph = await ExploreSubgraphTool(deps).execute(
        {"seed_node_ids": ["person_origen"], "top_k": 20}
    )
    assert subgraph.nodes, "the tool does find the neighbourhood"
    evidence.ingest("explore_subgraph", {}, subgraph)
    evidence.ingest(
        "read_passages",
        {"node_id": "person_origen"},
        await reader.execute({"node_id": "person_origen"}),
    )

    # A second deterministic pass over the same collector is a no-op too.
    first_report = state.metadata["graph_seed"]
    state = _state()
    await seed_graph_context(deps, state, evidence, tools)

    all_ids = _ids(evidence.primary_evidence) + _ids(evidence.secondary_evidence)
    assert len(all_ids) == len(set(all_ids))
    # Every node the seed step put in is there exactly once, whatever the
    # tool returned on top of it.
    for nid in ("person_origen", *first_report["expanded_nodes"]):
        assert all_ids.count(nid) == 1
    bundle_ids = [b.original_passage_id for b in evidence.evidence_bundles]
    assert len(bundle_ids) == len(set(bundle_ids)) == bundles_after_seed
    assert len(evidence.context_node_ids) == len(set(evidence.context_node_ids))
    assert state.metadata["graph_seed"]["expanded_nodes"] == []
    assert state.metadata["graph_seed"]["passages"] == 0


@pytest.mark.asyncio
async def test_graph_seed_runs_once_per_query(monkeypatch) -> None:
    """The sufficiency continuation re-enters ``run()`` with feedback appended
    to the question; the step must not re-discover seeds from that text."""
    monkeypatch.delenv(GRAPH_SEED_ENV, raising=False)
    strategy = _StubStrategy(["person_origen"])
    deps = _make_deps(strategy)
    tools, reader = _tools(deps)
    state = _state()

    loop = NativeAgentLoop(deps=deps, state=state, tools=tools, emitter=NullEmitter())
    await loop.run()
    first_report = dict(state.metadata["graph_seed"])
    state.question += "\n\nFill the evidence gap with a few targeted tool calls."
    await loop.run()

    assert strategy.calls == 1
    assert len(reader.calls) == 4
    assert state.metadata["graph_seed"] == first_report
    assert "Graph neighbourhood" not in loop.messages[1]["content"]


@pytest.mark.asyncio
async def test_graph_seed_skips_the_llm_lemma_expansion(monkeypatch) -> None:
    """With ``SQLStrategy`` wired, discovery runs without its LLM Step 0."""
    from eleutheria_graphrag.services.retrieval_strategy import SQLStrategy

    monkeypatch.delenv(GRAPH_SEED_ENV, raising=False)
    expander = AsyncMock()
    expander.expand = AsyncMock(return_value=["autexous"])
    deps = _make_deps(SQLStrategy(min_bundles=4, lemma_expander=expander))
    # An AsyncMock db answers every query with an empty row set.
    tools, _reader = _tools(deps)
    state = _state()

    await seed_graph_context(deps, state, EvidenceCollector(), tools)

    expander.expand.assert_not_awaited()
    assert deps.db.fetch.await_count >= 1
    assert state.metadata["graph_seed"]["status"] == "no_seeds"


# ── graceful degradation ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_graph_seed_survives_a_failing_strategy(monkeypatch) -> None:
    monkeypatch.delenv(GRAPH_SEED_ENV, raising=False)
    deps = _make_deps(_RaisingStrategy())
    tools, _reader = _tools(deps)
    state = _state()

    loop = NativeAgentLoop(deps=deps, state=state, tools=tools, emitter=NullEmitter())
    await loop.run()

    assert loop.final_answer == "done"
    assert state.metadata["graph_seed"]["status"] == "no_seeds"
    assert state.metadata["retrieval_errors"] == ["graph_seed: seed discovery: db down"]


@pytest.mark.asyncio
async def test_graph_seed_survives_a_failing_traversal(monkeypatch) -> None:
    monkeypatch.delenv(GRAPH_SEED_ENV, raising=False)
    deps = _make_deps(_StubStrategy(["person_origen"]))

    class _Boom:
        def expand_with_stats(self, *_args: Any, **_kwargs: Any) -> Any:
            raise RuntimeError("boom")

    deps.traversal = _Boom()  # type: ignore[assignment]
    tools, reader = _tools(deps)
    state = _state()

    loop = NativeAgentLoop(deps=deps, state=state, tools=tools, emitter=NullEmitter())
    await loop.run()

    assert loop.final_answer == "done"
    report = state.metadata["graph_seed"]
    assert report["status"] == "error"
    assert report["seed_nodes"] == ["person_origen"]
    assert report["expanded_nodes"] == []
    assert state.metadata["retrieval_errors"] == ["graph_seed: boom"]
    # What was ingested before the failure is kept, not rolled back.
    assert state.seed_node_ids == ["person_origen"]
    assert reader.calls == []


@pytest.mark.asyncio
async def test_graph_seed_records_a_failing_passage_read_and_continues(
    monkeypatch,
) -> None:
    monkeypatch.delenv(GRAPH_SEED_ENV, raising=False)
    deps = _make_deps(_StubStrategy(["person_origen"]))
    tools, reader = _tools(deps)

    healthy = reader.execute

    async def flaky(args: dict[str, Any]) -> ReadPassagesResult:
        if args["node_id"] == "concept_autexousion":
            raise RuntimeError("passage store unavailable")
        return await healthy(args)

    reader.execute = flaky  # type: ignore[method-assign]
    state = _state()
    evidence = EvidenceCollector()

    await seed_graph_context(deps, state, evidence, tools)

    report = state.metadata["graph_seed"]
    assert report["status"] == "ok"
    assert report["passages"] == 3
    assert state.metadata["retrieval_errors"] == [
        "graph_seed: read_passages[concept_autexousion]: passage store unavailable"
    ]
