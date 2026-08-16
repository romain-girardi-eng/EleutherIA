"""``research_note`` frames on the wire: the abandoned half of the research.

The streaming pipeline now narrates the leads it OPENED AND DROPPED, not only
the ones that landed. This pins the producer↔route contract for that new frame:
its shape, its chronological position (each note lands in the phase where the
lead actually died), and the fact that it never pollutes the answer prose.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

import eleutheria_graphrag.agents.scholarly_agent as sa_mod
from eleutheria_graphrag.agents.scholarly_agent import ScholarlyAgent
from eleutheria_graphrag.agents.state import (
    ClaimLedgerItem,
    ClaimStatus,
    ResearchToolCall,
)

from .test_dialectical_render_cutover import (
    DIALECTICAL_PROSE,
    _stub_map,
    make_stream_segmented,
)
from .test_dialectical_stream_plumbing import _boom_prompt, _classify_like_route


def _agent() -> ScholarlyAgent:
    llm = AsyncMock()
    llm.generate = AsyncMock(return_value=DIALECTICAL_PROSE)
    llm.stream_segmented = make_stream_segmented(DIALECTICAL_PROSE)
    llm.last_reasoning_content = ""
    llm.last_model_used = "gpt-5.6-sol"
    llm.last_provider_used = "codex"
    deps = AsyncMock()
    deps.llm = llm
    deps.verifier_v2 = None
    return ScholarlyAgent(deps)


async def _collect_with_dropped_leads(agent: ScholarlyAgent) -> list[str]:
    """Drive ``_stream_react`` over a run that dropped a lead in every phase."""
    captured: dict[str, object] = {}

    async def _classify(self, ctx):  # noqa: ARG001
        captured["state"] = ctx.state
        return None

    async def _fake_run():
        # The ReAct loop searched a lemma and got nothing back.
        state = captured["state"]
        state.research_notebook.tool_calls = [
            ResearchToolCall(
                tool_call_id="c1",
                tool_name="search_passages",
                stage_id="agent_loop",
                query="αὐτεξούσιον Chrysippus",
                rationale="looking for a Stoic anchor",
                detail_count=0,
            ),
            ResearchToolCall(
                tool_call_id="c2",
                tool_name="search_nodes",
                stage_id="agent_loop",
                query="Bobzien",
                detail_count=6,
            ),
        ]

    async def _inject_map(self, st, tools):  # noqa: ARG001
        st.controversy_map = _stub_map()
        st.metadata["controversy_map"] = {"status": "ok", "frames": 1}
        st.metadata["controversy_map_gaps"] = [
            "build_controversy_frame on debate_fate_1 returned no frame"
        ]
        return True

    async def _quality(self, st, ag):  # noqa: ARG001
        st.metadata["sufficiency_check"] = {
            "score": 0.41,
            "sufficient": False,
            "reason": "no primary passage on the Stoic side",
            "refinement": "",
            "continued": False,
        }
        st.metadata["counter_evidence_hunt"] = {
            "status": "ok",
            "claims_audited": 2,
            "total_testimonia": 0,
            "ledger_items": 0,
        }
        return []

    async def _draft(self, ctx):  # noqa: ARG001
        ctx.state.claim_ledger = [
            ClaimLedgerItem(
                claim="Origen read Chrysippus directly",
                status=ClaimStatus.INSUFFICIENT,
            )
        ]
        return None

    fake_agent = AsyncMock()
    fake_agent.run = AsyncMock(side_effect=_fake_run)
    fake_agent.calls_made = 0
    fake_agent.emitter = None

    events: list[str] = []
    with (
        patch("eleutheria_graphrag.agents.tools.build_tool_registry", return_value={}),
        patch(
            "eleutheria_graphrag.agents.react_loop.build_agent_loop",
            return_value=fake_agent,
        ),
        patch.object(sa_mod.ClassifyQueryType, "run", _classify),
        patch.object(sa_mod.DraftClaimLedger, "run", _draft),
        patch.object(ScholarlyAgent, "_assemble_controversy_map", _inject_map),
        patch.object(ScholarlyAgent, "_post_loop_quality_phase", _quality),
        patch.object(sa_mod, "build_render_prompt", _boom_prompt),
    ):
        async for ev in agent._stream_react("who owns the will in antiquity"):
            events.append(ev)
    return events


def _notes(events: list[str]) -> list[dict]:
    out = []
    for chunk in events:
        if not chunk.startswith('{"type"'):
            continue
        parsed = json.loads(chunk)
        if parsed.get("type") == "research_note":
            out.append(parsed)
    return out


@pytest.mark.asyncio
async def test_every_real_discard_point_reaches_the_wire(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ELEUTHERIA_SCHOLAR_RAG", "true")
    events = await _collect_with_dropped_leads(_agent())
    notes = _notes(events)

    kinds = [n["data"]["kind"] for n in notes]
    stages = [n["data"]["stage"] for n in notes]

    # One note per real discard point — and NOT one for the search that worked.
    assert kinds == ["dead_end", "abandoned", "gap", "dead_end", "rejected_claim"]
    assert stages == [
        "agent_loop",
        "controversy_map",
        "quality_gate",
        "quality_gate",
        "claim_ledger",
    ]

    summaries = " || ".join(n["data"]["summary"] for n in notes)
    assert "αὐτεξούσιον Chrysippus" in summaries
    assert "Bobzien" not in summaries  # the productive search is not a dead end
    assert "debate_fate_1" in summaries
    assert "no primary passage on the Stoic side" in summaries
    assert "Origen read Chrysippus directly" in summaries


@pytest.mark.asyncio
async def test_note_shape_and_prose_isolation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ELEUTHERIA_SCHOLAR_RAG", "true")
    events = await _collect_with_dropped_leads(_agent())

    notes = _notes(events)
    assert notes, "expected research_note frames"
    for note in notes:
        data = note["data"]
        assert set(data) <= {"kind", "summary", "stage", "detail"}
        assert {"kind", "summary", "stage"} <= set(data)
        assert isinstance(data["summary"], str) and data["summary"].strip()

    # The route classifies it as a typed trace event, so no note text can ever
    # end up inside the answer prose.
    prose = "".join(c for c in events if _classify_like_route(c)[0] == "answer_chunk")
    assert "αὐτεξούσιον Chrysippus" not in prose
    assert "research_note" not in prose


@pytest.mark.asyncio
async def test_notes_land_before_the_prose_of_their_phase(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The journal must read chronologically, not as a footnote after the answer."""
    monkeypatch.setenv("ELEUTHERIA_SCHOLAR_RAG", "true")
    events = await _collect_with_dropped_leads(_agent())

    last_note = max(
        i
        for i, c in enumerate(events)
        if c.startswith('{"type"') and json.loads(c).get("type") == "research_note"
    )
    first_prose = next(
        i for i, c in enumerate(events) if _classify_like_route(c)[0] == "answer_chunk"
    )
    assert last_note < first_prose
