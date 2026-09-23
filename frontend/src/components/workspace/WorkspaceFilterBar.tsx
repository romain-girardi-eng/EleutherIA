import { ChevronDown, SlidersHorizontal, X } from 'lucide-react';
import { memo, useId, useMemo, useState, type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';

import { useGraphWorkspace } from '../../context/GraphWorkspaceContext';
import { TYPE_PALETTE } from '../cosmograph/AtlasHelpers';
import type { KgFilterState } from '../cosmograph/KgFilters';
import {
  activeFilterCount,
  buildSearchIndex,
  computeFacetCounts,
  orderedPeriods,
  orderedSchools,
  searchRows,
  toggleValue,
  type FacetCounts,
  type FacetKey,
} from './scholarModel';
import { useScholarLabels } from './useScholarLabels';

const SCHOOLS_COLLAPSED = 8;

interface WorkspaceFilterBarProps {
  /** Counts over the current search result; computed from the whole release when omitted. */
  facetCounts?: FacetCounts;
  className?: string;
}

function useReleaseFacetCounts(filters: KgFilterState, provided?: FacetCounts): FacetCounts {
  const { data } = useGraphWorkspace();
  return useMemo(() => {
    if (provided) return provided;
    return computeFacetCounts(searchRows(buildSearchIndex(data.meta), ''), filters);
  }, [data.meta, filters, provided]);
}

function WorkspaceFilterBarComponent({ facetCounts, className = '' }: WorkspaceFilterBarProps) {
  const { t } = useTranslation();
  const labels = useScholarLabels();
  const { state, setFilters } = useGraphWorkspace();
  const { filters } = state;
  const counts = useReleaseFacetCounts(filters, facetCounts);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [allSchools, setAllSchools] = useState(false);
  const panelId = useId();
  const active = activeFilterCount(filters);

  const periods = useMemo(() => orderedPeriods(counts.periods, filters.periods), [counts.periods, filters.periods]);
  const schools = useMemo(() => orderedSchools(counts.schools, filters.schools), [counts.schools, filters.schools]);
  const visibleSchools = allSchools
    ? schools
    : schools.filter((school, index) => index < SCHOOLS_COLLAPSED || filters.schools.includes(school));
  const hiddenSchools = schools.length - visibleSchools.length;

  const toggle = (key: FacetKey, value: string) =>
    setFilters({ ...filters, [key]: toggleValue(filters[key], value) });
  const clearAll = () => setFilters({ periods: [], types: [], schools: [] });

  const activeChips: Array<{ key: FacetKey; value: string; label: string }> = [
    ...filters.types.map((value) => ({ key: 'types' as const, value, label: labels.type(value) })),
    ...filters.periods.map((value) => ({ key: 'periods' as const, value, label: labels.period(value) })),
    ...filters.schools.map((value) => ({ key: 'schools' as const, value, label: labels.school(value) })),
  ];

  return (
    <section aria-label={t('scholar.filters.title')} className={`font-body text-stone-700 ${className}`}>
      <div className="flex items-center justify-between gap-3">
        <button
          type="button"
          aria-expanded={mobileOpen}
          aria-controls={panelId}
          onClick={() => setMobileOpen((open) => !open)}
          className="inline-flex min-h-11 items-center gap-2 text-sm font-semibold text-stone-900 outline-none focus-visible:ring-2 focus-visible:ring-orange-700 xl:pointer-events-none xl:min-h-0"
        >
          <SlidersHorizontal className="h-4 w-4 text-orange-800" aria-hidden="true" />
          <span className="text-[10px] uppercase tracking-[0.2em] text-stone-600 xl:text-stone-500">
            {t('scholar.filters.title')}
          </span>
          {active > 0 && (
            <span className="rounded-full bg-orange-800 px-1.5 py-px text-[10px] font-bold tabular-nums text-[#fffdf9]">
              {labels.number(active)}
            </span>
          )}
          <ChevronDown
            className={`h-4 w-4 text-stone-500 transition-transform xl:hidden ${mobileOpen ? 'rotate-180' : ''}`}
            aria-hidden="true"
          />
        </button>
        {active > 0 && (
          <button
            type="button"
            onClick={clearAll}
            className="inline-flex min-h-11 items-center px-1 text-xs font-semibold text-orange-800 underline decoration-orange-300 underline-offset-4 outline-none hover:decoration-orange-800 focus-visible:ring-2 focus-visible:ring-orange-700 xl:min-h-8"
          >
            {t('scholar.filters.clearAll', { count: active })}
          </button>
        )}
      </div>

      {activeChips.length > 0 && (
        <ul className="mt-2 flex flex-wrap gap-1.5" aria-label={t('scholar.filters.active')}>
          {activeChips.map((chip) => (
            <li key={`${chip.key}:${chip.value}`}>
              <button
                type="button"
                onClick={() => toggle(chip.key, chip.value)}
                aria-label={t('scholar.filters.remove', { label: chip.label })}
                className="inline-flex min-h-11 [@media(pointer:fine)]:min-h-9 items-center gap-1 border border-orange-700 bg-orange-50 py-1 pl-2.5 pr-1.5 text-xs font-medium text-orange-900 outline-none hover:bg-orange-100 focus-visible:ring-2 focus-visible:ring-orange-700"
              >
                {chip.label}
                <X className="h-3.5 w-3.5" aria-hidden="true" />
              </button>
            </li>
          ))}
        </ul>
      )}

      <div id={panelId} className={`${mobileOpen ? 'block' : 'hidden'} mt-4 space-y-5 xl:block`}>
        <FacetGroup label={t('scholar.filters.type')}>
          {TYPE_PALETTE.map((entry) => (
            <FacetChip
              key={entry.key}
              label={labels.type(entry.key, entry.label)}
              count={counts.types.get(entry.key) ?? 0}
              active={filters.types.includes(entry.key)}
              swatch={entry.color}
              format={labels.number}
              onToggle={() => toggle('types', entry.key)}
            />
          ))}
        </FacetGroup>

        <FacetGroup label={t('scholar.filters.period')}>
          {periods.map((period) => (
            <FacetChip
              key={period}
              label={labels.period(period)}
              count={counts.periods.get(period) ?? 0}
              active={filters.periods.includes(period)}
              format={labels.number}
              onToggle={() => toggle('periods', period)}
            />
          ))}
        </FacetGroup>

        <FacetGroup label={t('scholar.filters.school')}>
          {visibleSchools.map((school) => (
            <FacetChip
              key={school}
              label={labels.school(school)}
              count={counts.schools.get(school) ?? 0}
              active={filters.schools.includes(school)}
              format={labels.number}
              onToggle={() => toggle('schools', school)}
            />
          ))}
          {(hiddenSchools > 0 || allSchools) && schools.length > SCHOOLS_COLLAPSED && (
            <li>
              <button
                type="button"
                aria-expanded={allSchools}
                onClick={() => setAllSchools((open) => !open)}
                className="inline-flex min-h-11 [@media(pointer:fine)]:min-h-9 items-center px-2 text-xs font-semibold text-teal-800 underline decoration-teal-300 underline-offset-4 outline-none hover:decoration-teal-800 focus-visible:ring-2 focus-visible:ring-teal-700"
              >
                {allSchools
                  ? t('scholar.filters.fewerSchools')
                  : t('scholar.filters.moreSchools', { count: hiddenSchools })}
              </button>
            </li>
          )}
        </FacetGroup>
      </div>
    </section>
  );
}

function FacetGroup({ label, children }: { label: string; children: ReactNode }) {
  const id = useId();
  return (
    <div role="group" aria-labelledby={id}>
      <h3 id={id} className="mb-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-stone-500">
        {label}
      </h3>
      <ul className="flex flex-wrap gap-1.5">{children}</ul>
    </div>
  );
}

function FacetChip({
  label,
  count,
  active,
  swatch,
  format,
  onToggle,
}: {
  label: string;
  count: number;
  active: boolean;
  swatch?: string;
  format: (value: number) => string;
  onToggle: () => void;
}) {
  const empty = count === 0 && !active;
  return (
    <li>
      <button
        type="button"
        aria-pressed={active}
        onClick={onToggle}
        className={[
          'inline-flex min-h-11 [@media(pointer:fine)]:min-h-9 items-center gap-1.5 border px-2.5 py-1 text-xs outline-none transition-colors focus-visible:ring-2 focus-visible:ring-orange-700',
          active
            ? 'border-orange-800 bg-orange-800 text-[#fffdf9]'
            : 'border-stone-300 bg-[#fffdf9] text-stone-700 hover:border-orange-600 hover:text-stone-950',
          empty ? 'opacity-45' : '',
        ].join(' ')}
      >
        {swatch && (
          <span
            aria-hidden="true"
            className="h-2 w-2 shrink-0 rounded-full ring-1 ring-black/10"
            style={{ backgroundColor: swatch }}
          />
        )}
        <span>{label}</span>
        <span className={`tabular-nums text-[11px] ${active ? 'text-orange-100' : 'text-stone-500'}`}>
          {format(count)}
        </span>
      </button>
    </li>
  );
}

export const WorkspaceFilterBar = memo(WorkspaceFilterBarComponent);
export default WorkspaceFilterBar;
