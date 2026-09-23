import { ArrowDown, ArrowUp, ArrowUpDown, BookmarkCheck, BookmarkPlus } from 'lucide-react';
import {
  memo,
  useCallback,
  useEffect,
  useImperativeHandle,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent,
  type ReactNode,
  type Ref,
} from 'react';
import { useTranslation } from 'react-i18next';

import type { AtlasNodeMeta } from '../cosmograph/AtlasHelpers';
import { MAX_COMPARE, UNATTACHED_SCHOOL, type ScholarSort, type ScholarSortKey } from './scholarModel';
import { useScholarLabels, type ScholarLabels } from './useScholarLabels';

export const ROW_HEIGHT = 60;
const OVERSCAN = 8;
// jsdom and the first paint report a zero-height viewport; render a screenful anyway.
const FALLBACK_VIEWPORT = 720;

export interface ScholarNodeTableHandle {
  focusRow: (index?: number) => void;
}

interface ScholarNodeTableProps {
  rows: ReadonlyArray<AtlasNodeMeta>;
  sort: ScholarSort;
  onSort: (key: ScholarSortKey) => void;
  primaryId: string | null;
  compareIds: ReadonlyArray<string>;
  threadIds: ReadonlySet<string>;
  onSelect: (id: string) => void;
  onToggleCompare: (id: string) => void;
  onToggleThread: (id: string) => void;
  loading: boolean;
  empty: ReactNode;
  captionId: string;
  ref?: Ref<ScholarNodeTableHandle>;
}

interface ColumnDef {
  key: ScholarSortKey;
  labelKey: string;
  className: string;
}

const COLUMNS: ReadonlyArray<ColumnDef> = [
  { key: 'label', labelKey: 'scholar.table.node', className: 'w-auto' },
  { key: 'type', labelKey: 'scholar.table.type', className: 'hidden w-36 md:table-cell' },
  { key: 'period', labelKey: 'scholar.table.period', className: 'hidden w-40 lg:table-cell' },
  { key: 'school', labelKey: 'scholar.table.school', className: 'hidden w-44 2xl:table-cell' },
  { key: 'degree', labelKey: 'scholar.table.links', className: 'w-20 text-right' },
];

function ScholarNodeTableComponent({
  rows,
  sort,
  onSort,
  primaryId,
  compareIds,
  threadIds,
  onSelect,
  onToggleCompare,
  onToggleThread,
  loading,
  empty,
  captionId,
  ref,
}: ScholarNodeTableProps) {
  const { t } = useTranslation();
  const labels = useScholarLabels();
  const scrollRef = useRef<HTMLDivElement>(null);
  const [scrollTop, setScrollTop] = useState(0);
  const [viewport, setViewport] = useState(0);
  const [activeId, setActiveId] = useState<string | null>(null);
  const pendingFocus = useRef(false);
  const frame = useRef(0);

  const indexById = useMemo(() => {
    const map = new Map<string, number>();
    rows.forEach((row, index) => map.set(row.id, index));
    return map;
  }, [rows]);
  const compareSet = useMemo(() => new Set(compareIds), [compareIds]);
  const compareFull = compareIds.length >= MAX_COMPARE;
  const columnCount = useVisibleColumnCount();

  const activeIndex = activeId !== null ? indexById.get(activeId) ?? -1 : -1;
  const tabStopIndex = activeIndex >= 0 ? activeIndex : 0;

  useLayoutEffect(() => {
    const element = scrollRef.current;
    if (!element) return undefined;
    const measure = () => setViewport(element.clientHeight);
    measure();
    if (typeof ResizeObserver === 'undefined') return undefined;
    const observer = new ResizeObserver(measure);
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  // A new result set starts at the top; keeping the old offset would land
  // the reader mid-list in an unrelated ordering.
  useEffect(() => {
    const element = scrollRef.current;
    if (element) element.scrollTop = 0;
    setScrollTop(0);
  }, [rows]);

  useEffect(() => () => cancelAnimationFrame(frame.current), []);

  const onScroll = useCallback(() => {
    cancelAnimationFrame(frame.current);
    frame.current = requestAnimationFrame(() => {
      if (scrollRef.current) setScrollTop(scrollRef.current.scrollTop);
    });
  }, []);

  const height = viewport > 0 ? viewport : FALLBACK_VIEWPORT;
  const start = Math.max(0, Math.floor(scrollTop / ROW_HEIGHT) - OVERSCAN);
  const end = Math.min(rows.length, Math.ceil((scrollTop + height) / ROW_HEIGHT) + OVERSCAN);
  const visible = rows.slice(start, end);

  const moveTo = useCallback((index: number) => {
    if (rows.length === 0) return;
    const clamped = Math.max(0, Math.min(rows.length - 1, index));
    const element = scrollRef.current;
    if (element) {
      const headerOffset = ROW_HEIGHT;
      const rowTop = clamped * ROW_HEIGHT;
      const view = element.clientHeight || FALLBACK_VIEWPORT;
      let nextTop = element.scrollTop;
      if (rowTop < nextTop) nextTop = rowTop;
      else if (rowTop + ROW_HEIGHT + headerOffset > nextTop + view) nextTop = rowTop + ROW_HEIGHT + headerOffset - view;
      element.scrollTop = nextTop;
      setScrollTop(nextTop);
    }
    pendingFocus.current = true;
    setActiveId(rows[clamped]?.id ?? null);
  }, [rows]);

  useEffect(() => {
    if (!pendingFocus.current || activeId === null) return;
    pendingFocus.current = false;
    const button = scrollRef.current?.querySelector<HTMLButtonElement>(
      `button[data-row-primary="${CSS.escape(activeId)}"]`,
    );
    button?.focus({ preventScroll: true });
  });

  useImperativeHandle(ref, () => ({
    focusRow: (index) => moveTo(index ?? (activeIndex >= 0 ? activeIndex : 0)),
  }), [activeIndex, moveTo]);

  const page = Math.max(1, Math.floor(height / ROW_HEIGHT) - 1);

  const onKeyDown = (event: KeyboardEvent<HTMLTableSectionElement>) => {
    if (event.altKey || event.ctrlKey || event.metaKey) return;
    const target = event.target as HTMLElement;
    const rowId = target.closest<HTMLElement>('[data-row-id]')?.dataset.rowId;
    const current = rowId !== undefined ? indexById.get(rowId) ?? 0 : tabStopIndex;
    const handled = (() => {
      switch (event.key) {
        case 'ArrowDown': moveTo(current + 1); return true;
        case 'ArrowUp': moveTo(current - 1); return true;
        case 'PageDown': moveTo(current + page); return true;
        case 'PageUp': moveTo(current - page); return true;
        case 'Home': moveTo(0); return true;
        case 'End': moveTo(rows.length - 1); return true;
        case 'c':
        case 'C': {
          const id = rows[current]?.id;
          if (id && (compareSet.has(id) || !compareFull)) onToggleCompare(id);
          return true;
        }
        case 't':
        case 'T': {
          const id = rows[current]?.id;
          if (id) onToggleThread(id);
          return true;
        }
        default: return false;
      }
    })();
    if (handled) event.preventDefault();
  };

  return (
    <div
      ref={scrollRef}
      onScroll={onScroll}
      className="relative h-full min-h-0 overflow-auto overscroll-contain"
    >
      <table
        aria-describedby={captionId}
        aria-rowcount={rows.length + 1}
        aria-busy={loading || undefined}
        className="w-full table-fixed border-separate border-spacing-0 text-left font-body text-sm"
      >
        <caption className="sr-only">{t('scholar.table.caption')}</caption>
        <thead className="sticky top-0 z-10 bg-[#f1ebe1]">
          <tr aria-rowindex={1} className="h-[60px]">
            <th scope="col" className="w-14 border-b border-stone-300 px-1 text-center">
              <span className="sr-only">{t('scholar.table.compare')}</span>
              <span aria-hidden="true" className="text-[10px] font-semibold uppercase tracking-[0.14em] text-stone-500">
                {labels.number(compareIds.length)}/{MAX_COMPARE}
              </span>
            </th>
            {COLUMNS.map((column) => (
              <SortHeader key={column.key} column={column} sort={sort} onSort={onSort} />
            ))}
            <th scope="col" className="w-14 border-b border-stone-300">
              <span className="sr-only">{t('scholar.table.thread')}</span>
            </th>
          </tr>
        </thead>
        <tbody onKeyDown={onKeyDown}>
          {loading && rows.length === 0 && <SkeletonRows columnCount={columnCount} />}
          {!loading && rows.length === 0 && (
            <tr>
              <td colSpan={columnCount} className="px-4 py-14">{empty}</td>
            </tr>
          )}
          {start > 0 && (
            <tr aria-hidden="true" style={{ height: start * ROW_HEIGHT }}><td /></tr>
          )}
          {visible.map((node, offset) => {
            const index = start + offset;
            return (
              <TableRow
                key={node.id}
                node={node}
                index={index}
                labels={labels}
                isPrimary={primaryId === node.id}
                isCompared={compareSet.has(node.id)}
                compareDisabled={compareFull && !compareSet.has(node.id)}
                inThread={threadIds.has(node.id)}
                isTabStop={index === tabStopIndex}
                onFocusRow={setActiveId}
                onSelect={onSelect}
                onToggleCompare={onToggleCompare}
                onToggleThread={onToggleThread}
              />
            );
          })}
          {end < rows.length && (
            <tr aria-hidden="true" style={{ height: (rows.length - end) * ROW_HEIGHT }}><td /></tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

// Tailwind breakpoints for the responsive columns (md, lg, 2xl). A colSpan
// wider than the rendered columns makes a fixed-layout table invent a
// phantom column, so spans must track what is actually displayed.
const COLUMN_QUERIES = ['(min-width: 768px)', '(min-width: 1024px)', '(min-width: 1536px)'] as const;

function countColumns(): number {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return 4;
  return 4 + COLUMN_QUERIES.filter((query) => window.matchMedia(query).matches).length;
}

function useVisibleColumnCount(): number {
  const [count, setCount] = useState(countColumns);
  useEffect(() => {
    if (typeof window.matchMedia !== 'function') return undefined;
    const lists = COLUMN_QUERIES.map((query) => window.matchMedia(query));
    const update = () => setCount(countColumns());
    lists.forEach((list) => list.addEventListener('change', update));
    return () => lists.forEach((list) => list.removeEventListener('change', update));
  }, []);
  return count;
}

function SortHeader({
  column,
  sort,
  onSort,
}: {
  column: ColumnDef;
  sort: ScholarSort;
  onSort: (key: ScholarSortKey) => void;
}) {
  const { t } = useTranslation();
  const active = sort.key === column.key;
  const ariaSort = active ? (sort.direction === 'asc' ? 'ascending' : 'descending') : 'none';
  const Icon = !active ? ArrowUpDown : sort.direction === 'asc' ? ArrowUp : ArrowDown;
  const numeric = column.key === 'degree';
  return (
    <th scope="col" aria-sort={ariaSort} className={`border-b border-stone-300 p-0 ${column.className}`}>
      <button
        type="button"
        onClick={() => onSort(column.key)}
        className={[
          'group inline-flex h-full min-h-11 w-full items-center gap-1.5 px-3 text-[10px] font-semibold uppercase tracking-[0.14em] outline-none transition-colors focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-orange-700',
          numeric ? 'justify-end' : 'justify-start',
          active ? 'text-orange-900' : 'text-stone-600 hover:text-stone-950',
        ].join(' ')}
      >
        {t(column.labelKey)}
        <Icon
          className={`h-3.5 w-3.5 shrink-0 ${active ? 'text-orange-800' : 'text-stone-400 group-hover:text-stone-600'}`}
          aria-hidden="true"
        />
        {active && (
          <span className="sr-only">
            {sort.direction === 'asc' ? t('scholar.table.sortedAsc') : t('scholar.table.sortedDesc')}
          </span>
        )}
      </button>
    </th>
  );
}

interface TableRowProps {
  node: AtlasNodeMeta;
  index: number;
  labels: ScholarLabels;
  isPrimary: boolean;
  isCompared: boolean;
  compareDisabled: boolean;
  inThread: boolean;
  isTabStop: boolean;
  onFocusRow: (id: string) => void;
  onSelect: (id: string) => void;
  onToggleCompare: (id: string) => void;
  onToggleThread: (id: string) => void;
}

const TableRow = memo(function TableRow({
  node,
  index,
  labels,
  isPrimary,
  isCompared,
  compareDisabled,
  inThread,
  isTabStop,
  onFocusRow,
  onSelect,
  onToggleCompare,
  onToggleThread,
}: TableRowProps) {
  const { t } = useTranslation();
  const term = node.greekTerm || node.latinTerm;
  const typeLabel = labels.nodeType(node);
  const cell = 'border-b border-stone-200/80 align-middle';
  return (
    <tr
      data-row-id={node.id}
      aria-rowindex={index + 2}
      onFocus={() => onFocusRow(node.id)}
      className={[
        'group/row h-[60px] transition-colors',
        isPrimary
          ? 'bg-orange-50 shadow-[inset_3px_0_0_#9a3412]'
          : isCompared
            ? 'bg-teal-50/60 hover:bg-teal-50'
            : 'bg-[#fffdf9] hover:bg-[#f7f2e9]',
      ].join(' ')}
    >
      <td className={`${cell} p-0 text-center`}>
        <label
          className={`inline-flex min-h-11 min-w-11 items-center justify-center ${compareDisabled ? 'cursor-not-allowed' : 'cursor-pointer'}`}
          title={compareDisabled ? t('scholar.table.compareFull') : undefined}
        >
          <input
            type="checkbox"
            tabIndex={isTabStop ? 0 : -1}
            checked={isCompared}
            disabled={compareDisabled}
            onChange={() => onToggleCompare(node.id)}
            aria-label={isCompared
              ? t('scholar.table.removeCompare', { label: node.label })
              : t('scholar.table.addCompare', { label: node.label })}
            className="h-5 w-5 rounded-sm border-stone-400 text-teal-700 focus:ring-teal-700 disabled:opacity-30"
          />
        </label>
      </td>
      <th scope="row" className={`${cell} p-0 font-medium`}>
        <button
          type="button"
          data-row-primary={node.id}
          tabIndex={isTabStop ? 0 : -1}
          onClick={() => onSelect(node.id)}
          aria-current={isPrimary ? 'true' : undefined}
          className="flex h-full min-h-11 w-full min-w-0 flex-col justify-center px-3 text-left outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-orange-700"
        >
          <span className={`block truncate ${isPrimary ? 'text-orange-950' : 'text-stone-950 group-hover/row:text-orange-900'}`}>
            {node.label}
          </span>
          {term ? (
            <span className="block truncate font-reader text-[15px] font-normal leading-5 text-stone-500">{term}</span>
          ) : (
            <span className="block truncate text-xs font-normal text-stone-500 md:hidden">
              {typeLabel} · {labels.period(node.periodLabel)}
            </span>
          )}
        </button>
      </th>
      <td className={`${cell} hidden px-3 text-stone-600 md:table-cell`}>
        <span className="inline-flex min-w-0 items-center gap-2">
          <span aria-hidden="true" className="h-2 w-2 shrink-0 rounded-full ring-1 ring-black/10" style={{ backgroundColor: node.color }} />
          <span className="truncate">{typeLabel}</span>
        </span>
      </td>
      <td className={`${cell} hidden truncate px-3 text-stone-600 lg:table-cell`}>{labels.period(node.periodLabel)}</td>
      <td className={`${cell} hidden truncate px-3 2xl:table-cell ${node.schoolLabel === UNATTACHED_SCHOOL ? 'text-stone-400' : 'text-stone-600'}`}>
        {node.schoolLabel === UNATTACHED_SCHOOL ? (
          <>
            <span aria-hidden="true">—</span>
            <span className="sr-only">{labels.school(node.schoolLabel)}</span>
          </>
        ) : node.schoolLabel}
      </td>
      <td className={`${cell} px-3 text-right tabular-nums text-stone-600`}>{labels.number(node.degree)}</td>
      <td className={`${cell} p-0 text-center`}>
        <button
          type="button"
          tabIndex={isTabStop ? 0 : -1}
          onClick={() => onToggleThread(node.id)}
          aria-pressed={inThread}
          aria-label={inThread
            ? t('scholar.table.removeThread', { label: node.label })
            : t('scholar.table.addThread', { label: node.label })}
          title={inThread ? t('scholar.table.inThread') : t('scholar.table.addThreadShort')}
          className={[
            'inline-flex h-11 w-11 items-center justify-center outline-none transition-colors focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-orange-700',
            inThread ? 'text-orange-800' : 'text-stone-400 hover:text-orange-800',
          ].join(' ')}
        >
          {inThread
            ? <BookmarkCheck className="h-4 w-4" aria-hidden="true" />
            : <BookmarkPlus className="h-4 w-4" aria-hidden="true" />}
        </button>
      </td>
    </tr>
  );
});

const SKELETON_WIDTHS = ['w-2/5', 'w-3/5', 'w-1/2', 'w-2/3', 'w-1/3'] as const;

function SkeletonRows({ columnCount }: { columnCount: number }) {
  return (
    <>
      {Array.from({ length: 10 }, (_, index) => (
        <tr key={index} aria-hidden="true" className="h-[60px]">
          <td className="border-b border-stone-200/80" />
          <td colSpan={columnCount - 1} className="border-b border-stone-200/80 px-3">
            <span
              className={`block h-3 rounded-sm bg-stone-200/80 motion-safe:animate-pulse ${SKELETON_WIDTHS[index % SKELETON_WIDTHS.length]}`}
            />
          </td>
        </tr>
      ))}
    </>
  );
}

export default memo(ScholarNodeTableComponent);
