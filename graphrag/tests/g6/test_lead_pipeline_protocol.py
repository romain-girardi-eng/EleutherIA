"""Lead-researcher pipeline, end to end with stubbed sub-agents.

The lead plans facets, the (stubbed) sub-agents return distilled dossiers —
one of them crashing — the merge builds the bounded evidence set + map, the
lead writes through the existing dialectical synthesis, and the SAME
verification tail as the react pipeline gates the answer. Both the sync facade
and the SSE stream are exercised; the stream's frame order is pinned.
"""

from __future__ import annotations

import contextlib
import json
from typing import Any
from unittest.mock import patch

import pytest

import eleutheria_graphrag.agents.lead_researcher as lr
import eleutheria_graphrag.agents.scholarly_agent as sa_mod
from eleutheria_graphrag.agents.dialectical_synthesis import (
    SynthesisResult,
    build_synthesis_prompt,
    synthesis_brief,
)
from eleutheria_graphrag.agents.scholarly_agent import (
    ANSWER_FINAL_EVENT,
    ANSWER_PROVISIONAL_EVENT,
    ScholarlyAgent,
)
from eleutheria_graphrag.models.dossier import (
    DossierNode,
    DossierPassage,
    ResearchDossier,
)
from eleutheria_graphrag.services.token_budget import estimate_tokens

from .test_dialectical_render_cutover import DIALECTICAL_PROSE, _stub_map
from .test_dialectical_stream_plumbing import (
    _answer_chunk_text,
    _classify_like_route,
    _make_agent,
)

BENCHMARK = (
    "How does Origen in De Principiis III.1 argue for self-determination "
    "(to eph hemin) against Stoic determinism, and how do Bobzien and Frede "
    "assess the continuity between the Stoic and the Origenian conceptions?"
)


async def _stub_subagent(deps, facet, tools, *, model=None, parent_state=None):  # noqa: ARG001
    """Sub-agent double: frames for the scholar facets, a passage for the
    primary facet, a crash for the tradition facet."""
    if facet.kind == "tradition":
        raise RuntimeError("stoic sub-agent lost its provider")
    if facet.kind == "scholar":
        return ResearchDossier(
            facet=facet,
            frames=list(_stub_map().frames),
            nodes=[
                DossierNode(
                    node_id=f"pub_{facet.target_scholars[0].lower()}",
                    type="publication",
                    label=f"{facet.target_scholars[0]} monograph",
                    statement="A publication node.",
                )
            ],
            open_questions=[f"What exactly does {facet.target_scholars[0]} concede?"],
        )
    return ResearchDossier(
        facet=facet,
        passages=[
            DossierPassage(
                passage_id="orig_princ_3_1_5",
                work="De Principiis",
                author="Origen",
                ref="III.1.5",
                language="grc",
                original_text="τὸ αὐτεξούσιον ...",
                translation="Self-determination ...",
                why_relevant="the locus of the argument",
            )
        ],
    )


class _Spy:
    """Records how a bound async-generator method is called, then delegates."""

    def __init__(self, original: Any) -> None:
        self.original = original
        self.calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

    def __get__(self, instance: Any, owner: type) -> Any:
        spy = self

        def bound(*args: Any, **kwargs: Any) -> Any:
            spy.calls.append((args, kwargs))
            return spy.original(instance, *args, **kwargs)

        return bound


@contextlib.contextmanager
def _stubbed():
    """Stub the heavy phases: registry, sub-agents, classify, claim ledger."""

    async def _classify(self, ctx):  # noqa: ARG001
        return None

    async def _noop_draft(self, ctx):  # noqa: ARG001
        return None

    with contextlib.ExitStack() as stack:
        stack.enter_context(
            patch(
                "eleutheria_graphrag.agents.tools.build_tool_registry",
                return_value={},
            )
        )
        stack.enter_context(patch.object(lr, "run_facet_subagent", _stub_subagent))
        stack.enter_context(patch.object(sa_mod.ClassifyQueryType, "run", _classify))
        stack.enter_context(patch.object(sa_mod.DraftClaimLedger, "run", _noop_draft))
        yield


@pytest.mark.asyncio
async def test_lead_query_writes_from_dossiers_and_runs_the_shared_tail_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ELEUTHERIA_SCHOLAR_RAG", "true")
    monkeypatch.setenv("ELEUTHERIA_LEAD_CONTEXT_TOKENS", "20000")
    agent = _make_agent()
    seen: dict[str, Any] = {}

    async def _record_synthesis(state, cmap, llm, **kwargs):  # noqa: ARG001
        seen["cmap"] = cmap
        seen["state"] = state
        return SynthesisResult(prose=DIALECTICAL_PROSE, model_used="stub")

    tail_spy = _Spy(ScholarlyAgent._verify_for_publication)
    with (
        _stubbed(),
        patch.object(sa_mod, "synthesize_dialectical", _record_synthesis),
        patch.object(ScholarlyAgent, "_verify_for_publication", tail_spy),
    ):
        answer = await agent.query(BENCHMARK, pipeline="lead")

    # The verdict: the lead's answer went through the one verification tail.
    assert answer.metadata["publication_gate"]["publishable"] is True
    assert "Bobzien holds the ancients had no free-will problem" in answer.answer
    assert answer.metadata["pipeline"] == "lead"
    assert len(tail_spy.calls) == 1
    args, kwargs = tail_spy.calls[0]
    assert isinstance(args[0], sa_mod.ScholarlyAnswer)
    assert isinstance(args[1], sa_mod.RAGState)
    assert set(kwargs) == {"journal", "result_into"}
    assert isinstance(kwargs["journal"], sa_mod.ResearchJournal)

    # The plan: the benchmark decomposed, one facet per assessor, and the
    # crashed tradition facet neither aborted the query nor vanished.
    lead = answer.metadata["lead"]
    kinds = [f["kind"] for f in lead["facets"]]
    assert kinds.count("scholar") == 2 and "primary" in kinds and "tradition" in kinds
    failed = [
        fid for fid, size in lead["dossier_sizes"].items() if size["status"] == "error"
    ]
    assert len(failed) == 1 and "stoic" in failed[0]
    assert lead["retrieval_errors"][failed[0]] == [
        "RuntimeError: stoic sub-agent lost its provider"
    ]
    assert lead["merged_passages"] == 1
    assert lead["merged_nodes"] == 2
    assert lead["frames"] == 1, "the same frame from two facets is one frame"
    assert lead["subagent_model"] == "utility-tier"
    assert set(lead["subagent_ms"]) == {f["facet_id"] for f in lead["facets"]}
    stages = [m["stage"] for m in answer.metadata["stage_metrics"]]
    assert stages == ["plan", "subagents", "merge", "synthesis"]

    # The lead wrote from the dossiers only, and the WHOLE dossiers are citable:
    # the sub-agents' frame leads the map, one facet frame per non-empty facet
    # carries the rest (the crashed tradition facet has none), every dossier
    # passage is in the provenance index, and the synthesis prompt — still a
    # fraction of the production 420k ceiling — shows every id to the writer.
    cmap = seen["cmap"]
    frame_ids = [f.frame_id for f in cmap.frames]
    assert frame_ids[0] == "discovery_of_will"
    assert len(frame_ids) == 4 and all(f.startswith("facet_") for f in frame_ids[1:])
    assert set(cmap.provenance) == {"cic_fat_41", "orig_princ_3_1_5"}
    state = seen["state"]
    prompt, _ = build_synthesis_prompt(cmap, coverage_note=synthesis_brief(state))
    assert "adsensiones igitur" in prompt
    assert "τὸ αὐτεξούσιον" in prompt, "the dossier passage reaches the writer"
    assert "[passage_orig_princ_3_1_5]" in prompt
    assert "[P_pub_bobzien]" in prompt and "[P_pub_frede]" in prompt
    assert "LEAD RESEARCHER'S BRIEF" in prompt
    assert estimate_tokens(prompt) < 20000
    assert lead["context_tokens_in"] <= 20000
    assert lead["citable_passages"] == 1 and lead["citable_nodes"] == 2
    assert lead["facet_frames"] == 3
    assert sorted(lead["frames_built"].values()) == [0, 0, 1, 1]
    assert set(lead["frames_built"]) == {f["facet_id"] for f in lead["facets"]}
    assert lead["markers_emitted"] == lr.count_citation_markers(DIALECTICAL_PROSE) > 0
    synthesis_stage = next(
        m for m in answer.metadata["stage_metrics"] if m["stage"] == "synthesis"
    )
    assert synthesis_stage["markers_emitted"] == lead["markers_emitted"]
    assert state.retrieval_budget.model_window == 20000
    assert [b.original_passage_id for b in state.evidence_bundles] == [
        "orig_princ_3_1_5"
    ]
    assert sorted(state.research_notebook.open_questions) == [
        "[f3_bobzien_on_the_continuity_between_the_st] What exactly does Bobzien "
        "concede?",
        "[f4_frede_on_the_continuity_between_the_stoi] What exactly does Frede "
        "concede?",
    ]
    assert any("error" in u for u in state.research_notebook.uncertainties)


def _kinds(events: list[str]) -> list[str]:
    return [_classify_like_route(c)[0] for c in events]


def _frames(events: list[str], kind: str) -> list[dict]:
    return [
        parsed
        for c in events
        if (parsed := _classify_like_route(c)[1]) is not None
        and parsed.get("type") == kind
    ]


@pytest.mark.asyncio
async def test_lead_stream_frame_order_and_shared_publication_tail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ELEUTHERIA_SCHOLAR_RAG", "true")
    agent = _make_agent()
    tail_spy = _Spy(ScholarlyAgent._stream_publication_tail)

    events: list[str] = []
    with (
        _stubbed(),
        patch.object(ScholarlyAgent, "_stream_publication_tail", tail_spy),
    ):
        async for ev in agent.query_stream(BENCHMARK, pipeline="lead"):
            events.append(ev)

    kinds = _kinds(events)
    stages = [f["stage"] for f in _frames(events, "stage_complete")]
    facet_stages = [s for s in stages if s.startswith("subagent:")]
    assert len(facet_stages) == 4
    non_facet = [s for s in stages if not s.startswith("subagent:")]
    # The lead's own stages, then whatever the shared tail adds (the audit).
    assert non_facet[:6] == [
        "classify",
        "plan",
        "subagents",
        "merge",
        "synthesis",
        "verify",
    ]
    assert non_facet[6:] == ["citation_audit"]
    # Phase order on the wire: plan -> every facet -> subagents -> merge ->
    # synthesis -> provisional prose -> verdict -> complete.
    assert stages.index("plan") < stages.index(facet_stages[0])
    assert stages.index(facet_stages[-1]) < stages.index("subagents")
    assert stages.index("subagents") < stages.index("merge") < stages.index("synthesis")

    plan_frame = next(
        f for f in _frames(events, "stage_complete") if f["stage"] == "plan"
    )
    assert plan_frame["metadata"]["planner"] == "heuristic"
    assert len(plan_frame["metadata"]["facets"]) == 4
    failed = next(
        f
        for f in _frames(events, "stage_complete")
        if f["stage"].startswith("subagent:") and f["metadata"]["status"] == "error"
    )
    assert "stoic" in failed["stage"]
    merge_frame = next(
        f for f in _frames(events, "stage_complete") if f["stage"] == "merge"
    )
    assert merge_frame["metadata"]["frames"] == 1

    provisional = [i for i, k in enumerate(kinds) if k == ANSWER_PROVISIONAL_EVENT]
    final_idx = kinds.index(ANSWER_FINAL_EVENT)
    synthesis_idx = next(
        i
        for i, c in enumerate(events)
        if (p := _classify_like_route(c)[1]) is not None
        and p.get("type") == "stage_complete"
        and p.get("stage") == "synthesis"
    )
    assert provisional and provisional[0] > stages.index("merge")
    assert provisional[-1] < synthesis_idx < final_idx
    assert all(k != "answer_chunk" for k in kinds[:final_idx])
    assert "answer_chunk" in kinds[final_idx:]
    assert kinds[-1] == "complete"

    final = _frames(events, ANSWER_FINAL_EVENT)[0]
    assert final["data"]["withheld"] is False
    complete = _frames(events, "complete")[0]
    assert complete["data"]["metadata"]["pipeline"] == "lead"
    assert complete["data"]["metadata"]["lead"]["frames"] == 1
    released = "".join(
        text for c in events if (text := _answer_chunk_text(c)) is not None
    )
    assert released == final["data"]["answer"]

    assert len(tail_spy.calls) == 1
    args, kwargs = tail_spy.calls[0]
    assert isinstance(args[0], sa_mod.ScholarlyAnswer)
    assert set(kwargs) == {"journal"}


@pytest.mark.asyncio
async def test_lead_stream_blocks_when_the_audit_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fail-closed exactly as react: no auditor -> blocked verdict, no prose."""
    monkeypatch.setenv("ELEUTHERIA_SCHOLAR_RAG", "true")
    agent = _make_agent()
    agent.deps.verifier_v2 = None
    events: list[str] = []
    with _stubbed():
        async for ev in agent.query_stream(BENCHMARK, pipeline="lead"):
            events.append(ev)
    kinds = _kinds(events)
    assert ANSWER_PROVISIONAL_EVENT in kinds
    assert "answer_chunk" not in kinds
    final = _frames(events, ANSWER_FINAL_EVENT)[0]
    assert final["data"]["withheld"] is True
    assert "citation_audit_not_passed" in final["data"]["reasons"]
    warning = _frames(events, "verification_warning")
    assert warning and warning[0]["data"]["status"] == "blocked"
    assert kinds[-1] == "complete"


@pytest.mark.asyncio
async def test_pipeline_selection_env_default_and_per_request_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    agent = _make_agent()
    routed: list[str] = []

    async def _lead(self, state, *, subagent_model=None):  # noqa: ARG001
        routed.append("lead")
        return sa_mod.ScholarlyAnswer(answer="", question=state.question)

    async def _react(self, state):  # noqa: ARG001
        routed.append("react")
        return sa_mod.ScholarlyAnswer(answer="", question=state.question)

    with (
        patch.object(ScholarlyAgent, "_run_lead", _lead),
        patch.object(ScholarlyAgent, "_run_react", _react),
    ):
        monkeypatch.setenv("ELEUTHERIA_AGENT_MODE", "lead")
        await agent.query("q")
        await agent.query("q", pipeline="react")
        monkeypatch.setenv("ELEUTHERIA_AGENT_MODE", "react")
        await agent.query("q")
        await agent.query("q", pipeline="lead")
        # agent_mode (the legacy keyword) still works and ranks after pipeline.
        await agent.query("q", agent_mode="lead")
        await agent.query("q", pipeline="react", agent_mode="lead")
    assert routed == ["lead", "react", "react", "lead", "lead", "react"]


@pytest.mark.asyncio
async def test_lead_stream_status_frames_are_json_control_frames() -> None:
    """Every non-prose frame the lead emits parses as a typed event."""
    agent = _make_agent()
    events: list[str] = []
    with patch.dict("os.environ", {"ELEUTHERIA_SCHOLAR_RAG": "true"}), _stubbed():
        async for ev in agent.query_stream(BENCHMARK, pipeline="lead"):
            events.append(ev)
    for chunk in events:
        parsed = json.loads(chunk)
        assert parsed.get("type"), chunk[:80]
