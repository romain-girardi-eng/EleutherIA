import { useDeferredValue, useMemo, useCallback, useEffect, useState } from 'react';
import { Cosmograph, CosmographProvider, useCosmograph } from '@cosmograph/react';
import { Maximize2, Pause, Play } from 'lucide-react';
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

function toPercent(value?: number): string {
  if (value === undefined || Number.isNaN(value)) {
    return '--';
  }

  const normalized = value <= 1 ? value * 100 : value;
  return `${Math.round(normalized)}%`;
}

function ControlButton({
  icon: Icon,
  label,
  onClick,
}: {
  icon: typeof Maximize2;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="pointer-events-auto inline-flex h-10 w-10 items-center justify-center rounded-2xl border border-stone-200/80 bg-white/88 text-stone-600 shadow-[0_16px_36px_-28px_rgba(120,53,15,0.4)] backdrop-blur-xl transition-all hover:-translate-y-0.5 hover:border-amber-300/70 hover:text-stone-900"
      aria-label={label}
      title={label}
      type="button"
    >
      <Icon className="h-4 w-4" />
    </button>
  );
}

function InnerControls({
  points,
  sourcePointIndexByCitation,
  highlightedSourceIndex,
  onHighlightRef,
  showControls,
}: {
  points: GraphPoint[];
  sourcePointIndexByCitation: Map<number, number>;
  highlightedSourceIndex: number | null;
  onHighlightRef?: (fn: (citationIndex: number) => void) => void;
  showControls: boolean;
}) {
  const { cosmograph } = useCosmograph();
  const [isPaused, setIsPaused] = useState(false);

  const highlightNode = useCallback(
    (citationIndex: number) => {
      const pointIndex = sourcePointIndexByCitation.get(citationIndex);
      if (pointIndex === undefined || !cosmograph) {
        return;
      }

      const point = points[pointIndex];
      if (!point) {
        return;
      }

      try {
        cosmograph.selectPoint(point.index, false, true);
        cosmograph.zoomToPoint(point.index, 700, 1.45, true);
      } catch {
        cosmograph.fitView(450, 0.14);
      }
    },
    [cosmograph, points, sourcePointIndexByCitation],
  );

  useEffect(() => {
    onHighlightRef?.(highlightNode);
  }, [highlightNode, onHighlightRef]);

  useEffect(() => {
    if (highlightedSourceIndex !== null) {
      highlightNode(highlightedSourceIndex);
    }
  }, [highlightNode, highlightedSourceIndex]);

  if (!showControls) {
    return null;
  }

  const handleFitView = () => cosmograph?.fitView(450, 0.14);
  const handleTogglePause = () => {
    if (!cosmograph) {
      return;
    }

    if (isPaused) {
      cosmograph.start();
    } else {
      cosmograph.pause();
    }

    setIsPaused((current) => !current);
  };

  return (
    <div className="pointer-events-none absolute right-4 top-4 z-20 flex items-center gap-2">
      <ControlButton icon={Maximize2} label="Center graph" onClick={handleFitView} />
      <ControlButton
        icon={isPaused ? Play : Pause}
        label={isPaused ? 'Resume simulation' : 'Pause simulation'}
        onClick={handleTogglePause}
      />
    </div>
  );
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
  showControls = true,
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
        sourcePointIndexByCitation: new Map<number, number>(),
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
    const sourcePointIndexByCitation = new Map<number, number>();
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
      if (node.citationIndex !== undefined) {
        sourcePointIndexByCitation.set(node.citationIndex, index);
      }

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
      sourcePointIndexByCitation,
      presentTypes: [...presentTypes],
    };
  }, [deferredAllResponses, deferredResponse]);

  const currentSources = deferredResponse?.sources ?? [];
  const highlightedSource = highlightedSourceIndex !== null ? currentSources[highlightedSourceIndex] : null;
  const confidence = deferredResponse?.quality_metrics?.confidence_score;

  const handleClick = useCallback(
    (clickedIndex: number | undefined) => {
      if (clickedIndex === undefined) {
        return;
      }

      const point = graph.points[clickedIndex];
      if (!point) {
        return;
      }

      if (point.citationIndex !== undefined && onSourceSelect) {
        onSourceSelect(point.citationIndex);
        return;
      }

      onNodeClick(point.id);
    },
    [graph.points, onNodeClick, onSourceSelect],
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

      <div className="pointer-events-none absolute left-4 top-4 z-20 max-w-[calc(100%-7rem)]">
        <div className="rounded-[24px] border border-stone-200/80 bg-white/82 px-4 py-3 shadow-[0_18px_42px_-30px_rgba(120,53,15,0.32)] backdrop-blur-xl">
          <div className="flex flex-wrap items-center gap-2 text-[11px] font-medium uppercase tracking-[0.22em] text-stone-400">
            <span className="rounded-full bg-amber-50 px-2.5 py-1 text-amber-700">Selected answer graph</span>
            <span>{graph.points.length} nodes</span>
            <span>{graph.links.length} links</span>
            <span>{currentSources.length} sources</span>
          </div>
          <p className="mt-2 text-sm font-semibold leading-6 text-stone-900 line-clamp-2">
            {deferredResponse?.query || 'The graph is built from the citations and traversal that support the current answer.'}
          </p>
          <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-stone-500">
            <span className="rounded-full border border-stone-200/80 bg-stone-50/80 px-2.5 py-1">
              Confidence {toPercent(confidence)}
            </span>
            {highlightedSource && (
              <span className="rounded-full border border-amber-200/80 bg-amber-50/90 px-2.5 py-1 text-amber-800">
                Focus {highlightedSource.id}. {highlightedSource.nodeLabel}
              </span>
            )}
          </div>
        </div>
      </div>

      <CosmographProvider>
        <Cosmograph
          points={graph.points}
          links={graph.links}
          pointIndexBy="index"
          pointIdBy="id"
          pointColorBy="color"
          pointSizeBy="size"
          pointLabelBy="label"
          pointLabelWeightBy="labelWeight"
          linkSourceBy="source"
          linkSourceIndexBy="sourceIndex"
          linkTargetBy="target"
          linkTargetIndexBy="targetIndex"
          linkColorBy="color"
          linkDefaultWidth={0.38}
          linkDefaultArrows={false}
          backgroundColor="#faf7f0"
          spaceSize={2048}
          pointSizeRange={[4, 18]}
          pointSizeScale={1}
          scalePointsOnZoom
          scaleLinksOnZoom
          showLabels
          showDynamicLabels
          showDynamicLabelsLimit={12}
          showTopLabels
          showTopLabelsLimit={14}
          showUnselectedPointLabels={false}
          selectedPointLabelsLimit={18}
          pointLabelFontSize={11}
          labelPadding={[4, 2, 4, 2]}
          labelMargin={5}
          showHoveredPointLabel
          pointLabelClassName="cosmograph-point-label"
          hoveredPointLabelClassName="cosmograph-hovered-label"
          enableDrag
          selectPointOnClick
          focusPointOnClick
          renderHoveredPointRing
          hoveredPointRingColor="#f59e0b"
          pointGreyoutOpacity={0.1}
          linkGreyoutOpacity={0.08}
          enableSimulation
          simulationRepulsion={1.18}
          simulationGravity={0.17}
          simulationCenter={0.09}
          simulationLinkSpring={0.9}
          simulationLinkDistance={28}
          simulationFriction={0.88}
          simulationDecay={2600}
          preservePointPositionsOnDataUpdate
          fitViewOnInit
          fitViewDelay={200}
          onClick={handleClick}
          style={{ width: '100%', height: '100%' }}
        />

        <InnerControls
          points={graph.points}
          sourcePointIndexByCitation={graph.sourcePointIndexByCitation}
          highlightedSourceIndex={highlightedSourceIndex}
          onHighlightRef={onHighlightRef}
          showControls={showControls}
        />
      </CosmographProvider>

      <div className="pointer-events-none absolute bottom-4 left-4 z-20">
        <GraphLegend types={graph.presentTypes} />
      </div>

      <div className="pointer-events-none absolute bottom-4 right-4 z-20 rounded-2xl border border-stone-200/80 bg-white/80 px-3.5 py-2.5 text-right shadow-[0_16px_36px_-28px_rgba(120,53,15,0.32)] backdrop-blur-xl">
        <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-stone-400">
          Smooth exploration
        </p>
        <p className="mt-1 text-xs text-stone-600">
          Drag to recompose the map. Click a source node to open its evidence card.
        </p>
      </div>
    </div>
  );
}
