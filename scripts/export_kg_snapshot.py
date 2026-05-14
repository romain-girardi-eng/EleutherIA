#!/usr/bin/env python3
"""Export the live KG (nodes + edges) as sorted JSONL files under data/kg/.

Designed to run from a GitHub Action daily: commit only if the snapshot
changed, so Git history becomes a time-series of every KG mutation.

Source: the Railway-hosted backend at $KG_API_BASE (public endpoints,
no auth required). Falls back to a sensible default for local runs.

The output is deterministic: JSONL sorted by a stable key, with stable
key ordering inside each object. That makes `git diff` and delta packing
work well.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_BASE = "https://eleutheria-backend-production.up.railway.app"
NODES_PATH = "/api/kg/nodes"
EDGES_PATH = "/api/kg/edges"
STATS_PATH = "/api/kg/stats"

EDGES_PAGE_SIZE = 10000  # server caps at 10000
REQUEST_TIMEOUT = 120


def fetch_json(url: str) -> Any:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
        return json.loads(resp.read())


def fetch_nodes(base: str) -> list[dict]:
    data = fetch_json(f"{base}{NODES_PATH}?limit=50000")
    if not isinstance(data, list):
        raise RuntimeError(f"Unexpected /api/kg/nodes response: {type(data).__name__}")
    return data


def fetch_edges(base: str) -> list[dict]:
    out: list[dict] = []
    offset = 0
    while True:
        url = f"{base}{EDGES_PATH}?limit={EDGES_PAGE_SIZE}&offset={offset}"
        page = fetch_json(url)
        if not isinstance(page, list):
            raise RuntimeError(
                f"Unexpected /api/kg/edges response: {type(page).__name__}"
            )
        if not page:
            break
        out.extend(page)
        if len(page) < EDGES_PAGE_SIZE:
            break
        offset += EDGES_PAGE_SIZE
    return out


def canonical_dumps(obj: Any) -> str:
    """Deterministic JSON: sorted keys, compact separators, unicode preserved."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


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
    return (str(n.get("type") or ""), str(n.get("id") or ""))


def edge_sort_key(e: dict) -> tuple[str, str, str]:
    return (
        str(e.get("source") or ""),
        str(e.get("target") or ""),
        str(e.get("relation") or ""),
    )


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


def main() -> int:
    parser = argparse.ArgumentParser(description="Export KG snapshot as sorted JSONL")
    parser.add_argument(
        "--base",
        default=os.environ.get("KG_API_BASE", DEFAULT_BASE),
        help="Backend base URL (default: env KG_API_BASE or Railway production)",
    )
    parser.add_argument(
        "--out",
        default="data/kg",
        help="Output directory relative to repo root (default: data/kg)",
    )
    parser.add_argument(
        "--skip-stats-endpoint",
        action="store_true",
        help="Do not call /api/kg/stats (counts are recomputed locally anyway)",
    )
    args = parser.parse_args()

    out_dir = Path(args.out)
    base = args.base.rstrip("/")

    print(f"[snapshot] base={base}", file=sys.stderr)
    print(f"[snapshot] output={out_dir}", file=sys.stderr)

    try:
        print("[snapshot] fetching nodes...", file=sys.stderr)
        nodes = fetch_nodes(base)
        print(f"[snapshot]   {len(nodes)} nodes", file=sys.stderr)

        print("[snapshot] fetching edges (paginated)...", file=sys.stderr)
        edges = fetch_edges(base)
        print(f"[snapshot]   {len(edges)} edges", file=sys.stderr)
    except urllib.error.HTTPError as e:
        print(f"[snapshot] ERROR HTTP {e.code}: {e.reason}", file=sys.stderr)
        return 2
    except urllib.error.URLError as e:
        print(f"[snapshot] ERROR URL: {e.reason}", file=sys.stderr)
        return 2

    nodes.sort(key=node_sort_key)
    edges.sort(key=edge_sort_key)

    write_jsonl(out_dir / "nodes.jsonl", nodes)
    write_jsonl(out_dir / "edges.jsonl", edges)

    counts = build_counts(nodes, edges)
    write_json(out_dir / "stats.json", counts)

    remote_stats: Any = None
    if not args.skip_stats_endpoint:
        try:
            remote_stats = fetch_json(f"{base}{STATS_PATH}")
        except Exception as e:
            print(f"[snapshot] stats endpoint unavailable: {e}", file=sys.stderr)

    snapshot_meta = {
        "source": base,
        "counts": counts,
    }
    if remote_stats:
        snapshot_meta["remote_stats"] = remote_stats
    write_json(out_dir / "_snapshot.json", snapshot_meta)

    print(
        f"[snapshot] wrote {len(nodes)} nodes, {len(edges)} edges to {out_dir}/",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
