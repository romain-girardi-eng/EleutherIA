#!/usr/bin/env python3
"""
Deep Analysis of Knowledge Graph Edges

SECURITY NOTE:
- This repository must NOT contain hardcoded DB credentials.
- The legacy version of this script did; it has been removed.

For JSON-based deep analysis (recommended for the shipped KG export), run:
  python3 scripts/maintenance/audit_kg_json.py --write

If you want DB-based analysis, set DATABASE_URL and adapt queries as needed.
"""

from __future__ import annotations

import json
import os
from typing import Any, cast

import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import RealDictCursor


def get_db_connection() -> connection:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is not set. For JSON audits run: "
            "python3 scripts/maintenance/audit_kg_json.py --write"
        )
    return psycopg2.connect(database_url)


def analyze_relation_patterns(conn: connection) -> list[dict[str, Any]]:
    """Analyze which node types connect to which via which relations"""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT
                src.type as source_type,
                e.relation,
                tgt.type as target_type,
                COUNT(*) as count
            FROM public.kg_edges e
            JOIN public.kg_nodes src ON e.source_id = src.node_id
            JOIN public.kg_nodes tgt ON e.target_id = tgt.node_id
            GROUP BY src.type, e.relation, tgt.type
            ORDER BY count DESC
        """)
        return cast(list[dict[str, Any]], cur.fetchall())


def find_high_degree_nodes(conn: connection) -> list[dict[str, Any]]:
    """Find nodes with unusually high in-degree or out-degree"""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            WITH out_degree AS (
                SELECT source_id, COUNT(*) as out_count
                FROM public.kg_edges
                GROUP BY source_id
            ),
            in_degree AS (
                SELECT target_id, COUNT(*) as in_count
                FROM public.kg_edges
                GROUP BY target_id
            )
            SELECT
                n.node_id,
                n.label,
                n.type,
                n.period,
                COALESCE(out_degree.out_count, 0) as outgoing,
                COALESCE(in_degree.in_count, 0) as incoming,
                COALESCE(out_degree.out_count, 0) + COALESCE(in_degree.in_count, 0) as total
            FROM public.kg_nodes n
            LEFT JOIN out_degree ON n.node_id = out_degree.source_id
            LEFT JOIN in_degree ON n.node_id = in_degree.target_id
            ORDER BY total DESC
            LIMIT 30
        """)
        return cast(list[dict[str, Any]], cur.fetchall())


def find_isolated_nodes(conn: connection) -> list[dict[str, Any]]:
    """Find nodes with no edges at all"""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT
                n.node_id,
                n.label,
                n.type,
                n.period
            FROM public.kg_nodes n
            WHERE NOT EXISTS (
                SELECT 1 FROM public.kg_edges e
                WHERE e.source_id = n.node_id OR e.target_id = n.node_id
            )
            ORDER BY n.type, n.label
        """)
        return cast(list[dict[str, Any]], cur.fetchall())


def find_weakly_connected_nodes(conn: connection) -> list[dict[str, Any]]:
    """Find nodes with only 1 or 2 connections"""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            WITH node_degree AS (
                SELECT
                    n.node_id,
                    n.label,
                    n.type,
                    n.period,
                    COUNT(DISTINCT e.edge_id) as edge_count
                FROM public.kg_nodes n
                LEFT JOIN public.kg_edges e ON n.node_id = e.source_id OR n.node_id = e.target_id
                GROUP BY n.node_id, n.label, n.type, n.period
            )
            SELECT *
            FROM node_degree
            WHERE edge_count > 0 AND edge_count <= 2
            ORDER BY edge_count, type, label
        """)
        return cast(list[dict[str, Any]], cur.fetchall())


def analyze_self_loops(conn: connection) -> list[dict[str, Any]]:
    """Find edges where source equals target (self-loops)"""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT
                e.edge_id,
                e.source_id,
                e.relation,
                n.label,
                n.type
            FROM public.kg_edges e
            JOIN public.kg_nodes n ON e.source_id = n.node_id
            WHERE e.source_id = e.target_id
        """)
        return cast(list[dict[str, Any]], cur.fetchall())


def analyze_duplicate_edges(conn: connection) -> list[dict[str, Any]]:
    """Find duplicate edges (same source, target, relation)"""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT
                source_id,
                target_id,
                relation,
                COUNT(*) as count,
                ARRAY_AGG(edge_id::text) as edge_ids
            FROM public.kg_edges
            GROUP BY source_id, target_id, relation
            HAVING COUNT(*) > 1
        """)
        return cast(list[dict[str, Any]], cur.fetchall())


def analyze_relation_inconsistencies(conn: connection) -> list[dict[str, Any]]:
    """Find potentially inconsistent relation uses"""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Find cases where A->B has multiple different relation types
        cur.execute("""
            SELECT
                source_id,
                target_id,
                ARRAY_AGG(DISTINCT relation) as relations,
                COUNT(DISTINCT relation) as relation_count
            FROM public.kg_edges
            GROUP BY source_id, target_id
            HAVING COUNT(DISTINCT relation) > 1
        """)
        return cast(list[dict[str, Any]], cur.fetchall())


def identify_missing_scholarly_edges(conn: connection) -> list[dict[str, Any]]:
    """Identify scholars who should be connected to concepts but aren't"""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT
                n.node_id,
                n.label,
                COUNT(e.edge_id) as edge_count
            FROM public.kg_nodes n
            LEFT JOIN public.kg_edges e ON n.node_id = e.source_id OR n.node_id = e.target_id
            WHERE n.type = 'scholar'
            GROUP BY n.node_id, n.label
            ORDER BY edge_count ASC
            LIMIT 20
        """)
        return cast(list[dict[str, Any]], cur.fetchall())


def analyze_period_distribution(conn: connection) -> list[dict[str, Any]]:
    """Analyze how edges distribute across periods"""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT
                src.period as source_period,
                tgt.period as target_period,
                e.relation,
                COUNT(*) as count
            FROM public.kg_edges e
            JOIN public.kg_nodes src ON e.source_id = src.node_id
            JOIN public.kg_nodes tgt ON e.target_id = tgt.node_id
            WHERE src.period IS NOT NULL AND tgt.period IS NOT NULL
            GROUP BY src.period, tgt.period, e.relation
            ORDER BY count DESC
            LIMIT 50
        """)
        return cast(list[dict[str, Any]], cur.fetchall())


def check_concept_to_argument_coverage(conn: connection) -> list[dict[str, Any]]:
    """Check if key concepts are properly linked to arguments"""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT
                n.node_id,
                n.label,
                n.type,
                COUNT(DISTINCT CASE WHEN e.relation = 'employs' THEN e.source_id END) as employed_by_count,
                COUNT(DISTINCT CASE WHEN e.relation = 'presupposes' THEN e.source_id END) as presupposed_by_count
            FROM public.kg_nodes n
            LEFT JOIN public.kg_edges e ON n.node_id = e.target_id
            WHERE n.type = 'concept'
            GROUP BY n.node_id, n.label, n.type
            HAVING COUNT(DISTINCT CASE WHEN e.relation = 'employs' THEN e.source_id END) = 0
               AND COUNT(DISTINCT CASE WHEN e.relation = 'presupposes' THEN e.source_id END) = 0
            ORDER BY n.label
        """)
        return cast(list[dict[str, Any]], cur.fetchall())


def main() -> None:
    print("=" * 80)
    print("DEEP KNOWLEDGE GRAPH EDGE ANALYSIS")
    print("=" * 80)
    print()

    conn = get_db_connection()

    try:
        # 1. Relation patterns by node type
        print("1. RELATION PATTERNS BY NODE TYPE")
        print("=" * 80)
        patterns = analyze_relation_patterns(conn)
        print("Top 30 relation patterns:")
        print(f"{'Source Type':<20} {'Relation':<25} {'Target Type':<20} {'Count':>10}")
        print("-" * 80)
        for p in patterns[:30]:
            print(
                f"{p['source_type']:<20} {p['relation']:<25} {p['target_type']:<20} {p['count']:>10}"
            )
        print()

        # 2. High-degree nodes (hubs)
        print("2. HIGH-DEGREE NODES (HUBS)")
        print("=" * 80)
        hubs = find_high_degree_nodes(conn)
        print(f"{'Node':<50} {'Type':<15} {'Out':>5} {'In':>5} {'Total':>6}")
        print("-" * 80)
        for hub in hubs:
            label = hub["label"][:48]
            print(
                f"{label:<50} {hub['type']:<15} {hub['outgoing']:>5} {hub['incoming']:>5} {hub['total']:>6}"
            )
        print()

        # 3. Isolated nodes
        print("3. ISOLATED NODES (NO CONNECTIONS)")
        print("=" * 80)
        isolated = find_isolated_nodes(conn)
        if isolated:
            print(f"⚠️  Found {len(isolated)} isolated nodes")
            print(f"\n{'Node':<60} {'Type':<15} {'Period':<20}")
            print("-" * 80)
            for node in isolated[:20]:
                label = node["label"][:58]
                period = node["period"] or "N/A"
                print(f"{label:<60} {node['type']:<15} {period:<20}")
            if len(isolated) > 20:
                print(f"\n... and {len(isolated) - 20} more")
        else:
            print("✓ No isolated nodes")
        print()

        # 4. Weakly connected nodes
        print("4. WEAKLY CONNECTED NODES (1-2 connections)")
        print("=" * 80)
        weak = find_weakly_connected_nodes(conn)
        if weak:
            print(f"Found {len(weak)} weakly connected nodes (showing first 20)")
            print(f"\n{'Node':<60} {'Type':<15} {'Edges':>6}")
            print("-" * 80)
            for node in weak[:20]:
                label = node["label"][:58]
                print(f"{label:<60} {node['type']:<15} {node['edge_count']:>6}")
        print()

        # 5. Self-loops
        print("5. SELF-LOOPS")
        print("=" * 80)
        loops = analyze_self_loops(conn)
        if loops:
            print(f"⚠️  Found {len(loops)} self-loops")
            for loop in loops:
                print(f"  {loop['label']} --[{loop['relation']}]--> {loop['label']}")
        else:
            print("✓ No self-loops found")
        print()

        # 6. Duplicate edges
        print("6. DUPLICATE EDGES")
        print("=" * 80)
        dupes = analyze_duplicate_edges(conn)
        if dupes:
            print(f"⚠️  Found {len(dupes)} sets of duplicate edges")
            for i, dupe in enumerate(dupes[:10], 1):
                print(
                    f"{i}. {dupe['source_id']} --[{dupe['relation']}]--> {dupe['target_id']}"
                )
                print(f"   Count: {dupe['count']}, IDs: {dupe['edge_ids']}")
            if len(dupes) > 10:
                print(f"... and {len(dupes) - 10} more")
        else:
            print("✓ No duplicate edges")
        print()

        # 7. Relation inconsistencies
        print("7. MULTIPLE RELATIONS BETWEEN SAME NODE PAIRS")
        print("=" * 80)
        inconsistencies = analyze_relation_inconsistencies(conn)
        if inconsistencies:
            print(
                f"Found {len(inconsistencies)} node pairs with multiple relation types"
            )
            print(
                "(This may be intentional - nodes can have multiple types of relationships)"
            )
            for i, inc in enumerate(inconsistencies[:10], 1):
                print(f"{i}. {inc['source_id']} <--> {inc['target_id']}")
                print(f"   Relations: {inc['relations']}")
        else:
            print("✓ Each node pair has at most one relation type")
        print()

        # 8. Scholar connectivity
        print("8. SCHOLAR CONNECTIVITY")
        print("=" * 80)
        scholars = identify_missing_scholarly_edges(conn)
        if scholars:
            print("Scholars with fewest connections (potential missing edges):")
            print(f"{'Scholar':<60} {'Edges':>6}")
            print("-" * 80)
            for scholar in scholars:
                label = scholar["label"][:58]
                print(f"{label:<60} {scholar['edge_count']:>6}")
        print()

        # 9. Period distribution
        print("9. CROSS-PERIOD EDGE PATTERNS (Top 30)")
        print("=" * 80)
        period_dist = analyze_period_distribution(conn)
        print(
            f"{'Source Period':<20} {'Relation':<25} {'Target Period':<20} {'Count':>6}"
        )
        print("-" * 80)
        for p in period_dist[:30]:
            print(
                f"{p['source_period']:<20} {p['relation']:<25} {p['target_period']:<20} {p['count']:>6}"
            )
        print()

        # 10. Orphaned concepts
        print("10. CONCEPTS NOT EMPLOYED OR PRESUPPOSED BY ANY ARGUMENT")
        print("=" * 80)
        orphaned_concepts = check_concept_to_argument_coverage(conn)
        if orphaned_concepts:
            print(f"⚠️  Found {len(orphaned_concepts)} concepts with no argument links")
            print(
                "\nThese concepts may need connections to arguments that employ/presuppose them:"
            )
            for i, concept in enumerate(orphaned_concepts[:20], 1):
                print(f"{i}. {concept['label']}")
            if len(orphaned_concepts) > 20:
                print(f"... and {len(orphaned_concepts) - 20} more")
        else:
            print("✓ All concepts are linked to arguments")
        print()

        # Export detailed results
        results = {
            "relation_patterns": [dict(p) for p in patterns],
            "high_degree_nodes": [dict(h) for h in hubs],
            "isolated_nodes": [dict(n) for n in isolated],
            "weakly_connected": [dict(n) for n in weak],
            "self_loops": [dict(loop) for loop in loops],
            "duplicates": [dict(d) for d in dupes],
            "multiple_relations": [dict(i) for i in inconsistencies],
            "scholar_connectivity": [dict(s) for s in scholars],
            "period_distribution": [dict(p) for p in period_dist],
            "orphaned_concepts": [dict(c) for c in orphaned_concepts],
        }

        output_file = "/Users/romaingirardi/Documents/Ancient Free Will Database/kg_edge_deep_analysis_results.json"
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2, default=str)

        print(f"✓ Detailed results exported to: {output_file}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
