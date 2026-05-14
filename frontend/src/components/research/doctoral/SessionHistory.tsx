/**
 * SessionHistory — past research-session drawer.
 *
 * Lists prior conversations via /api/graphrag/conversations with a search
 * input that hits /api/graphrag/conversations/search. Each row exposes
 * "Resume" (load the session into the current view) and "Branch" (fork a
 * new session seeded with the prior context).
 *
 * Layout: a collapsing left-side panel that slides over the timeline. On
 * mobile, it becomes a full-width sheet.
 */

import { useCallback, useEffect, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { GitBranch, History, Play, Search, X } from 'lucide-react';
import { apiClient } from '../../../api/client';
import { useDebounce } from '../../../hooks/useDebounce';
import { cn } from '../../../lib/utils';
import type { Conversation } from '../../../types';
import { useFocusTrap } from '../../../hooks/useFocusTrap';

interface Props {
  open: boolean;
  onClose: () => void;
  onResume: (conversation: Conversation) => void;
  onBranch: (conversation: Conversation) => void;
}

const formatDate = (iso: string): string => {
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
};

export function SessionHistory({
  open,
  onClose,
  onResume,
  onBranch,
}: Props) {
  const { t } = useTranslation();
  const [items, setItems] = useState<Conversation[]>([]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const debouncedQuery = useDebounce(query, 300);
  const focusRef = useFocusTrap(open);

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    setLoading(true);
    setError(null);

    const run = async (): Promise<void> => {
      try {
        const trimmed = debouncedQuery.trim();
        const res = trimmed
          ? await apiClient.searchConversations(trimmed, 50)
          : await apiClient.listConversations(50, 0);
        if (!cancelled) setItems(res.conversations);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    void run();
    return () => {
      cancelled = true;
    };
  }, [open, debouncedQuery]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent): void => {
      if (e.key === 'Escape' && open) onClose();
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  const onResumeClick = useCallback(
    (c: Conversation) => {
      onResume(c);
    },
    [onResume],
  );

  const onBranchClick = useCallback(
    (c: Conversation) => {
      onBranch(c);
    },
    [onBranch],
  );

  if (!open) return null;

  return (
    <AnimatePresence>
      <motion.div
        key="backdrop"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-40 bg-stone-900/30 backdrop-blur-sm md:hidden"
        onClick={onClose}
        aria-hidden="true"
      />
      <motion.aside
        key="panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby="session-history-title"
        ref={focusRef}
        initial={{ x: '-100%' }}
        animate={{ x: 0 }}
        exit={{ x: '-100%' }}
        transition={{ type: 'spring', stiffness: 280, damping: 32 }}
        className="fixed inset-y-0 left-0 z-50 flex w-full max-w-sm flex-col bg-[#fdfaf3] shadow-2xl ring-1 ring-stone-200"
      >
        <header className="flex shrink-0 items-center justify-between gap-3 border-b border-stone-200/70 px-4 py-3">
          <h2
            id="session-history-title"
            className="flex items-center gap-2 font-display text-[14px] font-semibold text-stone-900"
          >
            <History className="h-4 w-4 text-amber-700" aria-hidden="true" />
            {t('research.doctoral.history.title')}
          </h2>
          <button
            type="button"
            onClick={onClose}
            aria-label={t('research.doctoral.close')}
            className="shrink-0 rounded-full p-1 text-stone-500 hover:bg-stone-100"
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        </header>

        <div className="shrink-0 border-b border-stone-200/50 p-3">
          <div className="relative">
            <Search
              className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-stone-400"
              aria-hidden="true"
            />
            <input
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={t('research.doctoral.history.searchPlaceholder')}
              aria-label={t('research.doctoral.history.searchAria')}
              className="w-full rounded-lg border border-stone-200 bg-white/70 py-1.5 pl-7 pr-2.5 text-[13px] text-stone-800 placeholder:text-stone-400 focus:border-amber-300 focus:outline-none focus:ring-1 focus:ring-amber-200"
            />
          </div>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto px-2 py-2">
          {loading && (
            <p className="px-2 py-3 text-[12px] italic text-stone-500">
              {t('research.doctoral.loading')}
            </p>
          )}
          {error && (
            <p className="rounded-md border border-rose-200 bg-rose-50 px-2 py-1.5 text-[12px] text-rose-700">
              {error}
            </p>
          )}
          {!loading && !error && items.length === 0 && (
            <p className="px-2 py-6 text-center text-[12px] italic text-stone-400">
              {t('research.doctoral.history.empty')}
            </p>
          )}
          <ul className="space-y-1.5">
            {items.map((c) => (
              <li
                key={c.conversation_id}
                className={cn(
                  'rounded-lg border border-stone-200/70 bg-white/70 p-2.5 transition hover:border-amber-300 hover:bg-amber-50/40',
                )}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-[12.5px] font-medium text-stone-900">
                      {c.title ?? c.last_message_preview ?? t('research.doctoral.history.untitled')}
                    </p>
                    <p className="mt-0.5 text-[10.5px] uppercase tracking-wider text-stone-400">
                      {formatDate(c.updated_at)} ·{' '}
                      {t('research.doctoral.history.messages', {
                        count: c.message_count,
                      })}
                    </p>
                    {c.settings?.rigor_level && (
                      <span className="mt-1 inline-block rounded-full bg-amber-50 px-2 py-0.5 text-[10px] font-medium text-amber-800 ring-1 ring-amber-200">
                        {c.settings.rigor_level}
                      </span>
                    )}
                  </div>
                </div>
                <div className="mt-2 flex justify-end gap-1.5">
                  <button
                    type="button"
                    onClick={() => onBranchClick(c)}
                    className="inline-flex items-center gap-1 rounded-md border border-stone-200 bg-white px-2 py-0.5 text-[11px] text-stone-700 hover:bg-stone-50"
                  >
                    <GitBranch className="h-3 w-3" aria-hidden="true" />
                    {t('research.doctoral.history.branch')}
                  </button>
                  <button
                    type="button"
                    onClick={() => onResumeClick(c)}
                    className="inline-flex items-center gap-1 rounded-md border border-amber-300 bg-amber-50 px-2 py-0.5 text-[11px] font-medium text-amber-800 hover:bg-amber-100"
                  >
                    <Play className="h-3 w-3" aria-hidden="true" />
                    {t('research.doctoral.history.resume')}
                  </button>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </motion.aside>
    </AnimatePresence>
  );
}

export default SessionHistory;
