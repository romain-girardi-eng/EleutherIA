from __future__ import annotations

from typing import Any

import pytest

from eleutheria_database.services.text_integrity import text_sha256
from eleutheria_graphrag.services.secondary_evidence import (
    PageSelector,
    build_db_secondary_page_fetcher,
    parse_page_reference,
)


class _FakeDB:
    def __init__(self, response: list[dict[str, Any]] | Exception) -> None:
        self.response = response
        self.calls: list[tuple[str, tuple[Any, ...]]] = []

    async def fetch(self, query: str, *args: Any) -> list[dict[str, Any]]:
        self.calls.append((query, args))
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


def _reviewed_row(
    *,
    text: str = "Reviewed synthetic page evidence.",
    manifestation_id: str = "manifestation_fixture_v1",
    publication_id: str = "pub_fixture",
    physical_page: int = 7,
    printed_page: str | None = "5",
) -> dict[str, Any]:
    return {
        "manifestation_id": manifestation_id,
        "publication_id": publication_id,
        "source_locator": "fixture://source.pdf",
        "artifact_source_sha256": "a" * 64,
        "rights_status": "copyrighted",
        "reuse_status": "internal_research_only",
        "artifact_extraction_status": "partial",
        "artifact_review_status": "reviewed",
        "page_source_sha256": "a" * 64,
        "physical_page": physical_page,
        "printed_page": printed_page,
        "page_locator": f"fixture://source.pdf#page={physical_page}",
        "text_content": text,
        "text_sha256": text_sha256(text),
        "page_extraction_status": "extracted",
        "page_review_status": "reviewed",
    }


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("p. 5", PageSelector("printed", ("5",))),
        ("211 n. 3", PageSelector("printed", ("211",))),
        ("p. xi", PageSelector("printed", ("XI",))),
        ("pp. 103-105", PageSelector("printed", ("103", "104", "105"))),
        ("PDF page 17", PageSelector("physical", (17,))),
        ("physical: 8", PageSelector("physical", (8,))),
    ],
)
def test_parse_page_reference_accepts_only_explicit_page_locators(
    raw: str,
    expected: PageSelector,
) -> None:
    assert parse_page_reference(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "Chapter 7",
        "Prologue, final paragraph",
        "pp. 1-31",
        "p. 0",
        "physical: 0",
    ],
)
def test_parse_page_reference_refuses_inference_and_overbroad_ranges(raw: str) -> None:
    assert parse_page_reference(raw) is None


@pytest.mark.asyncio
async def test_fetches_exact_reviewed_hashed_printed_page() -> None:
    row = _reviewed_row()
    db = _FakeDB([row])
    fetch = build_db_secondary_page_fetcher(db)

    evidence = await fetch("pub_fixture", "p. 5")

    assert evidence is not None
    assert evidence["text"] == row["text_content"]
    assert evidence["manifestation_id"] == "manifestation_fixture_v1"
    assert evidence["source_locator"] == "fixture://source.pdf"
    assert evidence["source_sha256"] == "a" * 64
    assert evidence["rights_status"] == "copyrighted"
    assert evidence["reuse_status"] == "internal_research_only"
    assert evidence["pages"] == [
        {
            "physical_page": 7,
            "printed_page": "5",
            "page_locator": "fixture://source.pdf#page=7",
            "text_sha256": row["text_sha256"],
        }
    ]
    sql, args = db.calls[0]
    assert "secondary_source_artifacts" in sql
    assert "secondary_evidence_pages" in sql
    assert "kg_nodes" not in sql
    assert args == ("pub_fixture", ["5"], [])


@pytest.mark.asyncio
async def test_fetches_only_explicit_physical_page_mapping() -> None:
    row = _reviewed_row(printed_page=None)
    db = _FakeDB([row])
    fetch = build_db_secondary_page_fetcher(db)

    evidence = await fetch("pub_fixture", "physical: 7")

    assert evidence is not None
    assert db.calls[0][1] == ("pub_fixture", [], [7])


@pytest.mark.asyncio
async def test_unmapped_page_is_refused() -> None:
    fetch = build_db_secondary_page_fetcher(_FakeDB([]))
    assert await fetch("pub_fixture", "p. 99") is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("text_sha256", None),
        ("text_sha256", "0" * 64),
        ("page_source_sha256", None),
        ("page_source_sha256", "b" * 64),
        ("page_review_status", "unreviewed"),
        ("artifact_review_status", "in_review"),
        ("page_extraction_status", "pending"),
        ("reuse_status", "metadata_only"),
        ("rights_status", "unknown"),
    ],
)
async def test_unhashed_unreviewed_or_unsafe_page_is_refused(
    field: str,
    value: Any,
) -> None:
    row = _reviewed_row()
    row[field] = value
    fetch = build_db_secondary_page_fetcher(_FakeDB([row]))

    assert await fetch("pub_fixture", "p. 5") is None


@pytest.mark.asyncio
async def test_ambiguous_manifestations_are_refused() -> None:
    rows = [
        _reviewed_row(manifestation_id="manifestation_a"),
        _reviewed_row(manifestation_id="manifestation_b", physical_page=9),
    ]
    fetch = build_db_secondary_page_fetcher(_FakeDB(rows))

    assert await fetch("pub_fixture", "p. 5") is None


@pytest.mark.asyncio
async def test_small_printed_range_requires_complete_page_coverage() -> None:
    rows = [
        _reviewed_row(printed_page="103", physical_page=110),
        _reviewed_row(printed_page="105", physical_page=112),
    ]
    fetch = build_db_secondary_page_fetcher(_FakeDB(rows))

    assert await fetch("pub_fixture", "pp. 103-105") is None


@pytest.mark.asyncio
async def test_small_printed_range_returns_all_exact_reviewed_pages() -> None:
    rows = [
        _reviewed_row(printed_page=str(page), physical_page=page + 7)
        for page in range(103, 106)
    ]
    fetch = build_db_secondary_page_fetcher(_FakeDB(rows))

    evidence = await fetch("pub_fixture", "pp. 103-105")

    assert evidence is not None
    assert [page["printed_page"] for page in evidence["pages"]] == [
        "103",
        "104",
        "105",
    ]


def test_database_schema_identifier_is_not_interpolated_unsafely() -> None:
    with pytest.raises(ValueError, match="Invalid database schema"):
        build_db_secondary_page_fetcher(_FakeDB([]), schema="free_will; DROP SCHEMA")


@pytest.mark.asyncio
async def test_database_failure_is_missing_not_snapshot_fallback() -> None:
    fetch = build_db_secondary_page_fetcher(_FakeDB(RuntimeError("table unavailable")))
    assert await fetch("pub_fixture", "p. 5") is None
