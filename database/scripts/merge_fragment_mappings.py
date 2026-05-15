"""Merge curated + auto-DOCTORAT + Kimi DL mappings into one JSONL.

Inputs:
  - data/doxographical_audit/fragment_mappings.jsonl   (curated, hand-verified)
  - data/doxographical_audit/auto_mappings.jsonl       (auto from DOCTORAT)
  - data/doxographical_audit/kimi_dl_mappings.jsonl    (Kimi DL VII/X)

Priority order when the same passage_id appears in multiple sources:
  1. curated (always wins, never overwritten)
  2. auto_doctorat (loses to curated, wins over Kimi)
  3. Kimi (loses to both)

For multi-source overlaps on the same passage, fragment_collections are
*merged* (union), with the highest-priority source's other fields kept.

Output: data/doxographical_audit/fragment_mappings_merged.jsonl
        (replaces fragment_mappings.jsonl once reviewed)
"""

from __future__ import annotations

import argparse
import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import Any

logger = logging.getLogger("merge_fragment_mappings")

ROOT = Path(__file__).resolve().parents[2]
DOX_DIR = ROOT / "data" / "doxographical_audit"

INPUTS = [
    ("curated", DOX_DIR / "fragment_mappings.jsonl"),
    ("auto_doctorat", DOX_DIR / "auto_mappings.jsonl"),
    ("kimi_dl", DOX_DIR / "kimi_dl_mappings.jsonl"),
]

OUTPUT = DOX_DIR / "fragment_mappings_merged.jsonl"


def load(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open() as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            rows.append(json.loads(line))
    return rows


def collection_key(c: dict[str, Any]) -> tuple[str, str]:
    return (str(c.get("collection", "")), str(c.get("reference", "")))


def merge_collections(*lists: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: dict[tuple[str, str], dict[str, Any]] = {}
    for lst in lists:
        for c in lst or []:
            k = collection_key(c)
            if k not in seen:
                seen[k] = dict(c)
            else:
                # prefer the existing (earlier source = higher priority); only
                # patch verification_source if missing
                existing = seen[k]
                if "verification_source" not in existing and "verification_source" in c:
                    existing["verification_source"] = c["verification_source"]
    return list(seen.values())


def merge(rows_by_source: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    by_passage: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for source, rows in rows_by_source.items():
        for r in rows:
            pid = r.get("passage_id")
            if not pid:
                continue
            by_passage[pid][source].append(r)

    merged: list[dict[str, Any]] = []
    for _pid, by_src in by_passage.items():
        # Pick base = highest-priority source available
        for source in ("curated", "auto_doctorat", "kimi_dl"):
            if source in by_src:
                base = dict(by_src[source][0])
                base_source = source
                break
        else:
            continue
        # Aggregate collections from all sources
        all_collections = []
        for s in ("curated", "auto_doctorat", "kimi_dl"):
            for r in by_src.get(s, []):
                all_collections.append(r.get("fragment_collections") or [])
        base["fragment_collections"] = merge_collections(*all_collections)
        # Mark contributing sources
        contributing = sorted(by_src.keys())
        base.setdefault("doxographical_source", base_source)
        if len(contributing) > 1:
            base["doxographical_contributing_sources"] = contributing
        merged.append(base)
    # Stable sort by passage_id
    merged.sort(key=lambda r: r["passage_id"])
    return merged


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=OUTPUT)
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    rows_by_source: dict[str, list[dict[str, Any]]] = {}
    for source, path in INPUTS:
        rows = load(path)
        rows_by_source[source] = rows
        logger.info("Loaded %d rows from %s", len(rows), path.name)

    merged = merge(rows_by_source)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as fh:
        for r in merged:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Stats
    by_collection: dict[str, int] = defaultdict(int)
    by_confidence: dict[str, int] = defaultdict(int)
    by_source: dict[str, int] = defaultdict(int)
    for r in merged:
        for c in r.get("fragment_collections", []):
            by_collection[c.get("collection", "?")] += 1
        by_confidence[r.get("confidence", "unknown")] += 1
        by_source[r.get("doxographical_source", "unknown")] += 1

    stats = {
        "total_passages": len(merged),
        "by_collection": dict(by_collection),
        "by_confidence": dict(by_confidence),
        "by_source": dict(by_source),
    }
    print(json.dumps(stats, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
