# Quick Railway Deployment Guide

## Step 1: Deploy Backend to Railway (5 minutes)

1. Go to https://railway.app/dashboard
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository: `romain-girardi-eng/EleutherIA`
5. Railway will detect the `railway.toml` and `Dockerfile` automatically

## Step 2: Configure Environment Variables

After the project is created, click on your service and go to "Variables":

Add these environment variables:

```
GEMINI_API_KEY=AIzaSyBS6WTXFT3Z3xjhcE9_0McvpIRcHDsxD_M
POSTGRES_HOST=aws-1-eu-west-1.pooler.supabase.com
POSTGRES_PORT=6543
POSTGRES_DB=postgres
POSTGRES_USER=postgres.yngxlwbduhthkergfkif
POSTGRES_PASSWORD=Rororo@122112
POSTGRES_SSLMODE=require
QDRANT_HOST=7280fae4-4be6-4696-9b18-2ed0373dabb2.eu-west-2-0.aws.cloud.qdrant.io
QDRANT_HTTP_PORT=6333
QDRANT_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.kZ4-Gy0bbUP6j7CZPvn5bYi7Jy3Ug1GbEqjizwpartc
LOG_LEVEL=INFO
EMBEDDING_MODEL=gemini-embedding-001
EMBEDDING_DIMENSIONS=3072
PORT=8000
```

## Step 3: Get Your Railway URL

After deployment completes (~5 minutes):
1. Go to your service settings
2. Click on "Networking" → "Generate Domain"
3. Railway will give you a URL like: `https://your-project-name-production.up.railway.app`
4. Copy this URL

## Step 4: Update Frontend Configuration

Once you have your Railway URL, update `frontend/.env.production`:

```bash
VITE_API_URL=https://your-actual-railway-url.up.railway.app
```

(I've already created this file with a placeholder - just update the URL)

## Step 5: Redeploy Frontend

Commit and push:
```bash
git add .
git commit -m "feat: Add Railway backend deployment configuration"
git push origin main
```

This will trigger Cloudflare Pages to rebuild with the new API URL.

## Step 6: Test

Wait 2-3 minutes for Cloudflare Pages to rebuild, then visit:
https://free-will.app

The Database page should now show all 289 texts and 200+ bibliography references!

## Troubleshooting

- If Railway build fails, check the logs in Railway dashboard
- If frontend still shows 0 texts, verify the VITE_API_URL in Cloudflare Pages environment variables
- Test the backend directly: `https://your-railway-url.up.railway.app/api/health`
