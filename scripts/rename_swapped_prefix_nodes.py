#!/usr/bin/env python3
"""Rename node IDs whose prefix swaps another canonical type.

Five legacy nodes are typed ``synthesis`` but carry an ID prefixed
``concept_``. Per the SHACL IdPrefix shape (and the Python audit at
``scripts/audit_kg_quality.py``) this is a true "swapped prefix"
mismatch — the ID misadvertises the type and breaks downstream
type-prefix conventions.

This script:

1. Reads ``data/kg/nodes.jsonl`` and ``data/kg/edges.jsonl``
2. For each of the five known IDs, mints a ``synthesis_<rest>`` form
3. Rewrites the node's ``id``
4. Updates every edge whose ``source`` or ``target`` matches the old ID
5. Verifies no orphan references remain
6. Writes both files atomically (temp + rename)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Final

ROOT = Path(__file__).resolve().parents[1]
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"
EDGES_PATH = ROOT / "data" / "kg" / "edges.jsonl"

# old_id -> new_id. Each old ID starts with the foreign prefix; the new
# ID strips that foreign prefix and substitutes the correct one.
RENAMES: Final[dict[str, str]] = {
    "concept_ditte_hamartia_double_sin_plotinus": (
        "synthesis_ditte_hamartia_double_sin_plotinus"
    ),
    "concept_epict_eph_hemin_synthesis": (
        "synthesis_epict_eph_hemin_doctrine"
    ),
    "concept_cic_fat_synthesis": (
        "synthesis_cic_fat_in_nostra_potestate"
    ),
    "concept_epict_thematic_index": (
        "synthesis_epict_thematic_index"
    ),
    "concept_cic_fat_index": (
        "synthesis_cic_fat_index"
    ),
}


def _rewrite_jsonl(path: Path, transform) -> tuple[int, int]:
    rows: list[dict] = []
    with path.open(encoding="utf-8") as fh:
        for raw in fh:
            raw = raw.strip()
            if not raw:
                continue
            rows.append(json.loads(raw))

    touched = 0
    for r in rows:
        if transform(r):
            touched += 1

    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False))
            fh.write("\n")
    tmp.replace(path)
    return touched, len(rows)


def _rename_node(node: dict) -> bool:
    old = node.get("id")
    if old in RENAMES:
        node["id"] = RENAMES[old]
        return True
    return False


def _rename_edge(edge: dict) -> bool:
    changed = False
    src = edge.get("source")
    if src in RENAMES:
        edge["source"] = RENAMES[src]
        changed = True
    tgt = edge.get("target")
    if tgt in RENAMES:
        edge["target"] = RENAMES[tgt]
        changed = True
    return changed


def main() -> int:
    nodes_touched, nodes_total = _rewrite_jsonl(NODES_PATH, _rename_node)
    edges_touched, edges_total = _rewrite_jsonl(EDGES_PATH, _rename_edge)
    print(f"Renamed {nodes_touched}/{nodes_total} nodes in {NODES_PATH.name}")
    print(f"Updated {edges_touched}/{edges_total} edges in {EDGES_PATH.name}")

    # Sanity check: no edge still references an old ID.
    stale = 0
    with EDGES_PATH.open(encoding="utf-8") as fh:
        for raw in fh:
            raw = raw.strip()
            if not raw:
                continue
            e = json.loads(raw)
            if e.get("source") in RENAMES or e.get("target") in RENAMES:
                stale += 1
    if stale:
        print(f"WARN: {stale} edges still reference an old ID", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
