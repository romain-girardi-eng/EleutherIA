import {
  Columns3,
  Grid3x3,
  ListTree,
  PanelBottomOpen,
  Route,
  Search,
  X,
} from 'lucide-react';
import {
  lazy,
  Suspense,
  useCallback,
  useDeferredValue,
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent,
} from 'react';
import { useTranslation } from 'react-i18next';

import { useGraphWorkspace } from '../../context/GraphWorkspaceContext';
import type { AtlasNodeMeta } from '../cosmograph/AtlasHelpers';
import ScholarInspector from './ScholarInspector';
import ScholarNodeTable, { type ScholarNodeTableHandle } from './ScholarNodeTable';
import {
  activeFilterCount,
  buildAdjacency,
  buildSearchIndex,
  computeFacetCounts,
  matchesFacets,
  nextSort,
  searchRows,
  sortRows,
  type Adjacency,
  type ScholarSort,
  type ScholarSortKey,
} from './scholarModel';
import { useScholarLabels } from './useScholarLabels';
import WorkspaceFilterBar from './WorkspaceFilterBar';

const ScholarCompareView = lazy(() => import('./ScholarCompareView'));
const InfluenceMatrixPanel = lazy(() => import('./InfluenceMatrixPanel'));
const PathInspectorPanel = lazy(() => import('./PathInspectorPanel'));

type ScholarView = 'index' | 'compare' | 'matrix' | 'paths';
const VIEWS: ReadonlyArray<ScholarView> = ['index', 'compare', 'matrix', 'paths'];
const VIEW_ICONS = { index: ListTree, compare: Columns3, matrix: Grid3x3, paths: Route } as const;
const DEFAULT_SORT: ScholarSort = { key: 'relevance', direction: 'desc' };
const focusRing = 'outline-none focus-visible:ring-2 focus-visible:ring-orange-700';

function isTypingTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  return target.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName);
}

export default function ScholarWorkspace() {
  const { t } = useTranslation();
  const labels = useScholarLabels();
  const {
    state,
    data,
    loading,
    selectPrimary,
    toggleCompare,
    setEvidenceThread,
    setFilters,
    ensureNodeDetail,
  } = useGraphWorkspace();
  const [query, setQuery] = useState('');
  const [sort, setSort] = useState<ScholarSort>(DEFAULT_SORT);
  const [view, setView] = useState<ScholarView>('index');
  const deferredQuery = useDeferredValue(query);
  const searchRef = useRef<HTMLInputElement>(null);
  const tableRef = useRef<ScholarNodeTableHandle>(null);
  const inspectorRef = useRef<HTMLElement>(null);
  const tabRefs = useRef(new Map<ScholarView, HTMLButtonElement>());
  const captionId = useId();
  const panelId = useId();

  useEffect(() => {
    if (state.primarySelection) void ensureNodeDetail(state.primarySelection);
  }, [ensureNodeDetail, state.primarySelection]);

  const index = useMemo(() => buildSearchIndex(data.meta), [data.meta]);
  const metaById = useMemo(() => {
    const map = new Map<string, AtlasNodeMeta>();
    data.meta.forEach((node) => map.set(node.id, node));
    return map;
  }, [data.meta]);

  // Built on first need only: the index view never pays for it.
  const [needsAdjacency, setNeedsAdjacency] = useState(false);
  useEffect(() => {
    if (view === 'compare' || view === 'paths') setNeedsAdjacency(true);
  }, [view]);
  const adjacency = useMemo<Adjacency | null>(
    () => (needsAdjacency ? buildAdjacency(data.edges) : null),
    [data.edges, needsAdjacency],
  );

  const searched = useMemo(() => searchRows(index, deferredQuery), [deferredQuery, index]);
  const facetCounts = useMemo(() => computeFacetCounts(searched, state.filters), [searched, state.filters]);
  const rows = useMemo(() => {
    const filtered = searched.filter(({ row }) => matchesFacets(row.node, state.filters));
    return sortRows(filtered, sort);
  }, [searched, sort, state.filters]);
  const threadIds = useMemo(() => new Set(state.evidenceThread), [state.evidenceThread]);

  const filtersActive = activeFilterCount(state.filters);
  const searching = deferredQuery.trim().length > 0;
  const stale = deferredQuery !== query;

  const onSort = useCallback((key: ScholarSortKey) => setSort((current) => nextSort(current, key)), []);
  const onToggleThread = useCallback((id: string) => {
    setEvidenceThread(
      state.evidenceThread.includes(id)
        ? state.evidenceThread.filter((entry) => entry !== id)
        : [...state.evidenceThread, id],
    );
  }, [setEvidenceThread, state.evidenceThread]);
  const onSelect = useCallback((id: string) => selectPrimary(id), [selectPrimary]);

  const clearFilters = () => setFilters({ periods: [], types: [], schools: [] });
  const showSchools = useCallback((schools: string[]) => {
    setFilters({ ...state.filters, schools });
    setView('index');
  }, [setFilters, state.filters]);

  useEffect(() => {
    if (state.mode !== 'scholar') return undefined;
    const onKey = (event: globalThis.KeyboardEvent) => {
      if (event.key !== '/' || event.metaKey || event.ctrlKey || event.altKey) return;
      if (isTypingTarget(event.target)) return;
      event.preventDefault();
      setView('index');
      searchRef.current?.focus();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [state.mode]);

  const onSearchKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'ArrowDown' && rows.length > 0) {
      event.preventDefault();
      tableRef.current?.focusRow(0);
    } else if (event.key === 'Escape' && query) {
      event.preventDefault();
      setQuery('');
    }
  };

  const onTabKeyDown = (event: KeyboardEvent<HTMLButtonElement>) => {
    const current = VIEWS.indexOf(view);
    let next = current;
    if (event.key === 'ArrowRight') next = (current + 1) % VIEWS.length;
    else if (event.key === 'ArrowLeft') next = (current - 1 + VIEWS.length) % VIEWS.length;
    else if (event.key === 'Home') next = 0;
    else if (event.key === 'End') next = VIEWS.length - 1;
    else return;
    event.preventDefault();
    setView(VIEWS[next]);
    tabRefs.current.get(VIEWS[next])?.focus();
  };

  const primaryLabel = state.primarySelection
    ? metaById.get(state.primarySelection)?.label ?? data.rawById.get(state.primarySelection)?.label ?? null
    : null;

  const resultSummary = searching || filtersActive > 0
    ? t('scholar.results.matching', { count: rows.length, formatted: labels.number(rows.length), total: labels.number(data.meta.length) })
    : t('scholar.results.all', { count: data.meta.length, formatted: labels.number(data.meta.length) });

  const empty = (
    <div className="mx-auto max-w-md text-center">
      <p className="font-display text-2xl text-stone-900">{t('scholar.results.emptyTitle')}</p>
      <p className="mt-2 font-reader text-base leading-6 text-stone-600">
        {searching ? t('scholar.results.emptyQuery', { query: deferredQuery.trim() }) : t('scholar.results.emptyFilters')}
      </p>
      <div className="mt-4 flex flex-wrap justify-center gap-2">
        {searching && (
          <button type="button" onClick={() => setQuery('')} className={`inline-flex min-h-11 items-center border border-stone-900 px-4 font-body text-sm font-semibold text-stone-900 hover:bg-stone-900 hover:text-[#fffdf9] ${focusRing}`}>
            {t('scholar.results.clearSearch')}
          </button>
        )}
        {filtersActive > 0 && (
          <button type="button" onClick={clearFilters} className={`inline-flex min-h-11 items-center border border-orange-700 px-4 font-body text-sm font-semibold text-orange-800 hover:bg-orange-50 ${focusRing}`}>
            {t('scholar.filters.clearAll', { count: filtersActive })}
          </button>
        )}
      </div>
    </div>
  );

  const viewFallback = (
    <p role="status" className="px-4 py-16 text-center font-body text-sm text-stone-500">{t('scholar.views.loading')}</p>
  );

  return (
    <section
      id="workspace-panel-scholar"
      role="tabpanel"
      aria-labelledby="workspace-mode-scholar"
      tabIndex={-1}
      className="absolute inset-0 overflow-y-auto bg-[#fcf9f4] text-stone-900 outline-none xl:overflow-hidden"
    >
      <div className="flex min-h-full flex-col pt-[4.25rem] xl:h-full">
        <header className="flex flex-col gap-3 border-b border-stone-300/80 px-4 pb-3 pt-4 sm:px-5 lg:flex-row lg:items-end lg:justify-between lg:px-7">
          <div className="min-w-0">
            <p className="font-body text-[10px] font-semibold uppercase tracking-[0.24em] text-orange-800">
              {t('scholar.header.eyebrow', { release: state.releaseId?.slice(-10) ?? t('scholar.header.releaseLoading') })}
            </p>
            <h1 className="mt-1 font-display text-[clamp(1.9rem,3vw,2.9rem)] leading-none tracking-[-0.02em] text-stone-950">
              {t('scholar.header.title')}
            </h1>
          </div>
          <div className="flex min-w-0 items-end gap-2">
            <div
              role="tablist"
              aria-label={t('scholar.views.label')}
              className="-mb-3 flex min-w-0 overflow-x-auto"
            >
              {VIEWS.map((entry) => {
                const Icon = VIEW_ICONS[entry];
                const selected = view === entry;
                return (
                  <button
                    key={entry}
                    ref={(element) => {
                      if (element) tabRefs.current.set(entry, element);
                      else tabRefs.current.delete(entry);
                    }}
                    type="button"
                    role="tab"
                    id={`${panelId}-tab-${entry}`}
                    aria-selected={selected}
                    aria-controls={`${panelId}-panel`}
                    tabIndex={selected ? 0 : -1}
                    onClick={() => setView(entry)}
                    onKeyDown={onTabKeyDown}
                    className={[
                      'inline-flex min-h-11 shrink-0 items-center gap-1.5 border-b-2 px-2 pb-2 pt-2 font-body text-[13px] font-semibold transition-colors sm:gap-2 sm:px-3 sm:text-sm outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-orange-700',
                      selected ? 'border-orange-800 text-stone-950' : 'border-transparent text-stone-500 hover:text-stone-900',
                    ].join(' ')}
                  >
                    <Icon className={`hidden h-4 w-4 sm:block ${selected ? 'text-orange-800' : ''}`} aria-hidden="true" />
                    {t(`scholar.views.${entry}`)}
                    {entry === 'compare' && state.compareIds.length > 0 && (
                      <span className="min-w-5 bg-teal-700 px-1 text-center text-[10px] font-bold tabular-nums text-[#fffdf9]">
                        {labels.number(state.compareIds.length)}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        </header>

        <div className="grid min-h-0 flex-1 grid-cols-1 xl:grid-cols-[17rem_minmax(0,1fr)_24rem]">
          <div className="border-b border-stone-300/80 px-4 py-3 sm:px-5 xl:overflow-y-auto xl:border-b-0 xl:border-r xl:px-5 xl:py-5">
            <WorkspaceFilterBar facetCounts={facetCounts} />
          </div>

          <main
            id={`${panelId}-panel`}
            role="tabpanel"
            aria-labelledby={`${panelId}-tab-${view}`}
            className="flex min-h-0 min-w-0 flex-col"
          >
            {view === 'index' && (
              <>
                <div className="flex flex-col gap-2 border-b border-stone-300 bg-[#fcf9f4] px-3 py-3 sm:flex-row sm:items-center sm:px-5">
                  <label className="relative block min-w-0 flex-1">
                    <span className="sr-only">{t('scholar.search.label')}</span>
                    <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-stone-500" aria-hidden="true" />
                    <input
                      ref={searchRef}
                      type="search"
                      value={query}
                      onChange={(event) => setQuery(event.target.value)}
                      onKeyDown={onSearchKeyDown}
                      placeholder={t('scholar.search.placeholder')}
                      aria-describedby={captionId}
                      className="min-h-11 w-full border border-stone-300 bg-[#fffdf9] pl-10 pr-12 font-body text-base text-stone-900 placeholder:text-stone-400 focus:border-orange-700 focus:outline-none focus:ring-1 focus:ring-orange-700 [&::-webkit-search-cancel-button]:hidden"
                    />
                    {query ? (
                      <button
                        type="button"
                        onClick={() => {
                          setQuery('');
                          searchRef.current?.focus();
                        }}
                        aria-label={t('scholar.results.clearSearch')}
                        className={`absolute right-0 top-0 flex h-11 w-11 items-center justify-center text-stone-400 hover:text-stone-800 ${focusRing}`}
                      >
                        <X className="h-4 w-4" aria-hidden="true" />
                      </button>
                    ) : (
                      <kbd aria-hidden="true" className="pointer-events-none absolute right-3 top-1/2 hidden -translate-y-1/2 border border-stone-300 px-1.5 font-body text-[11px] text-stone-500 md:block">/</kbd>
                    )}
                  </label>
                  <div className="flex items-center justify-between gap-3 font-body text-xs text-stone-600 sm:justify-end">
                    <p id={captionId} aria-live="polite" className={`tabular-nums transition-opacity ${stale ? 'opacity-50' : ''}`}>
                      {resultSummary}
                    </p>
                    {sort.key !== 'relevance' && (
                      <button
                        type="button"
                        onClick={() => setSort(DEFAULT_SORT)}
                        className={`inline-flex min-h-11 items-center whitespace-nowrap font-semibold text-teal-800 underline decoration-teal-300 underline-offset-4 hover:decoration-teal-800 ${focusRing}`}
                      >
                        {t('scholar.table.resetSort')}
                      </button>
                    )}
                  </div>
                </div>
                <div className="h-[70svh] min-h-[22rem] bg-[#fffdf9] xl:h-auto xl:min-h-0 xl:flex-1">
                  <ScholarNodeTable
                    ref={tableRef}
                    rows={rows}
                    sort={sort}
                    onSort={onSort}
                    primaryId={state.primarySelection}
                    compareIds={state.compareIds}
                    threadIds={threadIds}
                    onSelect={onSelect}
                    onToggleCompare={toggleCompare}
                    onToggleThread={onToggleThread}
                    loading={loading}
                    empty={empty}
                    captionId={captionId}
                  />
                </div>
                <p className="hidden border-t border-stone-300 bg-[#f7f2e9] px-5 py-2 font-body text-[11px] text-stone-500 md:block">
                  {t('scholar.table.keyboardHint')}
                </p>
              </>
            )}
            {view !== 'index' && (
              <div className="min-h-0 flex-1 xl:overflow-y-auto">
                <Suspense fallback={viewFallback}>
                  {view === 'compare' && adjacency && (
                    <ScholarCompareView metaById={metaById} adjacency={adjacency} onShowIndex={() => setView('index')} />
                  )}
                  {view === 'matrix' && <InfluenceMatrixPanel onShowSchools={showSchools} />}
                  {view === 'paths' && adjacency && (
                    <PathInspectorPanel index={index} metaById={metaById} adjacency={adjacency} />
                  )}
                  {(view === 'compare' || view === 'paths') && !adjacency && viewFallback}
                </Suspense>
              </div>
            )}
          </main>

          <aside
            ref={inspectorRef}
            aria-label={t('scholar.inspector.label')}
            className="min-w-0 scroll-mt-20 border-t border-stone-300 px-4 py-6 sm:px-5 xl:overflow-y-auto xl:border-l xl:border-t-0 xl:px-6"
          >
            <ScholarInspector
              metaById={metaById}
              onOpenCompare={() => setView('compare')}
              onToggleThread={onToggleThread}
            />
          </aside>
        </div>
      </div>

      {primaryLabel && (
        <div className="sticky bottom-0 z-20 flex items-center justify-between gap-3 border-t border-stone-300 bg-[#fffdf9]/95 px-4 py-1.5 shadow-[0_-8px_24px_rgba(72,52,36,0.08)] backdrop-blur xl:hidden">
          <p className="min-w-0 truncate font-body text-sm">
            <span className="text-stone-500">{t('scholar.inspector.primary')} · </span>
            <span className="font-semibold text-stone-900">{primaryLabel}</span>
          </p>
          <button
            type="button"
            onClick={() => inspectorRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })}
            className={`inline-flex min-h-11 shrink-0 items-center gap-1.5 font-body text-sm font-semibold text-orange-800 ${focusRing}`}
          >
            <PanelBottomOpen className="h-4 w-4" aria-hidden="true" /> {t('scholar.inspector.jump')}
          </button>
        </div>
      )}
    </section>
  );
}
