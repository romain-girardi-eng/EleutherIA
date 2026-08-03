#!/usr/bin/env python3
"""Append ontology-VALID Supabase-only edges to data/kg; quarantine the rest.

The Supabase recovery surfaced 469 edges in the live DB that are not in git.
~253 of them violate the edge ontology (mostly reversed `created_by` edges with
a person as source, e.g. person -> concept/work/argument) — drift that bypassed
the deploy SHACL gate. Importing them wholesale breaks CI and pollutes the clean
git KG.

This appends only the ontology-valid Supabase-only edges to data/kg/edges.jsonl
and writes the invalid ones to data/kg/quarantine_supabase_drift_2026_05_21.jsonl
(each annotated with the reason) so nothing is lost and the drift can be fixed
and re-deployed later.

Validity is checked against knowledge graph/ontology/edge_types.json
(source_types / target_types), the same source the SHACL shapes are generated
from. Idempotent. Snapshot before mutation. Dry-run by default; --commit.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"
EDGES_PATH = ROOT / "data" / "kg" / "edges.jsonl"
ONTOLOGY = ROOT / "knowledge graph" / "ontology" / "edge_types.json"
QUARANTINE = ROOT / "data" / "kg" / "quarantine_supabase_drift_2026_05_21.jsonl"
SNAPSHOT_DIR = ROOT / "data" / "kg" / "snapshots" / "2026-05-21-pre-valid-edge-sync"

EDGE_COLS = ["edge_id", "source_id", "target_id", "source", "target",
             "relation", "weight", "metadata", "created_at"]


def db_url() -> str:
    for l in open(ROOT / ".env"):
        if l.startswith("DATABASE_URL="):
            return l.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("DATABASE_URL not in .env")


def as_str_json(v):
    if v is None or isinstance(v, str):
        return v
    return json.dumps(v, ensure_ascii=False)


def as_ts(v):
    return v.isoformat(sep=" ") if isinstance(v, datetime) else v


def edge_line(row: dict) -> str:
    o = {k: row.get(k) for k in EDGE_COLS}
    o["metadata"] = as_str_json(o.get("metadata"))
    o["created_at"] = as_ts(o.get("created_at"))
    if o.get("weight") is not None:
        try:
            o["weight"] = float(o["weight"])
        except (TypeError, ValueError):
            o["weight"] = 1.0
    return json.dumps(o, ensure_ascii=False, default=str)


async def main(commit: bool) -> int:
    import asyncpg

    ont = json.loads(ONTOLOGY.read_text())["edge_types"]
    ntype = {}
    for l in open(NODES_PATH):
        if l.strip():
            n = json.loads(l)
            ntype[n["id"]] = n.get("type")
    loc_edges = set()
    for l in open(EDGES_PATH):
        if l.strip():
            e = json.loads(l)
            loc_edges.add(((e.get("source") or e.get("source_id")),
                           (e.get("target") or e.get("target_id")), e.get("relation")))

    c = await asyncio.wait_for(asyncpg.connect(db_url()), timeout=30)
    edge_rows = [dict(r) for r in await c.fetch("select * from free_will.kg_edges")]
    await c.close()

    def validity(r) -> str | None:
        rel = r.get("relation")
        spec = ont.get(rel)
        if spec is None:
            return f"unknown relation '{rel}'"
        s, t = r.get("source_id"), r.get("target_id")
        st, tt = ntype.get(s), ntype.get(t)
        if st is None or tt is None:
            return "endpoint node missing from data/kg"
        if st not in (spec.get("source_types") or []):
            return f"source type '{st}' not allowed for '{rel}'"
        if tt not in (spec.get("target_types") or []):
            return f"target type '{tt}' not allowed for '{rel}'"
        return None

    valid, quarantine = [], []
    seen = set()
    for r in edge_rows:
        sig = (r.get("source_id"), r.get("target_id"), r.get("relation"))
        if sig in loc_edges or sig in seen:
            continue
        seen.add(sig)
        why = validity(r)
        (quarantine if why else valid).append((r, why))

    print(f"Supabase-only unique edges: {len(valid) + len(quarantine)}")
    print(f"  valid (append):       {len(valid)}")
    print(f"  invalid (quarantine): {len(quarantine)}")
    from collections import Counter
    print("  quarantine reasons:", dict(Counter(w for _, w in quarantine)))

    if not valid and not quarantine:
        print("OK: nothing to sync (idempotent).")
        return 0
    if not commit:
        print("[DRY-RUN] --commit to write.")
        return 0

    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(EDGES_PATH, SNAPSHOT_DIR / EDGES_PATH.name)
    if valid:
        with open(EDGES_PATH, "a", encoding="utf-8") as f:
            for r, _ in valid:
                f.write(edge_line(r) + "\n")
    if quarantine:
        with open(QUARANTINE, "w", encoding="utf-8") as f:
            for r, why in quarantine:
                o = json.loads(edge_line(r))
                o["_quarantine_reason"] = why
                f.write(json.dumps(o, ensure_ascii=False) + "\n")
    print(f"snapshot: {SNAPSHOT_DIR}")
    print(f"DONE: +{len(valid)} edges appended, {len(quarantine)} quarantined -> {QUARANTINE.name}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", action="store_true")
    raise SystemExit(asyncio.run(main(ap.parse_args().commit)))
