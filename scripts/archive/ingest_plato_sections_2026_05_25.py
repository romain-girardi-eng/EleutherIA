#!/usr/bin/env python3
"""Ingest free-will-relevant sections of Plato's Phaedo and Gorgias.

Only the Stephanus pages pertinent to free will, causation, and moral
responsibility are kept (lean ingestion). Text is verbatim from the Perseus
GitHub TEI — zero fabrication.

Dry-run by default; pass --commit to write to the database.

Usage:
    .venv/bin/python -m scripts.ingest_plato_sections_2026_05_25 [--commit]
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_DIR = ROOT / "data" / "corpus" / "fix_snapshots" / "ingest_plato_sections_2026_05_25"

DB_URL_KEY = "DATABASE_URL"

# ---------------------------------------------------------------------------
# Work definitions
# ---------------------------------------------------------------------------

WORKS: list[dict[str, Any]] = [
    {
        "canonical_id": "urn_cts_greeklit_tlg0059_tlg004_grc",
        "title": "Phaedo (Φαίδων)",
        "title_original": "Φαίδων",
        "cts_urn": "urn:cts:greekLit:tlg0059.tlg004.perseus-grc2",
        "author": "Plato",
        "language": "grc",
        "period": "Classical",
        # Stephanus pages to keep (Socrates on causation + the afterlife/eschatology)
        "keep_pages": {96, 97, 98, 99, 114, 115},
        # Sanity check: first kept passage should start with this string
        "opening_check": "ΦΑΙΔ.",
        "opening_page": 96,
    },
    {
        "canonical_id": "urn_cts_greeklit_tlg0059_tlg023_grc",
        "title": "Gorgias (Γοργίας)",
        "title_original": "Γοργίας",
        "cts_urn": "urn:cts:greekLit:tlg0059.tlg023.perseus-grc2",
        "author": "Plato",
        "language": "grc",
        "period": "Classical",
        # Pages 466-481: power / wanting / justice / tyrant's impotence
        # Pages 507-511: cosmic order, self-mastery, just punishment
        "keep_pages": set(range(466, 482)) | set(range(507, 512)),
        "opening_check": "ΣΩ.",
        "opening_page": 466,
    },
]

SOURCE_NOTE = "Perseus Digital Library (GitHub TEI — lean section ingestion)"


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def _db_url() -> str:
    for line in (ROOT / ".env").open(encoding="utf-8"):
        if line.startswith(f"{DB_URL_KEY}="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit(f"{DB_URL_KEY} not found in .env")


def _pg_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return "postgres://" + url[len("postgresql://"):]
    return url


async def _upsert_work(
    conn: Any, meta: dict[str, Any], *, commit: bool
) -> tuple[str, bool]:
    """Insert work row if absent. Returns (work_id, was_created)."""
    import asyncpg  # noqa: PLC0415

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
            (canonical_id, title, title_original, author, language, period,
             cts_urn, source, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $9)
        RETURNING work_id
        """,
        meta["canonical_id"],
        meta["title"],
        meta["title_original"],
        meta["author"],
        meta["language"],
        meta["period"],
        meta["cts_urn"],
        SOURCE_NOTE,
        datetime.now(UTC),
    )
    return str(row["work_id"]), True


async def _existing_urns(conn: Any, work_id: str) -> set[str]:
    rows = await conn.fetch(
        "SELECT cts_urn FROM free_will.passages WHERE work_id = $1",
        work_id,
    )
    return {r["cts_urn"] for r in rows}


async def _max_sequence(conn: Any, work_id: str) -> int:
    row = await conn.fetchrow(
        "SELECT max(sequence_number) AS m FROM free_will.passages WHERE work_id = $1",
        work_id,
    )
    return int(row["m"] or 0)


async def _insert_passages(
    conn: Any, work_id: str, passages: list[dict[str, Any]], start_seq: int
) -> int:
    rows = [
        (
            work_id,
            p["cts_urn"].split(":")[-1],   # canonical_ref = the part after last ':'
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


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------

def _stephanus_page(cts_urn: str) -> int | None:
    """Extract the integer Stephanus page from a passage CTS URN.

    Plato TEI refs at this edition level are plain integers (e.g. '96', '466').
    We take the part after the last ':' and parse its leading digits.
    """
    ref = cts_urn.split(":")[-1]
    # Strip any trailing letter suffixes (e.g. '96a' → 96).
    # In practice this edition uses bare integers, but be defensive.
    digits = ""
    for ch in ref:
        if ch.isdigit():
            digits += ch
        else:
            break
    if not digits:
        return None
    return int(digits)


def filter_passages(passages: list[dict], keep_pages: set[int]) -> list[dict]:
    return [p for p in passages if _stephanus_page(p["cts_urn"]) in keep_pages]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main(commit: bool) -> int:
    import asyncpg  # noqa: I001, PLC0415
    import scripts.corpus_github_fetch as _fetch_mod  # noqa: PLC0415

    fetch_work_passages = _fetch_mod.fetch_work_passages

    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

    pg_url = _pg_url(_db_url())
    conn: Any = await asyncio.wait_for(asyncpg.connect(pg_url), timeout=30)

    try:
        for meta in WORKS:
            print(f"\n{'=' * 64}")
            print(f"Work:   {meta['title']}")
            print(f"URN:    {meta['cts_urn']}")
            print(f"Keep:   {sorted(meta['keep_pages'])}")
            print(f"Mode:   {'COMMIT' if commit else 'DRY-RUN'}")

            # --- Collision guard ------------------------------------------
            existing_work = await conn.fetchrow(
                "SELECT work_id FROM free_will.ancient_works WHERE canonical_id = $1",
                meta["canonical_id"],
            )
            if existing_work and not commit:
                print(f"  Work row already exists (work_id={existing_work['work_id']}), "
                      "would reuse in commit mode.")
            elif existing_work:
                print(f"  Work row already exists (work_id={existing_work['work_id']}), reusing.")

            # --- Fetch full dialogue from GitHub --------------------------
            print(f"  Fetching TEI from GitHub...")
            all_passages = fetch_work_passages(meta["cts_urn"])
            print(f"  Full dialogue: {len(all_passages)} passages")

            if not all_passages:
                print("  ERROR: 0 passages fetched — aborting.")
                return 1

            # --- Filter to keep-set ---------------------------------------
            kept = filter_passages(all_passages, meta["keep_pages"])
            print(f"  After keep-set filter: {len(kept)} passages")

            if not kept:
                print("  ERROR: keep-set filter yielded 0 passages — check URN/pages.")
                return 1

            # --- Opening sample (sanity) -----------------------------------
            first = kept[0]
            first_ref = first["cts_urn"].split(":")[-1]
            first_text = first["text_content"]
            print(f"\n  Opening passage (p.{first_ref}):")
            print(f"  {first_text[:160]!r}")

            if not first_text.startswith(meta["opening_check"]):
                print(
                    f"\n  WARNING: Opening does not start with {meta['opening_check']!r}. "
                    "Verify page content manually."
                )
            # Don't abort on this — the dialogue attribute sigla may vary.

            # --- Snapshot pre-state ---------------------------------------
            snap = {
                "canonical_id": meta["canonical_id"],
                "cts_urn": meta["cts_urn"],
                "total_fetched": len(all_passages),
                "kept_count": len(kept),
                "keep_pages": sorted(meta["keep_pages"]),
                "first_kept_cts_urn": kept[0]["cts_urn"],
                "last_kept_cts_urn": kept[-1]["cts_urn"],
                "first_kept_text_sample": kept[0]["text_content"][:120],
                "timestamp": datetime.now(UTC).isoformat(),
            }
            snap_file = SNAPSHOT_DIR / f"{meta['canonical_id']}_pre.json"
            snap_file.write_text(
                json.dumps(snap, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            print(f"\n  Snapshot: {snap_file}")

            if not commit:
                print("  [DRY-RUN] Pass --commit to write to DB.")
                continue

            # --- Upsert work row ------------------------------------------
            work_id, was_created = await _upsert_work(conn, meta, commit=commit)
            print(f"  Work row: {'created' if was_created else 'reused'} (work_id={work_id})")

            # --- Skip already-present passages (idempotent) ---------------
            present = await _existing_urns(conn, work_id)
            new_passages = [p for p in kept if p["cts_urn"] not in present]
            print(f"  Already present: {len(present)} | New to insert: {len(new_passages)}")

            if not new_passages:
                print("  Nothing to insert (all passages already present).")
                continue

            start_seq = await _max_sequence(conn, work_id) + 1
            inserted = await _insert_passages(conn, work_id, new_passages, start_seq)
            print(f"  Inserted: {inserted} passages (seq {start_seq}–{start_seq + inserted - 1})")

            # --- Post-insert verification ----------------------------------
            count_after = await conn.fetchval(
                "SELECT count(*) FROM free_will.passages WHERE work_id = $1",
                work_id,
            )
            print(f"  DB total for this work: {count_after} passages")

    finally:
        await conn.close()

    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--commit",
        action="store_true",
        help="Write changes to DB (default: dry-run)",
    )
    args = ap.parse_args()
    sys.exit(asyncio.run(main(args.commit)))
