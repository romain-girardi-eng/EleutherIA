#!/usr/bin/env python3
"""Ingest / repair Pseudo-Plutarch De Fato (Moralia 568b-574f) into the corpus.

Source: Vernardakis, Plutarchi Moralia vol. III (Teubner 1891), via Perseus Digital
Library / Scaife CTS API.
Work URN: urn:cts:greekLit:tlg0007.tlg108.perseus-grc2
Edition: urn:cts:greekLit:tlg0007.tlg108.perseus-grc2
12 CTS sections (0-11), verbatim Greek text.

This script:
  1. Reads /tmp/plutarch_de_fato_grc.json (produced by fetch_scaife_work.py).
  2. Validates each section (Greek ratio >= 0.97, word count >= 10).
  3. Replaces the 19 incorrect passages (wrong canonical_id tlg099) with 12
     canonical Scaife sections.
  4. Remaps the 118 passage_citations from old passage_ids to new passage_ids
     using a best-effort overlap mapping.
  5. Updates ancient_works metadata (canonical_id, cts_urn, title, author, school).
  6. Updates KG node metadata (work_canonical_id in passage_plut_fat_*_sN nodes).

Usage:
    set -a; source .env; set +a

    # Dry run (no writes)
    .venv/bin/python database/scripts/ingest_plutarch_defato_2026_05_25.py

    # Commit to DB
    .venv/bin/python database/scripts/ingest_plutarch_defato_2026_05_25.py --commit
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import uuid
from pathlib import Path

import psycopg2
import psycopg2.extras

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCHEMA = "free_will"
INPUT_PATH = "/tmp/plutarch_de_fato_grc.json"

# Correct metadata for the work
CORRECT_CANONICAL_ID = "urn:cts:greekLit:tlg0007.tlg108"
CORRECT_CTS_URN_WORK = "urn:cts:greekLit:tlg0007.tlg108.perseus-grc2"
CORRECT_TITLE = "De Fato (Περὶ εἱμαρμένης)"
CORRECT_AUTHOR = "Plutarch (Ps.-Plutarch)"
CORRECT_SCHOOL = "Middle Platonism"
CORRECT_PERIOD = "Roman Imperial"
CORRECT_LANGUAGE = "grc"
CORRECT_EDITION = "Vernardakis, Plutarchi Moralia vol. III (Teubner 1891), via Scaife/PerseusDL"

# The existing work_id in ancient_works (Greek De Fato, wrong canonical_id)
EXISTING_GRC_WORK_ID = "6f16a0c0-034d-5df9-b001-97bb411132c5"

GREEK_RE = re.compile(r"[Ͱ-Ͽἀ-῿]")

# Mapping from old Moralia section numbers to new Scaife section numbers.
# Built by text-overlap analysis (see note below).
# Old sections: Mor. 1-19  →  New sections: De Fato 0-11 (CTS sections 0-11)
# The 19 Moralia sub-sections map to 12 Scaife sections by grouping.
# Mapping: old_sequence_number (1-indexed) → new_sequence_number (1-indexed, 1=section 0)
#
# Determined by word-overlap of the Scaife section text against the 19-passage text:
# Section 0 (29w)  ≈ start of Mor. 1
# Section 1 (149w) ≈ rest of Mor. 1 + Mor. 2 start
# Section 2 (128w) ≈ Mor. 2 remainder
# Section 3 (325w) ≈ Mor. 3 + Mor. 4 start
# Section 4 (379w) ≈ Mor. 4-5
# Section 5 (252w) ≈ Mor. 5-6
# Section 6 (546w) ≈ Mor. 6-8
# Section 7 (521w) ≈ Mor. 8-11
# Section 8 (63w)  ≈ Mor. 11-12 bridge
# Section 9 (627w) ≈ Mor. 14-17
# Section 10(194w) ≈ Mor. 17-18
# Section 11(214w) ≈ Mor. 18-19
#
# For passage_citations remapping we use the closest-section heuristic below.
OLD_TO_NEW_MAP: dict[int, int] = {
    # old sequence (Mor. N, 1-indexed) → new sequence (section_n, 1-indexed)
    1: 1,   # Mor. 1 → section 0
    2: 2,   # Mor. 2 → section 1
    3: 3,   # Mor. 3 → section 2 or 3
    4: 4,   # Mor. 4 → section 3
    5: 5,   # Mor. 5 → section 4
    6: 5,   # Mor. 6 → section 5
    7: 7,   # Mor. 7 → section 6
    8: 7,   # Mor. 8 → section 7
    9: 8,   # Mor. 9 → section 7
    10: 8,  # Mor. 10 → section 7 or 8
    11: 8,  # Mor. 11 → section 7 or 8
    12: 9,  # Mor. 12 → section 8 or 9
    13: 9,  # Mor. 13 → section 9
    14: 10, # Mor. 14 → section 9
    15: 10, # Mor. 15 → section 9
    16: 10, # Mor. 16 → section 9
    17: 11, # Mor. 17 → section 10
    18: 11, # Mor. 18 → section 11
    19: 12, # Mor. 19 → section 11
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def greek_char_ratio(text: str) -> float:
    alpha = [c for c in text if c.isalpha()]
    if not alpha:
        return 0.0
    return sum(1 for c in alpha if GREEK_RE.match(c)) / len(alpha)


def connect(db_url: str) -> psycopg2.extensions.connection:
    conn = psycopg2.connect(db_url)
    with conn.cursor() as cur:
        cur.execute("SET search_path TO %s", (SCHEMA,))
    return conn


def build_mapping(
    cur: psycopg2.extensions.cursor,
    old_passage_ids: list[tuple[str, int]],
    new_passage_ids: list[tuple[str, int]],
) -> dict[str, str]:
    """Build old_passage_id → new_passage_id mapping via sequence number heuristic."""
    # new_passage_ids: list of (passage_id, section_n 1-indexed)
    new_by_seq: dict[int, str] = {seq: pid for pid, seq in new_passage_ids}

    mapping: dict[str, str] = {}
    for old_pid, old_seq in old_passage_ids:
        new_seq = OLD_TO_NEW_MAP.get(old_seq, min(old_seq, 12))
        # Clamp to available sections
        new_seq = max(1, min(new_seq, 12))
        mapping[old_pid] = new_by_seq.get(new_seq, new_by_seq[1])
    return mapping


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest Pseudo-Plutarch De Fato (Moralia 568b-574f) from Scaife JSON."
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Write to database (default: dry run).",
    )
    parser.add_argument(
        "--db-url",
        default=None,
        help="PostgreSQL URL (default: DATABASE_URL env var).",
    )
    parser.add_argument(
        "--input",
        default=INPUT_PATH,
        help=f"Input JSON file (default: {INPUT_PATH}).",
    )
    args = parser.parse_args()

    db_url = args.db_url or os.environ.get("DATABASE_URL", "")
    if not db_url:
        print("ERROR: DATABASE_URL required.")
        sys.exit(1)

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: {input_path} not found.")
        print("Run: .venv/bin/python database/scripts/fetch_scaife_work.py \\")
        print("       --urn 'urn:cts:greekLit:tlg0007.tlg108.perseus-grc2' \\")
        print("       --lang grc --ref-prefix 'De Fato' --level 1 \\")
        print("       --source library --output /tmp/plutarch_de_fato_grc.json")
        sys.exit(1)

    with open(input_path, encoding="utf-8") as f:
        sections: list[dict] = json.load(f)

    print("=" * 62)
    print("Ingest: Pseudo-Plutarch, De Fato (Περὶ εἱμαρμένης)")
    print(f"Source: {CORRECT_EDITION}")
    print(f"Work URN: {CORRECT_CTS_URN_WORK}")
    print(f"Sections: {len(sections)}")
    print("=" * 62)

    # Validate sections
    print("\n[1/6] Validating sections...")
    errors = 0
    for s in sections:
        text = s.get("text", "")
        ratio = greek_char_ratio(text)
        wc = s.get("word_count", len(text.split()))
        if ratio < 0.97:
            print(f"  ERROR section {s['section_n']}: Greek ratio {ratio:.1%} < 0.97")
            errors += 1
        if wc < 10:
            print(f"  ERROR section {s['section_n']}: only {wc} words")
            errors += 1

    if errors:
        print(f"\nERROR: {errors} validation failures. Aborting.")
        sys.exit(1)

    total_words = sum(s.get("word_count", 0) for s in sections)
    total_chars = sum(s.get("char_length", len(s.get("text", ""))) for s in sections)
    print(f"  All {len(sections)} sections OK ({total_words:,} words, {total_chars:,} chars)")

    # Greek sample
    first_text = sections[0].get("text", "")
    print(f"\n  Greek sample (section 0):")
    print(f"  {first_text[:120]}")
    print(f"\n  Greek sample (section 9, longest):")
    longest = max(sections, key=lambda s: s.get("word_count", 0))
    print(f"  {longest.get('text', '')[:150]}")

    # Connect
    conn = connect(db_url)
    cur = conn.cursor()

    # Step 2: Find existing work
    print("\n[2/6] Checking existing work entry...")
    cur.execute(
        "SELECT work_id, canonical_id, title, author, cts_urn FROM ancient_works WHERE work_id = %s",
        (EXISTING_GRC_WORK_ID,),
    )
    row = cur.fetchone()
    if row:
        work_id, old_cid, old_title, old_author, old_cts = row
        print(f"  Found work_id: {work_id}")
        print(f"  canonical_id:  {old_cid} → {CORRECT_CANONICAL_ID}")
        print(f"  title:         {old_title} → {CORRECT_TITLE}")
        print(f"  author:        {old_author} → {CORRECT_AUTHOR}")
        print(f"  cts_urn:       {old_cts} → {CORRECT_CTS_URN_WORK}")
        use_work_id = work_id
    else:
        print(f"  No work found with id {EXISTING_GRC_WORK_ID}. Will create new.")
        use_work_id = str(uuid.uuid4())

    # Step 3: Check existing passages
    print("\n[3/6] Checking existing passages...")
    cur.execute(
        "SELECT passage_id, sequence_number, canonical_ref FROM passages "
        "WHERE work_id = %s ORDER BY sequence_number",
        (EXISTING_GRC_WORK_ID,),
    )
    old_passages = cur.fetchall()
    print(f"  Existing passages: {len(old_passages)}")
    old_passage_ids: list[tuple[str, int]] = [(r[0], r[1]) for r in old_passages]

    cur.execute(
        "SELECT COUNT(*) FROM passage_citations WHERE passage_id IN "
        "(SELECT passage_id FROM passages WHERE work_id = %s)",
        (EXISTING_GRC_WORK_ID,),
    )
    citation_count = cur.fetchone()[0]
    print(f"  Passage citations to remap: {citation_count}")

    # Step 4: Build new passage rows
    print("\n[4/6] Building new passage rows...")
    new_passage_rows: list[tuple] = []
    new_passage_ids: list[tuple[str, int]] = []

    for i, s in enumerate(sections):
        pid = str(uuid.uuid4())
        text = s.get("text", "")
        cts_urn = s.get("cts_urn", "")
        ref = s.get("canonical_ref", f"De Fato {i}")
        char_length = s.get("char_length", len(text))
        word_count = s.get("word_count", len(text.split()))
        section_n = s.get("section_n", i + 1)  # 1-indexed

        # Parse CTS ref for book/chapter: URN ends in ":N" where N is the section number
        urn_ref = cts_urn.rsplit(":", 1)[-1] if ":" in cts_urn else str(i)
        chapter = urn_ref

        new_passage_rows.append((
            pid,
            str(use_work_id),
            ref,
            cts_urn,
            None,       # book
            chapter,    # chapter (CTS section number as string)
            None,       # section
            i,          # sequence_number (0-indexed)
            text,
            char_length,
            word_count,
            json.dumps({"stephanus_range": "568b-574f", "source": "scaife_cts", "edition": CORRECT_EDITION}),
        ))
        new_passage_ids.append((pid, section_n))
        print(f"  [{i:2d}] {ref:20s} | {cts_urn} | {word_count} words")

    # Build citation remapping
    print("\n[5/6] Building citation remapping...")
    if old_passages:
        id_map = build_mapping(cur, old_passage_ids, new_passage_ids)
        print(f"  Mapped {len(id_map)} old passage_ids to {len(set(id_map.values()))} new passage_ids")
        for old_pid, seq in old_passage_ids[:3]:
            print(f"    Mor.{seq} ({old_pid[:8]}…) → section {id_map[old_pid][:8]}…")
    else:
        id_map = {}

    if not args.commit:
        print("\n" + "=" * 62)
        print("DRY RUN complete. Summary:")
        print(f"  Sections to ingest:    {len(sections)}")
        print(f"  Total words:           {total_words:,}")
        print(f"  Total chars:           {total_chars:,}")
        print(f"  Citations to remap:    {citation_count}")
        print(f"  Work canonical_id:     {CORRECT_CANONICAL_ID}")
        print(f"  Work CTS URN:          {CORRECT_CTS_URN_WORK}")
        print("\nRe-run with --commit to write to database.")
        cur.close()
        conn.close()
        return

    # ---- COMMIT ----
    print("\n[6/6] Writing to database...")
    try:
        # 6a: Update ancient_works
        if row:
            cur.execute(
                """
                UPDATE ancient_works SET
                    canonical_id = %s,
                    cts_urn      = %s,
                    title        = %s,
                    author       = %s,
                    school       = %s,
                    period       = %s,
                    language     = %s,
                    source       = %s,
                    updated_at   = NOW()
                WHERE work_id = %s
                """,
                (
                    CORRECT_CANONICAL_ID,
                    CORRECT_CTS_URN_WORK,
                    CORRECT_TITLE,
                    CORRECT_AUTHOR,
                    CORRECT_SCHOOL,
                    CORRECT_PERIOD,
                    CORRECT_LANGUAGE,
                    "scaife_cts",
                    str(use_work_id),
                ),
            )
            print(f"  Updated ancient_works (work_id={use_work_id})")
        else:
            cur.execute(
                """
                INSERT INTO ancient_works
                    (work_id, canonical_id, cts_urn, title, author, school, period, language, source)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    use_work_id,
                    CORRECT_CANONICAL_ID,
                    CORRECT_CTS_URN_WORK,
                    CORRECT_TITLE,
                    CORRECT_AUTHOR,
                    CORRECT_SCHOOL,
                    CORRECT_PERIOD,
                    CORRECT_LANGUAGE,
                    "scaife_cts",
                ),
            )
            print(f"  Created ancient_works (work_id={use_work_id})")

        # 6b: Insert new passages FIRST (so foreign key for citations is satisfied)
        psycopg2.extras.execute_values(
            cur,
            """
            INSERT INTO passages
                (passage_id, work_id, canonical_ref, cts_urn,
                 book, chapter, section, sequence_number,
                 text_content, char_length, word_count, citation_hierarchy)
            VALUES %s
            ON CONFLICT DO NOTHING
            """,
            new_passage_rows,
            template=(
                "(%s::uuid, %s::uuid, %s, %s,"
                " %s, %s, %s, %s,"
                " %s, %s, %s, %s::jsonb)"
            ),
            page_size=50,
        )
        print(f"  Inserted {len(new_passage_rows)} new passages")

        # 6c: Remap passage_citations (old passage_ids → new passage_ids)
        if id_map:
            updated_citations = 0
            for old_pid, new_pid in id_map.items():
                cur.execute(
                    "UPDATE passage_citations SET passage_id = %s WHERE passage_id = %s",
                    (new_pid, old_pid),
                )
                updated_citations += cur.rowcount
            print(f"  Re-pointed {updated_citations} passage_citations to new passage_ids")

        # 6d: Delete old passages (now safe: citations already remapped)
        cur.execute(
            "DELETE FROM passages WHERE work_id = %s AND cts_urn IS NULL",
            (str(use_work_id),),
        )
        print(f"  Deleted {cur.rowcount} old (no-CTS-URN) passages")

        # 6e: Update KG node metadata (work_canonical_id in passage_plut_fat_*_sN)
        cur.execute(
            """
            UPDATE kg_nodes
            SET metadata = jsonb_set(
                COALESCE(metadata, '{}'::jsonb),
                '{work_canonical_id}',
                %s::jsonb
            )
            WHERE node_id LIKE 'passage_plut_fat_%%'
              AND (metadata->>'work_canonical_id' = 'urn:cts:greekLit:tlg0007.tlg099'
                   OR metadata->>'work_canonical_id' IS NULL)
            """,
            (json.dumps(CORRECT_CANONICAL_ID),),
        )
        kg_updated = cur.rowcount
        print(f"  Updated {kg_updated} KG passage nodes (work_canonical_id → tlg108)")

        # 6f: Update work KG node
        cur.execute(
            """
            UPDATE kg_nodes
            SET metadata = jsonb_set(
                COALESCE(metadata, '{}'::jsonb),
                '{canonical_id}',
                %s::jsonb
            )
            WHERE node_id = 'work_plutarch_de_fato_complete'
            """,
            (json.dumps(CORRECT_CANONICAL_ID),),
        )
        print(f"  Updated work KG node metadata: {cur.rowcount} row(s)")

        conn.commit()
        print("\n  Transaction committed.")

        # Verify
        cur.execute(
            "SELECT COUNT(*) FROM passages WHERE work_id = %s",
            (str(use_work_id),),
        )
        final_count = cur.fetchone()[0]
        assert final_count == len(sections), (
            f"Expected {len(sections)}, got {final_count} passages"
        )

        cur.execute(
            "SELECT canonical_id, cts_urn, title, author FROM ancient_works WHERE work_id = %s",
            (str(use_work_id),),
        )
        aw = cur.fetchone()

        cur.execute(
            "SELECT COUNT(*) FROM passage_citations WHERE passage_id IN "
            "(SELECT passage_id FROM passages WHERE work_id = %s)",
            (str(use_work_id),),
        )
        final_citations = cur.fetchone()[0]

        print("\n" + "=" * 62)
        print("Verification")
        print("=" * 62)
        print(f"  Passages in DB:        {final_count}")
        print(f"  Passage citations:     {final_citations}")
        print(f"  canonical_id:          {aw[0]}")
        print(f"  cts_urn:               {aw[1]}")
        print(f"  title:                 {aw[2]}")
        print(f"  author:                {aw[3]}")
        print("\nDone.")

    except Exception as exc:
        conn.rollback()
        print(f"\nERROR: {exc}")
        print("Transaction rolled back.")
        sys.exit(1)
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
