import type { TimelineOverview, TimelinePeriodSummary } from '../../types';
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

export function periodBounds(label: string): PeriodBounds {
  return PERIOD_BOUNDS[label] ?? [null, null];
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
  nodes.forEach((node) => {
    if (!periodIntersectsWindow(periodBounds(node.periodLabel), start, end)) return;
    grouped.set(node.periodLabel, [...(grouped.get(node.periodLabel) ?? []), node]);
  });

  const periods: TimelinePeriodSummary[] = [...grouped.entries()]
    .map(([label, periodNodes]) => {
      const [startYear, endYear] = periodBounds(label);
      const counts: Record<string, number> = {};
      periodNodes.forEach((node) => {
        counts[node.typeKey] = (counts[node.typeKey] ?? 0) + 1;
      });
      return {
        key: label.toLowerCase().replace(/\s+/g, '-'),
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
      return byStart || a.label.localeCompare(b.label);
    });

  const byType: Record<string, number> = {};
  nodes.forEach((node) => {
    byType[node.typeKey] = (byType[node.typeKey] ?? 0) + 1;
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
