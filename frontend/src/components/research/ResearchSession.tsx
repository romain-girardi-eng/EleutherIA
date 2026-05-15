/**
 * ResearchSession — composes the streaming research UI primitives into the
 * doctoral workspace layout used by the /research page.
 *
 * Layout (desktop):
 *   - left rail  → SessionHistory drawer trigger + AgentTimeline + subagents
 *   - center     → ExportToolbar overlay + StreamingAnswer + MethodologyNotesPane (collapsible)
 *   - right rail → BibliographyPane (tabs: Primary / Secondary / Notes)
 *                  CitationFeed lives inside as the source of the "Primary" tab feed
 *   - modal layer → PassageViewer + AgentTrace
 *
 * On mobile (< md) the side rails collapse into a tab bar at the bottom.
 *
 * The component is layout-only; it does not own the SSE connection. Callers
 * pass the values returned by `useResearchStream`.
 */

import { useCallback, useMemo, useState } from 'react';
import { AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { Compass, FileText, History, Library, Network } from 'lucide-react';
import { cn } from '../../lib/utils';
import type {
  ActiveSubagent,
  CitationEntry,
  KGActivation,
  PairedToolCall,
  TokenUsageState,
} from '../../hooks/useResearchStream';
import { useBibliography } from '../../hooks/useBibliography';
import type { AgentEvent, FinalAnswerEvent, SessionStatus } from '../../types/agent-events';
import type { Conversation } from '../../types';
import { AgentTimeline } from './AgentTimeline';
import { CitationFeed } from './CitationFeed';
import { LiveKGViz } from './LiveKGViz';
import { CostCounter } from './CostCounter';
import { StreamingAnswer } from './StreamingAnswer';
import { SubagentStatusCard } from './SubagentStatusCard';
import {
  AgentTrace,
  BibliographyPane,
  ExportToolbar,
  MethodologyNotesPane,
  PassageViewer,
  SessionHistory,
} from './doctoral';

type MobileTab = 'timeline' | 'answer' | 'methodology' | 'bibliography';

interface Props {
  status: SessionStatus;
  events: AgentEvent[];
  toolCalls: PairedToolCall[];
  activeSubagents: ActiveSubagent[];
  citations: CitationEntry[];
  kgActivations: KGActivation[];
  streamedAnswer: string;
  finalAnswer: FinalAnswerEvent | null;
  /** Live token + USD cost accumulator from ``useResearchStream``. */
  tokenUsage?: TokenUsageState;
  /** Session identifier used to scope localStorage (bibliography, history). */
  sessionId?: string;
  /** Trace id used to build export URLs / fetch audit. */
  traceId?: string;
  /** Shareable canonical URL for this research session. */
  shareUrl?: string;
  /** Hooks for the SessionHistory drawer. */
  onResumeConversation?: (c: Conversation) => void;
  onBranchConversation?: (c: Conversation) => void;
  /** Optional callback when a KG node is requested in Cosmograph. */
  onOpenInCosmograph?: (nodeId: string) => void;
  className?: string;
}

export function ResearchSession({
  status,
  events,
  toolCalls,
  activeSubagents,
  citations,
  kgActivations,
  streamedAnswer,
  finalAnswer,
  tokenUsage,
  sessionId = 'default',
  traceId,
  shareUrl,
  onResumeConversation,
  onBranchConversation,
  onOpenInCosmograph,
  className,
}: Props) {
  const { t } = useTranslation();
  const isLive =
    status === 'streaming' || status === 'connecting' || status === 'synthesizing';
  const renderedAnswer = finalAnswer ? finalAnswer.answer : streamedAnswer;
  const effectiveTraceId = traceId ?? finalAnswer?.trace_id;

  const bibliography = useBibliography(sessionId);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [traceOpen, setTraceOpen] = useState(false);
  const [activePassage, setActivePassage] = useState<string | null>(null);
  const [mobileTab, setMobileTab] = useState<MobileTab>('answer');

  const scrollToCitation = useCallback((id: string) => {
    const el =
      document.querySelector(`[data-citation-id="${id}"]`) ??
      document.querySelector(`[data-passage-anchor="${id}"]`);
    if (el instanceof HTMLElement) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      el.classList.add('animate-amber-pulse');
      window.setTimeout(() => {
        el.classList.remove('animate-amber-pulse');
      }, 1500);
    }
  }, []);

  const tabs = useMemo(
    () =>
      [
        { id: 'timeline' as const, labelKey: 'research.doctoral.tabs.timeline', Icon: Network },
        { id: 'answer' as const, labelKey: 'research.doctoral.tabs.answer', Icon: FileText },
        {
          id: 'methodology' as const,
          labelKey: 'research.doctoral.tabs.methodology',
          Icon: Compass,
        },
        {
          id: 'bibliography' as const,
          labelKey: 'research.doctoral.tabs.bibliography',
          Icon: Library,
        },
      ] as const,
    [],
  );

  const onOpenAudit = useCallback(() => {
    if (effectiveTraceId) setTraceOpen(true);
  }, [effectiveTraceId]);

  return (
    <div className={cn('relative', className)}>
      {/* Toolbar row */}
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <button
          type="button"
          onClick={() => setHistoryOpen(true)}
          className="inline-flex items-center gap-1.5 rounded-lg border border-stone-200 bg-white/70 px-3 py-1.5 text-[12px] font-medium text-stone-700 hover:border-amber-300 hover:bg-amber-50"
        >
          <History className="h-3.5 w-3.5 text-amber-700" aria-hidden="true" />
          {t('research.doctoral.history.openButton')}
        </button>
        <div className="flex items-center gap-2">
          {tokenUsage && (tokenUsage.total_tokens > 0 || isLive) && (
            <CostCounter usage={tokenUsage} />
          )}
          {effectiveTraceId && (
            <button
              type="button"
              onClick={onOpenAudit}
              className="inline-flex items-center gap-1.5 rounded-lg border border-stone-200 bg-white/70 px-3 py-1.5 text-[12px] font-medium text-stone-700 hover:border-amber-300 hover:bg-amber-50"
            >
              <Network className="h-3.5 w-3.5 text-amber-700" aria-hidden="true" />
              {t('research.doctoral.audit.openButton')}
            </button>
          )}
          {effectiveTraceId && (
            <ExportToolbar traceId={effectiveTraceId} shareUrl={shareUrl} />
          )}
        </div>
      </div>

      {/* Desktop grid */}
      <div
        className={cn(
          'hidden h-full min-h-[600px] grid-cols-[280px_minmax(0,1fr)_340px] gap-3 lg:grid',
        )}
      >
        <aside
          aria-labelledby="research-timeline-header"
          className="flex h-full flex-col gap-3 rounded-2xl border border-stone-200/70 bg-white/70 backdrop-blur-sm"
        >
          <div className="shrink-0 border-b border-stone-200/50 px-4 py-2.5">
            <h2
              id="research-timeline-header"
              className="text-[11px] font-semibold uppercase tracking-[0.16em] text-stone-500"
            >
              {t('research.timeline.title')}
            </h2>
          </div>
          {activeSubagents.length > 0 && (
            <div className="space-y-1.5 px-3">
              <AnimatePresence initial={false}>
                {activeSubagents.map((a) => (
                  <SubagentStatusCard
                    key={`${a.agent}::${a.subagent}`}
                    agent={a}
                    nameKey={a.subagent}
                  />
                ))}
              </AnimatePresence>
            </div>
          )}
          <div className="min-h-0 flex-1">
            <AgentTimeline events={events} toolCalls={toolCalls} isLive={isLive} />
          </div>
        </aside>

        <div className="flex h-full min-h-0 flex-col gap-3">
          <div className="min-h-0 flex-1 overflow-y-auto">
            <StreamingAnswer
              text={renderedAnswer}
              citations={citations}
              isLive={isLive && !finalAnswer}
              traceId={effectiveTraceId}
            />
          </div>
          <MethodologyNotesPane
            events={events}
            onAnchorClick={scrollToCitation}
            className="max-h-64 shrink-0"
          />
          <LiveKGViz activations={kgActivations} />
        </div>

        <aside className="flex h-full flex-col gap-3">
          <BibliographyPane
            bibliography={bibliography}
            traceId={effectiveTraceId}
            shareUrl={shareUrl}
            className="flex-1"
          />
          <div className="max-h-72 rounded-2xl border border-stone-200/70 bg-white/70 backdrop-blur-sm">
            <CitationFeed citations={citations} isLive={isLive} onOpenPassage={setActivePassage} />
          </div>
        </aside>
      </div>

      {/* Mobile tabs */}
      <div className="block lg:hidden">
        <div className="mb-3 grid grid-cols-4 gap-1 rounded-xl border border-stone-200/70 bg-white/70 p-1">
          {tabs.map(({ id, labelKey, Icon }) => (
            <button
              key={id}
              type="button"
              onClick={() => setMobileTab(id)}
              aria-selected={mobileTab === id}
              className={cn(
                'flex flex-col items-center gap-0.5 rounded-lg px-1 py-1.5 text-[10px] font-medium',
                mobileTab === id
                  ? 'bg-amber-50 text-amber-800'
                  : 'text-stone-500 hover:text-stone-700',
              )}
            >
              <Icon className="h-4 w-4" aria-hidden="true" />
              {t(labelKey)}
            </button>
          ))}
        </div>
        <div className="min-h-[480px]">
          {mobileTab === 'timeline' && (
            <div className="rounded-2xl border border-stone-200/70 bg-white/70">
              <AgentTimeline events={events} toolCalls={toolCalls} isLive={isLive} />
            </div>
          )}
          {mobileTab === 'answer' && (
            <StreamingAnswer
              text={renderedAnswer}
              citations={citations}
              isLive={isLive && !finalAnswer}
              traceId={effectiveTraceId}
            />
          )}
          {mobileTab === 'methodology' && (
            <MethodologyNotesPane events={events} onAnchorClick={scrollToCitation} />
          )}
          {mobileTab === 'bibliography' && (
            <BibliographyPane
              bibliography={bibliography}
              traceId={effectiveTraceId}
              shareUrl={shareUrl}
            />
          )}
        </div>
      </div>

      <SessionHistory
        open={historyOpen}
        onClose={() => setHistoryOpen(false)}
        onResume={(c) => {
          setHistoryOpen(false);
          onResumeConversation?.(c);
        }}
        onBranch={(c) => {
          setHistoryOpen(false);
          onBranchConversation?.(c);
        }}
      />
      {activePassage && (
        <PassageViewer
          passageId={activePassage}
          open={true}
          onClose={() => setActivePassage(null)}
          onSaveToBibliography={bibliography.add}
          onOpenInCosmograph={onOpenInCosmograph}
        />
      )}
      {effectiveTraceId && (
        <AgentTrace
          traceId={effectiveTraceId}
          open={traceOpen}
          onClose={() => setTraceOpen(false)}
        />
      )}
    </div>
  );
}

export default ResearchSession;
