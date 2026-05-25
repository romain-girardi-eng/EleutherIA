#!/usr/bin/env python3
"""Ingest genuine De Divinatione (phi053) and De Natura Deorum (phi050) into the corpus.

Two new ancient_works rows are created (idempotent by canonical_id); all fetched
passages are inserted verbatim from the GitHub TEI (idempotent by cts_urn per work).

Dry-run by default; --commit to write.  Snapshot taken before any mutation.

Usage:
    .venv/bin/python -m scripts.ingest_cicero_genuine_2026_05_25 [--commit]
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import asyncpg

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_DIR = ROOT / "data" / "corpus" / "fix_snapshots" / "ingest_cicero_genuine_2026_05_25"

DB_URL_KEY = "DATABASE_URL"

WORKS = [
    {
        "canonical_id": "urn_cts_latinlit_phi0474_phi053_lat",
        "title": "De Divinatione",
        "title_original": "De Divinatione",
        "cts_urn": "urn:cts:latinLit:phi0474.phi053.perseus-lat1",
        "opening": "Vetus opinio est",
        "expected_min": 280,
    },
    {
        "canonical_id": "urn_cts_latinlit_phi0474_phi050_lat",
        "title": "De Natura Deorum",
        "title_original": "De Natura Deorum",
        "cts_urn": "urn:cts:latinLit:phi0474.phi050.perseus-lat1",
        "opening": "Cum multae res in philosophia",
        "expected_min": 380,
    },
]


def _db_url() -> str:
    for line in (ROOT / ".env").open(encoding="utf-8"):
        if line.startswith(f"{DB_URL_KEY}="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit(f"{DB_URL_KEY} not found in .env")


def _pg_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return "postgres://" + url[len("postgresql://"):]
    return url


async def _upsert_work(conn: asyncpg.Connection, meta: dict[str, Any], *, commit: bool) -> tuple[str, bool]:
    """Insert work if not present. Returns (work_id, was_created)."""
    existing = await conn.fetchrow(
        "SELECT work_id FROM free_will.ancient_works WHERE canonical_id = $1",
        meta["canonical_id"],
    )
    if existing:
        return str(existing["work_id"]), False

    if not commit:
        return "<new-if-committed>", True

    row = await conn.fetchrow(
        """
        INSERT INTO free_will.ancient_works
            (canonical_id, title, title_original, author, language, period, cts_urn, source, created_at, updated_at)
        VALUES ($1, $2, $3, 'Cicero', 'lat', 'Roman Republican', $4,
                'Perseus Digital Library (GitHub TEI)', $5, $5)
        RETURNING work_id
        """,
        meta["canonical_id"],
        meta["title"],
        meta["title_original"],
        meta["cts_urn"],
        datetime.now(UTC),
    )
    return str(row["work_id"]), True


async def _existing_urns(conn: asyncpg.Connection, work_id: str) -> set[str]:
    rows = await conn.fetch(
        "SELECT cts_urn FROM free_will.passages WHERE work_id = $1",
        work_id,
    )
    return {r["cts_urn"] for r in rows}


async def _insert_passages(conn: asyncpg.Connection, work_id: str, passages: list[dict[str, Any]], start_seq: int) -> int:
    rows = [
        (
            work_id,
            p["cts_urn"].split(":")[-1],  # canonical_ref = ref after last ':'
            p["cts_urn"],
            start_seq + i,
            p["text_content"],
            "original",
            len(p["text_content"]),
            len(p["text_content"].split()),
        )
        for i, p in enumerate(passages)
    ]
    async with conn.transaction():
        await conn.executemany(
            """
            INSERT INTO free_will.passages
                (work_id, canonical_ref, cts_urn, sequence_number,
                 text_content, passage_role, char_length, word_count)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            rows,
        )
    return len(rows)


async def main(commit: bool) -> int:
    import asyncpg  # noqa: I001, PLC0415
    import scripts.corpus_github_fetch as _fetch_mod  # noqa: PLC0415
    fetch_work_passages = _fetch_mod.fetch_work_passages

    raw_url = _db_url()
    pg_url = _pg_url(raw_url)

    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

    conn: asyncpg.Connection = await asyncio.wait_for(asyncpg.connect(pg_url), timeout=30)
    try:
        for meta in WORKS:
            print(f"\n{'='*60}")
            print(f"Work: {meta['title']} ({meta['canonical_id']})")
            print(f"URN:  {meta['cts_urn']}")
            print(f"Mode: {'COMMIT' if commit else 'DRY-RUN'}")

            # 1. Fetch passages from GitHub
            print("Fetching TEI from GitHub...")
            work_cts_urn = str(meta["cts_urn"])
            passages = fetch_work_passages(work_cts_urn)
            print(f"Fetched: {len(passages)} passages")

            if not passages:
                print("ERROR: 0 passages fetched — aborting this work.")
                return 1

            # Verify count and opening line
            expected_min = int(str(meta["expected_min"]))
            if len(passages) < expected_min:
                print(
                    f"ERROR: fetched {len(passages)} < expected_min {expected_min} "
                    "— refusing to insert."
                )
                return 1

            opening = passages[0]["text_content"]
            if not opening.startswith(str(meta["opening"])):
                print(
                    f"ERROR: opening mismatch.\n"
                    f"  Expected starts with: {meta['opening']!r}\n"
                    f"  Got:                  {opening[:60]!r}"
                )
                return 1
            print(f"Opening confirmed: {opening[:80]!r}")

            # 2. Snapshot state before mutation
            snap = {
                "canonical_id": meta["canonical_id"],
                "cts_urn": meta["cts_urn"],
                "fetched_count": len(passages),
                "first_cts_urn": passages[0]["cts_urn"],
                "last_cts_urn": passages[-1]["cts_urn"],
                "timestamp": datetime.now(UTC).isoformat(),
            }
            snap_file = SNAPSHOT_DIR / f"{meta['canonical_id']}_pre.json"
            snap_file.write_text(json.dumps(snap, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"Snapshot: {snap_file}")

            # 3. Upsert work row
            work_id, was_created = await _upsert_work(conn, meta, commit=commit)
            print(
                f"Work row: {'created' if was_created else 'reused'} "
                f"(work_id={work_id})"
            )

            # 4. Skip passages already present (idempotent)
            if commit and work_id != "<new-if-committed>":
                existing = await _existing_urns(conn, work_id)
            else:
                existing = set()

            new_passages = [p for p in passages if p["cts_urn"] not in existing]
            print(f"New passages to insert: {len(new_passages)} (already present: {len(existing)})")

            if not commit:
                print("[DRY-RUN] Pass --commit to write to DB.")
                continue

            if not new_passages:
                print("Nothing to insert (all passages already present).")
                continue

            # Start sequence after any existing passages
            if existing:
                max_seq_row = await conn.fetchrow(
                    "SELECT max(sequence_number) AS m FROM free_will.passages WHERE work_id = $1",
                    work_id,
                )
                start_seq = (max_seq_row["m"] or 0) + 1
            else:
                start_seq = 1

            inserted = await _insert_passages(conn, work_id, new_passages, start_seq)
            print(f"Inserted: {inserted} passages")

            # Post-insert verification
            count_after = await conn.fetchval(
                "SELECT count(*) FROM free_will.passages WHERE work_id = $1",
                work_id,
            )
            first_passage = await conn.fetchrow(
                "SELECT cts_urn, text_content FROM free_will.passages WHERE work_id = $1 ORDER BY sequence_number LIMIT 1",
                work_id,
            )
            print(f"DB now has: {count_after} passages for this work")
            if first_passage:
                print(f"First passage in DB: {first_passage['cts_urn']}")
                print(f"  text starts: {first_passage['text_content'][:80]!r}")

    finally:
        await conn.close()

    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--commit", action="store_true", help="Write changes to DB (default: dry-run)")
    args = ap.parse_args()
    sys.exit(asyncio.run(main(args.commit)))
