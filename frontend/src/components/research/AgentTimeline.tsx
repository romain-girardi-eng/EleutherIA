/**
 * AgentTimeline — vertical timeline of the agent's reasoning.
 * Renders agent_step + tool_call/tool_result events in chronological order,
 * with a left rail of status dots and connector lines. Designed to feel like
 * a research journal: read-once-then-archive.
 */

import { useEffect, useRef } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Brain, CheckCircle2, AlertTriangle, Wrench, Sparkles } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { cn } from '../../lib/utils';
import type { AgentEvent } from '../../types/agent-events';
import type { PairedToolCall } from '../../hooks/useResearchStream';
import { ToolCallTrace } from './ToolCallTrace';

interface Props {
  events: AgentEvent[];
  toolCalls: PairedToolCall[];
  isLive: boolean;
}

interface TimelineEntry {
  id: string;
  kind: 'step' | 'tool' | 'milestone';
  ts: number;
  payload: AgentEvent | PairedToolCall;
}

function buildEntries(events: AgentEvent[], toolCalls: PairedToolCall[]): TimelineEntry[] {
  const entries: TimelineEntry[] = [];
  const callsById = new Map(toolCalls.map((c) => [c.call.id, c]));
  const seenCall = new Set<string>();

  events.forEach((event, idx) => {
    const baseTs = idx;
    if (event.type === 'agent_step') {
      entries.push({
        id: `step-${idx}`,
        kind: 'step',
        ts: baseTs,
        payload: event,
      });
    } else if (event.type === 'tool_call') {
      const pair = callsById.get(event.id);
      if (pair && !seenCall.has(event.id)) {
        seenCall.add(event.id);
        entries.push({
          id: `tool-${event.id}`,
          kind: 'tool',
          ts: baseTs,
          payload: pair,
        });
      }
    } else if (event.type === 'agent_start') {
      entries.push({
        id: `milestone-${idx}`,
        kind: 'milestone',
        ts: baseTs,
        payload: event,
      });
    } else if (event.type === 'final_answer') {
      entries.push({
        id: `milestone-final-${idx}`,
        kind: 'milestone',
        ts: baseTs,
        payload: event,
      });
    }
  });

  return entries;
}

export function AgentTimeline({ events, toolCalls, isLive }: Props) {
  const { t } = useTranslation();
  const scrollRef = useRef<HTMLDivElement>(null);
  const entries = buildEntries(events, toolCalls);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el || typeof el.scrollTo !== 'function') return;
    el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
  }, [entries.length]);

  if (entries.length === 0) {
    return (
      <div className="flex h-full items-center justify-center p-8 text-center">
        <div>
          <Sparkles className="mx-auto h-7 w-7 text-amber-500" aria-hidden="true" />
          <p className="mt-2 font-display text-base text-stone-700">
            {t('research.timeline.idleTitle')}
          </p>
          <p className="mt-1 text-[12px] text-stone-500">
            {t('research.timeline.idleSubtitle')}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div ref={scrollRef} className="h-full overflow-y-auto px-4 py-4">
      <AnimatePresence initial={false}>
        {entries.map((entry) => (
          <motion.div
            key={entry.id}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="relative flex gap-3"
          >
            <div className="flex flex-col items-center">
              <TimelineDot entry={entry} />
              <div className="w-px flex-1 bg-gradient-to-b from-stone-200/80 to-transparent" />
            </div>
            <div className="mb-3 min-w-0 flex-1">
              <TimelineCard entry={entry} />
            </div>
          </motion.div>
        ))}
      </AnimatePresence>

      {isLive && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex items-center gap-3 pb-2 pl-1"
        >
          <div className="flex h-7 w-7 items-center justify-center">
            <motion.span
              className="h-2 w-2 rounded-full bg-amber-400"
              animate={{ scale: [1, 1.4, 1], opacity: [0.6, 1, 0.6] }}
              transition={{ duration: 1.4, repeat: Infinity }}
            />
          </div>
          <span className="text-[12px] italic text-stone-400">
            {t('research.timeline.thinking')}
          </span>
        </motion.div>
      )}
    </div>
  );
}

function TimelineDot({ entry }: { entry: TimelineEntry }) {
  if (entry.kind === 'milestone') {
    const isFinal = (entry.payload as AgentEvent).type === 'final_answer';
    return (
      <div
        className={cn(
          'relative z-10 flex h-8 w-8 shrink-0 items-center justify-center rounded-2xl border shadow-sm',
          isFinal
            ? 'border-emerald-300 bg-emerald-50 text-emerald-700'
            : 'border-amber-300 bg-amber-50 text-amber-700',
        )}
      >
        {isFinal ? (
          <CheckCircle2 className="h-4 w-4" aria-hidden="true" />
        ) : (
          <Sparkles className="h-4 w-4" aria-hidden="true" />
        )}
      </div>
    );
  }
  if (entry.kind === 'tool') {
    return (
      <div className="relative z-10 flex h-8 w-8 shrink-0 items-center justify-center rounded-2xl border border-stone-200 bg-white text-stone-700 shadow-sm">
        <Wrench className="h-3.5 w-3.5" aria-hidden="true" />
      </div>
    );
  }
  const step = entry.payload as AgentEvent;
  if (step.type === 'agent_step' && step.status === 'failed') {
    return (
      <div className="relative z-10 flex h-8 w-8 shrink-0 items-center justify-center rounded-2xl border border-rose-200 bg-rose-50 text-rose-700 shadow-sm">
        <AlertTriangle className="h-4 w-4" aria-hidden="true" />
      </div>
    );
  }
  return (
    <div className="relative z-10 flex h-8 w-8 shrink-0 items-center justify-center rounded-2xl border border-violet-200 bg-violet-50 text-violet-700 shadow-sm">
      <Brain className="h-4 w-4" aria-hidden="true" />
    </div>
  );
}

function TimelineCard({ entry }: { entry: TimelineEntry }) {
  const { t } = useTranslation();

  if (entry.kind === 'tool') {
    return <ToolCallTrace pair={entry.payload as PairedToolCall} />;
  }
  if (entry.kind === 'milestone') {
    const ev = entry.payload as AgentEvent;
    if (ev.type === 'agent_start') {
      return (
        <div className="rounded-xl border border-amber-200/70 bg-amber-50/70 px-3 py-2">
          <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-amber-700">
            {t('research.timeline.queryStarted')}
          </p>
          <p className="mt-1 font-mono text-[13px] text-stone-800">{ev.query}</p>
        </div>
      );
    }
    if (ev.type === 'final_answer') {
      return (
        <div className="rounded-xl border border-emerald-200/70 bg-emerald-50/70 px-3 py-2">
          <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-emerald-700">
            {t('research.timeline.answerReady')}
          </p>
          <p className="mt-1 text-[12px] text-stone-700">
            {ev.citations.length} {t('research.timeline.citationsCount')}
          </p>
        </div>
      );
    }
  }
  const step = entry.payload as AgentEvent;
  if (step.type !== 'agent_step') return null;
  return (
    <div
      className={cn(
        'rounded-xl border px-3 py-2',
        step.status === 'failed'
          ? 'border-rose-200/70 bg-rose-50/70'
          : 'border-violet-200/70 bg-violet-50/40',
      )}
    >
      <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-stone-500">
        {step.agent} / {step.subagent}
      </p>
      {step.message && (
        <p className="mt-0.5 text-[13px] italic leading-5 text-stone-600">
          {step.message}
        </p>
      )}
    </div>
  );
}

export default AgentTimeline;
