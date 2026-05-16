import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { FileText, Loader2, AlertCircle, Search } from 'lucide-react';
import { listContributions } from '../../api/contributions';
import ContributionCard, { type ContributionListItem } from './ContributionCard';
import StatusFilter, {
  type StatusFilterValue,
} from './StatusFilter';

const PAGE_LIMIT = 24;

function CardSkeleton() {
  return (
    <div
      className="h-[230px] animate-pulse rounded-2xl border border-stone-200/50 bg-white/40 p-5"
      aria-hidden="true"
    >
      <div className="mb-3 flex justify-between">
        <div className="h-4 w-16 rounded-full bg-stone-200/60" />
        <div className="h-3 w-10 rounded bg-stone-200/60" />
      </div>
      <div className="mb-3 h-1.5 w-full rounded-full bg-stone-200/60" />
      <div className="h-4 w-3/4 rounded bg-stone-200/60" />
      <div className="mt-2 h-3 w-1/2 rounded bg-stone-200/60" />
      <div className="mt-4 flex gap-1.5">
        <div className="h-4 w-16 rounded-full bg-stone-100" />
        <div className="h-4 w-12 rounded-full bg-stone-100" />
        <div className="h-4 w-14 rounded-full bg-stone-100" />
      </div>
      <div className="mt-4 flex justify-between border-t border-stone-100 pt-3">
        <div className="h-3 w-24 rounded bg-stone-100" />
        <div className="h-3 w-16 rounded bg-stone-100" />
      </div>
    </div>
  );
}

export default function ContributionsListPage() {
  const { t } = useTranslation();
  const [items, setItems] = useState<ContributionListItem[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<StatusFilterValue>('all');
  const [submitterQuery, setSubmitterQuery] = useState('');
  const [debouncedSubmitter, setDebouncedSubmitter] = useState('');
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sentinelRef = useRef<HTMLDivElement | null>(null);
  const fetchIdRef = useRef(0);

  // Debounce the submitter free-text filter.
  useEffect(() => {
    const handle = window.setTimeout(() => {
      setDebouncedSubmitter(submitterQuery.trim().toLowerCase());
    }, 250);
    return () => window.clearTimeout(handle);
  }, [submitterQuery]);

  const fetchPage = useCallback(
    async (opts: { append: boolean; cursorParam: string | null }) => {
      const fetchId = ++fetchIdRef.current;
      if (opts.append) setLoadingMore(true);
      else setLoading(true);
      setError(null);

      try {
        const response = await listContributions({
          ...(statusFilter !== 'all' ? { status: statusFilter } : {}),
          limit: PAGE_LIMIT,
          ...(opts.cursorParam ? { cursor: opts.cursorParam } : {}),
        });

        if (fetchId !== fetchIdRef.current) return;

        setItems((prev) =>
          opts.append ? [...prev, ...response.items] : response.items
        );
        setNextCursor(response.next_cursor);
      } catch (err: unknown) {
        if (fetchId !== fetchIdRef.current) return;
        const message =
          err instanceof Error ? err.message : t('contributions.errors.loadFailed');
        setError(message);
        if (!opts.append) setItems([]);
      } finally {
        if (fetchId === fetchIdRef.current) {
          setLoading(false);
          setLoadingMore(false);
        }
      }
    },
    [statusFilter, t]
  );

  useEffect(() => {
    fetchPage({ append: false, cursorParam: null });
  }, [statusFilter, fetchPage]);

  useEffect(() => {
    const node = sentinelRef.current;
    if (!node) return;
    if (!nextCursor) return;
    if (loading || loadingMore) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const target = entries[0];
        if (target?.isIntersecting && nextCursor) {
          fetchPage({ append: true, cursorParam: nextCursor });
        }
      },
      { rootMargin: '300px 0px' }
    );

    observer.observe(node);
    return () => observer.disconnect();
  }, [nextCursor, loading, loadingMore, fetchPage]);

  const visibleItems = useMemo(() => {
    if (!debouncedSubmitter) return items;
    return items.filter((item) =>
      item.authors.some((author) =>
        author.toLowerCase().includes(debouncedSubmitter)
      )
    );
  }, [items, debouncedSubmitter]);

  const counts = useMemo<Partial<Record<StatusFilterValue, number>>>(() => {
    const buckets: Partial<Record<StatusFilterValue, number>> = {
      all: items.length,
    };
    for (const item of items) {
      buckets[item.status] = (buckets[item.status] ?? 0) + 1;
    }
    return buckets;
  }, [items]);

  const isEmpty = !loading && !error && visibleItems.length === 0;

  return (
    <div className="min-h-screen w-full bg-transparent">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
          className="pt-28 pb-8 text-center"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-stone-800/5 border border-stone-300/30 text-xs font-medium text-stone-500 tracking-wide uppercase mb-5">
            <FileText className="w-3.5 h-3.5" aria-hidden="true" />
            {t('contributions.eyebrow')}
          </div>
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-display font-semibold text-stone-800 tracking-tight mb-3">
            {t('contributions.title')}
          </h1>
          <p className="text-base sm:text-lg text-stone-500 max-w-2xl mx-auto leading-relaxed">
            {t('contributions.subtitle')}
          </p>
        </motion.div>

        <div className="mb-8 space-y-4">
          <StatusFilter
            value={statusFilter}
            onChange={setStatusFilter}
            counts={counts}
          />

          <div className="relative max-w-md">
            <Search
              className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-stone-400"
              aria-hidden="true"
            />
            <input
              type="search"
              value={submitterQuery}
              onChange={(event) => setSubmitterQuery(event.target.value)}
              placeholder={t('contributions.filters.searchAuthorPlaceholder')}
              className="w-full rounded-full border border-stone-200/70 bg-white/60 py-2 sm:py-1.5 pl-9 pr-3 text-base sm:text-sm text-stone-700 placeholder:text-stone-400 backdrop-blur-sm transition-colors focus:border-amber-400/70 focus:outline-none focus:ring-2 focus:ring-amber-400/30"
              aria-label={t('contributions.filters.searchAuthorAria')}
            />
          </div>
        </div>

        {error && (
          <div
            role="alert"
            className="mb-6 flex items-start gap-3 rounded-xl border border-red-200/60 bg-red-50/70 p-4 text-sm text-red-800"
          >
            <AlertCircle
              className="mt-0.5 h-4 w-4 flex-shrink-0"
              aria-hidden="true"
            />
            <div>
              <p className="font-medium">{t('contributions.errors.title')}</p>
              <p className="text-red-700/80">{error}</p>
            </div>
          </div>
        )}

        {loading && items.length === 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 sm:gap-5">
            {Array.from({ length: 6 }).map((_, i) => (
              <CardSkeleton key={i} />
            ))}
          </div>
        ) : isEmpty ? (
          <div className="rounded-2xl border border-stone-200/60 bg-white/50 p-12 text-center">
            <FileText
              className="mx-auto h-8 w-8 text-stone-300"
              aria-hidden="true"
            />
            <h2 className="mt-4 text-sm font-medium text-stone-700">
              {t('contributions.empty.title')}
            </h2>
            <p className="mt-1 text-xs text-stone-500">
              {t(
                debouncedSubmitter
                  ? 'contributions.empty.bodySearch'
                  : 'contributions.empty.body'
              )}
            </p>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 sm:gap-5">
              {visibleItems.map((item, index) => (
                <ContributionCard
                  key={item.contribution_id}
                  item={item}
                  index={index}
                />
              ))}
            </div>

            <div ref={sentinelRef} className="h-px w-full" aria-hidden="true" />

            {loadingMore && (
              <div className="flex justify-center py-8">
                <Loader2
                  className="h-5 w-5 animate-spin text-stone-400"
                  aria-label={t('contributions.loadingMore')}
                />
              </div>
            )}

            {!loadingMore && !nextCursor && items.length > 0 && (
              <p className="py-10 text-center text-[11px] uppercase tracking-wider text-stone-300">
                {t('contributions.endOfList')}
              </p>
            )}
          </>
        )}

        <div className="h-16" />
      </div>
    </div>
  );
}
