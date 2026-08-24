const FALLBACK_API_BASE = 'http://localhost:8000';

export const API_BASE = (
  typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_URL
    ? import.meta.env.VITE_API_URL
    : FALLBACK_API_BASE
).trim().replace(/\/+$/, '');

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
