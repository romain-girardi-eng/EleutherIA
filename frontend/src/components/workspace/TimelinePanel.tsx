import { memo, useDeferredValue, useEffect, useMemo, useState } from 'react';
import { ChevronLeft, ChevronRight, Clock, Search } from 'lucide-react';
import AccordionPanel from '../mobile/AccordionPanel';
import type { TimelineNodeSummary, TimelinePeriodSummary } from '../../types';

export const TIMELINE_PAGE_SIZE = 24;

function formatYear(year?: number | null) {
  if (year === null || year === undefined) {
    return '';
  }
  if (year < 0) {
    return `${Math.abs(year)} BCE`;
  }
  if (year === 0) {
    return '0';
  }
  return `${year} CE`;
}

function formatPeriodRange(start?: number | null, end?: number | null) {
  if (start === null || start === undefined || end === null || end === undefined) {
    return 'Date range not asserted';
  }
  return `${formatYear(start)} — ${formatYear(end)}`;
}

function periodWidth(period: TimelinePeriodSummary, minYear?: number | null, maxYear?: number | null) {
  if (minYear === null || minYear === undefined || maxYear === null || maxYear === undefined) {
    return 1;
  }
  if (period.startYear === null || period.startYear === undefined
      || period.endYear === null || period.endYear === undefined) {
    return 50;
  }
  const start = period.startYear;
  const end = period.endYear;
  const clampedStart = Math.max(minYear, start);
  const clampedEnd = Math.min(maxYear, end);
  const span = Math.max(clampedEnd - clampedStart, 50); // enforce minimum width
  return span;
}

function normalizeWidths(periods: TimelinePeriodSummary[], minYear?: number | null, maxYear?: number | null) {
  const spans = periods.map((period) => periodWidth(period, minYear, maxYear));
  const total = spans.reduce((sum, span) => sum + span, 0);
  return periods.map((period, index) => ({
    period,
    width: total > 0 ? (spans[index] / total) * 100 : 100 / periods.length,
  }));
}

function sortTimelineNodes(nodes: TimelineNodeSummary[]): TimelineNodeSummary[] {
  return [...nodes].sort((a, b) => {
    const yearDifference = (a.startYear ?? Number.POSITIVE_INFINITY)
      - (b.startYear ?? Number.POSITIVE_INFINITY);
    if (yearDifference !== 0) return yearDifference;
    const relationDifference = (b.relationCount ?? 0) - (a.relationCount ?? 0);
    if (relationDifference !== 0) return relationDifference;
    return (a.label || '').localeCompare(b.label || '');
  });
}

function matchesTimelineQuery(node: TimelineNodeSummary, query: string): boolean {
  if (!query) return true;
  return [node.label, node.type, node.period, node.school]
    .filter(Boolean)
    .join(' ')
    .toLocaleLowerCase()
    .includes(query);
}

export interface TimelinePanelProps {
  timeline: import('../../types').TimelineOverview | null;
  loading?: boolean;
  onSelectNode: (nodeId: string) => void;
  defaultExpanded?: boolean;
}

function TimelinePanelComponent({
  timeline,
  loading = false,
  onSelectNode,
  defaultExpanded = true,
}: TimelinePanelProps) {
  const [query, setQuery] = useState('');
  const deferredQuery = useDeferredValue(query.trim().toLocaleLowerCase());
  const [pageByPeriod, setPageByPeriod] = useState<Record<string, number>>({});

  const normalized = useMemo(() => {
    if (!timeline) {
      return [];
    }
    return normalizeWidths(timeline.periods, timeline.range.minYear, timeline.range.maxYear);
  }, [timeline]);

  useEffect(() => {
    setPageByPeriod({});
  }, [deferredQuery, timeline]);

  const orderedPeriods = useMemo(() => normalized.map(({ period, width }) => ({
    period,
    width,
    orderedNodes: sortTimelineNodes(period.nodes),
  })), [normalized]);

  const matchingPeriods = useMemo(() => orderedPeriods.map(({ period, width, orderedNodes }) => ({
    period,
    width,
    matches: orderedNodes.filter((node) => matchesTimelineQuery(node, deferredQuery)),
  })), [deferredQuery, orderedPeriods]);

  const periodViews = useMemo(() => matchingPeriods.map(({ period, width, matches }) => {
    const pageCount = Math.max(1, Math.ceil(matches.length / TIMELINE_PAGE_SIZE));
    const requestedPage = pageByPeriod[period.key] ?? 0;
    const page = Math.min(Math.max(requestedPage, 0), pageCount - 1);
    const start = page * TIMELINE_PAGE_SIZE;
    return {
      period,
      width,
      matches,
      page,
      pageCount,
      visibleNodes: matches.slice(start, start + TIMELINE_PAGE_SIZE),
    };
  }), [matchingPeriods, pageByPeriod]);

  const matchingTotal = useMemo(
    () => matchingPeriods.reduce((total, view) => total + view.matches.length, 0),
    [matchingPeriods],
  );

  const totalPeriods = timeline?.periods.length || 0;
  const timeRange =
    timeline && timeline.range.minYear !== undefined && timeline.range.maxYear !== undefined
      ? `${formatYear(timeline.range.minYear)} → ${formatYear(timeline.range.maxYear)}`
      : null;

  if (loading && !timeline) {
    return (
      <AccordionPanel
        title="Chrono-Storyline"
        icon={<Clock className="w-5 h-5" />}
        defaultExpanded={defaultExpanded}
        headingLevel={2}
        className="min-w-0"
      >
        <div className="py-16 text-center text-academic-muted text-sm">Loading timeline…</div>
      </AccordionPanel>
    );
  }

  if (!timeline || timeline.periods.length === 0) {
    return (
      <AccordionPanel
        title="Chrono-Storyline"
        icon={<Clock className="w-5 h-5" />}
        defaultExpanded={defaultExpanded}
        headingLevel={2}
        className="min-w-0"
      >
        <div className="py-16 text-center text-academic-muted text-sm">
          Timeline data is unavailable for the current filter selection.
        </div>
      </AccordionPanel>
    );
  }

  return (
    <AccordionPanel
      title="Chrono-Storyline"
      icon={<Clock className="w-5 h-5" />}
      badge={`${totalPeriods} periods`}
      defaultExpanded={defaultExpanded}
      headingLevel={2}
      className="min-w-0 border-stone-200 bg-[#fffdf9] shadow-none"
    >
      {timeRange && (
        <div className="text-xs text-academic-muted mb-4">
          {timeRange}
        </div>
      )}

      <div className="mb-5 grid gap-2 border-y border-stone-200 py-4 sm:grid-cols-[minmax(0,28rem)_1fr] sm:items-end">
        <label htmlFor="chronos-node-search" className="block font-body text-xs font-semibold text-stone-700">
          Search every node in this chronology
          <span className="relative mt-1 block">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-stone-500" aria-hidden="true" />
            <input
              id="chronos-node-search"
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Thinker, work, school, concept…"
              className="min-h-11 w-full border border-stone-300 bg-white pl-10 pr-3 text-base font-normal text-stone-900 outline-none focus:border-orange-700 focus:ring-1 focus:ring-orange-700"
            />
          </span>
        </label>
        <p role="status" aria-live="polite" className="font-body text-xs leading-5 text-stone-600">
          {deferredQuery
            ? `${matchingTotal.toLocaleString()} matching nodes across all periods.`
            : `${timeline.totals.nodes.toLocaleString()} nodes available. Each period shows at most ${TIMELINE_PAGE_SIZE} at once; use search or page controls to reach every node.`}
        </p>
      </div>

      <div className="overflow-x-auto -mx-4 px-4 pb-2">
        {/* Stack vertically on mobile, horizontal scroll on larger screens */}
        <div className="flex flex-col sm:flex-row sm:min-w-[640px] gap-4 sm:gap-0">
          {periodViews.map(({ period, width, visibleNodes, matches, page, pageCount }) => (
            <TimelinePeriodBlock
              key={period.key}
              period={period}
              width={width}
              nodes={visibleNodes}
              matchingCount={matches.length}
              page={page}
              pageCount={pageCount}
              onPageChange={(nextPage) => setPageByPeriod((current) => ({
                ...current,
                [period.key]: nextPage,
              }))}
              onSelectNode={(node) => onSelectNode(node.id)}
            />
          ))}
        </div>
      </div>
    </AccordionPanel>
  );
}

interface TimelinePeriodBlockProps {
  period: TimelinePeriodSummary;
  width: number;
  nodes: TimelineNodeSummary[];
  matchingCount: number;
  page: number;
  pageCount: number;
  onPageChange: (page: number) => void;
  onSelectNode: (node: TimelineNodeSummary) => void;
}

function TimelinePeriodBlock({
  period,
  width,
  nodes,
  matchingCount,
  page,
  pageCount,
  onPageChange,
  onSelectNode,
}: TimelinePeriodBlockProps) {
  const firstVisible = matchingCount === 0 ? 0 : page * TIMELINE_PAGE_SIZE + 1;
  const lastVisible = Math.min((page + 1) * TIMELINE_PAGE_SIZE, matchingCount);
  const statusId = `chronos-period-${period.key.replace(/[^a-z0-9_-]/gi, '-')}-status`;
  // On mobile (< 640px): full width, stacked vertically
  // On desktop (≥ 640px): proportional width based on period span
  return (
    <div
      className="border border-gray-200 rounded-lg p-4 mr-0 sm:mr-4 last:mr-0 bg-white flex-shrink-0"
      style={{ minWidth: '220px', flex: `0 0 ${width}%` }}
    >
      <div className="flex items-center justify-between mb-3">
        <div>
          <div className="text-xs uppercase text-academic-muted font-semibold">{period.label}</div>
          <div className="text-xs text-academic-muted">
            {formatPeriodRange(period.startYear, period.endYear)}
          </div>
        </div>
        <div className="text-xs text-academic-muted text-right">
          {Object.entries(period.counts)
            .map(([type, count]) => `${count} ${type}`)
            .slice(0, 2)
            .join(' • ')}
        </div>
      </div>
      <div className="space-y-2">
        {nodes.map((node) => (
          <button
            key={node.id}
            data-testid="timeline-node"
            type="button"
            onClick={() => onSelectNode(node)}
            className="min-h-11 w-full rounded-md border border-stone-200 bg-[#fffdf9] px-3 py-2 text-left outline-none transition-colors hover:border-orange-400 hover:bg-orange-50 focus-visible:ring-2 focus-visible:ring-orange-700 focus-visible:ring-offset-2"
          >
            <div className="flex items-center justify-between text-sm font-medium text-academic-text">
              <span className="truncate pr-2">{node.label}</span>
              {typeof node.startYear === 'number' && (
                <span className="text-xs text-academic-muted">{formatYear(node.startYear)}</span>
              )}
            </div>
            {node.school && <div className="text-xs text-academic-muted">{node.school}</div>}
            {node.relatedTypes && node.relatedTypes.length > 0 && (
              <div className="mt-1 flex flex-wrap gap-1">
                {node.relatedTypes.map((relation) => (
                  relation && (
                    <span key={relation} className="text-[10px] uppercase tracking-wide bg-gray-100 px-1.5 py-0.5 rounded">
                      {relation.replace(/_/g, ' ')}
                    </span>
                  )
                ))}
              </div>
            )}
          </button>
        ))}
        {matchingCount === 0 && (
          <p className="py-5 text-center text-xs text-academic-muted">No matching nodes in this period.</p>
        )}
      </div>
      <div className="mt-4 border-t border-stone-200 pt-3">
        <p id={statusId} className="text-xs text-academic-muted" aria-live="polite">
          Showing {firstVisible.toLocaleString()}–{lastVisible.toLocaleString()} of {matchingCount.toLocaleString()}
        </p>
        {pageCount > 1 && (
          <div className="mt-2 flex items-center justify-between gap-2" role="group" aria-describedby={statusId}>
            <button
              type="button"
              onClick={() => onPageChange(page - 1)}
              disabled={page === 0}
              aria-label={`Previous nodes in ${period.label}`}
              className="inline-flex min-h-11 min-w-11 items-center justify-center border border-stone-300 text-stone-700 disabled:cursor-not-allowed disabled:opacity-40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-700"
            >
              <ChevronLeft className="h-4 w-4" aria-hidden="true" />
            </button>
            <span className="text-xs tabular-nums text-stone-600">Page {page + 1} / {pageCount}</span>
            <button
              type="button"
              onClick={() => onPageChange(page + 1)}
              disabled={page >= pageCount - 1}
              aria-label={`Next nodes in ${period.label}`}
              className="inline-flex min-h-11 min-w-11 items-center justify-center border border-stone-300 text-stone-700 disabled:cursor-not-allowed disabled:opacity-40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-700"
            >
              <ChevronRight className="h-4 w-4" aria-hidden="true" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export const TimelinePanel = memo(TimelinePanelComponent);
export default TimelinePanel;
