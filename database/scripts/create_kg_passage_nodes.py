#!/usr/bin/env python3
"""
Generic script to create KG passage nodes from the passages table.

For each passage in a given work, creates:
  1. A KG passage node (original language text in description)
  2. Edges: part_of → work node, authored_by → person node
  3. A passage_citation linking passage_id ↔ kg_node_id

Does NOT create _en translation nodes — use create_passage_translations.py
for that step after generating translations.

Usage:
    set -a; source .env; set +a

    # List available works (shows canonical_id, passage count, existing KG nodes)
    python database/scripts/create_kg_passage_nodes.py --list

    # Dry run for a specific work
    python database/scripts/create_kg_passage_nodes.py \
        --canonical-id "urn:cts:latinLit:phi0474.phi049" \
        --prefix "passage_cic_fat" \
        --work-node "work_de_fato_cicero_44bce_b9c4e5d2" \
        --person-node "person_cicero_marcus_tullius_106_43bce_a8f3d2c1"

    # Apply
    python database/scripts/create_kg_passage_nodes.py \
        --canonical-id "urn:cts:latinLit:phi0474.phi049" \
        --prefix "passage_cic_fat" \
        --work-node "work_de_fato_cicero_44bce_b9c4e5d2" \
        --person-node "person_cicero_marcus_tullius_106_43bce_a8f3d2c1" \
        --confirm
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

import psycopg2
import psycopg2.extras

SCHEMA = "free_will"


def get_db_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        print("ERROR: DATABASE_URL not set.")
        sys.exit(1)
    return url


def list_works(db_url: str) -> None:
    """Show all works with passages, their KG node counts, and suggested prefixes."""
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute(f"SET search_path TO {SCHEMA}")

    cur.execute("""
        SELECT w.canonical_id, w.title, w.author, w.language,
               COUNT(p.passage_id) as pcount, w.period, w.school
        FROM ancient_works w
        JOIN passages p ON p.work_id = w.work_id
        GROUP BY w.canonical_id, w.title, w.author, w.language, w.period, w.school
        ORDER BY pcount DESC
    """)
    rows = cur.fetchall()

    # Count existing KG passage nodes per work
    cur.execute("""
        SELECT metadata->>'work_canonical_id', COUNT(*)
        FROM kg_nodes
        WHERE type = 'passage' AND metadata->>'work_canonical_id' IS NOT NULL
        GROUP BY metadata->>'work_canonical_id'
    """)
    kg_counts = dict(cur.fetchall())

    print(f"{'passages':>8} {'kg':>6} {'lang':>4} {'author':<28} {'title':<50} canonical_id")
    print("-" * 140)
    for r in rows:
        cid, title, author, lang, pcount, period, school = r
        kg = kg_counts.get(cid, 0)
        flag = "" if kg > 0 else " ***"
        print(f"{pcount:>8} {kg:>6} {lang:>4} {author[:27]:<28} {title[:49]:<50} {cid}{flag}")

    conn.close()


def sanitize_label_part(text: str) -> str:
    """Create a safe label component from chapter/section refs."""
    # Replace dots and colons with underscores, strip non-alnum
    return re.sub(r"[^a-z0-9_]", "", text.lower().replace(".", "_").replace(":", "_").replace(" ", "_"))


def create_kg_nodes(
    db_url: str,
    canonical_id: str,
    prefix: str,
    work_node_id: str,
    person_node_id: str | None,
    dry_run: bool = True,
    label_template: str | None = None,
) -> int:
    """Create KG passage nodes for all passages in a work.

    Args:
        canonical_id: The work's canonical_id in ancient_works table.
        prefix: KG node_id prefix, e.g. "passage_cic_fat".
        work_node_id: Existing KG work node to link via part_of.
        person_node_id: Existing KG person node to link via authored_by (optional).
        label_template: Optional f-string template for labels. Available vars:
            {author}, {title}, {ref}, {n}. Default: "{author}, {title}, {ref}"
    """
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute(f"SET search_path TO {SCHEMA}")

    # 1. Fetch the work
    cur.execute(
        "SELECT work_id, title, author, language, period, school, cts_urn "
        "FROM ancient_works WHERE canonical_id = %s",
        (canonical_id,),
    )
    work = cur.fetchone()
    if not work:
        print(f"ERROR: No work found with canonical_id = {canonical_id}")
        conn.close()
        return 0

    work_id, title, author, language, period, school, work_cts_urn = work
    print(f"Work: {author} - {title} ({language}, {period})")

    # 2. Verify work KG node exists
    cur.execute("SELECT node_id FROM kg_nodes WHERE node_id = %s", (work_node_id,))
    if not cur.fetchone():
        print(f"ERROR: Work KG node '{work_node_id}' not found in kg_nodes.")
        conn.close()
        return 0

    # 3. Verify person KG node exists (if provided)
    if person_node_id:
        cur.execute("SELECT node_id FROM kg_nodes WHERE node_id = %s", (person_node_id,))
        if not cur.fetchone():
            print(f"ERROR: Person KG node '{person_node_id}' not found in kg_nodes.")
            conn.close()
            return 0

    # 4. Fetch all passages for this work, ordered by sequence
    cur.execute(
        """
        SELECT passage_id, canonical_ref, cts_urn, book, chapter, section,
               sequence_number, text_content, char_length, word_count
        FROM passages
        WHERE work_id = %s
        ORDER BY sequence_number
        """,
        (str(work_id),),
    )
    passages = cur.fetchall()
    print(f"Passages found: {len(passages)}")

    if not passages:
        print("No passages to process.")
        conn.close()
        return 0

    # 5. Check which KG nodes already exist
    existing_prefix = prefix + "_"
    cur.execute(
        "SELECT node_id FROM kg_nodes WHERE node_id LIKE %s",
        (existing_prefix + "%",),
    )
    existing_nodes = {r[0] for r in cur.fetchall()}
    # Also check exact prefix (no trailing _) for single-digit refs
    cur.execute(
        "SELECT node_id FROM kg_nodes WHERE node_id LIKE %s",
        (prefix + "%",),
    )
    existing_nodes.update(r[0] for r in cur.fetchall())

    # 6. Build node_id for each passage
    nodes_to_insert = []
    edges_to_insert = []
    citations_to_insert = []
    skipped = 0

    for p in passages:
        (passage_id, canonical_ref, cts_urn, book, chapter, section,
         seq_num, text_content, char_length, word_count) = p

        # Build suffix from the most specific available ref
        if book and chapter and section:
            suffix = sanitize_label_part(f"{book}_{chapter}_{section}")
        elif chapter and section:
            suffix = sanitize_label_part(f"{chapter}_{section}")
        elif book and chapter:
            suffix = sanitize_label_part(f"{book}_{chapter}")
        elif chapter:
            suffix = sanitize_label_part(chapter)
        elif section:
            suffix = sanitize_label_part(section)
        else:
            suffix = str(seq_num + 1)

        node_id = f"{prefix}_{suffix}"

        # Handle potential collisions (e.g. duplicate chapter refs)
        if node_id in existing_nodes or any(n[0] == node_id for n in nodes_to_insert):
            # Append sequence number to disambiguate
            node_id = f"{prefix}_{suffix}_s{seq_num}"

        if node_id in existing_nodes:
            skipped += 1
            continue

        # Build label
        if label_template:
            label = label_template.format(
                author=author, title=title, ref=canonical_ref, n=seq_num + 1
            )
        else:
            label = f"{author}, {title}, {canonical_ref}"

        # Truncate label if too long
        if len(label) > 200:
            label = label[:197] + "..."

        # Metadata
        metadata = {
            "language": language,
            "author": author,
            "work_title": title,
            "canonical_ref": canonical_ref,
            "work_canonical_id": canonical_id,
            "db_passage_id": str(passage_id),
            "passage_role": "original",
            "auto_generated": True,
        }
        if school:
            metadata["school"] = school
        if cts_urn:
            metadata["cts_urn"] = cts_urn
        elif work_cts_urn:
            metadata["cts_urn"] = work_cts_urn
        if char_length:
            metadata["char_length"] = char_length
        if word_count:
            metadata["word_count"] = word_count

        nodes_to_insert.append((
            node_id,
            label,
            "passage",
            text_content,
            period,
            json.dumps(metadata),
        ))

        # part_of → work
        edges_to_insert.append((
            node_id,
            work_node_id,
            "part_of",
            json.dumps({"auto_generated": True}),
        ))

        # authored_by → person
        if person_node_id:
            edges_to_insert.append((
                node_id,
                person_node_id,
                "authored_by",
                json.dumps({"auto_generated": True}),
            ))

        # passage_citation: passage_id → kg_node_id
        citations_to_insert.append((
            str(passage_id),
            node_id,
            "primary_source",
            1.0,
        ))

    print("\nSummary:")
    print(f"  Already exist (skip): {skipped}")
    print(f"  Nodes to insert:      {len(nodes_to_insert)}")
    print(f"  Edges to insert:      {len(edges_to_insert)}")
    print(f"  Citations to insert:  {len(citations_to_insert)}")

    if dry_run:
        print("\n  DRY RUN — no changes written. Use --confirm to execute.")
        # Show first 3 examples
        for i, (nid, label, _, desc, _, _) in enumerate(nodes_to_insert[:3]):
            print(f"\n  Example {i+1}: {nid}")
            print(f"    label: {label}")
            print(f"    desc:  {desc[:120]}...")
        conn.close()
        return len(nodes_to_insert)

    # 7. Execute inserts
    try:
        # Insert nodes
        psycopg2.extras.execute_values(
            cur,
            """
            INSERT INTO kg_nodes (node_id, label, type, description, period, metadata)
            VALUES %s
            ON CONFLICT (node_id) DO NOTHING
            """,
            nodes_to_insert,
            template="(%s, %s, %s, %s, %s, %s::jsonb)",
            page_size=100,
        )
        node_count = cur.rowcount
        print(f"\n  Inserted {node_count} KG nodes.")

        # Insert edges
        psycopg2.extras.execute_values(
            cur,
            """
            INSERT INTO kg_edges (source_id, target_id, relation, metadata)
            VALUES %s
            ON CONFLICT DO NOTHING
            """,
            edges_to_insert,
            template="(%s, %s, %s, %s::jsonb)",
            page_size=100,
        )
        edge_count = cur.rowcount
        print(f"  Inserted {edge_count} edges.")

        # Insert passage_citations
        psycopg2.extras.execute_values(
            cur,
            """
            INSERT INTO passage_citations (passage_id, kg_node_id, citation_type, confidence)
            VALUES %s
            ON CONFLICT DO NOTHING
            """,
            citations_to_insert,
            template="(%s::uuid, %s, %s, %s)",
            page_size=100,
        )
        cit_count = cur.rowcount
        print(f"  Inserted {cit_count} passage_citations.")

        conn.commit()
        print("\n  COMMITTED successfully.")

    except Exception as e:
        conn.rollback()
        print(f"\n  ERROR: {e}")
        raise
    finally:
        conn.close()

    return len(nodes_to_insert)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create KG passage nodes from the passages table."
    )
    parser.add_argument("--list", action="store_true", help="List works with passages")
    parser.add_argument("--canonical-id", help="Work canonical_id from ancient_works")
    parser.add_argument("--prefix", help="KG node_id prefix (e.g. passage_cic_fat)")
    parser.add_argument("--work-node", help="Existing KG work node_id")
    parser.add_argument("--person-node", help="Existing KG person node_id (optional)")
    parser.add_argument("--label-template", help="Label template with {author}, {title}, {ref}, {n}")
    parser.add_argument("--confirm", action="store_true", help="Actually write to DB")
    parser.add_argument("--db-url", help="Database URL (default: DATABASE_URL env var)")
    args = parser.parse_args()

    db_url = args.db_url or get_db_url()

    if args.list:
        list_works(db_url)
        return

    if not args.canonical_id or not args.prefix or not args.work_node:
        parser.error("--canonical-id, --prefix, and --work-node are required (or use --list)")

    create_kg_nodes(
        db_url=db_url,
        canonical_id=args.canonical_id,
        prefix=args.prefix,
        work_node_id=args.work_node,
        person_node_id=args.person_node,
        dry_run=not args.confirm,
        label_template=args.label_template,
    )


if __name__ == "__main__":
    main()
