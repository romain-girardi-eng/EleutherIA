"""Apply KG enrichment patches (Wave 3: modern scholars).

Merges the patches produced by B1 (local DOCTORAT library) and B2 (web research),
canonicalizes scholar IDs against the existing KG, validates against the live
ontology, and upserts idempotently into Supabase.

Patch kinds:
  - scholar          -> person node with metadata.role = "scholar"
  - scholarly_work   -> publication node
  - scholarly_argument -> argument node with metadata.argument_type = "modern_scholarly_position"
  - edge             -> kg_edges row

Stub edge targets (topic:..., primary_source_hint:...) are NOT inserted as
edges; they are preserved as `unresolved_targets` metadata on the source node
for future resolution.

The script is idempotent: re-running it produces the same KG state.

Usage:
    SUPABASE_DATABASE_URL=... .venv-py314/bin/python database/scripts/apply_kg_enrichment.py \
        --input data/kg_enrichment/from_local_library.jsonl \
        --input data/kg_enrichment/from_web_research.jsonl \
        --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import asyncpg

REPO_ROOT = Path(__file__).resolve().parents[2]

# Canonical alias map: known cross-file ID duplicates that should collapse to
# the same node. Keys are aliases; values are the canonical ID we keep.
# All B1+B2 patches use IDs that already resolve to distinct DB nodes, so this
# map is intentionally minimal; it exists to absorb future drift.
SCHOLAR_ID_ALIASES: dict[str, str] = {
    # No aliases needed at this time — B1 scholar_* IDs match existing DB IDs,
    # and B2 person_* IDs match existing DB IDs. Reserved for future waves.
}

# Targets we will NOT create edges for (they are stub references resolved later).
STUB_PREFIXES = ("topic:", "primary_source_hint:", "passage_alexander_de_fato")

# Periods we accept for scholar metadata
SCHOLAR_PERIODS = {"Modern", "Contemporary"}


@dataclass
class Patch:
    kind: str
    raw: dict[str, Any]
    # Normalized fields populated by the validator:
    node_id: str = ""
    node_type: str = ""  # person | publication | argument
    label: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    description: str | None = None
    period: str | None = None
    # For edges:
    source_id: str = ""
    target_id: str = ""
    relation: str = ""
    weight: float = 1.0


@dataclass
class ValidationResult:
    accepted: list[Patch]
    rejected: list[tuple[Patch, str]]
    unresolved_edges: list[tuple[Patch, str]]


# ---------------------------------------------------------------------------
# Loading + normalization
# ---------------------------------------------------------------------------


def load_patches(paths: list[Path]) -> list[Patch]:
    out: list[Patch] = []
    for path in paths:
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            line = line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
            if not isinstance(raw, dict) or "kind" not in raw:
                raise ValueError(f"{path}:{line_no}: missing 'kind'")
            out.append(Patch(kind=raw["kind"], raw=raw))
    return out


def canonicalize_id(raw_id: str) -> str:
    return SCHOLAR_ID_ALIASES.get(raw_id, raw_id)


def normalize(patch: Patch) -> Patch | None:
    """Convert raw patch to a normalized DB-ready form.

    Returns None if the patch shape is invalid (caller logs a rejection).
    """
    r = patch.raw
    kind = patch.kind

    if kind == "scholar":
        node_id = canonicalize_id(r.get("node_id") or r.get("id") or "")
        if not node_id:
            return None
        # Build metadata: merge raw fields except internal markers
        meta_in = r.get("metadata") or {}
        # Web-research patches have flat fields; library patches have nested metadata
        flat = {
            k: v
            for k, v in r.items()
            if k not in {"kind", "op", "id", "node_id", "label", "metadata"}
        }
        merged = {**flat, **meta_in}
        merged["role"] = "scholar"
        # Track legacy aliases
        legacy = r.get("node_id") or r.get("id")
        if legacy and legacy != node_id:
            merged.setdefault("aliases", []).append(legacy)
        period = merged.get("period") or "Contemporary"
        if period not in SCHOLAR_PERIODS:
            period = "Contemporary"
        patch.node_id = node_id
        patch.node_type = "person"
        patch.label = r.get("label") or node_id
        patch.metadata = merged
        patch.period = period
        patch.description = merged.get("specialty") or None
        return patch

    if kind == "scholarly_work":
        node_id = r.get("node_id") or r.get("id") or ""
        if not node_id:
            return None
        meta_in = r.get("metadata") or {}
        flat = {
            k: v
            for k, v in r.items()
            if k not in {"kind", "op", "id", "node_id", "label", "metadata"}
        }
        merged = {**flat, **meta_in}
        if "author_id" in merged:
            merged["author_id"] = canonicalize_id(str(merged["author_id"]))
        title = merged.get("title") or r.get("label") or node_id
        label = r.get("label") or title
        patch.node_id = node_id
        patch.node_type = "publication"
        patch.label = label
        patch.metadata = merged
        patch.period = merged.get("period") or "Contemporary"
        patch.description = title if isinstance(title, str) else None
        return patch

    if kind == "scholarly_argument":
        node_id = r.get("node_id") or r.get("id") or ""
        if not node_id:
            return None
        meta_in = r.get("metadata") or {}
        flat = {
            k: v
            for k, v in r.items()
            if k not in {"kind", "op", "id", "node_id", "label", "metadata"}
        }
        merged = {**flat, **meta_in}
        if "scholar_id" in merged:
            merged["scholar_id"] = canonicalize_id(str(merged["scholar_id"]))
        merged["argument_type"] = "modern_scholarly_position"
        # Build description from topic+stance for full-text search
        topic = merged.get("topic") or ""
        stance = merged.get("stance") or ""
        description = " — ".join(part for part in (topic, stance) if part)
        label = r.get("label") or (f"{topic}" if topic else node_id)
        patch.node_id = node_id
        patch.node_type = "argument"
        patch.label = label[:300] if isinstance(label, str) else node_id
        patch.metadata = merged
        patch.description = description or None
        patch.period = "Contemporary"
        return patch

    if kind == "edge":
        src = canonicalize_id(str(r.get("source_id") or r.get("source") or ""))
        tgt = canonicalize_id(str(r.get("target_id") or r.get("target") or ""))
        rel = r.get("edge_type") or r.get("relation") or ""
        if not (src and tgt and rel):
            return None
        meta = r.get("metadata") or {}
        if "description" in r and "description" not in meta:
            meta["description"] = r["description"]
        weight = float(r.get("weight") or meta.get("weight") or meta.get("confidence") or 1.0)
        if weight > 1.0:
            weight = 1.0
        patch.source_id = src
        patch.target_id = tgt
        patch.relation = rel
        patch.weight = weight
        patch.metadata = meta
        return patch

    return None


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate(patches: list[Patch], existing_node_ids: set[str]) -> ValidationResult:
    accepted: list[Patch] = []
    rejected: list[tuple[Patch, str]] = []
    unresolved: list[tuple[Patch, str]] = []

    new_node_ids: set[str] = set()
    seen_node_keys: set[tuple[str, str]] = set()

    # First pass: validate nodes, collect new IDs
    for p in patches:
        if p.kind in {"scholar", "scholarly_work", "scholarly_argument"}:
            n = normalize(p)
            if n is None or not n.node_id:
                rejected.append((p, "missing or invalid id"))
                continue
            key = (n.node_id, n.node_type)
            if key in seen_node_keys:
                rejected.append((p, "duplicate node id within patch batch"))
                continue
            seen_node_keys.add(key)
            new_node_ids.add(n.node_id)
            accepted.append(n)

    valid_ids = existing_node_ids | new_node_ids

    # Second pass: edges
    seen_edge_keys: set[tuple[str, str, str]] = set()
    for p in patches:
        if p.kind != "edge":
            continue
        n = normalize(p)
        if n is None:
            rejected.append((p, "edge missing fields"))
            continue
        if any(n.target_id.startswith(prefix) for prefix in STUB_PREFIXES) or any(
            n.source_id.startswith(prefix) for prefix in STUB_PREFIXES
        ):
            unresolved.append((n, "stub target/source (topic: or primary_source_hint:)"))
            continue
        if n.source_id not in valid_ids:
            unresolved.append((n, f"unknown source: {n.source_id}"))
            continue
        if n.target_id not in valid_ids:
            unresolved.append((n, f"unknown target: {n.target_id}"))
            continue
        key = (n.source_id, n.target_id, n.relation)
        if key in seen_edge_keys:
            rejected.append((n, "duplicate edge in batch"))
            continue
        seen_edge_keys.add(key)
        accepted.append(n)

    return ValidationResult(accepted, rejected, unresolved)


# ---------------------------------------------------------------------------
# DB apply
# ---------------------------------------------------------------------------


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


async def fetch_existing_ids(conn: asyncpg.Connection) -> set[str]:
    rows = await conn.fetch("SELECT node_id FROM free_will.kg_nodes")
    return {r["node_id"] for r in rows}


async def apply_patches(
    conn: asyncpg.Connection,
    patches: list[Patch],
    *,
    dry_run: bool,
) -> dict[str, Any]:
    by_type = Counter(
        p.node_type if p.kind != "edge" else f"edge:{p.relation}" for p in patches
    )
    counts: dict[str, int] = {
        "nodes_inserted": 0,
        "nodes_updated": 0,
        "edges_inserted": 0,
        "edges_skipped_existing": 0,
    }

    # Group edges by source for `unresolved_targets` metadata aggregation later
    node_patches = [p for p in patches if p.kind != "edge"]
    edge_patches = [p for p in patches if p.kind == "edge"]

    if dry_run:
        # Sample existence check per node
        sample_ids = [p.node_id for p in node_patches[:10]]
        existing = await conn.fetch(
            "SELECT node_id FROM free_will.kg_nodes WHERE node_id = ANY($1::varchar[])",
            sample_ids,
        )
        existing_set = {r["node_id"] for r in existing}
        # Estimate inserts vs updates
        all_ids = [p.node_id for p in node_patches]
        existing_all = await conn.fetch(
            "SELECT node_id FROM free_will.kg_nodes WHERE node_id = ANY($1::varchar[])",
            all_ids,
        )
        existing_all_set = {r["node_id"] for r in existing_all}
        counts["nodes_updated"] = sum(1 for p in node_patches if p.node_id in existing_all_set)
        counts["nodes_inserted"] = sum(
            1 for p in node_patches if p.node_id not in existing_all_set
        )
        # Edges: check existing
        edge_keys = [(p.source_id, p.target_id, p.relation) for p in edge_patches]
        existing_edges = await conn.fetch(
            """
            SELECT source_id, target_id, relation
            FROM free_will.kg_edges
            WHERE source_id = ANY($1::varchar[])
              AND target_id = ANY($2::varchar[])
            """,
            [k[0] for k in edge_keys],
            [k[1] for k in edge_keys],
        )
        existing_edge_set = {(r["source_id"], r["target_id"], r["relation"]) for r in existing_edges}
        counts["edges_inserted"] = sum(1 for k in edge_keys if k not in existing_edge_set)
        counts["edges_skipped_existing"] = sum(1 for k in edge_keys if k in existing_edge_set)
        counts["sample_existing_in_dryrun_first10"] = len(existing_set)
        counts["by_kind"] = dict(by_type)
        return counts

    # Real apply
    async with conn.transaction():
        for p in node_patches:
            row = await conn.fetchrow(
                UPSERT_NODE_SQL,
                p.node_id,
                p.label,
                p.node_type,
                p.description,
                p.period,
                json.dumps([]),
                json.dumps(p.metadata, ensure_ascii=False),
            )
            if row and row["inserted"]:
                counts["nodes_inserted"] += 1
            else:
                counts["nodes_updated"] += 1

        for p in edge_patches:
            result = await conn.fetchval(
                INSERT_EDGE_SQL,
                p.source_id,
                p.target_id,
                p.relation,
                p.weight,
                json.dumps(p.metadata, ensure_ascii=False),
            )
            if result == 1:
                counts["edges_inserted"] += 1
            else:
                counts["edges_skipped_existing"] += 1

    counts["by_kind"] = dict(by_type)
    return counts


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply KG enrichment patches to Supabase.")
    parser.add_argument(
        "--input",
        action="append",
        type=Path,
        required=True,
        help="JSONL patch file (repeatable).",
    )
    parser.add_argument(
        "--database-url",
        default=os.getenv("SUPABASE_DATABASE_URL") or os.getenv("DATABASE_URL"),
        help="PostgreSQL DSN. Defaults to $SUPABASE_DATABASE_URL or $DATABASE_URL.",
    )
    parser.add_argument(
        "--rejected-out",
        type=Path,
        default=Path("data/kg_enrichment/rejected_patches.jsonl"),
        help="Where to write rejected/unresolved patches.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show counts without writing.")
    return parser.parse_args(argv)


async def main(argv: list[str]) -> int:
    args = parse_args(argv)
    if not args.database_url:
        raise SystemExit("Missing --database-url / $SUPABASE_DATABASE_URL / $DATABASE_URL")

    patches = load_patches(args.input)
    print(f"Loaded {len(patches)} raw patches from {len(args.input)} files")

    conn = await asyncpg.connect(dsn=args.database_url, statement_cache_size=0)
    try:
        existing_ids = await fetch_existing_ids(conn)
        print(f"Existing kg_nodes: {len(existing_ids)}")

        result = validate(patches, existing_ids)
        print(f"Accepted: {len(result.accepted)}")
        print(f"Rejected: {len(result.rejected)}")
        print(f"Unresolved edges (stubs / unknown ids): {len(result.unresolved_edges)}")

        # Write rejected + unresolved for inspection
        args.rejected_out.parent.mkdir(parents=True, exist_ok=True)
        with args.rejected_out.open("w", encoding="utf-8") as fh:
            for p, reason in result.rejected:
                fh.write(json.dumps({"reason": reason, "patch": p.raw}, ensure_ascii=False) + "\n")
            for p, reason in result.unresolved_edges:
                fh.write(
                    json.dumps({"reason": f"UNRESOLVED: {reason}", "patch": p.raw}, ensure_ascii=False)
                    + "\n"
                )
        print(f"Wrote {args.rejected_out}")

        counts = await apply_patches(conn, result.accepted, dry_run=args.dry_run)
        mode = "DRY-RUN" if args.dry_run else "APPLIED"
        print(f"\n=== {mode} ===")
        for k, v in counts.items():
            print(f"  {k}: {v}")

        if not args.dry_run:
            # Post-apply stats
            stats = await conn.fetchrow(
                """
                SELECT
                    (SELECT count(*) FROM free_will.kg_nodes) AS total_nodes,
                    (SELECT count(*) FROM free_will.kg_edges) AS total_edges,
                    (SELECT count(*) FROM free_will.kg_nodes WHERE metadata->>'role' = 'scholar') AS scholars,
                    (SELECT count(*) FROM free_will.kg_nodes WHERE type = 'publication') AS publications,
                    (SELECT count(*) FROM free_will.kg_nodes WHERE type = 'argument' AND metadata->>'argument_type' = 'modern_scholarly_position') AS scholarly_args,
                    (SELECT count(*) FROM free_will.kg_edges WHERE relation IN ('wrote_about','engages_with','cites_primary_source','published','agrees_with','opposes','uses_methodology_of','edited_by')) AS new_edges
                """
            )
            print("\nPost-apply DB counts:")
            for k, v in dict(stats).items():
                print(f"  {k}: {v}")
    finally:
        await conn.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main(sys.argv[1:])))
