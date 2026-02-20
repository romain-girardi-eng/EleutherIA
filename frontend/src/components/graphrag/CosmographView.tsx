import { useMemo, useCallback, useEffect, useState } from 'react';
import { Cosmograph, CosmographProvider, useCosmograph } from '@cosmograph/react';
import { Maximize2, Pause, Play } from 'lucide-react';
import GraphLegend from './GraphLegend';
import { cn } from '../../utils/cn';
import type { GraphRAGResponse } from '../../types';

// Vibrant neon colors matching the main KG visualizer
const TYPE_COLORS: Record<string, string> = {
  person: '#60a5fa',
  work: '#fbbf24',
  concept: '#c084fc',
  argument: '#f472b6',
  debate: '#fb7185',
  school: '#4ade80',
  event: '#fb923c',
  quote: '#facc15',
  reformulation: '#a78bfa',
  passage: '#94a3b8',
  publication: '#06b6d4',
  synthesis: '#10b981',
  controversy: '#f43f5e',
  conceptual_evolution: '#818cf8',
  group: '#84cc16',
  argument_framework: '#e879f9',
  default: '#94a3b8',
};

// Size by type importance
const TYPE_SIZES: Record<string, number> = {
  person: 18,
  school: 16,
  concept: 14,
  argument: 14,
  debate: 13,
  work: 12,
  event: 11,
  quote: 10,
  passage: 8,
  publication: 10,
  default: 10,
};

// Label weight by type (higher = shown first)
const LABEL_WEIGHTS: Record<string, number> = {
  person: 10,
  school: 9,
  concept: 8,
  argument: 7,
  debate: 7,
  work: 6,
  event: 5,
  publication: 4,
  quote: 3,
  passage: 2,
  default: 1,
};

// --- Color blending for edges (matches main visualizer) ---

function hexToRgb(hex: string): { r: number; g: number; b: number } {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  if (!result) return { r: 148, g: 163, b: 184 };
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
      .map((x) => {
        const hex = Math.round(x).toString(16);
        return hex.length === 1 ? '0' + hex : hex;
      })
      .join('')
  );
}

function blendColors(c1: string, c2: string): string {
  const a = hexToRgb(c1);
  const b = hexToRgb(c2);
  return rgbToHex((a.r + b.r) / 2, (a.g + b.g) / 2, (a.b + b.b) / 2);
}

// -----------------------------------------------------------

function InnerControls({
  points,
  highlightedNodeIndex,
  onHighlightRef,
  showControls,
}: {
  points: Record<string, unknown>[];
  highlightedNodeIndex: number | null;
  onHighlightRef?: (fn: (citationIndex: number) => void) => void;
  showControls: boolean;
}) {
  const { cosmograph } = useCosmograph();
  const [isPaused, setIsPaused] = useState(false);

  const highlightNode = useCallback(
    (citationIndex: number) => {
      const point = points[citationIndex];
      if (point && cosmograph) {
        try {
          cosmograph.selectPoint(point.index as number, false, true);
          cosmograph.zoomToPoint(point.index as number, 800, 1.5, true);
        } catch {
          cosmograph.fitView(400, 0.1);
        }
      }
    },
    [points, cosmograph],
  );

  useEffect(() => {
    onHighlightRef?.(highlightNode);
  }, [highlightNode, onHighlightRef]);

  useEffect(() => {
    if (highlightedNodeIndex !== null) highlightNode(highlightedNodeIndex);
  }, [highlightedNodeIndex, highlightNode]);

  const handleFitView = () => cosmograph?.fitView(400, 0.1);
  const handleTogglePause = () => {
    if (isPaused) cosmograph?.start();
    else cosmograph?.pause();
    setIsPaused(!isPaused);
  };

  if (!showControls) return null;

  return (
    <div className="absolute top-3 right-3 flex flex-col gap-1.5 z-10">
      {[
        { icon: Maximize2, onClick: handleFitView, label: 'Fit view' },
        {
          icon: isPaused ? Play : Pause,
          onClick: handleTogglePause,
          label: isPaused ? 'Resume' : 'Pause',
        },
      ].map(({ icon: Icon, onClick, label }) => (
        <button
          key={label}
          onClick={onClick}
          className="flex items-center justify-center w-8 h-8 rounded-lg bg-white/10 backdrop-blur-sm border border-white/10 text-white/60 hover:text-white hover:bg-white/15 hover:border-white/20 shadow-sm transition-all"
          aria-label={label}
          title={label}
        >
          <Icon className="w-3.5 h-3.5" />
        </button>
      ))}
    </div>
  );
}

interface CosmographViewProps {
  response: GraphRAGResponse | null;
  /** All accumulated responses from the conversation for building a growing graph */
  allResponses?: GraphRAGResponse[];
  highlightedNodeIndex: number | null;
  onNodeClick: (nodeId: string) => void;
  onHighlightRef?: (fn: (citationIndex: number) => void) => void;
  className?: string;
  showControls?: boolean;
}

export default function CosmographView({
  response,
  allResponses,
  highlightedNodeIndex,
  onNodeClick,
  onHighlightRef,
  className,
  showControls = true,
}: CosmographViewProps) {
  const { points, links } = useMemo(() => {
    const responses = allResponses?.length ? allResponses : response ? [response] : [];
    if (responses.length === 0)
      return {
        points: [] as Record<string, unknown>[],
        links: [] as Record<string, unknown>[],
      };

    const nodeMap = new Map<string, { id: string; label: string; type: string }>();
    const addNode = (id: string, label: string, type: string) => {
      if (!nodeMap.has(id)) nodeMap.set(id, { id, label, type });
    };

    const linkSet = new Set<string>();
    const allLinks: { source: string; target: string }[] = [];
    const addLink = (source: string, target: string) => {
      const key = `${source}->${target}`;
      if (!linkSet.has(key)) {
        linkSet.add(key);
        allLinks.push({ source, target });
      }
    };

    for (const resp of responses) {
      resp.sources?.slice(0, 25).forEach((s) => addNode(s.nodeId, s.nodeLabel, s.nodeType));
      resp.reasoning_path?.starting_nodes?.forEach((n) => addNode(n.id, n.label, n.type));
      resp.reasoning_path?.expanded_nodes?.slice(0, 15).forEach((n) => addNode(n.id, n.label, n.type));

      if (resp.reasoning_path?.traversed_edges) {
        resp.reasoning_path.traversed_edges.slice(0, 30).forEach((e) => {
          addLink(e.source, e.target);
        });
      }
    }

    const idToIndex = new Map<string, number>();
    const idToColor = new Map<string, string>();
    const points: Record<string, unknown>[] = [];
    let idx = 0;
    for (const [, node] of nodeMap) {
      const typeLower = node.type?.toLowerCase() ?? 'default';
      const color = TYPE_COLORS[typeLower] ?? TYPE_COLORS.default;
      const size = TYPE_SIZES[typeLower] ?? TYPE_SIZES.default;
      const labelWeight = LABEL_WEIGHTS[typeLower] ?? LABEL_WEIGHTS.default;

      idToIndex.set(node.id, idx);
      idToColor.set(node.id, color);
      points.push({
        index: idx,
        id: node.id,
        label: node.label,
        type: node.type,
        color,
        size,
        labelWeight,
      });
      idx++;
    }

    // Build links with blended colors (both ID and index columns required by Cosmograph)
    const links: Record<string, unknown>[] = [];
    for (const l of allLinks) {
      const si = idToIndex.get(l.source);
      const ti = idToIndex.get(l.target);
      if (si !== undefined && ti !== undefined) {
        const srcColor = idToColor.get(l.source) ?? TYPE_COLORS.default;
        const tgtColor = idToColor.get(l.target) ?? TYPE_COLORS.default;
        links.push({
          source: l.source,
          target: l.target,
          sourceIndex: si,
          targetIndex: ti,
          sourceColor: srcColor,
          targetColor: tgtColor,
          color: blendColors(srcColor, tgtColor),
        });
      }
    }

    // Star topology fallback when no edges exist
    if (links.length === 0 && points.length > 1) {
      const firstId = points[0].id as string;
      const firstColor = points[0].color as string;
      for (let i = 1; i < Math.min(points.length, 8); i++) {
        const tgtColor = points[i].color as string;
        links.push({
          source: firstId,
          target: points[i].id as string,
          sourceIndex: 0,
          targetIndex: i,
          sourceColor: firstColor,
          targetColor: tgtColor,
          color: blendColors(firstColor, tgtColor),
        });
      }
    }

    return { points, links };
  }, [response, allResponses]);

  const handleClick = useCallback(
    (clickedIndex: number | undefined) => {
      if (clickedIndex !== undefined && clickedIndex < points.length) {
        onNodeClick(points[clickedIndex].id as string);
      }
    },
    [onNodeClick, points],
  );

  if (points.length === 0) return null;

  return (
    <div className={cn('relative w-full h-full rounded-xl overflow-hidden', className)}>
      <CosmographProvider>
        <Cosmograph
          points={points}
          links={links}
          // Point identification
          pointIndexBy="index"
          pointIdBy="id"
          pointColorBy="color"
          pointSizeBy="size"
          pointLabelBy="label"
          pointLabelWeightBy="labelWeight"
          // Link identification (all four required by Cosmograph v2)
          linkSourceBy="source"
          linkSourceIndexBy="sourceIndex"
          linkTargetBy="target"
          linkTargetIndexBy="targetIndex"
          // Link styling - blended colors
          linkColorBy="color"
          linkDefaultWidth={0.5}
          linkDefaultArrows
          linkArrowsSizeScale={0.3}
          // Dark canvas matching main KG visualizer
          backgroundColor="#020617"
          spaceSize={4096}
          pointSizeRange={[4, 30]}
          pointSizeScale={1.0}
          scalePointsOnZoom
          scaleLinksOnZoom
          // Labels
          showLabels
          showDynamicLabels
          showTopLabels
          showTopLabelsLimit={30}
          showHoveredPointLabel
          pointLabelClassName="cosmograph-point-label"
          hoveredPointLabelClassName="cosmograph-hovered-label"
          // Selection & hover
          pointGreyoutOpacity={0.15}
          linkGreyoutOpacity={0.05}
          renderHoveredPointRing
          hoveredPointRingColor="#8b5cf6"
          // Interaction
          selectPointOnClick
          focusPointOnClick
          // Disable physics for a static, clean layout
          enableSimulation={false}
          // Fit view on init
          fitViewOnInit
          fitViewDelay={200}
          onClick={handleClick}
          style={{ width: '100%', height: '100%' }}
        />
        <InnerControls
          points={points}
          highlightedNodeIndex={highlightedNodeIndex}
          onHighlightRef={onHighlightRef}
          showControls={showControls}
        />
      </CosmographProvider>

      <GraphLegend className="absolute bottom-3 left-3 z-10" />
    </div>
  );
}
