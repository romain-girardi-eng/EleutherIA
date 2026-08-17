#!/usr/bin/env python3
"""Apply the Origenality bibliographic import delta to the KG.

Merges scripts/data_2026_08_17_origenality_import.json:
- "nodes": new publication records (honesty markers citation_verdict=
  bibliographic_import + source_rank required on every one) — skipped if
  the id already exists;
- "edges": skipped if the (source, relation, target) triple exists; both
  endpoints must resolve; source_id/target_id enforced;
- "enrichments": metadata additions to EXISTING nodes, applied only when
  the recorded preconditions still hold and only for keys the target
  does not already carry.
The novel-node subset must pass check_ingestion_rules.py --new-only with
BLOCK 0 before anything is written.

Usage: python3 scripts/ingest_2026_08_17_origenality_import.py [--apply]
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
DELTA = ROOT / "scripts/data_2026_08_17_origenality_import.json"
BAK = ".bak-origenality"
STAMP = "origenality_import_2026_08_17"


def parse_md(node: dict) -> dict:
    md = node.get("metadata") or {}
    return json.loads(md) if isinstance(md, str) else md


def main() -> int:
    apply = "--apply" in sys.argv
    delta = json.loads(DELTA.read_text())
    nodes = [json.loads(l) for l in NODES.read_text().splitlines() if l.strip()]
    edges = [json.loads(l) for l in EDGES.read_text().splitlines() if l.strip()]
    by_id = {n["id"]: n for n in nodes}
    triples = {(e.get("source"), e.get("relation") or e.get("type"), e.get("target"))
               for e in edges}

    new_nodes = []
    for n in delta["nodes"]:
        if n["id"] in by_id:
            continue
        md = parse_md(n)
        assert md.get("citation_verdict") == "bibliographic_import", n["id"]
        assert md.get("source_rank"), n["id"]
        new_nodes.append(n)
    all_ids = set(by_id) | {n["id"] for n in new_nodes}

    new_edges = []
    unresolved = []
    for e in delta["edges"]:
        rel = e.get("relation") or e.get("type")
        t = (e["source"], rel, e["target"])
        if t in triples:
            continue
        if e["source"] not in all_ids or e["target"] not in all_ids:
            unresolved.append(t)
            continue
        e.setdefault("source_id", e["source"])
        e.setdefault("target_id", e["target"])
        new_edges.append(e)
        triples.add(t)
    if unresolved:
        print(f"FATAL: {len(unresolved)} unresolvable edges: {unresolved[:5]}")
        return 1

    enriched = skipped_enrich = 0
    for enr in delta.get("enrichments", []):
        tgt = by_id.get(enr["target_id"])
        if tgt is None:
            skipped_enrich += 1
            continue
        pre = enr.get("preconditions") or {}
        md = parse_md(tgt)
        ok = True
        if "type" in pre and tgt.get("type") != pre["type"]:
            ok = False
        if "label" in pre and tgt.get("label") != pre["label"]:
            ok = False
        if "metadata_year" in pre and md.get("year") not in (pre["metadata_year"], str(pre["metadata_year"])):
            ok = False
        if not ok:
            skipped_enrich += 1
            continue
        if md.get("origenality_import_stamp") == STAMP:
            continue
        added = {k: v for k, v in (enr.get("metadata") or {}).items() if k not in md}
        if added and apply:
            md.update(added)
            md["origenality_import_stamp"] = STAMP
            if isinstance(tgt.get("metadata"), str):
                tgt["metadata"] = json.dumps(md, ensure_ascii=False)
            else:
                tgt["metadata"] = md
        if added:
            enriched += 1

    print(f"delta: {len(delta['nodes'])} nodes / {len(delta['edges'])} edges / "
          f"{len(delta.get('enrichments', []))} enrichments")
    print(f"novel: {len(new_nodes)} nodes / {len(new_edges)} edges | "
          f"enrichable: {enriched} (skipped {skipped_enrich})")

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
        json.dump({"nodes": new_nodes, "edges": new_edges}, tf)
        subset = tf.name
    gate = subprocess.run(
        [sys.executable, str(ROOT / "scripts/check_ingestion_rules.py"),
         "--new-only", subset], capture_output=True, text=True)
    tail = gate.stdout.strip().splitlines()[-1] if gate.stdout.strip() else gate.stderr[-200:]
    print(tail)
    if gate.returncode != 0:
        print("FATAL: ingestion gate failed — nothing written")
        return 1

    merged = nodes + new_nodes
    assert len({n["id"] for n in merged}) == len(merged), "duplicate node id"
    for e in new_edges:
        assert e["source"] == e["source_id"] and e["target"] == e["target_id"]

    if not apply:
        print("dry-run: nothing written (use --apply)")
        return 0

    shutil.copy2(NODES, str(NODES) + BAK)
    shutil.copy2(EDGES, str(EDGES) + BAK)
    NODES.write_text("".join(json.dumps(n, ensure_ascii=False) + "\n" for n in merged))
    with EDGES.open("a") as f:
        for e in new_edges:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    print(f"applied: +{len(new_nodes)} nodes, +{len(new_edges)} edges, "
          f"{enriched} nodes enriched")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
