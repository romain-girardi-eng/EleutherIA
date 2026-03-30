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

Browse the ancient texts corpus (487 works, 69k passages).

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
    "total_works": 487,
    "greek_works": 310,
    "latin_works": 28,
    "english_works": 131,
    "hebrew_works": 13,
    "arabic_works": 5,
    "total_words": 8500000
  },
  "passages": {
    "total_passages": 69277,
    "with_morphology": 12450,
    "avg_passage_length": 168
  }
}
```

---

## Knowledge Graph API

Browse and analyze the knowledge graph (17,746 nodes, 42,925 edges).

### List Nodes

```http
GET /kg/nodes
```

Returns knowledge graph nodes with optional filtering.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `node_type` | string | - | Filter by type: `Person`, `Concept`, `Argument`, `Work`, `School`, `Debate`, `Position`, `Event`, `Institution`, `Text_Fragment`, `Modern_Interpretation`, `Term`, `Source_Collection`, `Doctrine`, `Passage`, `Publication`, `Quote`, `Synthesis`, `Controversy`, `Conceptual_Evolution`, `Group`, `Argument_Framework` |
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

**Relation Types (56 across 12 categories):**
- Argumentative: `argues_for`, `argues_against`, `refutes`, `responds_to`, `supports`, `critiques`
- Intellectual: `influences`, `influenced`, `influenced_by`, `taught_by`, `teaches`, `student_of`, `extends`
- Affiliation: `belongs_to_school`, `has_member`, `member_of`, `founded`
- Authorship: `wrote`, `authored_by`, `created_by`, `developed_by`
- Citation: `cites`, `cited_by`, `source_for`, `evidenced_by`
- Textual: `preserves`, `preserved_in`
- Structural: `contains`, `part_of`, `translation_of`, `has_translation`, `has_section`, `has_chapter`, `belongs_to_corpus`
- Semantic: `discusses`, `discussed_in`, `defines`, `related_to`, `contrasts_with`, `parallel_to`, `employs`, `presupposes`, `grounded_in`
- Doctrinal: `holds_position`, `endorses`, `rejects`
- Debate: `participates_in`, `contributes_to`
- Hermeneutic: `interprets`, `interpreted_by`, `represents`, `exemplifies`, `specializes_in`
- Temporal: `contemporary_of`, `precedes`, `follows`

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
  "total_nodes": 17746,
  "total_edges": 42925,
  "density": 0.00027,
  "connected_components": 1,
  "avg_degree": 4.84,
  "node_types": {
    "Person": 280,
    "Concept": 520,
    "Argument": 350,
    "Work": 500,
    "School": 22,
    "Debate": 40,
    "Passage": 14800,
    "Publication": 85,
    "Quote": 45,
    "Term": 180,
    "..."
  },
  "edge_types": {
    "part_of": 15200,
    "authored_by": 8500,
    "discusses": 2100,
    "argues_for": 1400,
    "influences": 950,
    "..."
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

Graph-based Retrieval Augmented Generation for scholarly Q&A. Uses the **PageIndex V3** pipeline: direct KG + passage retrieval with ONE synthesis call (see [PageIndex V3 docs](../PAGEINDEX_V3.md)).

### Query (Non-Streaming)

```http
POST /graphrag/query
```

Executes a PageIndex V3 query: parallel vector search, passage_citations enrichment, and LLM synthesis.

**Request Body:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `question` | string | **required** | User question (min 3 characters) |

**Example:**
```bash
curl -X POST "https://free-will.app/api/graphrag/answer" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What did the Stoics believe about fate and moral responsibility?"
  }'
```

**Response:**
```json
{
  "answer": "The Stoics, particularly Chrysippus, developed a sophisticated compatibilist position...",
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
      "ref": "P1",
      "type": "passage",
      "id": "660e8400...",
      "label": "Cicero, De Fato 43",
      "cts_urn": "urn:cts:latinLit:phi0474.phi049:43",
      "confidence": 0.95
    }
  ],
  "sources": [...],
  "metadata": {
    "llm_provider": "gemini",
    "model": "gemini-3.1-pro-preview",
    "pipeline": "pageindex-v3",
    "quality_score": 0.85,
    "quality_badge": "High"
  },
  "pageIndexInfo": {
    "linkedPassagesCount": 12,
    "neighborsCount": 8,
    "semanticPassagesCount": 5,
    "totalContextChars": 28500,
    "estimatedTokens": 7125
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
  "nodes_count": 17746
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

## Appendix: Node Types (22)

| Type | Description |
|------|-------------|
| `Person` | Philosophers and scholars |
| `Concept` | Philosophical concepts |
| `Argument` | Named arguments |
| `Work` | Ancient texts and modern scholarship |
| `School` | Philosophical schools |
| `Debate` | Philosophical debates |
| `Position` | Philosophical stances |
| `Event` | Historical events |
| `Institution` | Academies, schools |
| `Text_Fragment` | Fragmentary texts preserved in secondary sources |
| `Modern_Interpretation` | Scholarly interpretations |
| `Term` | Technical philosophical terms |
| `Source_Collection` | Collections (SVF, LS, etc.) |
| `Doctrine` | Formal doctrines |
| `Passage` | Key textual passages (source + translation pairs) |
| `Publication` | Modern scholarly publications |
| `Quote` | Notable philosophical quotations |
| `Synthesis` | Scholarly syntheses combining multiple sources |
| `Controversy` | Scholarly or philosophical controversies |
| `Conceptual_Evolution` | Historical evolution of a concept |
| `Group` | Groups of philosophers or intellectual communities |
| `Argument_Framework` | Structured frameworks for analyzing arguments |

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
