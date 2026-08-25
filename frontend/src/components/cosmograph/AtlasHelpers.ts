import type { KGEdge, KGNode } from '../../types';
import { ATLAS_THEME } from './atlasTheme';

// Visual hierarchy spec — see /tmp/cosmograph-ux-diagnosis.md §6.

export type LayerKind = 'ancient' | 'modern';

export interface AtlasNodeMeta {
  id: string;
  label: string;
  type: string;
  typeKey: string;
  typeLabel: string;
  layer: LayerKind;
  periodLabel: string;
  schoolLabel: string;
  degree: number;
  importance: number;
  color: string;
  opacity: number;
  size: number;
  description: string;
  greekTerm: string;
  latinTerm: string;
}

export interface AtlasEdgeMeta {
  id: string;
  source: string;
  target: string;
  relation: string;
  relationLabel: string;
  category: 'structural' | 'doctrinal' | 'evidential';
  width: number;
  opacity: number;
  color: string;
}

// Ink-forward colours calibrated for the light Atlas surface. Every swatch
// remains legible on parchment without relying on glow or bloom, which also
// keeps node identity intact when adaptive quality removes decoration.
const PERSON = ATLAS_THEME.nodes.person;
const SCHOLAR = ATLAS_THEME.nodes.scholar;
const CONCEPT = ATLAS_THEME.nodes.concept;
const ARGUMENT = ATLAS_THEME.nodes.argument;
const WORK = ATLAS_THEME.nodes.work;
const SCHOOL = ATLAS_THEME.nodes.school;
const PASSAGE = ATLAS_THEME.nodes.passage;
const DEBATE = ATLAS_THEME.nodes.debate;
const FALLBACK = ATLAS_THEME.nodes.fallback;

const TYPE_COLOR: Record<string, string> = {
  person: PERSON,
  scholar: SCHOLAR,
  concept: CONCEPT,
  argument: ARGUMENT,
  work: WORK,
  school: SCHOOL,
  passage: PASSAGE,
  debate: DEBATE,
};

const TYPE_LABEL: Record<string, string> = {
  person: 'Person',
  scholar: 'Scholar',
  concept: 'Concept',
  argument: 'Argument',
  work: 'Work',
  school: 'School',
  passage: 'Passage',
  debate: 'Debate',
  group: 'Group',
  controversy: 'Controversy',
  reformulation: 'Reformulation',
  publication: 'Publication',
  event: 'Event',
};

const PERIOD_OPACITY: Record<string, number> = {
  Presocratic: 0.55,
  'Classical Greek': 0.7,
  'Hellenistic Greek': 0.8,
  'Roman Republican': 0.82,
  'Roman Imperial': 0.85,
  Patristic: 0.9,
  'Late Antiquity': 1.0,
  Medieval: 0.85,
  Modern: 0.75,
  Contemporary: 0.75,
  Unspecified: 0.6,
};

const HIGH_WEIGHT = new Set(['authored_by', 'member_of', 'creates', 'created_by', 'part_of']);
const MEDIUM_WEIGHT = new Set([
  'interprets',
  'critiques',
  'influences',
  'influenced_by',
  'responds_to',
  'refutes',
  'supports',
  'opposes',
  'agrees_with',
  'critiqued_by',
  'discusses',
]);

export function normalizeType(value: string | undefined | null): string {
  if (!value) return 'unknown';
  return value.trim().toLowerCase().replace(/[\s-]+/g, '_');
}

export function detectLayer(node: KGNode): LayerKind {
  const period = node.period?.toLowerCase() ?? '';
  if (period.includes('modern') || period.includes('contemporary')) {
    return 'modern';
  }

  // Heuristic: a person with modern_scholarship as their primary signal counts as scholar.
  const raw = node as unknown as Record<string, unknown>;
  const role = typeof raw.scholarly_role === 'string' ? raw.scholarly_role.toLowerCase() : '';
  if (role.includes('scholar') || role.includes('historian')) {
    return 'modern';
  }

  return 'ancient';
}

export function nodeColor(node: KGNode, layer: LayerKind): string {
  const typeKey = normalizeType(node.type);
  if (layer === 'modern' && typeKey === 'person') return SCHOLAR;
  return TYPE_COLOR[typeKey] ?? FALLBACK;
}

export function nodeOpacity(node: KGNode): number {
  const period = node.period ?? 'Unspecified';
  return PERIOD_OPACITY[period] ?? 0.7;
}

export function typeLabel(type: string): string {
  const key = normalizeType(type);
  return TYPE_LABEL[key] ?? key.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());
}

export function relationLabel(relation: string): string {
  return relation
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function edgeCategory(relation: string): AtlasEdgeMeta['category'] {
  if (HIGH_WEIGHT.has(relation)) return 'structural';
  if (MEDIUM_WEIGHT.has(relation)) return 'doctrinal';
  return 'evidential';
}

export function edgeWidth(relation: string): number {
  if (HIGH_WEIGHT.has(relation)) return 2.4;
  if (MEDIUM_WEIGHT.has(relation)) return 1.4;
  return 0.6;
}

export function edgeOpacity(relation: string): number {
  if (HIGH_WEIGHT.has(relation)) return 0.7;
  if (MEDIUM_WEIGHT.has(relation)) return 0.45;
  return 0.25;
}

export function edgeColor(relation: string): string {
  const op = edgeOpacity(relation);
  // Warm graphite with opacity baked in for the parchment canvas.
  return `rgba(87, 83, 78, ${op.toFixed(2)})`;
}

export function computeDegreeMap(edges: KGEdge[]): Map<string, number> {
  const map = new Map<string, number>();
  for (const edge of edges) {
    map.set(edge.source, (map.get(edge.source) ?? 0) + 1);
    map.set(edge.target, (map.get(edge.target) ?? 0) + 1);
  }
  return map;
}

export function computeNodeSize(degree: number, maxDegree: number): number {
  // Power-scale: top nodes ~30px, lowest ~6px.
  const safeMax = Math.max(maxDegree, 1);
  const normalized = Math.pow(degree / safeMax, 0.55);
  return 6 + normalized * 24;
}

export function buildAtlasMeta(
  nodes: KGNode[],
  edges: KGEdge[],
): {
  nodes: AtlasNodeMeta[];
  edges: AtlasEdgeMeta[];
  nodeMap: Map<string, AtlasNodeMeta>;
} {
  const degreeMap = computeDegreeMap(edges);
  let maxDegree = 0;
  degreeMap.forEach((value) => {
    if (value > maxDegree) maxDegree = value;
  });

  const decorated: AtlasNodeMeta[] = nodes.map((node) => {
    const layer = detectLayer(node);
    const typeKey = normalizeType(node.type);
    const degree = degreeMap.get(node.id) ?? 0;
    const importance = degree;
    return {
      id: node.id,
      label: node.label || node.id,
      type: node.type,
      typeKey,
      typeLabel: layer === 'modern' && typeKey === 'person' ? 'Scholar' : typeLabel(node.type),
      layer,
      periodLabel: node.period ?? 'Unspecified',
      schoolLabel: node.school ?? 'Unattached',
      degree,
      importance,
      color: nodeColor(node, layer),
      opacity: nodeOpacity(node),
      size: computeNodeSize(degree, maxDegree),
      description: node.description ?? '',
      greekTerm: node.greek_term ?? '',
      latinTerm: node.latin_term ?? '',
    };
  });

  const nodeMap = new Map(decorated.map((n) => [n.id, n]));
  const validEdges = edges.filter((e) => nodeMap.has(e.source) && nodeMap.has(e.target));

  const decoratedEdges: AtlasEdgeMeta[] = validEdges.map((edge, index) => {
    const rel = edge.relation || 'related_to';
    return {
      id: edge.id || edge.edge_id || `${edge.source}->${edge.target}#${index}`,
      source: edge.source,
      target: edge.target,
      relation: rel,
      relationLabel: relationLabel(rel),
      category: edgeCategory(rel),
      width: edgeWidth(rel),
      opacity: edgeOpacity(rel),
      color: edgeColor(rel),
    };
  });

  return { nodes: decorated, edges: decoratedEdges, nodeMap };
}

export const TYPE_PALETTE: ReadonlyArray<{ key: string; color: string; label: string }> = [
  { key: 'person', color: PERSON, label: 'Person' },
  { key: 'scholar', color: SCHOLAR, label: 'Scholar (modern)' },
  { key: 'concept', color: CONCEPT, label: 'Concept' },
  { key: 'argument', color: ARGUMENT, label: 'Argument' },
  { key: 'work', color: WORK, label: 'Work' },
  { key: 'school', color: SCHOOL, label: 'School' },
  { key: 'passage', color: PASSAGE, label: 'Passage' },
];

export const PERIOD_ORDER: ReadonlyArray<string> = [
  'Presocratic',
  'Classical Greek',
  'Hellenistic Greek',
  'Roman Republican',
  'Roman Imperial',
  'Patristic',
  'Late Antiquity',
  'Medieval',
  'Modern',
];

export const SCHOOL_ORDER: ReadonlyArray<string> = [
  'Stoics',
  'Epicureans',
  'Peripatetics',
  'Academics',
  'Middle Platonism',
  'Neoplatonism',
  'Christian Patristics',
  'Pyrrhonists',
];
