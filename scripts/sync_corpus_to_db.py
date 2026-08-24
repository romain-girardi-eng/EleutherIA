#!/usr/bin/env python3
"""Legacy direct corpus sync plus reusable corpus loading helpers.

The mirror (data/corpus/passages.jsonl + citations.jsonl + manifest.jsonl) is
canonical after the 2026-06 audit campaigns; the DB corpus was a partial
derivation from KG passage nodes. The direct ``--commit`` CLI retains its
historical split transactions and must not be used on a serving database.
``scripts/deploy_data_staged.py`` reuses the payload/import functions below and
publishes the complete KG+corpus generation atomically.

Usage:
  set -a; source .env; set +a
  .venv/bin/python scripts/sync_corpus_to_db.py            # dry run (counts)
  .venv/bin/python scripts/sync_corpus_to_db.py --commit
"""

import argparse
import asyncio
import hashlib
import json
import os
import re
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database.scripts.bootstrap_supabase import ImportTables  # noqa: E402

GREEK = re.compile(r"[Ͱ-Ͽἀ-῿]")
NONSERVABLE_PASSAGE_ROLE = "unresolved_english_research_record"
NONSERVABLE_PASSAGE_CONTRACT = {
    "citability": "discoverable_only",
    "identity_status": "source_identity_unresolved",
    "language": "eng",
}


def p(*a):
    return str(ROOT.joinpath(*a))


def loadl(path):
    with open(p(path)) as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def infer_language(wcid: str, sample_text: str) -> str:
    if wcid.endswith("_eng"):
        return "eng"
    if wcid.endswith("_lat") or "latinlit" in wcid:
        return "lat"
    if GREEK.search(sample_text or ""):
        return "grc"
    return "lat"


def work_uuid(canonical_id: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"eleutheria:work:{canonical_id}"))


@dataclass(frozen=True)
class CorpusPayload:
    works: list[tuple[Any, ...]]
    passages: list[tuple[Any, ...]]
    citations: list[tuple[Any, ...]]
    source_counts: dict[str, int]
    excluded_nonservable: dict[str, Any]


def _is_explicitly_nonservable(row: dict[str, Any]) -> bool:
    citable_as_primary = row.get("citable_as_primary")
    return (
        row.get("passage_role") == NONSERVABLE_PASSAGE_ROLE
        and all(row.get(field) == value for field, value in NONSERVABLE_PASSAGE_CONTRACT.items())
        and (citable_as_primary is None or citable_as_primary is False)
        and row.get("source_passage_id") in (None, "")
        and isinstance(row.get("manifestation_id"), str)
        and bool(row["manifestation_id"].strip())
    )


def _cohort_sha256(values: list[str]) -> str:
    canonical = "\n".join(sorted(values)).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def load_corpus_payload(data_root: Path | None = None) -> CorpusPayload:
    root = (data_root or ROOT / "data").resolve()

    def rows(relative: str) -> list[dict[str, Any]]:
        with (root / relative).open(encoding="utf-8") as handle:
            return [json.loads(line) for line in handle if line.strip()]

    manifest_rows = rows("corpus/manifest.jsonl")
    passage_rows = rows("corpus/passages.jsonl")
    citation_rows = rows("corpus/citations.jsonl")
    manifest = {m["canonical_id"]: m for m in manifest_rows}

    nonservable_candidates = [
        row for row in passage_rows if row.get("passage_role") == NONSERVABLE_PASSAGE_ROLE
    ]
    malformed_nonservable = [
        row for row in nonservable_candidates if not _is_explicitly_nonservable(row)
    ]
    if malformed_nonservable:
        bad_ids = ", ".join(str(row.get("passage_id")) for row in malformed_nonservable[:5])
        raise ValueError(
            f"{NONSERVABLE_PASSAGE_ROLE!r} rows must satisfy the complete "
            f"discoverable-only unresolved-source contract: {bad_ids}"
        )
    excluded_passage_ids = {
        str(row["passage_id"]) for row in nonservable_candidates
    }
    servable_passage_rows = [
        row for row in passage_rows if str(row.get("passage_id")) not in excluded_passage_ids
    ]
    servable_source_ids = {
        str(row.get("source_passage_id"))
        for row in servable_passage_rows
        if row.get("source_passage_id")
    }
    invalid_source_links = sorted(servable_source_ids & excluded_passage_ids)
    if invalid_source_links:
        raise ValueError(
            "servable passages cannot reference excluded nonservable sources: "
            + ", ".join(invalid_source_links[:5])
        )

    works: dict[str, dict[str, Any]] = {}
    for row in servable_passage_rows:
        wcid = row.get("work_canonical_id") or "unknown_work"
        if wcid not in works:
            man = manifest.get(wcid, {})
            works[wcid] = {
                "work_id": work_uuid(wcid),
                "canonical_id": wcid,
                "title": man.get("title") or wcid,
                "author": man.get("author") or "Unknown",
                "language": infer_language(wcid, row.get("text_content") or ""),
                "period": man.get("period"),
                "source": man.get("source"),
                "cts_urn": (man.get("cts_urn") or None) or None,
                "n": 0,
            }
        works[wcid]["n"] += 1

    passage_ids = {row["passage_id"] for row in servable_passage_rows}
    excluded_citation_rows = [
        citation
        for citation in citation_rows
        if str(citation.get("passage_id")) in excluded_passage_ids
    ]
    kept_citations = [
        citation
        for citation in citation_rows
        if citation.get("passage_id") in passage_ids
    ]
    db_passages = []
    for index, row in enumerate(servable_passage_rows):
        text = row.get("text_content") or ""
        sequence = row.get("sequence_number")
        try:
            sequence = int(sequence)
        except (TypeError, ValueError):
            sequence = index + 1
        urn = row.get("cts_urn")
        if urn in ("None", "null", ""):
            urn = None
        passage_role = str(row.get("passage_role") or "original")
        if passage_role not in {"original", "translation", "paraphrase"}:
            raise ValueError(
                f"invalid passage_role={passage_role!r} for {row['passage_id']}"
            )
        db_passages.append(
            (
                row["passage_id"],
                works[row.get("work_canonical_id") or "unknown_work"]["work_id"],
                row.get("canonical_ref") or f"#{sequence}",
                urn,
                sequence,
                text,
                len(text),
                len(text.split()),
                passage_role,
                row.get("source_passage_id") or None,
            )
        )
    # Self-referential translation FKs are immediate in the canonical schema:
    # originals must be inserted before rows that point to them.
    db_passages.sort(key=lambda row: row[9] is not None)

    db_citations = []
    seen = set()
    for citation in kept_citations:
        key = (
            citation["passage_id"],
            citation.get("kg_node_id"),
            citation.get("citation_type"),
        )
        if key in seen:
            continue
        seen.add(key)
        confidence = citation.get("confidence")
        try:
            confidence = float(confidence) if confidence is not None else None
        except (TypeError, ValueError):
            confidence = None
        db_citations.append(
            (
                str(
                    uuid.uuid5(
                        uuid.NAMESPACE_URL,
                        f"eleutheria:cit:{key[0]}:{key[1]}:{key[2]}",
                    )
                ),
                citation["passage_id"],
                citation.get("kg_node_id"),
                citation.get("citation_type"),
                confidence,
                citation.get("notes"),
            )
        )

    return CorpusPayload(
        works=[
            (
                work["work_id"],
                work["canonical_id"],
                work["title"],
                work["author"],
                work["language"],
                work["period"],
                work["source"],
                work["cts_urn"],
                work["n"],
            )
            for work in works.values()
        ],
        passages=db_passages,
        citations=db_citations,
        source_counts={
            "ancient_works": len(manifest_rows),
            "passages": len(passage_rows),
            "passage_citations": len(citation_rows),
            "servable_passages": len(servable_passage_rows),
            "servable_passage_citations": len(kept_citations),
            "linkable_passage_citations": len(kept_citations),
        },
        excluded_nonservable={
            "contract": {
                "passage_role": NONSERVABLE_PASSAGE_ROLE,
                **NONSERVABLE_PASSAGE_CONTRACT,
                "citable_as_primary": "absent_or_false",
                "source_passage_id": "absent_or_empty",
            },
            "passages": {
                "count": len(excluded_passage_ids),
                "passage_ids_sha256": _cohort_sha256(list(excluded_passage_ids)),
            },
            "passage_citations": {
                "count": len(excluded_citation_rows),
                "citation_keys_sha256": _cohort_sha256(
                    [
                        "\0".join(
                            (
                                str(row.get("passage_id") or ""),
                                str(row.get("kg_node_id") or ""),
                                str(row.get("citation_type") or ""),
                            )
                        )
                        for row in excluded_citation_rows
                    ]
                ),
            },
        },
    )


async def import_corpus_payload(
    conn: Any,
    payload: CorpusPayload,
    *,
    tables: ImportTables | None = None,
    replace_data: bool = True,
    batch_size: int = 500,
) -> None:
    target = tables or ImportTables()
    if replace_data:
        await conn.execute(
            f"TRUNCATE {target.passage_citations}, {target.passages}, "
            f"{target.ancient_works} CASCADE"
        )

    await conn.executemany(
        f"""INSERT INTO {target.ancient_works}
           (work_id, canonical_id, title, author, language, period,
            source, cts_urn, total_divisions)
           VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
           ON CONFLICT (work_id) DO NOTHING""",
        payload.works,
    )
    for offset in range(0, len(payload.passages), batch_size):
        await conn.executemany(
            f"""INSERT INTO {target.passages}
               (passage_id, work_id, canonical_ref, cts_urn,
                sequence_number, text_content, char_length, word_count,
                passage_role, source_passage_id)
               VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
               ON CONFLICT (passage_id) DO NOTHING""",
            payload.passages[offset : offset + batch_size],
        )
        if offset % 5000 == 0:
            loaded = offset + min(batch_size, len(payload.passages) - offset)
            print(f"passages {loaded}/{len(payload.passages)}", flush=True)
    for offset in range(0, len(payload.citations), batch_size):
        await conn.executemany(
            f"""INSERT INTO {target.passage_citations}
               (citation_id, passage_id, kg_node_id, citation_type,
                confidence, notes)
               VALUES ($1,$2,$3,$4,$5,$6)
               ON CONFLICT (citation_id) DO NOTHING""",
            payload.citations[offset : offset + batch_size],
        )


async def main(commit: bool, resume: bool = False):
    import asyncpg

    url = os.environ.get("DATABASE_URL")
    if not url:
        raise SystemExit("DATABASE_URL not set (set -a; source .env; set +a)")

    payload = load_corpus_payload()
    print(
        f"mirror: works={len(payload.works)} passages={len(payload.passages)} "
        f"citations={payload.source_counts['passage_citations']} "
        f"(linkable {payload.source_counts['linkable_passage_citations']})"
    )
    if not commit:
        print("dry run — pass --commit to apply")
        return

    conn = await asyncio.wait_for(asyncpg.connect(url), timeout=30)
    try:
        existing = await conn.fetchval("select count(*) from free_will.passages")
        if not resume:
            # TRUNCATE in its own transaction so space is reclaimed before
            # the bulk load (a single transaction doubles storage and can
            # fill the project disk).
            replace_data = True
        else:
            print(
                f"resume mode: {existing} passages already present, "
                "ON CONFLICT DO NOTHING"
            )
            replace_data = False

        await import_corpus_payload(
            conn,
            payload,
            replace_data=replace_data,
        )
        for t in ("ancient_works", "passages", "passage_citations"):
            print(t, await conn.fetchval(f"select count(*) from free_will.{t}"))
    finally:
        await conn.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", action="store_true")
    ap.add_argument(
        "--resume", action="store_true", help="skip TRUNCATE; insert only missing rows"
    )
    a = ap.parse_args()
    asyncio.run(main(a.commit, a.resume))
