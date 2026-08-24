const FALLBACK_API_BASE = 'http://localhost:8000';
const PUBLIC_API_BASE = 'https://free-will.app';
const RETIRED_API_HOSTS = new Set([
  'ancient-free-will-api.romain-girardi-eng.workers.dev',
]);

function isEleutheriaPagesHost(hostname: string): boolean {
  return hostname === 'eleutheria.pages.dev'
    || hostname.endsWith('.eleutheria.pages.dev');
}

/** Resolve build-time configuration against the runtime host.
 *
 * Cloudflare Pages preview deployments do not proxy `/api/*`. They must call
 * the public API origin explicitly. A retired Worker hostname was historically
 * configured in the Pages environment; fail over deterministically instead of
 * letting every request end as an opaque browser `Network Error`.
 */
export function resolveApiBase(
  configuredBase: string | undefined,
  runtimeHostname = typeof window === 'undefined' ? '' : window.location.hostname,
): string {
  const normalized = (configuredBase?.trim() || FALLBACK_API_BASE).replace(/\/+$/, '');
  if (isEleutheriaPagesHost(runtimeHostname)) return PUBLIC_API_BASE;
  try {
    if (RETIRED_API_HOSTS.has(new URL(normalized).hostname)) return PUBLIC_API_BASE;
  } catch {
    // Relative bases such as `/api` remain valid for local proxy deployments.
  }
  return normalized;
}

export const API_BASE = resolveApiBase(
  typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_URL
    ? import.meta.env.VITE_API_URL
    : undefined,
);

/**
 * Join an API path to either an origin (`https://…`) or the local Vite `/api`
 * proxy without ever producing `/api/api/*`.
 */
export function apiEndpoint(path: string, base = API_BASE): string {
  const normalizedPath = `/${path.replace(/^\/+/, '')}`;
  const normalizedBase = base.trim().replace(/\/+$/, '');
  if (!normalizedBase) return normalizedPath;
  if (
    (normalizedBase === '/api' || normalizedBase.endsWith('/api'))
    && (normalizedPath === '/api' || normalizedPath.startsWith('/api/'))
  ) {
    return `${normalizedBase}${normalizedPath.slice(4)}`;
  }
  return `${normalizedBase}${normalizedPath}`;
}
