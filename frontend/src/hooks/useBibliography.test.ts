import { describe, it, expect, beforeEach } from 'vitest';
import { act, renderHook } from '@testing-library/react';
import { useBibliography } from './useBibliography';

describe('useBibliography', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it('starts empty', () => {
    const { result } = renderHook(() => useBibliography('s1'));
    expect(result.current.entries).toHaveLength(0);
    expect(result.current.primary).toHaveLength(0);
  });

  it('adds, annotates, and removes an entry', () => {
    const { result } = renderHook(() => useBibliography('s1'));

    act(() => {
      result.current.add({
        id: 'passage:p1',
        kind: 'primary',
        title: 'Cicero, De Fato 40',
        annotation: '',
      });
    });
    expect(result.current.primary).toHaveLength(1);

    act(() => {
      result.current.annotate('passage:p1', 'Key text for compatibilism');
    });
    expect(result.current.primary[0].annotation).toBe(
      'Key text for compatibilism',
    );

    act(() => {
      result.current.remove('passage:p1');
    });
    expect(result.current.entries).toHaveLength(0);
  });

  it('refuses to add duplicate IDs', () => {
    const { result } = renderHook(() => useBibliography('s1'));
    const entry = {
      id: 'dup',
      kind: 'primary' as const,
      title: 'x',
      annotation: '',
    };
    act(() => {
      result.current.add(entry);
      result.current.add(entry);
    });
    expect(result.current.entries).toHaveLength(1);
  });

  it('reorders entries by id list', () => {
    const { result } = renderHook(() => useBibliography('s1'));
    act(() => {
      result.current.add({ id: 'a', kind: 'primary', title: 'A', annotation: '' });
      result.current.add({ id: 'b', kind: 'primary', title: 'B', annotation: '' });
      result.current.add({ id: 'c', kind: 'primary', title: 'C', annotation: '' });
    });
    act(() => {
      result.current.reorder(['c', 'a', 'b']);
    });
    expect(result.current.entries.map((e) => e.id)).toEqual(['c', 'a', 'b']);
  });

  it('persists to localStorage and restores on remount', () => {
    const { result, unmount } = renderHook(() => useBibliography('s-persist'));
    act(() => {
      result.current.add({
        id: 'p1',
        kind: 'secondary',
        title: 'Bobzien 1998',
        annotation: '',
      });
    });
    unmount();

    const stored = window.localStorage.getItem(
      'eleutheria.bibliography.s-persist',
    );
    expect(stored).toBeTruthy();
    const { result: result2 } = renderHook(() => useBibliography('s-persist'));
    expect(result2.current.secondary).toHaveLength(1);
    expect(result2.current.secondary[0].title).toBe('Bobzien 1998');
  });

  it('expires entries older than 30 days', () => {
    const expired = {
      entries: [
        {
          id: 'old',
          kind: 'primary',
          title: 'old',
          annotation: '',
          added_at: 0,
        },
      ],
      written_at: Date.now() - 31 * 24 * 60 * 60 * 1000,
    };
    window.localStorage.setItem(
      'eleutheria.bibliography.s-expire',
      JSON.stringify(expired),
    );
    const { result } = renderHook(() => useBibliography('s-expire'));
    expect(result.current.entries).toHaveLength(0);
  });

  it('splits entries by kind', () => {
    const { result } = renderHook(() => useBibliography('s-split'));
    act(() => {
      result.current.add({ id: '1', kind: 'primary', title: '1', annotation: '' });
      result.current.add({ id: '2', kind: 'secondary', title: '2', annotation: '' });
      result.current.add({ id: '3', kind: 'note', title: '3', annotation: '' });
    });
    expect(result.current.primary).toHaveLength(1);
    expect(result.current.secondary).toHaveLength(1);
    expect(result.current.notes).toHaveLength(1);
  });
});
