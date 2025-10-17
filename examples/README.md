# Examples - EleutherIA Ancient Free Will Database

This folder contains example scripts for working with the **EleutherIA** database, including GraphRAG, semantic search, and embeddings examples.

**EleutherIA** = Ἐλευθερία (freedom) + IA (Intelligence Artificielle/AI)

## Available Examples

### 1. `basic_queries.py`

Simple queries demonstrating how to:
- Load the database
- Count nodes and edges
- Filter by node type
- Find specific persons (Stoics, Patristics, etc.)
- Find works by author
- Analyze refutation relationships
- Find most connected nodes

**Requirements:** Python 3.7+, standard library only

**Usage:**
```bash
python basic_queries.py
```

### 2. `generate_embeddings.py` (Coming Soon)

Generate vector embeddings using Google Gemini for semantic search:
- Load database and generate embeddings for all nodes
- Combine multiple fields (label, description, sources)
- Save embeddings for reuse
- Compatible with Gemini text-embedding-004

**Requirements:** `google-generativeai`

### 3. `semantic_search.py` (Coming Soon)

Perform semantic search across the database:
- Query by meaning rather than keywords
- Find conceptually similar arguments
- Cross-lingual search (Greek/Latin/English)
- Combine with graph traversal

**Requirements:** `google-generativeai`, `numpy`

### 4. `graphrag_example.py` (Coming Soon)

Complete GraphRAG pipeline demonstration:
- Semantic search to find relevant nodes
- Graph traversal to expand context
- Format context for LLM consumption
- Generate answers with citations

**Requirements:** `google-generativeai`, `langchain` (optional)

## Working with the Database

### Loading the Database

**Python:**
```python
import json

with open('ancient_free_will_database.json', 'r', encoding='utf-8') as f:
    db = json.load(f)

nodes = db['nodes']
edges = db['edges']
metadata = db['metadata']
```

**JavaScript/Node.js:**
```javascript
const fs = require('fs');

const db = JSON.parse(
  fs.readFileSync('ancient_free_will_database.json', 'utf8')
);

const nodes = db.nodes;
const edges = db.edges;
const metadata = db.metadata;
```

### Common Query Patterns

**Find all persons:**
```python
persons = [n for n in nodes if n['type'] == 'person']
```

**Find all works by an author:**
```python
# First find the author's ID
author = next(n for n in nodes if 'aristotle' in n['id'].lower())

# Then find 'authored' edges
works = [e['target'] for e in edges
         if e['source'] == author['id'] and e['relation'] == 'authored']
```

**Find all arguments that refute something:**
```python
refutations = [e for e in edges if e['relation'] == 'refutes']
```

**Filter by historical period:**
```python
hellenistic = [n for n in nodes
               if n.get('period') == 'Hellenistic Greek']
```

## Visualization Options

While this database was originally visualized with Semativerse (part of the Sematika project), you can use various other tools:

### Recommended Tools

**1. Cytoscape**
- Free, open-source network visualization
- Excellent for large graphs
- Download: https://cytoscape.org/

**2. Gephi**
- Network analysis and visualization
- Good for statistical analysis
- Download: https://gephi.org/

**3. D3.js**
- JavaScript library for web-based visualizations
- Highly customizable
- Website: https://d3js.org/

**4. NetworkX (Python)**
- Python library for network analysis
- Install: `pip install networkx matplotlib`

**5. vis.js**
- JavaScript library for network visualization
- Website: https://visjs.org/

### Export to Cytoscape

```python
import json
import csv

# Load database
with open('ancient_free_will_database.json', 'r') as f:
    db = json.load(f)

# Export nodes
with open('nodes.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['id', 'label', 'type', 'period', 'description'])
    for node in db['nodes']:
        writer.writerow([
            node['id'],
            node['label'],
            node['type'],
            node.get('period', ''),
            node.get('description', '')[:100]  # Truncate for CSV
        ])

# Export edges
with open('edges.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['source', 'target', 'relation', 'description'])
    for edge in db['edges']:
        writer.writerow([
            edge['source'],
            edge['target'],
            edge['relation'],
            edge.get('description', '')
        ])

print("Exported to nodes.csv and edges.csv")
print("Import these files into Cytoscape: File > Import > Network from File")
```

## Contributing Examples

If you develop useful scripts for working with this database, please consider contributing them! See CONTRIBUTING.md in the main directory.

## Questions?

For questions about using the database:
- Email: romain.girardi@univ-cotedazur.fr
- Open an issue on GitHub

## License

Examples are provided under the same CC BY 4.0 license as the database.
