/**
 * ResearchSession — composes the streaming research UI primitives into the
 * three-pane layout used by the /research page.
 *
 * Layout:
 *   left  — agent timeline + active sub-agents
 *   mid   — streaming answer + KG viz
 *   right — citation feed
 *
 * The component is layout-only; it does not own the SSE connection. Callers
 * pass the values returned by `useResearchStream`.
 */

import { AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { cn } from '../../lib/utils';
import type {
  ActiveSubagent,
  CitationEntry,
  KGActivation,
  PairedToolCall,
} from '../../hooks/useResearchStream';
import type { AgentEvent, FinalAnswerEvent, SessionStatus } from '../../types/agent-events';
import { AgentTimeline } from './AgentTimeline';
import { CitationFeed } from './CitationFeed';
import { LiveKGViz } from './LiveKGViz';
import { StreamingAnswer } from './StreamingAnswer';
import { SubagentStatusCard } from './SubagentStatusCard';

interface Props {
  status: SessionStatus;
  events: AgentEvent[];
  toolCalls: PairedToolCall[];
  activeSubagents: ActiveSubagent[];
  citations: CitationEntry[];
  kgActivations: KGActivation[];
  streamedAnswer: string;
  finalAnswer: FinalAnswerEvent | null;
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
  className,
}: Props) {
  const { t } = useTranslation();
  const isLive =
    status === 'streaming' || status === 'connecting' || status === 'synthesizing';
  const renderedAnswer = finalAnswer ? finalAnswer.answer : streamedAnswer;

  return (
    <div
      className={cn(
        'grid h-full min-h-[600px] grid-cols-1 gap-3 lg:grid-cols-[280px_minmax(0,1fr)_320px]',
        className,
      )}
    >
      {/* Left rail: timeline + subagents */}
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

      {/* Center: answer + KG viz */}
      <div className="flex h-full min-h-0 flex-col gap-3">
        <div className="min-h-0 flex-1 overflow-y-auto">
          <StreamingAnswer
            text={renderedAnswer}
            citations={citations}
            isLive={isLive && !finalAnswer}
          />
        </div>
        <LiveKGViz activations={kgActivations} />
      </div>

      {/* Right rail: citation feed */}
      <aside className="h-full rounded-2xl border border-stone-200/70 bg-white/70 backdrop-blur-sm">
        <CitationFeed citations={citations} isLive={isLive} />
      </aside>
    </div>
  );
}

export default ResearchSession;
