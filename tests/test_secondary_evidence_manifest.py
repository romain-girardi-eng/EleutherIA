from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from scripts.ingest_secondary_evidence_manifest import (
    IngestionConflict,
    ManifestError,
    ingest_manifest,
    load_manifest,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "secondary_evidence"
FIXTURE_MANIFEST = FIXTURE_DIR / "manifest.json"


class _Transaction:
    async def __aenter__(self) -> None:
        return None

    async def __aexit__(self, *_args: Any) -> None:
        return None


class _StatefulConnection:
    """Small conflict-aware stand-in for the two PostgreSQL upserts."""

    def __init__(self) -> None:
        self.artifacts: dict[str, tuple[Any, ...]] = {}
        self.pages: dict[tuple[str, int], tuple[Any, ...]] = {}
        self.queries: list[str] = []

    def transaction(self) -> _Transaction:
        return _Transaction()

    async def fetchrow(self, query: str, *args: Any) -> dict[str, Any] | None:
        self.queries.append(query)
        if "secondary_source_artifacts" in query:
            manifestation_id = str(args[0])
            existing = self.artifacts.get(manifestation_id)
            if existing is not None:
                immutable_existing = (
                    existing[1],
                    existing[2],
                    existing[3],
                    existing[4],
                    existing[5],
                    existing[6],
                )
                immutable_incoming = (
                    args[1],
                    args[2],
                    args[3],
                    args[4],
                    args[5],
                    args[6],
                )
                if existing[8] == "reviewed" and (
                    args[8] != "reviewed" or immutable_existing != immutable_incoming
                ):
                    return None
            self.artifacts[manifestation_id] = args
            return {"manifestation_id": manifestation_id}

        key = (str(args[0]), int(args[2]))
        existing = self.pages.get(key)
        if existing is not None:
            page_immutable_existing = (
                existing[1],
                existing[3],
                existing[4],
                existing[5],
                existing[6],
            )
            page_immutable_incoming = (args[1], args[3], args[4], args[5], args[6])
            if existing[8] == "reviewed" and (
                args[8] != "reviewed"
                or page_immutable_existing != page_immutable_incoming
            ):
                return None
        self.pages[key] = args
        return {"physical_page": key[1]}


def test_synthetic_fixture_has_verified_source_and_page_hashes() -> None:
    manifest = load_manifest(FIXTURE_MANIFEST)

    assert len(manifest.artifacts) == 1
    assert manifest.page_count == 1
    artifact = manifest.artifacts[0]
    assert artifact.publication_id == "pub_fixture_smith_2026"
    assert artifact.review_status == "reviewed"
    assert artifact.pages[0].printed_page == "101"
    assert artifact.pages[0].text_content == (
        "The synthetic author distinguishes a voluntary act from a compelled act.\n"
    )


def test_page_hash_drift_is_rejected_before_database_access(
    tmp_path: Path,
) -> None:
    fixture_copy = tmp_path / "fixture"
    fixture_copy.mkdir()
    for source in FIXTURE_DIR.iterdir():
        (fixture_copy / source.name).write_bytes(source.read_bytes())
    (fixture_copy / "page-001.txt").write_text(
        "The synthetic page was silently changed.\n",
        encoding="utf-8",
    )

    with pytest.raises(ManifestError, match="text_sha256 drift"):
        load_manifest(fixture_copy / "manifest.json")


def test_source_hash_drift_is_rejected_before_database_access(
    tmp_path: Path,
) -> None:
    fixture_copy = tmp_path / "fixture"
    fixture_copy.mkdir()
    for source in FIXTURE_DIR.iterdir():
        (fixture_copy / source.name).write_bytes(source.read_bytes())
    (fixture_copy / "source-fixture.txt").write_text(
        "Different source bytes.\n",
        encoding="utf-8",
    )

    with pytest.raises(ManifestError, match="source_sha256 drift"):
        load_manifest(fixture_copy / "manifest.json")


@pytest.mark.asyncio
async def test_ingestion_is_idempotent_for_identical_reviewed_manifest() -> None:
    manifest = load_manifest(FIXTURE_MANIFEST)
    connection = _StatefulConnection()

    first = await ingest_manifest(connection, manifest)
    second = await ingest_manifest(connection, manifest)

    assert first == second
    assert first.artifacts == 1
    assert first.pages == 1
    assert len(connection.artifacts) == 1
    assert len(connection.pages) == 1
    assert all("ON CONFLICT" in query for query in connection.queries)


@pytest.mark.asyncio
async def test_reviewed_page_text_cannot_be_silently_replaced() -> None:
    manifest = load_manifest(FIXTURE_MANIFEST)
    connection = _StatefulConnection()
    await ingest_manifest(connection, manifest)

    artifact = manifest.artifacts[0]
    changed_page = replace(
        artifact.pages[0],
        text_content="A conflicting synthetic claim.\n",
        text_sha256="a" * 64,
    )
    conflicting = replace(
        manifest,
        artifacts=(replace(artifact, pages=(changed_page,)),),
    )

    with pytest.raises(IngestionConflict, match="immutable reviewed page"):
        await ingest_manifest(connection, conflicting)


def test_schema_is_private_hashed_and_review_gated() -> None:
    migration = (
        ROOT / "database" / "migrations" / "20260824_03_secondary_page_evidence.sql"
    ).read_text(encoding="utf-8")
    canonical = (ROOT / "database" / "schema" / "schema.sql").read_text(
        encoding="utf-8"
    )

    for sql in (migration, canonical):
        assert "secondary_source_artifacts" in sql
        assert "secondary_evidence_pages" in sql
        assert "source_sha256" in sql
        assert "physical_page" in sql
        assert "printed_page" in sql
        assert "text_sha256" in sql
        assert "review_status" in sql
        assert "reuse_status" in sql
        assert "ENABLE ROW LEVEL SECURITY" in sql
    assert "FROM PUBLIC, anon, authenticated" in migration
    assert "Never derive a page mapping" in migration


def test_committed_fixture_contains_only_short_synthetic_text() -> None:
    texts = [
        (FIXTURE_DIR / "source-fixture.txt").read_text(encoding="utf-8"),
        (FIXTURE_DIR / "page-001.txt").read_text(encoding="utf-8"),
    ]
    assert all(len(text) < 500 for text in texts)
    assert all("synthetic" in text.lower() for text in texts)
