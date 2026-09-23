import type { TimelineNodeSummary, TimelineOverview, TimelinePeriodSummary } from '../../types';
import type { AtlasNodeMeta } from '../cosmograph/AtlasHelpers';

export type PeriodBounds = readonly [number | null, number | null];

/** Editorial period bands used only for grouping and range filtering.
 * They are never copied into a node as if they were that entity's date. */
export const PERIOD_BOUNDS: Readonly<Record<string, PeriodBounds>> = {
  'First Temple / Pre-exilic Judaism': [-1000, -586],
  Presocratic: [-650, -450],
  'Classical Greek': [-450, -323],
  'Second Temple Judaism': [-516, 70],
  Hellenistic: [-323, -31],
  'Hellenistic Greek': [-323, -31],
  'Roman Republican': [-146, -27],
  'Roman Imperial': [-27, 300],
  Rabbinic: [70, 600],
  Patristic: [150, 450],
  'Late Antiquity': [300, 650],
  Medieval: [500, 1500],
  'Early Modern': [1500, 1800],
  Modern: [1800, 1950],
  Contemporary: [1950, 2030],
  'Cross-period': [null, null],
  Unspecified: [null, null],
};

/** i18n key suffixes (`chronos.periods.*`) for the editorial period labels. */
export const PERIOD_I18N_KEYS: Readonly<Record<string, string>> = {
  'First Temple / Pre-exilic Judaism': 'firstTemple',
  Presocratic: 'presocratic',
  'Classical Greek': 'classicalGreek',
  'Second Temple Judaism': 'secondTemple',
  Hellenistic: 'hellenistic',
  'Hellenistic Greek': 'hellenisticGreek',
  'Roman Republican': 'romanRepublican',
  'Roman Imperial': 'romanImperial',
  Rabbinic: 'rabbinic',
  Patristic: 'patristic',
  'Late Antiquity': 'lateAntiquity',
  Medieval: 'medieval',
  'Early Modern': 'earlyModern',
  Modern: 'modern',
  Contemporary: 'contemporary',
  'Cross-period': 'crossPeriod',
  Unspecified: 'unspecified',
};

export function periodBounds(label: string): PeriodBounds {
  return PERIOD_BOUNDS[label] ?? [null, null];
}

export function isDatedPeriod(period: Pick<TimelinePeriodSummary, 'startYear' | 'endYear'>): boolean {
  return typeof period.startYear === 'number' && typeof period.endYear === 'number';
}

export function periodKey(label: string): string {
  return label.toLowerCase().replace(/\s+/g, '-');
}

export function periodIntersectsWindow(
  bounds: PeriodBounds,
  start: number | null,
  end: number | null,
): boolean {
  const [periodStart, periodEnd] = bounds;
  if (start === null && end === null) return true;
  // Unknown or cross-period dates must not be guessed into a filtered range.
  if (periodStart === null || periodEnd === null) return false;
  if (start !== null && periodEnd < start) return false;
  if (end !== null && periodStart > end) return false;
  return true;
}

export function timelineFromGraph(
  nodes: ReadonlyArray<AtlasNodeMeta>,
  edgeCount: number,
  start: number | null,
  end: number | null,
): TimelineOverview {
  const grouped = new Map<string, AtlasNodeMeta[]>();
  const byType: Record<string, number> = {};
  nodes.forEach((node) => {
    byType[node.typeKey] = (byType[node.typeKey] ?? 0) + 1;
    if (!periodIntersectsWindow(periodBounds(node.periodLabel), start, end)) return;
    const bucket = grouped.get(node.periodLabel);
    if (bucket) bucket.push(node);
    else grouped.set(node.periodLabel, [node]);
  });

  const periods: TimelinePeriodSummary[] = [...grouped.entries()]
    .map(([label, periodNodes]) => {
      const [startYear, endYear] = periodBounds(label);
      const counts: Record<string, number> = {};
      periodNodes.forEach((node) => {
        counts[node.typeKey] = (counts[node.typeKey] ?? 0) + 1;
      });
      return {
        key: periodKey(label),
        label,
        startYear,
        endYear,
        counts,
        nodes: periodNodes.map((node) => ({
          id: node.id,
          label: node.label,
          type: node.typeKey,
          period: node.periodLabel,
          school: node.schoolLabel === 'Unattached' ? null : node.schoolLabel,
          // A period band is not evidence for an entity's composition, life,
          // publication, or attestation date. Exact node dates remain null
          // until a source-backed temporal field enters the compact contract.
          startYear: null,
          endYear: null,
          relationCount: node.degree,
        })),
      };
    })
    .sort((a, b) => {
      const byStart = (a.startYear ?? Number.POSITIVE_INFINITY)
        - (b.startYear ?? Number.POSITIVE_INFINITY);
      const byEnd = (a.endYear ?? Number.POSITIVE_INFINITY)
        - (b.endYear ?? Number.POSITIVE_INFINITY);
      return byStart || byEnd || a.label.localeCompare(b.label);
    });

  const knownStarts = periods
    .map((period) => period.startYear)
    .filter((value): value is number => typeof value === 'number');
  const knownEnds = periods
    .map((period) => period.endYear)
    .filter((value): value is number => typeof value === 'number');

  return {
    periods,
    totals: { nodes: nodes.length, edges: edgeCount, byType },
    range: {
      minYear: knownStarts.length > 0 ? Math.min(...knownStarts) : null,
      maxYear: knownEnds.length > 0 ? Math.max(...knownEnds) : null,
    },
  };
}

/* ---------------------------------------------------------------------------
 * Time scale
 * Ten centuries of antiquity hold ~98 % of the corpus while the reception
 * layer spans fourteen more. A single linear scale would crush the ancient
 * debate into a sliver, so the axis is piecewise-linear with explicit breaks.
 * ------------------------------------------------------------------------- */

export interface ScaleSegment {
  readonly from: number;
  readonly to: number;
  readonly share: number;
}

export const CHRONOS_SCALE: ReadonlyArray<ScaleSegment> = [
  { from: -1000, to: -650, share: 0.05 },
  { from: -650, to: 650, share: 0.73 },
  { from: 650, to: 2030, share: 0.22 },
];

export const SCALE_MIN_YEAR = CHRONOS_SCALE[0].from;
export const SCALE_MAX_YEAR = CHRONOS_SCALE[CHRONOS_SCALE.length - 1].to;

/** Year where the scale changes slope; shown as a visible break on the axis. */
export const SCALE_BREAKS: ReadonlyArray<number> = CHRONOS_SCALE.slice(1).map((segment) => segment.from);

export function yearToFraction(year: number): number {
  const clamped = Math.min(SCALE_MAX_YEAR, Math.max(SCALE_MIN_YEAR, year));
  let offset = 0;
  for (const segment of CHRONOS_SCALE) {
    if (clamped <= segment.to) {
      return offset + ((clamped - segment.from) / (segment.to - segment.from)) * segment.share;
    }
    offset += segment.share;
  }
  return 1;
}

export function fractionToYear(fraction: number): number {
  const clamped = Math.min(1, Math.max(0, fraction));
  let offset = 0;
  for (const segment of CHRONOS_SCALE) {
    if (clamped <= offset + segment.share) {
      return segment.from + ((clamped - offset) / segment.share) * (segment.to - segment.from);
    }
    offset += segment.share;
  }
  return SCALE_MAX_YEAR;
}

/** Round a brushed year to a grain that matches the local scale density. */
export function snapYear(year: number): number {
  const grain = year > -650 && year < 650 ? 10 : 50;
  return Math.round(year / grain) * grain;
}

export interface AxisTick {
  readonly year: number;
  /** Labelled ticks carry a number; the others are bare marks. */
  readonly labelled: boolean;
  /** Kept on narrow screens. */
  readonly essential: boolean;
}

/* Labels are bare magnitudes: the BCE/CE divider under year 0 carries the
 * era, which keeps 200-year labels legible where the ancient span is dense. */
export const CHRONOS_TICKS: ReadonlyArray<AxisTick> = [
  { year: -800, labelled: false, essential: false },
  { year: -600, labelled: true, essential: false },
  { year: -500, labelled: false, essential: false },
  { year: -400, labelled: true, essential: true },
  { year: -300, labelled: false, essential: false },
  { year: -200, labelled: true, essential: false },
  { year: -100, labelled: false, essential: false },
  { year: 100, labelled: false, essential: false },
  { year: 200, labelled: true, essential: false },
  { year: 300, labelled: false, essential: false },
  { year: 400, labelled: true, essential: true },
  { year: 500, labelled: false, essential: false },
  { year: 600, labelled: true, essential: false },
  { year: 1000, labelled: true, essential: false },
  { year: 1500, labelled: true, essential: true },
  { year: 2000, labelled: true, essential: false },
];

/** Broad historiographical eras drawn behind the period rows. */
export interface EraBand {
  readonly key: 'presocratic' | 'classical' | 'hellenistic' | 'romanImperial' | 'lateAntiquity' | 'reception';
  readonly start: number;
  readonly end: number;
}

export const ERA_BANDS: ReadonlyArray<EraBand> = [
  { key: 'presocratic', start: -650, end: -450 },
  { key: 'classical', start: -450, end: -323 },
  { key: 'hellenistic', start: -323, end: -31 },
  { key: 'romanImperial', start: -31, end: 300 },
  { key: 'lateAntiquity', start: 300, end: 650 },
  { key: 'reception', start: 650, end: 2030 },
];

export function eraAtYear(year: number): EraBand | null {
  return ERA_BANDS.find((era) => year >= era.start && year < era.end) ?? null;
}

/** Log intensity so the 13-node Presocratic row is still visible next to
 * the 14 000-node Roman Imperial row. Returns 0..1. */
export function densityIntensity(count: number, max: number): number {
  if (count <= 0 || max <= 0) return 0;
  return Math.log1p(count) / Math.log1p(max);
}

/* ---------------------------------------------------------------------------
 * School × period matrix
 * ------------------------------------------------------------------------- */

export const SCHOOL_NONE = '__none__';
export const SCHOOL_OTHER = '__other__';

export interface SchoolFilter {
  readonly key: string;
  /** Concrete school labels covered by the key; `null` stands for "no school recorded". */
  readonly members: ReadonlyArray<string | null>;
}

export interface SchoolMatrixRow {
  readonly key: string;
  readonly label: string | null;
  readonly total: number;
  readonly cells: ReadonlyArray<number>;
  readonly members: ReadonlyArray<string | null>;
}

export interface SchoolMatrix {
  readonly columns: ReadonlyArray<TimelinePeriodSummary>;
  readonly rows: ReadonlyArray<SchoolMatrixRow>;
  readonly max: number;
}

export function buildSchoolMatrix(timeline: TimelineOverview, maxSchools = 12): SchoolMatrix {
  const columns = timeline.periods;
  const perSchool = new Map<string | null, number[]>();
  columns.forEach((period, columnIndex) => {
    period.nodes.forEach((node) => {
      const school = node.school ?? null;
      let cells = perSchool.get(school);
      if (!cells) {
        cells = new Array<number>(columns.length).fill(0);
        perSchool.set(school, cells);
      }
      cells[columnIndex] += 1;
    });
  });

  const named = [...perSchool.entries()]
    .filter((entry): entry is [string, number[]] => entry[0] !== null)
    .map(([school, cells]) => ({ school, cells, total: cells.reduce((sum, value) => sum + value, 0) }))
    .sort((a, b) => b.total - a.total || a.school.localeCompare(b.school));

  const kept = named.slice(0, maxSchools);
  const folded = named.slice(maxSchools);
  const rows: SchoolMatrixRow[] = kept.map(({ school, cells, total }) => ({
    key: school,
    label: school,
    total,
    cells,
    members: [school],
  }));

  if (folded.length > 0) {
    const cells = new Array<number>(columns.length).fill(0);
    folded.forEach((entry) => entry.cells.forEach((value, index) => { cells[index] += value; }));
    rows.push({
      key: SCHOOL_OTHER,
      label: null,
      total: cells.reduce((sum, value) => sum + value, 0),
      cells,
      members: folded.map((entry) => entry.school),
    });
  }

  const unattached = perSchool.get(null);
  if (unattached) {
    rows.push({
      key: SCHOOL_NONE,
      label: null,
      total: unattached.reduce((sum, value) => sum + value, 0),
      cells: unattached,
      members: [null],
    });
  }

  const max = rows.reduce((best, row) => Math.max(best, ...row.cells), 0);
  return { columns, rows, max };
}

export function nodeMatchesSchool(node: TimelineNodeSummary, filter: SchoolFilter | null): boolean {
  if (!filter) return true;
  return filter.members.includes(node.school ?? null);
}
