#!/usr/bin/env python3
"""Re-home English-edition citations to their Greek sibling passages, then delete the English works.

Two English works carry Greek-namespace CTS URNs and are redundant now that Greek text exists:

1. tlg0732_tlg014_eng (Alexander De Fato, English): 39 passages, 45 citations.
   Greek sibling: tlg0732_tlg014_grc (39 passages, same cts_urn space).
   Matching: by cts_urn (39/39 exact match per plan).

2. urn_cts_greeklit_tlg1766_tlg001_eng (Tatian English): 3 passages, 3 citations.
   Greek sibling: urn_cts_greeklit_tlg1766_tlg001_grc (post-dedup: 42 passages).
   Matching: by cts_urn (:7, :8, :11 → kept Greek passages from FIX 2).
   DEPENDENCY: FIX 2 (Tatian dedup) must run first.

Safety protocol:
  1. Snapshot before any mutation.
  2. Re-point citations passage_id → Greek passage_id (by cts_urn).
  3. Verify 0 citations remain on English passage_ids.
  4. DELETE English passages.
  5. DELETE English ancient_works row (only if no passages remain).

Dry-run by default; --commit to write to DB.

Usage:
    .venv/bin/python -m scripts.rehome_english_editions_2026_05_25 [--commit]
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_DIR = ROOT / "data" / "corpus" / "fix_snapshots" / "rehome_english_editions_2026_05_25"

ALEXANDER_ENG = "tlg0732_tlg014_eng"
ALEXANDER_GRC = "tlg0732_tlg014_grc"
TATIAN_ENG = "urn_cts_greeklit_tlg1766_tlg001_eng"
TATIAN_GRC = "urn_cts_greeklit_tlg1766_tlg001_grc"


def _db_url() -> str:
    for line in (ROOT / ".env").open(encoding="utf-8"):
        if line.startswith("DATABASE_URL="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("DATABASE_URL not found in .env")


def _pg_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return "postgres://" + url[len("postgresql://"):]
    return url


async def get_work_id(conn, canonical_id: str) -> str | None:
    row = await conn.fetchrow(
        "SELECT work_id FROM free_will.ancient_works WHERE canonical_id = $1",
        canonical_id,
    )
    return str(row["work_id"]) if row else None


async def get_passages(conn, work_id: str) -> list[dict]:
    rows = await conn.fetch(
        """SELECT p.passage_id::text AS passage_id, p.cts_urn, p.canonical_ref,
                  p.sequence_number
           FROM free_will.passages p
           WHERE p.work_id = $1::uuid
           ORDER BY p.sequence_number""",
        work_id,
    )
    return [dict(r) for r in rows]


async def get_citations(conn, work_id: str) -> list[dict]:
    rows = await conn.fetch(
        """SELECT pc.citation_id::text AS citation_id,
                  pc.passage_id::text AS passage_id,
                  pc.kg_node_id, pc.citation_type, pc.confidence,
                  p.cts_urn AS passage_cts_urn, p.canonical_ref
           FROM free_will.passage_citations pc
           JOIN free_will.passages p ON p.passage_id = pc.passage_id
           WHERE p.work_id = $1::uuid
           ORDER BY p.canonical_ref, pc.kg_node_id""",
        work_id,
    )
    return [dict(r) for r in rows]


async def process_rehome(
    conn,
    label: str,
    eng_canonical: str,
    grc_canonical: str,
    *,
    commit: bool,
) -> dict:
    print(f"\n{'='*60}")
    print(f"Group: {label}")
    print(f"  ENG: {eng_canonical}")
    print(f"  GRC: {grc_canonical}")

    eng_work_id = await get_work_id(conn, eng_canonical)
    grc_work_id = await get_work_id(conn, grc_canonical)

    if not eng_work_id:
        print(f"  SKIP: ENG work {eng_canonical} not found — already removed?")
        return {"rehomed": 0, "deleted_passages": 0, "deleted_works": 0, "errors": ["eng work not found"]}

    if not grc_work_id:
        print(f"  ERROR: GRC work {grc_canonical} not found")
        return {"rehomed": 0, "deleted_passages": 0, "deleted_works": 0, "errors": ["grc work not found"]}

    eng_passages = await get_passages(conn, eng_work_id)
    grc_passages = await get_passages(conn, grc_work_id)
    eng_cits = await get_citations(conn, eng_work_id)

    print(f"  ENG passages: {len(eng_passages)}, citations: {len(eng_cits)}")
    print(f"  GRC passages: {len(grc_passages)}")

    # Snapshot
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    snap_file = SNAPSHOT_DIR / f"snapshot_{label}.json"
    snap_file.write_text(
        json.dumps({
            "eng_passages": eng_passages,
            "eng_citations": eng_cits,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"  Snapshot: {snap_file}")

    # Build GRC index by cts_urn
    grc_by_cts: dict[str, str] = {}  # cts_urn -> passage_id
    for p in grc_passages:
        cts = p["cts_urn"]
        if cts in grc_by_cts:
            # Post-dedup there should be exactly one passage per cts_urn
            print(f"  WARNING: duplicate cts_urn in GRC after dedup: {cts}")
        else:
            grc_by_cts[cts] = p["passage_id"]

    # Map ENG passage_id -> GRC passage_id via cts_urn
    mapping: list[dict] = []
    unmatched: list[dict] = []
    for ep in eng_passages:
        grc_id = grc_by_cts.get(ep["cts_urn"])
        if grc_id:
            mapping.append({
                "eng_passage_id": ep["passage_id"],
                "grc_passage_id": grc_id,
                "cts_urn": ep["cts_urn"],
                "canonical_ref": ep["canonical_ref"],
            })
        else:
            unmatched.append(ep)

    print(f"  CTS-URN matches: {len(mapping)}/{len(eng_passages)}")
    if unmatched:
        print(f"  WARNING: {len(unmatched)} ENG passages have no GRC match:")
        for u in unmatched:
            print(f"    {u['passage_id'][:8]} | {u['cts_urn']}")

    if unmatched:
        print(f"  ERROR: cannot safely delete ENG passages without 100% mapping — aborting group")
        return {
            "rehomed": 0,
            "deleted_passages": 0,
            "deleted_works": 0,
            "errors": [f"{len(unmatched)} ENG passages without GRC match"],
        }

    # Map from eng_passage_id to grc_passage_id
    eng_to_grc: dict[str, str] = {m["eng_passage_id"]: m["grc_passage_id"] for m in mapping}

    # Count citations per eng_passage_id
    cits_by_eng: dict[str, list[dict]] = {}
    for c in eng_cits:
        cits_by_eng.setdefault(c["passage_id"], []).append(c)

    total_cits_to_repoint = len(eng_cits)
    print(f"  Citations to re-point: {total_cits_to_repoint}")

    for m in mapping:
        eng_pid = m["eng_passage_id"]
        cits = cits_by_eng.get(eng_pid, [])
        print(
            f"    {eng_pid[:8]} ({m['canonical_ref']}) → GRC {m['grc_passage_id'][:8]} "
            f"| {len(cits)} cits"
        )

    if commit:
        async with conn.transaction():
            # Step 1: re-point all citations
            repointed = 0
            for eng_pid, grc_pid in eng_to_grc.items():
                updated = await conn.execute(
                    "UPDATE free_will.passage_citations SET passage_id = $1::uuid WHERE passage_id = $2::uuid",
                    grc_pid,
                    eng_pid,
                )
                repointed += int(updated.split()[-1])

            # Step 2: verify 0 citations remain on ENG passages
            eng_ids_list = list(eng_to_grc.keys())
            remaining = await conn.fetchval(
                "SELECT COUNT(*) FROM free_will.passage_citations WHERE passage_id = ANY($1::uuid[])",
                eng_ids_list,
            )
            if remaining > 0:
                raise RuntimeError(
                    f"{label}: {remaining} citations still on ENG passages after re-point — rolling back"
                )

            # Step 3: delete ENG passages
            deleted_p = await conn.execute(
                "DELETE FROM free_will.passages WHERE passage_id = ANY($1::uuid[])",
                eng_ids_list,
            )
            n_deleted_p = int(deleted_p.split()[-1])

            # Step 4: delete ENG work row (only if empty)
            remaining_passages = await conn.fetchval(
                "SELECT COUNT(*) FROM free_will.passages WHERE work_id = $1::uuid",
                eng_work_id,
            )
            n_deleted_w = 0
            if remaining_passages == 0:
                await conn.execute(
                    "DELETE FROM free_will.ancient_works WHERE work_id = $1::uuid",
                    eng_work_id,
                )
                n_deleted_w = 1
                print(f"  Deleted ENG work row: {eng_canonical}")
            else:
                print(f"  WARNING: {remaining_passages} passages still in ENG work after delete — work row kept")

        print(f"  Re-pointed: {repointed} citations")
        print(f"  Deleted: {n_deleted_p} ENG passages, {n_deleted_w} ENG work rows")
        return {
            "rehomed": repointed,
            "deleted_passages": n_deleted_p,
            "deleted_works": n_deleted_w,
            "errors": [],
        }
    else:
        print(f"  [DRY-RUN] would re-point {total_cits_to_repoint} citations, delete {len(eng_passages)} passages + work row")
        return {
            "rehomed": total_cits_to_repoint,
            "deleted_passages": len(eng_passages),
            "deleted_works": 1,
            "errors": [],
        }


async def main(commit: bool) -> int:
    import asyncpg

    conn: asyncpg.Connection = await asyncio.wait_for(
        asyncpg.connect(_pg_url(_db_url())), timeout=30
    )
    try:
        print(f"Mode: {'COMMIT' if commit else 'DRY-RUN'}")
        print(f"Timestamp: {datetime.now(UTC).isoformat()}")

        # Process Alexander ENG (no dependency)
        result_alex = await process_rehome(
            conn,
            label="alexander_eng",
            eng_canonical=ALEXANDER_ENG,
            grc_canonical=ALEXANDER_GRC,
            commit=commit,
        )

        # Process Tatian ENG (depends on FIX 2 Tatian dedup)
        # Verify Tatian dedup ran: GRC should have at most 1 passage per cts_urn
        tatian_grc_work_id = await get_work_id(conn, TATIAN_GRC)
        if tatian_grc_work_id:
            dup_check = await conn.fetchval(
                """SELECT COUNT(*) FROM (
                       SELECT cts_urn, COUNT(*) as c
                       FROM free_will.passages WHERE work_id = $1::uuid
                       GROUP BY cts_urn HAVING COUNT(*) > 1
                   ) sub""",
                tatian_grc_work_id,
            )
            if dup_check > 0:
                print(f"\nWARNING: Tatian GRC still has {dup_check} duplicate cts_urn groups.")
                print("  FIX 2 (Tatian dedup) must run before Tatian ENG re-home.")
                print("  Aborting Tatian ENG group — run dedup_tatian_2026_05_25.py --commit first.")
                result_tatian = {
                    "rehomed": 0, "deleted_passages": 0, "deleted_works": 0,
                    "errors": ["Tatian GRC still has duplicates — run FIX 2 first"],
                }
            else:
                result_tatian = await process_rehome(
                    conn,
                    label="tatian_eng",
                    eng_canonical=TATIAN_ENG,
                    grc_canonical=TATIAN_GRC,
                    commit=commit,
                )
        else:
            result_tatian = {
                "rehomed": 0, "deleted_passages": 0, "deleted_works": 0,
                "errors": ["Tatian GRC work not found"],
            }

        print(f"\n{'='*60}")
        print("SUMMARY")
        for label, res in [("alexander_eng", result_alex), ("tatian_eng", result_tatian)]:
            print(
                f"  {label}: re-homed={res['rehomed']} cits, "
                f"deleted={res['deleted_passages']} passages + {res['deleted_works']} work rows"
            )
            if res["errors"]:
                for e in res["errors"]:
                    print(f"    ERROR: {e}")

        if not commit:
            print("\n[DRY-RUN] Pass --commit to execute.")

    finally:
        await conn.close()

    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--commit", action="store_true", help="Write to DB (default: dry-run)")
    args = ap.parse_args()
    sys.exit(asyncio.run(main(args.commit)))
