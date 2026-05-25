"""Fix the De Generatione et Corruptione misattribution.

The work `urn_cts_greeklit_tlg0086_tlg003_grc` (titled Aristotle, De Gen. et
Corr.) actually held the Constitution of Athens (tlg0086.tlg003). This replaces
its content with the genuine De Generatione et Corruptione (tlg0086.tlg013),
keeping only the free-will-relevant Book II chapters 9–11 (the necessity / cyclical
coming-to-be argument), matching the lean-corpus principle.

Strategy (Supabase = source of truth; passage_id reuse where possible):
  - Repurpose the 3 lowest-sequence passages + their KG anchors (passage_arist_
    gen_corr_1..3) -> DGC II.9, II.10, II.11 (text/ref/urn + anchor label/desc).
  - Delete the other 66 passages, their citations, KG anchors, and anchor edges.
  - Update the ancient_works row's cts_urn/tlg_code/divisions (title already
    correct).
The KG work node `work_de_gen_corr_aristotle` and the 3 kept anchors' authored_by/
part_of edges remain valid.

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

from scripts.corpus_github_fetch import fetch_work_xml, parse_passages

SCHEMA = "free_will"
OLD_CID = "urn_cts_greeklit_tlg0086_tlg003_grc"
DGC_URN = "urn:cts:greekLit:tlg0086.tlg013.1st1K-grc1"
KEEP = ["2.9", "2.10", "2.11"]
CH_LABEL = {"2.9": "II.9", "2.10": "II.10", "2.11": "II.11"}


def _db_url() -> str:
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
    url = os.getenv("DATABASE_URL")
    if not url:
        sys.exit("ERROR: DATABASE_URL not set")
    return url.replace("postgresql://", "postgres://")


async def run(commit: bool) -> None:
    xb = fetch_work_xml(DGC_URN)
    leaves = {p["cts_urn"].rsplit(":", 1)[1]: p["text_content"]
              for p in parse_passages(xb, DGC_URN, level=2)}
    dgc = [(r, leaves[r]) for r in KEEP if r in leaves]
    if len(dgc) != 3:
        sys.exit(f"ERROR: expected 3 DGC sections, got {len(dgc)}")

    conn = await asyncpg.connect(_db_url())
    try:
        work_id = await conn.fetchval(
            f"SELECT work_id FROM {SCHEMA}.ancient_works WHERE canonical_id=$1", OLD_CID)
        prows = await conn.fetch(
            f"""SELECT passage_id, sequence_number FROM {SCHEMA}.passages
                WHERE work_id=$1 ORDER BY sequence_number""", work_id)
        keep_pids = [r["passage_id"] for r in prows[:3]]
        drop_pids = [r["passage_id"] for r in prows[3:]]
        keep_anchors = [f"passage_arist_gen_corr_{i}" for i in (1, 2, 3)]
        drop_anchors = await conn.fetch(
            f"""SELECT node_id FROM {SCHEMA}.kg_nodes
                WHERE node_id LIKE 'passage_arist_gen_corr_%'
                  AND node_id NOT IN ($1,$2,$3)""", *keep_anchors)
        drop_anchor_ids = [r["node_id"] for r in drop_anchors]

        print(f"work_id={work_id}")
        print(f"passages: keep {len(keep_pids)} (-> DGC II.9-11), delete {len(drop_pids)}")
        print(f"kg anchors: keep {keep_anchors}, delete {len(drop_anchor_ids)}")
        for (ref, txt), pid, anc in zip(dgc, keep_pids, keep_anchors):
            print(f"  {anc} / {str(pid)[:8]} -> De Gen. et Corr. {CH_LABEL[ref]} "
                  f"({len(txt)} chars): {txt[:55]}")

        if not commit:
            print("\n(dry-run — use --commit to write)")
            return

        async with conn.transaction():
            # 1. repurpose the 3 kept passages + anchors
            for (ref, txt), pid, anc in zip(dgc, keep_pids, keep_anchors):
                cref = f"De Gen. et Corr. {CH_LABEL[ref]}"
                urn = f"{DGC_URN}:{ref}"
                await conn.execute(
                    f"""UPDATE {SCHEMA}.passages SET text_content=$2, canonical_ref=$3,
                        cts_urn=$4, char_length=$5, word_count=$6 WHERE passage_id=$1""",
                    pid, txt, cref, urn, len(txt), len(txt.split()))
                meta = await conn.fetchval(
                    f"SELECT metadata FROM {SCHEMA}.kg_nodes WHERE node_id=$1", anc)
                m = json.loads(meta) if isinstance(meta, str) else (meta or {})
                m["cts_urn"] = urn
                await conn.execute(
                    f"""UPDATE {SCHEMA}.kg_nodes
                        SET label=$2, description=$3, metadata=$4, updated_at=now()
                        WHERE node_id=$1""",
                    anc, f"Aristotle, De Generatione et Corruptione, {cref}",
                    txt, json.dumps(m, ensure_ascii=False))
            # 2. delete the 66 passages' citations + passages
            await conn.execute(
                f"DELETE FROM {SCHEMA}.passage_citations WHERE passage_id = ANY($1::uuid[])",
                drop_pids)
            await conn.execute(
                f"DELETE FROM {SCHEMA}.passages WHERE passage_id = ANY($1::uuid[])", drop_pids)
            # 3. delete the 66 anchor nodes + their edges
            await conn.execute(
                f"""DELETE FROM {SCHEMA}.kg_edges
                    WHERE source_id = ANY($1::text[]) OR target_id = ANY($1::text[])""",
                drop_anchor_ids)
            await conn.execute(
                f"DELETE FROM {SCHEMA}.kg_nodes WHERE node_id = ANY($1::text[])", drop_anchor_ids)
            # 4. update the work row to the genuine DGC edition
            await conn.execute(
                f"""UPDATE {SCHEMA}.ancient_works
                    SET cts_urn=$2, tlg_code='tlg0086.tlg013', total_divisions=3,
                        updated_at=now()
                    WHERE work_id=$1""", work_id, DGC_URN)
        print(f"\nCOMMITTED: 3 passages/anchors repurposed, {len(drop_pids)} passages + "
              f"{len(drop_anchor_ids)} anchors deleted")
    finally:
        await conn.close()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--commit", action="store_true")
    asyncio.run(run(ap.parse_args().commit))


if __name__ == "__main__":
    main()
