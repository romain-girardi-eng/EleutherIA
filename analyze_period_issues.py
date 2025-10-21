#!/usr/bin/env python3
"""
Analyze period field issues in the Ancient Free Will Database
Identifies all nodes with invalid controlled vocabulary values
"""

import json
from collections import Counter, defaultdict

# Valid controlled vocabulary for periods (EXTENDED for reception history)
VALID_PERIODS = {
    # Ancient (core focus - 4th BCE - 6th CE)
    "Presocratic",
    "Classical Greek",
    "Hellenistic Greek",
    "Roman Republican",
    "Roman Imperial",
    "Patristic",
    "Late Antiquity",
    # Medieval (7th-15th c. CE)
    "Early Medieval",
    "High Medieval",
    "Late Medieval",
    # Early Modern (15th-18th c. CE)
    "Renaissance",
    "Reformation",
    "Counter-Reformation",
    "Early Modern Rationalism",
    "Early Modern Empiricism",
    "Enlightenment",
    # Modern/Contemporary (19th-21st c. CE)
    "19th Century",
    "20th Century Analytic",
    "20th Century Continental",
    "21st Century",
    # Special categories
    "Second Temple Judaism",
    "Rabbinic Judaism"
}

def analyze_periods():
    """Analyze all period values in the database"""

    # Load database
    with open('ancient_free_will_database.json', 'r', encoding='utf-8') as f:
        db = json.load(f)

    nodes = db['nodes']

    # Count period values
    period_counts = Counter()
    invalid_periods = defaultdict(list)
    nodes_by_invalid_period = defaultdict(list)

    for node in nodes:
        period = node.get('period')
        if period:
            period_counts[period] += 1
            if period not in VALID_PERIODS:
                invalid_periods[period].append(node['id'])
                nodes_by_invalid_period[period].append({
                    'id': node['id'],
                    'label': node.get('label', 'N/A'),
                    'type': node.get('type', 'N/A'),
                    'date': node.get('date', 'N/A'),
                    'period': period
                })

    # Print summary
    print("=" * 80)
    print("PERIOD VOCABULARY ANALYSIS")
    print("=" * 80)
    print(f"\nTotal nodes: {len(nodes)}")
    print(f"Nodes with period field: {sum(period_counts.values())}")
    print(f"Valid periods found: {sum(1 for p in period_counts if p in VALID_PERIODS)}")
    print(f"Invalid periods found: {len(invalid_periods)}")
    print(f"Nodes affected: {sum(len(v) for v in invalid_periods.values())}")

    # Print all period values
    print("\n" + "=" * 80)
    print("ALL PERIOD VALUES (with counts)")
    print("=" * 80)
    for period, count in sorted(period_counts.items(), key=lambda x: -x[1]):
        status = "✓ VALID" if period in VALID_PERIODS else "✗ INVALID"
        print(f"{status:12} | {count:4} nodes | {period}")

    # Print invalid period details
    if invalid_periods:
        print("\n" + "=" * 80)
        print("INVALID PERIODS - DETAILED BREAKDOWN")
        print("=" * 80)

        for period in sorted(invalid_periods.keys()):
            nodes_list = nodes_by_invalid_period[period]
            print(f"\n'{period}' ({len(nodes_list)} nodes)")
            print("-" * 80)

            # Show first 10 examples with dates
            for i, node_info in enumerate(nodes_list[:10], 1):
                print(f"  {i}. {node_info['id']}")
                print(f"     Label: {node_info['label']}")
                print(f"     Type: {node_info['type']}, Date: {node_info['date']}")

            if len(nodes_list) > 10:
                print(f"  ... and {len(nodes_list) - 10} more")

    # Suggest mappings based on dates
    print("\n" + "=" * 80)
    print("SUGGESTED PERIOD MAPPINGS")
    print("=" * 80)

    mappings = {
        "Ancient Greek": "Needs date analysis → Classical Greek or Hellenistic Greek",
        "Hellenistic": "→ Hellenistic Greek",
        "Roman": "Needs date analysis → Roman Republican or Roman Imperial",
        "Early Christian": "→ Patristic",
        "Late Antique": "→ Late Antiquity"
    }

    for invalid, suggestion in mappings.items():
        if invalid in invalid_periods:
            print(f"\n'{invalid}': {suggestion}")

    return invalid_periods, nodes_by_invalid_period

if __name__ == '__main__':
    invalid_periods, nodes_by_invalid_period = analyze_periods()
