import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import {
  ORIGIN_QUESTION,
  THINKERS,
  loadWorkIndex,
  resetWorkIndexCache,
} from './theDebateCorpus';

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

  it('sources Origen from De Principiis III.1, not Contra Celsum', () => {
    const origen = THINKERS.find((t) => t.id === 'origen');
    expect(origen?.workCanonicalId).toContain('de_principiis');
  });

  it('sources Boethius from the Latin row, not the one labelled eng', () => {
    const boethius = THINKERS.find((t) => t.id === 'boethius');
    expect(boethius?.workCanonicalId.endsWith('_lat')).toBe(true);
  });
});

describe('THINKERS editorial invariants', () => {
  // The page used to chain each figure to the previous one as if answering it.
  // Every link was false, so the model now records the REAL opponent and the
  // modern disagreement, and both are mandatory.
  it('gives every figure a named opponent and a live controversy', () => {
    for (const t of THINKERS) {
      expect(t.opponent.trim(), `${t.id} opponent`).not.toBe('');
      expect(t.contested.trim(), `${t.id} contested`).not.toBe('');
    }
  });

  it('never claims a figure answers another figure on the page', () => {
    const names = THINKERS.map((t) => t.nav);
    for (const t of THINKERS) {
      // An opponent naming another station would resurrect the false chain.
      // Chrysippus is the one legitimate exception-free case: nobody here has
      // a page-mate as their attested target.
      for (const name of names) {
        if (name === t.nav) continue;
        expect(t.opponent, `${t.id} opponent must not name ${name}`).not.toContain(
          name,
        );
      }
    }
  });

  it('records reuse only as attested transmission, never as a reply', () => {
    for (const t of THINKERS) {
      for (const source of t.inheritsFrom ?? []) {
        expect(source.toLowerCase()).not.toMatch(/answers|replies|responds/);
      }
    }
  });

  it('keeps the figures in chronological order', () => {
    const years = THINKERS.map((t) => t.year);
    expect([...years].sort((a, b) => a - b)).toEqual(years);
  });

  it('marks Boethius as a coda and nobody else', () => {
    expect(THINKERS.filter((t) => t.coda).map((t) => t.id)).toEqual(['boethius']);
  });

  it('encodes tone as the source language, with no third thinker tone', () => {
    for (const t of THINKERS) {
      expect(['greek', 'latin']).toContain(t.tone);
    }
  });

  it('flags every figure whose text is a testimonium rather than their own', () => {
    // Epicurus, Chrysippus, Carneades and Epictetus left nothing that survives
    // in the work cited; saying so is the difference between a source and a
    // report of a source.
    for (const id of ['epicurus', 'chrysippus', 'carneades', 'epictetus']) {
      const t = THINKERS.find((x) => x.id === id);
      expect(t?.passageNote, `${id} needs a testimonium note`).toBeTruthy();
    }
  });
});

describe('ORIGIN_QUESTION', () => {
  it('offers several irreconcilable answers and adjudicates none', () => {
    expect(ORIGIN_QUESTION.answers.length).toBeGreaterThanOrEqual(5);
    const answers = ORIGIN_QUESTION.answers.map((a) => a.answer);
    expect(new Set(answers).size).toBe(answers.length);
    expect(ORIGIN_QUESTION.disclaimer).toMatch(/does not adjudicate/i);
  });

  it('includes the positions that reject the question itself', () => {
    const answers = ORIGIN_QUESTION.answers.map((a) => a.answer);
    expect(answers).toContain('Nobody in antiquity');
    expect(answers).toContain('The wrong question');
  });

  it('attributes every answer to a named scholar', () => {
    for (const a of ORIGIN_QUESTION.answers) {
      expect(a.scholar.trim()).not.toBe('');
      expect(a.claim.trim()).not.toBe('');
    }
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
