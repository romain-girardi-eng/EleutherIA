import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { THINKERS, loadWorkIndex, resetWorkIndexCache } from './theDebateCorpus';

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

beforeEach(() => {
  resetWorkIndexCache();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('THINKERS corpus addressing', () => {
  // The 2026-08-24 database rebuild re-minted every work_id UUID, so the five
  // hardcoded ids died and the page rendered "No passage indexed" five times
  // while promising original sources. canonical_id survives that rebuild.
  it('addresses works by canonical_id, never by a work_id UUID', () => {
    for (const thinker of THINKERS) {
      expect(thinker.workCanonicalId, thinker.id).not.toMatch(UUID);
      expect(thinker.workCanonicalId.length, thinker.id).toBeGreaterThan(0);
    }
  });

  it('gives every thinker a distinct work', () => {
    const ids = THINKERS.map((t) => t.workCanonicalId);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it('sources Origen from De Principiis III.1, not Contra Celsum', () => {
    const origen = THINKERS.find((t) => t.id === 'origen');
    expect(origen?.workCanonicalId).toContain('de_principiis');
  });

  it('sources Boethius from the Latin row, not the one labelled eng', () => {
    const boethius = THINKERS.find((t) => t.id === 'boethius');
    expect(boethius?.workCanonicalId.endsWith('_lat')).toBe(true);
  });
});

describe('loadWorkIndex', () => {
  function stubWorks(works: unknown[], ok = true) {
    const spy = vi.fn(async () => ({ ok, json: async () => ({ works }) }));
    vi.stubGlobal('fetch', spy as unknown as typeof fetch);
    return spy;
  }

  it('maps canonical_id to work_id', async () => {
    stubWorks([
      { work_id: 'uuid-a', canonical_id: 'tlg0732_tlg014_grc' },
      { work_id: 'uuid-b', canonical_id: 'urn_cts_latinlit_stoa0040_stoa003_lat' },
    ]);
    const index = await loadWorkIndex();
    expect(index.get('tlg0732_tlg014_grc')).toBe('uuid-a');
    expect(index.get('urn_cts_latinlit_stoa0040_stoa003_lat')).toBe('uuid-b');
  });

  it('skips rows with no canonical_id rather than indexing null', async () => {
    stubWorks([
      { work_id: 'uuid-a', canonical_id: null },
      { work_id: 'uuid-b', canonical_id: 'good' },
    ]);
    const index = await loadWorkIndex();
    expect(index.size).toBe(1);
    expect(index.get('good')).toBe('uuid-b');
  });

  it('fetches once and memoises across callers', async () => {
    const spy = stubWorks([{ work_id: 'uuid-a', canonical_id: 'x' }]);
    await Promise.all([loadWorkIndex(), loadWorkIndex()]);
    await loadWorkIndex();
    expect(spy).toHaveBeenCalledTimes(1);
  });

  it('does not memoise a failure, so a later call can recover', async () => {
    const failing = vi.fn(async () => {
      throw new TypeError('Failed to fetch');
    });
    vi.stubGlobal('fetch', failing as unknown as typeof fetch);
    await expect(loadWorkIndex()).rejects.toThrow();

    stubWorks([{ work_id: 'uuid-a', canonical_id: 'x' }]);
    const index = await loadWorkIndex();
    expect(index.get('x')).toBe('uuid-a');
  });

  it('rejects on a non-OK response instead of caching an empty index', async () => {
    stubWorks([], false);
    await expect(loadWorkIndex()).rejects.toThrow(/HTTP/);
  });
});
