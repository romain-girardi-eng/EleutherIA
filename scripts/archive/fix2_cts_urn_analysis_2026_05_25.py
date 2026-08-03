"""FIX 2 analysis: Plotinus and Boethius cts_urn degradation.

Dry-run: shows what the rebuilt cts_urns would look like, detects collisions.
Plotinus: canonical_ref 'Enn. VI.8.1' → new cts_urn tail '6.8.1' (standard CTS numeric)
Boethius: canonical_ref 'Cons. N' is flat sequential — no structure to rebuild from.
"""
from __future__ import annotations

import asyncio
import asyncpg
import os
import re
import sys
from pathlib import Path


def dsn() -> str:
    """Read the Postgres DSN from the environment; no hardcoded fallback."""
    value = os.environ.get("DATABASE_URL", "").strip()
    if not value:
        raise RuntimeError(
            "DATABASE_URL is not set. Export the Postgres DSN before running "
            "this script."
        )
    return value

PLOTINUS_CANONICAL_ID = "urn_cts_greeklit_tlg2000_tlg001_grc"
PLOTINUS_WORK_URN_BASE = "urn:cts:greekLit:tlg2000.tlg001.perseus-grc1"

BOETHIUS_CANONICAL_IDS = [
    "urn_cts_latinlit_phi2089_phi002_eng",
    "urn_cts_latinlit_phi2089_phi002_lat",
]
BOETHIUS_WORK_URN_BASE_ENG = "urn:cts:latinLit:lat7127.011.perseus-lat1"
BOETHIUS_WORK_URN_BASE_LAT = "urn:cts:latinLit:lat7127.011.perseus-lat1"

# Roman numeral → int mapping for Ennead refs
ROMAN = {
    "I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6,
}


def enn_ref_to_numeric_tail(canonical_ref: str) -> str | None:
    """Convert 'Enn. VI.8.1' → '6.8.1' (numeric CTS ref tail).
    Returns None if the ref cannot be parsed.
    """
    m = re.match(r"^Enn\.\s+([IVX]+)\.(\d+)\.(\d+)$", canonical_ref)
    if not m:
        return None
    roman, tractate, section = m.group(1), m.group(2), m.group(3)
    if roman not in ROMAN:
        return None
    return f"{ROMAN[roman]}.{tractate}.{section}"


async def analyse_plotinus(conn: asyncpg.Connection, dry_run: bool = True) -> tuple[int, int, list[tuple]]:
    """Returns (total, collisions, [(passage_id, old_cts_urn, new_cts_urn), ...])"""
    work_id = await conn.fetchval(
        "SELECT work_id FROM free_will.ancient_works WHERE canonical_id = $1",
        PLOTINUS_CANONICAL_ID,
    )
    if not work_id:
        print("ERROR: Plotinus work not found in DB")
        return 0, 0, []

    rows = await conn.fetch(
        "SELECT passage_id, cts_urn, canonical_ref FROM free_will.passages "
        "WHERE work_id = $1 ORDER BY sequence_number",
        work_id,
    )

    seen_new_urns: dict[str, str] = {}
    updates: list[tuple] = []
    collisions: list[str] = []
    skipped_no_structure = 0

    for r in rows:
        old_cts = r["cts_urn"] or ""
        cref = r["canonical_ref"] or ""

        numeric_tail = enn_ref_to_numeric_tail(cref)
        if numeric_tail is None:
            skipped_no_structure += 1
            continue

        new_cts = f"{PLOTINUS_WORK_URN_BASE}:{numeric_tail}"

        pid = str(r["passage_id"])
        if new_cts in seen_new_urns:
            collisions.append(new_cts)
            continue
        seen_new_urns[new_cts] = pid

        if old_cts != new_cts:
            updates.append((pid, old_cts, new_cts))

    print(f"\n=== PLOTINUS DRY-RUN ===")
    print(f"Total passages: {len(rows)}")
    print(f"Skipped (no structured ref): {skipped_no_structure}")
    print(f"Collisions (skipped): {len(collisions)}")
    if collisions:
        for c in collisions[:5]:
            print(f"  COLLISION: {c}")
    print(f"Would update: {len(updates)}")
    print("Sample updates (first 5):")
    for pid, old, new in updates[:5]:
        print(f"  {pid[:8]}... | OLD: {old!r} | NEW: {new!r}")

    return len(updates), len(collisions), updates


async def analyse_boethius(conn: asyncpg.Connection) -> tuple[int, list[tuple]]:
    """Boethius: section column = global passage index = CTS passage number.
    Rebuild cts_urn = base_urn + ':' + section for both eng and lat variants.
    Returns (update_count, [(passage_id, old_cts_urn, new_cts_urn), ...])
    """
    all_updates: list[tuple] = []
    for cid in BOETHIUS_CANONICAL_IDS:
        base_urn = BOETHIUS_WORK_URN_BASE_ENG  # same for both
        work_id = await conn.fetchval(
            "SELECT work_id FROM free_will.ancient_works WHERE canonical_id = $1",
            cid,
        )
        if not work_id:
            print(f"WARNING: {cid} not found")
            continue

        rows = await conn.fetch(
            "SELECT passage_id, cts_urn, canonical_ref, section "
            "FROM free_will.passages WHERE work_id = $1 ORDER BY sequence_number",
            work_id,
        )

        total = len(rows)
        print(f"\n=== BOETHIUS ({cid}) ===")
        print(f"Total passages: {total}")

        # section IS the passage index — use it as the CTS tail
        seen_new: dict[str, str] = {}
        collisions = 0
        updates_this: list[tuple] = []
        for r in rows:
            section = r["section"]
            if not section:
                print(f"  SKIP: passage {r['passage_id']} has no section")
                continue
            new_cts = f"{base_urn}:{section}"
            old_cts = r["cts_urn"] or ""
            pid = str(r["passage_id"])
            if new_cts in seen_new:
                collisions += 1
                print(f"  COLLISION: {new_cts}")
                continue
            seen_new[new_cts] = pid
            if old_cts != new_cts:
                updates_this.append((pid, old_cts, new_cts))

        print(f"  Would update: {len(updates_this)}, collisions: {collisions}")
        print("  Sample (first 3):")
        for pid, old, new in updates_this[:3]:
            print(f"    {pid[:8]}... OLD={old!r} -> NEW={new!r}")
        all_updates.extend(updates_this)

    return len(all_updates), all_updates


async def apply_boethius_updates(conn: asyncpg.Connection, updates: list[tuple]) -> int:
    """Apply Boethius cts_urn updates."""
    count = 0
    async with conn.transaction():
        for pid, old_cts, new_cts in updates:
            await conn.execute(
                "UPDATE free_will.passages SET cts_urn = $1 WHERE passage_id = $2::uuid",
                new_cts,
                pid,
            )
            count += 1
    return count


async def apply_plotinus_updates(conn: asyncpg.Connection, updates: list[tuple]) -> int:
    """Actually apply Plotinus cts_urn updates. Returns count applied."""
    count = 0
    async with conn.transaction():
        for pid, old_cts, new_cts in updates:
            await conn.execute(
                "UPDATE free_will.passages SET cts_urn = $1 WHERE passage_id = $2::uuid",
                new_cts,
                pid,
            )
            count += 1
    return count


async def main() -> None:
    conn = await asyncpg.connect(dsn())

    # Analysis phase
    plotinus_count, collision_count, plotinus_updates = await analyse_plotinus(conn, dry_run=True)
    boethius_count, boethius_updates = await analyse_boethius(conn)

    total_updates = plotinus_count + boethius_count
    print(f"\nTotal would-update: {total_updates} (Plotinus={plotinus_count}, Boethius={boethius_count})")
    print(f"Total collisions skipped: {collision_count}")

    if "--apply" in sys.argv and total_updates > 0:
        print(f"\nApplying {plotinus_count} Plotinus cts_urn updates...")
        applied_p = await apply_plotinus_updates(conn, plotinus_updates)
        print(f"Plotinus applied: {applied_p}")

        print(f"Applying {boethius_count} Boethius cts_urn updates...")
        applied_b = await apply_boethius_updates(conn, boethius_updates)
        print(f"Boethius applied: {applied_b}")

        print(f"\nTotal applied: {applied_p + applied_b}")
    else:
        if total_updates > 0:
            print(f"\nDRY-RUN COMPLETE. Pass --apply to write {total_updates} updates.")

    await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
