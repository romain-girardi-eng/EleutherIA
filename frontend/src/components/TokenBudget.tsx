interface TokenBudgetProps {
  modelLabel: string;
  retrievalMode: string;
  estimatedCost: number | null;
  answerLengthChars: number;
  modelContext: number;
}

function formatK(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${Math.round(n / 1_000)}k`;
  return String(n);
}

export function TokenBudget({
  modelLabel,
  retrievalMode,
  estimatedCost,
  answerLengthChars,
  modelContext,
}: TokenBudgetProps) {
  const estimatedInputTokens = answerLengthChars * 12;

  return (
    <div className="bg-amber-50/50 border border-amber-200/30 rounded px-2 py-1 text-right leading-tight">
      <div className="text-xs text-stone-500 truncate max-w-[180px]">
        {modelLabel}
        {retrievalMode && retrievalMode !== 'auto' && (
          <span className="text-stone-400"> · {retrievalMode}</span>
        )}
      </div>
      <div className="text-xs font-mono text-stone-700">
        {estimatedCost !== null ? (
          <span className="mr-1.5">${estimatedCost.toFixed(3)}</span>
        ) : null}
        <span className="text-stone-500">
          {formatK(estimatedInputTokens)} / {formatK(modelContext)}
        </span>
      </div>
    </div>
  );
}
