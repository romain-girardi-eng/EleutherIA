#!/usr/bin/env python3
"""Normalize ``period`` fields on ``data/kg/nodes.jsonl`` to the canonical set.

Several legacy nodes carry period labels that are shorthand or alternative
names for the canonical periods (e.g. ``Imperial`` → ``Roman Imperial``).
This script applies the documented mapping and rewrites ``nodes.jsonl`` in
place. Values already canonical are left untouched.

``Cross-period`` is intentionally **not** remapped: it is a meaningful tag
used on philosophical *positions* (fatalism, libertarianism, ...) that
span multiple periods. The canonical period whitelist is extended to
include it in ``generate_shapes.py``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Final

ROOT = Path(__file__).resolve().parents[1]
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"

PERIOD_REMAP: Final[dict[str, str]] = {
    "Imperial": "Roman Imperial",
    "Classical": "Classical Greek",
    "Late Republic": "Roman Republican",
    "Early Christian": "Patristic",
}


def main() -> int:
    rows: list[dict] = []
    with NODES_PATH.open(encoding="utf-8") as fh:
        for raw in fh:
            raw = raw.strip()
            if not raw:
                continue
            rows.append(json.loads(raw))

    touched = 0
    for n in rows:
        p = n.get("period")
        if p in PERIOD_REMAP:
            n["period"] = PERIOD_REMAP[p]
            touched += 1

    tmp = NODES_PATH.with_suffix(".jsonl.tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        for n in rows:
            fh.write(json.dumps(n, ensure_ascii=False))
            fh.write("\n")
    tmp.replace(NODES_PATH)
    print(f"Remapped {touched} period values across {len(rows)} nodes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
