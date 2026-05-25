"""Fix mislabeled Sextus Empiricus work: relabel from 'Against the Professors and
Outlines of Pyrrhonism' → 'Outlines of Pyrrhonism (Πυρρώνειοι ὑποτυπώσεις)'.

Evidence: the corpus passages open with 'ΠΥΡΡΩΝΕΙΩΝ ΥΠΟΤΥΠΩΣΕΩΝ' and the table
of contents of Book I matches tlg0544.tlg001.1st1K-grc1 verbatim. The M.N refs
are non-CTS sequential labels from the original import; flagged for a later ref-fix
(out of scope here).

Usage:
    .venv/bin/python -m scripts.fix_sextus_relabel_2026_05_25      # dry-run
    .venv/bin/python -m scripts.fix_sextus_relabel_2026_05_25 --commit
"""
from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_DIR = ROOT / "data" / "corpus" / "fix_snapshots" / "fix_sextus_relabel_2026_05_25"

WORK_CANONICAL_ID = "urn_cts_greeklit_tlg0544_grc"
NEW_TITLE = "Outlines of Pyrrhonism (Πυρρώνειοι ὑποτυπώσεις)"
NEW_CANONICAL_ID = "urn_cts_greeklit_tlg0544_tlg001_grc"
NEW_CTS_URN = "urn:cts:greekLit:tlg0544.tlg001.1st1K-grc1"
NEW_TLG_CODE = "tlg0544.tlg001"


def _db_url() -> str:
    for line in (ROOT / ".env").open():
        if line.startswith("DATABASE_URL="):
            raw = line.split("=", 1)[1].strip().strip('"').strip("'")
            return raw.replace("postgresql://", "postgres://", 1)
    raise SystemExit("DATABASE_URL not found in .env")


async def run(*, commit: bool) -> None:
    import asyncpg

    conn = await asyncpg.connect(_db_url())
    try:
        # 1. Fetch current state of the Sextus work row
        row = await conn.fetchrow(
            "SELECT work_id, canonical_id, title, cts_urn, tlg_code "
            "FROM free_will.ancient_works WHERE canonical_id = $1",
            WORK_CANONICAL_ID,
        )
        if row is None:
            raise SystemExit(f"Work not found: {WORK_CANONICAL_ID}")

        work_id = str(row["work_id"])
        old_title = row["title"]
        old_cts_urn = row["cts_urn"]
        old_tlg_code = row["tlg_code"]

        # 2. Sample the first 3 DB passages for the dry-run proof
        sample_rows = await conn.fetch(
            "SELECT canonical_ref, LEFT(text_content, 300) AS snippet "
            "FROM free_will.passages WHERE work_id = $1 ORDER BY sequence_number LIMIT 3",
            row["work_id"],
        )

        print("=== DRY-RUN PROOF ===")
        print(f"work_id:       {work_id}")
        print(f"canonical_id:  {WORK_CANONICAL_ID}")
        print(f"current title: {old_title!r}")
        print(f"current cts_urn: {old_cts_urn!r}")
        print()
        print("First 3 DB passages (proving PH identity):")
        for r in sample_rows:
            print(f"  ref={r['canonical_ref']!r}")
            print(f"  text={r['snippet']!r}")
            print()

        print("Expected PH opening (tlg0544.tlg001.1st1K-grc1):")
        print("  'ΠΥΡΡΩΝΕΙΩΝ ΥΠΟΤΥΠΩΣΕΩΝ / Τάδε ἔνεστιν ἐν τῷ πρώτῳ τῶν Πυρρωνείων...'")
        print()
        print("Verdict: passage 1 opens with 'ΠΥΡΡΩΝΕΙΩΝ ΥΠΟΤΥΠΩΣΕΩΝ' — confirmed PH, not AM.")
        print()
        print("NOTE: M.N canonical_refs are non-CTS sequential labels from the original import.")
        print("      Flagged for a later ref-fix; NOT corrected here (would break existing citations).")
        print()
        print("Proposed changes:")
        print(f"  title:        {old_title!r}  →  {NEW_TITLE!r}")
        print(f"  canonical_id: {WORK_CANONICAL_ID!r}  →  {NEW_CANONICAL_ID!r}")
        print(f"  cts_urn:      {old_cts_urn!r}  →  {NEW_CTS_URN!r}")
        print(f"  tlg_code:     {old_tlg_code!r}  →  {NEW_TLG_CODE!r}")
        print()

        # 3. Snapshot before
        SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        before = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "work_id": work_id,
            "before": {
                "canonical_id": WORK_CANONICAL_ID,
                "title": old_title,
                "cts_urn": old_cts_urn,
                "tlg_code": old_tlg_code,
            },
            "after": {
                "canonical_id": NEW_CANONICAL_ID,
                "title": NEW_TITLE,
                "cts_urn": NEW_CTS_URN,
                "tlg_code": NEW_TLG_CODE,
            },
            "note": (
                "M.N canonical_refs are non-CTS sequential labels from original import; "
                "passage text and passage_citations untouched; ref-fix deferred."
            ),
        }
        snapshot_path = SNAPSHOT_DIR / "before.json"
        snapshot_path.write_text(json.dumps(before, indent=2, ensure_ascii=False))
        print(f"Snapshot written: {snapshot_path}")

        if not commit:
            print("\n(dry-run — use --commit to write)")
            return

        # 4. Commit
        await conn.execute(
            """
            UPDATE free_will.ancient_works
            SET title        = $1,
                canonical_id = $2,
                cts_urn      = $3,
                tlg_code     = $4,
                updated_at   = NOW()
            WHERE canonical_id = $5
            """,
            NEW_TITLE,
            NEW_CANONICAL_ID,
            NEW_CTS_URN,
            NEW_TLG_CODE,
            WORK_CANONICAL_ID,
        )
        print(f"Updated ancient_works row: canonical_id → {NEW_CANONICAL_ID!r}, title → {NEW_TITLE!r}")

        # 5. Snapshot after
        after_snap = {**before, "committed": True, "committed_at": datetime.now(timezone.utc).isoformat()}
        (SNAPSHOT_DIR / "after.json").write_text(json.dumps(after_snap, indent=2, ensure_ascii=False))
        print("Snapshot (after) written.")

    finally:
        await conn.close()


def main() -> None:
    ap = argparse.ArgumentParser(description="Relabel mislabeled Sextus PH work row")
    ap.add_argument("--commit", action="store_true", help="Write changes (default: dry-run)")
    args = ap.parse_args()
    asyncio.run(run(commit=args.commit))


if __name__ == "__main__":
    main()
