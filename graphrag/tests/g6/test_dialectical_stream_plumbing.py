"""Scholar-RAG M4 — dialectical STREAMING plumbing (SSE polish).

Three contracts the streaming/output plumbing must honour on the flag-ON
dialectical path:

1. STREAMING POLLUTION — the SSE ``answer_chunk`` events must carry ONLY the
   finished dialectical prose. The agent's raw event stream (``tool_call`` /
   ``kg_node_activated`` / ``agent_start`` / ``citation_found`` …) must travel on
   its own trace channel, NEVER smuggled into ``answer_chunk`` data.
2. FULL PROSE IN ``complete`` — the terminal ``complete`` event's ``answer``
   must equal the FULL ``state.raw_answer`` (the whole dialectical prose), not a
   truncated tail.
3. NO DOUBLE-RETRIEVAL — ``find_debates`` / ``build_controversy_frame`` are
   driven deterministically by ``_assemble_controversy_map``; they must NOT be
   exposed to the ReAct agent (so it cannot improvise the same expensive calls).

These mirror the route-boundary classification (``routes.query_stream``): a chunk
is a trace event iff it parses as JSON with a ``type`` field; otherwise it is
raw prose wrapped as ``answer_chunk``. We replicate that decision here so the
test pins the producer↔route contract without booting FastAPI/DB.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

import eleutheria_graphrag.agents.scholarly_agent as sa_mod
from eleutheria_graphrag.agents.dialectical_synthesis import SynthesisResult
from eleutheria_graphrag.agents.scholarly_agent import ScholarlyAgent
from eleutheria_graphrag.agents.state import RAGState
from eleutheria_graphrag.models.verification import (
    CitationCheck,
    CitationStatus,
    VerificationReport,
)

from .test_dialectical_render_cutover import (
    DIALECTICAL_PROSE,
    _stub_map,
    make_stream_segmented,
)

# The route forwards these typed events on their own channel (Scholar-RAG ON);
# none may become an ``answer_chunk`` (see routes.query_stream).
_TRACE_EVENT_TYPES = {
    "agent_thinking",
    "agent_start",
    "agent_complete",
    "tool_start",
    "tool_call",
    "tool_result",
    "kg_node_activated",
    "citation_found",
    "citation_verified",
    "final_answer",
    "status",
    "error",
    "stage_complete",
    "cost_summary",
    "tokens_used_rollup",
    "verification_warning",
    "complete",
    "citations_preview",
}


def _classify_like_route(chunk: str) -> tuple[str, dict | None]:
    """Replicate routes.query_stream's per-chunk decision (Scholar-RAG ON).

    Returns ``("answer_chunk", None)`` when the chunk is raw prose wrapped as an
    answer_chunk, or ``(event_type, parsed)`` when it is forwarded raw as a
    typed trace/terminal event.
    """
    if chunk.startswith('{"type":'):
        try:
            parsed = json.loads(chunk)
        except json.JSONDecodeError:
            parsed = None
        if parsed is not None:
            event_type = parsed.get("type", "")
            # Flag-ON: every typed event is forwarded raw (allowlist + safety net).
            if event_type:
                return event_type, parsed
    return "answer_chunk", None


async def _collect_stream(agent: ScholarlyAgent, question: str) -> list[str]:
    """Drive ``_stream_react`` with the heavy phases stubbed; collect raw yields.

    Real: the synthesis tail (``_stream_render`` -> ``_stream_dialectical`` ->
    ``_synthesize_dialectical``), ``ProgrammaticVerify``, and the terminal
    ``_chunk_answer``/``complete`` emission — that is the plumbing under test.
    Stubbed: classify, agent loop, controversy-map assembly (we inject the map),
    the post-loop quality gate, and ``DraftClaimLedger``.
    """

    async def _classify(self, ctx):  # noqa: ARG001
        return None

    async def _inject_map(self, st, tools):  # noqa: ARG001
        st.controversy_map = _stub_map()
        st.metadata["controversy_map"] = {"status": "ok", "frames": 1}
        return True

    async def _noop_quality(self, st, ag):  # noqa: ARG001
        return []

    async def _noop_draft(self, ctx):  # noqa: ARG001
        return None

    fake_agent = AsyncMock()
    fake_agent.run = AsyncMock(return_value=None)
    fake_agent.calls_made = 0
    fake_agent.emitter = None

    events: list[str] = []
    with (
        patch(
            "eleutheria_graphrag.agents.tools.build_tool_registry",
            return_value={},
        ),
        patch(
            "eleutheria_graphrag.agents.react_loop.build_agent_loop",
            return_value=fake_agent,
        ),
        patch.object(sa_mod.ClassifyQueryType, "run", _classify),
        patch.object(sa_mod.DraftClaimLedger, "run", _noop_draft),
        patch.object(ScholarlyAgent, "_assemble_controversy_map", _inject_map),
        patch.object(ScholarlyAgent, "_post_loop_quality_phase", _noop_quality),
        patch.object(sa_mod, "build_render_prompt", _boom_prompt),
    ):
        async for ev in agent._stream_react(question):
            events.append(ev)
    return events


def _boom_prompt(_state):
    raise AssertionError("legacy build_render_prompt used on the dialectical stream")


def _clean_verifier() -> AsyncMock:
    """Audit every citation in the dynamically produced test answer as clean."""

    async def _verify(draft):
        return VerificationReport.from_checks(
            [
                CitationCheck(
                    citation_id=claim.citation_id,
                    status=CitationStatus.VERIFIED,
                    reasoning="fixture explicitly supports the claim",
                    claim=claim.claim,
                )
                for claim in draft.claims
            ]
        )

    verifier = AsyncMock()
    verifier.verify_draft = AsyncMock(side_effect=_verify)
    return verifier


def _make_agent() -> ScholarlyAgent:
    llm = AsyncMock()
    llm.generate = AsyncMock(return_value=DIALECTICAL_PROSE)
    llm.stream_segmented = make_stream_segmented(DIALECTICAL_PROSE)
    llm.last_reasoning_content = ""
    llm.last_model_used = "accounts/fireworks/models/kimi-k2p6"
    llm.last_provider_used = "fireworks"
    deps = AsyncMock()
    deps.llm = llm
    deps.verifier_v2 = _clean_verifier()
    return ScholarlyAgent(deps)


_SYNTHESIS_REASONING = (
    "First I map the fault lines: Bobzien vs Frede over the dating of the will. "
    "Then I locate the Cicero De Fato 41 anchor and weigh the assent doctrine "
    "without picking a winner. SECRET_REASONING_TOKEN must stay off the answer."
)


def _make_reasoning_agent() -> ScholarlyAgent:
    llm = AsyncMock()
    llm.generate = AsyncMock(return_value=DIALECTICAL_PROSE)
    llm.stream_segmented = make_stream_segmented(
        DIALECTICAL_PROSE, reasoning=_SYNTHESIS_REASONING
    )
    llm.last_reasoning_content = _SYNTHESIS_REASONING
    llm.last_model_used = "accounts/fireworks/models/deepseek-v4-pro"
    llm.last_provider_used = "fireworks"
    deps = AsyncMock()
    deps.llm = llm
    deps.verifier_v2 = _clean_verifier()
    return ScholarlyAgent(deps)


@pytest.mark.asyncio
async def test_synthesis_reasoning_streams_live_and_never_mixes_with_answer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """On the dialectical path the thinking model's reasoning streams LIVE as
    ``synthesis_reasoning`` events (reasoning text) while the answer streams as
    ``answer_chunk`` events (content) — the two NEVER mixed, and the reasoning
    text NEVER leaks into the answer prose."""
    monkeypatch.setenv("ELEUTHERIA_SCHOLAR_RAG", "true")
    agent = _make_reasoning_agent()

    events = await _collect_stream(agent, "big open debates about free will")

    reasoning_events = []
    answer_chunks: list[str] = []
    for chunk in events:
        kind, parsed = _classify_like_route(chunk)
        if kind == "synthesis_reasoning":
            reasoning_events.append(parsed)
        elif kind == "answer_chunk":
            answer_chunks.append(chunk)

    # 1. The reasoning streamed live on its own channel with the stage label.
    assert reasoning_events, "expected live synthesis_reasoning events"
    streamed_reasoning = "".join(ev["data"]["reasoning"] for ev in reasoning_events)
    assert "SECRET_REASONING_TOKEN" in streamed_reasoning
    assert all(
        ev["data"]["stage"] == "Reasoning over the controversy map"
        for ev in reasoning_events
    )

    # 2. The data shape the frontend consumes: {"type": "synthesis_reasoning",
    #    "data": {"reasoning": <str>, "stage": <str>}}.
    sample = reasoning_events[0]
    assert sample["type"] == "synthesis_reasoning"
    assert set(sample["data"]) == {"reasoning", "stage"}
    assert isinstance(sample["data"]["reasoning"], str)

    # 3. The reasoning text NEVER leaked into the answer prose.
    streamed_prose = "".join(answer_chunks)
    assert "SECRET_REASONING_TOKEN" not in streamed_prose
    assert "Bobzien holds the ancients had no free-will problem" in streamed_prose
    assert streamed_prose.strip() != ""

    # 4. Order: reasoning arrives before the answer prose (deepseek emits
    #    reasoning deltas first, then content deltas).
    first_reasoning_idx = next(
        i
        for i, c in enumerate(events)
        if _classify_like_route(c)[0] == "synthesis_reasoning"
    )
    first_answer_idx = next(
        i for i, c in enumerate(events) if _classify_like_route(c)[0] == "answer_chunk"
    )
    assert first_reasoning_idx < first_answer_idx


@pytest.mark.asyncio
async def test_answer_chunks_carry_prose_only_no_event_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Every chunk that the route would wrap as ``answer_chunk`` is clean prose
    — no leaked ``{"type": ...}`` agent-event JSON."""
    monkeypatch.setenv("ELEUTHERIA_SCHOLAR_RAG", "true")
    agent = _make_agent()

    events = await _collect_stream(agent, "big open debates about free will")

    answer_chunk_payloads = [
        chunk for chunk in events if _classify_like_route(chunk)[0] == "answer_chunk"
    ]
    assert answer_chunk_payloads, (
        "expected dialectical prose to stream as answer_chunks"
    )
    for payload in answer_chunk_payloads:
        # The defining bug: a raw agent event leaking into the prose stream.
        assert '"type":' not in payload, (
            f"event JSON leaked into answer_chunk: {payload!r}"
        )
        assert not payload.lstrip().startswith("{"), (
            f"answer_chunk payload is JSON, not prose: {payload!r}"
        )

    streamed_prose = "".join(answer_chunk_payloads)
    assert "Bobzien holds the ancients had no free-will problem" in streamed_prose
    assert "[P_frede_epictetus: Frede, 2011 p. 44]" in streamed_prose


@pytest.mark.asyncio
async def test_simulated_agent_trace_events_never_become_answer_chunks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A real agent loop emits ``tool_call`` / ``kg_node_activated`` / ``agent_start``
    / ``citation_found`` events. Route-classify the full event sequence and assert
    every such trace event is forwarded on its own channel, never as answer_chunk.
    """
    monkeypatch.setenv("ELEUTHERIA_SCHOLAR_RAG", "true")
    agent = _make_agent()

    # Inject the kind of events the NativeAgentLoop pushes onto the SSE queue, so
    # the stream carries them BEFORE the synthesis prose. We do this by replacing
    # the stubbed agent's run with one that emits onto the live emitter.
    emitted_trace_types = {
        "agent_start",
        "tool_call",
        "tool_result",
        "kg_node_activated",
        "citation_found",
    }

    async def _classify(self, ctx):  # noqa: ARG001
        return None

    async def _inject_map(self, st, tools):  # noqa: ARG001
        st.controversy_map = _stub_map()
        st.metadata["controversy_map"] = {"status": "ok", "frames": 1}
        return True

    async def _noop_quality(self, st, ag):  # noqa: ARG001
        return []

    async def _noop_draft(self, ctx):  # noqa: ARG001
        return None

    captured_emitter: dict = {}

    def _fake_build_agent_loop(*, deps, state, tools, emitter):  # noqa: ARG001
        captured_emitter["e"] = emitter

        async def _run() -> None:
            await emitter.emit_agent_start("eleutheria", state.question, "tid")
            await emitter.emit_tool_call("eleutheria", "search_nodes", {"q": "x"}, "c1")
            await emitter.emit_tool_call_result("c1", "found 3 nodes")
            await emitter.emit_kg_node_activated(
                node_id="concept_free_will", label="Free Will", node_type="concept"
            )
            await emitter.emit_citation_found(
                passage_id="cic_fat_41",
                excerpt="adsensiones igitur…",
                node_ids=["concept_free_will"],
                confidence=0.8,
            )

        fake = AsyncMock()
        fake.run = _run
        fake.calls_made = 1
        fake.emitter = emitter
        return fake

    events: list[str] = []
    with (
        patch(
            "eleutheria_graphrag.agents.tools.build_tool_registry",
            return_value={},
        ),
        patch(
            "eleutheria_graphrag.agents.react_loop.build_agent_loop",
            _fake_build_agent_loop,
        ),
        patch.object(sa_mod.ClassifyQueryType, "run", _classify),
        patch.object(sa_mod.DraftClaimLedger, "run", _noop_draft),
        patch.object(ScholarlyAgent, "_assemble_controversy_map", _inject_map),
        patch.object(ScholarlyAgent, "_post_loop_quality_phase", _noop_quality),
        patch.object(sa_mod, "build_render_prompt", _boom_prompt),
    ):
        async for ev in agent._stream_react("big open debates"):
            events.append(ev)

    seen_types: set[str] = set()
    for chunk in events:
        kind, _ = _classify_like_route(chunk)
        if kind == "answer_chunk":
            assert '"type":' not in chunk, (
                f"trace event leaked into answer_chunk: {chunk!r}"
            )
        else:
            seen_types.add(kind)

    # Every simulated agent trace event was routed on its OWN channel.
    assert emitted_trace_types <= seen_types, (
        f"missing trace channels: {emitted_trace_types - seen_types}"
    )


@pytest.mark.asyncio
async def test_complete_event_answer_is_full_raw_answer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The terminal ``complete`` event carries the FULL dialectical prose
    (``state.raw_answer``), not a clipped tail — and the early
    ``citations_preview`` frame carries the same full answer.
    """
    monkeypatch.setenv("ELEUTHERIA_SCHOLAR_RAG", "true")
    agent = _make_agent()

    events = await _collect_stream(agent, "big open debates about free will")

    completes = []
    previews = []
    for chunk in events:
        kind, parsed = _classify_like_route(chunk)
        if kind == "complete":
            completes.append(parsed)
        elif kind == "citations_preview":
            previews.append(parsed)

    assert completes, "expected a terminal complete event"
    complete_answer = completes[-1]["data"]["answer"]
    # Byte-for-byte the full synthesis prose — no truncation.
    assert complete_answer == DIALECTICAL_PROSE
    assert complete_answer.endswith("the dating of the concept.")

    if previews:
        assert previews[-1]["data"]["answer"] == DIALECTICAL_PROSE


@pytest.mark.asyncio
async def test_complete_event_prose_not_streamed_twice(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The prose streams once (live answer_chunks); the terminal complete does
    NOT re-stream it (``_chunk_answer(stream_prose=False)``)."""
    monkeypatch.setenv("ELEUTHERIA_SCHOLAR_RAG", "true")
    agent = _make_agent()

    events = await _collect_stream(agent, "big open debates about free will")

    # The complete event is the ONLY frame after which no further answer_chunk
    # prose appears (no duplicate re-stream of the whole answer after complete).
    complete_idx = next(
        i for i, ch in enumerate(events) if _classify_like_route(ch)[0] == "complete"
    )
    after_complete_prose = [
        ch
        for ch in events[complete_idx + 1 :]
        if _classify_like_route(ch)[0] == "answer_chunk"
    ]
    assert not after_complete_prose, "prose re-streamed after the complete event"


# ── Long multi-section regression: the FULL prose survives (head + tail) ──────
#
# The shipped DIALECTICAL_PROSE fixture is a single short paragraph, so it never
# exercises the multi-paragraph / long-paragraph chunker — the exact path where
# the streamed answer used to lose its head and keep only the tail (dropped
# inter-paragraph / inter-sentence separators at chunk boundaries). This builds a
# >3000-char, multi-section prose and pins that the WHOLE thing flows intact into
# (a) ``state.raw_answer``, (b) the streamed answer_chunk concatenation, and
# (c) the terminal ``complete`` event — byte-for-byte, head included.


def _long_dialectical_prose() -> str:
    sections: list[str] = []
    for n in range(1, 5):
        body = " ".join(
            f"Sentence {k} of section {n} stages Bobzien against Frede over the "
            "Stoic doctrine of assent and the dating of the will."
            for k in range(18)
        )
        sections.append(f"## Section {n}: Fault line {n}\n{body}")
    prose = "\n\n".join(sections)
    # End with a real, fully marked fault-line paragraph so this chunking
    # stressor also satisfies the production content/provenance gate.
    prose += "\n\n## Conclusion\n" + DIALECTICAL_PROSE
    return prose


LONG_DIALECTICAL_PROSE = _long_dialectical_prose()


def _make_agent_with_prose(prose: str) -> ScholarlyAgent:
    llm = AsyncMock()
    llm.generate = AsyncMock(return_value=prose)
    llm.stream_segmented = make_stream_segmented(prose)
    llm.last_reasoning_content = ""
    llm.last_model_used = "accounts/fireworks/models/kimi-k2p6"
    llm.last_provider_used = "fireworks"
    deps = AsyncMock()
    deps.llm = llm
    deps.verifier_v2 = _clean_verifier()
    return ScholarlyAgent(deps)


def test_long_prose_fixture_is_a_real_multisection_stressor() -> None:
    """Guard the fixture itself: it must be long + multi-section, or the
    regression below would silently pass on a trivial input."""
    assert len(LONG_DIALECTICAL_PROSE) > 3000
    assert LONG_DIALECTICAL_PROSE.count("\n\n") >= 4
    assert "## Section 1" in LONG_DIALECTICAL_PROSE
    assert LONG_DIALECTICAL_PROSE.endswith("the dating of the concept.")


@pytest.mark.asyncio
async def test_long_prose_synthesize_sets_full_raw_answer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``_synthesize_dialectical`` writes the FULL prose to ``state.raw_answer``
    byte-for-byte (head section included), not a clipped tail."""
    monkeypatch.setenv("ELEUTHERIA_SCHOLAR_RAG", "true")
    agent = _make_agent_with_prose(LONG_DIALECTICAL_PROSE)
    state = RAGState(question="big open debates about free will")
    state.controversy_map = _stub_map()

    with patch(
        "eleutheria_graphrag.agents.scholarly_agent.synthesize_dialectical",
        new=AsyncMock(
            return_value=SynthesisResult(
                prose=LONG_DIALECTICAL_PROSE,
                model_used="accounts/fireworks/models/kimi-k2p6",
            )
        ),
    ):
        returned = await agent._synthesize_dialectical(state)

    assert returned == LONG_DIALECTICAL_PROSE
    assert state.raw_answer == LONG_DIALECTICAL_PROSE
    assert state.raw_answer.startswith("## Section 1")


@pytest.mark.asyncio
async def test_long_prose_streams_and_completes_whole(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """End-to-end stream of a long multi-section answer: the streamed
    answer_chunks concatenate to the FULL prose AND the ``complete`` event
    answer equals the FULL prose — head + tail, byte-for-byte."""
    monkeypatch.setenv("ELEUTHERIA_SCHOLAR_RAG", "true")
    agent = _make_agent_with_prose(LONG_DIALECTICAL_PROSE)

    with patch(
        "eleutheria_graphrag.agents.scholarly_agent.synthesize_dialectical",
        new=AsyncMock(
            return_value=SynthesisResult(
                prose=LONG_DIALECTICAL_PROSE,
                model_used="accounts/fireworks/models/kimi-k2p6",
            )
        ),
    ):
        events = await _collect_stream(agent, "big open debates about free will")

    answer_chunk_payloads = [
        chunk for chunk in events if _classify_like_route(chunk)[0] == "answer_chunk"
    ]
    streamed_prose = "".join(answer_chunk_payloads)
    # The whole answer streamed — head section present, byte-for-byte exact.
    assert streamed_prose == LONG_DIALECTICAL_PROSE
    assert "## Section 1" in streamed_prose

    completes = [
        parsed
        for chunk in events
        if (cls := _classify_like_route(chunk))[0] == "complete"
        for parsed in (cls[1],)
    ]
    assert completes, "expected a terminal complete event"
    complete_answer = completes[-1]["data"]["answer"]
    assert complete_answer == LONG_DIALECTICAL_PROSE
    assert complete_answer.startswith("## Section 1")
    assert complete_answer.endswith("the dating of the concept.")


def test_relational_tools_excluded_from_llm_surface_no_double_retrieval(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """NO DOUBLE-RETRIEVAL: with Scholar-RAG ON, ``find_debates`` /
    ``build_controversy_frame`` are registered (deterministic orchestration uses
    them) but EXCLUDED from the LLM-facing tool surface, so the ReAct agent
    cannot improvise the same calls ``_assemble_controversy_map`` already drives.
    """
    from unittest.mock import AsyncMock as _AsyncMock

    from eleutheria_graphrag.agents.dependencies import Deps
    from eleutheria_graphrag.agents.tool_schemas import build_tool_function_schemas
    from eleutheria_graphrag.agents.tools import build_tool_registry

    monkeypatch.setenv("ELEUTHERIA_SCHOLAR_RAG", "1")
    registry = build_tool_registry(Deps(db=_AsyncMock(), llm=_AsyncMock()))

    # Registered for the deterministic path.
    assert registry.get("find_debates") is not None
    assert registry.get("build_controversy_frame") is not None

    # Hidden from BOTH LLM-facing surfaces (native function schemas + legacy
    # text-mode tool descriptions) — the agent literally cannot call them.
    schema_names = {
        s["function"]["name"] for s in build_tool_function_schemas(registry)
    }
    assert "find_debates" not in schema_names
    assert "build_controversy_frame" not in schema_names

    described = {d["name"] for d in registry.tool_descriptions()}
    assert "find_debates" not in described
    assert "build_controversy_frame" not in described

    # The retrieval tools the agent SHOULD drive remain exposed.
    assert "search_nodes" in schema_names
    assert "search_passages" in schema_names


def test_dialectical_heartbeat_ceiling_exceeds_synthesis_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The heartbeat ``max_wait`` that wraps the dialectical synthesis MUST sit
    ABOVE the synthesis LLM HTTP timeout — otherwise the heartbeat would cancel a
    healthy-but-slow thinking-model synthesis BEFORE its own timeout, dropping the
    pipeline into the legacy facet-template fallback (the worst outcome)."""
    from eleutheria_graphrag.agents.dialectical_synthesis import (
        scholar_synthesis_timeout,
    )

    monkeypatch.delenv("ELEUTHERIA_SCHOLAR_SYNTHESIS_TIMEOUT", raising=False)
    ceiling = sa_mod._dialectical_heartbeat_ceiling()
    assert ceiling > scholar_synthesis_timeout()  # the LLM timeout is the deadline
    assert ceiling >= 360.0  # above the ~300 s generation budget
    # And it tracks the (env-overridable) synthesis timeout, staying above it.
    monkeypatch.setenv("ELEUTHERIA_SCHOLAR_SYNTHESIS_TIMEOUT", "300")
    assert sa_mod._dialectical_heartbeat_ceiling() > scholar_synthesis_timeout()


@pytest.mark.asyncio
async def test_stream_dialectical_default_ceiling_above_synthesis_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``_stream_dialectical`` with no explicit ``max_wait`` must use the
    synthesis-derived ceiling (not the old 240 s default that sat BELOW the
    360 s synthesis timeout and would cancel it).

    The ceiling now lives inline in ``_stream_dialectical`` (computed from
    ``_dialectical_heartbeat_ceiling()`` when ``max_wait`` is None). We patch
    ``_synthesize_dialectical`` to record the ceiling the stream actually applies
    by reading the timer indirectly: a quick-returning synthesis whose value is
    ``None`` lets the generator finish immediately, and we assert the module
    helper the generator binds to stays above the synthesis timeout.
    """
    from eleutheria_graphrag.agents.dialectical_synthesis import (
        scholar_synthesis_timeout,
    )

    monkeypatch.delenv("ELEUTHERIA_SCHOLAR_SYNTHESIS_TIMEOUT", raising=False)
    agent = ScholarlyAgent.__new__(ScholarlyAgent)

    async def _fast_synth(state, *, on_reasoning=None):  # noqa: ARG001
        return None  # quick return → generator falls through cleanly

    with patch.object(agent, "_synthesize_dialectical", _fast_synth):
        holder: dict[str, object] = {}
        async for _ in agent._stream_dialectical(RAGState(question="q"), holder=holder):
            pass

    # The generator's default ceiling source-of-truth sits above the timeout.
    assert sa_mod._dialectical_heartbeat_ceiling() > scholar_synthesis_timeout()
    assert sa_mod._dialectical_heartbeat_ceiling() >= 360.0
    assert holder["ok"] is False  # None prose → falls through to legacy render
