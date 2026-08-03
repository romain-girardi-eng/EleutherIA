"""Split the Adversus Mathematicos passages out of the Outlines of Pyrrhonism node.

The PH node (urn_cts_greeklit_tlg0544_tlg001_grc) holds 396 passages that are
actually Adversus Mathematicos (cts_urn -> tlg0544.tlg002, refs 'AM b.s'). Move
them — with their passage-anchor KG nodes — into the AM work node
(urn_cts_greeklit_tlg0544_tlg002_grc), so PH and AM are properly separated.
Citations are preserved (passage_id unchanged). A KG work node for AM is created
if missing and the anchors' part_of edges are retargeted to it.

Note: books 9-10 of the moved set overlap the existing clean per-section AM IX-X
passages (different granularity, both cited) — an accepted minor redundancy.

Dry-run by default; --commit writes. Run from repo root (PYTHONPATH=.).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys

import asyncpg
from dotenv import load_dotenv

SCHEMA = "free_will"
PH_CID = "urn_cts_greeklit_tlg0544_tlg001_grc"
AM_CID = "urn_cts_greeklit_tlg0544_tlg002_grc"
PH_KGWORK = "work_sextus_outlines_pyrrhonism_f9a7c8e4"
AM_KGWORK = "work_sextus_adversus_mathematicos"
PERSON = "person_sextus_empiricus_c160_210ce_d4f8a2b1"


def _db_url() -> str:
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
    url = os.getenv("DATABASE_URL")
    if not url:
        sys.exit("ERROR: DATABASE_URL not set")
    return url.replace("postgresql://", "postgres://")


async def run(commit: bool) -> None:
    conn = await asyncpg.connect(_db_url())
    try:
        ph_wid = await conn.fetchval(
            f"SELECT work_id FROM {SCHEMA}.ancient_works WHERE canonical_id=$1", PH_CID)
        am_wid = await conn.fetchval(
            f"SELECT work_id FROM {SCHEMA}.ancient_works WHERE canonical_id=$1", AM_CID)
        if not am_wid:
            sys.exit("ERROR: AM work node not found")
        move_pids = [r["passage_id"] for r in await conn.fetch(
            f"""SELECT passage_id FROM {SCHEMA}.passages
                WHERE work_id=$1 AND cts_urn LIKE '%tlg0544.tlg002%'""", ph_wid)]
        anchors = [r["kg_node_id"] for r in await conn.fetch(
            f"""SELECT DISTINCT pc.kg_node_id FROM {SCHEMA}.passage_citations pc
                JOIN {SCHEMA}.kg_nodes n ON n.node_id=pc.kg_node_id
                WHERE pc.passage_id = ANY($1::uuid[]) AND n.type='passage'""", move_pids)]
        print(f"move {len(move_pids)} AM passages PH->AM; retarget {len(anchors)} anchors' part_of")
        if not commit:
            print("(dry-run — use --commit to write)")
            return
        async with conn.transaction():
            # AM KG work node (create if missing) + link ancient_works.kg_work_id
            exists = await conn.fetchval(
                f"SELECT 1 FROM {SCHEMA}.kg_nodes WHERE node_id=$1", AM_KGWORK)
            if not exists:
                await conn.execute(
                    f"""INSERT INTO {SCHEMA}.kg_nodes (node_id, label, type, description, metadata)
                        VALUES ($1,$2,'work',$3,$4)""",
                    AM_KGWORK, "Sextus Empiricus, Adversus Mathematicos",
                    "Sextus Empiricus, Adversus Mathematicos (Against the Mathematicians, "
                    "books I-XI incl. Against the Logicians/Physicists/Ethicists).",
                    json.dumps({"author": "Sextus Empiricus",
                                "cts_urn": "urn:cts:greekLit:tlg0544.tlg002"}, ensure_ascii=False))
                await conn.execute(
                    f"""INSERT INTO {SCHEMA}.kg_edges (source_id,target_id,relation,weight)
                        VALUES ($1::text,$2::text,'authored_by',1.0)""",
                    AM_KGWORK, PERSON)
            await conn.execute(
                f"UPDATE {SCHEMA}.ancient_works SET kg_work_id=$2, updated_at=now() WHERE work_id=$1",
                am_wid, AM_KGWORK)
            # move passages
            await conn.execute(
                f"UPDATE {SCHEMA}.passages SET work_id=$2 WHERE passage_id = ANY($1::uuid[])",
                move_pids, am_wid)
            # retarget anchors' part_of edge PH-kgwork -> AM-kgwork
            await conn.execute(
                f"""UPDATE {SCHEMA}.kg_edges SET target_id=$2
                    WHERE source_id = ANY($1::text[]) AND relation='part_of' AND target_id=$3""",
                anchors, AM_KGWORK, PH_KGWORK)
            # broaden AM node title (now spans I-XI, not just IX-X)
            await conn.execute(
                f"""UPDATE {SCHEMA}.ancient_works
                    SET title='Adversus Mathematicos (Against the Mathematicians, I-XI)',
                        total_divisions=(SELECT count(*) FROM {SCHEMA}.passages WHERE work_id=$1),
                        updated_at=now()
                    WHERE work_id=$1""", am_wid)
            # refresh PH node division count
            await conn.execute(
                f"""UPDATE {SCHEMA}.ancient_works
                    SET total_divisions=(SELECT count(*) FROM {SCHEMA}.passages WHERE work_id=$1),
                        updated_at=now() WHERE work_id=$1""", ph_wid)
        print(f"COMMITTED: moved {len(move_pids)} passages, retargeted {len(anchors)} anchors, "
              f"AM kg work node ensured, titles updated")
    finally:
        await conn.close()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--commit", action="store_true")
    asyncio.run(run(ap.parse_args().commit))


if __name__ == "__main__":
    main()
