#!/usr/bin/env python3
"""
Basic Queries - Ancient Free Will Database
==========================================

Simple examples of querying the Ancient Free Will Database.
"""

import json
from collections import Counter

# Load the database
with open('../ancient_free_will_database.json', 'r', encoding='utf-8') as f:
    db = json.load(f)

nodes = db['nodes']
edges = db['edges']

print("=" * 70)
print("ANCIENT FREE WILL DATABASE - BASIC QUERIES")
print("=" * 70)
print()

# ============================================================================
# QUERY 1: Database Statistics
# ============================================================================

print("📊 DATABASE STATISTICS")
print("-" * 70)
print(f"Total nodes: {len(nodes)}")
print(f"Total edges: {len(edges)}")
print()

# Node types breakdown
node_types = Counter(node['type'] for node in nodes)
print("Node types:")
for ntype, count in sorted(node_types.items(), key=lambda x: -x[1]):
    print(f"  {ntype:20s}: {count:3d}")
print()

# ============================================================================
# QUERY 2: Find All Persons
# ============================================================================

print("👥 ALL PERSONS (sample of first 10)")
print("-" * 70)
persons = [n for n in nodes if n['type'] == 'person']
for person in persons[:10]:
    label = person['label']
    dates = person.get('dates', 'unknown dates')
    school = person.get('school', 'unknown school')
    print(f"  • {label} ({dates}) - {school}")
print(f"  ... and {len(persons) - 10} more")
print()

# ============================================================================
# QUERY 3: Find All Stoic Philosophers
# ============================================================================

print("🏛️  STOIC PHILOSOPHERS")
print("-" * 70)
stoics = [n for n in nodes
          if n['type'] == 'person' and
          'Stoic' in n.get('school', '')]

for stoic in stoics:
    label = stoic['label']
    dates = stoic.get('dates', 'unknown')
    print(f"  • {label} ({dates})")
print()

# ============================================================================
# QUERY 4: Find All Patristic/Christian Thinkers
# ============================================================================

print("✝️  PATRISTIC/CHRISTIAN THINKERS")
print("-" * 70)
patristics = [n for n in nodes
              if n['type'] == 'person' and
              ('Patristic' in n.get('school', '') or
               'Christian' in n.get('school', ''))]

for person in patristics:
    label = person['label']
    dates = person.get('dates', 'unknown')
    print(f"  • {label} ({dates})")
print()

# ============================================================================
# QUERY 5: Find Works by Specific Author
# ============================================================================

print("📚 WORKS BY ARISTOTLE")
print("-" * 70)

# Find Aristotle's node
aristotle_nodes = [n for n in nodes
                   if n['type'] == 'person' and
                   'aristotle' in n['id'].lower()]

if aristotle_nodes:
    aristotle_id = aristotle_nodes[0]['id']

    # Find edges where Aristotle is the author
    authored_edges = [e for e in edges
                      if e['source'] == aristotle_id and
                      e['relation'] == 'authored']

    for edge in authored_edges:
        # Find the work node
        work = next((n for n in nodes if n['id'] == edge['target']), None)
        if work:
            print(f"  • {work['label']}")
print()

# ============================================================================
# QUERY 6: Find Arguments That Refute Other Arguments
# ============================================================================

print("⚔️  REFUTATION RELATIONSHIPS (sample)")
print("-" * 70)

refutation_edges = [e for e in edges if e['relation'] == 'refutes'][:5]

for edge in refutation_edges:
    source_node = next((n for n in nodes if n['id'] == edge['source']), None)
    target_node = next((n for n in nodes if n['id'] == edge['target']), None)

    if source_node and target_node:
        print(f"  • {source_node['label']}")
        print(f"    REFUTES")
        print(f"    {target_node['label']}")
        if 'description' in edge:
            print(f"    ({edge['description']})")
        print()

# ============================================================================
# QUERY 7: Find All Concepts Related to Fate/Determinism
# ============================================================================

print("🔮 CONCEPTS RELATED TO FATE/DETERMINISM")
print("-" * 70)

fate_concepts = [n for n in nodes
                 if n['type'] == 'concept' and
                 any(term in n['label'].lower() or term in n.get('description', '').lower()
                     for term in ['fate', 'determinism', 'heimarmene', 'necessity'])]

for concept in fate_concepts[:10]:
    print(f"  • {concept['label']}")
print()

# ============================================================================
# QUERY 8: Network Analysis - Most Connected Nodes
# ============================================================================

print("🌐 MOST CONNECTED NODES (by degree)")
print("-" * 70)

# Count connections for each node
connections = Counter()
for edge in edges:
    connections[edge['source']] += 1
    connections[edge['target']] += 1

# Get top 10 most connected
top_connected = connections.most_common(10)

for node_id, degree in top_connected:
    node = next((n for n in nodes if n['id'] == node_id), None)
    if node:
        print(f"  • {node['label']}: {degree} connections")

print()
print("=" * 70)
print("For more examples, see:")
print("  • network_analysis.py - Network visualization")
print("  • export_examples.py - Export to different formats")
print("=" * 70)
