import { memo, useRef, useState, type KeyboardEvent } from 'react';
import { useTranslation } from 'react-i18next';

import { formatCount, formatYearRange, periodName } from './chronosFormat';
import {
  densityIntensity,
  SCHOOL_NONE,
  SCHOOL_OTHER,
  type SchoolFilter,
  type SchoolMatrix,
  type SchoolMatrixRow,
} from './chronosTimeline';

export interface SchoolPeriodMatrixProps {
  matrix: SchoolMatrix;
  activePeriodKey: string | null;
  activeSchool: SchoolFilter | null;
  selectedPeriodLabel: string | null;
  selectedSchool: string | null;
  onSelect: (periodKey: string | null, school: SchoolFilter | null) => void;
}

function cellFill(intensity: number) {
  const weight = Math.round(14 + intensity * 86);
  return `color-mix(in oklab, #0f766e ${weight}%, #e3f1ee)`;
}

function SchoolPeriodMatrixComponent({
  matrix,
  activePeriodKey,
  activeSchool,
  selectedPeriodLabel,
  selectedSchool,
  onSelect,
}: SchoolPeriodMatrixProps) {
  const { t, i18n } = useTranslation();
  const locale = i18n.language || 'en';
  const tableRef = useRef<HTMLTableElement>(null);
  const [focusCell, setFocusCell] = useState<readonly [number, number]>([0, 0]);
  const { columns, rows, max } = matrix;
  const activeSchoolKey = activeSchool?.key ?? null;
  const compact = new Intl.NumberFormat(locale, { notation: 'compact', maximumFractionDigits: 1 });

  const rowName = (row: SchoolMatrixRow) => {
    if (row.key === SCHOOL_OTHER) return t('chronos.matrix.otherSchools', { count: row.members.length });
    if (row.key === SCHOOL_NONE) return t('chronos.matrix.noSchool');
    return row.label ?? row.key;
  };

  const moveFocus = (event: KeyboardEvent<HTMLButtonElement>, rowIndex: number, columnIndex: number) => {
    const deltas: Record<string, readonly [number, number]> = {
      ArrowUp: [-1, 0],
      ArrowDown: [1, 0],
      ArrowLeft: [0, -1],
      ArrowRight: [0, 1],
    };
    const delta = deltas[event.key];
    if (!delta) return;
    event.preventDefault();
    const nextRow = Math.min(rows.length - 1, Math.max(0, rowIndex + delta[0]));
    const nextColumn = Math.min(columns.length - 1, Math.max(0, columnIndex + delta[1]));
    setFocusCell([nextRow, nextColumn]);
    tableRef.current
      ?.querySelector<HTMLButtonElement>(`[data-cell="${nextRow}:${nextColumn}"]`)
      ?.focus();
  };

  if (rows.length === 0 || columns.length === 0) {
    return <p className="py-10 text-center font-reader text-lg text-stone-600">{t('chronos.states.noPeriods')}</p>;
  }

  const [focusRow, focusColumn] = [
    Math.min(focusCell[0], rows.length - 1),
    Math.min(focusCell[1], columns.length - 1),
  ];

  return (
    <div className="min-w-0">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="font-display text-[1.9rem] leading-none text-stone-950">{t('chronos.matrix.title')}</h2>
          <p className="mt-2 max-w-xl font-body text-[13px] leading-5 text-stone-600">{t('chronos.matrix.caption')}</p>
        </div>
        <p className="font-body text-[11px] text-stone-500">{t('chronos.matrix.keyboardHint')}</p>
      </div>
      <div className="mt-4 overflow-x-auto overscroll-x-contain border-y border-stone-300 bg-[#fffdf9]">
        <table ref={tableRef} className="border-separate border-spacing-0 font-body text-[12px]">
          <caption className="sr-only">{t('chronos.matrix.tableCaption')}</caption>
          <thead>
            <tr>
              <th scope="col" className="sticky left-0 z-10 bg-[#fffdf9] px-3 pb-2 text-left align-bottom text-[10px] font-semibold uppercase tracking-[0.16em] text-stone-500">
                {t('chronos.matrix.schoolColumn')}
              </th>
              {columns.map((period) => {
                const focused = period.label === selectedPeriodLabel;
                const active = period.key === activePeriodKey;
                return (
                  <th key={period.key} scope="col" className="h-36 w-9 min-w-9 px-0 pb-2 align-bottom">
                    <button
                      type="button"
                      onClick={() => onSelect(active ? null : period.key, activeSchool)}
                      title={`${periodName(t, period.label)} · ${formatYearRange(t, period.startYear, period.endYear)}`}
                      className={[
                        'mx-auto inline-flex max-h-32 rotate-180 items-center justify-start overflow-hidden rounded-sm px-1 py-1 text-[11px] font-semibold leading-none outline-none [writing-mode:vertical-rl] focus-visible:ring-2 focus-visible:ring-orange-700',
                        active ? 'bg-stone-900 text-[#fffaf1]' : focused ? 'text-orange-800' : 'text-stone-700 hover:text-orange-800',
                      ].join(' ')}
                    >
                      <span className="truncate">{periodName(t, period.label)}</span>
                    </button>
                  </th>
                );
              })}
              <th scope="col" className="px-3 pb-2 text-right align-bottom text-[10px] font-semibold uppercase tracking-[0.16em] text-stone-500">
                {t('chronos.matrix.totalColumn')}
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row, rowIndex) => {
              const name = rowName(row);
              const rowActive = row.key === activeSchoolKey;
              const rowSelected = selectedSchool !== null && row.members.includes(selectedSchool);
              const filter: SchoolFilter = { key: row.key, members: row.members };
              return (
                <tr key={row.key} className={rowSelected ? 'bg-orange-50' : ''}>
                  <th scope="row" className={['sticky left-0 z-10 max-w-[8.5rem] sm:max-w-[11rem] border-t border-stone-200 px-0 text-left font-normal', rowSelected ? 'bg-orange-50' : 'bg-[#fffdf9]'].join(' ')}>
                    <button
                      type="button"
                      onClick={() => onSelect(activePeriodKey, rowActive ? null : filter)}
                      className={[
                        'block min-h-9 w-full truncate px-3 text-left outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-orange-700',
                        row.key === SCHOOL_OTHER || row.key === SCHOOL_NONE ? 'italic text-stone-500' : 'text-stone-800',
                        rowActive ? 'font-bold text-stone-950' : 'font-semibold hover:text-orange-800',
                      ].join(' ')}
                      title={row.key === SCHOOL_OTHER ? row.members.filter(Boolean).join(', ') : name}
                    >
                      {name}
                    </button>
                  </th>
                  {row.cells.map((value, columnIndex) => {
                    const period = columns[columnIndex];
                    const intensity = densityIntensity(value, max);
                    const active = rowActive && period.key === activePeriodKey;
                    const tabbable = rowIndex === focusRow && columnIndex === focusColumn;
                    return (
                      <td key={period.key} className="border-l border-t border-stone-200 p-0">
                        <button
                          type="button"
                          data-cell={`${rowIndex}:${columnIndex}`}
                          tabIndex={tabbable ? 0 : -1}
                          aria-disabled={value === 0 || undefined}
                          onFocus={() => setFocusCell([rowIndex, columnIndex])}
                          onKeyDown={(event) => moveFocus(event, rowIndex, columnIndex)}
                          onClick={() => { if (value > 0) onSelect(active ? null : period.key, active ? null : filter); }}
                          aria-pressed={active}
                          aria-label={t('chronos.matrix.cellLabel', {
                            school: name,
                            period: periodName(t, period.label),
                            count: value,
                            formatted: formatCount(locale, value),
                          })}
                          className={[
                            'flex h-9 w-9 items-center justify-center text-[10px] font-semibold tabular-nums outline-none transition-[filter] focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-orange-700',
                            value === 0 ? 'cursor-default text-stone-300' : 'hover:brightness-110',
                            intensity > 0.62 ? 'text-white' : 'text-teal-950',
                            active ? 'ring-2 ring-inset ring-stone-950' : '',
                          ].join(' ')}
                          style={value > 0 ? { background: cellFill(intensity) } : undefined}
                        >
                          {value > 0 ? compact.format(value) : '·'}
                        </button>
                      </td>
                    );
                  })}
                  <td className="border-l border-t border-stone-200 px-3 text-right font-semibold tabular-nums text-stone-700">
                    {formatCount(locale, row.total)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export const SchoolPeriodMatrix = memo(SchoolPeriodMatrixComponent);
export default SchoolPeriodMatrix;
