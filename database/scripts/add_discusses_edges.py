#!/usr/bin/env python3
"""Add 'discusses' edges between work KG nodes and concept/argument nodes.

Derives relationships from existing KG edges:
- Forward: passage --discusses/source_for/etc--> concept, passage --part_of--> work
- Reverse: concept --evidenced_by/grounded_in--> passage, passage --part_of--> work

Only creates edges where >= 3 distinct passages link a work to a concept.
Skips edges that already exist (ON CONFLICT DO NOTHING via pre-check).
"""

import argparse
import asyncio
import json
import os

import asyncpg

SCHEMA = "free_will"

# Forward relations: passage -> concept/argument
FORWARD_RELATIONS = (
    "discusses",
    "source_for",
    "contributes_to",
    "supports",
    "exemplifies",
    "employs",
    "critiques",
    "responds_to",
)

# Reverse relations: concept/argument -> passage
REVERSE_RELATIONS = ("evidenced_by", "grounded_in")

TARGET_TYPES = ("concept", "argument", "debate", "position")

QUERY_FORWARD = f"""
SELECT
    pw.target_id AS work_node_id,
    pc.target_id AS concept_node_id,
    kn_concept.label AS concept_label,
    kn_concept.type AS concept_type,
    kn_work.label AS work_label,
    count(DISTINCT pc.source_id) AS passage_count,
    array_agg(DISTINCT pc.source_id) AS passage_ids
FROM {SCHEMA}.kg_edges pc
JOIN {SCHEMA}.kg_nodes kn_concept
    ON kn_concept.node_id = pc.target_id
    AND kn_concept.type = ANY($1::text[])
JOIN {SCHEMA}.kg_edges pw
    ON pw.source_id = pc.source_id
    AND pw.relation = 'part_of'
JOIN {SCHEMA}.kg_nodes kn_work
    ON kn_work.node_id = pw.target_id
    AND kn_work.type = 'work'
WHERE pc.relation = ANY($2::text[])
    AND pc.source_id LIKE 'passage_%'
GROUP BY pw.target_id, kn_work.label, pc.target_id, kn_concept.label, kn_concept.type
HAVING count(DISTINCT pc.source_id) >= $3
"""

QUERY_REVERSE = f"""
SELECT
    pw.target_id AS work_node_id,
    cp.source_id AS concept_node_id,
    kn_concept.label AS concept_label,
    kn_concept.type AS concept_type,
    kn_work.label AS work_label,
    count(DISTINCT cp.target_id) AS passage_count,
    array_agg(DISTINCT cp.target_id) AS passage_ids
FROM {SCHEMA}.kg_edges cp
JOIN {SCHEMA}.kg_nodes kn_concept
    ON kn_concept.node_id = cp.source_id
    AND kn_concept.type = ANY($1::text[])
JOIN {SCHEMA}.kg_edges pw
    ON pw.source_id = cp.target_id
    AND pw.relation = 'part_of'
JOIN {SCHEMA}.kg_nodes kn_work
    ON kn_work.node_id = pw.target_id
    AND kn_work.type = 'work'
WHERE cp.relation = ANY($2::text[])
    AND cp.target_id LIKE 'passage_%'
GROUP BY pw.target_id, kn_work.label, cp.source_id, kn_concept.label, kn_concept.type
HAVING count(DISTINCT cp.target_id) >= $3
"""

INSERT_EDGE = f"""
INSERT INTO {SCHEMA}.kg_edges (source_id, target_id, relation, metadata)
VALUES ($1, $2, 'discusses', $3)
"""

CHECK_EXISTING = f"""
SELECT source_id, target_id
FROM {SCHEMA}.kg_edges
WHERE relation = 'discusses'
    AND source_id LIKE 'work_%'
    AND target_id = ANY($1::text[])
"""


async def main(min_passages: int, dry_run: bool) -> None:
    database_url = os.environ["DATABASE_URL"]

    conn = await asyncpg.connect(dsn=database_url, statement_cache_size=0)

    try:
        # Collect work->concept pairs from both directions
        pairs: dict[tuple[str, str], dict] = {}

        forward_rows = await conn.fetch(
            QUERY_FORWARD,
            list(TARGET_TYPES),
            list(FORWARD_RELATIONS),
            min_passages,
        )
        for row in forward_rows:
            key = (row["work_node_id"], row["concept_node_id"])
            if key not in pairs:
                pairs[key] = {
                    "work_label": row["work_label"],
                    "concept_label": row["concept_label"],
                    "concept_type": row["concept_type"],
                    "passage_count": 0,
                    "passage_ids": set(),
                }
            pairs[key]["passage_count"] += row["passage_count"]
            pairs[key]["passage_ids"].update(row["passage_ids"])

        reverse_rows = await conn.fetch(
            QUERY_REVERSE,
            list(TARGET_TYPES),
            list(REVERSE_RELATIONS),
            min_passages,
        )
        for row in reverse_rows:
            key = (row["work_node_id"], row["concept_node_id"])
            if key not in pairs:
                pairs[key] = {
                    "work_label": row["work_label"],
                    "concept_label": row["concept_label"],
                    "concept_type": row["concept_type"],
                    "passage_count": 0,
                    "passage_ids": set(),
                }
            pairs[key]["passage_count"] += row["passage_count"]
            pairs[key]["passage_ids"].update(row["passage_ids"])

        # Filter: require >= min_passages distinct passages total
        pairs = {
            k: v for k, v in pairs.items() if len(v["passage_ids"]) >= min_passages
        }

        print(f"Found {len(pairs)} work->concept pairs with >= {min_passages} passage evidence")

        # Check existing discusses edges
        all_concept_ids = list({k[1] for k in pairs})
        existing_edges: set[tuple[str, str]] = set()
        if all_concept_ids:
            existing = await conn.fetch(CHECK_EXISTING, all_concept_ids)
            existing_edges = {(row["source_id"], row["target_id"]) for row in existing}

        print(f"Already existing discusses edges (will skip): {len(existing_edges)}")

        # Filter out existing
        new_pairs = {k: v for k, v in pairs.items() if k not in existing_edges}
        print(f"New edges to create: {len(new_pairs)}")

        if not new_pairs:
            print("Nothing to do.")
            return

        # Sort by passage count descending for display
        sorted_pairs = sorted(new_pairs.items(), key=lambda x: len(x[1]["passage_ids"]), reverse=True)

        for (_work_id, _concept_id), info in sorted_pairs:
            n = len(info["passage_ids"])
            print(
                f"  {info['work_label']}"
                f" -> {info['concept_label']}"
                f" [{info['concept_type']}]"
                f" ({n} passages)"
            )

        if dry_run:
            print("\n[DRY RUN] No edges created.")
            return

        # Insert edges
        created = 0
        for (work_id, concept_id), info in sorted_pairs:
            passage_list = sorted(info["passage_ids"])
            metadata = json.dumps({
                "source": "add_discusses_edges.py",
                "evidence_count": len(passage_list),
                "sample_passages": passage_list[:5],
            })
            await conn.execute(INSERT_EDGE, work_id, concept_id, metadata)
            created += 1

        print(f"\nCreated {created} new discusses edges.")

    finally:
        await conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add discusses edges between works and concepts")
    parser.add_argument(
        "--min-passages",
        type=int,
        default=3,
        help="Minimum distinct passages linking a work to a concept (default: 3)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created without writing to DB",
    )
    args = parser.parse_args()
    asyncio.run(main(min_passages=args.min_passages, dry_run=args.dry_run))
