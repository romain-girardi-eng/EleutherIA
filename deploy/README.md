# EleutherIA Deployment

Three deployment options: **local** (self-contained Docker), **production Docker** (managed services), and **Cloudflare Workers** (edge, current free-will.app).

## Local — Self-Contained

Everything runs in Docker: PostgreSQL, Qdrant, backend, and frontend. Zero external dependencies.

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
| Qdrant     | 6333 | http://localhost:6333/dashboard   |

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

## Production — Supabase + Qdrant Cloud

Only backend and frontend run as containers. PostgreSQL and Qdrant are external managed services.

See [`production/README.md`](production/README.md) for full setup instructions.

```bash
cd deploy/production
cp .env.example .env
# Fill in Supabase URL, Qdrant host, API keys

make prod
# Or: docker compose -f deploy/production/docker-compose.yml up -d --build
```

## Production (Cloudflare Workers) — Edge Backend

The current [free-will.app](https://free-will.app) backend runs on Cloudflare Workers using Hono (TypeScript). No containers needed.

See [`cloudflare/README.md`](cloudflare/README.md) for full setup instructions.

```bash
cd deploy/cloudflare
npm install
npx wrangler login
# Set secrets (see README)
npx wrangler deploy
```

## Environment Variables

- **Local:** See `.env.example` in repo root
- **Production (Docker):** See `deploy/production/.env.example`
- **Cloudflare Workers:** Secrets via `wrangler secret put`, vars in `wrangler.toml`
