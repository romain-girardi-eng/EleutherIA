"""LLM relevance triage: parsing, failure containment, and shed ordering.

The stage scores the prompt fitter's units (position claims, exegesis units,
contested passages past each frame's anchor) so the fitter sheds the LEAST
pertinent items first. Three properties matter and are covered here:

1. **Parsing is defensive.** The proxy may or may not honour ``json_schema``, so
   a valid, a partial and a fully malformed response must all be survivable.
2. **It can never fail a query.** Any failure — raise, timeout, garbage — leaves
   the fitter on its existing lexical ordering.
3. **Scores actually drive the shed.** A high-scored position survives a squeeze
   where a low-scored one is dropped, and a frame's top-1 contested passage is
   never reordered out regardless of its score.

No HTTP anywhere: the LLM is a stub with an async ``generate``.
"""

from __future__ import annotations

import asyncio
from unittest.mock import patch

import pytest

from eleutheria_graphrag.agents.controversy_map import (
    _relevance_passage_order,
    collect_triage_items,
    fit_controversy_frames_layer,
)
from eleutheria_graphrag.agents.dialectical_synthesis import triage_controversy_map
from eleutheria_graphrag.agents.relevance_triage import (
    BATCH_SIZE,
    NEUTRAL_SCORE,
    SNIPPET_CHARS,
    TriageItem,
    exegesis_key,
    parse_triage_scores,
    passage_key,
    position_key,
    prioritize,
    relevance_triage_enabled,
    score_relevance,
    triage_model,
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

GREEK = "τῶν ὄντων τὰ μέν ἐστιν ἐφ᾽ ἡμῖν τὰ δὲ οὐκ ἐφ᾽ ἡμῖν. "
EN = "Of things that exist, some are up to us and some are not up to us. "

TRIAGE_ON = {"ELEUTHERIA_RELEVANCE_TRIAGE": "true"}


class _StubLLM:
    """Records calls; returns queued responses (a string, or an exception to raise)."""

    def __init__(self, *responses, delay: float = 0.0) -> None:
        self._responses = list(responses)
        self._delay = delay
        self.calls: list[dict] = []

    async def generate(self, prompt: str, **kwargs):
        self.calls.append({"prompt": prompt, **kwargs})
        if self._delay:
            await asyncio.sleep(self._delay)
        response = self._responses.pop(0) if self._responses else '{"scores": []}'
        if isinstance(response, Exception):
            raise response
        return response


def _passage(pid: str, *, author: str = "Epictetus", size: int = 1) -> PassageRef:
    return PassageRef(
        passage_id=pid,
        work="Dissertationes",
        author=author,
        canonical_ref="1.1.1",
        original_text=GREEK * size,
        english_text=EN * size,
        language="grc",
    )


def _position(pid: str, *, claim_size: int = 1) -> GroundedPosition:
    return GroundedPosition(
        position_id=pid,
        holder=f"Scholar {pid}",
        holder_node_id=f"scholar_{pid}",
        claim=(
            "The capacity to do otherwise is read as a one-sided power over assent. "
            * claim_size
        ),
        publication="Determinism and Freedom",
        page_grounding="p. 234",
    )


def _map(*, positions: int = 2, passages: int = 2, frames: int = 1) -> ControversyMap:
    cmap = ControversyMap(
        question_frame="Did Epictetus think freedom is up to us?",
        shape=AnswerShape.SURVEY_OF_DEBATES,
    )
    for f in range(frames):
        cmap.frames.append(
            ControversyFrame(
                frame_id=f"f{f}",
                title=f"Fault line {f}",
                period="Imperial",
                positions=[
                    _position(f"f{f}p{i}", claim_size=12) for i in range(positions)
                ],
                links=[
                    DialecticalLink(
                        relation="opposes", from_id=f"f{f}p0", to_id=f"f{f}p1"
                    )
                ]
                if positions >= 2
                else [],
                contested_passages=[
                    _passage(f"f{f}x{i}", size=8) for i in range(passages)
                ],
                completeness=FrameCompleteness(incident_edge_count=3),
            )
        )
    return cmap


# ── 1. parsing ───────────────────────────────────────────────────────────────


class TestParsing:
    def test_valid_object_form(self):
        id_map = {"0": "pos:a", "1": "pos:b"}
        raw = '{"scores": [{"id": "0", "score": 9}, {"id": "1", "score": 2.5}]}'
        assert parse_triage_scores(raw, id_map) == {"pos:a": 9.0, "pos:b": 2.5}

    def test_bare_array_and_code_fence(self):
        id_map = {"0": "pos:a"}
        raw = '```json\n[{"id": "0", "score": 7}]\n```'
        assert parse_triage_scores(raw, id_map) == {"pos:a": 7.0}

    def test_partial_response_keeps_the_valid_part(self):
        id_map = {"0": "pos:a", "1": "pos:b", "2": "pos:c"}
        raw = (
            '{"scores": [{"id": "0", "score": 8}, {"id": "1"}, '
            '{"id": "9", "score": 5}, "junk", {"id": "2", "score": "nope"}]}'
        )
        assert parse_triage_scores(raw, id_map) == {"pos:a": 8.0}

    def test_malformed_yields_nothing(self):
        id_map = {"0": "pos:a"}
        assert parse_triage_scores("I think item 0 is very relevant!", id_map) == {}
        assert parse_triage_scores("", id_map) == {}
        assert parse_triage_scores("{", id_map) == {}

    def test_scores_are_clamped_and_string_numbers_accepted(self):
        id_map = {"0": "pos:a", "1": "pos:b", "2": "pos:c"}
        raw = '[{"id":"0","score":99},{"id":"1","score":-4},{"id":"2","score":"6.5"}]'
        assert parse_triage_scores(raw, id_map) == {
            "pos:a": 10.0,
            "pos:b": 0.0,
            "pos:c": 6.5,
        }

    def test_alternate_wrapper_keys(self):
        id_map = {"0": "pos:a"}
        raw = '{"results": [{"item_id": "0", "relevance": 4}]}'
        assert parse_triage_scores(raw, id_map) == {"pos:a": 4.0}


# ── 2. configuration ─────────────────────────────────────────────────────────


class TestConfiguration:
    def test_off_by_default(self):
        with patch.dict("os.environ", {}, clear=True):
            assert relevance_triage_enabled() is False

    def test_flag_on(self):
        with patch.dict("os.environ", TRIAGE_ON, clear=True):
            assert relevance_triage_enabled() is True

    def test_model_defaults_to_the_gemini_light_model_behind_the_proxy(self):
        env = {"GEMINI_PROXY_BASE_URL": "http://pragma-gemini-proxy:8320/v1"}
        with patch.dict("os.environ", env, clear=True):
            assert triage_model() == "gemini-3.7-flash-high"

    def test_model_falls_back_to_the_utility_tier(self):
        with patch.dict("os.environ", {}, clear=True):
            assert triage_model() == ""

    def test_model_pin_wins(self):
        env = {
            "GEMINI_PROXY_BASE_URL": "http://pragma-gemini-proxy:8320/v1",
            "ELEUTHERIA_TRIAGE_MODEL": "claude-sonnet-5",
        }
        with patch.dict("os.environ", env, clear=True):
            assert triage_model() == "claude-sonnet-5"


# ── 3. scoring ───────────────────────────────────────────────────────────────


class TestScoring:
    @pytest.mark.asyncio
    async def test_single_batch_maps_scores_back_to_keys(self):
        items = [TriageItem(key=f"pos:{i}", snippet=f"claim {i}") for i in range(3)]
        llm = _StubLLM('{"scores": [{"id": "0", "score": 9}, {"id": "2", "score": 1}]}')
        with patch.dict("os.environ", {}, clear=True):
            result = await score_relevance("q?", items, llm)

        assert result.scores == {"pos:0": 9.0, "pos:2": 1.0}
        assert result.batches == 1
        assert result.failures == 0
        assert len(llm.calls) == 1
        call = llm.calls[0]
        assert call["tier"] == "utility"
        assert call["temperature"] == 0.0
        assert "claim 0" in call["prompt"]

    @pytest.mark.asyncio
    async def test_batching(self):
        items = [
            TriageItem(key=f"pos:{i}", snippet=f"claim {i}")
            for i in range(BATCH_SIZE * 2 + 5)
        ]
        llm = _StubLLM(*(['{"scores": []}'] * 3))
        with patch.dict("os.environ", {}, clear=True):
            result = await score_relevance("q?", items, llm)

        assert result.batches == 3
        assert len(llm.calls) == 3

    @pytest.mark.asyncio
    async def test_item_ceiling(self):
        items = [TriageItem(key=f"pos:{i}", snippet="x") for i in range(200)]
        env = {"ELEUTHERIA_TRIAGE_MAX_ITEMS": str(BATCH_SIZE)}
        with patch.dict("os.environ", env, clear=True):
            result = await score_relevance("q?", items, _StubLLM())
        assert result.items_submitted == BATCH_SIZE
        assert result.batches == 1

    @pytest.mark.asyncio
    async def test_failure_is_contained(self):
        items = [TriageItem(key="pos:0", snippet="claim")]
        llm = _StubLLM(RuntimeError("provider down"))
        with patch.dict("os.environ", {}, clear=True):
            result = await score_relevance("q?", items, llm)

        assert result.scores == {}
        assert result.failures == 1

    @pytest.mark.asyncio
    async def test_partial_batch_failure_keeps_the_other_batch(self):
        items = [
            TriageItem(key=f"pos:{i}", snippet=f"claim {i}")
            for i in range(BATCH_SIZE + 1)
        ]
        llm = _StubLLM('{"scores": [{"id": "0", "score": 10}]}', RuntimeError("boom"))
        with patch.dict("os.environ", {}, clear=True):
            result = await score_relevance("q?", items, llm)

        assert result.scores == {"pos:0": 10.0}
        assert result.failures == 1
        assert result.batches == 2

    @pytest.mark.asyncio
    async def test_timeout_returns_no_scores_and_does_not_raise(self):
        items = [TriageItem(key="pos:0", snippet="claim")]
        llm = _StubLLM('{"scores": [{"id": "0", "score": 10}]}', delay=5.0)
        with patch.dict("os.environ", {"ELEUTHERIA_TRIAGE_TIMEOUT": "0.1"}, clear=True):
            result = await score_relevance("q?", items, llm)

        assert result.scores == {}
        assert result.failures == 1

    @pytest.mark.asyncio
    async def test_empty_items_never_calls_the_model(self):
        llm = _StubLLM()
        result = await score_relevance("q?", [], llm)
        assert result.scores == {}
        assert llm.calls == []


# ── 4. the stage seam ────────────────────────────────────────────────────────


class TestStageSeam:
    @pytest.mark.asyncio
    async def test_disabled_by_default_never_calls_the_model(self):
        llm = _StubLLM('{"scores": [{"id": "0", "score": 10}]}')
        with patch.dict("os.environ", {}, clear=True):
            assert await triage_controversy_map(_map(), llm) is None
        assert llm.calls == []

    @pytest.mark.asyncio
    async def test_enabled_returns_scores(self):
        cmap = _map(positions=2, passages=2)
        llm = _StubLLM('{"scores": [{"id": "0", "score": 9}]}')
        with patch.dict("os.environ", TRIAGE_ON, clear=True):
            scores = await triage_controversy_map(cmap, llm)
        assert scores == {position_key("f0p0"): 9.0}

    @pytest.mark.asyncio
    async def test_failure_returns_none(self):
        llm = _StubLLM(RuntimeError("provider down"))
        with patch.dict("os.environ", TRIAGE_ON, clear=True):
            assert await triage_controversy_map(_map(), llm) is None

    def test_collected_items_exclude_each_frame_anchor_passage(self):
        cmap = _map(positions=2, passages=3, frames=2)
        cmap.exegesis_units.append(_passage("ex0", author="Chrysippus"))
        keys = {item.key for item in collect_triage_items(cmap)}

        assert position_key("f0p0") in keys
        assert exegesis_key("ex0") in keys
        # Frame anchors are never scored: they must survive whatever the model says.
        assert passage_key("f0x0") not in keys
        assert passage_key("f1x0") not in keys
        assert passage_key("f0x1") in keys

    def test_snippets_are_capped(self):
        cmap = _map(positions=1, passages=1)
        for item in collect_triage_items(cmap):
            assert len(item.snippet) <= SNIPPET_CHARS + 1  # cap + ellipsis


# ── 5. consumption in the fitter ─────────────────────────────────────────────


class TestPrioritize:
    def test_no_scores_keeps_the_order(self):
        items = ["a", "b", "c"]
        assert prioritize(items, lambda x: f"pos:{x}", None) == items
        assert prioritize(items, lambda x: f"pos:{x}", {}) == items

    def test_scores_reorder_highest_first(self):
        items = ["a", "b", "c"]
        scores = {"pos:a": 1.0, "pos:c": 9.0}
        assert prioritize(items, lambda x: f"pos:{x}", scores) == ["c", "b", "a"]

    def test_unscored_items_sit_at_the_neutral_mark(self):
        items = ["a", "b"]
        scores = {"pos:a": NEUTRAL_SCORE + 1}
        assert prioritize(items, lambda x: f"pos:{x}", scores) == ["a", "b"]
        scores = {"pos:a": NEUTRAL_SCORE - 1}
        assert prioritize(items, lambda x: f"pos:{x}", scores) == ["b", "a"]


class TestShedOrdering:
    def _rendered(self, cmap: ControversyMap, budget: int, relevance=None) -> str:
        layer, _stats = fit_controversy_frames_layer(cmap, budget, relevance=relevance)
        return layer

    def test_high_scored_position_survives_where_a_low_one_sheds(self):
        cmap = _map(positions=6, passages=1)
        budget = 800

        baseline = self._rendered(cmap, budget)
        # Without triage the round-robin head survives and the tail is shed.
        assert "[P_f0p0]" in baseline
        assert "[P_f0p5]" not in baseline

        relevance = {
            position_key("f0p5"): 10.0,
            **{position_key(f"f0p{i}"): 0.0 for i in range(5)},
        }
        triaged = self._rendered(cmap, budget, relevance)
        assert "[P_f0p5]" in triaged
        assert "[P_f0p0]" not in triaged

    def test_low_scored_exegesis_sheds_first(self):
        cmap = _map(positions=2, passages=1)
        cmap.exegesis_units = [
            _passage("ex0", author="Chrysippus", size=60),
            _passage("ex1", author="Alexander", size=60),
        ]
        budget = 1_700

        relevance = {exegesis_key("ex0"): 0.0, exegesis_key("ex1"): 10.0}
        layer, stats = fit_controversy_frames_layer(cmap, budget, relevance=relevance)
        assert stats["exegesis_kept"] < stats["exegesis_total"]
        assert "passage_ex1" in layer
        assert "passage_ex0" not in layer

    def test_frame_anchor_passage_is_never_reordered_out(self):
        cmap = _map(positions=2, passages=3, frames=2)
        relevance = {
            passage_key("f0x0"): 0.0,
            passage_key("f1x0"): 0.0,
            passage_key("f0x2"): 10.0,
        }
        ordered = _relevance_passage_order(cmap, relevance)
        head = [pref.passage_id for pref in ordered[:2]]
        assert set(head) == {"f0x0", "f1x0"}
        # Beyond the anchors the highest-scored passage leads.
        assert ordered[2].passage_id == "f0x2"

    def test_fitting_is_unchanged_without_relevance(self):
        cmap = _map(positions=6, passages=2)
        assert self._rendered(cmap, 4_000) == self._rendered(cmap, 4_000, None)

    def test_map_is_never_mutated(self):
        cmap = _map(positions=4, passages=2)
        before = [[p.position_id for p in frame.positions] for frame in cmap.frames] + [
            [p.passage_id for p in frame.contested_passages] for frame in cmap.frames
        ]
        relevance = {position_key("f0p3"): 10.0, position_key("f0p0"): 0.0}
        fit_controversy_frames_layer(cmap, 2_000, relevance=relevance)
        after = [[p.position_id for p in frame.positions] for frame in cmap.frames] + [
            [p.passage_id for p in frame.contested_passages] for frame in cmap.frames
        ]
        assert before == after
