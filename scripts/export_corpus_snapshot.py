"""Export Supabase corpus (passages + passage_citations) to git-tracked JSONL.

The durable, copyright-safe backup of the corpus text (ancient text only — the
passages table holds no apparatus/commentary). Deterministic sorted output so
git diffs are a clean time-series. Reads DATABASE_URL from .env.

Usage:  .venv/bin/python -m scripts.export_corpus_snapshot
"""
from __future__ import annotations

import asyncio
from pathlib import Path

from scripts.corpus_lib import write_jsonl

ROOT = Path(__file__).resolve().parents[1]
PASSAGES_PATH = ROOT / "data" / "corpus" / "passages.jsonl"
CITATIONS_PATH = ROOT / "data" / "corpus" / "citations.jsonl"

PASSAGE_SQL = """
SELECT p.passage_id::text AS passage_id,
       w.canonical_id     AS work_canonical_id,
       p.cts_urn, p.canonical_ref, p.sequence_number, p.text_content
FROM free_will.passages p
JOIN free_will.ancient_works w ON w.work_id = p.work_id
"""
CITATION_SQL = """
SELECT passage_id::text AS passage_id, kg_node_id, citation_type, confidence
FROM free_will.passage_citations
"""


def _db_url() -> str:
    for line in open(ROOT / ".env"):
        if line.startswith("DATABASE_URL="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("DATABASE_URL not found in .env")


async def main() -> int:
    import asyncpg

    conn = await asyncio.wait_for(asyncpg.connect(_db_url()), timeout=30)
    try:
        passages = [dict(r) for r in await conn.fetch(PASSAGE_SQL)]
        citations = [dict(r) for r in await conn.fetch(CITATION_SQL)]
    finally:
        await conn.close()

    passages.sort(key=lambda r: (r["work_canonical_id"] or "", r["sequence_number"] or 0, r["passage_id"]))
    citations.sort(key=lambda r: (r["passage_id"], r["kg_node_id"], r.get("citation_type") or ""))

    write_jsonl(PASSAGES_PATH, passages)
    write_jsonl(CITATIONS_PATH, citations)
    print(f"wrote {len(passages)} passages -> {PASSAGES_PATH}")
    print(f"wrote {len(citations)} citations -> {CITATIONS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
