# Render Deployment Guide - Memory Optimization

## Memory Issue Analysis

Render Free Tier has a **512MB memory limit**. The backend was exceeding this due to:

### Primary Memory Consumers:
1. **PostgreSQL Connection Pool**: 5-20 connections × ~10-30MB each = **50-600MB** ❌
2. **Python Dependencies**: ~80-150MB (FastAPI, asyncpg, numpy, pandas, networkx, igraph)
3. **Qdrant Client**: ~30-50MB
4. **Gemini API Client**: ~20-40MB
5. **Application Code**: ~20-30MB

**Total**: Easily exceeds 512MB with default settings!

---

## 🔧 Required Render Environment Variables

### Memory-Optimized Settings (CRITICAL for Free Tier)

```bash
# Database Pool - REDUCED for memory efficiency
DB_POOL_MIN_SIZE=1          # Was 5 (saves ~40-120MB)
DB_POOL_MAX_SIZE=3          # Was 20 (saves ~170-510MB)

# PostgreSQL Connection
POSTGRES_HOST=your-supabase-host.supabase.co
POSTGRES_PORT=5432
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password
POSTGRES_SSLMODE=require

# Qdrant Vector Database
QDRANT_HOST=your-qdrant-host.cloud.qdrant.io
QDRANT_HTTP_PORT=443
QDRANT_API_KEY=your-qdrant-api-key
EMBEDDING_DIMENSIONS=3072

# LLM Configuration (Gemini only - Ollama requires too much memory)
LLM_PREFERRED_PROVIDER=gemini
GEMINI_API_KEY=your-gemini-api-key

# Authentication
JWT_SECRET_KEY=your-random-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Optional: Auth bypass for testing (remove in production)
# BYPASS_AUTH=true
```

---

## 📊 Memory Budget Breakdown (Optimized)

With optimizations:

| Component | Memory Usage | Notes |
|-----------|-------------|-------|
| PostgreSQL Pool (1-3 conn) | **30-90MB** | ✅ Reduced from 50-600MB |
| Python Dependencies | **80-150MB** | Can't reduce without removing features |
| Qdrant Client | **30-50MB** | External service, minimal local usage |
| Gemini API Client | **20-40MB** | Cloud API, lightweight client |
| Application Code | **20-30MB** | FastAPI routes, business logic |
| OS & Python Runtime | **50-80MB** | Base overhead |
| **TOTAL** | **230-440MB** | ✅ Within 512MB limit |

---

## 🚀 Deployment Steps

### 1. Set Environment Variables in Render Dashboard

Go to your Render service → Environment → Add the variables above.

**CRITICAL**: Set these first:
- `DB_POOL_MIN_SIZE=1`
- `DB_POOL_MAX_SIZE=3`

### 2. Deploy the Updated Code

Push the optimized `services/db.py` to your Git repository:

```bash
git add backend/services/db.py
git commit -m "Optimize database connection pool for Render free tier memory limits"
git push origin main
```

Render will auto-deploy the changes.

### 3. Monitor Memory Usage

After deployment, check Render metrics:
- Dashboard → Your Service → Metrics
- Watch "Memory Usage" graph
- Should stay below 400MB with these optimizations

---

## 🔍 If Memory Issues Persist

### Additional Optimizations:

#### 1. **Reduce Python Package Size** (Advanced)

Remove heavy dependencies if not needed:

```bash
# In requirements.txt, comment out or remove if unused:
# python-igraph>=0.11        # ~40MB - for graph algorithms
# leidenalg>=0.10            # ~20MB - for community detection
# python-louvain>=0.16       # ~15MB - alternative community detection
# pandas>=2.0.0              # ~80MB - for data processing
```

**Trade-off**: Loses some KG analytics features.

#### 2. **Lazy Load Heavy Libraries**

Instead of importing at startup, import only when needed:

```python
# Before (loads immediately):
import pandas as pd
import networkx as nx

# After (loads on first use):
def some_function():
    import pandas as pd
    import networkx as nx
    # ... use libraries
```

#### 3. **Use Render Paid Tier**

Upgrade to **Starter** plan ($7/month) for 512MB → 2GB memory.

#### 4. **Split Services**

Separate memory-intensive operations:
- **Service 1**: Main API (FastAPI, PostgreSQL, auth)
- **Service 2**: GraphRAG/Analytics (heavy ML operations)

---

## 📈 Expected Performance After Optimization

### Memory Usage:
- **Idle**: ~250-300MB (50% of limit)
- **Under Load**: ~350-400MB (70-80% of limit)
- **Peak**: ~430-480MB (85-95% of limit)

### Response Times:
- **Cold Start**: 30-60 seconds (Render free tier limitation)
- **Warm Requests**: 100-500ms
- **GraphRAG Queries**: 5-15 seconds (depends on Gemini API)

---

## 🛡️ Monitoring & Alerts

### Set Up Render Alerts:

1. **Dashboard → Service Settings → Notifications**
2. Enable "Memory limit exceeded" alerts
3. Add your email

### Health Check Endpoint:

Monitor at: `https://eleutheria.onrender.com/api/health`

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "qdrant": "connected"
}
```

---

## 🆘 Troubleshooting

### Memory Still Exceeding Limit?

```bash
# Add to Render environment variables:
PYTHONUNBUFFERED=1          # Reduce Python buffer memory
DB_POOL_MIN_SIZE=1          # Use absolute minimum
DB_POOL_MAX_SIZE=2          # Stricter limit
```

### Connection Pool Exhausted?

If you see "connection pool exhausted" errors:
- Increase `DB_POOL_MAX_SIZE` to 5 (but watch memory!)
- Or upgrade to Render Starter tier

### Frequent Cold Starts?

Free tier sleeps after 15 min inactivity. Solutions:
- Use a cron job to ping the health endpoint every 10 minutes
- Upgrade to paid tier for 24/7 uptime

---

## 📝 Summary

✅ **Done**: Reduced DB pool from 5-20 to 1-3 connections
✅ **Impact**: Saves 200-500MB memory
✅ **Trade-off**: Slightly slower under high concurrency (acceptable for free tier)
✅ **Next**: Deploy and monitor memory usage in Render dashboard

---

*Last Updated: 2025-01-23*
*Optimized for: Render Free Tier (512MB RAM)*
