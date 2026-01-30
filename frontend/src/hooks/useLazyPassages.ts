/**
 * useLazyPassages - Hook for lazy loading passages with infinite scroll
 *
 * This hook dramatically reduces initial page load time and database egress by:
 * 1. Loading only the first batch of passages initially
 * 2. Loading more as the user scrolls
 * 3. Prefetching the next batch for smooth UX
 * 4. Using cached data when available
 *
 * Usage:
 * const { passages, loading, hasMore, loadMore, loadingMore, sentinelRef } = useLazyPassages(workId);
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { cachedApiClient } from '../api/cachedClient';

interface Passage {
  passage_id: string;
  canonical_ref: string;
  cts_urn: string | null;
  sequence_number: number;
  text_content: string;
  char_length: number;
  citation_hierarchy?: Record<string, unknown>;
}

interface UseLazyPassagesOptions {
  /** Initial number of passages to load (default: 30) */
  initialLimit?: number;
  /** Number of passages to load per batch (default: 30) */
  batchSize?: number;
  /** Whether to automatically load more on scroll (default: true) */
  autoLoad?: boolean;
  /** Number of passages before end to trigger prefetch (default: 10) */
  prefetchThreshold?: number;
}

interface UseLazyPassagesResult {
  /** Currently loaded passages */
  passages: Passage[];
  /** Whether initial load is in progress */
  loading: boolean;
  /** Whether more passages are available */
  hasMore: boolean;
  /** Function to manually load more passages */
  loadMore: () => Promise<void>;
  /** Whether a batch is currently loading */
  loadingMore: boolean;
  /** Total number of passages for this work */
  totalCount: number;
  /** Error message if any */
  error: string | null;
  /** Ref to attach to sentinel element for infinite scroll */
  sentinelRef: (node: HTMLElement | null) => void;
  /** Reset and reload from beginning */
  reset: () => void;
  /** Current progress (passages loaded / total) */
  progress: { loaded: number; total: number };
}

export function useLazyPassages(
  workId: string | undefined,
  options: UseLazyPassagesOptions = {}
): UseLazyPassagesResult {
  const {
    initialLimit = 30,
    batchSize = 30,
    autoLoad = true,
    prefetchThreshold = 10,
  } = options;

  const [passages, setPassages] = useState<Passage[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [totalCount, setTotalCount] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const offsetRef = useRef(0);
  const observerRef = useRef<IntersectionObserver | null>(null);
  const sentinelNodeRef = useRef<HTMLElement | null>(null);
  const isPrefetchingRef = useRef(false);

  // Load initial batch
  useEffect(() => {
    if (!workId) return;

    const loadInitial = async () => {
      try {
        setLoading(true);
        setError(null);
        setPassages([]);
        offsetRef.current = 0;

        const response = await cachedApiClient.getWorkPassages(workId, {
          offset: 0,
          limit: initialLimit,
        });

        const newPassages = (response.passages || []) as Passage[];
        setPassages(newPassages);
        setTotalCount(response.total || 0);
        setHasMore(newPassages.length < (response.total || 0));
        offsetRef.current = newPassages.length;

        // Prefetch next batch
        if (newPassages.length < (response.total || 0)) {
          prefetchNext(workId, newPassages.length, batchSize);
        }
      } catch (err) {
        console.error('Error loading passages:', err);
        setError(err instanceof Error ? err.message : 'Failed to load passages');
      } finally {
        setLoading(false);
      }
    };

    loadInitial();
  }, [workId, initialLimit, batchSize]);

  // Prefetch next batch in background
  const prefetchNext = useCallback(
    async (wId: string, currentOffset: number, limit: number) => {
      if (isPrefetchingRef.current) return;
      isPrefetchingRef.current = true;

      try {
        await cachedApiClient.prefetchPassages(wId, currentOffset, limit);
      } finally {
        isPrefetchingRef.current = false;
      }
    },
    []
  );

  // Load more passages
  const loadMore = useCallback(async () => {
    if (!workId || loadingMore || !hasMore) return;

    try {
      setLoadingMore(true);

      const response = await cachedApiClient.getWorkPassages(workId, {
        offset: offsetRef.current,
        limit: batchSize,
      });

      const newPassages = (response.passages || []) as Passage[];

      setPassages((prev) => {
        // Deduplicate by passage_id
        const existingIds = new Set(prev.map((p) => p.passage_id));
        const uniqueNew = newPassages.filter((p) => !existingIds.has(p.passage_id));
        return [...prev, ...uniqueNew];
      });

      offsetRef.current += newPassages.length;
      setHasMore(offsetRef.current < (response.total || 0));

      // Prefetch next batch
      if (offsetRef.current < (response.total || 0)) {
        prefetchNext(workId, offsetRef.current, batchSize);
      }
    } catch (err) {
      console.error('Error loading more passages:', err);
      setError(err instanceof Error ? err.message : 'Failed to load more passages');
    } finally {
      setLoadingMore(false);
    }
  }, [workId, loadingMore, hasMore, batchSize, prefetchNext]);

  // Check if we should prefetch based on scroll position
  const checkPrefetch = useCallback(() => {
    if (!workId || !hasMore) return;

    const remainingPassages = totalCount - passages.length;
    if (remainingPassages > 0 && remainingPassages <= prefetchThreshold + batchSize) {
      prefetchNext(workId, offsetRef.current, batchSize);
    }
  }, [workId, hasMore, totalCount, passages.length, prefetchThreshold, batchSize, prefetchNext]);

  // Set up intersection observer for infinite scroll
  const sentinelRef = useCallback(
    (node: HTMLElement | null) => {
      // Disconnect previous observer
      if (observerRef.current) {
        observerRef.current.disconnect();
      }

      sentinelNodeRef.current = node;

      if (!node || !autoLoad) return;

      observerRef.current = new IntersectionObserver(
        (entries) => {
          const [entry] = entries;
          if (entry.isIntersecting && hasMore && !loadingMore && !loading) {
            loadMore();
          }
        },
        {
          root: null,
          rootMargin: '200px', // Start loading before reaching the end
          threshold: 0,
        }
      );

      observerRef.current.observe(node);
    },
    [autoLoad, hasMore, loadingMore, loading, loadMore]
  );

  // Check prefetch on passages change
  useEffect(() => {
    checkPrefetch();
  }, [passages.length, checkPrefetch]);

  // Cleanup observer on unmount
  useEffect(() => {
    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, []);

  // Reset function
  const reset = useCallback(() => {
    setPassages([]);
    setLoading(true);
    setLoadingMore(false);
    setHasMore(true);
    setTotalCount(0);
    setError(null);
    offsetRef.current = 0;
  }, []);

  return {
    passages,
    loading,
    hasMore,
    loadMore,
    loadingMore,
    totalCount,
    error,
    sentinelRef,
    reset,
    progress: {
      loaded: passages.length,
      total: totalCount,
    },
  };
}

export default useLazyPassages;
