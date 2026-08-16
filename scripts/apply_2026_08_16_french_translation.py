#!/usr/bin/env python3
"""Apply the 2026-08-16 French -> English translation of the analytical KG nodes.

A large part of the analytical layer of the graph (arguments, syntheses, person
and work notes, publication abstracts) was authored in French while the platform
itself is English. This script installs the reviewed English rendering as the
reader-facing `description` and archives the French original in
`metadata.description_fr`, so nothing is destroyed.

Scope and exclusions:

* `passage` and `quote` nodes are never touched — French inside them is the
  edition text (Sources Chretiennes and comparable bilingual editions), which is
  primary material, not project prose.
* A `publication` description that is nothing but the French bibliographic title
  of the publication is left alone: a title is a citation key, not prose.
* `publication` and `work` labels are left alone for the same reason.

The translations were produced by gpt-5.6-terra under a scholarly-translator
brief that requires every ancient Greek run, every Latin quotation, every
bibliographic reference and every markdown structure to be reproduced verbatim,
and were validated item by item before being written to the payload file
(`data/audit/2026-08-16_french_translations.jsonl`): Greek multiset identity
against the source, length ratio, citation-marker counts, and an
English-dominance check. Items that failed validation twice are absent from the
payload and are listed in the review file.

The script is deterministic and idempotent. Every write is guarded by an exact
match between the node's current `description` (resp. `label`) and the French
original recorded in the payload; a node whose text has drifted is reported and
skipped, never overwritten blind. A node already carrying
`metadata.translation_2026_08_16` is skipped on any later run, so re-running is
a no-op.

Usage:
    python3 scripts/apply_2026_08_16_french_translation.py [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"
PAYLOAD_PATH = ROOT / "data" / "audit" / "2026-08-16_french_translations.jsonl"

APPLIED_MARKER = "translation_2026_08_16"
ENGINE = "gpt-5.6-terra"

log: list[str] = []
stats: dict[str, int] = {}


def bump(key: str, n: int = 1) -> None:
    stats[key] = stats.get(key, 0) + n


# --- io ---------------------------------------------------------------------


def node_id_of(node: dict) -> str | None:
    return node.get("node_id") or node.get("id")


def load_jsonl(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def dump_jsonl(path: Path, rows: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def parse_metadata(node: dict) -> tuple[dict, str]:
    """Metadata is sometimes a dict, sometimes a (double-)encoded JSON string."""
    raw = node.get("metadata")
    if isinstance(raw, dict):
        return raw, "dict"
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except ValueError:
            return {}, "opaque"
        if isinstance(parsed, str):
            try:
                inner = json.loads(parsed)
            except ValueError:
                return {}, "opaque"
            return (inner, "str2") if isinstance(inner, dict) else ({}, "opaque")
        return (parsed, "str") if isinstance(parsed, dict) else ({}, "opaque")
    return {}, "none"


def dump_metadata(node: dict, meta: dict, form: str) -> None:
    if form in ("dict", "none"):
        node["metadata"] = meta
    elif form == "str":
        node["metadata"] = json.dumps(meta, ensure_ascii=False)
    elif form == "str2":
        node["metadata"] = json.dumps(
            json.dumps(meta, ensure_ascii=False), ensure_ascii=False
        )
    # "opaque" -> leave untouched


# --- apply ------------------------------------------------------------------


def apply_all(dry_run: bool) -> int:
    payload = {row["node_id"]: row for row in load_jsonl(PAYLOAD_PATH)}
    nodes = load_jsonl(NODES_PATH)
    by_id = {node_id_of(n): n for n in nodes}

    for nid, row in payload.items():
        node = by_id.get(nid)
        if node is None:
            log.append(f"[MISSING] {nid}: not in nodes.jsonl")
            bump("missing")
            continue

        meta, form = parse_metadata(node)
        if form == "opaque":
            log.append(f"[SKIP-META] {nid}: metadata is not decodable JSON")
            bump("skipped_opaque_metadata")
            continue
        if meta.get(APPLIED_MARKER):
            bump("already_applied")
            continue

        touched = False

        if row.get("description_en"):
            current = node.get("description") or ""
            if current != row["description_fr"]:
                log.append(
                    f"[SKIP-DESC] {nid}: current description differs from the "
                    "recorded French original — text drifted, not overwritten"
                )
                bump("skipped_desc_drift")
            else:
                # Archive the French original. Never destroy it.
                meta["description_fr"] = row["description_fr"]
                # A pre-existing English rendering is kept, under an archive key,
                # only when it actually differs from the new translation.
                prev_en = meta.get("description_en")
                if prev_en and prev_en.strip() != row["description_en"].strip():
                    meta["description_en_pre_2026_08_16"] = prev_en
                meta["description_en"] = row["description_en"]
                node["description"] = row["description_en"]
                touched = True
                bump("descriptions")

        if row.get("label_en"):
            if (node.get("label") or "") != row.get("label_fr"):
                log.append(
                    f"[SKIP-LABEL] {nid}: current label differs from the recorded "
                    "French original — not overwritten"
                )
                bump("skipped_label_drift")
            else:
                meta["label_fr"] = row["label_fr"]
                node["label"] = row["label_en"]
                touched = True
                bump("labels")

        if touched:
            meta[APPLIED_MARKER] = ENGINE
            dump_metadata(node, meta, form)
            bump("nodes_touched")

    if not dry_run and stats.get("nodes_touched"):
        dump_jsonl(NODES_PATH, nodes)

    print(f"payload rows: {len(payload)}")
    for key in sorted(stats):
        print(f"  {key}: {stats[key]}")
    for line in log:
        print(line)
    if dry_run:
        print("[dry-run] nodes.jsonl not written")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if not PAYLOAD_PATH.exists():
        print(f"payload not found: {PAYLOAD_PATH}", file=sys.stderr)
        return 1
    return apply_all(args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
