import type { AtlasNodeMeta } from './AtlasHelpers';

export interface KgFilterState {
  periods: ReadonlyArray<string>;
  types: ReadonlyArray<string>;
  schools: ReadonlyArray<string>;
}

export type Facet = keyof KgFilterState;

/** Chronological order of the period labels the release actually uses. */
export const PERIOD_CHRONOLOGY: ReadonlyArray<string> = [
  'First Temple / Pre-exilic Judaism',
  'Presocratic',
  'Classical Greek',
  'Hellenistic',
  'Hellenistic Greek',
  'Second Temple Judaism',
  'Roman Republican',
  'Roman Imperial',
  'Patristic',
  'Rabbinic',
  'Late Antiquity',
  'Medieval',
  'Early Modern',
  'Modern',
  'Contemporary',
  'Cross-period',
  'Unspecified',
];

export const UNATTACHED = 'Unattached';

export function toggle(list: ReadonlyArray<string>, value: string): string[] {
  return list.includes(value) ? list.filter((item) => item !== value) : [...list, value];
}

/** Same semantics as the renderer: `scholar` selects the modern layer. */
export function matchesTypes(node: AtlasNodeMeta, types: ReadonlyArray<string>): boolean {
  return (
    types.length === 0
    || types.includes(node.typeKey)
    || (node.layer === 'modern' && types.includes('scholar'))
  );
}

function inc(map: Map<string, number>, key: string) {
  map.set(key, (map.get(key) ?? 0) + 1);
}

/**
 * Faceted counts: each facet is counted against the nodes that pass the
 * OTHER facets, so a chip's number is exactly what selecting it would add.
 */
export function facetCounts(nodes: ReadonlyArray<AtlasNodeMeta>, state: KgFilterState) {
  const types = new Map<string, number>();
  const periods = new Map<string, number>();
  const schools = new Map<string, number>();
  let visible = 0;
  for (const node of nodes) {
    const okType = matchesTypes(node, state.types);
    const okPeriod = state.periods.length === 0 || state.periods.includes(node.periodLabel);
    const okSchool = state.schools.length === 0 || state.schools.includes(node.schoolLabel);
    if (okPeriod && okSchool) {
      inc(types, node.typeKey);
      if (node.layer === 'modern') inc(types, 'scholar');
    }
    if (okType && okSchool) inc(periods, node.periodLabel);
    if (okType && okPeriod && node.schoolLabel !== UNATTACHED) inc(schools, node.schoolLabel);
    if (okType && okPeriod && okSchool) visible += 1;
  }
  return { types, periods, schools, visible };
}

