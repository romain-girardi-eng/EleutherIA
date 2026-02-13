/**
 * CORS utility for Cloudflare Workers
 */

const ELEUTHERIA_PAGES_ORIGIN = /^https:\/\/([a-z0-9-]+\.)?eleutheria\.pages\.dev$/i;

function parseAllowedOrigins(allowedOrigins: string): string[] {
  return allowedOrigins
    .split(',')
    .map((origin) => origin.trim())
    .filter(Boolean);
}

/**
 * Resolve the request origin to an allowed CORS origin.
 * Returns null when the request origin is not permitted.
 */
export function resolveCorsOrigin(
  requestOrigin: string | undefined | null,
  allowedOrigins: string,
): string | null {
  const origin = (requestOrigin || '').trim();
  if (!origin) {
    return null;
  }

  const origins = parseAllowedOrigins(allowedOrigins);
  if (origins.includes('*') || origins.includes(origin)) {
    return origin;
  }

  // Allow Vercel preview deployments for visual-pulpit.
  if (origin.endsWith('.vercel.app') && origin.includes('visual-pulpit')) {
    return origin;
  }

  // Allow Cloudflare Pages production + preview branches for EleutherIA.
  if (ELEUTHERIA_PAGES_ORIGIN.test(origin)) {
    return origin;
  }

  return null;
}

export function getCorsHeaders(origin: string, allowedOrigins: string): Headers {
  const headers = new Headers();
  const allowOrigin = resolveCorsOrigin(origin, allowedOrigins);

  if (allowOrigin) {
    headers.set('Access-Control-Allow-Origin', allowOrigin);
    headers.set('Access-Control-Allow-Credentials', 'true');
  }

  headers.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  headers.set('Access-Control-Max-Age', '86400'); // 24 hours
  headers.set('Vary', 'Origin');

  return headers;
}

export function handleCors(request: Request, response: Response, allowedOrigins: string): Response {
  const origin = request.headers.get('Origin') || '';
  const corsHeaders = getCorsHeaders(origin, allowedOrigins);

  // Clone response and add CORS headers
  const newHeaders = new Headers(response.headers);
  corsHeaders.forEach((value, key) => {
    newHeaders.set(key, value);
  });

  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: newHeaders,
  });
}

export function createOptionsResponse(request: Request, allowedOrigins: string): Response {
  const origin = request.headers.get('Origin') || '';
  const headers = getCorsHeaders(origin, allowedOrigins);

  return new Response(null, {
    status: 204,
    headers,
  });
}
