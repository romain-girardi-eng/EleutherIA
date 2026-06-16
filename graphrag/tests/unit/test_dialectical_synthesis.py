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

from unittest.mock import AsyncMock

import pytest

from eleutheria_graphrag.agents.dialectical_synthesis import (
    DIALECTICAL_SYNTHESIS_SYSTEM,
    DIALECTICAL_SYNTHESIS_TEMPLATE,
    SynthesisResult,
    build_provenance_ledger,
    format_scholar_reference,
    passes_content_gate,
    resolve_scholar_synthesis_model,
    scholar_render_max_tokens,
    scholar_synthesis_fallback_chain,
    scholar_tool_call_budget,
    serialize_controversy_map,
    strip_reasoning_leak,
    synthesize_degraded,
    synthesize_dialectical,
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
    assert resolve_scholar_synthesis_model() == "accounts/fireworks/models/kimi-k2p6"


def test_resolve_model_ignores_moonshot_optin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Romain's constraint: Moonshot opt-in is NOT honoured until M6 wires K2.7.
    monkeypatch.setenv("SCHOLAR_SYNTHESIS_MODEL", "moonshot:kimi-k2.7-code-highspeed")
    assert resolve_scholar_synthesis_model() == "accounts/fireworks/models/kimi-k2p6"


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
    llm.last_model_used = "accounts/fireworks/models/kimi-k2p6"

    result = await synthesize_dialectical(state=None, cmap=_map(), llm=llm)

    assert isinstance(result, SynthesisResult)
    assert result.prose == grounded_prose
    assert result.model_used == "accounts/fireworks/models/kimi-k2p6"
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
    assert call.kwargs["model_override"] == "accounts/fireworks/models/kimi-k2p6"
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
    # head = resolved Fireworks default; NO Moonshot rung; gemini is the last resort
    assert chain[0] == "accounts/fireworks/models/kimi-k2p6"
    assert chain[-1] == "gemini-3.1-pro-preview"
    assert not any("moonshot" in m or "kimi-k2.7" in m for m in chain)
    assert len(chain) == len(set(chain))  # deduped


def test_fallback_chain_ignores_moonshot_optin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SCHOLAR_SYNTHESIS_MODEL", "moonshot:kimi-k2.7-code-highspeed")
    chain = scholar_synthesis_fallback_chain()
    assert chain[0] == "accounts/fireworks/models/kimi-k2p6"
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
    assert scholar_render_max_tokens("quick") == 6000
    assert scholar_render_max_tokens("standard") == 8000
    assert scholar_render_max_tokens("deep") == 8000  # >=5000 mandatory


def test_scholar_render_max_tokens_clamped(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ELEUTHERIA_SCHOLAR_RENDER_MAX_TOKENS", "1000")
    assert scholar_render_max_tokens("standard") == 5000  # clamped to floor


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
    llm.last_model_used = "accounts/fireworks/models/kimi-k2p6"
    result = asyncio.run(synthesize_dialectical(state=None, cmap=_map(), llm=llm))
    assert "Let me verify" not in result.prose
    assert "Matches the text" not in result.prose
    assert "Bobzien (1998: 330)" in result.prose
