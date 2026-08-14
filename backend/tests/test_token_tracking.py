"""Tests for the token + USD cost tracking pipeline.

Covers:

* :mod:`eleutheria_graphrag.services.llm_pricing` — price table, USD math,
  ``TokenUsage`` factories.
* :class:`backend.services.trace_writer.TraceWriter` — aggregation of
  per-call usage into per-agent / per-model / per-provider running totals,
  plus the persisted row contract.
* :mod:`backend.routes.opencode_proxy._synthesise_cost_events` —
  ``cost_summary`` envelope shape emitted on ``final_answer``.

The DB layer is stubbed via an in-memory recorder so no Postgres is needed.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from eleutheria_graphrag.services.llm_pricing import (
    TokenUsage,
    estimate_cost_usd,
    get_provider_price,
)

from backend.routes.opencode_proxy import (
    _register_trace_writer,
    _reset_trace_writers,
    _synthesise_cost_events,
)
from backend.services.trace_writer import TraceWriter

# ---------- llm_pricing ----------


def test_default_codex_price_matches_configured_rate() -> None:
    price = get_provider_price("codex")
    assert price.input_per_m == pytest.approx(1.25)
    assert price.output_per_m == pytest.approx(10.00)


def test_only_supported_providers_are_priced() -> None:
    """A retired provider must not silently keep a price row."""
    for retired in ("fireworks", "moonshot", "kimi", "openrouter"):
        price = get_provider_price(retired)
        assert price.input_per_m == 0.0
        assert price.output_per_m == 0.0


def test_env_override_changes_codex_price(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CODEX_PRICE_INPUT_USD_PER_M", "1.10")
    monkeypatch.setenv("CODEX_PRICE_OUTPUT_USD_PER_M", "4.20")
    price = get_provider_price("codex")
    assert price.input_per_m == pytest.approx(1.10)
    assert price.output_per_m == pytest.approx(4.20)


def test_estimate_cost_usd_known_pair() -> None:
    # 10k prompt + 2k completion at default codex rates
    # = (10_000 * 1.25 + 2_000 * 10.00) / 1_000_000 = 0.0125 + 0.02 = 0.0325
    cost = estimate_cost_usd(
        provider="codex", prompt_tokens=10_000, completion_tokens=2_000
    )
    assert cost == pytest.approx(0.0325)


def test_token_usage_from_openai_usage_handles_missing_total() -> None:
    usage = TokenUsage.from_openai_usage(
        {"prompt_tokens": 1_000, "completion_tokens": 500},
        model="gpt-5.6-sol",
        provider="codex",
        agent_id="scholar-orchestrator",
    )
    assert usage is not None
    assert usage.total_tokens == 1_500
    assert usage.agent_id == "scholar-orchestrator"
    assert usage.estimated_cost_usd == pytest.approx(
        (1_000 * 1.25 + 500 * 10.00) / 1_000_000
    )


def test_token_usage_from_openai_usage_returns_none_when_empty() -> None:
    assert TokenUsage.from_openai_usage(None, model="x", provider="y") is None
    assert (
        TokenUsage.from_openai_usage(
            {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            model="x",
            provider="y",
        )
        is None
    )


def test_token_usage_from_gemini_metadata_uses_response_tokens() -> None:
    usage = TokenUsage.from_gemini_metadata(
        {
            "promptTokenCount": 800,
            "candidatesTokenCount": 200,
            "totalTokenCount": 1_000,
        },
        model="gemini-3.1-pro-preview",
    )
    assert usage is not None
    assert usage.provider == "gemini"
    assert usage.total_tokens == 1_000
    # 800 * 1.25 + 200 * 5.00 = 1000 + 1000 = 2000 ; /1e6 = 0.002
    assert usage.estimated_cost_usd == pytest.approx(0.002)


def test_token_usage_to_event_includes_required_fields() -> None:
    usage = TokenUsage(
        prompt_tokens=10,
        completion_tokens=5,
        total_tokens=15,
        model="kimi-k2p6",
        provider="codex",
        estimated_cost_usd=0.000025,
        agent_id="concept-mapper",
    )
    payload = usage.to_event()
    assert payload == {
        "type": "tokens_used",
        "agent_id": "concept-mapper",
        "model": "kimi-k2p6",
        "provider": "codex",
        "prompt_tokens": 10,
        "completion_tokens": 5,
        "total_tokens": 15,
        "estimated_cost_usd": 0.000025,
    }


# ---------- TraceWriter aggregation ----------


class _RecordingDB:
    def __init__(self) -> None:
        self.executes: list[tuple[str, tuple[Any, ...]]] = []

    def is_connected(self) -> bool:
        return True

    async def execute(self, sql: str, *args: Any) -> None:
        self.executes.append((sql, args))


@pytest.fixture
def writer() -> TraceWriter:
    db = _RecordingDB()
    return TraceWriter(
        db=db,  # type: ignore[arg-type]
        trace_id="ses_token_test",
        query="Bobzien on Stoic compatibilism?",
        user_id=None,
        mode="deep",
    )


async def test_record_token_usage_accumulates_totals(writer: TraceWriter) -> None:
    await writer.record_agent_invocation("scholar-orchestrator")
    await writer.record_token_usage(
        "scholar-orchestrator",
        TokenUsage(
            prompt_tokens=4_000,
            completion_tokens=500,
            total_tokens=4_500,
            model="kimi-k2p6",
            provider="codex",
            estimated_cost_usd=0.005100,
            agent_id="scholar-orchestrator",
        ),
    )
    await writer.record_token_usage(
        "scholar-orchestrator",
        TokenUsage(
            prompt_tokens=2_000,
            completion_tokens=200,
            total_tokens=2_200,
            model="kimi-k2p6",
            provider="codex",
            estimated_cost_usd=0.002380,
            agent_id="scholar-orchestrator",
        ),
    )
    totals = writer.get_running_totals()
    assert totals["total_tokens"] == 6_700
    assert totals["total_cost_usd"] == pytest.approx(0.00748)
    assert totals["by_agent"]["scholar-orchestrator"]["tokens"] == 6_700
    assert totals["by_agent"]["scholar-orchestrator"]["calls"] == 2
    assert totals["by_model"]["kimi-k2p6"]["calls"] == 2
    assert totals["by_provider"]["codex"]["prompt_tokens"] == 6_000
    assert totals["by_provider"]["codex"]["completion_tokens"] == 700


async def test_finalize_persists_cost_columns(writer: TraceWriter) -> None:
    await writer.record_agent_invocation("scholar-orchestrator")
    await writer.record_token_usage(
        "scholar-orchestrator",
        TokenUsage(
            prompt_tokens=1_000,
            completion_tokens=200,
            total_tokens=1_200,
            model="kimi-k2p6",
            provider="codex",
            estimated_cost_usd=0.001530,
        ),
    )
    await writer.finalize(final_answer="...", citations=[])
    db = writer._db  # noqa: SLF001 — internal test access
    assert isinstance(db, _RecordingDB)
    assert db.executes, "finalize did not call execute"
    sql, args = db.executes[-1]
    assert "total_cost_usd" in sql
    assert "token_breakdown" in sql
    assert "provider_usage" in sql
    # Positional args: total_tokens at $17, total_cost at $18.
    assert args[16] == 1_200
    assert args[17] == pytest.approx(0.001530)
    breakdown = json.loads(args[18])
    assert "by_agent" in breakdown and "by_model" in breakdown
    provider = json.loads(args[19])
    assert provider["codex"]["calls"] == 1


# ---------- synthetic SSE envelopes ----------


async def test_synthesise_cost_events_emits_summary_on_final_answer(
    writer: TraceWriter,
) -> None:
    _reset_trace_writers()
    _register_trace_writer("ses_token_test", writer)
    await writer.record_agent_invocation("scholar-orchestrator")
    await writer.record_token_usage(
        "scholar-orchestrator",
        TokenUsage(
            prompt_tokens=12_000,
            completion_tokens=348,
            total_tokens=12_348,
            model="kimi-k2p6",
            provider="codex",
            estimated_cost_usd=0.0212,
        ),
    )
    events = _synthesise_cost_events(
        "ses_token_test", {"type": "final_answer", "properties": {}}
    )
    types = [e["type"] for e in events]
    assert "cost_summary" in types
    summary = next(e for e in events if e["type"] == "cost_summary")
    assert summary["total_tokens"] == 12_348
    assert summary["total_cost_usd"] == pytest.approx(0.0212)
    assert "kimi-k2p6" in summary["by_model"]
    _reset_trace_writers()


async def test_synthesise_cost_events_emits_rollup_on_subagent_complete(
    writer: TraceWriter,
) -> None:
    _reset_trace_writers()
    _register_trace_writer("ses_token_test", writer)
    await writer.record_agent_invocation("scholar-orchestrator")
    await writer.record_token_usage(
        "scholar-orchestrator",
        TokenUsage(
            prompt_tokens=10,
            completion_tokens=2,
            total_tokens=12,
            model="kimi-k2p6",
            provider="codex",
            estimated_cost_usd=0.000017,
        ),
    )
    events = _synthesise_cost_events(
        "ses_token_test",
        {"type": "subagent_complete", "properties": {"agent_id": "concept-mapper"}},
    )
    assert events and events[0]["type"] == "tokens_used_rollup"
    assert events[0]["total_tokens"] == 12
    _reset_trace_writers()
