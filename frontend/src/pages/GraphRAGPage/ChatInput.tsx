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
    <div className="shrink-0 px-4 py-3 border-t border-gray-200 bg-white/80 backdrop-blur-sm">
      <ShineBorder
        className="!p-0 bg-white/95 backdrop-blur-sm shadow-sm"
        borderRadius={9999}
        color={['#3B82F6', '#6366F1', '#06B6D4']}
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
              className="flex-1 px-6 py-3 text-[15px] bg-transparent focus:outline-none focus:ring-0 border-0"
            />
            {streaming ? (
              <button
                type="button"
                onClick={onStop}
                className="flex items-center gap-1.5 px-5 py-3 bg-red-600 text-white rounded-full hover:bg-red-700 font-medium transition-all text-sm"
              >
                <Square className="w-3 h-3 fill-current" />
                Stop
              </button>
            ) : (
              <button
                type="submit"
                disabled={loading || !query.trim()}
                className="px-6 py-3 bg-gradient-to-br from-gray-900 to-gray-800 text-white rounded-full hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all font-medium text-sm"
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
