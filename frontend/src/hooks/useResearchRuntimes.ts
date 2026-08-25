/**
 * useResearchRuntimes — ask the backend which /research runtimes are live.
 *
 * The "deep" runtime is an opencode upstream that the API proxies. When
 * `OPENCODE_SERVER_PASSWORD` is unset (which is the case on any deployment
 * that does not ship the opencode container) every deep query dies on a 503
 * the user cannot predict. Probing `/api/opencode/status` on mount lets the
 * page disable the option and say why, instead of offering a runtime that
 * cannot answer.
 *
 * The probe is public, cheap, and cached for the tab session: a failure is
 * treated as "deep unavailable", never as a page-level error.
 */

import { useEffect, useState } from 'react';
import { apiEndpoint } from '../api/baseUrl';

export type ResearchRuntime = 'quick' | 'deep';

export interface ResearchRuntimeAvailability {
  /** The Python ReAct pipeline ships with the API — always present. */
  quick: boolean;
  /** The opencode multi-agent runtime — present only when proxied. */
  deep: boolean;
  /** True until the probe settles; the UI keeps deep neutral meanwhile. */
  loading: boolean;
}

const INITIAL: ResearchRuntimeAvailability = {
  quick: true,
  deep: false,
  loading: true,
};

/** Module-level memo so navigating back to /research does not re-probe. */
let cached: ResearchRuntimeAvailability | null = null;

/** Test seam — drop the memo between cases. */
export function resetResearchRuntimeCache(): void {
  cached = null;
}

export function useResearchRuntimes(
  statusUrl = apiEndpoint('/api/opencode/status'),
): ResearchRuntimeAvailability {
  const [availability, setAvailability] = useState<ResearchRuntimeAvailability>(
    () => cached ?? INITIAL,
  );

  useEffect(() => {
    if (cached) {
      setAvailability(cached);
      return;
    }
    const controller = new AbortController();
    let active = true;

    const settle = (deep: boolean) => {
      if (!active) return;
      const next: ResearchRuntimeAvailability = { quick: true, deep, loading: false };
      cached = next;
      setAvailability(next);
    };

    fetch(statusUrl, { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) return settle(false);
        const body = (await response.json()) as { configured?: unknown };
        settle(body?.configured === true);
      })
      .catch(() => {
        // An unreachable probe means the runtime is unusable anyway. Never
        // surface this as an error — the quick runtime remains available.
        if (!controller.signal.aborted) settle(false);
      });

    return () => {
      active = false;
      controller.abort();
    };
  }, [statusUrl]);

  return availability;
}

export default useResearchRuntimes;
