"""Clean re-ingest of selected sections of a work as per-section passages.

Replaces a work's messy/mislabelled passages with genuine per-section text from
the authoritative TEI, for a chosen list of canonical section refs (lean: only
the free-will-relevant chapters). Regenerates the 1:1 passage-anchor KG nodes and
their authored_by/part_of edges and stub citations. SUBSTANTIVE citations (from
concept/synthesis/person/school nodes, i.e. non-passage citers) are reported for
manual remapping — they are deleted here (passage FK) and must be re-created
pointing at the new passages.

Config is passed as a JSON file: {canonical_id, tei_urn, level, refs[],
anchor_prefix, kg_work_id, person_id, abbrev}. Dry-run by default; --commit writes.
Run from repo root (PYTHONPATH=.).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys

import asyncpg
from dotenv import load_dotenv

from scripts.corpus_github_fetch import fetch_work_xml, parse_passages

SCHEMA = "free_will"


def _db_url() -> str:
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
    url = os.getenv("DATABASE_URL")
    if not url:
        sys.exit("ERROR: DATABASE_URL not set")
    return url.replace("postgresql://", "postgres://")


async def run(cfg: dict, commit: bool) -> None:
    tei_urn = cfg["tei_urn"]
    want = list(dict.fromkeys(cfg["refs"]))
    xb = fetch_work_xml(tei_urn)
    leaves = {p["cts_urn"].rsplit(":", 1)[1]: p["text_content"]
              for p in parse_passages(xb, tei_urn, level=cfg["level"])}
    selected = [(r, leaves[r]) for r in want if r in leaves]
    missing = [r for r in want if r not in leaves]
    if missing:
        print(f"WARNING: refs not found in TEI: {missing}")
    if not selected:
        sys.exit("ERROR: no selected sections found in TEI")

    conn = await asyncpg.connect(_db_url())
    try:
        work_id = await conn.fetchval(
            f"SELECT work_id FROM {SCHEMA}.ancient_works WHERE canonical_id=$1",
            cfg["canonical_id"])
        old_pids = [r["passage_id"] for r in await conn.fetch(
            f"SELECT passage_id FROM {SCHEMA}.passages WHERE work_id=$1", work_id)]
        # old anchor nodes = type='passage' nodes part_of this kg work
        old_anchors = [r["source_id"] for r in await conn.fetch(
            f"""SELECT e.source_id FROM {SCHEMA}.kg_edges e JOIN {SCHEMA}.kg_nodes n
                ON n.node_id=e.source_id
                WHERE e.relation='part_of' AND e.target_id=$1 AND n.type='passage'""",
            cfg["kg_work_id"])]
        # substantive citations (non-passage citers) on old passages -> must remap
        subst = await conn.fetch(
            f"""SELECT pc.kg_node_id, n.type, pc.citation_type, pc.confidence, pc.notes,
                       left(p.text_content, 60) AS old_text, p.canonical_ref AS old_ref
                FROM {SCHEMA}.passage_citations pc
                JOIN {SCHEMA}.kg_nodes n ON n.node_id=pc.kg_node_id
                JOIN {SCHEMA}.passages p ON p.passage_id=pc.passage_id
                WHERE pc.passage_id = ANY($1::uuid[]) AND n.type <> 'passage'""", old_pids)

        print(f"work={cfg['canonical_id']} work_id={work_id}")
        print(f"selected {len(selected)} sections: {[r for r, _ in selected]}")
        print(f"delete {len(old_pids)} old passages, {len(old_anchors)} old anchors")
        print(f"SUBSTANTIVE citations to remap manually: {len(subst)}")
        for s in subst:
            print(f"   {s['kg_node_id']} ({s['type']}) cited old {s['old_ref']!r}")
        if not commit:
            print("\n(dry-run — use --commit to write)")
            return

        async with conn.transaction():
            await conn.execute(
                f"DELETE FROM {SCHEMA}.passage_citations WHERE passage_id = ANY($1::uuid[])",
                old_pids)
            await conn.execute(
                f"DELETE FROM {SCHEMA}.passages WHERE passage_id = ANY($1::uuid[])", old_pids)
            if old_anchors:
                await conn.execute(
                    f"""DELETE FROM {SCHEMA}.kg_edges
                        WHERE source_id = ANY($1::text[]) OR target_id = ANY($1::text[])""",
                    old_anchors)
                await conn.execute(
                    f"DELETE FROM {SCHEMA}.kg_nodes WHERE node_id = ANY($1::text[])", old_anchors)

            for i, (ref, txt) in enumerate(selected, 1):
                cref = f"{cfg['abbrev']} {ref}"
                urn = f"{tei_urn}:{ref}"
                anchor = f"{cfg['anchor_prefix']}{ref.replace('.', '_')}"
                pid = await conn.fetchval(
                    f"""INSERT INTO {SCHEMA}.passages
                        (work_id, canonical_ref, cts_urn, sequence_number, text_content,
                         passage_role, char_length, word_count)
                        VALUES ($1,$2,$3,$4,$5,'original',$6,$7) RETURNING passage_id""",
                    work_id, cref, urn, i, txt, len(txt), len(txt.split()))
                await conn.execute(
                    f"""INSERT INTO {SCHEMA}.kg_nodes (node_id, id, label, type, description, metadata)
                        VALUES ($1,$1,$2,'passage',$3,$4)""",
                    anchor, f"{cfg['label_prefix']}, {cref}", txt,
                    json.dumps({"cts_urn": urn, "author": cfg["author_name"]}, ensure_ascii=False))
                await conn.executemany(
                    f"INSERT INTO {SCHEMA}.kg_edges (source_id, target_id, source, target, relation, weight) VALUES ($1,$2,$1,$2,$3,1.0)",
                    [(anchor, cfg["person_id"], "authored_by"),
                     (anchor, cfg["kg_work_id"], "part_of")])
                await conn.execute(
                    f"""INSERT INTO {SCHEMA}.passage_citations (passage_id, kg_node_id, citation_type, confidence)
                        VALUES ($1,$2,'direct_quote',1.0)""", pid, anchor)
            await conn.execute(
                f"""UPDATE {SCHEMA}.ancient_works SET cts_urn=$2, total_divisions=$3, updated_at=now()
                    WHERE work_id=$1""", work_id, tei_urn, len(selected))
        print(f"\nCOMMITTED: {len(selected)} sections ingested; "
              f"{len(old_pids)} old passages + {len(old_anchors)} anchors removed")
        if subst:
            print("REMAP NEEDED for substantive citers (re-link to new passages):")
            for s in subst:
                print(f"   {s['kg_node_id']}")
    finally:
        await conn.close()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", required=True, help="JSON config file")
    ap.add_argument("--commit", action="store_true")
    args = ap.parse_args()
    with open(args.config, encoding="utf-8") as fh:
        cfg = json.load(fh)
    asyncio.run(run(cfg, args.commit))


if __name__ == "__main__":
    main()
