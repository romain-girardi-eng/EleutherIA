# Deployment Guide - Ancient Free Will Database

## Overview

- **Frontend**: Cloudflare Pages (free-will.app) ✅ Already deployed
- **Backend**: Render (Free tier) or Railway ($5/month)
- **PostgreSQL**: Supabase (Free tier) or Railway PostgreSQL
- **Qdrant**: Qdrant Cloud (Free tier)

## 🆓 FREE Deployment Stack (Recommended)

This guide uses **100% free services**:
- **Render** (free web service with cold starts)
- **Supabase** (500MB PostgreSQL free tier)
- **Qdrant Cloud** (1GB vector storage free tier)

**Trade-offs**: Render free tier has cold starts (15min inactivity → 30sec restart)

---

## Step 1: Set up Supabase PostgreSQL (FREE)

1. Go to https://supabase.com and sign up
2. Click "New Project"
3. Fill in:
   - **Project name**: `ancient-free-will-db`
   - **Database password**: (generate a strong password)
   - **Region**: Choose closest to you
4. Wait for project to be created (~2 minutes)
5. Go to **Project Settings** → **Database**
6. Copy connection details:
   - **Host**: `db.[your-project-ref].supabase.co`
   - **Port**: `5432`
   - **Database**: `postgres`
   - **User**: `postgres`
   - **Password**: (the one you set)

7. **Initialize the database locally**:

```bash
# Update .env with Supabase credentials
POSTGRES_HOST=db.[your-project-ref].supabase.co
POSTGRES_PORT=5432
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password

# Run setup script
python3 setup_database.py
```

This will create the schema and load all 42 ancient texts.

---

## Step 2: Set up Qdrant Cloud (FREE)

1. Go to https://cloud.qdrant.io
2. Sign up for free tier (1GB storage)
3. Click "Create Cluster"
   - **Cluster name**: `ancient-free-will`
   - **Region**: Choose closest to you
   - **Tier**: Free (1GB)
4. Wait for cluster to be created (~1 minute)
5. Click on your cluster → **API Keys** → **Create API Key**
6. Copy:
   - **Cluster URL**: `https://[your-cluster-id].qdrant.io`
   - **API Key**: (save this securely)

7. **Create the embeddings collection**:

The collection will be created automatically by the API when you run the embedding setup script.

8. **Populate embeddings**:

```bash
# Update .env with Qdrant credentials
QDRANT_HOST=[your-cluster-id].qdrant.io
QDRANT_HTTP_PORT=6333
QDRANT_API_KEY=your-api-key

# Generate embeddings and upload to Qdrant
python3 setup_complete_embeddings.py
```

This will create embeddings for all 42 texts using Gemini and upload them to Qdrant Cloud.

---

## Step 3: Deploy Backend to Render (FREE)

1. Go to https://render.com and sign up
2. Click "New +" → "Web Service"
3. Connect your GitHub repository: `Ancient Free Will Database`
4. Configure:
   - **Name**: `ancient-free-will-api`
   - **Runtime**: Docker
   - **Branch**: `main`
   - **Dockerfile Path**: `backend/Dockerfile`
   - **Docker Context**: `backend`

5. **Set Environment Variables** (click "Advanced" → "Add Environment Variable"):

```
GEMINI_API_KEY=AIzaSyBS6WTXFT3Z3xjhcE9_0McvpIRcHDsxD_M
POSTGRES_HOST=db.[your-supabase-ref].supabase.co
POSTGRES_PORT=5432
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=[your-supabase-password]
QDRANT_HOST=[your-cluster-id].qdrant.io
QDRANT_HTTP_PORT=6333
QDRANT_API_KEY=[your-qdrant-api-key]
LOG_LEVEL=INFO
EMBEDDING_MODEL=gemini-embedding-001
EMBEDDING_DIMENSIONS=3072
```

6. Click "Create Web Service"
7. Wait for build to complete (~5-10 minutes)
8. Copy your public URL: `https://ancient-free-will-api.onrender.com`

**Note**: Render free tier spins down after 15 minutes of inactivity. First request after spin-down takes ~30 seconds.

---

## Step 4: Update Frontend on Cloudflare Pages

1. Go to https://dash.cloudflare.com
2. Navigate to **Pages** → your site (`free-will`)
3. Go to **Settings** → **Environment Variables**
4. Add production environment variable:
   - **Variable name**: `VITE_API_URL`
   - **Value**: `https://ancient-free-will-api.onrender.com`
   - **Environment**: Production
5. Click "Save"
6. Go to **Deployments** → **Redeploy**

Your frontend at https://free-will.app will now connect to the production backend!

---

## Step 5: Test Production Deployment

1. Visit https://free-will.app
2. Wait ~30 seconds if the backend is cold (first request)
3. Try hybrid search: "freedom and virtue"
4. Check that results appear from both full-text and semantic search
5. Try different search modes (semantic only, text only, knowledge graph)

---

## 💰 Costs Summary

### FREE Stack (Recommended)
- **Cloudflare Pages**: FREE
- **Render Web Service**: FREE (with cold starts)
- **Supabase PostgreSQL**: FREE (500MB, sufficient for 42 texts)
- **Qdrant Cloud**: FREE (1GB, sufficient for embeddings)

**Total**: $0/month

### Alternative: Railway Stack
- **Cloudflare Pages**: FREE
- **Railway**: ~$5/month (PostgreSQL + Backend)
- **Qdrant Cloud**: FREE

**Total**: ~$5/month

---

## 🔧 Troubleshooting

### Backend returns 502/503
- **Cause**: Cold start on Render free tier
- **Solution**: Wait 30 seconds and retry

### Search returns no semantic results
- **Check**: Qdrant collection has embeddings
- **Solution**: Run `python3 setup_complete_embeddings.py` again

### Database connection fails
- **Check**: Supabase credentials in Render environment variables
- **Solution**: Verify host, port, user, password are correct

### Frontend shows CORS errors
- **Check**: `VITE_API_URL` in Cloudflare Pages environment variables
- **Solution**: Ensure it points to correct Render URL

---

## 📊 Monitoring

### Render Dashboard
- Check logs: https://dashboard.render.com → your service → Logs
- View metrics: CPU, memory, request count
- Monitor cold starts

### Supabase Dashboard
- Database size: Project Settings → Database → Storage
- Active connections: Database → Connection pooling

### Qdrant Cloud Dashboard
- Vector count: Cluster → Collections → text_embeddings
- Storage usage: Cluster → Overview

---

## 🚀 Alternative: Keep Local Backend

If you prefer to keep costs at $0 without cold starts:

1. Run backend locally: `cd backend && uvicorn api.main:app --host 0.0.0.0 --port 8000`
2. Use ngrok to expose it: `ngrok http 8000`
3. Update Cloudflare Pages `VITE_API_URL` to ngrok URL

**Trade-off**: Requires your computer to be on 24/7.

---

## 🔄 CI/CD

The deployment is configured for automatic updates:

- **render.yaml**: Configured for auto-deploy on `git push`
- **Push to GitHub** → Render automatically rebuilds and deploys
- **No manual deployment** needed after initial setup

To deploy updates:
```bash
git add .
git commit -m "feat: your changes"
git push origin main
```

Render will automatically detect the push and redeploy within ~5 minutes.
