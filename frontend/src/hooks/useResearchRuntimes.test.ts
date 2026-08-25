import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useResearchRuntimes, resetResearchRuntimeCache } from './useResearchRuntimes';

const URL = 'https://api.test/api/opencode/status';

beforeEach(() => {
  resetResearchRuntimeCache();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

function stubFetch(impl: () => Promise<unknown>) {
  const spy = vi.fn(impl);
  vi.stubGlobal('fetch', spy as unknown as typeof fetch);
  return spy;
}

describe('useResearchRuntimes', () => {
  it('reports deep available when the backend says it is configured', async () => {
    stubFetch(async () => ({ ok: true, json: async () => ({ configured: true }) }));
    const { result } = renderHook(() => useResearchRuntimes(URL));
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.deep).toBe(true);
    expect(result.current.quick).toBe(true);
  });

  it('reports deep unavailable when the backend says it is unconfigured', async () => {
    stubFetch(async () => ({ ok: true, json: async () => ({ configured: false }) }));
    const { result } = renderHook(() => useResearchRuntimes(URL));
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.deep).toBe(false);
  });

  it('degrades to quick-only when the probe itself fails', async () => {
    stubFetch(async () => {
      throw new TypeError('Failed to fetch');
    });
    const { result } = renderHook(() => useResearchRuntimes(URL));
    await waitFor(() => expect(result.current.loading).toBe(false));
    // A probe that cannot be reached must never break the page: quick stays on.
    expect(result.current.deep).toBe(false);
    expect(result.current.quick).toBe(true);
  });

  it('treats a non-OK probe response as unavailable', async () => {
    stubFetch(async () => ({ ok: false, json: async () => ({}) }));
    const { result } = renderHook(() => useResearchRuntimes(URL));
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.deep).toBe(false);
  });

  it('probes once and serves the memo on remount', async () => {
    const spy = stubFetch(async () => ({
      ok: true,
      json: async () => ({ configured: true }),
    }));
    const first = renderHook(() => useResearchRuntimes(URL));
    await waitFor(() => expect(first.result.current.loading).toBe(false));
    first.unmount();

    const second = renderHook(() => useResearchRuntimes(URL));
    expect(second.result.current.deep).toBe(true);
    expect(second.result.current.loading).toBe(false);
    expect(spy).toHaveBeenCalledTimes(1);
  });
});
