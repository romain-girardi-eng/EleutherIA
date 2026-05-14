/**
 * useBibliography — session-scoped scholarly bibliography state.
 *
 * Persists to localStorage under `eleutheria.bibliography.{sessionId}` with
 * a 30-day TTL. Reducer-based to keep the surface area small and testable.
 *
 * The shape supports three kinds of entries used in doctoral writing:
 *   - primary   = an ancient source (passage / work) cited in the answer
 *   - secondary = a modern scholar / monograph cited
 *   - note      = a free-form research note keyed to neither
 *
 * Each entry has an editable `annotation` field and a stable position so
 * the user can reorder via drag-and-drop without losing context.
 */

import { useCallback, useEffect, useReducer } from 'react';

export type BibliographyKind = 'primary' | 'secondary' | 'note';

export interface BibliographyEntry {
  id: string;
  kind: BibliographyKind;
  title: string;
  author?: string;
  year?: number;
  cts_urn?: string;
  passage_id?: string;
  node_id?: string;
  excerpt?: string;
  edition?: string;
  page_or_section?: string;
  annotation: string;
  url?: string;
  bibtex_key?: string;
  added_at: number;
}

interface BibliographyState {
  entries: BibliographyEntry[];
}

type Action =
  | { type: 'add'; entry: Omit<BibliographyEntry, 'added_at'> }
  | { type: 'remove'; id: string }
  | { type: 'annotate'; id: string; annotation: string }
  | { type: 'reorder'; orderedIds: string[] }
  | { type: 'replace'; entries: BibliographyEntry[] }
  | { type: 'clear' };

const TTL_MS = 30 * 24 * 60 * 60 * 1000;
const STORAGE_PREFIX = 'eleutheria.bibliography.';

interface StoredPayload {
  entries: BibliographyEntry[];
  written_at: number;
}

const storageKey = (sessionId: string): string => `${STORAGE_PREFIX}${sessionId}`;

const loadFromStorage = (sessionId: string): BibliographyEntry[] => {
  if (typeof window === 'undefined') return [];
  try {
    const raw = window.localStorage.getItem(storageKey(sessionId));
    if (!raw) return [];
    const parsed = JSON.parse(raw) as StoredPayload;
    if (!parsed || typeof parsed.written_at !== 'number') return [];
    if (Date.now() - parsed.written_at > TTL_MS) {
      window.localStorage.removeItem(storageKey(sessionId));
      return [];
    }
    return Array.isArray(parsed.entries) ? parsed.entries : [];
  } catch {
    return [];
  }
};

const saveToStorage = (sessionId: string, entries: BibliographyEntry[]): void => {
  if (typeof window === 'undefined') return;
  try {
    const payload: StoredPayload = { entries, written_at: Date.now() };
    window.localStorage.setItem(storageKey(sessionId), JSON.stringify(payload));
  } catch {
    // Quota exceeded — silently drop. Bibliography is non-critical state.
  }
};

const reducer = (state: BibliographyState, action: Action): BibliographyState => {
  switch (action.type) {
    case 'add': {
      const duplicate = state.entries.find((e) => e.id === action.entry.id);
      if (duplicate) return state;
      return {
        entries: [...state.entries, { ...action.entry, added_at: Date.now() }],
      };
    }
    case 'remove':
      return { entries: state.entries.filter((e) => e.id !== action.id) };
    case 'annotate':
      return {
        entries: state.entries.map((e) =>
          e.id === action.id ? { ...e, annotation: action.annotation } : e,
        ),
      };
    case 'reorder': {
      const map = new Map(state.entries.map((e) => [e.id, e]));
      const ordered = action.orderedIds
        .map((id) => map.get(id))
        .filter((e): e is BibliographyEntry => Boolean(e));
      // Keep any that weren't in the ordered list (defensive).
      const remaining = state.entries.filter((e) => !action.orderedIds.includes(e.id));
      return { entries: [...ordered, ...remaining] };
    }
    case 'replace':
      return { entries: action.entries };
    case 'clear':
      return { entries: [] };
    default:
      return state;
  }
};

export interface UseBibliographyReturn {
  entries: BibliographyEntry[];
  primary: BibliographyEntry[];
  secondary: BibliographyEntry[];
  notes: BibliographyEntry[];
  add: (entry: Omit<BibliographyEntry, 'added_at'>) => void;
  remove: (id: string) => void;
  annotate: (id: string, annotation: string) => void;
  reorder: (orderedIds: string[]) => void;
  clear: () => void;
}

export function useBibliography(sessionId: string): UseBibliographyReturn {
  const [state, dispatch] = useReducer(reducer, { entries: [] });

  useEffect(() => {
    const loaded = loadFromStorage(sessionId);
    dispatch({ type: 'replace', entries: loaded });
  }, [sessionId]);

  useEffect(() => {
    saveToStorage(sessionId, state.entries);
  }, [sessionId, state.entries]);

  const add = useCallback(
    (entry: Omit<BibliographyEntry, 'added_at'>) => dispatch({ type: 'add', entry }),
    [],
  );
  const remove = useCallback((id: string) => dispatch({ type: 'remove', id }), []);
  const annotate = useCallback(
    (id: string, annotation: string) =>
      dispatch({ type: 'annotate', id, annotation }),
    [],
  );
  const reorder = useCallback(
    (orderedIds: string[]) => dispatch({ type: 'reorder', orderedIds }),
    [],
  );
  const clear = useCallback(() => dispatch({ type: 'clear' }), []);

  const primary = state.entries.filter((e) => e.kind === 'primary');
  const secondary = state.entries.filter((e) => e.kind === 'secondary');
  const notes = state.entries.filter((e) => e.kind === 'note');

  return {
    entries: state.entries,
    primary,
    secondary,
    notes,
    add,
    remove,
    annotate,
    reorder,
    clear,
  };
}
