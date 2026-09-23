import { X } from 'lucide-react';
import { useId, useMemo, useState, type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import { TYPE_PALETTE, type AtlasNodeMeta } from './AtlasHelpers';
import { ATLAS_THEME } from './atlasTheme';
import { useGraphVocabulary } from './graphVocabulary';
import { facetCounts, PERIOD_CHRONOLOGY, toggle, type Facet, type KgFilterState } from './filterFacets';

export type { KgFilterState };

interface KgFiltersProps {
  state: KgFilterState;
  nodes: ReadonlyArray<AtlasNodeMeta>;
  onChange: (next: KgFilterState) => void;
  labels: {
    period: string;
    type: string;
    school: string;
    clear: string;
  };
}

const PREVIEW = 8;

const TYPE_ORDER = TYPE_PALETTE.map((entry) => entry.key);

export default function KgFilters({ state, nodes, onChange, labels }: KgFiltersProps) {
  const { t } = useTranslation();
  const vocabulary = useGraphVocabulary();
  const [showAllSchools, setShowAllSchools] = useState(false);
  const [showAllTypes, setShowAllTypes] = useState(false);

  const counts = useMemo(() => facetCounts(nodes, state), [nodes, state]);
  // Chip sets are derived from the unfiltered graph so they never jump
  // around while filters change; only their counts move.
  const universe = useMemo(() => facetCounts(nodes, { periods: [], types: [], schools: [] }), [nodes]);

  const typeKeys = useMemo(() => {
    const present = [...universe.types.keys()];
    return present.sort((a, b) => {
      const ia = TYPE_ORDER.indexOf(a);
      const ib = TYPE_ORDER.indexOf(b);
      if (ia >= 0 || ib >= 0) return (ia < 0 ? 99 : ia) - (ib < 0 ? 99 : ib);
      return (universe.types.get(b) ?? 0) - (universe.types.get(a) ?? 0);
    });
  }, [universe]);

  const periodKeys = useMemo(() => {
    const present = [...universe.periods.keys()];
    const rank = (p: string) => {
      const i = PERIOD_CHRONOLOGY.indexOf(p);
      return i < 0 ? PERIOD_CHRONOLOGY.length - 2 : i;
    };
    return present.sort((a, b) => rank(a) - rank(b) || a.localeCompare(b));
  }, [universe]);

  const schoolKeys = useMemo(
    () => [...universe.schools.keys()].sort(
      (a, b) => (universe.schools.get(b) ?? 0) - (universe.schools.get(a) ?? 0),
    ),
    [universe],
  );
  const visibleSchools = showAllSchools
    ? schoolKeys
    : schoolKeys.filter((s, i) => i < PREVIEW || state.schools.includes(s));
  const visibleTypes = showAllTypes
    ? typeKeys
    : typeKeys.filter((key, i) => i < PREVIEW || state.types.includes(key));

  const typeName = (key: string) =>
    key === 'scholar'
      ? t('cosmograph.filters.modernLayer', 'Modern reception')
      : vocabulary.group(key);

  const active: ReadonlyArray<{ facet: Facet; value: string; label: string }> = [
    ...state.types.map((value) => ({ facet: 'types' as const, value, label: typeName(value) })),
    ...state.periods.map((value) => ({ facet: 'periods' as const, value, label: vocabulary.period(value) })),
    ...state.schools.map((value) => ({ facet: 'schools' as const, value, label: vocabulary.school(value) })),
  ];

  const swatchFor = (key: string) =>
    TYPE_PALETTE.find((entry) => entry.key === key)?.color ?? ATLAS_THEME.nodes.fallback;

  return (
    <div className="flex flex-col gap-4 font-body text-stone-700">
      <div
        className="flex flex-wrap items-center gap-x-3 gap-y-2 border-b border-stone-200 pb-3"
      >
        <p className="text-[13px] text-stone-600" aria-live="polite">
          {t('cosmograph.filters.visible', {
            count: counts.visible,
            visible: vocabulary.count(counts.visible),
            total: vocabulary.count(nodes.length),
            defaultValue: '{{visible}} of {{total}} nodes shown',
          })}
        </p>
        {active.length > 0 && (
          <button
            type="button"
            onClick={() => onChange({ periods: [], types: [], schools: [] })}
            className="ml-auto inline-flex min-h-8 items-center text-[12px] font-semibold text-orange-800 underline decoration-orange-800/30 underline-offset-2 hover:decoration-orange-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-700 [@media(pointer:coarse)]:min-h-11"
          >
            {labels.clear}
          </button>
        )}
        {active.length > 0 && (
          <ul
            aria-label={t('cosmograph.filters.active', 'Active filters')}
            className="flex w-full flex-wrap gap-1.5"
          >
            {active.map((item) => (
              <li key={`${item.facet}:${item.value}`}>
                <button
                  type="button"
                  onClick={() => onChange({ ...state, [item.facet]: toggle(state[item.facet], item.value) })}
                  aria-label={t('cosmograph.filters.remove', { label: item.label, defaultValue: 'Remove filter: {{label}}' })}
                  className="inline-flex min-h-8 items-center gap-1.5 rounded-full bg-stone-900 py-1 pl-3 pr-2 text-[12px] text-[#fffdf9] transition-colors hover:bg-orange-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-700 focus-visible:ring-offset-1 [@media(pointer:coarse)]:min-h-11"
                >
                  {item.label}
                  <X className="h-3.5 w-3.5" aria-hidden />
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <FilterGroup
        legend={labels.type}
        footer={typeKeys.length > PREVIEW ? (
          <MoreToggle expanded={showAllTypes} total={typeKeys.length} onToggle={() => setShowAllTypes((v) => !v)} />
        ) : null}
      >
        {visibleTypes.map((key) => (
          <Chip
            key={key}
            label={typeName(key)}
            active={state.types.includes(key)}
            count={counts.types.get(key) ?? 0}
            formatted={vocabulary.count(counts.types.get(key) ?? 0)}
            swatch={swatchFor(key)}
            onClick={() => onChange({ ...state, types: toggle(state.types, key) })}
          />
        ))}
      </FilterGroup>

      <FilterGroup legend={labels.period}>
        {periodKeys.map((period) => (
          <Chip
            key={period}
            label={vocabulary.period(period)}
            active={state.periods.includes(period)}
            count={counts.periods.get(period) ?? 0}
            formatted={vocabulary.count(counts.periods.get(period) ?? 0)}
            onClick={() => onChange({ ...state, periods: toggle(state.periods, period) })}
          />
        ))}
      </FilterGroup>

      <FilterGroup
        legend={labels.school}
        footer={schoolKeys.length > PREVIEW ? (
          <MoreToggle expanded={showAllSchools} total={schoolKeys.length} onToggle={() => setShowAllSchools((v) => !v)} />
        ) : null}
      >
        {visibleSchools.map((school) => (
          <Chip
            key={school}
            label={vocabulary.school(school)}
            active={state.schools.includes(school)}
            count={counts.schools.get(school) ?? 0}
            formatted={vocabulary.count(counts.schools.get(school) ?? 0)}
            onClick={() => onChange({ ...state, schools: toggle(state.schools, school) })}
          />
        ))}
      </FilterGroup>
    </div>
  );
}

function MoreToggle({ expanded, total, onToggle }: { expanded: boolean; total: number; onToggle: () => void }) {
  const { t } = useTranslation();
  return (
    <button
      type="button"
      onClick={onToggle}
      aria-expanded={expanded}
      className="mt-2 inline-flex min-h-8 items-center text-[12px] font-semibold text-teal-800 underline decoration-teal-700/30 underline-offset-2 hover:decoration-teal-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-700 [@media(pointer:coarse)]:min-h-11"
    >
      {expanded
        ? t('cosmograph.filters.showFewer', 'Show fewer')
        : t('cosmograph.filters.showAll', { count: total, defaultValue: 'Show all {{count}}' })}
    </button>
  );
}

function FilterGroup({
  legend,
  children,
  footer,
}: {
  legend: string;
  children: ReactNode;
  footer?: ReactNode;
}) {
  const id = useId();
  return (
    <div role="group" aria-labelledby={id}>
      <h3 id={id} className="mb-2 font-display text-[15px] leading-none text-stone-900">
        {legend}
      </h3>
      <div className="flex flex-wrap gap-1.5">{children}</div>
      {footer}
    </div>
  );
}

function Chip({
  label,
  active,
  count,
  formatted,
  swatch,
  onClick,
}: {
  label: string;
  active: boolean;
  count: number;
  formatted: string;
  swatch?: string;
  onClick: () => void;
}) {
  const empty = count === 0 && !active;
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={empty}
      aria-pressed={active}
      className={[
        'inline-flex min-h-8 items-center gap-1.5 rounded-full border px-3 py-1 text-[12px] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-700 focus-visible:ring-offset-1 [@media(pointer:coarse)]:min-h-11',
        active
          ? 'border-orange-800 bg-orange-50 text-orange-950 shadow-[inset_0_0_0_1px_rgba(154,52,18,0.5)]'
          : 'border-stone-300 bg-white text-stone-700 hover:border-stone-500 hover:text-stone-950',
        empty ? 'cursor-not-allowed opacity-45 hover:border-stone-300 hover:text-stone-700' : '',
      ].join(' ')}
    >
      {swatch && (
        <span aria-hidden className="h-2.5 w-2.5 rounded-full ring-1 ring-stone-900/10" style={{ backgroundColor: swatch }} />
      )}
      <span>{label}</span>
      <span className={['tabular-nums', active ? 'text-orange-900/80' : 'text-stone-500'].join(' ')}>
        {formatted}
      </span>
    </button>
  );
}
