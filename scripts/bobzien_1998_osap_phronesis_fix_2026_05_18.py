#!/usr/bin/env python3
"""Bobzien 1998 — OSAP → Phronesis factual fix — 2026-05-18

Bobzien 1998 "The Inadvertent Conception and Late Birth of the Free-Will
Problem" is in *Phronesis* 43(2): 133-175.

*OSAP* (Oxford Studies in Ancient Philosophy) is Bobzien 2000 "Did Epicurus
Discover the Free Will Problem?" — a different paper.

Several KG nodes mistakenly attribute the 1998 paper to OSAP. This patch
applies targeted, idempotent string substitutions to the 5 affected nodes
in ``data/kg/nodes.jsonl``. Genuine OSAP refs (Bobzien 2000) are not
touched — the substitution pattern always includes "1998" so 2000 refs are
safe.

Snapshots ``data/kg/nodes.jsonl`` before mutation. Preserves byte-exact
formatting of all unrelated lines (only re-serializes touched nodes).
"""
from __future__ import annotations

import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"
SNAPSHOT_DIR = ROOT / "data" / "kg" / "snapshots" / "2026-05-18-pre-bobzien-osap-phronesis-fix"

# Substitutions to apply on every JSON-string field of a touched node.
# Each tuple is (old, new). The "1998" anchor in every key prevents
# accidental rewriting of legitimate Bobzien 2000 OSAP references.
SUBSTITUTIONS: list[tuple[str, str]] = [
    ("Bobzien 1998 OSAP / Phronesis", "Bobzien 1998 Phronesis"),
    ("Bobzien 1998 OSAP", "Bobzien 1998 Phronesis"),
    ("1998 OSAP companion paper", "1998 Phronesis companion paper"),
    ("companion 1998 OSAP paper", "companion 1998 Phronesis paper"),
    ("her 1998 OSAP paper", "her 1998 Phronesis paper"),
    ("son 1998 OSAP", "son 1998 Phronesis"),
    ("dans Bobzien 1998 OSAP", "dans Bobzien 1998 Phronesis"),
]

NODES_TO_FIX = {
    "concept_eph_hemin_two_sided_potestative",
    "person_alexander_aphrodisias_fl200ce_n5o6p7q8",
    "person_bobzien_susanne_contemporary",
    "argument_bobzien_2001_b1_eph_hemin_one_vs_two_sided",
    "argument_bobzien_2001_b1_rise_fall_freedom_problem",
}

PATCH_MARKER = "osap_phronesis_fix_2026_05_18"


def node_id_of_line(line: str) -> str:
    n = json.loads(line)
    return n.get("id") or n.get("node_id") or ""


def apply_subs(value: Any) -> tuple[Any, int]:
    """Recursively apply string substitutions in any nested structure."""
    if isinstance(value, str):
        n = 0
        out = value
        for old, new in SUBSTITUTIONS:
            if old in out:
                n += out.count(old)
                out = out.replace(old, new)
        return out, n
    if isinstance(value, list):
        total = 0
        new_list = []
        for v in value:
            v2, k = apply_subs(v)
            new_list.append(v2)
            total += k
        return new_list, total
    if isinstance(value, dict):
        total = 0
        new_dict = {}
        for k, v in value.items():
            v2, n = apply_subs(v)
            new_dict[k] = v2
            total += n
        return new_dict, total
    return value, 0


def fix_node(node: dict[str, Any]) -> tuple[dict[str, Any], int]:
    """Apply substitutions across the node, including its serialised metadata blob."""
    # Plain string fields (description, description_en, label, etc.)
    new_node: dict[str, Any] = {}
    total = 0
    for k, v in node.items():
        if k == "metadata" and isinstance(v, str) and v.strip():
            try:
                md = json.loads(v)
            except json.JSONDecodeError:
                new_node[k] = v
                continue
            md2, count = apply_subs(md)
            total += count
            new_node[k] = json.dumps(md2, ensure_ascii=False)
        elif k == "metadata" and isinstance(v, dict):
            md2, count = apply_subs(v)
            total += count
            new_node[k] = md2
        else:
            v2, count = apply_subs(v)
            total += count
            new_node[k] = v2
    return new_node, total


def snapshot() -> None:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(NODES_PATH, SNAPSHOT_DIR / NODES_PATH.name)


def main() -> int:
    raw_lines = [
        line.rstrip("\n")
        for line in NODES_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    changes: dict[str, int] = {}
    new_lines = list(raw_lines)

    for idx, ln in enumerate(raw_lines):
        nid = node_id_of_line(ln)
        if nid not in NODES_TO_FIX:
            continue
        node = json.loads(ln)
        # Skip if already marked (idempotence — check the metadata blob).
        md_raw = node.get("metadata")
        if isinstance(md_raw, str):
            try:
                md_check = json.loads(md_raw)
            except json.JSONDecodeError:
                md_check = {}
        elif isinstance(md_raw, dict):
            md_check = md_raw
        else:
            md_check = {}
        if md_check.get(PATCH_MARKER):
            continue

        fixed, count = fix_node(node)
        if count == 0:
            # Nothing matched — mark anyway to avoid re-checking, but warn.
            print(f"WARN: no substitution matched for {nid}", file=sys.stderr)
            continue

        # Stamp the patch marker into metadata.
        md_field = fixed.get("metadata")
        if isinstance(md_field, str):
            md = json.loads(md_field) if md_field.strip() else {}
            md[PATCH_MARKER] = (
                "Fixed OSAP→Phronesis attribution of Bobzien 1998 "
                "'The Inadvertent Conception and Late Birth of the "
                "Free-Will Problem' (Phronesis 43(2): 133-175). OSAP "
                "is Bobzien 2000 on Epicurus."
            )
            fixed["metadata"] = json.dumps(md, ensure_ascii=False)
        elif isinstance(md_field, dict):
            md_field[PATCH_MARKER] = (
                "Fixed OSAP→Phronesis attribution of Bobzien 1998 "
                "Phronesis 43(2): 133-175."
            )
            fixed["metadata"] = md_field

        fixed["updated_at"] = datetime.now(UTC).isoformat(sep=" ")
        new_lines[idx] = json.dumps(fixed, ensure_ascii=False)
        changes[nid] = count

    if not changes:
        print("OK: no nodes needed patching (already fixed)")
        return 0

    snapshot()
    print(f"snapshot: {SNAPSHOT_DIR / NODES_PATH.name}")

    NODES_PATH.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    for nid, count in changes.items():
        print(f"OK: patched {nid} ({count} substitution(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
