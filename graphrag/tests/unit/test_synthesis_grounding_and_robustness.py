"""Regression tests for F3 (synthesis grounding depth) + F4 (model robustness).

F3 — only ~1 primary passage reaches the prose despite hundreds in the corpus:
  - the per-frame contested-passage budget was raised (12 -> 18) and the cap on
    ``build_controversy_frame.max_passages`` lifted (12 -> 24), so MORE quotable
    Greek survives retrieval into the map;
  - ``_quotable_greek_lead`` reorders a frame's contested passages so passages
    carrying real Greek lead ahead of ``**Reference:**`` metadata-only blocks,
    surfacing >=2 quotable-Greek passages per dominant fault line at the top;
  - the synthesis prompt now MANDATES quoting the strongest primary passage per
    position (original + English), not just citing a locus.

F4 — deepseek-v4-pro shares ``max_tokens`` between reasoning_content and content,
emptying intermittently:
  - ``generate``/``stream_segmented`` forward a ``reasoning_effort`` cap into the
    Fireworks payload (verified honoured against the live API);
  - ``synthesize_dialectical`` passes ``scholar_reasoning_effort()`` (default
    "low") so the chain-of-thought cannot eat the whole budget;
  - ``SynthesisResult`` now carries fallback/recovery instrumentation so the
    fallback/hedge rate is observable per query.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest

from eleutheria_graphrag.agents.controversy_map import (
    _contested_passage_budget,
    assemble_controversy_map,
)
from eleutheria_graphrag.agents.dialectical_synthesis import (
    DIALECTICAL_SYNTHESIS_SYSTEM,
    DIALECTICAL_SYNTHESIS_TEMPLATE,
    scholar_reasoning_effort,
    scholar_render_max_tokens,
    synthesize_dialectical,
)
from eleutheria_graphrag.agents.state import (
    AnswerShape,
    ControversyFrame,
    ControversyMap,
    DialecticalLink,
    FrameCompleteness,
    GroundedPosition,
    PassageRef,
)
from eleutheria_graphrag.agents.tools.build_controversy_frame import (
    BuildControversyFrameTool,
)
from eleutheria_graphrag.services.llm_service import LLMService, ModelProvider

# ── F4: reasoning_effort threads into the Codex payload ──────────────────────


def test_codex_payload_carries_reasoning_effort_when_requested() -> None:
    """The Codex payload gains a top-level ``reasoning_effort`` (the verified
    knob) ONLY when the caller passes one — never otherwise."""
    config = {"model": "gpt-5.6-sol"}
    with_effort = LLMService._openai_compatible_payload(
        ModelProvider.CODEX,
        "prompt",
        "system",
        0.3,
        12000,
        config,
        reasoning_effort="low",
    )
    assert with_effort["reasoning_effort"] == "low"

    without = LLMService._openai_compatible_payload(
        ModelProvider.CODEX,
        "prompt",
        "system",
        0.3,
        12000,
        config,
    )
    assert "reasoning_effort" not in without


def test_claude_payload_omits_reasoning_effort() -> None:
    """Only the Codex proxy is verified to honour the knob."""
    payload = LLMService._openai_compatible_payload(
        ModelProvider.CLAUDE,
        "prompt",
        None,
        0.3,
        4096,
        {"model": "claude-opus-5"},
        reasoning_effort="high",
    )
    assert "reasoning_effort" not in payload
    assert "reasoning" not in payload


def test_scholar_reasoning_effort_defers_to_the_tier_by_default(
    monkeypatch: Any,
) -> None:
    """``None`` lets the LLMService synthesis tier decide (CODEX_REASONING_EFFORT,
    default "high" — full academic quality)."""
    monkeypatch.delenv("SCHOLAR_SYNTHESIS_REASONING_EFFORT", raising=False)
    assert scholar_reasoning_effort() is None


def test_scholar_reasoning_effort_env_override(monkeypatch: Any) -> None:
    monkeypatch.setenv("SCHOLAR_SYNTHESIS_REASONING_EFFORT", "medium")
    assert scholar_reasoning_effort() == "medium"


def test_scholar_reasoning_effort_invalid_is_ignored(monkeypatch: Any) -> None:
    monkeypatch.setenv("SCHOLAR_SYNTHESIS_REASONING_EFFORT", "ludicrous")
    assert scholar_reasoning_effort() is None


# ── F4: synthesize_dialectical passes the cap + records instrumentation ───────


def _two_position_map() -> ControversyMap:
    a = GroundedPosition(position_id="p_a", holder="Bobzien", claim="no problem")
    b = GroundedPosition(position_id="p_b", holder="Frede", claim="will originates")
    passage = PassageRef(
        passage_id="epict_diss_1_1",
        work="Discourses",
        author="Epictetus",
        canonical_ref="1.1",
        original_text="τῶν ὄντων τὰ μέν ἐστιν ἐφ' ἡμῖν",
        english_text="Of things some are in our power",
        language="grc",
    )
    frame = ControversyFrame(
        frame_id="will_origin",
        title="Origin of the will",
        positions=[a, b],
        links=[DialecticalLink(relation="opposes", from_id="p_a", to_id="p_b")],
        contested_passages=[passage],
        completeness=FrameCompleteness(
            has_two_sides=True, has_primary_grounding=True, incident_edge_count=1
        ),
    )
    return ControversyMap(
        question_frame="Where does the will originate?",
        shape=AnswerShape.SURVEY_OF_DEBATES,
        frames=[frame],
    )


@pytest.mark.asyncio
async def test_synthesize_passes_reasoning_effort_to_llm(monkeypatch: Any) -> None:
    """The synthesis call carries the reasoning-budget cap so the thinking head's
    chain-of-thought cannot eat the whole answer budget (F4)."""
    monkeypatch.setenv("SCHOLAR_SYNTHESIS_REASONING_EFFORT", "low")
    prose = (
        "Bobzien [P_p_a: Bobzien] and Frede [P_p_b: Frede] clash "
        "[edge: opposes P_p_a->P_p_b] over Epictetus "
        "[passage_epict_diss_1_1: Epictetus, Discourses 1.1]."
    )
    llm = AsyncMock()
    llm.generate.return_value = prose
    llm.last_model_used = "gpt-5.6-sol"
    llm.last_reasoning_content = ""

    result = await synthesize_dialectical(state=None, cmap=_two_position_map(), llm=llm)

    assert result.prose == prose
    call = llm.generate.call_args
    assert call.kwargs["reasoning_effort"] == "low"
    # primary head produced it: no fallback recorded
    assert result.rung_index == 0
    assert result.fell_back is False
    assert result.rungs_tried == 1


@pytest.mark.asyncio
async def test_synthesis_records_fallback_rung_instrumentation() -> None:
    """When the primary head empties and a later rung writes the prose, the
    SynthesisResult records WHICH rung fired (F4 observability)."""

    class _PrimaryEmptiesThenFallbackWrites:
        def __init__(self) -> None:
            self.last_model_used = ""
            self.last_reasoning_content = ""

        async def generate(self, _prompt: str, **kwargs: Any) -> str:
            model = kwargs.get("model_override") or ""
            self.last_model_used = model
            if model == "gpt-5.6-sol":
                return ""  # budget eaten by reasoning -> empty content
            return (
                "Bobzien [P_p_a: Bobzien] opposes Frede [P_p_b: Frede] "
                "[edge: opposes P_p_a->P_p_b] over "
                "[passage_epict_diss_1_1: Epictetus, Discourses 1.1]."
            )

    llm = _PrimaryEmptiesThenFallbackWrites()
    result = await synthesize_dialectical(state=None, cmap=_two_position_map(), llm=llm)

    assert result.prose != ""
    assert result.rung_index == 1  # the claude-opus-5 rung produced it
    assert result.fell_back is True
    assert result.rungs_tried == 2
    assert result.model_used == "claude-opus-5"


def test_render_max_tokens_raised_with_answer_reserve() -> None:
    """The render cap was lifted so a bounded reasoning run still leaves an
    answer reserve (F4)."""
    assert scholar_render_max_tokens("standard") >= 12000
    assert scholar_render_max_tokens("deep") >= 12000
    # clamp floor lifted to 8000
    assert scholar_render_max_tokens("quick") >= 8000


# ── F3: prompt mandates quoting the strongest primary passage per position ────


def test_prompt_mandates_quoting_strongest_primary_per_position() -> None:
    system = DIALECTICAL_SYNTHESIS_SYSTEM.lower()
    template = DIALECTICAL_SYNTHESIS_TEMPLATE.lower()
    # the prompt must require quoting (original + English), not just a locus
    assert "must quote the strongest" in system
    assert "insufficient" in system  # locus-only is insufficient
    assert "strongest" in template
    assert "do not just cite a locus" in template


# ── F3: budget raised + quotable-Greek leads in the frame ─────────────────────


def test_contested_passage_budget_raised() -> None:
    assert _contested_passage_budget() >= 18


def test_contested_passage_budget_env_override(monkeypatch: Any) -> None:
    monkeypatch.setenv("ELEUTHERIA_SCHOLAR_CONTESTED_BUDGET", "22")
    assert _contested_passage_budget() == 22
    monkeypatch.setenv("ELEUTHERIA_SCHOLAR_CONTESTED_BUDGET", "1000")
    assert _contested_passage_budget() == 24  # clamped


def test_quotable_greek_passages_lead_over_reference_blocks() -> None:
    """A frame's contested passages are reordered so quotable Greek leads ahead
    of ``**Reference:**`` metadata-only blocks (F3): the synthesis sees quotable
    text first and can quote >=2 distinct passages per fault line."""
    tool = BuildControversyFrameTool.__new__(BuildControversyFrameTool)
    ref_block = PassageRef(
        passage_id="meta_only",
        author="Epictetus",
        original_text="**Reference:** Diss. 1.1 **Author:** Epictetus **Work:** D",
        language="grc",
    )
    greek_1 = PassageRef(
        passage_id="grc_1",
        author="Epictetus",
        original_text="τῶν ὄντων τὰ μέν ἐστιν ἐφ' ἡμῖν, τὰ δὲ οὐκ ἐφ' ἡμῖν",
        language="grc",
    )
    greek_2 = PassageRef(
        passage_id="grc_2",
        author="Epictetus",
        original_text="ἐφ' ἡμῖν μὲν ὑπόληψις, ὁρμή, ὄρεξις, ἔκκλισις",
        language="grc",
    )
    # input order puts the metadata block FIRST (the regression: it would win the
    # quoting slot and dump markdown instead of Greek)
    reordered = tool._quotable_greek_lead([ref_block, greek_1, greek_2])

    ids = [p.passage_id for p in reordered]
    # both quotable-Greek passages must lead; the metadata block sinks last
    assert ids[0] in {"grc_1", "grc_2"}
    assert ids[1] in {"grc_1", "grc_2"}
    assert ids[-1] == "meta_only"
    # >=2 quotable-Greek passages available at the top of the dossier
    quotable_leads = [p for p in reordered[:2] if tool._ref_greek_quotable_chars(p) > 0]
    assert len(quotable_leads) == 2


@pytest.mark.asyncio
async def test_assemble_map_uses_raised_budget() -> None:
    """assemble_controversy_map hands build_controversy_frame the raised
    per-frame budget (>=18), so more quotable Greek survives into the map."""

    class _Debate:
        debate_id = "debate_x"

    find_tool = AsyncMock()
    find_tool.execute.return_value = type("R", (), {"debates": [_Debate()]})()

    build_tool = AsyncMock()
    build_tool.execute.return_value = type(
        "FR",
        (),
        {
            "frame": ControversyFrame(
                frame_id="frame_debate_x",
                title="x",
                positions=[GroundedPosition(position_id="p", holder="H")],
                links=[DialecticalLink(relation="opposes", from_id="p", to_id="p2")],
            )
        },
    )()

    await assemble_controversy_map(
        "q", find_tool, build_tool, shape=AnswerShape.SURVEY_OF_DEBATES
    )

    call = build_tool.execute.call_args
    assert call.args[0]["max_passages"] >= 18
