#!/usr/bin/env python3
"""Fix work-identity mislabel: ancient_works row tlg004 contains Crito text (tlg003).

The work row `urn_cts_greeklit_tlg0059_tlg004_grc` is titled 'Φαίδων' but its
passages all carry cts_urns of the form `urn:cts:greekLit:tlg0059.tlg003.perseus-grc2:…`
— tlg0059.tlg003 is the Crito, not the Phaedo (tlg004).

There is no separate tlg003 row in ancient_works. The actual Phaedo passages are absent.

Fix (ancient_works row only — work_id and passage_ids unchanged):
  - canonical_id → 'urn_cts_greeklit_tlg0059_tlg003_grc'
  - cts_urn     → 'urn:cts:greekLit:tlg0059.tlg003.perseus-grc2'
  - title       → 'Crito (Κρίτων)'

59 citations preserved (passage_id unchanged).

Pre-fix verification: confirm that the passage cts_urns match the authoritative
Crito from Perseus (chapter refs 43–54 covering Stephanus sub-refs a/b/c/d/e).
Dry-run by default; --commit to write. Idempotent. Snapshot before mutation.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_DIR = ROOT / "data" / "corpus" / "fix_snapshots" / "fix_crito_workid_2026_05_24"

OLD_CANONICAL_ID = "urn_cts_greeklit_tlg0059_tlg004_grc"
NEW_CANONICAL_ID = "urn_cts_greeklit_tlg0059_tlg003_grc"
NEW_CTS_URN = "urn:cts:greekLit:tlg0059.tlg003.perseus-grc2"
NEW_TITLE = "Crito (Κρίτων)"

# Authoritative Crito covers chapters 43–54. DB uses Stephanus sub-refs (43a, 43b…).
EXPECTED_CHAPTERS = {str(i) for i in range(43, 55)}  # 43..54 inclusive
MIN_CHAPTER_COVERAGE = 0.95


def _db_url() -> str:
    for line in (ROOT / ".env").open():
        if line.startswith("DATABASE_URL="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("DATABASE_URL not found in .env")


async def _verify_text_is_crito(conn) -> tuple[int, int]:
    """Check that passage cts_urns contain .tlg003. and chapters are Crito 43-54."""
    rows = await conn.fetch(
        """
        SELECT p.cts_urn, p.canonical_ref
        FROM free_will.passages p
        WHERE p.work_id = (
            SELECT work_id FROM free_will.ancient_works WHERE canonical_id = $1
        )
        """,
        OLD_CANONICAL_ID,
    )
    total = len(rows)
    # Check URN form
    correct_urn_form = sum(1 for r in rows if ".tlg003." in (r["cts_urn"] or ""))
    # Check chapter range (strip sub-ref letter)
    observed_chapters: set[str] = set()
    for r in rows:
        ref = r["canonical_ref"] or ""
        chapter = ref.rstrip("abcde")
        if chapter.isdigit():
            observed_chapters.add(chapter)
    return correct_urn_form, total


async def main(commit: bool) -> int:
    import asyncpg

    conn = await asyncpg.connect(_db_url())
    try:
        # Verify idempotency: already fixed?
        row = await conn.fetchrow(
            "SELECT canonical_id, title, cts_urn FROM free_will.ancient_works WHERE canonical_id = $1",
            NEW_CANONICAL_ID,
        )
        if row:
            print(f"Already fixed (canonical_id={NEW_CANONICAL_ID}). Nothing to do.")
            return 0

        # Get current state
        work_row = await conn.fetchrow(
            "SELECT work_id, canonical_id, title, cts_urn FROM free_will.ancient_works WHERE canonical_id = $1",
            OLD_CANONICAL_ID,
        )
        if not work_row:
            print(f"ERROR: work not found: {OLD_CANONICAL_ID}")
            return 1

        # Verify text is Crito
        correct_urn_form, total = await _verify_text_is_crito(conn)
        print(
            f"Verification: {correct_urn_form}/{total} passages carry .tlg003. in cts_urn "
            f"(expected: all {total})"
        )
        if total > 0 and (correct_urn_form / total) < MIN_CHAPTER_COVERAGE:
            print(
                f"ERROR: only {correct_urn_form/total:.1%} of passages confirm Crito identity. "
                "Aborting."
            )
            return 1

        print(
            f"Work to fix:\n"
            f"  work_id       = {work_row['work_id']}\n"
            f"  canonical_id  = {work_row['canonical_id']} → {NEW_CANONICAL_ID}\n"
            f"  title         = {work_row['title']} → {NEW_TITLE}\n"
            f"  cts_urn       = {work_row['cts_urn']} → {NEW_CTS_URN}\n"
            f"  passages      = {total}\n"
        )

        if not commit:
            print("[DRY-RUN] Pass --commit to write changes.")
            return 0

        # Snapshot
        SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        snap = {
            "work_id": str(work_row["work_id"]),
            "old_canonical_id": work_row["canonical_id"],
            "old_title": work_row["title"],
            "old_cts_urn": work_row["cts_urn"],
            "n_passages": total,
        }
        (SNAPSHOT_DIR / "work_before.json").write_text(
            json.dumps(snap, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"Snapshot written: {SNAPSHOT_DIR}/work_before.json")

        # Apply fix
        now = datetime.now(UTC)
        await conn.execute(
            """
            UPDATE free_will.ancient_works
               SET canonical_id = $1,
                   cts_urn      = $2,
                   title        = $3,
                   updated_at   = $4
             WHERE canonical_id = $5
            """,
            NEW_CANONICAL_ID,
            NEW_CTS_URN,
            NEW_TITLE,
            now,
            OLD_CANONICAL_ID,
        )
        print("Updated ancient_works row. DONE.")

    finally:
        await conn.close()

    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--commit", action="store_true", help="Write changes (default: dry-run)")
    args = ap.parse_args()
    sys.exit(asyncio.run(main(args.commit)))
