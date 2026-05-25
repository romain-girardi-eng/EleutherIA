#!/usr/bin/env python3
"""Deduplicate Tatian Oratio ad Graecos passages (tlg1766_tlg001_grc).

Work urn_cts_greeklit_tlg1766_tlg001_grc was ingested multiple times: 98 passages
for 42 unique cts_urns. For each duplicate cts_urn group, keep the passage with the
most citations (tiebreak: lowest sequence_number), re-point all citations from the
dup passage_ids to the kept passage_id, then delete the duplicates.

Safety guarantee: citations are re-pointed BEFORE any DELETE. After re-pointing,
zero citations remain on passages-to-delete, then DELETE executes. Each group runs
in a single transaction.

Decision table is read verbatim from data/corpus/PLAN_tatian_dedup.md:
  keep_id = passage whose prefix matches the plan's "Keep" column.
  delete_ids = all other passage_ids in the same cts_urn group.

Dry-run by default; --commit to write to DB.
Snapshot written to data/corpus/fix_snapshots/dedup_tatian_2026_05_25/ before any mutation.

Usage:
    .venv/bin/python -m scripts.dedup_tatian_2026_05_25 [--commit]
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_DIR = ROOT / "data" / "corpus" / "fix_snapshots" / "dedup_tatian_2026_05_25"

WORK_CANONICAL_ID = "urn_cts_greeklit_tlg1766_tlg001_grc"

# Dedup table from PLAN_tatian_dedup.md.
# Each entry: (cts_urn_suffix, keep_prefix, [delete_prefixes])
# "prefix" = first 8 hex chars of the passage_id UUID.
PLAN: list[tuple[str, str, list[str]]] = [
    ("1",   "04a012aa", ["98d2f9ed", "caee9190"]),
    ("2",   "56fa068a", ["cbb585b5"]),
    ("3",   "6c3385fb", ["5c2f2a79", "1954e39f"]),
    ("4",   "d6337b3b", ["f440198a"]),
    ("5",   "3f5fbd39", ["c055123e"]),
    ("6",   "bea30080", ["dddc0b2d"]),
    ("7",   "a36c2d9d", ["56827782"]),
    ("8",   "8ac4c3f3", ["9049e7c9", "c5637aac", "de42fb55", "f470a2d3"]),
    ("9",   "e06ffb4e", ["9f79e224"]),
    ("10",  "c8077aeb", ["67f85d86", "2d084d31"]),
    ("11",  "f8ceab87", ["f0fc5be8"]),
    ("12",  "16167cda", ["9b395079", "161e51dc", "9c676659"]),
    ("13",  "9e1a5801", ["a195bc60"]),
    ("14",  "8e412b53", ["77425415"]),
    ("15",  "fdefee1b", ["0ad1bd43", "2de19140"]),
    ("16",  "ce388f19", ["ee1c8759"]),
    ("17",  "c684c41a", ["103575fe", "96abd640"]),
    ("18",  "b8c7e7f9", ["02b9eb09"]),
    ("19",  "7cf1609f", ["2bc3ada4", "f4421893"]),
    ("20",  "e3a3a853", ["abf966e8"]),
    ("21",  "662575cf", ["9b019453", "3d1d7512"]),
    ("22",  "6dcfe239", ["63ff5c99"]),
    ("23",  "47437519", ["e0ae5416"]),
    ("25",  "a169384a", ["764b9daa"]),
    ("26",  "330b4bfc", ["35072cd3", "842bb2a2"]),
    ("27",  "54589fa1", ["b851c6c6"]),
    ("29",  "8cc979d7", ["0b6da01e"]),
    ("31",  "915a040a", ["1e4b0729", "ba946085"]),
    ("32",  "f11e9e25", ["80e8fcf5", "cd7d4168"]),
    ("33",  "ab9edfce", ["25cbef0e", "e5b22a38"]),
    ("34",  "245a8d4a", ["deacfd2c", "62f07356"]),
    ("35",  "4b57006b", ["071be711"]),
    ("36",  "e3643908", ["abc4d835"]),
    ("37",  "808cc931", ["bbb59403"]),
    ("39",  "3c51df53", ["a98b975c", "32a158e2"]),
    ("40",  "890918ec", ["628e5168"]),
    ("41",  "9a953cc1", ["6a2e7bf0", "d733e0d8"]),
]


def _db_url() -> str:
    for line in (ROOT / ".env").open(encoding="utf-8"):
        if line.startswith("DATABASE_URL="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("DATABASE_URL not found in .env")


def _pg_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return "postgres://" + url[len("postgresql://"):]
    return url


async def _resolve_prefix(conn, prefix: str) -> str | None:
    """Resolve a passage_id UUID prefix to a full UUID string."""
    row = await conn.fetchrow(
        "SELECT passage_id FROM free_will.passages WHERE passage_id::text LIKE $1 || '%'",
        prefix,
    )
    return str(row["passage_id"]) if row else None


async def main(commit: bool) -> int:
    import asyncpg

    conn: asyncpg.Connection = await asyncio.wait_for(
        asyncpg.connect(_pg_url(_db_url())), timeout=30
    )
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

    try:
        print(f"Mode: {'COMMIT' if commit else 'DRY-RUN'}")
        print(f"Timestamp: {datetime.now(UTC).isoformat()}")

        # Verify work exists
        work = await conn.fetchrow(
            "SELECT work_id FROM free_will.ancient_works WHERE canonical_id = $1",
            WORK_CANONICAL_ID,
        )
        if not work:
            print(f"ERROR: work {WORK_CANONICAL_ID} not found in DB")
            return 1
        work_id = work["work_id"]

        # Snapshot all affected passages before anything
        passage_count_before = await conn.fetchval(
            "SELECT COUNT(*) FROM free_will.passages WHERE work_id = $1", work_id
        )
        citation_count_before = await conn.fetchval(
            """SELECT COUNT(*) FROM free_will.passage_citations pc
               JOIN free_will.passages p ON p.passage_id = pc.passage_id
               WHERE p.work_id = $1""",
            work_id,
        )
        print(f"\nBefore: {passage_count_before} passages, {citation_count_before} citations")

        # Snapshot passage state
        snap_passages = await conn.fetch(
            """SELECT p.passage_id::text, p.cts_urn, p.sequence_number, p.canonical_ref,
                      COUNT(pc.citation_id) as cit_count
               FROM free_will.passages p
               LEFT JOIN free_will.passage_citations pc ON pc.passage_id = p.passage_id
               WHERE p.work_id = $1
               GROUP BY p.passage_id, p.cts_urn, p.sequence_number, p.canonical_ref
               ORDER BY p.cts_urn, p.sequence_number""",
            work_id,
        )
        snap_file = SNAPSHOT_DIR / "passages_before.json"
        snap_file.write_text(
            json.dumps([dict(r) for r in snap_passages], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"Snapshot: {snap_file}")

        # Snapshot citation state
        snap_cits = await conn.fetch(
            """SELECT pc.citation_id::text, pc.passage_id::text, pc.kg_node_id,
                      pc.citation_type, pc.confidence
               FROM free_will.passage_citations pc
               JOIN free_will.passages p ON p.passage_id = pc.passage_id
               WHERE p.work_id = $1
               ORDER BY pc.passage_id::text, pc.kg_node_id""",
            work_id,
        )
        snap_cit_file = SNAPSHOT_DIR / "citations_before.json"
        snap_cit_file.write_text(
            json.dumps([dict(r) for r in snap_cits], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"Snapshot: {snap_cit_file}")

        # Resolve plan entries to full UUIDs
        total_repointed = 0
        total_deleted = 0
        groups_ok = 0
        errors: list[str] = []

        for suffix, keep_prefix, delete_prefixes in PLAN:
            keep_id = await _resolve_prefix(conn, keep_prefix)
            if not keep_id:
                errors.append(f"cts_urn :{suffix}: keep prefix {keep_prefix} NOT FOUND")
                continue

            delete_ids = []
            missing = []
            for dp in delete_prefixes:
                did = await _resolve_prefix(conn, dp)
                if did:
                    delete_ids.append(did)
                else:
                    missing.append(dp)

            if missing:
                errors.append(
                    f"cts_urn :{suffix}: delete prefix(es) not found: {missing}"
                )
                continue

            # Count citations on delete_ids before re-pointing
            cits_on_delete = await conn.fetchval(
                "SELECT COUNT(*) FROM free_will.passage_citations WHERE passage_id = ANY($1::uuid[])",
                delete_ids,
            )

            print(
                f"\ncts_urn :{suffix:3s}: keep={keep_prefix} | "
                f"delete={delete_prefixes} | cits_to_repoint={cits_on_delete}"
            )

            if commit:
                async with conn.transaction():
                    # Step 1: re-point citations
                    if cits_on_delete > 0:
                        for did in delete_ids:
                            updated = await conn.execute(
                                "UPDATE free_will.passage_citations SET passage_id = $1 WHERE passage_id = $2::uuid",
                                keep_id,
                                did,
                            )
                            total_repointed += int(updated.split()[-1])

                    # Step 2: verify 0 citations remain on delete_ids
                    remaining = await conn.fetchval(
                        "SELECT COUNT(*) FROM free_will.passage_citations WHERE passage_id = ANY($1::uuid[])",
                        delete_ids,
                    )
                    if remaining > 0:
                        raise RuntimeError(
                            f"cts_urn :{suffix}: {remaining} citations still on delete_ids after re-point — aborting group"
                        )

                    # Step 3: delete passages
                    deleted = await conn.execute(
                        "DELETE FROM free_will.passages WHERE passage_id = ANY($1::uuid[])",
                        delete_ids,
                    )
                    n_deleted = int(deleted.split()[-1])
                    total_deleted += n_deleted
                    print(f"  -> re-pointed {cits_on_delete}, deleted {n_deleted} passages")
            else:
                total_repointed += cits_on_delete
                total_deleted += len(delete_ids)
                print(f"  [DRY-RUN] would repoint {cits_on_delete} cits, delete {len(delete_ids)} passages")

            groups_ok += 1

        print(f"\n{'='*60}")
        print(f"Groups processed OK: {groups_ok}/{len(PLAN)}")
        print(f"Total citations re-pointed: {total_repointed}")
        print(f"Total passages deleted: {total_deleted}")
        if errors:
            print(f"\nERRORS ({len(errors)}):")
            for e in errors:
                print(f"  {e}")

        if commit:
            passage_count_after = await conn.fetchval(
                "SELECT COUNT(*) FROM free_will.passages WHERE work_id = $1", work_id
            )
            citation_count_after = await conn.fetchval(
                """SELECT COUNT(*) FROM free_will.passage_citations pc
                   JOIN free_will.passages p ON p.passage_id = pc.passage_id
                   WHERE p.work_id = $1""",
                work_id,
            )
            print(f"\nAfter: {passage_count_after} passages, {citation_count_after} citations")
            print(f"  (delta: -{passage_count_before - passage_count_after} passages, "
                  f"citations {citation_count_before}→{citation_count_after})")

            # Verify no dangling citations on deleted passages
            # (they've been deleted so FK should prevent any)
            print("  FK constraint guarantees 0 dangling citations on deleted passages.")
        else:
            print("\n[DRY-RUN] Pass --commit to execute.")

    finally:
        await conn.close()

    return 0 if not errors else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--commit", action="store_true", help="Write to DB (default: dry-run)")
    args = ap.parse_args()
    sys.exit(asyncio.run(main(args.commit)))
