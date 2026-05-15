/**
 * AgentTrace — full audit modal for a completed research session.
 *
 * Fetches /api/graphrag/query/{trace_id}/audit, builds a tree from the
 * agent_invocation rows via `parent_agent_id`, and renders each node with
 * its tool calls (args + result_summary expandable), latency, and token
 * count.
 *
 * "Copy as evidence" serialises the full trace JSON to the clipboard so
 * the user can paste it into a footnote / methodology section as audit
 * proof.
 */

import { useEffect, useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import {
  ChevronDown,
  ChevronRight,
  Clipboard,
  Clock,
  Coins,
  Cpu,
  Filter,
  Loader2,
  X,
} from 'lucide-react';
import { cn } from '../../../lib/utils';
import { doctoralApi } from '../../../services/doctoralApi';
import type {
  AgentInvocation,
  AgentInvocationToolCall,
  AuditResponse,
} from '../../../types/doctoral';
import { useFocusTrap } from '../../../hooks/useFocusTrap';
import { formatTokens, formatUsd } from '../CostCounter';

interface Props {
  traceId: string;
  open: boolean;
  onClose: () => void;
}

interface TreeNode extends AgentInvocation {
  children: TreeNode[];
}

const buildTree = (invocations: AgentInvocation[]): TreeNode[] => {
  const map = new Map<string, TreeNode>();
  for (const inv of invocations) {
    map.set(inv.agent_id, { ...inv, children: [] });
  }
  const roots: TreeNode[] = [];
  for (const node of map.values()) {
    if (node.parent_agent_id && map.has(node.parent_agent_id)) {
      map.get(node.parent_agent_id)?.children.push(node);
    } else {
      roots.push(node);
    }
  }
  return roots;
};

export function AgentTrace({ traceId, open, onClose }: Props) {
  const { t } = useTranslation();
  const [audit, setAudit] = useState<AuditResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>('');
  const [copied, setCopied] = useState(false);
  const focusRef = useFocusTrap(open);

  useEffect(() => {
    if (!open || !traceId) return;
    let cancelled = false;
    setLoading(true);
    setError(null);

    const run = async (): Promise<void> => {
      try {
        const res = await doctoralApi.getAudit(traceId);
        if (!cancelled) setAudit(res);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    void run();
    return () => {
      cancelled = true;
    };
  }, [open, traceId]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent): void => {
      if (e.key === 'Escape' && open) onClose();
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  const tree = useMemo(
    () => (audit ? buildTree(audit.invocations) : []),
    [audit],
  );

  const onCopy = async (): Promise<void> => {
    if (!audit) return;
    try {
      await navigator.clipboard.writeText(JSON.stringify(audit, null, 2));
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      // ignore
    }
  };

  if (!open) return null;

  return (
    <AnimatePresence>
      <motion.div
        key="backdrop"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 bg-stone-900/50 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
      />
      <motion.div
        key="dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="agent-trace-title"
        ref={focusRef}
        initial={{ opacity: 0, scale: 0.96 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.96 }}
        className="fixed inset-x-4 inset-y-8 z-50 mx-auto flex max-w-4xl flex-col rounded-2xl bg-[#fdfaf3] shadow-2xl ring-1 ring-stone-200"
      >
        <header className="flex shrink-0 items-center justify-between gap-3 border-b border-stone-200/70 px-5 py-3">
          <div className="min-w-0 flex-1">
            <h2
              id="agent-trace-title"
              className="flex items-center gap-2 font-display text-[15px] font-semibold text-stone-900"
            >
              <Cpu className="h-4 w-4 text-amber-700" aria-hidden="true" />
              {t('research.doctoral.audit.title')}
            </h2>
            {audit && (
              <p className="mt-0.5 truncate text-[11px] font-mono text-stone-500">
                {audit.trace_id}
              </p>
            )}
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label={t('research.doctoral.close')}
            className="shrink-0 rounded-full p-1.5 text-stone-500 hover:bg-stone-100"
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        </header>

        <div className="shrink-0 border-b border-stone-200/50 px-5 py-2">
          <div className="flex flex-wrap items-center gap-3 text-[11px] text-stone-600">
            {audit?.total_duration_ms !== undefined && (
              <span className="inline-flex items-center gap-1">
                <Clock className="h-3 w-3" aria-hidden="true" />
                {(audit.total_duration_ms / 1000).toFixed(2)}s
              </span>
            )}
            {audit?.total_tokens !== undefined && (
              <span className="inline-flex items-center gap-1">
                <Coins className="h-3 w-3" aria-hidden="true" />
                {audit.total_tokens.toLocaleString()} {t('research.doctoral.audit.tokens')}
              </span>
            )}
            {audit?.total_cost_usd !== undefined &&
              audit.total_cost_usd > 0 && (
                <span className="inline-flex items-center gap-1 font-mono text-amber-700">
                  {formatUsd(audit.total_cost_usd)}
                </span>
              )}
            <div className="relative ml-auto">
              <Filter
                className="pointer-events-none absolute left-2 top-1/2 h-3 w-3 -translate-y-1/2 text-stone-400"
                aria-hidden="true"
              />
              <input
                type="search"
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                placeholder={t('research.doctoral.audit.filterPlaceholder')}
                aria-label={t('research.doctoral.audit.filterAria')}
                className="w-44 rounded-md border border-stone-200 bg-white py-1 pl-6 pr-2 text-[11px] placeholder:text-stone-400 focus:border-amber-300 focus:outline-none"
              />
            </div>
          </div>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto px-5 py-3">
          {loading && (
            <div className="flex items-center gap-2 text-[13px] text-stone-500">
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
              {t('research.doctoral.loading')}
            </div>
          )}
          {error && (
            <div className="rounded-lg border border-rose-200 bg-rose-50/70 px-3 py-2 text-[13px] text-rose-700">
              {error}
            </div>
          )}
          {!loading && tree.length === 0 && !error && (
            <p className="px-1 py-6 text-center text-[12px] italic text-stone-400">
              {t('research.doctoral.audit.empty')}
            </p>
          )}
          <ul className="space-y-2">
            {tree.map((node) => (
              <AgentTreeNode key={node.agent_id} node={node} filter={filter} depth={0} />
            ))}
          </ul>
        </div>

        <footer className="flex shrink-0 items-center justify-end gap-2 border-t border-stone-200/70 bg-white/60 px-5 py-3">
          <button
            type="button"
            onClick={onCopy}
            disabled={!audit}
            className="inline-flex items-center gap-1.5 rounded-lg border border-amber-300 bg-amber-50 px-3 py-1.5 text-[12px] font-medium text-amber-800 hover:bg-amber-100 disabled:opacity-50"
          >
            <Clipboard className="h-3.5 w-3.5" aria-hidden="true" />
            {copied
              ? t('research.doctoral.audit.copied')
              : t('research.doctoral.audit.copyAsEvidence')}
          </button>
        </footer>
      </motion.div>
    </AnimatePresence>
  );
}

interface NodeProps {
  node: TreeNode;
  filter: string;
  depth: number;
}

function AgentTreeNode({ node, filter, depth }: NodeProps) {
  const [open, setOpen] = useState(true);
  const matches =
    !filter ||
    node.agent_name.toLowerCase().includes(filter.toLowerCase()) ||
    node.tool_calls.some((tc) =>
      tc.tool.toLowerCase().includes(filter.toLowerCase()),
    );

  if (!matches && node.children.every((c) => !filterMatches(c, filter))) {
    return <></>;
  }

  return (
    <li className={cn(depth > 0 && 'ml-4 border-l border-amber-200/60 pl-3')}>
      <div className="flex items-start gap-2">
        <button
          type="button"
          onClick={() => setOpen((o) => !o)}
          aria-label={open ? 'collapse' : 'expand'}
          className="mt-0.5 rounded p-0.5 text-stone-500 hover:bg-stone-100"
        >
          {open ? (
            <ChevronDown className="h-3 w-3" aria-hidden="true" />
          ) : (
            <ChevronRight className="h-3 w-3" aria-hidden="true" />
          )}
        </button>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="font-mono text-[12.5px] font-semibold text-stone-900">
              {node.agent_name}
            </span>
            <span
              className={cn(
                'rounded-full px-1.5 py-0.5 text-[9px] uppercase tracking-wider',
                node.status === 'failed'
                  ? 'bg-rose-50 text-rose-700'
                  : node.status === 'started'
                    ? 'bg-amber-50 text-amber-700'
                    : 'bg-emerald-50 text-emerald-700',
              )}
            >
              {node.status}
            </span>
            {node.duration_ms !== undefined && (
              <span className="text-[10px] text-stone-500">
                {(node.duration_ms / 1000).toFixed(2)}s
              </span>
            )}
            {node.tokens_used !== undefined && node.tokens_used > 0 && (
              <span className="text-[10px] text-stone-500">
                {formatTokens(node.tokens_used)}t
              </span>
            )}
            {node.cost_usd !== undefined && node.cost_usd > 0 && (
              <span className="font-mono text-[10px] text-amber-700">
                {formatUsd(node.cost_usd)}
              </span>
            )}
            {node.model && (
              <span className="font-mono text-[9px] uppercase tracking-wider text-stone-400">
                {node.model}
              </span>
            )}
          </div>
          {open && node.tool_calls.length > 0 && (
            <ul className="mt-1 space-y-1">
              {node.tool_calls.map((tc) => (
                <ToolCallRow key={tc.tool_call_id} call={tc} />
              ))}
            </ul>
          )}
          {open && node.children.length > 0 && (
            <ul className="mt-1.5 space-y-1.5">
              {node.children.map((c) => (
                <AgentTreeNode
                  key={c.agent_id}
                  node={c}
                  filter={filter}
                  depth={depth + 1}
                />
              ))}
            </ul>
          )}
        </div>
      </div>
    </li>
  );
}

function filterMatches(node: TreeNode, filter: string): boolean {
  if (!filter) return true;
  const q = filter.toLowerCase();
  if (node.agent_name.toLowerCase().includes(q)) return true;
  if (node.tool_calls.some((tc) => tc.tool.toLowerCase().includes(q))) return true;
  return node.children.some((c) => filterMatches(c, filter));
}

function ToolCallRow({ call }: { call: AgentInvocationToolCall }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <li className="rounded-md border border-stone-200/70 bg-white/60 px-2 py-1 text-[11.5px]">
      <button
        type="button"
        onClick={() => setExpanded((e) => !e)}
        className="flex w-full items-center justify-between text-left"
      >
        <span className="font-mono font-medium text-amber-800">{call.tool}</span>
        <div className="flex items-center gap-2 text-[10px] text-stone-500">
          {call.duration_ms !== undefined && (
            <span>{call.duration_ms}ms</span>
          )}
          {expanded ? (
            <ChevronDown className="h-3 w-3" aria-hidden="true" />
          ) : (
            <ChevronRight className="h-3 w-3" aria-hidden="true" />
          )}
        </div>
      </button>
      {expanded && (
        <div className="mt-1 space-y-1">
          <pre className="max-h-40 overflow-auto rounded bg-stone-50 p-1.5 font-mono text-[10px] text-stone-700">
            {JSON.stringify(call.args, null, 2)}
          </pre>
          {call.result_summary && (
            <p className="italic text-stone-600">{call.result_summary}</p>
          )}
        </div>
      )}
    </li>
  );
}

export default AgentTrace;
