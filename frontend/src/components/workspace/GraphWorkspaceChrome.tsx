import { Check, Link2, Redo2, Undo2 } from 'lucide-react';
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
    'inline-flex h-11 w-11 items-center justify-center rounded-full border outline-none transition-colors focus-visible:ring-2 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-35',
    'border-stone-300 bg-[#fffdf9]/95 text-stone-700 shadow-[0_8px_24px_rgba(72,52,36,0.08)] hover:border-orange-500 hover:text-orange-800 focus-visible:ring-orange-700 focus-visible:ring-offset-[#f7f2e9]',
  ].join(' ');

  return (
    <nav
      aria-label="Graph workspace controls"
      className="pointer-events-none absolute inset-x-0 top-0 z-[70] flex min-h-16 items-center justify-between gap-2 px-3 sm:px-5 lg:px-7"
    >
      <div
        className={[
          'pointer-events-auto hidden min-w-0 items-center gap-3 font-body text-[11px] xl:flex',
        'text-stone-600',
        ].join(' ')}
      >
        <span className="font-semibold uppercase tracking-[0.18em]">Evidence workspace</span>
        <span aria-hidden>·</span>
        <span>{state.evidenceThread.length} thread steps</span>
        <span aria-hidden>·</span>
        <span>{state.compareIds.length}/4 compared</span>
        {state.releaseId && (
          <>
            <span aria-hidden>·</span>
            <span title={state.releaseId}>release …{state.releaseId.slice(-8)}</span>
          </>
        )}
      </div>

      <div className="pointer-events-auto mx-auto lg:absolute lg:left-1/2 lg:-translate-x-1/2">
        <ModeSwitcher />
      </div>

      <div className="pointer-events-auto flex items-center gap-1">
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
