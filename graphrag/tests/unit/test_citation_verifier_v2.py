"""Unit tests for the adversarial v2 citation verifier."""

from __future__ import annotations

import asyncio
import json
from typing import Any
from unittest.mock import AsyncMock

import pytest

from eleutheria_graphrag.agents.sse_emitter import SSEEmitter
from eleutheria_graphrag.models.verification import (
    CitationStatus,
    DraftClaim,
    SynthesizedDraft,
)
from eleutheria_graphrag.services.citation_verifier_v2 import (
    CitationVerifierV2,
    _parse_verdict,
)

# --------------------------------------------------------------------------- helpers


def _llm_returning(*responses: str) -> AsyncMock:
    """Return an AsyncMock whose .generate() yields ``responses`` in order."""
    llm = AsyncMock()
    llm.generate = AsyncMock(side_effect=list(responses))
    return llm


def _fetcher(passages: dict[str, str | None]) -> Any:
    """Return an async passage-fetcher backed by a dict.

    ``None`` value triggers the MISSING path (matches a real "0 rows" result).
    """

    async def fetch(citation_id: str) -> dict[str, Any] | None:
        text = passages.get(citation_id)
        if text is None:
            return None
        return {"text": text, "label": citation_id}

    return fetch


def _verdict_json(
    status: str,
    reasoning: str = "test reasoning",
    suggested_action: str = "",
) -> str:
    return json.dumps(
        {
            "status": status,
            "reasoning": reasoning,
            "suggested_action": suggested_action,
        }
    )


# --------------------------------------------------------------------------- tests


class TestVerifyOne:
    """Single-citation verdicts across the four statuses."""

    @pytest.mark.asyncio
    async def test_verified_status(self) -> None:
        llm = _llm_returning(
            _verdict_json("VERIFIED", "explicit clause asserts the claim")
        )
        verifier = CitationVerifierV2(
            llm=llm,
            passage_fetcher=_fetcher(
                {"p1": "Chrysippus distinguishes perfect and auxiliary causes."}
            ),
        )
        check = await verifier.verify_one(
            "Chrysippus distinguished perfect from auxiliary causes.",
            "p1",
        )
        assert check.status is CitationStatus.VERIFIED
        assert check.is_passing
        assert check.passage_excerpt.startswith("Chrysippus distinguishes")
        llm.generate.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_weak_status(self) -> None:
        llm = _llm_returning(
            _verdict_json(
                "WEAK",
                '"discusses Chrysippus on fate" but never says assent is up to us',
            )
        )
        verifier = CitationVerifierV2(
            llm=llm,
            passage_fetcher=_fetcher(
                {"p1": "Chrysippus on fate as the sequence of causes."}
            ),
        )
        check = await verifier.verify_one("Chrysippus held assent is up to us.", "p1")
        assert check.status is CitationStatus.WEAK
        assert not check.is_passing

    @pytest.mark.asyncio
    async def test_rejected_status(self) -> None:
        llm = _llm_returning(
            _verdict_json("REJECTED", '"passage is by Marcus Aurelius, not Epictetus"')
        )
        verifier = CitationVerifierV2(
            llm=llm,
            passage_fetcher=_fetcher({"p1": "Marcus Aurelius reflects on virtue."}),
        )
        check = await verifier.verify_one("Epictetus argued for assent.", "p1")
        assert check.status is CitationStatus.REJECTED
        assert not check.is_passing

    @pytest.mark.asyncio
    async def test_missing_when_fetcher_returns_none(self) -> None:
        llm = AsyncMock()  # LLM should NOT be called when passage is missing
        verifier = CitationVerifierV2(llm=llm, passage_fetcher=_fetcher({"p1": None}))
        check = await verifier.verify_one("Any claim.", "p1")
        assert check.status is CitationStatus.MISSING
        assert check.suggested_action == "remove citation"
        llm.generate.assert_not_called()

    @pytest.mark.asyncio
    async def test_missing_when_fetcher_raises(self) -> None:
        async def boom(_: str) -> dict[str, Any] | None:
            raise RuntimeError("DB connection died")

        llm = AsyncMock()
        verifier = CitationVerifierV2(llm=llm, passage_fetcher=boom)
        check = await verifier.verify_one("Any claim.", "p1")
        assert check.status is CitationStatus.MISSING
        llm.generate.assert_not_called()


class TestLLMRetry:
    """LLM failures must NOT silently pass — they fall back to WEAK."""

    @pytest.mark.asyncio
    async def test_falls_back_to_weak_after_retries(self) -> None:
        llm = AsyncMock()
        llm.generate = AsyncMock(side_effect=RuntimeError("rate limited"))
        verifier = CitationVerifierV2(
            llm=llm,
            passage_fetcher=_fetcher({"p1": "Some valid passage text."}),
            retries=3,
        )
        check = await verifier.verify_one("Claim.", "p1")
        assert check.status is CitationStatus.WEAK
        assert "Verifier unable to assess" in check.reasoning
        assert llm.generate.await_count == 3

    @pytest.mark.asyncio
    async def test_recovers_on_second_attempt(self) -> None:
        llm = AsyncMock()
        llm.generate = AsyncMock(
            side_effect=[
                RuntimeError("transient"),
                _verdict_json("VERIFIED", "ok"),
            ]
        )
        verifier = CitationVerifierV2(
            llm=llm,
            passage_fetcher=_fetcher({"p1": "Some passage."}),
            retries=3,
        )
        check = await verifier.verify_one("Claim.", "p1")
        assert check.status is CitationStatus.VERIFIED
        assert llm.generate.await_count == 2


class TestParallelism:
    """asyncio.gather + Semaphore concurrency cap."""

    @pytest.mark.asyncio
    async def test_concurrency_capped(self) -> None:
        in_flight = 0
        peak = 0
        lock = asyncio.Lock()

        async def slow_generate(_prompt: str, **_: Any) -> str:
            nonlocal in_flight, peak
            async with lock:
                in_flight += 1
                peak = max(peak, in_flight)
            await asyncio.sleep(0.02)
            async with lock:
                in_flight -= 1
            return _verdict_json("VERIFIED", "ok")

        llm = AsyncMock()
        llm.generate = AsyncMock(side_effect=slow_generate)
        passages = {f"p{i}": f"text {i}" for i in range(20)}
        verifier = CitationVerifierV2(
            llm=llm,
            passage_fetcher=_fetcher(passages),
            concurrency=3,
        )
        draft = SynthesizedDraft(
            claims=[DraftClaim(claim=f"c{i}", citation_id=f"p{i}") for i in range(20)]
        )
        report = await verifier.verify_draft(draft)
        assert report.total == 20
        assert peak <= 3, f"concurrency cap breached: peak={peak}"


class TestAggregateReport:
    """Aggregate counters, thresholds, abort flag."""

    @pytest.mark.asyncio
    async def test_report_counts_and_warning_threshold(self) -> None:
        # 5 citations: 3 VERIFIED, 1 WEAK, 1 REJECTED → rejection rate 20% → warning
        responses = [
            _verdict_json("VERIFIED"),
            _verdict_json("VERIFIED"),
            _verdict_json("VERIFIED"),
            _verdict_json("WEAK", '"only consistent, not asserted"'),
            _verdict_json("REJECTED", '"passage is by a different author"'),
        ]
        llm = _llm_returning(*responses)
        passages = {f"p{i}": "text" for i in range(5)}
        verifier = CitationVerifierV2(
            llm=llm,
            passage_fetcher=_fetcher(passages),
            concurrency=1,  # deterministic ordering for the side_effect list
        )
        draft = SynthesizedDraft(
            claims=[DraftClaim(claim=f"c{i}", citation_id=f"p{i}") for i in range(5)]
        )
        report = await verifier.verify_draft(draft)
        assert report.total == 5
        assert report.verified == 3
        assert report.weak == 1
        assert report.rejected == 1
        assert report.missing == 0
        assert report.rejection_rate == pytest.approx(0.20)
        assert report.warning is not None
        assert not report.aborted
        assert set(report.flagged_for_rewrite) == {"p3", "p4"}

    @pytest.mark.asyncio
    async def test_abort_threshold_triggered(self) -> None:
        # 4 citations, 3 REJECTED → 75% → abort
        responses = [
            _verdict_json("VERIFIED"),
            _verdict_json("REJECTED", '"contradicts the claim"'),
            _verdict_json("REJECTED", '"different topic"'),
            _verdict_json("REJECTED", '"wrong author"'),
        ]
        llm = _llm_returning(*responses)
        passages = {f"p{i}": "text" for i in range(4)}
        verifier = CitationVerifierV2(
            llm=llm,
            passage_fetcher=_fetcher(passages),
            concurrency=1,
        )
        draft = SynthesizedDraft(
            claims=[DraftClaim(claim=f"c{i}", citation_id=f"p{i}") for i in range(4)]
        )
        report = await verifier.verify_draft(draft)
        assert report.aborted is True
        assert report.rejection_rate == pytest.approx(0.75)
        assert report.warning and "abort threshold" in report.warning

    @pytest.mark.asyncio
    async def test_empty_draft_returns_empty_report(self) -> None:
        llm = AsyncMock()
        verifier = CitationVerifierV2(llm=llm, passage_fetcher=_fetcher({}))
        report = await verifier.verify_draft(SynthesizedDraft())
        assert report.total == 0
        assert report.warning is None
        assert not report.aborted
        llm.generate.assert_not_called()


class TestSSEEmission:
    """The verifier emits a citation_verified SSE event per check."""

    @pytest.mark.asyncio
    async def test_emits_one_event_per_check(self) -> None:
        queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()
        emitter = SSEEmitter(queue)
        llm = _llm_returning(
            _verdict_json("VERIFIED"),
            _verdict_json("REJECTED", '"wrong author"'),
        )
        verifier = CitationVerifierV2(
            llm=llm,
            passage_fetcher=_fetcher({"p1": "good", "p2": "bad"}),
            emitter=emitter,
            concurrency=1,
        )
        draft = SynthesizedDraft(
            claims=[
                DraftClaim(claim="c1", citation_id="p1"),
                DraftClaim(claim="c2", citation_id="p2"),
            ]
        )
        await verifier.verify_draft(draft)

        events: list[dict[str, Any]] = []
        while not queue.empty():
            event = queue.get_nowait()
            if event is not None:
                events.append(event)
        assert len(events) == 2
        assert all(e["type"] == "citation_verified" for e in events)
        statuses = {e["passage_id"]: e["status"] for e in events}
        assert statuses == {"p1": "VERIFIED", "p2": "REJECTED"}
        # The boolean projection matches frontend expectation.
        verified_flags = {e["passage_id"]: e["verified"] for e in events}
        assert verified_flags == {"p1": True, "p2": False}


class TestVerdictParsing:
    """The JSON parser tolerates fences and rejects bad shapes."""

    def test_parses_plain_json(self) -> None:
        parsed = _parse_verdict('{"status": "VERIFIED", "reasoning": "ok"}')
        assert parsed is not None
        assert parsed["status"] is CitationStatus.VERIFIED

    def test_strips_markdown_fence(self) -> None:
        parsed = _parse_verdict('```json\n{"status":"WEAK","reasoning":"x"}\n```')
        assert parsed is not None
        assert parsed["status"] is CitationStatus.WEAK

    def test_rejects_unknown_status(self) -> None:
        assert _parse_verdict('{"status":"MAYBE","reasoning":"x"}') is None

    def test_rejects_non_json(self) -> None:
        assert _parse_verdict("not json at all") is None

    def test_parses_unescaped_inner_double_quotes(self) -> None:
        """The G2 killer: the model embeds a verbatim quote inside reasoning.

        The prompt used to demand a double-quoted verbatim quote *inside* the
        ``reasoning`` JSON string, producing invalid JSON that json.loads
        rejected — every WEAK/REJECTED verdict failed to parse, pinning
        verified_rate at 0.0. The repair pass must recover it.
        """
        raw = (
            '{"status": "WEAK", "reasoning": "The passage says "fate is the '
            'sequence of causes" but never asserts assent is up to us.", '
            '"suggested_action": ""}'
        )
        parsed = _parse_verdict(raw)
        assert parsed is not None
        assert parsed["status"] is CitationStatus.WEAK
        assert "fate is the sequence of causes" in parsed["reasoning"]

    def test_parses_prose_wrapped_json(self) -> None:
        raw = (
            "Here is my adversarial verdict:\n"
            '{"status": "REJECTED", "reasoning": "wrong author"}\n'
            "Let me know if you need more."
        )
        parsed = _parse_verdict(raw)
        assert parsed is not None
        assert parsed["status"] is CitationStatus.REJECTED

    def test_extracts_first_of_multiple_objects(self) -> None:
        """Greedy regex grabbed first { to last } — must take the FIRST object."""
        raw = (
            '{"status": "VERIFIED", "reasoning": "ok"} '
            '{"status": "REJECTED", "reasoning": "noise"}'
        )
        parsed = _parse_verdict(raw)
        assert parsed is not None
        assert parsed["status"] is CitationStatus.VERIFIED

    def test_tolerates_trailing_comma(self) -> None:
        parsed = _parse_verdict('{"status":"VERIFIED","reasoning":"ok",}')
        assert parsed is not None
        assert parsed["status"] is CitationStatus.VERIFIED

    def test_maps_field_name_variants(self) -> None:
        """verdict/rationale instead of status/reasoning; status synonym."""
        parsed = _parse_verdict(
            '{"verdict": "reject", "rationale": "different topic", '
            '"evidence_quote": "Marcus Aurelius reflects"}'
        )
        assert parsed is not None
        assert parsed["status"] is CitationStatus.REJECTED
        assert parsed["reasoning"].startswith("different topic")
        # evidence_quote is folded into reasoning for downstream consumers.
        assert "Marcus Aurelius reflects" in parsed["reasoning"]

    def test_folds_evidence_quote_into_reasoning(self) -> None:
        parsed = _parse_verdict(
            '{"status":"REJECTED","reasoning":"mismatch",'
            '"evidence_quote":"by Plato not Aristotle"}'
        )
        assert parsed is not None
        assert '"by Plato not Aristotle"' in parsed["reasoning"]

    def test_fence_without_object_returns_none(self) -> None:
        assert _parse_verdict("```json\n\n```") is None


class TestParseErrorVsWeak:
    """A parse failure must NOT masquerade as a real WEAK verdict."""

    @pytest.mark.asyncio
    async def test_unparseable_output_flags_parse_error(self) -> None:
        # Model returns junk on every retry → fall back to WEAK, but flagged.
        llm = _llm_returning("not json", "still not json", "garbage")
        verifier = CitationVerifierV2(
            llm=llm,
            passage_fetcher=_fetcher({"p1": "Some valid passage text."}),
            retries=3,
        )
        check = await verifier.verify_one("Claim.", "p1")
        assert check.status is CitationStatus.WEAK
        assert check.parse_error is True
        assert "unable to assess" in check.reasoning.lower()
        assert llm.generate.await_count == 3

    @pytest.mark.asyncio
    async def test_real_weak_verdict_not_flagged(self) -> None:
        llm = _llm_returning(_verdict_json("WEAK", '"only consistent"'))
        verifier = CitationVerifierV2(
            llm=llm,
            passage_fetcher=_fetcher({"p1": "Some valid passage text."}),
        )
        check = await verifier.verify_one("Claim.", "p1")
        assert check.status is CitationStatus.WEAK
        assert check.parse_error is False

    @pytest.mark.asyncio
    async def test_requests_json_mime_type(self) -> None:
        llm = _llm_returning(_verdict_json("VERIFIED"))
        verifier = CitationVerifierV2(
            llm=llm,
            passage_fetcher=_fetcher({"p1": "text"}),
        )
        await verifier.verify_one("Claim.", "p1")
        _, kwargs = llm.generate.await_args
        assert kwargs.get("response_mime_type") == "application/json"
