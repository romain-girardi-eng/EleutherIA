// Curated landing anchors: the ~40 nodes Romain's thesis actually pivots around.
// Matching is loose — the live KG uses ID suffixes like "_3c_ce", "_280_206bce_i9j0k1l2"
// or even "scholar_..." prefixes. We therefore match by:
//   - exact id or prefix match for canonical anchor ids
//   - keyword match against id for known scholars/works

export const ATLAS_CORE_CONCEPTS_PREFIXES: ReadonlyArray<string> = [
  'concept_ancient_free_will_debate_structure',
  'concept_autexousion',
  'concept_to_eph_hemin',
  'concept_eph_hemin',
  'concept_prohairesis',
  'concept_heimarmene',
  'concept_free_will',
];

export const ATLAS_PERSON_PREFIXES: ReadonlyArray<string> = [
  'person_aristotle',
  'person_chrysippus',
  'person_alexander_aphrodisias',
  'person_alexander_of_aphrodisias',
  'person_plotinus',
  'person_justin_martyr',
  'person_origen',
  'person_augustine',
  'person_boethius',
];

export const ATLAS_SCHOOLS: ReadonlyArray<string> = [
  'school_stoics',
  'school_epicureans',
  'school_peripatetics',
  'school_middle_platonism',
  'school_neoplatonism',
];

// Scholar / modern reception IDs use multiple naming conventions in the live KG
// (person_, scholar_, person_..._contemporary, etc.). We match by id keyword.
export const ATLAS_SCHOLAR_KEYWORDS: ReadonlyArray<string> = [
  'bobzien',
  'sharples',
  'dihle',
  'karamanolis',
  'kane_robert',
  'frede_dorothea',
  'frede_michael',
];

export const ATLAS_WORK_KEYWORDS: ReadonlyArray<string> = [
  'nicomachean_ethics',
  'alexander_de_fato',
  'cicero_de_fato',
  'plotinus_enneads',
  'origen_de_principiis',
  'boethius_consolatio',
];

const PREFIX_ANCHORS: ReadonlyArray<string> = [
  ...ATLAS_CORE_CONCEPTS_PREFIXES,
  ...ATLAS_PERSON_PREFIXES,
  ...ATLAS_SCHOOLS,
];

const KEYWORD_ANCHORS_PERSON: ReadonlyArray<string> = ATLAS_SCHOLAR_KEYWORDS;
const KEYWORD_ANCHORS_WORK: ReadonlyArray<string> = ATLAS_WORK_KEYWORDS;
const ATLAS_CORE_DEBATE_PREFIX = 'concept_ancient_free_will_debate_structure';

export function isAtlasNode(
  nodeId: string,
  nodeType: string | undefined,
): boolean {
  const lower = nodeId.toLowerCase();

  for (const anchor of PREFIX_ANCHORS) {
    const a = anchor.toLowerCase();
    if (lower === a || lower.startsWith(`${a}_`) || lower.startsWith(`${a}-`)) {
      return true;
    }
  }

  if ((nodeType === 'person' || lower.startsWith('scholar_'))
      && KEYWORD_ANCHORS_PERSON.some((kw) => lower.includes(kw))) {
    return true;
  }

  if (nodeType === 'work'
      && KEYWORD_ANCHORS_WORK.some((kw) => lower.includes(kw))) {
    return true;
  }

  return false;
}

export interface AtlasNodeRef {
  id: string;
  type?: string;
  importance?: number;
}

export type AtlasConstellationKey =
  | 'core'
  | 'agency'
  | 'stoic'
  | 'epicurean'
  | 'peripatetic'
  | 'christian'
  | 'late_antique'
  | 'reception';

export interface AtlasConstellationNodeRef extends AtlasNodeRef {
  layer?: 'ancient' | 'modern';
  periodLabel?: string;
  schoolLabel?: string;
}

export const ATLAS_CONSTELLATION_POSITIONS: Readonly<
  Record<AtlasConstellationKey, readonly [number, number]>
> = {
  core: [0, 0],
  agency: [0, -650],
  stoic: [510, -405],
  epicurean: [630, 165],
  late_antique: [245, 605],
  christian: [-325, 565],
  peripatetic: [-645, 90],
  reception: [-455, -460],
};

export function atlasConstellationKey(
  node: AtlasConstellationNodeRef,
): AtlasConstellationKey {
  const id = node.id.toLowerCase();
  const school = (node.schoolLabel ?? '').toLowerCase();
  const period = (node.periodLabel ?? '').toLowerCase();

  if (id.startsWith('concept_ancient_free_will_debate_structure')) return 'core';
  if (
    node.layer === 'modern'
    || period.includes('modern')
    || period.includes('contemporary')
    || id.startsWith('scholar_')
    || /bobzien|sharples|dihle|frede|karamanolis/.test(id)
  ) return 'reception';
  if (/epicur|clinamen|parenkl|democrit/.test(id) || school.includes('epicur')) {
    return 'epicurean';
  }
  if (
    /stoic|chrysipp|cleanth|synkat|heimarmen|cylinder|confatal/.test(id)
    || school.includes('stoic')
  ) return 'stoic';
  if (
    /alexander_aphrodis|alexander_of_aphrodis|alexander_de_fato|carnead|peripatetic/.test(id)
    || school.includes('peripat')
  ) return 'peripatetic';
  if (
    /justin|tatian|origen|augustine|irenaeus|autexous|liberum_arbitrium|christian/.test(id)
    || school.includes('christian')
    || period.includes('patristic')
  ) return 'christian';
  if (
    /plotinus|boethius|maximus|nemesius|neoplaton|apocatast/.test(id)
    || school.includes('neoplat')
    || period.includes('late antiquity')
    || period.includes('medieval')
  ) return 'late_antique';
  return 'agency';
}

export interface AtlasEdgeRef {
  id?: string;
  source: string;
  target: string;
  relation?: string;
  weight?: number;
}

export function pickAtlasNodeIds(nodes: ReadonlyArray<AtlasNodeRef>): Set<string> {
  const matched = new Set<string>();
  for (const node of nodes) {
    if (isAtlasNode(node.id, node.type)) {
      matched.add(node.id);
    }
  }
  return matched;
}

const LANDING_TYPE_WEIGHT: Readonly<Record<string, number>> = {
  concept: 90,
  person: 85,
  school: 80,
  debate: 75,
  controversy: 75,
  argument: 68,
  work: 62,
  publication: 45,
  passage: 22,
};

interface RankedLandingNode {
  id: string;
  ring: 1 | 2;
  anchorTouches: number;
  firstRingTouches: number;
  typeWeight: number;
  importance: number;
}

/**
 * Expand the hand-curated anchors into a deterministic, legible landing map.
 *
 * A scholar needs enough connective tissue to understand why an anchor is
 * central, but not the 23k-node release on first paint. Direct neighbours win,
 * then a small second ring fills sparse releases. The hard cap is a rendering
 * and cognitive-load contract, not a data-availability limit.
 */
export function pickAtlasLandingNodeIds(
  nodes: ReadonlyArray<AtlasNodeRef>,
  edges: ReadonlyArray<AtlasEdgeRef>,
  limit = 220,
): Set<string> {
  const nodeById = new Map(nodes.map((node) => [node.id, node]));
  const anchors = pickAtlasNodeIds(nodes);
  if (anchors.size === 0) return new Set();

  const incidentAnchors = new Set<string>();
  for (const edge of edges) {
    if (anchors.has(edge.source) && nodeById.has(edge.target)) incidentAnchors.add(edge.source);
    if (anchors.has(edge.target) && nodeById.has(edge.source)) incidentAnchors.add(edge.target);
  }
  if (incidentAnchors.size > 0) {
    for (const anchor of anchors) {
      if (!incidentAnchors.has(anchor) && !anchor.startsWith(ATLAS_CORE_DEBATE_PREFIX)) {
        anchors.delete(anchor);
      }
    }
  }

  const directTouches = new Map<string, number>();
  for (const edge of edges) {
    const sourceAnchor = anchors.has(edge.source);
    const targetAnchor = anchors.has(edge.target);
    if (sourceAnchor && !targetAnchor && nodeById.has(edge.target)) {
      directTouches.set(edge.target, (directTouches.get(edge.target) ?? 0) + 1);
    }
    if (targetAnchor && !sourceAnchor && nodeById.has(edge.source)) {
      directTouches.set(edge.source, (directTouches.get(edge.source) ?? 0) + 1);
    }
  }

  const firstRing = new Set(directTouches.keys());
  const secondTouches = new Map<string, number>();
  for (const edge of edges) {
    const sourceFirst = firstRing.has(edge.source);
    const targetFirst = firstRing.has(edge.target);
    if (sourceFirst && !anchors.has(edge.target) && !firstRing.has(edge.target) && nodeById.has(edge.target)) {
      secondTouches.set(edge.target, (secondTouches.get(edge.target) ?? 0) + 1);
    }
    if (targetFirst && !anchors.has(edge.source) && !firstRing.has(edge.source) && nodeById.has(edge.source)) {
      secondTouches.set(edge.source, (secondTouches.get(edge.source) ?? 0) + 1);
    }
  }

  const ranked: RankedLandingNode[] = [];
  for (const node of nodes) {
    if (anchors.has(node.id)) continue;
    const anchorTouches = directTouches.get(node.id) ?? 0;
    const firstRingTouches = secondTouches.get(node.id) ?? 0;
    if (anchorTouches === 0 && firstRingTouches === 0) continue;
    ranked.push({
      id: node.id,
      ring: anchorTouches > 0 ? 1 : 2,
      anchorTouches,
      firstRingTouches,
      typeWeight: LANDING_TYPE_WEIGHT[node.type ?? ''] ?? 10,
      importance: Number.isFinite(node.importance) ? node.importance ?? 0 : 0,
    });
  }

  ranked.sort((a, b) =>
    a.ring - b.ring
    || b.anchorTouches - a.anchorTouches
    || b.typeWeight - a.typeWeight
    || b.firstRingTouches - a.firstRingTouches
    || b.importance - a.importance
    || a.id.localeCompare(b.id));

  const safeLimit = Math.max(anchors.size, Math.max(1, Math.floor(limit)));
  const selected = new Set(anchors);
  for (const candidate of ranked) {
    if (selected.size >= safeLimit) break;
    selected.add(candidate.id);
  }

  // A disconnected anchor expands the fit bounds without contributing an
  // intelligible route (the current release has two such satellites). Keep it
  // searchable in Full/Scholar, but omit it from the spatial landing map when
  // there is a real connected projection to show.
  const connected = new Set<string>();
  for (const edge of edges) {
    if (selected.has(edge.source) && selected.has(edge.target)) {
      connected.add(edge.source);
      connected.add(edge.target);
    }
  }
  if (connected.size > 0) {
    for (const id of selected) {
      if (!connected.has(id) && !id.startsWith(ATLAS_CORE_DEBATE_PREFIX)) {
        selected.delete(id);
      }
    }
  }
  return selected;
}

const LANDING_RELATION_WEIGHT: Readonly<Record<string, number>> = {
  authored_by: 9,
  created_by: 9,
  advanced_in: 9,
  part_of: 9,
  member_of: 8,
  creates: 8,
  interprets: 7,
  critiques: 7,
  refutes: 7,
  opposes: 7,
  responds_to: 7,
  influences: 6,
  influenced_by: 6,
  supports: 6,
  agrees_with: 6,
  discusses: 4,
  evidenced_by: 3,
  cites: 2,
  mentions: 1,
};

function landingEdgeKey(edge: AtlasEdgeRef): string {
  return [edge.source, edge.target, edge.relation ?? '', edge.id ?? ''].join('\u0000');
}

function unorderedPair(edge: AtlasEdgeRef): string {
  return edge.source < edge.target
    ? `${edge.source}\u0000${edge.target}`
    : `${edge.target}\u0000${edge.source}`;
}

/**
 * Keep one deterministic semantic backbone instead of drawing every relation.
 *
 * A maximum-ranking spanning forest preserves reachability inside each visible
 * component. A small number of high-value extra pairs adds scholarly texture
 * without recreating the all-edge hairball. Parallel edges between the same
 * two nodes collapse to the strongest visible relation; their complete list is
 * still available in the node dossier and full graph.
 */
export function pickAtlasLandingEdges<T extends AtlasEdgeRef>(
  selectedNodeIds: ReadonlySet<string>,
  edges: ReadonlyArray<T>,
  anchors: ReadonlySet<string>,
  limit = Math.ceil(selectedNodeIds.size * 1.25),
): T[] {
  const ranked = edges
    .filter((edge) =>
      edge.source !== edge.target
      && selectedNodeIds.has(edge.source)
      && selectedNodeIds.has(edge.target))
    .map((edge) => ({
      edge,
      anchorTouches: Number(anchors.has(edge.source)) + Number(anchors.has(edge.target)),
      relationWeight: LANDING_RELATION_WEIGHT[edge.relation ?? ''] ?? 0,
      sourceWeight: Number.isFinite(edge.weight) ? edge.weight ?? 0 : 0,
      key: landingEdgeKey(edge),
    }))
    .sort((a, b) =>
      b.anchorTouches - a.anchorTouches
      || b.relationWeight - a.relationWeight
      || b.sourceWeight - a.sourceWeight
      || a.key.localeCompare(b.key));

  const parent = new Map<string, string>();
  for (const id of selectedNodeIds) parent.set(id, id);
  const find = (id: string): string => {
    const current = parent.get(id) ?? id;
    if (current === id) return id;
    const root = find(current);
    parent.set(id, root);
    return root;
  };
  const union = (left: string, right: string): boolean => {
    const a = find(left);
    const b = find(right);
    if (a === b) return false;
    const [root, child] = a < b ? [a, b] : [b, a];
    parent.set(child, root);
    return true;
  };

  const selected: T[] = [];
  const selectedKeys = new Set<string>();
  const selectedPairs = new Set<string>();
  for (const candidate of ranked) {
    if (!union(candidate.edge.source, candidate.edge.target)) continue;
    selected.push(candidate.edge);
    selectedKeys.add(candidate.key);
    selectedPairs.add(unorderedPair(candidate.edge));
  }

  const safeLimit = Math.max(selected.length, Math.max(1, Math.floor(limit)));
  for (const candidate of ranked) {
    if (selected.length >= safeLimit) break;
    if (selectedKeys.has(candidate.key)) continue;
    const pair = unorderedPair(candidate.edge);
    if (selectedPairs.has(pair)) continue;
    selected.push(candidate.edge);
    selectedKeys.add(candidate.key);
    selectedPairs.add(pair);
  }
  return selected;
}
