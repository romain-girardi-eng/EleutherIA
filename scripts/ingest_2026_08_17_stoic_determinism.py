#!/usr/bin/env python3
"""Apply the 2026-08-17 Stoic-determinism scholarship delta to the KG.

Idempotent merge of scripts/data_2026_08_17_stoic_determinism.json into
data/kg/{nodes,edges}.jsonl:
- nodes whose id already exists are skipped (batch 1 of this delta was
  applied by an earlier wave);
- edges whose (source, relation, target) triple already exists are skipped;
- every edge endpoint must resolve against existing + new nodes;
- the novel subset must pass check_ingestion_rules.py --new-only with
  BLOCK 0 before anything is written;
- invariants asserted before save; backup written alongside.

Usage: python3 scripts/ingest_2026_08_17_stoic_determinism.py [--apply]
Default is dry-run.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NODES = ROOT / "data/kg/nodes.jsonl"
EDGES = ROOT / "data/kg/edges.jsonl"
DELTA = ROOT / "scripts/data_2026_08_17_stoic_determinism.json"
BAK_SUFFIX = ".bak-stoic_determinism"


def main() -> int:
    apply = "--apply" in sys.argv

    delta = json.loads(DELTA.read_text())
    nodes = [json.loads(l) for l in NODES.read_text().splitlines() if l.strip()]
    edges = [json.loads(l) for l in EDGES.read_text().splitlines() if l.strip()]

    existing_ids = {n["id"] for n in nodes}
    existing_triples = {
        (e.get("source"), e.get("relation") or e.get("type"), e.get("target"))
        for e in edges
    }

    new_nodes = [n for n in delta["nodes"] if n["id"] not in existing_ids]
    skipped_nodes = len(delta["nodes"]) - len(new_nodes)
    all_ids = existing_ids | {n["id"] for n in new_nodes}

    new_edges = []
    skipped_edges = 0
    unresolved = []
    for e in delta["edges"]:
        rel = e.get("relation") or e.get("type")
        triple = (e["source"], rel, e["target"])
        if triple in existing_triples:
            skipped_edges += 1
            continue
        if e["source"] not in all_ids or e["target"] not in all_ids:
            unresolved.append(triple)
            continue
        e.setdefault("source_id", e["source"])
        e.setdefault("target_id", e["target"])
        new_edges.append(e)
        existing_triples.add(triple)

    print(f"delta: {len(delta['nodes'])} nodes / {len(delta['edges'])} edges")
    print(f"novel: {len(new_nodes)} nodes / {len(new_edges)} edges "
          f"(skipped existing: {skipped_nodes} nodes, {skipped_edges} edges)")
    if unresolved:
        print(f"FATAL: {len(unresolved)} edges with unresolvable endpoints: {unresolved[:5]}")
        return 1

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
        json.dump({"nodes": new_nodes, "edges": new_edges}, tf)
        subset_path = tf.name
    gate = subprocess.run(
        [sys.executable, str(ROOT / "scripts/check_ingestion_rules.py"),
         "--new-only", subset_path],
        capture_output=True, text=True,
    )
    print(gate.stdout.strip().splitlines()[-1] if gate.stdout.strip() else gate.stderr[-200:])
    if gate.returncode != 0:
        print("FATAL: ingestion gate failed on the novel subset — nothing written")
        return 1

    for e in new_edges:
        assert e["source"] == e["source_id"] and e["target"] == e["target_id"]
    merged_nodes = nodes + new_nodes
    assert len({n["id"] for n in merged_nodes}) == len(merged_nodes), "duplicate node id"

    if not apply:
        print("dry-run: nothing written (use --apply)")
        return 0

    shutil.copy2(NODES, str(NODES) + BAK_SUFFIX)
    shutil.copy2(EDGES, str(EDGES) + BAK_SUFFIX)
    with NODES.open("a") as f:
        for n in new_nodes:
            f.write(json.dumps(n, ensure_ascii=False) + "\n")
    with EDGES.open("a") as f:
        for e in new_edges:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    print(f"applied: +{len(new_nodes)} nodes, +{len(new_edges)} edges")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
