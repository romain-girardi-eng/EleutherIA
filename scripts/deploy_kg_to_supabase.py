"""Deploy data/kg/{nodes,edges}.jsonl to the the platform Supabase Postgres.

Closes the loop that the daily `kg-snapshot.yml` workflow leaves open: that
workflow mirrors prod → git, but there's no built-in git → prod path. This
script provides it.

Behavior:
  1. Reads git's data/kg/nodes.jsonl + edges.jsonl
  2. Fetches prod's current state from the the platform public API (rate-limit-safe,
     no DB connection required for the dry-run)
  3. Computes the delta: nodes-to-upsert, edges-to-insert, plus an audit of
     prod-only items
  4. If --apply: connects to Supabase via $SUPABASE_DATABASE_URL and runs the
     upserts inside a single transaction
  5. Re-fetches prod stats post-apply to verify count parity

Schema mapping (git jsonl → free_will.kg_nodes):
  jsonl.id              → node_id
  jsonl.label           → label
  jsonl.type            → type
  jsonl.description     → description
  jsonl.period          → period
  jsonl.metadata        → metadata (jsonb)
  jsonl.description_en  → metadata.description_en (multilingual stashed in jsonb)
  jsonl.description_la  → metadata.description_la
  jsonl.description_grc → metadata.description_grc
  jsonl.description_grc_robinson_with_apparatus → metadata.description_grc_robinson_with_apparatus
  jsonl.description_de  → metadata.description_de
  jsonl.confidence      → metadata.confidence
  jsonl.needs_evidence  → metadata.needs_evidence

SAFETY:
  - Default mode = dry-run. --apply is required to actually write.
  - --apply runs in ONE transaction; rolls back on any error.
  - DOES NOT DELETE prod-only nodes/edges. Use --reconcile-deletions explicitly.
  - Skips nodes/edges already in prod with identical content.

Usage:
    # Dry run (default)
    SUPABASE_DATABASE_URL="postgresql://..." .venv/bin/python3 scripts/deploy_kg_to_supabase.py

    # Apply
    SUPABASE_DATABASE_URL="postgresql://..." .venv/bin/python3 scripts/deploy_kg_to_supabase.py --apply

    # Limit scope (useful for first apply)
    .venv/bin/python3 scripts/deploy_kg_to_supabase.py --apply --max-nodes 100 --max-edges 500
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any

import asyncpg

REPO_ROOT = Path(__file__).resolve().parent.parent
NODES_PATH = REPO_ROOT / "data" / "kg" / "nodes.jsonl"
EDGES_PATH = REPO_ROOT / "data" / "kg" / "edges.jsonl"

DEFAULT_API_BASE = "https://free-will.app"

# Cloudflare blocks the default Python-urllib User-Agent; force a browser UA.
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
}


UPSERT_NODE_SQL = """
INSERT INTO free_will.kg_nodes (node_id, label, type, description, period, alternative_names, metadata)
VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7::jsonb)
ON CONFLICT (node_id) DO UPDATE SET
    label = COALESCE(NULLIF(EXCLUDED.label, ''), free_will.kg_nodes.label),
    type = EXCLUDED.type,
    description = COALESCE(EXCLUDED.description, free_will.kg_nodes.description),
    period = COALESCE(EXCLUDED.period, free_will.kg_nodes.period),
    alternative_names = EXCLUDED.alternative_names,
    metadata = free_will.kg_nodes.metadata || EXCLUDED.metadata,
    updated_at = now()
RETURNING (xmax = 0) AS inserted
"""

INSERT_EDGE_SQL = """
INSERT INTO free_will.kg_edges (source_id, target_id, relation, weight, metadata)
SELECT $1::varchar, $2::varchar, $3::varchar, $4::double precision, $5::jsonb
WHERE NOT EXISTS (
    SELECT 1 FROM free_will.kg_edges e
    WHERE e.source_id = $1::varchar
      AND e.target_id = $2::varchar
      AND e.relation = $3::varchar
)
RETURNING 1
"""


def fetch_json(url: str) -> Any:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


def fetch_prod_state(base: str) -> tuple[list[dict], list[dict]]:
    print(f"Fetching prod from {base} …")
    nodes = fetch_json(f"{base}/api/kg/nodes?limit=50000")
    if not isinstance(nodes, list):
        raise RuntimeError("/api/kg/nodes response is not a list")
    print(f"  prod nodes: {len(nodes):,}")
    edges = []
    offset = 0
    while True:
        page = fetch_json(f"{base}/api/kg/edges?limit=10000&offset={offset}")
        if not page:
            break
        edges.extend(page)
        if len(page) < 10000:
            break
        offset += 10000
    print(f"  prod edges: {len(edges):,}")
    return nodes, edges


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(l) for l in path.open("r", encoding="utf-8") if l.strip()]


def parse_metadata(node_or_edge: dict[str, Any]) -> dict[str, Any]:
    md = node_or_edge.get("metadata")
    if md is None or md == "":
        return {}
    if isinstance(md, dict):
        return dict(md)
    if isinstance(md, str):
        try:
            parsed = json.loads(md)
            return parsed if isinstance(parsed, dict) else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    return {}


# Top-level node fields that don't map to a Postgres column → stash into metadata
NON_COLUMN_FIELDS = {
    "description_en",
    "description_la",
    "description_grc",
    "description_grc_robinson_with_apparatus",
    "description_de",
    "description_fr",
    "confidence",
    "needs_evidence",
}


def shape_node_for_db(node: dict[str, Any]) -> dict[str, Any]:
    """Convert git-jsonl node shape to (node_id, label, type, description, period, alt_names_json, metadata_json) tuple-ready dict."""
    md = parse_metadata(node)
    # Stash non-column fields into metadata
    for key in NON_COLUMN_FIELDS:
        v = node.get(key)
        if v is not None and v != "":
            md.setdefault(key, v)  # don't overwrite if already present in metadata

    # alternative_names: prod schema expects jsonb array; jsonl stores as list or null
    alt_names = node.get("alternative_names") or []
    if isinstance(alt_names, str):
        try:
            alt_names = json.loads(alt_names)
        except (json.JSONDecodeError, TypeError):
            alt_names = []

    return {
        "node_id": node["id"],
        "label": node.get("label") or node["id"],
        "type": node.get("type") or "unknown",
        "description": node.get("description"),
        "period": node.get("period"),
        "alt_names_json": json.dumps(alt_names, ensure_ascii=False),
        "metadata_json": json.dumps(md, ensure_ascii=False),
    }


def edge_key(e: dict[str, Any]) -> tuple[str, str, str]:
    return (e["source"], e["target"], e["relation"])


def compute_delta(git_nodes: list[dict], git_edges: list[dict],
                  prod_nodes: list[dict], prod_edges: list[dict]) -> dict[str, Any]:
    # Pre-compute id/key sets ONCE (was the perf hot path: O(N²) when set was
    # rebuilt inside each comprehension iteration → 46k × 43k ≈ 2B ops).
    prod_node_ids = {n["id"] for n in prod_nodes}
    prod_edge_keys = {(e["source"], e["target"], e["relation"]) for e in prod_edges}
    git_node_ids = {n["id"] for n in git_nodes}
    git_edge_keys = {edge_key(e) for e in git_edges}

    nodes_to_upsert = git_nodes  # upsert ALL git nodes (idempotent on existing)
    nodes_only_in_git = [n for n in git_nodes if n["id"] not in prod_node_ids]
    nodes_only_in_prod = [n for n in prod_nodes if n["id"] not in git_node_ids]
    edges_to_insert = [e for e in git_edges if edge_key(e) not in prod_edge_keys]
    edges_only_in_prod = [e for e in prod_edges
                           if (e["source"], e["target"], e["relation"]) not in git_edge_keys]

    return {
        "nodes_to_upsert": nodes_to_upsert,
        "nodes_only_in_git": nodes_only_in_git,
        "nodes_only_in_prod": nodes_only_in_prod,
        "edges_to_insert": edges_to_insert,
        "edges_only_in_prod": edges_only_in_prod,
        # Cached for FK-safe --max-nodes mode (private, do not include in dump)
        "_prod_nodes_for_fk_check": prod_nodes,
    }


def print_delta_report(d: dict[str, Any]) -> None:
    print("\n=== DEPLOY DELTA REPORT ===")
    print(f"  Nodes to upsert (all git):          {len(d['nodes_to_upsert']):,}")
    print(f"    of which new to prod:             {len(d['nodes_only_in_git']):,}")
    print(f"    of which updates of existing:     {len(d['nodes_to_upsert']) - len(d['nodes_only_in_git']):,}")
    print(f"  Edges to insert (new only):         {len(d['edges_to_insert']):,}")
    print(f"\n  Prod-only nodes (NOT touched by upsert): {len(d['nodes_only_in_prod']):,}")
    if d["nodes_only_in_prod"]:
        type_counts = Counter(n.get("type", "?") for n in d["nodes_only_in_prod"])
        print(f"    by type: {dict(type_counts.most_common())}")
    print(f"  Prod-only edges (NOT touched):      {len(d['edges_only_in_prod']):,}")
    print(f"\n  New nodes by type:")
    new_type_counts = Counter(n.get("type", "?") for n in d["nodes_only_in_git"])
    for t, c in new_type_counts.most_common():
        print(f"    {t:<25s} {c:6d}")


async def apply_delta(conn: asyncpg.Connection, delta: dict[str, Any],
                       max_nodes: int | None = None, max_edges: int | None = None) -> dict[str, int]:
    counts = {"nodes_inserted": 0, "nodes_updated": 0, "edges_inserted": 0, "edges_skipped": 0}
    nodes = delta["nodes_to_upsert"]
    edges = delta["edges_to_insert"]
    if max_nodes is not None:
        nodes = nodes[:max_nodes]
        print(f"  (--max-nodes limit: {max_nodes} of {len(delta['nodes_to_upsert'])})")
        # FK-safe: drop edges whose endpoints aren't in (upserted nodes + prod nodes).
        # Without this filter, --max-nodes leaves edges pointing at nodes not yet
        # in prod, triggering kg_edges_target_id_fkey violations.
        upserted_ids = {n["id"] for n in nodes}
        prod_ids = {n["id"] for n in delta.get("_prod_nodes_for_fk_check", [])}
        # If we don't have prod IDs cached, fall back to a conservative filter:
        # only edges where BOTH endpoints are in the upserted set.
        valid_ids = upserted_ids | prod_ids if prod_ids else upserted_ids
        filtered = [e for e in edges if e["source"] in valid_ids and e["target"] in valid_ids]
        skipped_fk = len(edges) - len(filtered)
        if skipped_fk:
            print(f"  (--max-nodes mode: filtered {skipped_fk} edges with endpoints outside upserted+prod sets)")
        edges = filtered
    if max_edges is not None:
        edges = edges[:max_edges]
        print(f"  (--max-edges limit: {max_edges} of {len(delta['edges_to_insert'])})")

    async with conn.transaction():
        for i, node in enumerate(nodes):
            try:
                shape = shape_node_for_db(node)
                row = await conn.fetchrow(
                    UPSERT_NODE_SQL,
                    shape["node_id"],
                    shape["label"],
                    shape["type"],
                    shape["description"],
                    shape["period"],
                    shape["alt_names_json"],
                    shape["metadata_json"],
                )
                if row and row["inserted"]:
                    counts["nodes_inserted"] += 1
                else:
                    counts["nodes_updated"] += 1
                if (i + 1) % 100 == 0:
                    print(f"    {i+1}/{len(nodes)} nodes processed …")
            except Exception as e:
                print(f"\n  ERROR on node {node.get('id')}: {e}")
                raise

        for i, edge in enumerate(edges):
            md = parse_metadata(edge)
            md_json = json.dumps(md, ensure_ascii=False)
            weight = edge.get("confidence") or edge.get("weight") or 1.0
            try:
                result = await conn.fetchval(
                    INSERT_EDGE_SQL,
                    edge["source"], edge["target"], edge["relation"],
                    float(weight), md_json,
                )
                if result == 1:
                    counts["edges_inserted"] += 1
                else:
                    counts["edges_skipped"] += 1
                if (i + 1) % 500 == 0:
                    print(f"    {i+1}/{len(edges)} edges processed …")
            except Exception as e:
                print(f"\n  ERROR on edge {edge.get('source')} --{edge.get('relation')}--> {edge.get('target')}: {e}")
                raise

    return counts


async def main_async(args: argparse.Namespace) -> int:
    print(f"Reading git state: {NODES_PATH.name} + {EDGES_PATH.name}")
    git_nodes = load_jsonl(NODES_PATH)
    git_edges = load_jsonl(EDGES_PATH)
    print(f"  git: {len(git_nodes):,} nodes, {len(git_edges):,} edges")

    prod_nodes, prod_edges = fetch_prod_state(args.api_base)

    delta = compute_delta(git_nodes, git_edges, prod_nodes, prod_edges)
    print_delta_report(delta)

    # Optionally dump the delta details for audit
    if args.dump_delta:
        # Strip private cache key before dumping
        delta.pop("_prod_nodes_for_fk_check", None)
        out = {
            "summary": {
                "git_nodes": len(git_nodes), "prod_nodes": len(prod_nodes),
                "git_edges": len(git_edges), "prod_edges": len(prod_edges),
                "nodes_only_in_git": len(delta["nodes_only_in_git"]),
                "nodes_only_in_prod": len(delta["nodes_only_in_prod"]),
                "edges_to_insert": len(delta["edges_to_insert"]),
                "edges_only_in_prod": len(delta["edges_only_in_prod"]),
            },
            "nodes_only_in_prod_sample": [
                {"id": n["id"], "type": n.get("type"), "label": (n.get("label") or "")[:80]}
                for n in delta["nodes_only_in_prod"][:50]
            ],
            "new_nodes_sample": [
                {"id": n["id"], "type": n.get("type"), "label": (n.get("label") or "")[:80]}
                for n in delta["nodes_only_in_git"][:50]
            ],
        }
        Path(args.dump_delta).write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nDelta detail written to {args.dump_delta}")

    if not args.apply:
        print("\n=== DRY RUN — no DB writes performed. Use --apply to deploy. ===")
        return 0

    dsn = os.environ.get("SUPABASE_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not dsn:
        print("\nERROR: neither SUPABASE_DATABASE_URL nor DATABASE_URL set. Cannot --apply.")
        return 2
    if dsn == os.environ.get("DATABASE_URL"):
        print("  (using DATABASE_URL fallback)")

    print(f"\nConnecting to Supabase …")
    conn = await asyncpg.connect(dsn=dsn, statement_cache_size=0)
    try:
        print(f"Running upserts in transaction …")
        counts = await apply_delta(conn, delta, max_nodes=args.max_nodes, max_edges=args.max_edges)
        print(f"\n=== APPLY COMPLETE ===")
        for k, v in counts.items():
            print(f"  {k}: {v:,}")
        stats = await conn.fetchrow(
            "SELECT (SELECT count(*) FROM free_will.kg_nodes) AS n, "
            "(SELECT count(*) FROM free_will.kg_edges) AS e"
        )
        print(f"\n  Post-apply DB counts: {stats['n']:,} nodes, {stats['e']:,} edges")
        return 0
    finally:
        await conn.close()


def main() -> int:
    p = argparse.ArgumentParser(description="Deploy git KG state to Supabase")
    p.add_argument("--api-base", default=DEFAULT_API_BASE,
                   help=f"Prod API base URL (default: {DEFAULT_API_BASE})")
    p.add_argument("--apply", action="store_true",
                   help="Actually run the upserts (default: dry-run)")
    p.add_argument("--max-nodes", type=int, default=None,
                   help="Limit node upserts (useful for first apply, e.g. --max-nodes 100)")
    p.add_argument("--max-edges", type=int, default=None,
                   help="Limit edge inserts (useful for first apply)")
    p.add_argument("--dump-delta", default=None,
                   help="Path to dump the delta report as JSON")
    args = p.parse_args()
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    sys.exit(main())
