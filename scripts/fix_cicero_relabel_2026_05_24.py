#!/usr/bin/env python3
"""Relabel Cicero phi041 work to its true identity (Orator, not De Natura Deorum).

Work `urn_cts_latinlit_phi0474_phi041_lat` is titled 'De Natura Deorum' but phi041
is Cicero's *Orator* in the PHI/Perseus classification (phi042 = De Divinatione;
phi041 = Orator). The stored Latin text confirms this: it begins with rhetorical
theory on types of orators, not theology.

Fix (ancient_works title only — canonical_id, work_id, passages, and citations unchanged):
  - title → 'Orator'

Additionally writes data/corpus/REVIEW_cicero_citations.md listing the 22 KG node_ids
that cite this work. These were made believing the text was De Natura Deorum and need
scholarly review.

Note: No actual De Natura Deorum is present in the corpus (acquisition gap).

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
SNAPSHOT_DIR = ROOT / "data" / "corpus" / "fix_snapshots" / "fix_cicero_relabel_2026_05_24"
REVIEW_PATH = ROOT / "data" / "corpus" / "REVIEW_cicero_citations.md"

WORK_CANONICAL_ID = "urn_cts_latinlit_phi0474_phi041_lat"
OLD_TITLE = "De Natura Deorum"
NEW_TITLE = "Orator"


def _db_url() -> str:
    for line in (ROOT / ".env").open():
        if line.startswith("DATABASE_URL="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("DATABASE_URL not found in .env")


async def _collect_kg_nodes(conn) -> list[str]:
    """Return distinct KG node_ids that cite passages of this work."""
    rows = await conn.fetch(
        """
        SELECT DISTINCT pc.kg_node_id
        FROM free_will.passage_citations pc
        JOIN free_will.passages p ON p.passage_id = pc.passage_id
        JOIN free_will.ancient_works w ON w.work_id = p.work_id
        WHERE w.canonical_id = $1
        ORDER BY pc.kg_node_id
        """,
        WORK_CANONICAL_ID,
    )
    return [r["kg_node_id"] for r in rows]


def _write_review_file(node_ids: list[str]) -> None:
    lines = [
        "# Cicero phi041 Citation Review",
        "",
        "## Summary",
        "",
        "Work `urn_cts_latinlit_phi0474_phi041_lat` was stored as *De Natura Deorum*",
        "but the text is actually Cicero's *Orator* (PHI phi041). The title has been",
        "corrected to `Orator`.",
        "",
        "The 22 KG nodes listed below were linked to passages of this work under the",
        "belief that the text was *De Natura Deorum*. Their scholarly claims may be",
        "based on that false identity and require manual review:",
        "",
        "- For each node, verify whether the citation is appropriate for the *Orator*",
        "  (Cicero's treatise on the ideal orator, written 46 BCE).",
        "- If the intended source was *De Natura Deorum* (a different work, absent from",
        "  the corpus — acquisition gap), the citation should be removed or replaced",
        "  once the correct text is ingested.",
        "",
        "## Affected KG node_ids",
        "",
    ]
    for nid in node_ids:
        lines.append(f"- `{nid}`")
    lines += [
        "",
        "## Acquisition gap",
        "",
        "The corpus contains **no** passages of Cicero *De Natura Deorum* (phi045",
        "in PHI/TLG). Ingestion from Perseus `urn:cts:latinLit:phi0474.phi045.perseus-lat1`",
        "or the equivalent would be required before those KG citations can be",
        "properly sourced.",
        "",
    ]
    REVIEW_PATH.parent.mkdir(parents=True, exist_ok=True)
    REVIEW_PATH.write_text("\n".join(lines), encoding="utf-8")


async def main(commit: bool) -> int:
    import asyncpg

    conn = await asyncpg.connect(_db_url())
    try:
        work_row = await conn.fetchrow(
            "SELECT work_id, canonical_id, title FROM free_will.ancient_works WHERE canonical_id = $1",
            WORK_CANONICAL_ID,
        )
        if not work_row:
            print(f"ERROR: work not found: {WORK_CANONICAL_ID}")
            return 1

        current_title = work_row["title"]
        if current_title == NEW_TITLE:
            print(f"Already fixed (title='{NEW_TITLE}'). Nothing to do.")
        else:
            print(
                f"Work: {WORK_CANONICAL_ID}\n"
                f"  Current title: '{current_title}'\n"
                f"  New title:     '{NEW_TITLE}'\n"
            )

        kg_nodes = await _collect_kg_nodes(conn)
        print(f"KG nodes citing this work: {len(kg_nodes)}")
        for nid in kg_nodes:
            print(f"  {nid}")

        # Always write the review file (idempotent)
        _write_review_file(kg_nodes)
        print(f"\nReview file written: {REVIEW_PATH}")

        if current_title == NEW_TITLE:
            return 0

        if not commit:
            print("\n[DRY-RUN] Pass --commit to write changes to ancient_works.")
            return 0

        # Snapshot
        SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        snap = {
            "work_id": str(work_row["work_id"]),
            "canonical_id": work_row["canonical_id"],
            "old_title": current_title,
            "new_title": NEW_TITLE,
            "kg_node_ids": kg_nodes,
        }
        (SNAPSHOT_DIR / "work_before.json").write_text(
            json.dumps(snap, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"Snapshot written: {SNAPSHOT_DIR}/work_before.json")

        now = datetime.now(UTC)
        await conn.execute(
            """
            UPDATE free_will.ancient_works
               SET title      = $1,
                   updated_at = $2
             WHERE canonical_id = $3
            """,
            NEW_TITLE,
            now,
            WORK_CANONICAL_ID,
        )
        print("Updated title in ancient_works. DONE.")

    finally:
        await conn.close()

    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--commit", action="store_true", help="Write changes (default: dry-run)")
    args = ap.parse_args()
    sys.exit(asyncio.run(main(args.commit)))
