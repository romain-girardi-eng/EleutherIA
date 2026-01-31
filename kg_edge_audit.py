#!/usr/bin/env python3
"""
Knowledge Graph Edge Quality Audit

SECURITY NOTE:
- This repository must NOT contain hardcoded DB credentials.
- The legacy version of this script did; it has been removed.

If you want to audit the KG that the FastAPI backend serves from disk, use:
  python3 scripts/maintenance/audit_kg_json.py --write

If you want to audit a Postgres-backed KG, set DATABASE_URL and adapt as needed.
"""

from __future__ import annotations

import json
import os
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any, cast

import psycopg2
from psycopg2.extensions import connection

from psycopg2.extras import RealDictCursor


def get_db_connection() -> connection:
    """Establish database connection via DATABASE_URL."""
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is not set. For JSON audits run: "
            "python3 scripts/maintenance/audit_kg_json.py --write"
        )
    return psycopg2.connect(database_url)

def fetch_all_edges(conn: connection) -> list[dict[str, Any]]:
    """Retrieve all edges from kg_edges table"""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT
                edge_id, source_id, target_id, relation,
                metadata, created_at
            FROM public.kg_edges
            ORDER BY relation, source_id, target_id
        """)
        return cast(list[dict[str, Any]], cur.fetchall())

def fetch_all_nodes(conn: connection) -> list[dict[str, Any]]:
    """Retrieve all nodes from kg_nodes table"""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT
                node_id, label, type, period, description,
                alternative_names, metadata,
                created_at, updated_at
            FROM public.kg_nodes
            ORDER BY type, label
        """)
        return cast(list[dict[str, Any]], cur.fetchall())

def get_edge_count(conn: connection) -> int:
    """Get total edge count"""
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM public.kg_edges")
        result = cur.fetchone()
        return int(result[0]) if result else 0

def get_node_count(conn: connection) -> int:
    """Get total node count"""
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM public.kg_nodes")
        result = cur.fetchone()
        return int(result[0]) if result else 0

def analyze_relation_types(edges: list[dict[str, Any]]) -> dict[str, int]:
    """Analyze distribution of relation types"""
    relation_counts = Counter(edge['relation'] for edge in edges)
    return dict(sorted(relation_counts.items(), key=lambda x: x[1], reverse=True))

def find_orphaned_edges(edges: list[dict[str, Any]], node_ids: set[Any]) -> list[dict[str, Any]]:
    """Find edges pointing to non-existent nodes"""
    orphaned = []
    for edge in edges:
        if edge['source_id'] not in node_ids:
            orphaned.append({
                'edge_id': edge['edge_id'],
                'issue': 'missing_source',
                'source_id': edge['source_id'],
                'target_id': edge['target_id'],
                'relation': edge['relation']
            })
        if edge['target_id'] not in node_ids:
            orphaned.append({
                'edge_id': edge['edge_id'],
                'issue': 'missing_target',
                'source_id': edge['source_id'],
                'target_id': edge['target_id'],
                'relation': edge['relation']
            })
    return orphaned

def analyze_metadata_completeness(edges: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Check metadata quality and completeness"""
    total_edges = len(edges)
    with_metadata = 0
    without_metadata = 0
    metadata_fields: Counter[str] = Counter()

    edges_without_metadata: list[dict[str, Any]] = []

    for edge in edges:
        if edge['metadata'] and isinstance(edge['metadata'], dict) and edge['metadata']:
            with_metadata += 1
            for key in edge['metadata'].keys():
                metadata_fields[key] += 1
        else:
            without_metadata += 1
            edges_without_metadata.append({
                'edge_id': edge['edge_id'],
                'source': edge['source_id'],
                'target': edge['target_id'],
                'relation': edge['relation']
            })

    stats: dict[str, Any] = {
        'total_edges': total_edges,
        'with_metadata': with_metadata,
        'without_metadata': without_metadata,
        'metadata_fields': metadata_fields
    }

    return stats, edges_without_metadata

def analyze_bidirectional_consistency(edges: list[dict[str, Any]], nodes_by_id: dict[Any, dict[str, Any]]) -> list[dict[str, Any]]:
    """Check if bidirectional relationships are properly represented"""

    # Define expected bidirectional pairs
    bidirectional_pairs = {
        'influences': 'influenced_by',
        'influenced_by': 'influences',
        'critiques': 'critiqued_by',
        'critiqued_by': 'critiques',
        'responds_to': 'responded_to_by',
        'responded_to_by': 'responds_to',
        'develops': 'developed_by',
        'developed_by': 'develops',
        'opposes': 'opposed_by',
        'opposed_by': 'opposes'
    }

    # Build edge lookup
    edge_lookup = defaultdict(list)
    for edge in edges:
        key = (edge['source_id'], edge['target_id'], edge['relation'])
        edge_lookup[key].append(edge)

    missing_reciprocal = []

    for edge in edges:
        if edge['relation'] in bidirectional_pairs:
            reciprocal_type = bidirectional_pairs[edge['relation']]
            reciprocal_key = (edge['target_id'], edge['source_id'], reciprocal_type)

            if reciprocal_key not in edge_lookup:
                source_node = nodes_by_id.get(edge['source_id'], {})
                target_node = nodes_by_id.get(edge['target_id'], {})
                missing_reciprocal.append({
                    'existing_edge_id': str(edge['edge_id']),
                    'source': edge['source_id'],
                    'source_name': source_node.get('label', 'UNKNOWN'),
                    'target': edge['target_id'],
                    'target_name': target_node.get('label', 'UNKNOWN'),
                    'existing_relation': edge['relation'],
                    'missing_relation': reciprocal_type
                })

    return missing_reciprocal

def analyze_temporal_consistency(edges: list[dict[str, Any]], nodes_by_id: dict[Any, dict[str, Any]]) -> list[dict[str, Any]]:
    """Check if edges respect chronological order where applicable"""

    # Relations that imply temporal direction
    temporal_relations = {
        'influences': 'forward',  # Source should be earlier or contemporary
        'precedes': 'forward',
        'develops': 'forward',
        'responds_to': 'backward',  # Source responds to earlier target
        'critiques': 'any',  # Can critique earlier or contemporary
    }

    temporal_violations = []

    for edge in edges:
        if edge['relation'] not in temporal_relations:
            continue

        source_node = nodes_by_id.get(edge['source_id'])
        target_node = nodes_by_id.get(edge['target_id'])

        if not source_node or not target_node:
            continue

        # Extract period information - check both direct period field and metadata
        source_period = source_node.get('period')
        if not source_period and source_node.get('metadata'):
            source_period = source_node.get('metadata', {}).get('period')

        target_period = target_node.get('period')
        if not target_period and target_node.get('metadata'):
            target_period = target_node.get('metadata', {}).get('period')

        if not source_period or not target_period:
            continue

        # Define period ordering (rough chronology)
        period_order = {
            'Presocratic': 1,
            'Classical': 2,
            'Hellenistic': 3,
            'Imperial': 4,
            'Late Antiquity': 5,
            'Early Christian': 5,  # Overlaps with Late Antiquity
            'Modern': 6
        }

        source_order = period_order.get(source_period, 0)
        target_order = period_order.get(target_period, 0)

        direction = temporal_relations[edge['relation']]

        if direction == 'forward' and source_order > target_order:
            temporal_violations.append({
                'edge_id': edge['edge_id'],
                'source': source_node['label'],
                'source_period': source_period,
                'target': target_node['label'],
                'target_period': target_period,
                'relation': edge['relation'],
                'issue': f"Source ({source_period}) is later than target ({target_period})"
            })
        elif direction == 'backward' and source_order < target_order:
            temporal_violations.append({
                'edge_id': edge['edge_id'],
                'source': source_node['label'],
                'source_period': source_period,
                'target': target_node['label'],
                'target_period': target_period,
                'relation': edge['relation'],
                'issue': f"Source ({source_period}) is earlier than target ({target_period})"
            })

    return temporal_violations

def suggest_missing_edges(nodes_by_id: dict[Any, dict[str, Any]]) -> list[dict[str, Any]]:
    """Suggest important missing edges based on node analysis"""

    suggestions: list[dict[str, Any]] = []

    # Example: Check for Stoic school connections
    stoic_nodes = [n for n in nodes_by_id.values()
                   if n.get('metadata', {}).get('school') == 'Stoic']

    # Add more sophisticated logic as needed

    return suggestions

def calculate_quality_score(edges: list[dict[str, Any]], nodes_by_id: dict[Any, dict[str, Any]], orphaned: list[dict[str, Any]], missing_metadata: list[dict[str, Any]]) -> tuple[float, dict[str, float]]:
    """Calculate overall quality score for the knowledge graph"""

    total_edges = len(edges)

    scores = {
        'orphan_penalty': max(0, 100 - (len(orphaned) / total_edges * 100)) if total_edges > 0 else 0,
        'metadata_completeness': (1 - len(missing_metadata) / total_edges * 1) * 100 if total_edges > 0 else 0,
        'node_coverage': len(set(e['source_id'] for e in edges) | set(e['target_id'] for e in edges)) / len(nodes_by_id) * 100 if nodes_by_id else 0
    }

    overall_score = sum(scores.values()) / len(scores)

    return overall_score, scores

def main() -> None:
    """Execute comprehensive edge audit"""

    print("=" * 80)
    print("KNOWLEDGE GRAPH EDGE QUALITY AUDIT")
    print("EleutherIA - Ancient Free Will Database")
    print(f"Audit Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()

    # Connect to database
    print("Connecting to database...")
    conn = get_db_connection()

    try:
        # Fetch data
        print("Fetching all edges...")
        edges = fetch_all_edges(conn)
        edge_count = len(edges)

        print("Fetching all nodes...")
        nodes = fetch_all_nodes(conn)
        node_count = len(nodes)

        print(f"✓ Retrieved {edge_count} edges and {node_count} nodes")
        print()

        # Build lookup structures
        node_ids = {node['node_id'] for node in nodes}
        nodes_by_id = {node['node_id']: node for node in nodes}

        # 1. RELATION TYPE DISTRIBUTION
        print("=" * 80)
        print("1. RELATION TYPE DISTRIBUTION")
        print("=" * 80)
        relation_dist = analyze_relation_types(edges)

        print(f"Total unique relation types: {len(relation_dist)}")
        print()
        print(f"{'Relation Type':<40} {'Count':>10} {'%':>10}")
        print("-" * 80)
        for rel_type, count in relation_dist.items():
            percentage = (count / edge_count * 100) if edge_count > 0 else 0
            print(f"{rel_type:<40} {count:>10} {percentage:>9.1f}%")
        print()

        # 2. ORPHANED EDGES
        print("=" * 80)
        print("2. ORPHANED EDGES ANALYSIS")
        print("=" * 80)
        orphaned = find_orphaned_edges(edges, node_ids)

        if orphaned:
            print(f"⚠️  Found {len(orphaned)} orphaned edges")
            print()
            for i, orph in enumerate(orphaned[:20], 1):  # Show first 20
                print(f"{i}. Edge {orph['edge_id']}: {orph['issue']}")
                print(f"   {orph['source_id']} --[{orph['relation']}]--> {orph['target_id']}")
            if len(orphaned) > 20:
                print(f"   ... and {len(orphaned) - 20} more")
        else:
            print("✓ No orphaned edges found")
        print()

        # 3. METADATA COMPLETENESS
        print("=" * 80)
        print("3. METADATA COMPLETENESS")
        print("=" * 80)
        metadata_stats, missing_metadata = analyze_metadata_completeness(edges)

        print(f"Edges with metadata: {metadata_stats['with_metadata']} ({metadata_stats['with_metadata']/edge_count*100:.1f}%)")
        print(f"Edges without metadata: {metadata_stats['without_metadata']} ({metadata_stats['without_metadata']/edge_count*100:.1f}%)")
        print()

        if metadata_stats['metadata_fields']:
            print("Metadata fields used:")
            for field, count in sorted(metadata_stats['metadata_fields'].items(), key=lambda x: x[1], reverse=True):
                print(f"  {field}: {count} edges")
        print()

        # 4. BIDIRECTIONAL CONSISTENCY
        print("=" * 80)
        print("4. BIDIRECTIONAL CONSISTENCY")
        print("=" * 80)
        missing_reciprocal = analyze_bidirectional_consistency(edges, nodes_by_id)

        if missing_reciprocal:
            print(f"⚠️  Found {len(missing_reciprocal)} edges missing reciprocal relationships")
            print()
            for i, miss in enumerate(missing_reciprocal[:15], 1):
                print(f"{i}. {miss['source_name']} --[{miss['existing_relation']}]--> {miss['target_name']}")
                print(f"   Missing: {miss['target_name']} --[{miss['missing_relation']}]--> {miss['source_name']}")
            if len(missing_reciprocal) > 15:
                print(f"   ... and {len(missing_reciprocal) - 15} more")
        else:
            print("✓ All bidirectional relationships are consistent")
        print()

        # 5. TEMPORAL CONSISTENCY
        print("=" * 80)
        print("5. TEMPORAL CONSISTENCY")
        print("=" * 80)
        temporal_violations = analyze_temporal_consistency(edges, nodes_by_id)

        if temporal_violations:
            print(f"⚠️  Found {len(temporal_violations)} potential temporal inconsistencies")
            print()
            for i, viol in enumerate(temporal_violations[:10], 1):
                print(f"{i}. {viol['source']} --[{viol['relation']}]--> {viol['target']}")
                print(f"   {viol['issue']}")
            if len(temporal_violations) > 10:
                print(f"   ... and {len(temporal_violations) - 10} more")
        else:
            print("✓ No temporal inconsistencies detected")
        print()

        # 6. QUALITY SCORE
        print("=" * 80)
        print("6. OVERALL QUALITY ASSESSMENT")
        print("=" * 80)
        overall_score, score_breakdown = calculate_quality_score(
            edges, nodes_by_id, orphaned, missing_metadata
        )

        print(f"Overall Quality Score: {overall_score:.1f}/100")
        print()
        print("Score Breakdown:")
        print(f"  Orphan-free score: {score_breakdown['orphan_penalty']:.1f}/100")
        print(f"  Metadata completeness: {score_breakdown['metadata_completeness']:.1f}/100")
        print(f"  Node coverage: {score_breakdown['node_coverage']:.1f}/100")
        print()

        # Summary statistics
        print("=" * 80)
        print("SUMMARY STATISTICS")
        print("=" * 80)
        print(f"Total edges: {edge_count}")
        print(f"Total nodes: {node_count}")
        print(f"Unique relation types: {len(relation_dist)}")
        print(f"Orphaned edges: {len(orphaned)}")
        print(f"Edges without metadata: {len(missing_metadata)}")
        print(f"Missing reciprocal relationships: {len(missing_reciprocal)}")
        print(f"Temporal inconsistencies: {len(temporal_violations)}")
        print()

        # Export detailed results
        results = {
            'audit_date': datetime.now().isoformat(),
            'summary': {
                'total_edges': edge_count,
                'total_nodes': node_count,
                'unique_relation_types': len(relation_dist),
                'orphaned_edges': len(orphaned),
                'missing_metadata': len(missing_metadata),
                'missing_reciprocal': len(missing_reciprocal),
                'temporal_violations': len(temporal_violations),
                'quality_score': overall_score
            },
            'relation_distribution': relation_dist,
            'orphaned_edges': orphaned,
            'edges_without_metadata': missing_metadata[:100],  # Limit size
            'missing_reciprocal_relationships': missing_reciprocal[:100],
            'temporal_inconsistencies': temporal_violations[:50],
            'score_breakdown': score_breakdown
        }

        output_file = '[local-path] Free Will Database/kg_edge_audit_results.json'
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        print(f"✓ Detailed results exported to: {output_file}")
        print()

    finally:
        conn.close()
        print("Database connection closed")

if __name__ == "__main__":
    main()
