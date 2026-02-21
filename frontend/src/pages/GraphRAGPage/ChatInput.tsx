import { useTranslation } from 'react-i18next';
import { Square } from 'lucide-react';
import { ShineBorder } from '../../components/ui/shine-border';

interface ChatInputProps {
  query: string;
  setQuery: (q: string) => void;
  loading: boolean;
  streaming: boolean;
  inputRef: React.RefObject<HTMLInputElement | null>;
  onSubmit: (e: React.FormEvent) => void;
  onStop: () => void;
}

export default function ChatInput({
  query,
  setQuery,
  loading,
  streaming,
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
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={t('graphrag.placeholder')}
              disabled={loading || streaming}
              className="flex-1 px-6 py-3 xl:py-4 text-[15px] xl:text-base 2xl:text-lg bg-transparent focus:outline-none focus:ring-0 border-0"
            />
            {streaming ? (
              <button
                type="button"
                onClick={onStop}
                className="flex items-center gap-1.5 px-5 py-3 xl:py-4 bg-red-600 text-white rounded-full hover:bg-red-700 font-medium transition-all text-sm xl:text-base"
              >
                <Square className="w-3 h-3 xl:w-4 xl:h-4 fill-current" />
                Stop
              </button>
            ) : (
              <button
                type="submit"
                disabled={loading || !query.trim()}
                className="px-6 py-3 xl:py-4 bg-gradient-to-br from-orange-600 to-orange-500 text-white rounded-full hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all font-medium text-sm xl:text-base"
              >
                {loading ? 'Thinking...' : 'Ask'}
              </button>
            )}
          </div>
        </form>
      </ShineBorder>
    </div>
  );
}
