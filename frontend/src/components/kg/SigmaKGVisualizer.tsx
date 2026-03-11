// frontend/src/components/kg/SigmaKGVisualizer.tsx
import { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import Graph from 'graphology';
import {
  SigmaContainer,
  useSigma,
  useRegisterEvents,
  useLoadGraph,
} from '@react-sigma/core';
import '@react-sigma/core/lib/style.css';

import type { CytoscapeData, KGNode } from '@/types';
import type { KGNodeAttributes, KGEdgeAttributes } from '@/types/sigma';
import { ZoomLevel } from '@/types/sigma';

import { buildGraph } from '@/services/graphologyAdapter';
import { detectCommunities } from '@/services/communityDetection';
import { aggregatePassages, expandWorkPassages, collapseWorkPassages } from './PassageAggregation';
import { getZoomLevel } from './SemanticZoomController';
import { createEdgeReducer } from './EdgeFilterReducer';
import { createNodeReducer } from './NodeReducer';
import CommunityHullsLayer from './CommunityHullsLayer';
import { getGraphTypeTheme } from '@/components/graphrag/graphTheme';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface SigmaKGVisualizerProps {
  cyData: CytoscapeData;
  onNodeSelect?: (node: KGNode | null) => void;
  className?: string;
}

interface LayoutPositions {
  [nodeId: string]: { x: number; y: number };
}

// ---------------------------------------------------------------------------
// Community metadata helpers
// ---------------------------------------------------------------------------

function buildCommunityColors(
  graph: Graph<KGNodeAttributes, KGEdgeAttributes>,
  communities: Map<number, Set<string>>,
): Map<number, string> {
  const colors = new Map<number, string>();
  for (const [communityId, nodeIds] of communities) {
    // Count node types in this community to find dominant type
    const typeCounts = new Map<string, number>();
    for (const nodeId of nodeIds) {
      try {
        const t = graph.getNodeAttribute(nodeId, 'type') ?? 'default';
        typeCounts.set(t, (typeCounts.get(t) ?? 0) + 1);
      } catch {
        // node may not exist
      }
    }
    let dominantType = 'default';
    let maxCount = 0;
    for (const [t, count] of typeCounts) {
      if (count > maxCount) {
        maxCount = count;
        dominantType = t;
      }
    }
    colors.set(communityId, getGraphTypeTheme(dominantType).color);
  }
  return colors;
}

function buildCommunityLabels(
  graph: Graph<KGNodeAttributes, KGEdgeAttributes>,
  communities: Map<number, Set<string>>,
): Map<number, string> {
  const labels = new Map<number, string>();
  for (const [communityId, nodeIds] of communities) {
    let bestNode = '';
    let bestDegree = -1;
    for (const nodeId of nodeIds) {
      try {
        const degree = graph.degree(nodeId);
        if (degree > bestDegree) {
          bestDegree = degree;
          bestNode = nodeId;
        }
      } catch {
        // node may not exist
      }
    }
    if (bestNode) {
      labels.set(communityId, graph.getNodeAttribute(bestNode, 'label') ?? bestNode);
    }
  }
  return labels;
}

// ---------------------------------------------------------------------------
// Sigma settings (dark theme)
// ---------------------------------------------------------------------------

const SIGMA_SETTINGS = {
  renderLabels: true,
  labelRenderedSizeThreshold: 6,
  labelFont: 'Inter, system-ui, sans-serif',
  labelColor: { color: '#e2e8f0' },
  labelSize: 12,
  defaultEdgeColor: 'rgba(255,255,255,0.15)',
  defaultEdgeType: 'line',
  defaultNodeColor: '#8A8F98',
  minCameraRatio: 0.02,
  maxCameraRatio: 5,
  zoomDuration: 300,
  inertiaDuration: 300,
  zIndex: true,
} as const;

// ---------------------------------------------------------------------------
// Inner component that lives inside SigmaContainer (has access to useSigma)
// ---------------------------------------------------------------------------

interface SigmaGraphProps {
  graph: Graph<KGNodeAttributes, KGEdgeAttributes>;
  communities: Map<number, Set<string>>;
  communityColors: Map<number, string>;
  communityLabels: Map<number, string>;
  hiddenPassages: Set<string>;
  onNodeSelect?: (node: KGNode | null) => void;
}

function SigmaGraph({
  graph,
  communities,
  communityColors,
  communityLabels,
  hiddenPassages,
  onNodeSelect,
}: SigmaGraphProps) {
  const sigma = useSigma();
  const loadGraph = useLoadGraph();
  const registerEvents = useRegisterEvents();

  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [zoomLevel, setZoomLevel] = useState<ZoomLevel>(ZoomLevel.Overview);
  const [hoveredNeighbors, setHoveredNeighbors] = useState<Set<string>>(new Set());
  const expandedWorksRef = useRef<Set<string>>(new Set());
  const hiddenRef = useRef<Set<string>>(hiddenPassages);

  // Keep hiddenRef in sync
  useEffect(() => {
    hiddenRef.current = hiddenPassages;
  }, [hiddenPassages]);

  // Load graph into Sigma
  useEffect(() => {
    loadGraph(graph);
  }, [graph, loadGraph]);

  // Track camera zoom level
  useEffect(() => {
    const camera = sigma.getCamera();
    const handleUpdate = () => {
      setZoomLevel(getZoomLevel(camera.ratio));
    };
    camera.addListener('updated', handleUpdate);
    // Set initial zoom level
    handleUpdate();
    return () => {
      camera.removeListener('updated', handleUpdate);
    };
  }, [sigma]);

  // Compute hovered neighbors when hovered node changes
  useEffect(() => {
    if (!hoveredNode) {
      setHoveredNeighbors(new Set());
      return;
    }
    try {
      const g = sigma.getGraph();
      const neighbors = new Set<string>();
      g.forEachNeighbor(hoveredNode, (neighbor) => {
        neighbors.add(neighbor);
      });
      setHoveredNeighbors(neighbors);
    } catch {
      setHoveredNeighbors(new Set());
    }
  }, [hoveredNode, sigma]);

  // Register Sigma events
  useEffect(() => {
    registerEvents({
      enterNode: (event) => setHoveredNode(event.node),
      leaveNode: () => setHoveredNode(null),
      clickNode: (event) => {
        const g = sigma.getGraph();
        const nodeId = event.node;

        // Toggle passage expansion for aggregate work nodes
        try {
          const attrs = g.getNodeAttributes(nodeId);
          if (attrs.isAggregate && attrs.type === 'work') {
            if (attrs.passagesExpanded) {
              collapseWorkPassages(g, nodeId, hiddenRef.current);
              expandedWorksRef.current.delete(nodeId);
            } else {
              expandWorkPassages(g, nodeId, hiddenRef.current);
              expandedWorksRef.current.add(nodeId);
            }
            sigma.refresh();
            return;
          }
        } catch {
          // ignore
        }

        // Select node and notify parent
        if (selectedNode === nodeId) {
          setSelectedNode(null);
          onNodeSelect?.(null);
        } else {
          setSelectedNode(nodeId);
          try {
            const attrs = g.getNodeAttributes(nodeId);
            onNodeSelect?.({
              id: attrs.originalId,
              label: attrs.label,
              type: attrs.type,
              description: attrs.description,
              period: attrs.period,
              metadata: attrs.metadata as KGNode['metadata'],
            });
          } catch {
            // ignore
          }
        }
      },
      clickStage: () => {
        setSelectedNode(null);
        onNodeSelect?.(null);
      },
    });
  }, [sigma, registerEvents, selectedNode, onNodeSelect]);

  // Build node degrees map
  const nodeDegrees = useMemo(() => {
    const degrees = new Map<string, number>();
    try {
      const g = sigma.getGraph();
      g.forEachNode((node) => {
        degrees.set(node, g.degree(node));
      });
    } catch {
      // graph not yet loaded
    }
    return degrees;
  }, [sigma, graph]); // eslint-disable-line react-hooks/exhaustive-deps

  // Apply node/edge reducers via sigma settings
  useEffect(() => {
    const nodeReducer = createNodeReducer({
      zoomLevel,
      hoveredNode,
      selectedNode,
      hiddenNodes: hiddenRef.current,
      nodeDegrees,
      expandedWorks: expandedWorksRef.current,
      hoveredNeighbors,
    });

    const edgeReducer = createEdgeReducer({
      zoomLevel,
      hoveredNode,
      selectedNode,
      hiddenNodes: hiddenRef.current,
    });

    sigma.setSetting('nodeReducer', nodeReducer as Parameters<typeof sigma.setSetting<'nodeReducer'>>[1]);
    sigma.setSetting('edgeReducer', edgeReducer as Parameters<typeof sigma.setSetting<'edgeReducer'>>[1]);
  }, [sigma, zoomLevel, hoveredNode, selectedNode, nodeDegrees, hoveredNeighbors]);

  return (
    <CommunityHullsLayer
      communities={communities}
      communityColors={communityColors}
      communityLabels={communityLabels}
    />
  );
}

// ---------------------------------------------------------------------------
// Main orchestrator component
// ---------------------------------------------------------------------------

export default function SigmaKGVisualizer({
  cyData,
  onNodeSelect,
  className,
}: SigmaKGVisualizerProps) {
  const [layoutReady, setLayoutReady] = useState(false);
  const graphRef = useRef<Graph<KGNodeAttributes, KGEdgeAttributes> | null>(null);
  const [communities, setCommunities] = useState<Map<number, Set<string>>>(new Map());
  const [communityColors, setCommunityColors] = useState<Map<number, string>>(new Map());
  const [communityLabels, setCommunityLabels] = useState<Map<number, string>>(new Map());
  const [hiddenPassages, setHiddenPassages] = useState<Set<string>>(new Set());
  const workerRef = useRef<Worker | null>(null);

  // Build graph, detect communities, aggregate passages, launch layout worker
  useEffect(() => {
    if (!cyData.elements?.nodes?.length) return;

    setLayoutReady(false);

    // 1. Build Graphology graph
    const graph = buildGraph(cyData);
    graphRef.current = graph;

    // 2. Detect communities
    const communityMap = detectCommunities(graph);
    setCommunities(communityMap);
    setCommunityColors(buildCommunityColors(graph, communityMap));
    setCommunityLabels(buildCommunityLabels(graph, communityMap));

    // 3. Aggregate passages (hide individual passages, badge work nodes)
    const hidden = aggregatePassages(graph);
    setHiddenPassages(hidden);

    // 4. Launch layout Web Worker
    const nodes: [string, KGNodeAttributes][] = [];
    graph.forEachNode((key, attrs) => {
      nodes.push([key, { ...attrs }]);
    });

    const edges: [string, string, string, KGEdgeAttributes][] = [];
    graph.forEachEdge((key, attrs, source, target) => {
      edges.push([key, source, target, { ...attrs }]);
    });

    const worker = new Worker(
      new URL('../../workers/layoutWorkerEntry.ts', import.meta.url),
      { type: 'module' },
    );
    workerRef.current = worker;

    worker.onmessage = (event: MessageEvent) => {
      const { type, positions } = event.data as {
        type: string;
        positions: LayoutPositions;
      };
      if (type === 'layout-complete' && graphRef.current) {
        // Apply computed positions back to the graph
        for (const [nodeId, pos] of Object.entries(positions)) {
          try {
            graphRef.current.setNodeAttribute(nodeId, 'x', pos.x);
            graphRef.current.setNodeAttribute(nodeId, 'y', pos.y);
          } catch {
            // node may have been removed
          }
        }
        setLayoutReady(true);
      }
    };

    worker.postMessage({
      type: 'run-layout',
      payload: { nodes, edges, options: {} },
    });

    return () => {
      worker.terminate();
      workerRef.current = null;
    };
  }, [cyData]);

  const graph = graphRef.current;

  if (!graph || !layoutReady) {
    return (
      <div className={`flex items-center justify-center h-full w-full bg-slate-950 ${className ?? ''}`}>
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-slate-600 border-t-blue-400" />
          <span className="text-sm text-slate-400">Computing layout...</span>
        </div>
      </div>
    );
  }

  return (
    <div className={`relative h-full w-full bg-slate-950 ${className ?? ''}`}>
      <SigmaContainer
        graph={graph}
        settings={SIGMA_SETTINGS}
        style={{ width: '100%', height: '100%', background: 'transparent' }}
      >
        <SigmaGraph
          graph={graph}
          communities={communities}
          communityColors={communityColors}
          communityLabels={communityLabels}
          hiddenPassages={hiddenPassages}
          onNodeSelect={onNodeSelect}
        />
      </SigmaContainer>
    </div>
  );
}
