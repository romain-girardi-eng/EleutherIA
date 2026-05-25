#!/usr/bin/env python3
"""Export the live KG (nodes + edges) as sorted JSONL files under data/kg/.

SOURCE OF TRUTH = the Supabase Postgres DB (DATABASE_URL), read directly via
asyncpg — the same store the corpus snapshot and production use. (This previously
pulled from a Railway HTTP backend that has since diverged from Supabase; that
default was stale and would clobber the mirror.)

Deterministic output: JSONL sorted by a stable key with stable in-object key
ordering, so `git diff` and delta packing stay clean. Designed to run from a
GitHub Action: commit only if the snapshot changed.

Edges whose (source, target, relation) triple appears in the quarantine file
(`data/kg/quarantine_supabase_drift_*.jsonl`) are excluded, preserving the prior
deliberate decision to keep that drift out of the mirror.
"""
from __future__ import annotations

import argparse
import asyncio
import datetime
import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any

import asyncpg
from dotenv import load_dotenv

SCHEMA = "free_will"
ROOT = Path(__file__).resolve().parents[1]


def _db_url() -> str:
    load_dotenv(ROOT / ".env")
    url = os.getenv("DATABASE_URL")
    if not url:
        sys.exit("ERROR: DATABASE_URL not found in environment or .env")
    return url.replace("postgresql://", "postgres://")


def canonical_dumps(obj: Any) -> str:
    """Deterministic JSON: sorted keys, compact separators, unicode preserved."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _coerce(d: dict) -> dict:
    """Match the mirror's scalar forms: UUID/datetime -> str; weight -> float.
    metadata is left exactly as the DB JSON string."""
    out: dict[str, Any] = {}
    for k, v in d.items():
        if isinstance(v, (datetime.datetime, datetime.date, uuid.UUID)):
            out[k] = str(v)
        elif k == "weight" and v is not None:
            out[k] = float(v)
        else:
            out[k] = v
    return out


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(canonical_dumps(row))
            f.write("\n")
    tmp.replace(path)


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        f.write(json.dumps(obj, sort_keys=True, ensure_ascii=False, indent=2))
        f.write("\n")
    tmp.replace(path)


def node_sort_key(n: dict) -> tuple[str, str]:
    return (str(n.get("type") or ""), str(n.get("id") or n.get("node_id") or ""))


def edge_sort_key(e: dict) -> tuple[str, str, str]:
    return (str(e.get("source") or ""), str(e.get("target") or ""),
            str(e.get("relation") or ""))


def build_counts(nodes: list[dict], edges: list[dict]) -> dict[str, Any]:
    types: dict[str, int] = {}
    for n in nodes:
        t = str(n.get("type") or "unknown")
        types[t] = types.get(t, 0) + 1
    relations: dict[str, int] = {}
    for e in edges:
        r = str(e.get("relation") or "unknown")
        relations[r] = relations.get(r, 0) + 1
    return {
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "node_types": dict(sorted(types.items())),
        "edge_relations": dict(sorted(relations.items())),
    }


def _quarantine_triples(out_dir: Path) -> set[tuple]:
    triples: set[tuple] = set()
    for q in out_dir.glob("quarantine_*drift*.jsonl"):
        for ln in q.read_text(encoding="utf-8").splitlines():
            if not ln.strip():
                continue
            e = json.loads(ln)
            triples.add((e.get("source_id") or e.get("source"),
                         e.get("target_id") or e.get("target"),
                         e.get("relation")))
    return triples


async def _fetch(out_dir: Path) -> tuple[list[dict], list[dict]]:
    conn = await asyncpg.connect(_db_url())
    try:
        node_rows = await conn.fetch(f"SELECT * FROM {SCHEMA}.kg_nodes")
        edge_rows = await conn.fetch(f"SELECT * FROM {SCHEMA}.kg_edges")
    finally:
        await conn.close()
    nodes = [_coerce(dict(r)) for r in node_rows]
    quarantine = _quarantine_triples(out_dir)
    edges = []
    for r in edge_rows:
        e = _coerce(dict(r))
        if (e.get("source_id"), e.get("target_id"), e.get("relation")) in quarantine:
            continue
        edges.append(e)
    if quarantine:
        print(f"[snapshot] excluded {len(edge_rows) - len(edges)} quarantined edge(s)",
              file=sys.stderr)
    return nodes, edges


def main() -> int:
    parser = argparse.ArgumentParser(description="Export KG snapshot from Supabase as sorted JSONL")
    parser.add_argument("--out", default="data/kg",
                        help="Output directory relative to repo root (default: data/kg)")
    args = parser.parse_args()
    out_dir = ROOT / args.out if not os.path.isabs(args.out) else Path(args.out)

    print("[snapshot] source=Supabase (DATABASE_URL)", file=sys.stderr)
    nodes, edges = asyncio.run(_fetch(out_dir))
    print(f"[snapshot]   {len(nodes)} nodes, {len(edges)} edges", file=sys.stderr)

    nodes.sort(key=node_sort_key)
    edges.sort(key=edge_sort_key)
    write_jsonl(out_dir / "nodes.jsonl", nodes)
    write_jsonl(out_dir / "edges.jsonl", edges)
    counts = build_counts(nodes, edges)
    write_json(out_dir / "stats.json", counts)
    write_json(out_dir / "_snapshot.json", {"source": "supabase", "counts": counts})
    print(f"[snapshot] wrote {len(nodes)} nodes, {len(edges)} edges to {out_dir}/",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
