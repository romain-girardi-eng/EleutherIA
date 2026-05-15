"""Unit tests for :mod:`backend.services.topic_tagger`.

Mocks the :class:`DatabaseService` with ``AsyncMock`` so the tagger
runs in-process without a Postgres connection. We exercise:

* tag format invariants — only ``period|school|person:<slug>`` allowed
* dedupe + alphabetical sort
* period dominance — majority wins, ties resolve deterministically
* no ``period:*`` tag when no resolvable author/period
* hard cap of 25 tags
"""

from __future__ import annotations

import re
import uuid
from typing import Any
from unittest.mock import AsyncMock

import pytest

from backend.services.topic_tagger import TopicTagger

_TAG_PATTERN = re.compile(r"^(period|school|person):[a-z][a-z0-9_]*$")


def _fake_db(
    *,
    trace_row: dict[str, Any] | None,
    citation_rows: list[dict[str, Any]] | None = None,
) -> AsyncMock:
    """Build an :class:`AsyncMock` DB with curated ``fetchrow``/``fetch`` returns."""
    db = AsyncMock()
    db.is_connected = lambda: True
    db.fetchrow = AsyncMock(return_value=trace_row)
    db.fetch = AsyncMock(return_value=citation_rows or [])
    db.execute = AsyncMock(return_value="UPDATE 1")
    return db


def _uuid() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tag_format_invariants() -> None:
    """Every emitted tag must match ``^(period|school|person):[a-z][a-z0-9_]*$``."""
    citation_id = _uuid()
    trace_row = {
        "final_answer_citations": [{"id": citation_id, "label": "Justin, 1 Apol."}],
        "final_answer_text": (
            "Justin develops his argument (person_justin_martyr_2c_ce) "
            "against the Stoic school_stoics."
        ),
        "metadata": {"seed_nodes": ["person_origen", "school_middle_platonism"]},
    }
    citation_rows = [
        {
            "period": "Roman Imperial",
            "kg_work_id": "work_justin_first_apology",
            "person_id": "person_justin_martyr_2c_ce",
        }
    ]
    db = _fake_db(trace_row=trace_row, citation_rows=citation_rows)
    tagger = TopicTagger(db)

    tags = await tagger.tag_trace(_uuid())

    assert tags, "expected at least one tag"
    for tag in tags:
        assert _TAG_PATTERN.match(tag), f"malformed tag: {tag!r}"


@pytest.mark.asyncio
async def test_dedupe_and_sort() -> None:
    """Same node referenced from many sources collapses to one sorted tag list."""
    citation_id = _uuid()
    trace_row = {
        "final_answer_citations": [
            {"id": citation_id, "label": "Justin, 1 Apol."},
            {"id": _uuid(), "label": "Justin, Dial."},
            {"id": _uuid(), "label": "Justin, 2 Apol."},
        ],
        "final_answer_text": (
            "person_justin_martyr_2c_ce person_justin_martyr_2c_ce "
            "person_justin_martyr_2c_ce"
        ),
        "metadata": {
            "touched_node_ids": ["person_justin_martyr_2c_ce"],
            "seed_nodes": ["person_justin_martyr_2c_ce"],
        },
    }
    citation_rows = [
        {
            "period": "Roman Imperial",
            "kg_work_id": "work_x",
            "person_id": "person_justin_martyr_2c_ce",
        }
    ] * 3
    db = _fake_db(trace_row=trace_row, citation_rows=citation_rows)
    tagger = TopicTagger(db)

    tags = await tagger.tag_trace(_uuid())

    # Justin appears once; tags are sorted alphabetically.
    assert tags == sorted(tags)
    assert tags.count("person:person_justin_martyr_2c_ce") == 1


@pytest.mark.asyncio
async def test_period_dominance() -> None:
    """3 imperial + 1 classical citations → exactly one ``period:imperial`` tag."""
    trace_row = {
        "final_answer_citations": [
            {"id": _uuid(), "label": "a"},
            {"id": _uuid(), "label": "b"},
            {"id": _uuid(), "label": "c"},
            {"id": _uuid(), "label": "d"},
        ],
        "final_answer_text": "",
        "metadata": {},
    }
    citation_rows = [
        {"period": "Roman Imperial", "kg_work_id": None, "person_id": None},
        {"period": "Roman Imperial", "kg_work_id": None, "person_id": None},
        {"period": "Roman Imperial", "kg_work_id": None, "person_id": None},
        {"period": "Classical Greek", "kg_work_id": None, "person_id": None},
    ]
    db = _fake_db(trace_row=trace_row, citation_rows=citation_rows)
    tagger = TopicTagger(db)

    tags = await tagger.tag_trace(_uuid())

    period_tags = [t for t in tags if t.startswith("period:")]
    assert period_tags == ["period:imperial"]


@pytest.mark.asyncio
async def test_no_period_when_unknown() -> None:
    """Passages without resolvable author/period → no ``period:*`` tag emitted."""
    trace_row = {
        "final_answer_citations": [{"id": _uuid(), "label": "anonymous"}],
        "final_answer_text": "",
        "metadata": {},
    }
    # Join returns rows but every period is NULL or non-canonical.
    citation_rows: list[dict[str, Any]] = [
        {"period": None, "kg_work_id": None, "person_id": None},
        {"period": "Unknown Era", "kg_work_id": None, "person_id": None},
    ]
    db = _fake_db(trace_row=trace_row, citation_rows=citation_rows)
    tagger = TopicTagger(db)

    tags = await tagger.tag_trace(_uuid())

    assert not any(t.startswith("period:") for t in tags)


@pytest.mark.asyncio
async def test_cap_at_25() -> None:
    """Synthesising 50 distinct person ids must yield exactly 25 tags."""
    # Use 50 valid person ids only in the answer-text source so we can hit the cap.
    person_ids = [f"person_test_{i:03d}" for i in range(50)]
    trace_row = {
        "final_answer_citations": [],
        "final_answer_text": " ".join(person_ids),
        "metadata": {},
    }
    db = _fake_db(trace_row=trace_row, citation_rows=[])
    tagger = TopicTagger(db)

    tags = await tagger.tag_trace(_uuid())

    assert len(tags) == 25
    # The kept slice must be the alphabetically-first 25 (since output is sorted).
    expected = sorted(f"person:{pid}" for pid in person_ids)[:25]
    assert tags == expected


@pytest.mark.asyncio
async def test_tag_and_persist_writes_when_connected() -> None:
    """``tag_and_persist`` must call ``UPDATE`` with the computed tag list."""
    trace_row = {
        "final_answer_citations": [],
        "final_answer_text": "person_justin_martyr_2c_ce",
        "metadata": {},
    }
    db = _fake_db(trace_row=trace_row, citation_rows=[])
    tagger = TopicTagger(db)
    trace_id = _uuid()

    tags = await tagger.tag_and_persist(trace_id)

    assert tags == ["person:person_justin_martyr_2c_ce"]
    db.execute.assert_awaited_once()
    call = db.execute.call_args
    # First positional arg is the SQL; the trace_id and tag list follow.
    assert "UPDATE free_will.query_traces" in call.args[0]
    assert call.args[1] == trace_id
    assert call.args[2] == ["person:person_justin_martyr_2c_ce"]


@pytest.mark.asyncio
async def test_returns_empty_when_db_disconnected() -> None:
    """A disconnected DB short-circuits to ``[]`` without touching SQL."""
    db = AsyncMock()
    db.is_connected = lambda: False
    db.fetchrow = AsyncMock()
    db.fetch = AsyncMock()
    db.execute = AsyncMock()
    tagger = TopicTagger(db)

    tags = await tagger.tag_trace(_uuid())

    assert tags == []
    db.fetchrow.assert_not_awaited()


@pytest.mark.asyncio
async def test_ignores_non_uuid_citation_ids() -> None:
    """Citation ids that aren't UUIDs (e.g. KG node ids) skip the SQL join."""
    trace_row = {
        "final_answer_citations": [
            {"id": "kg_node_not_a_uuid", "label": "x"},
            {"id": "person_origen", "label": "y"},
        ],
        "final_answer_text": "",
        "metadata": {},
    }
    db = _fake_db(trace_row=trace_row, citation_rows=[])
    tagger = TopicTagger(db)

    tags = await tagger.tag_trace(_uuid())

    # Nothing to join → no period tag; non-uuid ids don't pollute output.
    assert all(_TAG_PATTERN.match(tag) for tag in tags)
    # The join SQL must NOT have been called (no uuid citations).
    db.fetch.assert_not_awaited()
