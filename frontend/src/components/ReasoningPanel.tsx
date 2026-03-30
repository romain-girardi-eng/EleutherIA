import { useState } from 'react';

interface ReasoningStep {
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
  steps: ReasoningStep[];
}

export function ReasoningPanel({ steps }: ReasoningPanelProps) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  if (steps.length === 0) {
    return (
      <div className="p-4 text-sm text-zinc-500">
        No reasoning trace available.
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-1 p-2">
      <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-500 px-2 pb-1">
        FSM Reasoning Trace
      </h3>
      {steps.map((step, i) => (
        <div
          key={i}
          className={`rounded border text-xs ${
            step.skipped
              ? 'border-zinc-800 bg-zinc-900/50 opacity-60'
              : 'border-zinc-700 bg-zinc-900'
          }`}
        >
          <button
            onClick={() => setExpandedIndex(expandedIndex === i ? null : i)}
            className="flex w-full items-center justify-between px-3 py-2 text-left"
          >
            <div className="flex items-center gap-2">
              <span className="font-mono text-zinc-300">{step.node}</span>
              {step.skipped && (
                <span className="rounded bg-zinc-800 px-1.5 py-0.5 text-zinc-500">
                  skipped
                </span>
              )}
            </div>
            <div className="flex items-center gap-2 text-zinc-500">
              {step.model && <span>{step.model.split('/').pop()}</span>}
              <span>{step.duration_ms}ms</span>
            </div>
          </button>
          {expandedIndex === i && (
            <div className="border-t border-zinc-800 px-3 py-2">
              {step.skipped ? (
                <p className="text-zinc-500">{step.skip_reason}</p>
              ) : (
                <>
                  {step.thinking && (
                    <details className="mb-2">
                      <summary className="cursor-pointer text-blue-400">
                        Chain of Thought
                      </summary>
                      <pre className="mt-1 whitespace-pre-wrap text-zinc-400 font-mono text-[11px] leading-relaxed max-h-64 overflow-y-auto">
                        {step.thinking}
                      </pre>
                    </details>
                  )}
                  <pre className="whitespace-pre-wrap text-zinc-300 font-mono text-[11px] leading-relaxed max-h-96 overflow-y-auto">
                    {step.raw_output}
                  </pre>
                  {step.parsed_result && (
                    <details className="mt-2">
                      <summary className="cursor-pointer text-zinc-500">
                        Parsed Result
                      </summary>
                      <pre className="mt-1 text-zinc-400 font-mono text-[11px]">
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
