import {
  memo,
  useCallback,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent,
  type PointerEvent,
} from 'react';
import { useTranslation } from 'react-i18next';

import type { TimelinePeriodSummary } from '../../types';
import { formatCount, formatHistoricalYear, formatYearRange, periodName } from './chronosFormat';
import {
  CHRONOS_TICKS,
  densityIntensity,
  ERA_BANDS,
  eraAtYear,
  fractionToYear,
  isDatedPeriod,
  periodBounds,
  periodIntersectsWindow,
  SCALE_BREAKS,
  snapYear,
  yearToFraction,
} from './chronosTimeline';

export interface PeriodMarkers {
  selected: boolean;
  compare: number;
  thread: ReadonlyArray<number>;
}

export interface ChronosAxisProps {
  periods: ReadonlyArray<TimelinePeriodSummary>;
  loading?: boolean;
  windowStart: number | null;
  windowEnd: number | null;
  onWindowChange: (start: number | null, end: number | null) => void;
  activePeriodKey: string | null;
  onActivatePeriod: (key: string | null) => void;
  markers: ReadonlyMap<string, PeriodMarkers>;
}

/* Shared column template: every row, the era strip and the tick strip align
 * on the same three tracks, so the overlay can sit on the middle one. */
const COLUMNS = 'grid grid-cols-[7.25rem_minmax(0,1fr)_3.25rem] gap-x-3 sm:grid-cols-[12.5rem_minmax(0,1fr)_4.5rem] sm:gap-x-4';

function pct(fraction: number) {
  return `${(fraction * 100).toFixed(3)}%`;
}

function barFill(intensity: number) {
  const weight = Math.round(18 + intensity * 82);
  return `color-mix(in oklab, #9a3412 ${weight}%, #fbe4cf)`;
}

function ChronosAxisComponent({
  periods,
  loading = false,
  windowStart,
  windowEnd,
  onWindowChange,
  activePeriodKey,
  onActivatePeriod,
  markers,
}: ChronosAxisProps) {
  const { t, i18n } = useTranslation();
  const locale = i18n.language || 'en';
  const stripRef = useRef<HTMLDivElement>(null);
  const dragRef = useRef<{ origin: number; moved: boolean } | null>(null);
  const [draft, setDraft] = useState<readonly [number, number] | null>(null);
  const rowRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const [focusIndex, setFocusIndex] = useState(0);

  const dated = useMemo(() => periods.filter(isDatedPeriod), [periods]);
  const undated = useMemo(() => periods.filter((period) => !isDatedPeriod(period)), [periods]);
  const ordered = useMemo(() => [...dated, ...undated], [dated, undated]);
  const maxCount = useMemo(
    () => dated.reduce((best, period) => Math.max(best, period.nodes.length), 0),
    [dated],
  );
  const windowed = windowStart !== null || windowEnd !== null;
  const windowFrom = windowStart === null ? 0 : yearToFraction(windowStart);
  const windowTo = windowEnd === null ? 1 : yearToFraction(windowEnd);
  const shadeFrom = draft ? draft[0] : windowFrom;
  const shadeTo = draft ? draft[1] : windowTo;
  const showShade = draft !== null || windowed;

  const fractionAt = useCallback((clientX: number) => {
    const rect = stripRef.current?.getBoundingClientRect();
    if (!rect || rect.width === 0) return 0;
    return Math.min(1, Math.max(0, (clientX - rect.left) / rect.width));
  }, []);

  const handlePointerDown = (event: PointerEvent<HTMLDivElement>) => {
    if (event.button !== 0) return;
    dragRef.current = { origin: fractionAt(event.clientX), moved: false };
    event.currentTarget.setPointerCapture(event.pointerId);
  };

  const handlePointerMove = (event: PointerEvent<HTMLDivElement>) => {
    const drag = dragRef.current;
    if (!drag) return;
    const current = fractionAt(event.clientX);
    const width = stripRef.current?.getBoundingClientRect().width ?? 1;
    if (!drag.moved && Math.abs(current - drag.origin) * width < 5) return;
    drag.moved = true;
    setDraft([Math.min(drag.origin, current), Math.max(drag.origin, current)]);
  };

  const handlePointerUp = (event: PointerEvent<HTMLDivElement>) => {
    const drag = dragRef.current;
    dragRef.current = null;
    if (!drag) return;
    const current = fractionAt(event.clientX);
    if (drag.moved) {
      const from = snapYear(fractionToYear(Math.min(drag.origin, current)));
      const to = snapYear(fractionToYear(Math.max(drag.origin, current)));
      if (to > from) onWindowChange(from, to);
    } else {
      const era = eraAtYear(fractionToYear(current));
      if (era) onWindowChange(era.start, era.end);
    }
    setDraft(null);
  };

  const handleRowKeyDown = (event: KeyboardEvent<HTMLButtonElement>, index: number) => {
    const last = ordered.length - 1;
    let next: number | null = null;
    if (event.key === 'ArrowDown') next = Math.min(last, index + 1);
    else if (event.key === 'ArrowUp') next = Math.max(0, index - 1);
    else if (event.key === 'Home') next = 0;
    else if (event.key === 'End') next = last;
    else if (event.key === 'Escape' && activePeriodKey) {
      event.preventDefault();
      onActivatePeriod(null);
      return;
    }
    if (next === null) return;
    event.preventDefault();
    setFocusIndex(next);
    rowRefs.current[next]?.focus();
  };

  const draftLabel = draft
    ? t('chronos.year.range', {
      start: formatHistoricalYear(t, snapYear(fractionToYear(draft[0]))),
      end: formatHistoricalYear(t, snapYear(fractionToYear(draft[1]))),
    })
    : null;
  const tabbableIndex = Math.min(focusIndex, Math.max(0, ordered.length - 1));

  return (
    <figure className="min-w-0" aria-busy={loading || undefined}>
      <figcaption className="flex flex-wrap items-end justify-between gap-x-6 gap-y-2 pb-4">
        <div>
          <h2 className="font-display text-[1.9rem] leading-none text-stone-950">{t('chronos.axis.title')}</h2>
          <p className="mt-2 max-w-2xl font-body text-[13px] leading-5 text-stone-600">{t('chronos.axis.caption')}</p>
        </div>
        <div className="flex items-center gap-3 font-body text-[11px] text-stone-600" aria-hidden="true">
          <span>{t('chronos.axis.legendFew')}</span>
          <span className="flex h-2.5 w-24 overflow-hidden rounded-sm">
            {[0, 0.25, 0.5, 0.75, 1].map((step) => (
              <span key={step} className="h-full flex-1" style={{ background: barFill(step) }} />
            ))}
          </span>
          <span>{t('chronos.axis.legendMany')}</span>
        </div>
      </figcaption>

      <div className="relative">
        {/* Era strip: brush target. Pointer-only; keyboard users get the era buttons and year fields. */}
        <div className={`${COLUMNS} items-end`}>
          <p className="pb-1 font-body text-[10px] font-semibold uppercase tracking-[0.18em] text-stone-500">
            {t('chronos.axis.periodColumn')}
          </p>
          <div
            ref={stripRef}
            onPointerDown={handlePointerDown}
            onPointerMove={handlePointerMove}
            onPointerUp={handlePointerUp}
            onPointerCancel={() => { dragRef.current = null; setDraft(null); }}
            title={t('chronos.axis.brushHint')}
            className="relative h-10 cursor-crosshair touch-none select-none border-b border-stone-400"
          >
            {ERA_BANDS.map((era, index) => {
              const left = yearToFraction(era.start);
              const right = yearToFraction(era.end);
              return (
                <span
                  key={era.key}
                  className={[
                    'absolute inset-y-0 flex items-end overflow-hidden px-1.5 pb-1.5 font-body text-[9px] font-bold uppercase tracking-[0.14em] sm:text-[10px]',
                    index % 2 === 0 ? 'bg-stone-900/[0.045] text-stone-600' : 'text-stone-500',
                  ].join(' ')}
                  style={{ left: pct(left), width: pct(right - left) }}
                  title={t(`chronos.eras.${era.key}`)}
                >
                  <span className="truncate max-sm:hidden">{t(`chronos.eras.${era.key}`)}</span>
                </span>
              );
            })}
            {draftLabel && (
              <span
                role="status"
                className="pointer-events-none absolute -top-7 z-20 whitespace-nowrap rounded-sm bg-stone-900 px-2 py-1 font-body text-[11px] font-semibold text-[#fffaf1]"
                style={{ left: pct(draft ? (draft[0] + draft[1]) / 2 : 0), transform: 'translateX(-50%)' }}
              >
                {draftLabel}
              </span>
            )}
          </div>
          <p className="pb-1 text-right font-body text-[10px] font-semibold uppercase tracking-[0.18em] text-stone-500">
            {t('chronos.axis.countColumn')}
          </p>
        </div>

        <div className="relative">
          {/* Overlay aligned on the plot track: era tints, BCE/CE divider, scale breaks, window shade. */}
          <div className={`${COLUMNS} pointer-events-none absolute inset-0`} aria-hidden="true">
            <span />
            <span className="relative">
              {ERA_BANDS.map((era, index) => (
                index % 2 === 0 ? (
                  <span
                    key={era.key}
                    className="absolute inset-y-0 bg-stone-900/[0.045]"
                    style={{ left: pct(yearToFraction(era.start)), width: pct(yearToFraction(era.end) - yearToFraction(era.start)) }}
                  />
                ) : null
              ))}
              <span className="absolute inset-y-0 w-px bg-stone-500/70" style={{ left: pct(yearToFraction(0)) }} />
              {SCALE_BREAKS.map((year) => (
                <span key={year} className="absolute inset-y-0 border-l border-dashed border-stone-400" style={{ left: pct(yearToFraction(year)) }} />
              ))}
              {showShade && (
                <>
                  <span className="absolute inset-y-0 left-0 bg-[#f7f2e9]/75" style={{ width: pct(shadeFrom) }} />
                  <span className="absolute inset-y-0 right-0 bg-[#f7f2e9]/75" style={{ width: pct(1 - shadeTo) }} />
                  <span className="absolute inset-y-0 w-0.5 bg-orange-700" style={{ left: pct(shadeFrom) }} />
                  <span className="absolute inset-y-0 w-0.5 -translate-x-full bg-orange-700" style={{ left: pct(shadeTo) }} />
                </>
              )}
            </span>
            <span />
          </div>

          {loading && periods.length === 0 ? (
            <div role="status" aria-live="polite" className="relative">
              <span className="sr-only">{t('chronos.states.loading')}</span>
              {Array.from({ length: 8 }, (_, index) => (
                <div key={index} className={`${COLUMNS} h-9 items-center border-b border-stone-200`}>
                  <span className="h-2.5 w-24 rounded-sm bg-stone-300/60 motion-safe:animate-pulse" />
                  <span className="relative h-3">
                    <span
                      className="absolute inset-y-0 rounded-sm bg-stone-300/60 motion-safe:animate-pulse"
                      style={{ left: `${8 + index * 9}%`, width: `${12 + (index % 3) * 6}%` }}
                    />
                  </span>
                  <span />
                </div>
              ))}
            </div>
          ) : periods.length === 0 ? (
            <p className="relative py-14 text-center font-reader text-lg text-stone-600">{t('chronos.states.noPeriods')}</p>
          ) : (
            <ul className="relative" aria-label={t('chronos.axis.rowsLabel')}>
              {ordered.map((period, index) => {
                const isDated = isDatedPeriod(period);
                const firstUndated = !isDated && index === dated.length;
                const active = period.key === activePeriodKey;
                const count = period.nodes.length;
                const marks = markers.get(period.label);
                const inWindow = periodIntersectsWindow(periodBounds(period.label), windowStart, windowEnd);
                const left = isDated ? yearToFraction(period.startYear ?? 0) : 0;
                const right = isDated ? yearToFraction(period.endYear ?? 0) : 0;
                const name = periodName(t, period.label);
                const range = formatYearRange(t, period.startYear, period.endYear);
                return (
                  <li key={period.key}>
                    {firstUndated && (
                      <p className={`${COLUMNS} border-b border-stone-300 pb-1.5 pt-5 font-body text-[10px] font-semibold uppercase tracking-[0.18em] text-stone-500`}>
                        <span className="col-span-3">{t('chronos.axis.undatedHeading')}</span>
                      </p>
                    )}
                    <button
                      ref={(element) => { rowRefs.current[index] = element; }}
                      type="button"
                      tabIndex={index === tabbableIndex ? 0 : -1}
                      aria-pressed={active}
                      aria-label={t('chronos.axis.rowLabel', {
                        period: name,
                        range,
                        count,
                        formatted: formatCount(locale, count),
                      })}
                      onFocus={() => setFocusIndex(index)}
                      onKeyDown={(event) => handleRowKeyDown(event, index)}
                      onClick={() => onActivatePeriod(active ? null : period.key)}
                      className={[
                        COLUMNS,
                        'group w-full min-h-9 items-center border-b border-stone-200 text-left outline-none transition-colors focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-orange-700',
                        active ? 'bg-orange-100/70' : 'hover:bg-orange-50/80',
                        inWindow ? '' : 'opacity-45',
                      ].join(' ')}
                    >
                      <span className="flex min-w-0 items-center gap-1.5 py-1.5">
                        <span className={['truncate font-body text-[12px] leading-4 sm:text-[13px]', active ? 'font-bold text-stone-950' : 'font-semibold text-stone-800'].join(' ')}>
                          {name}
                        </span>
                        {marks?.selected && (
                          <span className="h-2 w-2 shrink-0 rounded-full bg-orange-700 ring-2 ring-orange-200" title={t('chronos.axis.markerSelected')} />
                        )}
                        {marks && marks.compare > 0 && (
                          <span className="h-2 w-2 shrink-0 rounded-full border-2 border-teal-700" title={t('chronos.axis.markerCompare', { count: marks.compare })} />
                        )}
                        {marks && marks.thread.length > 0 && (
                          <span className="shrink-0 font-body text-[10px] font-semibold tabular-nums text-teal-800" title={t('chronos.axis.markerThread')}>
                            {marks.thread.map((step) => step + 1).join('·')}
                          </span>
                        )}
                      </span>
                      <span className="relative h-full min-h-9">
                        {isDated ? (
                          <span
                            className="absolute top-1/2 h-3.5 -translate-y-1/2 rounded-[3px] ring-2 ring-[#fffdf9] transition-[filter] group-hover:brightness-95"
                            style={{
                              left: pct(left),
                              width: `max(4px, ${pct(right - left)})`,
                              background: barFill(densityIntensity(count, maxCount)),
                            }}
                          >
                            {active && <span className="absolute inset-0 rounded-[3px] ring-2 ring-stone-900" />}
                          </span>
                        ) : (
                          <span className="absolute inset-y-2 left-0 flex items-center rounded-[3px] bg-[repeating-linear-gradient(135deg,rgba(120,113,108,0.16)_0_4px,transparent_4px_8px)] px-2 font-body text-[10px] italic text-stone-600">
                            {t('chronos.axis.undatedBar')}
                          </span>
                        )}
                      </span>
                      <span className="text-right font-body text-[12px] font-semibold tabular-nums text-stone-800">
                        {formatCount(locale, count)}
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </div>

        <div className={`${COLUMNS} pt-1`} aria-hidden="true">
          <span />
          <div className="relative h-9">
            {CHRONOS_TICKS.map((tick) => (
              <span
                key={tick.year}
                className={[
                  'absolute top-0 flex -translate-x-1/2 flex-col items-center font-body text-[10px] tabular-nums text-stone-500',
                  tick.essential ? '' : 'max-sm:hidden',
                ].join(' ')}
                style={{ left: pct(yearToFraction(tick.year)) }}
              >
                <span className={['w-px bg-stone-400', tick.labelled ? 'h-1.5' : 'h-1'].join(' ')} />
                {tick.labelled && <span className="mt-0.5 whitespace-nowrap">{Math.abs(tick.year)}</span>}
              </span>
            ))}
            <span
              className="absolute top-0 flex -translate-x-1/2 flex-col items-center font-body text-[10px] font-bold text-stone-700"
              style={{ left: pct(yearToFraction(0)) }}
            >
              <span className="h-3 w-px bg-stone-600" />
              <span className="mt-2.5 whitespace-nowrap">{t('chronos.axis.eraDivider')}</span>
            </span>
          </div>
          <span />
        </div>
        <p className="mt-1 font-body text-[11px] leading-4 text-stone-500">
          {t('chronos.axis.scaleNote', {
            from: formatHistoricalYear(t, SCALE_BREAKS[0]),
            to: formatHistoricalYear(t, SCALE_BREAKS[1]),
          })}
        </p>
      </div>
    </figure>
  );
}

export const ChronosAxis = memo(ChronosAxisComponent);
export default ChronosAxis;
