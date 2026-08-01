import { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { BookMarked, Loader2, AlertCircle } from 'lucide-react';
import {
  listCanonicalPassages,
  type CanonicalPassageItem,
} from '../../api/canonicalPassages';
import PassageCard from './PassageCard';
import { cn } from '../../lib/utils';

const DEFAULT_LIMIT = 50;

function CardSkeleton() {
  return (
    <div
      className="h-[230px] animate-pulse rounded-2xl border border-stone-200/50 bg-white/40 p-5"
      aria-hidden="true"
    >
      <div className="h-4 w-3/4 rounded bg-stone-200/60" />
      <div className="mt-2 h-3 w-1/2 rounded bg-stone-200/60" />
      <div className="mt-4 space-y-2">
        <div className="h-3 w-full rounded bg-stone-100" />
        <div className="h-3 w-11/12 rounded bg-stone-100" />
        <div className="h-3 w-9/12 rounded bg-stone-100" />
      </div>
      <div className="mt-6 flex justify-between border-t border-stone-100 pt-3">
        <div className="h-3 w-24 rounded bg-stone-100" />
        <div className="h-3 w-16 rounded bg-stone-100" />
      </div>
    </div>
  );
}

interface ChipOption {
  key: string;
  label: string;
}

function ChipGroup({
  label,
  options,
  selected,
  onSelect,
}: {
  label: string;
  options: ReadonlyArray<ChipOption>;
  selected: string | null;
  onSelect: (key: string | null) => void;
}) {
  if (options.length === 0) return null;
  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="text-[11px] font-medium uppercase tracking-wider text-stone-400">
        {label}
      </span>
      {options.map((option) => {
        const active = selected === option.key;
        return (
          <button
            key={option.key}
            type="button"
            onClick={() => onSelect(active ? null : option.key)}
            aria-pressed={active}
            className={cn(
              'rounded-full border px-3 py-1.5 sm:py-1 min-h-[44px] sm:min-h-0 text-xs font-medium transition-all',
              active
                ? 'border-amber-400/80 bg-amber-100/70 text-amber-900 shadow-sm'
                : 'border-stone-200/70 bg-white/60 text-stone-600 hover:border-amber-300/60 hover:bg-amber-50/60 hover:text-amber-800'
            )}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}

export default function CanonicalPassagesPage() {
  const { t } = useTranslation();
  const [items, setItems] = useState<CanonicalPassageItem[]>([]);
  const [total, setTotal] = useState(0);
  const [selectedPeriod, setSelectedPeriod] = useState<string | null>(null);
  const [selectedAuthor, setSelectedAuthor] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const periods = useMemo<ReadonlyArray<ChipOption>>(
    () => [
      { key: 'Presocratic', label: t('canonicalPassages.tags.period.presocratic') },
      { key: 'Classical', label: t('canonicalPassages.tags.period.classical') },
      { key: 'Hellenistic', label: t('canonicalPassages.tags.period.hellenistic') },
      { key: 'Imperial', label: t('canonicalPassages.tags.period.imperial') },
      { key: 'Late Antiquity', label: t('canonicalPassages.tags.period.lateAntique') },
    ],
    [t]
  );

  // Authors derived from the loaded set — a free-form selector would
  // overwhelm the chip row. Pick the top 6 distinct authors and let users
  // narrow.
  const authors = useMemo<ReadonlyArray<ChipOption>>(() => {
    const counts = new Map<string, number>();
    for (const item of items) {
      if (item.author) counts.set(item.author, (counts.get(item.author) ?? 0) + 1);
    }
    return Array.from(counts.entries())
      .sort(([, a], [, b]) => b - a)
      .slice(0, 6)
      .map(([author]) => ({ key: author, label: author }));
  }, [items]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await listCanonicalPassages({
        limit: DEFAULT_LIMIT,
        ...(selectedPeriod ? { period: selectedPeriod } : {}),
        ...(selectedAuthor ? { author: selectedAuthor } : {}),
      });
      setItems(response.items);
      setTotal(response.total);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : t('canonicalPassages.errors.loadFailed');
      setError(message);
      setItems([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [selectedPeriod, selectedAuthor, t]);

  useEffect(() => {
    void fetchData();
  }, [fetchData]);

  const isEmpty = !loading && !error && items.length === 0;

  return (
    <div className="min-h-screen w-full bg-transparent">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        {/* Hero */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
          className="pt-28 pb-8 text-center"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-stone-800/5 border border-stone-300/30 text-xs font-medium text-stone-500 tracking-wide uppercase mb-5">
            <BookMarked className="w-3.5 h-3.5" aria-hidden="true" />
            {t('canonicalPassages.eyebrow')}
          </div>
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-display font-semibold text-stone-800 tracking-tight mb-3">
            {t('canonicalPassages.title')}
          </h1>
          <p className="text-base sm:text-lg text-stone-500 max-w-2xl mx-auto leading-relaxed">
            {t('canonicalPassages.subtitle')}
          </p>
          {total > 0 && (
            <p className="mt-3 text-xs uppercase tracking-wider text-stone-400">
              {t('canonicalPassages.totalCount', { count: total })}
            </p>
          )}
        </motion.div>

        {/* Filters */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15, duration: 0.4 }}
          className="mb-8 space-y-4"
        >
          <ChipGroup
            label={t('canonicalPassages.filters.period')}
            options={periods}
            selected={selectedPeriod}
            onSelect={setSelectedPeriod}
          />
          {authors.length > 0 && (
            <ChipGroup
              label={t('canonicalPassages.filters.author')}
              options={authors}
              selected={selectedAuthor}
              onSelect={setSelectedAuthor}
            />
          )}
        </motion.div>

        {/* Content */}
        {error && (
          <div
            role="alert"
            className="mb-6 flex items-start gap-3 rounded-xl border border-red-200/60 bg-red-50/70 p-4 text-sm text-red-800"
          >
            <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" aria-hidden="true" />
            <div>
              <p className="font-medium">{t('canonicalPassages.errors.title')}</p>
              <p className="text-red-700/80">{error}</p>
            </div>
          </div>
        )}

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 sm:gap-5">
            {Array.from({ length: 6 }).map((_, i) => (
              <CardSkeleton key={i} />
            ))}
          </div>
        ) : isEmpty ? (
          <div className="rounded-2xl border border-stone-200/60 bg-white/50 p-12 text-center">
            <BookMarked className="mx-auto h-8 w-8 text-stone-300" aria-hidden="true" />
            <h2 className="mt-4 text-sm font-medium text-stone-700">
              {t('canonicalPassages.empty.title')}
            </h2>
            <p className="mt-1 text-xs text-stone-500">
              {t('canonicalPassages.empty.body')}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 sm:gap-5">
            {items.map((item, index) => (
              <PassageCard key={item.passage_id} item={item} index={index} />
            ))}
          </div>
        )}

        {loading && items.length > 0 && (
          <div className="flex justify-center py-8">
            <Loader2
              className="h-5 w-5 animate-spin text-stone-400"
              aria-label={t('canonicalPassages.loading')}
            />
          </div>
        )}

        <div className="h-16" />
      </div>
    </div>
  );
}
