import { useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { RotateCw } from 'lucide-react';
import MessageBubble from './MessageBubble';
import ChatInput from './ChatInput';
import { TerminalLoader } from '../../components/ui/terminal-loader';
import { ResponseTabs } from '@/components/ResponseTabs';
import type { ResponseTab } from '@/components/ResponseTabs';
import { TokenBudget } from '@/components/TokenBudget';
import type { GraphRAGChatMessage } from '../../types';
import type { CacheBadgeInfo } from '../../components/research/CostCounter';

interface LastMetrics {
  modelLabel: string;
  retrievalMode: string;
  estimatedCost: number | null;
  answerLengthChars: number;
  modelContext: number;
}

interface ChatPanelProps {
  messages: GraphRAGChatMessage[];
  query: string;
  setQuery: (q: string) => void;
  loading: boolean;
  streaming: boolean;
  error: string | null;
  setError: (e: string | null) => void;
  inputRef: React.RefObject<HTMLInputElement | null>;
  onSubmit: (e: React.FormEvent) => void;
  onStop: () => void;
  onNodeClick: (nodeId: string) => void;
  onCitationClick: (citationIndex: number) => void;
  onPassageCitationClick?: (passageId: string) => void;
  responseTabs: ResponseTab[];
  activeTabId: string;
  onTabChange: (tabId: string) => void;
  onRetry: () => void;
  lastMetrics?: LastMetrics | null;
  /** When non-null, the current assistant answer was served from cache. */
  cacheInfo?: CacheBadgeInfo | null;
  /** Force a fresh (non-cached) re-run of the last user question. */
  onRegenerate?: () => void;
}

export default function ChatPanel({
  messages,
  query,
  setQuery,
  loading,
  streaming,
  error,
  setError,
  inputRef,
  onSubmit,
  onStop,
  onNodeClick,
  onCitationClick,
  onPassageCitationClick,
  responseTabs,
  activeTabId,
  onTabChange,
  onRetry,
  lastMetrics,
  cacheInfo = null,
  onRegenerate,
}: ChatPanelProps) {
  const { t } = useTranslation();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const prevMessagesLengthRef = useRef(0);

  useEffect(() => {
    if (messages.length > prevMessagesLengthRef.current) {
      prevMessagesLengthRef.current = messages.length;
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  return (
    <div className="flex flex-col w-full lg:w-[60%] h-full overflow-hidden border-r border-amber-200/40">
      {/* Fixed header */}
      <div className="shrink-0 flex items-center justify-between px-4 sm:px-6 xl:px-10 py-3 border-b border-amber-200/40 bg-parchment-50/80 backdrop-blur-sm">
        <h1 className="text-xs sm:text-sm xl:text-base font-semibold text-stone-400 uppercase tracking-wider">{t('graphRagUi.chatTitle')}</h1>
        <div className="flex items-center gap-2">
          {cacheInfo &&
            messages.some((m) => m.role === 'assistant') &&
            onRegenerate && (
              <button
                type="button"
                onClick={onRegenerate}
                disabled={streaming || loading}
                aria-label={t('graphRagUi.regenerate.button')}
                title={t('graphRagUi.regenerate.tooltip')}
                className="inline-flex items-center gap-1 rounded-full border border-amber-300 bg-white/80 px-2 py-1 text-[11px] font-medium text-amber-800 hover:bg-amber-50 hover:border-amber-400 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <RotateCw className="h-3 w-3" aria-hidden="true" />
                <span className="hidden sm:inline">
                  {t('graphRagUi.regenerate.label')}
                </span>
              </button>
            )}
          {lastMetrics && (
            <TokenBudget
              modelLabel={lastMetrics.modelLabel}
              retrievalMode={lastMetrics.retrievalMode}
              estimatedCost={lastMetrics.estimatedCost}
              answerLengthChars={lastMetrics.answerLengthChars}
              modelContext={lastMetrics.modelContext}
            />
          )}
        </div>
      </div>

      {/* Response tabs (only visible with 2+ tabs) */}
      <ResponseTabs
        tabs={responseTabs}
        activeTabId={activeTabId}
        onTabChange={onTabChange}
        onRetry={onRetry}
      />

      {/* Scrollable messages */}
      <div className="flex-1 overflow-y-auto px-4 sm:px-6 xl:px-10 2xl:px-16 py-4 sm:py-5 xl:py-8 space-y-4 xl:space-y-6">
        <AnimatePresence>
          {messages.map((message, index) => (
            <MessageBubble
              key={index}
              message={message}
              onNodeClick={onNodeClick}
              onCitationClick={onCitationClick}
              onPassageCitationClick={onPassageCitationClick}
            />
          ))}
        </AnimatePresence>

        {streaming && !messages.some(m => m.role === 'assistant') && (
          <motion.div
            key="terminal-loader"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="flex justify-center items-center min-h-[40vh]"
          >
            <TerminalLoader size="large" />
          </motion.div>
        )}

        {error && !loading && !streaming && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="px-5 py-4 bg-red-50 border border-red-200 text-red-800 rounded-xl text-sm text-center"
          >
            <div className="font-medium mb-1">{t('graphRagUi.queryFailed')}</div>
            {error}
            <button
              onClick={() => setError(null)}
              className="mt-2 text-red-600 hover:text-red-800 underline text-xs block mx-auto"
            >
              {t('graphRagUi.dismiss')}
            </button>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Sticky input */}
      <ChatInput
        query={query}
        setQuery={setQuery}
        loading={loading}
        streaming={streaming}
        inputRef={inputRef}
        onSubmit={onSubmit}
        onStop={onStop}
      />
    </div>
  );
}
