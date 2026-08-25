/**
 * Research — the streaming agentic research page (route: /research).
 *
 * Two runtimes are wired side-by-side:
 *   - "quick"  → Python ReAct backend (fast, ~2 min) via `useResearchStream`
 *   - "deep"   → opencode multi-agent (thorough, ~10-15 min) via `useOpencodeStream`
 * Both hooks expose the same return shape so this component does not branch on
 * the runtime once a query has started.
 *
 * Three things the page has to get right BEFORE a query is sent, because each
 * one used to surface as an unactionable "Stream failed — HTTP 4xx":
 *   1. both runtimes bind every query to an authenticated user (cost
 *      accounting), so a logged-out visitor is prompted to sign in rather than
 *      allowed to fire a request that can only 401;
 *   2. the deep runtime only exists where the opencode upstream is proxied —
 *      `useResearchRuntimes` probes it and the option is disabled with a reason
 *      when it is absent;
 *   3. failures are classified (`classifyResearchError`) into something the
 *      reader can act on.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import {
  BookOpen,
  Loader2,
  LogIn,
  RotateCcw,
  Send,
  Sparkles,
  Square,
  Zap,
} from 'lucide-react';
import { Button } from '../components/ui/button';
import AuthModal from '../components/AuthModal';
import { ResearchSession } from '../components/research';
import { useAuth } from '../context/AuthContext';
import { useResearchStream } from '../hooks/useResearchStream';
import { useOpencodeStream } from '../hooks/useOpencodeStream';
import { useResearchRuntimes, type ResearchRuntime } from '../hooks/useResearchRuntimes';
import { classifyResearchError } from '../lib/researchErrors';

const SUGGESTED_QUERIES_KEYS = [
  'research.suggestions.chrysippusCompatibilism',
  'research.suggestions.augustinePelagius',
  'research.suggestions.stoicFate',
];

const MODE_STORAGE_KEY = 'eleutheria.research.mode';

function readPersistedMode(): ResearchRuntime {
  if (typeof window === 'undefined') return 'quick';
  const stored = window.localStorage.getItem(MODE_STORAGE_KEY);
  return stored === 'quick' || stored === 'deep' ? stored : 'quick';
}

function formatElapsed(ms: number): string {
  const total = Math.max(0, Math.floor(ms / 1000));
  const minutes = Math.floor(total / 60);
  const seconds = total % 60;
  return `${minutes}:${String(seconds).padStart(2, '0')}`;
}

export default function Research() {
  const { t } = useTranslation();
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const runtimes = useResearchRuntimes();

  const [query, setQuery] = useState('');
  const [mode, setMode] = useState<ResearchRuntime>(readPersistedMode);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [pendingQuery, setPendingQuery] = useState<string | null>(null);

  const quickStream = useResearchStream();
  const deepStream = useOpencodeStream();

  // A stored `deep` preference must not resurrect a runtime the deployment
  // does not serve — fall back to quick until the probe says otherwise.
  const effectiveMode: ResearchRuntime =
    mode === 'deep' && !runtimes.deep ? 'quick' : mode;
  const stream = effectiveMode === 'quick' ? quickStream : deepStream;

  useEffect(() => {
    if (typeof window === 'undefined') return;
    window.localStorage.setItem(MODE_STORAGE_KEY, mode);
  }, [mode]);

  const isRunning =
    stream.status === 'streaming' ||
    stream.status === 'connecting' ||
    stream.status === 'synthesizing';

  // ── Elapsed-time ticker ────────────────────────────────────────────────
  // A deep run is a 10-15 minute wait behind a silent panel. Showing the
  // stage and the elapsed clock is the difference between "working" and
  // "frozen" for the reader.
  const [elapsedMs, setElapsedMs] = useState(0);
  const startedAtRef = useRef<number | null>(null);
  useEffect(() => {
    if (!isRunning) {
      startedAtRef.current = null;
      return;
    }
    startedAtRef.current ??= Date.now();
    setElapsedMs(Date.now() - startedAtRef.current);
    const id = window.setInterval(() => {
      if (startedAtRef.current !== null) {
        setElapsedMs(Date.now() - startedAtRef.current);
      }
    }, 1000);
    return () => window.clearInterval(id);
  }, [isRunning]);

  const runQuery = useCallback(
    (text: string) => {
      const trimmed = text.trim();
      if (!trimmed) return;
      if (!isAuthenticated) {
        setPendingQuery(trimmed);
        setShowAuthModal(true);
        return;
      }
      void stream.start(trimmed);
    },
    [isAuthenticated, stream],
  );

  const onSubmit = useCallback(
    (e: React.FormEvent<HTMLFormElement>) => {
      e.preventDefault();
      runQuery(query);
    },
    [query, runQuery],
  );

  const onSuggest = useCallback(
    (text: string) => {
      setQuery(text);
      runQuery(text);
    },
    [runQuery],
  );

  const onAuthSuccess = useCallback(() => {
    setShowAuthModal(false);
    if (pendingQuery) {
      const text = pendingQuery;
      setPendingQuery(null);
      void stream.start(text);
    }
  }, [pendingQuery, stream]);

  const onModeChange = useCallback(
    (next: ResearchRuntime) => {
      if (next === mode || isRunning) return;
      if (next === 'deep' && !runtimes.deep) return;
      setMode(next);
    },
    [mode, isRunning, runtimes.deep],
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
          available: true,
        },
        {
          id: 'deep' as const,
          label: t('research.modes.deep.label'),
          description: runtimes.deep
            ? t('research.modes.deep.description')
            : t('research.modes.deep.unavailable'),
          latency: t('research.modes.deep.latency'),
          Icon: BookOpen,
          available: runtimes.deep,
        },
      ],
    [t, runtimes.deep],
  );

  const errorInfo = useMemo(
    () => classifyResearchError(stream.error),
    [stream.error],
  );

  const statusLabel = t(`research.status.${stream.status}`, {
    defaultValue: t('research.status.idle'),
  });

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
          {modeButtons.map(({ id, label, description, latency, Icon, available }) => {
            const selected = effectiveMode === id;
            const blocked = !available || isRunning;
            return (
              <button
                key={id}
                type="button"
                role="radio"
                aria-checked={selected}
                aria-disabled={!available}
                onClick={() => onModeChange(id)}
                disabled={blocked}
                className={[
                  'flex flex-col items-start gap-1 rounded-xl border px-3 py-2 text-left transition',
                  selected
                    ? 'border-amber-400 bg-amber-50/70 text-stone-900'
                    : 'border-stone-200 bg-white/60 text-stone-700 hover:border-amber-300',
                  blocked ? 'cursor-not-allowed opacity-60' : '',
                ].join(' ')}
              >
                <span className="flex items-center gap-2 text-[13px] font-semibold">
                  <Icon className="h-4 w-4 text-amber-600" aria-hidden="true" />
                  {label}
                  <span className="ml-1 rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-amber-800">
                    {latency}
                  </span>
                  {!available && !runtimes.loading && (
                    <span className="rounded-full bg-stone-200 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-stone-600">
                      {t('research.modes.offlineBadge')}
                    </span>
                  )}
                </span>
                <span className="text-[12px] text-stone-600">{description}</span>
              </button>
            );
          })}
        </div>
      </fieldset>

      {!isAuthenticated && !authLoading && (
        <div className="mb-4 flex flex-wrap items-center gap-3 rounded-xl border border-amber-200 bg-amber-50/70 px-4 py-2.5 text-[13px] text-amber-900">
          <LogIn className="h-4 w-4 shrink-0" aria-hidden="true" />
          <span className="min-w-0 flex-1">{t('research.auth.notice')}</span>
          <Button
            type="button"
            size="sm"
            variant="outline"
            onClick={() => setShowAuthModal(true)}
          >
            {t('research.auth.signIn')}
          </Button>
        </div>
      )}

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
          className="flex-1 min-w-0 rounded-xl border border-stone-200 bg-white/60 px-3 py-2 text-base sm:text-[14px] text-stone-800 placeholder:text-stone-400 focus:border-amber-400 focus:outline-none focus:ring-2 focus:ring-amber-100 disabled:opacity-60"
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
          className="mb-4 flex flex-wrap items-center gap-2"
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

      {isRunning && (
        <div
          role="status"
          aria-live="polite"
          className="mb-4 flex flex-wrap items-center gap-3 rounded-xl border border-stone-200/70 bg-white/80 px-4 py-2.5 text-[13px] text-stone-700"
        >
          <Loader2 className="h-4 w-4 animate-spin text-amber-600" aria-hidden="true" />
          <span className="font-medium text-stone-900">{statusLabel}</span>
          <span className="font-mono text-[12px] tabular-nums text-stone-500">
            {formatElapsed(elapsedMs)}
          </span>
          <span className="text-[12px] text-stone-500">
            {effectiveMode === 'deep'
              ? t('research.modes.deep.latency')
              : t('research.modes.quick.latency')}
          </span>
          {stream.retryCount > 0 && (
            <span className="text-[12px] italic text-stone-500">
              {t('research.errors.retrying', { count: stream.retryCount })}
            </span>
          )}
        </div>
      )}

      {errorInfo && (
        <div
          role="alert"
          className="mb-4 flex flex-wrap items-center gap-3 rounded-xl border border-rose-200 bg-rose-50/80 px-4 py-2.5 text-[13px] text-rose-800"
        >
          <span className="min-w-0 flex-1">{t(errorInfo.i18nKey)}</span>
          {errorInfo.needsAuth && (
            <Button
              type="button"
              size="sm"
              variant="outline"
              onClick={() => setShowAuthModal(true)}
            >
              {t('research.auth.signIn')}
            </Button>
          )}
          {errorInfo.retryable && query.trim() && (
            <Button
              type="button"
              size="sm"
              variant="outline"
              onClick={() => runQuery(query)}
            >
              {t('research.errors.retryAction')}
            </Button>
          )}
          <details className="w-full text-[11px] text-rose-600">
            <summary className="cursor-pointer">
              {t('research.errors.technicalDetails')}
            </summary>
            <code className="font-mono">{errorInfo.raw}</code>
          </details>
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
        answerVerification={
          effectiveMode === 'quick' ? quickStream.answerVerification : undefined
        }
        tokenUsage={stream.tokenUsage}
        traceId={stream.traceId ?? undefined}
        sessionId={stream.traceId ?? 'default'}
        onResumeConversation={(c) => {
          const text = c.title?.trim();
          if (text) {
            setQuery(text);
            runQuery(text);
          }
        }}
        onBranchConversation={(c) => {
          const text = c.title?.trim();
          if (text) setQuery(text);
        }}
        onOpenInCosmograph={(nodeId) => {
          window.open(
            `/visualizer?node=${encodeURIComponent(nodeId)}`,
            '_blank',
            'noopener,noreferrer',
          );
        }}
        className="min-h-[640px]"
      />

      <AuthModal
        isOpen={showAuthModal}
        onClose={() => {
          setShowAuthModal(false);
          setPendingQuery(null);
        }}
        onSuccess={onAuthSuccess}
        title={t('research.auth.modalTitle')}
        message={t('research.auth.modalMessage')}
      />
    </div>
  );
}
