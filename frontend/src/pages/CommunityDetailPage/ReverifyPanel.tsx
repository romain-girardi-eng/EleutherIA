import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { AnimatePresence, motion } from 'framer-motion';
import {
  X,
  Loader2,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  ScrollText,
  ShieldCheck,
} from 'lucide-react';
import {
  streamReverify,
  type ReverifyResponse,
  type ReverifyStage,
} from '../../api/community';
import { cn } from '../../lib/utils';

interface ReverifyPanelProps {
  open: boolean;
  slug: string;
  onClose: () => void;
  cachedAnswerExcerpt: string;
  cachedCitations: string[];
}

const STAGE_ORDER: ReverifyStage[] = [
  'classify',
  'search',
  'reading',
  'synthesis',
  'verify',
];

type StageState = 'pending' | 'active' | 'done';

interface StageProgress {
  stage: ReverifyStage;
  elapsed_s: number;
}

function similarityColorClass(similarity: number): string {
  if (similarity >= 0.9) return 'text-emerald-600';
  if (similarity >= 0.7) return 'text-amber-600';
  return 'text-rose-600';
}

function similarityBgClass(similarity: number): string {
  if (similarity >= 0.9) return 'bg-emerald-50 border-emerald-200';
  if (similarity >= 0.7) return 'bg-amber-50 border-amber-200';
  return 'bg-rose-50 border-rose-200';
}

function stageStatus(
  stage: ReverifyStage,
  current: ReverifyStage | null,
  completed: boolean
): StageState {
  if (completed) return 'done';
  if (!current) return 'pending';
  const stageIdx = STAGE_ORDER.indexOf(stage);
  const currentIdx = STAGE_ORDER.indexOf(current);
  if (stageIdx < currentIdx) return 'done';
  if (stageIdx === currentIdx) return 'active';
  return 'pending';
}

function CitationChip({
  ref: citationRef,
  tone,
}: {
  ref: string;
  tone: 'added' | 'removed' | 'neutral';
}) {
  const toneClass =
    tone === 'added'
      ? 'text-emerald-700 bg-emerald-50 border-emerald-200'
      : tone === 'removed'
        ? 'text-rose-700 bg-rose-50 border-rose-200'
        : 'text-stone-700 bg-stone-50 border-stone-200';
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-[11px] font-medium',
        toneClass
      )}
    >
      <ScrollText className="h-3 w-3" aria-hidden="true" />
      <span className="font-mono">{citationRef}</span>
    </span>
  );
}

export default function ReverifyPanel({
  open,
  slug,
  onClose,
  cachedAnswerExcerpt,
  cachedCitations,
}: ReverifyPanelProps) {
  const { t } = useTranslation();
  const [stages, setStages] = useState<StageProgress[]>([]);
  const [currentStage, setCurrentStage] = useState<ReverifyStage | null>(null);
  const [result, setResult] = useState<ReverifyResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [cancelled, setCancelled] = useState(false);
  const streamRef = useRef<{ cancel: () => void } | null>(null);

  const reset = useCallback(() => {
    setStages([]);
    setCurrentStage(null);
    setResult(null);
    setError(null);
    setCancelled(false);
  }, []);

  const startStream = useCallback(() => {
    reset();
    setIsRunning(true);
    const handle = streamReverify(slug, {
      onProgress: (event) => {
        setCurrentStage(event.stage);
        setStages((prev) => {
          const idx = prev.findIndex((s) => s.stage === event.stage);
          if (idx === -1) return [...prev, { stage: event.stage, elapsed_s: event.elapsed_s }];
          const next = prev.slice();
          next[idx] = { stage: event.stage, elapsed_s: event.elapsed_s };
          return next;
        });
      },
      onComplete: (event) => {
        setResult(event.data);
        setCurrentStage(null);
      },
      onError: (event) => {
        setError(event.message);
      },
      onClose: () => {
        setIsRunning(false);
      },
    });
    streamRef.current = handle;
  }, [reset, slug]);

  // Kick off the stream when the panel opens for the first time.
  useEffect(() => {
    if (!open) return;
    if (isRunning || result || error || cancelled) return;
    startStream();
  }, [open, isRunning, result, error, cancelled, startStream]);

  // Abort any in-flight stream on unmount or when closing.
  useEffect(() => {
    return () => {
      streamRef.current?.cancel();
    };
  }, []);

  const handleCancel = useCallback(() => {
    streamRef.current?.cancel();
    streamRef.current = null;
    setCancelled(true);
    setIsRunning(false);
  }, []);

  const handleClose = useCallback(() => {
    streamRef.current?.cancel();
    streamRef.current = null;
    onClose();
  }, [onClose]);

  const handleRetry = useCallback(() => {
    startStream();
  }, [startStream]);

  const handleApplyUpdate = useCallback(() => {
    // Stubbed future endpoint — surface a polite "coming soon" hint.
    window.alert(t('reproducibility.reverify.applyComingSoon'));
  }, [t]);

  const newCitations = useMemo<string[]>(() => {
    if (!result) return [];
    // Re-derive: original = cached - removed + (kept) ; new = (kept) + added
    const removed = new Set(result.citation_diff.removed);
    const kept = cachedCitations.filter((c) => !removed.has(c));
    return [...kept, ...result.citation_diff.added];
  }, [result, cachedCitations]);

  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            key="reverify-backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-stone-900/40 backdrop-blur-sm"
            onClick={handleClose}
            aria-hidden="true"
          />
          <motion.div
            key="reverify-panel"
            role="dialog"
            aria-modal="true"
            aria-labelledby="reverify-title"
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', stiffness: 280, damping: 32 }}
            className="fixed inset-y-0 right-0 z-50 flex w-full max-w-4xl flex-col bg-[#fdfaf3] shadow-2xl ring-1 ring-stone-200"
          >
            {/* Header */}
            <header className="flex shrink-0 items-start justify-between gap-3 border-b border-stone-200/70 px-5 pb-3 pt-[max(0.75rem,env(safe-area-inset-top))]">
              <div className="min-w-0 flex-1">
                <h2
                  id="reverify-title"
                  className="flex items-center gap-2 truncate font-display text-[15px] font-semibold text-stone-900"
                >
                  <ShieldCheck className="h-4 w-4 text-amber-700" aria-hidden="true" />
                  {t('reproducibility.reverify.title')}
                </h2>
                <p className="mt-0.5 text-[11px] text-stone-500">
                  {t('reproducibility.reverify.subtitle')}
                </p>
              </div>
              <button
                type="button"
                onClick={handleClose}
                aria-label={t('reproducibility.reverify.close')}
                className="shrink-0 flex h-11 w-11 items-center justify-center rounded-full text-stone-500 hover:bg-stone-100"
              >
                <X className="h-4 w-4" aria-hidden="true" />
              </button>
            </header>

            {/* Body */}
            <div className="min-h-0 flex-1 overflow-y-auto px-5 py-5">
              {/* Progress timeline */}
              {!result && !error && (
                <section aria-labelledby="reverify-progress">
                  <h3
                    id="reverify-progress"
                    className="text-xs font-semibold uppercase tracking-wider text-stone-500"
                  >
                    {t('reproducibility.reverify.progress')}
                  </h3>
                  <ol className="mt-3 space-y-2">
                    {STAGE_ORDER.map((stage) => {
                      const state = stageStatus(stage, currentStage, false);
                      const found = stages.find((s) => s.stage === stage);
                      return (
                        <li
                          key={stage}
                          className={cn(
                            'flex items-center gap-3 rounded-lg border px-3 py-2 text-sm',
                            state === 'done' &&
                              'border-emerald-200/70 bg-emerald-50/40 text-emerald-900',
                            state === 'active' &&
                              'border-amber-300/70 bg-amber-50/60 text-amber-900',
                            state === 'pending' &&
                              'border-stone-200/60 bg-stone-50/40 text-stone-500'
                          )}
                        >
                          <span className="flex h-5 w-5 items-center justify-center">
                            {state === 'done' && (
                              <CheckCircle2
                                className="h-4 w-4 text-emerald-600"
                                aria-hidden="true"
                              />
                            )}
                            {state === 'active' && (
                              <Loader2
                                className="h-4 w-4 animate-spin text-amber-600"
                                aria-hidden="true"
                              />
                            )}
                            {state === 'pending' && (
                              <span
                                className="h-2 w-2 rounded-full bg-stone-300"
                                aria-hidden="true"
                              />
                            )}
                          </span>
                          <span className="flex-1 text-[13px] font-medium">
                            {t(`reproducibility.reverify.stages.${stage}`)}
                          </span>
                          {found && (
                            <span className="font-mono text-[11px] text-stone-500">
                              {found.elapsed_s.toFixed(1)}s
                            </span>
                          )}
                        </li>
                      );
                    })}
                  </ol>
                </section>
              )}

              {/* Error state */}
              {error && (
                <div
                  role="alert"
                  className="flex items-start gap-3 rounded-xl border border-rose-200/70 bg-rose-50/70 p-4 text-sm text-rose-800"
                >
                  <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" aria-hidden="true" />
                  <div className="flex-1">
                    <p className="font-medium">
                      {t('reproducibility.reverify.errorTitle')}
                    </p>
                    <p className="text-rose-700/80">{error}</p>
                  </div>
                  <button
                    type="button"
                    onClick={handleRetry}
                    className="min-h-11 rounded-full bg-rose-700 px-3 text-[11px] font-semibold text-rose-50 hover:bg-rose-800"
                  >
                    {t('reproducibility.reverify.retry')}
                  </button>
                </div>
              )}

              {cancelled && !error && !result && (
                <div className="mt-6 rounded-xl border border-stone-200/70 bg-stone-50/50 p-4 text-sm text-stone-700">
                  <p>{t('reproducibility.reverify.cancelled')}</p>
                  <button
                    type="button"
                    onClick={handleRetry}
                    className="mt-3 inline-flex min-h-11 items-center gap-1.5 rounded-full bg-amber-700 px-3 text-[11px] font-semibold text-amber-50 hover:bg-amber-800"
                  >
                    {t('reproducibility.reverify.retry')}
                    <ArrowRight className="h-3 w-3" aria-hidden="true" />
                  </button>
                </div>
              )}

              {/* Diff result */}
              {result && (
                <section aria-labelledby="reverify-result" className="space-y-5">
                  <div
                    className={cn(
                      'flex flex-col items-center gap-1 rounded-2xl border p-5 text-center',
                      similarityBgClass(result.similarity)
                    )}
                  >
                    <span className="text-[11px] font-semibold uppercase tracking-wider text-stone-500">
                      {t('reproducibility.reverify.similarity')}
                    </span>
                    <span
                      className={cn(
                        'font-display text-4xl font-semibold tabular-nums',
                        similarityColorClass(result.similarity)
                      )}
                    >
                      {result.similarity.toFixed(3)}
                    </span>
                    <div className="mt-2 flex flex-wrap items-center justify-center gap-3 text-[11px] text-stone-600">
                      <span>
                        {t('reproducibility.reverify.charDiff', {
                          diff:
                            result.char_count_diff >= 0
                              ? `+${result.char_count_diff}`
                              : `${result.char_count_diff}`,
                        })}
                      </span>
                      <span aria-hidden="true">·</span>
                      <span>
                        {t('reproducibility.reverify.citationsAdded', {
                          count: result.citation_diff.added.length,
                        })}
                      </span>
                      <span aria-hidden="true">·</span>
                      <span>
                        {t('reproducibility.reverify.citationsRemoved', {
                          count: result.citation_diff.removed.length,
                        })}
                      </span>
                      <span aria-hidden="true">·</span>
                      <span>
                        {t('reproducibility.reverify.kgAdvancedBy', {
                          count: result.kg_advanced_by,
                        })}
                      </span>
                    </div>
                  </div>

                  <h3
                    id="reverify-result"
                    className="text-xs font-semibold uppercase tracking-wider text-stone-500"
                  >
                    {t('reproducibility.reverify.compare')}
                  </h3>

                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    {/* Cached column */}
                    <article className="flex flex-col rounded-xl border border-stone-200/70 bg-white/60 p-4">
                      <header className="mb-2 flex items-center justify-between">
                        <h4 className="text-[12px] font-semibold text-stone-700">
                          {t('reproducibility.reverify.cached')}
                        </h4>
                      </header>
                      <p className="whitespace-pre-wrap text-[13px] leading-relaxed text-stone-700">
                        {cachedAnswerExcerpt}
                      </p>
                      {cachedCitations.length > 0 && (
                        <div className="mt-3 flex flex-wrap gap-1.5">
                          {cachedCitations.map((ref, idx) => {
                            const removed = result.citation_diff.removed.includes(ref);
                            return (
                              <CitationChip
                                key={`${ref}-${idx}`}
                                ref={ref}
                                tone={removed ? 'removed' : 'neutral'}
                              />
                            );
                          })}
                        </div>
                      )}
                    </article>

                    {/* New column */}
                    <article className="flex flex-col rounded-xl border border-amber-200/70 bg-amber-50/30 p-4">
                      <header className="mb-2 flex items-center justify-between">
                        <h4 className="text-[12px] font-semibold text-amber-900">
                          {t('reproducibility.reverify.fresh')}
                        </h4>
                      </header>
                      <p className="whitespace-pre-wrap text-[13px] leading-relaxed text-stone-800">
                        {result.new_answer_excerpt}
                      </p>
                      {newCitations.length > 0 && (
                        <div className="mt-3 flex flex-wrap gap-1.5">
                          {newCitations.map((ref, idx) => {
                            const added = result.citation_diff.added.includes(ref);
                            return (
                              <CitationChip
                                key={`${ref}-${idx}`}
                                ref={ref}
                                tone={added ? 'added' : 'neutral'}
                              />
                            );
                          })}
                        </div>
                      )}
                    </article>
                  </div>
                </section>
              )}
            </div>

            {/* Footer */}
            <footer className="flex shrink-0 flex-wrap items-center justify-end gap-2 border-t border-stone-200/70 bg-white/50 px-5 pt-3 pb-[max(0.75rem,env(safe-area-inset-bottom))]">
              {isRunning && !result && !error && (
                <button
                  type="button"
                  onClick={handleCancel}
                  className="inline-flex min-h-11 items-center gap-1.5 rounded-full border border-stone-300 bg-white px-4 text-[12px] font-semibold text-stone-700 hover:bg-stone-50"
                >
                  {t('reproducibility.reverify.cancel')}
                </button>
              )}
              {result && (
                <button
                  type="button"
                  onClick={handleApplyUpdate}
                  className="inline-flex min-h-11 items-center gap-1.5 rounded-full bg-amber-700 px-4 text-[12px] font-semibold text-amber-50 hover:bg-amber-800"
                >
                  {t('reproducibility.reverify.applyUpdate')}
                  <ArrowRight className="h-3 w-3" aria-hidden="true" />
                </button>
              )}
              <button
                type="button"
                onClick={handleClose}
                className="inline-flex min-h-11 items-center gap-1.5 rounded-full border border-stone-300 bg-white px-4 text-[12px] font-semibold text-stone-700 hover:bg-stone-50"
              >
                {t('reproducibility.reverify.close')}
              </button>
            </footer>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
