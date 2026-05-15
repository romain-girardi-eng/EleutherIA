/**
 * ResearchTimelinePanel — phase-grouped accordion view of the agent's work.
 *
 * Instead of stacking one row per tool call (which grows unboundedly), we
 * bucket the live SSE events into 5 named phases:
 *
 *   1. Classification   – complexity / triage
 *   2. Search           – KG seed search + neighborhood expansion
 *   3. Reading          – passage retrieval + close reading
 *   4. Synthesis        – LLM answer drafting
 *   5. Verification     – citation verifier / counter-evidence
 *
 * The currently active phase is expanded with its sub-events; completed
 * phases collapse to a one-line summary ("Search · 3 tools · 11 nodes · 0.4s")
 * and a checkmark. After the query completes a footer surfaces sources,
 * KG-node count and live token + USD cost.
 */

import { useMemo, useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Brain,
  CheckCircle2,
  ChevronRight,
  Compass,
  FileText,
  GitBranch,
  Loader2,
  ScrollText,
  Coins,
  Network,
  PenLine,
  ShieldCheck,
  Triangle,
} from 'lucide-react';
import { cn } from '../../utils/cn';
import type { AgentStep } from './AgentActivityPanel';
import type { GraphRAGResponse } from '../../types';

type PhaseKey = 'classify' | 'search' | 'read' | 'synthesize' | 'verify';

interface PhaseDef {
  key: PhaseKey;
  label: string;
  Icon: typeof Compass;
}

const PHASES: PhaseDef[] = [
  { key: 'classify', label: 'Classification', Icon: Triangle },
  { key: 'search', label: 'Search', Icon: Compass },
  { key: 'read', label: 'Reading', Icon: ScrollText },
  { key: 'synthesize', label: 'Synthesis', Icon: PenLine },
  { key: 'verify', label: 'Verification', Icon: ShieldCheck },
];

const SEARCH_TOOLS = new Set(['search_nodes', 'get_neighbors', 'explore_subgraph']);
const READ_TOOLS = new Set([
  'search_passages',
  'read_passages',
  'get_node_detail',
  'read_work_section',
]);

function classifyStep(step: AgentStep): PhaseKey {
  if (step.type === 'status') {
    const msg = (step.summary || '').toLowerCase();
    if (msg.includes('classif')) return 'classify';
    if (msg.includes('synthes') || msg.includes('answer') || msg.includes('generat'))
      return 'synthesize';
    if (msg.includes('verif')) return 'verify';
    if (msg.includes('retriev') || msg.includes('found') || msg.includes('embed') || msg.includes('initial'))
      return 'search';
    return 'search';
  }
  if (step.type === 'thinking') {
    if ((step.thinking || '').toLowerCase().includes('synthes')) return 'synthesize';
    return 'read';
  }
  if (step.tool) {
    if (SEARCH_TOOLS.has(step.tool)) return 'search';
    if (READ_TOOLS.has(step.tool)) return 'read';
  }
  return 'read';
}

/** A single tool call as the user perceives it (start+result merged). */
interface ToolCallRow {
  key: string; // stable React key
  tool?: string;
  args?: Record<string, unknown>;
  reason?: string;
  // Latest known status info pulled from tool_result when it arrives.
  done: boolean;
  summary?: string;
  durationMs?: number;
  nodeCount?: number;
  passageCount?: number;
}

/** Anything that isn't a tool call (status, thinking). */
interface NonToolRow {
  key: string;
  kind: 'thinking' | 'status';
  text: string;
  remaining?: number;
}

type RenderRow =
  | ({ rowType: 'tool' } & ToolCallRow)
  | ({ rowType: 'misc' } & NonToolRow);

interface PhaseBucket {
  key: PhaseKey;
  label: string;
  Icon: typeof Compass;
  rows: RenderRow[];
  toolCalls: number; // total tool_result count
  uniqueTools: number;
  nodeCount: number;
  passageCount: number;
  durationMs: number;
  latestSummary: string;
}

function bucketize(steps: AgentStep[]): PhaseBucket[] {
  const map: Record<PhaseKey, PhaseBucket> = Object.fromEntries(
    PHASES.map((p) => [
      p.key,
      {
        key: p.key,
        label: p.label,
        Icon: p.Icon,
        rows: [],
        toolCalls: 0,
        uniqueTools: 0,
        nodeCount: 0,
        passageCount: 0,
        durationMs: 0,
        latestSummary: '',
      } as PhaseBucket,
    ]),
  ) as Record<PhaseKey, PhaseBucket>;

  // Per-phase queue of pending tool_start rows keyed by tool name. When a
  // matching tool_result arrives we update that row in place (flipping
  // the spinner to a checkmark) instead of appending a second row — that
  // was the "search row stuck on loader" the user reported.
  const pendingByPhaseTool = new Map<string, ToolCallRow>();

  for (const step of steps) {
    const phase = classifyStep(step);
    const bucket = map[phase];

    if (step.type === 'tool_start') {
      const row: ToolCallRow = {
        key: step.id,
        tool: step.tool,
        args: step.args,
        reason: step.reason,
        done: false,
      };
      bucket.rows.push({ rowType: 'tool', ...row });
      pendingByPhaseTool.set(`${phase}::${step.tool ?? ''}`, row);
      continue;
    }

    if (step.type === 'tool_result') {
      bucket.toolCalls += 1;
      bucket.nodeCount += step.nodeCount ?? 0;
      bucket.passageCount += step.passageCount ?? 0;
      bucket.durationMs += step.durationMs ?? 0;
      if (step.summary) bucket.latestSummary = step.summary;

      const pendingKey = `${phase}::${step.tool ?? ''}`;
      const pending = pendingByPhaseTool.get(pendingKey);
      if (pending) {
        // Mutate the existing pushed row (RenderRow is a struct, the array
        // holds a reference — find and replace).
        const idx = bucket.rows.findIndex(
          (r) => r.rowType === 'tool' && r.key === pending.key,
        );
        if (idx >= 0) {
          bucket.rows[idx] = {
            rowType: 'tool',
            ...pending,
            done: true,
            summary: step.summary,
            durationMs: step.durationMs,
            nodeCount: step.nodeCount,
            passageCount: step.passageCount,
          };
        }
        pendingByPhaseTool.delete(pendingKey);
      } else {
        // Result without a matching start — render it directly as a done row.
        bucket.rows.push({
          rowType: 'tool',
          key: step.id,
          tool: step.tool,
          done: true,
          summary: step.summary,
          durationMs: step.durationMs,
          nodeCount: step.nodeCount,
          passageCount: step.passageCount,
        });
      }
      continue;
    }

    if (step.type === 'thinking') {
      bucket.rows.push({
        rowType: 'misc',
        key: step.id,
        kind: 'thinking',
        text: step.thinking || step.summary || '',
        remaining: step.remaining,
      });
      continue;
    }

    if (step.type === 'status') {
      const text = step.summary || '';
      if (text) bucket.latestSummary = text;
      bucket.rows.push({
        rowType: 'misc',
        key: step.id,
        kind: 'status',
        text,
      });
    }
  }

  for (const k of Object.keys(map) as PhaseKey[]) {
    const toolNames = new Set<string>();
    for (const r of map[k].rows) {
      if (r.rowType === 'tool' && r.tool) toolNames.add(r.tool);
    }
    map[k].uniqueTools = toolNames.size;
  }

  return PHASES.map((p) => map[p.key]);
}

function formatMs(ms: number): string {
  if (ms < 1) return '';
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

function PhaseStatusIcon({
  status,
  Icon,
}: {
  status: 'pending' | 'active' | 'done';
  Icon: typeof Compass;
}) {
  if (status === 'done') {
    return (
      <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-emerald-200 bg-emerald-50 text-emerald-600">
        <CheckCircle2 className="h-4 w-4" />
      </span>
    );
  }
  if (status === 'active') {
    return (
      <span className="relative flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-amber-300 bg-amber-50 text-amber-700">
        <Icon className="h-3.5 w-3.5" />
        <motion.span
          className="absolute inset-0 rounded-full border border-amber-300/70"
          animate={{ scale: [1, 1.4], opacity: [0.6, 0] }}
          transition={{ duration: 1.6, repeat: Infinity }}
        />
      </span>
    );
  }
  return (
    <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-stone-200 bg-stone-50/60 text-stone-300">
      <Icon className="h-3.5 w-3.5" />
    </span>
  );
}

function PhaseRow({
  bucket,
  status,
  expanded,
  onToggle,
}: {
  bucket: PhaseBucket;
  status: 'pending' | 'active' | 'done';
  expanded: boolean;
  onToggle: () => void;
}) {
  const summaryBits: string[] = [];
  if (bucket.toolCalls > 0)
    summaryBits.push(
      `${bucket.toolCalls} ${bucket.toolCalls === 1 ? 'call' : 'calls'}`,
    );
  if (bucket.nodeCount > 0) summaryBits.push(`${bucket.nodeCount} nodes`);
  if (bucket.passageCount > 0) summaryBits.push(`${bucket.passageCount} passages`);
  const dur = formatMs(bucket.durationMs);
  if (dur && status === 'done') summaryBits.push(dur);

  return (
    <div
      className={cn(
        'rounded-2xl border transition-colors',
        status === 'active'
          ? 'border-amber-200/80 bg-amber-50/40'
          : status === 'done'
            ? 'border-stone-200/60 bg-white/60'
            : 'border-stone-200/40 bg-white/30',
      )}
    >
      <button
        type="button"
        onClick={onToggle}
        disabled={status === 'pending'}
        className={cn(
          'flex w-full items-center gap-3 px-3 py-2.5 text-left',
          status === 'pending' && 'cursor-default opacity-60',
        )}
      >
        <PhaseStatusIcon status={status} Icon={bucket.Icon} />
        <div className="min-w-0 flex-1">
          <div className="flex items-baseline gap-2">
            <span
              className={cn(
                'text-[12px] font-semibold uppercase tracking-[0.14em]',
                status === 'done'
                  ? 'text-stone-500'
                  : status === 'active'
                    ? 'text-amber-800'
                    : 'text-stone-300',
              )}
            >
              {bucket.label}
            </span>
            {summaryBits.length > 0 && (
              <span className="truncate text-[11px] text-stone-400">
                · {summaryBits.join(' · ')}
              </span>
            )}
          </div>
          {status === 'active' && bucket.latestSummary && (
            <p className="mt-0.5 truncate text-[11px] italic text-stone-500">
              {bucket.latestSummary}
            </p>
          )}
        </div>
        {status === 'active' && (
          <Loader2 className="h-3.5 w-3.5 shrink-0 animate-spin text-amber-600" />
        )}
        {status !== 'pending' && (
          <motion.span
            animate={{ rotate: expanded ? 90 : 0 }}
            transition={{ duration: 0.18 }}
            className="text-stone-400"
          >
            <ChevronRight className="h-3.5 w-3.5" />
          </motion.span>
        )}
      </button>

      <AnimatePresence initial={false}>
        {expanded && bucket.rows.length > 0 && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.22, ease: 'easeOut' }}
            className="overflow-hidden"
          >
            <div className="space-y-1.5 px-3 pb-3 pl-12">
              {bucket.rows.map((row) => (
                <SubRow key={row.key} row={row} />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function SubRow({ row }: { row: RenderRow }) {
  if (row.rowType === 'misc') {
    if (row.kind === 'thinking') {
      return (
        <div className="flex items-start gap-2">
          <Brain className="mt-0.5 h-3 w-3 shrink-0 text-violet-500" />
          <p className="text-[11.5px] italic leading-4 text-stone-600">
            {row.text}
          </p>
        </div>
      );
    }
    return (
      <p className="text-[11.5px] leading-4 text-stone-400">{row.text}</p>
    );
  }

  const query =
    (row.args?.query as string) ||
    (row.args?.node_id as string) ||
    (Array.isArray(row.args?.seed_node_ids)
      ? (row.args?.seed_node_ids as string[]).slice(0, 2).join(', ')
      : '') ||
    (row.args?.work_id as string) ||
    '';

  return (
    <div className="flex items-start gap-2">
      {row.done ? (
        <CheckCircle2 className="mt-0.5 h-3 w-3 shrink-0 text-emerald-500" />
      ) : (
        <Loader2 className="mt-0.5 h-3 w-3 shrink-0 animate-spin text-amber-600" />
      )}
      <div className="min-w-0 flex-1">
        <div className="flex items-baseline gap-1.5">
          <span className="font-mono text-[11px] text-stone-500">
            {row.tool}
          </span>
          {query && (
            <span className="truncate font-mono text-[11px] text-stone-700">
              {query}
            </span>
          )}
        </div>
        {row.done && row.summary && (
          <p className="mt-0.5 truncate text-[11px] text-stone-500">
            {row.summary}
          </p>
        )}
        <div className="mt-0.5 flex items-center gap-1.5">
          {row.nodeCount !== undefined && row.nodeCount > 0 && (
            <span className="inline-flex items-center gap-0.5 text-[10px] text-blue-700">
              <GitBranch className="h-2.5 w-2.5" />
              {row.nodeCount}
            </span>
          )}
          {row.passageCount !== undefined && row.passageCount > 0 && (
            <span className="inline-flex items-center gap-0.5 text-[10px] text-emerald-700">
              <FileText className="h-2.5 w-2.5" />
              {row.passageCount}
            </span>
          )}
          {row.durationMs !== undefined && row.durationMs > 0 && (
            <span className="text-[10px] text-stone-400">
              {formatMs(row.durationMs)}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

export interface TokenCost {
  total_tokens: number;
  total_cost_usd: number;
}

interface Props {
  steps: AgentStep[];
  isActive: boolean;
  response: GraphRAGResponse | null;
  cost?: TokenCost;
  onOpenSources?: () => void;
  className?: string;
}

export default function ResearchTimelinePanel({
  steps,
  isActive,
  response,
  cost,
  onOpenSources,
  className,
}: Props) {
  const buckets = useMemo(() => bucketize(steps), [steps]);
  const lastWithSteps = useMemo(() => {
    for (let i = buckets.length - 1; i >= 0; i--) {
      if (buckets[i].rows.length > 0) return i;
    }
    return -1;
  }, [buckets]);

  const phaseStatus = (i: number): 'pending' | 'active' | 'done' => {
    const b = buckets[i];
    if (b.rows.length === 0) return 'pending';
    if (!isActive) return 'done';
    if (i === lastWithSteps) return 'active';
    return 'done';
  };

  const [manuallyExpanded, setManuallyExpanded] = useState<Set<PhaseKey>>(
    new Set(),
  );

  const toggle = (k: PhaseKey) => {
    setManuallyExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(k)) next.delete(k);
      else next.add(k);
      return next;
    });
  };

  // Auto-expand the active phase; collapse it when it transitions to done.
  useEffect(() => {
    if (!isActive || lastWithSteps < 0) return;
    const active = buckets[lastWithSteps].key;
    setManuallyExpanded((prev) => {
      if (prev.has(active)) return prev;
      const next = new Set(prev);
      next.add(active);
      return next;
    });
  }, [lastWithSteps, isActive, buckets]);

  const sourceCount =
    response?.sources?.length ??
    (Array.isArray(response?.citations?.ancient_sources)
      ? response.citations.ancient_sources.length
      : 0);
  const kgNodeCount =
    (response?.reasoning_path?.starting_nodes?.length ?? 0) +
    (response?.reasoning_path?.expanded_nodes?.length ?? 0);

  const totalCalls = buckets.reduce((sum, b) => sum + b.toolCalls, 0);

  return (
    <div className={cn('flex h-full min-h-0 flex-col', className)}>
      {/* Header */}
      <div className="shrink-0 border-b border-stone-200/50 px-4 py-2.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ScrollText className="h-4 w-4 text-amber-700" />
            <span className="text-[11px] font-semibold uppercase tracking-[0.16em] text-stone-500">
              Agent reasoning
            </span>
          </div>
          <div className="flex items-center gap-2">
            {totalCalls > 0 && (
              <span className="rounded-full bg-stone-100/80 px-2 py-0.5 text-[10px] font-medium text-stone-500">
                {totalCalls} {totalCalls === 1 ? 'call' : 'calls'}
              </span>
            )}
            {isActive ? (
              <span className="flex items-center gap-1 rounded-full bg-amber-50 px-2 py-0.5 text-[10px] font-medium text-amber-700">
                <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-amber-500" />
                Live
              </span>
            ) : response ? (
              <span className="flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-medium text-emerald-700">
                <CheckCircle2 className="h-2.5 w-2.5" />
                Done
              </span>
            ) : null}
          </div>
        </div>
      </div>

      {/* Phases */}
      <div className="min-h-0 flex-1 overflow-y-auto px-3 py-3">
        {steps.length === 0 && !response ? (
          <IdleHero isActive={isActive} />
        ) : (
          <div className="space-y-2">
            {buckets.map((b, i) => (
              <PhaseRow
                key={b.key}
                bucket={b}
                status={phaseStatus(i)}
                expanded={manuallyExpanded.has(b.key)}
                onToggle={() => toggle(b.key)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Summary footer — Sources · KG · Cost */}
      {(sourceCount > 0 || kgNodeCount > 0 || (cost && cost.total_tokens > 0)) && (
        <div className="shrink-0 border-t border-stone-200/50 bg-white/40 px-4 py-2.5">
          <div className="flex items-center justify-between gap-2">
            <button
              type="button"
              onClick={onOpenSources}
              disabled={!onOpenSources}
              className={cn(
                'flex items-center gap-3 text-[11px] font-medium',
                onOpenSources
                  ? 'text-stone-600 hover:text-amber-700'
                  : 'text-stone-500',
              )}
            >
              <span className="inline-flex items-center gap-1">
                <FileText className="h-3 w-3 text-amber-700" />
                {sourceCount} sources
              </span>
              <span className="text-stone-300">·</span>
              <span className="inline-flex items-center gap-1">
                <Network className="h-3 w-3 text-blue-700" />
                {kgNodeCount} nodes
              </span>
              {cost && cost.total_tokens > 0 && (
                <>
                  <span className="text-stone-300">·</span>
                  <span className="inline-flex items-center gap-1">
                    <Coins className="h-3 w-3 text-emerald-700" />
                    {cost.total_tokens.toLocaleString()} tok
                  </span>
                  <span className="text-stone-300">·</span>
                  <span className="font-mono text-emerald-700">
                    ${cost.total_cost_usd.toFixed(4)}
                  </span>
                </>
              )}
            </button>
            {response && onOpenSources && (
              <span className="text-[10px] uppercase tracking-[0.14em] text-amber-700">
                View ›
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function IdleHero({ isActive }: { isActive: boolean }) {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-4 p-8">
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
          {isActive ? 'Scholar at work' : 'Research journal'}
        </p>
        <p className="mt-1 text-[12px] leading-5 text-stone-400">
          {isActive
            ? 'Classifying, searching and reading…'
            : 'Phases of the agent will appear here as it works.'}
        </p>
      </div>
    </div>
  );
}

