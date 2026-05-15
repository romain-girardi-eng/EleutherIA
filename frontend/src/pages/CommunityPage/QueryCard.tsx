import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { ScrollText, Sparkles, MessageSquareQuote } from 'lucide-react';
import { cn } from '../../lib/utils';
import type { CommunityListItem } from '../../api/community';

interface QueryCardProps {
  item: CommunityListItem;
  index: number;
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

export default function QueryCard({ item, index }: QueryCardProps) {
  const { t, i18n } = useTranslation();
  const date = formatDate(item.created_at, i18n.language);
  const visibleTags = item.topic_tags.slice(0, 3);
  const hiddenTagCount = Math.max(0, item.topic_tags.length - visibleTags.length);

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: Math.min(index, 8) * 0.04, ease: [0.22, 1, 0.36, 1] }}
    >
      <Link
        to={`/recherches/${encodeURIComponent(item.slug)}`}
        className={cn(
          'group block h-full rounded-2xl border border-stone-200/60 bg-white/65 backdrop-blur-sm p-5',
          'transition-all duration-300',
          'hover:-translate-y-0.5 hover:border-amber-300/70 hover:shadow-[0_6px_24px_-12px_rgba(180,83,9,0.25)]',
          'focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-400/60 focus-visible:ring-offset-2 focus-visible:ring-offset-parchment-50'
        )}
        aria-label={item.query}
      >
        {/* Tag row */}
        {visibleTags.length > 0 && (
          <div className="mb-3 flex flex-wrap items-center gap-1.5">
            {visibleTags.map((tag) => (
              <span
                key={tag}
                className="inline-flex items-center rounded-full bg-amber-50/70 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-amber-800 border border-amber-200/60"
              >
                {tag}
              </span>
            ))}
            {hiddenTagCount > 0 && (
              <span className="inline-flex items-center rounded-full bg-stone-100/70 px-2 py-0.5 text-[10px] font-medium text-stone-500 border border-stone-200/60">
                +{hiddenTagCount}
              </span>
            )}
          </div>
        )}

        {/* Question */}
        <h3 className="text-[15px] font-display font-semibold text-stone-800 leading-snug line-clamp-2 group-hover:text-amber-900 transition-colors">
          {item.query}
        </h3>

        {/* Excerpt */}
        <p className="mt-2 text-sm text-stone-500 leading-relaxed line-clamp-3">
          {item.excerpt}
        </p>

        {/* Footer meta */}
        <div className="mt-4 flex items-center justify-between gap-3 border-t border-stone-100 pt-3">
          <div className="flex items-center gap-3 text-[11px] text-stone-500">
            <span className="inline-flex items-center gap-1" title={t('recherches.card.citations')}>
              <ScrollText className="h-3.5 w-3.5 text-amber-700/70" aria-hidden="true" />
              <strong className="font-semibold text-stone-700">{item.citation_count}</strong>
            </span>
            <span className="inline-flex items-center gap-1" title={t('recherches.card.sections')}>
              <Sparkles className="h-3.5 w-3.5 text-amber-700/70" aria-hidden="true" />
              <strong className="font-semibold text-stone-700">{item.section_count}</strong>
            </span>
            <span className="inline-flex items-center gap-1" title={t('recherches.card.quotes')}>
              <MessageSquareQuote className="h-3.5 w-3.5 text-amber-700/70" aria-hidden="true" />
              <strong className="font-semibold text-stone-700">{item.quote_count}</strong>
            </span>
          </div>
          {date && (
            <time
              dateTime={item.created_at}
              className="text-[11px] font-medium text-stone-400"
            >
              {date}
            </time>
          )}
        </div>
      </Link>
    </motion.div>
  );
}
