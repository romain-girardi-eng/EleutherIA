#!/usr/bin/env python3
"""
Analyze citation coverage across all node types
Identify nodes with zero citations (ancient_sources + modern_scholarship)
"""

import json
from collections import defaultdict

def analyze_citations():
    """Analyze citation coverage"""

    # Load database
    with open('ancient_free_will_database.json', 'r', encoding='utf-8') as f:
        db = json.load(f)

    nodes = db['nodes']

    print("=" * 80)
    print("CITATION COVERAGE ANALYSIS")
    print("=" * 80)
    print(f"\nTotal nodes: {len(nodes)}")

    # Categorize by node type
    by_type = defaultdict(list)
    for node in nodes:
        by_type[node.get('type', 'unknown')].append(node)

    # Analyze each type
    results = {}

    for node_type in sorted(by_type.keys()):
        nodes_of_type = by_type[node_type]

        has_ancient = []
        has_modern = []
        has_both = []
        has_neither = []

        for node in nodes_of_type:
            ancient = node.get('ancient_sources', [])
            modern = node.get('modern_scholarship', [])

            has_a = bool(ancient and len(ancient) > 0)
            has_m = bool(modern and len(modern) > 0)

            if has_a:
                has_ancient.append(node)
            if has_m:
                has_modern.append(node)

            if has_a and has_m:
                has_both.append(node)
            elif has_a and not has_m:
                # has ancient only
                pass
            elif has_m and not has_a:
                # has modern only
                pass
            else:
                has_neither.append(node)

        results[node_type] = {
            'total': len(nodes_of_type),
            'has_ancient': len(has_ancient),
            'has_modern': len(has_modern),
            'has_both': len(has_both),
            'has_neither': len(has_neither),
            'neither_list': has_neither
        }

    # Print summary by type
    print("\n" + "=" * 80)
    print("CITATION COVERAGE BY NODE TYPE")
    print("=" * 80)

    total_nodes = 0
    total_neither = 0

    for node_type in sorted(results.keys()):
        r = results[node_type]
        print(f"\n{node_type.upper()} ({r['total']} nodes)")
        print(f"  Ancient sources:     {r['has_ancient']} ({r['has_ancient']/r['total']*100:.1f}%)")
        print(f"  Modern scholarship:  {r['has_modern']} ({r['has_modern']/r['total']*100:.1f}%)")
        print(f"  Both:                {r['has_both']} ({r['has_both']/r['total']*100:.1f}%)")
        print(f"  NEITHER:             {r['has_neither']} ({r['has_neither']/r['total']*100:.1f}%)")

        total_nodes += r['total']
        total_neither += r['has_neither']

    print("\n" + "=" * 80)
    print("OVERALL CITATION COVERAGE")
    print("=" * 80)
    print(f"Total nodes: {total_nodes}")
    print(f"Nodes with ZERO citations: {total_neither} ({total_neither/total_nodes*100:.1f}%)")
    print(f"Nodes with at least 1 citation: {total_nodes - total_neither} ({(total_nodes-total_neither)/total_nodes*100:.1f}%)")

    # List all nodes with neither
    print("\n" + "=" * 80)
    print("NODES WITH ZERO CITATIONS (by type)")
    print("=" * 80)

    uncited_by_type = {}

    for node_type in sorted(results.keys()):
        neither_list = results[node_type]['neither_list']
        if neither_list:
            uncited_by_type[node_type] = neither_list
            print(f"\n{node_type.upper()} ({len(neither_list)} nodes)")
            print("-" * 80)
            for i, node in enumerate(neither_list[:10], 1):
                print(f"  {i}. {node['id']}")
                print(f"     Label: {node.get('label', 'N/A')}")
                print(f"     Period: {node.get('period', 'N/A')}")
            if len(neither_list) > 10:
                print(f"  ... and {len(neither_list) - 10} more")

    # Focus on concepts (most critical for Phase 3)
    if 'concept' in uncited_by_type:
        print("\n" + "=" * 80)
        print("CRITICAL: CONCEPTS WITH ZERO CITATIONS")
        print("=" * 80)

        uncited_concepts = uncited_by_type['concept']
        print(f"\nTotal uncited concepts: {len(uncited_concepts)}")

        # Group by period
        by_period = defaultdict(list)
        for c in uncited_concepts:
            period = c.get('period', 'No period')
            by_period[period].append(c)

        for period in sorted(by_period.keys()):
            concepts = by_period[period]
            print(f"\n{period}: {len(concepts)} concepts")
            for c in concepts:
                print(f"  • {c['id']}")
                print(f"    {c.get('label', 'N/A')}")

    # Export detailed list
    export_data = {
        'summary': {
            'total_nodes': total_nodes,
            'total_uncited': total_neither,
            'uncited_percentage': total_neither/total_nodes*100
        },
        'by_type': {}
    }

    for node_type, neither_list in uncited_by_type.items():
        export_data['by_type'][node_type] = [
            {
                'id': n['id'],
                'label': n.get('label'),
                'period': n.get('period'),
                'description': n.get('description', '')[:200]
            } for n in neither_list
        ]

    with open('uncited_nodes.json', 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 80)
    print("Exported to: uncited_nodes.json")
    print("=" * 80)

    return uncited_by_type

if __name__ == '__main__':
    analyze_citations()
