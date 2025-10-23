/**
 * Cloudflare Worker - Static KG Data Caching
 *
 * Purpose: Cache static knowledge graph endpoints to reduce load on Render backend
 * and improve global performance via Cloudflare's edge network.
 *
 * Cached Endpoints:
 * - /api/health (5 min cache)
 * - /api/kg/stats (1 hour cache)
 * - /api/kg/nodes (1 hour cache)
 * - /api/kg/edges (1 hour cache)
 * - /api/kg/node/[id] (1 hour cache)
 *
 * NOT Cached (dynamic endpoints):
 * - /api/graphrag/* (AI responses, always fresh)
 * - /api/auth/* (authentication, security sensitive)
 * - /api/search/* (user-specific searches)
 * - /api/texts/* (large payloads, low cache hit rate)
 *
 * Deployment:
 * 1. Create Cloudflare Worker in dashboard
 * 2. Paste this code
 * 3. Add route: free-will.app/api/* → this worker
 * 4. Test with: curl -I https://free-will.app/api/health
 */

const BACKEND_URL = 'https://eleutheria.onrender.com';

// Cache durations in seconds
const CACHE_DURATIONS = {
  health: 5 * 60,           // 5 minutes
  kgStats: 60 * 60,         // 1 hour
  kgNodes: 60 * 60,         // 1 hour
  kgEdges: 60 * 60,         // 1 hour
  kgNode: 60 * 60,          // 1 hour (individual nodes)
  analytics: 30 * 60,       // 30 minutes (timeline, arguments, etc.)
};

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const pathname = url.pathname;

    // Determine if endpoint should be cached
    const cacheConfig = getCacheConfig(pathname);

    if (!cacheConfig.shouldCache) {
      // Don't cache dynamic endpoints - pass through to backend
      return fetch(BACKEND_URL + pathname + url.search, {
        method: request.method,
        headers: request.headers,
        body: request.body,
      });
    }

    // Use Cloudflare's cache API
    const cache = caches.default;
    const cacheKey = new Request(url.toString(), request);

    // Try to get from cache first
    let response = await cache.match(cacheKey);

    if (response) {
      // Cache HIT - add header for debugging
      const newResponse = new Response(response.body, response);
      newResponse.headers.set('X-Cache-Status', 'HIT');
      newResponse.headers.set('X-Cache-Age', getAgeHeader(response));
      return newResponse;
    }

    // Cache MISS - fetch from backend
    response = await fetch(BACKEND_URL + pathname + url.search, {
      method: request.method,
      headers: request.headers,
    });

    // Only cache successful responses
    if (response.ok) {
      // Clone response before caching (can only read body once)
      const responseToCache = response.clone();

      // Add cache headers
      const headers = new Headers(responseToCache.headers);
      headers.set('Cache-Control', `public, max-age=${cacheConfig.duration}`);
      headers.set('X-Cache-Status', 'MISS');
      headers.set('X-Cached-At', new Date().toISOString());

      const cachedResponse = new Response(responseToCache.body, {
        status: responseToCache.status,
        statusText: responseToCache.statusText,
        headers,
      });

      // Cache the response (fire and forget)
      ctx.waitUntil(cache.put(cacheKey, cachedResponse));
    }

    return response;
  },
};

/**
 * Determine if endpoint should be cached and for how long
 */
function getCacheConfig(pathname) {
  // Health endpoint - short cache
  if (pathname === '/api/health') {
    return { shouldCache: true, duration: CACHE_DURATIONS.health };
  }

  // KG static data - long cache
  if (pathname === '/api/kg/stats') {
    return { shouldCache: true, duration: CACHE_DURATIONS.kgStats };
  }

  if (pathname === '/api/kg/nodes' || pathname === '/api/kg/edges') {
    return { shouldCache: true, duration: CACHE_DURATIONS.kgNodes };
  }

  // Individual KG nodes
  if (pathname.startsWith('/api/kg/node/')) {
    return { shouldCache: true, duration: CACHE_DURATIONS.kgNode };
  }

  // KG analytics endpoints
  if (
    pathname.startsWith('/api/kg/analytics/') ||
    pathname === '/api/kg/viz/cytoscape'
  ) {
    return { shouldCache: true, duration: CACHE_DURATIONS.analytics };
  }

  // Don't cache dynamic endpoints
  if (
    pathname.startsWith('/api/graphrag/') ||
    pathname.startsWith('/api/auth/') ||
    pathname.startsWith('/api/search/') ||
    pathname.startsWith('/api/texts/')
  ) {
    return { shouldCache: false, duration: 0 };
  }

  // Default: don't cache unknown endpoints
  return { shouldCache: false, duration: 0 };
}

/**
 * Calculate how long the response has been in cache
 */
function getAgeHeader(response) {
  const cachedAt = response.headers.get('X-Cached-At');
  if (!cachedAt) return 'unknown';

  const cacheTime = new Date(cachedAt);
  const now = new Date();
  const ageSeconds = Math.floor((now - cacheTime) / 1000);

  if (ageSeconds < 60) {
    return `${ageSeconds}s`;
  } else if (ageSeconds < 3600) {
    return `${Math.floor(ageSeconds / 60)}m`;
  } else {
    return `${Math.floor(ageSeconds / 3600)}h`;
  }
}
