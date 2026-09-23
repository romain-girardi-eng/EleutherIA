import { ArrowRight, Grid3x3 } from 'lucide-react';
import { memo, useId, useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { useGraphWorkspace } from '../../context/GraphWorkspaceContext';
import {
  buildInfluenceMatrix,
  cellKey,
  type InfluenceCell,
  type RelationCategoryFilter,
} from './scholarModel';
import { useScholarLabels } from './useScholarLabels';

const CATEGORIES: ReadonlyArray<RelationCategoryFilter> = ['all', 'structural', 'doctrinal', 'evidential'];
const focusRing = 'outline-none focus-visible:ring-2 focus-visible:ring-orange-700';

// orange-800 (#9a3412) on parchment: a single-hue ramp reads as "more", never as a category.
function cellColor(count: number, max: number): string {
  if (count === 0 || max === 0) return 'transparent';
  const intensity = Math.sqrt(count / max);
  return `rgba(154, 52, 18, ${(0.08 + 0.82 * intensity).toFixed(3)})`;
}

function isDark(count: number, max: number): boolean {
  return max > 0 && Math.sqrt(count / max) > 0.55;
}

interface InfluenceMatrixPanelProps {
  onShowSchools?: (schools: string[]) => void;
}

function InfluenceMatrixPanelComponent({ onShowSchools }: InfluenceMatrixPanelProps) {
  const { t } = useTranslation();
  const labels = useScholarLabels();
  const { data, loading } = useGraphWorkspace();
  const [category, setCategory] = useState<RelationCategoryFilter>('all');
  const [activeKey, setActiveKey] = useState<string | null>(null);
  const [pinnedKey, setPinnedKey] = useState<string | null>(null);
  const detailId = useId();
  const detailRef = useRef<HTMLDivElement>(null);

  const matrix = useMemo(
    () => buildInfluenceMatrix(data.meta, data.edges, category),
    [category, data.edges, data.meta],
  );
  const focusKey = pinnedKey ?? activeKey;
  const active: InfluenceCell | null = focusKey ? matrix.cells.get(focusKey) ?? null : null;

  if (loading && data.meta.length === 0) {
    return <p role="status" className="px-4 py-16 text-center font-body text-sm text-stone-600">{t('scholar.matrix.loading')}</p>;
  }

  return (
    <div className="space-y-5 p-3 sm:p-5">
      <div className="flex flex-col gap-4">
        <div className="max-w-2xl">
          <h2 className="flex items-center gap-2 font-display text-3xl text-stone-950">
            <Grid3x3 className="h-5 w-5 text-orange-800" aria-hidden="true" />
            {t('scholar.matrix.title')}
          </h2>
          <p className="mt-1.5 font-reader text-base leading-6 text-stone-600">
            {t('scholar.matrix.description', { edges: labels.number(matrix.total), schools: matrix.schools.length })}
          </p>
        </div>
        <fieldset>
          <legend className="sr-only">{t('scholar.matrix.categoryLegend')}</legend>
          <div className="inline-flex max-w-full overflow-x-auto border border-stone-300 bg-[#fffdf9]">
            {CATEGORIES.map((value) => (
              <label
                key={value}
                className={[
                  'relative inline-flex min-h-11 cursor-pointer items-center px-3 font-body text-xs font-semibold transition-colors focus-within:ring-2 focus-within:ring-inset focus-within:ring-orange-700',
                  category === value ? 'bg-stone-900 text-[#fffdf9]' : 'text-stone-600 hover:text-stone-950',
                ].join(' ')}
              >
                <input
                  type="radio"
                  name="scholar-matrix-category"
                  value={value}
                  checked={category === value}
                  onChange={() => {
                    setCategory(value);
                    setPinnedKey(null);
                  }}
                  className="sr-only"
                />
                {t(`scholar.matrix.categories.${value}`)}
              </label>
            ))}
          </div>
        </fieldset>
      </div>

      {matrix.schools.length === 0 ? (
        <p className="border border-dashed border-stone-300 px-4 py-12 text-center font-reader text-lg text-stone-600">
          {t('scholar.matrix.empty')}
        </p>
      ) : (
        <div className="grid gap-6 2xl:grid-cols-[minmax(0,1fr)_22rem]">
          <div className="overflow-x-auto border border-stone-300 bg-[#fffdf9]">
            <table className="border-collapse font-body text-xs" aria-describedby={detailId}>
              <caption className="sr-only">{t('scholar.matrix.caption')}</caption>
              <thead>
                <tr>
                  <td className="sticky left-0 z-10 min-w-[10rem] border-b border-r border-stone-300 bg-[#f1ebe1] px-3 py-2 align-bottom text-[10px] font-semibold uppercase tracking-[0.14em] text-stone-500">
                    {t('scholar.matrix.axis')}
                  </td>
                  {matrix.schools.map((school) => (
                    <th
                      key={school}
                      scope="col"
                      className="h-40 w-12 min-w-12 border-b border-stone-300 bg-[#f1ebe1] px-1 pb-2 align-bottom font-medium text-stone-700"
                    >
                      <span className="inline-block max-h-36 rotate-180 truncate text-left [writing-mode:vertical-rl]">{school}</span>
                    </th>
                  ))}
                  <th scope="col" className="w-16 border-b border-l border-stone-300 bg-[#f1ebe1] px-2 pb-2 align-bottom text-[10px] font-semibold uppercase tracking-[0.14em] text-stone-500">
                    {t('scholar.matrix.outgoing')}
                  </th>
                </tr>
              </thead>
              <tbody>
                {matrix.schools.map((source) => (
                  <tr key={source}>
                    <th scope="row" className="sticky left-0 z-10 border-r border-stone-300 bg-[#fffdf9] px-3 text-left font-medium text-stone-800">
                      <span className="block max-w-[12rem] truncate">{source}</span>
                    </th>
                    {matrix.schools.map((target) => {
                      const key = cellKey(source, target);
                      const count = matrix.cells.get(key)?.count ?? 0;
                      const selected = focusKey === key;
                      return (
                        <td key={target} className="relative border border-stone-200 p-0">
                          <button
                            type="button"
                            disabled={count === 0}
                            aria-pressed={pinnedKey === key}
                            aria-label={t('scholar.matrix.cellLabel', { source, target, count, formatted: labels.number(count) })}
                            onMouseEnter={() => setActiveKey(key)}
                            onMouseLeave={() => setActiveKey(null)}
                            onFocus={() => setActiveKey(key)}
                            onBlur={() => setActiveKey(null)}
                            onClick={() => {
                              const next = pinnedKey === key ? null : key;
                              setPinnedKey(next);
                              if (next) detailRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                            }}
                            className={[
                              'flex h-11 w-12 items-center justify-center tabular-nums outline-none transition-shadow focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-stone-950 disabled:cursor-default',
                              selected ? 'ring-2 ring-inset ring-stone-950' : '',
                              source === target ? 'bg-[repeating-linear-gradient(135deg,transparent_0_4px,rgba(120,113,108,0.08)_4px_5px)]' : '',
                              isDark(count, matrix.max) ? 'font-semibold text-[#fffdf9]' : 'text-stone-700',
                            ].join(' ')}
                            style={{ backgroundColor: cellColor(count, matrix.max) }}
                          >
                            {count > 0 ? labels.number(count) : <span className="text-stone-300" aria-hidden="true">·</span>}
                          </button>
                          {activeKey === key && count > 0 && (
                            <CellTooltip cell={matrix.cells.get(key)} format={labels.number} relation={labels.relation} />
                          )}
                        </td>
                      );
                    })}
                    <td className="border-l border-stone-300 px-2 text-right tabular-nums text-stone-600">
                      {labels.number(matrix.outgoing.get(source) ?? 0)}
                    </td>
                  </tr>
                ))}
                <tr>
                  <th scope="row" className="sticky left-0 z-10 border-r border-t border-stone-300 bg-[#f1ebe1] px-3 py-2 text-left text-[10px] font-semibold uppercase tracking-[0.14em] text-stone-500">
                    {t('scholar.matrix.incoming')}
                  </th>
                  {matrix.schools.map((target) => (
                    <td key={target} className="border-t border-stone-300 bg-[#f1ebe1] py-2 text-center tabular-nums text-stone-600">
                      {labels.number(matrix.incoming.get(target) ?? 0)}
                    </td>
                  ))}
                  <td className="border-l border-t border-stone-300 bg-[#f1ebe1] px-2 text-right font-semibold tabular-nums text-stone-900">
                    {labels.number(matrix.total)}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <aside className="space-y-5">
            <div>
              <p className="font-body text-[10px] font-semibold uppercase tracking-[0.2em] text-stone-500">{t('scholar.matrix.legend')}</p>
              <div className="mt-2 h-3 w-full max-w-xs bg-[linear-gradient(90deg,rgba(154,52,18,0.08),rgba(154,52,18,0.9))]" aria-hidden="true" />
              <div className="mt-1 flex max-w-xs justify-between font-body text-[11px] tabular-nums text-stone-500">
                <span>1</span>
                <span>{labels.number(matrix.max)}</span>
              </div>
              <p className="mt-2 font-body text-xs leading-5 text-stone-600">{t('scholar.matrix.legendBody')}</p>
            </div>

            <div ref={detailRef} id={detailId} aria-live="polite" className="scroll-mb-6 border-t-2 border-stone-900 pt-3">
              {active ? (
                <>
                  <p className="flex flex-wrap items-center gap-x-1.5 font-display text-2xl leading-tight text-stone-950">
                    {active.source} <ArrowRight className="h-4 w-4 text-orange-800" aria-hidden="true" /> {active.target}
                  </p>
                  <p className="mt-1 font-body text-xs text-stone-600">
                    {t('scholar.matrix.cellCount', { count: active.count, formatted: labels.number(active.count) })}
                  </p>
                  <ul className="mt-3 space-y-1.5">
                    {active.relations.slice(0, 6).map(([relation, count]) => (
                      <li key={relation} className="grid grid-cols-[1fr_auto] items-center gap-x-3 gap-y-0.5 font-body text-xs">
                        <span className="truncate text-teal-800">{labels.relation(relation)}</span>
                        <span className="tabular-nums text-stone-600">{labels.number(count)}</span>
                        <span className="col-span-2 block h-1 bg-stone-200">
                          <span className="block h-1 bg-teal-700" style={{ width: `${Math.max(4, (count / active.count) * 100)}%` }} />
                        </span>
                      </li>
                    ))}
                  </ul>
                  {active.samples.length > 0 && (
                    <>
                      <p className="mt-4 font-body text-[10px] font-semibold uppercase tracking-[0.2em] text-stone-500">{t('scholar.matrix.examples')}</p>
                      <ul className="mt-1.5 space-y-1.5 font-body text-xs leading-5 text-stone-700">
                        {active.samples.map((sample, index) => (
                          <li key={`${sample.source}-${sample.target}-${index}`}>
                            <span className="text-stone-900">{sample.source}</span>
                            <span className="mx-1 text-teal-800">{labels.relation(sample.relation)}</span>
                            <span className="text-stone-900">{sample.target}</span>
                          </li>
                        ))}
                      </ul>
                    </>
                  )}
                  {onShowSchools && (
                    <button
                      type="button"
                      onClick={() => onShowSchools(active.source === active.target ? [active.source] : [active.source, active.target])}
                      className={`mt-4 inline-flex min-h-11 items-center border border-stone-900 px-4 font-body text-xs font-semibold text-stone-900 hover:bg-stone-900 hover:text-[#fffdf9] ${focusRing}`}
                    >
                      {t('scholar.matrix.showInIndex')}
                    </button>
                  )}
                </>
              ) : (
                <p className="font-reader text-base leading-6 text-stone-600">{t('scholar.matrix.hint')}</p>
              )}
            </div>
          </aside>
        </div>
      )}
    </div>
  );
}

function CellTooltip({
  cell,
  format,
  relation,
}: {
  cell: InfluenceCell | undefined;
  format: (value: number) => string;
  relation: (value: string) => string;
}) {
  if (!cell) return null;
  const top = cell.relations[0];
  return (
    <span
      aria-hidden="true"
      className="pointer-events-none absolute bottom-full left-1/2 z-30 mb-1.5 w-max max-w-[15rem] -translate-x-1/2 bg-stone-900 px-2.5 py-1.5 text-left font-body text-[11px] leading-4 text-[#fffdf9] shadow-[0_8px_20px_rgba(28,25,23,0.25)]"
    >
      <span className="block font-semibold">{cell.source} → {cell.target}</span>
      <span className="block tabular-nums text-stone-300">
        {format(cell.count)}
        {top ? ` · ${relation(top[0])} ${format(top[1])}` : ''}
      </span>
    </span>
  );
}

export const InfluenceMatrixPanel = memo(InfluenceMatrixPanelComponent);
export default InfluenceMatrixPanel;
