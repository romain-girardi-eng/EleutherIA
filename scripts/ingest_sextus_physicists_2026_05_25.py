"""Ingest Sextus Empiricus — Adversus Mathematicos IX–X (Against the Physicists).

CTS URN: urn:cts:greekLit:tlg0544.tlg002.1st1K-grc1
Source: OpenGreekAndLatin/First1KGreek (Mutschmann/Mau, Teubner 1912-1954)

Books 9 and 10 are ingested verbatim from the TEI. Relevant ranges per the
reading audit:
  - AM IX §§1–330 (on cause/αἰτία, god, matter, time — Against Physicists Part I)
  - AM X §§37–247 (on motion/κίνησις and place — Against Physicists Part II)

We ingest the full books 9 and 10 as fetched (all sections §§1–440 / §§1–351);
subsetting to exact paragraph ranges is not needed at ingest — citations and KG
linking handle relevance.

Idempotent: passages already present (same cts_urn) are skipped.

Usage:
    .venv/bin/python -m scripts.ingest_sextus_physicists_2026_05_25       # dry-run
    .venv/bin/python -m scripts.ingest_sextus_physicists_2026_05_25 --commit
"""
from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_DIR = ROOT / "data" / "corpus" / "fix_snapshots" / "ingest_sextus_physicists_2026_05_25"

AM_WORK_URN = "urn:cts:greekLit:tlg0544.tlg002.1st1K-grc1"
AM_CANONICAL_ID = "urn_cts_greeklit_tlg0544_tlg002_grc"

WORK_ROW = {
    "canonical_id": AM_CANONICAL_ID,
    "title": "Adversus Mathematicos IX–X (Against the Physicists)",
    "title_original": "Πρὸς φυσικούς",
    "author": "Sextus Empiricus",
    "author_original": "Σέξτος Ἐμπειρικός",
    "language": "grc",
    "period": "Imperial",
    "cts_urn": AM_WORK_URN,
    "tlg_code": "tlg0544.tlg002",
    "source": "First1KGreek / OpenGreekAndLatin — Mutschmann/Mau, Teubner 1912–1954",
    "source_url": "https://github.com/OpenGreekAndLatin/First1KGreek/tree/master/data/tlg0544/tlg002",
    "license": "CC BY-SA 3.0",
    "division_scheme": "book.section",
    "notes": (
        "Books 9–10 only. Book 9 (Prὸς φυσικούς I): "
        "αἰτία (cause), god, matter, time. "
        "Book 10 (Prὸς φυσικούς II): "
        "κίνησις (motion), place, number. "
        "The remaining books of Adversus Mathematicos (1–8, 11) are not included."
    ),
}


def _db_url() -> str:
    for line in (ROOT / ".env").open():
        if line.startswith("DATABASE_URL="):
            raw = line.split("=", 1)[1].strip().strip('"').strip("'")
            return raw.replace("postgresql://", "postgres://", 1)
    raise SystemExit("DATABASE_URL not found in .env")


async def _upsert_work(conn, *, commit: bool) -> str:
    """Insert the ancient_works row if absent; return work_id as str."""
    existing = await conn.fetchrow(
        "SELECT work_id FROM free_will.ancient_works WHERE canonical_id = $1",
        AM_CANONICAL_ID,
    )
    if existing:
        work_id = str(existing["work_id"])
        print(f"Work row already present: work_id={work_id}")
        return work_id

    if not commit:
        print("(dry-run) Would INSERT ancient_works row:")
        for k, v in WORK_ROW.items():
            print(f"  {k}: {v!r}")
        return "DRY-RUN-UUID"

    row = await conn.fetchrow(
        """
        INSERT INTO free_will.ancient_works
            (canonical_id, title, title_original, author, author_original,
             language, period, cts_urn, tlg_code, source, source_url,
             license, division_scheme, notes)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14)
        RETURNING work_id
        """,
        WORK_ROW["canonical_id"],
        WORK_ROW["title"],
        WORK_ROW["title_original"],
        WORK_ROW["author"],
        WORK_ROW["author_original"],
        WORK_ROW["language"],
        WORK_ROW["period"],
        WORK_ROW["cts_urn"],
        WORK_ROW["tlg_code"],
        WORK_ROW["source"],
        WORK_ROW["source_url"],
        WORK_ROW["license"],
        WORK_ROW["division_scheme"],
        WORK_ROW["notes"],
    )
    work_id = str(row["work_id"])
    print(f"Inserted ancient_works row: work_id={work_id}")
    return work_id


async def _load_existing_urns(conn, work_id: str) -> set[str]:
    if work_id == "DRY-RUN-UUID":
        return set()
    rows = await conn.fetch(
        "SELECT cts_urn FROM free_will.passages WHERE work_id = $1",
        work_id,
    )
    return {str(r["cts_urn"]) for r in rows if r["cts_urn"]}


async def _insert_passages(conn, work_id: str, rows: list[dict]) -> int:
    async with conn.transaction():
        await conn.executemany(
            """
            INSERT INTO free_will.passages
                (work_id, canonical_ref, cts_urn, sequence_number,
                 text_content, passage_role, char_length, word_count)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
            """,
            [
                (
                    work_id,
                    r["canonical_ref"],
                    r["cts_urn"],
                    r["sequence_number"],
                    r["text_content"],
                    "original",
                    len(r["text_content"]),
                    len(r["text_content"].split()),
                )
                for r in rows
            ],
        )
    return len(rows)


def _build_passages_to_insert(
    fetched: list[dict],
    existing_urns: set[str],
    work_id: str,
    start_seq: int,
) -> list[dict]:
    out: list[dict] = []
    seq = start_seq
    seen: set[str] = set()
    for f in fetched:
        urn = f.get("cts_urn", "")
        text = (f.get("text_content") or "").strip()
        if not urn or not text or urn in existing_urns or urn in seen:
            continue
        seen.add(urn)
        ref = urn.split(":")[-1] if ":" in urn else urn
        out.append({
            "work_id": work_id,
            "canonical_ref": ref,
            "cts_urn": urn,
            "sequence_number": seq,
            "text_content": text,
        })
        seq += 1
    return out


async def run(*, commit: bool) -> None:
    import asyncpg
    from scripts.corpus_github_fetch import fetch_work_passages

    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Fetch TEI verbatim
    print(f"Fetching {AM_WORK_URN} ...")
    all_passages = fetch_work_passages(AM_WORK_URN, level=2)
    print(f"Total parsed: {len(all_passages)} passages (all books)")

    # 2. Filter books 9 and 10
    book9 = [p for p in all_passages if p["cts_urn"].startswith(f"{AM_WORK_URN}:9.")]
    book10 = [p for p in all_passages if p["cts_urn"].startswith(f"{AM_WORK_URN}:10.")]
    to_ingest = book9 + book10
    print(f"Book 9: {len(book9)} passages | Book 10: {len(book10)} passages | Total: {len(to_ingest)}")

    # 3. Dry-run proof: Greek sample confirming αἰτία and κίνησις content
    import unicodedata

    def nfc(s: str) -> str:
        return unicodedata.normalize("NFC", s)

    aitia_hits = [p for p in book9 if "αἰτί" in nfc(p["text_content"])]
    kinesis_hits = [p for p in book10 if "κίνησ" in nfc(p["text_content"])]

    print()
    print("=== DRY-RUN PROOF: content verification ===")
    print(f"Passages with αἰτί (cause) in book 9: {len(aitia_hits)}")
    if aitia_hits:
        print(f"  Sample: {aitia_hits[0]['cts_urn']}")
        print(f"  Text: {aitia_hits[0]['text_content'][:300]!r}")
    print()
    print(f"Passages with κίνησ (motion) in book 10: {len(kinesis_hits)}")
    if kinesis_hits:
        print(f"  Sample: {kinesis_hits[0]['cts_urn']}")
        print(f"  Text: {kinesis_hits[0]['text_content'][:300]!r}")
    print()
    print("Book 9 opening (§1 — confirms 'Against Physicists' / Πρὸς φυσικούς):")
    print(f"  {book9[0]['cts_urn']}")
    print(f"  {book9[0]['text_content'][:400]!r}")
    print()

    # 4. Snapshot fetched sample
    snapshot_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "work_canonical_id": AM_CANONICAL_ID,
        "cts_urn": AM_WORK_URN,
        "book9_count": len(book9),
        "book10_count": len(book10),
        "total_to_ingest": len(to_ingest),
        "sample_book9_1": {
            "cts_urn": book9[0]["cts_urn"],
            "text_content": book9[0]["text_content"][:500],
        },
        "sample_book10_38": next(
            ({"cts_urn": p["cts_urn"], "text_content": p["text_content"][:300]}
             for p in book10 if p["cts_urn"].endswith(":10.38")),
            None,
        ),
        "committed": commit,
    }
    snapshot_path = SNAPSHOT_DIR / "before.json"
    snapshot_path.write_text(json.dumps(snapshot_data, indent=2, ensure_ascii=False))
    print(f"Snapshot written: {snapshot_path}")
    print()

    # 5. Connect to DB
    conn = await asyncpg.connect(_db_url())
    try:
        # 6. Ensure ancient_works row exists
        work_id = await _upsert_work(conn, commit=commit)

        # 7. Load existing passage URNs
        existing_urns = await _load_existing_urns(conn, work_id)
        max_seq_row = await conn.fetchrow(
            "SELECT COALESCE(MAX(sequence_number), 0) AS max_seq FROM free_will.passages"
        )
        max_seq = int(max_seq_row["max_seq"]) if max_seq_row else 0

        # 8. Compute new passages
        new_rows = _build_passages_to_insert(to_ingest, existing_urns, work_id, max_seq + 1)
        skipped = len(to_ingest) - len(new_rows)
        print(f"existing_urns_for_work={len(existing_urns)} new={len(new_rows)} skipped={skipped}")

        if not new_rows:
            print("Nothing to insert (already up to date).")
            return

        # 9. Insert or report
        print()
        if commit:
            inserted = await _insert_passages(conn, work_id, new_rows)
            print(f"Inserted {inserted} passages.")
            snapshot_data["committed"] = True
            snapshot_data["committed_at"] = datetime.now(timezone.utc).isoformat()
            snapshot_data["inserted"] = inserted
            (SNAPSHOT_DIR / "after.json").write_text(
                json.dumps(snapshot_data, indent=2, ensure_ascii=False)
            )
        else:
            print(f"(dry-run) Would insert {len(new_rows)} passages.")
            print("Use --commit to write.")

    finally:
        await conn.close()


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Ingest Sextus Empiricus AM IX-X verbatim from First1KGreek"
    )
    ap.add_argument("--commit", action="store_true", help="Write to DB (default: dry-run)")
    args = ap.parse_args()
    asyncio.run(run(commit=args.commit))


if __name__ == "__main__":
    main()
