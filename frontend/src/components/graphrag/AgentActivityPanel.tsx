import { useEffect, useRef } from 'react';
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
  AlertCircle,
} from 'lucide-react';
import { cn } from '../../utils/cn';

export interface AgentStep {
  id: string;
  type: 'thinking' | 'tool_start' | 'tool_result' | 'status';
  tool?: string;
  args?: Record<string, unknown>;
  reason?: string;
  summary?: string;
  thinking?: string;
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

const TOOL_ICONS: Record<string, typeof Search> = {
  search_nodes: Search,
  get_neighbors: GitBranch,
  read_passages: BookOpen,
  search_passages: FileText,
  get_node_detail: Info,
  read_work_section: Map,
  explore_subgraph: GitBranch,
};

const TOOL_LABELS: Record<string, string> = {
  search_nodes: 'Searching nodes',
  get_neighbors: 'Exploring connections',
  read_passages: 'Reading passages',
  search_passages: 'Searching texts',
  get_node_detail: 'Inspecting node',
  read_work_section: 'Browsing work',
  explore_subgraph: 'Exploring subgraph',
};

function ToolStartStep({ step }: { step: AgentStep }) {
  const Icon = (step.tool && TOOL_ICONS[step.tool]) || Search;
  const label = (step.tool && TOOL_LABELS[step.tool]) || step.tool || 'Tool call';
  const query = step.args?.query || step.args?.node_id || '';

  return (
    <div className="flex items-start gap-3">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-amber-100/80 text-amber-700">
        <Icon className="h-4 w-4" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-stone-800">{label}</span>
          <Loader2 className="h-3 w-3 animate-spin text-amber-600" />
        </div>
        {query && (
          <p className="mt-0.5 truncate text-xs text-stone-500">
            {typeof query === 'string' ? query : JSON.stringify(query)}
          </p>
        )}
        {step.reason && (
          <p className="mt-0.5 text-xs italic text-stone-400">{step.reason}</p>
        )}
      </div>
    </div>
  );
}

function ToolResultStep({ step }: { step: AgentStep }) {
  const Icon = (step.tool && TOOL_ICONS[step.tool]) || Search;

  return (
    <div className="flex items-start gap-3">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-emerald-100/80 text-emerald-700">
        <CheckCircle2 className="h-4 w-4" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <Icon className="h-3.5 w-3.5 text-stone-400" />
          <span className="text-sm text-stone-700">{step.summary}</span>
        </div>
        <div className="mt-1 flex flex-wrap gap-1.5">
          {step.durationMs !== undefined && step.durationMs > 0 && (
            <span className="rounded-full bg-stone-100 px-2 py-0.5 text-[10px] text-stone-500">
              {step.durationMs}ms
            </span>
          )}
          {step.nodeCount !== undefined && step.nodeCount > 0 && (
            <span className="rounded-full bg-blue-50 px-2 py-0.5 text-[10px] text-blue-600">
              {step.nodeCount} nodes
            </span>
          )}
          {step.passageCount !== undefined && step.passageCount > 0 && (
            <span className="rounded-full bg-amber-50 px-2 py-0.5 text-[10px] text-amber-600">
              {step.passageCount} passages
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

function ThinkingStep({ step }: { step: AgentStep }) {
  return (
    <div className="flex items-start gap-3">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-violet-100/80 text-violet-700">
        <Brain className="h-4 w-4" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-sm text-stone-600">{step.thinking || step.summary}</p>
        {step.remaining !== undefined && (
          <span className="mt-1 inline-block rounded-full bg-stone-100 px-2 py-0.5 text-[10px] text-stone-500">
            {step.remaining} calls remaining
          </span>
        )}
      </div>
    </div>
  );
}

function StatusStep({ step }: { step: AgentStep }) {
  return (
    <div className="flex items-center gap-3">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-stone-100 text-stone-500">
        <AlertCircle className="h-4 w-4" />
      </div>
      <span className="text-sm text-stone-500">{step.summary}</span>
    </div>
  );
}

export default function AgentActivityPanel({ steps, isActive, className }: AgentActivityPanelProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new steps arrive
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [steps.length]);

  if (steps.length === 0 && !isActive) {
    return (
      <div className={cn('flex items-center justify-center p-8 text-sm text-stone-400', className)}>
        No agent activity yet
      </div>
    );
  }

  return (
    <div
      ref={scrollRef}
      className={cn(
        'flex flex-col gap-3 overflow-y-auto p-4',
        className,
      )}
    >
      <AnimatePresence initial={false}>
        {steps.map((step) => (
          <motion.div
            key={step.id}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
            className="rounded-2xl border border-stone-200/60 bg-white/80 px-4 py-3"
          >
            {step.type === 'tool_start' && <ToolStartStep step={step} />}
            {step.type === 'tool_result' && <ToolResultStep step={step} />}
            {step.type === 'thinking' && <ThinkingStep step={step} />}
            {step.type === 'status' && <StatusStep step={step} />}
          </motion.div>
        ))}
      </AnimatePresence>

      {isActive && (
        <div className="flex items-center justify-center gap-2 py-2 text-xs text-stone-400">
          <Loader2 className="h-3 w-3 animate-spin" />
          Agent exploring...
        </div>
      )}
    </div>
  );
}
