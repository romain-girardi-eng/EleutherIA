import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { ScrollText } from 'lucide-react';
import { cn } from '../../lib/utils';
import type { CanonicalPassageItem } from '../../api/canonicalPassages';

interface PassageCardProps {
  item: CanonicalPassageItem;
  index: number;
}

function languageAccent(language: string | null): {
  border: string;
  dot: string;
  label: string;
} {
  switch (language) {
    case 'grc':
      return {
        border: 'border-l-blue-400/70',
        dot: 'bg-blue-400/80',
        label: 'GRC',
      };
    case 'lat':
      return {
        border: 'border-l-red-400/70',
        dot: 'bg-red-400/80',
        label: 'LAT',
      };
    case 'hbo':
      return {
        border: 'border-l-emerald-400/70',
        dot: 'bg-emerald-400/80',
        label: 'HBO',
      };
    default:
      return {
        border: 'border-l-stone-300',
        dot: 'bg-stone-300',
        label: (language ?? 'ENG').toUpperCase(),
      };
  }
}

function slugColor(slug: string): string {
  let hash = 0;
  for (let i = 0; i < slug.length; i += 1) {
    hash = (hash * 31 + slug.charCodeAt(i)) % 360;
  }
  const hue = Math.abs(hash) % 360;
  // Tailwind-safe hue rotation through inline class fallback won't work
  // (rule above bans inline styles). Map hue to a discrete palette instead.
  if (hue < 60) return 'bg-amber-300';
  if (hue < 120) return 'bg-lime-300';
  if (hue < 180) return 'bg-emerald-300';
  if (hue < 240) return 'bg-sky-300';
  if (hue < 300) return 'bg-violet-300';
  return 'bg-rose-300';
}

export default function PassageCard({ item, index }: PassageCardProps) {
  const { t } = useTranslation();
  const accent = languageAccent(item.language);
  const refLabel = item.canonical_ref ?? item.label;
  const subtitle = [item.author, item.work_title].filter(Boolean).join(' — ');

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
        to={`/passages-canoniques/${encodeURIComponent(item.passage_id)}`}
        className={cn(
          'group block h-full rounded-2xl border border-stone-200/60 bg-white/65 backdrop-blur-sm p-5',
          'border-l-4',
          accent.border,
          'transition-all duration-300',
          'hover:-translate-y-0.5 hover:border-amber-300/70 hover:shadow-[0_6px_24px_-12px_rgba(180,83,9,0.25)]',
          'focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-400/60 focus-visible:ring-offset-2 focus-visible:ring-offset-parchment-50'
        )}
        aria-label={refLabel}
      >
        {/* Reference */}
        <div className="flex items-start justify-between gap-2">
          <h3 className="text-[15px] font-display font-semibold text-stone-800 leading-snug group-hover:text-amber-900 transition-colors">
            {refLabel}
          </h3>
          <span className="shrink-0 rounded-full bg-stone-100/80 px-1.5 py-0.5 text-[9px] font-mono text-stone-500">
            {accent.label}
          </span>
        </div>

        {/* Author + work */}
        {subtitle && (
          <p className="mt-1 text-xs text-stone-500 italic">{subtitle}</p>
        )}

        {/* Excerpt — serif italic, language-tinted left border */}
        {item.preview_text && (
          <p className="mt-3 whitespace-pre-wrap font-serif text-sm italic leading-relaxed text-stone-700 line-clamp-4">
            {item.preview_text}
          </p>
        )}

        {/* Footer */}
        <div className="mt-4 flex items-center justify-between gap-3 border-t border-stone-100 pt-3">
          <span
            className="inline-flex items-center gap-1.5 rounded-full bg-amber-50/70 px-2.5 py-1 text-[11px] font-medium text-amber-900 border border-amber-200/60"
            title={t('canonicalPassages.card.citedIn', {
              count: item.distinct_answer_count,
            })}
          >
            <ScrollText className="h-3 w-3 text-amber-700" aria-hidden="true" />
            {t('canonicalPassages.card.citedIn', {
              count: item.distinct_answer_count,
            })}
          </span>

          <div className="flex items-center gap-2">
            {item.period && (
              <span className="rounded-full bg-stone-100/70 px-2 py-0.5 text-[10px] font-medium text-stone-600 border border-stone-200/60">
                {item.period}
              </span>
            )}
            {item.preview_slugs.slice(0, 3).map((slug) => (
              <span
                key={slug}
                className={cn('h-2 w-2 rounded-full', slugColor(slug))}
                title={slug}
                aria-label={slug}
              />
            ))}
          </div>
        </div>
      </Link>
    </motion.div>
  );
}
