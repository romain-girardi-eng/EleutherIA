#!/usr/bin/env python3
"""Wire the new person_paul_apostle node to its Pauline-studies arguments.

The acquisition-patch integration created person_paul_apostle but the reading
agents had targeted work_new_testament (no Paul person existed at read time),
leaving the node disconnected. Eastman 2017 (Paul and the Person) and
Barclay 2020 (Paul and the Power of Grace) are both Pauline exegesis end-to-end,
so every one of their arguments discusses Paul.

Idempotent. Snapshot before mutation. Dry-run by default; --commit to write.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EDGES_PATH = ROOT / "data" / "kg" / "edges.jsonl"
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"
PATCHES_DIR = ROOT / "data" / "kg" / "acquisition_patches"
SNAPSHOT_DIR = ROOT / "data" / "kg" / "snapshots" / "2026-05-21-pre-paul-wiring"

WAVE = "paul_wiring_2026_05_21"
NOW = datetime.now(UTC).isoformat(sep=" ")
PAUL = "person_paul_apostle"
PAULINE_PATCHES = ("eastman", "barclay_2020")


def main(commit: bool) -> int:
    node_ids = set()
    for ln in NODES_PATH.read_text(encoding="utf-8").splitlines():
        if ln.strip():
            node_ids.add(json.loads(ln).get("id"))
    if PAUL not in node_ids:
        print(f"ERROR: {PAUL} not in nodes.jsonl — run integrate_acquisition_patches first", file=sys.stderr)
        return 2

    edge_lines = [ln for ln in EDGES_PATH.read_text(encoding="utf-8").splitlines() if ln.strip()]
    sigs = set()
    for ln in edge_lines:
        e = json.loads(ln)
        sigs.add(((e.get("source") or e.get("source_id")),
                  (e.get("target") or e.get("target_id")),
                  e.get("relation")))

    arg_ids: list[str] = []
    for name in PAULINE_PATCHES:
        d = json.loads((PATCHES_DIR / f"{name}.json").read_text(encoding="utf-8"))
        for a in (d.get("arguments") or d.get("scholarly_arguments") or []):
            if a.get("id") in node_ids:
                arg_ids.append(a["id"])

    new_edges = []
    for aid in arg_ids:
        sig = (aid, PAUL, "discusses")
        if sig not in sigs:
            new_edges.append({"source": aid, "target": PAUL, "relation": "discusses",
                              "confidence": 0.9, "metadata": {"wave": WAVE}})
            sigs.add(sig)

    print(f"Pauline args found: {len(arg_ids)} | new discusses→{PAUL}: {len(new_edges)}")
    if not new_edges:
        print("OK: nothing to apply (idempotent).")
        return 0
    if not commit:
        print("[DRY-RUN] --commit to write.")
        return 0

    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(EDGES_PATH, SNAPSHOT_DIR / EDGES_PATH.name)
    edge_lines.extend(json.dumps(e, ensure_ascii=False) for e in new_edges)
    EDGES_PATH.write_text("\n".join(edge_lines) + "\n", encoding="utf-8")
    print(f"DONE: +{len(new_edges)} edges")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", action="store_true")
    sys.exit(main(ap.parse_args().commit))
