#!/usr/bin/env python3
"""Build and persist hierarchical tree indices for all ancient works.

This script pre-computes the work tree indices used by the
TreeReasoningRetrieve FSM node.  It queries the database for all ancient
works and their passages, builds a hierarchical section tree for each work
using the canonical reference structure (book.chapter.section), and stores
the result in the ``work_tree_indices`` table.

Usage
-----
    python scripts/build_work_tree_indices.py [--schema free_will] [--dry-run]

Environment
-----------
    DATABASE_URL    PostgreSQL connection string (required)

The script is idempotent: existing rows are updated via INSERT … ON CONFLICT.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import re
import sys
from collections import defaultdict
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tree building helpers
# ---------------------------------------------------------------------------


def _parse_ref(canonical_ref: str) -> tuple[str, str, str]:
    """Extract (book, chapter, section) from a canonical ref string.

    Handles formats like:
    - "1.2.3"  → book="1", chapter="2", section="3"
    - "1.2"    → book="1", chapter="2", section=""
    - "Frag. 3" → book="Frag", chapter="3", section=""
    """
    parts = re.split(r"[.\s]+", canonical_ref.strip(), maxsplit=2)
    book = parts[0] if len(parts) > 0 else ""
    chapter = parts[1] if len(parts) > 1 else ""
    section = parts[2] if len(parts) > 2 else ""
    return book, chapter, section


def build_tree_for_work(
    work: dict[str, Any],
    passages: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build a hierarchical tree dict from work metadata and its passages.

    Returns a dict matching the TreeNode schema:
    {
        "node_id": str,
        "title": str,
        "start_passage": int,
        "end_passage": int,
        "summary": str,
        "nodes": [...]
    }
    """
    if not passages:
        return {
            "node_id": f"work_{work['work_id']}",
            "title": work["title"],
            "start_passage": 0,
            "end_passage": 0,
            "summary": f"{work.get('author', 'Unknown')}: {work['title']}",
            "nodes": [],
        }

    # Sort passages by sequence_number for consistent ordering
    passages = sorted(passages, key=lambda p: p["sequence_number"])
    first_seq = passages[0]["sequence_number"]
    last_seq = passages[-1]["sequence_number"]

    # Group by book
    by_book: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for p in passages:
        book, _, _ = _parse_ref(p.get("canonical_ref", ""))
        by_book[book if book else "main"].append(p)

    book_nodes: list[dict[str, Any]] = []
    for book_label, book_passages in sorted(by_book.items()):
        b_first = book_passages[0]["sequence_number"]
        b_last = book_passages[-1]["sequence_number"]

        # Group by chapter within book
        by_chapter: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for p in book_passages:
            _, chapter, _ = _parse_ref(p.get("canonical_ref", ""))
            by_chapter[chapter if chapter else "main"].append(p)

        chapter_nodes: list[dict[str, Any]] = []
        for ch_label, ch_passages in sorted(by_chapter.items()):
            c_first = ch_passages[0]["sequence_number"]
            c_last = ch_passages[-1]["sequence_number"]
            chapter_nodes.append({
                "node_id": f"book_{book_label}_ch_{ch_label}",
                "title": f"Book {book_label}, Chapter {ch_label}" if ch_label != "main" else f"Book {book_label}",
                "start_passage": c_first,
                "end_passage": c_last,
                "summary": f"{len(ch_passages)} passages",
                "nodes": [],
            })

        book_nodes.append({
            "node_id": f"book_{book_label}",
            "title": f"Book {book_label}" if book_label != "main" else work["title"],
            "start_passage": b_first,
            "end_passage": b_last,
            "summary": f"{len(book_passages)} passages across {len(by_chapter)} chapters",
            "nodes": chapter_nodes,
        })

    return {
        "node_id": f"work_{work['work_id']}",
        "title": work["title"],
        "start_passage": first_seq,
        "end_passage": last_seq,
        "summary": (
            f"{work.get('author', 'Unknown')}: {work['title']}. "
            f"{len(passages)} passages, {len(by_book)} book(s)."
        ),
        "nodes": book_nodes,
    }


# ---------------------------------------------------------------------------
# Database interaction
# ---------------------------------------------------------------------------


async def _fetch_works(conn: Any, schema: str) -> list[dict[str, Any]]:
    rows = await conn.fetch(f"""
        SELECT work_id, title, author, period
        FROM {schema}.ancient_works
        ORDER BY author, title
    """)
    return [dict(r) for r in rows]


async def _fetch_passages_for_work(
    conn: Any,
    schema: str,
    work_id: Any,
) -> list[dict[str, Any]]:
    rows = await conn.fetch(f"""
        SELECT passage_id, canonical_ref, sequence_number
        FROM {schema}.passages
        WHERE work_id = $1
        ORDER BY sequence_number
    """, work_id)
    return [dict(r) for r in rows]


async def _upsert_index(
    conn: Any,
    schema: str,
    work: dict[str, Any],
    work_index: dict[str, Any],
    total_passages: int,
    dry_run: bool,
) -> None:
    if dry_run:
        logger.info(
            "[DRY RUN] Would upsert tree index for %s (%s) — %d passages",
            work["title"], work.get("author", "?"), total_passages,
        )
        return

    await conn.execute(f"""
        INSERT INTO {schema}.work_tree_indices
            (work_id, title, author, period, total_passages, tree_json)
        VALUES ($1, $2, $3, $4, $5, $6::jsonb)
        ON CONFLICT (work_id) DO UPDATE SET
            title          = EXCLUDED.title,
            author         = EXCLUDED.author,
            period         = EXCLUDED.period,
            total_passages = EXCLUDED.total_passages,
            tree_json      = EXCLUDED.tree_json,
            updated_at     = now()
    """,
        str(work["work_id"]),
        work["title"],
        work.get("author", "Unknown"),
        work.get("period"),
        total_passages,
        json.dumps(work_index, ensure_ascii=False),
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def main(schema: str, dry_run: bool) -> None:
    import asyncpg

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL environment variable is required")
        sys.exit(1)

    logger.info("Connecting to database…")
    conn = await asyncpg.connect(database_url)

    try:
        works = await _fetch_works(conn, schema)
        logger.info("Found %d works to index", len(works))

        success = 0
        skipped = 0
        for work in works:
            passages = await _fetch_passages_for_work(conn, schema, work["work_id"])
            if not passages:
                logger.debug("Skipping %s — no passages", work["title"])
                skipped += 1
                continue

            tree = build_tree_for_work(work, passages)
            # Store WorkTreeIndex format for TreeIndexService compatibility
            work_index = {
                "work_id": str(work["work_id"]),
                "title": work["title"],
                "author": work.get("author", "Unknown"),
                "period": work.get("period"),
                "total_passages": len(passages),
                "nodes": tree["nodes"],
            }
            await _upsert_index(conn, schema, work, work_index, len(passages), dry_run)
            success += 1
        logger.info(
            "Indexed %s (%s) — %d passages, %d books",
            work["title"],
            work.get("author", "?"),
            len(passages),
            len(work_index.get("nodes", [])),
        )

        logger.info(
            "Done. Indexed=%d skipped=%d dry_run=%s",
            success, skipped, dry_run,
        )
    finally:
        await conn.close()


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--schema",
        default="free_will",
        help="PostgreSQL schema name (default: free_will)",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done without writing to DB",
    )
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    asyncio.run(main(schema=args.schema, dry_run=args.dry_run))
