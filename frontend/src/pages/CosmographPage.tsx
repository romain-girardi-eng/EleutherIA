import { AlertTriangle, LoaderCircle, RefreshCw } from 'lucide-react';
import { lazy, Suspense } from 'react';

import GraphWorkspaceChrome from '../components/workspace/GraphWorkspaceChrome';
import {
  GraphWorkspaceProvider,
  useGraphWorkspace,
  type GraphWorkspaceMode,
} from '../context/GraphWorkspaceContext';
import {
  loadAtlasWorkspace,
  loadChronosWorkspace,
  loadScholarWorkspace,
} from '../components/workspace/workspaceLoaders';

const AtlasWorkspace = lazy(loadAtlasWorkspace);
const ChronosWorkspace = lazy(loadChronosWorkspace);
const ScholarWorkspace = lazy(loadScholarWorkspace);

export default function CosmographPage() {
  return (
    <GraphWorkspaceProvider>
      <GraphWorkspaceShell />
    </GraphWorkspaceProvider>
  );
}

function GraphWorkspaceShell() {
  const { state, loading, error } = useGraphWorkspace();

  return (
    <div
      className="fixed inset-x-0 bottom-0 top-12 overflow-hidden bg-[#f7f2e9]"
      aria-busy={loading}
    >
      <GraphWorkspaceChrome />

      {error ? (
        <WorkspaceLoadError error={error} />
      ) : (
        <Suspense fallback={<WorkspaceSurfaceFallback mode={state.mode} phase="surface" />}>
          <WorkspaceSurface mode={state.mode} />
        </Suspense>
      )}

      {loading && state.mode !== 'atlas' && !error && (
        <WorkspaceSurfaceFallback mode={state.mode} phase="data" overlay />
      )}
    </div>
  );
}

function WorkspaceSurface({ mode }: { mode: GraphWorkspaceMode }) {
  if (mode === 'chronos') return <ChronosWorkspace />;
  if (mode === 'scholar') return <ScholarWorkspace />;
  return <AtlasWorkspace />;
}

export function WorkspaceSurfaceFallback({
  mode,
  phase,
  overlay = false,
}: {
  mode: GraphWorkspaceMode;
  phase: 'surface' | 'data';
  overlay?: boolean;
}) {
  const title = phase === 'surface'
    ? `Opening ${mode === 'atlas' ? 'the Atlas' : mode === 'chronos' ? 'Chronos' : 'Scholar'}…`
    : 'Verifying the complete graph release…';
  return (
    <div
      role="status"
      aria-live="polite"
      aria-label={title}
      className={[
        overlay ? 'absolute inset-0 z-50' : 'absolute inset-0 z-40',
        'flex items-center justify-center bg-[#f7f2e9] px-6 text-stone-900',
      ].join(' ')}
    >
      <div className="flex max-w-sm items-center gap-4 text-left font-body">
        <LoaderCircle
          className={[
            'h-6 w-6 shrink-0 motion-safe:animate-spin',
            'text-orange-800',
          ].join(' ')}
          aria-hidden="true"
        />
        <div>
          <p className="text-sm font-semibold">{title}</p>
          <p className="mt-1 text-xs leading-5 text-stone-500">
            Selection, filters, comparisons, and evidence history remain intact.
          </p>
        </div>
      </div>
    </div>
  );
}

function WorkspaceLoadError({ error }: { error: Error }) {
  return (
    <div
      role="alert"
      className="absolute inset-0 z-[60] flex items-center justify-center bg-[#f7f2e9] px-6 text-stone-900"
    >
      <div className="max-w-lg border-t-2 border-red-800 pt-5">
        <div className="flex items-center gap-3">
          <AlertTriangle className="h-5 w-5 text-red-800" aria-hidden="true" />
          <h1 className="font-display text-2xl">The graph release could not be opened</h1>
        </div>
        <p className="mt-4 font-body text-sm leading-6 text-stone-600">{error.message}</p>
        <button
          type="button"
          onClick={() => window.location.reload()}
          className={[
            'mt-6 inline-flex min-h-11 items-center gap-2 border px-4 font-body text-sm font-semibold outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
            'border-stone-400 text-stone-800 hover:border-red-700 hover:text-red-800 focus-visible:ring-red-800 focus-visible:ring-offset-[#f7f2e9]',
          ].join(' ')}
        >
          <RefreshCw className="h-4 w-4" aria-hidden="true" /> Retry
        </button>
      </div>
    </div>
  );
}
