"""Shared (de)serialization + schema helpers for the EleutherIA corpus layer.

Deterministic JSONL (sorted keys, compact separators, unicode preserved) so
git diffs stay clean and round-trips are byte-stable. Mirrors the conventions in
scripts/export_kg_snapshot.py.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

MANIFEST_FIELDS = ("canonical_id", "label", "author", "period", "cts_urn",
                   "source", "status", "expected_passages")
PASSAGE_FIELDS = ("passage_id", "work_canonical_id", "cts_urn", "canonical_ref",
                  "sequence_number", "text_content")
CITATION_FIELDS = ("passage_id", "kg_node_id", "citation_type", "confidence")


def canonical_dumps(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(canonical_dumps(row))
            f.write("\n")
    tmp.replace(path)


def read_jsonl(path: Path) -> list[dict]:
    out: list[dict] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                out.append(json.loads(line))
    return out
