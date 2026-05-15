/**
 * Research — the streaming agentic research page (route: /research).
 *
 * Two runtimes are wired side-by-side:
 *   - "quick"  → Python ReAct backend (fast, ~2 min) via `useResearchStream`
 *   - "deep"   → opencode multi-agent (thorough, ~10-15 min) via `useOpencodeStream`
 * Both hooks expose the same return shape so this component does not branch on
 * the runtime once a query has started.
 */

import { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { Send, Square, Sparkles, RotateCcw, Zap, BookOpen } from 'lucide-react';
import { Button } from '../components/ui/button';
import { ResearchSession } from '../components/research';
import { useResearchStream } from '../hooks/useResearchStream';
import { useOpencodeStream } from '../hooks/useOpencodeStream';

const SUGGESTED_QUERIES_KEYS = [
  'research.suggestions.chrysippusCompatibilism',
  'research.suggestions.augustinePelagius',
  'research.suggestions.stoicFate',
];

const MODE_STORAGE_KEY = 'eleutheria.research.mode';

type Runtime = 'quick' | 'deep';

function readPersistedMode(): Runtime {
  if (typeof window === 'undefined') return 'deep';
  const stored = window.localStorage.getItem(MODE_STORAGE_KEY);
  return stored === 'quick' || stored === 'deep' ? stored : 'deep';
}

export default function Research() {
  const { t } = useTranslation();
  const [query, setQuery] = useState('');
  const [mode, setMode] = useState<Runtime>(readPersistedMode);

  const quickStream = useResearchStream();
  const deepStream = useOpencodeStream();
  const stream = mode === 'quick' ? quickStream : deepStream;

  useEffect(() => {
    if (typeof window === 'undefined') return;
    window.localStorage.setItem(MODE_STORAGE_KEY, mode);
  }, [mode]);

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

  const onModeChange = useCallback(
    (next: Runtime) => {
      if (next === mode || isRunning) return;
      setMode(next);
    },
    [mode, isRunning],
  );

  const modeButtons = useMemo(
    () =>
      [
        {
          id: 'quick' as const,
          label: t('research.modes.quick.label'),
          description: t('research.modes.quick.description'),
          latency: t('research.modes.quick.latency'),
          Icon: Zap,
        },
        {
          id: 'deep' as const,
          label: t('research.modes.deep.label'),
          description: t('research.modes.deep.description'),
          latency: t('research.modes.deep.latency'),
          Icon: BookOpen,
        },
      ],
    [t],
  );

  return (
    <div className="academic-container pt-28 pb-10">
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

      <fieldset
        className="mb-4 rounded-2xl border border-stone-200/70 bg-white/80 p-3 shadow-sm"
        disabled={isRunning}
      >
        <legend className="px-1 text-[11px] font-semibold uppercase tracking-[0.12em] text-stone-500">
          {t('research.modes.legend')}
        </legend>
        <div
          role="radiogroup"
          aria-label={t('research.modes.legend')}
          className="grid gap-2 sm:grid-cols-2"
        >
          {modeButtons.map(({ id, label, description, latency, Icon }) => {
            const selected = mode === id;
            return (
              <button
                key={id}
                type="button"
                role="radio"
                aria-checked={selected}
                onClick={() => onModeChange(id)}
                disabled={isRunning}
                className={[
                  'flex flex-col items-start gap-1 rounded-xl border px-3 py-2 text-left transition',
                  selected
                    ? 'border-amber-400 bg-amber-50/70 text-stone-900'
                    : 'border-stone-200 bg-white/60 text-stone-700 hover:border-amber-300',
                  isRunning ? 'cursor-not-allowed opacity-60' : '',
                ].join(' ')}
              >
                <span className="flex items-center gap-2 text-[13px] font-semibold">
                  <Icon className="h-4 w-4 text-amber-600" aria-hidden="true" />
                  {label}
                  <span className="ml-1 rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-amber-800">
                    {latency}
                  </span>
                </span>
                <span className="text-[12px] text-stone-600">{description}</span>
              </button>
            );
          })}
        </div>
      </fieldset>

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
        tokenUsage={stream.tokenUsage}
        className="min-h-[640px]"
      />
    </div>
  );
}
