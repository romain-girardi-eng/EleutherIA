/**
 * Research — the streaming agentic research page (route: /research).
 *
 * Showcases the new SSE-driven experience: live timeline, citation feed,
 * KG constellation, token-by-token answer. The legacy /graphrag page is
 * untouched.
 */

import { useCallback, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { Send, Square, Sparkles, RotateCcw } from 'lucide-react';
import { Button } from '../components/ui/button';
import { ResearchSession } from '../components/research';
import { useResearchStream } from '../hooks/useResearchStream';

const SUGGESTED_QUERIES_KEYS = [
  'research.suggestions.chrysippusCompatibilism',
  'research.suggestions.augustinePelagius',
  'research.suggestions.stoicFate',
];

export default function Research() {
  const { t } = useTranslation();
  const [query, setQuery] = useState('');
  const stream = useResearchStream();

  const onSubmit = useCallback(
    (e: React.FormEvent<HTMLFormElement>) => {
      e.preventDefault();
      const trimmed = query.trim();
      if (!trimmed) return;
      void stream.start(trimmed);
    },
    [query, stream],
  );

  const onSuggest = useCallback(
    (text: string) => {
      setQuery(text);
      void stream.start(text);
    },
    [stream],
  );

  const isRunning =
    stream.status === 'streaming' ||
    stream.status === 'connecting' ||
    stream.status === 'synthesizing';

  return (
    <div className="academic-container pt-20 pb-10">
      <header className="mb-6">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-amber-600" aria-hidden="true" />
          <h1 className="font-display text-2xl font-semibold tracking-tight text-stone-900">
            {t('research.page.title')}
          </h1>
        </div>
        <p className="mt-2 max-w-3xl text-[14px] leading-6 text-stone-600">
          {t('research.page.intro')}
        </p>
      </header>

      <form
        onSubmit={onSubmit}
        className="mb-4 flex flex-col gap-2 rounded-2xl border border-stone-200/70 bg-white/80 p-3 shadow-sm sm:flex-row sm:items-center"
      >
        <label htmlFor="research-query" className="sr-only">
          {t('research.page.queryLabel')}
        </label>
        <input
          id="research-query"
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={t('research.page.queryPlaceholder')}
          disabled={isRunning}
          className="flex-1 rounded-xl border border-stone-200 bg-white/60 px-3 py-2 text-[14px] text-stone-800 placeholder:text-stone-400 focus:border-amber-400 focus:outline-none focus:ring-2 focus:ring-amber-100 disabled:opacity-60"
        />
        <div className="flex gap-2">
          {isRunning ? (
            <Button
              type="button"
              variant="outline"
              onClick={stream.cancel}
              className="gap-2"
            >
              <Square className="h-3.5 w-3.5" aria-hidden="true" />
              {t('research.page.cancel')}
            </Button>
          ) : (
            <Button type="submit" disabled={!query.trim()} className="gap-2">
              <Send className="h-3.5 w-3.5" aria-hidden="true" />
              {t('research.page.send')}
            </Button>
          )}
          {(stream.status === 'complete' ||
            stream.status === 'cancelled' ||
            stream.status === 'error') && (
            <Button
              type="button"
              variant="ghost"
              onClick={stream.reset}
              className="gap-2"
            >
              <RotateCcw className="h-3.5 w-3.5" aria-hidden="true" />
              {t('research.page.newSession')}
            </Button>
          )}
        </div>
      </form>

      {stream.status === 'idle' && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-4 flex flex-wrap gap-2"
        >
          <span className="text-[11px] font-semibold uppercase tracking-[0.12em] text-stone-500">
            {t('research.page.suggestionsLabel')}
          </span>
          {SUGGESTED_QUERIES_KEYS.map((key) => {
            const label = t(key);
            return (
              <button
                key={key}
                type="button"
                onClick={() => onSuggest(label)}
                className="rounded-full border border-stone-200/70 bg-white/70 px-3 py-1 text-[12px] text-stone-700 hover:border-amber-300 hover:bg-amber-50"
              >
                {label}
              </button>
            );
          })}
        </motion.div>
      )}

      {stream.error && (
        <div
          role="alert"
          className="mb-4 rounded-xl border border-rose-200 bg-rose-50/80 px-4 py-2 text-[13px] text-rose-700"
        >
          {t('research.errors.streamFailed')} — {stream.error}
        </div>
      )}

      {stream.retryCount > 0 && isRunning && (
        <div className="mb-3 text-[12px] italic text-stone-500">
          {t('research.errors.retrying', { count: stream.retryCount })}
        </div>
      )}

      <ResearchSession
        status={stream.status}
        events={stream.events}
        toolCalls={stream.toolCalls}
        activeSubagents={stream.activeSubagents}
        citations={stream.citations}
        kgActivations={stream.kgActivations}
        streamedAnswer={stream.streamedAnswer}
        finalAnswer={stream.finalAnswer}
        className="min-h-[640px]"
      />
    </div>
  );
}
