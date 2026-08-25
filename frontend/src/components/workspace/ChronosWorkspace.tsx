import { ArrowRight, LoaderCircle, RefreshCw, RotateCcw } from 'lucide-react';
import { useEffect, useMemo } from 'react';

import { useGraphWorkspace } from '../../context/GraphWorkspaceContext';
import type { AtlasNodeMeta } from '../cosmograph/AtlasHelpers';
import {
  periodBounds,
  periodIntersectsWindow,
  timelineFromGraph,
} from './chronosTimeline';
import TimelinePanel from './TimelinePanel';

function withinFilters(
  node: AtlasNodeMeta,
  filters: ReturnType<typeof useGraphWorkspace>['state']['filters'],
) {
  if (filters.periods.length > 0 && !filters.periods.includes(node.periodLabel)) return false;
  if (filters.schools.length > 0 && !filters.schools.includes(node.schoolLabel)) return false;
  if (
    filters.types.length > 0 &&
    !filters.types.includes(node.typeKey) &&
    !(node.layer === 'modern' && filters.types.includes('scholar'))
  ) return false;
  return true;
}

function formatYear(value: number | null) {
  if (value === null) return 'Open';
  return value < 0 ? `${Math.abs(value)} BCE` : `${value} CE`;
}

export default function ChronosWorkspace() {
  const {
    state,
    data,
    nodeDetailStates,
    selectPrimary,
    setEvidenceThread,
    setTimeWindow,
    ensureNodeDetail,
  } = useGraphWorkspace();

  useEffect(() => {
    if (state.primarySelection) void ensureNodeDetail(state.primarySelection);
  }, [ensureNodeDetail, state.primarySelection]);

  const filtered = useMemo(
    () => data.meta.filter((node) => {
      if (!withinFilters(node, state.filters)) return false;
      return periodIntersectsWindow(
        periodBounds(node.periodLabel),
        state.timeWindow.start,
        state.timeWindow.end,
      );
    }),
    [data.meta, state.filters, state.timeWindow.end, state.timeWindow.start],
  );
  const filteredIds = useMemo(() => new Set(filtered.map((node) => node.id)), [filtered]);
  const edgeCount = useMemo(
    () => data.edges.filter((edge) => filteredIds.has(edge.source) && filteredIds.has(edge.target)).length,
    [data.edges, filteredIds],
  );
  const timeline = useMemo(
    () => timelineFromGraph(
      filtered,
      edgeCount,
      state.timeWindow.start,
      state.timeWindow.end,
    ),
    [edgeCount, filtered, state.timeWindow.end, state.timeWindow.start],
  );
  const selected = state.primarySelection
    ? data.rawById.get(state.primarySelection) ?? null
    : null;
  const selectedDetailState = state.primarySelection
    ? nodeDetailStates.get(state.primarySelection)
    : undefined;

  const selectFromTimeline = (nodeId: string) => {
    selectPrimary(nodeId);
    setEvidenceThread([...state.evidenceThread, nodeId]);
  };

  return (
    <section
      id="workspace-panel-chronos"
      role="tabpanel"
      aria-labelledby="workspace-mode-chronos"
      tabIndex={0}
      className="absolute inset-0 overflow-y-auto bg-[#f7f2e9] text-stone-900 outline-none"
    >
      <div className="mx-auto w-full max-w-[1560px] px-4 pb-16 pt-24 sm:px-6 lg:px-10 lg:pt-28">
        <header className="grid gap-8 border-b border-stone-300/80 pb-8 lg:grid-cols-[minmax(0,1fr)_minmax(25rem,0.7fr)] lg:items-end">
          <div>
            <p className="font-body text-[11px] font-semibold uppercase tracking-[0.24em] text-orange-800">
              Transmission map · one shared release
            </p>
            <h1 className="mt-3 max-w-4xl font-display text-[clamp(2.4rem,5vw,5.5rem)] leading-[0.92] tracking-[-0.035em] text-stone-950">
              Arguments move through time.
            </h1>
            <p className="mt-5 max-w-2xl font-body text-[15px] leading-7 text-stone-600 sm:text-base">
              Follow when a claim appears, disappears, and returns under a new vocabulary—without losing the selected source or evidence thread.
            </p>
          </div>

          <div className="border-l border-stone-300 pl-5 font-body">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-stone-600">Visible interval</p>
                <p className="mt-1 font-display text-2xl text-stone-900">
                  {formatYear(state.timeWindow.start)} <ArrowRight className="mx-1 inline h-4 w-4" /> {formatYear(state.timeWindow.end)}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setTimeWindow({ start: null, end: null })}
                className="inline-flex min-h-11 items-center gap-2 rounded-full border border-stone-300 px-4 text-sm font-semibold text-stone-700 hover:border-orange-500 hover:text-orange-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-700"
              >
                <RotateCcw className="h-3.5 w-3.5" aria-hidden="true" />
                All time
              </button>
            </div>
            <div className="mt-5 grid grid-cols-2 gap-3">
              <label className="text-xs text-stone-600">
                From year
                <input
                  type="number"
                  value={state.timeWindow.start ?? ''}
                  onChange={(event) => setTimeWindow({
                    ...state.timeWindow,
                    start: event.target.value === '' ? null : Number(event.target.value),
                  })}
                  className="mt-1 min-h-11 w-full border border-stone-300 bg-[#fffdf9] px-3 text-base text-stone-900 outline-none focus:border-orange-600 focus:ring-1 focus:ring-orange-600"
                />
              </label>
              <label className="text-xs text-stone-600">
                To year
                <input
                  type="number"
                  value={state.timeWindow.end ?? ''}
                  onChange={(event) => setTimeWindow({
                    ...state.timeWindow,
                    end: event.target.value === '' ? null : Number(event.target.value),
                  })}
                  className="mt-1 min-h-11 w-full border border-stone-300 bg-[#fffdf9] px-3 text-base text-stone-900 outline-none focus:border-orange-600 focus:ring-1 focus:ring-orange-600"
                />
              </label>
            </div>
          </div>
        </header>

        <div className="mt-8 grid gap-7 xl:grid-cols-[minmax(0,1fr)_20rem]">
          <TimelinePanel timeline={timeline} onSelectNode={selectFromTimeline} />

          <aside
            aria-label="Chronos selection"
            aria-busy={selectedDetailState?.loading || undefined}
            className="border-t border-stone-300 pt-5 xl:border-l xl:border-t-0 xl:pl-6 xl:pt-0"
          >
            <p className="font-body text-[10px] font-semibold uppercase tracking-[0.2em] text-stone-500">
              Current locus
            </p>
            {selected ? (
              <div className="mt-4">
                <p className="font-display text-3xl leading-tight text-stone-950">{selected.label}</p>
                <div className="mt-3 flex flex-wrap gap-2 font-body text-[11px] text-stone-600">
                  <span>{selected.type}</span>
                  {selected.period && <><span aria-hidden>·</span><span>{selected.period}</span></>}
                  {selected.school && <><span aria-hidden>·</span><span>{selected.school}</span></>}
                </div>
                {selectedDetailState?.loading && (
                  <p role="status" aria-live="polite" className="mt-4 flex items-center gap-2 font-body text-sm text-stone-600">
                    <LoaderCircle className="h-4 w-4 text-orange-700 motion-safe:animate-spin" aria-hidden="true" />
                    Loading full editorial detail…
                  </p>
                )}
                {selectedDetailState?.error && (
                  <div role="alert" className="mt-4 border-l-2 border-red-800 pl-3 font-body text-sm leading-6 text-stone-700">
                    <p>Full editorial detail could not be loaded. The release-bound summary remains available.</p>
                    <button
                      type="button"
                      onClick={() => void ensureNodeDetail(selected.id)}
                      className="mt-2 inline-flex min-h-11 items-center gap-2 font-semibold text-red-800 underline decoration-red-300 underline-offset-4 hover:decoration-red-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-800"
                    >
                      <RefreshCw className="h-4 w-4" aria-hidden="true" /> Retry full detail
                    </button>
                  </div>
                )}
                <p className="mt-5 line-clamp-8 font-reader text-lg leading-7 text-stone-700">
                  {selected.description || 'Select this locus in Scholar mode to inspect its sources and relations.'}
                </p>
              </div>
            ) : (
              <p className="mt-4 font-reader text-lg leading-7 text-stone-600">
                Choose a thinker, work, concept, or passage from the chronology. Your selection will remain active in Atlas and Scholar.
              </p>
            )}
            <div className="mt-8 border-t border-stone-300 pt-5">
              <p className="font-body text-[10px] font-semibold uppercase tracking-[0.2em] text-stone-500">Session</p>
              <dl className="mt-3 grid grid-cols-2 gap-y-3 font-body text-sm">
                <dt className="text-stone-500">Nodes</dt><dd className="text-right font-semibold">{timeline.totals.nodes.toLocaleString()}</dd>
                <dt className="text-stone-500">Relations</dt><dd className="text-right font-semibold">{timeline.totals.edges.toLocaleString()}</dd>
                <dt className="text-stone-500">Thread steps</dt><dd className="text-right font-semibold">{state.evidenceThread.length}</dd>
              </dl>
            </div>
          </aside>
        </div>
      </div>
    </section>
  );
}
