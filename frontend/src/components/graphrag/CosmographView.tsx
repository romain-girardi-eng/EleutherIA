import { useMemo, useCallback, useEffect, useState } from 'react';
import { Cosmograph, CosmographProvider, useCosmograph } from '@cosmograph/react';
import { Maximize2, Pause, Play } from 'lucide-react';
import GraphLegend from './GraphLegend';
import { cn } from '../../utils/cn';
import type { GraphRAGResponse } from '../../types';

const NODE_COLORS: Record<string, string> = {
  person: '#60A5FA',
  concept: '#4ADE80',
  argument: '#C084FC',
  work: '#FBBF24',
  school: '#4ADE80',
  debate: '#FB7185',
  quote: '#FACC15',
  passage: '#94A3B8',
  publication: '#06B6D4',
  default: '#94A3B8',
};

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
          // Fallback: just fit view if selection fails
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
        { icon: isPaused ? Play : Pause, onClick: handleTogglePause, label: isPaused ? 'Resume' : 'Pause' },
      ].map(({ icon: Icon, onClick, label }) => (
        <button
          key={label}
          onClick={onClick}
          className="flex items-center justify-center w-8 h-8 rounded-lg bg-white/90 border border-gray-200 text-gray-500 hover:text-gray-700 hover:border-gray-300 shadow-sm transition-all hover:shadow"
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
    // Build graph from all accumulated responses (or just the current one)
    const responses = allResponses?.length ? allResponses : response ? [response] : [];
    if (responses.length === 0) return { points: [] as Record<string, unknown>[], links: [] as Record<string, unknown>[] };

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

    const points: Record<string, unknown>[] = [];
    let idx = 0;
    for (const [, node] of nodeMap) {
      points.push({
        index: idx,
        id: node.id,
        label: node.label,
        type: node.type,
        color: NODE_COLORS[node.type?.toLowerCase()] ?? NODE_COLORS.default,
        size: 8,
      });
      idx++;
    }

    // Filter links to only include those where both endpoints exist
    const nodeIds = new Set(nodeMap.keys());
    const links: Record<string, unknown>[] = [];
    for (const l of allLinks) {
      if (nodeIds.has(l.source) && nodeIds.has(l.target)) {
        links.push({ source: l.source, target: l.target });
      }
    }

    // If no edges but we have nodes, create star topology from first node
    if (links.length === 0 && points.length > 1) {
      const firstId = points[0].id as string;
      for (let i = 1; i < Math.min(points.length, 8); i++) {
        links.push({ source: firstId, target: points[i].id as string });
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
    <div className={cn('relative w-full h-full', className)}>
      <CosmographProvider>
        <Cosmograph
          points={points}
          links={links}
          pointIndexBy="index"
          pointIdBy="id"
          pointColorBy="color"
          pointSizeBy="size"
          pointLabelBy="label"
          linkSourceBy="source"
          linkTargetBy="target"
          linkDefaultColor="#D1D5DB"
          linkDefaultWidth={1}
          backgroundColor="#ffffff"
          simulationRepulsion={0.5}
          simulationLinkSpring={1.0}
          simulationLinkDistance={5}
          simulationGravity={0.15}
          simulationDecay={3000}
          showDynamicLabels
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
