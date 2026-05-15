"""Apply Patristic KG enrichment patches.

Distinct from apply_kg_enrichment.py (modern scholars): this script handles
ancient persons, ancient works, ancient arguments — preserving the proper
type, period, and metadata semantics (no `role = scholar` injection, no
`argument_type = modern_scholarly_position` injection).

Patch kinds supported:
  - person         -> upsert ancient person node (type=person, period set explicitly)
  - person_update  -> merge into existing person node (description/metadata overwrite,
                       label and period preserved unless explicitly provided)
  - work           -> upsert ancient work node (type=work)
  - argument       -> upsert ancient argument node (type=argument,
                       metadata.argument_type = ancient_philosophical_argument)
  - edge           -> insert kg_edges row idempotently

Idempotent: re-running produces the same KG state. Works against either the
live Supabase pooler DSN (SUPABASE_DATABASE_URL / DATABASE_URL) or against the
local JSONL snapshot (data/kg/nodes.jsonl + edges.jsonl) when --offline is
passed (writes a patched-snapshot for later upload).

Usage:
    set -a; source .env; set +a
    .venv-py314/bin/python database/scripts/apply_patristic_enrichment.py \
        --input data/kg_enrichment/patristic_deep.jsonl \
        --dry-run

    # Offline mode (DB unreachable) — produces data/kg/patched/{nodes,edges}.jsonl
    .venv-py314/bin/python database/scripts/apply_patristic_enrichment.py \
        --input data/kg_enrichment/patristic_deep.jsonl --offline
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]

VALID_KINDS = {"person", "person_update", "work", "argument", "concept", "edge"}


@dataclass
class Patch:
    kind: str
    raw: dict[str, Any]
    node_id: str = ""
    node_type: str = ""
    label: str = ""
    description: str | None = None
    period: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    source_id: str = ""
    target_id: str = ""
    relation: str = ""
    weight: float = 1.0


def normalize(p: Patch) -> Patch | None:
    r = p.raw
    if p.kind in ("person", "person_update"):
        p.node_id = r.get("node_id") or ""
        if not p.node_id:
            return None
        p.node_type = "person"
        p.label = r.get("label") or p.node_id
        p.description = r.get("description")
        p.period = r.get("period")
        p.metadata = r.get("metadata") or {}
        return p
    if p.kind == "work":
        p.node_id = r.get("node_id") or ""
        if not p.node_id:
            return None
        p.node_type = "work"
        p.label = r.get("label") or p.node_id
        p.description = r.get("description")
        p.period = r.get("period")
        p.metadata = r.get("metadata") or {}
        return p
    if p.kind == "argument":
        p.node_id = r.get("node_id") or ""
        if not p.node_id:
            return None
        p.node_type = "argument"
        p.label = (r.get("label") or p.node_id)[:300]
        p.description = r.get("description")
        p.period = r.get("period") or "Late Antiquity"
        meta = dict(r.get("metadata") or {})
        meta.setdefault("argument_type", "ancient_philosophical_argument")
        p.metadata = meta
        return p
    if p.kind == "concept":
        p.node_id = r.get("node_id") or ""
        if not p.node_id:
            return None
        p.node_type = "concept"
        p.label = (r.get("label") or p.node_id)[:300]
        p.description = r.get("description")
        p.period = r.get("period")
        p.metadata = r.get("metadata") or {}
        return p
    if p.kind == "edge":
        p.source_id = r.get("source_id") or ""
        p.target_id = r.get("target_id") or ""
        p.relation = r.get("edge_type") or r.get("relation") or ""
        if not (p.source_id and p.target_id and p.relation):
            return None
        meta = dict(r.get("metadata") or {})
        p.metadata = meta
        try:
            w = float(meta.get("weight") or meta.get("confidence") or 1.0)
        except (TypeError, ValueError):
            w = 1.0
        p.weight = min(w, 1.0)
        return p
    return None


def load(paths: list[Path]) -> list[Patch]:
    out: list[Patch] = []
    for path in paths:
        for ln_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            line = line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"{path}:{ln_no}: invalid JSON: {exc}") from exc
            kind = raw.get("kind")
            if kind not in VALID_KINDS:
                raise SystemExit(f"{path}:{ln_no}: unknown kind {kind!r}")
            out.append(Patch(kind=kind, raw=raw))
    return out


# -------- DB apply path --------

UPSERT_SQL = """
INSERT INTO free_will.kg_nodes (node_id, label, type, description, period, alternative_names, metadata)
VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7::jsonb)
ON CONFLICT (node_id) DO UPDATE SET
    label = COALESCE(NULLIF(EXCLUDED.label, ''), free_will.kg_nodes.label),
    type = EXCLUDED.type,
    description = COALESCE(EXCLUDED.description, free_will.kg_nodes.description),
    period = COALESCE(EXCLUDED.period, free_will.kg_nodes.period),
    metadata = free_will.kg_nodes.metadata || EXCLUDED.metadata,
    updated_at = now()
RETURNING (xmax = 0) AS inserted
"""

EDGE_SQL = """
INSERT INTO free_will.kg_edges (source_id, target_id, relation, weight, metadata)
SELECT $1::varchar, $2::varchar, $3::varchar, $4::double precision, $5::jsonb
WHERE NOT EXISTS (
    SELECT 1 FROM free_will.kg_edges e
    WHERE e.source_id = $1::varchar AND e.target_id = $2::varchar AND e.relation = $3::varchar
)
RETURNING 1
"""


async def apply_db(patches: list[Patch], dsn: str, *, dry_run: bool) -> dict[str, Any]:
    import asyncpg  # type: ignore

    conn = await asyncpg.connect(dsn=dsn, statement_cache_size=0)
    counts: Counter[str] = Counter()
    try:
        existing = {r["node_id"] for r in await conn.fetch("SELECT node_id FROM free_will.kg_nodes")}
        for p in patches:
            n = normalize(p)
            if n is None:
                counts["rejected_normalize"] += 1
                continue
            if p.kind == "edge":
                if n.source_id not in existing and n.source_id not in {q.node_id for q in patches if q.kind != "edge"}:
                    counts["edges_unresolved_source"] += 1
                    continue
                if n.target_id not in existing and n.target_id not in {q.node_id for q in patches if q.kind != "edge"}:
                    counts["edges_unresolved_target"] += 1
                    continue
                if dry_run:
                    counts["edges_planned"] += 1
                    continue
                got = await conn.fetchval(
                    EDGE_SQL,
                    n.source_id, n.target_id, n.relation, n.weight,
                    json.dumps(n.metadata, ensure_ascii=False),
                )
                counts["edges_inserted" if got == 1 else "edges_skipped_existing"] += 1
            else:
                if dry_run:
                    counts["nodes_updated" if n.node_id in existing else "nodes_inserted"] += 1
                    continue
                row = await conn.fetchrow(
                    UPSERT_SQL,
                    n.node_id, n.label, n.node_type, n.description, n.period,
                    json.dumps([]),
                    json.dumps(n.metadata, ensure_ascii=False),
                )
                counts["nodes_inserted" if row and row["inserted"] else "nodes_updated"] += 1
    finally:
        await conn.close()
    return dict(counts)


# -------- Offline (JSONL snapshot) path --------

def apply_offline(patches: list[Patch], out_dir: Path) -> dict[str, Any]:
    nodes_in = REPO_ROOT / "data" / "kg" / "nodes.jsonl"
    edges_in = REPO_ROOT / "data" / "kg" / "edges.jsonl"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_nodes = out_dir / "nodes.jsonl"
    out_edges = out_dir / "edges.jsonl"

    # Load
    by_id: dict[str, dict[str, Any]] = {}
    with nodes_in.open("r", encoding="utf-8") as fh:
        for line in fh:
            n = json.loads(line)
            by_id[n["node_id"]] = n
    edges = [json.loads(line) for line in edges_in.open("r", encoding="utf-8")]

    counts: Counter[str] = Counter()
    new_edges: list[dict[str, Any]] = []
    edge_set = {(e["source_id"], e["target_id"], e.get("relation")) for e in edges}

    for p in patches:
        n = normalize(p)
        if n is None:
            counts["rejected_normalize"] += 1
            continue
        if p.kind == "edge":
            if n.source_id not in by_id:
                counts["edges_unresolved_source"] += 1
                continue
            if n.target_id not in by_id:
                counts["edges_unresolved_target"] += 1
                continue
            key = (n.source_id, n.target_id, n.relation)
            if key in edge_set:
                counts["edges_skipped_existing"] += 1
                continue
            edge_set.add(key)
            new_edges.append({
                "source_id": n.source_id,
                "target_id": n.target_id,
                "relation": n.relation,
                "weight": n.weight,
                "metadata": n.metadata,
            })
            counts["edges_inserted"] += 1
        else:
            existing = by_id.get(n.node_id)
            if existing is None:
                by_id[n.node_id] = {
                    "node_id": n.node_id,
                    "label": n.label,
                    "type": n.node_type,
                    "description": n.description or "",
                    "period": n.period,
                    "metadata": n.metadata,
                }
                counts["nodes_inserted"] += 1
            else:
                existing["label"] = n.label or existing.get("label")
                if n.description:
                    existing["description"] = n.description
                if n.period:
                    existing["period"] = n.period
                merged = dict(existing.get("metadata") or {})
                merged.update(n.metadata)
                existing["metadata"] = merged
                existing["type"] = n.node_type
                counts["nodes_updated"] += 1

    with out_nodes.open("w", encoding="utf-8") as fh:
        for nid in sorted(by_id):
            fh.write(json.dumps(by_id[nid], ensure_ascii=False) + "\n")
    with out_edges.open("w", encoding="utf-8") as fh:
        for e in edges:
            fh.write(json.dumps(e, ensure_ascii=False) + "\n")
        for e in new_edges:
            fh.write(json.dumps(e, ensure_ascii=False) + "\n")

    counts["total_nodes_after"] = len(by_id)
    counts["total_edges_after"] = len(edges) + len(new_edges)
    return dict(counts)


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Apply Patristic KG enrichment.")
    p.add_argument("--input", action="append", type=Path, required=True)
    p.add_argument("--database-url", default=os.getenv("SUPABASE_DATABASE_URL") or os.getenv("DATABASE_URL"))
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--offline", action="store_true", help="Apply against data/kg/nodes.jsonl + edges.jsonl, writing to data/kg/patched/")
    p.add_argument("--out-dir", type=Path, default=REPO_ROOT / "data" / "kg" / "patched")
    return p.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    patches = load(args.input)
    print(f"Loaded {len(patches)} patches")
    by_kind = Counter(p.kind for p in patches)
    for k, c in sorted(by_kind.items()):
        print(f"  kind={k:18s} count={c}")

    if args.offline:
        counts = apply_offline(patches, args.out_dir)
        print(f"\n=== OFFLINE APPLY → {args.out_dir} ===")
    else:
        if not args.database_url:
            print("Missing --database-url / $DATABASE_URL — use --offline to apply against JSONL snapshot.", file=sys.stderr)
            return 2
        counts = asyncio.run(apply_db(patches, args.database_url, dry_run=args.dry_run))
        print(f"\n=== {'DRY-RUN' if args.dry_run else 'APPLIED to DB'} ===")
    for k, v in sorted(counts.items()):
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
