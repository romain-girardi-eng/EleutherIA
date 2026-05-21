#!/usr/bin/env python3
"""Append Supabase-only KG rows into data/kg so git becomes the superset backup.

After the Supabase recovery (2026-05-21) the live DB held 18 nodes / 469 unique
edges that were not in data/kg (and 0 rows the other way — Supabase fully
contains git). This pulls those missing rows directly from Supabase via asyncpg
and APPENDS them to data/kg/{nodes,edges}.jsonl in the existing schema, leaving
all current lines byte-for-byte untouched.

Idempotent (re-running appends nothing). Snapshot before mutation. Dry-run by
default; --commit to write. Reads DATABASE_URL from .env.
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
SNAPSHOT_DIR = ROOT / "data" / "kg" / "snapshots" / "2026-05-21-pre-supabase-superset-sync"

NODE_COLS = ["node_id", "id", "label", "type", "description", "period",
             "alternative_names", "metadata", "school", "role",
             "created_at", "updated_at"]
EDGE_COLS = ["edge_id", "source_id", "target_id", "source", "target",
             "relation", "weight", "metadata", "created_at"]


def db_url() -> str:
    for l in open(ROOT / ".env"):
        if l.startswith("DATABASE_URL="):
            return l.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("DATABASE_URL not in .env")


def as_str_json(v):
    """Match existing lines: metadata/alternative_names stored as a JSON string."""
    if v is None:
        return None
    if isinstance(v, str):
        return v
    return json.dumps(v, ensure_ascii=False)


def as_ts(v):
    return v.isoformat(sep=" ") if isinstance(v, datetime) else v


def node_line(row: dict) -> str:
    o = {k: row.get(k) for k in NODE_COLS}
    o["metadata"] = as_str_json(o.get("metadata"))
    o["alternative_names"] = as_str_json(o.get("alternative_names"))
    o["created_at"] = as_ts(o.get("created_at"))
    o["updated_at"] = as_ts(o.get("updated_at"))
    return json.dumps(o, ensure_ascii=False, default=str)


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

    loc_nodes = {json.loads(l)["id"] for l in open(NODES_PATH) if l.strip()}
    loc_edges = set()
    for l in open(EDGES_PATH):
        if l.strip():
            e = json.loads(l)
            loc_edges.add(((e.get("source") or e.get("source_id")),
                           (e.get("target") or e.get("target_id")), e.get("relation")))

    c = await asyncio.wait_for(asyncpg.connect(db_url()), timeout=30)
    node_rows = [dict(r) for r in await c.fetch("select * from free_will.kg_nodes")]
    edge_rows = [dict(r) for r in await c.fetch("select * from free_will.kg_edges")]
    await c.close()

    missing_nodes = [r for r in node_rows if r["id"] not in loc_nodes]
    seen = set()
    missing_edges = []
    for r in edge_rows:
        sig = (r.get("source_id"), r.get("target_id"), r.get("relation"))
        if sig in loc_edges or sig in seen:
            continue
        seen.add(sig)
        missing_edges.append(r)

    # superset sanity: nothing should be local-only
    sb_node_ids = {r["id"] for r in node_rows}
    sb_edge_sigs = {(r.get("source_id"), r.get("target_id"), r.get("relation")) for r in edge_rows}
    local_only_nodes = loc_nodes - sb_node_ids
    local_only_edges = loc_edges - sb_edge_sigs

    print(f"missing nodes (to append): {len(missing_nodes)}")
    print(f"missing edges (to append): {len(missing_edges)}")
    print(f"local-only nodes (NOT in Supabase): {len(local_only_nodes)}")
    print(f"local-only edges (NOT in Supabase): {len(local_only_edges)}")
    if local_only_nodes or local_only_edges:
        print("WARNING: git has rows absent from Supabase — not a clean superset; "
              "review before relying on Supabase as source of truth.")

    if not missing_nodes and not missing_edges:
        print("OK: git already contains all Supabase rows (idempotent no-op).")
        return 0
    if not commit:
        print("[DRY-RUN] --commit to append.")
        return 0

    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(NODES_PATH, SNAPSHOT_DIR / NODES_PATH.name)
    shutil.copy2(EDGES_PATH, SNAPSHOT_DIR / EDGES_PATH.name)

    if missing_nodes:
        with open(NODES_PATH, "a", encoding="utf-8") as f:
            for r in missing_nodes:
                f.write(node_line(r) + "\n")
    if missing_edges:
        with open(EDGES_PATH, "a", encoding="utf-8") as f:
            for r in missing_edges:
                f.write(edge_line(r) + "\n")
    print(f"snapshot: {SNAPSHOT_DIR}")
    print(f"DONE: +{len(missing_nodes)} nodes, +{len(missing_edges)} edges")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", action="store_true")
    raise SystemExit(asyncio.run(main(ap.parse_args().commit)))
