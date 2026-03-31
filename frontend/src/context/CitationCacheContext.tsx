import React, { createContext, useContext, useRef, useCallback } from 'react';

interface Citation {
  id: string;
  text: string;
  author: string;
  work: string;
  passage_ref?: string;
  confidence?: number;
  // Add other citation fields as needed
}

interface CitationCacheContextValue {
  getCitation: (id: string) => Citation | undefined;
  setCitation: (id: string, citation: Citation) => void;
  getCitations: (ids: string[]) => Map<string, Citation>;
  prefetchCitations: (ids: string[]) => Promise<void>;
}

const CitationCacheContext = createContext<CitationCacheContextValue | null>(null);

export function CitationCacheProvider({
  children
}: {
  children: React.ReactNode
}) {
  const cache = useRef<Map<string, Citation>>(new Map());
  const pendingFetches = useRef<Map<string, Promise<void>>>(new Map());

  const getCitation = useCallback((id: string) => {
    return cache.current.get(id);
  }, []);

  const setCitation = useCallback((id: string, citation: Citation) => {
    cache.current.set(id, citation);
  }, []);

  const getCitations = useCallback((ids: string[]) => {
    const results = new Map<string, Citation>();

    ids.forEach((id) => {
      const citation = cache.current.get(id);
      if (citation) {
        results.set(id, citation);
      }
    });

    return results;
  }, []);

  const prefetchCitations = useCallback(async (ids: string[]) => {
    const missingIds = ids.filter((id) => !cache.current.has(id));

    if (missingIds.length === 0) return;

    // Check for already pending fetches
    const newIds = missingIds.filter((id) => !pendingFetches.current.has(id));

    if (newIds.length > 0) {
      const apiUrl = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/+$/, '') ?? '';
      const fetchPromise = fetch(`${apiUrl}/api/citations/batch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ids: newIds }),
      })
        .then((res) => {
          if (!res.ok) {
            throw new Error(`Failed to fetch citations: ${res.statusText}`);
          }
          return res.json();
        })
        .then((citations: Citation[]) => {
          citations.forEach((citation) => {
            cache.current.set(citation.id, citation);
            pendingFetches.current.delete(citation.id);
          });
        })
        .catch((error) => {
          console.error('Error prefetching citations:', error);
          // Remove pending fetches on error so they can be retried
          newIds.forEach((id) => pendingFetches.current.delete(id));
        });

      newIds.forEach((id) => {
        pendingFetches.current.set(id, fetchPromise);
      });
    }

    // Wait for all fetches to complete
    await Promise.all(
      missingIds
        .map((id) => pendingFetches.current.get(id))
        .filter(Boolean) as Promise<void>[]
    );
  }, []);

  return (
    <CitationCacheContext.Provider
      value={{ getCitation, setCitation, getCitations, prefetchCitations }}
    >
      {children}
    </CitationCacheContext.Provider>
  );
}

export function useCitationCache() {
  const context = useContext(CitationCacheContext);

  if (!context) {
    throw new Error(
      'useCitationCache must be used within CitationCacheProvider'
    );
  }

  return context;
}
