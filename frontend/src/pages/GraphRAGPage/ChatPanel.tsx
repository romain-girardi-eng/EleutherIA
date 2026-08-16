import { useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { RotateCw } from 'lucide-react';
import MessageBubble from './MessageBubble';
import ChatInput from './ChatInput';
import RunTabs from './RunTabs';
import type { RunTabItem } from './RunTabs';
import { TerminalLoader } from '../../components/ui/terminal-loader';
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
  /** True while the ACTIVE run streams — other runs may stream in background. */
  streaming: boolean;
  /** False once MAX_CONCURRENT_RUNS streams are already in flight. */
  canSubmit: boolean;
  maxConcurrentRuns: number;
  error: string | null;
  onDismissError: () => void;
  /** Page-level, run-independent message (cap reached, server busy). */
  notice?: string | null;
  onDismissNotice?: () => void;
  inputRef: React.RefObject<HTMLInputElement | null>;
  onSubmit: (e: React.FormEvent) => void;
  onStop: () => void;
  onNodeClick: (nodeId: string) => void;
  onCitationClick: (citationIndex: number) => void;
  onPassageCitationClick?: (passageId: string) => void;
  /** Called when a [P_<kg_node_id>: ...] inline scholar/argument badge is clicked. */
  onNodeCitationClick?: (nodeId: string) => void;
  runs: RunTabItem[];
  activeRunId: string | null;
  onRunSelect: (runId: string) => void;
  onRunClose: (runId: string) => void;
  onRetry: () => void;
  lastMetrics?: LastMetrics | null;
  /** When non-null, the current assistant answer was served from cache. */
  cacheInfo?: CacheBadgeInfo | null;
  /** Force a fresh (non-cached) re-run of the active question. */
  onRegenerate?: () => void;
}

export default function ChatPanel({
  messages,
  query,
  setQuery,
  streaming,
  canSubmit,
  maxConcurrentRuns,
  error,
  onDismissError,
  notice = null,
  onDismissNotice,
  inputRef,
  onSubmit,
  onStop,
  onNodeClick,
  onCitationClick,
  onPassageCitationClick,
  onNodeCitationClick,
  runs,
  activeRunId,
  onRunSelect,
  onRunClose,
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
                disabled={!canSubmit}
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

      {/* One chip per parallel run (hidden while a single run exists) */}
      <RunTabs
        runs={runs}
        activeRunId={activeRunId}
        onSelect={onRunSelect}
        onClose={onRunClose}
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
              onNodeCitationClick={onNodeCitationClick}
            />
          ))}
        </AnimatePresence>

        {streaming && !messages.some(m => m.role === 'assistant') && (
          <motion.div
            key="terminal-loader"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="flex flex-col justify-center items-center gap-4 min-h-[40vh]"
          >
            <TerminalLoader size="large" />
            <p className="max-w-md text-center text-xs leading-5 text-amber-800/90">
              Deep scholarly research can take{' '}
              <strong className="font-semibold">5 to 10 minutes</strong>. The scholar
              is reasoning over the controversy map — watch the live reasoning in the
              right-hand panel.
            </p>
          </motion.div>
        )}

        {error && !streaming && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="px-5 py-4 bg-red-50 border border-red-200 text-red-800 rounded-xl text-sm text-center"
          >
            <div className="font-medium mb-1">{t('graphRagUi.queryFailed')}</div>
            {error}
            <button
              onClick={onDismissError}
              className="mt-2 text-red-600 hover:text-red-800 underline text-xs block mx-auto"
            >
              {t('graphRagUi.dismiss')}
            </button>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Run-independent notice (server busy, cap reached) */}
      {notice && (
        <div
          role="status"
          data-testid="run-notice"
          className="shrink-0 mx-4 xl:mx-10 2xl:mx-16 mb-2 flex items-center justify-between gap-3 rounded-xl border border-amber-300 bg-amber-50 px-4 py-2 text-sm text-amber-900"
        >
          <span>{notice}</span>
          {onDismissNotice && (
            <button
              type="button"
              onClick={onDismissNotice}
              className="shrink-0 text-xs text-amber-700 underline hover:text-amber-900"
            >
              {t('graphRagUi.dismiss')}
            </button>
          )}
        </div>
      )}

      {/* Sticky input */}
      <ChatInput
        query={query}
        setQuery={setQuery}
        streaming={streaming}
        canSubmit={canSubmit}
        maxConcurrentRuns={maxConcurrentRuns}
        inputRef={inputRef}
        onSubmit={onSubmit}
        onStop={onStop}
      />
    </div>
  );
}
