import { useState } from 'react';
import { ChevronRight, Wrench } from 'lucide-react';
import { cn } from '../../lib/utils';
import type { PairedToolCall } from '../../hooks/useResearchStream';

interface Props {
  pair: PairedToolCall;
}

export function ToolCallTrace({ pair }: Props) {
  const [open, setOpen] = useState(false);
  const isDone = pair.result !== undefined;
  const duration =
    pair.completed_at && pair.started_at
      ? pair.completed_at - pair.started_at
      : pair.result?.duration_ms;

  return (
    <div className="rounded-xl border border-stone-200/70 bg-white/80">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-2 px-3 py-2 text-left"
        aria-expanded={open}
      >
        <Wrench className="h-3.5 w-3.5 text-stone-500" aria-hidden="true" />
        <span className="font-mono text-[12px] font-semibold text-stone-800">
          {pair.call.tool}
        </span>
        <span
          className={cn(
            'rounded-full px-1.5 py-0.5 text-[10px] font-medium',
            isDone
              ? 'bg-emerald-50 text-emerald-700'
              : 'bg-amber-50 text-amber-700',
          )}
        >
          {isDone ? 'ok' : 'running'}
        </span>
        {duration !== undefined && (
          <span className="text-[10px] text-stone-400">{duration}ms</span>
        )}
        <ChevronRight
          className={cn(
            'ml-auto h-3.5 w-3.5 text-stone-400 transition-transform',
            open && 'rotate-90',
          )}
          aria-hidden="true"
        />
      </button>
      {open && (
        <div className="space-y-2 border-t border-stone-100 px-3 py-2 text-[11px]">
          <div>
            <p className="mb-1 text-[10px] font-semibold uppercase tracking-[0.12em] text-stone-400">
              args
            </p>
            <pre className="max-h-40 overflow-auto rounded bg-stone-50 px-2 py-1 font-mono text-[11px] text-stone-700">
              {JSON.stringify(pair.call.args, null, 2)}
            </pre>
          </div>
          {pair.result && (
            <div>
              <p className="mb-1 text-[10px] font-semibold uppercase tracking-[0.12em] text-stone-400">
                result
              </p>
              <p className="leading-5 text-stone-700">{pair.result.result_summary}</p>
              {(pair.result.nodes_touched?.length ?? 0) > 0 && (
                <p className="mt-1 text-[10px] text-stone-500">
                  nodes: {pair.result.nodes_touched?.length}
                </p>
              )}
              {(pair.result.passages_touched?.length ?? 0) > 0 && (
                <p className="text-[10px] text-stone-500">
                  passages: {pair.result.passages_touched?.length}
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default ToolCallTrace;
