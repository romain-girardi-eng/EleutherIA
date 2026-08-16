import { useTranslation } from 'react-i18next';
import { Check, Loader2, RefreshCw, Square, X } from 'lucide-react';
import type { RunStatus } from './runs';

export interface RunTabItem {
  id: string;
  question: string;
  status: RunStatus;
}

interface RunTabsProps {
  runs: RunTabItem[];
  activeRunId: string | null;
  onSelect: (runId: string) => void;
  onClose: (runId: string) => void;
  onRetry: () => void;
}

function StatusMark({ status }: { status: RunStatus }) {
  const { t } = useTranslation();
  switch (status) {
    case 'streaming':
      return (
        <Loader2
          className="h-3 w-3 shrink-0 animate-spin text-amber-600"
          aria-label={t('graphRagUi.runs.statusStreaming')}
        />
      );
    case 'done':
      return (
        <Check
          className="h-3 w-3 shrink-0 text-emerald-600"
          aria-label={t('graphRagUi.runs.statusDone')}
        />
      );
    case 'stopped':
      return (
        <Square
          className="h-2.5 w-2.5 shrink-0 fill-current text-stone-400"
          aria-label={t('graphRagUi.runs.statusStopped')}
        />
      );
    default:
      return (
        <span
          className="inline-block h-2 w-2 shrink-0 rounded-full bg-red-500"
          role="img"
          aria-label={t('graphRagUi.runs.statusError')}
        />
      );
  }
}

/**
 * One chip per run. Hidden while a single run exists — a lone tab is noise.
 */
export default function RunTabs({
  runs,
  activeRunId,
  onSelect,
  onClose,
  onRetry,
}: RunTabsProps) {
  const { t } = useTranslation();

  if (runs.length <= 1) return null;

  return (
    <div
      className="flex items-center gap-1 overflow-x-auto border-b border-amber-200/40 bg-parchment-50/60 px-2"
      role="tablist"
      aria-label={t('graphRagUi.runs.tabsLabel')}
    >
      {runs.map((run) => {
        const isActive = run.id === activeRunId;
        return (
          <div
            key={run.id}
            className={`flex shrink-0 items-center gap-1.5 rounded-t px-2 py-1.5 transition-colors ${
              isActive
                ? 'border-b-2 border-amber-500 bg-white'
                : 'hover:bg-white/50'
            }`}
          >
            <button
              type="button"
              role="tab"
              aria-selected={isActive}
              onClick={() => onSelect(run.id)}
              title={run.question}
              className={`flex max-w-[11rem] items-center gap-1.5 text-xs ${
                isActive
                  ? 'font-semibold text-stone-800'
                  : 'text-stone-500 hover:text-stone-700'
              }`}
            >
              <StatusMark status={run.status} />
              <span className="truncate">{run.question}</span>
            </button>
            <button
              type="button"
              onClick={() => onClose(run.id)}
              aria-label={t('graphRagUi.runs.close', { question: run.question })}
              className="rounded p-0.5 text-stone-400 transition-colors hover:bg-stone-100 hover:text-stone-700"
            >
              <X className="h-3 w-3" />
            </button>
          </div>
        );
      })}
      <button
        type="button"
        onClick={onRetry}
        className="ml-auto flex shrink-0 items-center gap-1 px-2 py-1 text-xs text-stone-500 transition-colors hover:text-stone-700"
        title={t('graphRagUi.runs.retryTooltip')}
      >
        <RefreshCw className="h-3 w-3" />
        {t('graphRagUi.runs.retryWith')}
      </button>
    </div>
  );
}
