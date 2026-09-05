"""Unit tests for :mod:`backend.services.answer_cache`.

The :class:`DatabaseService` is fully stubbed with ``AsyncMock`` so the
tests run without any Postgres connection. We exercise:

* normalisation (whitespace, case, polytonic preservation, NFC)
* cache-key stability + sensitivity to (model, retrieval_mode)
* miss / hit / TTL-expiry / KG-version invalidation semantics
* hit-count increment side-effect on a hit
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock

import pytest

from backend.services.answer_cache import AnswerCache

# ---------- normalisation ----------


def test_normalize_question_collapses_whitespace_and_lowercases() -> None:
    q = "  What\tIS\nfree   will?  "
    assert AnswerCache.normalize_question(q) == "what is free will?"


def test_normalize_question_preserves_polytonic_greek() -> None:
    # ἐλευθερία must round-trip with diacritics intact (NFC composes them
    # back, casefold lowercases). The casefolded form is still legitimate
    # polytonic Greek.
    q = "  Ἐλευθερία  "
    out = AnswerCache.normalize_question(q)
    assert out == "ἐλευθερία"


def test_normalize_question_preserves_latin_macrons() -> None:
    q = "  Cicerō  dē  fātō  "
    assert AnswerCache.normalize_question(q) == "cicerō dē fātō"


def test_normalize_question_nfc_collides_decomposed_form() -> None:
    composed = "café"
    decomposed = "café"
    assert AnswerCache.normalize_question(composed) == AnswerCache.normalize_question(
        decomposed
    )


# ---------- cache_key ----------


def test_cache_key_stable_for_same_inputs() -> None:
    k1 = AnswerCache.cache_key("What is free will?", "gemini-3.1-pro", "auto")
    k2 = AnswerCache.cache_key("What is free will?", "gemini-3.1-pro", "auto")
    assert k1 == k2
    assert len(k1) == 64  # sha256 hex


def test_cache_key_collides_for_equivalent_normalised_forms() -> None:
    k1 = AnswerCache.cache_key("What  is FREE will?", "gemini-3.1-pro", "auto")
    k2 = AnswerCache.cache_key(" what is free will? ", "gemini-3.1-pro", "auto")
    assert k1 == k2


def test_cache_key_changes_when_model_changes() -> None:
    k_a = AnswerCache.cache_key("q", "gemini-3.1-pro", "auto")
    k_b = AnswerCache.cache_key("q", "kimi-k2-5", "auto")
    assert k_a != k_b


def test_cache_key_changes_when_retrieval_mode_changes() -> None:
    k_a = AnswerCache.cache_key("q", "gemini-3.1-pro", "auto")
    k_b = AnswerCache.cache_key("q", "gemini-3.1-pro", "snapshot")
    assert k_a != k_b


# ---------- lookup / store / record_hit ----------


def _make_db(
    *,
    connected: bool = True,
    fetchrow_return: dict[str, Any] | None = None,
    fetchval_return: Any = 0,
) -> AsyncMock:
    db = AsyncMock()
    db.is_connected = lambda: connected  # not async
    db.fetchrow = AsyncMock(return_value=fetchrow_return)
    db.fetchval = AsyncMock(return_value=fetchval_return)
    db.execute = AsyncMock(return_value="OK")
    return db


@pytest.mark.asyncio
async def test_lookup_returns_none_when_db_disconnected() -> None:
    cache = AnswerCache(_make_db(connected=False))
    result = await cache.lookup(question="q", model="m", retrieval_mode="auto")
    assert result is None


@pytest.mark.asyncio
async def test_lookup_miss_returns_none() -> None:
    db = _make_db(fetchrow_return=None, fetchval_return=0)
    cache = AnswerCache(db)
    result = await cache.lookup(question="q", model="m", retrieval_mode="auto")
    assert result is None
    db.fetchrow.assert_awaited_once()
    db.execute.assert_not_awaited()  # no hit_count bump


@pytest.mark.asyncio
async def test_lookup_hit_returns_payload_and_increments_hit_count() -> None:
    now = datetime.now(UTC)
    fake_key = AnswerCache.cache_key("q", "m", "auto")
    db = _make_db(
        fetchrow_return={
            "cache_key": fake_key,
            "answer": "the answer",
            "citations_json": [{"label": "Cic. De Fato 1"}],
            "passage_citations_json": [{"ref": "P1"}],
            "sources_json": [{"id": 1}],
            "reasoning_path_json": {"total_nodes": 4},
            "total_tokens": 12345,
            "total_cost_usd": 0.456,
            "trace_id": None,
            "kg_version_at_creation": 0,
            "hit_count": 2,
            "created_at": now,
        },
        fetchval_return=0,
    )
    cache = AnswerCache(db)
    result = await cache.lookup(question="q", model="m", retrieval_mode="auto")

    assert result is not None
    assert result["answer"] == "the answer"
    assert result["citations"] == [{"label": "Cic. De Fato 1"}]
    assert result["passage_citations"] == [{"ref": "P1"}]
    assert result["sources"] == [{"id": 1}]
    assert result["reasoning_path"] == {"total_nodes": 4}
    assert result["total_tokens"] == 12345
    assert result["total_cost_usd"] == pytest.approx(0.456)
    assert result["hit_count"] == 2
    assert result["cache_key"] == fake_key

    # hit_count bump query must have fired
    db.execute.assert_awaited_once()
    args = db.execute.await_args
    assert "UPDATE free_will.answer_cache" in args.args[0]
    assert "hit_count + 1" in args.args[0]
    assert args.args[1] == fake_key


@pytest.mark.asyncio
async def test_lookup_hit_parses_string_jsonb() -> None:
    """asyncpg may surface JSONB columns as raw strings — handle both."""
    now = datetime.now(UTC)
    db = _make_db(
        fetchrow_return={
            "cache_key": "abc",
            "answer": "x",
            "citations_json": '[{"label": "str-decoded"}]',
            "passage_citations_json": "[]",
            "sources_json": "[]",
            "reasoning_path_json": "{}",
            "total_tokens": 0,
            "total_cost_usd": 0,
            "trace_id": None,
            "kg_version_at_creation": 0,
            "hit_count": 0,
            "created_at": now,
        },
        fetchval_return=0,
    )
    cache = AnswerCache(db)
    result = await cache.lookup(question="q", model="m", retrieval_mode="auto")
    assert result is not None
    assert result["citations"] == [{"label": "str-decoded"}]
    assert result["reasoning_path"] == {}


@pytest.mark.asyncio
async def test_lookup_expired_returns_none_when_older_than_ttl() -> None:
    """The SQL WHERE clause filters by TTL — simulate that by returning
    None from fetchrow (Postgres would do this for an expired row)."""
    db = _make_db(fetchrow_return=None, fetchval_return=0)
    cache = AnswerCache(db)
    result = await cache.lookup(
        question="q", model="m", retrieval_mode="auto", ttl_days=1
    )
    assert result is None
    # Confirm we pass ttl_days through to the query as the 2nd positional arg.
    db.fetchrow.assert_awaited_once()
    assert db.fetchrow.await_args.args[2] == 1


@pytest.mark.asyncio
async def test_lookup_returns_none_when_kg_version_advanced() -> None:
    """Row stored at kg_version=0, current=5 -> WHERE clause excludes it."""
    # When the row's kg_version_at_creation < current version, the WHERE
    # clause `kg_version_at_creation >= $3` filters it out — simulate by
    # asserting the param is forwarded and fetchrow returns None.
    db = _make_db(fetchrow_return=None, fetchval_return=5)
    cache = AnswerCache(db)
    result = await cache.lookup(question="q", model="m", retrieval_mode="auto")
    assert result is None
    db.fetchrow.assert_awaited_once()
    # 3rd positional param to fetchrow is the current kg version
    assert db.fetchrow.await_args.args[3] == 5


@pytest.mark.asyncio
async def test_store_upserts_with_normalised_question_and_key() -> None:
    db = _make_db(fetchval_return=0)
    cache = AnswerCache(db)
    await cache.store(
        question=" WHAT  is free will? ",
        model="gemini-3.1-pro",
        retrieval_mode="auto",
        answer="a" * 1500,
        citations=[{"label": "Cic."}],
        passage_citations=[{"ref": "P1"}],
        sources=[],
        reasoning_path={"total_nodes": 3},
        total_tokens=1234,
        total_cost_usd=0.5,
        trace_id="00000000-0000-0000-0000-000000000001",
    )
    db.execute.assert_awaited_once()
    args = db.execute.await_args.args
    sql = args[0]
    assert "INSERT INTO free_will.answer_cache" in sql
    assert "ON CONFLICT (cache_key) DO UPDATE" in sql
    # cache_key, normalised_question, raw_question
    assert args[1] == AnswerCache.cache_key(
        " WHAT  is free will? ", "gemini-3.1-pro", "auto"
    )
    assert args[2] == "what is free will?"
    assert args[3] == " WHAT  is free will? "


@pytest.mark.asyncio
async def test_store_noop_when_db_disconnected() -> None:
    db = _make_db(connected=False)
    cache = AnswerCache(db)
    await cache.store(
        question="q",
        model="m",
        retrieval_mode="auto",
        answer="x",
        citations=[],
        passage_citations=[],
        sources=[],
        reasoning_path={},
        total_tokens=0,
        total_cost_usd=0,
        trace_id=None,
    )
    db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_record_hit_executes_update() -> None:
    db = _make_db()
    cache = AnswerCache(db)
    await cache.record_hit("some-key")
    db.execute.assert_awaited_once()
    assert db.execute.await_args.args[1] == "some-key"


# ---------- provenance (metadata + claim_ledger) round-trip ----------


@pytest.mark.asyncio
async def test_store_packs_provenance_into_reasoning_path_json() -> None:
    """Regression: metadata + claim_ledger must survive the cache (G9-B)."""
    import json as json_mod

    db = _make_db(fetchval_return=0)
    cache = AnswerCache(db)
    metadata = {"text_verification": {"verified": 3, "unverified": 1}}
    ledger = [{"claim": "c1", "evidence_ids": ["P1"], "status": "supported"}]
    await cache.store(
        question="q",
        model="m",
        retrieval_mode="auto",
        answer="a" * 1500,
        citations=[],
        passage_citations=[],
        sources=[],
        reasoning_path={"total_nodes": 3},
        total_tokens=1,
        total_cost_usd=0.0,
        trace_id=None,
        metadata=metadata,
        claim_ledger=ledger,
    )
    args = db.execute.await_args.args
    # reasoning_path_json is the 10th SQL parameter (args[10] after sql)
    stored_reasoning = json_mod.loads(args[10])
    assert stored_reasoning["total_nodes"] == 3
    provenance = stored_reasoning["__answer_provenance__"]
    assert provenance["metadata"] == metadata
    assert provenance["claim_ledger"] == ledger


@pytest.mark.asyncio
async def test_lookup_unpacks_provenance_and_strips_reserved_key() -> None:
    now = datetime.now(UTC)
    metadata = {"grounding": {"score": 92, "method": "verifier_v2_sample"}}
    ledger = [{"claim": "c1", "status": "supported"}]
    db = _make_db(
        fetchrow_return={
            "cache_key": "k",
            "answer": "the answer",
            "citations_json": [],
            "passage_citations_json": [],
            "sources_json": [],
            "reasoning_path_json": {
                "total_nodes": 4,
                "__answer_provenance__": {
                    "metadata": metadata,
                    "claim_ledger": ledger,
                },
            },
            "total_tokens": 1,
            "total_cost_usd": 0.0,
            "trace_id": None,
            "kg_version_at_creation": 0,
            "hit_count": 0,
            "created_at": now,
        },
        fetchval_return=0,
    )
    cache = AnswerCache(db)
    result = await cache.lookup(question="q", model="m", retrieval_mode="auto")
    assert result is not None
    assert result["metadata"] == metadata
    assert result["claim_ledger"] == ledger
    # Reserved key must not leak into the replayed reasoning_path.
    assert result["reasoning_path"] == {"total_nodes": 4}


@pytest.mark.asyncio
async def test_lookup_without_provenance_returns_empty_defaults() -> None:
    """Older cache rows (no packed provenance) keep working."""
    now = datetime.now(UTC)
    db = _make_db(
        fetchrow_return={
            "cache_key": "k",
            "answer": "the answer",
            "citations_json": [],
            "passage_citations_json": [],
            "sources_json": [],
            "reasoning_path_json": {"total_nodes": 4},
            "total_tokens": 1,
            "total_cost_usd": 0.0,
            "trace_id": None,
            "kg_version_at_creation": 0,
            "hit_count": 0,
            "created_at": now,
        },
        fetchval_return=0,
    )
    cache = AnswerCache(db)
    result = await cache.lookup(question="q", model="m", retrieval_mode="auto")
    assert result is not None
    assert result["metadata"] == {}
    assert result["claim_ledger"] == []
    assert result["reasoning_path"] == {"total_nodes": 4}


# ---------- fast/deep mode segmentation ----------


def test_cache_key_changes_when_mode_changes() -> None:
    """Regression: deep (counter-evidence) and fast answers must never
    share a cache slot — a deep request used to silently replay a cached
    fast answer and skip the counter-evidence hunt."""
    k_fast = AnswerCache.cache_key("q", "gemini-3.1-pro", "auto", "fast")
    k_deep = AnswerCache.cache_key("q", "gemini-3.1-pro", "auto", "deep")
    assert k_fast != k_deep


def test_cache_key_defaults_to_fast_mode() -> None:
    assert AnswerCache.cache_key("q", "m", "auto") == AnswerCache.cache_key(
        "q", "m", "auto", "fast"
    )


@pytest.mark.asyncio
async def test_lookup_keys_on_mode() -> None:
    db = _make_db(fetchrow_return=None, fetchval_return=0)
    cache = AnswerCache(db)
    await cache.lookup(question="q", model="m", retrieval_mode="auto", mode="deep")
    looked_up_key = db.fetchrow.await_args.args[1]
    assert looked_up_key == AnswerCache.cache_key("q", "m", "auto", "deep")
    assert looked_up_key != AnswerCache.cache_key("q", "m", "auto", "fast")


@pytest.mark.asyncio
async def test_store_keys_on_mode() -> None:
    db = _make_db(fetchval_return=0)
    cache = AnswerCache(db)
    await cache.store(
        question="q",
        model="m",
        retrieval_mode="auto",
        mode="deep",
        answer="a" * 1500,
        citations=[],
        passage_citations=[],
        sources=[],
        reasoning_path={},
        total_tokens=0,
        total_cost_usd=0,
        trace_id=None,
    )
    stored_key = db.execute.await_args.args[1]
    assert stored_key == AnswerCache.cache_key("q", "m", "auto", "deep")
    assert stored_key != AnswerCache.cache_key("q", "m", "auto", "fast")


@pytest.mark.asyncio
async def test_cache_storage_and_replay_remove_private_diagnostics_without_losing_provenance():
    import json

    draft = "PRIVATE_CACHE_DRAFT"
    gate = {"publishable": True, "status": "passed", "reasons": []}
    metadata = {
        "publication_gate": gate,
        "debug_trace": {"synthesis": {"raw_excerpt": draft}},
    }
    ledger = [
        {"claim": "A reviewed claim", "evidence_ids": ["p1"], "status": "supported"}
    ]
    db = _make_db(fetchval_return=0)
    cache = AnswerCache(db)
    await cache.store(
        question="q",
        model="m",
        retrieval_mode="auto",
        answer="Published answer",
        citations=[],
        passage_citations=[{"id": "p1"}],
        sources=[],
        reasoning_path={"total_nodes": 1},
        total_tokens=1,
        total_cost_usd=0,
        trace_id=None,
        metadata=metadata,
        claim_ledger=ledger,
    )
    args = db.execute.await_args.args
    assert draft not in json.dumps(args, default=str)
    packed = json.loads(args[10])
    assert packed["__answer_provenance__"]["metadata"]["publication_gate"] == gate
    assert packed["__answer_provenance__"]["claim_ledger"] == ledger
    # A legacy row returned by the DB must be sanitized on read as well.
    packed["__answer_provenance__"]["metadata"]["debug_trace"] = {"raw_excerpt": draft}
    db.fetchrow.return_value = {
        "cache_key": "k",
        "answer": "Published answer",
        "citations_json": [],
        "passage_citations_json": [{"id": "p1"}],
        "sources_json": [],
        "reasoning_path_json": packed,
        "total_tokens": 1,
        "total_cost_usd": 0,
        "trace_id": None,
        "hit_count": 0,
        "created_at": datetime.now(UTC),
        "kg_version_at_creation": 0,
    }
    replay = await cache.lookup(question="q", model="m", retrieval_mode="auto")
    assert draft not in json.dumps(replay, default=str)
    assert replay["metadata"]["publication_gate"] == gate
    assert replay["claim_ledger"] == ledger
    assert draft in json.dumps(metadata)  # caller's internal record unchanged
