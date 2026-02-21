import { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
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
    ? 'bg-red-900/30 text-red-300 border-red-700/30'
    : 'bg-blue-900/30 text-blue-300 border-blue-700/30';

  const langLabel = target.language === 'lat' ? 'Latin' : 'Greek';

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
      className="flex flex-col h-full bg-[#020617] text-white"
    >
      {/* Sticky Header */}
      <div className="shrink-0 px-4 py-3 border-b border-white/10 bg-[#0a1128]">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 mb-1">
              <BookOpen className="w-4 h-4 text-amber-400 shrink-0" />
              <span className="text-sm font-semibold text-white/90 truncate">
                {target.author}
              </span>
              <span className={cn(
                'inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium border shrink-0',
                langBadge
              )}>
                {langLabel}
              </span>
            </div>
            <p className="text-xs text-white/50 truncate">{target.workTitle}</p>
            <p className="text-[10px] text-white/30 mt-0.5 font-mono">{rangeLabel}</p>
          </div>
          <button
            onClick={onClose}
            className="shrink-0 p-1.5 rounded-lg hover:bg-white/10 text-white/40 hover:text-white/70 transition-colors"
            aria-label="Close passage reader"
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
              className="flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-medium text-white/40 hover:text-white/70 bg-white/5 hover:bg-white/10 rounded-lg transition-colors disabled:opacity-30"
            >
              <ChevronUp className="w-3.5 h-3.5" />
              Load earlier passages
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
                    ? 'bg-amber-500/10 border-l-2 border-amber-400'
                    : 'bg-transparent hover:bg-white/[0.03] border-l-2 border-transparent'
                )}
              >
                {/* Reference badge */}
                <div className="flex items-center gap-2 mb-1.5">
                  <span className={cn(
                    'inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono',
                    isTarget
                      ? 'bg-amber-400/20 text-amber-300'
                      : 'bg-white/5 text-white/30'
                  )}>
                    {passage.canonicalRef}
                  </span>
                  {isTarget && (
                    <span className="text-[10px] font-medium text-amber-400/70 uppercase tracking-wider">
                      cited
                    </span>
                  )}
                </div>

                {/* Passage text */}
                <p className={cn(
                  'leading-relaxed text-[13px]',
                  isGreek ? 'font-serif italic' : 'font-serif',
                  isTarget ? 'text-white/90' : 'text-white/60'
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
              className="flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-medium text-white/40 hover:text-white/70 bg-white/5 hover:bg-white/10 rounded-lg transition-colors disabled:opacity-30"
            >
              <ChevronDown className="w-3.5 h-3.5" />
              Load later passages
            </button>
          </div>
        )}
      </div>

      {/* Sticky Footer */}
      <div className="shrink-0 px-4 py-2.5 border-t border-white/10 bg-[#0a1128] flex items-center justify-between">
        <span className="text-[10px] text-white/30">
          {passages.length} of {totalPassagesInWork} passages
        </span>
        <button
          onClick={() => navigate(`/texts?work=${workId}&passage=${target.passageId}`)}
          className="flex items-center gap-1 text-[11px] font-medium text-amber-400/70 hover:text-amber-400 transition-colors"
        >
          View in text reader
          <ExternalLink className="w-3 h-3" />
        </button>
      </div>
    </motion.div>
  );
}
