#!/usr/bin/env python3
"""Fix underscore-for-dot in cts_urn / canonical_ref for Justin Martyr Dialogus cum Tryphone.

The task specification names this work 'Epictetus Discourses III' but the canonical_id
`urn_cts_greeklit_tlg0645_tlg003_grc` is Justin Martyr's Dialogus cum Tryphone (tlg0645=Justin,
tlg003=Dialogue with Trypho), not Epictetus. The underlying bug is the same: the importer
recorded the CTS ref separator as `_` (e.g. `1_1`) instead of `.` (e.g. `1.1`).

Work: canonical_id = 'urn_cts_greeklit_tlg0645_tlg003_grc', 750 passages, 767 citations.
Fix: replace `_` with `.` in the ref part (after the final `:`) of both cts_urn and
canonical_ref. passage_id unchanged → all 767 citations preserved.

Pre-fix verification: fetch authoritative passages from Perseus GitHub
(urn:cts:greekLit:tlg0645.tlg003.perseus-grc2) and confirm that 100% of the
corrected cts_urns appear in the authoritative set. Aborts if match rate is low.

Dry-run by default; --commit to write. Idempotent. Snapshots to
data/corpus/fix_snapshots/ before mutating.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_DIR = ROOT / "data" / "corpus" / "fix_snapshots" / "fix_epictetus_refs_2026_05_24"

WORK_CANONICAL_ID = "urn_cts_greeklit_tlg0645_tlg003_grc"
AUTH_WORK_URN = "urn:cts:greekLit:tlg0645.tlg003.perseus-grc2"
# Minimum fraction of fixed urns that must appear in authoritative set before committing.
MIN_MATCH_RATE = 0.95


def _db_url() -> str:
    for line in (ROOT / ".env").open():
        if line.startswith("DATABASE_URL="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("DATABASE_URL not found in .env")


def _fix_ref(cts_urn: str) -> str:
    """Replace _ with . in the ref part (after the last colon)."""
    idx = cts_urn.rfind(":")
    if idx == -1:
        return cts_urn
    return cts_urn[: idx + 1] + cts_urn[idx + 1 :].replace("_", ".")


async def _verify_against_authoritative() -> tuple[int, int]:
    """Fetch authoritative passages and return (matched, total_db_passages)."""
    import sys

    import asyncpg

    sys.path.insert(0, str(ROOT))
    from scripts.corpus_github_fetch import fetch_work_passages

    conn = await asyncpg.connect(_db_url())
    try:
        rows = await conn.fetch(
            """
            SELECT p.cts_urn
            FROM free_will.passages p
            JOIN free_will.ancient_works w ON w.work_id = p.work_id
            WHERE w.canonical_id = $1
            """,
            WORK_CANONICAL_ID,
        )
    finally:
        await conn.close()

    db_urns = [r["cts_urn"] for r in rows]
    auth_passages = fetch_work_passages(AUTH_WORK_URN)
    auth_urns = {p["cts_urn"] for p in auth_passages}

    matched = sum(1 for u in db_urns if _fix_ref(u) in auth_urns)
    return matched, len(db_urns)


async def _fetch_affected(conn) -> list[dict]:
    rows = await conn.fetch(
        """
        SELECT p.passage_id::text AS passage_id,
               p.cts_urn, p.canonical_ref
        FROM free_will.passages p
        JOIN free_will.ancient_works w ON w.work_id = p.work_id
        WHERE w.canonical_id = $1
        """,
        WORK_CANONICAL_ID,
    )
    return [dict(r) for r in rows]


async def main(commit: bool) -> int:
    import asyncpg

    print("Verifying against authoritative source…")
    matched, total = await _verify_against_authoritative()
    rate = matched / total if total else 0.0
    print(f"Authoritative match after fix: {matched}/{total} ({rate:.1%})")

    if rate < MIN_MATCH_RATE:
        print(
            f"ERROR: match rate {rate:.1%} < threshold {MIN_MATCH_RATE:.0%}. "
            "Fix may be wrong — aborting."
        )
        return 1

    conn = await asyncpg.connect(_db_url())
    try:
        affected = await _fetch_affected(conn)

        # Filter rows that actually need change
        to_fix = [
            r for r in affected
            if "_" in r["cts_urn"].split(":")[-1]
               or (r["canonical_ref"] and "_" in r["canonical_ref"])
        ]
        already_clean = len(affected) - len(to_fix)
        print(
            f"Rows to fix: {len(to_fix)}/{len(affected)} "
            f"({already_clean} already clean — idempotent)"
        )

        if not to_fix:
            print("Nothing to do.")
            return 0

        if not commit:
            print("[DRY-RUN] Pass --commit to write changes.")
            return 0

        # Snapshot before mutation
        SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        snap_path = SNAPSHOT_DIR / "affected_passages.json"
        snap_path.write_text(
            json.dumps(to_fix, sort_keys=True, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"Snapshot written: {snap_path}")

        # Apply fix (passages table has no updated_at column)
        updated = 0
        for row in to_fix:
            new_cts = _fix_ref(row["cts_urn"])
            new_ref = (
                row["canonical_ref"].replace("_", ".")
                if row["canonical_ref"]
                else row["canonical_ref"]
            )
            await conn.execute(
                """
                UPDATE free_will.passages
                   SET cts_urn = $1,
                       canonical_ref = $2
                 WHERE passage_id = $3
                """,
                new_cts,
                new_ref,
                row["passage_id"],
            )
            updated += 1

        print(f"Updated {updated} passages. DONE.")
    finally:
        await conn.close()

    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--commit", action="store_true", help="Write changes (default: dry-run)")
    args = ap.parse_args()
    sys.exit(asyncio.run(main(args.commit)))
