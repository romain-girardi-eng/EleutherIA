"""Scholar-RAG M4 — the dialectical RENDER cutover (orchestrator seam).

The synthesis core (`synthesize_dialectical`) is unit-tested in
``tests/unit/test_dialectical_synthesis.py``. This file asserts the *wiring*: that
when ``ELEUTHERIA_SCHOLAR_RAG`` is ON and a ``ControversyMap`` assembled, the
ORCHESTRATOR's final answer prose comes from ``synthesize_dialectical`` over the
map — NOT the legacy ``DraftClaimLedger`` facet template / ``RenderGroundedAnswer``
/ ``_render_answer_fallback`` chain.

The regression bar (ARCHITECTURE §7.2, the anti-template fixture): the final
answer == the stubbed dialectical prose, contains NONE of the facet-template
strings ("frames the issue as" / "Textual Basis" / "Counterpoint and Nuance"),
and the legacy facet render was never invoked.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

import eleutheria_graphrag.agents.scholarly_agent as sa_mod
from eleutheria_graphrag.agents.scholarly_agent import ScholarlyAgent
from eleutheria_graphrag.agents.state import (
    AnswerShape,
    ControversyFrame,
    ControversyMap,
    DialecticalLink,
    FrameCompleteness,
    GroundedPosition,
    PassageRef,
    RAGState,
)

# The dialectical prose the stubbed synthesis LLM returns: cite-as-you-write with
# inline [P_*]/[passage_*]/[edge:*] markers, and NONE of the facet-template strings.
DIALECTICAL_PROSE = (
    "The liveliest dispute is not whether the ancients were free but whether they "
    "had the concept at all. Bobzien holds the ancients had no free-will problem "
    "[P_bobzien_no_problem: Bobzien, 1998 p. 330], whereas Frede dates a notion of "
    "will to Epictetus [P_frede_epictetus: Frede, 2011 p. 44]; the two positions "
    "[edge: opposes P_bobzien_no_problem->P_frede_epictetus] argue over the Stoic "
    "doctrine of assent recorded at [passage_cic_fat_41: Cicero, De Fato 41]. What "
    "remains genuinely open is the dating of the concept."
)

# The facet-template fingerprints that must NEVER appear in a flag-ON answer.
_TEMPLATE_FINGERPRINTS = (
    "frames the issue as",
    "Textual Basis",
    "Counterpoint and Nuance",
)


def _stub_map() -> ControversyMap:
    bobzien = GroundedPosition(
        position_id="bobzien_no_problem",
        holder="Bobzien",
        holder_node_id="scholar_position_bobzien_no_free_will_problem_ancients",
        holder_type="modern_scholar",
        claim="the ancients had no free-will problem",
        publication="Bobzien 1998",
        page_grounding="p. 330",
    )
    frede = GroundedPosition(
        position_id="frede_epictetus",
        holder="Frede",
        holder_node_id="scholar_position_frede_will_originates_epictetus",
        holder_type="modern_scholar",
        claim="the notion of will originates with Epictetus",
        publication="Frede 2011",
        page_grounding="p. 44",
    )
    passage = PassageRef(
        passage_id="cic_fat_41",
        work="De Fato",
        author="Cicero",
        canonical_ref="41",
        original_text="adsensiones igitur, quas prius docui...",
        english_text="Assent, then, which I explained earlier...",
        language="lat",
    )
    frame = ControversyFrame(
        frame_id="discovery_of_will",
        debate_node_id="debate_origins_notion_of_will_modern_paradigm",
        title="Discovery of the will",
        period="Imperial / modern reception",
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
        contested_passages=[passage],
        completeness=FrameCompleteness(
            has_two_sides=True, has_primary_grounding=True, incident_edge_count=1
        ),
    )
    cmap = ControversyMap(
        question_frame="What are the big open debates about free will in antiquity?",
        shape=AnswerShape.SURVEY_OF_DEBATES,
        frames=[frame],
    )
    cmap.provenance[passage.passage_id] = passage
    return cmap


async def _drive_run_react(agent: ScholarlyAgent, state: RAGState):
    """Drive ScholarlyAgent._run_react with the heavy phases stubbed out.

    Only the synthesis/render/verify tail is real — that is the cutover under
    test. The agent loop, controversy-map assembly (we inject the map directly),
    the post-loop quality gate, and DraftClaimLedger (the legacy generative
    pre-step) are no-ops here.
    """

    async def _inject_map(self, st, tools):  # noqa: ARG001
        st.controversy_map = _stub_map()
        return True

    async def _noop_quality(self, st, ag):  # noqa: ARG001
        return []

    async def _classify(self, ctx):  # noqa: ARG001
        return None

    async def _noop_draft(self, ctx):  # noqa: ARG001
        return None

    fake_agent = AsyncMock()
    fake_agent.run = AsyncMock(return_value=None)
    fake_agent.calls_made = 0
    fake_agent.evidence.primary_evidence = []
    fake_agent.evidence.secondary_evidence = []
    fake_agent.evidence.evidence_bundles = []

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
    ):
        return await agent._run_react(state)


@pytest.mark.asyncio
async def test_flag_on_final_answer_is_dialectical_prose_not_template(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ELEUTHERIA_SCHOLAR_RAG", "true")

    llm = AsyncMock()
    llm.generate = AsyncMock(return_value=DIALECTICAL_PROSE)
    llm.last_model_used = "accounts/fireworks/models/kimi-k2p6"
    llm.last_provider_used = "fireworks"
    deps = AsyncMock()
    deps.llm = llm
    deps.verifier_v2 = None

    state = RAGState(question="big open debates about free will in antiquity")
    agent = ScholarlyAgent(deps)

    # The legacy facet render must NEVER be invoked on the flag-ON path. Guard
    # both the LLM render node and the deterministic facet fallback.
    def _boom_fallback(_state):
        raise AssertionError("legacy facet fallback was used on the dialectical path")

    async def _boom_render(self, ctx):  # noqa: ARG001
        raise AssertionError("legacy RenderGroundedAnswer was used on dialectical path")

    with (
        patch.object(sa_mod, "_render_answer_fallback", _boom_fallback),
        patch.object(sa_mod.RenderGroundedAnswer, "run", _boom_render),
    ):
        answer = await _drive_run_react(agent, state)

    # 1. the final answer IS the dialectical prose
    assert answer.answer == DIALECTICAL_PROSE
    # 2. none of the facet-template fingerprints leaked in
    for fp in _TEMPLATE_FINGERPRINTS:
        assert fp not in answer.answer
    # 3. the synthesis LLM was called with the dialectical system prompt (not a render)
    from eleutheria_graphrag.agents.dialectical_synthesis import (
        DIALECTICAL_SYNTHESIS_SYSTEM,
    )

    assert llm.generate.await_count == 1
    assert (
        llm.generate.call_args.kwargs["system_prompt"] == DIALECTICAL_SYNTHESIS_SYSTEM
    )
    # 4. the answer carries the prose-derived provenance ledger (byproduct), and a
    #    passage citation resolved from the inline [passage_*] marker survives verify.
    assert state.metadata.get("render_answer_mode") == "dialectical"
    assert any(item.support_type == "passage" for item in answer.claim_ledger)
    assert any(c.id == "cic_fat_41" for c in answer.citations)


@pytest.mark.asyncio
async def test_flag_on_falls_back_to_legacy_when_synthesis_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Last-resort fallback: when BOTH the full dialectical synthesis AND the
    still-dialectical degraded hedge yield nothing (every LLM call empty), the
    legacy render runs (no crash). The degraded hedge is the safety belt; only
    when it too is empty does the legacy facet render become the last resort."""
    monkeypatch.setenv("ELEUTHERIA_SCHOLAR_RAG", "true")

    llm = AsyncMock()
    llm.generate = AsyncMock(return_value="")  # synthesis AND degraded hedge empty
    llm.last_model_used = "accounts/fireworks/models/kimi-k2p6"
    llm.last_provider_used = "fireworks"
    deps = AsyncMock()
    deps.llm = llm
    deps.verifier_v2 = None

    state = RAGState(question="big open debates about free will in antiquity")
    agent = ScholarlyAgent(deps)

    legacy_used = {"render": False}

    async def _legacy_render(self, ctx):  # noqa: ARG001
        legacy_used["render"] = True
        ctx.state.raw_answer = "LEGACY FACET RENDER OUTPUT"
        from eleutheria_graphrag.agents.graph_nodes import ProgrammaticVerify

        return ProgrammaticVerify()

    with patch.object(sa_mod.RenderGroundedAnswer, "run", _legacy_render):
        answer = await _drive_run_react(agent, state)

    # The legacy render WAS invoked (graceful fallback, no crash) and the answer
    # is NOT marked dialectical. (ProgrammaticVerify may then prune the unref'd
    # legacy stub prose to the insufficient-evidence message — that is the legacy
    # path doing its normal thing; what matters is we degraded to it.)
    assert legacy_used["render"] is True
    assert state.metadata.get("render_answer_mode") != "dialectical"
    assert isinstance(answer.answer, str)


@pytest.mark.asyncio
async def test_synthesis_failure_uses_degraded_hedge_not_facet_template(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """SAFETY BELT: when the full dialectical synthesis fails/empties, the still-
    dialectical degraded hedge over the ControversyMap is used — the legacy facet
    template ("frames the issue as") is NEVER reached."""
    monkeypatch.setenv("ELEUTHERIA_SCHOLAR_RAG", "true")

    # Same grounded markers as DIALECTICAL_PROSE so the hedge resolves a citation
    # and survives ProgrammaticVerify, but explicitly states a coverage limit.
    degraded_prose = (
        "Coverage was thin this run, so this is a hedge, not a survey. Bobzien holds "
        "the ancients had no free-will problem [P_bobzien_no_problem: Bobzien, 1998 "
        "p. 330], against Frede's dating of will to Epictetus [P_frede_epictetus: "
        "Frede, 2011 p. 44], with the assent doctrine at [passage_cic_fat_41: "
        "Cicero, De Fato 41]."
    )

    async def _generate(*args: object, **kwargs: object) -> str:
        # The full synthesis fails (empty on every rung); the degraded hedge —
        # whose prompt asks for a SHORT honest answer — returns grounded prose.
        prompt = args[0] if args else kwargs.get("prompt", "")
        if "SHORT, honest scholarly answer" in str(prompt):
            return degraded_prose
        return ""  # full synthesis: empty → triggers the safety belt

    llm = AsyncMock()
    llm.generate = AsyncMock(side_effect=_generate)
    llm.last_model_used = "accounts/fireworks/models/deepseek-v4-pro"
    llm.last_provider_used = "fireworks"
    llm.last_reasoning_content = ""
    deps = AsyncMock()
    deps.llm = llm
    deps.verifier_v2 = None

    state = RAGState(question="big open debates about free will in antiquity")
    agent = ScholarlyAgent(deps)

    def _boom_fallback(_state):
        raise AssertionError("legacy facet fallback used despite degraded hedge")

    async def _boom_render(self, ctx):  # noqa: ARG001
        raise AssertionError("legacy RenderGroundedAnswer used despite degraded hedge")

    with (
        patch.object(sa_mod, "_render_answer_fallback", _boom_fallback),
        patch.object(sa_mod.RenderGroundedAnswer, "run", _boom_render),
    ):
        answer = await _drive_run_react(agent, state)

    # The degraded hedge IS the answer — still dialectical, not the template.
    assert "hedge" in answer.answer.lower()
    for fp in _TEMPLATE_FINGERPRINTS:
        assert fp not in answer.answer
    assert state.metadata.get("render_answer_mode") == "dialectical"
    assert state.metadata.get("scholar_synthesis", {}).get("status") == "degraded"


@pytest.mark.asyncio
async def test_stream_render_emits_dialectical_prose_as_answer_chunks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The streaming render path emits the dialectical prose as answer_chunk
    strings (not the facet template), and never invokes the legacy stream render.
    """
    monkeypatch.setenv("ELEUTHERIA_SCHOLAR_RAG", "true")

    llm = AsyncMock()
    llm.generate = AsyncMock(return_value=DIALECTICAL_PROSE)
    llm.last_model_used = "accounts/fireworks/models/kimi-k2p6"
    deps = AsyncMock()
    deps.llm = llm

    state = RAGState(question="big open debates about free will in antiquity")
    state.controversy_map = _stub_map()
    agent = ScholarlyAgent(deps)

    def _boom_prompt(_state):
        raise AssertionError("legacy build_render_prompt used on dialectical stream")

    # _stream_render yields a mix of raw prose strings (answer_chunks) and JSON
    # status heartbeats. Collect the non-JSON pieces — that is the streamed prose.
    raw_chunks: list[str] = []
    with patch.object(sa_mod, "build_render_prompt", _boom_prompt):
        async for ev in agent._stream_render(state):
            if not ev.lstrip().startswith("{"):
                raw_chunks.append(ev)

    streamed = "".join(raw_chunks)
    # The dialectical prose streamed live as answer_chunks (chunked like the
    # legacy _chunk_answer; sentence-split can drop a single whitespace at a
    # chunk boundary — the same lossiness the legacy streamed path has). Assert
    # the substantive content + inline markers streamed, and that the
    # AUTHORITATIVE answer (state.raw_answer, carried by the terminal complete
    # event) is byte-for-byte the synthesis prose.
    assert "Bobzien holds the ancients had no free-will problem" in streamed
    assert "[P_frede_epictetus: Frede, 2011 p. 44]" in streamed
    assert "[edge: opposes P_bobzien_no_problem->P_frede_epictetus]" in streamed
    assert "[passage_cic_fat_41: Cicero, De Fato 41]" in streamed
    for fp in _TEMPLATE_FINGERPRINTS:
        assert fp not in streamed
    assert state.metadata.get("render_answer_mode") == "dialectical"
    assert state.raw_answer == DIALECTICAL_PROSE


def test_dialectical_citations_surface_modern_scholarship_as_citable() -> None:
    """The citation payload built from the prose includes NAMED MODERN SCHOLARS as
    first-class citable items (SECONDARY layer, scholar + work + page), not only
    ancient passages — so the frontend CitationGenerator can export them.
    """
    from eleutheria_graphrag.agents.dialectical_synthesis import (
        build_provenance_ledger,
    )
    from eleutheria_graphrag.agents.graph_nodes import _dialectical_citations
    from eleutheria_graphrag.agents.state import EvidenceLayer

    cmap = _stub_map()
    state = RAGState(question="q")
    state.controversy_map = cmap
    state.claim_ledger = build_provenance_ledger(DIALECTICAL_PROSE, cmap)
    state.metadata["render_answer_mode"] = "dialectical"

    citations = _dialectical_citations(state)

    primary = [c for c in citations if c.layer == EvidenceLayer.PRIMARY]
    secondary = [c for c in citations if c.layer == EvidenceLayer.SECONDARY]

    # ancient passage cited as PRIMARY
    assert any(c.id == "cic_fat_41" for c in primary)
    # BOTH named scholars cited as SECONDARY (modern scholarship), citable items
    assert len(secondary) >= 2
    sec_labels = " | ".join(c.label for c in secondary)
    assert "Bobzien" in sec_labels and "Bobzien 1998" in sec_labels
    assert "Frede" in sec_labels and "Frede 2011" in sec_labels
    # page grounding carried into the citable reference
    assert "p. 330" in sec_labels and "p. 44" in sec_labels
    # the scholar citations are node-typed, verified, and resolvable
    for c in secondary:
        assert c.type == "node"
        assert c.verified is True
        assert c.id  # holder/position node id present


def test_dialectical_answer_has_no_reasoning_leak_markers() -> None:
    """A stubbed synthesis whose prose carries a trailing self-check is cleaned
    before it becomes the answer — no reasoning-leak markers survive.
    """
    import asyncio

    from eleutheria_graphrag.agents.dialectical_synthesis import synthesize_dialectical

    leaky = (
        DIALECTICAL_PROSE + "\n\nLet's double check the Greek quotes.\n"
        "Matches the text.\nVerified."
    )
    llm = AsyncMock()
    llm.generate = AsyncMock(return_value=leaky)
    llm.last_model_used = "accounts/fireworks/models/kimi-k2p6"

    result = asyncio.run(
        synthesize_dialectical(state=None, cmap=_stub_map(), llm=llm)
    )
    for marker in ("Let's double check", "Matches the text", "Verified."):
        assert marker not in result.prose
    # the substantive scholarly prose survived intact
    assert "Bobzien holds the ancients had no free-will problem" in result.prose
