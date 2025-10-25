# Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React 19)                    │
│  - SPA with React Router                                    │
│  - Cytoscape.js for graph visualization                     │
│  - D3.js for analytics charts                               │
│  - Tailwind CSS for styling                                 │
└──────────────────┬──────────────────────────────────────────┘
                   │ REST API (HTTP/JSON)
                   ↓
┌─────────────────────────────────────────────────────────────┐
│                   Backend (FastAPI/Python 3.11)             │
│  - Async architecture (asyncio/uvicorn)                     │
│  - JWT authentication                                       │
│  - Structured logging (structlog)                           │
│  - Prometheus metrics                                       │
│  - Sentry error tracking                                    │
└──────┬──────────────────┬──────────────────┬───────────────┘
       │                  │                  │
       ↓                  ↓                  ↓
┌─────────────┐  ┌──────────────────┐  ┌────────────────────┐
│ PostgreSQL  │  │   Qdrant Vector  │  │  Knowledge Graph   │
│    16       │  │   Database v1.13 │  │  (JSON 13.4 MB)    │
│             │  │                  │  │                    │
│ 289 texts   │  │ 285 text vectors │  │  509 nodes         │
│ 35M+ chars  │  │ 3072 dimensions  │  │  820 edges         │
└─────────────┘  └──────────────────┘  └────────────────────┘
```

## Core Design Patterns

### 1. Layered Architecture

**API Layer** (`/backend/api/`)
- Route handlers
- Request/response validation (Pydantic)
- Authentication & authorization
- Error handling

**Service Layer** (`/backend/services/`)
- Business logic
- External service integration
- Data transformation
- Caching

**Data Layer**
- Database access (PostgreSQL via asyncpg)
- Vector search (Qdrant client)
- File I/O (Knowledge Graph JSON)

### 2. Async/Await Pattern

All I/O operations use async/await for non-blocking execution:

```python
@app.get("/api/kg/nodes")
async def get_nodes():
    nodes = await kg_service.get_all_nodes()  # Non-blocking
    return nodes
```

### 3. Dependency Injection

Services injected via FastAPI lifespan context:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize services
    db_service = DatabaseService()
    await db_service.connect()
    app.state.db = db_service

    yield

    # Shutdown: Clean up
    await db_service.close()
```

### 4. Service Locator Pattern

Global services accessible throughout the application:

```python
app.state.db       # DatabaseService
app.state.qdrant   # QdrantService
app.state.llm      # LLMService
```

## Key Components

### GraphRAG Pipeline (6 steps)

```
1. Semantic Search (Qdrant)
   ↓
2. Graph Traversal (NetworkX)
   ↓
3. Context Building (Metadata aggregation)
   ↓
4. Citation Extraction (Ancient + Modern sources)
   ↓
5. LLM Synthesis (Gemini/Ollama)
   ↓
6. Reasoning Path (Provenance tracking)
```

### Hybrid Search (RRF Fusion)

```
Full-Text Search (PostgreSQL ts_vector)  ─┐
                                          │
Lemmatic Search (Normalized tokens)     ─┤─→ RRF Merger
                                          │
Semantic Search (Vector similarity)     ─┘
```

## Technology Choices

### Backend: FastAPI + Python 3.11

**Why FastAPI?**
- Native async support (critical for I/O-heavy workloads)
- Automatic OpenAPI documentation
- Pydantic validation
- Excellent performance (similar to Node.js/Go)

**Why Python 3.11?**
- Rich ecosystem for NLP/ML (vector embeddings)
- NetworkX for graph algorithms
- Mature async libraries

**Alternatives Considered:**
- ❌ Django: Too heavy, sync-focused
- ❌ Flask: No native async, minimal structure
- ❌ Node.js: Less suitable for graph algorithms

### Database: PostgreSQL 16

**Why PostgreSQL?**
- Excellent full-text search (ts_vector/ts_query)
- JSONB support for flexible metadata
- Trigram similarity for fuzzy matching
- Rock-solid reliability

**Alternatives Considered:**
- ❌ MongoDB: Weaker full-text search
- ❌ Elasticsearch: Overkill, harder to manage
- ❌ SQLite: Not suitable for production scale

### Vector DB: Qdrant

**Why Qdrant?**
- Pure vector database (not a plugin)
- Excellent performance (HNSW algorithm)
- Easy self-hosting
- Good Python client

**Alternatives Considered:**
- ❌ Pinecone: Vendor lock-in, costly at scale
- ❌ Weaviate: More complex setup
- ❌ pgvector: Good but less performant

### LLM: Gemini + Ollama Fallback

**Why Gemini?**
- Free tier sufficient for research
- Good quality responses
- Fast inference
- No local GPU required

**Why Ollama Fallback?**
- Local execution (privacy)
- No API costs
- Works offline

### Frontend: React 19 + Vite

**Why React?**
- Large component ecosystem
- Excellent graph visualization libraries
- Mature routing (React Router)

**Why Vite?**
- Ultra-fast HMR
- Modern build tooling
- TypeScript out-of-the-box

## Data Flow

### GraphRAG Query

```
User → Frontend
  ↓ POST /api/graphrag/query
Backend API Layer
  ↓ Validate JWT
GraphRAG Service
  ↓ Embed query → Qdrant
  ↓ Find nodes → KG JSON
  ↓ Traverse graph → NetworkX
  ↓ Build context → String concat
  ↓ Generate answer → Gemini API
  ↓ Format response
Frontend ← JSON response
  ↓ Render answer + sources
User ← Display
```

### Search Query

```
User → Frontend
  ↓ POST /api/search/hybrid
Hybrid Search Service
  ├─→ PostgreSQL full-text ──→│
  ├─→ PostgreSQL lemmatic ───→│ RRF Merger
  └─→ Qdrant semantic ───────→│
  ↓ Merge & rank
Frontend ← Ranked results
```

## Performance Optimizations

### 1. Caching Strategy

**LRU Cache with TTL:**
```python
@cached(ttl=3600)  # 1 hour
async def get_kg_stats():
    # Expensive operation
    return compute_stats()
```

**Edge Caching (Cloudflare):**
- Static KG data: 1 hour
- Analytics: 30 minutes
- Health checks: 5 minutes

### 2. Connection Pooling

**PostgreSQL:**
- Min: 2 connections
- Max: 5 connections (Render free tier)
- Timeout: 60 seconds

**Qdrant:**
- Persistent HTTP/2 connection
- Connection reuse

### 3. Memory Management

**Garbage Collection:**
```python
@app.middleware("http")
async def gc_middleware(request, call_next):
    response = await call_next(request)
    gc.collect()  # Force GC after each request
    return response
```

**Reason:** Prevent memory leaks on Render free tier (512MB limit)

### 4. Lazy Loading

- Knowledge Graph loaded once on startup
- Embeddings fetched on-demand
- Texts streamed for large queries

## Security

### Authentication

- JWT tokens (HS256)
- 24-hour expiration
- Bcrypt password hashing (cost factor: 12)

### Authorization

- Public: KG, Search, Texts APIs
- Protected: GraphRAG API (requires JWT)
- Admin-only: User management

### CORS

- Environment-based origin whitelist
- No `allow_origins="*"` in production

### Rate Limiting

- GraphRAG: 30 req/15min per user
- Other: 100 req/min per IP

### Input Validation

- Pydantic models for all requests
- SQL injection prevention (parameterized queries)
- XSS prevention (no raw HTML rendering)

## Monitoring & Observability

### Structured Logging (structlog)

```json
{
  "event": "graphrag_query",
  "query": "What did Aristotle think...",
  "user_id": "uuid-here",
  "duration_seconds": 2.341,
  "nodes_retrieved": 5,
  "timestamp": "2025-10-25T10:00:00Z"
}
```

### Metrics (Prometheus)

- HTTP request counts/duration
- GraphRAG query performance
- LLM token usage
- Database query times
- Cache hit rates

### Error Tracking (Sentry)

- Automatic exception capture
- Breadcrumb tracking
- User context
- Performance monitoring

## Scalability Considerations

### Current Limitations (Render Free Tier)

- 512MB RAM
- Cold starts (15min inactivity)
- Single instance (no load balancing)

### Future Scaling Plan

1. **Horizontal Scaling:**
   - Move to Render paid tier
   - Add load balancer
   - Stateless API design (ready)

2. **Database Scaling:**
   - Migrate to managed PostgreSQL (Supabase/RDS)
   - Read replicas for search queries
   - Connection pooling via PgBouncer

3. **Vector DB Scaling:**
   - Migrate to Qdrant Cloud
   - Shard collections by time period
   - Batch embedding generation

4. **Caching Layer:**
   - Redis for distributed caching
   - Cache GraphRAG responses
   - CDN for static assets (already implemented)

## Deployment Architecture

```
┌─────────────────────────────────────────┐
│         Cloudflare CDN (Edge Cache)     │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│         Render.com (Free Tier)          │
│  - Docker container                     │
│  - Auto-deploy from main branch         │
│  - Environment variables                │
│  - Health check monitoring              │
└──────┬───────────────┬──────────────────┘
       │               │
       ↓               ↓
┌─────────────┐ ┌─────────────────────────┐
│ PostgreSQL  │ │    Qdrant Cloud         │
│ (Supabase)  │ │    (Cloud hosting)      │
└─────────────┘ └─────────────────────────┘
```

## Development Workflow

```
1. Local Development
   ├─ Docker Compose (PostgreSQL + Qdrant)
   ├─ Vite dev server (HMR)
   └─ Uvicorn reload mode

2. Testing
   ├─ Backend: pytest + coverage
   ├─ Frontend: Vitest + React Testing Library
   └─ Integration: API tests with httpx

3. CI/CD (GitHub Actions)
   ├─ Lint (ESLint, Flake8, Black)
   ├─ Type check (TypeScript, mypy)
   ├─ Tests
   └─ Build Docker image

4. Deployment
   ├─ Push to main branch
   ├─ Render auto-deploys
   └─ Health check verification
```

## Future Enhancements

### Short-term (Q2 2025)
- [ ] WebSocket support for real-time updates
- [ ] Batch GraphRAG queries
- [ ] Export to Gephi/Cytoscape formats
- [ ] Advanced filtering UI

### Mid-term (Q3-Q4 2025)
- [ ] Multi-language UI (i18n)
- [ ] GraphQL API
- [ ] Python SDK
- [ ] R package for researchers

### Long-term (2026+)
- [ ] Machine learning for argument classification
- [ ] Automated entity extraction from new texts
- [ ] Collaborative annotation features
- [ ] Mobile app (React Native)

---

**Last Updated**: 2025-10-25
**Version**: 1.0.0
