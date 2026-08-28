"""Lead-researcher pipeline — planner, sub-agents, dossiers, merge, selection.

Everything here runs with stubbed LLM / DB doubles: no provider, no database.
"""

from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

import eleutheria_graphrag.agents.lead_researcher as lr
from eleutheria_graphrag.agents.dependencies import Deps
from eleutheria_graphrag.agents.graph_nodes import _build_context_pack
from eleutheria_graphrag.agents.scholarly_agent import resolve_pipeline
from eleutheria_graphrag.agents.state import (
    ControversyFrame,
    DialecticalLink,
    FrameCompleteness,
    GroundedPosition,
    PassageRef,
    RAGState,
)
from eleutheria_graphrag.agents.tools import ToolRegistry
from eleutheria_graphrag.agents.tools.search_passages import (
    PassageHit,
    SearchPassagesResult,
)
from eleutheria_graphrag.api import routes as graphrag_routes
from eleutheria_graphrag.models.dossier import (
    DossierNode,
    DossierPassage,
    LeadFacet,
    ResearchDossier,
    empty_dossier,
)
from eleutheria_graphrag.models.query import QueryRequest
from eleutheria_graphrag.services.graphrag_service import ResponseCache

BENCHMARK = (
    "How does Origen in De Principiis III.1 argue for self-determination "
    "(to eph hemin) against Stoic determinism, and how do Bobzien and Frede "
    "assess the continuity between the Stoic and the Origenian conceptions?"
)


def _facet(fid: str, question: str = "q?", **kw: Any) -> LeadFacet:
    return LeadFacet(facet_id=fid, title=fid, question=question, **kw)


def _passage(pid: str, text: str = "adsensiones igitur", **kw: Any) -> DossierPassage:
    return DossierPassage(
        passage_id=pid,
        work="De Fato",
        author="Cicero",
        ref="41",
        original_text=text,
        translation=f"translation of {pid}",
        **kw,
    )


def _frame(frame_id: str = "discovery_of_will") -> ControversyFrame:
    bobzien = GroundedPosition(
        position_id="bobzien_no_problem",
        holder="Bobzien",
        holder_type="modern_scholar",
        claim="the ancients had no free-will problem",
        publication="Bobzien 1998",
        page_grounding="p. 330",
    )
    frede = GroundedPosition(
        position_id="frede_epictetus",
        holder="Frede",
        holder_type="modern_scholar",
        claim="the notion of will originates with Epictetus",
        publication="Frede 2011",
        page_grounding="p. 44",
    )
    return ControversyFrame(
        frame_id=frame_id,
        title="Discovery of the will",
        positions=[bobzien, frede],
        links=[
            DialecticalLink(
                relation="opposes",
                from_id="bobzien_no_problem",
                to_id="frede_epictetus",
                from_holder="Bobzien",
                to_holder="Frede",
            )
        ],
        contested_passages=[
            PassageRef(
                passage_id="cic_fat_41",
                work="De Fato",
                author="Cicero",
                canonical_ref="41",
                original_text="adsensiones igitur, quas prius docui...",
                english_text="Assent, then, which I explained earlier...",
                language="lat",
            )
        ],
        completeness=FrameCompleteness(
            has_two_sides=True, has_primary_grounding=True, incident_edge_count=1
        ),
    )


# ── 1. planner ───────────────────────────────────────────────────────────────


def test_benchmark_question_decomposes_into_named_facets() -> None:
    facets = lr.plan_facets_heuristic(BENCHMARK)
    assert 3 <= len(facets) <= 5
    titles = " | ".join(f.title for f in facets)
    origen = next(f for f in facets if "Origen" in f.target_entities)
    assert any("De Principiis III" in w for w in origen.target_works)
    assert "Origen" in origen.title and "De Principiis" in origen.title
    assert any(f.target_scholars == ["Bobzien"] for f in facets)
    assert any(f.target_scholars == ["Frede"] for f in facets)
    assert any(f.kind == "tradition" and "Stoic" in f.tradition_hints for f in facets)
    assert "Bobzien" in titles and "Frede" in titles
    # Facet order: the primary locus first, background next, assessors last.
    assert facets[0].kind == "primary"
    assert facets[-1].kind == "scholar"
    assert len({f.facet_id for f in facets}) == len(facets)


@pytest.mark.asyncio
async def test_planner_makes_no_llm_call_when_heuristic_is_rich() -> None:
    llm = AsyncMock()
    facets, planner = await lr.plan_facets(BENCHMARK, llm)
    assert planner == "heuristic"
    assert len(facets) >= 3
    llm.generate.assert_not_awaited()


@pytest.mark.asyncio
async def test_thin_heuristic_triggers_exactly_one_llm_refinement() -> None:
    llm = AsyncMock()
    llm.generate = AsyncMock(
        return_value=json.dumps(
            {
                "facets": [
                    {
                        "title": "Stoic fate",
                        "question": "What is heimarmene for Chrysippus?",
                        "target_entities": ["Chrysippus"],
                    },
                    {
                        "title": "Ancient critics",
                        "question": "How did Carneades attack Stoic fate?",
                        "target_entities": ["Carneades"],
                    },
                    {
                        "title": "Modern readings",
                        "question": "How does Bobzien reconstruct the doctrine?",
                        "target_scholars": ["Bobzien"],
                    },
                ]
            }
        )
    )
    facets, planner = await lr.plan_facets("What did the Stoics think about fate?", llm)
    assert planner == "llm"
    assert [f.kind for f in facets] == ["refined"] * 3
    assert facets[2].target_scholars == ["Bobzien"]
    assert llm.generate.await_count == 1
    assert llm.generate.await_args.kwargs["tier"] == "utility"


@pytest.mark.asyncio
async def test_failed_refinement_falls_back_to_a_deterministic_pair() -> None:
    llm = AsyncMock()
    llm.generate = AsyncMock(side_effect=RuntimeError("provider down"))
    facets, planner = await lr.plan_facets("What did the Stoics think about fate?", llm)
    assert planner == "heuristic+default"
    assert len(facets) == 2
    assert facets[1].kind == "background"
    assert facets[0].facet_id != facets[1].facet_id


@pytest.mark.asyncio
async def test_planner_without_llm_still_yields_two_facets() -> None:
    facets, planner = await lr.plan_facets("What did the Stoics think about fate?")
    assert planner == "heuristic+default"
    assert len(facets) == 2


# ── 2. dossier schema ────────────────────────────────────────────────────────


def test_dossier_bounds_text_and_round_trips(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ELEUTHERIA_DOSSIER_PASSAGE_CHARS", "200")
    monkeypatch.setenv("ELEUTHERIA_DOSSIER_MAX_PASSAGES", "2")
    long_text = "λόγος " * 500
    dossier = ResearchDossier(
        facet=_facet("f1"),
        passages=[_passage("p1", long_text), _passage("p2"), _passage("p3")],
        nodes=[DossierNode(node_id="n1", label="Chrysippus", statement="x" * 5000)],
        frames=[_frame()],
        open_questions=["y" * 5000],
    )
    assert len(dossier.passages) == 2, "capped at ELEUTHERIA_DOSSIER_MAX_PASSAGES"
    assert dossier.passages[0].original_text.endswith("[…]")
    assert len(dossier.passages[0].original_text) <= 200 + 4
    assert dossier.nodes[0].statement.endswith("[…]")
    assert len(dossier.open_questions[0]) <= 600 + 4

    restored = ResearchDossier.model_validate_json(dossier.model_dump_json())
    assert restored == dossier
    assert restored.frames[0].frame_id == "discovery_of_will"
    assert restored.token_estimate() == dossier.token_estimate() > 0
    assert restored.summary()["passages"] == 2


# ── 3. merge ─────────────────────────────────────────────────────────────────


def test_merge_dedupes_keeps_provenance_and_prioritises_multi_facet_items() -> None:
    shared = _passage("shared")
    d1 = ResearchDossier(
        facet=_facet("f1"),
        passages=[_passage("only_f1"), shared],
        nodes=[DossierNode(node_id="n_a", label="A", statement="alpha")],
        frames=[_frame("fr1")],
    )
    d2 = ResearchDossier(
        facet=_facet("f2"),
        passages=[_passage("only_f2")],
        frames=[_frame("fr1"), _frame("fr2")],
    )
    d3 = ResearchDossier(
        facet=_facet("f3"),
        passages=[shared.model_copy(update={"why_relevant": "the crux"})],
        nodes=[DossierNode(node_id="n_a", label="A", statement="alpha")],
    )
    merge = lr.merge_dossiers("q", [d1, d2, d3], context_tokens=1_000_000)
    ids = [b.original_passage_id for b in merge.evidence_bundles]
    assert ids[0] == "shared", "a passage two facets found leads"
    assert sorted(ids) == ["only_f1", "only_f2", "shared"]
    assert merge.passage_provenance["shared"] == ["f1", "f3"]
    assert merge.passage_provenance["only_f2"] == ["f2"]
    # The copy carrying the sub-agent's note wins the dedupe.
    assert merge.evidence_bundles[0].metadata["why_relevant"] == "the crux"
    assert [f.frame_id for f in merge.frames] == ["fr1", "fr2"]
    assert merge.frame_provenance["fr1"] == ["f1", "f2"]
    assert len(merge.primary_evidence) == 1
    assert merge.node_provenance["n_a"] == ["f1", "f3"]
    assert merge.controversy_map is not None
    assert [f.frame_id for f in merge.controversy_map.frames] == ["fr1", "fr2"]
    assert "cic_fat_41" in merge.controversy_map.provenance
    assert merge.dropped == {}
    assert merge.summary()["multi_facet_passages"] == 1


def test_merge_token_cap_drops_deterministically_by_priority() -> None:
    big = "word " * 400  # ~ 700 tokens each
    shared = _passage("shared", big)
    d1 = ResearchDossier(
        facet=_facet("f1"), passages=[_passage("f1_first", big), shared]
    )
    d2 = ResearchDossier(
        facet=_facet("f2"), passages=[shared, _passage("f2_only", big)]
    )
    one_passage = lr._passage_tokens(shared)
    merge = lr.merge_dossiers("q", [d1, d2], context_tokens=one_passage * 2 + 1)
    ids = [b.original_passage_id for b in merge.evidence_bundles]
    # Multi-facet first, then facet order; the last single-facet item is shed.
    assert ids == ["shared", "f1_first"]
    assert merge.dropped == {"passage": 1}
    assert merge.context_tokens <= merge.context_cap
    # Same input, same output: the cap is deterministic.
    again = lr.merge_dossiers("q", [d1, d2], context_tokens=one_passage * 2 + 1)
    assert [b.original_passage_id for b in again.evidence_bundles] == ids


def test_apply_merge_bounds_the_legacy_context_pack_to_the_dossiers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ELEUTHERIA_SCHOLAR_RAG", "false")
    sentinel = "RAW_TOOL_CHATTER_SENTINEL"
    dossier = ResearchDossier(
        facet=_facet("f1"),
        passages=[_passage("p1", "the dossier text about assent")],
        nodes=[DossierNode(node_id="n1", label="Chrysippus", statement="Stoic")],
    )
    merge = lr.merge_dossiers("q", [dossier], context_tokens=9000)
    state = RAGState(question="q")
    state.metadata["something_raw"] = sentinel
    lr.apply_merge_to_state(
        state,
        merge,
        facets=[dossier.facet],
        dossiers=[dossier],
        plan=None,
        planner="heuristic",
        subagent_model=None,
    )
    assert state.retrieval_budget.model_window == 9000
    pack = _build_context_pack(state)
    assert "the dossier text about assent" in pack.prompt_context
    assert "Chrysippus" in pack.prompt_context
    assert sentinel not in pack.prompt_context
    assert pack.token_estimate <= 9000
    assert state.metadata["pipeline"] == "lead"
    lead_meta = state.metadata["lead"]
    assert lead_meta["merged_passages"] == 1
    assert lead_meta["context_tokens_in"] <= 9000
    assert lead_meta["passage_provenance"] == {"p1": ["f1"]}
    assert state.controversy_map is None
    assert state.metadata["controversy_map"]["status"] == "skipped"
    assert state.research_notebook.facets[0].facet_id == "f1"


# ── 4. sub-agents ────────────────────────────────────────────────────────────


class _FakeSearchPassages:
    name = "search_passages"
    description = "search"
    parameters_schema = {"type": "object", "properties": {"query": {"type": "string"}}}

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def execute(self, args: dict[str, Any]) -> BaseModel:
        self.calls.append(args)
        return SearchPassagesResult(
            passages=[
                PassageHit(
                    passage_id="orig_princ_3_1_5",
                    work_title="De Principiis",
                    author="Origen",
                    canonical_ref="III.1.5",
                    language="grc",
                    text_content="τὸ αὐτεξούσιον " * 40 + " RAW_ONLY_TAIL " * 300,
                )
            ],
            total_found=1,
        )


class _FrameResult(BaseModel):
    frame: ControversyFrame
    used_fallback: bool = False
    note: str = ""


class _FakeBuildFrame:
    name = "build_controversy_frame"
    description = "frame"
    parameters_schema = {
        "type": "object",
        "properties": {"seed_id": {"type": "string"}},
    }

    async def execute(self, args: dict[str, Any]) -> BaseModel:  # noqa: ARG002
        return _FrameResult(frame=_frame())


class _FakeSearchNodes:
    """Registered but not in SUBAGENT_TOOLS' twin: proves the restriction."""

    name = "infer_transitive"
    description = "never exposed"
    parameters_schema = {"type": "object", "properties": {}}

    async def execute(self, args: dict[str, Any]) -> BaseModel:  # noqa: ARG002
        raise AssertionError("a sub-agent must not reach infer_transitive")


def _registry() -> tuple[ToolRegistry, _FakeSearchPassages]:
    reg = ToolRegistry()
    search = _FakeSearchPassages()
    reg.register(search)
    reg.register(_FakeBuildFrame())
    reg.register(_FakeSearchNodes())
    return reg, search


def _tool_call(name: str, args: dict[str, Any], call_id: str) -> dict[str, Any]:
    return {
        "id": call_id,
        "type": "function",
        "function": {"name": name, "arguments": json.dumps(args)},
    }


def _deps(llm: Any) -> Deps:
    return Deps(db=AsyncMock(), llm=llm)


def _subagent_llm(distill_json: str) -> AsyncMock:
    llm = AsyncMock()
    llm.generate_with_tools = AsyncMock(
        side_effect=[
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    _tool_call("search_passages", {"query": "autexousion"}, "c1"),
                    _tool_call("build_controversy_frame", {"seed_id": "d1"}, "c2"),
                ],
            },
            {"role": "assistant", "content": "DONE: read III.1.5; frame built."},
        ]
    )
    llm.generate = AsyncMock(return_value=distill_json)
    return llm


@pytest.mark.asyncio
async def test_subagent_runs_bounded_loop_and_returns_a_hydrated_dossier(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ELEUTHERIA_GRAPH_SEED", "off")
    monkeypatch.setenv("ELEUTHERIA_DOSSIER_PASSAGE_CHARS", "300")
    llm = _subagent_llm(
        json.dumps(
            {
                "passages": [
                    {"passage_id": "orig_princ_3_1_5", "why_relevant": "the locus"},
                    {"passage_id": "INVENTED_ID", "why_relevant": "made up"},
                ],
                "nodes": [],
                "tensions": [
                    {"statement": "frame vs passage", "between": ["orig_princ_3_1_5"]}
                ],
                "candidate_citations": ["Origen, Princ. III.1.5"],
                "open_questions": ["Which Greek text underlies the Latin?"],
            }
        )
    )
    registry, search = _registry()
    facet = _facet(
        "f1", "How does Origen argue in Princ. III.1?", tool_budget=5, wall_clock_s=30
    )
    dossier = await lr.run_facet_subagent(_deps(llm), facet, registry)

    assert dossier.status == "ok"
    assert [p.passage_id for p in dossier.passages] == ["orig_princ_3_1_5"]
    assert dossier.passages[0].why_relevant == "the locus"
    assert dossier.passages[0].author == "Origen"
    # Bounded: the raw tool text ran to thousands of chars; the dossier does not.
    assert len(dossier.passages[0].original_text) <= 304
    assert "RAW_ONLY_TAIL" not in dossier.passages[0].original_text
    assert [f.frame_id for f in dossier.frames] == ["discovery_of_will"]
    assert dossier.tensions[0].between == ["orig_princ_3_1_5"]
    assert dossier.candidate_citations == ["Origen, Princ. III.1.5"]
    assert dossier.open_questions == ["Which Greek text underlies the Latin?"]
    assert any("unknown id" in e for e in dossier.retrieval_errors)
    assert dossier.usage.tool_calls == 2
    assert dossier.usage.llm_turns == 2
    assert dossier.usage.model == "utility-tier"
    assert search.calls == [{"query": "autexousion"}]

    # The loop ran on the utility tier with no explicit override, over the
    # restricted surface (deterministic-only frame tool exposed, others not).
    first_call = llm.generate_with_tools.await_args_list[0].kwargs
    assert first_call["tier"] == "utility"
    assert first_call["model_override"] == ""
    exposed = {t["function"]["name"] for t in first_call["tools"]}
    assert exposed == {"search_passages", "build_controversy_frame"}
    assert "Facet targets" in first_call["messages"][0]["content"]
    # Distillation was a structured-JSON call fed the inventory, never prose.
    distill_prompt = llm.generate.await_args.args[0]
    assert "orig_princ_3_1_5" in distill_prompt
    assert "DONE: read III.1.5" in distill_prompt
    assert llm.generate.await_args.kwargs["tier"] == "utility"


@pytest.mark.asyncio
async def test_subagent_honours_an_explicit_model_and_survives_bad_distillation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ELEUTHERIA_GRAPH_SEED", "off")
    llm = _subagent_llm("not json at all")
    registry, _ = _registry()
    dossier = await lr.run_facet_subagent(
        _deps(llm), _facet("f1", tool_budget=5), registry, model="claude-sonnet-5"
    )
    assert llm.generate_with_tools.await_args_list[0].kwargs["model_override"] == (
        "claude-sonnet-5"
    )
    assert dossier.usage.model == "claude-sonnet-5"
    # Distillation unparseable: the retrieved evidence is still delivered.
    assert [p.passage_id for p in dossier.passages] == ["orig_princ_3_1_5"]
    assert dossier.passages[0].why_relevant == ""
    assert any("distillation" in e for e in dossier.retrieval_errors)


@pytest.mark.asyncio
async def test_subagent_wall_clock_budget_returns_partial_dossier(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ELEUTHERIA_GRAPH_SEED", "off")
    llm = AsyncMock()

    async def _slow(**_kwargs: Any) -> dict[str, Any]:
        await asyncio.sleep(5)
        return {"role": "assistant", "content": "late"}

    llm.generate_with_tools = AsyncMock(side_effect=_slow)
    llm.generate = AsyncMock(return_value="{}")
    registry, _ = _registry()
    dossier = await lr.run_facet_subagent(
        _deps(llm), _facet("f1", wall_clock_s=0.05), registry
    )
    assert dossier.status == "timeout"
    assert dossier.usage.timed_out is True
    assert any("wall-clock" in e for e in dossier.retrieval_errors)
    assert dossier.is_empty()


@pytest.mark.asyncio
async def test_parallel_subagents_isolate_a_failing_facet() -> None:
    facets = [_facet("f1"), _facet("f2"), _facet("f3")]
    started: list[str] = []

    async def _run(deps, facet, tools, *, model=None, parent_state=None):  # noqa: ARG001
        started.append(facet.facet_id)
        await asyncio.sleep(0.01)
        if facet.facet_id == "f2":
            raise RuntimeError("tool registry exploded")
        return ResearchDossier(facet=facet, passages=[_passage(f"p_{facet.facet_id}")])

    with patch.object(lr, "run_facet_subagent", _run):
        dossiers = await lr.run_subagents(SimpleNamespace(), facets, {})

    assert [d.facet.facet_id for d in dossiers] == ["f1", "f2", "f3"]
    assert dossiers[1].status == "error"
    assert dossiers[1].is_empty()
    assert dossiers[1].retrieval_errors == ["RuntimeError: tool registry exploded"]
    assert dossiers[0].passages[0].passage_id == "p_f1"
    assert dossiers[2].passages[0].passage_id == "p_f3"
    assert sorted(started) == ["f1", "f2", "f3"]

    merge = lr.merge_dossiers("q", dossiers)
    assert sorted(merge.passage_provenance) == ["p_f1", "p_f3"]


def test_empty_dossier_carries_the_error() -> None:
    dossier = empty_dossier(_facet("f9"), status="error", error="boom")
    assert dossier.status == "error"
    assert dossier.retrieval_errors == ["boom"]
    assert dossier.summary()["errors"] == 1


def test_subagent_registry_is_restricted_to_the_allowed_tools() -> None:
    registry, _ = _registry()
    restricted, capture = lr.build_subagent_registry(registry)
    assert "infer_transitive" not in restricted
    assert "search_passages" in restricted
    assert capture is not None and capture.name == "build_controversy_frame"
    names = {s["function"]["name"] for s in lr.subagent_tool_schemas(restricted)}
    assert names == {"search_passages", "build_controversy_frame"}


# ── 5. selection: env, per-request, cache slots, API validation ──────────────


def test_resolve_pipeline_env_and_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ELEUTHERIA_AGENT_MODE", raising=False)
    assert resolve_pipeline() == "react"
    monkeypatch.setenv("ELEUTHERIA_AGENT_MODE", "lead")
    assert resolve_pipeline() == "lead"
    assert resolve_pipeline("react") == "react", "per-request override wins"
    assert resolve_pipeline(None, "fsm") == "fsm"
    assert resolve_pipeline("bogus") == "lead", "unknown override -> env"
    monkeypatch.setenv("ELEUTHERIA_AGENT_MODE", "bogus")
    assert resolve_pipeline() == "react"


def test_response_cache_never_shares_a_slot_across_pipelines() -> None:
    cache = ResponseCache()
    react_key = cache._key("Q?", "auto", "auto")
    assert react_key == cache._key("Q?", "auto", "auto", pipeline="react")
    assert react_key != cache._key("Q?", "auto", "auto", pipeline="lead")
    cache.put("Q?", "auto", "auto", {"answer": "lead"}, pipeline="lead")
    assert cache.get("Q?", "auto", "auto") is None
    assert cache.get("Q?", "auto", "auto", pipeline="lead") == {"answer": "lead"}


def test_subagent_model_resolution(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ELEUTHERIA_SUBAGENT_MODEL", raising=False)
    assert lr.resolve_subagent_model() is None
    monkeypatch.setenv("ELEUTHERIA_SUBAGENT_MODEL", "gemini-3.7-flash-high")
    assert lr.resolve_subagent_model() == "gemini-3.7-flash-high"
    assert lr.resolve_subagent_model("claude-sonnet-5") == "claude-sonnet-5"
    monkeypatch.setenv("ELEUTHERIA_SUBAGENT_TOOL_BUDGET", "7")
    monkeypatch.setenv("ELEUTHERIA_LEAD_CONTEXT_TOKENS", "70000")
    assert lr.subagent_tool_budget() == 7
    assert lr.lead_context_tokens() == 70000
    facets = lr.plan_facets_heuristic(BENCHMARK)
    assert all(f.tool_budget == 7 for f in facets)


class _RecordingGraphRAG:
    calls: list[dict[str, Any]] = []

    async def query_stream(self, **kwargs: Any):
        _RecordingGraphRAG.calls.append(kwargs)
        return
        yield ""  # pragma: no cover — async generator marker

    async def query(self, **kwargs: Any) -> dict[str, Any]:
        _RecordingGraphRAG.calls.append(kwargs)
        return {
            "answer": "",
            "question": kwargs["question"],
            "citations": [],
            "seed_nodes": [],
            "context_nodes": [],
            "passages_used": 0,
            "claim_ledger": [],
            "llm_model": "",
            "llm_provider": "",
            "metadata": {},
        }


@pytest.fixture
def client() -> TestClient:
    _RecordingGraphRAG.calls = []
    app = FastAPI()
    app.include_router(graphrag_routes.router, prefix="/api/graphrag")
    app.dependency_overrides[graphrag_routes.get_graphrag] = _RecordingGraphRAG
    return TestClient(app)


@pytest.mark.parametrize("bad", ["fsm", "leader", "react-lead", "auto"])
def test_stream_route_rejects_unknown_pipeline_with_422(
    client: TestClient, bad: str
) -> None:
    resp = client.get(
        "/api/graphrag/query/stream", params={"question": "q", "pipeline": bad}
    )
    assert resp.status_code == 422
    assert "pipeline" in resp.json()["detail"]


@pytest.mark.parametrize("ok", ["lead", "Lead", " react "])
def test_stream_route_threads_pipeline_to_the_service(
    client: TestClient, ok: str
) -> None:
    resp = client.get(
        "/api/graphrag/query/stream",
        params={"question": "q", "pipeline": ok, "subagent_model": "claude-sonnet-5"},
    )
    assert resp.status_code == 200
    assert _RecordingGraphRAG.calls[-1]["pipeline"] == ok.strip().lower()
    assert _RecordingGraphRAG.calls[-1]["subagent_model"] == "claude-sonnet-5"


def test_stream_route_default_leaves_pipeline_to_the_env(client: TestClient) -> None:
    resp = client.get("/api/graphrag/query/stream", params={"question": "q"})
    assert resp.status_code == 200
    assert "pipeline" not in _RecordingGraphRAG.calls[-1]


def test_query_request_validates_pipeline() -> None:
    assert QueryRequest(question="abc", pipeline="lead").pipeline == "lead"
    assert QueryRequest(question="abc").pipeline is None
    with pytest.raises(ValueError):
        QueryRequest(question="abc", pipeline="turbo")


def test_post_query_threads_pipeline_and_rejects_bad_values(client: TestClient) -> None:
    resp = client.post(
        "/api/graphrag/query",
        json={"question": "what is fate", "pipeline": "lead"},
    )
    assert resp.status_code == 200
    assert _RecordingGraphRAG.calls[-1]["pipeline"] == "lead"
    resp = client.post(
        "/api/graphrag/query",
        json={"question": "what is fate", "pipeline": "turbo"},
    )
    assert resp.status_code == 422
