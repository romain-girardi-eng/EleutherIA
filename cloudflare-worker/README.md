# Cloudflare Worker - Static KG Data Caching

This Cloudflare Worker caches static knowledge graph endpoints at the edge for lightning-fast global performance.

## Benefits

### Performance 🚀
- **500ms → 50ms**: 10x faster response times for cached endpoints
- **Global**: Cloudflare's edge network (200+ locations worldwide)
- **Reduced Load**: 60-70% less traffic to Render backend

### Cost Savings 💰
- **Render**: Fewer requests = longer before rate limits
- **Gemini API**: Not cached, so costs remain accurate
- **Free**: Cloudflare Workers Free tier (100k requests/day)

### User Experience 😊
- **Instant** database browsing
- **Responsive** visualizations
- **No lag** when exploring KG nodes

## What's Cached vs Not Cached

### ✅ Cached (Static Data)

| Endpoint | Cache Duration | Why |
|----------|---------------|-----|
| `/api/health` | 5 minutes | Quick health checks |
| `/api/kg/stats` | 1 hour | Database statistics change rarely |
| `/api/kg/nodes` | 1 hour | Node list is static |
| `/api/kg/edges` | 1 hour | Edge list is static |
| `/api/kg/node/[id]` | 1 hour | Individual nodes don't change |
| `/api/kg/analytics/*` | 30 minutes | Analytics data changes rarely |
| `/api/kg/viz/cytoscape` | 30 minutes | Visualization data is static |

### ❌ Not Cached (Dynamic Data)

| Endpoint | Why Not Cached |
|----------|---------------|
| `/api/graphrag/*` | AI responses, always fresh, user-specific |
| `/api/auth/*` | Security sensitive, session-based |
| `/api/search/*` | Unique queries, low hit rate |
| `/api/texts/*` | Large payloads, low hit rate |

## Deployment Instructions

### Step 1: Create Cloudflare Worker

1. Log in to [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Go to **Workers & Pages** → **Create Application**
3. Click **Create Worker**
4. Name it: `eleuther ia-cache-worker`
5. Click **Deploy**

### Step 2: Add Worker Code

1. Click **Edit Code**
2. Delete the default code
3. Copy and paste the entire contents of `worker.js`
4. Click **Save and Deploy**

### Step 3: Add Route to Your Domain

1. Go back to **Workers & Pages**
2. Select your worker
3. Click **Triggers** tab
4. Under **Routes**, click **Add Route**
5. Enter:
   - **Route**: `free-will.app/api/*`
   - **Zone**: `free-will.app`
   - **Worker**: `eleutheria-cache-worker`
6. Click **Save**

### Step 4: Verify It's Working

Test with curl:

```bash
# First request (cache MISS)
curl -I https://free-will.app/api/health
# Look for: X-Cache-Status: MISS

# Second request (cache HIT)
curl -I https://free-will.app/api/health
# Look for: X-Cache-Status: HIT
# Look for: X-Cache-Age: 5s (or similar)
```

Or check in browser DevTools:
1. Open https://free-will.app
2. Open DevTools → Network tab
3. Navigate to Database page
4. Look for `/api/kg/stats` request
5. Check Response Headers:
   - `X-Cache-Status: HIT` = cached ✅
   - `X-Cache-Age: 15m` = cached 15 minutes ago

## Monitoring

### Cache Hit Rate

Check in Cloudflare Dashboard:
1. **Workers & Pages** → Your Worker
2. **Metrics** tab
3. Look at:
   - **Requests**: Total requests handled
   - **Cache Hit Rate**: Percentage of cached responses
   - **P99 Latency**: 99th percentile response time

**Expected Hit Rate**: 60-80% after a few hours of traffic

### Performance Comparison

Before Worker (direct to Render):
- `/api/kg/stats`: ~500-800ms
- `/api/kg/nodes`: ~300-600ms
- Global users: +100-300ms (distance to Render US server)

After Worker (cached at edge):
- `/api/kg/stats`: ~30-80ms ⚡
- `/api/kg/nodes`: ~30-80ms ⚡
- Global users: ~20-50ms ⚡ (nearest Cloudflare data center)

## Cache Invalidation

### When to Manually Purge Cache

**You updated the database** and want users to see new data immediately:

1. Go to **Cloudflare Dashboard**
2. **Caching** → **Configuration**
3. **Purge Cache** → **Purge by URL**
4. Enter:
   ```
   https://free-will.app/api/kg/stats
   https://free-will.app/api/kg/nodes
   https://free-will.app/api/kg/edges
   ```
5. Click **Purge**

### Automatic Cache Expiration

Caches automatically expire after their duration:
- Health: 5 minutes
- KG Data: 1 hour
- Analytics: 30 minutes

## Troubleshooting

### Cache Always Shows MISS

**Problem**: `X-Cache-Status: MISS` on every request

**Solutions**:
1. Check route is configured correctly (`free-will.app/api/*`)
2. Verify worker is deployed
3. Wait a few seconds between requests (cache takes moment to write)
4. Check endpoint is in the "should cache" list

### Worker Not Responding

**Problem**: Requests timeout or fail

**Solutions**:
1. Check worker is deployed and active
2. Check `BACKEND_URL` in worker code is correct
3. Test backend directly: `curl https://eleutheria.onrender.com/api/health`
4. Check Cloudflare logs in Dashboard → Workers → Logs

### Cache Too Aggressive

**Problem**: Users seeing outdated data

**Solutions**:
1. Reduce cache duration in `worker.js`:
   ```javascript
   kgStats: 30 * 60,  // Change from 1 hour to 30 min
   ```
2. Redeploy worker
3. Purge cache manually (see above)

## Cost Analysis

### Cloudflare Workers Pricing

**Free Tier**:
- ✅ 100,000 requests/day
- ✅ Unlimited worker scripts
- ✅ No bandwidth charges

**Paid Tier** ($5/month):
- 10 million requests/month included
- $0.50 per additional million requests

### Expected Usage

With ~1000 daily visitors:
- Page loads: ~1000/day
- API calls per page: ~3-5
- Total requests: **3,000-5,000/day**
- **Well within free tier** ✅

Even at 10,000 daily visitors (~30k requests/day), still free ✅

## Advanced Configuration

### Adjust Cache Durations

Edit `worker.js`:

```javascript
const CACHE_DURATIONS = {
  health: 5 * 60,      // 5 min → change to 10 * 60 for 10 min
  kgStats: 60 * 60,    // 1 hour → change to 30 * 60 for 30 min
  // ... etc
};
```

### Add More Cached Endpoints

```javascript
// In getCacheConfig function:
if (pathname === '/api/your-new-endpoint') {
  return { shouldCache: true, duration: 3600 }; // 1 hour
}
```

### Enable CORS (if needed)

```javascript
// Add CORS headers in fetch handler:
const headers = new Headers(response.headers);
headers.set('Access-Control-Allow-Origin', '*');
headers.set('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
```

## Testing

### Local Testing (Wrangler CLI)

1. Install Wrangler:
   ```bash
   npm install -g wrangler
   ```

2. Test locally:
   ```bash
   cd cloudflare-worker
   wrangler dev
   ```

3. Access at `http://localhost:8787/api/health`

### Production Testing

```bash
# Test cache miss (first request)
curl -I https://free-will.app/api/kg/stats

# Test cache hit (second request)
curl -I https://free-will.app/api/kg/stats

# Test non-cached endpoint (should always be MISS)
curl -I https://free-will.app/api/graphrag/query
```

## Summary

✅ **Deploy**: 5 minutes
✅ **Cost**: Free (100k requests/day)
✅ **Performance**: 10x faster (500ms → 50ms)
✅ **Maintenance**: Zero (automatic cache expiration)
✅ **Ethical**: Only caches static data, respects backend limitations

---

*Last Updated: 2025-01-23*
*Optimized for: Cloudflare Workers Free Tier*
