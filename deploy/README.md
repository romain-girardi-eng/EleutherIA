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

## Production — platform Compose + Cloudflare Pages

The serving API, worker and PostgreSQL 16 database run on the platform host
through its private Compose overlay and Cloudflare tunnel. The public frontend
is the Cloudflare Pages project `eleutheria`; the host-side frontend container
is not the canonical public surface.

Production is release-addressed. From the repository root, use an exact
40-character commit only:

```bash
make deploy RC_SHA=<verified-release-sha>
```

`make deploy` is the complete ordered cutover: backup, image build, migrations,
staging dry-run, atomic data swap, API/worker recreation and public
expected-release probes. Do **not** follow it with `make deploy-data`; a second
successful swap would replace the retained `__old` rollback generation with
the generation just deployed.

The narrower targets are standalone maintenance alternatives on a host already
checked out at the exact same SHA:

```bash
make deploy-data-dry-run RC_SHA=<verified-release-sha>  # verify only, no swap
make deploy-data RC_SHA=<verified-release-sha>          # retry data swap/recreate only
```

Deploy and verify backend/data first from a release branch or detached commit.
Only after the public API reports that same release should the commit be pushed
to `main`; the Git-connected Cloudflare Pages project then publishes the public
frontend automatically. This ordering prevents a new Atlas from calling an old
workspace API.

The current atomic data procedure and rollback contract live in
[`docs/development/staged-deploy.md`](../docs/development/staged-deploy.md).
`deploy/production/docker-compose.yml` and its README remain a legacy Supabase
bootstrap/reference configuration; they are not the current serving topology.

## Environment Variables

- **Local:** See `.env.example` in repo root
- **Production (Docker):** See `deploy/production/.env.example`

## Applying Application Migrations

Application migrations are not run automatically at API startup. For an
existing self-hosted PostgreSQL database or Supabase project, apply each new
idempotent migration once with a direct or session-pooler maintenance DSN (not
the transaction pooler). For answer feedback:

```bash
export SUPABASE_DATABASE_URL='postgresql://...'
uv run --with asyncpg python database/scripts/apply_schema.py \
  --migration database/migrations/20260817_01_answer_feedback.sql
```

For a local Docker database, set `DATABASE_URL` to the exposed PostgreSQL
connection and run the same command. The mounted `/docker-entrypoint-initdb.d`
schema only runs when a volume is first created and does not upgrade an
existing volume.
