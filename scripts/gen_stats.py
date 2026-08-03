#!/usr/bin/env python3
"""Generate truthful corpus/KG statistics from the repo data snapshots.

Counts are computed from the committed JSONL snapshots (``data/kg/*.jsonl``,
``data/corpus/*.jsonl``) so that README/docs claims can always be
regenerated from the actual dataset instead of hand-maintained numbers that
drift (the README shipped "487 works / 69,277 passages" while the dataset
holds 241 work nodes).

Optionally (env-gated), live database counts are added when ``DATABASE_URL``
is set and ``asyncpg`` is importable; without it the DB section is skipped
silently. The script never writes to the database.

Usage:
    python3 scripts/gen_stats.py                # writes data/stats.json + data/stats.md
    python3 scripts/gen_stats.py --check        # exit 1 if data/stats.json is stale
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
KG_NODES = REPO_ROOT / "data" / "kg" / "nodes.jsonl"
KG_EDGES = REPO_ROOT / "data" / "kg" / "edges.jsonl"
CORPUS_PASSAGES = REPO_ROOT / "data" / "corpus" / "passages.jsonl"
CORPUS_CITATIONS = REPO_ROOT / "data" / "corpus" / "citations.jsonl"
CORPUS_MANIFEST = REPO_ROOT / "data" / "corpus" / "manifest.jsonl"
ONTOLOGY_DIR = REPO_ROOT / "knowledge graph" / "ontology"
STATS_JSON = REPO_ROOT / "data" / "stats.json"
STATS_MD = REPO_ROOT / "data" / "stats.md"


def _iter_jsonl(path: Path):
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def kg_stats() -> dict[str, Any]:
    node_types: Counter[str] = Counter()
    for record in _iter_jsonl(KG_NODES):
        node_types[str(record.get("type", "unknown"))] += 1
    edge_relations: Counter[str] = Counter()
    for record in _iter_jsonl(KG_EDGES):
        edge_relations[str(record.get("relation", "unknown"))] += 1
    return {
        "nodes": sum(node_types.values()),
        "edges": sum(edge_relations.values()),
        "works": node_types.get("work", 0),
        "passage_nodes": node_types.get("passage", 0),
        "node_types_in_use": len(node_types),
        "edge_relations_in_use": len(edge_relations),
        "node_type_counts": dict(node_types.most_common()),
        "edge_relation_counts": dict(edge_relations.most_common()),
    }


def corpus_stats() -> dict[str, Any]:
    passages = 0
    works_with_text: set[str] = set()
    for record in _iter_jsonl(CORPUS_PASSAGES):
        passages += 1
        work_id = record.get("work_canonical_id")
        if work_id:
            works_with_text.add(str(work_id))
    citations = sum(1 for _ in _iter_jsonl(CORPUS_CITATIONS))
    manifest_status: Counter[str] = Counter()
    for record in _iter_jsonl(CORPUS_MANIFEST):
        manifest_status[str(record.get("status", "unknown"))] += 1
    return {
        "passages": passages,
        "works_with_text": len(works_with_text),
        "passage_citations": citations,
        "manifest_entries": sum(manifest_status.values()),
        "manifest_status_counts": dict(manifest_status.most_common()),
    }


def ontology_stats() -> dict[str, Any]:
    def _count(path: Path, key: str) -> int | None:
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        types = data.get(key) if isinstance(data, dict) else data
        return len(types) if isinstance(types, (list, dict)) else None

    return {
        "node_types_defined": _count(ONTOLOGY_DIR / "node_types.json", "node_types"),
        "edge_types_defined": _count(ONTOLOGY_DIR / "edge_types.json", "edge_types"),
    }


def db_stats() -> dict[str, Any] | None:
    """Read-only row counts from the live DB. Skipped without DATABASE_URL."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        return None
    try:
        import asyncio

        import asyncpg
    except ImportError:
        print("DATABASE_URL set but asyncpg unavailable — skipping DB stats")
        return None

    async def _fetch() -> dict[str, Any]:
        conn = await asyncpg.connect(database_url)
        try:
            return {
                table: await conn.fetchval(f"SELECT count(*) FROM {table}")  # noqa: S608 — fixed identifiers
                for table in (
                    "ancient_works",
                    "passages",
                    "kg_nodes",
                    "kg_edges",
                    "passage_citations",
                )
            }
        finally:
            await conn.close()

    try:
        return asyncio.run(_fetch())
    except Exception as exc:  # pragma: no cover — connectivity dependent
        print(f"DB stats skipped ({type(exc).__name__}: {exc})")
        return None


def build_stats() -> dict[str, Any]:
    stats: dict[str, Any] = {
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sources": {
            "kg": "data/kg/nodes.jsonl + data/kg/edges.jsonl",
            "corpus": "data/corpus/*.jsonl",
            "ontology": "knowledge graph/ontology/*.json",
        },
        "kg": kg_stats(),
        "corpus": corpus_stats(),
        "ontology": ontology_stats(),
    }
    db = db_stats()
    if db is not None:
        stats["database"] = db
    return stats


def markdown_snippet(stats: dict[str, Any]) -> str:
    kg = stats["kg"]
    corpus = stats["corpus"]
    ontology = stats["ontology"]
    rows = [
        ("Knowledge graph nodes", f"{kg['nodes']:,}"),
        ("Knowledge graph edges", f"{kg['edges']:,}"),
        ("Ancient works (KG)", f"{kg['works']:,}"),
        ("Corpus text passages", f"{corpus['passages']:,}"),
        ("Passage citations", f"{corpus['passage_citations']:,}"),
        (
            "Node types (ontology / in use)",
            f"{ontology['node_types_defined']} / {kg['node_types_in_use']}",
        ),
        (
            "Edge types (ontology / in use)",
            f"{ontology['edge_types_defined']} / {kg['edge_relations_in_use']}",
        ),
    ]
    if "database" in stats:
        rows.extend(
            (f"DB rows: {table}", f"{count:,}")
            for table, count in stats["database"].items()
        )
    lines = [
        f"<!-- generated by scripts/gen_stats.py on {stats['generated_at']} -->",
        "| Metric | Count |",
        "|--------|-------|",
        *(f"| {label} | {value} |" for label, value in rows),
    ]
    return "\n".join(lines) + "\n"


def _stable(stats: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in stats.items() if key != "generated_at"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit 1 when data/stats.json is stale instead of rewriting it",
    )
    args = parser.parse_args()

    stats = build_stats()
    snippet = markdown_snippet(stats)

    if args.check:
        if not STATS_JSON.exists():
            print("data/stats.json missing — run scripts/gen_stats.py")
            return 1
        existing = json.loads(STATS_JSON.read_text(encoding="utf-8"))
        if _stable(existing) != _stable(stats):
            print("data/stats.json is stale — run scripts/gen_stats.py")
            return 1
        print("data/stats.json is up to date")
        return 0

    STATS_JSON.write_text(
        json.dumps(stats, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    STATS_MD.write_text(snippet, encoding="utf-8")
    print(f"wrote {STATS_JSON.relative_to(REPO_ROOT)}")
    print(f"wrote {STATS_MD.relative_to(REPO_ROOT)}")
    print()
    print(snippet)
    return 0


if __name__ == "__main__":
    sys.exit(main())
