import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { FileText, CalendarDays } from 'lucide-react';
import { cn } from '../../lib/utils';
import type {
  ContributionListItem,
  ContributionStatus,
} from '../../api/contributions';

// Re-export so the page can still `import { type ContributionListItem }
// from './ContributionCard'`. The canonical definition lives in api/.
export type { ContributionListItem };

interface ContributionCardProps {
  item: ContributionListItem;
  index: number;
}

const STATUS_CHIP: Record<ContributionStatus, string> = {
  uploaded: 'border-blue-300/70 bg-blue-50/80 text-blue-800',
  processing: 'border-blue-300/70 bg-blue-50/80 text-blue-800',
  ready: 'border-amber-300/70 bg-amber-50/80 text-amber-900',
  approved: 'border-emerald-300/70 bg-emerald-50/80 text-emerald-800',
  merged: 'border-violet-300/70 bg-violet-50/80 text-violet-800',
  rejected: 'border-rose-300/70 bg-rose-50/80 text-rose-800',
  failed: 'border-red-300/70 bg-red-50/80 text-red-800',
};

function relevanceBarColor(score: number): string {
  if (score >= 0.8) return 'bg-emerald-500';
  if (score >= 0.6) return 'bg-amber-500';
  if (score >= 0.4) return 'bg-orange-500';
  return 'bg-stone-400';
}

function formatDate(iso: string, locale: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return '';
  return new Intl.DateTimeFormat(locale, {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(date);
}

function formatAuthors(authors: string[], maxVisible = 2): string {
  if (authors.length === 0) return '';
  if (authors.length <= maxVisible) return authors.join(', ');
  return `${authors.slice(0, maxVisible).join(', ')} et al.`;
}

export default function ContributionCard({ item, index }: ContributionCardProps) {
  const { t, i18n } = useTranslation();
  const date = formatDate(item.submitted_at, i18n.language);
  const visibleConcepts = item.free_will_concepts.slice(0, 4);
  const hiddenConceptCount = Math.max(
    0,
    item.free_will_concepts.length - visibleConcepts.length
  );
  const relevancePct =
    typeof item.relevance_score === 'number'
      ? Math.max(0, Math.min(1, item.relevance_score)) * 100
      : null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        duration: 0.4,
        delay: Math.min(index, 8) * 0.04,
        ease: [0.22, 1, 0.36, 1],
      }}
    >
      <Link
        to={`/contributions/${encodeURIComponent(item.contribution_id)}`}
        className={cn(
          'group block h-full rounded-2xl border border-stone-200/60 bg-white/65 backdrop-blur-sm p-5',
          'transition-all duration-300',
          'hover:-translate-y-0.5 hover:border-amber-300/70 hover:shadow-[0_6px_24px_-12px_rgba(180,83,9,0.25)]',
          'focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-400/60 focus-visible:ring-offset-2 focus-visible:ring-offset-parchment-50'
        )}
        aria-label={item.title ?? undefined}
      >
        <div className="mb-3 flex items-center justify-between gap-2">
          <span
            className={cn(
              'inline-flex items-center rounded-full border px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide',
              STATUS_CHIP[item.status]
            )}
          >
            {t(`contributions.status.${item.status}`)}
          </span>
          {relevancePct !== null && (
            <span className="text-[10px] font-medium text-stone-500">
              {t('contributions.card.relevance', {
                value: relevancePct.toFixed(0),
              })}
            </span>
          )}
        </div>

        {relevancePct !== null && (
          <div
            className="mb-3 h-1.5 w-full overflow-hidden rounded-full bg-stone-100"
            role="progressbar"
            aria-valuenow={Math.round(relevancePct)}
            aria-valuemin={0}
            aria-valuemax={100}
          >
            <div
              className={cn(
                'h-full rounded-full transition-all',
                relevanceBarColor(relevancePct / 100)
              )}
              style={{ width: `${relevancePct}%` }}
            />
          </div>
        )}

        <h3 className="text-[15px] font-display font-semibold text-stone-800 leading-snug line-clamp-2 group-hover:text-amber-900 transition-colors">
          {item.title}
        </h3>

        <p className="mt-1 text-xs text-stone-500">
          {formatAuthors(item.authors)}
          {item.publication_year ? ` · ${item.publication_year}` : ''}
        </p>

        {visibleConcepts.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1.5">
            {visibleConcepts.map((concept) => (
              <span
                key={concept}
                className="inline-flex items-center rounded-full bg-amber-50/70 px-2 py-0.5 text-[10px] font-medium text-amber-800 border border-amber-200/60"
              >
                {concept}
              </span>
            ))}
            {hiddenConceptCount > 0 && (
              <span className="inline-flex items-center rounded-full bg-stone-100/70 px-2 py-0.5 text-[10px] font-medium text-stone-500 border border-stone-200/60">
                +{hiddenConceptCount}
              </span>
            )}
          </div>
        )}

        <div className="mt-4 flex items-center justify-between gap-3 border-t border-stone-100 pt-3">
          <span
            className="inline-flex items-center gap-1.5 text-[11px] text-stone-500"
            title={t('contributions.card.proposalsTooltip')}
          >
            <FileText className="h-3.5 w-3.5 text-amber-700/70" aria-hidden="true" />
            <strong className="font-semibold text-stone-700">
              {item.proposal_count}
            </strong>
            <span>{t('contributions.card.proposals', { count: item.proposal_count })}</span>
          </span>
          {date && (
            <span className="inline-flex items-center gap-1 text-[11px] font-medium text-stone-400">
              <CalendarDays className="h-3 w-3" aria-hidden="true" />
              <time dateTime={item.submitted_at}>{date}</time>
            </span>
          )}
        </div>
      </Link>
    </motion.div>
  );
}
