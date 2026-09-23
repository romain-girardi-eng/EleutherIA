import { ArrowRight, GitCompareArrows, LoaderCircle, RefreshCw, RotateCcw, X } from 'lucide-react';
import { useCallback, useEffect, useId, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { useGraphWorkspace } from '../../context/GraphWorkspaceContext';
import type { AtlasNodeMeta } from '../cosmograph/AtlasHelpers';
import ChronosAxis, { type PeriodMarkers } from './ChronosAxis';
import { formatCount, formatHistoricalYear, periodName, typeName } from './chronosFormat';
import {
  buildSchoolMatrix,
  ERA_BANDS,
  periodBounds,
  periodIntersectsWindow,
  periodKey,
  type SchoolFilter,
  timelineFromGraph,
} from './chronosTimeline';
import SchoolPeriodMatrix from './SchoolPeriodMatrix';
import TimelinePanel from './TimelinePanel';

type Filters = ReturnType<typeof useGraphWorkspace>['state']['filters'];

function withinFilters(node: AtlasNodeMeta, filters: Filters) {
  if (filters.periods.length > 0 && !filters.periods.includes(node.periodLabel)) return false;
  if (filters.schools.length > 0 && !filters.schools.includes(node.schoolLabel)) return false;
  if (
    filters.types.length > 0 &&
    !filters.types.includes(node.typeKey) &&
    !(node.layer === 'modern' && filters.types.includes('scholar'))
  ) return false;
  return true;
}

type Era = 'bce' | 'ce';

function YearField({
  label,
  value,
  defaultEra,
  onCommit,
}: {
  label: string;
  value: number | null;
  defaultEra: Era;
  onCommit: (year: number | null) => void;
}) {
  const { t } = useTranslation();
  const id = useId();
  const [draftEra, setDraftEra] = useState<Era>(defaultEra);
  const era: Era = value === null ? draftEra : value < 0 ? 'bce' : 'ce';
  const magnitude = value === null ? '' : String(Math.abs(value));

  const commit = (text: string, nextEra: Era) => {
    if (text.trim() === '') {
      onCommit(null);
      return;
    }
    const parsed = Number.parseInt(text, 10);
    // There is no year 0 in historical reckoning: 1 BCE is followed by 1 CE.
    if (!Number.isFinite(parsed) || parsed < 1 || parsed > 2100) return;
    onCommit(nextEra === 'bce' ? -parsed : parsed);
  };

  return (
    <div className="min-w-0">
      <label htmlFor={id} className="font-body text-[11px] font-semibold text-stone-600">{label}</label>
      <div className="mt-1 flex">
        <input
          id={id}
          type="number"
          inputMode="numeric"
          min={1}
          max={2100}
          placeholder={t('chronos.interval.openPlaceholder')}
          value={magnitude}
          onChange={(event) => commit(event.target.value, era)}
          className="min-h-11 w-full min-w-0 border border-stone-300 bg-[#fffdf9] px-3 font-body text-base tabular-nums text-stone-900 outline-none focus:z-10 focus:border-orange-700 focus:ring-1 focus:ring-orange-700"
        />
        <select
          aria-label={t('chronos.interval.eraLabel', { field: label })}
          value={era}
          onChange={(event) => {
            const nextEra = event.target.value === 'bce' ? 'bce' : 'ce';
            setDraftEra(nextEra);
            if (value !== null) onCommit(nextEra === 'bce' ? -Math.abs(value) : Math.abs(value));
          }}
          className="-ml-px min-h-11 border border-stone-300 bg-[#f7f2e9] px-2 font-body text-sm text-stone-800 outline-none focus:z-10 focus:border-orange-700 focus:ring-1 focus:ring-orange-700"
        >
          <option value="bce">{t('chronos.interval.bce')}</option>
          <option value="ce">{t('chronos.interval.ce')}</option>
        </select>
      </div>
    </div>
  );
}

const SECTION_EYEBROW = 'font-body text-[10px] font-semibold uppercase tracking-[0.2em] text-stone-500';

export default function ChronosWorkspace() {
  const { t, i18n } = useTranslation();
  const locale = i18n.language || 'en';
  const {
    state,
    data,
    loading,
    nodeDetailStates,
    selectPrimary,
    setEvidenceThread,
    toggleCompare,
    setTimeWindow,
    ensureNodeDetail,
  } = useGraphWorkspace();
  const { start: windowStart, end: windowEnd } = state.timeWindow;

  const [includePassages, setIncludePassages] = useState(true);
  const [activePeriodKey, setActivePeriodKey] = useState<string | null>(null);
  const [schoolFilter, setSchoolFilter] = useState<SchoolFilter | null>(null);

  useEffect(() => {
    if (state.primarySelection) void ensureNodeDetail(state.primarySelection);
  }, [ensureNodeDetail, state.primarySelection]);

  const byFilters = useMemo(
    () => data.meta.filter((node) => withinFilters(node, state.filters)),
    [data.meta, state.filters],
  );
  const inWindow = useMemo(
    () => (windowStart === null && windowEnd === null
      ? byFilters
      : byFilters.filter((node) => periodIntersectsWindow(periodBounds(node.periodLabel), windowStart, windowEnd))),
    [byFilters, windowEnd, windowStart],
  );
  const edgeCount = useMemo(() => {
    const ids = new Set(inWindow.map((node) => node.id));
    return data.edges.reduce((sum, edge) => (ids.has(edge.source) && ids.has(edge.target) ? sum + 1 : sum), 0);
  }, [data.edges, inWindow]);
  const hiddenPassages = useMemo(
    () => (includePassages ? 0 : inWindow.reduce((sum, node) => (node.typeKey === 'passage' ? sum + 1 : sum), 0)),
    [inWindow, includePassages],
  );
  const scopeNodes = useMemo(
    () => (includePassages ? byFilters : byFilters.filter((node) => node.typeKey !== 'passage')),
    [byFilters, includePassages],
  );
  // The axis keeps every period visible (dimming those outside the window)
  // so brushing never hides the context the reader is narrowing from.
  const contextTimeline = useMemo(() => timelineFromGraph(scopeNodes, 0, null, null), [scopeNodes]);
  const windowTimeline = useMemo(
    () => (windowStart === null && windowEnd === null
      ? contextTimeline
      : timelineFromGraph(scopeNodes, 0, windowStart, windowEnd)),
    [contextTimeline, scopeNodes, windowEnd, windowStart],
  );
  const matrix = useMemo(() => buildSchoolMatrix(windowTimeline), [windowTimeline]);
  const scopeCount = useMemo(
    () => windowTimeline.periods.reduce((sum, period) => sum + period.nodes.length, 0),
    [windowTimeline],
  );

  const effectivePeriodKey = windowTimeline.periods.some((period) => period.key === activePeriodKey)
    ? activePeriodKey
    : null;

  const selected = state.primarySelection ? data.rawById.get(state.primarySelection) ?? null : null;
  const selectedPeriodLabel = selected ? selected.period ?? 'Unspecified' : null;
  const selectedDetailState = state.primarySelection ? nodeDetailStates.get(state.primarySelection) : undefined;

  const markers = useMemo(() => {
    const map = new Map<string, PeriodMarkers>();
    const entry = (label: string) => {
      const existing = map.get(label);
      if (existing) return existing;
      const created: PeriodMarkers = { selected: false, compare: 0, thread: [] };
      map.set(label, created);
      return created;
    };
    const periodOf = (id: string) => {
      const node = data.rawById.get(id);
      return node ? node.period ?? 'Unspecified' : null;
    };
    if (state.primarySelection) {
      const label = periodOf(state.primarySelection);
      if (label) entry(label).selected = true;
    }
    state.compareIds.forEach((id) => {
      const label = periodOf(id);
      if (label) entry(label).compare += 1;
    });
    state.evidenceThread.forEach((id, index) => {
      const label = periodOf(id);
      if (label) entry(label).thread = [...entry(label).thread, index];
    });
    return map;
  }, [data.rawById, state.compareIds, state.evidenceThread, state.primarySelection]);

  const { evidenceThread } = state;
  const selectFromTimeline = useCallback((nodeId: string) => {
    selectPrimary(nodeId);
    setEvidenceThread([...evidenceThread, nodeId]);
  }, [evidenceThread, selectPrimary, setEvidenceThread]);

  const handleWindowChange = useCallback(
    (start: number | null, end: number | null) => setTimeWindow({ start, end }),
    [setTimeWindow],
  );
  const handleMatrixSelect = useCallback((key: string | null, school: SchoolFilter | null) => {
    setActivePeriodKey(key);
    setSchoolFilter(school);
  }, []);
  const clearScope = useCallback(() => {
    setActivePeriodKey(null);
    setSchoolFilter(null);
  }, []);

  const windowed = windowStart !== null || windowEnd !== null;
  const loadingData = loading && data.meta.length === 0;

  return (
    <section
      id="workspace-panel-chronos"
      role="tabpanel"
      aria-labelledby="workspace-mode-chronos"
      tabIndex={0}
      className="absolute inset-0 overflow-y-auto overflow-x-hidden bg-[#f7f2e9] text-stone-900 outline-none"
    >
      <div className="mx-auto w-full max-w-[1560px] px-4 pb-16 pt-24 sm:px-6 lg:px-10 lg:pt-28">
        <header className="grid gap-8 border-b border-stone-300/80 pb-8 lg:grid-cols-[minmax(0,1fr)_minmax(24rem,32rem)] lg:items-start">
          <div className="min-w-0">
            <p className="font-body text-[11px] font-semibold uppercase tracking-[0.24em] text-orange-800">
              {t('chronos.header.eyebrow')}
            </p>
            <h1 className="mt-3 max-w-4xl font-display text-[clamp(2.3rem,4.4vw,4.4rem)] leading-[0.95] tracking-[-0.03em] text-stone-950">
              {t('chronos.header.title')}
            </h1>
            <p className="mt-4 max-w-2xl font-body text-[15px] leading-7 text-stone-600">
              {t('chronos.header.lede')}
            </p>
          </div>

          <div className="min-w-0 border-stone-300 font-body lg:border-l lg:pl-6">
            <div className="flex items-start justify-between gap-4">
              <div className="min-w-0">
                <p className={SECTION_EYEBROW}>{t('chronos.interval.label')}</p>
                <p className="mt-1 flex flex-wrap items-center gap-x-2 font-display text-2xl text-stone-900" aria-live="polite">
                  <span>{windowStart === null ? t('chronos.interval.openStart') : formatHistoricalYear(t, windowStart)}</span>
                  <ArrowRight className="h-4 w-4 text-stone-500" aria-hidden="true" />
                  <span>{windowEnd === null ? t('chronos.interval.openEnd') : formatHistoricalYear(t, windowEnd)}</span>
                </p>
              </div>
              <button
                type="button"
                onClick={() => handleWindowChange(null, null)}
                disabled={!windowed}
                className="inline-flex min-h-11 shrink-0 items-center gap-2 rounded-full border border-stone-300 px-4 text-sm font-semibold text-stone-700 hover:border-orange-500 hover:text-orange-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-700 disabled:opacity-40 disabled:hover:border-stone-300 disabled:hover:text-stone-700"
              >
                <RotateCcw className="h-3.5 w-3.5" aria-hidden="true" />
                {t('chronos.interval.reset')}
              </button>
            </div>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <YearField label={t('chronos.interval.from')} value={windowStart} defaultEra="bce" onCommit={(year) => handleWindowChange(year, windowEnd)} />
              <YearField label={t('chronos.interval.to')} value={windowEnd} defaultEra="ce" onCommit={(year) => handleWindowChange(windowStart, year)} />
            </div>
            <div className="mt-4">
              <p className={SECTION_EYEBROW}>{t('chronos.interval.eras')}</p>
              <div className="mt-2 flex flex-wrap gap-1.5">
                {ERA_BANDS.map((era) => {
                  const active = windowStart === era.start && windowEnd === era.end;
                  return (
                    <button
                      key={era.key}
                      type="button"
                      aria-pressed={active}
                      onClick={() => (active ? handleWindowChange(null, null) : handleWindowChange(era.start, era.end))}
                      className={[
                        'min-h-9 rounded-full border px-3 text-xs font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-700',
                        active ? 'border-stone-900 bg-stone-900 text-[#fffaf1]' : 'border-stone-300 text-stone-700 hover:border-orange-500 hover:text-orange-800',
                      ].join(' ')}
                    >
                      {t(`chronos.eras.${era.key}`)}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        </header>

        <div className="mt-6 flex flex-wrap items-center justify-between gap-3 font-body">
          <p className="text-[13px] text-stone-600">
            {t('chronos.scope.summary', {
              count: scopeCount,
              formatted: formatCount(locale, scopeCount),
              periods: windowTimeline.periods.length,
            })}
            {!includePassages && hiddenPassages > 0 && (
              <span className="text-stone-500"> {t('chronos.scope.passagesHidden', { count: hiddenPassages, formatted: formatCount(locale, hiddenPassages) })}</span>
            )}
          </p>
          <button
            type="button"
            role="switch"
            aria-checked={includePassages}
            onClick={() => setIncludePassages((value) => !value)}
            className="inline-flex min-h-11 items-center gap-2.5 text-sm font-semibold text-stone-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-700"
          >
            <span className={['relative h-5 w-9 rounded-full transition-colors', includePassages ? 'bg-teal-700' : 'bg-stone-300'].join(' ')} aria-hidden="true">
              <span className={['absolute left-0.5 top-0.5 h-4 w-4 rounded-full bg-[#fffdf9] shadow-sm transition-transform', includePassages ? 'translate-x-4' : 'translate-x-0'].join(' ')} />
            </span>
            {t('chronos.scope.includePassages')}
          </button>
        </div>

        <div className="mt-6 border-t border-stone-300 pt-6">
          <ChronosAxis
            periods={contextTimeline.periods}
            loading={loadingData}
            windowStart={windowStart}
            windowEnd={windowEnd}
            onWindowChange={handleWindowChange}
            activePeriodKey={effectivePeriodKey}
            onActivatePeriod={setActivePeriodKey}
            markers={markers}
          />
        </div>

        <div className="mt-12 grid gap-10 xl:grid-cols-[minmax(0,1fr)_21rem]">
          <div className="min-w-0 space-y-12">
            <SchoolPeriodMatrix
              matrix={matrix}
              activePeriodKey={effectivePeriodKey}
              activeSchool={schoolFilter}
              selectedPeriodLabel={selectedPeriodLabel}
              selectedSchool={selected?.school ?? null}
              onSelect={handleMatrixSelect}
            />
            <TimelinePanel
              timeline={loadingData ? null : windowTimeline}
              loading={loadingData}
              onSelectNode={selectFromTimeline}
              onToggleCompare={toggleCompare}
              activePeriodKey={effectivePeriodKey}
              schoolFilter={schoolFilter}
              onClearScope={clearScope}
              primarySelection={state.primarySelection}
              compareIds={state.compareIds}
              threadIds={state.evidenceThread}
            />
          </div>

          <aside
            aria-label={t('chronos.locus.ariaLabel')}
            aria-busy={selectedDetailState?.loading || undefined}
            className="min-w-0 border-t border-stone-300 pt-6 xl:sticky xl:top-6 xl:self-start xl:border-l xl:border-t-0 xl:pl-6 xl:pt-0"
          >
            <p className={SECTION_EYEBROW}>{t('chronos.locus.heading')}</p>
            {selected ? (
              <div className="mt-3">
                <p className="break-words font-display text-3xl leading-tight text-stone-950">{selected.label}</p>
                <p className="mt-2 font-body text-[11px] uppercase tracking-[0.12em] text-stone-600">
                  {[
                    typeName(t, selected.type),
                    periodName(t, selected.period ?? 'Unspecified'),
                    selected.school,
                  ].filter(Boolean).join(' · ')}
                </p>
                {selected.dates && (
                  <p className="mt-1 font-body text-xs text-stone-600">
                    {t('chronos.locus.recordedDates', { dates: selected.dates })}
                  </p>
                )}
                <div className="mt-4 flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      setActivePeriodKey(periodKey(selected.period ?? 'Unspecified'));
                      setSchoolFilter(null);
                    }}
                    className="inline-flex min-h-9 items-center gap-1.5 rounded-full border border-stone-300 px-3 font-body text-xs font-semibold text-stone-700 hover:border-orange-500 hover:text-orange-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-700"
                  >
                    {t('chronos.locus.showPeriod')}
                  </button>
                  <button
                    type="button"
                    aria-pressed={state.compareIds.includes(selected.id)}
                    onClick={() => toggleCompare(selected.id)}
                    className="inline-flex min-h-9 items-center gap-1.5 rounded-full border border-stone-300 px-3 font-body text-xs font-semibold text-stone-700 hover:border-teal-600 hover:text-teal-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-700 aria-pressed:border-teal-700 aria-pressed:text-teal-800"
                  >
                    <GitCompareArrows className="h-3.5 w-3.5" aria-hidden="true" />
                    {state.compareIds.includes(selected.id) ? t('chronos.locus.inCompare') : t('chronos.locus.addCompare')}
                  </button>
                </div>
                {selectedDetailState?.loading && (
                  <p role="status" aria-live="polite" className="mt-4 flex items-center gap-2 font-body text-sm text-stone-600">
                    <LoaderCircle className="h-4 w-4 text-orange-700 motion-safe:animate-spin" aria-hidden="true" />
                    {t('chronos.locus.loadingDetail')}
                  </p>
                )}
                {selectedDetailState?.error && (
                  <div role="alert" className="mt-4 font-body text-sm leading-6 text-stone-700">
                    <p>{t('chronos.locus.detailError')}</p>
                    <button
                      type="button"
                      onClick={() => void ensureNodeDetail(selected.id)}
                      className="mt-2 inline-flex min-h-11 items-center gap-2 font-semibold text-red-800 underline decoration-red-300 underline-offset-4 hover:decoration-red-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-800"
                    >
                      <RefreshCw className="h-4 w-4" aria-hidden="true" /> {t('chronos.locus.retry')}
                    </button>
                  </div>
                )}
                <p className="mt-4 line-clamp-[10] font-reader text-lg leading-7 text-stone-700">
                  {selected.description || t('chronos.locus.noDescription')}
                </p>
              </div>
            ) : (
              <p className="mt-3 font-reader text-lg leading-7 text-stone-600">{t('chronos.locus.empty')}</p>
            )}

            <div className="mt-8 border-t border-stone-300 pt-5">
              <div className="flex items-center justify-between gap-3">
                <p className={SECTION_EYEBROW}>{t('chronos.thread.heading', { count: state.evidenceThread.length })}</p>
                {state.evidenceThread.length > 0 && (
                  <button
                    type="button"
                    onClick={() => setEvidenceThread([])}
                    className="min-h-9 px-1 font-body text-xs font-semibold text-stone-600 underline decoration-stone-300 underline-offset-4 hover:text-orange-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-700"
                  >
                    {t('chronos.thread.clear')}
                  </button>
                )}
              </div>
              {state.evidenceThread.length === 0 ? (
                <p className="mt-2 font-body text-[13px] leading-5 text-stone-600">{t('chronos.thread.empty')}</p>
              ) : (
                <ol className="mt-2">
                  {state.evidenceThread.map((id, index) => {
                    const node = data.rawById.get(id);
                    return (
                      <li key={id}>
                        <button
                          type="button"
                          aria-current={id === state.primarySelection || undefined}
                          onClick={() => selectPrimary(id)}
                          className="grid min-h-11 w-full grid-cols-[1.5rem_1fr] items-center gap-2 border-b border-stone-200 py-1.5 text-left font-body outline-none hover:text-orange-900 focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-orange-700 aria-[current]:text-orange-900"
                        >
                          <span className="text-[11px] font-semibold tabular-nums text-teal-800">{index + 1}</span>
                          <span className="min-w-0">
                            <span className="block truncate text-sm font-semibold">{node?.label ?? id}</span>
                            <span className="block truncate text-[10px] uppercase tracking-[0.12em] text-stone-500">
                              {node ? periodName(t, node.period ?? 'Unspecified') : t('chronos.thread.notLoaded')}
                            </span>
                          </span>
                        </button>
                      </li>
                    );
                  })}
                </ol>
              )}
            </div>

            {state.compareIds.length > 0 && (
              <div className="mt-8 border-t border-stone-300 pt-5">
                <p className={SECTION_EYEBROW}>{t('chronos.compare.heading', { count: state.compareIds.length })}</p>
                <ul className="mt-2 flex flex-wrap gap-1.5">
                  {state.compareIds.map((id) => {
                    const label = data.rawById.get(id)?.label ?? id;
                    return (
                      <li key={id}>
                        <button
                          type="button"
                          onClick={() => toggleCompare(id)}
                          aria-label={t('chronos.ledger.removeCompare', { label })}
                          className="inline-flex min-h-9 max-w-[18rem] items-center gap-1.5 rounded-full border border-teal-700/40 bg-teal-50 px-3 font-body text-xs font-semibold text-teal-900 hover:border-teal-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-700"
                        >
                          <span className="truncate">{label}</span>
                          <X className="h-3 w-3 shrink-0" aria-hidden="true" />
                        </button>
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}

            <div className="mt-8 border-t border-stone-300 pt-5">
              <p className={SECTION_EYEBROW}>{t('chronos.session.heading')}</p>
              <dl className="mt-3 grid grid-cols-2 gap-y-3 font-body text-sm">
                <dt className="text-stone-600">{t('chronos.session.nodes')}</dt>
                <dd className="text-right font-semibold tabular-nums">{formatCount(locale, inWindow.length)}</dd>
                <dt className="text-stone-600">{t('chronos.session.relations')}</dt>
                <dd className="text-right font-semibold tabular-nums">{formatCount(locale, edgeCount)}</dd>
              </dl>
            </div>
          </aside>
        </div>
      </div>
    </section>
  );
}
