import { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { X, ChevronUp, ChevronDown, BookOpen, ExternalLink } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { cn } from '../../utils/cn';
import type { PassageContext } from '../../types/graphrag';

interface PassageReaderPanelProps {
  passageContext: PassageContext;
  onClose: () => void;
  onLoadMore: (direction: 'up' | 'down') => void;
  loading?: boolean;
}

export default function PassageReaderPanel({
  passageContext,
  onClose,
  onLoadMore,
  loading = false,
}: PassageReaderPanelProps) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const targetRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  const { target, passages, workId, totalPassagesInWork } = passageContext;

  // Auto-scroll to target passage on mount
  useEffect(() => {
    const timer = setTimeout(() => {
      targetRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 100);
    return () => clearTimeout(timer);
  }, [target.passageId]);

  // Language badge color
  const langBadge = target.language === 'lat'
    ? 'bg-red-50 text-red-700 border-red-200'
    : 'bg-blue-50 text-blue-700 border-blue-200';

  const langLabel = target.language === 'lat' ? t('graphRagUi.passageReader.language.latin') : t('graphRagUi.passageReader.language.greek');

  // Reference range for the header
  const firstRef = passages[0]?.canonicalRef || '';
  const lastRef = passages[passages.length - 1]?.canonicalRef || '';
  const rangeLabel = firstRef === lastRef ? firstRef : `${firstRef} — ${lastRef}`;

  // Check if we can load more in each direction
  const firstSeq = passages[0]?.sequenceNumber ?? 0;
  const lastSeq = passages[passages.length - 1]?.sequenceNumber ?? 0;
  const canLoadUp = firstSeq > 1;
  const canLoadDown = lastSeq < totalPassagesInWork - 1;

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      transition={{ duration: 0.25 }}
      className="flex flex-col h-full bg-parchment-50 text-stone-800"
    >
      {/* Sticky Header */}
      <div className="shrink-0 px-4 py-3 border-b border-amber-200/40 bg-parchment-100">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 mb-1">
              <BookOpen className="w-4 h-4 text-orange-500 shrink-0" />
              <span className="text-sm font-semibold text-stone-800 truncate">
                {target.author}
              </span>
              <span className={cn(
                'inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium border shrink-0',
                langBadge
              )}>
                {langLabel}
              </span>
            </div>
            <p className="text-xs text-stone-600 truncate">{target.workTitle}</p>
            <p className="text-[10px] text-stone-400 mt-0.5 font-mono">{rangeLabel}</p>
          </div>
          <button
            onClick={onClose}
            className="shrink-0 p-1.5 rounded-lg hover:bg-stone-100 text-stone-400 hover:text-stone-600 transition-colors"
            aria-label={t('graphRagUi.passageReader.close')}
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Scrollable Passage Body */}
      <div ref={scrollContainerRef} className="flex-1 overflow-y-auto">
        {/* Load more above */}
        {canLoadUp && (
          <div className="flex justify-center py-3">
            <button
              onClick={() => onLoadMore('up')}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-medium text-stone-400 hover:text-stone-600 bg-amber-50 hover:bg-amber-100/50 rounded-lg transition-colors disabled:opacity-30"
          >
            <ChevronUp className="w-3.5 h-3.5" />
            {t('graphRagUi.passageReader.loadEarlier')}
          </button>
        </div>
        )}

        {/* Passages list */}
        <div className="px-4 py-2 space-y-1">
          {passages.map((passage) => {
            const isTarget = passage.isTarget;
            const isGreek = passage.language === 'grc';
            return (
              <div
                key={passage.passageId}
                ref={isTarget ? targetRef : undefined}
                className={cn(
                  'rounded-lg px-4 py-3 transition-colors',
                  isTarget
                    ? 'bg-amber-100/40 border-l-4 border-amber-600'
                    : 'bg-transparent hover:bg-amber-50/50 border-l-2 border-transparent'
                )}
              >
                {/* Reference badge */}
                <div className="flex items-center gap-2 mb-1.5">
                  <span className={cn(
                    'inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono',
                    isTarget
                      ? 'bg-amber-100 text-amber-700'
                      : 'bg-stone-100 text-stone-400'
                  )}>
                    {passage.canonicalRef}
                  </span>
                  {isTarget && (
                    <span className="text-[10px] font-medium text-amber-600 uppercase tracking-wider">
                      {t('graphRagUi.passageReader.cited')}
                    </span>
                  )}
                </div>

                {/* Passage text */}
                <p className={cn(
                  'leading-relaxed text-[13px]',
                  isGreek ? 'font-serif italic' : 'font-serif',
                  isTarget ? 'text-stone-800' : 'text-stone-600'
                )}>
                  {passage.textContent}
                </p>
              </div>
            );
          })}
        </div>

        {/* Load more below */}
        {canLoadDown && (
          <div className="flex justify-center py-3">
            <button
              onClick={() => onLoadMore('down')}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-medium text-stone-400 hover:text-stone-600 bg-amber-50 hover:bg-amber-100/50 rounded-lg transition-colors disabled:opacity-30"
          >
            <ChevronDown className="w-3.5 h-3.5" />
            {t('graphRagUi.passageReader.loadLater')}
          </button>
        </div>
        )}
      </div>

      {/* Sticky Footer */}
      <div className="shrink-0 px-4 py-2.5 border-t border-amber-200/40 bg-parchment-100 flex items-center justify-between">
        <span className="text-[10px] text-stone-400">
          {t('graphRagUi.passageReader.passageCount', { count: passages.length, total: totalPassagesInWork })}
        </span>
        <button
          onClick={() => navigate(`/texts?work=${workId}&passage=${target.passageId}`)}
          className="flex items-center gap-1 text-[11px] font-medium text-orange-600 hover:text-orange-700 transition-colors"
        >
          {t('graphRagUi.passageReader.viewInTextReader')}
          <ExternalLink className="w-3 h-3" />
        </button>
      </div>
    </motion.div>
  );
}
