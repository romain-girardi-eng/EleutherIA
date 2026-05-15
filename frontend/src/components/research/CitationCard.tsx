import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  BookOpen,
  CheckCircle2,
  XCircle,
  HelpCircle,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { cn } from '../../lib/utils';
import type { CitationEntry } from '../../hooks/useResearchStream';

interface Props {
  citation: CitationEntry;
  /** Index within the live citation feed; used for the [Source N] badge. */
  index: number;
  /** Called when the user clicks the card to inspect the full passage. */
  onOpenPassage?: (passageId: string) => void;
}

function confidenceTone(confidence: number): {
  bar: string;
  badge: string;
  label: string;
} {
  if (confidence >= 0.8) {
    return { bar: 'bg-emerald-400', badge: 'bg-emerald-50 text-emerald-700', label: 'high' };
  }
  if (confidence >= 0.5) {
    return { bar: 'bg-amber-400', badge: 'bg-amber-50 text-amber-700', label: 'medium' };
  }
  return { bar: 'bg-stone-400', badge: 'bg-stone-100 text-stone-600', label: 'low' };
}

export function CitationCard({ citation, index, onOpenPassage }: Props) {
  const { t } = useTranslation();
  const [expanded, setExpanded] = useState(false);
  const tone = confidenceTone(citation.confidence);
  const VerifIcon =
    citation.verified === true
      ? CheckCircle2
      : citation.verified === false
      ? XCircle
      : HelpCircle;
  const verifTone =
    citation.verified === true
      ? 'text-emerald-600'
      : citation.verified === false
      ? 'text-rose-500'
      : 'text-stone-400';

  const previewClamp = expanded ? '' : 'line-clamp-3';

  return (
    <motion.article
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      role={onOpenPassage ? 'button' : undefined}
      tabIndex={onOpenPassage ? 0 : undefined}
      onClick={() => onOpenPassage?.(citation.passage_id)}
      onKeyDown={(e) => {
        if (onOpenPassage && (e.key === 'Enter' || e.key === ' ')) {
          e.preventDefault();
          onOpenPassage(citation.passage_id);
        }
      }}
      className={cn(
        'rounded-2xl border border-stone-200/70 bg-white/80 px-3 py-2 shadow-sm',
        onOpenPassage
          ? 'cursor-pointer hover:border-amber-300 hover:bg-amber-50/40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-400'
          : 'hover:border-amber-200',
      )}
    >
      <header className="flex items-center gap-2">
        <span className="rounded-full bg-amber-50 px-1.5 py-0.5 font-mono text-[10px] font-semibold text-amber-700">
          [{t('research.citations.sourcePrefix')} {index + 1}]
        </span>
        <VerifIcon
          className={cn('h-3.5 w-3.5', verifTone)}
          aria-label={
            citation.verified === true
              ? t('research.citations.verified')
              : citation.verified === false
              ? t('research.citations.refuted')
              : t('research.citations.pending')
          }
        />
        <span
          className={cn(
            'rounded-full px-1.5 py-0.5 text-[10px] font-medium',
            tone.badge,
          )}
          title={`${(citation.confidence * 100).toFixed(0)}%`}
        >
          {t(`research.citations.confidence.${tone.label}`)}
        </span>
      </header>

      <div className="mt-1.5 flex items-center gap-1.5">
        <BookOpen className="h-3 w-3 text-stone-400" aria-hidden="true" />
        <p className="truncate text-[12px] font-medium text-stone-700">
          {citation.work_label ?? citation.passage_id}
        </p>
      </div>

      {citation.cts_urn && (
        <p className="mt-0.5 truncate font-mono text-[10px] text-stone-400">
          {citation.cts_urn}
        </p>
      )}

      <p
        className={cn(
          'mt-1.5 text-[12px] leading-5 text-stone-700',
          previewClamp,
        )}
      >
        {citation.excerpt}
      </p>

      <footer className="mt-1.5 flex items-center justify-between">
        <div
          className="h-1 flex-1 overflow-hidden rounded-full bg-stone-100"
          role="progressbar"
          aria-valuenow={Math.round(citation.confidence * 100)}
          aria-valuemin={0}
          aria-valuemax={100}
        >
          <div
            className={cn('h-full rounded-full transition-all', tone.bar)}
            ref={(el) => {
              if (el) el.style.width = `${Math.round(citation.confidence * 100)}%`;
            }}
          />
        </div>
        <button
          type="button"
          onClick={() => setExpanded((v) => !v)}
          className="ml-2 inline-flex items-center gap-0.5 text-[11px] text-stone-500 hover:text-stone-700"
          aria-expanded={expanded}
        >
          {expanded
            ? t('research.citations.collapse')
            : t('research.citations.expand')}
          {expanded ? (
            <ChevronUp className="h-3 w-3" aria-hidden="true" />
          ) : (
            <ChevronDown className="h-3 w-3" aria-hidden="true" />
          )}
        </button>
      </footer>
    </motion.article>
  );
}

export default CitationCard;
