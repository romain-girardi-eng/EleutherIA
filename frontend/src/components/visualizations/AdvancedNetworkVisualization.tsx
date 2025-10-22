import { useEffect, useMemo, useRef } from 'react';
import * as d3 from 'd3';
import type { D3DragEvent, D3ZoomEvent } from 'd3';
import { Network } from 'lucide-react';
import { useKGWorkspace } from '../../context/KGWorkspaceContext';
import type { CytoscapeData } from '../../types';
import { filterCytoscapeData } from '../../utils/cytoscapeFilters';

interface SimulationNode extends d3.SimulationNodeDatum {
  id: string;
  label: string;
  type: string;
}

interface SimulationLink extends d3.SimulationLinkDatum<SimulationNode> {
  relation: string;
  strength: number;
}

interface DrawOptions {
  selectedIds: Set<string>;
  focusId: string | null;
  onNodeClick?: (nodeId: string) => void;
  containerEl: HTMLElement | null;
}

const NetworkColors = {
  person: '#2563eb',
  work: '#7c3aed',
  concept: '#dc2626',
  argument: '#ea580c',
  debate: '#059669',
  school: '#0891b2',
  period: '#be185d',
  default: '#6b7280',
};

function getNodeColor(type: string) {
  return NetworkColors[type as keyof typeof NetworkColors] || NetworkColors.default;
}

function createSimulation(
  data: CytoscapeData,
  width: number,
  height: number,
): {
  nodes: SimulationNode[];
  links: SimulationLink[];
  simulation: d3.Simulation<SimulationNode, SimulationLink>;
  centerMap: Map<string, { x: number; y: number }>;
  clusterForceX: d3.ForceX<SimulationNode>;
  clusterForceY: d3.ForceY<SimulationNode>;
} {
  const rawNodes = data.elements.nodes.map((node, index) => ({
    id: node.data.id,
    label: node.data.label || node.data.id,
    type: node.data.type || 'concept',
    x: width / 2 + Math.cos(index) * 120,
    y: height / 2 + Math.sin(index) * 120,
  }));

  const nodes: SimulationNode[] = rawNodes as SimulationNode[];

  const links: SimulationLink[] = data.elements.edges.map((edge) => ({
    source: edge.data.source || '',
    target: edge.data.target || '',
    relation: edge.data.relation || '',
    strength: 1,
  })) as SimulationLink[];

  const typeOrder = Array.from(new Set(nodes.map((node) => node.type)));
  if (typeOrder.length === 0) {
    typeOrder.push('concept');
  }

  const clusterRadius = Math.min(width, height) / 2.8;
  const centerMap = new Map<string, { x: number; y: number }>(
    typeOrder.map((type, idx) => {
      if (typeOrder.length === 1) {
        return [type, { x: width / 2, y: height / 2 }];
      }
      const angle = (idx / typeOrder.length) * Math.PI * 2;
      return [
        type,
        {
          x: width / 2 + Math.cos(angle) * clusterRadius,
          y: height / 2 + Math.sin(angle) * clusterRadius,
        },
      ];
    }),
  );

  const clusterForceX = d3
    .forceX<SimulationNode>((d) => centerMap.get(d.type)?.x ?? width / 2)
    .strength(0.45);
  const clusterForceY = d3
    .forceY<SimulationNode>((d) => centerMap.get(d.type)?.y ?? height / 2)
    .strength(0.12);

  const simulation = d3
    .forceSimulation<SimulationNode>(nodes)
    .force(
      'link',
      d3.forceLink<SimulationNode, SimulationLink>(links)
        .id((d) => d.id)
        .distance((link) => (link.relation === 'influenced_by' ? 140 : 95))
        .strength(0.18),
    )
    .force('charge', d3.forceManyBody<SimulationNode>().strength(-320).distanceMax(320))
    .force('collision', d3.forceCollide<SimulationNode>().radius(28))
    .force('clusterX', clusterForceX)
    .force('clusterY', clusterForceY);

  simulation.alpha(0.9).restart();

  return {
    nodes,
    links,
    simulation,
    centerMap,
    clusterForceX,
    clusterForceY,
  };
}

function drawAdvancedNetwork(
  svg: d3.Selection<SVGSVGElement, unknown, null, undefined>,
  data: CytoscapeData,
  width: number,
  height: number,
  { selectedIds, focusId, onNodeClick, containerEl }: DrawOptions,
): () => void {
  svg.selectAll('*').remove();

  const uniqueId = Math.random().toString(36).slice(2, 8);

  const defs = svg.append('defs');
  const nodeGradientId = `network-node-${uniqueId}`;
  const linkGradientId = `network-link-${uniqueId}`;
  const backgroundGradientId = `network-bg-${uniqueId}`;

  const nodeGradient = defs.append('radialGradient')
    .attr('id', nodeGradientId)
    .attr('cx', '50%')
    .attr('cy', '50%')
    .attr('r', '60%');
  nodeGradient.append('stop').attr('offset', '0%').attr('stop-color', '#ffffff').attr('stop-opacity', 0.85);
  nodeGradient.append('stop').attr('offset', '100%').attr('stop-color', '#dbeafe').attr('stop-opacity', 0.35);

  const linkGradient = defs.append('linearGradient')
    .attr('id', linkGradientId)
    .attr('x1', '0%')
    .attr('y1', '0%')
    .attr('x2', '100%')
    .attr('y2', '0%');
  linkGradient.append('stop').attr('offset', '0%').attr('stop-color', '#475569').attr('stop-opacity', 0.5);
  linkGradient.append('stop').attr('offset', '100%').attr('stop-color', '#94a3b8').attr('stop-opacity', 0.25);

  const backgroundGradient = defs.append('radialGradient')
    .attr('id', backgroundGradientId)
    .attr('cx', '50%')
    .attr('cy', '50%')
    .attr('r', '75%');
  backgroundGradient.append('stop').attr('offset', '0%').attr('stop-color', '#f8fafc').attr('stop-opacity', 0.25);
  backgroundGradient.append('stop').attr('offset', '100%').attr('stop-color', '#e0f2fe').attr('stop-opacity', 0.15);

  const zoomLayer = svg.append('g').attr('class', 'network-zoom-layer');
  const content = zoomLayer.append('g').attr('class', 'network-content');

  const background = content.append('rect')
    .attr('width', width)
    .attr('height', height)
    .attr('fill', `url(#${backgroundGradientId})`)
    .attr('rx', 18)
    .attr('ry', 18);

  const {
    nodes,
    links,
    simulation,
    centerMap,
    clusterForceX,
    clusterForceY,
  } = createSimulation(data, width, height);
  const clusterKeys = Array.from(centerMap.keys());
  const nodeLookup = new Map(nodes.map((node) => [node.id, node]));
  const nodeIndexLookup = new Map<number, SimulationNode>();
  nodes.forEach((node, index) => nodeIndexLookup.set(index, node));

  const getNodeFromRef = (ref: string | number | SimulationNode): SimulationNode | undefined => {
    if (typeof ref === 'object') {
      return ref;
    }
    if (typeof ref === 'string') {
      return nodeLookup.get(ref);
    }
    if (typeof ref === 'number') {
      return nodeIndexLookup.get(ref);
    }
    return undefined;
  };

  const getNodeIdFromRef = (ref: string | number | SimulationNode): string => {
    if (typeof ref === 'object') {
      return ref.id;
    }
    if (typeof ref === 'string') {
      return ref;
    }
    if (typeof ref === 'number') {
      const node = nodeIndexLookup.get(ref);
      return node?.id ?? String(ref);
    }
    return '';
  };

  const getNodeTypeFromRef = (ref: string | number | SimulationNode): string | undefined => {
    return getNodeFromRef(ref)?.type;
  };

  const getNodePosition = (ref: string | number | SimulationNode) => {
    const node = getNodeFromRef(ref);
    return {
      x: node?.x ?? width / 2,
      y: node?.y ?? height / 2,
    };
  };

  const clusterHullGroup = content.append('g').attr('class', 'network-cluster-hulls');
  const linkGroup = content.append('g').attr('class', 'network-links');
  const nodeGroup = content.append('g').attr('class', 'network-nodes');

  const linkSelection = linkGroup
    .selectAll<SVGLineElement, SimulationLink>('line')
    .data(links)
    .enter()
    .append('line')
    .attr('stroke', `url(#${linkGradientId})`)
    .attr('stroke-width', 1.4)
    .attr('opacity', 0.55);

  const nodeSelection: d3.Selection<SVGGElement, SimulationNode, SVGGElement, SimulationNode> = nodeGroup
    .selectAll<SVGGElement, SimulationNode>('g')
    .data(nodes)
    .enter()
    .append('g')
    .attr('class', 'network-node')
    .style('cursor', 'pointer');

  nodeSelection
    .append('circle')
    .attr('class', 'network-node-glow')
    .attr('r', 23)
    .attr('fill', (d) => getNodeColor(d.type))
    .attr('opacity', 0.18);

  const nodeCircle = nodeSelection
    .append('circle')
    .attr('class', 'network-node-base')
    .attr('r', 16)
    .attr('fill', `url(#${nodeGradientId})`)
    .attr('stroke', (d) => getNodeColor(d.type))
    .attr('stroke-width', 1.6)
    .attr('opacity', 0.95);

  nodeSelection
    .append('text')
    .attr('text-anchor', 'middle')
    .attr('dy', 28)
    .text((d) => d.label)
    .style('font-family', 'Georgia, serif')
    .style('font-size', '10px')
    .style('font-weight', '500')
    .style('fill', '#1f2937')
    .style('text-shadow', '0 1px 2px rgba(255,255,255,0.85)');

  nodeSelection
    .append('text')
    .attr('text-anchor', 'middle')
    .attr('dy', 40)
    .text((d) => d.type)
    .style('font-family', 'Georgia, serif')
    .style('font-size', '8px')
    .style('fill', '#6b7280')
    .style('text-transform', 'uppercase')
    .style('letter-spacing', '0.6px');

  const clusterHullSelection = clusterHullGroup
    .selectAll<SVGPathElement, string>('path')
    .data(clusterKeys)
    .enter()
    .append('path')
    .attr('stroke-dasharray', '10 8')
    .attr('stroke-opacity', 0.6);

  const tooltip = containerEl
    ? d3.select<HTMLElement, unknown>(containerEl)
        .selectAll<HTMLDivElement, unknown>('.afw-network-tooltip')
        .data([null])
        .join('div')
        .attr(
          'class',
          'afw-network-tooltip pointer-events-none absolute z-30 hidden rounded-md border border-gray-200 bg-white px-3 py-2 text-[11px] shadow-lg',
        )
    : null;

  const updatePositions = () => {
    nodeSelection.attr('transform', (d) => `translate(${d.x ?? width / 2}, ${d.y ?? height / 2})`);

    linkSelection
      .attr('x1', (d) => getNodePosition(d.source).x)
      .attr('y1', (d) => getNodePosition(d.source).y)
      .attr('x2', (d) => getNodePosition(d.target).x)
      .attr('y2', (d) => getNodePosition(d.target).y);
  };

  const hullPadding = 36;
  const generateHullPath = (points: [number, number][], padding: number) => {
    if (points.length === 0) {
      return '';
    }

    const hull = d3.polygonHull(points);
    if (hull && hull.length > 2) {
      const pathBuilder = d3.path();
      hull.forEach(([x, y], index) => {
        if (index === 0) {
          pathBuilder.moveTo(x, y);
        } else {
          pathBuilder.lineTo(x, y);
        }
      });
      pathBuilder.closePath();
      return pathBuilder.toString();
    }

    const centerX = points.reduce((acc, [x]) => acc + x, 0) / points.length;
    const centerY = points.reduce((acc, [, y]) => acc + y, 0) / points.length;
    let radius = padding;
    for (const [x, y] of points) {
      const dist = Math.sqrt((x - centerX) ** 2 + (y - centerY) ** 2);
      radius = Math.max(radius, dist + padding);
    }
    const pathBuilder = d3.path();
    pathBuilder.moveTo(centerX + radius, centerY);
    pathBuilder.arc(centerX, centerY, radius, 0, Math.PI * 2);
    pathBuilder.closePath();
    return pathBuilder.toString();
  };

  const updateClusterHulls = () => {
    clusterHullSelection
      .attr('d', (cluster) => {
        const points = nodes
          .filter((node) => node.type === cluster && node.x !== undefined && node.y !== undefined)
          .map((node) => [node.x ?? width / 2, node.y ?? height / 2] as [number, number]);
        const path = generateHullPath(points, hullPadding);
        return path || '';
      })
      .attr('display', (cluster) => {
        const points = nodes.filter((node) => node.type === cluster);
        return points.length === 0 ? 'none' : null;
      });
  };

  let activeCluster: string | null = null;

  const colorWithOpacity = (cluster: string, opacity: number) => {
    const base =
      d3.color(getNodeColor(cluster)) ||
      d3.color('#94a3b8') ||
      d3.rgb(148, 163, 184);
    if (!base) {
      return `rgba(148, 163, 184, ${opacity})`;
    }
    const copy = base.copy();
    copy.opacity = opacity;
    return copy.formatRgb();
  };

  const updateSelectionStyles = () => {
    const hasHighlightedNodes = selectedIds.size > 0 || Boolean(focusId);

    nodeCircle
      .attr('stroke', (d) => {
        if (focusId === d.id) {
          return '#111827';
        }
        if (selectedIds.has(d.id)) {
          return '#312e81';
        }
        if (activeCluster && d.type !== activeCluster) {
          return d3.color(getNodeColor(d.type))?.darker(0.2).formatRgb() ?? getNodeColor(d.type);
        }
        return getNodeColor(d.type);
      })
      .attr('stroke-width', (d) => {
        if (focusId === d.id) {
          return 3;
        }
        if (selectedIds.has(d.id)) {
          return 2.4;
        }
        if (activeCluster && d.type === activeCluster) {
          return 2;
        }
        return 1.6;
      })
      .attr('opacity', (d) => {
        if (!hasHighlightedNodes && !activeCluster) {
          return 0.95;
        }
        if (focusId === d.id || selectedIds.has(d.id)) {
          return 1;
        }
        if (activeCluster && d.type !== activeCluster) {
          return 0.18;
        }
        return 0.55;
      });

    linkSelection
      .attr('stroke-width', (d) => {
        const sourceId = getNodeIdFromRef(d.source);
        const targetId = getNodeIdFromRef(d.target);
        if (focusId === sourceId || focusId === targetId) {
          return 2.4;
        }
        if (selectedIds.has(sourceId) || selectedIds.has(targetId)) {
          return 2;
        }
        if (activeCluster) {
          const sourceType = getNodeTypeFromRef(d.source);
          const targetType = getNodeTypeFromRef(d.target);
          if (sourceType === activeCluster || targetType === activeCluster) {
            return 1.6;
          }
        }
        return 1.1;
      })
      .attr('opacity', (d) => {
        if (!hasHighlightedNodes && !activeCluster) {
          return 0.55;
        }
        const sourceId = getNodeIdFromRef(d.source);
        const targetId = getNodeIdFromRef(d.target);
        if (
          focusId === sourceId ||
          focusId === targetId ||
          selectedIds.has(sourceId) ||
          selectedIds.has(targetId)
        ) {
          return 0.85;
        }
        if (activeCluster) {
          const sourceType = getNodeTypeFromRef(d.source);
          const targetType = getNodeTypeFromRef(d.target);
          if (sourceType === activeCluster || targetType === activeCluster) {
            return 0.5;
          }
        }
        return 0.12;
      });

    clusterHullSelection
      .attr('fill', (cluster) => colorWithOpacity(cluster, activeCluster === cluster ? 0.28 : 0.14))
      .attr('stroke', (cluster) => getNodeColor(cluster))
      .attr('stroke-width', (cluster) => (activeCluster === cluster ? 2 : 1.2))
      .attr('opacity', (cluster) => {
        if (!activeCluster && !hasHighlightedNodes) {
          return 0.7;
        }
        return activeCluster === cluster ? 0.95 : 0.45;
      });
  };

  simulation.on('tick', () => {
    updatePositions();
    updateClusterHulls();
  });
  updatePositions();
  updateClusterHulls();
  updateSelectionStyles();

  const dragBehaviour = d3
    .drag<SVGGElement, SimulationNode>()
    .on('start', (event: D3DragEvent<SVGGElement, SimulationNode, SimulationNode>, d) => {
      if (!event.active) {
        simulation.alphaTarget(0.3).restart();
      }
      d.fx = d.x;
      d.fy = d.y;
    })
    .on('drag', (event: D3DragEvent<SVGGElement, SimulationNode, SimulationNode>, d) => {
      d.fx = event.x;
      d.fy = event.y;
      updatePositions();
    })
    .on('end', (event: D3DragEvent<SVGGElement, SimulationNode, SimulationNode>, d) => {
      if (!event.active) {
        simulation.alphaTarget(0);
      }
      d.fx = undefined;
      d.fy = undefined;
    });

  nodeSelection.call(dragBehaviour);

  const zoomBehaviour = d3
    .zoom<SVGSVGElement, unknown>()
    .scaleExtent([0.35, 2.8])
    .on('zoom', (event: D3ZoomEvent<SVGSVGElement, unknown>) => {
      zoomLayer.attr('transform', event.transform.toString());
    });

  svg.call(zoomBehaviour);
  svg.on('dblclick.zoom', null);

  const focusOnCluster = (cluster: string | null) => {
    activeCluster = cluster;
    clusterForceX.x((d) => {
      if (!cluster) {
        return centerMap.get(d.type)?.x ?? width / 2;
      }
      if (d.type === cluster) {
        return width / 2;
      }
      return centerMap.get(d.type)?.x ?? width / 2;
    });
    clusterForceY.y((d) => {
      if (!cluster) {
        return centerMap.get(d.type)?.y ?? height / 2;
      }
      if (d.type === cluster) {
        return height / 2;
      }
      return centerMap.get(d.type)?.y ?? height / 2;
    });
    simulation.alpha(0.9).restart();
    updateSelectionStyles();
    updateClusterHulls();
  };

  nodeSelection
    .on('mouseenter', (event, d) => {
      if (!tooltip) return;
      const [x, y] = d3.pointer(event, containerEl);
      tooltip
        .classed('hidden', false)
        .style('left', `${x + 18}px`)
        .style('top', `${y - 12}px`)
        .html(
          `<div class="font-semibold text-academic-text mb-1">${d.label}</div>
           <div class="text-academic-muted">${d.type}</div>
           <div class="text-academic-muted text-[10px] uppercase tracking-wide">Node ID: ${d.id}</div>`,
        );
    })
    .on('mouseleave', () => {
      tooltip?.classed('hidden', true);
    })
    .on('click', (event, d) => {
      event.stopPropagation();
      onNodeClick?.(d.id);
    })
    .on('dblclick', (event, d) => {
      event.stopPropagation();
      focusOnCluster(d.type);
      onNodeClick?.(d.id);
      const nodeX = d.x ?? width / 2;
      const nodeY = d.y ?? height / 2;
      const focusScale = 1.2;
      const focusTransform = d3.zoomIdentity
        .translate(width / 2, height / 2)
        .scale(focusScale)
        .translate(-nodeX, -nodeY);
      svg.transition().duration(450).call(zoomBehaviour.transform, focusTransform);
    });

  background.on('click', () => {
    onNodeClick?.('');
  });

  background.on('dblclick', () => {
    focusOnCluster(null);
    svg.transition().duration(450).call(zoomBehaviour.transform, d3.zoomIdentity);
  });

  return () => {
    simulation.stop();
    svg.selectAll('*').remove();
    tooltip?.remove();
  };
}

interface AdvancedNetworkVisualizationProps {
  data: CytoscapeData | null;
  loading: boolean;
  error: string | null;
  standalone?: boolean;
}

export default function AdvancedNetworkVisualization({
  data,
  loading,
  error,
  standalone = true,
}: AdvancedNetworkVisualizationProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const { state, updateSelection, setFilters } = useKGWorkspace();

  const networkData = useMemo(
    () =>
      filterCytoscapeData(
        data,
        state.filters,
        state.selection,
        {
          maxNodes: 140,
        },
      ),
    [data, state.filters, state.selection],
  );

  useEffect(() => {
    if (!svgRef.current || !networkData || networkData.elements.nodes.length === 0) {
      return;
    }

    const width = 1000;
    const height = 620;
    const svg = d3.select(svgRef.current);
    svg.attr('viewBox', `0 0 ${width} ${height}`);

    const cleanup = drawAdvancedNetwork(
      svg,
      networkData,
      width,
      height,
      {
        selectedIds: new Set(state.selection.nodes),
        focusId: state.selection.focusNodeId ?? null,
        onNodeClick: (nodeId) => {
          if (!nodeId) {
            updateSelection({ nodes: [], focusNodeId: null });
          } else {
            updateSelection({ nodes: [nodeId], focusNodeId: nodeId });
          }
        },
        containerEl: svgRef.current.parentElement,
      },
    );

    return () => {
      cleanup();
    };
  }, [networkData, state.selection, updateSelection]);

  const isEmpty = !networkData || networkData.elements.nodes.length === 0;

  const handleResetFilters = () => {
    setFilters(() => ({
      nodeTypes: [],
      periods: [],
      schools: [],
      relations: [],
      searchTerm: '',
    }));
  };

  const renderStatus = (message: string, isError: boolean = false) => {
    const filtersActive =
      state.filters.nodeTypes.length > 0 ||
      state.filters.periods.length > 0 ||
      state.filters.schools.length > 0 ||
      state.filters.relations.length > 0 ||
      Boolean(state.filters.searchTerm?.trim());

    const content = (
      <div className="py-16 text-center text-sm space-y-2">
        <div className={isError ? 'text-red-500' : 'text-academic-muted'}>
          {message}
        </div>
        {!isError && filtersActive && (
          <div className="space-y-2">
            <div className="text-xs text-academic-muted">
              Adjust or clear filters to widen the slice of the network.
            </div>
            <button
              type="button"
              onClick={handleResetFilters}
              className="inline-flex items-center rounded-md border border-primary-300 bg-primary-50 px-3 py-1.5 text-xs font-semibold text-primary-700 transition hover:bg-primary-100"
            >
              Clear filters
            </button>
          </div>
        )}
      </div>
    );

    if (standalone) {
      return <div className="academic-card">{content}</div>;
    }

    return content;
  };

  if (loading) {
    return renderStatus('Loading network data…');
  }

  if (error) {
    return renderStatus(error, true);
  }

  if (isEmpty) {
    return renderStatus('No network entities match the current filters.');
  }

  const chart = (
    <>
      {standalone && (
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2 text-sm font-semibold text-academic-text uppercase">
            <Network className="w-4 h-4 text-primary-600" />
            Advanced Network Analysis
          </div>
          <div className="text-xs text-academic-muted">
            Drag nodes to explore, scroll to zoom, click to focus on key entities.
          </div>
        </div>
      )}

      <div className={`overflow-x-auto ${standalone ? '-mx-4 px-4' : ''}`}>
        <svg
          ref={svgRef}
          className="w-full h-[620px] border border-gray-200 rounded-lg bg-gradient-to-br from-slate-50 to-blue-50"
        />
      </div>

      <div className="mt-4 flex flex-wrap gap-4 text-xs">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-blue-600"></div>
          <span>Philosophers</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-purple-600"></div>
          <span>Works</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-red-600"></div>
          <span>Concepts</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-orange-600"></div>
          <span>Arguments</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-green-600"></div>
          <span>Debates</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-cyan-600"></div>
          <span>Schools</span>
        </div>
      </div>
    </>
  );

  if (standalone) {
    return (
      <div className="academic-card">
        {chart}
      </div>
    );
  }

  return chart;
}
