import { Clock3, LibraryBig, Network } from 'lucide-react';
import { useRef, type KeyboardEvent } from 'react';

import {
  useGraphWorkspace,
  type GraphWorkspaceMode,
} from '../../context/GraphWorkspaceContext';
import { preloadWorkspace } from '../workspace/workspaceLoaders';

const MODES: ReadonlyArray<{
  id: GraphWorkspaceMode;
  label: string;
  description: string;
  shortcut: string;
  icon: typeof Network;
}> = [
  {
    id: 'atlas',
    label: 'Atlas',
    description: 'Explore arguments and evidence spatially',
    shortcut: 'Alt+Shift+1',
    icon: Network,
  },
  {
    id: 'chronos',
    label: 'Chronos',
    description: 'Read transmission and debate across time',
    shortcut: 'Alt+Shift+2',
    icon: Clock3,
  },
  {
    id: 'scholar',
    label: 'Scholar',
    description: 'Compare sources in a dense research table',
    shortcut: 'Alt+Shift+3',
    icon: LibraryBig,
  },
];

export default function ModeSwitcher() {
  const { state, setMode } = useGraphWorkspace();
  const refs = useRef<Array<HTMLButtonElement | null>>([]);

  const handleKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    const current = MODES.findIndex((mode) => mode.id === state.mode);
    let next = current;
    if (event.key === 'ArrowRight' || event.key === 'ArrowDown') next = (current + 1) % MODES.length;
    else if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') next = (current - 1 + MODES.length) % MODES.length;
    else if (event.key === 'Home') next = 0;
    else if (event.key === 'End') next = MODES.length - 1;
    else return;

    event.preventDefault();
    preloadWorkspace(MODES[next].id);
    setMode(MODES[next].id);
    refs.current[next]?.focus();
  };

  return (
    <div
      role="tablist"
      aria-label="Knowledge graph workspace mode"
      onKeyDown={handleKeyDown}
      className="inline-flex min-h-11 items-center gap-1 rounded-full border border-stone-300/80 bg-[#fffdf9]/95 p-1 font-body text-stone-700 shadow-[0_8px_30px_rgba(72,52,36,0.10)] backdrop-blur-xl"
    >
      {MODES.map((mode, index) => {
        const Icon = mode.icon;
        const active = state.mode === mode.id;
        return (
          <button
            key={mode.id}
            ref={(element) => { refs.current[index] = element; }}
            type="button"
            role="tab"
            id={`workspace-mode-${mode.id}`}
            aria-selected={active}
            aria-controls={`workspace-panel-${mode.id}`}
            aria-label={`${mode.label}: ${mode.description}. Shortcut ${mode.shortcut}`}
            tabIndex={active ? 0 : -1}
            title={`${mode.description} · ${mode.shortcut}`}
            onFocus={() => preloadWorkspace(mode.id)}
            onPointerEnter={() => preloadWorkspace(mode.id)}
            onTouchStart={() => preloadWorkspace(mode.id)}
            onClick={() => {
              preloadWorkspace(mode.id);
              setMode(mode.id);
            }}
            className={[
              'inline-flex min-h-11 items-center gap-2 rounded-full px-2 py-1.5 text-[12px] font-semibold tracking-[0.01em] outline-none transition-[background-color,color,box-shadow] duration-200 focus-visible:ring-2 focus-visible:ring-offset-2 sm:px-3',
              'focus-visible:ring-orange-700 focus-visible:ring-offset-[#fffdf9]',
              active
                ? 'bg-stone-900 text-[#fffaf1] shadow-[0_8px_24px_-14px_rgba(28,25,23,0.55)]'
                : 'text-stone-600 hover:bg-stone-100 hover:text-stone-950',
            ].join(' ')}
          >
            <Icon className="h-3.5 w-3.5" aria-hidden="true" />
            <span className="hidden min-[390px]:inline">{mode.label}</span>
            <span className="sr-only"> — {mode.description}. Shortcut {mode.shortcut}.</span>
          </button>
        );
      })}
    </div>
  );
}
