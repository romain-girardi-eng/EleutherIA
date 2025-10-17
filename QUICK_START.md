# 🚀 Quick Start Guide - Ancient Free Will Database Interface

Get the backend running in under 5 minutes!

---

## Prerequisites Check

```bash
# Check Python version (need 3.11+)
python3 --version

# Check if PostgreSQL is running (port 5433)
psql -h localhost -p 5433 -U free_will_user -d ancient_free_will_db -c "SELECT version();"

# Check if Qdrant is running (port 6333)
curl http://localhost:6333/collections
```

---

## Step-by-Step Setup

### 1. Start Required Services

```bash
# If PostgreSQL not running:
cd "Ancient Free Will Database"
docker-compose up -d postgres

# If Qdrant not running:
docker run -p 6333:6333 -d qdrant/qdrant
```

### 2. Setup Qdrant (One-Time)

```bash
# Generate embeddings and populate Qdrant
python3 setup_qdrant_vector_db.py
```

This will:
- Load KG embeddings
- Create 3 collections (kg_nodes, kg_edges, text_embeddings)
- Upload all vectors to Qdrant
- Takes ~5 minutes

### 3. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your Gemini API key
nano .env  # or use your preferred editor

# Required: Set GEMINI_API_KEY
# Optional: Change SEMATIVERSE_ACCESS_KEY
```

### 4. Install Backend Dependencies

```bash
# Create virtual environment
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 5. Start Backend Server

```bash
# From backend directory
python3 -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     🚀 Starting Ancient Free Will Database API
INFO:     ✅ Connected to PostgreSQL
INFO:     ✅ Connected to Qdrant
INFO:     ✅ API ready to serve requests
```

### 6. Test the API

Open your browser to:
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/api/health

Or use curl:
```bash
# Health check
curl http://localhost:8000/api/health

# Get KG statistics
curl http://localhost:8000/api/kg/stats

# Test hybrid search
curl -X POST http://localhost:8000/api/search/hybrid \
  -H "Content-Type: application/json" \
  -d '{"query": "free will", "limit": 5}'
```

---

## Quick Test Examples

### 1. Search for "ἐφ ἡμῖν" (eph' hêmin - in our power)

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

### 2. Get Cytoscape.js Data

```bash
curl http://localhost:8000/api/kg/viz/cytoscape > cytoscape_data.json
```

### 3. List Ancient Texts

```bash
# Get all Greek texts
curl "http://localhost:8000/api/texts/list?language=grc"

# Get texts by Aristotle
curl "http://localhost:8000/api/texts/list?author=Aristotle"
```

### 4. Search Knowledge Graph

```bash
curl -X POST http://localhost:8000/api/search/kg \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Stoic philosophy determinism",
    "limit": 10
  }'
```

### 5. Check Semativerse Permission 🔒

```bash
curl -X POST http://localhost:8000/api/auth/semativerse/check \
  -H "Content-Type: application/json" \
  -d '{
    "access_key": "demo-key-change-in-production"
  }'
```

---

## Troubleshooting

### Problem: "Database not connected"

**Solution:**
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# If not running, start it
docker-compose up -d postgres

# Verify connection
psql -h localhost -p 5433 -U free_will_user -d ancient_free_will_db -c "SELECT COUNT(*) FROM free_will.texts;"
```

### Problem: "Qdrant not connected"

**Solution:**
```bash
# Check if Qdrant is running
curl http://localhost:6333/collections

# If not running, start it
docker run -p 6333:6333 -d qdrant/qdrant

# Verify Qdrant has data
curl http://localhost:6333/collections/kg_nodes
```

### Problem: "Gemini API error"

**Solution:**
```bash
# Verify your API key is set
echo $GEMINI_API_KEY

# If empty, set it
export GEMINI_API_KEY="your_actual_key_here"

# Test Gemini API
python3 -c "
import google.generativeai as genai
import os
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
result = genai.embed_content(
    model='models/text-embedding-004',
    content='test',
    task_type='retrieval_query'
)
print('Gemini API working!')
"
```

### Problem: Port already in use

**Solution:**
```bash
# Change port in command
python3 -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8001

# Or kill process using port 8000
lsof -ti:8000 | xargs kill -9
```

---

## Next Steps

### For Development:

1. **Explore API Documentation:**
   - Open http://localhost:8000/docs
   - Try interactive API endpoints

2. **Enhance GraphRAG:**
   - Implement full Microsoft GraphRAG integration
   - Add streaming responses
   - Build reasoning path tracking

3. **Build Frontend:**
   - Set up React + TypeScript project
   - Integrate Cytoscape.js
   - Build search interface

### For Production:

1. **Security:**
   - Change SEMATIVERSE_ACCESS_KEY to secure random value
   - Set up proper authentication (JWT tokens)
   - Configure CORS for production domains

2. **Performance:**
   - Enable caching (Redis)
   - Set up connection pooling
   - Optimize database queries

3. **Deployment:**
   - Create Docker images
   - Set up docker-compose for all services
   - Configure reverse proxy (Nginx)
   - Enable HTTPS (Let's Encrypt)

---

## API Endpoints Summary

### Knowledge Graph
- `GET /api/kg/nodes` - Get all nodes
- `GET /api/kg/edges` - Get all edges
- `GET /api/kg/node/{id}` - Node details
- `GET /api/kg/viz/cytoscape` - Cytoscape data
- `GET /api/kg/stats` - Statistics

### Search
- `POST /api/search/hybrid` - Hybrid search (RRF)
- `POST /api/search/fulltext` - Full-text only
- `POST /api/search/lemmatic` - Lemmatic only
- `POST /api/search/semantic` - Semantic only
- `POST /api/search/kg` - KG semantic search

### Texts
- `GET /api/texts/list` - List all texts
- `GET /api/texts/{id}` - Get text content
- `GET /api/texts/{id}/structure` - Text structure
- `GET /api/texts/stats/overview` - Statistics

### GraphRAG
- `POST /api/graphrag/query` - Question answering
- `GET /api/graphrag/status` - Service status

### Auth
- `POST /api/auth/semativerse/check` - Check permission 🔒
- `GET /api/auth/semativerse/status` - Status

---

## Performance Expectations

- **Hybrid Search:** <200ms (combined 3 modes)
- **Semantic Search:** <100ms (Qdrant HNSW)
- **Full-text Search:** <50ms (PostgreSQL)
- **KG Node Retrieval:** <10ms
- **API Response Time:** <500ms (p95)

---

## Resources

- **Full Documentation:** `INTERFACE_ARCHITECTURE_README.md`
- **API Docs:** http://localhost:8000/docs
- **Redoc:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/api/health

---

**You're all set! 🎉**

The backend is now running with:
- ✅ FastAPI REST API
- ✅ Hybrid Search (Full-text + Lemmatic + Semantic)
- ✅ Qdrant Vector Search
- ✅ PostgreSQL 289 Ancient Texts
- ✅ Knowledge Graph (465 nodes, 740 edges)
- ✅ Semativerse Auth 🔒

Next: Build the React frontend with Cytoscape.js and Semativerse visualization!
