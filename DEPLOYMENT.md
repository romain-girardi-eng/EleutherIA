# Deployment Guide - Ancient Free Will Database

## Overview

- **Frontend**: Cloudflare Pages (free-will.app) ✅ Already deployed
- **Backend**: Railway (FastAPI)
- **PostgreSQL**: Railway PostgreSQL
- **Qdrant**: Qdrant Cloud (free tier)

## Step 1: Deploy PostgreSQL on Railway

1. Go to https://railway.app and sign up/login
2. Click "New Project" → "Provision PostgreSQL"
3. Copy the connection details:
   - `POSTGRES_HOST`
   - `POSTGRES_PORT`
   - `POSTGRES_DB`
   - `POSTGRES_USER`
   - `POSTGRES_PASSWORD`

## Step 2: Set up Qdrant Cloud

1. Go to https://cloud.qdrant.io
2. Sign up for free tier (1GB storage)
3. Create a cluster
4. Create a collection named `text_embeddings`:
   - Vector size: 3072
   - Distance: Cosine
5. Get API key and cluster URL

## Step 3: Deploy Backend to Railway

1. In Railway, click "New" → "GitHub Repo"
2. Connect your Ancient Free Will Database repository
3. Railway will auto-detect the Dockerfile
4. Set environment variables in Railway:

```
GEMINI_API_KEY=AIzaSyBS6WTXFT3Z3xjhcE9_0McvpIRcHDsxD_M
POSTGRES_HOST=<from Railway PostgreSQL>
POSTGRES_PORT=<from Railway PostgreSQL>
POSTGRES_DB=<from Railway PostgreSQL>
POSTGRES_USER=<from Railway PostgreSQL>
POSTGRES_PASSWORD=<from Railway PostgreSQL>
QDRANT_HOST=<your-cluster>.qdrant.io
QDRANT_HTTP_PORT=6333
QDRANT_API_KEY=<from Qdrant Cloud>
LOG_LEVEL=INFO
EMBEDDING_MODEL=gemini-embedding-001
EMBEDDING_DIMENSIONS=3072
```

5. Deploy and wait for build to complete
6. Copy the public URL (e.g., `https://your-app.railway.app`)

## Step 4: Initialize Database

After deployment, run these scripts to set up the database:

```bash
# Run setup_database.py to create schema and load texts
# This needs to be done from your local machine pointing to Railway PostgreSQL

python3 setup_database.py
```

Then populate Qdrant embeddings (you'll need to create this script or use the API).

## Step 5: Update Frontend

Update the frontend to use the production backend URL:

1. In Cloudflare Pages settings, add environment variable:
   ```
   VITE_API_URL=https://your-app.railway.app
   ```

2. Update frontend API calls to use `import.meta.env.VITE_API_URL`

## Step 6: Test

1. Visit https://free-will.app
2. Try the hybrid search
3. Check all features are working

## Costs (Estimated)

- **Cloudflare Pages**: FREE
- **Railway**: ~$5/month (500MB RAM should be enough)
- **PostgreSQL on Railway**: Included in Railway plan
- **Qdrant Cloud**: FREE (1GB tier)

**Total**: ~$5/month

## Alternative: Keep Local Backend

If you prefer to keep costs at $0, you can:
1. Run backend locally
2. Use ngrok to expose it: `ngrok http 8000`
3. Update frontend to use ngrok URL

This works but requires your computer to be on.
