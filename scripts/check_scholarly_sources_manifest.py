#!/usr/bin/env python3
"""Validate and, explicitly, migrate the scholarly manifest v2 contract."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/scholarly_sources/manifest.jsonl"
STATUSES = {
    "pending",
    "in_progress",
    "partial",
    "targeted_primary_grounding",
    "complete",
}
SCOPES = {
    "amand1945fatalisme": "Selected anti-fatalist argument waves B0-B4; full-book claim coverage remains incomplete.",
    "firmicusmathesis": "Firmicus Mathesis I.2.5-11 witness extraction from volume I only.",
    "junod1976philocalie": "Selected Philocalia 21-27 passages, currently centered on Philocalia 23.",
    "stahlin_gcs_clement_strom_tlg": "Named Clement primary-grounding loci only; not the whole Stromata artifact.",
    "svf_chrysippus": "SVF II fragments 913-1000 of 1232 in the declared OGL TEI artifact.",
    "svf_cleanthes": "Complete Hymn to Zeus plus eleven selected Cleanthes fragments; the full 157-fragment artifact remains partial.",
}
REQUIRED = {
    "publication_dir",
    "bibtex_key",
    "kg_publication_id",
    "title",
    "author",
    "year_edition_used",
    "edition_used",
    "language_primary",
    "kg_ingestion_status",
    "ingestion_scope",
    "kg_ingestion_batches",
    "added_to_archive",
    "last_updated",
}


def read_rows(path: Path = MANIFEST) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def migrate_contract(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    migrated: list[dict[str, Any]] = []
    for row in rows:
        row = dict(row)
        publication_dir = row.get("publication_dir")
        if publication_dir not in SCOPES:
            raise ValueError(f"no reviewed ingestion scope for {publication_dir!r}")
        row["ingestion_scope"] = SCOPES[publication_dir]
        if publication_dir == "svf_cleanthes":
            # The artifact has 157 fragments, while the notes state that the
            # Hymn and eleven selected fragments were ingested. "complete" was
            # therefore a scope-free false completion claim.
            row["kg_ingestion_status"] = "partial"
            row.pop("completion_basis", None)
        row["manifest_schema_version"] = "2.0.0"
        row["last_updated"] = "2026-08-24"
        migrated.append(row)
    return migrated


def validate(rows: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for row in rows:
        name = str(row.get("publication_dir") or "<missing>")
        missing = sorted(REQUIRED - row.keys())
        if missing:
            errors.append(f"{name}: missing {', '.join(missing)}")
        if name in seen:
            errors.append(f"{name}: duplicate publication_dir")
        seen.add(name)
        if not re.fullmatch(r"[a-z0-9_]+", name):
            errors.append(f"{name}: invalid publication_dir")
        status = row.get("kg_ingestion_status")
        if status not in STATUSES:
            errors.append(f"{name}: invalid status {status!r}")
        batches = row.get("kg_ingestion_batches")
        if not isinstance(batches, list):
            errors.append(f"{name}: kg_ingestion_batches must be a list")
        if status in {"in_progress", "partial", "targeted_primary_grounding", "complete"} and not batches:
            errors.append(f"{name}: non-pending status requires a batch")
        if status == "complete" and not row.get("completion_basis"):
            errors.append(f"{name}: complete requires completion_basis")
        for key in ("md_md5", "pdf_md5", "tei_md5"):
            value = row.get(key)
            if value is not None and not re.fullmatch(r"[0-9a-f]{32}", str(value)):
                errors.append(f"{name}: invalid {key}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-contract", action="store_true")
    args = parser.parse_args(argv)
    rows = read_rows()
    if args.write_contract:
        rows = migrate_contract(rows)
        MANIFEST.write_text(
            "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
            encoding="utf-8",
        )
        print("manifest v2 contract fields written")
    errors = validate(rows)
    print(f"records: {len(rows)}; errors: {len(errors)}")
    for error in errors:
        print("-", error)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
