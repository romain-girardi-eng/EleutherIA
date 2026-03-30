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
- 487 ancient works
- 69,277 passages
- CTS URN support
- Lemmatization data

### 2. eleutheria-kg

**Purpose:** Knowledge graph framework

**Key Components:**
- `KGAnalytics` - Community detection, centrality
- `QdrantService` - Vector similarity search
- `KGCache` - TTL-based caching

**Data:**
- 17,746 nodes (22 types) — including passage translation pairs
- 42,925 edges (56 relation types)
- 3072-dim Gemini embeddings

**Two-Node Passage Architecture:**
Every passage has a source node (Greek/Latin) and a translation node (English, `_en` suffix). The source node preserves authoritative text; the translation node makes it discoverable via English semantic search. Linked by `translation_of` / `has_translation` edges. See [Passage Translation Architecture](../plans/2026-02-24-passage-translation-architecture.md).

### 3. eleutheria-graphrag

**Purpose:** Graph-based RAG for Q&A

**Key Components:**
- `PageIndex V3` - Direct retrieval pipeline (2 LLM calls)
- `LLMService` - Multi-provider LLM interface (Kimi K2 / Gemini)
- Streaming SSE responses

**Pipeline (PageIndex V3):**
1. Embed query → Qdrant parallel search (KG nodes + passages + edges)
2. Enrich → passage_citations lookup + KG neighbor expansion
3. Build FULL context (no truncation — Gemini 1M token context)
4. ONE synthesis call → scholarly answer with citations

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

### GraphRAG Query (PageIndex V3)
```
User Question
    │
    ▼
┌─────────────────────────────────────┐
│ 1. Embed + Detect References        │
│    Query → Gemini embedding          │
│    + CTS URN reference detection     │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│ 2. Parallel Search (no LLM)         │
│    KG nodes + passages + edges       │
│    via Qdrant vector similarity      │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│ 3. Parallel Enrichment              │
│    passage_citations → full text     │
│    + KG neighbor expansion           │
│    + textual grounding               │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│ 4. Build FULL Context               │
│    No truncation (Gemini 1M tokens)  │
│    Primary sources + KG entities     │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│ 5. ONE Synthesis Call               │
│    Kimi K2 / Gemini                  │
│    → Scholarly answer + citations    │
└──────────────────┬──────────────────┘
                   │
                   ▼
            Answer + Sources
```

## Database Schema

### Core Tables

| Table | Description |
|-------|-------------|
| `ancient_works` | 487 canonical texts with CTS URNs |
| `passages` | 69,277 hierarchical text units |
| `passage_citations` | Links passages to KG nodes |
| `kg_nodes` | 17,746 knowledge graph nodes |
| `kg_edges` | 42,925 relationships |
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
| LLM | Gemini (gemini-3.1-pro-preview, primary), Kimi K2.5 Thinking (extended reasoning) |
| Deployment | Docker Compose |

## FAIR Compliance

| Principle | Implementation |
|-----------|----------------|
| **Findable** | DOI via Zenodo, CITATION.cff, codemeta.json |
| **Accessible** | REST API, HTTPS, OpenAPI spec |
| **Interoperable** | CTS URNs, JSON-LD, RDF ontology |
| **Reusable** | CC BY 4.0, modular packages, docs |
