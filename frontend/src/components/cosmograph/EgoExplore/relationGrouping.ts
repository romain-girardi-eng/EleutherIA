import type { AtlasNodeMeta } from '../AtlasHelpers';

export interface Neighbor {
  readonly id: string;
  readonly label: string;
  readonly type: string;
  readonly relation: string;
  readonly direction: 'incoming' | 'outgoing';
}

export interface RelationGroup {
  readonly key: string;
  readonly relation: string;
  readonly direction: 'incoming' | 'outgoing';
  readonly neighbors: ReadonlyArray<Neighbor>;
}

const PRIORITY_ORDER: ReadonlyArray<string> = [
  'authored_by',
  'creates',
  'created_by',
  'member_of',
  'part_of',
  'student_of',
  'teaches',
  'influences',
  'influenced_by',
  'interprets',
  'discusses',
  'agrees_with',
  'supports',
  'opposes',
  'critiques',
  'critiqued_by',
  'responds_to',
  'refutes',
  'evidenced_by',
  'mentions',
  'cites',
  'related_to',
];

const PRIORITY_INDEX = new Map<string, number>(
  PRIORITY_ORDER.map((relation, index) => [relation, index]),
);

function priorityFor(relation: string): number {
  return PRIORITY_INDEX.get(relation) ?? PRIORITY_ORDER.length + 1;
}

function groupKey(relation: string, direction: 'incoming' | 'outgoing'): string {
  return `${direction}:${relation}`;
}

export function relationDisplayLabel(
  relation: string,
  direction: 'incoming' | 'outgoing',
): string {
  const base = relation.replace(/_/g, ' ');
  if (direction === 'incoming') {
    if (relation === 'authored_by') return 'author of';
    if (relation === 'creates') return 'created by';
    if (relation === 'created_by') return 'creator of';
    if (relation === 'member_of') return 'members';
    if (relation === 'part_of') return 'contains';
    if (relation === 'influences') return 'influenced by';
    if (relation === 'influenced_by') return 'influences';
    if (relation === 'interprets') return 'interpreted by';
    if (relation === 'critiques') return 'critiqued by';
    if (relation === 'critiqued_by') return 'critiques';
    if (relation === 'student_of') return 'teachers';
    if (relation === 'teaches') return 'students';
    if (relation === 'discusses') return 'discussed by';
    if (relation === 'responds_to') return 'responses';
    if (relation === 'refutes') return 'refuted by';
    if (relation === 'mentions') return 'mentioned by';
    if (relation === 'cites') return 'cited by';
    return base;
  }
  return base;
}

export function groupNeighborsByRelation(
  neighbors: ReadonlyArray<Neighbor>,
  metaById: Map<string, AtlasNodeMeta>,
): ReadonlyArray<RelationGroup> {
  const buckets = new Map<string, Neighbor[]>();
  neighbors.forEach((n) => {
    const key = groupKey(n.relation, n.direction);
    const list = buckets.get(key);
    if (list) {
      list.push(n);
    } else {
      buckets.set(key, [n]);
    }
  });

  const groups: RelationGroup[] = [];
  buckets.forEach((list, key) => {
    const sorted = [...list].sort((a, b) => {
      const da = metaById.get(a.id)?.degree ?? 0;
      const db = metaById.get(b.id)?.degree ?? 0;
      return db - da;
    });
    groups.push({
      key,
      relation: sorted[0].relation,
      direction: sorted[0].direction,
      neighbors: sorted,
    });
  });

  groups.sort((a, b) => {
    const pa = priorityFor(a.relation);
    const pb = priorityFor(b.relation);
    if (pa !== pb) return pa - pb;
    if (a.direction !== b.direction) return a.direction === 'outgoing' ? -1 : 1;
    return b.neighbors.length - a.neighbors.length;
  });

  return groups;
}

export function pickInitialFocalId(
  meta: ReadonlyArray<AtlasNodeMeta>,
  atlasIds: ReadonlySet<string>,
): string | undefined {
  let best: AtlasNodeMeta | undefined;
  for (const node of meta) {
    if (!atlasIds.has(node.id)) continue;
    if (!best || node.degree > best.degree) {
      best = node;
      continue;
    }
    if (node.degree === best.degree && node.id < best.id) {
      best = node;
    }
  }
  return best?.id;
}
