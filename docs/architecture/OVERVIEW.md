# Architecture Overview

EleutherIA is a FAIR-compliant knowledge graph system with three independent packages.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│                  React + TypeScript + Vite                   │
│         Cosmograph (GPU graph) + Tailwind CSS (styling)     │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP/REST
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway                             │
│                        FastAPI                               │
│            Routes: /works, /kg, /graphrag, /search          │
└───────┬─────────────────┬─────────────────┬─────────────────┘
        │                 │                 │
        ▼                 ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│   database    │ │      kg       │ │   graphrag    │
│   Package     │ │   Package     │ │   Package     │
│               │ │               │ │               │
│ - Works API   │ │ - Analytics   │ │ - RAG Pipeline│
│ - Search      │ │ - Communities │ │ - LLM Service │
│ - Passages    │ │ - Centrality  │ │ - Citations   │
└───────┬───────┘ └───────┬───────┘ └───────┬───────┘
        │                 │                 │
        ▼                 ▼                 │
┌───────────────┐ ┌───────────────┐         │
│  PostgreSQL   │ │    Qdrant     │◄────────┘
│  (Relational) │ │   (Vectors)   │
│               │ │               │
│ - Works       │ │ - KG nodes    │
│ - Passages    │ │ - Text embeds │
│ - Citations   │ │ - Edge embeds │
└───────────────┘ └───────────────┘
```

## The Three Packages

### 1. eleutheria-database

**Purpose:** Ancient texts corpus management

**Key Components:**
- `DatabaseService` - AsyncPG connection pooling
- `HybridSearchService` - Full-text + lemmatic search
- Works/Passages API routes

**Data:**
- 189 ancient works
- 16,968 passages
- CTS URN support
- Lemmatization data

### 2. eleutheria-kg

**Purpose:** Knowledge graph framework

**Key Components:**
- `KGAnalytics` - Community detection, centrality
- `QdrantService` - Vector similarity search
- `KGCache` - TTL-based caching

**Data:**
- 2,193 nodes (15 types)
- 8,616 edges (32 relation types)
- 3072-dim Gemini embeddings

### 3. eleutheria-graphrag

**Purpose:** Graph-based RAG for Q&A

**Key Components:**
- `GraphRAGService` - 5-stage RAG pipeline
- `LLMService` - Multi-provider LLM interface
- Streaming SSE responses

**Pipeline:**
1. Semantic search → seed nodes
2. Graph traversal → expanded context
3. Context building → prompt assembly
4. LLM synthesis → answer generation
5. Citation extraction → source grounding

## Data Flow

### Search Query
```
User Query
    │
    ▼
┌─────────────┐
│ Hybrid      │
│ Search      │
└──────┬──────┘
       │
       ├──────────────┬──────────────┐
       ▼              ▼              ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ Full-text   │ │ Lemmatic    │ │ Semantic    │
│ PostgreSQL  │ │ PostgreSQL  │ │ Qdrant      │
└──────┬──────┘ └──────┬──────┘ └──────┬──────┘
       │              │              │
       └──────────────┴──────────────┘
                      │
                      ▼
               ┌─────────────┐
               │ RRF Fusion  │
               │ Merge ranks │
               └──────┬──────┘
                      │
                      ▼
               Final Results
```

### GraphRAG Query
```
User Question
    │
    ▼
┌─────────────────────────────────────┐
│ 1. Semantic Search                  │
│    Question → Embedding → Qdrant    │
│    → Top-K seed nodes               │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│ 2. Graph Traversal                  │
│    BFS from seeds (depth 1-3)       │
│    → Expanded node set              │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│ 3. Context Building                 │
│    Node descriptions + passages     │
│    → Structured prompt              │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│ 4. LLM Synthesis                    │
│    Gemini 3 / Kimi K2.5 Thinking    │
│    → Scholarly answer               │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│ 5. Citation Extraction              │
│    Parse [1], [2], [P1] refs        │
│    → Grounded citations             │
└──────────────────┬──────────────────┘
                   │
                   ▼
            Answer + Sources
```

## Database Schema

### Core Tables

| Table | Description |
|-------|-------------|
| `ancient_works` | 189 canonical texts with CTS URNs |
| `passages` | 16,968 hierarchical text units |
| `passage_citations` | Links passages to KG nodes |
| `kg_nodes` | 2,193 knowledge graph nodes |
| `kg_edges` | 8,616 relationships |
| `text_embeddings` | 3072-dim vectors in Qdrant |

### Key Indexes

- Full-text GIN on `passages.text_content`
- B-tree on CTS URNs for canonical lookups
- JSONB GIN on metadata fields

## Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 19, TypeScript, Vite, Tailwind CSS |
| Visualization | Cosmograph (GPU-accelerated WebGL) |
| API | FastAPI (Python 3.11+) |
| Database | PostgreSQL 16 |
| Vector DB | Qdrant |
| LLM | Gemini 3 (primary), Kimi K2.5 Thinking (extended reasoning) |
| Deployment | Docker Compose |

## FAIR Compliance

| Principle | Implementation |
|-----------|----------------|
| **Findable** | DOI via Zenodo, CITATION.cff, codemeta.json |
| **Accessible** | REST API, HTTPS, OpenAPI spec |
| **Interoperable** | CTS URNs, JSON-LD, RDF ontology |
| **Reusable** | CC BY 4.0, modular packages, docs |
