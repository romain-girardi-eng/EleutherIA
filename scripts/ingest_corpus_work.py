"""Manifest-driven runner that ingests ONE Scaife work into free_will.passages.

Dry-run by default; use --commit to write.

Usage:
    python -m scripts.ingest_corpus_work --canonical-id <id> [--commit] [--db-url <url>]
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
import time
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

# Reuse helpers from the existing Scaife fetcher (importable module-level functions):
#   get_valid_reff   — discover all leaf URNs for a work-level URN
#   get_passage      — fetch + strip TEI → plain text for one URN
#   RATE_LIMIT_SECONDS — shared courtesy delay between requests
from database.scripts.fetch_scaife_work import (
    RATE_LIMIT_SECONDS,
    get_passage,
    get_valid_reff,
)
from scripts.corpus_ingest_merge import passages_to_insert
from scripts.corpus_lib import read_jsonl

# ---------------------------------------------------------------------------

MANIFEST_PATH = Path(__file__).parent.parent / "data" / "corpus" / "manifest.jsonl"
SCHEMA = "free_will"


def _load_db_url(override: str | None) -> str:
    if override:
        return override
    load_dotenv(Path(__file__).parent.parent / ".env")
    url = os.getenv("DATABASE_URL")
    if not url:
        sys.exit("ERROR: DATABASE_URL not found in environment or .env")
    return url


def _pg_url(url: str) -> str:
    """Convert postgresql:// to postgres:// for asyncpg if needed."""
    if url.startswith("postgresql://"):
        return "postgres://" + url[len("postgresql://"):]
    return url


async def _load_existing(conn: asyncpg.Connection, work_id: str) -> list[dict]:
    rows = await conn.fetch(
        f"SELECT cts_urn, sequence_number FROM {SCHEMA}.passages WHERE work_id = $1",
        work_id,
    )
    return [dict(r) for r in rows]


async def _resolve_work_id(conn: asyncpg.Connection, canonical_id: str) -> str | None:
    row = await conn.fetchrow(
        f"SELECT work_id FROM {SCHEMA}.ancient_works WHERE canonical_id = $1",
        canonical_id,
    )
    return str(row["work_id"]) if row else None


async def _insert_passages(
    conn: asyncpg.Connection,
    work_id: str,
    rows: list[dict],
) -> int:
    async with conn.transaction():
        await conn.executemany(
            f"""
            INSERT INTO {SCHEMA}.passages
                (work_id, canonical_ref, cts_urn, sequence_number,
                 text_content, passage_role, char_length, word_count)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            [
                (
                    work_id,
                    r["canonical_ref"],
                    r["cts_urn"],
                    r["sequence_number"],
                    r["text_content"],
                    "original",
                    len(r["text_content"]),
                    len(r["text_content"].split()),
                )
                for r in rows
            ],
        )
    return len(rows)


def _fetch_full_work(work_urn: str) -> list[dict]:
    """Discover refs then fetch each passage; return list of {cts_urn, text_content}."""
    print(f"  Discovering refs for: {work_urn}")
    urns = get_valid_reff(work_urn, level=1)

    if not urns:
        # Try deeper levels before giving up
        for lvl in (2, 3):
            urns = get_valid_reff(work_urn, level=lvl)
            if urns:
                print(f"  Found {len(urns)} refs at level {lvl}")
                break

    print(f"  Total refs to fetch: {len(urns)}")

    passages: list[dict] = []
    errors = 0
    for i, urn in enumerate(urns):
        try:
            text = get_passage(urn)
        except Exception as exc:
            print(f"  WARN: failed to fetch {urn}: {exc}")
            errors += 1
            continue

        text = text.strip()
        if text:
            passages.append({"cts_urn": urn, "text_content": text})

        if i < len(urns) - 1:
            time.sleep(RATE_LIMIT_SECONDS)

    if errors:
        print(f"  Fetch errors: {errors}/{len(urns)}")

    return passages


async def run(canonical_id: str, *, commit: bool, db_url: str) -> None:
    # 1. Load manifest and find work entry
    manifest = read_jsonl(MANIFEST_PATH)
    entry = next((r for r in manifest if r.get("canonical_id") == canonical_id), None)
    if entry is None:
        sys.exit(f"ERROR: canonical_id '{canonical_id}' not found in manifest")

    ingest_class = entry.get("ingest_class", "")
    if ingest_class != "scaife":
        sys.exit(
            f"BLOCKED: ingest_class is '{ingest_class}' (not 'scaife') "
            f"for '{canonical_id}'. Only Scaife works are handled by this runner."
        )

    work_urn = entry.get("cts_urn", "")
    if not work_urn:
        sys.exit(f"ERROR: no cts_urn in manifest for '{canonical_id}'")

    print(f"Work:      {entry.get('title', canonical_id)}")
    print(f"Author:    {entry.get('author', '')}")
    print(f"URN:       {work_urn}")
    print(f"Mode:      {'COMMIT' if commit else 'DRY-RUN'}")
    print()

    # 2. Connect to DB
    conn: asyncpg.Connection = await asyncpg.connect(_pg_url(db_url))
    try:
        # 3. Resolve work_id
        work_id = await _resolve_work_id(conn, canonical_id)
        if work_id is None:
            sys.exit(f"BLOCKED: canonical_id '{canonical_id}' not found in free_will.ancient_works")

        # 4. Load existing passages
        existing = await _load_existing(conn, work_id)
        max_seq = max((p["sequence_number"] for p in existing), default=0)

        # 5. Fetch full work from Scaife
        print("Fetching from Scaife...")
        fetched = _fetch_full_work(work_urn)

        # 6. Compute new passages
        new = passages_to_insert(existing, fetched, canonical_id, start_seq=max_seq + 1)

        # 7. Integrity report
        print()
        print(f"existing={len(existing)} fetched={len(fetched)} new={len(new)}")
        print(f"URN: {work_urn}")

        if fetched:
            sample = fetched[0]["text_content"][:80]
            print(f"Sample: {sample!r}")
        else:
            print("WARNING: fetched=0 — no passages returned from Scaife.")
            print("  Check that the work URN exists and the CTS API is reachable.")
            print("  No rows will be inserted.")
            return

        # 8. Insert (if --commit and new>0)
        if commit:
            if new:
                inserted = await _insert_passages(conn, work_id, new)
                print(f"inserted {inserted}")
            else:
                print("Nothing to insert (already up to date).")
        else:
            print("(dry-run — use --commit to write)")

    finally:
        await conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest one Scaife work from the corpus manifest")
    parser.add_argument("--canonical-id", required=True, help="canonical_id from manifest.jsonl")
    parser.add_argument("--commit", action="store_true", help="Write to DB (default: dry-run)")
    parser.add_argument("--db-url", default=None, help="Override DATABASE_URL")
    args = parser.parse_args()

    db_url = _load_db_url(args.db_url)
    asyncio.run(run(args.canonical_id, commit=args.commit, db_url=db_url))


if __name__ == "__main__":
    main()
