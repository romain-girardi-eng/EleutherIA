# Railway Deployment — EleutherIA Backend (retired)

Railway is no longer the production host. Production now runs as
`eleutheria-api` / `eleutheria-worker` in the platform's Docker Compose, exposed
through the Cloudflare tunnel at `https://free-will.app`.

This document is retained only as historical rollback context.

## Architecture

```
                    free-will.app (Cloudflare DNS)
                         |
            +------------+------------+
            |                         |
    Cloudflare Pages            Railway (EU-West)
    (frontend React)         (Python FastAPI)
     Static assets              |        |
                          Supabase
                         (Postgres)
```

This was the former Railway topology. It is not the production deployment path anymore; use the the platform compose fragment and Cloudflare tunnel instead.

## Quick Start

### 1. Install Railway CLI

```bash
npm install -g @railway/cli
railway login
```

### 2. Create project and link

```bash
cd /path/to/EleutherIA
railway init          # Create a new Railway project
railway link          # Link this repo
```

### 3. Set environment variables

```bash
# Database (Supabase)
railway variables set DATABASE_URL="postgresql://postgres.xxx:password@aws-0-eu-west-1.pooler.supabase.com:6543/postgres?sslmode=require"

# LLM providers
railway variables set GEMINI_API_KEY="your-key"
railway variables set OPENROUTER_API_KEY="your-key"
railway variables set MOONSHOT_API_KEY="your-key"

# Security
railway variables set JWT_SECRET_KEY="your-production-secret"
railway variables set ALLOWED_ORIGINS="https://free-will.app"

# Config
railway variables set LLM_PREFERRED_PROVIDER="gemini"
railway variables set OPENROUTER_HTTP_REFERER="https://free-will.app"
railway variables set OPENROUTER_APP_NAME="EleutherIA"
railway variables set RETRIEVAL_MODE="auto"
```

### 4. Deploy

```bash
railway up            # Deploy from local (for testing)
# Or push to GitHub — Railway auto-deploys on push
```

### 5. Get your URL

```bash
railway domain        # Generate a Railway public URL
# e.g. eleutheria-backend-production.up.railway.app
```

### 6. Update frontend

Set the `VITE_API_URL` environment variable in Cloudflare Pages:
```
VITE_API_URL=https://eleutheria-backend-production.up.railway.app
```

Or if using a custom domain, point `free-will.app` to Railway and set:
```
VITE_API_URL=https://free-will.app
```

## Custom Domain (optional)

```bash
railway domain add free-will.app
```

Then add a CNAME record in Cloudflare DNS:
```
free-will.app → eleutheria-backend-production.up.railway.app
```

This keeps `free-will.app` for the frontend and `free-will.app` for the backend.

## Configuration

### railway.json

The `railway.json` at the repo root configures:
- **Build**: uses `backend/Dockerfile` (multi-stage, Python 3.11)
- **Deploy**: uvicorn with 2 workers, uvloop, health check on `/api/health`
- **Restart**: auto-restart on failure (max 3 retries)

### Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | yes | Supabase Postgres connection string (pooler port 6543) |
| `GEMINI_API_KEY` | yes | Google AI API key (primary LLM provider) |
| `OPENROUTER_API_KEY` | yes | OpenRouter API key (multi-model routing) |
| `MOONSHOT_API_KEY` | no | Kimi/Moonshot API key (thinking mode) |
| `JWT_SECRET_KEY` | yes | JWT signing secret |
| `ALLOWED_ORIGINS` | yes | Comma-separated allowed CORS origins |
| `LLM_PREFERRED_PROVIDER` | no | Default: `gemini` |
| `RETRIEVAL_MODE` | no | Default: `auto`. Set to `sql` to force vectorless mode |

## Monitoring

```bash
railway logs          # Tail logs
railway status        # Service status
```

## Cost

- Hobby plan: $5/month with $5 compute credits included
- Typical usage (~100 req/day, 2 workers): well within hobby credits
- No hidden IPv4 or volume costs

## Migration from Cloudflare Workers

The Cloudflare Workers TS edge pipeline was retired on 2026-05-14 (see `deploy/cloudflare/README.md`). Historic migration steps (kept for reference):

1. Deploy backend on Railway (this guide)
2. Update `VITE_API_URL` in Cloudflare Pages env vars
3. Verify frontend connects to Railway backend
4. Update DNS if using custom domain
