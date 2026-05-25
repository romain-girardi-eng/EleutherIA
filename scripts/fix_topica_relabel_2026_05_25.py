#!/usr/bin/env python3
"""Relabel phi042 slot to its true title: Topica.

Work `urn_cts_latinlit_phi0474_phi042_lat` was mislabeled "De Divinatione" but
its 100 passages are actually Cicero's Topica (phi042 in PHI/Perseus). The text
confirms this: it is a treatise on legal argumentation addressed to C. Trebatius,
not a dialogue on divination.

Fix: set title = "Topica" in free_will.ancient_works. The canonical_id, work_id,
passages, and citations are left untouched.

Dry-run by default; --commit to write. Idempotent. Snapshot before mutation.

Usage:
    .venv/bin/python -m scripts.fix_topica_relabel_2026_05_25 [--commit]
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_DIR = ROOT / "data" / "corpus" / "fix_snapshots" / "fix_topica_relabel_2026_05_25"

WORK_CANONICAL_ID = "urn_cts_latinlit_phi0474_phi042_lat"
NEW_TITLE = "Topica"


def _db_url() -> str:
    for line in (ROOT / ".env").open(encoding="utf-8"):
        if line.startswith("DATABASE_URL="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("DATABASE_URL not found in .env")


def _pg_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return "postgres://" + url[len("postgresql://"):]
    return url


async def main(commit: bool) -> int:
    import asyncpg

    conn: asyncpg.Connection = await asyncio.wait_for(
        asyncpg.connect(_pg_url(_db_url())), timeout=30
    )
    try:
        row = await conn.fetchrow(
            "SELECT work_id, canonical_id, title FROM free_will.ancient_works WHERE canonical_id = $1",
            WORK_CANONICAL_ID,
        )
        if not row:
            print(f"ERROR: work not found: {WORK_CANONICAL_ID}")
            return 1

        current_title = row["title"]
        work_id = str(row["work_id"])

        print(f"Work:          {WORK_CANONICAL_ID}")
        print(f"Current title: {current_title!r}")
        print(f"New title:     {NEW_TITLE!r}")
        print(f"Mode:          {'COMMIT' if commit else 'DRY-RUN'}")

        if current_title == NEW_TITLE:
            print("Already correct — nothing to do.")
            return 0

        # Snapshot
        SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        snap = {
            "work_id": work_id,
            "canonical_id": WORK_CANONICAL_ID,
            "old_title": current_title,
            "new_title": NEW_TITLE,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        snap_file = SNAPSHOT_DIR / "work_before.json"
        snap_file.write_text(json.dumps(snap, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Snapshot: {snap_file}")

        if not commit:
            print("\n[DRY-RUN] Pass --commit to write changes to ancient_works.")
            return 0

        await conn.execute(
            """
            UPDATE free_will.ancient_works
               SET title      = $1,
                   updated_at = $2
             WHERE canonical_id = $3
            """,
            NEW_TITLE,
            datetime.now(UTC),
            WORK_CANONICAL_ID,
        )
        print(f"\nUpdated: title → {NEW_TITLE!r}. DONE.")

    finally:
        await conn.close()

    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--commit", action="store_true", help="Write changes to DB (default: dry-run)")
    args = ap.parse_args()
    sys.exit(asyncio.run(main(args.commit)))
