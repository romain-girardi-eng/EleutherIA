# Database Query Examples

Common patterns for querying the Ancient Free Will Database.

---

## Loading the Database

```python
import json

# Load the database
with open('ancient_free_will_database.json', 'r', encoding='utf-8') as f:
    db = json.load(f)

# Extract components
nodes = db['nodes']
edges = db['edges']
metadata = db['metadata']

print(f"Loaded {len(nodes)} nodes and {len(edges)} edges")
```

---

## Basic Node Queries

### Find All Nodes of Specific Type

```python
# Find all persons
persons = [n for n in nodes if n['type'] == 'person']
print(f"Found {len(persons)} persons")

# Find all concepts
concepts = [n for n in nodes if n['type'] == 'concept']

# Find all arguments
arguments = [n for n in nodes if n['type'] == 'argument']

# Find all works
works = [n for n in nodes if n['type'] == 'work']
```

---

### Find Nodes by Philosophical School

```python
# Find all Stoic philosophers
stoics = [n for n in nodes
          if n['type'] == 'person' and
          n.get('school') == 'Stoic']

for stoic in stoics:
    print(f"{stoic['label']} ({stoic.get('dates', 'unknown')})")

# Find all Peripatetic philosophers
peripatetics = [n for n in nodes
                if n['type'] == 'person' and
                n.get('school', '').startswith('Peripatetic')]

# Find all Christian/Patristic thinkers
patristics = [n for n in nodes
              if n['type'] == 'person' and
              ('Patristic' in n.get('school', '') or
               'Christian' in n.get('school', ''))]
```

---

### Find Nodes by Historical Period

```python
# Find all Classical Greek figures
classical = [n for n in nodes
             if n.get('period') == 'Classical Greek']

# Find all Hellenistic figures
hellenistic = [n for n in nodes
               if n.get('period') == 'Hellenistic Greek']

# Find all Late Antiquity figures
late_antiquity = [n for n in nodes
                  if n.get('period') == 'Late Antiquity']
```

---

### Find Node by ID

```python
def find_node_by_id(node_id):
    """Find a node by its unique ID"""
    return next((n for n in nodes if n['id'] == node_id), None)

# Example
aristotle = find_node_by_id('person_aristotle_384_322bce_b2c3d4e5')
if aristotle:
    print(f"Found: {aristotle['label']}")
```

---

### Search Nodes by Label

```python
# Find nodes with "Aristotle" in label
aristotle_nodes = [n for n in nodes
                   if 'aristotle' in n['label'].lower()]

# Find nodes with "fate" in label
fate_nodes = [n for n in nodes
              if 'fate' in n['label'].lower()]

# Case-insensitive partial match
def search_by_label(search_term):
    """Search nodes by label (case-insensitive)"""
    term = search_term.lower()
    return [n for n in nodes if term in n['label'].lower()]

results = search_by_label("free will")
```

---

### Search Nodes by Description

```python
# Find nodes mentioning "determinism" in description
determinism_nodes = [n for n in nodes
                     if 'determinism' in n.get('description', '').lower()]

# Full-text search across label and description
def full_text_search(search_term):
    """Search across label and description"""
    term = search_term.lower()
    return [n for n in nodes
            if term in n['label'].lower() or
               term in n.get('description', '').lower()]

results = full_text_search("compatibilism")
```

---

## Edge Relationship Queries

### Find All Edges of Specific Relation Type

```python
# Find all "formulated" relationships
formulated = [e for e in edges if e['relation'] == 'formulated']

# Find all "refutes" relationships
refutations = [e for e in edges if e['relation'] == 'refutes']

# Find all "influenced" relationships
influences = [e for e in edges if e['relation'] == 'influenced']

# Find all "authored" relationships
authorships = [e for e in edges if e['relation'] == 'authored']
```

---

### Find Edges Connected to Specific Node

```python
def get_outgoing_edges(node_id):
    """Find all edges where node is source"""
    return [e for e in edges if e['source'] == node_id]

def get_incoming_edges(node_id):
    """Find all edges where node is target"""
    return [e for e in edges if e['target'] == node_id]

def get_all_edges(node_id):
    """Find all edges connected to node"""
    return [e for e in edges
            if e['source'] == node_id or e['target'] == node_id]

# Example: Find all edges connected to Aristotle
aristotle_id = 'person_aristotle_384_322bce_b2c3d4e5'
aristotle_edges = get_all_edges(aristotle_id)
print(f"Aristotle has {len(aristotle_edges)} connections")
```

---

### Find Works by Author

```python
def get_works_by_author(person_id):
    """Find all works authored by a person"""
    authored_edges = [e for e in edges
                      if e['source'] == person_id and
                      e['relation'] == 'authored']

    work_ids = [e['target'] for e in authored_edges]
    works = [find_node_by_id(wid) for wid in work_ids]
    return [w for w in works if w is not None]

# Example: Find Aristotle's works
aristotle_id = 'person_aristotle_384_322bce_b2c3d4e5'
aristotle_works = get_works_by_author(aristotle_id)
for work in aristotle_works:
    print(f"  • {work['label']}")
```

---

### Find Concepts Formulated by Person

```python
def get_concepts_by_formulator(person_id):
    """Find all concepts formulated by a person"""
    formulated_edges = [e for e in edges
                        if e['source'] == person_id and
                        e['relation'] == 'formulated']

    concept_ids = [e['target'] for e in formulated_edges]
    concepts = [find_node_by_id(cid) for cid in concept_ids]
    return [c for c in concepts if c is not None]

# Example
concepts = get_concepts_by_formulator(aristotle_id)
```

---

### Find Who Refutes Whom

```python
def get_refutation_pairs():
    """Get all (refuter, refuted) pairs"""
    refutations = [e for e in edges if e['relation'] == 'refutes']

    pairs = []
    for edge in refutations:
        source_node = find_node_by_id(edge['source'])
        target_node = find_node_by_id(edge['target'])
        if source_node and target_node:
            pairs.append({
                'refuter': source_node['label'],
                'refuted': target_node['label'],
                'description': edge.get('description', '')
            })
    return pairs

# Display refutations
for pair in get_refutation_pairs()[:5]:  # First 5
    print(f"{pair['refuter']} refutes {pair['refuted']}")
```

---

## Advanced Queries

### Find Influence Chains

```python
def get_influence_chain(start_person_id, depth=2):
    """Find who influenced whom, recursively"""
    influenced_edges = [e for e in edges
                        if e['source'] == start_person_id and
                        e['relation'] == 'influenced']

    influenced_ids = [e['target'] for e in influenced_edges]

    chain = []
    for person_id in influenced_ids:
        person = find_node_by_id(person_id)
        if person:
            chain.append(person)
            if depth > 1:
                # Recursively find their influences
                sub_chain = get_influence_chain(person_id, depth - 1)
                chain.extend(sub_chain)

    return chain

# Example: Who did Aristotle influence?
aristotle_id = 'person_aristotle_384_322bce_b2c3d4e5'
influenced = get_influence_chain(aristotle_id, depth=1)
```

---

### Network Analysis: Most Connected Nodes

```python
from collections import Counter

def get_node_degree():
    """Count connections for each node"""
    connections = Counter()

    for edge in edges:
        connections[edge['source']] += 1
        connections[edge['target']] += 1

    return connections

def get_most_connected(n=10):
    """Get top N most connected nodes"""
    connections = get_node_degree()
    top_nodes = []

    for node_id, degree in connections.most_common(n):
        node = find_node_by_id(node_id)
        if node:
            top_nodes.append({
                'label': node['label'],
                'type': node['type'],
                'connections': degree
            })

    return top_nodes

# Display most connected nodes
for node in get_most_connected(10):
    print(f"{node['label']} ({node['type']}): {node['connections']} connections")
```

---

### Find Nodes with Specific Greek/Latin Terms

```python
# Find concepts with specific Greek term
eph_hemin = [n for n in nodes
             if n['type'] == 'concept' and
             'ἐφ' ἡμῖν' in n.get('greek_term', '')]

# Find concepts with specific Latin term
liberum_arbitrium = [n for n in nodes
                     if n['type'] == 'concept' and
                     'liberum arbitrium' in n.get('latin_term', '').lower()]

# Find all concepts with Greek terms
greek_concepts = [n for n in nodes
                  if n['type'] == 'concept' and
                  'greek_term' in n]
```

---

### Filter by Multiple Criteria

```python
# Find Stoic arguments
stoic_arguments = [n for n in nodes
                   if n['type'] == 'argument' and
                   any('Stoic' in source for source in n.get('ancient_sources', []))]

# Find Classical Greek persons who are Peripatetic
classical_peripatetics = [n for n in nodes
                          if n['type'] == 'person' and
                          n.get('period') == 'Classical Greek' and
                          n.get('school', '').startswith('Peripatetic')]

# Find concepts formulated during Hellenistic period
hellenistic_concepts = [n for n in nodes
                        if n['type'] == 'concept' and
                        n.get('period') == 'Hellenistic Greek']
```

---

### Get Statistics by Category

```python
from collections import Counter

# Count nodes by type
node_type_counts = Counter(n['type'] for n in nodes)
print("Node types:")
for ntype, count in sorted(node_type_counts.items(), key=lambda x: -x[1]):
    print(f"  {ntype}: {count}")

# Count persons by school
school_counts = Counter(n.get('school', 'Unknown')
                        for n in nodes if n['type'] == 'person')
print("\nPhilosophical schools:")
for school, count in sorted(school_counts.items(), key=lambda x: -x[1]):
    print(f"  {school}: {count}")

# Count nodes by period
period_counts = Counter(n.get('period', 'Unknown') for n in nodes)
print("\nHistorical periods:")
for period, count in sorted(period_counts.items(), key=lambda x: -x[1]):
    print(f"  {period}: {count}")
```

---

## GraphRAG-Style Queries

### Multi-field Semantic Content Extraction

```python
def extract_semantic_content(node):
    """Extract rich content for embedding/semantic search"""
    parts = [f"{node['label']}: {node['description']}"]

    # Add ancient sources
    if 'ancient_sources' in node and node['ancient_sources']:
        sources = "; ".join(node['ancient_sources'])
        parts.append(f"Ancient sources: {sources}")

    # Add modern scholarship
    if 'modern_scholarship' in node and node['modern_scholarship']:
        scholarship = "; ".join(node['modern_scholarship'])
        parts.append(f"Modern scholarship: {scholarship}")

    # Add key concepts
    if 'key_concepts' in node and node['key_concepts']:
        concepts = ", ".join(node['key_concepts'])
        parts.append(f"Key concepts: {concepts}")

    # Add Greek/Latin terms
    if 'greek_term' in node:
        parts.append(f"Greek: {node['greek_term']}")
    if 'latin_term' in node:
        parts.append(f"Latin: {node['latin_term']}")

    return " | ".join(parts)

# Example
for node in persons[:3]:
    content = extract_semantic_content(node)
    print(f"\n{content[:200]}...")
```

---

### Graph Traversal for Context Expansion

```python
def expand_context(node_id, depth=1):
    """Expand context around a node via graph traversal"""
    context = {'central_node': find_node_by_id(node_id)}

    # Get directly connected nodes
    outgoing = get_outgoing_edges(node_id)
    incoming = get_incoming_edges(node_id)

    context['formulated_concepts'] = [
        find_node_by_id(e['target'])
        for e in outgoing if e['relation'] == 'formulated'
    ]

    context['authored_works'] = [
        find_node_by_id(e['target'])
        for e in outgoing if e['relation'] == 'authored'
    ]

    context['influenced_by'] = [
        find_node_by_id(e['source'])
        for e in incoming if e['relation'] == 'influenced'
    ]

    context['refutes'] = [
        find_node_by_id(e['target'])
        for e in outgoing if e['relation'] == 'refutes'
    ]

    context['refuted_by'] = [
        find_node_by_id(e['source'])
        for e in incoming if e['relation'] == 'refutes'
    ]

    # Filter out None values
    for key in context:
        if isinstance(context[key], list):
            context[key] = [n for n in context[key] if n is not None]

    return context

# Example: Expand context around Aristotle
aristotle_id = 'person_aristotle_384_322bce_b2c3d4e5'
context = expand_context(aristotle_id)
print(f"Aristotle formulated {len(context['formulated_concepts'])} concepts")
print(f"Aristotle authored {len(context['authored_works'])} works")
```

---

## Export Queries

### Export to CSV

```python
import csv

def export_persons_to_csv(filename='persons.csv'):
    """Export all persons to CSV"""
    persons = [n for n in nodes if n['type'] == 'person']

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'id', 'label', 'dates', 'school', 'period', 'position_on_free_will'
        ])
        writer.writeheader()

        for person in persons:
            writer.writerow({
                'id': person['id'],
                'label': person['label'],
                'dates': person.get('dates', ''),
                'school': person.get('school', ''),
                'period': person.get('period', ''),
                'position_on_free_will': person.get('position_on_free_will', '')
            })

    print(f"Exported {len(persons)} persons to {filename}")

# Export
export_persons_to_csv()
```

---

### Export to NetworkX

```python
import networkx as nx

def create_networkx_graph():
    """Convert database to NetworkX graph"""
    G = nx.DiGraph()

    # Add nodes
    for node in nodes:
        G.add_node(node['id'], **{
            'label': node['label'],
            'type': node['type'],
            'description': node.get('description', '')
        })

    # Add edges
    for edge in edges:
        G.add_edge(
            edge['source'],
            edge['target'],
            relation=edge['relation'],
            description=edge.get('description', '')
        )

    return G

# Create graph
G = create_networkx_graph()
print(f"Created NetworkX graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")

# Analyze
print(f"Graph density: {nx.density(G):.4f}")
print(f"Number of connected components: {nx.number_weakly_connected_components(G)}")
```

---

## Performance Tips

### Pre-index for Faster Lookups

```python
# Create lookup dictionaries at load time
node_by_id = {n['id']: n for n in nodes}
edges_by_source = {}
edges_by_target = {}

for edge in edges:
    edges_by_source.setdefault(edge['source'], []).append(edge)
    edges_by_target.setdefault(edge['target'], []).append(edge)

# Now lookups are O(1) instead of O(n)
aristotle = node_by_id.get('person_aristotle_384_322bce_b2c3d4e5')
aristotle_outgoing = edges_by_source.get(aristotle['id'], [])
```

---

**Last Updated**: 2025-10-21
**Source**: Based on `examples/basic_queries.py` and database structure
