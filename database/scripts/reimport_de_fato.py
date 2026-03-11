"""Delete messy De Fato passages and reimport 39 clean chapters.

Reads clean sections from /tmp/de_fato_clean_sections.json (produced by
fetch_de_fato_cts.py) and writes them into the database.

Usage:
    # Dry run (no writes)
    python database/scripts/reimport_de_fato.py

    # Confirmed (writes to DB)
    python database/scripts/reimport_de_fato.py --confirm

    # With explicit DB URL
    python database/scripts/reimport_de_fato.py --confirm --db-url postgresql://...
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import uuid

import psycopg2
import psycopg2.extras

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCHEMA = "free_will"
INPUT_PATH = "/tmp/de_fato_clean_sections.json"
CORRECT_CANONICAL_ID = "tlg0732.tlg014"
CORRECT_CTS_URN = "urn:cts:greekLit:tlg0732.tlg014.1st1K-grc1"
GREEK_RE = re.compile(r"[\u0370-\u03FF\u1F00-\u1FFF]")


# ---------------------------------------------------------------------------
# DB Helpers (follows import_sc/importer.py patterns)
# ---------------------------------------------------------------------------

def connect(db_url: str) -> psycopg2.extensions.connection:
    """Open a connection and set search_path."""
    conn = psycopg2.connect(db_url)
    with conn.cursor() as cur:
        cur.execute("SET search_path TO %s", (SCHEMA,))
    return conn


def greek_char_ratio(text: str) -> float:
    """Fraction of alphabetic characters that are Greek."""
    alpha_chars = [c for c in text if c.isalpha()]
    if not alpha_chars:
        return 0.0
    greek_count = sum(1 for c in alpha_chars if GREEK_RE.match(c))
    return greek_count / len(alpha_chars)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reimport De Fato passages from clean JSON."
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Actually write to the database (default: dry run).",
    )
    parser.add_argument(
        "--db-url",
        default=None,
        help="PostgreSQL connection URL (default: DATABASE_URL env var).",
    )
    args = parser.parse_args()

    db_url = args.db_url or os.environ.get("DATABASE_URL", "")
    dry_run = not args.confirm

    if not db_url:
        print("ERROR: DATABASE_URL required. Set env var or pass --db-url.")
        sys.exit(1)

    # Load clean sections
    if not os.path.exists(INPUT_PATH):
        print(f"ERROR: {INPUT_PATH} not found. Run fetch_de_fato_cts.py first.")
        sys.exit(1)

    with open(INPUT_PATH, encoding="utf-8") as f:
        sections = json.load(f)

    print(f"Loaded {len(sections)} sections from {INPUT_PATH}")
    if len(sections) != 39:
        print(f"WARNING: Expected 39 sections, got {len(sections)}")

    # Validate all sections before touching the database
    for s in sections:
        ratio = greek_char_ratio(s["greek_text"])
        if ratio < 0.85:
            print(f"ERROR: Section {s['section_n']} has low Greek ratio: {ratio:.1%}")
            print("  Aborting. Review fetch output before reimporting.")
            sys.exit(1)
        if s["word_count"] < 10:
            print(f"ERROR: Section {s['section_n']} has only {s['word_count']} words.")
            sys.exit(1)

    print("All sections pass validation.")

    if dry_run:
        print("\n[DRY RUN] Would perform the following operations:")
        print("  1. Find work_id for Alexander De Fato")
        print("  2. Delete all edges involving passage_alex_fat_* KG nodes")
        print("  3. Delete all passage_alex_fat_* KG nodes (659 old nodes)")
        print("  4. Delete all existing passages for that work_id (659)")
        print("  5. Update ancient_works: canonical_id → tlg0732.tlg014")
        print(f"  6. Insert {len(sections)} clean passages")
        print("\nRun with --confirm to execute.")
        return

    # Connect and execute
    conn = connect(db_url)
    try:
        with conn.cursor() as cur:
            # Step 1: Find the work
            cur.execute(
                """
                SELECT work_id, canonical_id, title, author
                FROM ancient_works
                WHERE author ILIKE %s AND title ILIKE %s
                """,
                ("%alexander%", "%fato%"),
            )
            row = cur.fetchone()
            if not row:
                print("ERROR: No Alexander De Fato work found in ancient_works.")
                sys.exit(1)

            work_id, old_canonical_id, title, author = row
            print(f"\nFound work: {author} - {title}")
            print(f"  work_id:       {work_id}")
            print(f"  canonical_id:  {old_canonical_id} → {CORRECT_CANONICAL_ID}")

            # Step 2: Delete old KG edges and nodes
            # Edges where passage_alex_fat_* is SOURCE
            cur.execute(
                "DELETE FROM kg_edges WHERE source_id LIKE 'passage_alex_fat_%%'"
            )
            src_deleted = cur.rowcount
            # Edges where passage_alex_fat_* is TARGET
            cur.execute(
                "DELETE FROM kg_edges WHERE target_id LIKE 'passage_alex_fat_%%'"
            )
            tgt_deleted = cur.rowcount
            print(f"\n  Deleted {src_deleted + tgt_deleted} KG edges "
                  f"({src_deleted} outgoing, {tgt_deleted} incoming)")

            # Delete old KG passage nodes
            cur.execute(
                "DELETE FROM kg_nodes WHERE node_id LIKE 'passage_alex_fat_%%'"
            )
            print(f"  Deleted {cur.rowcount} old KG passage nodes.")

            # Step 3: Delete existing passages
            cur.execute(
                "SELECT COUNT(*) FROM passages WHERE work_id = %s",
                (str(work_id),),
            )
            old_count = cur.fetchone()[0]
            print(f"\n  Deleting {old_count} existing passages...")

            cur.execute(
                "DELETE FROM passages WHERE work_id = %s",
                (str(work_id),),
            )
            print(f"  Deleted {cur.rowcount} passages.")

            # Step 4: Update ancient_works metadata
            cur.execute(
                """
                UPDATE ancient_works
                SET canonical_id = %s,
                    cts_urn = %s,
                    total_divisions = %s,
                    source = %s,
                    division_scheme = %s,
                    citation_levels = %s,
                    updated_at = NOW()
                WHERE work_id = %s
                """,
                (
                    CORRECT_CANONICAL_ID,
                    CORRECT_CTS_URN,
                    len(sections),
                    "scaife_cts",
                    "chapter",
                    ["chapter"],
                    str(work_id),
                ),
            )
            print("  Updated ancient_works (canonical_id, cts_urn, etc.)")

            # Step 5: Insert clean passages
            passage_rows = []
            for s in sections:
                passage_rows.append((
                    str(uuid.uuid4()),      # passage_id
                    str(work_id),           # work_id
                    s["canonical_ref"],     # canonical_ref
                    s["cts_urn"],           # cts_urn
                    None,                   # book
                    str(s["section_n"]),    # chapter
                    None,                   # section
                    s["section_n"] - 1,     # sequence_number (0-indexed)
                    s["greek_text"],        # text_content
                    s["char_length"],       # char_length
                    s["word_count"],        # word_count
                    json.dumps({            # citation_hierarchy
                        "chapter": s["section_n"],
                        "bruns_pages": s["bruns_pages"],
                    }),
                ))

            psycopg2.extras.execute_values(
                cur,
                """
                INSERT INTO passages
                    (passage_id, work_id, canonical_ref, cts_urn,
                     book, chapter, section, sequence_number,
                     text_content, char_length, word_count,
                     citation_hierarchy)
                VALUES %s
                """,
                passage_rows,
                template=(
                    "(%s::uuid, %s::uuid, %s, %s, "
                    "%s, %s, %s, %s, "
                    "%s, %s, %s, "
                    "%s::jsonb)"
                ),
                page_size=50,
            )
            print(f"  Inserted {len(passage_rows)} clean passages.")

        conn.commit()
        print("\nTransaction committed successfully.")

        # Verification
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM passages WHERE work_id = %s",
                (str(work_id),),
            )
            final_count = cur.fetchone()[0]
            print("\nVerification:")
            print(f"  Passages in DB: {final_count}")
            assert final_count == len(sections), (
                f"Expected {len(sections)}, got {final_count}"
            )

            cur.execute(
                """
                SELECT canonical_id, cts_urn
                FROM ancient_works WHERE work_id = %s
                """,
                (str(work_id),),
            )
            row = cur.fetchone()
            print(f"  canonical_id:   {row[0]}")
            print(f"  cts_urn:        {row[1]}")

        print("\nDone. Proceed to Phase 4 (KG nodes).")

    except Exception as exc:
        conn.rollback()
        print(f"\nERROR: {exc}")
        print("Transaction rolled back.")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
