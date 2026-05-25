"""Surgically sync a KG subgraph (nodes whose node_id starts with a prefix, and
all edges touching them) from the live Supabase DB into the git mirror
data/kg/{nodes,edges}.jsonl — matching export_kg_snapshot's deterministic format.

Why not export_kg_snapshot? That tool reads the *Railway* backend, which is a
separate/stale DB (different counts). The corpus + KG git mirrors track the
Supabase DB (DATABASE_URL). This helper rewrites only the targeted subgraph's
lines, leaving the rest of the mirror (incl. pre-existing drift) untouched.

Usage: python -m scripts.sync_kg_subgraph_to_git --prefix passage_arist_gen_corr_ [--commit]
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

from scripts.export_kg_snapshot import (
    edge_sort_key,
    node_sort_key,
    write_jsonl,
)

SCHEMA = "free_will"
ROOT = Path(__file__).resolve().parents[1]
NODES = ROOT / "data" / "kg" / "nodes.jsonl"
EDGES = ROOT / "data" / "kg" / "edges.jsonl"


def _db_url() -> str:
    load_dotenv(ROOT / ".env")
    url = os.getenv("DATABASE_URL")
    if not url:
        sys.exit("ERROR: DATABASE_URL not set")
    return url.replace("postgresql://", "postgres://")


def _read(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


async def run(prefix: str, commit: bool) -> None:
    conn = await asyncpg.connect(_db_url())
    try:
        node_rows = await conn.fetch(
            f"SELECT * FROM {SCHEMA}.kg_nodes WHERE node_id LIKE $1", prefix + "%")
        edge_rows = await conn.fetch(
            f"""SELECT * FROM {SCHEMA}.kg_edges
                WHERE source_id LIKE $1 OR target_id LIKE $1""", prefix + "%")
    finally:
        await conn.close()
    import datetime
    import uuid

    # The DB columns already match the git mirror's key set exactly; just coerce
    # UUID/datetime/Decimal-like values to the same string/number forms the mirror
    # uses (metadata stays the DB JSON string). No reshaping (no normalize_*).
    def _row(r) -> dict:
        out = {}
        for k, v in dict(r).items():
            if isinstance(v, (datetime.datetime, datetime.date, uuid.UUID)):
                out[k] = str(v)
            elif k == "weight" and v is not None:
                out[k] = float(v)
            else:
                out[k] = v
        return out

    live_nodes = [_row(r) for r in node_rows]
    live_edges = [_row(r) for r in edge_rows]

    import json
    # rebuild nodes.jsonl: drop any line whose node_id matches the prefix, add live
    kept_n = [ln for ln in _read(NODES)
              if not str(json.loads(ln).get("node_id", "")).startswith(prefix)]
    all_n = [json.loads(ln) for ln in kept_n] + live_nodes
    all_n.sort(key=node_sort_key)
    # rebuild edges.jsonl: drop lines touching the prefix, add live
    def _touches(e: dict) -> bool:
        return (str(e.get("source_id", "")).startswith(prefix)
                or str(e.get("target_id", "")).startswith(prefix))
    kept_e = [json.loads(ln) for ln in _read(EDGES) if not _touches(json.loads(ln))]
    all_e = kept_e + live_edges
    all_e.sort(key=edge_sort_key)

    print(f"prefix={prefix!r}")
    print(f"nodes: git had {len(_read(NODES))}, live-subgraph {len(live_nodes)}, "
          f"new total {len(all_n)}")
    print(f"edges: git had {len(_read(EDGES))}, live-subgraph {len(live_edges)}, "
          f"new total {len(all_e)}")
    if commit:
        write_jsonl(NODES, all_n)
        write_jsonl(EDGES, all_e)
        print("WROTE nodes.jsonl + edges.jsonl")
    else:
        print("(dry-run — use --commit to write)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prefix", required=True, help="node_id prefix of the subgraph")
    ap.add_argument("--commit", action="store_true")
    args = ap.parse_args()
    asyncio.run(run(args.prefix, args.commit))


if __name__ == "__main__":
    main()
