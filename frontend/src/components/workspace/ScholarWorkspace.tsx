import {
  Check,
  GitCompareArrows,
  Link2,
  LoaderCircle,
  Plus,
  RefreshCw,
  Search,
  X,
} from 'lucide-react';
import { useDeferredValue, useEffect, useMemo, useState } from 'react';

import { useGraphWorkspace } from '../../context/GraphWorkspaceContext';
import type { AtlasNodeMeta } from '../cosmograph/AtlasHelpers';

const TABLE_LIMIT = 240;

function matchesFilters(
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

export default function ScholarWorkspace() {
  const {
    state,
    data,
    nodeDetailStates,
    permalink,
    selectPrimary,
    toggleCompare,
    setEvidenceThread,
    ensureNodeDetail,
  } = useGraphWorkspace();
  const [query, setQuery] = useState('');
  const [copied, setCopied] = useState(false);
  const deferredQuery = useDeferredValue(query.trim().toLocaleLowerCase());

  useEffect(() => {
    if (state.primarySelection) void ensureNodeDetail(state.primarySelection);
  }, [ensureNodeDetail, state.primarySelection]);

  const matching = useMemo(() => {
    const filtered = data.meta.filter((node) => {
      if (!matchesFilters(node, state.filters)) return false;
      if (!deferredQuery) return true;
      const haystack = [
        node.label,
        node.typeLabel,
        node.periodLabel,
        node.schoolLabel,
        node.greekTerm,
        node.latinTerm,
      ].join(' ').toLocaleLowerCase();
      return haystack.includes(deferredQuery);
    });
    return filtered.sort((a, b) => b.importance - a.importance || a.label.localeCompare(b.label));
  }, [data.meta, deferredQuery, state.filters]);

  const visible = matching.slice(0, TABLE_LIMIT);
  const selected = state.primarySelection
    ? data.rawById.get(state.primarySelection) ?? null
    : null;
  const selectedRelationships = state.primarySelection
    ? data.relationships.get(state.primarySelection) ?? []
    : [];
  const selectedDetailState = state.primarySelection
    ? nodeDetailStates.get(state.primarySelection)
    : undefined;
  const comparison = state.compareIds
    .map((id) => data.rawById.get(id))
    .filter((node): node is NonNullable<typeof node> => Boolean(node));

  const copyPermalink = async () => {
    await navigator.clipboard.writeText(permalink);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1800);
  };

  return (
    <section
      id="workspace-panel-scholar"
      role="tabpanel"
      aria-labelledby="workspace-mode-scholar"
      tabIndex={0}
      className="absolute inset-0 overflow-y-auto bg-[#fcf9f4] text-stone-900 outline-none"
    >
      <div className="mx-auto w-full max-w-[1720px] px-3 pb-12 pt-24 sm:px-5 lg:px-7 lg:pt-28">
        <header className="flex flex-col gap-5 border-b border-stone-300/80 pb-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="font-body text-[10px] font-semibold uppercase tracking-[0.24em] text-orange-800">
              Research desk · release {state.releaseId?.slice(-10) ?? 'loading'}
            </p>
            <h1 className="mt-2 font-display text-[clamp(2rem,4vw,4.6rem)] leading-none tracking-[-0.03em] text-stone-950">
              Scholar workspace
            </h1>
          </div>
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
            <label className="relative block min-w-0 sm:w-[min(34rem,46vw)]">
              <span className="sr-only">Search the loaded knowledge graph</span>
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-stone-500" aria-hidden="true" />
              <input
                type="search"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search this release—Greek, Latin, scholar, work…"
                className="min-h-11 w-full border border-stone-300 bg-[#fffdf9] pl-10 pr-4 font-body text-base text-stone-900 outline-none placeholder:text-stone-400 focus:border-orange-700 focus:ring-1 focus:ring-orange-700"
              />
            </label>
            <button
              type="button"
              onClick={() => void copyPermalink()}
              className="inline-flex min-h-11 items-center justify-center gap-2 border border-stone-300 bg-[#fffdf9] px-4 font-body text-sm font-semibold text-stone-700 hover:border-orange-600 hover:text-orange-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-700"
            >
              {copied ? <Check className="h-4 w-4" aria-hidden="true" /> : <Link2 className="h-4 w-4" aria-hidden="true" />}
              {copied ? 'Permalink copied' : 'Copy permalink'}
            </button>
          </div>
        </header>

        <div className="mt-5 grid gap-5 xl:grid-cols-[minmax(42rem,1fr)_minmax(19rem,25rem)]">
          <div className="min-w-0 overflow-hidden border border-stone-300 bg-[#fffdf9]">
            <div className="flex min-h-12 items-center justify-between gap-4 border-b border-stone-300 px-4 font-body text-xs text-stone-600">
              <p aria-live="polite">
                <strong className="text-stone-900">{matching.length.toLocaleString()}</strong> matching nodes
                {matching.length > TABLE_LIMIT && ` · showing the first ${TABLE_LIMIT}`}
              </p>
              <p>{state.compareIds.length}/4 compared</p>
            </div>
            <div className="max-h-[calc(100svh-14rem)] overflow-auto">
              <table className="w-full border-collapse font-body text-left text-sm">
                <caption className="sr-only">
                  Knowledge graph nodes in the current release. Select a row for details or add up to four nodes to comparison.
                </caption>
                <thead className="sticky top-0 z-10 bg-[#f1ebe1] text-[10px] font-semibold uppercase tracking-[0.14em] text-stone-600">
                  <tr>
                    <th scope="col" className="w-12 border-b border-stone-300 px-3 py-3 text-center">Compare</th>
                    <th scope="col" className="border-b border-stone-300 px-3 py-3">Node</th>
                    <th scope="col" className="hidden border-b border-stone-300 px-3 py-3 md:table-cell">Type</th>
                    <th scope="col" className="hidden border-b border-stone-300 px-3 py-3 lg:table-cell">Period</th>
                    <th scope="col" className="hidden border-b border-stone-300 px-3 py-3 lg:table-cell">School</th>
                    <th scope="col" className="w-20 border-b border-stone-300 px-3 py-3 text-right">Links</th>
                  </tr>
                </thead>
                <tbody>
                  {visible.map((node) => {
                    const isSelected = state.primarySelection === node.id;
                    const isCompared = state.compareIds.includes(node.id);
                    return (
                      <tr
                        key={node.id}
                        className={isSelected ? 'bg-orange-50' : 'odd:bg-[#fffdf9] even:bg-stone-50/60'}
                      >
                        <td className="border-b border-stone-200 p-0 text-center">
                          <label className="inline-flex min-h-11 min-w-11 cursor-pointer items-center justify-center">
                            <input
                              type="checkbox"
                              checked={isCompared}
                              onChange={() => toggleCompare(node.id)}
                              aria-label={`${isCompared ? 'Remove' : 'Add'} ${node.label} ${isCompared ? 'from' : 'to'} comparison`}
                              className="h-5 w-5 rounded-sm border-stone-400 text-orange-700 focus:ring-orange-700"
                            />
                          </label>
                        </td>
                        <th scope="row" className="border-b border-stone-200 p-0 font-medium">
                          <button
                            type="button"
                            onClick={() => selectPrimary(node.id)}
                            aria-current={isSelected ? 'true' : undefined}
                            className="min-h-12 w-full px-3 py-2 text-left outline-none hover:text-orange-800 focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-orange-700"
                          >
                            <span className="block text-stone-950">{node.label}</span>
                            {(node.greekTerm || node.latinTerm) && (
                              <span className="mt-0.5 block font-reader text-base font-normal text-stone-500">{node.greekTerm || node.latinTerm}</span>
                            )}
                          </button>
                        </th>
                        <td className="hidden border-b border-stone-200 px-3 py-2 text-stone-600 md:table-cell">{node.typeLabel}</td>
                        <td className="hidden border-b border-stone-200 px-3 py-2 text-stone-600 lg:table-cell">{node.periodLabel}</td>
                        <td className="hidden border-b border-stone-200 px-3 py-2 text-stone-600 lg:table-cell">{node.schoolLabel}</td>
                        <td className="border-b border-stone-200 px-3 py-2 text-right tabular-nums text-stone-600">{node.degree.toLocaleString()}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          <aside aria-label="Scholar inspector" className="min-w-0 space-y-6 xl:max-h-[calc(100svh-12rem)] xl:overflow-y-auto xl:pr-1">
            <section
              className="border-t-2 border-stone-900 pt-4"
              aria-busy={selectedDetailState?.loading || undefined}
            >
              <p className="font-body text-[10px] font-semibold uppercase tracking-[0.2em] text-stone-500">Primary selection</p>
              {selected ? (
                <>
                  <h2 className="mt-3 font-display text-3xl leading-tight text-stone-950">{selected.label}</h2>
                  <p className="mt-2 font-body text-xs text-stone-500">{selected.type} · {selected.period || 'Unspecified'} · {selectedRelationships.length} visible relations</p>
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
                  <p className="mt-5 font-reader text-lg leading-7 text-stone-700">{selected.description || 'No editorial description is available for this node yet.'}</p>
                  <button
                    type="button"
                    onClick={() => setEvidenceThread([...state.evidenceThread, selected.id])}
                    className="mt-5 inline-flex min-h-11 items-center gap-2 border border-orange-700 px-4 font-body text-sm font-semibold text-orange-800 hover:bg-orange-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-700"
                  >
                    <Plus className="h-4 w-4" aria-hidden="true" /> Add to evidence thread
                  </button>
                </>
              ) : (
                <p className="mt-3 font-reader text-lg leading-7 text-stone-600">Select a table row. The same node will remain selected when you return to Atlas or Chronos.</p>
              )}
            </section>

            <section className="border-t border-stone-300 pt-4">
              <div className="flex items-center justify-between gap-3">
                <p className="font-body text-[10px] font-semibold uppercase tracking-[0.2em] text-stone-500">Comparison</p>
                <GitCompareArrows className="h-4 w-4 text-stone-400" aria-hidden="true" />
              </div>
              {comparison.length > 0 ? (
                <ol className="mt-3 space-y-3">
                  {comparison.map((node, index) => (
                    <li key={node.id} className="grid grid-cols-[1.5rem_1fr_auto] gap-2 border-b border-stone-200 pb-3">
                      <span className="font-display text-xl text-orange-800">{index + 1}</span>
                      <button type="button" onClick={() => selectPrimary(node.id)} className="min-h-11 text-left font-body text-sm font-semibold text-stone-800 hover:text-orange-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-700">{node.label}</button>
                      <button type="button" onClick={() => toggleCompare(node.id)} aria-label={`Remove ${node.label} from comparison`} className="flex h-11 w-11 items-center justify-center text-stone-500 hover:text-orange-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-700"><X className="h-4 w-4" /></button>
                    </li>
                  ))}
                </ol>
              ) : (
                <p className="mt-3 font-reader text-base leading-6 text-stone-600">Use the table checkboxes to hold up to four nodes side by side.</p>
              )}
            </section>

            <section className="border-t border-stone-300 pt-4">
              <p className="font-body text-[10px] font-semibold uppercase tracking-[0.2em] text-stone-500">Evidence thread · {state.evidenceThread.length}</p>
              {state.evidenceThread.length > 0 ? (
                <ol className="mt-3 border-l border-orange-300 pl-4">
                  {state.evidenceThread.map((id) => {
                    const node = data.rawById.get(id);
                    return (
                      <li key={id} className="relative pb-4 font-body text-sm text-stone-700 before:absolute before:-left-[1.22rem] before:top-1.5 before:h-2 before:w-2 before:rounded-full before:bg-orange-700">
                        <button type="button" onClick={() => selectPrimary(id)} className="inline-flex min-h-11 items-center text-left hover:text-orange-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-700">{node?.label ?? id}</button>
                      </li>
                    );
                  })}
                </ol>
              ) : (
                <p className="mt-3 font-reader text-base leading-6 text-stone-600">Build a citable route by adding selected loci in the order you inspect them.</p>
              )}
            </section>
          </aside>
        </div>
      </div>
    </section>
  );
}
