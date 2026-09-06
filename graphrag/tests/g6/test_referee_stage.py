"""Senior-scholar hardening of the synthesis: verdict, source rank, referee.

Three deliverables, three groups of tests:

1. THE DEFENDED VERDICT — the synthesis prompt must REQUIRE a defended thesis
   when the question asks for an assessment, and must keep the anachronism and
   citation discipline inside it.
2. SOURCE-RANK DISCLOSURE — a curated ``metadata.source_rank`` rides into the
   serialised map as a bracket after the citation, and the prompt tells the model
   to disclose it and never to weigh grey literature as peer-reviewed work.
3. THE REFEREE STAGE — one bounded referee call + at most one revision, with
   every failure path keeping the ORIGINAL answer.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

import pytest

from eleutheria_graphrag.agents.controversy_map import (
    _fmt_position_line,
    condense_source_rank,
)
from eleutheria_graphrag.agents.dialectical_synthesis import (
    DIALECTICAL_SYNTHESIS_SYSTEM,
    DIALECTICAL_SYNTHESIS_TEMPLATE,
    MAX_REFEREE_REVISIONS,
    REFEREE_SYSTEM,
    REVISION_SYSTEM,
    RefereeRevision,
    apply_referee_revisions,
    deterministic_map_hedge,
    parse_referee_verdict,
    referee_enabled,
    referee_timeout,
    revision_timeout,
    run_referee,
    serialize_controversy_map,
)
from eleutheria_graphrag.agents.scholarly_agent import ScholarlyAgent
from eleutheria_graphrag.agents.state import (
    AnswerShape,
    ControversyFrame,
    ControversyMap,
    GroundedPosition,
    RAGState,
    ScholarlyAnswer,
)

# ── fixtures ─────────────────────────────────────────────────────────────────

_MA_RANK = (
    "MA thesis — University of British Columbia (Classical, Near Eastern and "
    "Religious Studies), December 2016; not peer-reviewed"
)
_ESSAY_RANK = "online essay — not peer-reviewed [unverified]"


def _ranked_map() -> ControversyMap:
    """A one-frame map with a ranked (grey-literature) and an unranked position."""
    moon = GroundedPosition(
        position_id="moon_2016",
        holder="Moon",
        holder_node_id="scholar_moon",
        claim="Romans 9 was read deterministically by the Greek fathers",
        publication="Moon 2016",
        page_grounding="p. 42",
        source_rank=_MA_RANK,
        disclosure_required=True,
    )
    bobzien = GroundedPosition(
        position_id="bobzien_1998",
        holder="Bobzien",
        holder_node_id="scholar_bobzien",
        claim="the ancients had no free-will problem",
        publication="Bobzien 1998",
        page_grounding="p. 330",
    )
    return ControversyMap(
        question_frame="How original is Origen's account of freedom?",
        shape=AnswerShape.POSITION_COMPARISON,
        frames=[
            ControversyFrame(
                frame_id="f1",
                title="Reading Romans 9",
                positions=[moon, bobzien],
            )
        ],
    )


class _StubLLM:
    """Minimal ``LLMService`` stand-in: canned replies, recorded calls."""

    def __init__(self, replies: list[Any]) -> None:
        self._replies = list(replies)
        self.calls: list[dict[str, Any]] = []
        self.last_model_used = "stub-model"
        self.last_reasoning_content = ""
        self.last_finish_reason = "stop"

    async def generate(self, prompt: str, **kwargs: Any) -> str:
        self.calls.append({"prompt": prompt, **kwargs})
        if not self._replies:
            raise AssertionError("stub LLM called more times than scripted")
        reply = self._replies.pop(0)
        if isinstance(reply, BaseException):
            raise reply
        if callable(reply):
            return await reply()
        return reply


def _agent_stub(llm: _StubLLM, *, gate_marker: str = "") -> Any:
    """A duck-typed ``self`` for the unbound ``_referee_answer``."""
    gate_calls: list[str] = []

    async def _verify(answer: ScholarlyAnswer, _state: RAGState) -> ScholarlyAnswer:
        gate_calls.append(answer.answer)
        if not gate_marker:
            return answer
        return answer.model_copy(update={"answer": answer.answer + gate_marker})

    stub = SimpleNamespace(deps=SimpleNamespace(llm=llm), _verify_ancient_text=_verify)
    stub.gate_calls = gate_calls
    return stub


def _answer(text: str) -> ScholarlyAnswer:
    return ScholarlyAnswer(answer=text, question="How original is Origen?")


def _run(coro: Any) -> Any:
    return asyncio.run(coro)


# ── 1. the defended verdict (prompt behaviour) ───────────────────────────────


class TestDefendedVerdictPrompt:
    def test_system_prompt_requires_a_reasoned_assessment_when_requested(self) -> None:
        text = " ".join(DIALECTICAL_SYNTHESIS_SYSTEM.lower().split())
        assert "defend a verdict when the question asks for one" in text
        assert "best-supported conclusion" in text
        assert "strongest" in text and "objection" in text

    def test_system_prompt_keeps_the_verdict_bounded(self) -> None:
        text = " ".join(DIALECTICAL_SYNTHESIS_SYSTEM.lower().split())
        assert "warranted uncertainty is a scholarly conclusion" in text
        assert "ancient self-descriptions" in text
        assert "never imply that a dispute" in text

    def test_system_prompt_no_longer_forbids_adjudication_outright(self) -> None:
        assert "never adjudicate" not in DIALECTICAL_SYNTHESIS_SYSTEM

    def test_template_allows_direct_answers_and_underdetermined_assessments(
        self,
    ) -> None:
        text = " ".join(DIALECTICAL_SYNTHESIS_TEMPLATE.lower().split())
        assert "defended conclusion" in text
        assert "without a mandatory verdict section" in text
        assert "rather than inventing a preference" in text

    def test_template_still_carries_the_citation_discipline(self) -> None:
        text = DIALECTICAL_SYNTHESIS_TEMPLATE
        assert "[P_<id>: …]" in text
        assert "[passage_<id>: …]" in text
        assert "never reconstruct" in text
        assert "EXACTLY" in text


class TestSourceRankPrompt:
    def test_system_prompt_mandates_rank_disclosure(self) -> None:
        text = DIALECTICAL_SYNTHESIS_SYSTEM
        assert "DISCLOSE THE RANK OF YOUR SOURCES" in text
        assert "[MA thesis]" in text
        assert "not peer-reviewed" in text

    def test_system_prompt_forbids_upgrading_an_unranked_source(self) -> None:
        text = DIALECTICAL_SYNTHESIS_SYSTEM
        assert "UNSTATED, not established" in text
        assert "never be the authority that decides a contested point" in text

    def test_template_repeats_the_rule_at_the_writing_step(self) -> None:
        assert "DISCLOSE SOURCE RANK" in DIALECTICAL_SYNTHESIS_TEMPLATE
        assert "RANK THE SOURCES" in DIALECTICAL_SYNTHESIS_TEMPLATE


# ── 2. source-rank serialisation ─────────────────────────────────────────────


class TestCondenseSourceRank:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            (_MA_RANK, "MA thesis, not peer-reviewed"),
            (_ESSAY_RANK, "online essay, not peer-reviewed, unverified"),
            (
                "PhD dissertation — Marquette University, May 2018, no. 769",
                "PhD dissertation",
            ),
            (
                "peer-reviewed volume chapter — Oxford University Press, 2017",
                "peer-reviewed volume chapter",
            ),
            (None, ""),
            ("   ", ""),
        ],
    )
    def test_condensation_is_subtractive(self, raw: str | None, expected: str) -> None:
        assert condense_source_rank(raw) == expected

    def test_long_rank_is_capped(self) -> None:
        label = condense_source_rank("x" * 400)
        assert len(label) <= 80
        assert label.endswith("…")


class TestPositionLineSerialisation:
    def test_rank_renders_in_brackets_after_the_citation(self) -> None:
        pos = _ranked_map().frames[0].positions[0]
        line = _fmt_position_line(pos)
        assert "(Moon 2016, p. 42) [MA thesis, not peer-reviewed]:" in line

    def test_absent_rank_renders_no_bracket(self) -> None:
        pos = _ranked_map().frames[0].positions[1]
        line = _fmt_position_line(pos)
        assert "(Bobzien 1998, p. 330):" in line
        assert "[" not in line.split("] ", 1)[1]

    def test_rank_reaches_the_serialised_map(self) -> None:
        markdown = serialize_controversy_map(_ranked_map())
        assert "[MA thesis, not peer-reviewed]" in markdown

    def test_rank_reaches_the_deterministic_hedge(self) -> None:
        hedge = deterministic_map_hedge(_ranked_map())
        assert "[MA thesis, not peer-reviewed]" in hedge


class TestSourceRankGrounding:
    """The rank must actually be READ off the KG, or the bracket never fires."""

    def _tool(self) -> Any:
        from unittest.mock import AsyncMock

        from eleutheria_graphrag.agents.dependencies import Deps
        from eleutheria_graphrag.agents.tools.build_controversy_frame import (
            BuildControversyFrameTool,
        )

        node_lookup: dict[str, dict[str, Any]] = {
            "scholar_position_moon_romans": {
                "id": "scholar_position_moon_romans",
                "label": "Moon: Romans 9 read deterministically",
                "type": "position",
                "metadata": {"stance": "Romans 9 was read deterministically."},
            },
            "scholarly_work_moon_2016": {
                "id": "scholarly_work_moon_2016",
                "label": "Moon 2016",
                "type": "scholarly_work",
                "metadata": {
                    "source_rank": _MA_RANK,
                    "synthesis_disclosure_required": "must be disclosed as an MA thesis",
                },
            },
            "scholar_position_bobzien": {
                "id": "scholar_position_bobzien",
                "label": "Bobzien: no free-will problem",
                "type": "position",
                "metadata": {"stance": "There is no free-will problem."},
            },
        }
        deps = Deps(
            db=AsyncMock(),
            llm=AsyncMock(),
            node_lookup=node_lookup,
            outgoing_edges={
                "scholar_position_moon_romans": [
                    {
                        "relation": "advanced_in",
                        "source": "scholar_position_moon_romans",
                        "target": "scholarly_work_moon_2016",
                    }
                ]
            },
            incoming_edges={},
            pagerank_scores={},
        )
        return BuildControversyFrameTool(deps)

    def test_rank_is_read_off_the_publication_node(self) -> None:
        pos = self._tool()._ground_position("scholar_position_moon_romans")
        assert pos.source_rank == _MA_RANK
        assert pos.disclosure_required is True
        assert "[MA thesis, not peer-reviewed]" in _fmt_position_line(pos)

    def test_a_node_without_a_rank_stays_unstated(self) -> None:
        pos = self._tool()._ground_position("scholar_position_bobzien")
        assert pos.source_rank is None
        assert pos.disclosure_required is False


# ── 3. referee verdict parsing ───────────────────────────────────────────────


class TestParseRefereeVerdict:
    def test_valid_pass(self) -> None:
        verdict = parse_referee_verdict('{"passes": true}')
        assert verdict is not None
        assert verdict.passes is True
        assert verdict.revisions == []
        assert "passed" in verdict.summary

    def test_valid_fail_with_revisions(self) -> None:
        raw = """```json
        {"passes": false, "revisions": [
          {"issue": "(a) no defended verdict", "instruction": "Add a Verdict section."},
          {"issue": "(b) Sorabji dangling", "instruction": "Introduce Sorabji."}
        ]}
        ```"""
        verdict = parse_referee_verdict(raw)
        assert verdict is not None
        assert verdict.passes is False
        assert [r.issue for r in verdict.revisions] == [
            "(a) no defended verdict",
            "(b) Sorabji dangling",
        ]
        assert "2 correction(s)" in verdict.summary

    def test_revisions_are_capped(self) -> None:
        entries = ", ".join(
            f'{{"issue": "i{i}", "instruction": "fix {i}"}}' for i in range(12)
        )
        verdict = parse_referee_verdict(
            f'{{"passes": false, "revisions": [{entries}]}}'
        )
        assert verdict is not None
        assert len(verdict.revisions) == MAX_REFEREE_REVISIONS

    def test_entries_without_an_instruction_are_dropped(self) -> None:
        raw = (
            '{"passes": false, "revisions": [{"issue": "x"}, {"instruction": "do y"}]}'
        )
        verdict = parse_referee_verdict(raw)
        assert verdict is not None
        assert len(verdict.revisions) == 1
        assert verdict.revisions[0].issue == "unspecified defect"

    def test_fail_with_no_actionable_instruction_becomes_a_pass(self) -> None:
        verdict = parse_referee_verdict('{"passes": false, "revisions": []}')
        assert verdict is not None
        assert verdict.passes is True

    @pytest.mark.parametrize(
        "raw",
        [
            "",
            "the answer looks fine to me",
            "{",
            '{"revisions": []}',  # no verdict key at all
            '{"passes": "maybe"}',
            "[1, 2, 3]",
        ],
    )
    def test_malformed_output_returns_none(self, raw: str) -> None:
        assert parse_referee_verdict(raw) is None


class TestRefereeFlagsAndTimeouts:
    def test_flag_is_off_by_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("ELEUTHERIA_REFEREE", raising=False)
        assert referee_enabled() is False

    def test_flag_reads_truthy_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        for value in ("1", "true", "YES", "on"):
            monkeypatch.setenv("ELEUTHERIA_REFEREE", value)
            assert referee_enabled() is True

    def test_default_timeouts_are_the_mandated_bounds(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("ELEUTHERIA_REFEREE_TIMEOUT", raising=False)
        monkeypatch.delenv("ELEUTHERIA_REVISION_TIMEOUT", raising=False)
        assert referee_timeout() == 90.0
        assert revision_timeout() == 240.0

    def test_timeouts_are_clamped(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ELEUTHERIA_REFEREE_TIMEOUT", "5")
        monkeypatch.setenv("ELEUTHERIA_REVISION_TIMEOUT", "99999")
        assert referee_timeout() == 30.0
        assert revision_timeout() == 600.0


# ── 4. the referee / revision calls ──────────────────────────────────────────


class TestRunReferee:
    def test_returns_the_parsed_verdict_and_sees_the_dossier(self) -> None:
        llm = _StubLLM(['{"passes": true}'])
        verdict = _run(
            run_referee("How original is Origen?", "an essay", llm, cmap=_ranked_map())
        )
        assert verdict is not None and verdict.passes
        prompt = llm.calls[0]["prompt"]
        assert "SUBMITTED ANSWER" in prompt and "an essay" in prompt
        # the dossier — including the source-rank bracket — reaches the referee
        assert "[MA thesis, not peer-reviewed]" in prompt
        assert llm.calls[0]["system_prompt"] is REFEREE_SYSTEM

    def test_empty_answer_is_never_refereed(self) -> None:
        llm = _StubLLM([])
        assert _run(run_referee("q", "   ", llm)) is None
        assert llm.calls == []

    def test_transport_error_keeps_the_original(self) -> None:
        llm = _StubLLM([RuntimeError("proxy down")])
        assert _run(run_referee("q", "an essay", llm)) is None

    def test_timeout_keeps_the_original(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ELEUTHERIA_REFEREE_TIMEOUT", "30")

        async def _hang() -> str:
            await asyncio.sleep(30)
            return '{"passes": false}'

        llm = _StubLLM([_hang])
        # squeeze the wait so the test is instant but still exercises wait_for
        monkeypatch.setattr(
            "eleutheria_graphrag.agents.dialectical_synthesis.referee_timeout",
            lambda: 0.05,
        )
        assert _run(run_referee("q", "an essay", llm)) is None

    def test_malformed_json_retries_then_keeps_the_original(self) -> None:
        llm = _StubLLM(["I think it reads well, actually.", "Still prose, no verdict."])
        assert _run(run_referee("q", "an essay", llm)) is None
        assert len(llm.calls) == 2

    def test_truncated_json_retries_once_with_a_doubled_budget(self) -> None:
        # F4 on the Claude proxy: thinking ate the budget and the verdict JSON
        # was cut mid-object — same recovery as the empty completion.
        llm = _StubLLM(['{"passes": false, "revisions": [{"iss', '{"passes": true}'])
        verdict = _run(run_referee("q", "an essay", llm))
        assert verdict is not None and verdict.passes
        assert len(llm.calls) == 2
        assert llm.calls[1]["max_tokens"] == llm.calls[0]["max_tokens"] * 2

    def test_referee_budget_leaves_room_for_the_answer(self) -> None:
        # F4: the synthesis tier bills reasoning tokens inside max_tokens, so a
        # modest cap came back with 0 chars of content.
        llm = _StubLLM(['{"passes": true}'])
        _run(run_referee("q", "an essay", llm))
        assert llm.calls[0]["max_tokens"] >= 12000

    def test_empty_completion_retries_once_with_a_doubled_budget(self) -> None:
        llm = _StubLLM(
            [
                "",
                '{"passes": false, "revisions": '
                '[{"issue": "i", "instruction": "Fix it."}]}',
            ]
        )
        verdict = _run(run_referee("q", "an essay", llm))
        assert verdict is not None and verdict.passes is False
        assert [rev.instruction for rev in verdict.revisions] == ["Fix it."]
        assert len(llm.calls) == 2
        assert llm.calls[1]["max_tokens"] == llm.calls[0]["max_tokens"] * 2

    def test_two_empty_completions_keep_the_original(self) -> None:
        llm = _StubLLM(["", "   "])
        assert _run(run_referee("q", "an essay", llm)) is None
        assert len(llm.calls) == 2


class TestApplyRefereeRevisions:
    def _revisions(self) -> list[RefereeRevision]:
        return [RefereeRevision(issue="(a) no verdict", instruction="Add a Verdict.")]

    def test_returns_the_corrected_answer(self) -> None:
        original = "An essay. " * 60
        revised = original + "\n\n## Verdict\nI hold that…" * 3
        llm = _StubLLM([revised])
        out = _run(apply_referee_revisions("q", original, self._revisions(), llm))
        assert out.startswith("An essay.")
        assert "## Verdict" in out
        prompt = llm.calls[0]["prompt"]
        assert "1. [(a) no verdict] Add a Verdict." in prompt
        assert llm.calls[0]["system_prompt"] is REVISION_SYSTEM

    def test_revision_system_prompt_forbids_new_ancient_text(self) -> None:
        assert "may NOT introduce any ancient-language text" in REVISION_SYSTEM
        assert "ALREADY PRESENT VERBATIM" in REVISION_SYSTEM
        assert "CORRECTED FULL ANSWER" in REVISION_SYSTEM

    def test_no_revisions_is_a_no_op(self) -> None:
        llm = _StubLLM([])
        assert _run(apply_referee_revisions("q", "an essay", [], llm)) == ""

    def test_failure_keeps_the_original(self) -> None:
        llm = _StubLLM([RuntimeError("boom")])
        assert (
            _run(apply_referee_revisions("q", "x" * 900, self._revisions(), llm)) == ""
        )

    def test_truncated_revision_is_rejected(self) -> None:
        original = "A long essay. " * 100
        llm = _StubLLM(["too short"])
        assert (
            _run(apply_referee_revisions("q", original, self._revisions(), llm)) == ""
        )


# ── 5. the stage, e2e-shaped, with a mocked LLM ──────────────────────────────


class TestRefereeStageSeam:
    def _state(self) -> RAGState:
        return RAGState(question="How original is Origen's account of freedom?")

    def test_stage_is_inert_when_the_flag_is_off(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("ELEUTHERIA_REFEREE", raising=False)
        llm = _StubLLM([])
        stub = _agent_stub(llm)
        answer, note = _run(
            ScholarlyAgent._referee_answer(stub, _answer("prose"), self._state())
        )
        assert answer.answer == "prose"
        assert note is None
        assert llm.calls == []

    def test_passing_referee_leaves_the_answer_untouched(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ELEUTHERIA_REFEREE", "1")
        llm = _StubLLM(['{"passes": true}'])
        stub = _agent_stub(llm, gate_marker=" [GATED]")
        state = self._state()
        answer, note = _run(
            ScholarlyAgent._referee_answer(stub, _answer("original prose"), state)
        )
        assert answer.answer == "original prose"
        assert note is None
        assert answer.metadata["referee"]["status"] == "passed"
        assert state.metadata["referee"]["status"] == "passed"
        # no revision call, and the gate did NOT run a second time
        assert len(llm.calls) == 1
        assert stub.gate_calls == []

    def test_failing_referee_returns_the_revised_answer_and_regates_it(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ELEUTHERIA_REFEREE", "1")
        monkeypatch.setenv("ELEUTHERIA_TEXT_VERIFIER", "1")
        original = "An essay without a verdict. " * 40
        revised = original + "\n\n## Verdict\nI hold that Origen is original."
        llm = _StubLLM(
            [
                '{"passes": false, "revisions": [{"issue": "(a) no defended verdict",'
                ' "instruction": "Add a Verdict section."}]}',
                revised,
            ]
        )
        stub = _agent_stub(llm, gate_marker=" [GATED]")
        state = self._state()
        answer, note = _run(
            ScholarlyAgent._referee_answer(stub, _answer(original), state)
        )
        assert "## Verdict" in answer.answer
        # the text gate ran AGAIN on the revised prose (a revision is model output)
        assert answer.answer.endswith(" [GATED]")
        assert stub.gate_calls and "## Verdict" in stub.gate_calls[0]
        assert answer.metadata["referee"]["status"] == "revised"
        assert answer.metadata["referee"]["issues"] == ["(a) no defended verdict"]
        assert note is not None
        assert note["kind"] == "gap"
        assert "Add a Verdict section." in note["detail"]

    def test_failed_revision_keeps_the_original_answer(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ELEUTHERIA_REFEREE", "1")
        original = "An essay without a verdict. " * 40
        llm = _StubLLM(
            [
                '{"passes": false, "revisions": [{"issue": "(a)",'
                ' "instruction": "Add a Verdict."}]}',
                RuntimeError("revision proxy down"),
            ]
        )
        stub = _agent_stub(llm, gate_marker=" [GATED]")
        answer, note = _run(
            ScholarlyAgent._referee_answer(stub, _answer(original), self._state())
        )
        assert answer.answer == original
        assert answer.metadata["referee"]["status"] == "revision_failed"
        assert note is not None  # the reader still learns what was asked for

    def test_revision_that_breaks_provenance_keeps_the_original_answer(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A stylistic improvement cannot erase the grounded source grammar."""
        monkeypatch.setenv("ELEUTHERIA_REFEREE", "1")
        monkeypatch.setattr(
            "eleutheria_graphrag.agents.scholarly_agent.passes_content_gate",
            lambda _prose, _cmap: False,
        )
        original = "Grounded prose with preserved source markers. " * 40
        revised = "Smoother prose whose source markers disappeared. " * 40
        llm = _StubLLM(
            [
                '{"passes": false, "revisions": [{"issue": "style",'
                ' "instruction": "Rewrite the essay."}]}',
                revised,
            ]
        )
        stub = _agent_stub(llm)
        state = self._state()
        state.metadata["render_answer_mode"] = "dialectical"
        state.controversy_map = SimpleNamespace()

        answer, note = _run(
            ScholarlyAgent._referee_answer(stub, _answer(original), state)
        )

        assert answer.answer == original
        assert answer.metadata["referee"]["status"] == (
            "revision_rejected_content_gate"
        )
        assert note is not None

    def test_referee_failure_keeps_the_original_answer(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ELEUTHERIA_REFEREE", "1")
        llm = _StubLLM([RuntimeError("proxy down")])
        stub = _agent_stub(llm)
        answer, note = _run(
            ScholarlyAgent._referee_answer(
                stub, _answer("original prose"), self._state()
            )
        )
        assert answer.answer == "original prose"
        assert answer.metadata["referee"]["status"] == "unavailable"
        assert note is None

    def test_stage_metadata_records_the_seam_even_on_a_pass(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ELEUTHERIA_REFEREE", "1")
        llm = _StubLLM(['{"passes": true}'])
        stub = _agent_stub(llm)
        state = self._state()
        answer, _ = _run(ScholarlyAgent._referee_answer(stub, _answer("prose"), state))
        assert answer.metadata["referee"]["model"] == "stub-model"
        assert answer.metadata["referee"]["revisions_requested"] == 0

    def test_exactly_one_referee_and_at_most_one_revision(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ELEUTHERIA_REFEREE", "1")
        original = "An essay. " * 60
        llm = _StubLLM(
            [
                '{"passes": false, "revisions": [{"issue": "(a)",'
                ' "instruction": "Add a Verdict."}]}',
                original + "\n\n## Verdict\nI hold that…",
            ]
        )
        stub = _agent_stub(llm)
        _run(ScholarlyAgent._referee_answer(stub, _answer(original), self._state()))
        assert len(llm.calls) == 2  # the stub raises if called a third time


# ── 6. the SSE seam: the stage is visible on the wire ────────────────────────


@pytest.mark.asyncio
async def test_referee_stage_reaches_the_wire(monkeypatch: pytest.MonkeyPatch) -> None:
    """A status frame names the stage and a research_note reports what it fixed."""
    import json
    from unittest.mock import patch

    from .test_dialectical_stream_plumbing import _clean_verifier
    from .test_research_note_stream import _agent, _collect_with_dropped_leads

    monkeypatch.setenv("ELEUTHERIA_SCHOLAR_RAG", "true")
    monkeypatch.setenv("ELEUTHERIA_REFEREE", "1")

    async def _fake_referee(
        self: Any,  # noqa: ARG001 — duck-typed patch target
        answer: ScholarlyAnswer,
        state: RAGState,  # noqa: ARG001
    ) -> tuple[ScholarlyAnswer, dict[str, str]]:
        revised = answer.model_copy(
            update={"answer": answer.answer + "\n\n## Verdict\nI hold that…"}
        )
        return revised, {
            "kind": "gap",
            "summary": "Referee review asked for 1 correction(s): (a) no defended verdict",
            "detail": "Add a Verdict section.",
        }

    agent = _agent()
    agent.deps.verifier_v2 = _clean_verifier()
    with patch.object(ScholarlyAgent, "_referee_answer", _fake_referee):
        events = await _collect_with_dropped_leads(agent)

    parsed = [json.loads(e) for e in events if e.startswith('{"type"')]
    statuses = [
        p
        for p in parsed
        if p.get("type") == "status" and "Referee" in p.get("message", "")
    ]
    assert statuses, "expected a 'Referee review…' status frame"
    assert statuses[0]["data"]["stage"] == "referee"

    notes = [
        p
        for p in parsed
        if p.get("type") == "research_note" and p["data"].get("stage") == "referee"
    ]
    assert notes, "expected a referee research_note"
    assert "no defended verdict" in notes[0]["data"]["summary"]

    # The REVISED answer ships only on the post-audit terminal frame.
    terminal = [p for p in parsed if p.get("type") == "complete"]
    assert terminal
    for frame in terminal:
        assert "## Verdict" in json.dumps(frame)


@pytest.mark.asyncio
async def test_stage_is_absent_from_the_wire_when_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import json

    from .test_research_note_stream import _agent, _collect_with_dropped_leads

    monkeypatch.setenv("ELEUTHERIA_SCHOLAR_RAG", "true")
    monkeypatch.delenv("ELEUTHERIA_REFEREE", raising=False)
    events = await _collect_with_dropped_leads(_agent())
    parsed = [json.loads(e) for e in events if e.startswith('{"type"')]
    # `answer_provisional` frames carry a prose string as `data`; only
    # dict-shaped payloads can name a stage.
    assert not [
        p
        for p in parsed
        if isinstance(p.get("data"), dict) and p["data"].get("stage") == "referee"
    ]
