import { useRef, useMemo, useState, useEffect, useCallback } from 'react';
import * as d3 from 'd3';
import { linkHorizontal } from 'd3-shape';
import dagre from '@dagrejs/dagre';
import { cn } from '../../utils/cn';
import type { GraphRAGResponse } from '../../types';
import { getGraphTypeTheme } from './graphTheme';

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

/* ---------- constants ---------- */

const QUERY_THEME = {
  color: '#C79A31',
  tint: '#FFF7E0',
  border: '#F0D79B',
  text: '#876114',
  glow: '#FFEAB3',
  label: 'Query',
};

/* ---------- helpers ---------- */

function truncateLabel(label: string, max: number): string {
  if (label.length <= max) return label;
  return `${label.slice(0, max - 1)}\u2026`;
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
  const [mounted, setMounted] = useState(false);

  /* ---- compute layout ---- */

  const layout = useMemo<DAGLayout | null>(() => {
    const responses =
      allResponses && allResponses.length > 0
        ? allResponses
        : response
          ? [response]
          : [];

    if (responses.length === 0) return null;

    const currentResponse = response ?? responses[responses.length - 1];

    // Accumulate nodes
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

    // Add query root node
    const queryLabel = truncateLabel(currentResponse.query || 'Query', 24);
    upsertNode('__query__', queryLabel, 'query', {});

    // ---- curated subgraph (the answer's own knowledge graph) ----
    // When the backend shipped one, it IS the graph: controversy frames, the
    // positions that clash inside them, the contested passages grounding those
    // positions, and the KG nodes retrieval actually activated. It supersedes
    // the flat starting/expanded id lists the legacy branch below reassembles.
    const curated = currentResponse.reasoning_path?.subgraph;
    if (curated && curated.nodes.length > 0) {
      const sourceIndexByNodeId = new Map<string, number>();
      (currentResponse.sources ?? []).forEach((source, index) => {
        if (source.nodeId && !sourceIndexByNodeId.has(source.nodeId)) {
          sourceIndexByNodeId.set(source.nodeId, index);
        }
      });

      curated.nodes.forEach((node) => {
        const citationIndex =
          sourceIndexByNodeId.get(node.ref ?? node.id) ?? undefined;
        upsertNode(node.id, node.label, node.type, {
          isSource: citationIndex !== undefined,
          isStarting: Boolean(node.root),
          citationIndex,
          ref: node.ref,
          detail: node.detail ?? node.publication,
        });
      });

      curated.edges.forEach((edge) => {
        addEdge(edge.source, edge.target, edge.relation);
      });

      // Hang the fault lines (and any node the map left unconnected) off the
      // question, so the panel always reads question -> debate -> evidence.
      const connected = new Set<string>();
      edgeList.forEach((edge) => {
        connected.add(edge.source);
        connected.add(edge.target);
      });
      curated.nodes.forEach((node) => {
        if (node.root) {
          addEdge('__query__', node.id, 'entry point');
        } else if (!connected.has(node.id)) {
          addEdge('__query__', node.id, 'retrieved');
        }
      });
    } else {
    responses.forEach((resp) => {
      // Starting nodes
      resp.reasoning_path?.starting_nodes?.forEach((node) => {
        upsertNode(node.id, node.label, node.type, { isStarting: true });
        addEdge('__query__', node.id, 'entry point');
      });

      // Sources
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

      // Expanded nodes
      resp.reasoning_path?.expanded_nodes?.slice(0, 18).forEach((node) => {
        upsertNode(node.id, node.label, node.type, {});
      });

      // Traversed edges
      resp.reasoning_path?.traversed_edges?.slice(0, 36).forEach((edge) => {
        upsertNode(edge.source, edge.source, 'default', {});
        upsertNode(edge.target, edge.target, 'default', {});
        addEdge(edge.source, edge.target, edge.relation);
      });
    });
    }

    // Filter to only connected nodes
    const connectedIds = new Set<string>();
    edgeList.forEach((e) => {
      connectedIds.add(e.source);
      connectedIds.add(e.target);
    });
    // Always include query node
    connectedIds.add('__query__');

    if (connectedIds.size <= 1) {
      // No edges — add all nodes as direct children of query
      nodeMap.forEach((node) => {
        if (node.id !== '__query__') {
          connectedIds.add(node.id);
          addEdge('__query__', node.id, 'related');
        }
      });
    }

    // Build dagre graph
    const g = new dagre.graphlib.Graph();
    g.setGraph({ rankdir: 'LR', ranksep: 80, nodesep: 40, edgesep: 20 });
    g.setDefaultEdgeLabel(() => ({}));

    nodeMap.forEach((node) => {
      if (!connectedIds.has(node.id)) return;
      const isQuery = node.id === '__query__';
      const isSource = node.isSource;
      const width = isQuery ? 120 : isSource ? 140 : 130;
      const height = isQuery ? 44 : isSource ? 48 : 44;
      g.setNode(node.id, { label: node.label, width, height });
    });

    edgeList.forEach((edge) => {
      if (connectedIds.has(edge.source) && connectedIds.has(edge.target)) {
        g.setEdge(edge.source, edge.target);
      }
    });

    dagre.layout(g);

    // Read back positions
    const nodes: DAGNode[] = [];
    const nodeRanks = new Map<string, number>();

    g.nodes().forEach((id) => {
      const dagreNode = g.node(id);
      if (!dagreNode) return;
      const meta = nodeMap.get(id);
      if (!meta) return;

      // Approximate rank from x position
      const rank = Math.round(dagreNode.x / 100);
      nodeRanks.set(id, rank);

      const isQuery = id === '__query__';
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
        rank,
        ref: meta.ref,
        detail: meta.detail,
      });
    });

    const edges: DAGEdge[] = edgeList
      .filter((e) => connectedIds.has(e.source) && connectedIds.has(e.target))
      .map((e) => {
        const sourceNode = nodeMap.get(e.source);
        const sourceType = e.source === '__query__' ? 'query' : sourceNode?.type;
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
  }, [response, allResponses]);

  /* ---- zoom behavior ---- */

  useEffect(() => {
    if (!svgRef.current || !layout || layout.nodes.length === 0) return;

    const svg = d3.select(svgRef.current);
    const gElem = svg.select<SVGGElement>('g.zoom-container');

    // Fit all nodes with padding
    const rect = svgRef.current.getBoundingClientRect();
    const svgWidth = rect.width || 600;
    const svgHeight = rect.height || 400;

    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.4, 2.5])
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

    let minX = Infinity,
      minY = Infinity,
      maxX = -Infinity,
      maxY = -Infinity;
    layout.nodes.forEach((n) => {
      minX = Math.min(minX, n.x - n.width / 2);
      minY = Math.min(minY, n.y - n.height / 2);
      maxX = Math.max(maxX, n.x + n.width / 2);
      maxY = Math.max(maxY, n.y + n.height / 2);
    });

    const graphWidth = maxX - minX;
    const graphHeight = maxY - minY;
    const padding = 40;
    const scale = Math.min(
      (svgWidth - padding * 2) / graphWidth,
      (svgHeight - padding * 2) / graphHeight,
      1.2,
    );
    const tx = svgWidth / 2 - ((minX + maxX) / 2) * scale;
    const ty = svgHeight / 2 - ((minY + maxY) / 2) * scale;

    const initialTransform = d3.zoomIdentity.translate(tx, ty).scale(scale);
    svg.call(zoom.transform, initialTransform);

    return () => {
      svg.on('.zoom', null);
    };
  }, [layout]);

  /* ---- trigger mount animation ---- */

  useEffect(() => {
    if (layout && layout.nodes.length > 0) {
      setMounted(false);
      const raf = requestAnimationFrame(() => setMounted(true));
      return () => cancelAnimationFrame(raf);
    }
  }, [layout]);

  /* ---- path generator ---- */

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

  /* ---- node position lookup ---- */

  const nodePositionMap = useMemo(() => {
    const map = new Map<string, DAGNode>();
    layout?.nodes.forEach((n) => map.set(n.id, n));
    return map;
  }, [layout]);

  /* ---- handlers ---- */

  const handleNodeClick = useCallback(
    (node: DAGNode) => {
      if (node.id === '__query__') return;
      onNodeSelect(node.ref ?? node.id, node.citationIndex);
      // Curated-subgraph nodes carry the KG id they stand for (a frame's debate
      // node, a position's holder, a passage) — open its detail card.
      if (node.ref) {
        onNodeOpen?.(node.ref);
      }
    },
    [onNodeSelect, onNodeOpen],
  );

  /* ---- get theme for a node ---- */

  const getNodeTheme = useCallback((node: DAGNode) => {
    if (node.type === 'query') return QUERY_THEME;
    return getGraphTypeTheme(node.type);
  }, []);

  /* ---- edge midpoints for tooltips ---- */

  const getEdgeMidpoint = useCallback(
    (edge: DAGEdge): [number, number] | null => {
      const s = nodePositionMap.get(edge.source);
      const t = nodePositionMap.get(edge.target);
      if (!s || !t) return null;
      return [(s.x + s.width / 2 + (t.x - t.width / 2)) / 2, (s.y + t.y) / 2];
    },
    [nodePositionMap],
  );

  /* ---- max rank for animation stagger ---- */

  const maxRank = useMemo(() => {
    if (!layout) return 0;
    return Math.max(0, ...layout.nodes.map((n) => n.rank));
  }, [layout]);

  /* ---- empty state ---- */

  if (!layout || layout.nodes.length === 0) {
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

  /* ---- what the curated graph actually contains (counter chip) ---- */

  const curatedStats = response?.reasoning_path?.subgraph?.stats;
  const graphNodeCount = layout.nodes.filter((n) => n.id !== '__query__').length;
  const graphEdgeCount = layout.edges.length;

  /* ---- compute edge path strings ---- */

  const edgePaths = layout.edges.map((edge) => {
    const s = nodePositionMap.get(edge.source);
    const t = nodePositionMap.get(edge.target);
    if (!s || !t) return { ...edge, d: '', sourceRank: 0 };
    const d = pathGenerator({
      source: [s.x + s.width / 2, s.y] as [number, number],
      target: [t.x - t.width / 2, t.y] as [number, number],
    });
    return { ...edge, d: d ?? '', sourceRank: s.rank };
  });

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
        {curatedStats?.truncated && (
          <span className="rounded-full border border-amber-200/80 bg-amber-50/85 px-2 py-0.5 text-[10px] text-amber-700 backdrop-blur">
            top {curatedStats.node_count} of {curatedStats.candidate_nodes}
          </span>
        )}
      </div>
      <svg
        ref={svgRef}
        className="h-full w-full"
        style={{ display: 'block' }}
      >
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
            <feDropShadow dx="0" dy="0" stdDeviation="3" floodColor="#F59E0B" floodOpacity="0.4" />
          </filter>
        </defs>

        <g className="zoom-container">
          {/* ---- edges ---- */}
          {edgePaths.map((ep) => {
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
                {/* invisible wider hit area */}
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

          {/* ---- edge label tooltip ---- */}
          {hoveredEdge &&
            (() => {
              const edge = layout.edges.find(
                (e) => `${e.source}->${e.target}` === hoveredEdge,
              );
              if (!edge) return null;
              const mid = getEdgeMidpoint(edge);
              if (!mid) return null;
              const labelText = edge.relation || 'related';
              const labelWidth = Math.min(labelText.length * 6.5 + 16, 160);

              return (
                <g
                  transform={`translate(${mid[0] - labelWidth / 2}, ${mid[1] - 12})`}
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
                    {truncateLabel(labelText, 22)}
                  </text>
                </g>
              );
            })()}

          {/* ---- nodes ---- */}
          {layout.nodes.map((node) => {
            const theme = getNodeTheme(node);
            const isHighlighted =
              highlightedSourceIndex !== null &&
              node.citationIndex === highlightedSourceIndex;
            const staggerDelay =
              (node.rank / Math.max(maxRank, 1)) * 0.35 + 0.05;

            return (
              <g
                key={node.id}
                transform={`translate(${node.x - node.width / 2}, ${node.y - node.height / 2})`}
                onClick={() => handleNodeClick(node)}
                className={cn(
                  'cursor-pointer',
                  node.id === '__query__' && 'cursor-default',
                )}
                style={{
                  opacity: mounted ? 1 : 0,
                  transition: `opacity 0.4s ease ${staggerDelay}s, transform 0.15s ease`,
                }}
              >
                {/* highlight glow ring */}
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

                {/* node body */}
                <rect
                  width={node.width}
                  height={node.height}
                  rx={12}
                  fill={theme.tint}
                  stroke={isHighlighted ? '#F59E0B' : theme.border}
                  strokeWidth={isHighlighted ? 2 : 1}
                />

                {/* citation badge for source nodes */}
                {node.isSource && node.citationIndex !== undefined && (
                  <>
                    <circle
                      cx={10}
                      cy={10}
                      r={8}
                      fill={theme.color}
                    />
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

                {/* label */}
                <text
                  x={node.width / 2}
                  y={node.height / 2 + 4}
                  textAnchor="middle"
                  fontSize={11}
                  fontWeight={600}
                  fill={theme.text}
                  style={{ userSelect: 'none' }}
                >
                  {truncateLabel(node.label, 18)}
                </text>

                {/* hover area (transparent rect for hover effect) */}
                <rect
                  width={node.width}
                  height={node.height}
                  rx={12}
                  fill="transparent"
                  className="transition-opacity duration-150 hover:fill-black/[0.03]"
                >
                  <title>
                    {node.detail ? `${node.label} — ${node.detail}` : node.label}
                  </title>
                </rect>
              </g>
            );
          })}
        </g>
      </svg>
    </div>
  );
}
