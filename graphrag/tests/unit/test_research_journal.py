"""The researcher's journal: hypotheses the pipeline formed and then dropped.

The timeline used to narrate only what worked. These helpers read REAL pipeline
state — an empty search, a claim the grounding gate refused, the critic's own
"still missing" verdict, an adversarial hunt that found nothing — and turn it
into ``research_note`` frames. Nothing here may invent a lead the run did not
actually follow, so every test starts from state a real run would leave behind.
"""

from __future__ import annotations

import json

import pytest

from eleutheria_graphrag.agents.scholarly_agent import (
    _RESEARCH_NOTE_CAP,
    ResearchJournal,
    controversy_gap_notes,
    counter_evidence_notes,
    dead_end_tool_notes,
    rejected_claim_notes,
    sufficiency_gap_notes,
)
from eleutheria_graphrag.agents.state import (
    ClaimLedgerItem,
    ClaimStatus,
    RAGState,
    ResearchToolCall,
)


def _state(**metadata) -> RAGState:
    state = RAGState(question="Did Chrysippus hold that assent is up to us?")
    state.metadata.update(metadata)
    return state


class TestDeadEndToolNotes:
    def test_a_search_that_returned_nothing_is_reported(self):
        state = _state()
        state.research_notebook.tool_calls = [
            ResearchToolCall(
                tool_call_id="c1",
                tool_name="search_passages",
                stage_id="agent_loop",
                query="ἐφ᾽ ἡμῖν clinamen",
                rationale="testing an Epicurean parallel",
                detail_count=0,
            ),
        ]
        notes = dead_end_tool_notes(state)
        assert len(notes) == 1
        assert notes[0]["kind"] == "dead_end"
        assert "ἐφ᾽ ἡμῖν clinamen" in notes[0]["summary"]
        assert "search_passages" in notes[0]["summary"]
        assert notes[0]["detail"] == "testing an Epicurean parallel"

    def test_a_productive_search_is_not_reported(self):
        state = _state()
        state.research_notebook.tool_calls = [
            ResearchToolCall(
                tool_call_id="c1",
                tool_name="search_nodes",
                stage_id="agent_loop",
                query="Chrysippus assent",
                detail_count=7,
            ),
        ]
        assert dead_end_tool_notes(state) == []

    def test_an_unnameable_lead_is_skipped_rather_than_described_vaguely(self):
        state = _state()
        state.research_notebook.tool_calls = [
            ResearchToolCall(
                tool_call_id="c1",
                tool_name="explore_subgraph",
                stage_id="agent_loop",
                query="",
                detail_count=0,
            ),
        ]
        assert dead_end_tool_notes(state) == []

    def test_repeated_empty_searches_collapse_and_stay_bounded(self):
        state = _state()
        state.research_notebook.tool_calls = [
            ResearchToolCall(
                tool_call_id=f"c{i}",
                tool_name="search_passages",
                stage_id="agent_loop",
                query=f"lemma-{i % 2}",
                detail_count=0,
            )
            for i in range(12)
        ]
        notes = dead_end_tool_notes(state)
        assert len(notes) == 2  # deduped by (tool, lead)


class TestControversyGapNotes:
    def test_each_dropped_debate_seed_is_named(self):
        state = _state(
            controversy_map_gaps=[
                "build_controversy_frame on debate_fate_1 returned no frame",
                "frame debate_assent_2 under-filled (no positions or links)",
            ],
            controversy_map={"status": "ok", "frames": 3},
        )
        notes = controversy_gap_notes(state)
        assert [n["kind"] for n in notes] == ["abandoned", "abandoned"]
        assert "debate_fate_1" in notes[0]["summary"]

    def test_a_zero_frame_assembly_reports_the_abandoned_approach(self):
        state = _state(
            controversy_map_gaps=[],
            controversy_map={
                "status": "degraded",
                "reason": "assembly yielded 0 frames",
            },
        )
        notes = controversy_gap_notes(state)
        assert len(notes) == 1
        assert notes[0]["kind"] == "abandoned"
        assert "non-dialectical" in notes[0]["summary"]

    def test_a_clean_map_produces_nothing(self):
        state = _state(controversy_map={"status": "ok", "frames": 4})
        assert controversy_gap_notes(state) == []


class TestSufficiencyGapNotes:
    def test_the_critics_verdict_is_surfaced_verbatim(self):
        state = _state(
            sufficiency_check={
                "score": 0.42,
                "sufficient": False,
                "reason": "no primary passage for the Stoic side",
                "refinement": "search Epictetus Diss. 1.1",
                "continued": True,
            }
        )
        notes = sufficiency_gap_notes(state)
        assert len(notes) == 1
        assert notes[0]["kind"] == "gap"
        assert "no primary passage for the Stoic side" in notes[0]["summary"]
        assert "0.42" in notes[0]["summary"]
        assert "Epictetus" in notes[0]["detail"]
        assert "One extra retrieval round was granted." in notes[0]["detail"]

    def test_no_continuation_available_is_stated(self):
        state = _state(
            sufficiency_check={
                "score": 0.3,
                "sufficient": False,
                "reason": "thin evidence",
                "refinement": "",
                "continued": False,
            }
        )
        assert "No extra retrieval round" in sufficiency_gap_notes(state)[0]["detail"]

    def test_a_sufficient_verdict_is_silent(self):
        state = _state(
            sufficiency_check={"score": 0.9, "sufficient": True, "reason": "ok"}
        )
        assert sufficiency_gap_notes(state) == []


class TestCounterEvidenceNotes:
    def test_an_empty_hunt_is_reported_as_a_dead_end(self):
        state = _state(
            counter_evidence_hunt={
                "status": "ok",
                "claims_audited": 3,
                "total_testimonia": 0,
                "ledger_items": 0,
            }
        )
        notes = counter_evidence_notes(state)
        assert len(notes) == 1
        assert notes[0]["kind"] == "dead_end"
        assert "3 working hypotheses" in notes[0]["summary"]

    def test_a_hunt_that_found_objections_is_silent(self):
        state = _state(
            counter_evidence_hunt={
                "status": "ok",
                "claims_audited": 3,
                "total_testimonia": 5,
            }
        )
        assert counter_evidence_notes(state) == []

    def test_a_skipped_hunt_names_why(self):
        state = _state(
            counter_evidence_hunt={
                "status": "skipped",
                "reason": "no hypotheses to audit",
            }
        )
        notes = counter_evidence_notes(state)
        assert notes[0]["kind"] == "abandoned"
        assert "no hypotheses to audit" in notes[0]["summary"]

    def test_no_hunt_at_all_is_silent(self):
        assert counter_evidence_notes(_state()) == []


class TestRejectedClaimNotes:
    def test_insufficient_and_unverified_claims_are_both_reported(self):
        state = _state()
        state.claim_ledger = [
            ClaimLedgerItem(
                claim="Chrysippus made assent up to us", status=ClaimStatus.SUPPORTED
            ),
            ClaimLedgerItem(
                claim="Origen read Chrysippus directly",
                evidence_ids=["P1"],
                confidence=0.3,
                status=ClaimStatus.INSUFFICIENT,
            ),
            ClaimLedgerItem(
                claim="Alexander cites a lost Stoic treatise",
                status=ClaimStatus.UNVERIFIED,
            ),
        ]
        notes = rejected_claim_notes(state)
        assert len(notes) == 2
        assert all(n["kind"] == "rejected_claim" for n in notes)
        assert "evidence did not hold up" in notes[0]["summary"]
        assert "Origen read Chrysippus directly" in notes[0]["summary"]
        assert "1 evidence reference(s)" in notes[0]["detail"]
        assert "resolved to no source" in notes[1]["summary"]

    def test_a_fully_supported_ledger_is_silent(self):
        state = _state()
        state.claim_ledger = [
            ClaimLedgerItem(claim="a", status=ClaimStatus.SUPPORTED),
            ClaimLedgerItem(claim="b", status=ClaimStatus.SUPPORTED),
        ]
        assert rejected_claim_notes(state) == []

    def test_rejections_stay_bounded(self):
        state = _state()
        state.claim_ledger = [
            ClaimLedgerItem(claim=f"claim {i}", status=ClaimStatus.INSUFFICIENT)
            for i in range(20)
        ]
        assert len(rejected_claim_notes(state)) == 4


class TestResearchJournalFraming:
    def test_frame_shape(self):
        journal = ResearchJournal()
        frame = journal.note(
            "dead_end", "Searched X — nothing.", stage="agent_loop", detail="why"
        )
        assert json.loads(frame) == {
            "type": "research_note",
            "data": {
                "kind": "dead_end",
                "summary": "Searched X — nothing.",
                "stage": "agent_loop",
                "detail": "why",
            },
        }

    def test_detail_is_optional(self):
        frame = json.loads(
            ResearchJournal().note(
                "gap", "Missing the Stoic side.", stage="quality_gate"
            )
        )
        assert "detail" not in frame["data"]

    def test_an_empty_summary_is_never_emitted(self):
        assert ResearchJournal().note("gap", "   ", stage="quality_gate") is None

    def test_the_run_budget_caps_the_flood(self):
        journal = ResearchJournal()
        emitted = [
            journal.note("abandoned", f"lead {i}", stage="agent_loop")
            for i in range(50)
        ]
        assert sum(1 for e in emitted if e is not None) == _RESEARCH_NOTE_CAP
        assert journal.remaining == 0


class TestSufficiencyCheckIsRecordedOnState:
    """The critic's verdict must survive onto state even with no continuation."""

    @pytest.mark.asyncio
    async def test_verdict_is_stashed_when_no_continuation_is_granted(
        self, monkeypatch
    ):
        from eleutheria_graphrag.agents import scholarly_agent as mod

        async def _fake_assess(state, deps):  # noqa: ARG001
            return 0.25, False, "no primary passage", "search Epictetus"

        monkeypatch.setattr(mod, "assess_evidence_sufficiency", _fake_assess)
        monkeypatch.setattr(mod, "_sufficiency_continuation_budget", lambda: 0)

        state = _state()
        agent = mod.ScholarlyAgent.__new__(mod.ScholarlyAgent)
        agent.deps = object()
        continued = await mod.ScholarlyAgent._maybe_continue_for_sufficiency(
            agent, state, object()
        )

        assert continued is False
        check = state.metadata["sufficiency_check"]
        assert check["sufficient"] is False
        assert check["reason"] == "no primary passage"
        assert check["continued"] is False
        assert sufficiency_gap_notes(state)[0]["kind"] == "gap"
