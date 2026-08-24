"""Tests for the activated quality machinery (G11).

Covers:
- deep-mode flag plumbing + ResponseCache key separation
- counter-evidence hunter excerpt substring-grounding
- counter-evidence → claim-ledger merging (support_type contradicts/qualifies)
- cross-encoder reranker gating (off / on with mock / degraded)
- bounded evidence-sufficiency continuation
"""

from __future__ import annotations

import inspect
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from eleutheria_graphrag.agents.dependencies import Deps
from eleutheria_graphrag.agents.graph_nodes import _bundle_score
from eleutheria_graphrag.agents.scholarly_agent import (
    ScholarlyAgent,
    _reranker_enabled,
    _sufficiency_continuation_budget,
    counter_report_to_ledger_items,
)
from eleutheria_graphrag.agents.state import EvidenceBundle, RAGState
from eleutheria_graphrag.models.counter_evidence import (
    ClaimFinding,
    ClaimUnit,
    CounterEvidenceReport,
    OpposingTestimony,
)
from eleutheria_graphrag.services.counter_evidence_hunter import (
    CounterEvidenceHunter,
    MCPToolset,
)
from eleutheria_graphrag.services.graphrag_service import (
    GraphRAGService,
    ResponseCache,
)
from tests.publication_fixtures import verified_result

# ---------------------------------------------------------------------------
# Shared stubs
# ---------------------------------------------------------------------------

PASSAGE_TEXT = "Carneades denies fate and the chain of antecedent causes."


class _StubTool:
    def __init__(self, result):
        self._result = result
        self.calls: list[dict] = []

    async def execute(self, args):
        self.calls.append(args)
        return self._result


def _make_hunter(llm_json: str) -> CounterEvidenceHunter:
    llm = MagicMock()
    llm.generate = AsyncMock(return_value=llm_json)
    toolset = MCPToolset(
        search_passages=_StubTool(
            {
                "passages": [
                    {
                        "passage_id": "p_carn_1",
                        "work_title": "De Fato",
                        "text_content": PASSAGE_TEXT,
                    }
                ]
            }
        ),
        explore_subgraph=_StubTool({"nodes": []}),
        get_neighbors=None,
    )
    return CounterEvidenceHunter(llm=llm, tools=toolset)


def _make_bundle(bundle_id: str, text: str = PASSAGE_TEXT) -> EvidenceBundle:
    return EvidenceBundle(
        bundle_id=bundle_id,
        work_id="work-1",
        work_title="De Fato",
        author="Cicero",
        original_passage_id=f"{bundle_id}-orig",
        original_text=text,
        token_estimate=50,
    )


def _make_agent() -> ScholarlyAgent:
    deps = MagicMock(spec=Deps)
    deps.llm = MagicMock()
    deps.reranker = None
    return ScholarlyAgent(deps)


# ---------------------------------------------------------------------------
# B — Cache correctness: deep and fast answers must not collide
# ---------------------------------------------------------------------------


class TestResponseCacheDeepFlag:
    def test_deep_and_fast_have_distinct_keys(self):
        cache = ResponseCache()
        k_fast = cache._key("q", "model-a", "auto", deep=False)
        k_deep = cache._key("q", "model-a", "auto", deep=True)
        assert k_fast != k_deep

    def test_fast_entry_not_returned_for_deep_lookup(self):
        cache = ResponseCache()
        cache.put("q", "m", "auto", {"answer": "fast"}, deep=False)
        assert cache.get("q", "m", "auto", deep=True) is None
        assert cache.get("q", "m", "auto", deep=False) == {"answer": "fast"}

    def test_deep_entry_roundtrip(self):
        cache = ResponseCache()
        cache.put("q", "m", "auto", {"answer": "deep"}, deep=True)
        assert cache.get("q", "m", "auto", deep=True) == {"answer": "deep"}
        assert cache.get("q", "m", "auto", deep=False) is None


class TestDeepModePlumbing:
    @pytest.mark.asyncio
    async def test_query_forwards_hunt_flag_to_agent(self):
        svc = GraphRAGService(db_service=MagicMock())
        svc._kg_loaded = True
        agent = AsyncMock()
        agent.query_dict = AsyncMock(return_value=verified_result("fast answer"))
        agent._tools_by_name = {}
        svc._agent = agent

        await svc.query("test question")
        assert agent.query_dict.call_args.kwargs["hunt_counter_evidence"] is False

    @pytest.mark.asyncio
    async def test_fast_and_deep_do_not_share_cache(self):
        svc = GraphRAGService(db_service=MagicMock())
        svc._kg_loaded = True
        agent = AsyncMock()
        agent.query_dict = AsyncMock(
            side_effect=[
                verified_result("fast answer"),
                verified_result("deep answer"),
            ]
        )
        agent._tools_by_name = {}  # hunter degrades to empty report
        svc._agent = agent
        svc.llm = MagicMock()
        svc.llm.generate = AsyncMock(return_value="summary")

        fast = await svc.query("same question")
        deep = await svc.query("same question", hunt_counter_evidence=True)

        assert fast["answer"] == "fast answer"
        assert deep["answer"] == "deep answer"
        assert deep.get("cached") is not True

    def test_query_stream_accepts_hunt_flag(self):
        # Routes wire mode='deep' through inspect.signature() — this is the
        # contract that activates the pass-through.
        svc_params = inspect.signature(GraphRAGService.query_stream).parameters
        assert "hunt_counter_evidence" in svc_params
        agent_params = inspect.signature(ScholarlyAgent.query_stream).parameters
        assert "hunt_counter_evidence" in agent_params


# ---------------------------------------------------------------------------
# A — Hunter excerpt substring-grounding
# ---------------------------------------------------------------------------


def _testimony_json(excerpt: str) -> str:
    return json.dumps(
        {
            "opposing_testimonia": [
                {
                    "type": "contradiction",
                    "source": "Cicero, De Fato 31",
                    "source_node_id": None,
                    "passage_id": "p_carn_1",
                    "excerpt": excerpt,
                    "force": "strong",
                    "brief_reasoning": "Direct denial.",
                }
            ]
        }
    )


class TestHunterExcerptGrounding:
    @pytest.mark.asyncio
    async def test_grounded_excerpt_is_kept(self):
        hunter = _make_hunter(_testimony_json("Carneades denies fate"))
        claim = ClaimUnit(claim_id="c1", claim_text="Stoics held determinism.")
        out = await hunter.hunt_passage_contradiction(claim)
        assert len(out) == 1
        assert out[0].excerpt == "Carneades denies fate"

    @pytest.mark.asyncio
    async def test_fabricated_excerpt_is_dropped_testimony_kept(self):
        hunter = _make_hunter(
            _testimony_json("an invented sentence never returned by any tool")
        )
        claim = ClaimUnit(claim_id="c1", claim_text="Stoics held determinism.")
        out = await hunter.hunt_passage_contradiction(claim)
        assert len(out) == 1  # ids are valid, testimony survives
        assert out[0].excerpt == ""  # fabricated excerpt dropped

    @pytest.mark.asyncio
    async def test_grounding_is_punctuation_and_case_insensitive(self):
        hunter = _make_hunter(_testimony_json("carneades DENIES fate,"))
        claim = ClaimUnit(claim_id="c1", claim_text="Stoics held determinism.")
        out = await hunter.hunt_passage_contradiction(claim)
        assert len(out) == 1
        assert out[0].excerpt == "carneades DENIES fate,"

    def test_no_source_texts_skips_grounding(self):
        # Legacy callers without source_texts keep the old behaviour.
        out = CounterEvidenceHunter._parse_and_validate(
            _testimony_json("anything at all"),
            valid_passage_ids={"p_carn_1"},
            valid_node_ids=set(),
        )
        assert out[0].excerpt == "anything at all"


# ---------------------------------------------------------------------------
# A — counter-evidence → ledger items
# ---------------------------------------------------------------------------


def _report(*testimonia: OpposingTestimony) -> CounterEvidenceReport:
    return CounterEvidenceReport(
        per_claim_findings=[
            ClaimFinding(
                claim_id="c1",
                claim_text="Stoics held determinism.",
                opposing_testimonia=list(testimonia),
            )
        ],
        aggregate_summary="",
    )


class TestCounterEvidenceLedgerMerge:
    def test_contradiction_maps_to_contradicts(self):
        items = counter_report_to_ledger_items(
            _report(
                OpposingTestimony(
                    type="contradiction",
                    source="Cicero, De Fato 31",
                    passage_id="p_carn_1",
                    force="strong",
                    brief_reasoning="Direct denial.",
                )
            )
        )
        assert len(items) == 1
        assert items[0].support_type == "contradicts"
        assert items[0].evidence_class == "counter_evidence"
        assert items[0].evidence_ids == ["p_carn_1"]
        assert items[0].confidence == 0.7
        assert items[0].quote_original is None

    def test_qualification_maps_to_qualifies(self):
        items = counter_report_to_ledger_items(
            _report(
                OpposingTestimony(
                    type="qualification",
                    source="Bobzien 1998",
                    source_node_id="scholar_bobzien",
                    force="moderate",
                )
            )
        )
        assert items[0].support_type == "qualifies"
        assert items[0].confidence == 0.5

    def test_unanchored_testimony_skipped(self):
        items = counter_report_to_ledger_items(
            _report(
                OpposingTestimony(
                    type="contradiction",
                    source="nowhere",
                    force="strong",
                )
            )
        )
        assert items == []

    def test_merge_appends_to_drafted_ledger(self):
        from eleutheria_graphrag.agents.state import ClaimLedgerItem

        state = RAGState(question="q")
        state.claim_ledger = [ClaimLedgerItem(claim="main claim")]
        counter = [
            ClaimLedgerItem(
                claim="Counter-evidence (contradiction): Cicero",
                support_type="contradicts",
                evidence_class="counter_evidence",
            )
        ]
        ScholarlyAgent._merge_counter_ledger_items(state, counter)
        assert len(state.claim_ledger) == 2
        assert state.claim_ledger[-1].support_type == "contradicts"
        assert state.research_notebook.claim_ledger is state.claim_ledger


# ---------------------------------------------------------------------------
# C — reranker gating + degradation
# ---------------------------------------------------------------------------


class TestRerankerWiring:
    def test_env_gate_defaults_off(self, monkeypatch):
        monkeypatch.delenv("ELEUTHERIA_RERANKER", raising=False)
        assert _reranker_enabled() is False
        monkeypatch.setenv("ELEUTHERIA_RERANKER", "true")
        assert _reranker_enabled() is True

    @pytest.mark.asyncio
    async def test_off_means_no_rerank_call(self, monkeypatch):
        monkeypatch.delenv("ELEUTHERIA_RERANKER", raising=False)
        agent = _make_agent()
        agent.deps.reranker = AsyncMock()
        state = RAGState(question="q")
        state.evidence_bundles = [_make_bundle("b1")]

        await agent._maybe_rerank_bundles(state)

        agent.deps.reranker.rerank.assert_not_called()
        assert "rerank_score" not in state.evidence_bundles[0].metadata

    @pytest.mark.asyncio
    async def test_on_scores_bundles_and_changes_packing_order(self, monkeypatch):
        monkeypatch.setenv("ELEUTHERIA_RERANKER", "true")
        agent = _make_agent()

        async def _fake_rerank(
            query,  # noqa: ARG001 — RerankerService.rerank signature
            evidence,
            top_k=None,  # noqa: ARG001
            score_threshold=None,  # noqa: ARG001
        ):
            for ev in evidence:
                ev.score = 0.9 if ev.id == "b2" else 0.1
            return evidence

        reranker = MagicMock()
        reranker.rerank = AsyncMock(side_effect=_fake_rerank)
        agent.deps.reranker = reranker

        state = RAGState(question="q")
        b1, b2 = _make_bundle("b1"), _make_bundle("b2")
        state.evidence_bundles = [b1, b2]

        await agent._maybe_rerank_bundles(state)

        assert b1.metadata["rerank_score"] == 0.1
        assert b2.metadata["rerank_score"] == 0.9
        assert state.metadata["reranker"] == {"applied": True, "scored": 2}
        # The rerank score is the tie-break in _bundle_score: identical
        # bundles must now order b2 above b1.
        assert _bundle_score(b2, state) > _bundle_score(b1, state)

    @pytest.mark.asyncio
    async def test_degrades_cleanly_when_model_unavailable(self, monkeypatch):
        monkeypatch.setenv("ELEUTHERIA_RERANKER", "true")
        agent = _make_agent()
        reranker = MagicMock()
        reranker.rerank = AsyncMock(side_effect=RuntimeError("no weights"))
        agent.deps.reranker = reranker

        state = RAGState(question="q")
        state.evidence_bundles = [_make_bundle("b1")]

        await agent._maybe_rerank_bundles(state)  # must not raise

        assert state.metadata["reranker"] == {"applied": False, "error": True}
        assert "rerank_score" not in state.evidence_bundles[0].metadata

    @pytest.mark.asyncio
    async def test_reranker_service_returns_input_order_on_load_failure(self):
        from eleutheria_graphrag.agents.state import Evidence
        from eleutheria_graphrag.services.reranker import RerankerService

        svc = RerankerService(model_name="definitely/not-a-real-model")
        svc._load_model = MagicMock(side_effect=RuntimeError("offline"))
        evidence = [Evidence(id="e1"), Evidence(id="e2")]
        result = await svc.rerank("q", evidence)
        assert [e.id for e in result] == ["e1", "e2"]


# ---------------------------------------------------------------------------
# D — bounded sufficiency continuation
# ---------------------------------------------------------------------------


class _StubLoop:
    """Duck-typed agent loop (legacy-shaped: budget + calls_made)."""

    def __init__(self):
        self.budget = 10
        self.calls_made = 10
        self.run_count = 0
        self.seen_questions: list[str] = []

    async def run(self):
        self.run_count += 1


class TestSufficiencyContinuation:
    def test_budget_env_clamped_to_one(self, monkeypatch):
        monkeypatch.setenv("ELEUTHERIA_SUFFICIENCY_CONTINUATIONS", "7")
        assert _sufficiency_continuation_budget() == 1
        monkeypatch.setenv("ELEUTHERIA_SUFFICIENCY_CONTINUATIONS", "0")
        assert _sufficiency_continuation_budget() == 0
        monkeypatch.setenv("ELEUTHERIA_SUFFICIENCY_CONTINUATIONS", "junk")
        assert _sufficiency_continuation_budget() == 1

    @pytest.mark.asyncio
    async def test_sufficient_verdict_skips_continuation(self):
        agent = _make_agent()
        loop = _StubLoop()
        state = RAGState(question="q")
        with patch(
            "eleutheria_graphrag.agents.scholarly_agent.assess_evidence_sufficiency",
            new=AsyncMock(return_value=(0.9, True, "plenty", None)),
        ):
            continued = await agent._maybe_continue_for_sufficiency(state, loop)
        assert continued is False
        assert loop.run_count == 0

    @pytest.mark.asyncio
    async def test_insufficient_grants_exactly_one_round(self, monkeypatch):
        monkeypatch.delenv("ELEUTHERIA_SUFFICIENCY_CONTINUATIONS", raising=False)
        agent = _make_agent()
        loop = _StubLoop()
        state = RAGState(question="original question")
        verdict = AsyncMock(
            return_value=(0.2, False, "too few works", "search Alexander De Fato")
        )
        with patch(
            "eleutheria_graphrag.agents.scholarly_agent.assess_evidence_sufficiency",
            new=verdict,
        ):
            first = await agent._maybe_continue_for_sufficiency(state, loop)
            second = await agent._maybe_continue_for_sufficiency(state, loop)

        assert first is True
        assert second is False  # bounded: max 1 continuation
        assert loop.run_count == 1
        # Continuation round budget was bounded, question restored after run
        assert loop.budget == loop.calls_made + 3
        assert state.question == "original question"
        assert state.sub_queries == ["search Alexander De Fato"]
        assert state.metadata["sufficiency_continuations"] == 1

    @pytest.mark.asyncio
    async def test_env_zero_disables_continuation(self, monkeypatch):
        monkeypatch.setenv("ELEUTHERIA_SUFFICIENCY_CONTINUATIONS", "0")
        agent = _make_agent()
        loop = _StubLoop()
        state = RAGState(question="q")
        with patch(
            "eleutheria_graphrag.agents.scholarly_agent.assess_evidence_sufficiency",
            new=AsyncMock(return_value=(0.1, False, "thin", "refine")),
        ):
            continued = await agent._maybe_continue_for_sufficiency(state, loop)
        assert continued is False
        assert loop.run_count == 0

    @pytest.mark.asyncio
    async def test_feedback_injected_during_continuation(self, monkeypatch):
        monkeypatch.delenv("ELEUTHERIA_SUFFICIENCY_CONTINUATIONS", raising=False)
        agent = _make_agent()
        state = RAGState(question="original question")

        class _Recorder(_StubLoop):
            def __init__(self, state):
                super().__init__()
                self._state = state

            async def run(self):
                await super().run()
                self.seen_questions.append(self._state.question)

        loop = _Recorder(state)
        with patch(
            "eleutheria_graphrag.agents.scholarly_agent.assess_evidence_sufficiency",
            new=AsyncMock(return_value=(0.2, False, "too few works", None)),
        ):
            await agent._maybe_continue_for_sufficiency(state, loop)

        assert len(loop.seen_questions) == 1
        injected = loop.seen_questions[0]
        assert injected.startswith("original question")
        assert "TOOL RESULT — evidence_sufficiency_check" in injected
        assert "too few works" in injected
        # Restored afterwards
        assert state.question == "original question"
