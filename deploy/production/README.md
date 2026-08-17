# Production Deployment

Production setup for [free-will.app](https://free-will.app). The canonical production host is now the platform Docker Compose behind the platform's Cloudflare tunnel; the API worker and public SPARQL sidecar run there. Supabase remains the PostgreSQL store.

## Prerequisites

- Docker and Docker Compose
- A [Supabase](https://supabase.com) project
- At least one LLM API key (Gemini, Kimi, or OpenRouter)

## Setup

### 1. Supabase Database

1. Create a project at [supabase.com/dashboard](https://supabase.com/dashboard)
2. Copy a direct or session-pooler PostgreSQL URL for maintenance imports. Do
   not commit this URL or put it in Cloudflare secrets; it is an admin database
   credential for local/CI bootstrap only.
3. Pour une base **neuve et vide seulement**, initialiser le schéma et les
   données de départ depuis la racine du dépôt :

```bash
export SUPABASE_DATABASE_URL='postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT_REF.supabase.co:5432/postgres?sslmode=require'

uv run --with asyncpg \
  python database/scripts/bootstrap_supabase.py \
  --replace-data
```

This applies:

- `database/schema/schema.sql`
- `database/schema/work_tree_indices.sql`
- `database/schema/supabase_public_api.sql`
- `database/schema/supabase_functions.sql`
- `database/migrations/20260514_01_supabase_rebuild_support.sql`

It then imports the recovered `data/kg` snapshot into:

- `free_will.kg_nodes`
- `free_will.kg_edges`
- derived `free_will.ancient_works`
- derived `free_will.passages`
- derived `free_will.passage_citations`

Expected snapshot import volume is currently about `17,757` KG nodes, `43,063` KG edges, `166` works, `16,872` passages, and `19,124` passage citations.

Ne jamais réutiliser `--replace-data` pour une base déjà servie. Les mises à
jour courantes passent par le déploiement staging transactionnel décrit dans
[`docs/development/staged-deploy.md`](../../docs/development/staged-deploy.md).

4. Copy the **Transaction** connection string from **Settings > Database > Connection string** (port 6543, pgbouncer mode) into `DATABASE_URL` for the running backend
5. Set `DATABASE_REQUIRED=true` in production so startup fails if the restored Supabase database is unavailable

### Supabase Security Notes

- Keep `SUPABASE_DATABASE_URL` out of Git, Cloudflare, and frontend builds.
- Prefer the Supabase anon key for Cloudflare `SUPABASE_KEY`; the public read
  paths are protected with explicit `SELECT` grants and RLS policies.
- Do not use `service_role` unless a server-only admin route needs RLS bypass.
- Rotate the old Supabase password/key material if it appeared in source,
  terminal output, logs, screenshots, or pasted chat context.
- In Supabase API settings, expose only `public` and `free_will` if both are
  required by the Worker. Do not expose private schemas.
- If your Supabase plan supports it, restrict direct Postgres access to trusted
  IP ranges after the bootstrap is complete.

### 2. Configure & Deploy

Before rebuilding the application containers, apply the answer-feedback
migration once with the maintenance connection:

```bash
export SUPABASE_DATABASE_URL='postgresql://...'
uv run --with asyncpg python database/scripts/apply_schema.py \
  --migration database/migrations/20260817_01_answer_feedback.sql
```

The API does not run application migrations at startup. The SQL is idempotent,
so reapplying it is safe; use a direct or session-pooler DSN rather than the
runtime transaction-pooler URL.

```bash
cd deploy/production
cp .env.example .env
# Edit .env with your Supabase URL and LLM API keys

docker compose up -d --build
```

### 4. Verify

```bash
curl http://localhost:8000/api/health
# Should include: "database":"connected", "kg_source":"database"
```

Optional DB-level verification:

```bash
uv run --with asyncpg python - <<'PY'
import asyncio, os, asyncpg

async def main():
    conn = await asyncpg.connect(os.environ["SUPABASE_DATABASE_URL"], statement_cache_size=0)
    row = await conn.fetchrow("""
        SELECT
            (SELECT COUNT(*) FROM free_will.kg_nodes) AS kg_nodes,
            (SELECT COUNT(*) FROM free_will.kg_edges) AS kg_edges,
            (SELECT COUNT(*) FROM free_will.passages) AS passages,
            public.get_kg_stats() AS kg_stats
    """)
    print(dict(row))
    await conn.close()

asyncio.run(main())
PY
```

## Architecture

```
Internet → Nginx (frontend :80) → FastAPI (backend :8000) → Supabase
```

- **Backend** connects to Supabase via `DATABASE_URL` (asyncpg DSN with SSL)
- **Frontend** serves the React SPA and proxies `/api` to the backend
- No local PostgreSQL container needed

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
