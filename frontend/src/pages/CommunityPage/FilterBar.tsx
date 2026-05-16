import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { Flame, Clock } from 'lucide-react';
import { cn } from '../../lib/utils';

export type CommunitySort = 'recent' | 'popular';

interface FilterBarProps {
  sort: CommunitySort;
  onSortChange: (sort: CommunitySort) => void;

  periods: ReadonlyArray<{ key: string; label: string }>;
  philosophers: ReadonlyArray<{ key: string; label: string }>;

  selectedPeriod: string | null;
  selectedPhilosopher: string | null;
  onPeriodChange: (period: string | null) => void;
  onPhilosopherChange: (philosopher: string | null) => void;
}

function ChipGroup({
  label,
  options,
  selected,
  onSelect,
}: {
  label: string;
  options: ReadonlyArray<{ key: string; label: string }>;
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
              'rounded-full border px-3 py-1.5 sm:py-1 min-h-[36px] sm:min-h-0 text-xs font-medium transition-all',
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

export default function FilterBar({
  sort,
  onSortChange,
  periods,
  philosophers,
  selectedPeriod,
  selectedPhilosopher,
  onPeriodChange,
  onPhilosopherChange,
}: FilterBarProps) {
  const { t } = useTranslation();

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.15, duration: 0.4 }}
      className="space-y-4"
    >
      {/* Sort toggle */}
      <div
        className="inline-flex rounded-full border border-stone-200/70 bg-white/60 p-1 backdrop-blur-sm shadow-sm"
        role="group"
        aria-label={t('recherches.filters.sort')}
      >
        <button
          type="button"
          onClick={() => onSortChange('recent')}
          aria-pressed={sort === 'recent'}
          className={cn(
            'inline-flex items-center gap-1.5 rounded-full px-4 py-1.5 text-xs font-medium transition-colors',
            sort === 'recent'
              ? 'bg-amber-100/80 text-amber-900'
              : 'text-stone-500 hover:text-stone-700'
          )}
        >
          <Clock className="h-3.5 w-3.5" aria-hidden="true" />
          {t('recherches.filters.recent')}
        </button>
        <button
          type="button"
          onClick={() => onSortChange('popular')}
          aria-pressed={sort === 'popular'}
          className={cn(
            'inline-flex items-center gap-1.5 rounded-full px-4 py-1.5 text-xs font-medium transition-colors',
            sort === 'popular'
              ? 'bg-amber-100/80 text-amber-900'
              : 'text-stone-500 hover:text-stone-700'
          )}
        >
          <Flame className="h-3.5 w-3.5" aria-hidden="true" />
          {t('recherches.filters.popular')}
        </button>
      </div>

      {/* Tag groups */}
      <ChipGroup
        label={t('recherches.filters.period')}
        options={periods}
        selected={selectedPeriod}
        onSelect={onPeriodChange}
      />
      <ChipGroup
        label={t('recherches.filters.philosopher')}
        options={philosophers}
        selected={selectedPhilosopher}
        onSelect={onPhilosopherChange}
      />
    </motion.div>
  );
}
