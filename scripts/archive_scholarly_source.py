#!/usr/bin/env python3
"""Idempotent indexer for data/scholarly_sources/ocr/.

Usage:
    python scripts/archive_scholarly_source.py <publication_dir>

For the given publication_dir, scans data/scholarly_sources/ocr/{dir}/,
computes md5/size/word_count/line_count of source.md (and source.pdf if
symlinked or copied), reads ocr_meta.json if present for engine details,
and upserts a single line in data/scholarly_sources/manifest.jsonl
keyed by publication_dir.

Existing fields in the manifest entry are preserved unless recomputed
metrics override them. Title/author/edition/kg_* fields are NEVER
overwritten by this script — they must be set manually in the manifest
or via ocr_meta.json.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_ROOT = ROOT / "data" / "scholarly_sources"
OCR_ROOT = ARCHIVE_ROOT / "ocr"
MANIFEST_PATH = ARCHIVE_ROOT / "manifest.jsonl"


def _md5(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _scan_publication(publication_dir: str) -> dict:
    src_dir = OCR_ROOT / publication_dir
    if not src_dir.is_dir():
        raise SystemExit(f"directory not found: {src_dir}")

    out: dict = {"publication_dir": publication_dir}

    md = src_dir / "source.md"
    if md.is_file():
        text = md.read_text(encoding="utf-8")
        out["md_md5"] = _md5(md)
        out["md_size_bytes"] = md.stat().st_size
        out["word_count"] = len(text.split())
        out["line_count"] = text.count("\n") + (0 if text.endswith("\n") else 1)

    pdf = src_dir / "source.pdf"
    if pdf.is_file() or pdf.is_symlink():
        try:
            out["pdf_md5"] = _md5(pdf)
            out["pdf_size_bytes"] = pdf.stat().st_size
        except FileNotFoundError:
            pass

    meta = src_dir / "ocr_meta.json"
    if meta.is_file():
        meta_d = json.loads(meta.read_text(encoding="utf-8"))
        for k in (
            "ocr_engine",
            "ocr_quality_pct_fr",
            "ocr_quality_pct_grc",
            "ocr_quality_pct_lat",
            "page_count",
            "language_primary",
            "languages_secondary",
            "notes",
        ):
            if k in meta_d:
                out[k] = meta_d[k]

    return out


def _upsert(manifest_entries: list[dict], new_entry: dict) -> tuple[list[dict], str]:
    pub_dir = new_entry["publication_dir"]
    for i, e in enumerate(manifest_entries):
        if e.get("publication_dir") == pub_dir:
            merged = {**e, **new_entry, "last_updated": _today()}
            manifest_entries[i] = merged
            return manifest_entries, "update"
    new_entry.setdefault("added_to_archive", _today())
    new_entry.setdefault("last_updated", _today())
    new_entry.setdefault("kg_ingestion_status", "pending")
    new_entry.setdefault("kg_ingestion_batches", [])
    new_entry.setdefault("kg_node_count", None)
    manifest_entries.append(new_entry)
    return manifest_entries, "insert"


def _read_manifest() -> list[dict]:
    if not MANIFEST_PATH.is_file():
        return []
    return [
        json.loads(line)
        for line in MANIFEST_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _write_manifest(entries: list[dict]) -> None:
    MANIFEST_PATH.write_text(
        "\n".join(json.dumps(e, ensure_ascii=False) for e in entries) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    publication_dir = argv[1]
    new_entry = _scan_publication(publication_dir)
    entries = _read_manifest()
    entries, op = _upsert(entries, new_entry)
    _write_manifest(entries)
    print(f"{op}: {publication_dir}")
    print(json.dumps(new_entry, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
