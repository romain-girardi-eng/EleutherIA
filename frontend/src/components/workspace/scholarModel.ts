import {
  PERIOD_ORDER,
  SCHOOL_ORDER,
  type AtlasEdgeMeta,
  type AtlasNodeMeta,
} from '../cosmograph/AtlasHelpers';
import type { KgFilterState } from '../cosmograph/KgFilters';

export const UNSPECIFIED_PERIOD = 'Unspecified';
export const UNATTACHED_SCHOOL = 'Unattached';
export const MAX_COMPARE = 4;

export type ScholarSortKey = 'relevance' | 'label' | 'type' | 'period' | 'school' | 'degree';
export type SortDirection = 'asc' | 'desc';
export interface ScholarSort {
  key: ScholarSortKey;
  direction: SortDirection;
}

export type FacetKey = 'types' | 'periods' | 'schools';

export interface ScholarRow {
  node: AtlasNodeMeta;
  /** Folded label, used for ranking. */
  label: string;
  /** Folded concatenation of every searchable field. */
  haystack: string;
  periodRank: number;
}

export interface ScoredRow {
  row: ScholarRow;
  score: number;
}

export interface FacetCounts {
  types: ReadonlyMap<string, number>;
  periods: ReadonlyMap<string, number>;
  schools: ReadonlyMap<string, number>;
}

/**
 * Case-, accent- and breathing-insensitive folding so that a classicist can
 * type `autexousion`-style Latin transliterations or unaccented Greek
 * (`αυτεξουσιον`) and still hit the polytonic form held in the data.
 */
export function foldText(value: string): string {
  return value
    .normalize('NFD')
    .replace(/\p{M}+/gu, '')
    .replace(/ς/g, 'σ')
    .toLocaleLowerCase('en');
}

function periodRank(period: string): number {
  const index = PERIOD_ORDER.indexOf(period);
  if (index >= 0) return index;
  return period === UNSPECIFIED_PERIOD ? PERIOD_ORDER.length + 1 : PERIOD_ORDER.length;
}

export function buildSearchIndex(meta: ReadonlyArray<AtlasNodeMeta>): ScholarRow[] {
  return meta.map((node) => ({
    node,
    label: foldText(node.label),
    haystack: foldText([
      node.label,
      node.id,
      node.typeLabel,
      node.periodLabel,
      node.schoolLabel,
      node.greekTerm,
      node.latinTerm,
    ].join(' \u0000 ')),
    periodRank: periodRank(node.periodLabel),
  }));
}

export function facetTypeKeys(node: AtlasNodeMeta): string[] {
  return node.layer === 'modern' && node.typeKey === 'person'
    ? [node.typeKey, 'scholar']
    : [node.typeKey];
}

/** Mirrors the Atlas filter semantics so a shared filter means the same thing in every mode. */
export function matchesFacets(
  node: AtlasNodeMeta,
  filters: KgFilterState,
  skip?: FacetKey,
): boolean {
  if (skip !== 'periods' && filters.periods.length > 0 && !filters.periods.includes(node.periodLabel)) {
    return false;
  }
  if (skip !== 'schools' && filters.schools.length > 0 && !filters.schools.includes(node.schoolLabel)) {
    return false;
  }
  if (
    skip !== 'types' &&
    filters.types.length > 0 &&
    !filters.types.includes(node.typeKey) &&
    !(node.layer === 'modern' && filters.types.includes('scholar'))
  ) {
    return false;
  }
  return true;
}

export function tokenizeQuery(query: string): string[] {
  return foldText(query).split(/\s+/).filter(Boolean);
}

function scoreRow(row: ScholarRow, tokens: ReadonlyArray<string>, phrase: string): number {
  let score = 0;
  if (row.label === phrase) score += 1000;
  else if (row.label.startsWith(phrase)) score += 600;
  else if (row.label.includes(phrase)) score += 300;
  for (const token of tokens) {
    if (row.label.startsWith(token)) score += 60;
    else if (row.label.includes(` ${token}`)) score += 40;
    else if (row.label.includes(token)) score += 20;
  }
  // Break ties by centrality without letting a hub drown an exact title match.
  return score + Math.log1p(row.node.degree);
}

/** All tokens must occur; returns rows with a relevance score. */
export function searchRows(rows: ReadonlyArray<ScholarRow>, query: string): ScoredRow[] {
  const tokens = tokenizeQuery(query);
  if (tokens.length === 0) {
    return rows.map((row) => ({ row, score: row.node.importance }));
  }
  const phrase = tokens.join(' ');
  const result: ScoredRow[] = [];
  for (const row of rows) {
    if (tokens.every((token) => row.haystack.includes(token))) {
      result.push({ row, score: scoreRow(row, tokens, phrase) });
    }
  }
  return result;
}

export function computeFacetCounts(
  rows: ReadonlyArray<ScoredRow>,
  filters: KgFilterState,
): FacetCounts {
  const types = new Map<string, number>();
  const periods = new Map<string, number>();
  const schools = new Map<string, number>();
  for (const { row } of rows) {
    const { node } = row;
    if (matchesFacets(node, filters, 'types')) {
      for (const key of facetTypeKeys(node)) types.set(key, (types.get(key) ?? 0) + 1);
    }
    if (matchesFacets(node, filters, 'periods')) {
      periods.set(node.periodLabel, (periods.get(node.periodLabel) ?? 0) + 1);
    }
    if (matchesFacets(node, filters, 'schools')) {
      schools.set(node.schoolLabel, (schools.get(node.schoolLabel) ?? 0) + 1);
    }
  }
  return { types, periods, schools };
}

const collator = new Intl.Collator('en', { sensitivity: 'base', numeric: true });

export function defaultDirection(key: ScholarSortKey): SortDirection {
  return key === 'degree' || key === 'relevance' ? 'desc' : 'asc';
}

export function nextSort(current: ScholarSort, key: ScholarSortKey): ScholarSort {
  if (current.key !== key) return { key, direction: defaultDirection(key) };
  return { key, direction: current.direction === 'asc' ? 'desc' : 'asc' };
}

export function sortRows(rows: ScoredRow[], sort: ScholarSort): AtlasNodeMeta[] {
  const sign = sort.direction === 'asc' ? 1 : -1;
  const byLabel = (a: ScoredRow, b: ScoredRow) => collator.compare(a.row.node.label, b.row.node.label);
  const compare = (a: ScoredRow, b: ScoredRow): number => {
    switch (sort.key) {
      case 'label':
        return sign * byLabel(a, b);
      case 'type':
        return sign * collator.compare(a.row.node.typeLabel, b.row.node.typeLabel) || byLabel(a, b);
      case 'period':
        return sign * (a.row.periodRank - b.row.periodRank) || byLabel(a, b);
      case 'school': {
        const aNone = a.row.node.schoolLabel === UNATTACHED_SCHOOL;
        const bNone = b.row.node.schoolLabel === UNATTACHED_SCHOOL;
        // Unattached rows always sink: they are absence of data, not a value.
        if (aNone !== bNone) return aNone ? 1 : -1;
        return sign * collator.compare(a.row.node.schoolLabel, b.row.node.schoolLabel) || byLabel(a, b);
      }
      case 'degree':
        return sign * (a.row.node.degree - b.row.node.degree) || byLabel(a, b);
      case 'relevance':
      default:
        return sign * (a.score - b.score) || byLabel(a, b);
    }
  };
  return [...rows].sort(compare).map((entry) => entry.row.node);
}

export function orderedPeriods(counts: ReadonlyMap<string, number>, active: ReadonlyArray<string>): string[] {
  const keys = new Set([...counts.keys(), ...active]);
  return [...keys].sort((a, b) => periodRank(a) - periodRank(b) || collator.compare(a, b));
}

export function orderedSchools(counts: ReadonlyMap<string, number>, active: ReadonlyArray<string>): string[] {
  const keys = new Set([...counts.keys(), ...active]);
  keys.delete(UNATTACHED_SCHOOL);
  const rank = (school: string) => {
    const index = SCHOOL_ORDER.indexOf(school);
    return index >= 0 ? index : SCHOOL_ORDER.length;
  };
  return [...keys].sort(
    (a, b) =>
      rank(a) - rank(b) ||
      (counts.get(b) ?? 0) - (counts.get(a) ?? 0) ||
      collator.compare(a, b),
  );
}

export function toggleValue(list: ReadonlyArray<string>, value: string): string[] {
  return list.includes(value) ? list.filter((item) => item !== value) : [...list, value];
}

export function activeFilterCount(filters: KgFilterState): number {
  return filters.periods.length + filters.types.length + filters.schools.length;
}

/* ------------------------------------------------------------------ */
/* Influence matrix: school → school, over the edges of the release.   */
/* ------------------------------------------------------------------ */

export type RelationCategoryFilter = 'all' | AtlasEdgeMeta['category'];

export interface InfluenceSample {
  source: string;
  target: string;
  relation: string;
}

export interface InfluenceCell {
  source: string;
  target: string;
  count: number;
  relations: Array<[string, number]>;
  samples: InfluenceSample[];
}

export interface InfluenceMatrix {
  schools: string[];
  cells: ReadonlyMap<string, InfluenceCell>;
  max: number;
  total: number;
  outgoing: ReadonlyMap<string, number>;
  incoming: ReadonlyMap<string, number>;
}

export const cellKey = (source: string, target: string) => `${source}\u0000${target}`;

const MAX_MATRIX_SCHOOLS = 12;
const MAX_SAMPLES = 4;

export function buildInfluenceMatrix(
  meta: ReadonlyArray<AtlasNodeMeta>,
  edges: ReadonlyArray<AtlasEdgeMeta>,
  category: RelationCategoryFilter,
): InfluenceMatrix {
  const schoolById = new Map<string, string>();
  const labelById = new Map<string, string>();
  for (const node of meta) {
    if (node.schoolLabel !== UNATTACHED_SCHOOL) {
      schoolById.set(node.id, node.schoolLabel);
      labelById.set(node.id, node.label);
    }
  }

  const raw = new Map<string, { source: string; target: string; count: number; relations: Map<string, number>; samples: InfluenceSample[] }>();
  const volume = new Map<string, number>();
  for (const edge of edges) {
    if (category !== 'all' && edge.category !== category) continue;
    const source = schoolById.get(edge.source);
    const target = schoolById.get(edge.target);
    if (!source || !target) continue;
    const key = cellKey(source, target);
    let cell = raw.get(key);
    if (!cell) {
      cell = { source, target, count: 0, relations: new Map(), samples: [] };
      raw.set(key, cell);
    }
    cell.count += 1;
    cell.relations.set(edge.relation, (cell.relations.get(edge.relation) ?? 0) + 1);
    if (cell.samples.length < MAX_SAMPLES) {
      cell.samples.push({
        source: labelById.get(edge.source) ?? edge.source,
        target: labelById.get(edge.target) ?? edge.target,
        relation: edge.relation,
      });
    }
    volume.set(source, (volume.get(source) ?? 0) + 1);
    if (target !== source) volume.set(target, (volume.get(target) ?? 0) + 1);
  }

  const schools = orderedSchools(volume, [])
    .sort((a, b) => (volume.get(b) ?? 0) - (volume.get(a) ?? 0))
    .slice(0, MAX_MATRIX_SCHOOLS);
  const kept = new Set(schools);
  const cells = new Map<string, InfluenceCell>();
  const outgoing = new Map<string, number>();
  const incoming = new Map<string, number>();
  let max = 0;
  let total = 0;
  raw.forEach((cell, key) => {
    if (!kept.has(cell.source) || !kept.has(cell.target)) return;
    max = Math.max(max, cell.count);
    total += cell.count;
    outgoing.set(cell.source, (outgoing.get(cell.source) ?? 0) + cell.count);
    incoming.set(cell.target, (incoming.get(cell.target) ?? 0) + cell.count);
    cells.set(key, {
      source: cell.source,
      target: cell.target,
      count: cell.count,
      relations: [...cell.relations.entries()].sort((a, b) => b[1] - a[1]),
      samples: cell.samples,
    });
  });
  return { schools, cells, max, total, outgoing, incoming };
}

/* ------------------------------------------------------------------ */
/* Shortest path over the full (unbounded) edge list.                   */
/* ------------------------------------------------------------------ */

export interface AdjacentEdge {
  id: string;
  relation: string;
  outgoing: boolean;
}

export type Adjacency = ReadonlyMap<string, ReadonlyArray<AdjacentEdge>>;

export function buildAdjacency(edges: ReadonlyArray<AtlasEdgeMeta>): Adjacency {
  const adjacency = new Map<string, AdjacentEdge[]>();
  const push = (from: string, entry: AdjacentEdge) => {
    const list = adjacency.get(from);
    if (list) list.push(entry);
    else adjacency.set(from, [entry]);
  };
  for (const edge of edges) {
    if (edge.source === edge.target) continue;
    push(edge.source, { id: edge.target, relation: edge.relation, outgoing: true });
    push(edge.target, { id: edge.source, relation: edge.relation, outgoing: false });
  }
  return adjacency;
}

export interface PathStep {
  from: string;
  to: string;
  relation: string;
  /** True when the stored edge points from `from` to `to`. */
  forward: boolean;
}

export const MAX_PATH_DEPTH = 6;

/**
 * Breadth-first search, edge direction ignored for reachability but recorded
 * per step so the reader sees which way each attested relation runs.
 */
export function findShortestPath(
  adjacency: Adjacency,
  sourceId: string,
  targetId: string,
  maxDepth = MAX_PATH_DEPTH,
): PathStep[] | null {
  if (sourceId === targetId) return [];
  const previous = new Map<string, PathStep>();
  const visited = new Set([sourceId]);
  let frontier = [sourceId];
  for (let depth = 0; depth < maxDepth && frontier.length > 0; depth += 1) {
    const next: string[] = [];
    for (const current of frontier) {
      for (const edge of adjacency.get(current) ?? []) {
        if (visited.has(edge.id)) continue;
        visited.add(edge.id);
        previous.set(edge.id, { from: current, to: edge.id, relation: edge.relation, forward: edge.outgoing });
        if (edge.id === targetId) {
          const steps: PathStep[] = [];
          let cursor = targetId;
          while (cursor !== sourceId) {
            const step = previous.get(cursor);
            if (!step) return null;
            steps.push(step);
            cursor = step.from;
          }
          return steps.reverse();
        }
        next.push(edge.id);
      }
    }
    frontier = next;
  }
  return null;
}

/* ------------------------------------------------------------------ */
/* Comparison: neighbours shared by at least two compared nodes.        */
/* ------------------------------------------------------------------ */

export interface SharedNeighbour {
  id: string;
  memberIds: string[];
}

export function sharedNeighbours(
  adjacency: Adjacency,
  ids: ReadonlyArray<string>,
  limit = 24,
): SharedNeighbour[] {
  if (ids.length < 2) return [];
  const members = new Map<string, Set<string>>();
  const compared = new Set(ids);
  for (const id of ids) {
    for (const edge of adjacency.get(id) ?? []) {
      if (compared.has(edge.id)) continue;
      let set = members.get(edge.id);
      if (!set) {
        set = new Set();
        members.set(edge.id, set);
      }
      set.add(id);
    }
  }
  return [...members.entries()]
    .filter(([, set]) => set.size >= 2)
    .map(([id, set]) => ({ id, memberIds: ids.filter((member) => set.has(member)) }))
    .sort((a, b) => b.memberIds.length - a.memberIds.length || a.id.localeCompare(b.id))
    .slice(0, limit);
}

export function directLinks(
  adjacency: Adjacency,
  ids: ReadonlyArray<string>,
): Array<{ from: string; to: string; relation: string }> {
  const compared = new Set(ids);
  const links: Array<{ from: string; to: string; relation: string }> = [];
  for (const id of ids) {
    for (const edge of adjacency.get(id) ?? []) {
      if (edge.outgoing && compared.has(edge.id)) {
        links.push({ from: id, to: edge.id, relation: edge.relation });
      }
    }
  }
  return links;
}
