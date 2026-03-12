import {
  Camera,
  ChevronRight,
  Filter,
  Focus,
  Info,
  Layers3,
  Map as MapIcon,
  Network,
  Palette,
  Pause,
  Pin,
  Play,
  RefreshCw,
  Route,
  Search,
  Sparkles,
  Spline,
  X,
} from 'lucide-react';
import { startTransition, useDeferredValue, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  Cosmograph,
  CosmographBars,
  CosmographPopup,
  CosmographProvider,
  CosmographRangeColorLegend,
  CosmographSizeLegend,
  CosmographTimeline,
  prepareCosmographData,
  type CosmographConfig,
  type CosmographData,
  type CosmographRef,
} from '@cosmograph/react';
import { apiClient } from '../api/client';
import type { CytoscapeData, KGEdge, KGNode } from '../types';
import ModeSwitcher from '../components/canvas/ModeSwitcher';
import BottomTabNav from '../components/mobile/BottomTabNav';
import NodeDetailPanel from '../components/NodeDetailPanel';

type ColorMode = 'community' | 'type' | 'school' | 'period' | 'importance';
type SizeMode = 'importance' | 'degree' | 'sources';
type ClusterMode = 'community' | 'type' | 'school' | 'period' | 'none';
type SelectionMode = 'rect' | 'polygon' | null;

type RawKGNode = KGNode & {
  approximate_dates?: string;
  floruit?: string;
  birth?: string;
  death?: string;
  date?: string;
  year?: number;
  scholarly_role?: string;
};

type EdgeApiResponse = KGEdge[] | { edges?: KGEdge[] };

interface FlatGraphNode {
  id: string;
  label: string;
  typeKey: string;
  typeLabel: string;
  periodLabel: string;
  schoolGroup: string;
  datesLabel: string;
  year: number;
  degree: number;
  relationDiversity: number;
  sourceCount: number;
  ancientSourceCount: number;
  modernSourceCount: number;
  importance: number;
  labelWeight: number;
  communityKey: string;
  communityLabel: string;
  descriptionPreview: string;
  greekTerm: string;
  latinTerm: string;
  searchHint: string;
}

interface FlatGraphLink {
  id: string;
  source: string;
  target: string;
  relation: string;
  relationCategory: string;
  relationLabel: string;
  strength: number;
  directed: boolean;
}

interface RelatedNode {
  id: string;
  label: string;
  type: string;
  relation: string;
  direction: 'incoming' | 'outgoing';
}

interface GraphModel {
  points: CosmographData | undefined;
  links: CosmographData | undefined;
  cosmographConfig: Omit<CosmographConfig, 'points' | 'links'>;
  flatNodes: FlatGraphNode[];
  flatLinks: FlatGraphLink[];
  nodesById: Map<string, RawKGNode>;
  flatNodesById: Map<string, FlatGraphNode>;
  relationshipsByNodeId: Map<string, RelatedNode[]>;
  typeColorMap: Record<string, string>;
  schoolColorMap: Record<string, string>;
  periodColorMap: Record<string, string>;
  communityColorMap: Record<string, string>;
  communityOrder: string[];
  topStops: string[];
  totalNodes: number;
  totalEdges: number;
  minImportance: number;
  maxImportance: number;
}

interface SimulationControls {
  decay: number;
  gravity: number;
  center: number;
  repulsion: number;
  theta: number;
  linkSpring: number;
  linkDistance: number;
  mouseRepulsion: number;
  friction: number;
  impulse: number;
}

interface LegendItem {
  label: string;
  color: string;
  count: number;
}

const TYPE_META: Record<string, { label: string; color: string; bias: number }> = {
  person: { label: 'Thinker', color: '#4cc9f0', bias: 28 },
  work: { label: 'Work', color: '#f4d35e', bias: 18 },
  concept: { label: 'Concept', color: '#ff8fab', bias: 24 },
  argument: { label: 'Argument', color: '#ff6b6b', bias: 20 },
  debate: { label: 'Debate', color: '#b794f4', bias: 18 },
  school: { label: 'School', color: '#2ec4b6', bias: 26 },
  quote: { label: 'Quote', color: '#f97316', bias: 10 },
  passage: { label: 'Passage', color: '#94a3b8', bias: 4 },
  publication: { label: 'Publication', color: '#14b8a6', bias: 14 },
  event: { label: 'Event', color: '#fb7185', bias: 12 },
  group: { label: 'Group', color: '#818cf8', bias: 14 },
  controversy: { label: 'Controversy', color: '#ef4444', bias: 20 },
  reformulation: { label: 'Reformulation', color: '#34d399', bias: 16 },
  argument_framework: { label: 'Framework', color: '#f59e0b', bias: 16 },
  conceptual_evolution: { label: 'Evolution', color: '#c084fc', bias: 16 },
};

const PERIOD_RANGES: Record<string, [number, number]> = {
  Presocratic: [-600, -450],
  'Classical Greek': [-450, -323],
  'Hellenistic Greek': [-323, -31],
  'Roman Republican': [-146, -27],
  'Roman Imperial': [-27, 300],
  Patristic: [150, 450],
  'Late Antiquity': [300, 600],
};

const PERIOD_COLORS: Record<string, string> = {
  Presocratic: '#7dd3fc',
  'Classical Greek': '#fde68a',
  'Hellenistic Greek': '#fda4af',
  'Roman Republican': '#c4b5fd',
  'Roman Imperial': '#5eead4',
  Patristic: '#fb7185',
  'Late Antiquity': '#f97316',
  Unspecified: '#94a3b8',
};

const PALETTE = [
  '#4cc9f0',
  '#f72585',
  '#f4d35e',
  '#06d6a0',
  '#f97316',
  '#818cf8',
  '#2ec4b6',
  '#fb7185',
  '#22c55e',
  '#a78bfa',
  '#38bdf8',
  '#f59e0b',
  '#14b8a6',
  '#e879f9',
  '#84cc16',
  '#f87171',
];

const RELATION_META: Array<{ match: RegExp; category: string; weight: number; color: string }> = [
  { match: /(influ|respond|critic|refut|support|attacks?|oppos|agrees?)/i, category: 'Argumentation', weight: 4.8, color: '#fb7185' },
  { match: /(author|part_of|contains|translation|cites?|cited|mentions?|witness|testifies?)/i, category: 'Textual', weight: 3.6, color: '#7dd3fc' },
  { match: /(evidenc|ground|source|quote|passage|attests?)/i, category: 'Evidence', weight: 4.2, color: '#f4d35e' },
  { match: /(school|member|belongs|tradition|success|teacher|student)/i, category: 'Affiliation', weight: 3.2, color: '#2ec4b6' },
  { match: /(same_as|alias|instance|type_of|subclass|equivalent)/i, category: 'Identity', weight: 2.4, color: '#c084fc' },
];

const DEFAULT_SIMULATION_CONTROLS: SimulationControls = {
  decay: 4300,
  gravity: 0.18,
  center: 0.02,
  repulsion: 1.34,
  theta: 1.08,
  linkSpring: 1,
  linkDistance: 22,
  mouseRepulsion: 3.2,
  friction: 0.9,
  impulse: 0.56,
};

const SIMULATION_PRESETS: Array<{
  id: string;
  label: string;
  description: string;
  controls: Partial<SimulationControls>;
}> = [
  {
    id: 'constellation',
    label: 'Constellation',
    description: 'Balanced layout for day-to-day exploration.',
    controls: {},
  },
  {
    id: 'debate',
    label: 'Debate',
    description: 'Tighter arguments and sharper communities.',
    controls: {
      repulsion: 1.42,
      linkSpring: 1.3,
      linkDistance: 16,
      friction: 0.9,
      gravity: 0.18,
      impulse: 0.54,
    },
  },
  {
    id: 'nebula',
    label: 'Nebula',
    description: 'More breathing room between conceptual worlds.',
    controls: {
      repulsion: 1.68,
      linkSpring: 0.92,
      linkDistance: 22,
      gravity: 0.14,
      center: 0.03,
      impulse: 0.62,
    },
  },
];

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max);
}

function formatSliderValue(value: number, digits = value >= 10 ? 0 : 2) {
  return value.toLocaleString(undefined, {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits === 0 ? 0 : Math.min(digits, 2),
  });
}

function normalizeNodeType(type?: string | null) {
  if (!type) return 'unknown';
  return type.trim().toLowerCase().replace(/[\s-]+/g, '_');
}

function formatRelationLabel(relation: string) {
  return relation
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function compactLabel(label: string, maxWords = 3) {
  return label.split(/\s+/).slice(0, maxWords).join(' ');
}

function trimPreview(text?: string, maxLength = 170) {
  if (!text) return '';
  const collapsed = text.replace(/\s+/g, ' ').trim();
  if (collapsed.length <= maxLength) return collapsed;
  return `${collapsed.slice(0, maxLength - 1).trimEnd()}…`;
}

function countSourceEntries(value: unknown) {
  if (Array.isArray(value)) return value.length;
  if (typeof value === 'string' && value.trim()) return 1;
  return 0;
}

function inferNodeYear(node: RawKGNode) {
  if (typeof node.year === 'number') {
    return node.year;
  }

  const dateCandidates = [
    node.dates,
    node.approximate_dates,
    node.floruit,
    node.birth,
    node.death,
    node.date,
  ];

  for (const candidate of dateCandidates) {
    if (!candidate) continue;
    const match = String(candidate).match(/-?\d+/);
    if (!match) continue;
    let year = Number.parseInt(match[0], 10);
    if (Number.isNaN(year)) continue;
    if (String(candidate).toLowerCase().includes('bce') && year > 0) {
      year = -year;
    }
    return year;
  }

  const periodRange = node.period ? PERIOD_RANGES[node.period] : undefined;
  return periodRange?.[0] ?? 0;
}

function formatYear(year?: number | null) {
  if (year === null || year === undefined || Number.isNaN(year)) return 'Unplaced';
  if (year < 0) return `${Math.abs(year)} BCE`;
  if (year === 0) return '0';
  return `${year} CE`;
}

function buildPaletteMap(values: string[], palette = PALETTE, fallback = '#94a3b8') {
  const entries = values.filter(Boolean);
  const result: Record<string, string> = {};

  entries.forEach((value, index) => {
    result[value] = palette[index % palette.length] ?? fallback;
  });

  return result;
}

function collectLegendItems(nodes: FlatGraphNode[], accessor: keyof FlatGraphNode, colorMap: Record<string, string>) {
  const counts = new Map<string, number>();

  nodes.forEach((node) => {
    const key = String(node[accessor] ?? '');
    if (!key) return;
    counts.set(key, (counts.get(key) ?? 0) + 1);
  });

  return Array.from(counts.entries())
    .map(([label, count]) => ({
      label,
      color: colorMap[label] ?? '#94a3b8',
      count,
    }))
    .sort((left, right) => right.count - left.count || left.label.localeCompare(right.label));
}

function scoreSearchNode(node: FlatGraphNode, rawQuery: string) {
  const query = rawQuery.trim().toLowerCase();
  if (!query) {
    return node.importance + node.degree * 2;
  }

  const label = node.label.toLowerCase();
  const searchHint = node.searchHint.toLowerCase();
  const community = node.communityLabel.toLowerCase();
  const type = node.typeLabel.toLowerCase();
  const period = node.periodLabel.toLowerCase();
  const school = node.schoolGroup.toLowerCase();
  const greek = node.greekTerm.toLowerCase();
  const latin = node.latinTerm.toLowerCase();

  let score = 0;

  if (label === query) score += 150;
  if (label.startsWith(query)) score += 110;
  if (label.includes(query)) score += 90;
  if (greek.startsWith(query) || latin.startsWith(query)) score += 80;
  if (greek.includes(query) || latin.includes(query)) score += 55;
  if (school.includes(query)) score += 44;
  if (period.includes(query)) score += 38;
  if (type.includes(query)) score += 34;
  if (community.includes(query)) score += 26;
  if (searchHint.includes(query)) score += 20;

  if (score === 0) return -1;

  return score + node.importance / 30 + node.degree / 5;
}

function getSearchResults(nodes: FlatGraphNode[], query: string, limit = 10) {
  const ranked = nodes
    .map((node) => ({
      node,
      score: scoreSearchNode(node, query),
    }))
    .filter((entry) => entry.score >= 0)
    .sort((left, right) => right.score - left.score)
    .slice(0, limit);

  return ranked.map((entry) => entry.node);
}

function classifyRelation(relation?: string | null) {
  const safeRelation = relation?.trim() || 'related_to';

  for (const meta of RELATION_META) {
    if (meta.match.test(safeRelation)) {
      return {
        category: meta.category,
        color: meta.color,
        weight: meta.weight,
      };
    }
  }

  return {
    category: 'Structural',
    color: '#94a3b8',
    weight: 2.8,
  };
}

function importanceColor(value: unknown, min: number, max: number) {
  const numeric = typeof value === 'number' ? value : Number(value);
  const denominator = Math.max(max - min, 1);
  const normalized = clamp((numeric - min) / denominator, 0, 1);
  const hue = 210 - normalized * 175;
  const lightness = 68 - normalized * 22;
  return `hsl(${hue} 90% ${lightness}% / 0.95)`;
}

function escapeHtml(value: string) {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function buildPopupContent(node: FlatGraphNode | null) {
  if (!node) return '';

  return `
    <div style="min-width: 260px; max-width: 320px; color: #f8fafc; background: linear-gradient(180deg, rgba(12,18,32,0.98) 0%, rgba(3,7,18,0.98) 100%); border: 1px solid rgba(148,163,184,0.18); border-radius: 18px; box-shadow: 0 18px 60px rgba(2,6,23,0.55); overflow: hidden;">
      <div style="padding: 12px 14px; background: linear-gradient(90deg, rgba(34,211,238,0.16) 0%, rgba(251,191,36,0.12) 100%); border-bottom: 1px solid rgba(148,163,184,0.14);">
        <div style="font-size: 11px; letter-spacing: 0.08em; text-transform: uppercase; color: rgba(191,219,254,0.9);">${escapeHtml(node.typeLabel)}</div>
        <div style="font-size: 15px; font-weight: 700; line-height: 1.2; margin-top: 4px;">${escapeHtml(node.label)}</div>
      </div>
      <div style="padding: 12px 14px;">
        <div style="font-size: 12px; color: rgba(226,232,240,0.82); line-height: 1.45;">${escapeHtml(node.descriptionPreview || 'Mapped in the EleutherIA knowledge graph.')}</div>
        <div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; margin-top: 12px;">
          <div style="padding: 8px 10px; background: rgba(15,23,42,0.72); border: 1px solid rgba(148,163,184,0.12); border-radius: 12px;">
            <div style="font-size: 10px; text-transform: uppercase; letter-spacing: 0.08em; color: rgba(148,163,184,0.85);">Community</div>
            <div style="font-size: 12px; margin-top: 4px;">${escapeHtml(node.communityLabel)}</div>
          </div>
          <div style="padding: 8px 10px; background: rgba(15,23,42,0.72); border: 1px solid rgba(148,163,184,0.12); border-radius: 12px;">
            <div style="font-size: 10px; text-transform: uppercase; letter-spacing: 0.08em; color: rgba(148,163,184,0.85);">Degree</div>
            <div style="font-size: 12px; margin-top: 4px;">${node.degree}</div>
          </div>
          <div style="padding: 8px 10px; background: rgba(15,23,42,0.72); border: 1px solid rgba(148,163,184,0.12); border-radius: 12px;">
            <div style="font-size: 10px; text-transform: uppercase; letter-spacing: 0.08em; color: rgba(148,163,184,0.85);">Period</div>
            <div style="font-size: 12px; margin-top: 4px;">${escapeHtml(node.periodLabel)}</div>
          </div>
          <div style="padding: 8px 10px; background: rgba(15,23,42,0.72); border: 1px solid rgba(148,163,184,0.12); border-radius: 12px;">
            <div style="font-size: 10px; text-transform: uppercase; letter-spacing: 0.08em; color: rgba(148,163,184,0.85);">Sources</div>
            <div style="font-size: 12px; margin-top: 4px;">${node.sourceCount}</div>
          </div>
        </div>
      </div>
    </div>
  `;
}

function extractCommunityAssignments(communityData: CytoscapeData | null) {
  const assignments = new Map<string, string>();
  const colors = new Map<string, string>();

  if (!communityData) {
    return { assignments, colors };
  }

  const metaColors = new Map<string, string>();
  const communities = communityData.meta?.community?.communities ?? [];
  communities.forEach((community) => {
    metaColors.set(String(community.id), community.color);
  });

  const rawElements = communityData.elements as CytoscapeData['elements'] | Array<{ data?: Record<string, unknown>; group?: string }> | undefined;
  let nodeElements: Array<{ data?: Record<string, unknown> }> = [];

  if (Array.isArray(rawElements)) {
    nodeElements = rawElements.filter((element) => {
      const source = element.data?.source;
      const target = element.data?.target;
      return !source && !target && (element.group === 'nodes' || !element.group);
    });
  } else {
    nodeElements = rawElements?.nodes ?? [];
  }

  nodeElements.forEach((element) => {
    const data = element.data ?? {};
    const id = typeof data.id === 'string' ? data.id : undefined;
    const communityKey =
      data.communityId ??
      data.community_id ??
      data.community ??
      data.communityIndex;

    if (!id || communityKey === undefined || communityKey === null) {
      return;
    }

    const normalizedKey = String(communityKey);
    assignments.set(id, normalizedKey);

    const color =
      (typeof data.communityColor === 'string' && data.communityColor) ||
      (typeof data.community_color === 'string' && data.community_color) ||
      (typeof data.color === 'string' && data.color) ||
      metaColors.get(normalizedKey);

    if (color) {
      colors.set(normalizedKey, color);
    }
  });

  return { assignments, colors };
}

async function buildGraphModel(
  rawNodes: RawKGNode[],
  rawEdges: KGEdge[],
  communityData: CytoscapeData | null,
) {
  const nodeIds = new Set(rawNodes.map((node) => node.id));
  const validEdges = rawEdges.filter((edge) => nodeIds.has(edge.source) && nodeIds.has(edge.target));
  const degreeMap = new Map<string, number>();
  const relationDiversity = new Map<string, Set<string>>();

  validEdges.forEach((edge) => {
    degreeMap.set(edge.source, (degreeMap.get(edge.source) ?? 0) + 1);
    degreeMap.set(edge.target, (degreeMap.get(edge.target) ?? 0) + 1);

    if (!relationDiversity.has(edge.source)) relationDiversity.set(edge.source, new Set());
    if (!relationDiversity.has(edge.target)) relationDiversity.set(edge.target, new Set());
    relationDiversity.get(edge.source)?.add(edge.relation ?? 'related_to');
    relationDiversity.get(edge.target)?.add(edge.relation ?? 'related_to');
  });

  const { assignments: communityAssignments, colors: extractedCommunityColors } = extractCommunityAssignments(communityData);
  const nodesById = new Map<string, RawKGNode>();

  rawNodes.forEach((node) => {
    nodesById.set(node.id, node);
  });

  const firstPassNodes = rawNodes.map((node) => {
    const typeKey = normalizeNodeType(node.type);
    const typeMeta = TYPE_META[typeKey] ?? {
      label: typeKey.replace(/_/g, ' ').replace(/\b\w/g, (letter) => letter.toUpperCase()),
      color: '#94a3b8',
      bias: 8,
    };
    const periodLabel = node.period || 'Unspecified';
    const schoolGroup = node.school || 'Unattached';
    const degree = degreeMap.get(node.id) ?? 0;
    const diversity = relationDiversity.get(node.id)?.size ?? 0;
    const ancientSourceCount = countSourceEntries(node.ancient_sources);
    const modernSourceCount =
      countSourceEntries(node.modern_scholarship) +
      countSourceEntries(node.metadata?.modern_scholarship);
    const sourceCount = ancientSourceCount + modernSourceCount;
    const importance = Math.round(
      Math.sqrt(degree + 1) * 15 +
      sourceCount * 5 +
      diversity * 3 +
      typeMeta.bias,
    );

    const communityKey =
      communityAssignments.get(node.id) ??
      (schoolGroup !== 'Unattached' ? `school:${schoolGroup}` : `type:${typeKey}`);

    return {
      id: node.id,
      label: node.label || node.id,
      typeKey,
      typeLabel: typeMeta.label,
      periodLabel,
      schoolGroup,
      datesLabel: node.dates || node.approximate_dates || node.floruit || '',
      year: inferNodeYear(node),
      degree,
      relationDiversity: diversity,
      ancientSourceCount,
      modernSourceCount,
      sourceCount,
      importance,
      labelWeight: Math.max(importance, degree * 8, sourceCount * 10, 12),
      communityKey,
      communityLabel: communityKey,
      descriptionPreview: trimPreview(node.description),
      greekTerm: node.greek_term || '',
      latinTerm: node.latin_term || '',
      searchHint: [
        node.label,
        node.greek_term,
        node.latin_term,
        node.english_term,
        node.school,
        node.period,
      ].filter(Boolean).join(' • '),
    } satisfies FlatGraphNode;
  });

  const communityBuckets = new Map<string, FlatGraphNode[]>();
  firstPassNodes.forEach((node) => {
    if (!communityBuckets.has(node.communityKey)) {
      communityBuckets.set(node.communityKey, []);
    }
    communityBuckets.get(node.communityKey)?.push(node);
  });

  const orderedCommunities = Array.from(communityBuckets.entries())
    .sort((left, right) => right[1].length - left[1].length)
    .map(([key]) => key);

  const communityColorMap: Record<string, string> = {};
  const communityLabelMap = new Map<string, string>();

  orderedCommunities.forEach((communityKey, index) => {
    const nodes = communityBuckets.get(communityKey) ?? [];
    const leader = [...nodes].sort((left, right) => right.importance - left.importance)[0];
    const extractedKey = communityKey.replace(/^school:|^type:/, '');
    const label =
      leader
        ? `${compactLabel(leader.label)} cluster`
        : communityKey.startsWith('school:')
          ? `${compactLabel(extractedKey)} cluster`
          : `Community ${index + 1}`;

    communityLabelMap.set(communityKey, label);
    communityColorMap[label] =
      extractedCommunityColors.get(communityKey) ??
      extractedCommunityColors.get(extractedKey) ??
      PALETTE[index % PALETTE.length] ??
      '#94a3b8';
  });

  const flatNodes = firstPassNodes.map((node) => ({
    ...node,
    communityLabel: communityLabelMap.get(node.communityKey) ?? node.communityKey,
  }));

  const flatNodesById = new Map(flatNodes.map((node) => [node.id, node]));

  const typeColorMap = Object.fromEntries(
    Object.entries(TYPE_META).map(([, meta]) => [meta.label, meta.color]),
  );
  const schoolColorMap = buildPaletteMap(
    Array.from(new Set(flatNodes.map((node) => node.schoolGroup))).sort(),
  );
  const periodColorMap = Object.fromEntries(
    Array.from(new Set(flatNodes.map((node) => node.periodLabel))).map((period) => [
      period,
      PERIOD_COLORS[period] ?? '#94a3b8',
    ]),
  );

  const flatLinks = validEdges.map((edge) => {
    const relationLabel = formatRelationLabel(edge.relation || 'related_to');
    const meta = classifyRelation(edge.relation);

    return {
      id: edge.id || `${edge.source}:${edge.target}:${edge.relation || 'related_to'}`,
      source: edge.source,
      target: edge.target,
      relation: edge.relation || 'related_to',
      relationCategory: meta.category,
      relationLabel,
      strength: meta.weight,
      directed: true,
    } satisfies FlatGraphLink;
  });

  const relationshipsByNodeId = new Map<string, RelatedNode[]>();
  flatNodes.forEach((node) => {
    relationshipsByNodeId.set(node.id, []);
  });

  flatLinks.forEach((edge) => {
    const sourceNode = flatNodesById.get(edge.source);
    const targetNode = flatNodesById.get(edge.target);

    if (!sourceNode || !targetNode) {
      return;
    }

    relationshipsByNodeId.get(edge.source)?.push({
      id: edge.target,
      label: targetNode.label,
      type: targetNode.typeKey,
      relation: edge.relation,
      direction: 'outgoing',
    });

    relationshipsByNodeId.get(edge.target)?.push({
      id: edge.source,
      label: sourceNode.label,
      type: sourceNode.typeKey,
      relation: edge.relation,
      direction: 'incoming',
    });
  });

  relationshipsByNodeId.forEach((relationships, nodeId) => {
    relationships.sort((left, right) => {
      const leftNode = flatNodesById.get(left.id);
      const rightNode = flatNodesById.get(right.id);
      return (rightNode?.importance ?? 0) - (leftNode?.importance ?? 0);
    });
    relationshipsByNodeId.set(nodeId, relationships.slice(0, 28));
  });

  const minImportance = Math.min(...flatNodes.map((node) => node.importance));
  const maxImportance = Math.max(...flatNodes.map((node) => node.importance));
  const leadersByCommunity = orderedCommunities
    .map((communityKey) =>
      [...(communityBuckets.get(communityKey) ?? [])].sort((left, right) => right.importance - left.importance)[0],
    )
    .filter(Boolean)
    .map((leader) => leader.id);
  const topStops = Array.from(new Set([
    ...leadersByCommunity.slice(0, 8),
    ...[...flatNodes].sort((left, right) => right.importance - left.importance).slice(0, 12).map((node) => node.id),
  ]));

  const prepared = await prepareCosmographData(
    {
      points: {
        pointIdBy: 'id',
        pointLabelBy: 'label',
        pointLabelWeightBy: 'labelWeight',
        pointSizeBy: 'importance',
        pointClusterBy: 'communityLabel',
        pointIncludeColumns: ['*'],
        pointDefaultColor: '#7dd3fc',
        pointDefaultSize: 4,
      },
      links: {
        linkSourceBy: 'source',
        linkTargetsBy: ['target'],
        linkWidthBy: 'strength',
        linkIncludeColumns: ['*'],
        linkDefaultWidth: 1,
        linkDefaultColor: 'rgba(148, 163, 184, 0.28)',
      },
    },
    flatNodes,
    flatLinks,
  );

  return {
    points: prepared?.points,
    links: prepared?.links,
    cosmographConfig: prepared?.cosmographConfig ?? {},
    flatNodes,
    flatLinks,
    nodesById,
    flatNodesById,
    relationshipsByNodeId,
    typeColorMap,
    schoolColorMap,
    periodColorMap,
    communityColorMap,
    communityOrder: orderedCommunities.map((communityKey) => communityLabelMap.get(communityKey) ?? communityKey),
    topStops,
    totalNodes: flatNodes.length,
    totalEdges: flatLinks.length,
    minImportance,
    maxImportance,
  } satisfies GraphModel;
}

function ControlButton({
  active = false,
  icon,
  label,
  onClick,
  disabled = false,
}: {
  active?: boolean;
  icon: import('react').ReactNode;
  label: string;
  onClick: () => void;
  disabled?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={[
        'inline-flex items-center gap-2 rounded-full border px-3 py-2 text-xs font-medium transition-all',
        disabled
          ? 'cursor-not-allowed border-white/5 bg-white/5 text-white/30'
          : active
            ? 'border-cyan-300/40 bg-cyan-300/12 text-cyan-50 shadow-[0_12px_34px_rgba(34,211,238,0.12)]'
            : 'border-white/10 bg-slate-950/60 text-slate-200 hover:border-white/20 hover:bg-slate-900/80',
      ].join(' ')}
    >
      {icon}
      <span>{label}</span>
    </button>
  );
}

function SegmentedGroup<T extends string>({
  title,
  value,
  options,
  onChange,
}: {
  title: string;
  value: T;
  options: Array<{ value: T; label: string }>;
  onChange: (nextValue: T) => void;
}) {
  return (
    <div className="space-y-2">
      <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">
        {title}
      </p>
      <div className="flex flex-wrap gap-2">
        {options.map((option) => (
          <button
            key={option.value}
            type="button"
            onClick={() => onChange(option.value)}
            className={[
              'rounded-full border px-3 py-1.5 text-xs transition-colors',
              value === option.value
                ? 'border-amber-300/45 bg-amber-200/12 text-amber-100'
                : 'border-white/10 bg-slate-950/60 text-slate-300 hover:border-white/20',
            ].join(' ')}
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  );
}

function SimulationSlider({
  label,
  hint,
  value,
  min,
  max,
  step,
  onChange,
  formatter,
  compact = false,
}: {
  label: string;
  hint?: string;
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (nextValue: number) => void;
  formatter?: (value: number) => string;
  compact?: boolean;
}) {
  const valueLabel = formatter ? formatter(value) : formatSliderValue(value);
  const minLabel = formatter ? formatter(min) : formatSliderValue(min);
  const maxLabel = formatter ? formatter(max) : formatSliderValue(max);

  return (
    <label
      className={[
        'block rounded-[20px] border border-white/8 bg-[#040916]/80',
        compact ? 'px-3 py-3' : 'px-4 py-3.5',
      ].join(' ')}
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-white">
            {label}
          </p>
          {hint && !compact && (
            <p className="mt-1 text-[11px] leading-5 text-slate-400">
              {hint}
            </p>
          )}
        </div>
        <span className="rounded-full border border-cyan-300/20 bg-cyan-300/10 px-2.5 py-1 text-[11px] font-medium text-cyan-100">
          {valueLabel}
        </span>
      </div>

      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
        className="mt-3 h-2 w-full cursor-pointer accent-cyan-300"
      />

      <div className="mt-2 flex items-center justify-between text-[10px] uppercase tracking-[0.14em] text-slate-500">
        <span>{minLabel}</span>
        <span>{maxLabel}</span>
      </div>
    </label>
  );
}

export default function CosmographPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { nodeId } = useParams();
  const graphRef = useRef<CosmographRef>(undefined);

  const [graphModel, setGraphModel] = useState<GraphModel | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [graphReady, setGraphReady] = useState(false);

  const [colorMode, setColorMode] = useState<ColorMode>('community');
  const [sizeMode, setSizeMode] = useState<SizeMode>('importance');
  const [clusterMode, setClusterMode] = useState<ClusterMode>('community');
  const [showLabels, setShowLabels] = useState(true);
  const [showClusterLabels, setShowClusterLabels] = useState(true);
  const [showCurvedLinks, setShowCurvedLinks] = useState(true);
  const [showArrows, setShowArrows] = useState(false);
  const [selectionMode, setSelectionMode] = useState<SelectionMode>(null);
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [visibleNodeCount, setVisibleNodeCount] = useState(0);
  const [selectedPointIndices, setSelectedPointIndices] = useState<number[]>([]);
  const [selectedLinkCount, setSelectedLinkCount] = useState(0);
  const [pinnedNodeIds, setPinnedNodeIds] = useState<string[]>([]);
  const [simulationRunning, setSimulationRunning] = useState(true);
  const [simulationControls, setSimulationControls] = useState<SimulationControls>(DEFAULT_SIMULATION_CONTROLS);
  const [mobilePanelOpen, setMobilePanelOpen] = useState(false);
  const [tourCursor, setTourCursor] = useState(0);
  const [timelineSelectionLabel, setTimelineSelectionLabel] = useState<string | null>(null);
  const [timelineHoverLabel, setTimelineHoverLabel] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchCursor, setSearchCursor] = useState(0);

  const deferredHoveredNodeId = useDeferredValue(hoveredNodeId);
  const deferredSearchQuery = useDeferredValue(searchQuery);

  const selectedNode = selectedNodeId && graphModel ? graphModel.nodesById.get(selectedNodeId) ?? null : null;
  const selectedFlatNode =
    selectedNodeId && graphModel
      ? graphModel.flatNodesById.get(selectedNodeId) ?? null
      : null;
  const selectedRelationships =
    selectedNodeId && graphModel
      ? graphModel.relationshipsByNodeId.get(selectedNodeId) ?? []
      : [];

  const popupNode =
    deferredHoveredNodeId && graphModel
      ? graphModel.flatNodesById.get(deferredHoveredNodeId) ?? null
      : null;
  const searchResults = useMemo(
    () => (graphModel ? getSearchResults(graphModel.flatNodes, deferredSearchQuery, 10) : []),
    [graphModel, deferredSearchQuery],
  );
  const selectedNeighborhoodSummary = useMemo(() => {
    if (!graphModel || !selectedFlatNode) {
      return null;
    }

    const relationCounts = new Map<string, number>();
    const typeCounts = new Map<string, number>();
    let incoming = 0;
    let outgoing = 0;

    selectedRelationships.forEach((relationship) => {
      const relationLabel = formatRelationLabel(relationship.relation);
      relationCounts.set(relationLabel, (relationCounts.get(relationLabel) ?? 0) + 1);

      const relatedType = graphModel.flatNodesById.get(relationship.id)?.typeLabel ?? relationship.type;
      typeCounts.set(relatedType, (typeCounts.get(relatedType) ?? 0) + 1);

      if (relationship.direction === 'incoming') {
        incoming += 1;
      } else {
        outgoing += 1;
      }
    });

    const topRelations = Array.from(relationCounts.entries())
      .sort((left, right) => right[1] - left[1] || left[0].localeCompare(right[0]))
      .slice(0, 4);
    const topTypes = Array.from(typeCounts.entries())
      .sort((left, right) => right[1] - left[1] || left[0].localeCompare(right[0]))
      .slice(0, 3);

    return {
      neighborCount: selectedFlatNode.degree,
      linkCount: Math.max(selectedLinkCount, selectedFlatNode.degree),
      incoming,
      outgoing,
      topRelations,
      topTypes,
    };
  }, [graphModel, selectedFlatNode, selectedLinkCount, selectedRelationships]);

  useEffect(() => {
    setSearchCursor(0);
  }, [deferredSearchQuery]);

  useEffect(() => {
    if (!searchResults.length) {
      setSearchCursor(0);
      return;
    }

    setSearchCursor((current) => clamp(current, 0, searchResults.length - 1));
  }, [searchResults]);

  useEffect(() => {
    let cancelled = false;

    async function loadGraph() {
      setLoading(true);
      setError(null);

      try {
        const [nodesResponse, edgesResponse, communityData] = await Promise.all([
          apiClient.getNodes(),
          apiClient.getEdges() as Promise<EdgeApiResponse>,
          apiClient.getCytoscapeData({ algorithm: 'semantic' }).catch(() => null),
        ]);

        if (cancelled) return;

        const nodes = (nodesResponse?.nodes ?? []) as RawKGNode[];
        const edgePayload = edgesResponse;
        const edges = Array.isArray(edgePayload) ? edgePayload : edgePayload?.edges ?? [];
        const model = await buildGraphModel(nodes, edges, communityData);

        if (cancelled) return;

        setGraphModel(model);
        setVisibleNodeCount(model.totalNodes);
        setLoading(false);
      } catch (loadError) {
        if (cancelled) return;
        setLoading(false);
        setError(loadError instanceof Error ? loadError.message : 'Failed to load graph data.');
      }
    }

    void loadGraph();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!graphModel || !graphReady || !nodeId) {
      return;
    }

    if (selectedNodeId === nodeId) {
      return;
    }

    void focusNodeById(nodeId, { fitNeighborhood: false, pushRoute: false });
  }, [graphModel, graphReady, nodeId, selectedNodeId]);

  async function getPointIndexById(id: string) {
    if (!graphRef.current) return undefined;
    const indices = await graphRef.current.getPointIndicesByIds([id]);
    return indices?.[0];
  }

  async function focusNodeById(
    id: string,
    options?: {
      fitNeighborhood?: boolean;
      pushRoute?: boolean;
    },
  ) {
    if (!graphModel || !graphRef.current) return;

    const pointIndex = await getPointIndexById(id);
    if (pointIndex === undefined) return;

    const graph = graphRef.current;
    const connected = graph.getConnectedPointIndices(pointIndex) ?? [];
    const frame = options?.fitNeighborhood ? [pointIndex, ...connected.slice(0, 28)] : [pointIndex];

    graph.selectPoint(pointIndex, false, true);
    graph.setFocusedPoint(pointIndex);

    if (frame.length > 1 && options?.fitNeighborhood) {
      graph.fitViewByIndices(frame, 650, 80);
    } else {
      graph.zoomToPoint(pointIndex, 650, 2.5, true);
    }

    startTransition(() => {
      setSelectedNodeId(id);
      setHoveredNodeId(null);
    });

    if (options?.pushRoute !== false) {
      navigate(`/visualizer/${id}`, { replace: true });
    }
  }

  async function focusNeighborhood() {
    if (!selectedNodeId || !graphRef.current) return;
    const index = await getPointIndexById(selectedNodeId);
    if (index === undefined) return;
    const connected = graphRef.current.getConnectedPointIndices(index) ?? [];
    const frame = [index, ...connected.slice(0, 36)];

    graphRef.current.selectPoints(frame, false);
    graphRef.current.fitViewByIndices(frame, 700, 96);
  }

  async function togglePinnedSelection() {
    if (!graphModel || !graphRef.current) return;
    const activeSelection = graphRef.current.getSelectedPointIndices() ?? [];
    if (activeSelection.length === 0) return;

    const selectedIds = activeSelection
      .map((index) => graphModel.flatNodes[index]?.id)
      .filter(Boolean) as string[];

    const allSelectedAlreadyPinned = selectedIds.every((id) => pinnedNodeIds.includes(id));
    const nextPinnedIds = allSelectedAlreadyPinned
      ? pinnedNodeIds.filter((id) => !selectedIds.includes(id))
      : Array.from(new Set([...pinnedNodeIds, ...selectedIds]));

    const nextIndices = (
      await graphRef.current.getPointIndicesByIds(nextPinnedIds)
    )?.filter((value): value is number => typeof value === 'number') ?? [];

    graphRef.current.setPinnedPoints(nextIndices);
    setPinnedNodeIds(nextPinnedIds);
  }

  function clearSelection() {
    if (graphRef.current) {
      graphRef.current.unselectAllPoints();
      graphRef.current.setFocusedPoint(undefined);
      if (selectionMode === 'rect') graphRef.current.deactivateRectSelection();
      if (selectionMode === 'polygon') graphRef.current.deactivatePolygonalSelection();
    }

    setSelectionMode(null);
    setSelectedPointIndices([]);
    setSelectedLinkCount(0);
    setSelectedNodeId(null);
    setHoveredNodeId(null);
    navigate('/visualizer', { replace: true });
  }

  function fitView() {
    graphRef.current?.fitView(550, 72);
  }

  function toggleSimulation() {
    if (!graphRef.current) return;

    if (simulationRunning) {
      graphRef.current.pause();
    } else {
      graphRef.current.unpause();
    }
  }

  function pulseSimulation(alpha = simulationControls.impulse) {
    graphRef.current?.start(alpha);
  }

  function setSimulationControl<Key extends keyof SimulationControls>(key: Key, value: SimulationControls[Key]) {
    const nextControls = {
      ...simulationControls,
      [key]: value,
    };

    setSimulationControls(nextControls);

    if (graphReady && simulationRunning) {
      pulseSimulation(nextControls.impulse);
    }
  }

  function applySimulationPreset(presetId: string) {
    const preset = SIMULATION_PRESETS.find((item) => item.id === presetId);
    if (!preset) return;

    const nextControls = {
      ...DEFAULT_SIMULATION_CONTROLS,
      ...preset.controls,
    };

    setSimulationControls(nextControls);
    if (graphReady) {
      pulseSimulation(nextControls.impulse);
    }
  }

  function resetSimulationControls() {
    setSimulationControls(DEFAULT_SIMULATION_CONTROLS);
    if (graphReady) {
      pulseSimulation(DEFAULT_SIMULATION_CONTROLS.impulse);
    }
  }

  function toggleRectSelection() {
    if (!graphRef.current) return;

    if (selectionMode === 'rect') {
      graphRef.current.deactivateRectSelection();
      setSelectionMode(null);
      return;
    }

    graphRef.current.deactivatePolygonalSelection();
    graphRef.current.activateRectSelection();
    setSelectionMode('rect');
  }

  function togglePolygonSelection() {
    if (!graphRef.current) return;

    if (selectionMode === 'polygon') {
      graphRef.current.deactivatePolygonalSelection();
      setSelectionMode(null);
      return;
    }

    graphRef.current.deactivateRectSelection();
    graphRef.current.activatePolygonalSelection();
    setSelectionMode('polygon');
  }

  function exportScreenshot() {
    graphRef.current?.captureScreenshot('eleutheria-cosmograph', 2);
  }

  async function surpriseMe() {
    if (!graphModel?.topStops.length) return;
    const nextId = graphModel.topStops[tourCursor % graphModel.topStops.length];
    setTourCursor((current) => current + 1);
    await focusNodeById(nextId, { fitNeighborhood: true });
  }

  const pinnedSet = new Set(pinnedNodeIds);
  const selectedPointCount = selectedPointIndices.length;

  const colorAccessorMap: Record<ColorMode, string> = {
    community: 'communityLabel',
    type: 'typeLabel',
    school: 'schoolGroup',
    period: 'periodLabel',
    importance: 'importance',
  };

  const sizeAccessorMap: Record<SizeMode, string> = {
    importance: 'importance',
    degree: 'degree',
    sources: 'sourceCount',
  };

  const clusterAccessorMap: Record<Exclude<ClusterMode, 'none'>, string> = {
    community: 'communityLabel',
    type: 'typeLabel',
    school: 'schoolGroup',
    period: 'periodLabel',
  };

  const activeColorAccessor = colorAccessorMap[colorMode];
  const activeSizeAccessor = sizeAccessorMap[sizeMode];
  const activeClusterAccessor = clusterMode === 'none' ? undefined : clusterAccessorMap[clusterMode];
  const activeColorMap =
    colorMode === 'community'
      ? graphModel?.communityColorMap
      : colorMode === 'type'
        ? graphModel?.typeColorMap
        : colorMode === 'school'
          ? graphModel?.schoolColorMap
          : colorMode === 'period'
            ? graphModel?.periodColorMap
            : undefined;
  const categoricalLegendItems = useMemo(() => {
    if (!graphModel || colorMode === 'importance' || !activeColorMap) {
      return [] as LegendItem[];
    }

    const accessor: keyof FlatGraphNode =
      colorMode === 'community'
        ? 'communityLabel'
        : colorMode === 'type'
          ? 'typeLabel'
          : colorMode === 'school'
            ? 'schoolGroup'
            : 'periodLabel';

    return collectLegendItems(graphModel.flatNodes, accessor, activeColorMap);
  }, [activeColorMap, colorMode, graphModel]);
  const colorLegendTitle =
    colorMode === 'community'
      ? 'Semantic clusters'
      : colorMode === 'type'
        ? 'Node types'
        : colorMode === 'school'
          ? 'Schools'
          : colorMode === 'period'
            ? 'Periods'
            : 'Influence pulse';
  const sizeLegendTitle =
    sizeMode === 'importance'
      ? 'Node importance'
      : sizeMode === 'degree'
        ? 'Connection degree'
        : 'Source density';

  const dynamicGraphConfig: Partial<CosmographConfig> | undefined = graphModel
    ? {
        ...graphModel.cosmographConfig,
        points: graphModel.points,
        links: graphModel.links,
        backgroundColor: '#020617',
        renderHoveredPointRing: true,
        hoveredPointRingColor: '#fde68a',
        focusedPointRingColor: '#22d3ee',
        pointDefaultColor: '#7dd3fc',
        pointDefaultSize: 4,
        pointGreyoutOpacity: 0.12,
        linkDefaultColor: 'rgba(148,163,184,0.22)',
        linkGreyoutOpacity: 0.04,
        linkDefaultWidth: 1,
        hoveredLinkColor: '#f8fafc',
        hoveredLinkWidthIncrease: 1.5,
        linkVisibilityDistanceRange: [32, 110],
        linkVisibilityMinTransparency: 0.08,
        curvedLinks: showCurvedLinks,
        linkDefaultArrows: showArrows,
        enableZoom: true,
        enableDrag: true,
        enableRightClickRepulsion: true,
        enableSimulationDuringZoom: false,
        fitViewOnInit: true,
        fitViewDelay: 360,
        fitViewDuration: 500,
        fitViewPadding: 0.14,
        randomSeed: 'eleutheria-cosmograph-v2',
        spaceSize: 5400,
        pointSamplingDistance: 152,
        pointColorBy: activeColorAccessor,
        pointColorByMap: activeColorMap,
        pointColorByFn:
          colorMode === 'importance'
            ? (value: unknown) => importanceColor(value, graphModel.minImportance, graphModel.maxImportance)
            : undefined,
        pointSizeBy: activeSizeAccessor,
        pointSizeRange: [2.6, 14],
        pointClusterBy: activeClusterAccessor,
        showLabels,
        showDynamicLabels: showLabels,
        showDynamicLabelsLimit: 36,
        showTopLabels: showLabels,
        showTopLabelsLimit: 30,
        showFocusedPointLabel: true,
        showHoveredPointLabel: true,
        showSelectedLabels: true,
        selectedPointLabelsLimit: 120,
        showUnselectedPointLabels: !selectedNodeId,
        showClusterLabels: showLabels && showClusterLabels && Boolean(activeClusterAccessor),
        usePointColorStrategyForClusterLabels: Boolean(activeClusterAccessor) && activeColorAccessor === activeClusterAccessor,
        pointLabelBy: 'label',
        pointLabelWeightBy: 'labelWeight',
        showLabelsFor: [
          ...(selectedNodeId ? [selectedNodeId] : []),
          ...pinnedNodeIds,
        ],
        pointLabelFontSize: 13,
        clusterLabelFontSize: 18,
        labelMargin: 8,
        labelPadding: [8, 5.5, 8, 5.5],
        pointLabelClassName: (_text, _index, pointId) => {
          const isPinned = pointId ? pinnedSet.has(pointId) : false;
          const isFocused = pointId === selectedNodeId;

          return [
            `background: ${isFocused ? 'rgba(251,191,36,0.18)' : 'rgba(7,14,28,0.76)'}`,
            `border: 1px solid ${isFocused ? 'rgba(251,191,36,0.4)' : isPinned ? 'rgba(34,211,238,0.28)' : 'rgba(148,163,184,0.16)'}`,
            `color: ${isFocused ? '#fef3c7' : isPinned ? '#cffafe' : '#f8fafc'}`,
            `box-shadow: ${isFocused ? '0 14px 36px rgba(251,191,36,0.16)' : '0 10px 30px rgba(2,6,23,0.38)'}`,
            'backdrop-filter: blur(12px)',
            'border-radius: 999px',
            `font-weight: ${isFocused || isPinned ? 700 : 520}`,
            'letter-spacing: 0.02em',
          ].join('; ');
        },
        hoveredPointLabelClassName: () => [
          'background: rgba(8,15,28,0.96)',
          'border: 1px solid rgba(34,211,238,0.3)',
          'color: #f8fafc',
          'box-shadow: 0 18px 48px rgba(15,23,42,0.45)',
          'backdrop-filter: blur(14px)',
          'border-radius: 14px',
          'font-weight: 600',
        ].join('; '),
        clusterLabelClassName: () => [
          'background: rgba(15,23,42,0.88)',
          'border: 1px solid rgba(148,163,184,0.14)',
          'color: #e2e8f0',
          'backdrop-filter: blur(14px)',
          'border-radius: 999px',
          'font-weight: 600',
          'letter-spacing: 0.04em',
          'text-transform: uppercase',
          'box-shadow: 0 14px 38px rgba(2,6,23,0.32)',
        ].join('; '),
        selectPointOnClick: true,
        focusPointOnClick: true,
        selectPointOnLabelClick: true,
        focusPointOnLabelClick: true,
        resetSelectionOnEmptyCanvasClick: true,
        simulationDecay: simulationControls.decay,
        simulationGravity: simulationControls.gravity,
        simulationCenter: simulationControls.center,
        simulationRepulsion: simulationControls.repulsion,
        simulationRepulsionTheta: simulationControls.theta,
        simulationLinkSpring: simulationControls.linkSpring,
        simulationLinkDistance: simulationControls.linkDistance,
        simulationLinkDistRandomVariationRange: [1.06, 1.18],
        simulationCluster: clusterMode === 'none' ? 0 : 0.18,
        simulationRepulsionFromMouse: simulationControls.mouseRepulsion,
        simulationFriction: simulationControls.friction,
        simulationImpulse: simulationControls.impulse,
      }
    : undefined;

  return (
    <div className="fixed inset-x-0 bottom-0 top-12 overflow-hidden bg-[#020617]">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_18%_20%,rgba(34,211,238,0.12),transparent_34%),radial-gradient(circle_at_78%_18%,rgba(251,191,36,0.12),transparent_30%),radial-gradient(circle_at_50%_85%,rgba(244,114,182,0.12),transparent_28%)]" />
        <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(2,6,23,0.18)_0%,rgba(2,6,23,0.58)_100%)]" />
      </div>

      {loading && (
        <div className="absolute inset-0 z-40 flex items-center justify-center bg-slate-950/78 backdrop-blur-xl">
          <div className="mx-6 max-w-md rounded-[28px] border border-white/10 bg-slate-950/75 px-8 py-7 text-center shadow-[0_24px_80px_rgba(2,6,23,0.55)]">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full border border-cyan-300/20 bg-cyan-300/10">
              <Network className="h-8 w-8 text-cyan-200" />
            </div>
            <p className="mt-5 text-sm font-semibold uppercase tracking-[0.24em] text-cyan-200/80">
              Cosmograph 2.x
            </p>
            <h2 className="mt-2 text-2xl font-semibold text-white">
              Building the field
            </h2>
            <p className="mt-3 text-sm leading-6 text-slate-300">
              Preparing the EleutherIA knowledge graph for GPU layout, semantic communities, interactive filters, and cinematic exploration.
            </p>
          </div>
        </div>
      )}

      {!loading && error && (
        <div className="absolute inset-0 z-40 flex items-center justify-center bg-slate-950/80 px-6 backdrop-blur-xl">
          <div className="max-w-lg rounded-[28px] border border-rose-300/20 bg-slate-950/78 px-8 py-7 shadow-[0_24px_80px_rgba(2,6,23,0.55)]">
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-rose-200/80">
              Graph load failed
            </p>
            <h2 className="mt-2 text-2xl font-semibold text-white">
              The observatory is offline
            </h2>
            <p className="mt-3 text-sm leading-6 text-slate-300">
              {error}
            </p>
            <button
              type="button"
              onClick={() => window.location.reload()}
              className="mt-6 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-white/10"
            >
              <RefreshCw className="h-4 w-4" />
              Reload visualizer
            </button>
          </div>
        </div>
      )}

      {graphModel && dynamicGraphConfig && (
        <CosmographProvider>
          <Cosmograph
            {...dynamicGraphConfig}
            ref={graphRef}
            onMount={() => setGraphReady(true)}
            onSimulationStart={() => setSimulationRunning(true)}
            onSimulationUnpause={() => setSimulationRunning(true)}
            onSimulationPause={() => setSimulationRunning(false)}
            onSimulationEnd={() => setSimulationRunning(false)}
            onPointClick={(index) => {
              const clickedNode = graphModel.flatNodes[index];
              if (!clickedNode) return;
              void focusNodeById(clickedNode.id, { fitNeighborhood: false });
            }}
            onLabelClick={(_index, id) => {
              void focusNodeById(id, { fitNeighborhood: false });
            }}
            onBackgroundClick={() => {
              clearSelection();
            }}
            onPointMouseOver={(index) => {
              const hovered = graphModel.flatNodes[index];
              setHoveredNodeId(hovered?.id ?? null);
            }}
            onPointMouseOut={() => {
              setHoveredNodeId(null);
            }}
            onRectSelected={(_selection, pointIndices) => {
              setSelectionMode(null);
              if (pointIndices?.length === 1) {
                const onlyNode = graphModel.flatNodes[pointIndices[0]];
                if (onlyNode) {
                  void focusNodeById(onlyNode.id, { fitNeighborhood: false });
                }
              }
            }}
            onPolygonSelected={() => {
              setSelectionMode(null);
            }}
            onPointsFiltered={(filteredPoints, pointIndices, linkIndices) => {
              const rowCount = Number((filteredPoints as { numRows?: number }).numRows ?? graphModel.totalNodes);
              setVisibleNodeCount(rowCount);
              setSelectedPointIndices(pointIndices ?? []);
              setSelectedLinkCount(linkIndices?.length ?? 0);
            }}
            style={{ width: '100%', height: '100%' }}
          />

          <CosmographPopup
            bindTo={popupNode?.id}
            content={buildPopupContent(popupNode)}
            placement="top"
            hidden={!popupNode || popupNode.id === selectedNodeId}
          />

          <div className="absolute left-4 top-4 z-30 flex items-center gap-2 md:hidden">
            <button
              type="button"
              onClick={() => setMobilePanelOpen((open) => !open)}
              className="inline-flex h-12 w-12 items-center justify-center rounded-full border border-white/10 bg-slate-950/75 text-white shadow-[0_14px_40px_rgba(2,6,23,0.4)] backdrop-blur-xl"
              aria-label={mobilePanelOpen ? 'Close graph controls' : 'Open graph controls'}
            >
              {mobilePanelOpen ? <X className="h-5 w-5" /> : <ChevronRight className="h-5 w-5" />}
            </button>
          </div>

          <div
            className={[
              'absolute left-4 top-4 z-30 w-[min(26rem,calc(100%-2rem))] overflow-hidden rounded-[30px] border border-white/10 bg-slate-950/72 shadow-[0_24px_80px_rgba(2,6,23,0.45)] backdrop-blur-2xl transition-transform duration-300',
              mobilePanelOpen ? 'translate-x-0' : '-translate-x-[calc(100%+1rem)] md:translate-x-0',
            ].join(' ')}
          >
            <div className="max-h-[calc(100vh-8rem)] overflow-y-auto px-5 pb-6 pt-5">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-cyan-200/80">
                    {t('graphPage.badge', 'Cosmograph 2.x')}
                  </p>
                  <h1 className="mt-2 text-2xl font-semibold text-white">
                    {t('graphPage.title', 'EleutherIA Atlas')}
                  </h1>
                  <p className="mt-2 max-w-sm text-sm leading-6 text-slate-300">
                    {t(
                      'graphPage.subtitle',
                      'Semantic communities, temporal filtering, search-driven focus, lasso selection, and publication-grade screenshots over the ancient free will knowledge graph.',
                    )}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setMobilePanelOpen(false)}
                  className="mt-1 hidden h-10 w-10 items-center justify-center rounded-full border border-white/10 bg-white/5 text-slate-300 transition-colors hover:bg-white/10 md:hidden"
                  aria-label="Close graph controls"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

              <div className="mt-5 grid grid-cols-2 gap-3">
                <StatCard label="Visible" value={visibleNodeCount.toLocaleString()} accent="cyan" />
                <StatCard label="Edges" value={graphModel.totalEdges.toLocaleString()} accent="amber" />
                <StatCard label="Selected" value={selectedPointCount.toLocaleString()} accent="rose" />
                <StatCard label="Pinned" value={pinnedNodeIds.length.toLocaleString()} accent="emerald" />
              </div>

              {selectedFlatNode && selectedNeighborhoodSummary && (
                <div className="mt-5 rounded-[24px] border border-cyan-300/12 bg-[linear-gradient(180deg,rgba(6,16,32,0.95)_0%,rgba(2,6,23,0.92)_100%)] p-4 shadow-[0_18px_50px_rgba(14,165,233,0.12)]">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-cyan-100/80">
                        <Focus className="h-3.5 w-3.5" />
                        Neighborhood spotlight
                      </div>
                      <p className="mt-2 text-sm font-semibold text-white">
                        {selectedFlatNode.label}
                      </p>
                      <p className="mt-1 text-xs leading-5 text-slate-400">
                        Click now selects the node plus its first-degree neighborhood and the links tying that local structure together.
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        void focusNeighborhood();
                      }}
                      className="inline-flex shrink-0 items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-3 py-2 text-xs font-medium text-slate-100 transition-colors hover:border-cyan-300/30 hover:bg-cyan-300/[0.08]"
                    >
                      <Route className="h-3.5 w-3.5" />
                      Fit neighborhood
                    </button>
                  </div>

                  <div className="mt-4 grid grid-cols-2 gap-3">
                    <StatCard label="Neighbors" value={selectedNeighborhoodSummary.neighborCount.toLocaleString()} accent="cyan" />
                    <StatCard label="Links lit" value={selectedNeighborhoodSummary.linkCount.toLocaleString()} accent="amber" />
                    <StatCard label="Incoming" value={selectedNeighborhoodSummary.incoming.toLocaleString()} accent="rose" />
                    <StatCard label="Outgoing" value={selectedNeighborhoodSummary.outgoing.toLocaleString()} accent="emerald" />
                  </div>

                  <div className="mt-4 grid gap-3 md:grid-cols-2">
                    <div className="rounded-[18px] border border-white/8 bg-white/[0.03] p-3">
                      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">
                        Dominant relations
                      </p>
                      <div className="mt-3 flex flex-wrap gap-2">
                        {selectedNeighborhoodSummary.topRelations.map(([label, count]) => (
                          <span
                            key={label}
                            className="rounded-full border border-white/10 bg-white/[0.04] px-2.5 py-1 text-xs text-slate-200"
                          >
                            {label} · {count}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div className="rounded-[18px] border border-white/8 bg-white/[0.03] p-3">
                      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">
                        Connected node types
                      </p>
                      <div className="mt-3 flex flex-wrap gap-2">
                        {selectedNeighborhoodSummary.topTypes.map(([label, count]) => (
                          <span
                            key={label}
                            className="rounded-full border border-white/10 bg-white/[0.04] px-2.5 py-1 text-xs text-slate-200"
                          >
                            {label} · {count}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <div className="mt-5 rounded-[24px] border border-white/8 bg-[linear-gradient(180deg,rgba(5,10,22,0.96)_0%,rgba(2,6,23,0.88)_100%)] p-4 shadow-[0_18px_50px_rgba(2,6,23,0.24)]">
                <GraphSearchPanel
                  query={searchQuery}
                  activeIndex={searchCursor}
                  results={searchResults}
                  selectedNodeId={selectedNodeId}
                  typeColorMap={graphModel.typeColorMap}
                  onQueryChange={setSearchQuery}
                  onMoveCursor={(direction) => {
                    if (!searchResults.length) return;
                    setSearchCursor((current) => {
                      const next = current + direction;
                      return clamp(next, 0, searchResults.length - 1);
                    });
                  }}
                  onSelect={(node) => {
                    setSearchQuery(node.label);
                    void focusNodeById(node.id, { fitNeighborhood: false });
                  }}
                  onClear={() => {
                    setSearchQuery('');
                    setSearchCursor(0);
                  }}
                />
              </div>

              <div className="mt-5 space-y-5">
                <SegmentedGroup
                  title="Color field"
                  value={colorMode}
                  onChange={setColorMode}
                  options={[
                    { value: 'community', label: 'Community' },
                    { value: 'type', label: 'Type' },
                    { value: 'school', label: 'School' },
                    { value: 'period', label: 'Period' },
                    { value: 'importance', label: 'Pulse' },
                  ]}
                />

                <SegmentedGroup
                  title="Size field"
                  value={sizeMode}
                  onChange={setSizeMode}
                  options={[
                    { value: 'importance', label: 'Importance' },
                    { value: 'degree', label: 'Degree' },
                    { value: 'sources', label: 'Sources' },
                  ]}
                />

                <SegmentedGroup
                  title="Cluster field"
                  value={clusterMode}
                  onChange={setClusterMode}
                  options={[
                    { value: 'community', label: 'Community' },
                    { value: 'type', label: 'Type' },
                    { value: 'school', label: 'School' },
                    { value: 'period', label: 'Period' },
                    { value: 'none', label: 'None' },
                  ]}
                />
              </div>

              <div className="mt-5 flex flex-wrap gap-2">
                <ControlButton
                  active={showLabels}
                  icon={<Sparkles className="h-3.5 w-3.5" />}
                  label="Labels"
                  onClick={() => setShowLabels((value) => !value)}
                />
                <ControlButton
                  active={showClusterLabels}
                  icon={<Layers3 className="h-3.5 w-3.5" />}
                  label="Cluster labels"
                  onClick={() => setShowClusterLabels((value) => !value)}
                  disabled={clusterMode === 'none'}
                />
                <ControlButton
                  active={showCurvedLinks}
                  icon={<Spline className="h-3.5 w-3.5" />}
                  label="Curved links"
                  onClick={() => setShowCurvedLinks((value) => !value)}
                />
                <ControlButton
                  active={showArrows}
                  icon={<Route className="h-3.5 w-3.5" />}
                  label="Arrows"
                  onClick={() => setShowArrows((value) => !value)}
                />
              </div>

              <div className="mt-5 grid grid-cols-2 gap-2">
                <ControlButton
                  icon={<Focus className="h-3.5 w-3.5" />}
                  label="Fit view"
                  onClick={fitView}
                />
                <ControlButton
                  icon={simulationRunning ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />}
                  label={simulationRunning ? 'Pause' : 'Resume'}
                  onClick={toggleSimulation}
                />
                <ControlButton
                  active={selectionMode === 'rect'}
                  icon={<Filter className="h-3.5 w-3.5" />}
                  label="Rect select"
                  onClick={toggleRectSelection}
                />
                <ControlButton
                  active={selectionMode === 'polygon'}
                  icon={<MapIcon className="h-3.5 w-3.5" />}
                  label="Lasso select"
                  onClick={togglePolygonSelection}
                />
                <ControlButton
                  icon={<Camera className="h-3.5 w-3.5" />}
                  label="Screenshot"
                  onClick={exportScreenshot}
                />
                <ControlButton
                  icon={<Sparkles className="h-3.5 w-3.5" />}
                  label="Atlas tour"
                  onClick={() => {
                    void surpriseMe();
                  }}
                />
                <ControlButton
                  icon={<Route className="h-3.5 w-3.5" />}
                  label="Neighborhood"
                  onClick={() => {
                    void focusNeighborhood();
                  }}
                  disabled={!selectedNodeId}
                />
                <ControlButton
                  icon={<Pin className="h-3.5 w-3.5" />}
                  label="Pin selection"
                  onClick={() => {
                    void togglePinnedSelection();
                  }}
                  disabled={selectedPointCount === 0}
                />
              </div>

              <div className="mt-5 rounded-[22px] border border-cyan-300/12 bg-[linear-gradient(180deg,rgba(8,15,30,0.94)_0%,rgba(2,6,23,0.94)_100%)] p-4 shadow-[0_18px_50px_rgba(8,47,73,0.18)]">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-cyan-100/80">
                      <Network className="h-3.5 w-3.5" />
                      Simulation lab
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-300">
                      Live layout sliders inspired by the official Cosmograph simulation controls example.
                    </p>
                  </div>
                  <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-medium text-slate-200">
                    {simulationRunning ? 'Live' : 'Paused'}
                  </span>
                </div>

                <div className="mt-4 grid gap-2 sm:grid-cols-3">
                  {SIMULATION_PRESETS.map((preset) => (
                    <button
                      key={preset.id}
                      type="button"
                      onClick={() => applySimulationPreset(preset.id)}
                      className="rounded-[18px] border border-white/10 bg-white/[0.04] px-3 py-3 text-left transition-colors hover:border-cyan-300/30 hover:bg-cyan-300/[0.08]"
                    >
                      <p className="text-sm font-semibold text-white">
                        {preset.label}
                      </p>
                      <p className="mt-1 text-[11px] leading-5 text-slate-400">
                        {preset.description}
                      </p>
                    </button>
                  ))}
                </div>

                <div className="mt-4 flex flex-wrap gap-2">
                  <ControlButton
                    icon={<Play className="h-3.5 w-3.5" />}
                    label="Reheat"
                    onClick={() => {
                      pulseSimulation();
                    }}
                  />
                  <ControlButton
                    icon={<RefreshCw className="h-3.5 w-3.5" />}
                    label="Reset sliders"
                    onClick={resetSimulationControls}
                  />
                </div>

                <div className="mt-4 space-y-3">
                  <SimulationSlider
                    label="Repulsion"
                    hint="How strongly nodes push each other apart."
                    value={simulationControls.repulsion}
                    min={0.3}
                    max={2.2}
                    step={0.02}
                    onChange={(value) => setSimulationControl('repulsion', value)}
                  />
                  <SimulationSlider
                    label="Link spring"
                    hint="How tightly linked nodes pull together."
                    value={simulationControls.linkSpring}
                    min={0.3}
                    max={1.8}
                    step={0.02}
                    onChange={(value) => setSimulationControl('linkSpring', value)}
                  />
                  <SimulationSlider
                    label="Link distance"
                    hint="Minimum spacing kept between connected nodes."
                    value={simulationControls.linkDistance}
                    min={8}
                    max={32}
                    step={1}
                    onChange={(value) => setSimulationControl('linkDistance', value)}
                    formatter={(value) => `${formatSliderValue(value)} px`}
                  />
                  <SimulationSlider
                    label="Gravity"
                    hint="Global pull that keeps the field cohesive."
                    value={simulationControls.gravity}
                    min={0}
                    max={0.5}
                    step={0.01}
                    onChange={(value) => setSimulationControl('gravity', value)}
                  />
                  <SimulationSlider
                    label="Friction"
                    hint="How quickly motion settles after reheating."
                    value={simulationControls.friction}
                    min={0.7}
                    max={0.98}
                    step={0.01}
                    onChange={(value) => setSimulationControl('friction', value)}
                  />
                  <SimulationSlider
                    label="Decay"
                    hint="How long the simulation keeps cooling."
                    value={simulationControls.decay}
                    min={1200}
                    max={9000}
                    step={100}
                    onChange={(value) => setSimulationControl('decay', value)}
                    formatter={(value) => formatSliderValue(value)}
                  />
                </div>

                <div className="mt-3 grid gap-3 md:grid-cols-2">
                  <SimulationSlider
                    label="Center"
                    value={simulationControls.center}
                    min={0}
                    max={0.2}
                    step={0.01}
                    onChange={(value) => setSimulationControl('center', value)}
                    compact
                  />
                  <SimulationSlider
                    label="Theta"
                    value={simulationControls.theta}
                    min={0.6}
                    max={1.4}
                    step={0.01}
                    onChange={(value) => setSimulationControl('theta', value)}
                    compact
                  />
                  <SimulationSlider
                    label="Mouse force"
                    value={simulationControls.mouseRepulsion}
                    min={0}
                    max={5}
                    step={0.1}
                    onChange={(value) => setSimulationControl('mouseRepulsion', value)}
                    compact
                  />
                  <SimulationSlider
                    label="Reheat impulse"
                    value={simulationControls.impulse}
                    min={0.1}
                    max={1}
                    step={0.02}
                    onChange={(value) => setSimulationControl('impulse', value)}
                    compact
                  />
                </div>
              </div>

              <div className="mt-5 rounded-[22px] border border-white/8 bg-slate-950/70 p-4">
                <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
                  <Filter className="h-3.5 w-3.5" />
                  Filter bars
                </div>
                <p className="mt-2 text-xs leading-5 text-slate-400">
                  Click bars to isolate schools or node kinds. These filters compose with the timeline and search.
                </p>

                <div className="mt-4 space-y-4">
                  <div>
                    <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">
                      Node types
                    </p>
                    <CosmographBars
                      accessor="typeLabel"
                      id="visualizer-type-bars"
                      expanded
                      maxDisplayedItems={8}
                      selectOnClick
                      highlightSelectedData
                      showSortingBlock={false}
                      showSearch={false}
                      moveFilteredToTop
                      showTotalWhenFiltered
                      style={{ height: 180 }}
                    />
                  </div>

                  <div className="hidden lg:block">
                    <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">
                      Schools
                    </p>
                    <CosmographBars
                      accessor="schoolGroup"
                      id="visualizer-school-bars"
                      expanded
                      maxDisplayedItems={8}
                      selectOnClick
                      highlightSelectedData
                      showSortingBlock={false}
                      showSearch={false}
                      moveFilteredToTop
                      showTotalWhenFiltered
                      style={{ height: 220 }}
                    />
                  </div>
                </div>
              </div>

              <div className="mt-5 rounded-[22px] border border-white/8 bg-slate-950/70 p-4">
                <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
                  <Info className="h-3.5 w-3.5" />
                  Field notes
                </div>
                <div className="mt-3 space-y-2 text-xs leading-5 text-slate-300">
                  <p>Left click a node to open its dossier. Use Atlas Tour to jump between community leaders.</p>
                  <p>Hold right click to repel the field and open hidden channels inside dense clusters.</p>
                  <p>Rect select and lasso select persist across search, bars, and time filtering.</p>
                </div>
              </div>
            </div>
          </div>

          <div className="absolute right-4 top-4 z-30 flex flex-col items-end gap-3">
            <div className="rounded-full border border-white/10 bg-slate-950/75 p-1 shadow-[0_14px_40px_rgba(2,6,23,0.4)] backdrop-blur-xl">
              <ModeSwitcher />
            </div>

            <div className="rounded-[24px] border border-white/10 bg-slate-950/72 px-4 py-3 text-right shadow-[0_24px_80px_rgba(2,6,23,0.45)] backdrop-blur-2xl">
              <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-400">
                Observatory
              </p>
              <div className="mt-2 flex items-center justify-end gap-2 text-white">
                <span className="rounded-full border border-cyan-300/20 bg-cyan-300/10 px-3 py-1 text-xs font-medium text-cyan-100">
                  {visibleNodeCount.toLocaleString()} / {graphModel.totalNodes.toLocaleString()} visible
                </span>
                <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-medium text-slate-200">
                  {selectedPointCount} selected
                </span>
              </div>
              {(timelineSelectionLabel || timelineHoverLabel) && (
                <p className="mt-2 text-xs text-slate-300">
                  {timelineSelectionLabel || timelineHoverLabel}
                </p>
              )}
            </div>
          </div>

          <div className="absolute bottom-4 right-4 z-30 hidden w-[23rem] max-w-[calc(100vw-2rem)] flex-col gap-3 lg:flex">
            <div className="rounded-[24px] border border-white/10 bg-slate-950/72 p-5 shadow-[0_24px_80px_rgba(2,6,23,0.45)] backdrop-blur-2xl">
              <div className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
                <Palette className="h-3.5 w-3.5" />
                Legend
              </div>
              {colorMode === 'importance' ? (
                <CosmographRangeColorLegend
                  steps={9}
                  showSublabels
                  minSubLabel="quiet"
                  maxSubLabel="central"
                  labelResolver={() => 'Influence pulse'}
                />
              ) : (
                <DiscreteLegend
                  label={colorLegendTitle}
                  items={categoricalLegendItems}
                  maxVisibleItems={7}
                />
              )}
              <div className="mt-5 border-t border-white/8 pt-4">
                <CosmographSizeLegend
                  useQuantiles={sizeMode !== 'degree'}
                  labelResolver={() => sizeLegendTitle}
                />
              </div>
            </div>
          </div>

          <div className="absolute bottom-4 left-1/2 z-30 hidden w-[min(58rem,calc(100%-2rem))] -translate-x-1/2 md:block">
            <div className="rounded-[28px] border border-white/10 bg-slate-950/72 px-4 pb-3 pt-4 shadow-[0_24px_80px_rgba(2,6,23,0.45)] backdrop-blur-2xl">
              <div className="mb-3 flex items-center justify-between gap-4">
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-400">
                    Chronology scrubber
                  </p>
                  <p className="mt-1 text-xs text-slate-300">
                    Brush across centuries to isolate debates, or press play to animate the graph through time.
                  </p>
                </div>
                {(timelineSelectionLabel || timelineHoverLabel) && (
                  <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-200">
                    {timelineSelectionLabel || timelineHoverLabel}
                  </span>
                )}
              </div>

              <CosmographTimeline
                accessor="year"
                id="visualizer-year-timeline"
                barCount={90}
                stickySelection
                highlightSelectedData
                showAnimationControls
                animationSpeed={45}
                formatter={(value) => formatYear(typeof value === 'number' ? value : value.getFullYear())}
                onSelection={(selection) => {
                  if (!selection) {
                    setTimelineSelectionLabel(null);
                    return;
                  }

                  const [from, to] = selection;
                  const fromYear = typeof from === 'number' ? from : from.getFullYear();
                  const toYear = typeof to === 'number' ? to : to.getFullYear();
                  setTimelineSelectionLabel(`${formatYear(fromYear)} → ${formatYear(toYear)}`);
                }}
                onBarHover={(bar) => {
                  const start = typeof bar.rangeStart === 'number' ? bar.rangeStart : bar.rangeStart.getFullYear();
                  const end = typeof bar.rangeEnd === 'number' ? bar.rangeEnd : bar.rangeEnd.getFullYear();
                  setTimelineHoverLabel(`${formatYear(start)} → ${formatYear(end)} · ${bar.count.toLocaleString()} nodes`);
                }}
                style={{ height: 128 }}
              />
            </div>
          </div>

          <NodeDetailPanel
            node={selectedNode}
            onClose={clearSelection}
            relationships={selectedRelationships}
            onNavigateToNode={(nextNodeId) => {
              void focusNodeById(nextNodeId, { fitNeighborhood: false });
            }}
          />
        </CosmographProvider>
      )}

      <div className="md:hidden">
        <BottomTabNav />
      </div>
    </div>
  );
}

function StatCard({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
  accent: 'cyan' | 'amber' | 'rose' | 'emerald';
}) {
  const accentClass =
    accent === 'cyan'
      ? 'from-cyan-300/18 to-cyan-500/5 text-cyan-100'
      : accent === 'amber'
        ? 'from-amber-300/18 to-amber-500/5 text-amber-100'
        : accent === 'rose'
          ? 'from-rose-300/18 to-rose-500/5 text-rose-100'
          : 'from-emerald-300/18 to-emerald-500/5 text-emerald-100';

  return (
    <div className={`rounded-[22px] border border-white/8 bg-gradient-to-br ${accentClass} px-4 py-3`}>
      <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">
        {label}
      </p>
      <p className="mt-1 text-xl font-semibold">
        {value}
      </p>
    </div>
  );
}

function GraphSearchPanel({
  query,
  activeIndex,
  results,
  selectedNodeId,
  typeColorMap,
  onQueryChange,
  onMoveCursor,
  onSelect,
  onClear,
}: {
  query: string;
  activeIndex: number;
  results: FlatGraphNode[];
  selectedNodeId: string | null;
  typeColorMap: Record<string, string>;
  onQueryChange: (nextQuery: string) => void;
  onMoveCursor: (direction: -1 | 1) => void;
  onSelect: (node: FlatGraphNode) => void;
  onClear: () => void;
}) {
  const hasQuery = query.trim().length > 0;
  const activeResult = results[activeIndex] ?? results[0] ?? null;

  return (
    <div>
      <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
        <Search className="h-3.5 w-3.5" />
        Search the graph
      </div>
      <p className="mt-2 text-xs leading-5 text-slate-400">
        Jump to a thinker, concept, Greek term, school, or semantic cluster. Use the arrow keys and press Enter to focus instantly.
      </p>

      <div className="mt-3 rounded-[20px] border border-white/10 bg-[#040916]/88 p-2 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]">
        <div className="flex items-center gap-3 rounded-[16px] border border-white/8 bg-[#020617] px-4 py-3">
          <Search className="h-4 w-4 shrink-0 text-slate-500" />
          <input
            type="search"
            value={query}
            onChange={(event) => onQueryChange(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'ArrowDown') {
                event.preventDefault();
                onMoveCursor(1);
                return;
              }

              if (event.key === 'ArrowUp') {
                event.preventDefault();
                onMoveCursor(-1);
                return;
              }

              if (event.key === 'Enter' && activeResult) {
                event.preventDefault();
                onSelect(activeResult);
                return;
              }

              if (event.key === 'Escape') {
                event.preventDefault();
                if (query) {
                  onClear();
                } else {
                  event.currentTarget.blur();
                }
              }
            }}
            placeholder="Philosopher, concept, Greek term, school..."
            className="min-w-0 flex-1 bg-transparent text-sm text-white outline-none placeholder:text-slate-500"
          />
          <span className="hidden rounded-full border border-white/10 bg-white/[0.04] px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-400 sm:inline-flex">
            Enter
          </span>
          {query && (
            <button
              type="button"
              onClick={onClear}
              className="inline-flex h-7 w-7 items-center justify-center rounded-full border border-white/10 bg-white/[0.04] text-slate-400 transition-colors hover:border-white/20 hover:text-white"
              aria-label="Clear graph search"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>
      </div>

      <div className="mt-3 overflow-hidden rounded-[20px] border border-white/8 bg-[#020617]/92">
        <div className="flex items-center justify-between gap-3 border-b border-white/8 px-4 py-3 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
          <span>{hasQuery ? 'Best matches' : 'Top launch nodes'}</span>
          <span>{results.length ? `${results.length} shown` : '0 shown'}</span>
        </div>

        {results.length ? (
          <div className="max-h-[22rem] space-y-2 overflow-y-auto p-2">
            {results.map((node, index) => {
              const isActive = index === activeIndex;
              const isSelected = node.id === selectedNodeId;
              const metaLine = [
                node.typeLabel,
                node.periodLabel !== 'Unspecified' ? node.periodLabel : null,
                node.schoolGroup !== 'Unattached' ? node.schoolGroup : null,
              ].filter(Boolean).join(' · ');

              return (
                <button
                  key={node.id}
                  type="button"
                  onMouseDown={(event) => event.preventDefault()}
                  onClick={() => onSelect(node)}
                  className={[
                    'flex w-full items-start gap-3 rounded-[16px] border px-3 py-3 text-left transition-all',
                    isSelected
                      ? 'border-amber-300/30 bg-amber-300/[0.08] shadow-[0_12px_32px_rgba(251,191,36,0.08)]'
                      : isActive
                        ? 'border-cyan-300/25 bg-cyan-300/[0.08] shadow-[0_12px_32px_rgba(34,211,238,0.08)]'
                        : 'border-white/6 bg-white/[0.03] hover:border-white/14 hover:bg-white/[0.05]',
                  ].join(' ')}
                >
                  <span
                    className="mt-1 h-2.5 w-2.5 shrink-0 rounded-full border border-white/10"
                    style={{ backgroundColor: typeColorMap[node.typeLabel] ?? '#7dd3fc' }}
                  />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <p className="truncate text-sm font-semibold text-white" title={node.label}>
                        {node.label}
                      </p>
                      {isSelected && (
                        <span className="rounded-full border border-amber-300/20 bg-amber-300/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.16em] text-amber-100">
                          Open
                        </span>
                      )}
                    </div>
                    <p className="mt-1 truncate text-[11px] uppercase tracking-[0.18em] text-slate-500">
                      {metaLine || 'Graph node'}
                    </p>
                    <p className="mt-1 truncate text-xs text-slate-400" title={node.communityLabel}>
                      {node.communityLabel}
                    </p>
                  </div>
                  <ChevronRight className="mt-0.5 h-4 w-4 shrink-0 text-slate-500" />
                </button>
              );
            })}
          </div>
        ) : (
          <div className="px-4 py-5 text-sm text-slate-400">
            No nodes match that query.
          </div>
        )}
      </div>
    </div>
  );
}

function DiscreteLegend({
  label,
  items,
  maxVisibleItems = 7,
}: {
  label: string;
  items: LegendItem[];
  maxVisibleItems?: number;
}) {
  const visibleItems = items.slice(0, maxVisibleItems);
  const maxCount = visibleItems[0]?.count ?? 1;
  const hiddenCount = Math.max(items.length - visibleItems.length, 0);

  return (
    <div>
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-white">
            {label}
          </p>
          <p className="mt-1 text-[11px] leading-5 text-slate-400">
            Top visible groups by node count.
          </p>
        </div>
        <span className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-[11px] font-medium text-slate-200">
          {items.length.toLocaleString()} groups
        </span>
      </div>

      <div className="mt-4 space-y-2.5">
        {visibleItems.map((item) => {
          const width = Math.max((item.count / maxCount) * 100, 8);

          return (
            <div
              key={item.label}
              className="grid grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-3 rounded-[18px] border border-white/8 bg-white/[0.03] px-3 py-3"
            >
              <span
                className="h-3 w-3 rounded-full border border-white/10"
                style={{ backgroundColor: item.color }}
              />
              <div className="min-w-0">
                <p className="truncate text-sm text-slate-100" title={item.label}>
                  {item.label}
                </p>
                <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-white/6">
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${width}%`,
                      backgroundColor: item.color,
                    }}
                  />
                </div>
              </div>
              <span className="text-xs font-medium text-slate-400">
                {item.count.toLocaleString()}
              </span>
            </div>
          );
        })}
      </div>

      {hiddenCount > 0 && (
        <p className="mt-3 text-xs leading-5 text-slate-400">
          {hiddenCount.toLocaleString()} more groups hidden to keep the legend readable.
        </p>
      )}
    </div>
  );
}
