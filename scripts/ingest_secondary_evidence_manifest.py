#!/usr/bin/env python3
"""Validate and ingest reviewed secondary-source pages from a local manifest.

The manifest is deliberately local: repository fixtures contain only short,
synthetic text.  Real copyrighted page extracts and source artifacts must stay
outside git.  Dry-run validation is the default; ``--apply`` is required for
database writes.

Hash contract:

* ``source_sha256`` hashes the source artifact bytes exactly;
* ``text_sha256`` hashes NFC-normalized UTF-8 page text, using the same
  canonical function as ancient corpus passages.

No page concordance is inferred. ``physical_page`` and ``printed_page`` are
accepted only as explicit manifest assertions reviewed by a human.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import asyncpg

REPO_ROOT = Path(__file__).resolve().parents[1]
DATABASE_SRC = REPO_ROOT / "database" / "src"
if str(DATABASE_SRC) not in sys.path:
    sys.path.insert(0, str(DATABASE_SRC))

from eleutheria_database.services.text_integrity import (  # noqa: E402
    canonical_text_form,
    text_sha256,
)

MANIFEST_SCHEMA_VERSION = "1.0.0"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_MANIFESTATION_RE = re.compile(r"^[a-z0-9][a-z0-9_.:-]{2,127}$")
_SCHEMA_RE = re.compile(r"^[a-z_][a-z0-9_]*$")
_PRINTED_PAGE_RE = re.compile(r"^(?:[1-9]\d*[a-z]?|[ivxlcdm]+)$", re.IGNORECASE)

ARTIFACT_EXTRACTION_STATUSES = frozenset(
    {"registered", "pending", "partial", "complete", "failed"}
)
PAGE_EXTRACTION_STATUSES = frozenset({"pending", "extracted", "failed"})
REVIEW_STATUSES = frozenset({"unreviewed", "in_review", "reviewed", "rejected"})
RIGHTS_STATUSES = frozenset({"public_domain", "licensed", "copyrighted", "unknown"})
REUSE_STATUSES = frozenset(
    {
        "full_text_allowed",
        "quotation_only",
        "internal_research_only",
        "metadata_only",
        "prohibited",
        "unverified_do_not_republish",
    }
)


class ManifestError(ValueError):
    """The local manifest is incomplete, inconsistent, or has hash drift."""


class IngestionConflict(RuntimeError):
    """A reviewed database row conflicts with the manifest."""


@dataclass(frozen=True, slots=True)
class SecondaryEvidencePage:
    manifestation_id: str
    source_sha256: str
    physical_page: int
    printed_page: str | None
    page_locator: str | None
    text_content: str | None
    text_sha256: str | None
    extraction_status: str
    review_status: str
    reviewed_by: str | None
    reviewed_at: datetime | None
    extraction_metadata: dict[str, Any]


@dataclass(frozen=True, slots=True)
class SecondarySourceArtifact:
    manifestation_id: str
    publication_id: str
    source_locator: str
    source_sha256: str
    media_type: str
    rights_status: str
    reuse_status: str
    extraction_status: str
    review_status: str
    reviewed_by: str | None
    reviewed_at: datetime | None
    manifest_metadata: dict[str, Any]
    pages: tuple[SecondaryEvidencePage, ...]


@dataclass(frozen=True, slots=True)
class SecondaryEvidenceManifest:
    schema_version: str
    artifacts: tuple[SecondarySourceArtifact, ...]

    @property
    def page_count(self) -> int:
        return sum(len(artifact.pages) for artifact in self.artifacts)


@dataclass(frozen=True, slots=True)
class IngestionSummary:
    artifacts: int
    pages: int


def _mapping(value: Any, *, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ManifestError(f"{field} must be an object")
    return dict(value)


def _required_text(row: dict[str, Any], field: str, *, context: str) -> str:
    value = row.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ManifestError(f"{context}.{field} must be a non-empty string")
    return value.strip()


def _optional_text(row: dict[str, Any], field: str) -> str | None:
    value = row.get(field)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ManifestError(f"{field} must be null or a non-empty string")
    return value.strip()


def _printed_page(row: dict[str, Any], *, context: str) -> str | None:
    value = _optional_text(row, "printed_page")
    if value is None:
        return None
    if not _PRINTED_PAGE_RE.fullmatch(value):
        raise ManifestError(
            f"{context}.printed_page must be a single numeric/alphanumeric "
            "or Roman printed-page label"
        )
    return value.upper() if value.isalpha() else value.lower()


def _status(
    row: dict[str, Any],
    field: str,
    allowed: frozenset[str],
    *,
    context: str,
) -> str:
    value = _required_text(row, field, context=context)
    if value not in allowed:
        raise ManifestError(
            f"{context}.{field}={value!r} is invalid; expected one of {sorted(allowed)}"
        )
    return value


def _review_provenance(
    row: dict[str, Any],
    *,
    review_status: str,
    context: str,
) -> tuple[str | None, datetime | None]:
    reviewed_by = _optional_text(row, "reviewed_by")
    raw_reviewed_at = _optional_text(row, "reviewed_at")
    reviewed_at: datetime | None = None
    if raw_reviewed_at:
        try:
            reviewed_at = datetime.fromisoformat(raw_reviewed_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ManifestError(f"{context}.reviewed_at is not ISO-8601") from exc
        if reviewed_at.utcoffset() is None:
            raise ManifestError(f"{context}.reviewed_at must include a timezone")
    if review_status == "reviewed" and (reviewed_by is None or reviewed_at is None):
        raise ManifestError(
            f"{context} marked reviewed without reviewed_by and reviewed_at"
        )
    return reviewed_by, reviewed_at


def _sha256_bytes(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _local_path(base: Path, value: Any, *, field: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ManifestError(f"{field} must be a non-empty relative path")
    candidate = Path(value)
    if candidate.is_absolute():
        raise ManifestError(f"{field} must be relative to the local manifest")
    base = base.resolve()
    resolved = (base / candidate).resolve()
    if not resolved.is_relative_to(base):
        raise ManifestError(f"{field} escapes the manifest directory")
    if not resolved.is_file():
        raise ManifestError(f"{field} does not exist: {candidate}")
    return resolved


def _declared_sha(row: dict[str, Any], field: str, *, context: str) -> str:
    digest = _required_text(row, field, context=context).lower()
    if not _SHA256_RE.fullmatch(digest):
        raise ManifestError(f"{context}.{field} must be 64 lowercase hex characters")
    return digest


def _load_page(
    row: dict[str, Any],
    *,
    base: Path,
    manifestation_id: str,
    source_sha256: str,
) -> SecondaryEvidencePage:
    context = f"artifact[{manifestation_id}].page"
    raw_physical_page = row.get("physical_page")
    if (
        isinstance(raw_physical_page, bool)
        or not isinstance(raw_physical_page, int)
        or raw_physical_page <= 0
    ):
        raise ManifestError(f"{context}.physical_page must be a positive integer")

    printed_page = _printed_page(row, context=context)
    page_locator = _optional_text(row, "page_locator")
    extraction_status = _status(
        row,
        "extraction_status",
        PAGE_EXTRACTION_STATUSES,
        context=context,
    )
    review_status = _status(
        row,
        "review_status",
        REVIEW_STATUSES,
        context=context,
    )
    reviewed_by, reviewed_at = _review_provenance(
        row,
        review_status=review_status,
        context=context,
    )

    raw_text_path = row.get("text_path")
    text_content: str | None = None
    declared_text_sha = row.get("text_sha256")
    if raw_text_path is not None:
        text_path = _local_path(base, raw_text_path, field=f"{context}.text_path")
        try:
            text_content = canonical_text_form(text_path.read_text(encoding="utf-8"))
        except UnicodeDecodeError as exc:
            raise ManifestError(f"{context}.text_path must be UTF-8") from exc
        if not text_content.strip():
            raise ManifestError(f"{context}.text_path contains no evidence text")
        expected_text_sha = _declared_sha(row, "text_sha256", context=context)
        actual_text_sha = text_sha256(text_content)
        if actual_text_sha != expected_text_sha:
            raise ManifestError(
                f"{context}.text_sha256 drift: declared {expected_text_sha}, "
                f"actual {actual_text_sha}"
            )
        declared_text_sha = expected_text_sha
    elif declared_text_sha is not None:
        raise ManifestError(f"{context}.text_sha256 requires text_path")

    if extraction_status == "extracted" and text_content is None:
        raise ManifestError(f"{context} is extracted but has no text_path")
    if review_status == "reviewed" and extraction_status != "extracted":
        raise ManifestError(f"{context} is reviewed but not extracted")

    metadata = row.get("extraction_metadata", {})
    if not isinstance(metadata, dict):
        raise ManifestError(f"{context}.extraction_metadata must be an object")

    return SecondaryEvidencePage(
        manifestation_id=manifestation_id,
        source_sha256=source_sha256,
        physical_page=raw_physical_page,
        printed_page=printed_page,
        page_locator=page_locator,
        text_content=text_content,
        text_sha256=str(declared_text_sha) if declared_text_sha is not None else None,
        extraction_status=extraction_status,
        review_status=review_status,
        reviewed_by=reviewed_by,
        reviewed_at=reviewed_at,
        extraction_metadata=dict(metadata),
    )


def _load_artifact(row: dict[str, Any], *, base: Path) -> SecondarySourceArtifact:
    context = "artifact"
    manifestation_id = _required_text(row, "manifestation_id", context=context)
    if not _MANIFESTATION_RE.fullmatch(manifestation_id):
        raise ManifestError(f"artifact[{manifestation_id}].manifestation_id is invalid")
    context = f"artifact[{manifestation_id}]"

    publication_id = _required_text(row, "publication_id", context=context)
    source_locator = _required_text(row, "source_locator", context=context)
    source_path = _local_path(
        base, row.get("source_path"), field=f"{context}.source_path"
    )
    source_sha256 = _declared_sha(row, "source_sha256", context=context)
    actual_source_sha = _sha256_bytes(source_path)
    if actual_source_sha != source_sha256:
        raise ManifestError(
            f"{context}.source_sha256 drift: declared {source_sha256}, "
            f"actual {actual_source_sha}"
        )

    media_type = _required_text(row, "media_type", context=context)
    rights_status = _status(
        row,
        "rights_status",
        RIGHTS_STATUSES,
        context=context,
    )
    reuse_status = _status(
        row,
        "reuse_status",
        REUSE_STATUSES,
        context=context,
    )
    extraction_status = _status(
        row,
        "extraction_status",
        ARTIFACT_EXTRACTION_STATUSES,
        context=context,
    )
    review_status = _status(
        row,
        "review_status",
        REVIEW_STATUSES,
        context=context,
    )
    reviewed_by, reviewed_at = _review_provenance(
        row,
        review_status=review_status,
        context=context,
    )
    if review_status == "reviewed" and extraction_status not in {"partial", "complete"}:
        raise ManifestError(
            f"{context} is reviewed but extraction_status is not partial/complete"
        )

    raw_pages = row.get("pages")
    if not isinstance(raw_pages, list):
        raise ManifestError(f"{context}.pages must be an array")
    pages = tuple(
        _load_page(
            _mapping(page, field=f"{context}.pages[{index}]"),
            base=base,
            manifestation_id=manifestation_id,
            source_sha256=source_sha256,
        )
        for index, page in enumerate(raw_pages)
    )
    physical_pages = [page.physical_page for page in pages]
    if len(physical_pages) != len(set(physical_pages)):
        raise ManifestError(f"{context} contains duplicate physical_page mappings")

    metadata = row.get("manifest_metadata", {})
    if not isinstance(metadata, dict):
        raise ManifestError(f"{context}.manifest_metadata must be an object")

    return SecondarySourceArtifact(
        manifestation_id=manifestation_id,
        publication_id=publication_id,
        source_locator=source_locator,
        source_sha256=source_sha256,
        media_type=media_type,
        rights_status=rights_status,
        reuse_status=reuse_status,
        extraction_status=extraction_status,
        review_status=review_status,
        reviewed_by=reviewed_by,
        reviewed_at=reviewed_at,
        manifest_metadata=dict(metadata),
        pages=pages,
    )


def load_manifest(path: Path) -> SecondaryEvidenceManifest:
    """Load a local JSON manifest and verify every declared source/text hash."""

    path = path.resolve()
    try:
        root = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ManifestError(f"cannot read manifest {path}: {exc}") from exc
    root = _mapping(root, field="manifest")
    schema_version = _required_text(root, "manifest_schema_version", context="manifest")
    if schema_version != MANIFEST_SCHEMA_VERSION:
        raise ManifestError(
            f"manifest_schema_version={schema_version!r}; "
            f"expected {MANIFEST_SCHEMA_VERSION!r}"
        )
    raw_artifacts = root.get("artifacts")
    if not isinstance(raw_artifacts, list) or not raw_artifacts:
        raise ManifestError("manifest.artifacts must be a non-empty array")
    artifacts = tuple(
        _load_artifact(
            _mapping(row, field=f"manifest.artifacts[{index}]"),
            base=path.parent,
        )
        for index, row in enumerate(raw_artifacts)
    )
    manifestation_ids = [artifact.manifestation_id for artifact in artifacts]
    if len(manifestation_ids) != len(set(manifestation_ids)):
        raise ManifestError("manifest contains duplicate manifestation_id values")
    return SecondaryEvidenceManifest(schema_version=schema_version, artifacts=artifacts)


def _qualified(schema: str, table: str) -> str:
    if not _SCHEMA_RE.fullmatch(schema):
        raise ManifestError(f"invalid PostgreSQL schema identifier: {schema!r}")
    return f'"{schema}"."{table}"'


async def ingest_manifest(
    connection: Any,
    manifest: SecondaryEvidenceManifest,
    *,
    schema: str = "free_will",
) -> IngestionSummary:
    """Idempotently upsert one validated manifest in a transaction.

    A source SHA/publication change under an existing manifestation id is a
    conflict. A reviewed page may be replayed byte-for-byte, but its locator,
    printed-page mapping, source SHA, or text hash cannot be silently changed.
    """

    artifacts_table = _qualified(schema, "secondary_source_artifacts")
    pages_table = _qualified(schema, "secondary_evidence_pages")
    artifact_sql = f"""
        INSERT INTO {artifacts_table} AS current (
            manifestation_id, publication_id, source_locator, source_sha256,
            media_type, rights_status, reuse_status, extraction_status,
            review_status, reviewed_by, reviewed_at, manifest_metadata
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12::jsonb
        )
        ON CONFLICT (manifestation_id) DO UPDATE SET
            source_locator = EXCLUDED.source_locator,
            media_type = EXCLUDED.media_type,
            rights_status = EXCLUDED.rights_status,
            reuse_status = EXCLUDED.reuse_status,
            extraction_status = EXCLUDED.extraction_status,
            review_status = EXCLUDED.review_status,
            reviewed_by = EXCLUDED.reviewed_by,
            reviewed_at = EXCLUDED.reviewed_at,
            manifest_metadata = EXCLUDED.manifest_metadata,
            updated_at = now()
        WHERE current.source_sha256 = EXCLUDED.source_sha256
          AND current.publication_id = EXCLUDED.publication_id
          AND (
              current.review_status <> 'reviewed'
              OR (
                  EXCLUDED.review_status = 'reviewed'
                  AND current.source_locator = EXCLUDED.source_locator
                  AND current.media_type = EXCLUDED.media_type
                  AND current.rights_status = EXCLUDED.rights_status
                  AND current.reuse_status = EXCLUDED.reuse_status
                  AND current.reviewed_by IS NOT DISTINCT FROM EXCLUDED.reviewed_by
                  AND current.reviewed_at IS NOT DISTINCT FROM EXCLUDED.reviewed_at
                  AND current.manifest_metadata = EXCLUDED.manifest_metadata
              )
          )
        RETURNING manifestation_id
    """
    page_sql = f"""
        INSERT INTO {pages_table} AS current (
            manifestation_id, source_sha256, physical_page, printed_page,
            page_locator, text_content, text_sha256, extraction_status,
            review_status, reviewed_by, reviewed_at, extraction_metadata
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12::jsonb
        )
        ON CONFLICT (manifestation_id, physical_page) DO UPDATE SET
            printed_page = EXCLUDED.printed_page,
            page_locator = EXCLUDED.page_locator,
            text_content = EXCLUDED.text_content,
            text_sha256 = EXCLUDED.text_sha256,
            extraction_status = EXCLUDED.extraction_status,
            review_status = EXCLUDED.review_status,
            reviewed_by = EXCLUDED.reviewed_by,
            reviewed_at = EXCLUDED.reviewed_at,
            extraction_metadata = EXCLUDED.extraction_metadata,
            updated_at = now()
        WHERE current.source_sha256 = EXCLUDED.source_sha256
          AND (
              current.review_status <> 'reviewed'
              OR (
                  EXCLUDED.review_status = 'reviewed'
                  AND current.printed_page IS NOT DISTINCT FROM EXCLUDED.printed_page
                  AND current.page_locator IS NOT DISTINCT FROM EXCLUDED.page_locator
                  AND current.text_content IS NOT DISTINCT FROM EXCLUDED.text_content
                  AND current.text_sha256 IS NOT DISTINCT FROM EXCLUDED.text_sha256
                  AND current.reviewed_by IS NOT DISTINCT FROM EXCLUDED.reviewed_by
                  AND current.reviewed_at IS NOT DISTINCT FROM EXCLUDED.reviewed_at
                  AND current.extraction_metadata = EXCLUDED.extraction_metadata
              )
          )
        RETURNING physical_page
    """

    async with connection.transaction():
        for artifact in manifest.artifacts:
            row = await connection.fetchrow(
                artifact_sql,
                artifact.manifestation_id,
                artifact.publication_id,
                artifact.source_locator,
                artifact.source_sha256,
                artifact.media_type,
                artifact.rights_status,
                artifact.reuse_status,
                artifact.extraction_status,
                artifact.review_status,
                artifact.reviewed_by,
                artifact.reviewed_at,
                json.dumps(
                    artifact.manifest_metadata, ensure_ascii=False, sort_keys=True
                ),
            )
            if row is None:
                raise IngestionConflict(
                    "immutable reviewed artifact conflict for "
                    f"{artifact.manifestation_id}"
                )

            for page in artifact.pages:
                row = await connection.fetchrow(
                    page_sql,
                    page.manifestation_id,
                    page.source_sha256,
                    page.physical_page,
                    page.printed_page,
                    page.page_locator,
                    page.text_content,
                    page.text_sha256,
                    page.extraction_status,
                    page.review_status,
                    page.reviewed_by,
                    page.reviewed_at,
                    json.dumps(
                        page.extraction_metadata,
                        ensure_ascii=False,
                        sort_keys=True,
                    ),
                )
                if row is None:
                    raise IngestionConflict(
                        "immutable reviewed page conflict for "
                        f"{page.manifestation_id} physical_page={page.physical_page}"
                    )

    return IngestionSummary(
        artifacts=len(manifest.artifacts),
        pages=manifest.page_count,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate/import independently reviewed secondary-source pages."
    )
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument(
        "--database-url",
        default=os.getenv("DATABASE_URL"),
        help="Maintenance PostgreSQL DSN; required with --apply.",
    )
    parser.add_argument("--schema", default="free_will")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write validated rows. Without this flag the command is a dry-run.",
    )
    return parser.parse_args(argv)


async def _run(args: argparse.Namespace) -> int:
    manifest = load_manifest(args.manifest)
    if not args.apply:
        print(
            "validated "
            f"{len(manifest.artifacts)} artifact(s), {manifest.page_count} page(s); "
            "dry-run only"
        )
        return 0
    if not args.database_url:
        raise SystemExit("--database-url or DATABASE_URL is required with --apply")

    connection = await asyncpg.connect(args.database_url, statement_cache_size=0)
    try:
        summary = await ingest_manifest(connection, manifest, schema=args.schema)
    finally:
        await connection.close()
    print(f"ingested {summary.artifacts} artifact(s), {summary.pages} page(s)")
    return 0


def main(argv: list[str] | None = None) -> int:
    return asyncio.run(_run(parse_args(argv)))


if __name__ == "__main__":
    raise SystemExit(main())
