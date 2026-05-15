import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { cn } from '../../lib/utils';
import type { ContributionStatus } from '../../api/contributions';

export type { ContributionStatus };

export type StatusFilterValue = ContributionStatus | 'all';

interface StatusFilterProps {
  value: StatusFilterValue;
  onChange: (value: StatusFilterValue) => void;
  counts?: Partial<Record<StatusFilterValue, number>>;
}

const ORDER: StatusFilterValue[] = [
  'all',
  'processing',
  'ready',
  'approved',
  'merged',
  'rejected',
];

const COLOR_BY_STATUS: Record<StatusFilterValue, string> = {
  all: 'border-stone-300/70 bg-white/60 text-stone-700 hover:border-amber-300/60 hover:bg-amber-50/60 hover:text-amber-800',
  uploaded:
    'border-blue-200/70 bg-blue-50/60 text-blue-800 hover:border-blue-300/70',
  processing:
    'border-blue-200/70 bg-blue-50/60 text-blue-800 hover:border-blue-300/70',
  ready: 'border-amber-200/70 bg-amber-50/60 text-amber-900 hover:border-amber-300/80',
  approved:
    'border-emerald-200/70 bg-emerald-50/60 text-emerald-800 hover:border-emerald-300/70',
  merged:
    'border-violet-200/70 bg-violet-50/60 text-violet-800 hover:border-violet-300/70',
  rejected: 'border-rose-200/70 bg-rose-50/60 text-rose-800 hover:border-rose-300/70',
  failed: 'border-red-200/70 bg-red-50/60 text-red-800 hover:border-red-300/70',
};

const ACTIVE_BY_STATUS: Record<StatusFilterValue, string> = {
  all: 'border-stone-500/70 bg-stone-800/90 text-white shadow-sm',
  uploaded: 'border-blue-500/80 bg-blue-600 text-white shadow-sm',
  processing: 'border-blue-500/80 bg-blue-600 text-white shadow-sm',
  ready: 'border-amber-500/80 bg-amber-500 text-white shadow-sm',
  approved: 'border-emerald-500/80 bg-emerald-600 text-white shadow-sm',
  merged: 'border-violet-500/80 bg-violet-600 text-white shadow-sm',
  rejected: 'border-rose-500/80 bg-rose-600 text-white shadow-sm',
  failed: 'border-red-500/80 bg-red-600 text-white shadow-sm',
};

export default function StatusFilter({ value, onChange, counts }: StatusFilterProps) {
  const { t } = useTranslation();

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.1 }}
      className="flex flex-wrap items-center gap-2"
      role="group"
      aria-label={t('contributions.filters.statusGroup')}
    >
      <span className="text-[11px] font-medium uppercase tracking-wider text-stone-400">
        {t('contributions.filters.status')}
      </span>
      {ORDER.map((status) => {
        const active = value === status;
        const count = counts?.[status];
        return (
          <button
            key={status}
            type="button"
            onClick={() => onChange(status)}
            aria-pressed={active}
            className={cn(
              'inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium transition-all',
              active ? ACTIVE_BY_STATUS[status] : COLOR_BY_STATUS[status]
            )}
          >
            {t(`contributions.status.${status}`)}
            {typeof count === 'number' && (
              <span
                className={cn(
                  'rounded-full px-1.5 py-px text-[10px] font-semibold',
                  active ? 'bg-white/20 text-white' : 'bg-stone-100 text-stone-600'
                )}
              >
                {count}
              </span>
            )}
          </button>
        );
      })}
    </motion.div>
  );
}
