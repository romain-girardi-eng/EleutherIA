import { useTranslation } from 'react-i18next';
import { Square } from 'lucide-react';
import { ShineBorder } from '../../components/ui/shine-border';
import { ScholarlyWaitExpectation } from './WaitingExperience';

interface ChatInputProps {
  query: string;
  setQuery: (q: string) => void;
  /** True while the ACTIVE run streams — Stop only ever stops that one. */
  streaming: boolean;
  /** False once the concurrent-run cap is reached. */
  canSubmit: boolean;
  maxConcurrentRuns: number;
  inputRef: React.RefObject<HTMLInputElement | null>;
  onSubmit: (e: React.FormEvent) => void;
  onStop: () => void;
}

export default function ChatInput({
  query,
  setQuery,
  streaming,
  canSubmit,
  maxConcurrentRuns,
  inputRef,
  onSubmit,
  onStop,
}: ChatInputProps) {
  const { t } = useTranslation();

  return (
    <div className="shrink-0 px-4 xl:px-10 2xl:px-16 py-3 xl:py-4 border-t border-amber-200/40 bg-parchment-50/80 backdrop-blur-sm">
      <ShineBorder
        className="!p-0 bg-white/95 backdrop-blur-sm shadow-sm"
        borderRadius={9999}
        color={['#fdba74', '#f97316', '#fbbf24']}
      >
        <form onSubmit={onSubmit} className="p-2">
          <div className="flex gap-2">
            {/* The ask box stays live during a stream: a new question opens a
                new run instead of waiting for the current one. */}
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={t('graphrag.placeholder')}
              className="flex-1 min-w-0 px-4 sm:px-6 py-3 xl:py-4 text-base xl:text-base 2xl:text-lg bg-transparent focus:outline-none focus:ring-0 border-0"
            />
            {streaming && (
              <button
                type="button"
                onClick={onStop}
                aria-label={t('graphRagUi.runs.stopAria')}
                className="flex items-center gap-1.5 px-4 sm:px-5 py-3 xl:py-4 min-h-[44px] bg-red-600 text-white rounded-full hover:bg-red-700 font-medium transition-all text-sm xl:text-base"
              >
                <Square className="w-3 h-3 xl:w-4 xl:h-4 fill-current" />
                {t('graphRagUi.runs.stop')}
              </button>
            )}
            <button
              type="submit"
              disabled={!canSubmit || !query.trim()}
              aria-label={t('graphrag.ask')}
              className="px-4 sm:px-6 py-3 xl:py-4 min-h-[44px] bg-gradient-to-br from-orange-600 to-orange-500 text-white rounded-full hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all font-medium text-sm xl:text-base"
            >
              {t('graphrag.ask')}
            </button>
          </div>
        </form>
      </ShineBorder>
      <ScholarlyWaitExpectation className="mt-2" />
      {!canSubmit && (
        <p className="mt-2 px-2 text-xs text-amber-800" data-testid="run-cap-hint">
          {t('graphRagUi.runs.capReached', { max: maxConcurrentRuns })}
        </p>
      )}
    </div>
  );
}
