# Cloudflare Workers Deployment

Production edge backend for [free-will.app](https://free-will.app) running on Cloudflare Workers. This is the backend that currently serves the production site.

Built with [Hono](https://hono.dev) (TypeScript), connecting to Supabase (PostgreSQL) and Qdrant Cloud for data, with Gemini for LLM inference.

## Prerequisites

- [Node.js](https://nodejs.org) 18+
- A [Cloudflare](https://dash.cloudflare.com) account
- A [Supabase](https://supabase.com) project (PostgreSQL)
- A [Qdrant Cloud](https://cloud.qdrant.io) cluster
- A Gemini API key

## Setup

### 1. Install dependencies

```bash
cd deploy/cloudflare
npm install
```

### 2. Authenticate with Cloudflare

```bash
npx wrangler login
npx wrangler whoami   # Verify
```

### 3. Set secrets

Each secret must be set individually via the CLI:

```bash
npx wrangler secret put SUPABASE_URL
npx wrangler secret put SUPABASE_KEY
npx wrangler secret put QDRANT_HOST
npx wrangler secret put QDRANT_API_KEY
npx wrangler secret put GEMINI_API_KEY
npx wrangler secret put JWT_SECRET_KEY
npx wrangler secret put SEMATIVERSE_ACCESS_KEY
```

You'll be prompted for each value interactively.

### 4. Deploy

```bash
npx wrangler deploy
```

## Local Development

```bash
npx wrangler dev
# Starts local dev server on http://localhost:8787
```

The dev server uses the `[vars]` section in `wrangler.toml` for non-secret environment variables. Secrets must be provided via a `.dev.vars` file:

```bash
# deploy/cloudflare/.dev.vars (not committed)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-key
QDRANT_HOST=your-cluster.qdrant.io
QDRANT_API_KEY=your-key
GEMINI_API_KEY=your-key
JWT_SECRET_KEY=dev-secret
SEMATIVERSE_ACCESS_KEY=dev-key
```

## Architecture

```
Internet → Cloudflare Edge → Worker (Hono) → Supabase + Qdrant Cloud + Gemini
                                ↓
                          KV (TEXT_CACHE) for response caching
```

- **Routes** mirror the FastAPI endpoints, extended with Cloudflare-specific features
- **Services** handle database queries, vector search, LLM calls, and RAG pipelines
- **KV namespace** (`TEXT_CACHE`) caches expensive text/passage lookups

## Useful Commands

```bash
# Verify wrangler can build the Worker
npx wrangler deploy --dry-run --outdir=.wrangler/tmp-build

# View live logs
npx wrangler tail

# Deploy
npx wrangler deploy
```

## Configuration

All configuration is in `wrangler.toml`:

- `name` — Worker name on Cloudflare
- `route` — URL pattern (currently `free-will.app/api/*`)
- `[vars]` — Non-secret environment variables
- `[[kv_namespaces]]` — KV bindings for caching
