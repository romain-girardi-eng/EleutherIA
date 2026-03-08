import { motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { ArrowUpRight, ChevronLeft, ChevronRight, Quote, X } from 'lucide-react';
import { cn } from '../../utils/cn';
import type { SourceCitation } from '../../types';
import { formatGraphNodeType, getGraphTypeTheme } from './graphTheme';

interface SourceDetailCardProps {
  source: SourceCitation;
  citationText?: { original: string; originalLanguage: string; translation: string };
  citationIndex: number;
  totalCitations: number;
  onClose: () => void;
  onPrev: () => void;
  onNext: () => void;
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

export default function SourceDetailCard({
  source,
  citationText,
  citationIndex,
  totalCitations,
  onClose,
  onPrev,
  onNext,
}: SourceDetailCardProps) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const theme = getGraphTypeTheme(source.nodeType);
  const confidence = formatConfidence(source.metadata?.confidence);

  return (
    <motion.div
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -18 }}
      transition={{ duration: 0.24, ease: 'easeOut' }}
      className="flex h-full min-h-0 flex-col overflow-hidden rounded-[26px] border border-stone-200/80 bg-white/88 shadow-[0_30px_80px_-46px_rgba(120,53,15,0.4)] backdrop-blur-xl"
    >
      <div
        className="relative overflow-hidden border-b border-stone-200/70 px-5 py-4"
        style={{
          background: `linear-gradient(135deg, ${theme.tint}, rgba(255,255,255,0.96) 58%, rgba(252,249,244,0.92) 100%)`,
        }}
      >
        <div className="absolute -right-8 -top-8 h-28 w-28 rounded-full blur-2xl" style={{ backgroundColor: `${theme.color}22` }} />
        <div className="relative flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <span className="inline-flex h-8 w-8 items-center justify-center rounded-2xl bg-white/88 text-sm font-bold text-stone-700 shadow-sm">
                {source.id}
              </span>
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
                  {t('graphRagUi.sourceDetail.confidence', { value: confidence })}
                </span>
              )}
            </div>
            <h3 className="mt-3 font-display text-[1.45rem] leading-tight text-stone-900">
              {source.nodeLabel}
            </h3>
            {(source.metadata?.period || source.metadata?.school) && (
              <div className="mt-2 flex flex-wrap items-center gap-2 text-sm text-stone-500">
                {source.metadata?.period && (
                  <span className="rounded-full border border-stone-200/80 bg-white/70 px-2.5 py-1">
                    {source.metadata.period}
                  </span>
                )}
                {source.metadata?.school && (
                  <span className="rounded-full border border-stone-200/80 bg-white/70 px-2.5 py-1 italic">
                    {source.metadata.school as string}
                  </span>
                )}
              </div>
            )}
          </div>

          <button
            onClick={onClose}
            className="shrink-0 rounded-2xl border border-white/70 bg-white/88 p-2 text-stone-500 shadow-sm transition-colors hover:text-stone-900"
            aria-label={t('graphRagUi.sourceDetail.close')}
            type="button"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-5 py-4">
        <div className="space-y-4">
          <div className="rounded-[22px] border border-stone-200/70 bg-[linear-gradient(180deg,rgba(252,249,244,0.95),rgba(255,255,255,0.98))] p-4">
            <SectionLabel>{t('graphRagUi.sourceDetail.whyItMatters')}</SectionLabel>
            <p className="mt-2 text-sm leading-7 text-stone-600">
              {source.content || t('graphRagUi.sourceDetail.fallback')}
            </p>
          </div>

          {citationText?.original && (
            <div className="rounded-[22px] border border-stone-200/70 bg-white/92 p-4 shadow-[0_16px_40px_-34px_rgba(120,53,15,0.3)]">
              <SectionLabel>
                {citationText.originalLanguage === 'greek'
                  ? t('graphRagUi.sourceDetail.greekText')
                  : citationText.originalLanguage === 'latin'
                    ? t('graphRagUi.sourceDetail.latinText')
                    : t('graphRagUi.sourceDetail.originalText')}
              </SectionLabel>
              <div className="mt-3 flex gap-3">
                <div
                  className="mt-0.5 h-10 w-1 rounded-full"
                  style={{ backgroundColor: theme.color }}
                />
                <p className="font-ancient text-[1rem] italic leading-8 text-stone-800">
                  {citationText.original}
                </p>
              </div>
            </div>
          )}

          {citationText?.translation && (
            <div className="rounded-[22px] border border-stone-200/70 bg-parchment-50/72 p-4">
              <SectionLabel>{t('graphRagUi.sourceDetail.translation')}</SectionLabel>
              <div className="mt-3 flex gap-3">
                <Quote className="mt-0.5 h-4 w-4 shrink-0 text-stone-400" />
                <p className="text-sm leading-7 text-stone-700">
                  {citationText.translation}
                </p>
              </div>
            </div>
          )}

          {!citationText?.original && !citationText?.translation && (
            <div className="rounded-[22px] border border-dashed border-stone-300 bg-stone-50/80 p-4 text-sm text-stone-500">
              {t('graphRagUi.sourceDetail.missingPassage')}
            </div>
          )}
        </div>
      </div>

      <div className="flex items-center justify-between border-t border-stone-200/70 bg-[linear-gradient(180deg,rgba(255,255,255,0.92),rgba(252,249,244,0.92))] px-5 py-3">
        <div className="flex items-center gap-2">
          <button
            onClick={onPrev}
            disabled={citationIndex <= 0}
            className="inline-flex h-10 w-10 items-center justify-center rounded-2xl border border-stone-200/80 bg-white text-stone-500 transition-all hover:border-stone-300 hover:text-stone-900 disabled:opacity-35"
            aria-label={t('graphRagUi.sourceDetail.previous')}
            type="button"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
          <div className="rounded-full border border-stone-200/80 bg-white/85 px-3 py-1.5 text-xs font-medium text-stone-500">
            {t('graphRagUi.sourceDetail.sourcePosition', { index: citationIndex + 1, total: totalCitations })}
          </div>
          <button
            onClick={onNext}
            disabled={citationIndex >= totalCitations - 1}
            className="inline-flex h-10 w-10 items-center justify-center rounded-2xl border border-stone-200/80 bg-white text-stone-500 transition-all hover:border-stone-300 hover:text-stone-900 disabled:opacity-35"
            aria-label={t('graphRagUi.sourceDetail.next')}
            type="button"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>

        {source.nodeId && !source.nodeId.startsWith('source_') && (
          <button
            onClick={() => navigate(`/node/${source.nodeId}`)}
            className={cn(
              'inline-flex items-center gap-2 rounded-full border px-3 py-2 text-xs font-semibold transition-colors',
            )}
            style={{
              borderColor: theme.border,
              backgroundColor: theme.tint,
              color: theme.text,
            }}
            type="button"
          >
            {t('graphRagUi.sourceDetail.openNode')}
            <ArrowUpRight className="h-3.5 w-3.5" />
          </button>
        )}
      </div>
    </motion.div>
  );
}
