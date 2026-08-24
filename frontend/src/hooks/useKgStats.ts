import { useEffect, useState } from 'react';
import { apiEndpoint } from '../api/baseUrl';

/**
 * Single source of truth for KG/corpus counts shown across the app.
 *
 * Fetches `/api/kg/stats` and `/api/works/stats` once on mount, caches the
 * result in localStorage (TTL: 1 hour) and serves it stale-while-revalidate.
 *
 * Returns RAW numbers; consumers format with `value.toLocaleString(i18n.language)`
 * to respect the user's locale (1,234 / 1.234 / 1 234).
 *
 * No hardcoded stat numbers: until the live fetch resolves (and if it fails)
 * every count is non-finite, which all formatters (`formatCount`,
 * `formatCompact`, `formatFull`) render as "—". The last successful fetch is
 * cached in localStorage and reused on return so numbers persist across visits.
 */

const STORAGE_KEY = 'kg_stats_v1';
const TTL_MS = 60 * 60 * 1000; // 1 hour

interface KgStatsPayload {
  total_nodes: number;
  total_edges: number;
  node_types?: Record<string, number>;
  edge_types?: Record<string, number>;
  connected_components?: number;
  density?: number;
}

interface WorksStatsPayload {
  works: {
    total_works: number;
    unique_authors: number;
    total_words: number;
    languages_count?: number;
  };
  passages: {
    total_passages: number;
    avg_passage_words?: string;
  };
}

export interface KgStats {
  /** True if the data is from a cached fetch and may be slightly stale. */
  isCached: boolean;
  /** True until the first successful fetch completes. */
  isLoading: boolean;
  error: string | null;

  // KG counts
  nodes: number;
  edges: number;
  nodeTypes: Record<string, number>;
  edgeTypes: Record<string, number>;
  connectedComponents: number;

  // Corpus counts
  works: number;
  uniqueAuthors: number;
  passages: number;
  totalWords: number;
  languagesCount: number;

  // Convenience: largest node-type categories
  personCount: number;
  argumentCount: number;
  conceptCount: number;
  publicationCount: number;
}

// "Unknown" state — no hardcoded stat numbers. Non-finite counts render as "—"
// via the formatters until the live fetch resolves (or if it fails).
const UNKNOWN: Omit<KgStats, 'isCached' | 'isLoading' | 'error'> = {
  nodes: Number.NaN,
  edges: Number.NaN,
  nodeTypes: {},
  edgeTypes: {},
  connectedComponents: Number.NaN,
  works: Number.NaN,
  uniqueAuthors: Number.NaN,
  passages: Number.NaN,
  totalWords: Number.NaN,
  languagesCount: Number.NaN,
  personCount: Number.NaN,
  argumentCount: Number.NaN,
  conceptCount: Number.NaN,
  publicationCount: Number.NaN,
};

interface CachedRecord {
  fetchedAt: number;
  payload: Pick<
    KgStats,
    | 'nodes'
    | 'edges'
    | 'nodeTypes'
    | 'edgeTypes'
    | 'connectedComponents'
    | 'works'
    | 'uniqueAuthors'
    | 'passages'
    | 'totalWords'
    | 'languagesCount'
    | 'personCount'
    | 'argumentCount'
    | 'conceptCount'
    | 'publicationCount'
  >;
}

function readCache(): CachedRecord | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const rec = JSON.parse(raw) as CachedRecord;
    if (!rec || typeof rec.fetchedAt !== 'number') return null;
    return rec;
  } catch {
    return null;
  }
}

function writeCache(payload: CachedRecord['payload']): void {
  if (typeof window === 'undefined') return;
  try {
    const rec: CachedRecord = { fetchedAt: Date.now(), payload };
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(rec));
  } catch {
    // localStorage may be unavailable (private mode, quota). Non-fatal.
  }
}

async function fetchFresh(): Promise<CachedRecord['payload']> {
  const [kgResp, worksResp] = await Promise.all([
    fetch(apiEndpoint('/api/kg/stats'), { headers: { Accept: 'application/json' } }),
    fetch(apiEndpoint('/api/works/stats'), { headers: { Accept: 'application/json' } }),
  ]);

  if (!kgResp.ok) throw new Error(`kg/stats HTTP ${kgResp.status}`);
  if (!worksResp.ok) throw new Error(`works/stats HTTP ${worksResp.status}`);

  const kg: KgStatsPayload = await kgResp.json();
  const works: WorksStatsPayload = await worksResp.json();

  const nodeTypes = kg.node_types ?? {};
  const edgeTypes = kg.edge_types ?? {};

  return {
    nodes: kg.total_nodes ?? Number.NaN,
    edges: kg.total_edges ?? Number.NaN,
    nodeTypes,
    edgeTypes,
    connectedComponents: kg.connected_components ?? Number.NaN,
    works: works.works?.total_works ?? Number.NaN,
    uniqueAuthors: works.works?.unique_authors ?? Number.NaN,
    passages: works.passages?.total_passages ?? Number.NaN,
    totalWords: works.works?.total_words ?? Number.NaN,
    languagesCount: works.works?.languages_count ?? Number.NaN,
    personCount: nodeTypes['person'] ?? Number.NaN,
    argumentCount: nodeTypes['argument'] ?? Number.NaN,
    conceptCount: nodeTypes['concept'] ?? Number.NaN,
    publicationCount: nodeTypes['publication'] ?? Number.NaN,
  };
}

export function useKgStats(): KgStats {
  const cached = readCache();
  const initial: KgStats = cached
    ? { ...cached.payload, isCached: true, isLoading: false, error: null }
    : { ...UNKNOWN, isCached: false, isLoading: true, error: null };
  const [stats, setStats] = useState<KgStats>(initial);

  useEffect(() => {
    let mounted = true;
    const fresh = !cached || Date.now() - cached.fetchedAt > TTL_MS;
    if (!fresh && cached) return; // Cache is fresh — no fetch needed

    fetchFresh()
      .then((payload) => {
        if (!mounted) return;
        writeCache(payload);
        setStats({ ...payload, isCached: false, isLoading: false, error: null });
      })
      .catch((err: unknown) => {
        if (!mounted) return;
        // On error: keep cached/fallback values, just record the error.
        setStats((prev) => ({
          ...prev,
          isLoading: false,
          error: err instanceof Error ? err.message : String(err),
        }));
      });

    return () => {
      mounted = false;
    };
    // Run once on mount; cache mediates re-fetches across mounts.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return stats;
}

/**
 * Convenience formatter — produces a locale-aware integer string for a count.
 * Returns '—' for non-finite values so partial data never crashes copy.
 */
export function formatCount(value: number | undefined | null, locale?: string): string {
  if (value == null || !Number.isFinite(value)) return '—';
  return value.toLocaleString(locale);
}
