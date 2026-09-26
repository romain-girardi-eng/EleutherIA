# eleutheria-kg

Knowledge graph framework for the EleutherIA ancient philosophy database.

## Installation

```bash
pip install eleutheria-kg
```

For community detection algorithms:
```bash
pip install eleutheria-kg[community]
```

For FastAPI integration:
```bash
pip install eleutheria-kg[api]
```

## Quick Start

```python
from eleutheria_kg import KGAnalytics
from eleutheria_database import DatabaseService

# Connect to the relational corpus/KG store
db = DatabaseService()
await db.connect()

# Load knowledge graph
kg_data = await load_kg_from_database(db)

# Analyze graph
analytics = KGAnalytics(kg_data)

# Get node statistics
stats = analytics.get_statistics()
print(f"Nodes: {stats['total_nodes']}, Edges: {stats['total_edges']}")

# Find communities
communities = analytics.detect_communities(algorithm="leiden")

# Calculate centrality
centrality = analytics.calculate_centrality(metric="betweenness")

# Current GraphRAG retrieval is vectorless and lives in the graphrag package:
# SQLStrategy combines tree routing, KG label matches, passage_citations,
# lemmatic lookup, and full-text/lemmatic RRF.
```

## Features

- **22,912 nodes** of 16 types in use (24 declared) (Person, Concept, Argument, Work, etc.)
- **54,497 edges** across 53 relation types in use (77 declared)
- **Community detection** via Leiden, Louvain, or greedy modularity
- **Centrality metrics** (betweenness, PageRank, degree)
- **Vectorless GraphRAG retrieval** via SQLStrategy, tree routing, passage_citations, lemmatic lookup, and full-text/lemmatic RRF
- **Dual-layer structure** separating ancient sources from modern scholarship

## Knowledge Graph Schema

### Node Types (24 declared, 16 in use)

| Type | Count | Description |
|------|-------|-------------|
| Person | 496 | Ancient philosophers and modern scholars |
| Concept | 212 | Philosophical concepts (e.g., fate, determinism) |
| Argument | 1,682 | Philosophical arguments and scholarly positions |
| Work | 248 | Ancient texts (modern scholarship is in `publication`, 509) |
| School | 16 | Philosophical schools (Stoic, Epicurean, etc.) |
| ... | ... | ... |

### Relation Types (77 declared, 53 in use)

- `argues_for`, `argues_against` - Argumentative relationships
- `influences`, `influenced_by` - Intellectual lineage
- `belongs_to_school` - School affiliation
- `wrote`, `authored_by` - Authorship
- `cites`, `cited_by` - Citation networks
- `translation_of`, `has_translation` - Passage translation alignments
- `has_section`, `part_of` - Structural hierarchy
- ... and more (see `ontology/edge_types.json` for full list with source/target constraints)

## Ontology

The knowledge graph ontology is defined in:
- `src/eleutheria_kg/semantic/rdf_export.py` - generates the RDF/OWL ontology header and the VoID/DCAT dataset description at export time
- `ontology/node_types.json` - Node type definitions
- `ontology/edge_types.json` - Edge type definitions

## API Routes (Optional)

If installed with `[api]`:

```python
from fastapi import FastAPI
from eleutheria_kg.api import router as kg_router

app = FastAPI()
app.include_router(kg_router, prefix="/api/kg")
```

Endpoints:
- `GET /nodes` - List KG nodes with filtering
- `GET /nodes/{node_id}` - Get node details
- `GET /edges` - List edges
- `GET /communities` - Get community assignments
- `GET /centrality` - Get centrality scores
- `GET /search` - Label/description KG search

## Configuration

Environment variables:
```bash
ELEUTHERIA_DB_SCHEMA=free_will
```

## License

CC BY 4.0
