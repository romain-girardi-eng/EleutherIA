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
from eleutheria_kg import KGAnalytics, QdrantService
from eleutheria_database import DatabaseService

# Connect to services
db = DatabaseService()
qdrant = QdrantService()
await db.connect()
await qdrant.connect()

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

# Semantic search
results = await qdrant.search_nodes(query_embedding, limit=10)
```

## Features

- **2,193 nodes** across 15 types (Person, Concept, Argument, Work, etc.)
- **8,616 edges** across 56 relation types
- **Community detection** via Leiden, Louvain, or greedy modularity
- **Centrality metrics** (betweenness, PageRank, degree)
- **Semantic search** via Qdrant vector similarity (3072-dim Gemini embeddings)
- **Dual-layer structure** separating ancient sources from modern scholarship

## Knowledge Graph Schema

### Node Types (15)

| Type | Count | Description |
|------|-------|-------------|
| Person | ~200 | Ancient philosophers and modern scholars |
| Concept | ~800 | Philosophical concepts (e.g., fate, determinism) |
| Argument | ~400 | Philosophical arguments and debates |
| Work | ~300 | Ancient texts and modern scholarship |
| School | ~20 | Philosophical schools (Stoic, Epicurean, etc.) |
| ... | ... | ... |

### Relation Types (56)

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
- `ontology/eleutheria-ontology.ttl` - RDF/OWL ontology
- `ontology/node_types.json` - Node type definitions
- `ontology/edge_types.json` - Edge type definitions
- `ontology/void.ttl` - VoID dataset description

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
- `GET /search` - Semantic search

## Configuration

Environment variables:
```bash
QDRANT_HOST=localhost
QDRANT_HTTP_PORT=6333
QDRANT_API_KEY=  # For Qdrant Cloud
EMBEDDING_DIMENSIONS=3072
```

## License

CC BY 4.0
