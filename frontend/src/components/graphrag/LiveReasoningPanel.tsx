/**
 * LiveReasoningPanel — real-time view of the synthesis model's chain-of-thought.
 *
 * Receives the accumulated reasoning text as a prop (parent supplies the
 * growing string + a streaming flag).  Renders in a parchment-amber-stone
 * mono trace with auto-scroll pinned to the bottom unless the user has
 * manually scrolled up.
 */

import { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { Brain, BrainCircuit, Loader2, CheckCircle2, ScrollText } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { cn } from '../../utils/cn';

interface LiveReasoningPanelProps {
  reasoning: string;
  isStreaming: boolean;
  /**
   * True once the run has ended (stream closed, whether it completed normally
   * or degraded). Distinguishes "no trace was ever captured" from "synthesis
   * hasn't started yet".
   */
  hasRunEnded?: boolean;
  /**
   * True when `reasoning` is NOT the model's chain-of-thought but the
   * pipeline's own research journal (the leads it opened and dropped), shown
   * on the rungs that expose no chain-of-thought. Labelled as such everywhere
   * it is rendered — the two must never be passed off as one another.
   */
  isJournal?: boolean;
  className?: string;
}

const NEAR_BOTTOM_THRESHOLD = 80; // px

export default function LiveReasoningPanel({
  reasoning,
  isStreaming,
  hasRunEnded = false,
  isJournal = false,
  className,
}: LiveReasoningPanelProps) {
  const { t } = useTranslation();
  const scrollRef = useRef<HTMLDivElement>(null);
  const userScrolledRef = useRef(false);
  const charCount = reasoning.length;

  // Auto-scroll: only when near the bottom (respect manual scroll-up).
  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    if (!userScrolledRef.current) {
      el.scrollTop = el.scrollHeight;
    }
  }, [charCount]);

  // Track whether the user has scrolled away from the bottom.
  const handleScroll = () => {
    const el = scrollRef.current;
    if (!el) return;
    const distFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
    userScrolledRef.current = distFromBottom > NEAR_BOTTOM_THRESHOLD;
  };

  // Reset scroll-lock when streaming starts fresh (new query).
  useEffect(() => {
    if (isStreaming && reasoning.length === 0) {
      userScrolledRef.current = false;
    }
  }, [isStreaming, reasoning.length]);

  // --- Empty state: the run ended without any reasoning trace --------
  // (degraded run, cached replay, or a model that never streamed a
  // chain-of-thought). Distinct from "synthesis hasn't started yet".
  if (!reasoning && hasRunEnded && !isStreaming) {
    return (
      <motion.div
        key="reasoning-no-trace"
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.28 }}
        className={cn(
          'flex h-full flex-col items-center justify-center gap-6 px-8 py-12',
          className,
        )}
      >
        <div className="flex h-16 w-16 items-center justify-center rounded-[22px] border border-stone-200/70 bg-gradient-to-br from-stone-50 to-white shadow-[0_16px_40px_-20px_rgba(68,64,60,0.18)]">
          <BrainCircuit className="h-7 w-7 text-stone-400" />
        </div>

        <div className="max-w-sm text-center">
          <p className="font-display text-base font-semibold text-stone-700">
            {t('graphRagUi.liveReasoning.emptyTitleNoTrace')}
          </p>
          <p className="mt-2 text-[13px] leading-6 text-stone-400">
            {t('graphRagUi.liveReasoning.emptyBodyNoTraceJournal')}
          </p>
        </div>
      </motion.div>
    );
  }

  // --- Empty state: synthesis hasn't started yet ---------------------
  if (!reasoning) {
    return (
      <motion.div
        key="reasoning-empty"
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.28 }}
        className={cn(
          'flex h-full flex-col items-center justify-center gap-6 px-8 py-12',
          className,
        )}
      >
        <div className="relative">
          <div className="flex h-16 w-16 items-center justify-center rounded-[22px] border border-amber-200/60 bg-gradient-to-br from-amber-50 to-white shadow-[0_16px_40px_-20px_rgba(120,53,15,0.22)]">
            <Brain className="h-7 w-7 text-amber-700/80" />
          </div>
          {isStreaming && (
            <>
              {[0, 1, 2].map((i) => (
                <motion.div
                  key={i}
                  className="absolute inset-0 rounded-[22px] border border-amber-300/40"
                  animate={{ scale: [1, 1.55], opacity: [0.5, 0] }}
                  transition={{ duration: 2.2, repeat: Infinity, delay: i * 0.55 }}
                />
              ))}
            </>
          )}
        </div>

        <div className="max-w-sm text-center">
          <p className="font-display text-base font-semibold text-stone-800">
            {t('graphRagUi.liveReasoning.emptyTitle')}
          </p>
          <p className="mt-2 text-[13px] leading-6 text-stone-400">
            {isStreaming
              ? t('graphRagUi.liveReasoning.emptyBodyStreaming')
              : t('graphRagUi.liveReasoning.emptyBodyIdle')}
          </p>
        </div>
      </motion.div>
    );
  }

  // --- Live / completed reasoning trace ------------------------------
  return (
    <motion.div
      key="reasoning-active"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.22 }}
      className={cn('flex h-full min-h-0 flex-col', className)}
    >
      {/* Header bar */}
      <div className="shrink-0 border-b border-stone-200/50 px-4 py-2.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {isJournal ? (
              <ScrollText className="h-4 w-4 text-amber-700" />
            ) : (
              <Brain className="h-4 w-4 text-amber-700" />
            )}
            <span className="text-[11px] font-semibold uppercase tracking-[0.16em] text-stone-500">
              {t(
                isJournal
                  ? 'graphRagUi.liveReasoning.journalHeaderLabel'
                  : 'graphRagUi.liveReasoning.headerLabel',
              )}
            </span>
          </div>

          <div className="flex items-center gap-2">
            {/* char count */}
            <span className="font-mono rounded-full bg-stone-100/80 px-2 py-0.5 text-[10px] font-medium text-stone-400">
              {charCount.toLocaleString()} chars
            </span>

            {isStreaming ? (
              <span className="flex items-center gap-1 rounded-full bg-amber-50 px-2 py-0.5 text-[10px] font-medium text-amber-700">
                <motion.span
                  className="h-1.5 w-1.5 rounded-full bg-amber-500"
                  animate={{ opacity: [1, 0.3, 1] }}
                  transition={{ duration: 1.2, repeat: Infinity }}
                />
                {t('graphRagUi.liveReasoning.live')}
              </span>
            ) : (
              <span className="flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-medium text-emerald-700">
                <CheckCircle2 className="h-2.5 w-2.5" />
                {t('graphRagUi.liveReasoning.complete')}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Journal disclosure: this is the PIPELINE's record of the leads it
          dropped, NOT the model's chain-of-thought. Never elide the difference. */}
      {isJournal && (
        <p className="shrink-0 border-b border-amber-200/40 bg-amber-50/50 px-4 py-2 text-[11px] leading-4 text-amber-800">
          {t('graphRagUi.liveReasoning.journalNotice')}
        </p>
      )}

      {/* Scrollable trace */}
      <div
        ref={scrollRef}
        onScroll={handleScroll}
        className="min-h-0 flex-1 overflow-y-auto"
      >
        {/* Left-rule gutter */}
        <div className="relative mx-4 my-4">
          <div className="absolute left-0 top-0 bottom-0 w-px bg-gradient-to-b from-amber-300/60 via-amber-200/40 to-transparent" />
          <div className="pl-5">
            <pre className="whitespace-pre-wrap font-mono text-[12.5px] leading-[1.75] text-stone-600">
              {reasoning}
            </pre>
            {isStreaming && (
              <motion.span
                className="ml-0.5 inline-block h-[1.1em] w-[2px] rounded-sm bg-amber-500 align-text-bottom"
                animate={{ opacity: [1, 0] }}
                transition={{ duration: 0.6, repeat: Infinity, repeatType: 'reverse' }}
              />
            )}
          </div>
        </div>
      </div>

      {/* Bottom status bar while streaming */}
      {isStreaming && (
        <div className="shrink-0 border-t border-amber-200/40 bg-amber-50/60 px-4 py-2">
          <p className="flex items-center gap-1.5 text-[11px] leading-4 text-amber-800">
            <Loader2 className="h-3 w-3 shrink-0 animate-spin text-amber-600" aria-hidden />
            <span>{t('graphRagUi.liveReasoning.streamingNotice')}</span>
          </p>
        </div>
      )}
    </motion.div>
  );
}

// Compact inline placeholder used when the Reasoning tab is visible but
// synthesis hasn't started (during retrieval).
export function ReasoningTabEmptyHint() {
  const { t } = useTranslation();
  return (
    <div className="flex h-full flex-col items-center justify-center gap-4 px-6 py-10">
      <ScrollText className="h-8 w-8 text-amber-300" />
      <p className="max-w-xs text-center text-[12px] leading-6 text-stone-400">
        {t('graphRagUi.liveReasoning.tabHint')}
      </p>
    </div>
  );
}
