# Production Deployment

Production setup for [free-will.app](https://free-will.app) using Supabase (PostgreSQL) and Qdrant Cloud as managed services. Only the backend and frontend run as Docker containers.

## Prerequisites

- Docker and Docker Compose
- A [Supabase](https://supabase.com) project
- A [Qdrant Cloud](https://cloud.qdrant.io) cluster
- At least one LLM API key (Gemini, Kimi, or OpenRouter)

## Setup

### 1. Supabase Database

1. Create a project at [supabase.com/dashboard](https://supabase.com/dashboard)
2. Open **SQL Editor** and run `database/schema/schema.sql` from this repo
3. Optionally run `database/schema/supabase_functions.sql` for optimized RPC search functions
4. Copy the **Transaction** connection string from **Settings > Database > Connection string** (port 6543, pgbouncer mode)

### 2. Qdrant Cloud

1. Create a cluster at [cloud.qdrant.io](https://cloud.qdrant.io)
2. Note the cluster hostname and API key

### 3. Configure & Deploy

```bash
cd deploy/production
cp .env.example .env
# Edit .env with your Supabase URL, Qdrant host, API keys

docker compose up -d --build
```

### 4. Verify

```bash
curl http://localhost:8000/api/health
# Should return: {"status":"healthy","database":"connected",...}
```

## Architecture

```
Internet → Nginx (frontend :80) → FastAPI (backend :8000) → Supabase + Qdrant Cloud
```

- **Backend** connects to Supabase via `DATABASE_URL` (asyncpg DSN with SSL)
- **Frontend** serves the React SPA and proxies `/api` to the backend
- No local PostgreSQL or Qdrant containers needed

## Updating

```bash
cd deploy/production
docker compose pull    # If using pre-built images
docker compose up -d --build  # If building from source
```

## Useful Commands

```bash
# View logs
docker compose logs -f backend

# Restart backend only
docker compose restart backend

# Stop everything
docker compose down
```
