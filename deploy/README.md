# EleutherIA Deployment

Two deployment options: **local** (self-contained Docker) and **production Docker** (managed services). The legacy Cloudflare Workers edge pipeline was retired on 2026-05-14 — see [`cloudflare/README.md`](cloudflare/README.md).

## Local — Self-Contained

Everything runs in Docker: PostgreSQL, backend, and frontend. Zero external dependencies for retrieval; the current GraphRAG path is vectorless.

```bash
# From repo root
cp .env.example .env
# Add at least one LLM API key to .env

make run
# Or: docker compose up -d --build
```

| Service    | Port | URL                              |
|------------|------|----------------------------------|
| Frontend   | 80   | http://localhost                  |
| Backend    | 8000 | http://localhost:8000/docs        |
| PostgreSQL | 5432 | localhost:5432                    |

Optional profiles:

```bash
docker compose --profile admin up -d       # + PgAdmin on :8080
docker compose --profile monitoring up -d  # + Prometheus + Grafana
docker compose --profile full up -d        # Everything
```

```bash
make stop         # Stop services
make local-clean  # Stop + delete volumes
make logs         # Tail logs
```

## Production — Supabase

Only backend and frontend run as containers. PostgreSQL is provided by Supabase; GraphRAG retrieval is SQL/tree/lemma based.

See [`production/README.md`](production/README.md) for full setup instructions.

```bash
cd deploy/production
cp .env.example .env
# Fill in Supabase URL and LLM API keys
# Rebuild Supabase first from repo root if needed:
# uv run --with asyncpg python database/scripts/bootstrap_supabase.py --replace-data

make prod
# Or: docker compose -f deploy/production/docker-compose.yml up -d --build
```

## Environment Variables

- **Local:** See `.env.example` in repo root
- **Production (Docker):** See `deploy/production/.env.example`
