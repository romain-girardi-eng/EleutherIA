# Ancient Free Will Database - API Documentation

**Version**: 1.0.0
**Base URL**: `https://yourapi.com` (or `http://localhost:8000` for development)
**OpenAPI Spec**: Available at `/docs` (Swagger UI) and `/redoc` (ReDoc)

---

## Table of Contents

1. [Authentication](#authentication)
2. [Knowledge Graph API](#knowledge-graph-api)
3. [Search API](#search-api)
4. [GraphRAG API](#graphrag-api)
5. [Texts API](#texts-api)
6. [Monitoring](#monitoring)
7. [Error Handling](#error-handling)
8. [Rate Limiting](#rate-limiting)
9. [Examples](#examples)

---

## Authentication

Most endpoints are publicly accessible. GraphRAG endpoints require JWT authentication.

### Register

Create a new user account.

```http
POST /api/auth/register
Content-Type: application/json

{
  "username": "researcher",
  "email": "researcher@university.edu",
  "password": "securepassword123"
}
```

**Response** (201 Created):
```json
{
  "user_id": "uuid-here",
  "username": "researcher",
  "email": "researcher@university.edu",
  "created_at": "2025-10-25T10:00:00Z"
}
```

### Login

Obtain a JWT access token.

```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "researcher",
  "password": "securepassword123"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

### Using Tokens

Include the token in the Authorization header:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## Knowledge Graph API

### Get All Nodes

Retrieve all nodes or filter by type, period, or school.

```http
GET /api/kg/nodes?type=person&period=Classical%20Greek&school=Stoic
```

**Query Parameters**:
- `type` (optional): Node type (person, concept, work, argument, etc.)
- `period` (optional): Historical period (Classical Greek, Hellenistic Greek, etc.)
- `school` (optional): Philosophical school (Stoic, Epicurean, Peripatetic, etc.)
- `limit` (optional): Maximum results (default: 1000)
- `offset` (optional): Pagination offset (default: 0)

**Response** (200 OK):
```json
[
  {
    "id": "person_chrysippus_279_206bce_a1b2c3d4",
    "label": "Chrysippus of Soli",
    "type": "person",
    "category": "philosopher",
    "description": "Third head of the Stoic school...",
    "period": "Hellenistic Greek",
    "school": "Stoic",
    "dates": "279-206 BCE",
    "position_on_free_will": "Chrysippus argued for compatibilism...",
    "ancient_sources": ["Cicero, De Fato 39-44", "Aulus Gellius 7.2"],
    "modern_scholarship": ["Bobzien 1998", "Frede 2011"]
  }
]
```

### Get Single Node

Retrieve a specific node with its neighbors.

```http
GET /api/kg/node/{node_id}
```

**Response** (200 OK):
```json
{
  "node": {
    "id": "person_chrysippus_279_206bce_a1b2c3d4",
    "label": "Chrysippus of Soli",
    ...
  },
  "neighbors": [
    {
      "id": "concept_compatibilism_e5f6g7h8",
      "relation": "developed",
      "label": "Compatibilism"
    }
  ]
}
```

### Get All Edges

Retrieve all relationships.

```http
GET /api/kg/edges?relation=refutes&limit=100
```

**Query Parameters**:
- `relation` (optional): Filter by relation type (refutes, influenced, authored, etc.)
- `source` (optional): Filter by source node ID
- `target` (optional): Filter by target node ID
- `limit` (optional): Maximum results (default: 1000)

**Response** (200 OK):
```json
[
  {
    "source": "person_carneades_214_129bce_i9j0k1l2",
    "target": "argument_lazy_argument_m3n4o5p6",
    "relation": "refuted"
  }
]
```

### Get Neighbors

Find all nodes connected to a specific node.

```http
GET /api/kg/neighbors?node_id=person_aristotle_384_322bce_b2c3d4e5&max_depth=2
```

**Query Parameters**:
- `node_id` (required): Starting node ID
- `max_depth` (optional): Maximum traversal depth (default: 1)
- `relation_filter` (optional): Only include specific relations

**Response** (200 OK):
```json
{
  "node_id": "person_aristotle_384_322bce_b2c3d4e5",
  "neighbors": [
    {
      "id": "work_nicomachean_ethics_q7r8s9t0",
      "label": "Nicomachean Ethics",
      "relation": "authored",
      "distance": 1
    }
  ],
  "count": 12
}
```

### Find Shortest Path

Find the shortest path between two nodes.

```http
GET /api/kg/paths?source=person_aristotle_384_322bce_b2c3d4e5&target=person_augustine_354_430ce_u1v2w3x4
```

**Query Parameters**:
- `source` (required): Source node ID
- `target` (required): Target node ID
- `max_paths` (optional): Maximum paths to return (default: 5)

**Response** (200 OK):
```json
{
  "paths": [
    {
      "nodes": [
        "person_aristotle_384_322bce_b2c3d4e5",
        "concept_voluntary_action_y5z6a7b8",
        "person_augustine_354_430ce_u1v2w3x4"
      ],
      "edges": [
        {
          "source": "person_aristotle_384_322bce_b2c3d4e5",
          "target": "concept_voluntary_action_y5z6a7b8",
          "relation": "developed"
        },
        {
          "source": "concept_voluntary_action_y5z6a7b8",
          "target": "person_augustine_354_430ce_u1v2w3x4",
          "relation": "appropriated_by"
        }
      ],
      "length": 2
    }
  ]
}
```

### Get Statistics

Get database statistics.

```http
GET /api/kg/stats
```

**Response** (200 OK):
```json
{
  "total_nodes": 509,
  "total_edges": 820,
  "node_types": {
    "person": 164,
    "argument": 117,
    "concept": 85,
    "work": 50,
    "reformulation": 53
  },
  "historical_periods": {
    "Classical Greek": 78,
    "Hellenistic Greek": 102,
    "Roman Imperial": 145
  },
  "philosophical_schools": {
    "Stoic": 89,
    "Peripatetic": 67,
    "Epicurean": 45
  }
}
```

### Analytics Endpoints

#### Timeline

```http
GET /api/kg/analytics/timeline
```

Returns chronological visualization data.

#### Concept Clusters

```http
GET /api/kg/analytics/concept-clusters
```

Returns hierarchical concept groupings.

#### Influence Matrix

```http
GET /api/kg/analytics/influence-matrix
```

Returns school-to-school influence heatmap.

#### Communities

```http
GET /api/kg/analytics/communities
```

Returns detected graph communities using Leiden algorithm.

### Export Formats

#### Cytoscape Format

```http
GET /api/kg/viz/cytoscape
```

Returns graph in Cytoscape.js format for visualization.

---

## Search API

### Full-Text Search

Search ancient texts using PostgreSQL full-text search.

```http
POST /api/search/fulltext
Content-Type: application/json

{
  "query": "liberum arbitrium",
  "limit": 10,
  "offset": 0
}
```

**Response** (200 OK):
```json
{
  "results": [
    {
      "text_id": "augustine_de_libero_arbitrio_1",
      "title": "De Libero Arbitrio",
      "author": "Augustine of Hippo",
      "snippet": "...quid est <em>liberum arbitrium</em> nisi...",
      "score": 0.95,
      "language": "latin"
    }
  ],
  "total": 42,
  "query_time_ms": 15
}
```

### Lemmatic Search

Search lemmatized texts (case-insensitive, normalized).

```http
POST /api/search/lemmatic
Content-Type: application/json

{
  "query": "ἐφ' ἡμῖν",
  "limit": 10
}
```

### Semantic Search

Vector similarity search using embeddings.

```http
POST /api/search/semantic
Content-Type: application/json

{
  "query": "What is the relationship between fate and free will?",
  "limit": 10,
  "threshold": 0.7
}
```

**Query Parameters**:
- `query` (required): Search query
- `limit` (optional): Maximum results (default: 10)
- `threshold` (optional): Minimum similarity score (0-1, default: 0.7)

### Hybrid Search

Combines full-text, lemmatic, and semantic search using Reciprocal Rank Fusion.

```http
POST /api/search/hybrid
Content-Type: application/json

{
  "query": "Stoic views on determinism",
  "limit": 10
}
```

**Response** (200 OK):
```json
{
  "results": [
    {
      "text_id": "chrysippus_on_fate_fragment_1",
      "title": "On Fate (Fragment)",
      "author": "Chrysippus",
      "snippet": "...everything happens according to fate...",
      "rrf_score": 0.92,
      "fulltext_rank": 2,
      "semantic_rank": 1,
      "lemmatic_rank": 3
    }
  ],
  "total": 15,
  "query_time_ms": 45,
  "search_types_used": ["fulltext", "semantic", "lemmatic"]
}
```

---

## GraphRAG API

**Authentication Required**: All GraphRAG endpoints require JWT token.

### Query

Ask questions about ancient free will debates using GraphRAG.

```http
POST /api/graphrag/query
Authorization: Bearer <token>
Content-Type: application/json

{
  "query": "How did Aristotle's concept of voluntary action influence later Stoic thought?"
}
```

**Response** (200 OK):
```json
{
  "query": "How did Aristotle's concept of voluntary action...",
  "answer": "Aristotle's concept of voluntary action (ἑκούσιον, hekousion) in Nicomachean Ethics III significantly influenced Stoic debates...",
  "sources": [
    {
      "type": "ancient",
      "citation": "Aristotle, Nicomachean Ethics III.1-5",
      "relevance": "primary"
    },
    {
      "type": "ancient",
      "citation": "Chrysippus, On Fate (fragments in Cicero, De Fato)",
      "relevance": "reception"
    },
    {
      "type": "modern",
      "citation": "Bobzien, S. (1998). Determinism and Freedom in Stoic Philosophy",
      "relevance": "scholarly_analysis"
    }
  ],
  "reasoning_path": [
    {
      "node_id": "person_aristotle_384_322bce_b2c3d4e5",
      "label": "Aristotle",
      "reason": "Semantic match on query concept"
    },
    {
      "node_id": "concept_voluntary_action_y5z6a7b8",
      "label": "Voluntary Action (ἑκούσιον)",
      "reason": "Direct relationship with Aristotle"
    },
    {
      "node_id": "person_chrysippus_279_206bce_a1b2c3d4",
      "label": "Chrysippus",
      "reason": "Appropriated Aristotelian concepts"
    }
  ],
  "llm_provider": "gemini",
  "llm_model": "gemini-2.0-flash-exp",
  "query_time_ms": 2341
}
```

### Streaming Query

For long-running queries, use Server-Sent Events (SSE).

```http
GET /api/graphrag/streams?query=<url-encoded-query>
Authorization: Bearer <token>
```

**Response** (text/event-stream):
```
data: {"type": "progress", "message": "Searching knowledge graph..."}

data: {"type": "progress", "message": "Found 5 relevant nodes"}

data: {"type": "chunk", "content": "Aristotle's concept of voluntary action..."}

data: {"type": "chunk", "content": " significantly influenced..."}

data: {"type": "complete", "sources": [...], "reasoning_path": [...]}
```

---

## Texts API

### List Texts

Get all available ancient texts.

```http
GET /api/texts?category=Origen&language=greek&limit=20
```

**Query Parameters**:
- `category` (optional): Text category
- `author` (optional): Author name
- `language` (optional): Language (greek, latin)
- `limit` (optional): Maximum results
- `offset` (optional): Pagination offset

**Response** (200 OK):
```json
{
  "texts": [
    {
      "text_id": "origen_de_principiis_1",
      "title": "De Principiis (On First Principles)",
      "author": "Origen of Alexandria",
      "category": "Origen",
      "language": "greek",
      "date": "c. 220-230 CE",
      "word_count": 45678,
      "has_lemmatized": true,
      "has_embeddings": true
    }
  ],
  "total": 48,
  "page": 1
}
```

### Get Text

Retrieve full text content.

```http
GET /api/texts/{text_id}
```

**Response** (200 OK):
```json
{
  "text_id": "origen_de_principiis_1",
  "title": "De Principiis",
  "author": "Origen",
  "content": "Πάντων μὲν οὖν τῶν ὄντων...",
  "lemmatized_content": "πᾶς μὲν οὖν ὁ εἰμί...",
  "metadata": {
    "edition": "SC 252, 253, 268, 269, 312",
    "editor": "Henri Crouzel, Manlio Simonetti",
    "year": "1978-1980"
  }
}
```

### Search Texts

Search within ancient texts.

```http
GET /api/texts/search?q=αὐτεξούσιον&limit=10
```

---

## Monitoring

### Health Check

```http
GET /api/health
```

**Response** (200 OK):
```json
{
  "status": "healthy",
  "database": "connected",
  "qdrant": "connected",
  "llm": "available",
  "uptime_seconds": 3600
}
```

### Prometheus Metrics

```http
GET /metrics
```

**Response** (text/plain; version=0.0.4):
```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/api/kg/nodes",status="200"} 1234

# HELP graphrag_query_duration_seconds GraphRAG query duration
# TYPE graphrag_query_duration_seconds histogram
graphrag_query_duration_seconds_bucket{le="1.0"} 45
graphrag_query_duration_seconds_bucket{le="2.5"} 89
...
```

---

## Error Handling

All errors follow this format:

```json
{
  "error": "Error message",
  "error_type": "ValidationError",
  "details": {
    "field": "query",
    "reason": "Query cannot be empty"
  },
  "request_id": "uuid-here",
  "timestamp": "2025-10-25T10:00:00Z"
}
```

### HTTP Status Codes

- `200 OK`: Success
- `201 Created`: Resource created
- `400 Bad Request`: Invalid request
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service temporarily unavailable

---

## Rate Limiting

### GraphRAG Endpoints

- **Limit**: 30 requests per 15 minutes per user
- **Response Header**: `X-RateLimit-Remaining: 25`

When exceeded:
```json
{
  "error": "Rate limit exceeded",
  "retry_after_seconds": 600
}
```

### Other Endpoints

- **Limit**: 100 requests per minute per IP
- No authentication required

---

## Examples

### Python

```python
import requests

# Search the knowledge graph
response = requests.get(
    "https://api.yoursite.com/api/kg/nodes",
    params={"type": "person", "school": "Stoic"}
)
stoics = response.json()

# GraphRAG query (authenticated)
headers = {"Authorization": "Bearer YOUR_TOKEN"}
response = requests.post(
    "https://api.yoursite.com/api/graphrag/query",
    headers=headers,
    json={"query": "What did Chrysippus think about fate?"}
)
answer = response.json()
print(answer["answer"])
```

### JavaScript

```javascript
// Hybrid search
const response = await fetch('https://api.yoursite.com/api/search/hybrid', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: 'Stoic determinism',
    limit: 10
  })
});

const results = await response.json();
console.log(results.results);
```

### cURL

```bash
# Get all Stoic philosophers
curl -X GET "https://api.yoursite.com/api/kg/nodes?school=Stoic&type=person"

# GraphRAG query
curl -X POST https://api.yoursite.com/api/graphrag/query \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "Compare Epicurean and Stoic views on free will"}'
```

---

## SDK Support

Official SDKs coming soon:
- Python SDK
- JavaScript/TypeScript SDK
- R package (for researchers)

---

## Changelog

### v1.0.0 (2025-10-25)
- Initial public release
- Knowledge Graph API with 509 nodes, 820 edges
- GraphRAG with streaming support
- Hybrid search (full-text + semantic + lemmatic)
- 289 ancient texts indexed
- Prometheus metrics
- Sentry error tracking

---

## Support

- **Documentation**: https://docs.yoursite.com
- **Issues**: https://github.com/yourusername/ancient-free-will-database/issues
- **Email**: romain.girardi@univ-cotedazur.fr
- **ORCID**: 0000-0002-5310-5346

---

## License

Data: CC BY 4.0
API: MIT License

When using this API, please cite:

**APA**:
```
Girardi, R. (2025). Ancient Free Will Database (Version 1.0.0) [Knowledge Graph].
Université Côte d'Azur. https://doi.org/10.5281/zenodo.XXXXXXX
```

**BibTeX**:
```bibtex
@misc{girardi2025ancientfreewill,
  author = {Girardi, Romain},
  title = {Ancient Free Will Database},
  year = {2025},
  version = {1.0.0},
  doi = {10.5281/zenodo.XXXXXXX},
  url = {https://yoursite.com}
}
```
