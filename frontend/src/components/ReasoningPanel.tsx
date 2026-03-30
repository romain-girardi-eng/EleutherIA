import { useState } from 'react';
import { ChevronDown, ChevronRight, SkipForward, Clock, Cpu } from 'lucide-react';

export interface ReasoningTraceStep {
  node: string;
  duration_ms: number;
  model: string | null;
  skipped: boolean;
  skip_reason: string | null;
  raw_output: string;
  thinking: string | null;
  parsed_result: Record<string, unknown> | null;
}

interface ReasoningPanelProps {
  steps: ReasoningTraceStep[];
}

export function ReasoningPanel({ steps }: ReasoningPanelProps) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  if (steps.length === 0) {
    return (
      <div className="p-4 text-sm text-stone-400 italic">
        No reasoning trace available.
      </div>
    );
  }

  const totalDuration = steps.reduce((sum, s) => sum + s.duration_ms, 0);

  return (
    <div className="flex flex-col gap-1 p-2">
      <div className="flex items-center justify-between px-2 pb-1">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-stone-500">
          FSM Reasoning Trace
        </h3>
        <span className="inline-flex items-center gap-1 text-[10px] text-stone-400">
          <Clock className="w-3 h-3" />
          {(totalDuration / 1000).toFixed(1)}s total
        </span>
      </div>
      {steps.map((step, i) => (
        <div
          key={i}
          className={`rounded-lg border text-xs ${
            step.skipped
              ? 'border-stone-200/60 bg-stone-50/50 opacity-60'
              : 'border-amber-200/60 bg-white/80'
          }`}
        >
          <button
            onClick={() => setExpandedIndex(expandedIndex === i ? null : i)}
            className="flex w-full items-center justify-between px-3 py-2 text-left hover:bg-parchment-50/50 transition-colors rounded-lg"
          >
            <div className="flex items-center gap-2">
              {expandedIndex === i ? (
                <ChevronDown className="w-3 h-3 text-stone-400" />
              ) : (
                <ChevronRight className="w-3 h-3 text-stone-400" />
              )}
              <span className="font-mono font-medium text-stone-700">{step.node}</span>
              {step.skipped && (
                <span className="inline-flex items-center gap-0.5 rounded bg-stone-100 px-1.5 py-0.5 text-stone-400">
                  <SkipForward className="w-2.5 h-2.5" />
                  skipped
                </span>
              )}
            </div>
            <div className="flex items-center gap-2 text-stone-400">
              {step.model && (
                <span className="inline-flex items-center gap-0.5">
                  <Cpu className="w-2.5 h-2.5" />
                  {step.model.split('/').pop()}
                </span>
              )}
              <span className="tabular-nums">{step.duration_ms}ms</span>
            </div>
          </button>
          {expandedIndex === i && (
            <div className="border-t border-amber-200/40 px-3 py-2">
              {step.skipped ? (
                <p className="text-stone-400 italic">{step.skip_reason}</p>
              ) : (
                <>
                  {step.thinking && (
                    <details className="mb-2">
                      <summary className="cursor-pointer text-amber-700 font-medium hover:text-amber-800">
                        Chain of Thought
                      </summary>
                      <pre className="mt-1 whitespace-pre-wrap text-stone-500 font-mono text-[11px] leading-relaxed max-h-64 overflow-y-auto bg-parchment-50/50 rounded p-2">
                        {step.thinking}
                      </pre>
                    </details>
                  )}
                  <pre className="whitespace-pre-wrap text-stone-600 font-mono text-[11px] leading-relaxed max-h-96 overflow-y-auto bg-parchment-50/50 rounded p-2">
                    {step.raw_output}
                  </pre>
                  {step.parsed_result && (
                    <details className="mt-2">
                      <summary className="cursor-pointer text-stone-400 hover:text-stone-600 font-medium">
                        Parsed Result
                      </summary>
                      <pre className="mt-1 text-stone-500 font-mono text-[11px] bg-parchment-50/50 rounded p-2 max-h-64 overflow-y-auto">
                        {JSON.stringify(step.parsed_result, null, 2)}
                      </pre>
                    </details>
                  )}
                </>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
