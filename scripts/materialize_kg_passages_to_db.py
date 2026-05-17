#!/usr/bin/env python3
"""Materialize KG passage nodes into the live Postgres corpus tables.

This is the incremental counterpart to ``database/scripts/bootstrap_supabase.py``.
It reuses the bootstrap snapshot mapper, but writes only:

- ``free_will.ancient_works`` rows that do not already exist
- ``free_will.passages`` rows that do not already exist
- missing ``free_will.passage_citations``

It intentionally does not upsert ``kg_nodes`` or ``kg_edges``. That keeps this
safe for production databases where the KG layer may have live-only metadata or
edges, while still making checked-in passage nodes queryable through the corpus
tables and citation joins.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import asyncpg

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from database.scripts.bootstrap_supabase import (
    ImportPayload,
    build_import_payload,
    load_snapshot,
)
from database.scripts.philological_audit._common import dsn as repo_default_dsn


@dataclass(frozen=True)
class PreparedImport:
    works: list[tuple[Any, ...]]
    passages: list[tuple[Any, ...]]
    citations: list[tuple[Any, ...]]
    work_id_remaps: int
    affected_work_ids: set[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--snapshot-dir",
        type=Path,
        default=REPO_ROOT / "data" / "kg",
        help="Directory containing nodes.jsonl and edges.jsonl.",
    )
    parser.add_argument(
        "--database-url",
        default=(
            os.getenv("SUPABASE_DATABASE_URL")
            or os.getenv("DATABASE_URL")
            or repo_default_dsn()
        ),
        help="PostgreSQL DSN. Defaults to SUPABASE_DATABASE_URL, DATABASE_URL, then the repo's configured audit DSN.",
    )
    parser.add_argument(
        "--prefix",
        action="append",
        default=[],
        help="Optional passage node_id prefix to materialize. May be repeated. Default: all passage nodes.",
    )
    parser.add_argument("--batch-size", type=int, default=1000)
    parser.add_argument("--apply", action="store_true", help="Write changes. Default is dry-run.")
    return parser.parse_args()


def filter_payload(payload: ImportPayload, prefixes: list[str]) -> ImportPayload:
    if not prefixes:
        return payload

    passage_id_to_node: dict[str, str] = {}
    for passage_id, kg_node_id, citation_type, *_rest in payload.passage_citations:
        if citation_type == "snapshot_passage_node":
            passage_id_to_node[str(passage_id)] = kg_node_id

    keep_passage_ids = {
        passage_id
        for passage_id, node_id in passage_id_to_node.items()
        if any(node_id.startswith(prefix) for prefix in prefixes)
    }
    keep_work_ids = {
        str(row[1]) for row in payload.passages if str(row[0]) in keep_passage_ids
    }

    return ImportPayload(
        kg_nodes=[],
        kg_edges=[],
        ancient_works=[
            row for row in payload.ancient_works if str(row[0]) in keep_work_ids
        ],
        passages=[row for row in payload.passages if str(row[0]) in keep_passage_ids],
        passage_citations=[
            row
            for row in payload.passage_citations
            if str(row[0]) in keep_passage_ids
        ],
    )


async def _fetch_existing_passage_ids(
    conn: asyncpg.Connection,
    passage_ids: list[str],
    batch_size: int,
) -> set[str]:
    existing: set[str] = set()
    for offset in range(0, len(passage_ids), batch_size):
        batch = passage_ids[offset : offset + batch_size]
        rows = await conn.fetch(
            "SELECT passage_id::text FROM free_will.passages WHERE passage_id = ANY($1::uuid[])",
            batch,
        )
        existing.update(row["passage_id"] for row in rows)
    return existing


async def _fetch_existing_citation_keys(
    conn: asyncpg.Connection,
    passage_ids: list[str],
    batch_size: int,
) -> set[tuple[str, str, str]]:
    existing: set[tuple[str, str, str]] = set()
    for offset in range(0, len(passage_ids), batch_size):
        batch = passage_ids[offset : offset + batch_size]
        rows = await conn.fetch(
            """
            SELECT passage_id::text, kg_node_id, COALESCE(citation_type, '') AS citation_type
            FROM free_will.passage_citations
            WHERE passage_id = ANY($1::uuid[])
            """,
            batch,
        )
        existing.update(
            (row["passage_id"], row["kg_node_id"], row["citation_type"])
            for row in rows
        )
    return existing


async def prepare_import(
    conn: asyncpg.Connection,
    payload: ImportPayload,
    batch_size: int,
) -> PreparedImport:
    existing_works = await conn.fetch(
        "SELECT work_id::text, canonical_id FROM free_will.ancient_works"
    )
    existing_work_ids = {row["work_id"] for row in existing_works}
    existing_work_id_by_canonical = {
        row["canonical_id"]: row["work_id"] for row in existing_works
    }

    work_id_map: dict[str, str] = {}
    new_works: list[tuple[Any, ...]] = []
    remaps = 0

    for row in payload.ancient_works:
        work_id = str(row[0])
        canonical_id = row[2]
        if work_id in existing_work_ids:
            work_id_map[work_id] = work_id
        elif canonical_id in existing_work_id_by_canonical:
            work_id_map[work_id] = existing_work_id_by_canonical[canonical_id]
            remaps += 1
        else:
            work_id_map[work_id] = work_id
            new_works.append(row)

    passage_ids = [str(row[0]) for row in payload.passages]
    existing_passage_ids = await _fetch_existing_passage_ids(
        conn, passage_ids, batch_size
    )

    new_passages: list[tuple[Any, ...]] = []
    affected_work_ids: set[str] = set()
    for row in payload.passages:
        passage_id = str(row[0])
        if passage_id in existing_passage_ids:
            continue
        old_work_id = str(row[1])
        new_work_id = work_id_map.get(old_work_id, old_work_id)
        adjusted = (
            row[0],
            uuid.UUID(new_work_id),
            row[2],
            row[3],
            row[4],
            row[5],
            row[6],
            row[7],
            row[8],
            row[9],
            row[10],
            row[11],
        )
        new_passages.append(adjusted)
        affected_work_ids.add(new_work_id)

    existing_citations = await _fetch_existing_citation_keys(
        conn, passage_ids, batch_size
    )
    new_citations = [
        row
        for row in payload.passage_citations
        if (str(row[0]), row[1], row[2] or "") not in existing_citations
    ]

    for row in new_works:
        affected_work_ids.add(str(row[0]))

    return PreparedImport(
        works=new_works,
        passages=new_passages,
        citations=new_citations,
        work_id_remaps=remaps,
        affected_work_ids=affected_work_ids,
    )


async def _executemany(
    conn: asyncpg.Connection,
    sql: str,
    rows: list[tuple[Any, ...]],
    batch_size: int,
    label: str,
) -> None:
    if not rows:
        print(f"{label}: 0")
        return
    for offset in range(0, len(rows), batch_size):
        await conn.executemany(sql, rows[offset : offset + batch_size])
    print(f"{label}: {len(rows)}")


async def apply_import(
    conn: asyncpg.Connection,
    prepared: PreparedImport,
    batch_size: int,
) -> None:
    async with conn.transaction():
        await _executemany(
            conn,
            """
            INSERT INTO free_will.ancient_works (
                work_id, kg_work_id, canonical_id, title, author, language,
                period, school, source, metadata
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'kg_snapshot', $9::jsonb)
            ON CONFLICT (work_id) DO NOTHING
            """,
            prepared.works,
            batch_size,
            "ancient_works inserted",
        )
        await _executemany(
            conn,
            """
            INSERT INTO free_will.passages (
                passage_id, work_id, canonical_ref, cts_urn, book, chapter,
                section, sequence_number, text_content, char_length,
                word_count, citation_hierarchy
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12::jsonb)
            ON CONFLICT (passage_id) DO NOTHING
            """,
            prepared.passages,
            batch_size,
            "passages inserted",
        )
        await _executemany(
            conn,
            """
            INSERT INTO free_will.passage_citations (
                passage_id, kg_node_id, citation_type, confidence, notes
            )
            SELECT $1, $2, $3, $4, $5
            WHERE NOT EXISTS (
                SELECT 1
                FROM free_will.passage_citations pc
                WHERE pc.passage_id = $1
                  AND pc.kg_node_id = $2
                  AND COALESCE(pc.citation_type, '') = COALESCE($3, '')
            )
            """,
            prepared.citations,
            batch_size,
            "passage_citations inserted",
        )

        if prepared.affected_work_ids:
            await conn.execute(
                """
                UPDATE free_will.ancient_works aw
                SET
                    total_divisions = stats.total_passages,
                    total_words = stats.total_words,
                    total_chars = stats.total_chars,
                    updated_at = now()
                FROM (
                    SELECT
                        work_id,
                        COUNT(*)::INTEGER AS total_passages,
                        COALESCE(SUM(word_count), 0)::INTEGER AS total_words,
                        COALESCE(SUM(char_length), 0)::INTEGER AS total_chars
                    FROM free_will.passages
                    WHERE work_id = ANY($1::uuid[])
                    GROUP BY work_id
                ) stats
                WHERE aw.work_id = stats.work_id
                """,
                list(prepared.affected_work_ids),
            )


async def main() -> int:
    args = parse_args()
    payload = filter_payload(
        build_import_payload(load_snapshot(args.snapshot_dir)),
        args.prefix,
    )
    print("Snapshot corpus payload")
    print(f"  ancient_works: {len(payload.ancient_works)}")
    print(f"  passages: {len(payload.passages)}")
    print(f"  passage_citations: {len(payload.passage_citations)}")
    if args.prefix:
        print(f"  prefixes: {', '.join(args.prefix)}")

    conn = await asyncpg.connect(
        dsn=args.database_url,
        statement_cache_size=0,
        timeout=30,
        command_timeout=300,
    )
    try:
        prepared = await prepare_import(conn, payload, max(1, args.batch_size))
        print("Pending DB changes")
        print(f"  ancient_works: {len(prepared.works)}")
        print(f"  passages: {len(prepared.passages)}")
        print(f"  passage_citations: {len(prepared.citations)}")
        print(f"  work_id_remaps_by_canonical_id: {prepared.work_id_remaps}")

        if not args.apply:
            print("DRY RUN - no DB writes. Re-run with --apply to commit.")
            return 0

        await apply_import(conn, prepared, max(1, args.batch_size))
        stats = await conn.fetchrow(
            """
            SELECT
                (SELECT COUNT(*) FROM free_will.ancient_works) AS ancient_works,
                (SELECT COUNT(*) FROM free_will.passages) AS passages,
                (SELECT COUNT(*) FROM free_will.passage_citations) AS passage_citations
            """
        )
        print("Post-apply corpus counts")
        for key, value in dict(stats).items():
            print(f"  {key}: {value}")
    finally:
        await conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
