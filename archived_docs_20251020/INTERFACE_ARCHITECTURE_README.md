# 🏛️ Ancient Free Will Database - Complete Interface Architecture

**Version:** 1.0.0
**Date:** October 17, 2025
**Status:** Backend Complete (Phase 1 & 2 ✅), Frontend Planned (Phase 3 📅)

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Backend (COMPLETED ✅)](#backend-completed)
4. [Frontend (PLANNED)](#frontend-planned)
5. [Setup and Installation](#setup-and-installation)
6. [API Documentation](#api-documentation)
7. [Deployment](#deployment)
8. [Development Roadmap](#development-roadmap)

---

## Overview

This interface provides a comprehensive web-based platform for exploring the Ancient Free Will Database, combining:

- **Dual Knowledge Graph Visualization** (Cytoscape.js + Semativerse 🔒)
- **Hybrid Search** (Full-text + Lemmatic + Semantic via Qdrant)
- **GraphRAG Question Answering** (Gemini LLM + Graph Traversal)
- **289 Ancient Texts** (Greek & Latin with lemmas)
- **465 KG Nodes, 740 Edges**

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                      Frontend (React)                      │
│  ┌──────────────┬──────────────┬──────────────────────┐  │
│  │ KG Visualizer│ Search UI    │ GraphRAG Q&A         │  │
│  │ Cytoscape /  │ Hybrid       │ Natural Language     │  │
│  │ Semativerse🔒│ Full+Lem+Sem │ with Citations       │  │
│  └──────────────┴──────────────┴──────────────────────┘  │
└───────────────────────────┬──────────────────────────────┘
                            │ REST API (JSON)
┌───────────────────────────▼──────────────────────────────┐
│                  Backend (FastAPI)                         │
│  ┌──────────────┬──────────────┬──────────────────────┐  │
│  │ KG Routes    │ Search Routes│ GraphRAG Routes      │  │
│  │ Text Routes  │ Auth Routes  │                      │  │
│  └──────────────┴──────────────┴──────────────────────┘  │
│  ┌──────────────┬──────────────┬──────────────────────┐  │
│  │ Hybrid Search│ Qdrant Svc   │ DB Service           │  │
│  │ (RRF)        │ (Semantic)   │ (PostgreSQL)         │  │
│  └──────────────┴──────────────┴──────────────────────┘  │
└───────────────────────────┬──────────────────────────────┘
                            │
           ┌────────────────┼────────────────┐
           │                │                │
           ▼                ▼                ▼
    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
    │ PostgreSQL  │  │   Qdrant    │  │  Gemini API │
    │ (289 texts) │  │ (Vectors)   │  │ (Embeddings)│
    │ (Lemmas)    │  │ (3072 dim)  │  │ (LLM)       │
    └─────────────┘  └─────────────┘  └─────────────┘
```

---

## Backend (COMPLETED ✅)

### Components

#### 1. **FastAPI Main Application** (`backend/api/main.py`)

- Lifespan management (startup/shutdown)
- CORS middleware
- Service initialization (PostgreSQL + Qdrant)
- Global exception handling
- Health check endpoint

**Key Features:**
- Async context manager for DB connections
- Automatic service injection
- OpenAPI documentation at `/docs`

#### 2. **Services**

##### **DatabaseService** (`backend/services/db.py`)
- PostgreSQL connection pooling (asyncpg)
- Query execution helpers (`fetch`, `fetchrow`, `fetchval`, `execute`)
- Connection context manager
- 289 ancient texts with lemmas (109 texts lemmatized)

##### **QdrantService** (`backend/services/qdrant_service.py`)
- Qdrant vector database integration
- Three collections:
  - `kg_nodes` - 465 Knowledge Graph nodes
  - `kg_edges` - 740 Knowledge Graph edges
  - `text_embeddings` - 289 ancient texts
- HNSW indexing for fast ANN search
- Cosine similarity search

##### **HybridSearchService** (`backend/services/hybrid_search.py`)
- **Three search modes:**
  - Full-text (PostgreSQL `ts_rank`)
  - Lemmatic (existing lemmas in JSONB)
  - Semantic (Qdrant vector similarity)
- **Reciprocal Rank Fusion (RRF)** for result merging
- Query embedding generation (Gemini)
- Configurable search modes

**RRF Algorithm:**
```python
score(item) = Σ 1/(k + rank_i) for all search modes i
```

##### **GraphRAGService** (`backend/services/graphrag_service.py`) ✨ NEW
- **Complete 6-step pipeline** for question answering:
  1. Semantic search (Qdrant) - find relevant starting nodes
  2. Graph traversal (BFS) - expand to connected nodes (depth-limited)
  3. Citation extraction - gather ancient sources + modern scholarship
  4. Context building - prioritize nodes for LLM consumption
  5. LLM synthesis (Gemini 1.5 Pro) - generate grounded answer
  6. Reasoning path - create visualization data
- **BFS graph traversal** with adjacency list caching
- **Citation tracking** for academic rigor
- **Hallucination prevention** via strict system prompt
- **Configurable parameters**: semantic_k, graph_depth, max_context, temperature

#### 3. **API Routes**

##### **Knowledge Graph Routes** (`backend/api/kg_routes.py`)
- `GET /api/kg/nodes` - Get all nodes (filterable)
- `GET /api/kg/edges` - Get all edges (filterable)
- `GET /api/kg/node/{id}` - Node details
- `GET /api/kg/node/{id}/connections` - Node connections
- `GET /api/kg/viz/cytoscape` - Cytoscape.js formatted data
- `GET /api/kg/stats` - KG statistics

##### **Search Routes** (`backend/api/search_routes.py`)
- `POST /api/search/hybrid` - Hybrid search (RRF)
- `POST /api/search/fulltext` - Full-text only
- `POST /api/search/lemmatic` - Lemmatic only
- `POST /api/search/semantic` - Semantic only
- `POST /api/search/kg` - KG semantic search

##### **GraphRAG Routes** (`backend/api/graphrag_routes.py`)
- `POST /api/graphrag/query` - Question answering (complete pipeline)
- `POST /api/graphrag/query/stream` - Streaming question answering (SSE)
- `GET /api/graphrag/status` - Service status and capabilities

**Pipeline Steps:**
1. Semantic search (Qdrant) - find relevant starting nodes
2. Graph traversal (BFS) - expand to connected nodes
3. Context building - create rich context with citations
4. LLM synthesis (Gemini) - generate grounded answer
5. Citation extraction - track ancient sources and modern scholarship
6. Reasoning path - visualize graph traversal

##### **Text Routes** (`backend/api/text_routes.py`)
- `GET /api/texts/list` - List all texts (filterable)
- `GET /api/texts/{id}` - Get text content
- `GET /api/texts/{id}/structure` - Hierarchical structure
- `GET /api/texts/stats/overview` - Text statistics

##### **Auth Routes** (`backend/api/auth.py`)
- `POST /api/auth/semativerse/check` - Check Semativerse permission 🔒
- `GET /api/auth/semativerse/status` - Semativerse status

---

## Frontend (PLANNED)

### Tech Stack

- **React 18** + **TypeScript**
- **Vite** (build tool)
- **Cytoscape.js** (public KG visualization)
- **Semativerse** (private 3D/2D visualization) 🔒
- **Tailwind CSS** (styling)

### Components

#### 1. **KG Visualizer** (`KGVisualizerCytoscape.tsx` + `KGVisualizerSemativerse.tsx`)

**Cytoscape.js (Public):**
- 465 nodes, 740 edges
- Force-directed layout
- Node types: person, work, concept, argument, etc.
- Interactive: zoom, pan, filter, search
- Node inspector panel
- Export: PNG, SVG, PDF

**Semativerse (Private) 🔒:**
- 3D Mode: WebGL2 + Three.js + UnrealBloomPass
- 2D Mode: Canvas2D with optimized glow
- 60 FPS with 5,000+ nodes
- Category suns, domain colors
- Recording (60 FPS video), screenshots
- Auth-gated via `/api/auth/semativerse/check`

**User Choice:**
- Settings dropdown: "Visualization Mode: [Cytoscape | Semativerse 🔒]"
- Permission check before loading Semativerse
- Fallback to Cytoscape if no permission

#### 2. **Search Interface** (`SearchInterface.tsx`)

- Query input (Greek/Latin/English)
- Mode toggles:
  - ☑ Full-text
  - ☑ Lemmatic (109 lemmatized texts)
  - ☑ Semantic (Qdrant)
- Results list with:
  - Title, author, language
  - Relevance scores (RRF)
  - Snippets with highlights
  - Links to full text
- Pagination

#### 3. **GraphRAG Q&A** (`GraphRAGChat.tsx`)

- Natural language input
- Streaming responses
- Visual reasoning path (graph traversal highlighted in KG)
- Citation sidebar:
  - Ancient sources
  - Modern scholarship
- Export: PDF, LaTeX, BibTeX
- Deep Mode toggle (includes full-text search)

#### 4. **Text Explorer** (`TextExplorer.tsx`)

- Browse 289 texts by category:
  - New Testament (57)
  - Origen (48)
  - Tertullian (99)
  - Original Works (61)
  - Etc.
- Hierarchical structure viewer
- Full-text display with annotations
- Cross-references to KG nodes

---

## Setup and Installation

### Prerequisites

1. **Python 3.11+**
2. **PostgreSQL 15+** (running on port 5433)
3. **Qdrant** (running on port 6333)
4. **Gemini API Key**

### Backend Setup

```bash
# 1. Navigate to backend directory
cd "Ancient Free Will Database/backend"

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set environment variables
export GEMINI_API_KEY="your_gemini_api_key"
export SEMATIVERSE_ACCESS_KEY="your_secret_key"  # For Semativerse auth

# 5. Ensure services are running
# PostgreSQL: docker-compose up postgres (port 5433)
# Qdrant: docker run -p 6333:6333 qdrant/qdrant

# 6. Setup Qdrant (one-time)
cd ..
python3 setup_qdrant_vector_db.py

# 7. Start FastAPI server
cd backend
python3 -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**Server will be available at:**
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/health

### Frontend Setup (Coming Soon)

```bash
# Navigate to frontend directory
cd "Ancient Free Will Database/frontend"

# Install dependencies
npm install

# Set environment variables
echo "VITE_API_URL=http://localhost:8000" > .env

# Start development server
npm run dev
```

---

## API Documentation

### Example: Hybrid Search

```bash
curl -X POST http://localhost:8000/api/search/hybrid \
  -H "Content-Type: application/json" \
  -d '{
    "query": "ἐφ ἡμῖν",
    "limit": 10,
    "enable_fulltext": true,
    "enable_lemmatic": true,
    "enable_semantic": true
  }'
```

**Response:**
```json
{
  "combined_results": [
    {
      "id": "...",
      "title": "Nicomachean Ethics",
      "author": "Aristotle",
      "rrf_score": 0.347,
      "snippet": "...ἐφ ἡμῖν καὶ τὸ μὴ πράττειν..."
    }
  ],
  "fulltext_results": [...],
  "lemmatic_results": [...],
  "semantic_results": [...],
  "total_found": 10
}
```

### Example: Get Cytoscape Data

```bash
curl http://localhost:8000/api/kg/viz/cytoscape
```

**Response:**
```json
{
  "elements": {
    "nodes": [
      {
        "data": {
          "id": "person_aristotle_384_322bce_c2d4f6a8",
          "label": "Aristotle",
          "type": "person",
          "period": "Ancient Greek",
          ...
        }
      }
    ],
    "edges": [
      {
        "data": {
          "id": "edge_123",
          "source": "person_aristotle_384_322bce_c2d4f6a8",
          "target": "work_nicomachean_ethics_f3e7d2a1",
          "relation": "authored"
        }
      }
    ]
  }
}
```

### Example: Semativerse Permission Check 🔒

```bash
curl -X POST http://localhost:8000/api/auth/semativerse/check \
  -H "Content-Type: application/json" \
  -d '{
    "access_key": "your_secret_key"
  }'
```

**Response:**
```json
{
  "has_permission": true,
  "message": "Access granted"
}
```

---

## Deployment

### Docker Setup (Recommended)

**Create `docker-compose.yml`:**

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    ports:
      - "5433:5432"
    environment:
      POSTGRES_DB: ancient_free_will_db
      POSTGRES_USER: free_will_user
      POSTGRES_PASSWORD: free_will_password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - qdrant
    environment:
      GEMINI_API_KEY: ${GEMINI_API_KEY}
      SEMATIVERSE_ACCESS_KEY: ${SEMATIVERSE_ACCESS_KEY}
    command: uvicorn api.main:app --host 0.0.0.0 --port 8000

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
    environment:
      VITE_API_URL: http://backend:8000

volumes:
  postgres_data:
  qdrant_data:
```

**Deploy:**
```bash
docker-compose up -d
```

---

## Development Roadmap

### ✅ Phase 1: Backend Foundation (COMPLETE)
- [x] FastAPI application setup
- [x] PostgreSQL service
- [x] Qdrant service
- [x] Hybrid search with RRF
- [x] API routes (KG, Search, GraphRAG, Texts, Auth)
- [x] Semativerse authentication

### ✅ Phase 2: GraphRAG Enhancement (COMPLETE)
- [x] Complete GraphRAG service implementation
- [x] Implement graph traversal algorithm (BFS)
- [x] Citation tracking and extraction
- [x] Reasoning path visualization data
- [x] Streaming responses (SSE)
- [x] Standard and streaming API endpoints

**Documentation:** See `PHASE2_GRAPHRAG_SUMMARY.md` for detailed implementation docs

### 📅 Phase 3: Frontend Development (PLANNED)
- [ ] React + TypeScript setup (Vite)
- [ ] Cytoscape.js KG visualizer
- [ ] Semativerse integration (auth-gated)
- [ ] Search interface (hybrid mode)
- [ ] GraphRAG Q&A panel
- [ ] Text explorer
- [ ] Export capabilities

### 📅 Phase 4: Polish & Deployment (PLANNED)
- [ ] Academic styling
- [ ] Responsive design
- [ ] Accessibility (WCAG 2.1)
- [ ] Performance optimization
- [ ] Docker deployment
- [ ] Documentation
- [ ] Testing

---

## Key Technologies

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| Backend | FastAPI | 0.104+ | REST API framework |
| Database | PostgreSQL | 15+ | Text storage, full-text search |
| Vector DB | Qdrant | Latest | Semantic search, HNSW indexing |
| Embeddings | Gemini | text-embedding-004 | 3072-dim vectors |
| LLM | Gemini | gemini-1.5-pro | GraphRAG synthesis |
| Lemmatization | Existing lemmas | - | 109/289 texts pre-lemmatized |
| Search Fusion | RRF Algorithm | - | State-of-the-art 2024 |
| Frontend | React + TypeScript | 18+ | Modern web UI |
| KG Viz (Public) | Cytoscape.js | Latest | Academic standard |
| KG Viz (Private) | Semativerse 🔒 | Custom | 3D/2D, 60 FPS |

---

## Notes

### Semativerse Integration 🔒

**CRITICAL:** Semativerse code is private and requires explicit permission.

**Implementation Strategy:**
1. Separate module (not in main repo)
2. Auth-gated endpoint `/api/auth/semativerse/check`
3. Frontend permission check before loading
4. Fallback to Cytoscape if no permission
5. Environment variable for access key

**File Structure:**
```
frontend/
├── src/
│   └── components/
│       ├── KGVisualizerCytoscape.tsx  (public)
│       └── KGVisualizerProxy.tsx      (permission check)
└── private/                            (git-ignored)
    └── semativerse/
        └── SemativerseComponent.tsx
```

### Existing Lemmatization

**Status:** 109/289 texts already have lemmas in PostgreSQL

**Location:** `free_will.texts` table, `lemmas` JSONB column

**Usage:** Hybrid search automatically includes lemmatic mode

**Future:** Can use Lemmatika (`/Users/romaingirardi/Documents/Lemmatika`) to lemmatize remaining 180 texts if needed

---

## Support

For questions or issues:
1. Check `/docs` endpoint for API documentation
2. Review this README
3. Examine example code in `examples/`
4. Open GitHub issue (if applicable)

---

**Status:** Backend Complete ✅ | Frontend Planned 📅 | Docker Setup Pending 🔧

**Last Updated:** October 17, 2025
