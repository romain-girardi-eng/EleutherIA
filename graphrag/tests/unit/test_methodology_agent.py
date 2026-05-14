"""Tests for the Methodology Agent sub-agent."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from eleutheria_graphrag.models.methodology import (
    MethodologyFlag,
    MethodologyReport,
)
from eleutheria_graphrag.services.methodology_agent import (
    MethodologyAgent,
    format_blockers_for_synthesizer,
    format_non_blockers_as_editorial_markers,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_llm(payload: str | list[str]) -> MagicMock:
    llm = MagicMock()
    if isinstance(payload, list):
        llm.generate = AsyncMock(side_effect=payload)
    else:
        llm.generate = AsyncMock(return_value=payload)
    return llm


def _draft(answer: str, claims: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "answer": answer,
        "claim_ledger": claims or [],
    }


# ---------------------------------------------------------------------------
# Tests — five canonical claim categories
# ---------------------------------------------------------------------------


class TestMethodologySeverityClassification:
    """Each of the four flag types should map to the right severity."""

    @pytest.mark.asyncio
    async def test_anachronism_blocker_classified(self) -> None:
        """Un-hedged 'Aristotle on free will' must come back as a blocker."""
        llm_payload = json.dumps(
            {
                "methodology_flags": [
                    {
                        "type": "anachronism",
                        "claim_id_or_excerpt": "Aristotle defended free will",
                        "issue": "'Free will' is a post-ancient concept; Aristotle has hekousion/prohairesis only.",
                        "scholarly_basis": "Bobzien 1998/2014 vs Frede 2011 vs Dihle 1982 — three positions on origin.",
                        "suggested_revision": "Aristotle distinguishes voluntary action (hekousion) from involuntary; modern scholars debate whether this constitutes free will (Frede 2011 vs Bobzien 2014).",
                        "severity": "blocker",
                    }
                ],
                "approved_for_polishing": False,
            }
        )
        agent = MethodologyAgent(_make_llm(llm_payload))
        report = await agent.audit(_draft("Aristotle defended free will."))
        assert len(report.methodology_flags) == 1
        assert report.methodology_flags[0].type == "anachronism"
        assert report.methodology_flags[0].severity == "blocker"
        assert report.approved_for_polishing is False
        assert len(report.blockers) == 1

    @pytest.mark.asyncio
    async def test_source_criticism_major_classified(self) -> None:
        """Sloppy direct attestation should come back as a major flag."""
        llm_payload = json.dumps(
            {
                "methodology_flags": [
                    {
                        "type": "source_criticism",
                        "claim_id_or_excerpt": "Chrysippus argued that …",
                        "issue": "Chrysippus' argument survives only via Aulus Gellius; the testimonium chain must be named.",
                        "scholarly_basis": "Standard source-criticism in Long & Sedley.",
                        "suggested_revision": "Chrysippus is reported by Aulus Gellius (Noctes Atticae VII.2.6-13 = SVF II.1000) to have argued …",
                        "severity": "major",
                    }
                ],
                "approved_for_polishing": True,
            }
        )
        agent = MethodologyAgent(_make_llm(llm_payload))
        report = await agent.audit(_draft("Chrysippus argued that fate is causal."))
        assert report.methodology_flags[0].type == "source_criticism"
        assert report.methodology_flags[0].severity == "major"
        # Major flags do not block polishing
        assert report.approved_for_polishing is True
        assert len(report.blockers) == 0
        assert len(report.non_blockers) == 1

    @pytest.mark.asyncio
    async def test_scholarly_consensus_blocker_classified(self) -> None:
        """Picking a side in Frede vs Bobzien without naming the other is a blocker."""
        llm_payload = json.dumps(
            {
                "methodology_flags": [
                    {
                        "type": "scholarly_consensus",
                        "claim_id_or_excerpt": "Ancient philosophy had no concept of free will",
                        "issue": "Draft sides with Bobzien (1998/2014) without engaging Frede (2011) or Dihle (1982).",
                        "scholarly_basis": "Frede argues yes (Stoic-Patristic synthesis); Bobzien argues no (post-ancient); Dihle locates later in Augustine.",
                        "suggested_revision": "Whether ancient philosophy contains a concept of free will is debated: Bobzien (1998, 2014) holds it does not; Frede (2011) locates its emergence in the Stoic-Patristic synthesis; Dihle (1982) places it later in Augustine.",
                        "severity": "blocker",
                    }
                ],
                "approved_for_polishing": False,
            }
        )
        agent = MethodologyAgent(_make_llm(llm_payload))
        report = await agent.audit(
            _draft("Ancient philosophy had no concept of free will.")
        )
        assert report.methodology_flags[0].type == "scholarly_consensus"
        assert report.methodology_flags[0].severity == "blocker"
        assert report.approved_for_polishing is False

    @pytest.mark.asyncio
    async def test_period_mismatch_blocker_classified(self) -> None:
        """Stoic doctrine attributed to Aristotle is a period_appropriateness blocker."""
        llm_payload = json.dumps(
            {
                "methodology_flags": [
                    {
                        "type": "period_appropriateness",
                        "claim_id_or_excerpt": "Aristotle's doctrine of synkatathesis",
                        "issue": "Synkatathesis is a Stoic technical term (Zeno/Chrysippus); Aristotle has no such doctrine.",
                        "scholarly_basis": "Long & Sedley vol. 1 ch. 40; Bobzien 1998.",
                        "suggested_revision": "Aristotle's account of assent (Nicomachean Ethics III) is distinct from the Stoic doctrine of synkatathesis.",
                        "severity": "blocker",
                    }
                ],
                "approved_for_polishing": False,
            }
        )
        agent = MethodologyAgent(_make_llm(llm_payload))
        report = await agent.audit(_draft("Aristotle's doctrine of synkatathesis."))
        assert report.methodology_flags[0].type == "period_appropriateness"
        assert report.approved_for_polishing is False

    @pytest.mark.asyncio
    async def test_clean_draft_approved(self) -> None:
        """A methodologically clean draft must return zero flags and approved=True."""
        llm_payload = json.dumps(
            {"methodology_flags": [], "approved_for_polishing": True}
        )
        agent = MethodologyAgent(_make_llm(llm_payload))
        report = await agent.audit(
            _draft(
                "Aristotle distinguishes hekousion (voluntary) from akousion (involuntary).",
            )
        )
        assert report.methodology_flags == []
        assert report.approved_for_polishing is True


# ---------------------------------------------------------------------------
# Tests — JSON parsing fallback
# ---------------------------------------------------------------------------


class TestMethodologyJsonParsing:
    @pytest.mark.asyncio
    async def test_malformed_json_returns_empty_report(self) -> None:
        """Unparseable LLM output should not crash; defaults to empty + approved."""
        agent = MethodologyAgent(_make_llm("not json at all"))
        report = await agent.audit(_draft("anything"))
        assert report.methodology_flags == []
        assert report.approved_for_polishing is True

    @pytest.mark.asyncio
    async def test_invalid_severity_filtered_out(self) -> None:
        """Flags with invalid severity strings must be dropped, not promoted."""
        llm_payload = json.dumps(
            {
                "methodology_flags": [
                    {
                        "type": "anachronism",
                        "claim_id_or_excerpt": "x",
                        "issue": "y",
                        "scholarly_basis": "z",
                        "suggested_revision": "w",
                        "severity": "catastrophic",  # invalid
                    }
                ],
                "approved_for_polishing": True,
            }
        )
        agent = MethodologyAgent(_make_llm(llm_payload))
        report = await agent.audit(_draft("anything"))
        assert report.methodology_flags == []

    @pytest.mark.asyncio
    async def test_approved_derived_from_flags_not_llm(self) -> None:
        """If LLM says approved=true but emits a blocker, we override to false."""
        llm_payload = json.dumps(
            {
                "methodology_flags": [
                    {
                        "type": "anachronism",
                        "claim_id_or_excerpt": "x",
                        "issue": "y",
                        "scholarly_basis": "z",
                        "suggested_revision": "w",
                        "severity": "blocker",
                    }
                ],
                "approved_for_polishing": True,  # LLM lying — we override
            }
        )
        agent = MethodologyAgent(_make_llm(llm_payload))
        report = await agent.audit(_draft("anything"))
        assert report.approved_for_polishing is False


# ---------------------------------------------------------------------------
# Tests — re-synth loop
# ---------------------------------------------------------------------------


class TestMethodologyResynthLoop:
    @pytest.mark.asyncio
    async def test_blocker_triggers_resynth(self) -> None:
        """If first audit returns a blocker, resynthesize is invoked."""
        first_payload = json.dumps(
            {
                "methodology_flags": [
                    {
                        "type": "anachronism",
                        "claim_id_or_excerpt": "Aristotle on free will",
                        "issue": "anachronism",
                        "scholarly_basis": "Bobzien 1998",
                        "suggested_revision": "use hekousion/prohairesis",
                        "severity": "blocker",
                    }
                ],
                "approved_for_polishing": False,
            }
        )
        # Second audit returns clean — loop exits.
        clean_payload = json.dumps(
            {"methodology_flags": [], "approved_for_polishing": True}
        )
        llm = _make_llm([first_payload, clean_payload])
        agent = MethodologyAgent(llm)

        call_count = {"n": 0}

        async def _resynth(
            _draft_in: dict[str, Any], blockers: list[MethodologyFlag]
        ) -> dict[str, Any]:
            call_count["n"] += 1
            assert len(blockers) == 1
            return {"answer": "revised", "claim_ledger": []}

        final_draft, final_report = await agent.run_with_resynth_loop(
            initial_draft=_draft("Aristotle on free will."),
            resynthesize=_resynth,
        )
        assert call_count["n"] == 1
        assert final_report.approved_for_polishing is True
        assert final_draft["answer"] == "revised"

    @pytest.mark.asyncio
    async def test_resynth_loop_capped_at_two_iterations(self) -> None:
        """Even if blockers persist, we never exceed max_iterations re-synth calls."""
        blocker_payload = json.dumps(
            {
                "methodology_flags": [
                    {
                        "type": "anachronism",
                        "claim_id_or_excerpt": "x",
                        "issue": "still bad",
                        "scholarly_basis": "z",
                        "suggested_revision": "w",
                        "severity": "blocker",
                    }
                ],
                "approved_for_polishing": False,
            }
        )
        # Every audit returns a blocker — loop must stop on its own.
        # max_iterations=2 means: 1st audit, 1 re-synth, 2nd audit. Then stop.
        llm = _make_llm([blocker_payload, blocker_payload, blocker_payload])
        agent = MethodologyAgent(llm, max_iterations=2)

        resynth_calls = {"n": 0}

        async def _resynth(
            _draft_in: dict[str, Any], _blockers: list[MethodologyFlag]
        ) -> dict[str, Any]:
            resynth_calls["n"] += 1
            return {"answer": f"attempt {resynth_calls['n']}", "claim_ledger": []}

        _final_draft, final_report = await agent.run_with_resynth_loop(
            initial_draft=_draft("bad"),
            resynthesize=_resynth,
        )
        # With max_iterations=2, only one re-synth call is allowed.
        assert resynth_calls["n"] == 1
        # The remaining blocker flags ride along on the final report.
        assert len(final_report.blockers) == 1


# ---------------------------------------------------------------------------
# Tests — SSE event emission
# ---------------------------------------------------------------------------


class TestMethodologyEventEmission:
    @pytest.mark.asyncio
    async def test_flag_event_emitted_per_finding(self) -> None:
        """Each flag should produce one ``methodology_flagged`` event."""
        llm_payload = json.dumps(
            {
                "methodology_flags": [
                    {
                        "type": "anachronism",
                        "claim_id_or_excerpt": "x",
                        "issue": "y",
                        "scholarly_basis": "z",
                        "suggested_revision": "w",
                        "severity": "major",
                    },
                    {
                        "type": "source_criticism",
                        "claim_id_or_excerpt": "x2",
                        "issue": "y2",
                        "scholarly_basis": "z2",
                        "suggested_revision": "w2",
                        "severity": "minor",
                    },
                ],
                "approved_for_polishing": True,
            }
        )
        events: list[dict[str, Any]] = []

        async def _on_event(event: dict[str, Any]) -> None:
            events.append(event)

        agent = MethodologyAgent(_make_llm(llm_payload), on_event=_on_event)
        await agent.audit(_draft("anything"))
        # Two flag events + one approved event
        flag_events = [e for e in events if e["type"] == "methodology_flagged"]
        approved_events = [e for e in events if e["type"] == "methodology_approved"]
        assert len(flag_events) == 2
        assert len(approved_events) == 1


# ---------------------------------------------------------------------------
# Tests — formatters (pure functions)
# ---------------------------------------------------------------------------


class TestFormatters:
    def test_blockers_render_as_prompt_block(self) -> None:
        flag = MethodologyFlag(
            type="anachronism",
            claim_id_or_excerpt="c1",
            issue="anachronism",
            scholarly_basis="Bobzien 1998",
            suggested_revision="rewrite without 'free will'",
            severity="blocker",
        )
        rendered = format_blockers_for_synthesizer([flag])
        assert "METHODOLOGY FLAGS" in rendered
        assert "anachronism" in rendered
        assert "rewrite without 'free will'" in rendered

    def test_blockers_empty_renders_empty(self) -> None:
        assert format_blockers_for_synthesizer([]) == ""

    def test_non_blockers_render_as_editorial_markers(self) -> None:
        flag = MethodologyFlag(
            type="source_criticism",
            claim_id_or_excerpt="c2",
            issue="missing testimonium chain",
            scholarly_basis="",
            suggested_revision="add Aulus Gellius reference",
            severity="major",
        )
        rendered = format_non_blockers_as_editorial_markers([flag])
        assert "[ED:" in rendered
        assert "source_criticism" in rendered
        assert "missing testimonium chain" in rendered


# ---------------------------------------------------------------------------
# Tests — pydantic model invariants
# ---------------------------------------------------------------------------


class TestMethodologyReportModel:
    def test_blockers_and_non_blockers_partition(self) -> None:
        flags = [
            MethodologyFlag(
                type="anachronism",
                claim_id_or_excerpt="x",
                issue="i",
                scholarly_basis="",
                suggested_revision="r",
                severity="blocker",
            ),
            MethodologyFlag(
                type="anachronism",
                claim_id_or_excerpt="y",
                issue="i",
                scholarly_basis="",
                suggested_revision="r",
                severity="major",
            ),
            MethodologyFlag(
                type="anachronism",
                claim_id_or_excerpt="z",
                issue="i",
                scholarly_basis="",
                suggested_revision="r",
                severity="minor",
            ),
        ]
        report = MethodologyReport(
            methodology_flags=flags, approved_for_polishing=False
        )
        assert len(report.blockers) == 1
        assert len(report.non_blockers) == 2
