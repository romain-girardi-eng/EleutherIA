/**
 * AgentActivityPanel — real-time visualization of the scholarly agent's reasoning.
 *
 * Design concept: a "scriptorium" — watching a scholar work in real time.
 * Each tool call appears as a note in a research journal, with a vertical
 * timeline connecting the steps. The aesthetic follows EleutherIA's parchment
 * + amber + stone palette.
 */

import { useEffect, useRef, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search,
  GitBranch,
  BookOpen,
  FileText,
  Info,
  Map,
  Brain,
  CheckCircle2,
  Loader2,
  Sparkles,
  ScrollText,
  Compass,
  Eye,
} from 'lucide-react';
import { cn } from '../../utils/cn';

export interface AgentStep {
  id: string;
  type: 'thinking' | 'tool_start' | 'tool_result' | 'status' | 'synthesis_reasoning';
  tool?: string;
  args?: Record<string, unknown>;
  reason?: string;
  summary?: string;
  thinking?: string;
  // Live dialectical-synthesis chain-of-thought (accumulated across deltas).
  reasoning?: string;
  stage?: string;
  durationMs?: number;
  nodeCount?: number;
  passageCount?: number;
  remaining?: number;
  timestamp: number;
}

interface AgentActivityPanelProps {
  steps: AgentStep[];
  isActive: boolean;
  className?: string;
}

const TOOL_META: Record<string, { icon: typeof Search; label: string; verb: string; color: string }> = {
  search_nodes: { icon: Compass, label: 'Knowledge Graph', verb: 'Searching', color: 'amber' },
  get_neighbors: { icon: GitBranch, label: 'Connections', verb: 'Exploring', color: 'blue' },
  read_passages: { icon: ScrollText, label: 'Ancient Texts', verb: 'Reading', color: 'emerald' },
  search_passages: { icon: FileText, label: 'Corpus', verb: 'Searching', color: 'violet' },
  get_node_detail: { icon: Eye, label: 'Node Detail', verb: 'Inspecting', color: 'stone' },
  read_work_section: { icon: Map, label: 'Work Structure', verb: 'Navigating', color: 'indigo' },
  explore_subgraph: { icon: Sparkles, label: 'Subgraph', verb: 'Exploring', color: 'orange' },
};

const COLOR_MAP: Record<string, { bg: string; border: string; text: string; dot: string }> = {
  amber: { bg: 'bg-amber-50/90', border: 'border-amber-200/80', text: 'text-amber-800', dot: 'bg-amber-400' },
  blue: { bg: 'bg-blue-50/90', border: 'border-blue-200/80', text: 'text-blue-800', dot: 'bg-blue-400' },
  emerald: { bg: 'bg-emerald-50/90', border: 'border-emerald-200/80', text: 'text-emerald-800', dot: 'bg-emerald-400' },
  violet: { bg: 'bg-violet-50/90', border: 'border-violet-200/80', text: 'text-violet-800', dot: 'bg-violet-400' },
  stone: { bg: 'bg-stone-50/90', border: 'border-stone-200/80', text: 'text-stone-700', dot: 'bg-stone-400' },
  indigo: { bg: 'bg-indigo-50/90', border: 'border-indigo-200/80', text: 'text-indigo-800', dot: 'bg-indigo-400' },
  orange: { bg: 'bg-orange-50/90', border: 'border-orange-200/80', text: 'text-orange-800', dot: 'bg-orange-400' },
};

function extractQuery(args?: Record<string, unknown>): string {
  if (!args) return '';
  const q = args.query || args.node_id || args.seed_node_ids || args.work_id || '';
  if (Array.isArray(q)) return q.slice(0, 2).join(', ');
  return typeof q === 'string' ? q : JSON.stringify(q);
}

function ToolCallCard({ step, index }: { step: AgentStep; index: number }) {
  const meta = (step.tool && TOOL_META[step.tool]) || TOOL_META.search_nodes;
  const colors = COLOR_MAP[meta.color] || COLOR_MAP.amber;
  const Icon = meta.icon;
  const isStart = step.type === 'tool_start';
  const query = extractQuery(step.args);

  return (
    <div className="relative flex gap-3">
      {/* Timeline dot + line */}
      <div className="flex flex-col items-center">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring', stiffness: 400, damping: 20, delay: 0.05 }}
          className={cn(
            'relative z-10 flex h-9 w-9 shrink-0 items-center justify-center rounded-2xl border shadow-sm',
            isStart ? colors.bg : 'bg-white',
            isStart ? colors.border : 'border-emerald-200/80',
          )}
        >
          {isStart ? (
            <Icon className={cn('h-4 w-4', colors.text)} />
          ) : (
            <CheckCircle2 className="h-4 w-4 text-emerald-600" />
          )}
          {isStart && (
            <motion.div
              className={cn('absolute inset-0 rounded-2xl border', colors.border)}
              animate={{ scale: [1, 1.4, 1], opacity: [0.6, 0, 0.6] }}
              transition={{ duration: 2, repeat: Infinity }}
            />
          )}
        </motion.div>
        {/* Connecting line */}
        <div className="w-px flex-1 bg-gradient-to-b from-stone-200/80 to-transparent" />
      </div>

      {/* Card content */}
      <motion.div
        initial={{ opacity: 0, x: -12 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.25, delay: 0.08 }}
        className={cn(
          'mb-2.5 flex-1 rounded-2xl border px-4 py-3',
          isStart
            ? cn(colors.bg, colors.border)
            : 'border-emerald-100/80 bg-white/90',
        )}
      >
        {isStart ? (
          <>
            <div className="flex items-center gap-2">
              <span className={cn('text-[11px] font-semibold uppercase tracking-[0.12em]', colors.text)}>
                {meta.verb}
              </span>
              <span className="text-[10px] text-stone-400">#{index + 1}</span>
              <Loader2 className={cn('ml-auto h-3 w-3 animate-spin', colors.text)} />
            </div>
            {query && (
              <p className="mt-1.5 font-mono text-[13px] font-medium leading-5 text-stone-800">
                {query}
              </p>
            )}
            {step.reason && (
              <p className="mt-1 text-[11px] italic leading-4 text-stone-400">
                {step.reason}
              </p>
            )}
          </>
        ) : (
          <>
            <p className="text-[13px] leading-5 text-stone-700">{step.summary}</p>
            <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
              {step.nodeCount !== undefined && step.nodeCount > 0 && (
                <span className="inline-flex items-center gap-1 rounded-full border border-blue-100 bg-blue-50/80 px-2 py-0.5 text-[10px] font-medium text-blue-700">
                  <GitBranch className="h-2.5 w-2.5" />
                  {step.nodeCount}
                </span>
              )}
              {step.passageCount !== undefined && step.passageCount > 0 && (
                <span className="inline-flex items-center gap-1 rounded-full border border-emerald-100 bg-emerald-50/80 px-2 py-0.5 text-[10px] font-medium text-emerald-700">
                  <BookOpen className="h-2.5 w-2.5" />
                  {step.passageCount}
                </span>
              )}
              {step.durationMs !== undefined && step.durationMs > 0 && (
                <span className="rounded-full border border-stone-100 bg-stone-50/80 px-2 py-0.5 text-[10px] text-stone-500">
                  {step.durationMs}ms
                </span>
              )}
            </div>
          </>
        )}
      </motion.div>
    </div>
  );
}

function ThinkingCard({ step }: { step: AgentStep }) {
  return (
    <div className="relative flex gap-3">
      <div className="flex flex-col items-center">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring', stiffness: 400, damping: 20 }}
          className="relative z-10 flex h-9 w-9 shrink-0 items-center justify-center rounded-2xl border border-violet-200/80 bg-violet-50/90 shadow-sm"
        >
          <Brain className="h-4 w-4 text-violet-700" />
        </motion.div>
        <div className="w-px flex-1 bg-gradient-to-b from-stone-200/80 to-transparent" />
      </div>
      <motion.div
        initial={{ opacity: 0, x: -12 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.25 }}
        className="mb-2.5 flex-1 rounded-2xl border border-violet-100/80 bg-gradient-to-br from-violet-50/60 to-white/90 px-4 py-3"
      >
        <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-violet-700">
          Reasoning
        </p>
        <p className="mt-1 text-[13px] italic leading-5 text-stone-600">
          {step.thinking || step.summary}
        </p>
        {step.remaining !== undefined && (
          <div className="mt-2 flex items-center gap-1.5">
            <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-stone-100">
              <motion.div
                className="h-full rounded-full bg-amber-400/80"
                initial={{ width: '100%' }}
                animate={{ width: `${Math.max(5, (step.remaining / 15) * 100)}%` }}
                transition={{ duration: 0.4 }}
              />
            </div>
            <span className="text-[10px] text-stone-400">{step.remaining} left</span>
          </div>
        )}
      </motion.div>
    </div>
  );
}

function SynthesisReasoningCard({ step }: { step: AgentStep }) {
  const scrollRef = useRef<HTMLDivElement>(null);
  // Keep the live chain-of-thought pinned to its latest line as deltas arrive.
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [step.reasoning]);

  return (
    <div className="relative flex gap-3">
      <div className="flex flex-col items-center">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring', stiffness: 400, damping: 20 }}
          className="relative z-10 flex h-9 w-9 shrink-0 items-center justify-center rounded-2xl border border-amber-300/80 bg-amber-50/90 shadow-sm"
        >
          <Brain className="h-4 w-4 text-amber-700" />
        </motion.div>
        <div className="w-px flex-1 bg-gradient-to-b from-amber-200/80 to-transparent" />
      </div>
      <motion.div
        initial={{ opacity: 0, x: -12 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.25 }}
        className="mb-2.5 flex-1 rounded-2xl border border-amber-100/80 bg-gradient-to-br from-amber-50/60 to-white/90 px-4 py-3"
      >
        <div className="flex items-center gap-2">
          <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-amber-700">
            {step.stage || 'Reasoning over the controversy map'}
          </p>
          <Loader2 className="h-3 w-3 animate-spin text-amber-500/80" aria-hidden />
        </div>
        <div
          ref={scrollRef}
          className="mt-1.5 max-h-56 overflow-y-auto whitespace-pre-wrap font-mono text-[12px] leading-5 text-stone-600"
        >
          {step.reasoning}
        </div>
      </motion.div>
    </div>
  );
}

function StatusCard({ step }: { step: AgentStep }) {
  return (
    <div className="relative flex gap-3">
      <div className="flex flex-col items-center">
        <div className="relative z-10 flex h-9 w-9 shrink-0 items-center justify-center rounded-2xl border border-stone-200/80 bg-stone-50/90">
          <Info className="h-4 w-4 text-stone-400" />
        </div>
        <div className="w-px flex-1 bg-gradient-to-b from-stone-200/80 to-transparent" />
      </div>
      <div className="mb-2.5 flex-1 py-2">
        <p className="text-[12px] text-stone-400">{step.summary}</p>
      </div>
    </div>
  );
}

function IdleState({ isActive }: { isActive: boolean }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex h-full flex-col items-center justify-center gap-4 p-8"
    >
      <div className="relative">
        <div className="flex h-16 w-16 items-center justify-center rounded-[22px] border border-amber-200/60 bg-gradient-to-br from-amber-50 to-white shadow-[0_16px_40px_-20px_rgba(120,53,15,0.25)]">
          <ScrollText className="h-7 w-7 text-amber-700/80" />
        </div>
        {isActive && (
          <>
            {[0, 1, 2].map((i) => (
              <motion.div
                key={i}
                className="absolute inset-0 rounded-[22px] border border-amber-300/40"
                animate={{ scale: [1, 1.5], opacity: [0.5, 0] }}
                transition={{ duration: 2, repeat: Infinity, delay: i * 0.6 }}
              />
            ))}
          </>
        )}
      </div>
      <div className="text-center">
        <p className="font-display text-base font-semibold text-stone-800">
          {isActive ? 'Scholar at work' : 'Research Journal'}
        </p>
        <p className="mt-1 text-[12px] leading-5 text-stone-400">
          {isActive
            ? 'The agent is exploring the knowledge graph...'
            : 'Tool calls and reasoning will appear here as the agent works.'}
        </p>
      </div>
    </motion.div>
  );
}

export default function AgentActivityPanel({ steps, isActive, className }: AgentActivityPanelProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Track tool call index (only for tool_start/tool_result)
  const toolCallIndices = useMemo(() => {
    const indices: Record<string, number> = {};
    let idx = 0;
    for (const step of steps) {
      if (step.type === 'tool_start') {
        indices[step.id] = idx;
        idx++;
      } else if (step.type === 'tool_result') {
        indices[step.id] = idx - 1;
      }
    }
    return indices;
  }, [steps]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
    }
  }, [steps.length]);

  if (steps.length === 0) {
    return (
      <div className={cn('flex h-full', className)}>
        <IdleState isActive={isActive} />
      </div>
    );
  }

  return (
    <div className={cn('flex h-full flex-col', className)}>
      {/* Header */}
      <div className="shrink-0 border-b border-stone-200/50 px-4 py-2.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ScrollText className="h-4 w-4 text-amber-700" />
            <span className="text-[11px] font-semibold uppercase tracking-[0.16em] text-stone-500">
              Research Journal
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="rounded-full bg-stone-100/80 px-2 py-0.5 text-[10px] font-medium text-stone-500">
              {steps.filter((s) => s.type === 'tool_result').length} calls
            </span>
            {isActive && (
              <span className="flex items-center gap-1 rounded-full bg-amber-50 px-2 py-0.5 text-[10px] font-medium text-amber-700">
                <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-amber-500" />
                Live
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Long-run notice: deep scholarly research is a thinking-model synthesis
          that can take several minutes. Surfaced while the agent is active so the
          scholar knows the wait is expected, not a hang. */}
      {isActive && (
        <div className="shrink-0 border-b border-amber-200/40 bg-amber-50/60 px-4 py-2">
          <p className="flex items-center gap-1.5 text-[11px] leading-4 text-amber-800">
            <Loader2 className="h-3 w-3 shrink-0 animate-spin text-amber-600" aria-hidden />
            <span>
              Deep scholarly research can take{' '}
              <strong className="font-semibold">5 to 10 minutes</strong> — the scholar
              is reasoning over the controversy map live below.
            </span>
          </p>
        </div>
      )}

      {/* Timeline */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-4 pt-4"
      >
        <AnimatePresence initial={false}>
          {steps.map((step) => {
            if (step.type === 'tool_start' || step.type === 'tool_result') {
              return (
                <ToolCallCard
                  key={step.id}
                  step={step}
                  index={toolCallIndices[step.id] ?? 0}
                />
              );
            }
            if (step.type === 'thinking') {
              return <ThinkingCard key={step.id} step={step} />;
            }
            if (step.type === 'synthesis_reasoning') {
              return <SynthesisReasoningCard key={step.id} step={step} />;
            }
            if (step.type === 'status') {
              return <StatusCard key={step.id} step={step} />;
            }
            return null;
          })}
        </AnimatePresence>

        {isActive && steps.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex items-center gap-3 pb-4 pl-1"
          >
            <div className="flex h-9 w-9 shrink-0 items-center justify-center">
              <motion.div
                className="h-2.5 w-2.5 rounded-full bg-amber-400"
                animate={{ scale: [1, 1.3, 1], opacity: [0.7, 1, 0.7] }}
                transition={{ duration: 1.5, repeat: Infinity }}
              />
            </div>
            <span className="text-[12px] italic text-stone-400">Scholar thinking...</span>
          </motion.div>
        )}
      </div>
    </div>
  );
}
