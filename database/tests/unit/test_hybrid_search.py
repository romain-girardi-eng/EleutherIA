"""G5 regression tests — FTS config unification + passage_role filtering.

Covers:
  * ``fts_fragments`` uses the stored 'simple'+f_unaccent search_vector
    (and its GIN index) once the migration has run, and falls back to the
    legacy runtime expression beforehand (bug D, deploy-order safe).
  * The capability probe is cached on success and NOT cached on failure.
  * Primary-text legs filter ``passage_role = 'original'`` by default and
    honour the env override (bug E).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from eleutheria_database.services import hybrid_search as hs
from eleutheria_database.services.hybrid_search import (
    HybridSearchService,
    fts_fragments,
    passage_role_condition,
)


@pytest.fixture(autouse=True)
def _reset_capability_cache(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(hs, "_UNACCENT_AVAILABLE", None)
    monkeypatch.delenv("ELEUTHERIA_PASSAGE_ROLE_FILTER", raising=False)


def _db(unaccent_available: bool | None = True) -> MagicMock:
    db = MagicMock()
    if unaccent_available is None:
        db.fetchrow = AsyncMock(side_effect=RuntimeError("connection down"))
    else:
        db.fetchrow = AsyncMock(return_value={"available": unaccent_available})
    db.fetch = AsyncMock(return_value=[])
    return db


# ---------------------------------------------------------------------------
# fts_fragments capability behavior
# ---------------------------------------------------------------------------


async def test_fts_fragments_uses_stored_vector_when_f_unaccent_exists() -> None:
    match, rank = await fts_fragments(_db(True), "$1")
    assert match == (
        "p.search_vector @@ plainto_tsquery('simple', free_will.f_unaccent($1))"
    )
    assert rank.startswith("ts_rank(p.search_vector,")


async def test_fts_fragments_legacy_before_migration() -> None:
    match, rank = await fts_fragments(_db(False), "$1")
    assert "to_tsvector('simple', p.text_content)" in match
    assert "f_unaccent" not in match
    assert "to_tsvector('simple', p.text_content)" in rank


async def test_fts_fragments_probe_cached_on_success() -> None:
    db = _db(True)
    await fts_fragments(db, "$1")
    await fts_fragments(db, "$1")
    assert db.fetchrow.await_count == 1


async def test_fts_fragments_probe_failure_not_cached() -> None:
    db = _db(None)
    match, _rank = await fts_fragments(db, "$1")
    assert "to_tsvector('simple', p.text_content)" in match
    # Failure did not pin the legacy path: a healthy probe upgrades it.
    db.fetchrow = AsyncMock(return_value={"available": True})
    match, _rank = await fts_fragments(db, "$1")
    assert "p.search_vector" in match


# ---------------------------------------------------------------------------
# Search legs: stored vector + passage_role filter
# ---------------------------------------------------------------------------


async def test_fulltext_search_uses_index_and_role_filter() -> None:
    db = _db(True)
    service = HybridSearchService(db)

    await service.fulltext_search("eleutheria", limit=10)

    sql = db.fetch.await_args.args[0]
    assert "p.search_vector @@ plainto_tsquery('simple', free_will.f_unaccent($1))" in sql
    assert "p.passage_role = 'original'" in sql


async def test_fulltext_search_role_filter_env_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ELEUTHERIA_PASSAGE_ROLE_FILTER", "all")
    db = _db(True)
    service = HybridSearchService(db)

    await service.fulltext_search("eleutheria", limit=10)

    sql = db.fetch.await_args.args[0]
    assert "passage_role =" not in sql


async def test_lemmatic_search_filters_role() -> None:
    db = _db(True)
    service = HybridSearchService(db)

    await service.lemmatic_search("sum", limit=10)

    sql = db.fetch.await_args.args[0]
    assert "p.passage_role = 'original'" in sql


async def test_search_by_author_filters_role_both_branches() -> None:
    db = _db(True)
    service = HybridSearchService(db)

    await service.search_by_author("Cicero", query="fatum", limit=10)
    sql_with_query = db.fetch.await_args.args[0]
    await service.search_by_author("Cicero", limit=10)
    sql_without_query = db.fetch.await_args.args[0]

    assert "p.passage_role = 'original'" in sql_with_query
    assert "p.passage_role = 'original'" in sql_without_query


# ---------------------------------------------------------------------------
# passage_role_condition validation
# ---------------------------------------------------------------------------


def test_role_condition_default() -> None:
    assert passage_role_condition("p") == "p.passage_role = 'original'"


def test_role_condition_env_role(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ELEUTHERIA_PASSAGE_ROLE_FILTER", "translation")
    assert passage_role_condition("p") == "p.passage_role = 'translation'"


def test_role_condition_rejects_injection(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ELEUTHERIA_PASSAGE_ROLE_FILTER", "x'; DROP TABLE passages;--")
    assert passage_role_condition("p") == "p.passage_role = 'original'"
