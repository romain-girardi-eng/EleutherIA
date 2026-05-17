#!/usr/bin/env python3
"""Repair small structural metadata issues surfaced by scholarly backlog.

The scholarly backlog treats every ``passage_role="translation"`` node as a
standalone translation node and expects ``metadata.source_passage_id``. Several
Origen passage anchors are not standalone translations: they carry original
Greek and/or Latin text fields plus French/English helper text. Mark those as
``original`` source anchors instead.

The Eusebius Praeparatio book-level placeholders are structural stubs rather
than source-text passages. Mark them as ``paraphrase`` so the audit does not
confuse them with missing original passage text.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import asyncpg

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from database.scripts.philological_audit import _common


NODES_PATH = REPO_ROOT / "data" / "kg" / "nodes.jsonl"
CREATED_BY = "repair_scholarly_backlog_metadata_2026_05_17"

EUSEBIUS_BOOK_STUBS = {
    f"passage_eusebius_praep_ev_book_{n:02d}" for n in range(1, 16)
}


def load_jsonl(path: Path) -> list[tuple[str, dict[str, Any] | None]]:
    with path.open("r", encoding="utf-8") as f:
        return [(line, json.loads(line) if line.strip() else None) for line in f]


def dump_jsonl(path: Path, rows: list[tuple[str, dict[str, Any] | None]], changed_ids: set[str]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for raw, row in rows:
            if row is None or node_id(row) not in changed_ids:
                f.write(raw)
            else:
                f.write(json.dumps(row, ensure_ascii=False))
                f.write("\n")
    tmp.replace(path)


def metadata(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def node_id(node: dict[str, Any]) -> str:
    return str(node.get("node_id") or node.get("id") or "")


def is_origen_source_anchor(node: dict[str, Any], md: dict[str, Any]) -> bool:
    if md.get("passage_role") != "translation":
        return False
    nid = node_id(node)
    if not nid.startswith("passage_origen_"):
        return False
    return bool(node.get("description_grc") or node.get("description_la"))


def repair_node(node: dict[str, Any], now: str) -> bool:
    nid = node_id(node)
    md = metadata(node.get("metadata"))
    changed = False

    if nid in EUSEBIUS_BOOK_STUBS:
        if md.get("passage_role") != "paraphrase":
            md["passage_role"] = "paraphrase"
            changed = True
        for key, value in {
            "author": "Eusebius of Caesarea",
            "work_title": "Praeparatio Evangelica",
            "language": "grc",
            "semantic_status": "structural_stub",
            "text_status": "stub_needs_ingestion",
            "repair_note": "Book-level structural placeholder, not an ingested original-language passage.",
        }.items():
            if md.get(key) != value:
                md[key] = value
                changed = True

    elif is_origen_source_anchor(node, md):
        md["passage_role"] = "original"
        md["translation_note"] = (
            "This is a primary-source anchor with original Greek/Latin text fields "
            "and helper translations/summaries, not a standalone translation node."
        )
        if node.get("description_grc") and not md.get("language"):
            md["language"] = "grc"
        changed = True

    if changed:
        md["metadata_repaired_by"] = CREATED_BY
        md["metadata_repaired_at"] = now
        node["metadata"] = json.dumps(md, ensure_ascii=False, sort_keys=True)
        if "updated_at" in node:
            node["updated_at"] = now
    return changed


async def apply_db(db_url: str, changed_nodes: list[dict[str, Any]]) -> int:
    if not changed_nodes:
        return 0
    conn = await asyncpg.connect(db_url, statement_cache_size=0)
    try:
        async with conn.transaction():
            count = 0
            for node in changed_nodes:
                await conn.execute(
                    """
                    UPDATE free_will.kg_nodes
                    SET metadata = metadata || $2::jsonb,
                        updated_at = now()
                    WHERE node_id = $1
                    """,
                    node_id(node),
                    json.dumps(metadata(node.get("metadata")), ensure_ascii=False),
                )
                count += 1
    finally:
        await conn.close()
    return count


async def run(args: argparse.Namespace) -> int:
    rows = load_jsonl(args.nodes)
    nodes = [node for _, node in rows if node is not None]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f+00:00")
    changed_nodes = [node for node in nodes if repair_node(node, now)]
    changed_ids = {node_id(node) for node in changed_nodes}

    print(f"Changed nodes: {len(changed_nodes)}")
    for node in changed_nodes[:20]:
        print(f"  {node_id(node)}")
    if len(changed_nodes) > 20:
        print(f"  ... {len(changed_nodes) - 20} more")

    if not args.apply and not args.apply_db:
        print("DRY RUN - no writes. Use --apply and/or --apply-db.")
        return 0

    if args.apply:
        dump_jsonl(args.nodes, rows, changed_ids)
        print(f"Wrote {args.nodes}")

    if args.apply_db:
        db_url = args.db_url or os.getenv("SUPABASE_DATABASE_URL") or os.getenv("DATABASE_URL") or _common.dsn()
        count = await apply_db(db_url, changed_nodes)
        print(f"Updated DB nodes: {count}")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nodes", type=Path, default=NODES_PATH)
    parser.add_argument("--db-url", help="PostgreSQL DSN. Defaults to env, then repo audit DSN.")
    parser.add_argument("--apply", action="store_true", help="Rewrite local nodes JSONL.")
    parser.add_argument("--apply-db", action="store_true", help="Patch live free_will.kg_nodes metadata.")
    return asyncio.run(run(parser.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
