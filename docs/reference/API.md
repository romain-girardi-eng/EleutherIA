# EleutherIA REST API Reference

Complete API documentation for the EleutherIA knowledge graph system.

**Base URL:** `http://localhost:8000/api`

**Interactive Docs:** `http://localhost:8000/docs` (Swagger UI)

---

## Table of Contents

1. [Authentication](#authentication)
2. [Works API](#works-api) - Ancient texts corpus
3. [Knowledge Graph API](#knowledge-graph-api) - Nodes, edges, analytics
4. [GraphRAG API](#graphrag-api) - Q&A with citations
5. [Error Handling](#error-handling)
6. [Rate Limits](#rate-limits)

---

## Authentication

Most endpoints are public. GraphRAG and write operations may require authentication.

### Headers

```http
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

### Get Token

```http
POST /auth/login
```

**Request:**
```json
{
  "username": "user@example.com",
  "password": "password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 604800
}
```

---

## Works API

Browse the ancient texts corpus (189 works, 17k passages).

### List Works

```http
GET /works
```

Returns paginated list of ancient works with metadata.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `language` | string | - | Filter by language code: `grc` (Greek), `lat` (Latin), `eng` (English) |
| `author` | string | - | Filter by author name (partial match, case-insensitive) |
| `school` | string | - | Filter by philosophical school (e.g., `Stoic`, `Epicurean`) |
| `limit` | integer | 100 | Results per page (1-1000) |
| `offset` | integer | 0 | Pagination offset |

**Example:**
```bash
curl "http://localhost:8000/api/works?language=grc&school=Stoic&limit=10"
```

**Response:**
```json
[
  {
    "work_id": "550e8400-e29b-41d4-a716-446655440000",
    "canonical_id": "chrysippus_on_fate",
    "title": "On Fate",
    "title_original": "Περὶ εἱμαρμένης",
    "author": "Chrysippus",
    "author_original": "Χρύσιππος",
    "language": "grc",
    "period": "Hellenistic Greek",
    "date_composed": "3rd c. BCE",
    "school": "Stoic",
    "source": "tlg",
    "cts_urn": "urn:cts:greekLit:tlg0546.tlg001",
    "citation_levels": ["book", "section"],
    "has_morphology": true,
    "total_words": 15420,
    "created_at": "2025-01-15T10:30:00Z"
  }
]
```

### Get Work

```http
GET /works/{work_id}
```

Returns a single work with full metadata.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `work_id` | UUID | Work identifier |

**Response:** Same as list item above.

**Errors:**
- `404` - Work not found

### List Passages

```http
GET /works/{work_id}/passages
```

Returns passages for a specific work in sequence order.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `work_id` | UUID | Work identifier |

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `book` | string | - | Filter by book identifier |
| `chapter` | string | - | Filter by chapter |
| `limit` | integer | 100 | Results per page (1-1000) |
| `offset` | integer | 0 | Pagination offset |

**Example:**
```bash
curl "http://localhost:8000/api/works/550e8400.../passages?book=3&limit=50"
```

**Response:**
```json
[
  {
    "passage_id": "660e8400-e29b-41d4-a716-446655440001",
    "work_id": "550e8400-e29b-41d4-a716-446655440000",
    "canonical_ref": "3.191",
    "cts_urn": "urn:cts:greekLit:tlg0546.tlg001:3.191",
    "book": "3",
    "chapter": null,
    "section": "191",
    "sequence_number": 191,
    "text_content": "τὸ ἐφ' ἡμῖν ἐστιν ὃ δι' ἡμῶν γίνεται...",
    "char_length": 245,
    "word_count": 42,
    "morphology": {
      "lemmas": [
        {"f": "τὸ", "l": "ὁ", "p": "DET", "m": {"case": "nom", "number": "sg"}},
        {"f": "ἐφ'", "l": "ἐπί", "p": "ADP"}
      ]
    },
    "previous_passage_id": "660e8400...",
    "next_passage_id": "660e8400..."
  }
]
```

### Get Passage

```http
GET /passages/{passage_id}
```

Returns a single passage with full content and morphology.

**Errors:**
- `404` - Passage not found

### Search Passages

```http
GET /search
```

Full-text search across all passages with highlighted snippets.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `q` | string | Yes | Search query (min 2 characters) |
| `language` | string | No | Filter by language |
| `author` | string | No | Filter by author |
| `limit` | integer | No | Max results (default: 50, max: 200) |

**Example:**
```bash
curl "http://localhost:8000/api/search?q=εἱμαρμένη&language=grc&limit=20"
```

**Response:**
```json
[
  {
    "passage_id": "660e8400...",
    "work_id": "550e8400...",
    "canonical_ref": "1.28",
    "text_content": "...εἱμαρμένη δέ ἐστιν...",
    "title": "De Fato",
    "author": "Cicero",
    "language": "lat",
    "rank": 0.9523,
    "snippet": "...about <mark>εἱμαρμένη</mark> (fate) as the Stoics..."
  }
]
```

### Get Corpus Statistics

```http
GET /statistics
```

Returns aggregate statistics for the entire corpus.

**Response:**
```json
{
  "works": {
    "total_works": 189,
    "greek_works": 172,
    "latin_works": 17,
    "total_words": 2847291
  },
  "passages": {
    "total_passages": 16968,
    "with_morphology": 12450,
    "avg_passage_length": 168
  }
}
```

---

## Knowledge Graph API

Browse and analyze the knowledge graph (2,193 nodes, 8,616 edges).

### List Nodes

```http
GET /kg/nodes
```

Returns knowledge graph nodes with optional filtering.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `node_type` | string | - | Filter by type: `Person`, `Concept`, `Argument`, `Work`, `School`, `Debate`, `Position`, `Event`, `Institution`, `Text_Fragment`, `Modern_Interpretation`, `Term`, `Source_Collection`, `Doctrine`, `Passage` |
| `period` | string | - | Filter by period: `Presocratic`, `Classical Greek`, `Hellenistic Greek`, `Roman Republican`, `Roman Imperial`, `Late Antiquity` |
| `school` | string | - | Filter by school: `Stoic`, `Epicurean`, `Academic`, `Peripatetic`, `Pyrrhonist`, `Platonist` |
| `search` | string | - | Text search in label and description |
| `limit` | integer | 100 | Results per page (1-1000) |
| `offset` | integer | 0 | Pagination offset |

**Example:**
```bash
curl "http://localhost:8000/api/kg/nodes?node_type=Person&school=Stoic"
```

**Response:**
```json
[
  {
    "id": "chrysippus",
    "label": "Chrysippus",
    "type": "Person",
    "description": "Third head of the Stoic school (c. 279-206 BCE). Systematized Stoic logic and physics. Developed the Stoic position on fate and moral responsibility.",
    "period": "Hellenistic Greek",
    "school": "Stoic",
    "role": "ancient_primary",
    "metadata": {
      "birth_year": -279,
      "death_year": -206,
      "place": "Soli, Cilicia"
    },
    "community_id": 3,
    "centrality": 0.847
  }
]
```

### Get Node

```http
GET /kg/nodes/{node_id}
```

Returns a single node with full details.

**Errors:**
- `404` - Node not found

### Get Node Neighbors

```http
GET /kg/nodes/{node_id}/neighbors
```

Returns nodes and edges connected to the specified node up to a given depth.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `node_id` | string | Node identifier |

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `depth` | integer | 1 | Traversal depth (1-3) |

**Example:**
```bash
curl "http://localhost:8000/api/kg/nodes/chrysippus/neighbors?depth=2"
```

**Response:**
```json
{
  "center": "chrysippus",
  "depth": 2,
  "nodes": [
    {"id": "chrysippus", "label": "Chrysippus", "type": "Person"},
    {"id": "fate", "label": "Fate (εἱμαρμένη)", "type": "Concept"},
    {"id": "stoic_determinism", "label": "Stoic Determinism", "type": "Doctrine"}
  ],
  "edges": [
    {"source": "chrysippus", "target": "fate", "relation": "argues_for"},
    {"source": "chrysippus", "target": "stoic_determinism", "relation": "developed"}
  ]
}
```

### List Edges

```http
GET /kg/edges
```

Returns knowledge graph edges with optional filtering.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `relation` | string | - | Filter by relation type (see below) |
| `source` | string | - | Filter by source node ID |
| `target` | string | - | Filter by target node ID |
| `limit` | integer | 100 | Results per page (1-1000) |
| `offset` | integer | 0 | Pagination offset |

**Relation Types:**
- Argumentative: `argues_for`, `argues_against`, `refutes`, `supports`
- Intellectual: `influences`, `influenced_by`, `taught_by`, `student_of`
- Affiliation: `belongs_to_school`, `founded`, `member_of`
- Authorship: `wrote`, `authored_by`, `attributed_to`
- Citation: `cites`, `cited_by`, `references`, `quoted_in`
- Semantic: `discusses`, `defines`, `related_to`, `synonym_of`

**Response:**
```json
[
  {
    "id": "edge_001",
    "source": "chrysippus",
    "target": "fate",
    "relation": "argues_for",
    "description": "Chrysippus defends cosmic determinism",
    "weight": 0.95,
    "metadata": {"evidence": "SVF 2.912-944"}
  }
]
```

### Get Statistics

```http
GET /kg/statistics
```

Returns knowledge graph statistics.

**Response:**
```json
{
  "total_nodes": 2193,
  "total_edges": 8616,
  "density": 0.0036,
  "connected_components": 1,
  "avg_degree": 7.86,
  "node_types": {
    "Person": 245,
    "Concept": 412,
    "Argument": 189,
    "Work": 156,
    "School": 12,
    "Debate": 34
  },
  "edge_types": {
    "argues_for": 1245,
    "influences": 892,
    "wrote": 567,
    "discusses": 1123
  }
}
```

### Detect Communities

```http
GET /kg/communities
```

Detects and returns community structure using graph clustering algorithms.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `algorithm` | string | `leiden` | Algorithm: `leiden`, `louvain`, `greedy`, `semantic` |
| `resolution` | float | 1.0 | Resolution parameter (0.1-5.0). Higher = more communities |

**Example:**
```bash
curl "http://localhost:8000/api/kg/communities?algorithm=leiden&resolution=1.2"
```

**Response:**
```json
{
  "algorithm": "leiden",
  "resolution": 1.2,
  "total_communities": 15,
  "assignments": {
    "chrysippus": 3,
    "fate": 3,
    "epicurus": 7,
    "atomic_swerve": 7
  },
  "colors": {
    "3": "#e41a1c",
    "7": "#377eb8"
  },
  "communities": [
    {
      "id": 3,
      "color": "#e41a1c",
      "node_count": 145,
      "nodes": ["chrysippus", "cleanthes", "zeno", "fate", "stoic_determinism"]
    },
    {
      "id": 7,
      "color": "#377eb8",
      "node_count": 89,
      "nodes": ["epicurus", "lucretius", "atomic_swerve", "clinamen"]
    }
  ]
}
```

### Calculate Centrality

```http
GET /kg/centrality
```

Calculates centrality scores to identify influential nodes.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `metric` | string | `betweenness` | Metric: `betweenness`, `pagerank`, `degree`, `eigenvector` |
| `top_k` | integer | 20 | Number of top nodes to return (1-100) |

**Metric Descriptions:**
- `betweenness`: Nodes that bridge different communities
- `pagerank`: Nodes referenced by important nodes
- `degree`: Nodes with most connections
- `eigenvector`: Nodes connected to well-connected nodes

**Example:**
```bash
curl "http://localhost:8000/api/kg/centrality?metric=pagerank&top_k=10"
```

**Response:**
```json
{
  "metric": "pagerank",
  "top_k": 10,
  "top_nodes": [
    {"id": "fate", "score": 0.0847, "label": "Fate (εἱμαρμένη)", "type": "Concept"},
    {"id": "chrysippus", "score": 0.0723, "label": "Chrysippus", "type": "Person"},
    {"id": "to_eph_hemin", "score": 0.0651, "label": "τὸ ἐφ' ἡμῖν", "type": "Term"},
    {"id": "determinism", "score": 0.0589, "label": "Determinism", "type": "Concept"}
  ]
}
```

### Find Shortest Path

```http
GET /kg/path/{source}/{target}
```

Finds the shortest path between two nodes in the graph.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `source` | string | Source node ID |
| `target` | string | Target node ID |

**Example:**
```bash
curl "http://localhost:8000/api/kg/path/epicurus/augustine"
```

**Response:**
```json
{
  "source": "epicurus",
  "target": "augustine",
  "length": 4,
  "path": ["epicurus", "atomic_swerve", "free_will", "pelagius", "augustine"],
  "nodes": [
    {"id": "epicurus", "label": "Epicurus", "type": "Person"},
    {"id": "atomic_swerve", "label": "Atomic Swerve", "type": "Concept"},
    {"id": "free_will", "label": "Free Will", "type": "Concept"},
    {"id": "pelagius", "label": "Pelagius", "type": "Person"},
    {"id": "augustine", "label": "Augustine", "type": "Person"}
  ]
}
```

**Errors:**
- `404` - No path found between nodes

### Get Timeline

```http
GET /kg/timeline
```

Returns nodes grouped by historical period for timeline visualization.

**Response:**
```json
[
  {
    "period": "Presocratic",
    "start_year": -600,
    "end_year": -400,
    "nodes": [
      {"id": "heraclitus", "label": "Heraclitus", "type": "Person"}
    ]
  },
  {
    "period": "Classical Greek",
    "start_year": -400,
    "end_year": -323,
    "nodes": [
      {"id": "plato", "label": "Plato", "type": "Person"},
      {"id": "aristotle", "label": "Aristotle", "type": "Person"}
    ]
  }
]
```

---

## GraphRAG API

Graph-based Retrieval Augmented Generation for scholarly Q&A.

### Query (Non-Streaming)

```http
POST /graphrag/query
```

Executes a GraphRAG query combining semantic search, graph traversal, and LLM synthesis.

**Request Body:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `question` | string | **required** | User question (min 3 characters) |
| `semantic_k` | integer | 10 | Number of semantic search results (1-50) |
| `graph_depth` | integer | 2 | Graph traversal depth (1-4) |
| `max_context_nodes` | integer | 30 | Maximum nodes in LLM context (5-100) |
| `include_passages` | boolean | true | Include ancient text passages in context |
| `stream` | boolean | false | Enable streaming (use GET endpoint instead) |

**Example:**
```bash
curl -X POST "http://localhost:8000/api/graphrag/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What did the Stoics believe about fate and moral responsibility?",
    "semantic_k": 15,
    "graph_depth": 2,
    "include_passages": true
  }'
```

**Response:**
```json
{
  "answer": "The Stoics, particularly Chrysippus, developed a sophisticated compatibilist position on fate and moral responsibility. They held that all events are causally determined by fate (εἱμαρμένη), yet moral responsibility remains meaningful because our actions depend on our character and assent [1].\n\nChrysippus distinguished between 'principal' and 'auxiliary' causes to explain how our choices can be 'up to us' (τὸ ἐφ' ἡμῖν) even within a deterministic framework [2]. External circumstances provide occasions for action, but our responses flow from our internal character [P1].\n\nThis position was criticized by the Epicureans, who argued that genuine freedom requires the 'atomic swerve' (clinamen) to break causal chains [3].",
  "question": "What did the Stoics believe about fate and moral responsibility?",
  "citations": [
    {
      "ref": "1",
      "type": "node",
      "id": "stoic_compatibilism",
      "label": "Stoic Compatibilism",
      "confidence": 0.92
    },
    {
      "ref": "2",
      "type": "node",
      "id": "chrysippus_cylinder",
      "label": "Cylinder Argument",
      "confidence": 0.88
    },
    {
      "ref": "P1",
      "type": "passage",
      "id": "660e8400...",
      "label": "Cicero, De Fato 43",
      "confidence": 0.95
    },
    {
      "ref": "3",
      "type": "node",
      "id": "epicurean_clinamen",
      "label": "Epicurean Clinamen",
      "confidence": 0.85
    }
  ],
  "seed_nodes": ["fate", "stoic", "moral_responsibility"],
  "context_nodes": ["chrysippus", "fate", "stoic_determinism", "to_eph_hemin", "cylinder_argument", "cleanthes", "zeno", "epicurus", "clinamen"],
  "passages_used": 5,
  "metadata": {
    "llm_provider": "gemini",
    "model": "gemini-3-flash",
    "thinking_mode": false,
    "query_time_ms": 2340
  }
}
```

### Query (Streaming)

```http
GET /graphrag/query/stream
```

Executes a GraphRAG query with Server-Sent Events (SSE) for real-time streaming.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `question` | string | **required** | User question |
| `semantic_k` | integer | 10 | Semantic search results |
| `graph_depth` | integer | 2 | Graph traversal depth |
| `max_context_nodes` | integer | 30 | Max context nodes |

**Example:**
```bash
curl -N "http://localhost:8000/api/graphrag/query/stream?question=What%20is%20fate"
```

**Response (SSE):**
```
data: The

data: Stoics

data: believed

data: that fate

data: (εἱμαρμένη)

data: governs

data: all events...

data: [DONE]
```

**Client Example (JavaScript):**
```javascript
const eventSource = new EventSource(
  '/api/graphrag/query/stream?question=What%20is%20fate'
);

eventSource.onmessage = (event) => {
  if (event.data === '[DONE]') {
    eventSource.close();
  } else if (event.data.startsWith('[ERROR]')) {
    console.error(event.data);
    eventSource.close();
  } else {
    process.stdout.write(event.data);
  }
};
```

### Health Check

```http
GET /graphrag/health
```

Returns GraphRAG service health status.

**Response:**
```json
{
  "status": "healthy",
  "kg_loaded": true,
  "nodes_count": 2193
}
```

---

## Error Handling

All errors return a consistent JSON structure:

```json
{
  "detail": "Error message describing the problem"
}
```

### HTTP Status Codes

| Code | Meaning | Common Causes |
|------|---------|---------------|
| `400` | Bad Request | Invalid query parameters, validation failed |
| `401` | Unauthorized | Missing or invalid authentication token |
| `403` | Forbidden | Insufficient permissions for operation |
| `404` | Not Found | Resource does not exist |
| `422` | Unprocessable Entity | Request body validation failed |
| `429` | Too Many Requests | Rate limit exceeded |
| `500` | Internal Server Error | Server-side error, check logs |
| `503` | Service Unavailable | Database or external service down |

### Validation Errors (422)

```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "question"],
      "msg": "String should have at least 3 characters",
      "input": "hi"
    }
  ]
}
```

---

## Rate Limits

Rate limits are enforced per IP address or authenticated user.

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/search` | 60 | 1 minute |
| `/kg/*` | 100 | 1 minute |
| `/graphrag/query` | 20 | 1 minute |
| `/graphrag/query/stream` | 10 | 1 minute |
| `/works/*` | 100 | 1 minute |

**Rate Limit Headers:**

```http
X-RateLimit-Limit: 20
X-RateLimit-Remaining: 15
X-RateLimit-Reset: 1706644800
```

**When exceeded:**
```json
{
  "detail": "Rate limit exceeded. Try again in 45 seconds."
}
```

---

## Appendix: Node Types

| Type | Count | Description |
|------|-------|-------------|
| `Person` | 245 | Philosophers and scholars |
| `Concept` | 412 | Philosophical concepts |
| `Argument` | 189 | Named arguments |
| `Work` | 156 | Ancient texts |
| `School` | 12 | Philosophical schools |
| `Debate` | 34 | Philosophical debates |
| `Position` | 67 | Philosophical stances |
| `Event` | 23 | Historical events |
| `Institution` | 8 | Academies, schools |
| `Text_Fragment` | 89 | Fragmentary texts |
| `Modern_Interpretation` | 45 | Scholarly interpretations |
| `Term` | 156 | Technical terms |
| `Source_Collection` | 12 | Collections like SVF |
| `Doctrine` | 78 | Formal doctrines |
| `Passage` | 617 | Key passages |

## Appendix: Historical Periods

| Period | Dates | Description |
|--------|-------|-------------|
| Presocratic | 6th-5th c. BCE | Early Greek philosophy |
| Classical Greek | 5th-4th c. BCE | Plato, Aristotle |
| Hellenistic Greek | 4th-1st c. BCE | Stoics, Epicureans, Skeptics |
| Roman Republican | 2nd-1st c. BCE | Cicero, Lucretius |
| Roman Imperial | 1st-3rd c. CE | Seneca, Epictetus, Marcus Aurelius |
| Patristic | 2nd-5th c. CE | Church Fathers |
| Late Antiquity | 4th-6th c. CE | Boethius, Neoplatonists |
