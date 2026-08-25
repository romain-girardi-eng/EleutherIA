import { useMemo } from 'react';
import { PERIOD_ORDER, SCHOOL_ORDER, TYPE_PALETTE, type AtlasNodeMeta } from './AtlasHelpers';

export interface KgFilterState {
  periods: ReadonlyArray<string>;
  types: ReadonlyArray<string>;
  schools: ReadonlyArray<string>;
}

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

function toggle(list: ReadonlyArray<string>, value: string): string[] {
  return list.includes(value) ? list.filter((item) => item !== value) : [...list, value];
}

export default function KgFilters({ state, nodes, onChange, labels }: KgFiltersProps) {
  const periodCounts = useMemo(() => {
    const counts = new Map<string, number>();
    nodes.forEach((node) => counts.set(node.periodLabel, (counts.get(node.periodLabel) ?? 0) + 1));
    return counts;
  }, [nodes]);

  const schoolCounts = useMemo(() => {
    const counts = new Map<string, number>();
    nodes.forEach((node) => {
      if (node.schoolLabel === 'Unattached') return;
      counts.set(node.schoolLabel, (counts.get(node.schoolLabel) ?? 0) + 1);
    });
    return counts;
  }, [nodes]);

  const typeCounts = useMemo(() => {
    const counts = new Map<string, number>();
    nodes.forEach((node) => counts.set(node.typeKey, (counts.get(node.typeKey) ?? 0) + 1));
    return counts;
  }, [nodes]);

  const orderedPeriods = useMemo(() => {
    const known = PERIOD_ORDER.filter((p) => periodCounts.has(p));
    const extra = [...periodCounts.keys()].filter((p) => !PERIOD_ORDER.includes(p)).sort();
    return [...known, ...extra];
  }, [periodCounts]);

  const orderedSchools = useMemo(() => {
    const known = SCHOOL_ORDER.filter((s) => schoolCounts.has(s));
    const extra = [...schoolCounts.keys()]
      .filter((s) => !SCHOOL_ORDER.includes(s))
      .sort((a, b) => (schoolCounts.get(b) ?? 0) - (schoolCounts.get(a) ?? 0))
      .slice(0, 6);
    return [...known, ...extra];
  }, [schoolCounts]);

  const hasFilters =
    state.periods.length + state.types.length + state.schools.length > 0;

  return (
    <div className="flex flex-col gap-2 rounded-2xl border border-stone-300 bg-[#fffdf9]/92 p-3 text-stone-700 shadow-[0_12px_36px_rgba(72,52,36,0.10)] backdrop-blur-xl">
      <FilterRow label={labels.type}>
        {TYPE_PALETTE.map((entry) => {
          const isActive = state.types.includes(entry.key);
          const count = typeCounts.get(entry.key) ?? 0;
          if (count === 0 && entry.key !== 'scholar') return null;
          return (
            <Chip
              key={entry.key}
              label={entry.label}
              active={isActive}
              count={count}
              swatch={entry.color}
              onClick={() => onChange({ ...state, types: toggle(state.types, entry.key) })}
            />
          );
        })}
      </FilterRow>

      <FilterRow label={labels.period}>
        {orderedPeriods.map((period) => {
          const isActive = state.periods.includes(period);
          return (
            <Chip
              key={period}
              label={period}
              active={isActive}
              count={periodCounts.get(period) ?? 0}
              onClick={() => onChange({ ...state, periods: toggle(state.periods, period) })}
            />
          );
        })}
      </FilterRow>

      <FilterRow label={labels.school}>
        {orderedSchools.map((school) => {
          const isActive = state.schools.includes(school);
          return (
            <Chip
              key={school}
              label={school}
              active={isActive}
              count={schoolCounts.get(school) ?? 0}
              onClick={() => onChange({ ...state, schools: toggle(state.schools, school) })}
            />
          );
        })}
      </FilterRow>

      {hasFilters && (
        <button
          type="button"
          onClick={() => onChange({ periods: [], types: [], schools: [] })}
          className="self-end rounded-full border border-stone-300 bg-white/70 px-3 py-1 text-[11px] text-stone-600 transition-colors hover:border-orange-500 hover:text-orange-800"
        >
          {labels.clear}
        </button>
      )}
    </div>
  );
}

function FilterRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-start gap-3">
      <span className="mt-1.5 w-16 shrink-0 text-[10px] font-semibold uppercase tracking-[0.16em] text-stone-500">
        {label}
      </span>
      <div className="flex flex-1 flex-wrap gap-1.5">{children}</div>
    </div>
  );
}

function Chip({
  label,
  active,
  count,
  swatch,
  onClick,
}: {
  label: string;
  active: boolean;
  count: number;
  swatch?: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={[
        'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] transition-colors',
        active
          ? 'border-orange-700 bg-orange-50 text-orange-900'
          : 'border-stone-300 bg-white/70 text-stone-600 hover:border-orange-400 hover:text-stone-900',
      ].join(' ')}
      aria-pressed={active}
    >
      {swatch && (
        <span
          aria-hidden
          className="h-2 w-2 rounded-full"
          style={{ backgroundColor: swatch }}
        />
      )}
      <span>{label}</span>
      <span className="text-[10px] text-stone-500">{count.toLocaleString()}</span>
    </button>
  );
}
