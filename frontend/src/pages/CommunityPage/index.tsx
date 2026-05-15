import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { BookOpenText, Loader2, AlertCircle } from 'lucide-react';
import { listCommunityQueries, type CommunityListItem } from '../../api/community';
import QueryCard from './QueryCard';
import FilterBar, { type CommunitySort } from './FilterBar';

const PAGE_LIMIT = 20;

function CardSkeleton() {
  return (
    <div
      className="h-[210px] animate-pulse rounded-2xl border border-stone-200/50 bg-white/40 p-5"
      aria-hidden="true"
    >
      <div className="mb-3 flex gap-1.5">
        <div className="h-4 w-16 rounded-full bg-stone-200/60" />
        <div className="h-4 w-12 rounded-full bg-stone-200/60" />
      </div>
      <div className="h-4 w-3/4 rounded bg-stone-200/60" />
      <div className="mt-2 h-4 w-5/6 rounded bg-stone-200/60" />
      <div className="mt-4 space-y-2">
        <div className="h-3 w-full rounded bg-stone-100" />
        <div className="h-3 w-11/12 rounded bg-stone-100" />
        <div className="h-3 w-8/12 rounded bg-stone-100" />
      </div>
      <div className="mt-4 flex justify-between border-t border-stone-100 pt-3">
        <div className="h-3 w-24 rounded bg-stone-100" />
        <div className="h-3 w-16 rounded bg-stone-100" />
      </div>
    </div>
  );
}

export default function CommunityPage() {
  const { t } = useTranslation();
  const [items, setItems] = useState<CommunityListItem[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [sort, setSort] = useState<CommunitySort>('recent');
  const [selectedPeriod, setSelectedPeriod] = useState<string | null>(null);
  const [selectedPhilosopher, setSelectedPhilosopher] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sentinelRef = useRef<HTMLDivElement | null>(null);
  // Track the latest fetch so stale responses don't overwrite newer ones
  // when filters change quickly.
  const fetchIdRef = useRef(0);

  const periods = useMemo(
    () => [
      { key: 'Présocratique', label: t('recherches.tags.period.presocratic') },
      { key: 'Classique', label: t('recherches.tags.period.classical') },
      { key: 'Hellénistique', label: t('recherches.tags.period.hellenistic') },
      { key: 'Impérial', label: t('recherches.tags.period.imperial') },
      { key: 'Tardo-antique', label: t('recherches.tags.period.lateAntique') },
    ],
    [t]
  );

  const philosophers = useMemo(
    () => [
      { key: 'Stoic', label: t('recherches.tags.school.stoic') },
      { key: 'Epicurean', label: t('recherches.tags.school.epicurean') },
      { key: 'Peripatetic', label: t('recherches.tags.school.peripatetic') },
      { key: 'Academic', label: t('recherches.tags.school.academic') },
      { key: 'Platonist', label: t('recherches.tags.school.platonist') },
      { key: 'Patristic', label: t('recherches.tags.school.patristic') },
    ],
    [t]
  );

  const fetchPage = useCallback(
    async (opts: { append: boolean; cursorParam: string | null }) => {
      const fetchId = ++fetchIdRef.current;
      if (opts.append) setLoadingMore(true);
      else setLoading(true);
      setError(null);

      try {
        const response = await listCommunityQueries({
          sort,
          limit: PAGE_LIMIT,
          ...(selectedPeriod ? { period: selectedPeriod } : {}),
          ...(selectedPhilosopher ? { philosopher: selectedPhilosopher } : {}),
          ...(opts.cursorParam ? { cursor: opts.cursorParam } : {}),
        });

        if (fetchId !== fetchIdRef.current) return;

        setItems((prev) => (opts.append ? [...prev, ...response.items] : response.items));
        setNextCursor(response.next_cursor);
      } catch (err: unknown) {
        if (fetchId !== fetchIdRef.current) return;
        const message =
          err instanceof Error ? err.message : t('recherches.errors.loadFailed');
        setError(message);
        if (!opts.append) setItems([]);
      } finally {
        if (fetchId === fetchIdRef.current) {
          setLoading(false);
          setLoadingMore(false);
        }
      }
    },
    [sort, selectedPeriod, selectedPhilosopher, t]
  );

  // Reset & fetch when filters/sort change
  useEffect(() => {
    setCursor(null);
    fetchPage({ append: false, cursorParam: null });
  }, [sort, selectedPeriod, selectedPhilosopher, fetchPage]);

  // Infinite scroll via IntersectionObserver
  useEffect(() => {
    const node = sentinelRef.current;
    if (!node) return;
    if (!nextCursor) return;
    if (loading || loadingMore) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const target = entries[0];
        if (target?.isIntersecting && nextCursor) {
          setCursor(nextCursor);
          fetchPage({ append: true, cursorParam: nextCursor });
        }
      },
      { rootMargin: '300px 0px' }
    );

    observer.observe(node);
    return () => observer.disconnect();
  }, [nextCursor, loading, loadingMore, fetchPage]);

  // cursor state isn't directly used for rendering but kept for potential
  // explicit "Load more" button or analytics.
  void cursor;

  const isEmpty = !loading && !error && items.length === 0;

  return (
    <div className="min-h-screen w-full bg-transparent">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        {/* ── Hero ── */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
          className="pt-28 pb-8 text-center"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-stone-800/5 border border-stone-300/30 text-xs font-medium text-stone-500 tracking-wide uppercase mb-5">
            <BookOpenText className="w-3.5 h-3.5" aria-hidden="true" />
            {t('recherches.eyebrow')}
          </div>
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-display font-semibold text-stone-800 tracking-tight mb-3">
            {t('recherches.title')}
          </h1>
          <p className="text-base sm:text-lg text-stone-500 max-w-2xl mx-auto leading-relaxed">
            {t('recherches.subtitle')}
          </p>
        </motion.div>

        {/* ── Filter bar ── */}
        <div className="mb-8">
          <FilterBar
            sort={sort}
            onSortChange={setSort}
            periods={periods}
            philosophers={philosophers}
            selectedPeriod={selectedPeriod}
            selectedPhilosopher={selectedPhilosopher}
            onPeriodChange={setSelectedPeriod}
            onPhilosopherChange={setSelectedPhilosopher}
          />
        </div>

        {/* ── Content ── */}
        {error && (
          <div
            role="alert"
            className="mb-6 flex items-start gap-3 rounded-xl border border-red-200/60 bg-red-50/70 p-4 text-sm text-red-800"
          >
            <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" aria-hidden="true" />
            <div>
              <p className="font-medium">{t('recherches.errors.title')}</p>
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
            <BookOpenText className="mx-auto h-8 w-8 text-stone-300" aria-hidden="true" />
            <h2 className="mt-4 text-sm font-medium text-stone-700">
              {t('recherches.empty.title')}
            </h2>
            <p className="mt-1 text-xs text-stone-500">{t('recherches.empty.body')}</p>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 sm:gap-5">
              {items.map((item, index) => (
                <QueryCard key={item.slug} item={item} index={index} />
              ))}
            </div>

            {/* Sentinel for infinite scroll */}
            <div ref={sentinelRef} className="h-px w-full" aria-hidden="true" />

            {loadingMore && (
              <div className="flex justify-center py-8">
                <Loader2
                  className="h-5 w-5 animate-spin text-stone-400"
                  aria-label={t('recherches.loadingMore')}
                />
              </div>
            )}

            {!loadingMore && !nextCursor && items.length > 0 && (
              <p className="py-10 text-center text-[11px] uppercase tracking-wider text-stone-300">
                {t('recherches.endOfList')}
              </p>
            )}
          </>
        )}

        <div className="h-16" />
      </div>
    </div>
  );
}
