import { motion } from 'framer-motion';
import { ArrowUpRight, X, Quote } from 'lucide-react';
import { getGraphTypeTheme, formatGraphNodeType } from './graphTheme';
import type { SourceCitation } from '../../types';

interface NodeDetailCardProps {
  source: SourceCitation;
  citationText?: { original: string; originalLanguage: string; translation: string };
  onClose: () => void;
  onOpenInDatabase: () => void;
}

function formatConfidence(confidence?: number) {
  if (confidence === undefined || Number.isNaN(confidence)) {
    return null;
  }
  const normalized = confidence <= 1 ? confidence * 100 : confidence;
  return `${Math.round(normalized)}%`;
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-stone-400">
      {children}
    </p>
  );
}

export default function NodeDetailCard({
  source,
  citationText,
  onClose,
  onOpenInDatabase,
}: NodeDetailCardProps) {
  const theme = getGraphTypeTheme(source.nodeType);
  const confidence = formatConfidence(source.metadata?.confidence);

  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -14 }}
      transition={{ duration: 0.22, ease: 'easeOut' }}
      className="flex flex-col overflow-hidden rounded-[22px] border border-stone-200/80 bg-white/92 shadow-[0_20px_60px_-36px_rgba(120,53,15,0.35)] backdrop-blur-xl"
    >
      {/* Header */}
      <div
        className="relative overflow-hidden border-b border-stone-200/70 px-4 py-3"
        style={{
          background: `linear-gradient(135deg, ${theme.tint}, rgba(255,255,255,0.96) 58%, rgba(252,249,244,0.92) 100%)`,
        }}
      >
        <div className="absolute -right-6 -top-6 h-20 w-20 rounded-full blur-2xl" style={{ backgroundColor: `${theme.color}22` }} />
        <div className="relative flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <span
                className="inline-flex items-center rounded-full border px-2.5 py-1 text-[11px] font-semibold"
                style={{
                  borderColor: theme.border,
                  backgroundColor: theme.tint,
                  color: theme.text,
                }}
              >
                {formatGraphNodeType(source.nodeType)}
              </span>
              {confidence && (
                <span className="inline-flex items-center rounded-full border border-amber-200/80 bg-amber-50/90 px-2.5 py-1 text-[11px] font-medium text-amber-800">
                  {confidence} confidence
                </span>
              )}
            </div>
            <h3 className="mt-2 font-display text-lg leading-tight text-stone-900">
              {source.nodeLabel}
            </h3>
            {(source.metadata?.period || source.metadata?.school) && (
              <div className="mt-1.5 flex flex-wrap items-center gap-1.5 text-xs text-stone-500">
                {source.metadata?.period && (
                  <span className="rounded-full border border-stone-200/80 bg-white/70 px-2 py-0.5">
                    {source.metadata.period}
                  </span>
                )}
                {source.metadata?.school && (
                  <span className="rounded-full border border-stone-200/80 bg-white/70 px-2 py-0.5 italic">
                    {source.metadata.school as string}
                  </span>
                )}
              </div>
            )}
          </div>

          <button
            onClick={onClose}
            className="shrink-0 rounded-xl border border-white/70 bg-white/88 p-1.5 text-stone-500 shadow-sm transition-colors hover:text-stone-900"
            aria-label="Close"
            type="button"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto px-4 py-3">
        <div className="space-y-3">
          {/* Why this source */}
          <div className="rounded-[18px] border border-stone-200/70 bg-[linear-gradient(180deg,rgba(252,249,244,0.95),rgba(255,255,255,0.98))] p-3">
            <SectionLabel>Why this source</SectionLabel>
            <p className="mt-1.5 text-sm leading-6 text-stone-600">
              {source.content || 'No additional context available.'}
            </p>
          </div>

          {/* Original text */}
          {citationText?.original && (
            <div className="rounded-[18px] border border-stone-200/70 bg-white/92 p-3 shadow-[0_12px_30px_-28px_rgba(120,53,15,0.25)]">
              <SectionLabel>
                {citationText.originalLanguage === 'greek'
                  ? 'Greek Text'
                  : citationText.originalLanguage === 'latin'
                    ? 'Latin Text'
                    : 'Original Text'}
              </SectionLabel>
              <div className="mt-2 flex gap-2.5">
                <div
                  className="mt-0.5 h-8 w-1 rounded-full"
                  style={{ backgroundColor: theme.color }}
                />
                <p className="font-ancient text-sm italic leading-7 text-stone-800">
                  {citationText.original}
                </p>
              </div>
            </div>
          )}

          {/* Translation */}
          {citationText?.translation && (
            <div className="rounded-[18px] border border-stone-200/70 bg-parchment-50/72 p-3">
              <SectionLabel>Translation</SectionLabel>
              <div className="mt-2 flex gap-2.5">
                <Quote className="mt-0.5 h-3.5 w-3.5 shrink-0 text-stone-400" />
                <p className="text-sm leading-6 text-stone-700">
                  {citationText.translation}
                </p>
              </div>
            </div>
          )}

          {/* No passage available */}
          {!citationText?.original && !citationText?.translation && (
            <div className="rounded-[18px] border border-dashed border-stone-300 bg-stone-50/80 p-3 text-sm text-stone-500">
              Passage text not yet available.
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between border-t border-stone-200/70 bg-[linear-gradient(180deg,rgba(255,255,255,0.92),rgba(252,249,244,0.92))] px-4 py-2.5">
        <span className="text-[10px] text-stone-400">
          {source.nodeId}
        </span>
        <button
          onClick={onOpenInDatabase}
          className="inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-semibold transition-colors"
          style={{
            borderColor: theme.border,
            backgroundColor: theme.tint,
            color: theme.text,
          }}
          type="button"
        >
          View in database
          <ArrowUpRight className="h-3.5 w-3.5" />
        </button>
      </div>
    </motion.div>
  );
}
