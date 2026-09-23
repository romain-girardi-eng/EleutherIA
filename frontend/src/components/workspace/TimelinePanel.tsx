import { memo, useDeferredValue, useEffect, useMemo, useState } from 'react';
import { ArrowRight, ChevronLeft, ChevronRight, Clock, GitCompareArrows, Search, X } from 'lucide-react';
import { useTranslation } from 'react-i18next';

import AccordionPanel from '../mobile/AccordionPanel';
import type { TimelineNodeSummary, TimelineOverview } from '../../types';
import { formatCount, periodName, typeName } from './chronosFormat';
import { nodeMatchesSchool, SCHOOL_NONE, SCHOOL_OTHER, type SchoolFilter } from './chronosTimeline';

export const TIMELINE_PAGE_SIZE = 24;

function sortNodes(nodes: TimelineNodeSummary[]) {
  return nodes.sort((left, right) => {
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

const EMPTY_IDS: ReadonlyArray<string> = [];

export interface TimelinePanelProps {
  timeline: TimelineOverview | null;
  loading?: boolean;
  onSelectNode: (nodeId: string) => void;
  onToggleCompare?: (nodeId: string) => void;
  /** Period key to list; `null` lists every visible period. */
  activePeriodKey?: string | null;
  schoolFilter?: SchoolFilter | null;
  onClearScope?: () => void;
  primarySelection?: string | null;
  compareIds?: ReadonlyArray<string>;
  threadIds?: ReadonlyArray<string>;
  defaultExpanded?: boolean;
}

function TimelinePanelComponent({
  timeline,
  loading = false,
  onSelectNode,
  onToggleCompare,
  activePeriodKey = null,
  schoolFilter = null,
  onClearScope,
  primarySelection = null,
  compareIds = EMPTY_IDS,
  threadIds = EMPTY_IDS,
  defaultExpanded = true,
}: TimelinePanelProps) {
  const { t, i18n } = useTranslation();
  const locale = i18n.language || 'en';
  const [query, setQuery] = useState('');
  const deferredQuery = useDeferredValue(query.trim().toLocaleLowerCase());
  const [page, setPage] = useState(0);

  const periods = useMemo(() => timeline?.periods ?? [], [timeline]);
  const activePeriod = periods.find((period) => period.key === activePeriodKey) ?? null;
  const compareSet = useMemo(() => new Set(compareIds), [compareIds]);
  const threadIndex = useMemo(
    () => new Map(threadIds.map((id, index) => [id, index + 1])),
    [threadIds],
  );

  useEffect(() => setPage(0), [activePeriodKey, schoolFilter, deferredQuery, timeline]);

  const scoped = useMemo(() => {
    const source = activePeriod ? activePeriod.nodes : periods.flatMap((period) => period.nodes);
    return schoolFilter ? source.filter((node) => nodeMatchesSchool(node, schoolFilter)) : source;
  }, [activePeriod, periods, schoolFilter]);
  const results = useMemo(
    () => sortNodes(scoped.filter((node) => matches(node, deferredQuery))),
    [deferredQuery, scoped],
  );

  const pageCount = Math.max(1, Math.ceil(results.length / TIMELINE_PAGE_SIZE));
  const safePage = Math.min(page, pageCount - 1);
  const visibleNodes = results.slice(safePage * TIMELINE_PAGE_SIZE, (safePage + 1) * TIMELINE_PAGE_SIZE);
  const firstVisible = results.length === 0 ? 0 : safePage * TIMELINE_PAGE_SIZE + 1;
  const lastVisible = Math.min((safePage + 1) * TIMELINE_PAGE_SIZE, results.length);

  const schoolName = schoolFilter
    ? schoolFilter.key === SCHOOL_NONE
      ? t('chronos.matrix.noSchool')
      : schoolFilter.key === SCHOOL_OTHER
        ? t('chronos.matrix.otherSchools', { count: schoolFilter.members.length })
        : schoolFilter.key
    : null;
  const scopeName = [activePeriod ? periodName(t, activePeriod.label) : null, schoolName]
    .filter(Boolean)
    .join(' · ') || t('chronos.ledger.allPeriods');
  const hasScope = activePeriod !== null || schoolFilter !== null;
  const title = t('chronos.ledger.title');

  if (loading && !timeline) {
    return (
      <AccordionPanel title={title} icon={<Clock className="h-5 w-5" />} defaultExpanded={defaultExpanded} headingLevel={2} className="min-w-0">
        <p role="status" className="py-16 text-center font-body text-sm text-stone-600">{t('chronos.states.loading')}</p>
      </AccordionPanel>
    );
  }

  if (!timeline || periods.length === 0) {
    return (
      <AccordionPanel title={title} icon={<Clock className="h-5 w-5" />} defaultExpanded={defaultExpanded} headingLevel={2} className="min-w-0">
        <p className="py-16 text-center font-reader text-lg text-stone-600">{t('chronos.states.noPeriods')}</p>
      </AccordionPanel>
    );
  }

  return (
    <AccordionPanel
      title={title}
      icon={<Clock className="h-5 w-5" />}
      badge={formatCount(locale, scoped.length)}
      defaultExpanded={defaultExpanded}
      headingLevel={2}
      className="min-w-0 border-stone-300 bg-[#fffdf9] shadow-none"
    >
      <div className="grid gap-4 border-y border-stone-300 py-4 lg:grid-cols-[minmax(0,24rem)_1fr] lg:items-end">
        <label className="block font-body text-xs font-semibold text-stone-700">
          {t('chronos.ledger.searchLabel')}
          <span className="relative mt-1 block">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-stone-500" aria-hidden="true" />
            <input
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder={t('chronos.ledger.searchPlaceholder')}
              aria-label={t('chronos.ledger.searchLabel')}
              className="min-h-11 w-full border border-stone-300 bg-white pl-10 pr-3 text-base font-normal text-stone-900 outline-none focus:border-orange-700 focus:ring-1 focus:ring-orange-700"
            />
          </span>
        </label>
        <div className="flex min-w-0 items-end justify-between gap-3">
          <div className="min-w-0">
            <p className="truncate font-body text-[10px] font-bold uppercase tracking-[0.18em] text-orange-800">{scopeName}</p>
            <p role="status" aria-live="polite" className="mt-1 font-body text-xs leading-5 text-stone-600">
              {deferredQuery
                ? t('chronos.ledger.matches', { count: results.length, formatted: formatCount(locale, results.length) })
                : t('chronos.ledger.inScope', { count: results.length, formatted: formatCount(locale, results.length) })}
            </p>
          </div>
          {hasScope && onClearScope && (
            <button
              type="button"
              onClick={onClearScope}
              className="inline-flex min-h-11 shrink-0 items-center gap-1.5 px-2 font-body text-xs font-semibold text-stone-700 underline decoration-stone-300 underline-offset-4 hover:text-orange-800 hover:decoration-orange-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-700"
            >
              <X className="h-3.5 w-3.5" aria-hidden="true" />
              {t('chronos.ledger.clearScope')}
            </button>
          )}
        </div>
      </div>

      <ol className="grid gap-x-6 md:grid-cols-2" start={firstVisible}>
        {visibleNodes.map((node, index) => {
          const selected = node.id === primarySelection;
          const compared = compareSet.has(node.id);
          const threadStep = threadIndex.get(node.id);
          const meta = [
            typeName(t, node.type),
            node.school,
            deferredQuery || !activePeriod ? (node.period ? periodName(t, node.period) : null) : null,
          ].filter(Boolean).join(' · ');
          return (
            <li
              key={node.id}
              className={['group flex min-h-11 items-stretch border-b border-stone-200', selected ? 'bg-orange-50' : ''].join(' ')}
            >
              <button
                data-testid="timeline-node"
                type="button"
                aria-current={selected || undefined}
                onClick={() => onSelectNode(node.id)}
                className="grid min-h-11 min-w-0 flex-1 grid-cols-[2.25rem_1fr_auto] items-center gap-3 py-2.5 pl-1 text-left outline-none transition-colors hover:text-orange-900 focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-orange-700"
              >
                <span className="font-display text-lg tabular-nums text-stone-400">{String(firstVisible + index).padStart(2, '0')}</span>
                <span className="min-w-0">
                  <span className={['block truncate font-body text-sm font-semibold group-hover:text-orange-900', selected ? 'text-orange-900' : 'text-stone-900'].join(' ')}>{node.label}</span>
                  <span className="mt-0.5 block truncate font-body text-[10px] uppercase tracking-[0.12em] text-stone-500">{meta}</span>
                </span>
                <span className="flex items-center gap-2">
                  {threadStep !== undefined && (
                    <span className="font-body text-[10px] font-semibold tabular-nums text-teal-800">
                      {t('chronos.ledger.threadStep', { step: threadStep })}
                    </span>
                  )}
                  <ArrowRight className="h-3.5 w-3.5 text-stone-400 transition-transform motion-safe:group-hover:translate-x-1" aria-hidden="true" />
                </span>
              </button>
              {onToggleCompare && (
                <button
                  type="button"
                  aria-pressed={compared}
                  aria-label={t(compared ? 'chronos.ledger.removeCompare' : 'chronos.ledger.addCompare', { label: node.label })}
                  title={t(compared ? 'chronos.ledger.removeCompare' : 'chronos.ledger.addCompare', { label: node.label })}
                  onClick={() => onToggleCompare(node.id)}
                  className={[
                    'inline-flex w-11 shrink-0 items-center justify-center outline-none transition-colors focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-teal-700',
                    compared ? 'text-teal-700' : 'text-stone-400 hover:text-teal-700',
                  ].join(' ')}
                >
                  <GitCompareArrows className="h-4 w-4" aria-hidden="true" />
                </button>
              )}
            </li>
          );
        })}
      </ol>

      {results.length === 0 && (
        <p className="py-12 text-center font-reader text-lg text-stone-600">{t('chronos.ledger.noMatches')}</p>
      )}

      <div className="mt-5 flex items-center justify-between gap-3 border-t border-stone-300 pt-4">
        <p className="font-body text-xs text-stone-600" aria-live="polite">
          {t('chronos.ledger.showing', {
            first: formatCount(locale, firstVisible),
            last: formatCount(locale, lastVisible),
            total: formatCount(locale, results.length),
          })}
        </p>
        {pageCount > 1 && (
          <div className="flex items-center gap-2">
            <button type="button" onClick={() => setPage(Math.max(0, safePage - 1))} disabled={safePage === 0} aria-label={t('chronos.ledger.previous', { scope: scopeName })} className="inline-flex h-11 w-11 items-center justify-center border border-stone-300 disabled:opacity-30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-700"><ChevronLeft className="h-4 w-4" aria-hidden="true" /></button>
            <span className="min-w-20 text-center font-body text-xs tabular-nums text-stone-600">{safePage + 1} / {pageCount}</span>
            <button type="button" onClick={() => setPage(Math.min(pageCount - 1, safePage + 1))} disabled={safePage >= pageCount - 1} aria-label={t('chronos.ledger.next', { scope: scopeName })} className="inline-flex h-11 w-11 items-center justify-center border border-stone-300 disabled:opacity-30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-700"><ChevronRight className="h-4 w-4" aria-hidden="true" /></button>
          </div>
        )}
      </div>
    </AccordionPanel>
  );
}

export const TimelinePanel = memo(TimelinePanelComponent);
export default TimelinePanel;
