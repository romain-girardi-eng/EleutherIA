import { Check, Link2, Redo2, Route, Undo2 } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { useGraphWorkspace } from '../../context/GraphWorkspaceContext';
import ModeSwitcher from '../canvas/ModeSwitcher';

const MAX_COMPARED = 4;

export default function GraphWorkspaceChrome() {
  const { t } = useTranslation();
  const {
    state,
    canUndo,
    canRedo,
    permalink,
    undo,
    redo,
  } = useGraphWorkspace();
  const [copied, setCopied] = useState(false);
  const resetTimerRef = useRef<number | null>(null);

  useEffect(() => () => {
    if (resetTimerRef.current !== null) window.clearTimeout(resetTimerRef.current);
  }, []);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(permalink);
    } catch {
      return;
    }
    setCopied(true);
    if (resetTimerRef.current !== null) window.clearTimeout(resetTimerRef.current);
    resetTimerRef.current = window.setTimeout(() => setCopied(false), 1600);
  };

  const controlClass = [
    'inline-flex h-11 w-11 items-center justify-center border-l border-stone-300 outline-none transition-colors focus-visible:ring-2 focus-visible:ring-inset disabled:cursor-not-allowed disabled:opacity-30',
    'text-stone-600 hover:bg-orange-50 hover:text-orange-900 focus-visible:ring-orange-700',
  ].join(' ');

  return (
    <nav
      aria-label={t('workspace.header.nav', 'Graph workspace controls')}
      className="pointer-events-none absolute inset-x-0 top-0 z-[70] grid h-[4.25rem] grid-cols-[1fr_auto_1fr] items-center border-b border-stone-300/80 bg-[#f7f2e9]/96 px-3 shadow-[0_1px_0_rgba(255,255,255,0.8)] backdrop-blur-xl sm:px-5"
    >
      <div
        className="pointer-events-auto hidden min-w-0 items-center gap-3 font-body text-[11px] xl:flex"
      >
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-stone-900 text-[#fffaf1]">
          <Route className="h-4 w-4" aria-hidden="true" />
        </span>
        <span className="min-w-0">
          <span className="block text-[9px] font-bold uppercase tracking-[0.22em] text-orange-800">EleutherIA</span>
          <span className="block truncate text-sm font-semibold text-stone-900">
            {t('workspace.header.title', 'Critical evidence atlas')}
          </span>
        </span>
      </div>

      <div className="pointer-events-auto col-start-2 mx-auto">
        <ModeSwitcher />
      </div>

      <div className="pointer-events-auto col-start-3 ml-auto flex items-center border border-stone-300 bg-[#fffdf9]">
        <div className="hidden px-3 text-right font-body 2xl:block">
          <p className="text-[9px] font-semibold uppercase tracking-[0.16em] text-stone-500">
            {t('workspace.header.thread', 'Evidence thread')}
          </p>
          <p className="text-[11px] font-semibold text-stone-800">
            {t('workspace.header.loci', {
              count: state.evidenceThread.length,
              defaultValue: '{{count, number}} loci',
            })}
            {' · '}
            {t('workspace.header.compared', {
              count: state.compareIds.length,
              max: MAX_COMPARED,
              defaultValue: '{{count}}/{{max}} compared',
            })}
          </p>
        </div>
        <button
          type="button"
          onClick={undo}
          disabled={!canUndo}
          className={controlClass}
          aria-label={t('workspace.header.undo', 'Undo workspace change (Control or Command Z)')}
          title={t('workspace.header.undoTitle', 'Undo · ⌘Z')}
        >
          <Undo2 className="h-4 w-4" aria-hidden="true" />
        </button>
        <button
          type="button"
          onClick={redo}
          disabled={!canRedo}
          className={controlClass}
          aria-label={t('workspace.header.redo', 'Redo workspace change (Control or Command Shift Z)')}
          title={t('workspace.header.redoTitle', 'Redo · ⇧⌘Z')}
        >
          <Redo2 className="h-4 w-4" aria-hidden="true" />
        </button>
        <button
          type="button"
          onClick={() => void copy()}
          className={`${controlClass} hidden sm:inline-flex`}
          aria-label={t('workspace.header.copy', 'Copy a permalink to this workspace state')}
          title={t('workspace.header.copyTitle', 'Copy workspace permalink')}
        >
          {copied ? <Check className="h-4 w-4" aria-hidden="true" /> : <Link2 className="h-4 w-4" aria-hidden="true" />}
        </button>
      </div>
      <span className="sr-only" aria-live="polite">
        {copied ? t('workspace.header.copied', 'Workspace permalink copied.') : ''}
      </span>
    </nav>
  );
}
