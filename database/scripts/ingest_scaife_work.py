#!/usr/bin/env python3
"""
Ingest a Scaife-fetched work JSON into the passages table and create KG nodes.

Takes the JSON output of fetch_scaife_work.py and:
1. Creates/verifies an ancient_works entry
2. Inserts passages into the passages table
3. Creates KG passage nodes via create_kg_passage_nodes.py logic

Usage:
    set -a; source .env; set +a

    # Dry run
    python database/scripts/ingest_scaife_work.py \
        --input /tmp/aristotle_de_gen_corr.json \
        --canonical-id "urn:cts:greekLit:tlg0086.tlg003" \
        --title "De Generatione et Corruptione" \
        --author "Aristotle" \
        --language grc \
        --period "Classical" \
        --school "Peripatetic" \
        --prefix "passage_arist_gen_corr" \
        --work-node "work_de_gen_corr_aristotle" \
        --person-node "person_aristotle_384_322bce_b2c3d4e5"

    # Apply
    python database/scripts/ingest_scaife_work.py \
        --input /tmp/aristotle_de_gen_corr.json \
        --canonical-id "urn:cts:greekLit:tlg0086.tlg003" \
        --title "De Generatione et Corruptione" \
        --author "Aristotle" \
        --language grc \
        --period "Classical" \
        --school "Peripatetic" \
        --prefix "passage_arist_gen_corr" \
        --work-node "work_de_gen_corr_aristotle" \
        --person-node "person_aristotle_384_322bce_b2c3d4e5" \
        --confirm
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid

import psycopg2
import psycopg2.extras

SCHEMA = "free_will"


def get_db_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        print("ERROR: DATABASE_URL not set.")
        sys.exit(1)
    return url


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest Scaife work into DB + KG")
    parser.add_argument("--input", required=True, help="JSON file from fetch_scaife_work.py")
    parser.add_argument("--canonical-id", required=True, help="Work canonical_id (CTS URN without edition)")
    parser.add_argument("--title", required=True, help="Work title")
    parser.add_argument("--author", required=True, help="Author name")
    parser.add_argument("--language", required=True, choices=["grc", "lat"], help="Language code")
    parser.add_argument("--period", required=True, help="Historical period")
    parser.add_argument("--school", default=None, help="Philosophical school")
    parser.add_argument("--prefix", required=True, help="KG node_id prefix")
    parser.add_argument("--work-node", required=True, help="KG work node_id (will create if missing)")
    parser.add_argument("--person-node", default=None, help="KG person node_id")
    parser.add_argument("--confirm", action="store_true", help="Actually write to DB")
    parser.add_argument("--db-url", help="Database URL")
    args = parser.parse_args()

    db_url = args.db_url or get_db_url()

    with open(args.input) as f:
        sections = json.load(f)

    print(f"Loaded {len(sections)} sections from {args.input}")
    total_chars = sum(s.get("char_length", len(s.get("text", ""))) for s in sections)
    total_words = sum(s.get("word_count", 0) for s in sections)
    print(f"Total: {total_words:,} words, {total_chars:,} chars")

    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute(f"SET search_path TO {SCHEMA}")

    # 1. Check/create ancient_works entry
    cur.execute("SELECT work_id FROM ancient_works WHERE canonical_id = %s", (args.canonical_id,))
    row = cur.fetchone()
    if row:
        work_id = row[0]
        print(f"Work already exists: {args.canonical_id} (work_id={work_id})")
    else:
        work_id = str(uuid.uuid4())
        print(f"Will create work: {args.canonical_id} (work_id={work_id})")
        if args.confirm:
            cur.execute(
                """INSERT INTO ancient_works (work_id, canonical_id, title, author, language, period, school, cts_urn)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (work_id, args.canonical_id, args.title, args.author,
                 args.language, args.period, args.school,
                 sections[0].get("cts_urn", "").rsplit(":", 1)[0] if sections else None),
            )

    # 2. Check existing passages
    cur.execute("SELECT COUNT(*) FROM passages WHERE work_id = %s", (str(work_id),))
    existing_passages = cur.fetchone()[0]
    if existing_passages > 0:
        print(f"WARNING: {existing_passages} passages already exist for this work")

    # 3. Insert passages
    passages_to_insert = []
    for i, s in enumerate(sections):
        text = s.get("text", s.get("greek_text", ""))
        ref = s.get("canonical_ref", "")
        cts_urn = s.get("cts_urn", "")

        # Parse CTS ref into book/chapter/section from the URN
        # The CTS URN contains the structured reference (e.g., "1.2.3")
        urn_ref = cts_urn.rsplit(":", 1)[-1] if ":" in cts_urn else ""
        urn_parts = urn_ref.split(".") if urn_ref else []
        book = urn_parts[0] if len(urn_parts) >= 2 else None
        chapter = urn_parts[1] if len(urn_parts) >= 2 else urn_parts[0] if urn_parts else None
        section = urn_parts[2] if len(urn_parts) >= 3 else None

        passage_id = str(uuid.uuid4())
        passages_to_insert.append((
            passage_id,
            str(work_id),
            ref,
            cts_urn,
            book,
            chapter,
            section,
            i,  # sequence_number
            text,
            len(text),
            len(text.split()),
        ))

    print(f"\nPassages to insert: {len(passages_to_insert)}")

    if not args.confirm:
        print("\nDRY RUN — showing first 3 passages:")
        for p in passages_to_insert[:3]:
            print(f"  ref={p[2]:20s} book={p[4]} ch={p[5]} sec={p[6]} words={p[10]} chars={p[9]}")
        print("\nRe-run with --confirm to apply.")
        conn.close()
        return

    # Insert passages
    psycopg2.extras.execute_values(
        cur,
        """INSERT INTO passages (passage_id, work_id, canonical_ref, cts_urn,
           book, chapter, section, sequence_number, text_content, char_length, word_count)
           VALUES %s
           ON CONFLICT DO NOTHING""",
        passages_to_insert,
        template="(%s::uuid, %s::uuid, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        page_size=100,
    )
    print(f"Inserted passages: {cur.rowcount}")

    # 4. Create work KG node if it doesn't exist
    cur.execute("SELECT 1 FROM kg_nodes WHERE node_id = %s", (args.work_node,))
    if not cur.fetchone():
        cur.execute(
            """INSERT INTO kg_nodes (node_id, label, type, description, period, metadata)
               VALUES (%s, %s, 'work', %s, %s, %s::jsonb)""",
            (args.work_node, f"{args.author}, {args.title}",
             f"{args.author}, {args.title} ({args.language}, {args.period})",
             args.period,
             json.dumps({"canonical_id": args.canonical_id, "language": args.language,
                          "author": args.author, "auto_generated": True})),
        )
        print(f"Created work KG node: {args.work_node}")

        # Add authored_by edge if person provided
        if args.person_node:
            cur.execute(
                "INSERT INTO kg_edges (source_id, target_id, relation, metadata) VALUES (%s, %s, 'authored_by', %s::jsonb)",
                (args.work_node, args.person_node, json.dumps({"auto_generated": True})),
            )

    conn.commit()
    conn.close()

    # 5. Now create KG passage nodes using the existing script's logic
    print("\nNow run create_kg_passage_nodes.py:")
    print("  python database/scripts/create_kg_passage_nodes.py \\")
    print(f"    --canonical-id \"{args.canonical_id}\" \\")
    print(f"    --prefix \"{args.prefix}\" \\")
    print(f"    --work-node \"{args.work_node}\" \\")
    if args.person_node:
        print(f"    --person-node \"{args.person_node}\" \\")
    print("    --confirm")


if __name__ == "__main__":
    main()
