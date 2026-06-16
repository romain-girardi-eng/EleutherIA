"""Tests for the Scholar-RAG M4 dialectical synthesis (the cutover core).

Covers:
- ``serialize_controversy_map`` emitting the ``## QUESTION`` header over the M3
  edge-first frame layer (first-class ``A --opposes--> B`` rows, bilingual untruncated
  passages), with shape + coverage gaps.
- ``synthesize_dialectical`` assembling the prompt and running end-to-end over a
  hand-built ControversyMap with a STUBBED LLM — NOT the facet template — and
  emitting a provenance ledger parsed from the prose.
- ``build_provenance_ledger`` resolving real markers to SUPPORTED items and
  hallucinated ids to UNVERIFIED.
- ``passes_content_gate`` (content gate, not a char floor) accepting grounded prose
  and rejecting the dead template / ungrounded prose.
- ``synthesize_degraded`` producing a prose hedge, never a node-paste.
- ``resolve_scholar_synthesis_model`` staying Fireworks-only.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock

import pytest

from eleutheria_graphrag.agents.dialectical_synthesis import (
    DIALECTICAL_SYNTHESIS_SYSTEM,
    DIALECTICAL_SYNTHESIS_TEMPLATE,
    SynthesisResult,
    build_provenance_ledger,
    deterministic_map_hedge,
    format_scholar_reference,
    model_separates_reasoning,
    passes_content_gate,
    resolve_scholar_synthesis_model,
    scholar_render_max_tokens,
    scholar_synthesis_fallback_chain,
    scholar_synthesis_timeout,
    scholar_tool_call_budget,
    serialize_controversy_map,
    strip_reasoning_leak,
    synthesize_degraded,
    synthesize_dialectical,
    synthesize_dialectical_stream,
)
from eleutheria_graphrag.agents.state import (
    AnswerShape,
    ClaimStatus,
    ControversyFrame,
    ControversyMap,
    DialecticalLink,
    FrameCompleteness,
    GroundedPosition,
    PassageRef,
)

# ── fixtures ─────────────────────────────────────────────────────────────────


def _map() -> ControversyMap:
    """A two-position, one-edge, one-passage controversy frame on the will-origin."""
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


# ── serialiser ───────────────────────────────────────────────────────────────


def test_serialize_emits_question_header_and_shape() -> None:
    md = serialize_controversy_map(_map())
    assert md.startswith("## QUESTION")
    assert "What are the big open debates" in md
    assert "survey_of_debates" in md


def test_serialize_emits_first_class_edge_row() -> None:
    md = serialize_controversy_map(_map())
    # the M3 edge-first layer: a literal A --opposes--> B row (F2 fix)
    assert "--opposes-->" in md
    assert "P_bobzien_no_problem" in md and "P_frede_epictetus" in md


def test_serialize_emits_bilingual_untruncated_passage() -> None:
    md = serialize_controversy_map(_map())
    assert "passage_cic_fat_41" in md
    assert "adsensiones igitur, quas prius docui..." in md  # original, untruncated
    assert "Assent, then, which I explained earlier..." in md  # english


def test_serialize_includes_coverage_gaps() -> None:
    cmap = _map()
    cmap.coverage_gaps = ["Stoic compatibilism frame thinly retrieved"]
    md = serialize_controversy_map(cmap)
    assert "Coverage Gaps" in md
    assert "Stoic compatibilism frame thinly retrieved" in md


# ── provenance ledger (byproduct of prose) ───────────────────────────────────


def test_ledger_resolves_real_markers_to_supported() -> None:
    prose = (
        "Bobzien argues the ancients lacked the concept "
        "[P_bobzien_no_problem: Bobzien, 1998 p. 330]. "
        "Cicero records the Stoic view "
        "[passage_cic_fat_41: Cicero, De Fato 41]. "
        "These positions clash [edge: opposes P_bobzien_no_problem->P_frede_epictetus]."
    )
    ledger = build_provenance_ledger(prose, _map())
    assert len(ledger) == 3
    assert all(item.status == ClaimStatus.SUPPORTED for item in ledger)
    passage_items = [i for i in ledger if i.support_type == "passage"]
    assert passage_items and passage_items[0].quote_original.startswith("adsensiones")
    assert passage_items[0].evidence_class == "assertion"


def test_ledger_marks_hallucinated_id_unverified() -> None:
    prose = "An invented claim [P_does_not_exist: Nobody, 2099 p. 1]."
    ledger = build_provenance_ledger(prose, _map())
    assert len(ledger) == 1
    assert ledger[0].status == ClaimStatus.UNVERIFIED
    assert ledger[0].confidence == 0.0


def test_ledger_empty_for_unmarked_prose() -> None:
    assert build_provenance_ledger("No markers here at all.", _map()) == []


# ── content gate (replaces the ~10k-char floor) ──────────────────────────────


def test_content_gate_accepts_grounded_prose() -> None:
    prose = (
        "They disagree [edge: opposes P_a->P_b]. "
        "Cicero attests it [passage_cic_fat_41: Cicero, De Fato 41]."
    )
    assert passes_content_gate(prose, _map()) is True


def test_content_gate_accepts_arrow_edge_form() -> None:
    prose = (
        "Bobzien --opposes--> Frede on the will. "
        "The text is [passage_cic_fat_41: Cicero, De Fato 41]."
    )
    assert passes_content_gate(prose, _map()) is True


def test_content_gate_rejects_no_primary_cite() -> None:
    prose = "They disagree [edge: opposes P_a->P_b], but no passage is cited."
    assert passes_content_gate(prose, _map()) is False


def test_content_gate_rejects_dead_template_string() -> None:
    prose = (
        "Definition: Free will frames the issue as a problem "
        "[edge: opposes P_a->P_b] [passage_cic_fat_41: Cicero, De Fato 41]."
    )
    assert passes_content_gate(prose, _map()) is False


def test_content_gate_rejects_empty() -> None:
    assert passes_content_gate("   ", _map()) is False


def test_content_gate_rejects_fabricated_passage_id() -> None:
    # the gate is map-aware: a passage marker that does NOT resolve to cmap fails.
    prose = (
        "They disagree [edge: opposes P_a->P_b]. "
        "Invented citation [passage_not_in_map: Nobody, 0]."
    )
    assert passes_content_gate(prose, _map()) is False


# ── model resolution (Fireworks-only) ────────────────────────────────────────


def test_resolve_model_defaults_to_fireworks(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SCHOLAR_SYNTHESIS_MODEL", raising=False)
    # the synthesis runs on the true thinking model (clean answer in `content`)
    assert (
        resolve_scholar_synthesis_model() == "accounts/fireworks/models/deepseek-v4-pro"
    )


def test_resolve_model_ignores_moonshot_optin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Romain's constraint: Moonshot opt-in is NOT honoured until K2-thinking lands.
    monkeypatch.setenv("SCHOLAR_SYNTHESIS_MODEL", "moonshot:kimi-k2.7-code-highspeed")
    assert (
        resolve_scholar_synthesis_model() == "accounts/fireworks/models/deepseek-v4-pro"
    )


def test_resolve_model_accepts_fireworks_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "SCHOLAR_SYNTHESIS_MODEL", "fireworks:accounts/fireworks/models/kimi-k2p6"
    )
    assert resolve_scholar_synthesis_model() == "accounts/fireworks/models/kimi-k2p6"


# ── end-to-end synthesis with a stubbed LLM (NOT the template) ───────────────


@pytest.mark.asyncio
async def test_synthesize_dialectical_runs_end_to_end_with_stub() -> None:
    grounded_prose = (
        "The live debate turns on when, if ever, antiquity has a notion of will. "
        "Bobzien holds the ancients had no free-will problem "
        "[P_bobzien_no_problem: Bobzien, 1998 p. 330], whereas Frede dates the will "
        "to Epictetus [P_frede_epictetus: Frede, 2011 p. 44]; the two positions "
        "[edge: opposes P_bobzien_no_problem->P_frede_epictetus] argue over the "
        "Stoic doctrine of assent recorded at "
        "[passage_cic_fat_41: Cicero, De Fato 41]."
    )
    llm = AsyncMock()
    llm.generate.return_value = grounded_prose
    llm.last_model_used = "accounts/fireworks/models/deepseek-v4-pro"
    llm.last_reasoning_content = ""

    result = await synthesize_dialectical(state=None, cmap=_map(), llm=llm)

    assert isinstance(result, SynthesisResult)
    assert result.prose == grounded_prose
    assert result.model_used == "accounts/fireworks/models/deepseek-v4-pro"
    # the prose became a ledger (byproduct), not the other way round
    assert len(result.ledger) == 4
    assert all(i.status == ClaimStatus.SUPPORTED for i in result.ledger)

    # the call assembled the dialectical prompt — the map markdown + system role,
    # NOT a facet/render template, NOT a pre-built ledger_json
    call = llm.generate.call_args
    user_prompt = call.args[0] if call.args else call.kwargs["prompt"]
    assert "## QUESTION" in user_prompt
    assert "--opposes-->" in user_prompt
    assert "REASON" in user_prompt and "WRITE the scholarly answer" in user_prompt
    assert call.kwargs["system_prompt"] == DIALECTICAL_SYNTHESIS_SYSTEM
    assert call.kwargs["model_override"] == "accounts/fireworks/models/deepseek-v4-pro"
    # the answer comes from synthesis, not a template
    assert "frames the issue as" not in result.prose
    assert passes_content_gate(result.prose, _map())


@pytest.mark.asyncio
async def test_synthesize_dialectical_empty_on_llm_error() -> None:
    llm = AsyncMock()
    llm.generate.side_effect = RuntimeError("provider down")
    result = await synthesize_dialectical(state=None, cmap=_map(), llm=llm)
    assert result.prose == ""
    assert result.ledger == []


@pytest.mark.asyncio
async def test_synthesize_dialectical_emits_coverage_note() -> None:
    cmap = _map()
    cmap.coverage_gaps = ["Alexander libertarian frame thinly retrieved"]
    llm = AsyncMock()
    llm.generate.return_value = "prose"
    await synthesize_dialectical(state=None, cmap=cmap, llm=llm)
    call = llm.generate.call_args
    user_prompt = call.args[0] if call.args else call.kwargs["prompt"]
    assert "COVERAGE GAPS" in user_prompt
    assert "thinly retrieved" in user_prompt


@pytest.mark.asyncio
async def test_synthesize_dialectical_threads_deep_tier_from_state_plan() -> None:
    from eleutheria_graphrag.agents.state import ResearchPlan

    class _State:
        research_plan = ResearchPlan(budget_tier="deep")

    llm = AsyncMock()
    llm.generate.return_value = "prose"
    await synthesize_dialectical(state=_State(), cmap=_map(), llm=llm)
    # a deep plan routes to the thinking model (thinking_mode=True)
    assert llm.generate.call_args.kwargs["thinking_mode"] is True


# ── degraded mode (the reasoned hedge, never a paste) ────────────────────────


@pytest.mark.asyncio
async def test_synthesize_degraded_produces_prose_hedge() -> None:
    cmap = _map()
    cmap.coverage_gaps = ["only one fault line surfaced"]
    llm = AsyncMock()
    llm.generate.return_value = (
        "A short, honest hedge over the one frame that assembled."
    )
    out = await synthesize_degraded(cmap, llm)
    assert out == "A short, honest hedge over the one frame that assembled."
    call = llm.generate.call_args
    prompt = call.args[0] if call.args else call.kwargs["prompt"]
    # the degraded prompt is STILL the map + a hedge instruction, never a node-paste
    assert "## QUESTION" in prompt
    assert "scholar's hedge" in prompt
    assert "only one fault line surfaced" in prompt  # gaps stated in prose


@pytest.mark.asyncio
async def test_synthesize_degraded_empty_on_error() -> None:
    llm = AsyncMock()
    llm.generate.side_effect = RuntimeError("down")
    assert await synthesize_degraded(_map(), llm) == ""


# ── M6: fallback chain + flag-ON budget tiers (Fireworks-only) ───────────────


def test_fallback_chain_is_fireworks_then_gemini(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("SCHOLAR_SYNTHESIS_MODEL", raising=False)
    chain = scholar_synthesis_fallback_chain()
    # head = resolved Fireworks thinking default; NO Moonshot rung; gemini last resort
    assert chain[0] == "accounts/fireworks/models/deepseek-v4-pro"
    assert chain[-1] == "gemini-3.1-pro-preview"
    assert not any("moonshot" in m or "kimi-k2.7" in m for m in chain)
    assert len(chain) == len(set(chain))  # deduped


def test_fallback_chain_ignores_moonshot_optin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SCHOLAR_SYNTHESIS_MODEL", "moonshot:kimi-k2.7-code-highspeed")
    chain = scholar_synthesis_fallback_chain()
    assert chain[0] == "accounts/fireworks/models/deepseek-v4-pro"
    assert not any("moonshot" in m for m in chain)


@pytest.mark.asyncio
async def test_synthesize_falls_back_when_first_rung_fails() -> None:
    # first chain rung raises; the synthesis advances to the next rung.
    llm = AsyncMock()
    grounded = (
        "They clash [edge: opposes P_a->P_b] over Cicero "
        "[passage_cic_fat_41: Cicero, De Fato 41]."
    )
    llm.generate.side_effect = [RuntimeError("rung 1 down"), grounded]
    result = await synthesize_dialectical(state=None, cmap=_map(), llm=llm)
    assert result.prose == grounded
    assert llm.generate.await_count == 2  # advanced past the failed rung


def test_scholar_tool_call_budget_by_tier(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ELEUTHERIA_SCHOLAR_MAX_TOOL_CALLS", raising=False)
    assert scholar_tool_call_budget("quick") == 12
    assert scholar_tool_call_budget("standard") == 24
    assert scholar_tool_call_budget("deep") == 45  # survey/transmission


def test_scholar_tool_call_budget_env_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ELEUTHERIA_SCHOLAR_MAX_TOOL_CALLS", "60")
    assert scholar_tool_call_budget("quick") == 60


def test_scholar_render_max_tokens_by_tier(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ELEUTHERIA_SCHOLAR_RENDER_MAX_TOKENS", raising=False)
    # F4: per-tier defaults lifted so a reasoning-effort-bounded thinking run still
    # leaves an answer reserve (deepseek shares max_tokens reasoning/content).
    assert scholar_render_max_tokens("quick") == 9000
    assert scholar_render_max_tokens("standard") == 12000
    assert scholar_render_max_tokens("deep") == 14000  # >=5000 mandatory


def test_scholar_render_max_tokens_clamped(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ELEUTHERIA_SCHOLAR_RENDER_MAX_TOKENS", "1000")
    assert scholar_render_max_tokens("standard") == 8000  # clamped to raised floor


# ── synthesis timeout: a slow thinking model must NEVER hit the 120 s default ──


def test_scholar_synthesis_timeout_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ELEUTHERIA_SCHOLAR_SYNTHESIS_TIMEOUT", raising=False)
    # 360 s default — comfortably above the ~150-220 s deepseek-v4-pro run and the
    # ~300 s generation budget, and far above the shared 120 s client timeout that
    # used to cut a healthy synthesis into the facet-template fallback.
    assert scholar_synthesis_timeout() == 360.0
    assert scholar_synthesis_timeout() > 300.0
    assert scholar_synthesis_timeout() > 120.0


def test_scholar_synthesis_timeout_env_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ELEUTHERIA_SCHOLAR_SYNTHESIS_TIMEOUT", "300")
    assert scholar_synthesis_timeout() == 300.0


def test_scholar_synthesis_timeout_clamped(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ELEUTHERIA_SCHOLAR_SYNTHESIS_TIMEOUT", "30")
    assert scholar_synthesis_timeout() == 120.0  # clamped to floor
    monkeypatch.setenv("ELEUTHERIA_SCHOLAR_SYNTHESIS_TIMEOUT", "5000")
    assert scholar_synthesis_timeout() == 900.0  # clamped to ceiling


@pytest.mark.asyncio
async def test_synthesize_dialectical_threads_generous_request_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The deepseek synthesis call must pass the dedicated generous
    ``request_timeout`` so the underlying httpx 120 s client timeout can NEVER
    cancel a slow-but-healthy thinking-model synthesis into the template."""
    monkeypatch.delenv("ELEUTHERIA_SCHOLAR_SYNTHESIS_TIMEOUT", raising=False)
    llm = AsyncMock()
    llm.generate.return_value = "prose"
    llm.last_reasoning_content = ""
    await synthesize_dialectical(state=None, cmap=_map(), llm=llm)
    timeout = llm.generate.call_args.kwargs["request_timeout"]
    assert timeout == 360.0
    assert timeout > 120.0  # above the shared client timeout — the bug


@pytest.mark.asyncio
async def test_synthesize_dialectical_completes_under_slow_thinking_model() -> None:
    """A ~200 s-equivalent thinking-model synthesis must complete, not be cut.

    The stub LLM ``generate`` only returns AFTER asserting the caller granted a
    request_timeout that exceeds a 200 s generation — i.e. the call would have
    raised a ReadTimeout under the old 120 s default and dropped to the template.
    """

    async def _slow_generate(*_args: object, **kwargs: object) -> str:
        granted = kwargs["request_timeout"]
        assert isinstance(granted, float)
        # A 200 s-equivalent run only survives if the granted budget exceeds it.
        assert granted >= 200.0
        return (
            "Bobzien holds the ancients had no free-will problem "
            "[P_bobzien_no_problem: Bobzien, 1998 p. 330]; the assent doctrine is at "
            "[passage_cic_fat_41: Cicero, De Fato 41]."
        )

    llm = AsyncMock()
    llm.generate.side_effect = _slow_generate
    llm.last_reasoning_content = ""
    result = await synthesize_dialectical(state=None, cmap=_map(), llm=llm)
    assert result.prose  # synthesis produced prose — NOT cancelled to None
    assert "frames the issue as" not in result.prose


# ── scholar dialogue + completeness demanded by the prompt ───────────────────


def test_system_prompt_demands_named_scholar_dialogue() -> None:
    sys = DIALECTICAL_SYNTHESIS_SYSTEM.lower()
    # the answer must ENTER a dialogue with NAMED modern scholars (not just primary)
    assert "named modern scholar" in sys or "names a modern scholar" in sys
    assert "dialogue with other scholars" in sys
    # the scholar-citation form is documented, with year + publication + page
    assert "[p_<id>:" in sys
    assert "page" in sys


def test_system_prompt_forbids_meta_reasoning_leak() -> None:
    sys = DIALECTICAL_SYNTHESIS_SYSTEM.lower()
    assert "output only the finished scholarly prose" in sys
    assert "matches the text" in sys  # the exact leak phrase is banned
    assert "let's double-check" in sys or "let me check" in sys


def test_write_template_demands_complete_detailed_survey() -> None:
    tpl = DIALECTICAL_SYNTHESIS_TEMPLATE.lower()
    # completeness: every fault line, no frame skipped
    assert "every fault line" in tpl
    assert "cover all frames present" in tpl
    # detail / length: full, example-rich, long-form
    assert "example-rich" in tpl
    assert "long-form" in tpl
    assert "multiple" in tpl  # multiple examples per frame
    # explicit scholar-vs-scholar staging
    assert "contending modern scholars" in tpl
    # forbids planning / self-check text in the output
    assert "write only the essay" in tpl


# ── scholar reference formatter (citable modern scholarship) ─────────────────


def test_format_scholar_reference_full() -> None:
    pos = GroundedPosition(
        position_id="frede_epictetus",
        holder="Michael Frede",
        publication="Frede 2011, A Free Will",
        page_grounding="pp. 153-174",
    )
    assert (
        format_scholar_reference(pos)
        == "Michael Frede, Frede 2011, A Free Will, pp. 153-174"
    )


def test_format_scholar_reference_no_page_never_invents() -> None:
    pos = GroundedPosition(
        position_id="dihle_will",
        holder="Albrecht Dihle",
        publication="Dihle 1982",
    )
    ref = format_scholar_reference(pos)
    assert ref == "Albrecht Dihle, Dihle 1982"
    assert "p." not in ref  # no fabricated page


# ── provenance ledger carries the scholar reference for position items ───────


def test_position_ledger_item_carries_scholar_reference() -> None:
    prose = "Frede dates the will to Epictetus [P_frede_epictetus: Frede 2011 p. 44]."
    ledger = build_provenance_ledger(prose, _map())
    pos_items = [i for i in ledger if i.support_type == "position"]
    assert len(pos_items) == 1
    item = pos_items[0]
    assert item.status == ClaimStatus.SUPPORTED
    # quote_translation carries the formatted "<holder>, <pub>, <page>" reference
    assert item.quote_translation == "Frede, Frede 2011, p. 44"
    assert item.evidence_class == "attributed_position"


# ── defensive chain-of-thought stripper (the reasoning-leak post-clean) ──────


def test_strip_reasoning_leak_cuts_trailing_self_check() -> None:
    prose = (
        "Bobzien (1998: 330) argues the ancients had no free-will problem, "
        "whereas Frede (2011: 44) dates a notion of will to Epictetus.\n\n"
        "Let's double check the Greek quotes.\n"
        "Matches the text.\n"
        "Verified."
    )
    cleaned = strip_reasoning_leak(prose)
    assert "Bobzien (1998: 330)" in cleaned
    assert "Let's double check" not in cleaned
    assert "Matches the text" not in cleaned
    assert cleaned.strip().endswith("Epictetus.")


def test_strip_reasoning_leak_cuts_leading_preamble() -> None:
    prose = (
        "First, I will map the fault lines.\n"
        "Now let me write the answer.\n\n"
        "The liveliest dispute is whether antiquity had a concept of the will at all."
    )
    cleaned = strip_reasoning_leak(prose)
    assert cleaned.startswith("The liveliest dispute")
    assert "First, I will map" not in cleaned
    assert "Now let me write" not in cleaned


def test_strip_reasoning_leak_cuts_verification_heading_block() -> None:
    prose = (
        "Sharples (1983: 22) reads Alexander as a libertarian.\n\n"
        "## Verification\n"
        "Checking the Latin: matches.\n"
        "All citations resolve."
    )
    cleaned = strip_reasoning_leak(prose)
    assert "Sharples (1983: 22)" in cleaned
    assert "Verification" not in cleaned
    assert "All citations resolve" not in cleaned


def test_strip_reasoning_leak_preserves_real_prose() -> None:
    # a genuine scholarly sentence that merely contains "checks" is NOT a leak.
    prose = (
        "Bobzien checks the Chrysippean argument against the lazy-argument and "
        "finds it wanting [P_bobzien_no_problem: Bobzien 1998 p. 330]."
    )
    assert strip_reasoning_leak(prose) == prose


def test_synthesize_dialectical_strips_leak_from_prose() -> None:
    import asyncio

    grounded = (
        "Bobzien (1998: 330) holds the ancients lacked the concept "
        "[P_bobzien_no_problem: Bobzien 1998 p. 330], a passage at "
        "[passage_cic_fat_41: Cicero, De Fato 41] both sides invoke "
        "[edge: opposes P_bobzien_no_problem->P_frede_epictetus].\n\n"
        "Let me verify the Latin quote.\nMatches the text."
    )
    llm = AsyncMock()
    llm.generate.return_value = grounded
    # k2p6 is a NON-reasoning model that inlines its scratch into content, so the
    # defensive stripper MUST run here (it does not run for thinking models).
    llm.last_model_used = "accounts/fireworks/models/kimi-k2p6"
    llm.last_reasoning_content = ""
    result = asyncio.run(synthesize_dialectical(state=None, cmap=_map(), llm=llm))
    assert "Let me verify" not in result.prose
    assert "Matches the text" not in result.prose
    assert "Bobzien (1998: 330)" in result.prose


# ── thinking-model path: reasoning_content separated from the answer ──────────


def test_model_separates_reasoning_flags_thinking_models() -> None:
    assert model_separates_reasoning("accounts/fireworks/models/deepseek-v4-pro")
    assert model_separates_reasoning("accounts/fireworks/models/kimi-k2-thinking")
    # the non-reasoning instruct model still needs the defensive stripper
    assert not model_separates_reasoning("accounts/fireworks/models/kimi-k2p6")
    assert not model_separates_reasoning("gemini-3.1-pro-preview")
    assert not model_separates_reasoning("")


@pytest.mark.asyncio
async def test_synthesize_uses_content_only_excludes_reasoning_content() -> None:
    """A thinking model returns BOTH reasoning_content (scratch) + a clean content
    answer. The synthesized prose must be ``content`` ONLY; reasoning goes to the
    trace side-channel; the scholar path runs deepseek-v4-pro; strip does NOT run."""
    clean_answer = (
        "Bobzien (1998: 330) holds the ancients had no free-will problem "
        "[P_bobzien_no_problem: Bobzien 1998 p. 330], whereas Frede (2011: 44) dates "
        "the will to Epictetus [P_frede_epictetus: Frede 2011 p. 44]; the two clash "
        "[edge: opposes P_bobzien_no_problem->P_frede_epictetus] over Cicero "
        "[passage_cic_fat_41: Cicero, De Fato 41]."
    )
    # The model's private chain-of-thought — contains the EXACT phrases the
    # defensive stripper would cut if it (wrongly) ran on a clean answer. It must
    # never appear in the prose.
    reasoning_scratch = (
        "The user wants a survey. Let me check the Greek quotes. First, I will map "
        "the fault lines. Matches the text. Verified."
    )

    llm = AsyncMock()
    llm.generate.return_value = clean_answer  # content ONLY (reasoning is separate)
    llm.last_model_used = "accounts/fireworks/models/deepseek-v4-pro"
    llm.last_reasoning_content = reasoning_scratch

    result = await synthesize_dialectical(state=None, cmap=_map(), llm=llm)

    # 1. the answer is content ONLY — reasoning_content is excluded
    assert result.prose == clean_answer
    assert "The user wants" not in result.prose
    assert "Let me check" not in result.prose
    # 2. the scholar path resolved the deepseek-v4-pro thinking model
    assert result.model_used == "accounts/fireworks/models/deepseek-v4-pro"
    assert (
        llm.generate.call_args.kwargs["model_override"]
        == "accounts/fireworks/models/deepseek-v4-pro"
    )
    # 3. reasoning_content is routed to the trace side-channel, not the answer
    assert result.reasoning_trace == reasoning_scratch
    # 4. strip_reasoning_leak did NOT run on the clean answer (it would have cut
    #    the "Matches the text" / "First, I will" lines IF present — but they are
    #    only in reasoning, never in content). The answer is byte-for-byte intact.
    assert model_separates_reasoning(result.model_used) is True


# ── SYNTHESIS ROBUSTNESS: never-empty guarantee ──────────────────────────────
#
# Root cause: Fireworks deepseek-v4-pro shares max_tokens between reasoning_content
# and content; a long reasoning run eats the whole budget → finish_reason=length
# with ZERO content deltas → empty prose. The guarantees under test:
#   1. the streaming synthesis advances to the kimi-k2p7-code CONTENT rung (which
#      gives its whole budget to content) and returns NON-EMPTY prose;
#   2. synthesize_degraded resolves to kimi-k2p7-code (NOT deepseek), so the
#      safety-belt cannot empty the same budget-shared way;
#   3. deterministic_map_hedge yields non-empty grounded prose from a populated map
#      with NO LLM call at all (the absolute floor).


class _BudgetEatenThenContentLLM:
    """Stub LLM: the deepseek rung emits ONLY reasoning + empty content (finish
    reason 'length'); its answer-only re-call also empties; the kimi rung WRITES.

    No live LLM call. ``stream_segmented`` is the segmented stream the streaming
    synthesis drives; ``generate`` is the targeted answer-only re-call.
    """

    def __init__(self, kimi_answer: str) -> None:
        self._kimi_answer = kimi_answer
        self.last_reasoning_content = ""
        self.last_finish_reason = ""
        self.last_model_used = ""
        self.stream_calls: list[str] = []
        self.generate_calls: list[str] = []

    async def stream_segmented(
        self, _prompt: str, **kwargs: Any
    ) -> AsyncIterator[tuple[str, str]]:
        model_override = kwargs.get("model_override")
        self.stream_calls.append(model_override or "")
        self.last_model_used = model_override or ""
        # Mirror the real segmented stream: reset the reasoning side-channel and
        # finish_reason at the start of every call.
        self.last_reasoning_content = ""
        self.last_finish_reason = ""
        if model_override == "accounts/fireworks/models/deepseek-v4-pro":
            # Budget eaten by reasoning: reasoning deltas only, NO content, and the
            # stream truncated at max_tokens (finish_reason=length).
            for delta in (
                "Let me map the fault lines. ",
                "Weighing Bobzien vs Frede. ",
            ):
                self.last_reasoning_content += delta
                yield ("reasoning", delta)
            self.last_finish_reason = "length"
            return
        # The content (kimi) rung: gives its whole budget to content → real prose.
        self.last_finish_reason = "stop"
        for delta in (self._kimi_answer,):
            yield ("answer", delta)

    async def generate(self, _prompt: str, **kwargs: Any) -> str:
        # The answer-only re-call on the deepseek rung: it STILL empties here, so
        # the loop must advance to the kimi rung (the real guarantee).
        model_override = kwargs.get("model_override")
        self.generate_calls.append(model_override or "")
        self.last_model_used = model_override or ""
        return ""


@pytest.mark.asyncio
async def test_stream_never_empty_advances_to_content_rung_when_deepseek_only_reasons() -> (
    None
):
    """deepseek emits ONLY reasoning + empty content (finish_reason=length) and its
    answer-only re-call also empties; the streaming synthesis MUST advance to the
    kimi-k2p7-code content rung and return NON-EMPTY prose — never ''."""
    kimi_answer = (
        "The central fault line concerns whether antiquity possessed a concept of "
        "the will at all. Bobzien (1998: 330) holds the ancients had no free-will "
        "problem [P_bobzien_no_problem: Bobzien 1998 p. 330], reading the Stoic "
        "debate as one about fate and causation rather than a faculty of volition. "
        "Frede (2011: 44), by contrast, dates the emergence of the will to Epictetus "
        "[P_frede_epictetus: Frede 2011 p. 44], finding in prohairesis the first "
        "genuine theory of a self-determining will. The two readings clash directly "
        "[edge: opposes P_bobzien_no_problem->P_frede_epictetus] over how to construe "
        "Cicero's report of Stoic assent "
        "[passage_cic_fat_41: Cicero, De Fato 41], which each side mobilises for "
        "incompatible conclusions about the antiquity of the problem."
    )
    assert len(kimi_answer) >= 400  # a genuine finished answer, not 'too thin'
    llm = _BudgetEatenThenContentLLM(kimi_answer)

    result = await synthesize_dialectical_stream(state=None, cmap=_map(), llm=llm)

    # the guarantee: NON-EMPTY prose, sourced from the content rung
    assert result.prose == kimi_answer
    assert result.prose != ""
    assert result.model_used == "accounts/fireworks/models/kimi-k2p7-code"
    # the deepseek rung was tried (stream) AND its answer-only re-call fired before
    # advancing to kimi (the targeted recovery, then the content-rung guarantee)
    assert llm.stream_calls[0] == "accounts/fireworks/models/deepseek-v4-pro"
    assert llm.generate_calls == ["accounts/fireworks/models/deepseek-v4-pro"]
    assert "accounts/fireworks/models/kimi-k2p7-code" in llm.stream_calls


@pytest.mark.asyncio
async def test_degraded_uses_content_model_not_deepseek() -> None:
    """The safety-belt must NOT resolve to deepseek (which empties the same
    budget-shared way) — it uses the kimi-k2p7-code content model."""
    llm = AsyncMock()
    llm.generate.return_value = "A short, honest hedge over the assembled frames."
    await synthesize_degraded(_map(), llm)
    model_override = llm.generate.call_args.kwargs["model_override"]
    assert model_override == "accounts/fireworks/models/kimi-k2p7-code"
    assert model_override != "accounts/fireworks/models/deepseek-v4-pro"


def test_deterministic_map_hedge_is_non_empty_and_grounded() -> None:
    """The absolute floor: a populated map yields non-empty, attributed prose with
    resolvable inline markers and NO LLM call."""
    cmap = _map()
    hedge = deterministic_map_hedge(cmap)
    assert hedge  # NON-EMPTY for a populated map
    # carries the contending holders + their markers + the edge + the quoted passage
    assert "Bobzien" in hedge and "Frede" in hedge
    assert "[P_bobzien_no_problem" in hedge and "[P_frede_epictetus" in hedge
    assert "[edge: opposes P_bobzien_no_problem->P_frede_epictetus]" in hedge
    assert "[passage_cic_fat_41" in hedge
    assert "adsensiones igitur, quas prius docui..." in hedge  # quoted original
    # the prose-derived ledger resolves the markers (it is a real, indexable answer)
    ledger = build_provenance_ledger(hedge, cmap)
    assert any(
        i.support_type == "passage" and i.status == ClaimStatus.SUPPORTED
        for i in ledger
    )


def test_deterministic_map_hedge_empty_for_empty_map() -> None:
    """An empty map (no frames/positions/passages) yields '' so the caller can
    fall through to the legacy render (there is nothing to render)."""
    from eleutheria_graphrag.agents.state import AnswerShape as _Shape

    empty: Any = ControversyMap(
        question_frame="q?", shape=_Shape.SURVEY_OF_DEBATES, frames=[]
    )
    assert deterministic_map_hedge(empty) == ""
