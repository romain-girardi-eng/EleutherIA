#!/usr/bin/env python3
"""Repair three work nodes whose canonical CTS id contradicts every child.

Default is dry-run.  The operation is idempotent, verifies exact old values,
and reruns the work/child consistency detector before any write.
"""

from __future__ import annotations

import argparse
import copy
import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.check_kg_work_child_canonical import (  # noqa: E402
    DEFAULT_ALLOWLIST,
    EDGES_PATH,
    MANIFEST_PATH,
    NODES_PATH,
    find_mismatches,
    is_allowlisted,
    load_allowlist,
    read_jsonl,
)

WAVE = "work_canonical_repair_2026_08_18"
BACKUP_SUFFIX = ".bak-work_canonical_repair_2026_08_18"

REPAIRS: dict[str, dict[str, Any]] = {
    "work_de_fato_alexander_c200ce_o6p7q8r9": {
        "expected": "urn:cts:greekLit:tlg2018.tlg005",
        "replacement": "urn:cts:greekLit:tlg0732.tlg014",
        "child_count": 78,
        "manifest": "De Fato, Alexander of Aphrodisias, manifest line 22",
    },
    "work_de_interpretatione_aristotle_c350bce_e4f6g8h0": {
        "expected": "urn:cts:greekLit:tlg0086.tlg038",
        "replacement": "urn:cts:greekLit:tlg0086.tlg017",
        "child_count": 29,
        "manifest": "De interpretatione, Aristotle, manifest line 7",
    },
    "work_de_libero_arbitrio": {
        "expected": "urn:cts:latinLit:stoa0040.stoa054",
        "replacement": "urn:cts:latinLit:stoa0040.stoa003",
        "child_count": 340,
        "manifest": "De Libero Arbitrio, Augustine, manifest line 62",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    return parser.parse_args()


def parse_metadata(node: dict[str, Any]) -> tuple[dict[str, Any], str]:
    value = node.get("metadata") or {}
    if isinstance(value, dict):
        return copy.deepcopy(value), "dict"
    if isinstance(value, str):
        parsed = json.loads(value)
        if isinstance(parsed, dict):
            return parsed, "string"
    raise ValueError(f"unreadable metadata on {node.get('id')}")


def set_metadata(node: dict[str, Any], value: dict[str, Any], form: str) -> None:
    node["metadata"] = (
        json.dumps(value, ensure_ascii=False) if form == "string" else value
    )


def append_note(metadata: dict[str, Any], note: str) -> None:
    notes = metadata.get("verification_notes")
    if not isinstance(notes, list):
        notes = [notes] if isinstance(notes, str) else []
    if note not in notes:
        notes.append(note)
    metadata["verification_notes"] = notes


def transform(nodes: list[dict[str, Any]], now: str) -> list[str]:
    by_id = {str(node.get("id") or node.get("node_id")): node for node in nodes}
    changed: list[str] = []
    for work_id, spec in REPAIRS.items():
        node = by_id.get(work_id)
        if node is None or node.get("type") != "work":
            raise ValueError(f"missing work repair target: {work_id}")
        metadata, form = parse_metadata(node)
        current = metadata.get("cts_urn")
        if current == spec["replacement"] and metadata.get(WAVE):
            continue
        if current != spec["expected"]:
            raise ValueError(
                f"{work_id}: expected old CTS {spec['expected']!r}, got {current!r}"
            )
        note = (
            f"[Vérif. 2026-08-18: corrected work CTS {spec['expected']} -> "
            f"{spec['replacement']}. All {spec['child_count']} part_of passages "
            f"agree on the replacement; corroborated by {spec['manifest']}.]"
        )
        metadata.update(
            {
                "cts_urn": spec["replacement"],
                "work_canonical_id": spec["replacement"],
                "citation_verdict": "corrected",
                "citation_verified": True,
                WAVE: {
                    "previous_cts_urn": spec["expected"],
                    "corrected_cts_urn": spec["replacement"],
                    "attested_children": spec["child_count"],
                    "manifest_evidence": spec["manifest"],
                },
            }
        )
        append_note(metadata, note)
        node["updated_at"] = now
        set_metadata(node, metadata, form)
        changed.append(work_id)
    return changed


def write_nodes_preserving_unchanged(path: Path, rows: list[dict[str, Any]]) -> None:
    raw_rows: dict[str, tuple[dict[str, Any], str]] = {}
    order: list[str] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            wanted_id = str(row.get("id") or row.get("node_id"))
            raw_rows[wanted_id] = (row, line)
            order.append(wanted_id)
    current = {str(row.get("id") or row.get("node_id")): row for row in rows}
    if len(current) != len(rows):
        raise ValueError("duplicate node ids while writing canonical repairs")
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        for wanted_id in order:
            row = current[wanted_id]
            old, raw = raw_rows[wanted_id]
            handle.write(
                raw if row == old else json.dumps(row, ensure_ascii=False) + "\n"
            )
    temporary.replace(path)


def main() -> int:
    args = parse_args()
    nodes = read_jsonl(NODES_PATH)
    edges = read_jsonl(EDGES_PATH)
    manifest = read_jsonl(MANIFEST_PATH)
    try:
        before = find_mismatches(nodes, edges, manifest)
        changed = transform(nodes, datetime.now(UTC).isoformat(sep=" "))
        after = find_mismatches(nodes, edges, manifest)
        allowlist = load_allowlist(DEFAULT_ALLOWLIST)
        novel = [
            finding
            for finding in after
            if not (
                (entry := allowlist.get(finding["work_id"]))
                and is_allowlisted(finding, entry)
            )
        ]
        if novel:
            raise ValueError(f"unresolved novel work/child mismatches: {novel}")
        before_ids = {row["work_id"] for row in before}
        allowed_before = {*REPAIRS, "work_plutarch_de_communibus_notitiis"}
        unexpected_before = before_ids - allowed_before
        if unexpected_before:
            raise ValueError(
                f"unexpected pre-repair mismatch population: {unexpected_before}"
            )
        if set(changed) - before_ids:
            raise ValueError("repair target was not present in the mismatch population")
    except (json.JSONDecodeError, OSError, ValueError) as exc:
        print(f"ABORT: {exc}")
        return 1

    summary = {
        "mode": "apply" if args.apply else "dry-run",
        "changed": changed,
        "mismatches_before": len(before),
        "mismatches_after": len(after),
        "known_ambiguities_after": [row["work_id"] for row in after],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    if not args.apply:
        print("dry-run: nothing written (use --apply)")
        return 0
    backup = NODES_PATH.with_name(NODES_PATH.name + BACKUP_SUFFIX)
    if not backup.exists():
        shutil.copy2(NODES_PATH, backup)
    write_nodes_preserving_unchanged(NODES_PATH, nodes)
    print(json.dumps({"status": "applied", "backup": str(backup)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
