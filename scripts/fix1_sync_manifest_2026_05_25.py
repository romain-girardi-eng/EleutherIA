"""FIX 1 — Sync data/corpus/manifest.jsonl to live ancient_works.

Changes:
- Remove rows whose canonical_id no longer exists in ancient_works (orphaned rows)
- Replace stale Cicero De Div / De Nat Deorum rows:
    phi042 (Topica/Orator slot) → phi053 (De Divinatione)
    phi041 (Topica/Orator slot) → phi050 (De Natura Deorum)
- Fix Plutarch De Fato row: old tlg099_grc ref → canonical canonical_id urn:cts:greekLit:tlg0007.tlg108
- Fix Sextus PH row: was 'urn_cts_greeklit_tlg0544_grc' → now 'urn_cts_greeklit_tlg0544_tlg001_grc'
- ADD new free-will works now in corpus:
    Plato Phaedo     urn_cts_greeklit_tlg0059_tlg004_grc
    Plato Gorgias    urn_cts_greeklit_tlg0059_tlg023_grc
    Sextus Adv Math  urn_cts_greeklit_tlg0544_tlg002_grc
    Plutarch De Fato urn:cts:greekLit:tlg0007.tlg108
- Refresh passage counts + cts_urns from live DB for all kept rows
- Emit status: in_corpus if passages >= 5, thin_needs_ingestion if < 5
- Output sorted by canonical_id
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import asyncpg
from scripts.corpus_lib import read_jsonl, write_jsonl

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data" / "corpus" / "manifest.jsonl"

DATABASE_URL = (
    "postgresql://postgres.alqwfeddgigzpxrdbdbo:"
    "ANQffBsZ77fq5CsLWwTaBlfa1ke1gTrQ@"
    "aws-0-eu-west-1.pooler.supabase.com:5432/postgres?sslmode=require"
)

# Mapping: old stale canonical_id → correct canonical_id
REMAP = {
    # Cicero: phi041 was Topica/Orator slot, real De Natura Deorum is phi050
    "urn_cts_latinlit_phi0474_phi041_lat": "urn_cts_latinlit_phi0474_phi050_lat",
    # Cicero: phi042 was Topica/Orator slot, real De Divinatione is phi053
    "urn_cts_latinlit_phi0474_phi042_lat": "urn_cts_latinlit_phi0474_phi053_lat",
    # Plutarch De Fato: old non-existent tlg099_grc → real canonical_id
    "urn_cts_greeklit_tlg0007_tlg099_grc": "urn:cts:greekLit:tlg0007.tlg108",
    # Sextus PH: old umbrella canonical_id → proper work canonical_id
    "urn_cts_greeklit_tlg0544_grc": "urn_cts_greeklit_tlg0544_tlg001_grc",
}

# New free-will works to ADD (must exist in ancient_works)
NEW_WORKS = {
    "urn_cts_greeklit_tlg0059_tlg004_grc",
    "urn_cts_greeklit_tlg0059_tlg023_grc",
    "urn_cts_greeklit_tlg0544_tlg002_grc",
    "urn:cts:greekLit:tlg0007.tlg108",
}


async def main() -> None:
    conn = await asyncpg.connect(DATABASE_URL)

    # Fetch all live works + passage counts
    rows = await conn.fetch("""
        SELECT aw.canonical_id, aw.cts_urn, aw.title, aw.author, aw.period,
               COUNT(p.passage_id) AS passages
        FROM free_will.ancient_works aw
        LEFT JOIN free_will.passages p ON p.work_id = aw.work_id
        GROUP BY aw.canonical_id, aw.cts_urn, aw.title, aw.author, aw.period
    """)
    await conn.close()

    live: dict[str, dict] = {}
    for r in rows:
        live[r["canonical_id"]] = {
            "canonical_id": r["canonical_id"],
            "cts_urn": r["cts_urn"] or "",
            "title": r["title"] or "",
            "author": r["author"] or "",
            "period": r["period"] or "",
            "passages": r["passages"],
        }

    old_manifest = read_jsonl(MANIFEST_PATH)
    before_count = len(old_manifest)

    # Apply remap: update old rows to point at correct canonical_id
    remapped_rows: list[dict] = []
    already_have: set[str] = set()
    removed: list[str] = []
    fixed: list[tuple[str, str]] = []

    for row in old_manifest:
        cid = row["canonical_id"]
        if cid in REMAP:
            new_cid = REMAP[cid]
            fixed.append((cid, new_cid))
            cid = new_cid
            row["canonical_id"] = cid

        if cid not in live:
            removed.append(cid)
            continue

        if cid in already_have:
            # Dedup: already added via remap or duplicate
            continue
        already_have.add(cid)
        remapped_rows.append(row)

    # Add new works not yet in manifest
    added: list[str] = []
    for new_cid in NEW_WORKS:
        if new_cid not in already_have:
            if new_cid in live:
                remapped_rows.append({"canonical_id": new_cid})
                already_have.add(new_cid)
                added.append(new_cid)
            else:
                print(f"WARNING: new work {new_cid!r} not in live DB — skipping")

    # Rebuild each row with fresh DB data, preserving manual fields
    manual_field_defaults = {
        "ingest_class": "scaife",
        "source": "",
    }

    def build_row(old_row: dict, db: dict) -> dict:
        passages = db["passages"]
        status = "in_corpus" if passages >= 5 else "thin_needs_ingestion"
        # Preserve manually curated fields if present, otherwise derive
        result = {
            "author": db["author"] or old_row.get("author", ""),
            "canonical_id": db["canonical_id"],
            "cts_urn": db["cts_urn"],
            "ingest_class": old_row.get("ingest_class", manual_field_defaults["ingest_class"]),
            "passages": passages,
            "period": db["period"] or old_row.get("period", ""),
            "source": old_row.get("source", manual_field_defaults["source"]),
            "status": status,
            "title": db["title"] or old_row.get("title", ""),
        }
        return result

    # Build old_row lookup from remapped_rows (keyed by canonical_id)
    old_by_cid: dict[str, dict] = {r["canonical_id"]: r for r in remapped_rows}

    final_rows: list[dict] = []
    for cid in sorted(already_have):
        if cid not in live:
            continue
        old_row = old_by_cid.get(cid, {"canonical_id": cid})
        final_rows.append(build_row(old_row, live[cid]))

    final_rows.sort(key=lambda r: r["canonical_id"])

    write_jsonl(MANIFEST_PATH, final_rows)

    after_count = len(final_rows)
    print(f"\nManifest rebuild complete:")
    print(f"  Before: {before_count} rows")
    print(f"  After:  {after_count} rows")
    print(f"  Removed (canonical_id not in DB): {len(removed)}")
    for r in removed:
        print(f"    - {r!r}")
    print(f"  Fixed (canonical_id remapped): {len(fixed)}")
    for old, new in fixed:
        print(f"    {old!r} -> {new!r}")
    print(f"  Added (new free-will works): {len(added)}")
    for a in added:
        print(f"    + {a!r}")


if __name__ == "__main__":
    asyncio.run(main())
