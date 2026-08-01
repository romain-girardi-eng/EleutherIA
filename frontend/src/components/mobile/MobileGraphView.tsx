import React, { useRef, useEffect, useState, useCallback } from 'react';
import * as d3 from 'd3';
import { ZoomIn, ZoomOut, RotateCcw, Maximize2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useTouchGestures } from '@/hooks/useTouchGestures';
import { NodeDetailSheet } from './NodeDetailSheet';
import { motion } from 'framer-motion';

interface GraphNode {
  id: string;
  label: string;
  type?: string;
  description?: string;
  period?: string;
  school?: string;
  x?: number;
  y?: number;
  fx?: number | null;
  fy?: number | null;
  vx?: number;
  vy?: number;
  metadata?: Record<string, unknown>;
  sources?: Array<{
    citation: string;
    cts_urn?: string;
    url?: string;
  }>;
}

interface GraphEdge {
  source: string | GraphNode;
  target: string | GraphNode;
  relationship?: string;
}

interface MobileGraphViewProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  onNodeClick?: (node: GraphNode) => void;
  maxNodes?: number;
  className?: string;
}

export const MobileGraphView: React.FC<MobileGraphViewProps> = ({
  nodes,
  edges,
  onNodeClick,
  maxNodes = 100,
  className = '',
}) => {
  const { t } = useTranslation();
  const containerRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [zoom, setZoom] = useState(1);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Limit nodes for performance
  const limitedNodes = nodes.slice(0, maxNodes);
  const limitedEdges = edges.filter((edge) => {
    const sourceId = typeof edge.source === 'string' ? edge.source : edge.source.id;
    const targetId = typeof edge.target === 'string' ? edge.target : edge.target.id;
    return (
      limitedNodes.some((n) => n.id === sourceId) &&
      limitedNodes.some((n) => n.id === targetId)
    );
  });

  // Touch gestures
  useTouchGestures(containerRef as React.RefObject<HTMLElement>, {
    onPinchZoom: (scale) => {
      setZoom((prev) => Math.max(0.5, Math.min(3, prev * scale)));
    },
    onDoubleTap: () => {
      setZoom(1);
    },
  });

  // Update dimensions on resize
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        setDimensions({ width: rect.width, height: rect.height });
      }
    };

    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, [isFullscreen]);

  // D3 Force Simulation
  useEffect(() => {
    if (!svgRef.current || dimensions.width === 0 || limitedNodes.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const width = dimensions.width;
    const height = dimensions.height;

    // Create container group for zoom/pan
    const g = svg.append('g').attr('class', 'graph-container');

    // Create links
    const link = g
      .append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(limitedEdges)
      .enter()
      .append('line')
      .attr('stroke', '#475569')
      .attr('stroke-opacity', 0.4)
      .attr('stroke-width', 1);

    // Create node groups
    const node = g
      .append('g')
      .attr('class', 'nodes')
      .selectAll('g')
      .data(limitedNodes)
      .enter()
      .append('g')
      .attr('cursor', 'pointer')
      .on('click', (_event, d) => {
        setSelectedNode(d);
        onNodeClick?.(d);
      });

    // Add circles to nodes
    node
      .append('circle')
      .attr('r', (d) => {
        const edgeCount = limitedEdges.filter((e) => {
          const sourceId = typeof e.source === 'string' ? e.source : e.source.id;
          const targetId = typeof e.target === 'string' ? e.target : e.target.id;
          return sourceId === d.id || targetId === d.id;
        }).length;
        return Math.min(8 + edgeCount * 0.5, 20);
      })
      .attr('fill', (d) => {
        switch (d.type?.toLowerCase()) {
          case 'person':
            return '#3b82f6';
          case 'concept':
            return '#a855f7';
          case 'text':
            return '#22c55e';
          default:
            return '#64748b';
        }
      })
      .attr('stroke', '#1e293b')
      .attr('stroke-width', 2);

    // Add labels to nodes
    node
      .append('text')
      .text((d) => (d.label.length > 15 ? d.label.slice(0, 12) + '...' : d.label))
      .attr('x', 0)
      .attr('y', (d) => {
        const edgeCount = limitedEdges.filter((e) => {
          const sourceId = typeof e.source === 'string' ? e.source : e.source.id;
          const targetId = typeof e.target === 'string' ? e.target : e.target.id;
          return sourceId === d.id || targetId === d.id;
        }).length;
        return Math.min(8 + edgeCount * 0.5, 20) + 12;
      })
      .attr('text-anchor', 'middle')
      .attr('fill', '#cbd5e1')
      .attr('font-size', '10px')
      .attr('font-weight', '500');

    // Create force simulation
    const simulation = d3
      .forceSimulation(limitedNodes as d3.SimulationNodeDatum[])
      .force(
        'link',
        d3
          .forceLink(limitedEdges)
          .id((d: unknown) => (d as GraphNode).id)
          .distance(60)
      )
      .force('charge', d3.forceManyBody().strength(-100))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(25));

    // Update positions on tick
    simulation.on('tick', () => {
      link
        .attr('x1', (d) => (d.source as GraphNode).x || 0)
        .attr('y1', (d) => (d.source as GraphNode).y || 0)
        .attr('x2', (d) => (d.target as GraphNode).x || 0)
        .attr('y2', (d) => (d.target as GraphNode).y || 0);

      node.attr('transform', (d) => `translate(${d.x || 0},${d.y || 0})`);
    });

    // Stop simulation after settling
    simulation.alpha(1).restart();
    setTimeout(() => simulation.stop(), 3000);

    return () => {
      simulation.stop();
    };
  }, [limitedNodes, limitedEdges, dimensions, onNodeClick]);

  // Apply zoom transform
  useEffect(() => {
    if (!svgRef.current) return;
    const g = d3.select(svgRef.current).select('g.graph-container');
    g.attr(
      'transform',
      `translate(${dimensions.width / 2},${dimensions.height / 2}) scale(${zoom}) translate(${-dimensions.width / 2},${-dimensions.height / 2})`
    );
  }, [zoom, dimensions]);

  const handleZoomIn = () => setZoom((prev) => Math.min(prev * 1.3, 3));
  const handleZoomOut = () => setZoom((prev) => Math.max(prev / 1.3, 0.5));
  const handleReset = () => setZoom(1);

  const toggleFullscreen = useCallback(async () => {
    if (!containerRef.current) return;

    if (!document.fullscreenElement) {
      await containerRef.current.requestFullscreen();
      setIsFullscreen(true);
    } else {
      await document.exitFullscreen();
      setIsFullscreen(false);
    }
  }, []);

  const handleCloseSheet = () => setSelectedNode(null);

  const handleNodeNavigation = (nodeId: string) => {
    const node = limitedNodes.find((n) => n.id === nodeId);
    if (node) {
      setSelectedNode(node);
      onNodeClick?.(node);
    }
  };

  return (
    <div
      ref={containerRef}
      className={`relative bg-slate-950 rounded-xl overflow-hidden ${className} ${
        isFullscreen ? 'fixed inset-0 z-50' : ''
      }`}
      role="application"
      aria-label={t('graphUi.mobileGraph.ariaLabel')}
    >
      {/* Graph Canvas */}
      <svg
        ref={svgRef}
        width={dimensions.width || '100%'}
        height={dimensions.height || 300}
        className="touch-none"
      />

      {/* Control Buttons */}
      <motion.div
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        className="absolute top-4 right-4 flex flex-col gap-2"
      >
        <button
          onClick={handleZoomIn}
          className="min-h-11 min-w-11 flex items-center justify-center bg-slate-800/80 backdrop-blur-sm rounded-lg hover:bg-slate-700 transition-colors touch-manipulation"
          aria-label={t('graphUi.mobileGraph.zoomIn')}
        >
          <ZoomIn className="h-5 w-5 text-white" />
        </button>
        <button
          onClick={handleZoomOut}
          className="min-h-11 min-w-11 flex items-center justify-center bg-slate-800/80 backdrop-blur-sm rounded-lg hover:bg-slate-700 transition-colors touch-manipulation"
          aria-label={t('graphUi.mobileGraph.zoomOut')}
        >
          <ZoomOut className="h-5 w-5 text-white" />
        </button>
        <button
          onClick={handleReset}
          className="min-h-11 min-w-11 flex items-center justify-center bg-slate-800/80 backdrop-blur-sm rounded-lg hover:bg-slate-700 transition-colors touch-manipulation"
          aria-label={t('graphUi.mobileGraph.resetZoom')}
        >
          <RotateCcw className="h-5 w-5 text-white" />
        </button>
        <button
          onClick={toggleFullscreen}
          className="min-h-11 min-w-11 flex items-center justify-center bg-slate-800/80 backdrop-blur-sm rounded-lg hover:bg-slate-700 transition-colors touch-manipulation"
          aria-label={isFullscreen ? t('graphUi.mobileGraph.exitFullscreen') : t('graphUi.mobileGraph.enterFullscreen')}
        >
          <Maximize2 className="h-5 w-5 text-white" />
        </button>
      </motion.div>

      {/* Stats Overlay */}
      <div className="absolute bottom-4 left-4 bg-slate-800/80 backdrop-blur-sm rounded-lg px-3 py-2">
        <p className="text-xs text-slate-300">
          {t('graphUi.mobileGraph.stats', { nodes: limitedNodes.length, edges: limitedEdges.length })}
          {nodes.length > maxNodes && (
            <span className="text-yellow-400 ml-1">
              {t('graphUi.mobileGraph.limitedFrom', { count: nodes.length })}
            </span>
          )}
        </p>
      </div>

      {/* Legend */}
      <div className="absolute top-4 left-4 bg-slate-800/80 backdrop-blur-sm rounded-lg p-3">
        <p className="text-xs font-medium text-slate-300 mb-2">{t('graphUi.mobileGraph.legend')}</p>
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-blue-500" />
            <span className="text-xs text-slate-300">{t('graphUi.mobileGraph.person')}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-purple-500" />
            <span className="text-xs text-slate-300">{t('graphUi.mobileGraph.concept')}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-green-500" />
            <span className="text-xs text-slate-300">{t('graphUi.mobileGraph.text')}</span>
          </div>
        </div>
      </div>

      {/* Instructions */}
      <div className="absolute bottom-4 right-4 bg-slate-800/80 backdrop-blur-sm rounded-lg px-3 py-2">
        <p className="text-xs text-slate-400">
          {t('graphUi.mobileGraph.instructions')}
        </p>
      </div>

      {/* Node Detail Sheet */}
      <NodeDetailSheet
        node={selectedNode}
        onClose={handleCloseSheet}
        onNodeClick={handleNodeNavigation}
      />
    </div>
  );
};
