#!/usr/bin/env python3
"""Unify the Methodius De autexousio work number on tlg2959.tlg002.

14 passage_meth_dla_* nodes carry urn:cts:greekLit:tlg2959.tlg001 while the
other 97 carry tlg2959.tlg002. First1KGreek's CTS metadata for tlg2959.tlg002
titles it "De Libero Arbitrio" (data/tlg2959/tlg002/__cts__.xml), so .tlg002 is
the canonical work number; .tlg001 belongs to the Symposium. This surfaced as a
NEW kg_work_id collision group once passage URNs were demoted to work level.

Usage: python3 scripts/apply_2026_08_17_methodius_work_urn_fix.py [--write]
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NODES = ROOT / "data/kg/nodes.jsonl"
OLD = "urn:cts:greekLit:tlg2959.tlg001"
NEW = "urn:cts:greekLit:tlg2959.tlg002"
STAMP = "methodius_work_urn_fix_2026_08_17"


def main() -> int:
    write = "--write" in sys.argv
    nodes = [json.loads(line) for line in NODES.read_text().splitlines() if line.strip()]
    changed = 0
    for n in nodes:
        raw = n.get("metadata")
        md = json.loads(raw) if isinstance(raw, str) else (raw or {})
        if not n["id"].startswith("passage_meth_dla_"):
            continue
        touched = False
        for key in ("cts_urn", "work_canonical_id"):
            val = md.get(key)
            if isinstance(val, str) and OLD in val:
                md[key] = val.replace(OLD, NEW)
                touched = True
        if touched:
            md[STAMP] = (
                "work number unified on tlg002 (was tlg001; First1KGreek "
                "tlg2959/tlg002 = De Libero Arbitrio)"
            )
            n["metadata"] = json.dumps(md, ensure_ascii=False) if isinstance(raw, str) else md
            changed += 1
    print(f"nodes touched: {changed}")
    blob = "".join(json.dumps(n, ensure_ascii=False) + "\n" for n in nodes)
    assert OLD not in blob, "old work number still present after rewrite"
    if not write:
        print("dry-run: nothing written (use --write)")
        return 0
    shutil.copy2(NODES, str(NODES) + ".bak-meth_urn_fix")
    NODES.write_text(blob)
    print("written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
