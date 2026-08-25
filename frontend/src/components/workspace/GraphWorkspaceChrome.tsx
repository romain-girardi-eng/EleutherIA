import { Check, Link2, Redo2, Route, Undo2 } from 'lucide-react';
import { useState } from 'react';

import { useGraphWorkspace } from '../../context/GraphWorkspaceContext';
import ModeSwitcher from '../canvas/ModeSwitcher';

export default function GraphWorkspaceChrome() {
  const {
    state,
    canUndo,
    canRedo,
    permalink,
    undo,
    redo,
  } = useGraphWorkspace();
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    await navigator.clipboard.writeText(permalink);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1600);
  };

  const controlClass = [
    'inline-flex h-10 w-10 items-center justify-center border-l border-stone-300 outline-none transition-colors focus-visible:ring-2 focus-visible:ring-inset disabled:cursor-not-allowed disabled:opacity-30',
    'text-stone-600 hover:bg-orange-50 hover:text-orange-900 focus-visible:ring-orange-700',
  ].join(' ');

  return (
    <nav
      aria-label="Graph workspace controls"
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
          <span className="block truncate text-sm font-semibold text-stone-900">Critical evidence atlas</span>
        </span>
      </div>

      <div className="pointer-events-auto col-start-2 mx-auto">
        <ModeSwitcher />
      </div>

      <div className="pointer-events-auto col-start-3 ml-auto flex items-center border border-stone-300 bg-[#fffdf9]">
        <div className="hidden px-3 text-right font-body 2xl:block">
          <p className="text-[9px] font-semibold uppercase tracking-[0.16em] text-stone-500">Evidence thread</p>
          <p className="text-[11px] font-semibold text-stone-800">{state.evidenceThread.length} loci · {state.compareIds.length}/4 compared</p>
        </div>
        <button type="button" onClick={undo} disabled={!canUndo} className={controlClass} aria-label="Undo workspace change (Control or Command Z)" title="Undo · ⌘Z">
          <Undo2 className="h-4 w-4" aria-hidden="true" />
        </button>
        <button type="button" onClick={redo} disabled={!canRedo} className={controlClass} aria-label="Redo workspace change (Control or Command Shift Z)" title="Redo · ⇧⌘Z">
          <Redo2 className="h-4 w-4" aria-hidden="true" />
        </button>
        <button type="button" onClick={() => void copy()} className={`${controlClass} hidden sm:inline-flex`} aria-label="Copy a permalink to this workspace state" title="Copy workspace permalink">
          {copied ? <Check className="h-4 w-4" aria-hidden="true" /> : <Link2 className="h-4 w-4" aria-hidden="true" />}
        </button>
      </div>
      <span className="sr-only" aria-live="polite">{copied ? 'Workspace permalink copied.' : ''}</span>
    </nav>
  );
}
