import { memo, useDeferredValue, useEffect, useMemo, useState } from 'react';
import { ArrowRight, ChevronLeft, ChevronRight, Clock, Search } from 'lucide-react';
import AccordionPanel from '../mobile/AccordionPanel';
import type { TimelineNodeSummary, TimelineOverview, TimelinePeriodSummary } from '../../types';

export const TIMELINE_PAGE_SIZE = 24;

function formatYear(year?: number | null) {
  if (year === null || year === undefined) return '';
  if (year < 0) return `${Math.abs(year)} BCE`;
  if (year === 0) return '0';
  return `${year} CE`;
}

function formatPeriodRange(period: TimelinePeriodSummary) {
  if (period.startYear === null || period.startYear === undefined
    || period.endYear === null || period.endYear === undefined) {
    return 'Date range not asserted';
  }
  return `${formatYear(period.startYear)} — ${formatYear(period.endYear)}`;
}

function sortNodes(nodes: TimelineNodeSummary[]) {
  return [...nodes].sort((left, right) => {
    const relationDelta = (right.relationCount ?? 0) - (left.relationCount ?? 0);
    return relationDelta || (left.label || '').localeCompare(right.label || '');
  });
}

function matches(node: TimelineNodeSummary, query: string) {
  if (!query) return true;
  return [node.label, node.type, node.period, node.school]
    .filter(Boolean)
    .join(' ')
    .toLocaleLowerCase()
    .includes(query);
}

export interface TimelinePanelProps {
  timeline: TimelineOverview | null;
  loading?: boolean;
  onSelectNode: (nodeId: string) => void;
  defaultExpanded?: boolean;
  focusPeriod?: string | null;
}

function TimelinePanelComponent({
  timeline,
  loading = false,
  onSelectNode,
  defaultExpanded = true,
  focusPeriod = null,
}: TimelinePanelProps) {
  const [query, setQuery] = useState('');
  const deferredQuery = useDeferredValue(query.trim().toLocaleLowerCase());
  const [activePeriodKey, setActivePeriodKey] = useState<string | null>(null);
  const [page, setPage] = useState(0);

  const periods = useMemo(() => timeline?.periods ?? [], [timeline]);
  const activePeriod = periods.find((period) => period.key === activePeriodKey) ?? periods[0] ?? null;

  useEffect(() => {
    if (!activePeriodKey && periods[0]) setActivePeriodKey(periods[0].key);
    if (activePeriodKey && !periods.some((period) => period.key === activePeriodKey)) {
      setActivePeriodKey(periods[0]?.key ?? null);
    }
  }, [activePeriodKey, periods]);

  useEffect(() => {
    if (!focusPeriod) return;
    const focused = periods.find((period) => period.label === focusPeriod);
    if (focused) setActivePeriodKey(focused.key);
  }, [focusPeriod, periods]);

  useEffect(() => setPage(0), [activePeriodKey, deferredQuery, timeline]);

  const allNodes = useMemo(() => periods.flatMap((period) => period.nodes), [periods]);
  const results = useMemo(() => {
    if (deferredQuery) return sortNodes(allNodes.filter((node) => matches(node, deferredQuery)));
    return sortNodes(activePeriod?.nodes ?? []);
  }, [activePeriod, allNodes, deferredQuery]);
  const pageCount = Math.max(1, Math.ceil(results.length / TIMELINE_PAGE_SIZE));
  const safePage = Math.min(page, pageCount - 1);
  const visibleNodes = results.slice(safePage * TIMELINE_PAGE_SIZE, (safePage + 1) * TIMELINE_PAGE_SIZE);
  const firstVisible = results.length === 0 ? 0 : safePage * TIMELINE_PAGE_SIZE + 1;
  const lastVisible = Math.min((safePage + 1) * TIMELINE_PAGE_SIZE, results.length);
  const statusPeriod = activePeriod?.label ?? 'chronology';

  if (loading && !timeline) {
    return (
      <AccordionPanel title="Chrono-Storyline" icon={<Clock className="h-5 w-5" />} defaultExpanded={defaultExpanded} headingLevel={2} className="min-w-0">
        <div className="py-16 text-center text-sm text-stone-500">Loading chronology…</div>
      </AccordionPanel>
    );
  }

  if (!timeline || periods.length === 0) {
    return (
      <AccordionPanel title="Chrono-Storyline" icon={<Clock className="h-5 w-5" />} defaultExpanded={defaultExpanded} headingLevel={2} className="min-w-0">
        <div className="py-16 text-center text-sm text-stone-500">No dated evidence matches this view.</div>
      </AccordionPanel>
    );
  }

  return (
    <AccordionPanel title="Chrono-Storyline" icon={<Clock className="h-5 w-5" />} badge={`${periods.length} periods`} defaultExpanded={defaultExpanded} headingLevel={2} className="min-w-0 border-stone-300 bg-[#fffdf9] shadow-none">
      <div className="border-y border-stone-300">
        <div className="overflow-x-auto">
          <div className="flex min-w-max items-stretch">
            {periods.map((period, index) => {
              const active = !deferredQuery && period.key === activePeriod?.key;
              return (
                <button key={period.key} type="button" onClick={() => { setQuery(''); setActivePeriodKey(period.key); }} aria-pressed={active} className={['group relative min-h-[5.5rem] w-44 border-r border-stone-300 px-4 py-3 text-left outline-none transition-colors focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-orange-700', active ? 'bg-stone-900 text-[#fffaf1]' : 'bg-[#f7f2e9] text-stone-700 hover:bg-orange-50'].join(' ')}>
                  <span className={['block text-[9px] font-bold uppercase tracking-[0.18em]', active ? 'text-orange-300' : 'text-stone-400'].join(' ')}>Period {String(index + 1).padStart(2, '0')}</span>
                  <span className="mt-1 block text-xs font-semibold leading-4">{period.label}</span>
                  <span className={['mt-1 block text-[10px]', active ? 'text-stone-300' : 'text-stone-500'].join(' ')}>{formatPeriodRange(period)}</span>
                  {active && <span className="absolute inset-x-0 bottom-0 h-[3px] bg-orange-600" />}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      <div className="grid gap-4 border-b border-stone-300 py-5 lg:grid-cols-[minmax(0,28rem)_1fr] lg:items-end">
        <label className="block text-xs font-semibold text-stone-700">
          Search every node in this chronology
          <span className="relative mt-1 block">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-stone-500" aria-hidden="true" />
            <input type="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Thinker, work, school, concept…" aria-label="Search every node in this chronology" className="min-h-11 w-full border border-stone-300 bg-white pl-10 pr-3 text-base font-normal text-stone-900 outline-none focus:border-orange-700 focus:ring-1 focus:ring-orange-700" />
          </span>
        </label>
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-stone-500">{deferredQuery ? 'Corpus search' : activePeriod?.label}</p>
          <p role="status" aria-live="polite" className="mt-1 text-xs leading-5 text-stone-600">
            {deferredQuery ? `${results.length.toLocaleString()} matching nodes across all periods.` : `${results.length.toLocaleString()} nodes in this period. The strongest connected loci appear first.`}
          </p>
        </div>
      </div>

      <div className="grid gap-x-6 md:grid-cols-2">
        {visibleNodes.map((node, index) => (
          <button key={node.id} data-testid="timeline-node" type="button" onClick={() => onSelectNode(node.id)} className="group grid min-h-11 grid-cols-[2rem_1fr_auto] items-center gap-3 border-b border-stone-200 py-3 text-left outline-none transition-colors hover:text-orange-900 focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-orange-700">
            <span className="font-display text-lg text-stone-400">{String(firstVisible + index).padStart(2, '0')}</span>
            <span className="min-w-0">
              <span className="block truncate text-sm font-semibold text-stone-900 group-hover:text-orange-900">{node.label}</span>
              <span className="mt-0.5 block truncate text-[10px] uppercase tracking-[0.12em] text-stone-500">{[node.type, node.school].filter(Boolean).join(' · ')}</span>
            </span>
            <ArrowRight className="h-3.5 w-3.5 text-stone-400 transition-transform group-hover:translate-x-1" aria-hidden="true" />
          </button>
        ))}
      </div>

      {results.length === 0 && <p className="py-12 text-center font-reader text-lg text-stone-500">No evidence matches this query.</p>}

      <div className="mt-5 flex items-center justify-between gap-3 border-t border-stone-300 pt-4">
        <p className="text-xs text-stone-500" aria-live="polite">Showing {firstVisible.toLocaleString()}–{lastVisible.toLocaleString()} of {results.length.toLocaleString()}</p>
        {pageCount > 1 && (
          <div className="flex items-center gap-2">
            <button type="button" onClick={() => setPage(Math.max(0, safePage - 1))} disabled={safePage === 0} aria-label={`Previous nodes in ${statusPeriod}`} className="inline-flex h-11 w-11 items-center justify-center border border-stone-300 disabled:opacity-30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-700"><ChevronLeft className="h-4 w-4" /></button>
            <span className="min-w-20 text-center text-xs tabular-nums text-stone-600">{safePage + 1} / {pageCount}</span>
            <button type="button" onClick={() => setPage(Math.min(pageCount - 1, safePage + 1))} disabled={safePage >= pageCount - 1} aria-label={`Next nodes in ${statusPeriod}`} className="inline-flex h-11 w-11 items-center justify-center border border-stone-300 disabled:opacity-30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-700"><ChevronRight className="h-4 w-4" /></button>
          </div>
        )}
      </div>
    </AccordionPanel>
  );
}

export const TimelinePanel = memo(TimelinePanelComponent);
export default TimelinePanel;
