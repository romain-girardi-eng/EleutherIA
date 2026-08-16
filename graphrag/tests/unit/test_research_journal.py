"""The researcher's journal: hypotheses the pipeline formed and then dropped.

The timeline used to narrate only what worked. These helpers read REAL pipeline
state — an empty search, a claim the grounding gate refused, the critic's own
"still missing" verdict, an adversarial hunt that found nothing — and turn it
into ``research_note`` frames. Nothing here may invent a lead the run did not
actually follow, so every test starts from state a real run would leave behind.
"""

from __future__ import annotations

import json
import re

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

#: A slice of the KG the way ``Deps.node_lookup`` holds it — the journal
#: resolves ids against this so the reader sees names, never identifiers.
_LOOKUP: dict[str, dict[str, str]] = {
    "pub_furst_2022_wege_freiheit": {
        "id": "pub_furst_2022_wege_freiheit",
        "label": "Fürst, Wege zur Freiheit",
        "type": "publication",
    },
    "scholarly_argument_gorday_origen_s_view_of_free_will_and_0": {
        "id": "scholarly_argument_gorday_origen_s_view_of_free_will_and_0",
        "label": "Gorday, Origen's view of free will",
        "type": "scholarly_argument",
    },
    "debate_fate_1": {
        "id": "debate_fate_1",
        "label": "Fate and what is up to us",
        "type": "debate",
    },
    "debate_assent_2": {
        "id": "debate_assent_2",
        "label": "Assent and impulse",
        "type": "debate",
    },
}


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
        # The reader is told what was searched, not which tool ran it.
        assert "search_passages" not in notes[0]["summary"]
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


class TestANodeThatWasReadIsNeverADeadEnd:
    """A false "dropped lead" about a source the run actually read misleads.

    ``pub_furst_2022_wege_freiheit`` exists in the KG with rich content; a
    successful ``get_node_detail`` on it must never be narrated as a dead end.
    """

    def _read(self, node_id: str, detail_count: int) -> RAGState:
        state = _state()
        state.research_notebook.tool_calls = [
            ResearchToolCall(
                tool_call_id="c1",
                tool_name="get_node_detail",
                stage_id="agent_loop",
                query=node_id,
                rationale="checking the modern reception",
                detail_count=detail_count,
            )
        ]
        return state

    def test_a_successful_node_read_produces_no_note(self):
        state = self._read("pub_furst_2022_wege_freiheit", 1)
        assert dead_end_tool_notes(state, _LOOKUP) == []

    def test_a_node_whose_content_reached_the_evidence_produces_no_note(self):
        """Even if the counter says 0, ingested content means it was read."""
        state = self._read("pub_furst_2022_wege_freiheit", 0)
        state.context_node_ids = ["pub_furst_2022_wege_freiheit"]
        assert dead_end_tool_notes(state, _LOOKUP) == []

    def test_a_genuinely_empty_read_is_reported_under_the_nodes_own_name(self):
        state = self._read(
            "scholarly_argument_gorday_origen_s_view_of_free_will_and_0", 0
        )
        notes = dead_end_tool_notes(state, _LOOKUP)
        assert len(notes) == 1
        assert notes[0]["kind"] == "dead_end"
        assert "Gorday, Origen's view of free will" in notes[0]["summary"]
        assert "scholarly_argument" not in notes[0]["summary"]
        assert "get_node_detail" not in notes[0]["summary"]

    def test_an_id_the_graph_cannot_name_is_skipped_rather_than_printed(self):
        state = self._read("pub_not_in_the_graph_at_all", 0)
        assert dead_end_tool_notes(state, _LOOKUP) == []

    def test_an_empty_search_is_still_a_dead_end(self):
        state = _state()
        state.research_notebook.tool_calls = [
            ResearchToolCall(
                tool_call_id="c1",
                tool_name="search_nodes",
                stage_id="agent_loop",
                query="Stoic theory of moral luck",
                detail_count=0,
            )
        ]
        notes = dead_end_tool_notes(state, _LOOKUP)
        assert len(notes) == 1
        assert "Stoic theory of moral luck" in notes[0]["summary"]


class TestTheJournalSpeaksToAResearcher:
    """No summary may leak identifiers, tool names or pipeline vocabulary."""

    #: Raw ids (``pub_furst_2022_…``), tool names (``get_node_detail``) and
    #: internal mode/gate names.
    MACHINE_TALK = re.compile(r"_[a-z0-9]{6,}|llm mode|heuristic", re.IGNORECASE)

    def _every_summary(self) -> list[str]:
        state = _state(
            controversy_map_gaps=[
                "build_controversy_frame on debate_fate_1 returned no frame",
                "frame debate_assent_2 under-filled (no positions or links)",
            ],
            controversy_map={"status": "degraded", "reason": "assembly yielded 0"},
            sufficiency_check={
                "score": 0.24,
                "sufficient": False,
                "reason": "heuristic sufficiency (minimal llm mode)",
                "refinement": "",
                "continued": True,
            },
            counter_evidence_hunt={
                "status": "ok",
                "claims_audited": 2,
                "total_testimonia": 0,
            },
        )
        state.research_notebook.tool_calls = [
            ResearchToolCall(
                tool_call_id="c1",
                tool_name="get_node_detail",
                stage_id="agent_loop",
                query="pub_furst_2022_wege_freiheit",
                detail_count=0,
            ),
            ResearchToolCall(
                tool_call_id="c2",
                tool_name="get_node_detail",
                stage_id="agent_loop",
                query="scholarly_argument_gorday_origen_s_view_of_free_will_and_0",
                detail_count=0,
            ),
            ResearchToolCall(
                tool_call_id="c3",
                tool_name="search_passages",
                stage_id="agent_loop",
                query="αὐτεξούσιον Chrysippus",
                detail_count=0,
            ),
        ]
        state.claim_ledger = [
            ClaimLedgerItem(
                claim="Origen read Chrysippus directly",
                status=ClaimStatus.INSUFFICIENT,
            )
        ]
        notes = [
            *dead_end_tool_notes(state, _LOOKUP),
            *controversy_gap_notes(state, _LOOKUP),
            *sufficiency_gap_notes(state),
            *counter_evidence_notes(state),
            *rejected_claim_notes(state),
        ]
        assert len(notes) >= 6, "expected every producer to contribute"
        return [n["summary"] for n in notes]

    def test_no_summary_reads_as_machine_output(self):
        for summary in self._every_summary():
            assert not self.MACHINE_TALK.search(summary), summary

    def test_the_named_leads_use_their_kg_labels(self):
        summaries = " || ".join(self._every_summary())
        assert "Fürst, Wege zur Freiheit" in summaries
        assert "Gorday, Origen's view of free will" in summaries
        assert "Fate and what is up to us" in summaries


class TestControversyGapNotes:
    def test_each_dropped_debate_seed_is_named(self):
        state = _state(
            controversy_map_gaps=[
                "build_controversy_frame on debate_fate_1 returned no frame",
                "frame debate_assent_2 under-filled (no positions or links)",
            ],
            controversy_map={"status": "ok", "frames": 3},
        )
        notes = controversy_gap_notes(state, _LOOKUP)
        assert [n["kind"] for n in notes] == ["abandoned", "abandoned"]
        # The debate is named the way the graph names it, never by its id.
        assert "Fate and what is up to us" in notes[0]["summary"]
        assert "debate_fate_1" not in notes[0]["summary"]
        assert "build_controversy_frame" not in notes[0]["summary"]
        assert "Assent and impulse" in notes[1]["summary"]
        assert "neither positions nor" in notes[1]["summary"]

    def test_a_seed_the_graph_cannot_name_is_skipped_not_printed(self):
        state = _state(
            controversy_map_gaps=[
                "build_controversy_frame on debate_unknown_9 returned no frame"
            ],
            controversy_map={"status": "ok", "frames": 1},
        )
        assert controversy_gap_notes(state, _LOOKUP) == []

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
    def test_the_verdict_is_told_in_plain_words_with_the_score_in_detail(self):
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
        assert "too thin" in notes[0]["summary"]
        assert "one more retrieval round was run" in notes[0]["summary"]
        assert "no primary passage for the Stoic side" in notes[0]["summary"]
        # The number is a measurement, not a sentence: it belongs in detail.
        assert "0.42" not in notes[0]["summary"]
        assert "0.42" in notes[0]["detail"]
        assert "Epictetus" in notes[0]["detail"]

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
        summary = sufficiency_gap_notes(state)[0]["summary"]
        assert "no retrieval round left to run" in summary

    def test_an_internal_verdict_marker_is_never_quoted_at_the_reader(self):
        """The heuristic path writes machine vocabulary, not a finding."""
        state = _state(
            sufficiency_check={
                "score": 0.24,
                "sufficient": False,
                "reason": "heuristic sufficiency (minimal llm mode)",
                "refinement": "",
                "continued": True,
            }
        )
        note = sufficiency_gap_notes(state)[0]
        assert "heuristic" not in note["summary"]
        assert "llm" not in note["summary"].lower()
        assert "What was missing" not in note["summary"]
        # The note still says what happened to the research.
        assert "one more retrieval round was run" in note["summary"]
        assert "0.24" in note["detail"]

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
