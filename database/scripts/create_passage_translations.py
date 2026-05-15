#!/usr/bin/env python3
"""
Bulk-insert English translation KG nodes for passage nodes.

Two-Node Architecture:
  - Source node (original language) → untouched
  - English node ({node_id}_en)    → AI translation, linked via translation_of edge

Usage:
    python3 create_passage_translations.py --translations /tmp/translations_batch_1.json [--confirm]

    # Dry-run (default): shows what would be inserted
    # --confirm: actually writes to DB

Input JSON format:
    [
        {
            "node_id": "passage_alex_fat_1",       # original node ID
            "translation": "English translation..."  # English description
        },
        ...
    ]

Edges created per _en node:
    1. translation_of → original passage node
    2. part_of → same work node (copied from original)
    3. authored_by → same person node (copied from original)
"""

import argparse
import json
import os

import psycopg2
import psycopg2.extras


def get_db_url():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL is required")
    return db_url


def insert_translations(translations, db_url, dry_run=True):
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute("SET search_path TO free_will")

    # Collect all original node IDs
    node_ids = [t["node_id"] for t in translations]

    # Fetch original node metadata + edges in batch
    cur.execute(
        """
        SELECT node_id, label, period, metadata
        FROM kg_nodes
        WHERE node_id = ANY(%s)
        """,
        (node_ids,),
    )
    originals = {r[0]: {"label": r[1], "period": r[2], "metadata": r[3]} for r in cur.fetchall()}

    # Fetch part_of edges
    cur.execute(
        """
        SELECT source_id, target_id
        FROM kg_edges
        WHERE source_id = ANY(%s) AND relation = 'part_of'
        """,
        (node_ids,),
    )
    part_of = {r[0]: r[1] for r in cur.fetchall()}

    # Fetch authored_by edges
    cur.execute(
        """
        SELECT source_id, target_id
        FROM kg_edges
        WHERE source_id = ANY(%s) AND relation = 'authored_by'
        """,
        (node_ids,),
    )
    authored_by = {r[0]: r[1] for r in cur.fetchall()}

    # Check which _en nodes already exist
    en_ids = [t["node_id"] + "_en" for t in translations]
    cur.execute(
        "SELECT node_id FROM kg_nodes WHERE node_id = ANY(%s)",
        (en_ids,),
    )
    existing = {r[0] for r in cur.fetchall()}

    # Prepare inserts
    nodes_to_insert = []
    edges_to_insert = []
    skipped = 0

    for t in translations:
        orig_id = t["node_id"]
        en_id = orig_id + "_en"

        if en_id in existing:
            skipped += 1
            continue

        if orig_id not in originals:
            print(f"  WARNING: {orig_id} not found in DB, skipping")
            skipped += 1
            continue

        orig = originals[orig_id]
        orig_meta = orig["metadata"] or {}

        # Build _en metadata
        en_meta = {
            "language": "eng",
            "source": "ai_translation",
            "source_model": "claude-opus-4-6",
            "source_language": orig_meta.get("language", "unknown"),
            "original_node_id": orig_id,
            "source_passage_id": orig_meta.get("db_passage_id") or orig_id,
            "passage_role": "translation",
            "work_title": orig_meta.get("work_title", ""),
            "author": orig_meta.get("author", ""),
            "auto_generated": True,
        }
        # Carry over useful fields
        for key in ("edition", "canonical_ref", "cts_urn", "school", "db_passage_id"):
            if key in orig_meta:
                en_meta[key] = orig_meta[key]

        # Build label
        en_label = orig["label"] + " (English)" if orig["label"] else en_id

        nodes_to_insert.append((
            en_id,
            en_label,
            "passage",
            t["translation"],
            orig["period"],
            json.dumps(en_meta),
        ))

        # translation_of edge
        edges_to_insert.append((
            en_id,
            orig_id,
            "translation_of",
            json.dumps({
                "auto_generated": True,
                "source_model": "claude-opus-4-6",
                "source_language": orig_meta.get("language", "unknown"),
            }),
        ))

        # part_of edge (same work)
        if orig_id in part_of:
            edges_to_insert.append((
                en_id,
                part_of[orig_id],
                "part_of",
                json.dumps({"auto_generated": True}),
            ))

        # authored_by edge (same person)
        if orig_id in authored_by:
            edges_to_insert.append((
                en_id,
                authored_by[orig_id],
                "authored_by",
                json.dumps({"auto_generated": True}),
            ))

    print("\nSummary:")
    print(f"  Translations provided: {len(translations)}")
    print(f"  Already exist (skip):  {skipped}")
    print(f"  Nodes to insert:       {len(nodes_to_insert)}")
    print(f"  Edges to insert:       {len(edges_to_insert)}")

    if dry_run:
        print("\n  DRY RUN — no changes written. Use --confirm to execute.")
        conn.close()
        return len(nodes_to_insert)

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

        conn.commit()
        print(f"\n  COMMITTED: {len(nodes_to_insert)} nodes + {len(edges_to_insert)} edges")
    except Exception as e:
        conn.rollback()
        print(f"\n  ERROR: {e}")
        raise
    finally:
        conn.close()

    return len(nodes_to_insert)


def main():
    parser = argparse.ArgumentParser(description="Insert English translation KG nodes")
    parser.add_argument("--translations", required=True, help="JSON file with translations")
    parser.add_argument("--confirm", action="store_true", help="Actually write to DB")
    parser.add_argument("--db-url", help="Database URL (or set DATABASE_URL)")
    args = parser.parse_args()

    db_url = args.db_url or get_db_url()

    with open(args.translations) as f:
        translations = json.load(f)

    print(f"Loaded {len(translations)} translations from {args.translations}")
    insert_translations(translations, db_url, dry_run=not args.confirm)


if __name__ == "__main__":
    main()
