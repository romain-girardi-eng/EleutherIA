import { useDeferredValue, useMemo, useCallback, useEffect } from 'react';
import GraphLegend from './GraphLegend';
import { cn } from '../../utils/cn';
import type { GraphRAGResponse } from '../../types';
import { getGraphTypeTheme } from './graphTheme';

const TYPE_SIZES: Record<string, number> = {
  person: 11,
  school: 10,
  concept: 9,
  argument: 8,
  debate: 8,
  work: 8,
  event: 7,
  quote: 7,
  publication: 7,
  synthesis: 7,
  controversy: 7,
  passage: 5,
  default: 6,
};

const LABEL_WEIGHTS: Record<string, number> = {
  person: 1.0,
  school: 0.9,
  concept: 0.82,
  argument: 0.74,
  debate: 0.68,
  work: 0.62,
  event: 0.54,
  publication: 0.5,
  quote: 0.44,
  passage: 0.24,
  default: 0.34,
};

type GraphPoint = {
  index: number;
  id: string;
  label: string;
  type: string;
  color: string;
  size: number;
  labelWeight: number;
  citationIndex?: number;
  importance: number;
  isSource: boolean;
  isStarting: boolean;
  isExpanded: boolean;
};

type GraphLink = {
  source: string;
  target: string;
  sourceIndex: number;
  targetIndex: number;
  color: string;
};

type AccumulatedNode = {
  id: string;
  label: string;
  type: string;
  isSource: boolean;
  isStarting: boolean;
  isExpanded: boolean;
  citationIndex?: number;
  occurrences: number;
  degree: number;
};

type PositionedNode = GraphPoint & {
  x: number;
  y: number;
  width: number;
  height: number;
  radius: number;
};

function hexToRgb(hex: string): { r: number; g: number; b: number } {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  if (!result) {
    return { r: 138, g: 143, b: 152 };
  }

  return {
    r: parseInt(result[1], 16),
    g: parseInt(result[2], 16),
    b: parseInt(result[3], 16),
  };
}

function rgbToHex(r: number, g: number, b: number): string {
  return (
    '#' +
    [r, g, b]
      .map((value) => {
        const hex = Math.round(value).toString(16);
        return hex.length === 1 ? `0${hex}` : hex;
      })
      .join('')
  );
}

function blendColors(colorA: string, colorB: string): string {
  const a = hexToRgb(colorA);
  const b = hexToRgb(colorB);

  return rgbToHex(
    a.r * 0.55 + b.r * 0.45,
    a.g * 0.55 + b.g * 0.45,
    a.b * 0.55 + b.b * 0.45,
  );
}

function truncateLabel(label: string, maxLength: number) {
  if (label.length <= maxLength) {
    return label;
  }

  return `${label.slice(0, maxLength - 1)}…`;
}

function nodeFrame(point: GraphPoint) {
  const label = truncateLabel(point.label, point.isSource ? 26 : 22);
  const width = Math.max(110, Math.min(220, label.length * 7.4 + 42));
  const height = point.isSource ? 48 : 42;
  const radius = point.isSource ? 16 : 14;

  return { label, width, height, radius };
}

interface CosmographViewProps {
  response: GraphRAGResponse | null;
  allResponses?: GraphRAGResponse[];
  highlightedSourceIndex: number | null;
  onNodeClick: (nodeId: string) => void;
  onSourceSelect?: (citationIndex: number) => void;
  onHighlightRef?: (fn: (citationIndex: number) => void) => void;
  className?: string;
  showControls?: boolean;
}

export default function CosmographView({
  response,
  allResponses,
  highlightedSourceIndex,
  onNodeClick,
  onSourceSelect,
  onHighlightRef,
  className,
}: CosmographViewProps) {
  const deferredResponse = useDeferredValue(response);
  const deferredAllResponses = useDeferredValue(allResponses);

  const graph = useMemo(() => {
    const responses =
      deferredAllResponses && deferredAllResponses.length > 0
        ? deferredAllResponses
        : deferredResponse
          ? [deferredResponse]
          : [];

    if (responses.length === 0) {
      return {
        points: [] as GraphPoint[],
        links: [] as GraphLink[],
        presentTypes: [] as string[],
      };
    }

    const currentResponse = deferredResponse ?? responses[responses.length - 1];
    const nodeMap = new Map<string, AccumulatedNode>();
    const linkSet = new Set<string>();
    const rawLinks: Array<{ source: string; target: string }> = [];

    const upsertNode = (
      id: string,
      label: string,
      type: string,
      flags: Partial<Pick<AccumulatedNode, 'isSource' | 'isStarting' | 'isExpanded' | 'citationIndex'>>,
    ) => {
      if (!id) {
        return;
      }

      const existing = nodeMap.get(id);
      if (existing) {
        existing.occurrences += 1;
        existing.label = existing.label || label || id;
        existing.type = existing.type || type || 'default';
        existing.isSource = existing.isSource || Boolean(flags.isSource);
        existing.isStarting = existing.isStarting || Boolean(flags.isStarting);
        existing.isExpanded = existing.isExpanded || Boolean(flags.isExpanded);
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
        isExpanded: Boolean(flags.isExpanded),
        citationIndex: flags.citationIndex,
        occurrences: 1,
        degree: 0,
      });
    };

    const addLink = (source: string, target: string) => {
      if (!source || !target) {
        return;
      }

      const key = `${source}->${target}`;
      if (linkSet.has(key)) {
        return;
      }

      linkSet.add(key);
      rawLinks.push({ source, target });
    };

    responses.forEach((resp) => {
      resp.sources?.slice(0, 28).forEach((source) => {
        const isCurrentSource = currentResponse?.sources?.some((item) => item.nodeId === source.nodeId);
        const citationIndex =
          isCurrentSource && currentResponse?.sources
            ? currentResponse.sources.findIndex((item) => item.nodeId === source.nodeId)
            : -1;

        upsertNode(source.nodeId, source.nodeLabel, source.nodeType, {
          isSource: true,
          citationIndex: citationIndex >= 0 ? citationIndex : undefined,
        });
      });

      resp.reasoning_path?.starting_nodes?.forEach((node) => {
        upsertNode(node.id, node.label, node.type, { isStarting: true });
      });

      resp.reasoning_path?.expanded_nodes?.slice(0, 22).forEach((node) => {
        upsertNode(node.id, node.label, node.type, { isExpanded: true });
      });

      resp.reasoning_path?.traversed_edges?.slice(0, 42).forEach((edge) => {
        upsertNode(edge.source, edge.source, 'default', {});
        upsertNode(edge.target, edge.target, 'default', {});
        addLink(edge.source, edge.target);
      });
    });

    rawLinks.forEach((link) => {
      const sourceNode = nodeMap.get(link.source);
      const targetNode = nodeMap.get(link.target);
      if (sourceNode) {
        sourceNode.degree += 1;
      }
      if (targetNode) {
        targetNode.degree += 1;
      }
    });

    const orderedNodes = [...nodeMap.values()].sort((a, b) => {
      const aScore =
        (a.isSource ? 400 : 0) +
        (a.isStarting ? 250 : 0) +
        (a.isExpanded ? 80 : 0) +
        a.degree * 18 +
        a.occurrences * 6;
      const bScore =
        (b.isSource ? 400 : 0) +
        (b.isStarting ? 250 : 0) +
        (b.isExpanded ? 80 : 0) +
        b.degree * 18 +
        b.occurrences * 6;
      if (aScore !== bScore) {
        return bScore - aScore;
      }
      return a.label.localeCompare(b.label);
    });

    const idToIndex = new Map<string, number>();
    const idToColor = new Map<string, string>();
    const presentTypes = new Set<string>();

    const points = orderedNodes.map((node, index) => {
      const key = node.type?.toLowerCase() || 'default';
      const theme = getGraphTypeTheme(key);
      const baseSize = TYPE_SIZES[key] ?? TYPE_SIZES.default;
      const size =
        baseSize +
        (node.isSource ? 3.5 : 0) +
        (node.isStarting ? 1.5 : 0) +
        Math.min(node.degree * 0.3, 2);
      const labelWeight =
        (LABEL_WEIGHTS[key] ?? LABEL_WEIGHTS.default) +
        (node.isSource ? 0.18 : 0) +
        (node.isStarting ? 0.08 : 0);
      const importance =
        (node.isSource ? 3 : 0) +
        (node.isStarting ? 2 : 0) +
        (node.isExpanded ? 1 : 0) +
        node.degree;

      idToIndex.set(node.id, index);
      idToColor.set(node.id, theme.color);
      presentTypes.add(key);

      return {
        index,
        id: node.id,
        label: node.label,
        type: node.type,
        color: theme.color,
        size,
        labelWeight,
        citationIndex: node.citationIndex,
        importance,
        isSource: node.isSource,
        isStarting: node.isStarting,
        isExpanded: node.isExpanded,
      };
    });

    const links = rawLinks.reduce<GraphLink[]>((accumulator, link) => {
      const sourceIndex = idToIndex.get(link.source);
      const targetIndex = idToIndex.get(link.target);
      if (sourceIndex === undefined || targetIndex === undefined) {
        return accumulator;
      }

      const sourceColor = idToColor.get(link.source) ?? getGraphTypeTheme().color;
      const targetColor = idToColor.get(link.target) ?? getGraphTypeTheme().color;
      accumulator.push({
        source: link.source,
        target: link.target,
        sourceIndex,
        targetIndex,
        color: blendColors(sourceColor, targetColor),
      });
      return accumulator;
    }, []);

    return {
      points,
      links,
      presentTypes: [...presentTypes],
    };
  }, [deferredAllResponses, deferredResponse]);

  const highlightedNode = useMemo(
    () =>
      highlightedSourceIndex !== null
        ? graph.points.find((point) => point.citationIndex === highlightedSourceIndex) ?? null
        : null,
    [graph.points, highlightedSourceIndex],
  );

  const emitHighlight = useCallback(
    (citationIndex: number) => {
      onSourceSelect?.(citationIndex);
    },
    [onSourceSelect],
  );

  useEffect(() => {
    onHighlightRef?.(emitHighlight);
  }, [emitHighlight, onHighlightRef]);

  const layout = useMemo(() => {
    const width = 920;
    const height = 520;
    const centerX = width / 2;
    const centerY = height / 2 + 8;

    const positioned = new Map<string, PositionedNode>();

    if (graph.points.length === 0) {
      return { width, height, positioned };
    }

    const core = graph.points.filter((point) => point.isSource || point.isStarting);
    const outer = graph.points.filter((point) => !point.isSource && !point.isStarting);

    const primary = core.length > 0 ? core : graph.points;
    const focusNode = primary[0];
    const restPrimary = primary.slice(1);

    const placeNode = (point: GraphPoint, x: number, y: number) => {
      const frame = nodeFrame(point);
      positioned.set(point.id, {
        ...point,
        x,
        y,
        width: frame.width,
        height: frame.height,
        radius: frame.radius,
      });
    };

    placeNode(focusNode, centerX, centerY);

    restPrimary.forEach((point, index) => {
      const angle = (-Math.PI / 2) + (index * (2 * Math.PI)) / Math.max(restPrimary.length, 1);
      const radius = 155 + (index % 2) * 16;
      placeNode(
        point,
        centerX + Math.cos(angle) * radius,
        centerY + Math.sin(angle) * radius * 0.78,
      );
    });

    outer.forEach((point, index) => {
      const ring = Math.floor(index / 8);
      const radius = 235 + ring * 72;
      const angle = (-Math.PI / 2) + ((index % 8) * (2 * Math.PI)) / Math.min(8, Math.max(outer.length, 1));
      placeNode(
        point,
        centerX + Math.cos(angle) * radius,
        centerY + Math.sin(angle) * radius * 0.72,
      );
    });

    return { width, height, positioned };
  }, [graph.points]);

  const handleNodeActivate = useCallback(
    (point: GraphPoint) => {
      if (point.citationIndex !== undefined && onSourceSelect) {
        onSourceSelect(point.citationIndex);
        return;
      }

      onNodeClick(point.id);
    },
    [onNodeClick, onSourceSelect],
  );

  if (graph.points.length === 0) {
    return null;
  }

  return (
    <div
      className={cn(
        'relative h-full w-full overflow-hidden rounded-[28px] border border-white/70 bg-[radial-gradient(circle_at_top_left,_rgba(255,243,220,0.88),_rgba(255,255,255,0.92)_36%,_rgba(247,243,235,0.96)_100%)] shadow-[inset_0_1px_0_rgba(255,255,255,0.85),0_28px_70px_-42px_rgba(120,53,15,0.35)]',
        className,
      )}
    >
      <div
        className="pointer-events-none absolute inset-0 opacity-50"
        style={{
          backgroundImage:
            'linear-gradient(rgba(148, 163, 184, 0.07) 1px, transparent 1px), linear-gradient(90deg, rgba(148, 163, 184, 0.07) 1px, transparent 1px)',
          backgroundSize: '26px 26px',
        }}
      />
      <div className="pointer-events-none absolute -left-16 top-0 h-52 w-52 rounded-full bg-amber-200/25 blur-3xl" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-56 w-56 rounded-full bg-blue-100/35 blur-3xl" />

      <div className="pointer-events-none absolute left-4 top-4 z-20 flex max-w-[calc(100%-2rem)] flex-wrap items-center gap-2">
        <span className="rounded-full border border-amber-200/80 bg-amber-50/92 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-amber-800">
          Answer map
        </span>
        <span className="rounded-full border border-stone-200/80 bg-white/88 px-3 py-1 text-[11px] font-medium text-stone-500">
          {graph.points.length} nodes
        </span>
        <span className="rounded-full border border-stone-200/80 bg-white/88 px-3 py-1 text-[11px] font-medium text-stone-500">
          {graph.links.length} links
        </span>
        {highlightedNode && (
          <span className="rounded-full border border-amber-200/80 bg-white/92 px-3 py-1 text-[11px] font-medium text-stone-700">
            Focus {highlightedNode.label}
          </span>
        )}
      </div>

      <svg
        viewBox={`0 0 ${layout.width} ${layout.height}`}
        className="relative z-10 h-full w-full"
        role="img"
        aria-label="Selected answer knowledge graph"
      >
        {graph.links.map((link) => {
          const source = layout.positioned.get(link.source);
          const target = layout.positioned.get(link.target);
          if (!source || !target) {
            return null;
          }

          const isActive =
            highlightedNode &&
            (highlightedNode.id === link.source || highlightedNode.id === link.target);

          return (
            <line
              key={`${link.source}-${link.target}`}
              x1={source.x}
              y1={source.y}
              x2={target.x}
              y2={target.y}
              stroke={link.color}
              strokeOpacity={isActive ? 0.75 : 0.28}
              strokeWidth={isActive ? 2.2 : 1.35}
            />
          );
        })}

        {[...layout.positioned.values()].map((point) => {
          const theme = getGraphTypeTheme(point.type);
          const isSelected = highlightedNode?.id === point.id;
          const textX = -point.width / 2 + 30;
          const label = truncateLabel(point.label, point.isSource ? 26 : 22);

          return (
            <g
              key={point.id}
              transform={`translate(${point.x}, ${point.y})`}
              onClick={() => handleNodeActivate(point)}
              style={{ cursor: 'pointer' }}
            >
              {isSelected && (
                <rect
                  x={-point.width / 2 - 6}
                  y={-point.height / 2 - 6}
                  width={point.width + 12}
                  height={point.height + 12}
                  rx={point.radius + 6}
                  fill={`${theme.color}14`}
                  stroke={`${theme.color}55`}
                  strokeWidth={1.6}
                />
              )}
              <rect
                x={-point.width / 2}
                y={-point.height / 2}
                width={point.width}
                height={point.height}
                rx={point.radius}
                fill="rgba(255,255,255,0.95)"
                stroke={isSelected ? theme.color : theme.border}
                strokeWidth={isSelected ? 1.8 : 1.1}
              />
              <circle
                cx={-point.width / 2 + 16}
                cy={0}
                r={point.isSource ? 6.5 : 5.5}
                fill={theme.color}
              />
              <text
                x={textX}
                y={1}
                fill="#292524"
                fontSize={13}
                fontWeight={point.isSource ? 700 : 600}
                dominantBaseline="middle"
              >
                {label}
              </text>
              {point.citationIndex !== undefined && (
                <text
                  x={point.width / 2 - 12}
                  y={-point.height / 2 + 14}
                  fill={theme.text}
                  fontSize={11}
                  fontWeight={700}
                  textAnchor="end"
                >
                  {point.citationIndex + 1}
                </text>
              )}
            </g>
          );
        })}
      </svg>

      <div className="pointer-events-none absolute bottom-4 left-4 z-20">
        <GraphLegend types={graph.presentTypes} />
      </div>
    </div>
  );
}
