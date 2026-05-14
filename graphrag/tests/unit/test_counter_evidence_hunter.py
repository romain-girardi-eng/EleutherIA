"""Tests for the Counter-Evidence Hunter sub-agent."""

from __future__ import annotations

import asyncio
import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from eleutheria_graphrag.models.counter_evidence import (
    ClaimUnit,
    CounterEvidenceReport,
    SynthesizedDraft,
)
from eleutheria_graphrag.services.counter_evidence_hunter import (
    CounterEvidenceHunter,
    MCPToolset,
    format_report_for_synthesizer,
    stream_counter_evidence_events,
)

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _passage(
    passage_id: str, text: str, work: str = "Cicero, De Fato"
) -> dict[str, Any]:
    return {
        "passage_id": passage_id,
        "work_title": work,
        "author": "Cicero",
        "canonical_ref": "10.20",
        "language": "lat",
        "text_content": text,
        "score": 0.9,
    }


def _make_search_tool(passages: list[dict[str, Any]]) -> MagicMock:
    tool = MagicMock()
    result = MagicMock()
    result.passages = [MagicMock(model_dump=lambda p=p: p) for p in passages]
    tool.execute = AsyncMock(return_value=result)
    return tool


def _make_subgraph_tool(nodes: list[dict[str, Any]]) -> MagicMock:
    tool = MagicMock()
    result = MagicMock()
    result.nodes = nodes
    result.model_dump = lambda: {"nodes": nodes, "seed_count": 1}
    tool.execute = AsyncMock(return_value=result)
    return tool


def _make_neighbors_tool(edges: list[dict[str, Any]]) -> MagicMock:
    tool = MagicMock()
    tool.execute = AsyncMock(return_value={"edges": edges})
    return tool


def _make_llm(payload: str | list[str]) -> MagicMock:
    llm = MagicMock()
    if isinstance(payload, list):
        llm.generate = AsyncMock(side_effect=payload)
    else:
        llm.generate = AsyncMock(return_value=payload)
    return llm


def _claim(
    cid: str = "c1",
    text: str = "The Stoics held that all events are causally determined.",
    seeds: list[str] | None = None,
) -> ClaimUnit:
    return ClaimUnit(
        claim_id=cid,
        claim_text=text,
        seed_node_ids=seeds or ["concept_fate", "school_stoics"],
        keywords=["fate", "determinism"],
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestCounterEvidenceHunterSingleClaim:
    """Test single-claim hunting + classification."""

    @pytest.mark.asyncio
    async def test_contradiction_strong_passes(self):
        """A strong contradiction with a real passage id should be kept."""
        passages = [_passage("p_carneades_1", "Carneades argues fate is no cause.")]
        edges = [
            {
                "source": "school_stoics",
                "relation": "critiques",
                "target": "person_carneades",
                "label": "Carneades",
            }
        ]
        llm_response = json.dumps(
            {
                "opposing_testimonia": [
                    {
                        "type": "contradiction",
                        "source": "Cicero, De Fato 31",
                        "source_node_id": "person_carneades",
                        "passage_id": "p_carneades_1",
                        "excerpt": "Carneades argues fate is no cause.",
                        "force": "strong",
                        "brief_reasoning": "Direct denial of causal determinism.",
                    }
                ]
            }
        )

        hunter = CounterEvidenceHunter(
            llm=_make_llm(llm_response),
            tools=MCPToolset(
                search_passages=_make_search_tool(passages),
                explore_subgraph=_make_subgraph_tool([]),
                get_neighbors=_make_neighbors_tool(edges),
            ),
        )
        finding = await hunter.hunt_one(_claim())
        assert len(finding.opposing_testimonia) == 1
        t = finding.opposing_testimonia[0]
        assert t.type == "contradiction"
        assert t.force == "strong"
        assert t.passage_id == "p_carneades_1"

    @pytest.mark.asyncio
    async def test_qualification_vs_alternative_classification(self):
        """Both qualification and alternative types should be preserved."""
        passages = [
            _passage("p1", "Even the Stoics admit some events are 'eph'hêmin'."),
            _passage("p2", "Epicurus posits the swerve as undetermined."),
        ]
        llm_response = json.dumps(
            {
                "opposing_testimonia": [
                    {
                        "type": "qualification",
                        "source": "Epictetus Diss. 1.1",
                        "source_node_id": None,
                        "passage_id": "p1",
                        "excerpt": "eph hêmin nuance",
                        "force": "moderate",
                        "brief_reasoning": "Adds the 'up to us' qualification.",
                    },
                    {
                        "type": "alternative",
                        "source": "Epicurus, swerve",
                        "source_node_id": None,
                        "passage_id": "p2",
                        "excerpt": "swerve as undetermined",
                        "force": "strong",
                        "brief_reasoning": "Rival school doctrine.",
                    },
                ]
            }
        )
        hunter = CounterEvidenceHunter(
            llm=_make_llm(llm_response),
            tools=MCPToolset(
                search_passages=_make_search_tool(passages),
                explore_subgraph=_make_subgraph_tool([]),
            ),
        )
        finding = await hunter.hunt_one(_claim())
        types = {t.type for t in finding.opposing_testimonia}
        assert types == {"qualification", "alternative"}

    @pytest.mark.asyncio
    async def test_weak_findings_are_dropped(self):
        """The hunter must discard 'weak' force findings."""
        passages = [_passage("p1", "Mentions fate in passing.")]
        llm_response = json.dumps(
            {
                "opposing_testimonia": [
                    {
                        "type": "contradiction",
                        "source": "Some text",
                        "source_node_id": None,
                        "passage_id": "p1",
                        "excerpt": "fate is mentioned",
                        "force": "weak",
                        "brief_reasoning": "passing mention",
                    }
                ]
            }
        )
        hunter = CounterEvidenceHunter(
            llm=_make_llm(llm_response),
            tools=MCPToolset(
                search_passages=_make_search_tool(passages),
                explore_subgraph=_make_subgraph_tool([]),
            ),
        )
        finding = await hunter.hunt_one(_claim())
        assert finding.opposing_testimonia == []

    @pytest.mark.asyncio
    async def test_hallucinated_ids_are_rejected(self):
        """Findings citing ids that don't appear in tool results must be dropped."""
        passages = [_passage("p_real", "real passage.")]
        llm_response = json.dumps(
            {
                "opposing_testimonia": [
                    {
                        "type": "contradiction",
                        "source": "Made up",
                        "source_node_id": None,
                        "passage_id": "p_FABRICATED",
                        "excerpt": "invented",
                        "force": "strong",
                        "brief_reasoning": "n/a",
                    }
                ]
            }
        )
        hunter = CounterEvidenceHunter(
            llm=_make_llm(llm_response),
            tools=MCPToolset(
                search_passages=_make_search_tool(passages),
                explore_subgraph=_make_subgraph_tool([]),
            ),
        )
        finding = await hunter.hunt_one(_claim())
        assert finding.opposing_testimonia == []

    @pytest.mark.asyncio
    async def test_no_results_returns_empty_finding_without_llm_call(self):
        """If both retrievers return nothing, skip the LLM classifier."""
        llm = _make_llm("never called")
        hunter = CounterEvidenceHunter(
            llm=llm,
            tools=MCPToolset(
                search_passages=_make_search_tool([]),
                explore_subgraph=_make_subgraph_tool([]),
            ),
        )
        finding = await hunter.hunt_one(_claim(seeds=[]))
        assert finding.opposing_testimonia == []
        llm.generate.assert_not_called()

    @pytest.mark.asyncio
    async def test_malformed_llm_json_is_handled(self):
        """If the LLM returns garbage, return an empty finding (no crash)."""
        passages = [_passage("p1", "x")]
        hunter = CounterEvidenceHunter(
            llm=_make_llm("not json at all"),
            tools=MCPToolset(
                search_passages=_make_search_tool(passages),
                explore_subgraph=_make_subgraph_tool([]),
            ),
        )
        finding = await hunter.hunt_one(_claim())
        assert finding.opposing_testimonia == []


class TestCounterEvidenceHunterConcurrency:
    """Test parallel hunt + concurrency cap."""

    @pytest.mark.asyncio
    async def test_concurrency_cap_enforced(self):
        """Claim-level semaphore must hold no more than `concurrency` active hunts."""
        # Patch _hunt_one to count concurrent claim hunts directly.
        active = {"now": 0, "peak": 0}
        lock = asyncio.Lock()

        hunter = CounterEvidenceHunter(
            llm=_make_llm("{}"),
            tools=MCPToolset(
                search_passages=_make_search_tool([]),
                explore_subgraph=_make_subgraph_tool([]),
            ),
            concurrency=2,
        )

        original = hunter._hunt_one

        async def instrumented(claim: ClaimUnit) -> Any:
            async with lock:
                active["now"] += 1
                active["peak"] = max(active["peak"], active["now"])
            try:
                await asyncio.sleep(0.01)
                return await original(claim)
            finally:
                async with lock:
                    active["now"] -= 1

        hunter._hunt_one = instrumented  # type: ignore[assignment]

        draft = SynthesizedDraft(answer="x", claims=[_claim(f"c{i}") for i in range(8)])
        await hunter.hunt(draft)
        assert active["peak"] <= 2

    @pytest.mark.asyncio
    async def test_hunt_aggregates_all_claims(self):
        """hunt() must return one ClaimFinding per claim — even on failures."""
        passages = [_passage("p1", "denial of stoic position")]
        llm_response = json.dumps(
            {
                "opposing_testimonia": [
                    {
                        "type": "contradiction",
                        "source": "Cicero",
                        "source_node_id": None,
                        "passage_id": "p1",
                        "excerpt": "x",
                        "force": "strong",
                        "brief_reasoning": "y",
                    }
                ]
            }
        )
        hunter = CounterEvidenceHunter(
            llm=_make_llm([llm_response] * 3 + ["short."]),
            tools=MCPToolset(
                search_passages=_make_search_tool(passages),
                explore_subgraph=_make_subgraph_tool([]),
            ),
        )
        draft = SynthesizedDraft(answer="x", claims=[_claim(f"c{i}") for i in range(3)])
        report = await hunter.hunt(draft)
        assert len(report.per_claim_findings) == 3
        assert report.total_testimonia == 3
        assert report.aggregate_summary  # non-empty


class TestCounterEvidenceCallback:
    """Test SSE event emission for live streaming."""

    @pytest.mark.asyncio
    async def test_on_finding_callback_invoked(self):
        """Each surfaced testimony must trigger the on_finding callback."""
        passages = [_passage("p1", "denial")]
        llm_response = json.dumps(
            {
                "opposing_testimonia": [
                    {
                        "type": "contradiction",
                        "source": "Cicero",
                        "source_node_id": None,
                        "passage_id": "p1",
                        "excerpt": "x",
                        "force": "strong",
                        "brief_reasoning": "y",
                    }
                ]
            }
        )
        events: list[dict[str, Any]] = []

        async def cb(evt: dict[str, Any]) -> None:
            events.append(evt)

        hunter = CounterEvidenceHunter(
            llm=_make_llm(llm_response),
            tools=MCPToolset(
                search_passages=_make_search_tool(passages),
                explore_subgraph=_make_subgraph_tool([]),
            ),
            on_finding=cb,
        )
        await hunter.hunt_one(_claim())
        assert len(events) == 1
        assert events[0]["type"] == "counter_evidence_found"
        assert events[0]["claim_id"] == "c1"
        assert events[0]["testimony_type"] == "contradiction"
        assert events[0]["force"] == "strong"

    @pytest.mark.asyncio
    async def test_stream_helper_yields_events_then_complete(self):
        """stream_counter_evidence_events must yield per-finding then a complete event."""
        passages = [_passage("p1", "denial")]
        llm_response = json.dumps(
            {
                "opposing_testimonia": [
                    {
                        "type": "contradiction",
                        "source": "Cicero",
                        "source_node_id": None,
                        "passage_id": "p1",
                        "excerpt": "x",
                        "force": "moderate",
                        "brief_reasoning": "y",
                    }
                ]
            }
        )
        hunter = CounterEvidenceHunter(
            llm=_make_llm([llm_response, "summary."]),
            tools=MCPToolset(
                search_passages=_make_search_tool(passages),
                explore_subgraph=_make_subgraph_tool([]),
            ),
        )
        draft = SynthesizedDraft(answer="x", claims=[_claim()])
        events: list[dict[str, Any]] = []
        async for evt in stream_counter_evidence_events(hunter, draft):
            events.append(evt)
        types = [e["type"] for e in events]
        assert "counter_evidence_found" in types
        assert types[-1] == "counter_evidence_complete"


class TestTwoPassIntegration:
    """Test the synth v1 → hunter → synth v2 loop."""

    def test_format_report_for_synthesizer_engages_with_findings(self):
        """The formatter must produce a prompt block referencing each finding."""
        report = CounterEvidenceReport(
            per_claim_findings=[],
        )
        # Empty report → empty block.
        assert format_report_for_synthesizer(report) == ""

        from eleutheria_graphrag.models.counter_evidence import (
            ClaimFinding,
            OpposingTestimony,
        )

        report = CounterEvidenceReport(
            per_claim_findings=[
                ClaimFinding(
                    claim_id="c1",
                    claim_text="Stoics held all events are determined.",
                    opposing_testimonia=[
                        OpposingTestimony(
                            type="contradiction",
                            source="Carneades via Cicero De Fato 31",
                            source_node_id="person_carneades",
                            passage_id="p_carn_1",
                            excerpt="fate is no cause",
                            force="strong",
                            brief_reasoning="Direct denial.",
                        )
                    ],
                )
            ],
            aggregate_summary="Draft ignores Academic skepticism.",
        )
        block = format_report_for_synthesizer(report)
        assert "COUNTER-EVIDENCE" in block
        assert "Carneades" in block
        assert "STRONG" in block
        assert "However, against this view" in block  # engagement template
        assert "OVERALL" in block

    @pytest.mark.asyncio
    async def test_graphrag_service_two_pass_loop(self):
        """GraphRAGService.query with hunt_counter_evidence=True runs v1, hunt, v2."""
        from eleutheria_graphrag.services.graphrag_service import GraphRAGService

        svc = GraphRAGService(db_service=MagicMock())
        svc._kg_loaded = True

        v1_result = {
            "answer": "v1 draft",
            "claim_ledger": [
                {"claim": "Stoics held determinism.", "evidence_ids": ["concept_fate"]}
            ],
            "seed_nodes": ["concept_fate"],
        }
        v2_result = {"answer": "v2 revised draft (engages with Carneades)"}

        # Mock agent: v1 then v2
        agent = AsyncMock()
        agent.query_dict = AsyncMock(side_effect=[v1_result, v2_result])
        agent._tools_by_name = {
            "search_passages": _make_search_tool(
                [_passage("p_carn_1", "Carneades denies fate.")]
            ),
            "explore_subgraph": _make_subgraph_tool([]),
            "get_neighbors": _make_neighbors_tool(
                [
                    {
                        "source": "concept_fate",
                        "relation": "critiques",
                        "target": "person_carneades",
                        "label": "Carneades",
                    }
                ]
            ),
        }
        svc._agent = agent

        # Stub LLM: one classification + one aggregate summary
        classification = json.dumps(
            {
                "opposing_testimonia": [
                    {
                        "type": "contradiction",
                        "source": "Cicero De Fato 31",
                        "source_node_id": "person_carneades",
                        "passage_id": "p_carn_1",
                        "excerpt": "Carneades denies fate.",
                        "force": "strong",
                        "brief_reasoning": "Direct denial.",
                    }
                ]
            }
        )
        svc.llm = MagicMock()
        svc.llm.generate = AsyncMock(side_effect=[classification, "summary"])

        result = await svc.query(
            "Did Stoics hold determinism?", hunt_counter_evidence=True
        )

        # v2 must have replaced v1
        assert result["answer"] == "v2 revised draft (engages with Carneades)"
        # Counter-evidence metadata must be attached
        assert "counter_evidence" in result["metadata"]
        report_dict = result["metadata"]["counter_evidence"]
        assert (
            report_dict["per_claim_findings"][0]["opposing_testimonia"][0]["force"]
            == "strong"
        )
        # Agent was called twice (v1 + v2)
        assert agent.query_dict.call_count == 2

    @pytest.mark.asyncio
    async def test_graphrag_service_skips_hunt_when_flag_false(self):
        """Default (hunt_counter_evidence=False) must not invoke the hunter."""
        from eleutheria_graphrag.services.graphrag_service import GraphRAGService

        svc = GraphRAGService(db_service=MagicMock())
        svc._kg_loaded = True
        agent = AsyncMock()
        agent.query_dict = AsyncMock(return_value={"answer": "v1 only"})
        svc._agent = agent

        result = await svc.query("test question")

        assert result["answer"] == "v1 only"
        assert agent.query_dict.call_count == 1
        assert "counter_evidence" not in result.get("metadata", {})
