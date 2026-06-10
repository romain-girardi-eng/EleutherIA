"""G5 retrieval-correctness regression tests for SQLStrategy.

Covers:
  * Step-2 anchors carry passage UUIDs, not kg_node_ids (bug B).
  * Capability-aware lemma lookup: passage-level GROUP BY when
    ``oga_tokens.passage_id`` exists, legacy work-level join plus a
    warning otherwise; the probe is cached once per instance (bug A).
  * Partial step failures surface in ``state.metadata['retrieval_errors']``
    while ``discover_seeds`` keeps its public contract (bug F).
  * ``passage_role_condition`` defaults to original-only and is
    env-overridable (bug E).
"""

from __future__ import annotations

import logging
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from eleutheria_graphrag.agents.state import RAGState
from eleutheria_graphrag.services.retrieval_strategy import (
    SQLStrategy,
    passage_role_condition,
)

PASSAGE_UUID = "11111111-2222-3333-4444-555555555555"


def _make_deps(fetch: AsyncMock) -> MagicMock:
    deps = MagicMock()
    deps.db = AsyncMock()
    deps.db.fetch = fetch
    deps.tree_index = None
    deps.search = None
    deps.outgoing_edges = {}
    deps.incoming_edges = {}
    deps.state = None
    return deps


def _sql_router(
    *,
    label_rows: list[dict[str, Any]] | None = None,
    citation_rows: list[dict[str, Any]] | None = None,
    probe_rows: list[dict[str, Any]] | None = None,
    lemma_rows: list[dict[str, Any]] | None = None,
) -> AsyncMock:
    async def _fetch(sql: str, *_args: Any) -> list[dict[str, Any]]:
        if "information_schema.columns" in sql:
            return probe_rows or []
        if "passage_citations" in sql:
            return citation_rows or []
        if "kg_nodes" in sql:
            return label_rows or []
        if "oga_tokens" in sql:
            return lemma_rows or []
        return []

    return AsyncMock(side_effect=_fetch)


# ---------------------------------------------------------------------------
# Bug B — anchors must be passage UUIDs from citations, not kg_node_ids
# ---------------------------------------------------------------------------


async def test_step2_anchors_use_passage_id_not_kg_node_id() -> None:
    fetch = _sql_router(
        label_rows=[{"node_id": "work_de_fato", "type": "work", "priority": 2}],
        citation_rows=[
            {
                "passage_id": PASSAGE_UUID,
                "kg_node_id": "work_de_fato",
                "confidence": 0.9,
            }
        ],
    )
    deps = _make_deps(fetch)
    strategy = SQLStrategy(min_bundles=1)

    seeds, anchors = await strategy.discover_seeds(["De Fato"], deps)

    assert "work_de_fato" in seeds
    assert anchors == [PASSAGE_UUID]
    assert "work_de_fato" not in anchors


# ---------------------------------------------------------------------------
# Bug A — capability-aware lemma lookup
# ---------------------------------------------------------------------------


def _lemma_expander(terms: list[str]) -> MagicMock:
    expander = MagicMock()
    expander.expand = AsyncMock(return_value=terms)
    return expander


async def test_lemma_lookup_groups_by_passage_when_column_exists() -> None:
    fetch = _sql_router(
        probe_rows=[{"?column?": 1}],
        lemma_rows=[{"passage_id": PASSAGE_UUID}],
    )
    deps = _make_deps(fetch)
    strategy = SQLStrategy(
        min_bundles=4, lemma_expander=_lemma_expander(["eleuther"])
    )

    _seeds, anchors = await strategy.discover_seeds(["eleutheria"], deps)

    assert PASSAGE_UUID in anchors
    lemma_sqls = [
        call.args[0] for call in fetch.call_args_list if "t.lemma ILIKE" in call.args[0]
    ]
    assert lemma_sqls
    assert "GROUP BY t.passage_id" in lemma_sqls[0]
    assert "count(DISTINCT t.lemma)" in lemma_sqls[0]
    assert "p.passage_id = t.passage_id" in lemma_sqls[0]


async def test_lemma_lookup_falls_back_and_warns_without_column(
    caplog: pytest.LogCaptureFixture,
) -> None:
    fetch = _sql_router(probe_rows=[], lemma_rows=[{"passage_id": PASSAGE_UUID}])
    deps = _make_deps(fetch)
    strategy = SQLStrategy(
        min_bundles=4, lemma_expander=_lemma_expander(["eleuther"])
    )

    with caplog.at_level(logging.WARNING):
        _seeds, anchors = await strategy.discover_seeds(["eleutheria"], deps)

    assert PASSAGE_UUID in anchors
    lemma_sqls = [
        call.args[0] for call in fetch.call_args_list if "t.lemma ILIKE" in call.args[0]
    ]
    assert "p.work_id = t.work_id" in lemma_sqls[0]
    assert "GROUP BY" not in lemma_sqls[0]
    assert any("oga_tokens.passage_id missing" in rec.message for rec in caplog.records)


async def test_capability_probe_cached_once_per_instance() -> None:
    fetch = _sql_router(
        probe_rows=[{"?column?": 1}],
        lemma_rows=[{"passage_id": PASSAGE_UUID}],
    )
    deps = _make_deps(fetch)
    strategy = SQLStrategy(
        min_bundles=4, lemma_expander=_lemma_expander(["eleuther"])
    )

    await strategy.discover_seeds(["eleutheria"], deps)
    await strategy.discover_seeds(["eleutheria"], deps)

    probes = [
        call
        for call in fetch.call_args_list
        if "information_schema.columns" in call.args[0]
    ]
    assert len(probes) == 1


# ---------------------------------------------------------------------------
# Bug F — partial failures recorded in state.metadata['retrieval_errors']
# ---------------------------------------------------------------------------


async def test_step_failures_recorded_in_state_metadata() -> None:
    async def _fetch(sql: str, *_args: Any) -> list[dict[str, Any]]:
        if "kg_nodes" in sql:
            raise RuntimeError("connection reset")
        return []

    deps = _make_deps(AsyncMock(side_effect=_fetch))
    state = RAGState(question="who wrote De Fato")
    deps.state = state
    strategy = SQLStrategy(min_bundles=1)

    seeds, anchors = await strategy.discover_seeds(["De Fato"], deps)

    # Public contract intact: still a (seeds, anchors) tuple.
    assert seeds == []
    assert anchors == []
    errors = state.metadata.get("retrieval_errors", [])
    assert errors
    assert any(err.startswith("label_match:") for err in errors)


# ---------------------------------------------------------------------------
# Bug E — passage_role filtering, env-overridable
# ---------------------------------------------------------------------------


def test_passage_role_condition_defaults_to_original(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ELEUTHERIA_PASSAGE_ROLE_FILTER", raising=False)
    assert passage_role_condition("p") == "p.passage_role = 'original'"


def test_passage_role_condition_env_disable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ELEUTHERIA_PASSAGE_ROLE_FILTER", "all")
    assert passage_role_condition("p") == "TRUE"


def test_passage_role_condition_rejects_unknown_role(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ELEUTHERIA_PASSAGE_ROLE_FILTER", "drop table")
    assert passage_role_condition("p") == "p.passage_role = 'original'"


async def test_lemma_lookup_sql_filters_passage_role(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ELEUTHERIA_PASSAGE_ROLE_FILTER", raising=False)
    fetch = _sql_router(probe_rows=[{"?column?": 1}], lemma_rows=[])
    deps = _make_deps(fetch)
    strategy = SQLStrategy(
        min_bundles=4, lemma_expander=_lemma_expander(["eleuther"])
    )

    await strategy.discover_seeds(["eleutheria"], deps)

    lemma_sqls = [
        call.args[0] for call in fetch.call_args_list if "t.lemma ILIKE" in call.args[0]
    ]
    assert "p.passage_role = 'original'" in lemma_sqls[0]
