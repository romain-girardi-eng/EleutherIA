# Performance Optimization Guide

## Profiling Tools

### Backend Profiling

**Using cProfile**:
```bash
python -m cProfile -o profile.prof -m uvicorn api.main:app

# Analyze results
python -m pstats profile.prof
>>> sort time
>>> stats 20
```

**Using py-spy** (sampling profiler):
```bash
pip install py-spy
py-spy record -o profile.svg -- python -m uvicorn api.main:app
# Open profile.svg in browser
```

**Using memory_profiler**:
```python
from memory_profiler import profile

@profile
async def expensive_function():
    # Function code
    pass
```

### Database Profiling

**PostgreSQL EXPLAIN ANALYZE**:
```sql
EXPLAIN ANALYZE
SELECT * FROM texts
WHERE to_tsvector('english', content) @@ to_tsquery('liberum & arbitrium');
```

**Slow Query Log**:
```sql
ALTER DATABASE ancient_free_will_db
SET log_min_duration_statement = 1000;  -- Log queries > 1s
```

### API Profiling

**Using FastAPI middleware**:
```python
import time

@app.middleware("http")
async def profile_middleware(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    if duration > 1.0:  # Log slow requests
        logger.warning(f"Slow request: {request.url.path} took {duration:.2f}s")
    return response
```

## Optimization Techniques

### 1. Database Optimization

**Query Optimization**:
```sql
-- Bad: Fetches all rows then limits
SELECT * FROM texts ORDER BY created_at DESC LIMIT 10;

-- Good: Uses index
CREATE INDEX idx_texts_created_at_desc ON texts(created_at DESC);
SELECT * FROM texts ORDER BY created_at DESC LIMIT 10;
```

**Connection Pooling**:
```python
# Adjust pool size based on load
DB_POOL_MIN_SIZE=5
DB_POOL_MAX_SIZE=20
```

**Prepared Statements**:
```python
# asyncpg uses prepared statements automatically
result = await conn.fetch("SELECT * FROM texts WHERE text_id = $1", text_id)
```

### 2. Caching Strategies

**API Response Caching**:
```python
from functools import lru_cache
from utils.kg_cache import cached

@cached(ttl=3600)
async def get_kg_stats():
    # Expensive operation
    return stats
```

**Edge Caching (Cloudflare)**:
```python
# Set cache headers
response.headers["Cache-Control"] = "public, max-age=3600"
```

**Memoization**:
```python
@lru_cache(maxsize=128)
def calculate_centrality(graph):
    return nx.degree_centrality(graph)
```

### 3. Async Optimization

**Concurrent Execution**:
```python
import asyncio

# Bad: Sequential
result1 = await service1.call()
result2 = await service2.call()

# Good: Concurrent
result1, result2 = await asyncio.gather(
    service1.call(),
    service2.call()
)
```

**Batch Operations**:
```python
# Bad: N+1 queries
for node_id in node_ids:
    node = await db.fetch_node(node_id)

# Good: Single query
nodes = await db.fetch_nodes(node_ids)
```

### 4. Memory Optimization

**Generator Expressions**:
```python
# Bad: Creates list in memory
nodes = [process(n) for n in all_nodes]

# Good: Generator
nodes = (process(n) for n in all_nodes)
```

**Streaming Responses**:
```python
from fastapi.responses import StreamingResponse

async def generate_data():
    for chunk in large_data:
        yield json.dumps(chunk) + "\n"

@app.get("/stream")
async def stream():
    return StreamingResponse(generate_data())
```

**Garbage Collection Tuning**:
```python
import gc

gc.set_threshold(700, 10, 10)  # Adjust thresholds
gc.collect()  # Force collection
```

### 5. GraphRAG Optimization

**Limit Graph Traversal Depth**:
```python
# Don't traverse entire graph
neighbors = get_neighbors(node_id, max_depth=2)
```

**Prune Irrelevant Nodes**:
```python
# Filter before traversal
relevant_nodes = [n for n in nodes if n.score > 0.7]
```

**Batch Embedding Queries**:
```python
# Embed multiple queries at once
embeddings = await qdrant.search_batch(queries)
```

## Hotspots & Fixes

### Hotspot 1: Full-Text Search

**Problem**: Slow search on large text corpus

**Solution**:
```sql
-- Add GIN index
CREATE INDEX idx_texts_fulltext_gin ON texts USING GIN (to_tsvector('english', content));

-- Use specific configuration
SELECT * FROM texts
WHERE to_tsvector('simple', content) @@ to_tsquery('simple', 'query');
```

### Hotspot 2: Graph Traversal

**Problem**: BFS on large graph is slow

**Solution**:
```python
# Use NetworkX with optimizations
import networkx as nx

# Cache graph structure
G_cached = nx.Graph(KG_data)

# Use faster algorithms
# Bad: nx.all_shortest_paths (exhaustive)
# Good: nx.shortest_path (single path)
path = nx.shortest_path(G, source, target)
```

### Hotspot 3: LLM API Calls

**Problem**: High latency waiting for LLM

**Solution**:
```python
# Use streaming
async for chunk in llm.generate_stream(prompt):
    yield chunk

# Cache responses
@cached(ttl=86400)
async def llm_call(prompt_hash):
    return await llm.generate(prompt)
```

### Hotspot 4: Vector Search

**Problem**: Qdrant queries are slow

**Solution**:
```python
# Use HNSW index (already configured)
# Optimize ef parameter
collection_info = await qdrant.get_collection("texts")

# Increase ef for better quality
await qdrant.search(
    collection_name="texts",
    query_vector=embedding,
    limit=10,
    search_params={"hnsw_ef": 128}  # Default is 100
)
```

## Benchmarking Results

### Before Optimization

```
Endpoint             p50      p95      p99
/api/kg/nodes        120ms    450ms    1.2s
/api/search/hybrid   850ms    2.1s     4.5s
/api/graphrag/query  3.2s     8.5s     15s
```

### After Optimization

```
Endpoint             p50      p95      p99    Improvement
/api/kg/nodes        45ms     180ms    320ms  2.6x faster
/api/search/hybrid   320ms    780ms    1.8s   2.7x faster
/api/graphrag/query  1.8s     3.5s     6.2s   1.8x faster
```

## Monitoring Performance

### Key Metrics to Track

1. **Latency**:
   - p50, p95, p99 response times
   - Histogram distribution

2. **Throughput**:
   - Requests per second
   - Concurrent users handled

3. **Error Rates**:
   - 5xx errors
   - Timeout errors

4. **Resource Usage**:
   - CPU utilization
   - Memory consumption
   - Database connections
   - Cache hit rate

### Prometheus Queries

```promql
# p95 latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Error rate
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])

# Cache hit ratio
cache_operations_total{result="hit"} / cache_operations_total
```

## Continuous Improvement

1. **Profile regularly**: Run profiling monthly
2. **Load test before deployment**: Run k6 tests
3. **Monitor production**: Track metrics in Grafana
4. **Iterate**: Optimize top 3 slowest endpoints
5. **Document**: Record optimizations and results

---

**Last Updated**: 2025-10-25
