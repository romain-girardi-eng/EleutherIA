import { useRef, useMemo, useState, useEffect, useCallback } from 'react';
import * as d3 from 'd3';
import { linkHorizontal } from 'd3-shape';
import dagre from '@dagrejs/dagre';
import { cn } from '../../utils/cn';
import type { GraphRAGResponse } from '../../types';
import { getGraphTypeTheme } from './graphTheme';
import {
  layoutAnswerSubgraph,
  truncateLabel,
  QUERY_NODE_ID,
  type RadialNode,
  type SubgraphRadialLayout,
} from './answerSubgraphLayout';

/* ---------- types ---------- */

interface TraversalDAGProps {
  response: GraphRAGResponse | null;
  allResponses?: GraphRAGResponse[];
  highlightedSourceIndex: number | null;
  onNodeSelect: (nodeId: string, citationIndex?: number) => void;
  /** Curated-subgraph clicks: open the KG node detail for a resolvable node. */
  onNodeOpen?: (nodeId: string) => void;
  className?: string;
}

interface DAGNode {
  id: string;
  label: string;
  type: string;
  x: number;
  y: number;
  width: number;
  height: number;
  citationIndex?: number;
  isSource: boolean;
  isStarting: boolean;
  rank: number;
  /** KG node / passage id behind this box, when it resolves to one. */
  ref?: string;
  detail?: string;
}

interface DAGEdge {
  source: string;
  target: string;
  relation: string;
  sourceColor: string;
}

interface DAGLayout {
  nodes: DAGNode[];
  edges: DAGEdge[];
}

interface Bounds {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
}

/* ---------- constants ---------- */

const QUERY_THEME = {
  color: '#C79A31',
  tint: '#FFF7E0',
  border: '#F0D79B',
  text: '#876114',
  glow: '#FFEAB3',
  label: 'Query',
};

/** Cream of the page, used as the halo behind radial labels. */
const LABEL_HALO = '#FDFBF6';

/* ---------- legacy (non-subgraph) layout ---------- */

/**
 * The pre-subgraph reasoning path is a genuine left-to-right walk — seeds,
 * expansions, traversed edges — so it keeps its rank layout untouched.
 */
function buildLegacyLayout(
  responses: GraphRAGResponse[],
  currentResponse: GraphRAGResponse,
): DAGLayout | null {
  const nodeMap = new Map<
    string,
    {
      id: string;
      label: string;
      type: string;
      isSource: boolean;
      isStarting: boolean;
      citationIndex?: number;
      ref?: string;
      detail?: string;
    }
  >();
  const edgeList: Array<{ source: string; target: string; relation: string }> = [];
  const edgeSet = new Set<string>();

  const upsertNode = (
    id: string,
    label: string,
    type: string,
    flags: {
      isSource?: boolean;
      isStarting?: boolean;
      citationIndex?: number;
      ref?: string;
      detail?: string;
    },
  ) => {
    if (!id) return;
    const existing = nodeMap.get(id);
    if (existing) {
      existing.label = existing.label || label || id;
      existing.type = existing.type || type || 'default';
      existing.isSource = existing.isSource || Boolean(flags.isSource);
      existing.isStarting = existing.isStarting || Boolean(flags.isStarting);
      existing.ref = existing.ref ?? flags.ref;
      existing.detail = existing.detail ?? flags.detail;
      if (flags.citationIndex !== undefined && existing.citationIndex === undefined) {
        existing.citationIndex = flags.citationIndex;
      }
      return;
    }
    nodeMap.set(id, {
      id,
      label: label || id,
      type: type || 'default',
      isSource: Boolean(flags.isSource),
      isStarting: Boolean(flags.isStarting),
      citationIndex: flags.citationIndex,
      ref: flags.ref,
      detail: flags.detail,
    });
  };

  const addEdge = (source: string, target: string, relation: string) => {
    if (!source || !target || source === target) return;
    const key = `${source}->${target}`;
    if (edgeSet.has(key)) return;
    edgeSet.add(key);
    edgeList.push({ source, target, relation });
  };

  upsertNode(
    QUERY_NODE_ID,
    truncateLabel(currentResponse.query || 'Query', 24),
    'query',
    {},
  );

  responses.forEach((resp) => {
    resp.reasoning_path?.starting_nodes?.forEach((node) => {
      upsertNode(node.id, node.label, node.type, { isStarting: true });
      addEdge(QUERY_NODE_ID, node.id, 'entry point');
    });

    resp.sources?.slice(0, 28).forEach((source) => {
      const isCurrentSource = currentResponse?.sources?.some(
        (item) => item.nodeId === source.nodeId,
      );
      const citationIndex =
        isCurrentSource && currentResponse?.sources
          ? currentResponse.sources.findIndex((item) => item.nodeId === source.nodeId)
          : -1;

      upsertNode(source.nodeId, source.nodeLabel, source.nodeType, {
        isSource: true,
        citationIndex: citationIndex >= 0 ? citationIndex : undefined,
      });
    });

    resp.reasoning_path?.expanded_nodes?.slice(0, 18).forEach((node) => {
      upsertNode(node.id, node.label, node.type, {});
    });

    resp.reasoning_path?.traversed_edges?.slice(0, 36).forEach((edge) => {
      upsertNode(edge.source, edge.source, 'default', {});
      upsertNode(edge.target, edge.target, 'default', {});
      addEdge(edge.source, edge.target, edge.relation);
    });
  });

  const connectedIds = new Set<string>();
  edgeList.forEach((e) => {
    connectedIds.add(e.source);
    connectedIds.add(e.target);
  });
  connectedIds.add(QUERY_NODE_ID);

  if (connectedIds.size <= 1) {
    nodeMap.forEach((node) => {
      if (node.id !== QUERY_NODE_ID) {
        connectedIds.add(node.id);
        addEdge(QUERY_NODE_ID, node.id, 'related');
      }
    });
  }

  const g = new dagre.graphlib.Graph();
  g.setGraph({ rankdir: 'LR', ranksep: 80, nodesep: 40, edgesep: 20 });
  g.setDefaultEdgeLabel(() => ({}));

  nodeMap.forEach((node) => {
    if (!connectedIds.has(node.id)) return;
    const isQuery = node.id === QUERY_NODE_ID;
    const width = isQuery ? 120 : node.isSource ? 140 : 130;
    const height = isQuery ? 44 : node.isSource ? 48 : 44;
    g.setNode(node.id, { label: node.label, width, height });
  });

  edgeList.forEach((edge) => {
    if (connectedIds.has(edge.source) && connectedIds.has(edge.target)) {
      g.setEdge(edge.source, edge.target);
    }
  });

  dagre.layout(g);

  const nodes: DAGNode[] = [];
  g.nodes().forEach((id) => {
    const dagreNode = g.node(id);
    if (!dagreNode) return;
    const meta = nodeMap.get(id);
    if (!meta) return;

    const isQuery = id === QUERY_NODE_ID;
    nodes.push({
      id,
      label: meta.label,
      type: isQuery ? 'query' : meta.type,
      x: dagreNode.x,
      y: dagreNode.y,
      width: dagreNode.width ?? (isQuery ? 120 : meta.isSource ? 140 : 130),
      height: dagreNode.height ?? (isQuery ? 44 : meta.isSource ? 48 : 44),
      citationIndex: meta.citationIndex,
      isSource: meta.isSource,
      isStarting: meta.isStarting,
      rank: Math.round(dagreNode.x / 100),
      ref: meta.ref,
      detail: meta.detail,
    });
  });

  if (nodes.length === 0) return null;

  const edges: DAGEdge[] = edgeList
    .filter((e) => connectedIds.has(e.source) && connectedIds.has(e.target))
    .map((e) => {
      const sourceNode = nodeMap.get(e.source);
      const sourceType = e.source === QUERY_NODE_ID ? 'query' : sourceNode?.type;
      const theme =
        sourceType === 'query' ? QUERY_THEME : getGraphTypeTheme(sourceType);
      return {
        source: e.source,
        target: e.target,
        relation: e.relation,
        sourceColor: theme.color,
      };
    });

  return { nodes, edges };
}

/* ---------- radial node marks ---------- */

/** `rotate(a) translate(offset,0)` walks out along the ray; the extra 180°
 *  keeps labels on the left half of the circle right-way-up. */
function radialLabelTransform(node: RadialNode): string {
  return `rotate(${node.angleDeg}) translate(${node.labelOffset},0)${
    node.flip ? ' rotate(180)' : ''
  }`;
}

function nodeTitle(node: { label: string; detail?: string }): string {
  return node.detail ? `${node.label} — ${node.detail}` : node.label;
}

/* ---------- component ---------- */

export default function TraversalDAG({
  response,
  allResponses,
  highlightedSourceIndex,
  onNodeSelect,
  onNodeOpen,
  className,
}: TraversalDAGProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [hoveredEdge, setHoveredEdge] = useState<string | null>(null);
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);

  /* ---- which graph are we drawing? ---- */

  const currentResponse = useMemo(() => {
    const responses =
      allResponses && allResponses.length > 0
        ? allResponses
        : response
          ? [response]
          : [];
    if (responses.length === 0) return null;
    return response ?? responses[responses.length - 1];
  }, [response, allResponses]);

  /**
   * The curated subgraph IS the answer's knowledge graph: controversy frames,
   * the positions clashing inside them, the contested passages grounding those
   * positions, and the KG nodes retrieval activated. When the backend ships
   * one it supersedes the flat id lists the legacy branch reassembles.
   */
  const radial = useMemo<SubgraphRadialLayout | null>(() => {
    const curated = currentResponse?.reasoning_path?.subgraph;
    if (!curated || curated.nodes.length === 0) return null;

    const citationIndexByRef = new Map<string, number>();
    (currentResponse?.sources ?? []).forEach((source, index) => {
      if (source.nodeId && !citationIndexByRef.has(source.nodeId)) {
        citationIndexByRef.set(source.nodeId, index);
      }
    });

    return layoutAnswerSubgraph(curated, {
      queryLabel: currentResponse?.query || 'Query',
      citationIndexByRef,
    });
  }, [currentResponse]);

  const legacy = useMemo<DAGLayout | null>(() => {
    if (radial) return null;
    if (!currentResponse) return null;
    const responses =
      allResponses && allResponses.length > 0 ? allResponses : [currentResponse];
    return buildLegacyLayout(responses, currentResponse);
  }, [radial, currentResponse, allResponses]);

  const bounds = useMemo<Bounds | null>(() => {
    if (radial) return radial.bounds;
    if (!legacy || legacy.nodes.length === 0) return null;
    let minX = Infinity;
    let minY = Infinity;
    let maxX = -Infinity;
    let maxY = -Infinity;
    legacy.nodes.forEach((n) => {
      minX = Math.min(minX, n.x - n.width / 2);
      minY = Math.min(minY, n.y - n.height / 2);
      maxX = Math.max(maxX, n.x + n.width / 2);
      maxY = Math.max(maxY, n.y + n.height / 2);
    });
    return { minX, minY, maxX, maxY };
  }, [radial, legacy]);

  /* ---- zoom + initial fit ---- */

  useEffect(() => {
    if (!svgRef.current || !bounds) return;

    const svg = d3.select(svgRef.current);
    const gElem = svg.select<SVGGElement>('g.zoom-container');

    const rect = svgRef.current.getBoundingClientRect();
    const svgWidth = rect.width || 600;
    const svgHeight = rect.height || 400;

    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.2, 3])
      // Pin the viewport extent to the measured box. d3's default reads the
      // SVG's width/height baseVal, which is absent outside a real browser.
      .extent([
        [0, 0],
        [svgWidth, svgHeight],
      ])
      .on('zoom', (event) => {
        gElem.attr('transform', event.transform.toString());
      });

    svg.call(zoom);

    const graphWidth = Math.max(bounds.maxX - bounds.minX, 1);
    const graphHeight = Math.max(bounds.maxY - bounds.minY, 1);
    const padding = 28;
    // Never open so far out that labels stop being readable — a corona that
    // spills past the frame is what pan and zoom are for.
    const fitted = Math.min(
      (svgWidth - padding * 2) / graphWidth,
      (svgHeight - padding * 2) / graphHeight,
    );
    const scale = Math.max(0.45, Math.min(fitted, 1.2));
    const tx = svgWidth / 2 - ((bounds.minX + bounds.maxX) / 2) * scale;
    const ty = svgHeight / 2 - ((bounds.minY + bounds.maxY) / 2) * scale;

    svg.call(zoom.transform, d3.zoomIdentity.translate(tx, ty).scale(scale));

    return () => {
      svg.on('.zoom', null);
    };
  }, [bounds]);

  /* ---- trigger mount animation ---- */

  useEffect(() => {
    if (!bounds) return;
    setMounted(false);
    const raf = requestAnimationFrame(() => setMounted(true));
    return () => cancelAnimationFrame(raf);
  }, [bounds]);

  /* ---- legacy path generator ---- */

  const pathGenerator = useMemo(
    () =>
      linkHorizontal<
        { source: [number, number]; target: [number, number] },
        [number, number]
      >()
        .x((d) => d[0])
        .y((d) => d[1]),
    [],
  );

  const legacyPositions = useMemo(() => {
    const map = new Map<string, DAGNode>();
    legacy?.nodes.forEach((n) => map.set(n.id, n));
    return map;
  }, [legacy]);

  /* ---- handlers ---- */

  const openNode = useCallback(
    (id: string, ref: string | undefined, citationIndex: number | undefined) => {
      if (id === QUERY_NODE_ID) return;
      onNodeSelect(ref ?? id, citationIndex);
      // Curated nodes carry the KG id they stand for (a frame's debate node, a
      // position's holder, a passage) — open its detail card.
      if (ref) onNodeOpen?.(ref);
    },
    [onNodeSelect, onNodeOpen],
  );

  /* ---- empty state ---- */

  if (!bounds || (!radial && (!legacy || legacy.nodes.length === 0))) {
    return (
      <div
        className={cn(
          'relative flex h-full w-full items-center justify-center overflow-hidden rounded-[24px] border border-stone-200/80 bg-[radial-gradient(circle_at_top_left,_rgba(255,248,235,0.98),_rgba(255,255,255,0.97)_45%,_rgba(247,243,235,0.98)_100%)]',
          className,
        )}
      >
        <p className="text-sm text-stone-400">
          Ask a question to see the reasoning graph
        </p>
      </div>
    );
  }

  /* ---- counters ---- */

  const curatedStats = currentResponse?.reasoning_path?.subgraph?.stats;
  const graphNodeCount = radial
    ? radial.nodes.filter((n) => n.id !== QUERY_NODE_ID).length
    : (legacy?.nodes.length ?? 1) - 1;
  const graphEdgeCount = radial ? radial.edges.length : (legacy?.edges.length ?? 0);
  const oppositionCount = radial
    ? radial.edges.filter((e) => e.kind === 'opposition').length
    : 0;

  // A fan of eighty spokes has to whisper; a fan of four can speak up.
  const containmentOpacity = Math.max(
    0.16,
    Math.min(0.45, 0.45 - 0.006 * (radial?.nodes.filter((n) => n.tier === 'position').length ?? 0)),
  );

  /* ---- legacy edge paths ---- */

  const legacyEdgePaths = (legacy?.edges ?? []).map((edge) => {
    const s = legacyPositions.get(edge.source);
    const t = legacyPositions.get(edge.target);
    if (!s || !t) return { ...edge, d: '', sourceRank: 0 };
    const d = pathGenerator({
      source: [s.x + s.width / 2, s.y] as [number, number],
      target: [t.x - t.width / 2, t.y] as [number, number],
    });
    return { ...edge, d: d ?? '', sourceRank: s.rank };
  });

  const maxRank = Math.max(0, ...(legacy?.nodes ?? []).map((n) => n.rank));

  const hoveredEdgeInfo = ((): { relation: string; mid: [number, number] } | null => {
    if (!hoveredEdge) return null;
    if (radial) {
      const edge = radial.edges.find((e) => e.id === hoveredEdge);
      return edge
        ? { relation: edge.relation, mid: [edge.midX, edge.midY] }
        : null;
    }
    const edge = (legacy?.edges ?? []).find(
      (e) => `${e.source}->${e.target}` === hoveredEdge,
    );
    if (!edge) return null;
    const s = legacyPositions.get(edge.source);
    const t = legacyPositions.get(edge.target);
    if (!s || !t) return null;
    return {
      relation: edge.relation,
      mid: [(s.x + s.width / 2 + (t.x - t.width / 2)) / 2, (s.y + t.y) / 2],
    };
  })();

  /* ---- radial node mark ---- */

  const renderRadialNode = (node: RadialNode) => {
    const isHighlighted =
      highlightedSourceIndex !== null && node.citationIndex === highlightedSourceIndex;
    const isHovered = hoveredNode === node.id;
    const delay = node.depth * 0.09 + 0.05;
    const commonProps = {
      className: cn(
        'subgraph-node',
        `subgraph-node--${node.tier}`,
        node.tier === 'question' ? 'cursor-default' : 'cursor-pointer',
      ),
      'data-tier': node.tier,
      'data-node-id': node.id,
      onClick: () => openNode(node.id, node.ref, node.citationIndex),
      onMouseEnter: () => setHoveredNode(node.id),
      onMouseLeave: () => setHoveredNode(null),
      style: {
        opacity: mounted ? 1 : 0,
        transition: `opacity 0.45s ease ${delay}s`,
      },
    };

    /* Boxed tiers: the question medallion and the fault-line cards. */
    if (node.tier === 'question' || node.tier === 'frame') {
      const isQuestion = node.tier === 'question';
      const lineHeight = isQuestion ? 16 : 14;
      const firstLine = isQuestion
        ? -((node.lines.length - 1) * lineHeight) / 2 + 5
        : -node.height / 2 + 30;

      return (
        <g key={node.id} transform={`translate(${node.x},${node.y})`} {...commonProps}>
          {isHighlighted && (
            <rect
              x={-node.width / 2 - 4}
              y={-node.height / 2 - 4}
              width={node.width + 8}
              height={node.height + 8}
              rx={isQuestion ? 22 : 17}
              fill="none"
              stroke="#F59E0B"
              strokeWidth={2.2}
              filter="url(#glow-highlight)"
            />
          )}
          <rect
            x={-node.width / 2}
            y={-node.height / 2}
            width={node.width}
            height={node.height}
            rx={isQuestion ? 18 : 13}
            fill={node.tint}
            stroke={node.border}
            strokeWidth={isQuestion ? 1.2 : 1.4}
          />
          {!isQuestion && (
            <text
              x={0}
              y={-node.height / 2 + 14}
              textAnchor="middle"
              fontSize={7.5}
              fontWeight={600}
              letterSpacing="0.1em"
              fill={node.color}
              className="uppercase"
            >
              fault line
            </text>
          )}
          <text
            x={0}
            y={firstLine}
            textAnchor="middle"
            fontSize={node.fontSize}
            fontWeight={isQuestion ? 400 : 600}
            fill={node.textColor}
            className="font-serif"
          >
            {node.lines.map((line, index) => (
              <tspan key={`${node.id}-line-${index}`} x={0} dy={index === 0 ? 0 : lineHeight}>
                {line}
              </tspan>
            ))}
          </text>
          <title>{nodeTitle(node)}</title>
        </g>
      );
    }

    /* Dot tiers: positions on the ring, passage beads, corona context. */
    const isPosition = node.tier === 'position';
    const strokeWidth = isPosition ? 1.8 : 1.3;

    return (
      <g key={node.id} transform={`translate(${node.x},${node.y})`} {...commonProps}>
        {isHighlighted && (
          <circle
            r={node.dotRadius + 6}
            fill="none"
            stroke="#F59E0B"
            strokeWidth={2}
            filter="url(#glow-highlight)"
          />
        )}
        {node.isSource && (
          <circle
            r={node.dotRadius + 3.4}
            fill="none"
            stroke={node.color}
            strokeWidth={0.9}
            strokeOpacity={0.5}
          />
        )}
        <circle
          r={node.dotRadius}
          fill={node.isSource || isPosition ? node.tint : LABEL_HALO}
          stroke={node.color}
          strokeWidth={isHovered ? strokeWidth + 0.8 : strokeWidth}
        />
        {node.showLabel && (
          <text
            className="subgraph-node__label font-serif"
            transform={radialLabelTransform(node)}
            textAnchor={node.flip ? 'end' : 'start'}
            dominantBaseline="middle"
            fontSize={node.fontSize}
            fontWeight={isPosition ? 600 : 400}
            fill={isHovered ? node.color : node.textColor}
            stroke={LABEL_HALO}
            strokeWidth={3}
            strokeLinejoin="round"
            paintOrder="stroke"
          >
            {node.displayLabel}
          </text>
        )}
        {node.citationIndex !== undefined && (
          <text
            transform={`rotate(${node.angleDeg}) translate(${-node.dotRadius - 7},0)${
              node.flip ? ' rotate(180)' : ''
            }`}
            textAnchor={node.flip ? 'start' : 'end'}
            dominantBaseline="middle"
            fontSize={8}
            fontWeight={700}
            fill={node.color}
          >
            {node.citationIndex + 1}
          </text>
        )}
        <circle r={Math.max(node.dotRadius + 6, 10)} fill="transparent" />
        <title>{nodeTitle(node)}</title>
      </g>
    );
  };

  /* ---- main render ---- */

  return (
    <div
      ref={containerRef}
      className={cn(
        'relative h-full w-full overflow-hidden rounded-[24px] border border-stone-200/80 bg-[radial-gradient(circle_at_top_left,_rgba(255,248,235,0.98),_rgba(255,255,255,0.97)_45%,_rgba(247,243,235,0.98)_100%)]',
        className,
      )}
    >
      <div
        className="pointer-events-none absolute left-3 top-3 z-10 flex flex-wrap items-center gap-1.5"
        data-testid="traversal-dag-counters"
      >
        <span className="rounded-full border border-stone-200/80 bg-white/85 px-2 py-0.5 text-[10px] text-stone-500 backdrop-blur">
          <span className="font-semibold text-stone-700">{graphNodeCount}</span> nodes
        </span>
        <span className="rounded-full border border-stone-200/80 bg-white/85 px-2 py-0.5 text-[10px] text-stone-500 backdrop-blur">
          <span className="font-semibold text-stone-700">{graphEdgeCount}</span> edges
        </span>
        {curatedStats && curatedStats.frame_count > 0 && (
          <span className="rounded-full border border-rose-200/80 bg-rose-50/85 px-2 py-0.5 text-[10px] text-rose-700 backdrop-blur">
            <span className="font-semibold">{curatedStats.frame_count}</span>{' '}
            {curatedStats.frame_count === 1 ? 'fault line' : 'fault lines'}
          </span>
        )}
        {oppositionCount > 0 && (
          <span className="rounded-full border border-rose-200/80 bg-white/85 px-2 py-0.5 text-[10px] text-rose-600 backdrop-blur">
            <span className="font-semibold">{oppositionCount}</span> opposed
          </span>
        )}
        {curatedStats?.truncated && (
          <span className="rounded-full border border-amber-200/80 bg-amber-50/85 px-2 py-0.5 text-[10px] text-amber-700 backdrop-blur">
            top {curatedStats.node_count} of {curatedStats.candidate_nodes}
          </span>
        )}
      </div>

      {radial && (
        <div
          className="pointer-events-none absolute bottom-3 left-3 z-10 flex flex-wrap items-center gap-x-3 gap-y-1 rounded-full border border-stone-200/70 bg-white/80 px-3 py-1.5 backdrop-blur"
          data-testid="traversal-dag-legend"
        >
          <span className="flex items-center gap-1.5 text-[9px] text-stone-500">
            <span className="inline-block h-2 w-3 rounded-[2px] border border-rose-300 bg-rose-50" />
            fault line
          </span>
          <span className="flex items-center gap-1.5 text-[9px] text-stone-500">
            <span className="inline-block h-2 w-2 rounded-full border border-indigo-300 bg-indigo-50" />
            position
          </span>
          <span className="flex items-center gap-1.5 text-[9px] text-stone-500">
            <span className="inline-block h-1.5 w-1.5 rounded-full border border-slate-300 bg-white" />
            passage
          </span>
          <span className="flex items-center gap-1.5 text-[9px] text-stone-500">
            <span className="inline-block h-px w-3 bg-rose-500" />
            opposes
          </span>
        </div>
      )}

      <svg ref={svgRef} className="h-full w-full" style={{ display: 'block' }}>
        <defs>
          <marker
            id="arrowhead"
            viewBox="0 0 10 8"
            refX="9"
            refY="4"
            markerWidth="8"
            markerHeight="6"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 10 4 L 0 8 z" fill="#9CA3AF" fillOpacity={0.6} />
          </marker>
          <filter id="glow-highlight" x="-30%" y="-30%" width="160%" height="160%">
            <feDropShadow
              dx="0"
              dy="0"
              stdDeviation="3"
              floodColor="#F59E0B"
              floodOpacity="0.4"
            />
          </filter>
        </defs>

        <g className="zoom-container">
          {radial ? (
            <>
              {/* ---- the orrery's guide rings ---- */}
              <g className="subgraph-rings" pointerEvents="none">
                {radial.rings.map((r) => (
                  <circle
                    key={`ring-${r}`}
                    r={r}
                    fill="none"
                    stroke="#E4DCCB"
                    strokeWidth={0.8}
                    strokeDasharray="2 7"
                    opacity={mounted ? 0.85 : 0}
                    style={{ transition: 'opacity 0.6s ease' }}
                  />
                ))}
                {radial.sectorBoundaries.map((angle) => (
                  <line
                    key={`sector-${angle}`}
                    x1={Math.cos(angle) * (radial.rings[0] ?? 0)}
                    y1={Math.sin(angle) * (radial.rings[0] ?? 0)}
                    x2={Math.cos(angle) * radial.sectorRadius}
                    y2={Math.sin(angle) * radial.sectorRadius}
                    stroke="#E4DCCB"
                    strokeWidth={0.8}
                    strokeDasharray="3 6"
                    opacity={mounted ? 0.7 : 0}
                    style={{ transition: 'opacity 0.6s ease' }}
                  />
                ))}
              </g>

              {/* ---- edges: quiet containment, loud dialectic ---- */}
              <g className="subgraph-edges">
                {radial.edges.map((edge) => {
                  const isHovered = hoveredEdge === edge.id;
                  const touchesHovered =
                    hoveredNode !== null &&
                    (edge.source === hoveredNode || edge.target === hoveredNode);
                  const opposition = edge.kind === 'opposition';
                  // Containment is already told by the geometry, so it fades as
                  // the fan grows; opposition and evidence stems carry the ink.
                  const base =
                    opposition
                      ? 0.68
                      : edge.kind === 'entry'
                        ? 0.55
                        : edge.kind === 'containment'
                          ? containmentOpacity
                          : edge.kind === 'evidence'
                            ? 0.45
                            : 0.38;
                  const dimmed =
                    hoveredNode !== null && !touchesHovered ? base * 0.35 : base;
                  const width = opposition ? 1.7 : edge.kind === 'entry' ? 1.4 : 1;

                  return (
                    <g key={edge.id}>
                      <path
                        className={cn('subgraph-edge', `subgraph-edge--${edge.kind}`)}
                        data-relation={edge.relation}
                        d={edge.path}
                        fill="none"
                        stroke={edge.color}
                        strokeOpacity={isHovered || touchesHovered ? 0.92 : dimmed}
                        strokeWidth={isHovered || touchesHovered ? width + 0.9 : width}
                        strokeLinecap="round"
                        style={{
                          strokeDasharray: opposition ? undefined : 1400,
                          strokeDashoffset: mounted ? 0 : 1400,
                          transition: `stroke-dashoffset 0.7s ease ${
                            edge.depth * 0.08
                          }s, stroke-opacity 0.15s ease, stroke-width 0.15s ease`,
                          opacity: opposition && !mounted ? 0 : 1,
                        }}
                      />
                      <path
                        d={edge.path}
                        fill="none"
                        stroke="transparent"
                        strokeWidth={11}
                        onMouseEnter={() => setHoveredEdge(edge.id)}
                        onMouseLeave={() => setHoveredEdge(null)}
                        className="cursor-pointer"
                      />
                    </g>
                  );
                })}
              </g>

              {/* ---- nodes ---- */}
              <g className="subgraph-nodes">{radial.nodes.map(renderRadialNode)}</g>
            </>
          ) : (
            <>
              {/* ---- legacy rank layout ---- */}
              {legacyEdgePaths.map((ep) => {
                if (!ep.d) return null;
                const edgeKey = `${ep.source}->${ep.target}`;
                const isHovered = hoveredEdge === edgeKey;
                const staggerDelay = (ep.sourceRank / Math.max(maxRank, 1)) * 0.4;

                return (
                  <g key={edgeKey}>
                    <path
                      d={ep.d}
                      fill="none"
                      stroke={ep.sourceColor}
                      strokeOpacity={isHovered ? 0.8 : 0.5}
                      strokeWidth={isHovered ? 2.5 : 1.5}
                      markerEnd="url(#arrowhead)"
                      style={{
                        strokeDasharray: 1000,
                        strokeDashoffset: mounted ? 0 : 1000,
                        transition: `stroke-dashoffset 0.6s ease ${staggerDelay}s, stroke-opacity 0.15s ease, stroke-width 0.15s ease`,
                      }}
                      onMouseEnter={() => setHoveredEdge(edgeKey)}
                      onMouseLeave={() => setHoveredEdge(null)}
                      className="cursor-pointer"
                    />
                    <path
                      d={ep.d}
                      fill="none"
                      stroke="transparent"
                      strokeWidth={12}
                      onMouseEnter={() => setHoveredEdge(edgeKey)}
                      onMouseLeave={() => setHoveredEdge(null)}
                      className="cursor-pointer"
                    />
                  </g>
                );
              })}

              {(legacy?.nodes ?? []).map((node) => {
                const theme =
                  node.type === 'query' ? QUERY_THEME : getGraphTypeTheme(node.type);
                const isHighlighted =
                  highlightedSourceIndex !== null &&
                  node.citationIndex === highlightedSourceIndex;
                const staggerDelay = (node.rank / Math.max(maxRank, 1)) * 0.35 + 0.05;

                return (
                  <g
                    key={node.id}
                    transform={`translate(${node.x - node.width / 2}, ${
                      node.y - node.height / 2
                    })`}
                    onClick={() => openNode(node.id, node.ref, node.citationIndex)}
                    className={cn(
                      'cursor-pointer',
                      node.id === QUERY_NODE_ID && 'cursor-default',
                    )}
                    style={{
                      opacity: mounted ? 1 : 0,
                      transition: `opacity 0.4s ease ${staggerDelay}s, transform 0.15s ease`,
                    }}
                  >
                    {isHighlighted && (
                      <rect
                        x={-3}
                        y={-3}
                        width={node.width + 6}
                        height={node.height + 6}
                        rx={14}
                        fill="none"
                        stroke="#F59E0B"
                        strokeWidth={2.5}
                        filter="url(#glow-highlight)"
                      />
                    )}
                    <rect
                      width={node.width}
                      height={node.height}
                      rx={12}
                      fill={theme.tint}
                      stroke={isHighlighted ? '#F59E0B' : theme.border}
                      strokeWidth={isHighlighted ? 2 : 1}
                    />
                    {node.isSource && node.citationIndex !== undefined && (
                      <>
                        <circle cx={10} cy={10} r={8} fill={theme.color} />
                        <text
                          x={10}
                          y={13.5}
                          textAnchor="middle"
                          fontSize={9}
                          fontWeight={700}
                          fill="white"
                        >
                          {node.citationIndex + 1}
                        </text>
                      </>
                    )}
                    <text
                      x={node.width / 2}
                      y={node.height / 2 + 4}
                      textAnchor="middle"
                      fontSize={11}
                      fontWeight={600}
                      fill={theme.text}
                      className="font-serif"
                      style={{ userSelect: 'none' }}
                    >
                      {truncateLabel(node.label, 18)}
                    </text>
                    <rect
                      width={node.width}
                      height={node.height}
                      rx={12}
                      fill="transparent"
                      className="transition-opacity duration-150 hover:fill-black/[0.03]"
                    >
                      <title>{nodeTitle(node)}</title>
                    </rect>
                  </g>
                );
              })}
            </>
          )}

          {/* ---- edge relation tooltip ---- */}
          {hoveredEdgeInfo &&
            (() => {
              const labelText = hoveredEdgeInfo.relation || 'related';
              const labelWidth = Math.min(labelText.length * 6.5 + 16, 170);
              return (
                <g
                  transform={`translate(${hoveredEdgeInfo.mid[0] - labelWidth / 2}, ${
                    hoveredEdgeInfo.mid[1] - 12
                  })`}
                  style={{ pointerEvents: 'none' }}
                >
                  <rect
                    width={labelWidth}
                    height={22}
                    rx={6}
                    fill="white"
                    stroke="#D6D3D1"
                    strokeWidth={0.8}
                    filter="drop-shadow(0 2px 4px rgba(0,0,0,0.08))"
                  />
                  <text
                    x={labelWidth / 2}
                    y={15}
                    textAnchor="middle"
                    fontSize={10}
                    fontWeight={500}
                    fill="#57534E"
                  >
                    {truncateLabel(labelText, 24)}
                  </text>
                </g>
              );
            })()}
        </g>
      </svg>
    </div>
  );
}
