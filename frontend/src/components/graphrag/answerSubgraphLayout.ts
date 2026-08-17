import { getGraphTypeTheme } from './graphTheme';
import type { AnswerSubgraph, AnswerSubgraphNode } from '../../types';

/**
 * Deterministic radial layout for the curated per-answer subgraph.
 *
 * The curated map is not a DAG: it is one (rarely a few) controversy frames,
 * each holding a fan of scholarly positions, each position grounded in a
 * handful of contested passages, plus the KG nodes retrieval activated.
 * A rank layout degenerates on that shape — one frame with eighty positions
 * becomes an endless column. A radial fan is the natural reading:
 *
 *   centre        the question
 *   ring 1        the fault lines (frames), one angular sector each
 *   ring 2        the positions, fanned inside their frame's sector,
 *                 labelled radially so labels never collide
 *   beads         contested passages, strung outward along each position's ray
 *   corona        activated KG nodes, parked next to whatever they connect to
 *
 * Opposition between positions is drawn as an interior chord: the dialectic
 * is the point of the panel, so it must be the most visible ink on it.
 *
 * Everything here is pure arithmetic — no force simulation, no jitter, same
 * input always gives the same pixels.
 */

export const QUERY_NODE_ID = 'question';

const TAU = Math.PI * 2;
/** 12 o'clock. Angles grow clockwise in SVG's y-down space. */
const TOP_ANGLE = -Math.PI / 2;

const QUESTION_WIDTH = 200;
const QUESTION_HEIGHT = 60;
const FRAME_WIDTH = 178;
const FRAME_HEIGHT = 50;

const FRAME_RING_MIN = 158;
/** Clearance between the outer edge of a fault-line card and the position ring. */
const POSITION_RING_GAP = 56;
/** Arc length reserved per position on its ring — a label line plus leading. */
const POSITION_SLOT = 17;
const BEAD_STEP = 15;
const CORONA_GAP = 36;
const CORONA_SLOT = 15;

const POSITION_FONT = 11.5;
const CONTEXT_FONT = 9.5;
const PASSAGE_FONT = 8.5;

const POSITION_LABEL_MAX = 26;
const CONTEXT_LABEL_MAX = 22;
const PASSAGE_LABEL_MAX = 18;

export type SubgraphTier = 'question' | 'frame' | 'position' | 'passage' | 'context';
export type SubgraphEdgeKind =
  | 'entry'
  | 'containment'
  | 'opposition'
  | 'evidence'
  | 'context';

export interface RadialNode {
  id: string;
  ref?: string;
  /** Full label — hover title, never clipped. */
  label: string;
  /** Clipped label actually painted next to the node. */
  displayLabel: string;
  /** Wrapped label lines — boxed tiers only (question, frame). */
  lines: string[];
  detail?: string;
  type: string;
  tier: SubgraphTier;
  /** Centre of the box, or the dot, in layout space (question sits at 0,0). */
  x: number;
  y: number;
  radius: number;
  angle: number;
  angleDeg: number;
  /** Left half of the circle: the radial label is flipped so it reads inward. */
  flip: boolean;
  dotRadius: number;
  width: number;
  height: number;
  /** Distance from the dot at which the radial label starts. */
  labelOffset: number;
  fontSize: number;
  showLabel: boolean;
  /** 0 question, 1 frame, 2 position, 3 evidence/corona — drives the stagger. */
  depth: number;
  citationIndex?: number;
  isSource: boolean;
  color: string;
  tint: string;
  border: string;
  textColor: string;
  groupId: string;
}

export interface RadialEdge {
  id: string;
  source: string;
  target: string;
  relation: string;
  origin?: string;
  kind: SubgraphEdgeKind;
  path: string;
  color: string;
  midX: number;
  midY: number;
  depth: number;
}

export interface SubgraphRadialLayout {
  nodes: RadialNode[];
  edges: RadialEdge[];
  /** Faint guide circles: the frame ring and the position ring. */
  rings: number[];
  /** Angles (radians) separating frame sectors — drawn only for 2+ frames. */
  sectorBoundaries: number[];
  sectorRadius: number;
  bounds: { minX: number; minY: number; maxX: number; maxY: number };
}

/* ---------- text helpers ---------- */

export function truncateLabel(label: string, max: number): string {
  if (label.length <= max) return label;
  return `${label.slice(0, max - 1)}…`;
}

export function estimateTextWidth(text: string, fontSize: number): number {
  return text.length * fontSize * 0.53;
}

export function wrapLabel(text: string, maxChars: number, maxLines: number): string[] {
  const words = text.trim().split(/\s+/).filter(Boolean);
  if (words.length === 0) return [''];

  const lines: string[] = [];
  let current = '';
  let overflow = false;

  for (const word of words) {
    const candidate = current ? `${current} ${word}` : word;
    if (candidate.length <= maxChars) {
      current = candidate;
      continue;
    }
    if (current) {
      lines.push(current);
      current = '';
    }
    if (lines.length >= maxLines) {
      overflow = true;
      break;
    }
    current = word.length > maxChars ? word.slice(0, maxChars) : word;
  }

  if (!overflow && current) {
    if (lines.length < maxLines) lines.push(current);
    else overflow = true;
  }

  if (overflow && lines.length > 0) {
    const last = lines[lines.length - 1];
    lines[lines.length - 1] = truncateLabel(`${last}…`, maxChars);
  }

  return lines.length > 0 ? lines : [''];
}

/* ---------- geometry helpers ---------- */

function round(value: number): number {
  return Math.round(value * 100) / 100;
}

function polar(angle: number, radius: number): [number, number] {
  return [round(Math.cos(angle) * radius), round(Math.sin(angle) * radius)];
}

function normalizeDelta(delta: number): number {
  let value = delta;
  while (value > Math.PI) value -= TAU;
  while (value < -Math.PI) value += TAU;
  return value;
}

/** d3.linkRadial's curve, hand-rolled: control points sit at the mid radius. */
function radialLinkPath(
  a0: number,
  r0: number,
  a1: number,
  r1: number,
): { path: string; midX: number; midY: number } {
  const [x0, y0] = polar(a0, r0);
  const [x1, y1] = polar(a1, r1);
  const rm = (r0 + r1) / 2;
  const [cx0, cy0] = polar(a0, rm);
  const [cx1, cy1] = polar(a1, rm);
  return {
    path: `M${x0},${y0}C${cx0},${cy0} ${cx1},${cy1} ${x1},${y1}`,
    midX: round((x0 + 3 * cx0 + 3 * cx1 + x1) / 8),
    midY: round((y0 + 3 * cy0 + 3 * cy1 + y1) / 8),
  };
}

/**
 * Opposition: an arc hugging just inside the ring, whatever the angular
 * distance between the two positions. The control radius is solved so the
 * curve's own midpoint lands at `hug × r` — near neighbours dip barely at
 * all, antipodes bow across without ever crossing the fault-line cards.
 */
function chordPath(
  a0: number,
  r0: number,
  a1: number,
  r1: number,
  hug = 0.9,
): { path: string; midX: number; midY: number } {
  const [x0, y0] = polar(a0, r0);
  const [x1, y1] = polar(a1, r1);
  const delta = normalizeDelta(a1 - a0);
  const mid = a0 + delta / 2;
  const target = hug * Math.min(r0, r1);
  const pull = Math.max(
    0,
    2 * target - ((r0 + r1) / 2) * Math.cos(Math.abs(delta) / 2),
  );
  const [cx, cy] = polar(mid, pull);
  return {
    path: `M${x0},${y0}Q${cx},${cy} ${x1},${y1}`,
    midX: round(0.25 * x0 + 0.5 * cx + 0.25 * x1),
    midY: round(0.25 * y0 + 0.5 * cy + 0.25 * y1),
  };
}

/**
 * Push angles apart until each owns `minGap` radians, preserving order.
 * Deterministic: sorted by angle then id, single forward pass, backward pass
 * when the ring overflows, uniform spread when it cannot possibly fit.
 */
export function spreadAngles(
  items: ReadonlyArray<{ id: string; angle: number }>,
  minGap: number,
): Map<string, number> {
  const out = new Map<string, number>();
  if (items.length === 0) return out;

  const sorted = [...items].sort(
    (a, b) => a.angle - b.angle || (a.id < b.id ? -1 : a.id > b.id ? 1 : 0),
  );

  if (minGap * sorted.length >= TAU) {
    const step = TAU / sorted.length;
    sorted.forEach((item, index) => out.set(item.id, TOP_ANGLE + index * step));
    return out;
  }

  const angles = sorted.map((item) => item.angle);
  for (let i = 1; i < angles.length; i += 1) {
    if (angles[i] < angles[i - 1] + minGap) angles[i] = angles[i - 1] + minGap;
  }
  const span = angles[angles.length - 1] - angles[0];
  if (span > TAU - minGap) {
    for (let i = angles.length - 2; i >= 0; i -= 1) {
      if (angles[i] > angles[i + 1] - minGap) angles[i] = angles[i + 1] - minGap;
    }
  }
  sorted.forEach((item, index) => out.set(item.id, angles[index]));
  return out;
}

/* ---------- classification ---------- */

const FRAME_ORIGINS = new Set([
  'controversy_debate',
  'controversy_frame',
  'frame',
  'controversy',
]);
const POSITION_ORIGINS = new Set([
  'position_holder',
  'position',
  'scholar_position',
  'scholarly_position',
]);
const PASSAGE_ORIGINS = new Set(['contested_passage', 'passage']);
const FRAME_TYPES = new Set(['debate', 'controversy']);
const PASSAGE_TYPES = new Set(['passage', 'quote']);

const OPPOSITION_RELATION =
  /oppos|contradict|refut|contest|rival|against|contra|disagree|challeng|reject/i;
const EVIDENCE_RELATION = /ground|cite|quote|attest|evidence|support|passage|text/i;

export function tierOfSubgraphNode(node: AnswerSubgraphNode): SubgraphTier {
  const origin = node.origin?.toLowerCase();
  if (origin && FRAME_ORIGINS.has(origin)) return 'frame';
  if (origin && POSITION_ORIGINS.has(origin)) return 'position';
  if (origin && PASSAGE_ORIGINS.has(origin)) return 'passage';

  const type = node.type?.toLowerCase() ?? '';
  if (PASSAGE_TYPES.has(type)) return 'passage';
  if (!origin && FRAME_TYPES.has(type)) return 'frame';
  // A root with nowhere else to sit still deserves a slot on the debate ring.
  if (node.root) return 'position';
  return 'context';
}

function edgeKindOf(
  relation: string,
  sourceTier: SubgraphTier,
  targetTier: SubgraphTier,
): SubgraphEdgeKind {
  if (sourceTier === 'question' || targetTier === 'question') return 'entry';
  if (OPPOSITION_RELATION.test(relation)) return 'opposition';
  if (sourceTier === 'frame' && targetTier === 'position') return 'containment';
  if (sourceTier === 'position' && targetTier === 'frame') return 'containment';
  if (targetTier === 'passage' || sourceTier === 'passage') return 'evidence';
  if (EVIDENCE_RELATION.test(relation)) return 'evidence';
  return 'context';
}

const EDGE_COLORS: Record<SubgraphEdgeKind, string> = {
  entry: '#D8C79C',
  containment: '#CBB9A6',
  opposition: '#C1605F',
  evidence: '#A9AFBB',
  context: '#CBC4B6',
};

/* ---------- layout ---------- */

export interface AnswerSubgraphLayoutOptions {
  queryLabel: string;
  /** citation index keyed by `node.ref ?? node.id`. */
  citationIndexByRef?: ReadonlyMap<string, number>;
}

interface Placed {
  node: RadialNode;
  /** Radius at which the node's own drawn ink ends, label included. */
  outerRadius: number;
}

export function layoutAnswerSubgraph(
  subgraph: AnswerSubgraph,
  options: AnswerSubgraphLayoutOptions,
): SubgraphRadialLayout {
  const citations = options.citationIndexByRef ?? new Map<string, number>();
  const questionAnchor = subgraph.nodes.find((node) => node.id === QUERY_NODE_ID);
  const source = subgraph.nodes.filter(
    (node) => Boolean(node.id) && node.id !== QUERY_NODE_ID,
  );

  const tiers = new Map<string, SubgraphTier>();
  const byId = new Map<string, AnswerSubgraphNode>();
  source.forEach((node) => {
    if (byId.has(node.id)) return;
    byId.set(node.id, node);
    tiers.set(node.id, tierOfSubgraphNode(node));
  });

  const edges = subgraph.edges.filter(
    (edge) =>
      edge.source !== edge.target &&
      (edge.source === QUERY_NODE_ID || byId.has(edge.source)) &&
      (edge.target === QUERY_NODE_ID || byId.has(edge.target)),
  );

  const neighbours = new Map<string, string[]>();
  edges.forEach((edge) => {
    if (edge.source === QUERY_NODE_ID || edge.target === QUERY_NODE_ID) return;
    if (!neighbours.has(edge.source)) neighbours.set(edge.source, []);
    if (!neighbours.has(edge.target)) neighbours.set(edge.target, []);
    neighbours.get(edge.source)!.push(edge.target);
    neighbours.get(edge.target)!.push(edge.source);
  });

  const idsOfTier = (tier: SubgraphTier) =>
    source.filter((node) => tiers.get(node.id) === tier).map((node) => node.id);

  const frameIds = idsOfTier('frame');
  const positionIds = idsOfTier('position');
  const passageIds = idsOfTier('passage');
  const contextIds = idsOfTier('context');

  const frameSet = new Set(frameIds);
  const positionSet = new Set(positionIds);

  /** First neighbour whose tier passes the predicate, in edge order. */
  const findNeighbour = (id: string, accept: (candidate: string) => boolean) =>
    (neighbours.get(id) ?? []).find(accept);

  const frameOfPosition = new Map<string, string>();
  positionIds.forEach((id) => {
    const frame = findNeighbour(id, (candidate) => frameSet.has(candidate));
    if (frame) frameOfPosition.set(id, frame);
  });

  // Only a position can carry beads: a passage contested by the whole debate
  // has no ray of its own and belongs on the corona.
  const positionOfPassage = new Map<string, string>();
  passageIds.forEach((id) => {
    const holder = findNeighbour(id, (candidate) => positionSet.has(candidate));
    if (holder) positionOfPassage.set(id, holder);
  });

  /* ----- sectors ----- */

  interface Group {
    id: string;
    frameId?: string;
    positions: string[];
    start: number;
    span: number;
    angle: number;
  }

  const groups: Group[] = frameIds.map((frameId) => ({
    id: frameId,
    frameId,
    positions: [],
    start: 0,
    span: 0,
    angle: 0,
  }));
  const groupIndex = new Map(groups.map((group) => [group.id, group]));

  const loose: Group = {
    id: '__loose__',
    positions: [],
    start: 0,
    span: 0,
    angle: 0,
  };
  positionIds.forEach((id) => {
    const frameId = frameOfPosition.get(id);
    const group = frameId ? groupIndex.get(frameId) : undefined;
    (group ?? loose).positions.push(id);
  });
  if (loose.positions.length > 0) groups.push(loose);

  const laidOut = groups.length > 0 ? groups : [loose];
  const totalWeight = laidOut.reduce(
    (sum, group) => sum + Math.max(1, group.positions.length),
    0,
  );
  const gap = laidOut.length > 1 ? Math.min(0.06, (TAU * 0.1) / laidOut.length) : 0;
  const usable = TAU - gap * (laidOut.length > 1 ? laidOut.length : 0);

  // A single sector is centred on 12 o'clock so its frame card sits on top.
  let cursor = laidOut.length === 1 ? TOP_ANGLE - usable / 2 : TOP_ANGLE;
  laidOut.forEach((group) => {
    const span = (usable * Math.max(1, group.positions.length)) / totalWeight;
    group.start = cursor;
    group.span = span;
    group.angle = cursor + span / 2;
    cursor += span + gap;
  });

  /* ----- radii ----- */

  const frameCount = frameIds.length;
  const frameAngles = laidOut.filter((group) => group.frameId).map((group) => group.angle);

  /** How far a flat card reaches along its own ray, and across it. */
  const cardReach = (angle: number) =>
    Math.abs(Math.cos(angle)) * (FRAME_WIDTH / 2) +
    Math.abs(Math.sin(angle)) * (FRAME_HEIGHT / 2);
  /** A card laid across the question medallion must clear it in that direction. */
  const questionClearance = (angle: number) =>
    Math.abs(Math.cos(angle)) * (QUESTION_WIDTH / 2 + FRAME_WIDTH / 2) +
    Math.abs(Math.sin(angle)) * (QUESTION_HEIGHT / 2 + FRAME_HEIGHT / 2) +
    18;

  const frameRing =
    frameCount === 0
      ? 0
      : Math.max(
          FRAME_RING_MIN,
          ...frameAngles.map(questionClearance),
          frameCount > 1
            ? (FRAME_WIDTH * 0.62) / Math.max(Math.sin(Math.PI / frameCount), 0.05)
            : 0,
        );

  let minPitch = Math.PI;
  laidOut.forEach((group) => {
    if (group.positions.length === 0) return;
    minPitch = Math.min(minPitch, group.span / group.positions.length);
  });

  const positionBase =
    frameCount > 0
      ? frameRing + Math.max(...frameAngles.map(cardReach)) + POSITION_RING_GAP
      : QUESTION_HEIGHT / 2 + 110;
  const slotRadius =
    minPitch >= Math.PI
      ? positionBase
      : POSITION_SLOT / (2 * Math.sin(Math.max(minPitch, 1e-4) / 2));
  const positionRing = Math.max(positionBase, Math.min(slotRadius, 4000));

  const positionLabels = new Map<string, string>();
  let widestLabel = 0;
  positionIds.forEach((id) => {
    const label = truncateLabel(byId.get(id)?.label ?? id, POSITION_LABEL_MAX);
    positionLabels.set(id, label);
    widestLabel = Math.max(widestLabel, estimateTextWidth(label, POSITION_FONT));
  });
  const labelBand = Math.max(72, Math.min(widestLabel + 26, 170));
  const beadRing = positionRing + labelBand;

  /* ----- placement ----- */

  const placed = new Map<string, Placed>();
  const themeOf = (type: string) => getGraphTypeTheme(type);

  const questionLabel = questionAnchor?.label || options.queryLabel;
  const questionLines = wrapLabel(questionLabel, 30, 2);
  placed.set(QUERY_NODE_ID, {
    node: {
      id: QUERY_NODE_ID,
      label: questionLabel,
      displayLabel: questionLines.join(' '),
      lines: questionLines,
      type: questionAnchor?.type || 'question',
      tier: 'question',
      x: 0,
      y: 0,
      radius: 0,
      angle: TOP_ANGLE,
      angleDeg: -90,
      flip: false,
      dotRadius: 0,
      width: QUESTION_WIDTH,
      height: QUESTION_HEIGHT,
      labelOffset: 0,
      fontSize: 13,
      showLabel: true,
      depth: 0,
      isSource: false,
      color: '#C79A31',
      tint: '#FFF8E8',
      border: '#EBD6A4',
      textColor: '#7A5610',
      groupId: '__root__',
    },
    outerRadius: Math.hypot(QUESTION_WIDTH, QUESTION_HEIGHT) / 2,
  });

  const place = (
    node: AnswerSubgraphNode,
    tier: SubgraphTier,
    angle: number,
    radius: number,
    groupId: string,
    overrides: Partial<RadialNode> & { showLabel: boolean; labelMax: number },
  ) => {
    const theme = themeOf(node.type);
    const citationIndex = citations.get(node.ref ?? node.id);
    const [x, y] = polar(angle, radius);
    const flip = Math.cos(angle) < 0;
    const fontSize = overrides.fontSize ?? POSITION_FONT;
    const label = node.label || node.id;
    const displayLabel = truncateLabel(label, overrides.labelMax);
    const dotRadius = overrides.dotRadius ?? 6;
    const labelOffset = overrides.labelOffset ?? dotRadius + 5;

    const radial: RadialNode = {
      id: node.id,
      ref: node.ref ?? node.id,
      label,
      displayLabel,
      lines: overrides.lines ?? [],
      detail: node.detail ?? node.publication,
      type: node.type,
      tier,
      x,
      y,
      radius,
      angle,
      angleDeg: round((angle * 180) / Math.PI),
      flip,
      dotRadius,
      width: overrides.width ?? 0,
      height: overrides.height ?? 0,
      labelOffset,
      fontSize,
      showLabel: overrides.showLabel,
      depth: overrides.depth ?? 2,
      citationIndex,
      isSource: citationIndex !== undefined,
      color: theme.color,
      tint: theme.tint,
      border: theme.border,
      textColor: theme.text,
      groupId,
    };

    const inkOut = overrides.width
      ? radius + overrides.width / 2
      : radius +
        labelOffset +
        (overrides.showLabel ? estimateTextWidth(displayLabel, fontSize) : 0);
    placed.set(node.id, { node: radial, outerRadius: inkOut });
    return radial;
  };

  // Frames.
  laidOut.forEach((group) => {
    if (!group.frameId) return;
    const node = byId.get(group.frameId);
    if (!node) return;
    const theme = themeOf(node.type);
    const citationIndex = citations.get(node.ref ?? node.id);
    const [x, y] = polar(group.angle, frameRing);
    placed.set(node.id, {
      node: {
        id: node.id,
        ref: node.ref ?? node.id,
        label: node.label || node.id,
        displayLabel: truncateLabel(node.label || node.id, 56),
        lines: wrapLabel(node.label || node.id, 28, 2),
        detail: node.detail ?? node.publication,
        type: node.type,
        tier: 'frame',
        x,
        y,
        radius: frameRing,
        angle: group.angle,
        angleDeg: round((group.angle * 180) / Math.PI),
        flip: false,
        dotRadius: 0,
        width: FRAME_WIDTH,
        height: FRAME_HEIGHT,
        labelOffset: 0,
        fontSize: 12.5,
        showLabel: true,
        depth: 1,
        citationIndex,
        isSource: citationIndex !== undefined,
        color: theme.color,
        tint: theme.tint,
        border: theme.border,
        textColor: theme.text,
        groupId: group.id,
      },
      outerRadius: frameRing + Math.hypot(FRAME_WIDTH, FRAME_HEIGHT) / 2,
    });
  });

  // Positions, fanned inside their sector.
  const positionAngle = new Map<string, number>();
  laidOut.forEach((group) => {
    const count = group.positions.length;
    if (count === 0) return;
    group.positions.forEach((id, index) => {
      const node = byId.get(id);
      if (!node) return;
      const angle = group.start + (group.span * (index + 0.5)) / count;
      positionAngle.set(id, angle);
      place(node, 'position', angle, positionRing, group.id, {
        showLabel: true,
        labelMax: POSITION_LABEL_MAX,
        dotRadius: 6,
        fontSize: POSITION_FONT,
        depth: 2,
      });
    });
  });

  // Contested passages: beads strung outward along their position's ray.
  const beadsByHolder = new Map<string, string[]>();
  passageIds.forEach((id) => {
    const holder = positionOfPassage.get(id);
    if (!holder) return;
    if (!beadsByHolder.has(holder)) beadsByHolder.set(holder, []);
    beadsByHolder.get(holder)!.push(id);
  });

  let beadOuter = beadRing;
  beadsByHolder.forEach((beads, holderId) => {
    const holder = placed.get(holderId);
    if (!holder) return;
    const group = laidOut.find((candidate) => candidate.id === holder.node.groupId);
    const count = group && group.positions.length > 0 ? group.positions.length : 1;
    const pitchPx = group ? (positionRing * group.span) / count : 400;
    // Roomy sectors get a tangential fan with visible refs; crowded ones get a
    // silent radial string of beads (refs live in the hover title).
    const fan = pitchPx >= 58 && beads.length <= 6;

    beads.forEach((id, index) => {
      const node = byId.get(id);
      if (!node) return;
      let angle = holder.node.angle;
      let radius = beadRing;
      if (fan) {
        const spacing = Math.min(24, (pitchPx * 0.62) / Math.max(beads.length, 1));
        angle += ((index - (beads.length - 1) / 2) * spacing) / beadRing;
      } else {
        const columns = beads.length > 4 ? 2 : 1;
        const column = index % columns;
        const row = Math.floor(index / columns);
        if (columns === 2) angle += ((column === 0 ? -1 : 1) * 9) / beadRing;
        radius = beadRing + row * BEAD_STEP;
      }
      place(node, 'passage', angle, radius, holder.node.groupId, {
        showLabel: fan,
        labelMax: PASSAGE_LABEL_MAX,
        dotRadius: 4,
        fontSize: PASSAGE_FONT,
        depth: 3,
      });
      beadOuter = Math.max(beadOuter, placed.get(id)?.outerRadius ?? radius);
    });
  });

  // Corona: activated KG nodes and any orphan passage, parked at the angle of
  // whatever they connect to, then pushed apart until each has breathing room.
  const orphanPassages = passageIds.filter((id) => !positionOfPassage.has(id));
  const coronaIds = [...contextIds, ...orphanPassages];
  const coronaRing = Math.max(beadOuter, positionRing) + CORONA_GAP;

  const desired = coronaIds.map((id, index) => {
    const anchor = findNeighbour(id, (candidate) => placed.has(candidate));
    const anchorNode = anchor ? placed.get(anchor)?.node : undefined;
    const fallback = TOP_ANGLE + (TAU * index) / Math.max(coronaIds.length, 1);
    return { id, angle: anchorNode ? anchorNode.angle : fallback };
  });
  const coronaAngles = spreadAngles(desired, CORONA_SLOT / coronaRing);

  coronaIds.forEach((id) => {
    const node = byId.get(id);
    if (!node) return;
    const angle = coronaAngles.get(id) ?? TOP_ANGLE;
    const tier = tiers.get(id) === 'passage' ? 'passage' : 'context';
    place(node, tier, angle, coronaRing, '__corona__', {
      showLabel: true,
      labelMax: CONTEXT_LABEL_MAX,
      dotRadius: tier === 'passage' ? 4 : 4.6,
      fontSize: CONTEXT_FONT,
      depth: 3,
    });
  });

  /* ----- edges ----- */

  const radialEdges: RadialEdge[] = [];
  const seen = new Set<string>();

  const pushEdge = (
    sourceId: string,
    targetId: string,
    relation: string,
    kind: SubgraphEdgeKind,
    origin?: string,
  ) => {
    const key = `${sourceId}->${targetId}:${relation}`;
    if (seen.has(key)) return;
    const from = placed.get(sourceId);
    const to = placed.get(targetId);
    if (!from || !to) return;
    seen.add(key);

    const a0 = from.node.angle;
    const a1 = to.node.angle;
    // The question has no angle of its own — leave it along the target's ray.
    const r0 = from.node.tier === 'question' ? QUESTION_HEIGHT / 2 + 6 : from.node.radius;
    const startAngle = from.node.tier === 'question' ? a1 : a0;
    const geometry =
      kind === 'opposition'
        ? chordPath(a0, from.node.radius, a1, to.node.radius)
        : radialLinkPath(startAngle, r0, a1, to.node.radius);

    radialEdges.push({
      id: key,
      source: sourceId,
      target: targetId,
      relation,
      origin,
      kind,
      path: geometry.path,
      color: kind === 'containment' ? from.node.color : EDGE_COLORS[kind],
      midX: geometry.midX,
      midY: geometry.midY,
      depth: Math.max(from.node.depth, to.node.depth),
    });
  };

  const questionEdges = edges.filter(
    (edge) => edge.source === QUERY_NODE_ID || edge.target === QUERY_NODE_ID,
  );
  questionEdges.forEach((edge) => {
    pushEdge(
      edge.source,
      edge.target,
      edge.relation,
      'entry',
      edge.origin,
    );
  });

  // Legacy payload compatibility: current backends serialise these links and
  // mark them runtime_inference. Older answers still get an honest fallback.
  if (questionEdges.length === 0) {
    frameIds.forEach((id) =>
      pushEdge(QUERY_NODE_ID, id, 'entry point', 'entry', 'runtime_inference'),
    );
    if (frameIds.length === 0) {
      loose.positions.forEach((id) =>
        pushEdge(QUERY_NODE_ID, id, 'entry point', 'entry', 'runtime_inference'),
      );
      if (positionIds.length === 0) {
        coronaIds.forEach((id) =>
          pushEdge(QUERY_NODE_ID, id, 'retrieved', 'entry', 'runtime_inference'),
        );
      }
    }
  }

  edges
    .filter(
      (edge) => edge.source !== QUERY_NODE_ID && edge.target !== QUERY_NODE_ID,
    )
    .forEach((edge) => {
      const sourceTier = tiers.get(edge.source) ?? 'context';
      const targetTier = tiers.get(edge.target) ?? 'context';
      pushEdge(
        edge.source,
        edge.target,
        edge.relation,
        edgeKindOf(edge.relation, sourceTier, targetTier),
        edge.origin,
      );
    });

  /* ----- bounds ----- */

  let minX = -QUESTION_WIDTH / 2;
  let minY = -QUESTION_HEIGHT / 2;
  let maxX = QUESTION_WIDTH / 2;
  let maxY = QUESTION_HEIGHT / 2;

  placed.forEach(({ node, outerRadius }) => {
    if (node.width > 0) {
      minX = Math.min(minX, node.x - node.width / 2);
      maxX = Math.max(maxX, node.x + node.width / 2);
      minY = Math.min(minY, node.y - node.height / 2);
      maxY = Math.max(maxY, node.y + node.height / 2);
      return;
    }
    const [fx, fy] = polar(node.angle, outerRadius);
    const pad = node.fontSize;
    minX = Math.min(minX, node.x - node.dotRadius, fx - pad);
    maxX = Math.max(maxX, node.x + node.dotRadius, fx + pad);
    minY = Math.min(minY, node.y - node.dotRadius, fy - pad);
    maxY = Math.max(maxY, node.y + node.dotRadius, fy + pad);
  });

  const sectorBoundaries =
    laidOut.length > 1 ? laidOut.map((group) => group.start - gap / 2) : [];

  const nodes = Array.from(placed.values()).map((entry) => entry.node);

  return {
    nodes,
    edges: radialEdges,
    rings: frameCount > 1 ? [frameRing, positionRing] : [positionRing],
    sectorBoundaries,
    sectorRadius: Math.max(maxX - minX, maxY - minY) / 2,
    bounds: {
      minX: round(minX - 16),
      minY: round(minY - 16),
      maxX: round(maxX + 16),
      maxY: round(maxY + 16),
    },
  };
}
