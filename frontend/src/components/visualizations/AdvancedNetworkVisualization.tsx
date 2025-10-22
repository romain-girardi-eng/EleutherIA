import { useEffect, useRef, useMemo } from 'react';
import * as d3 from 'd3';
import { Network } from 'lucide-react';
import { useKGWorkspace } from '../../context/KGWorkspaceContext';
import type { CytoscapeData } from '../../types';

interface NetworkNode {
  id: string;
  label: string;
  type: string;
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
  fx?: number;
  fy?: number;
}

interface NetworkLink {
  source: string | NetworkNode;
  target: string | NetworkNode;
  relation: string;
  strength: number;
}

const NetworkColors = {
  person: '#2563eb',
  work: '#7c3aed',
  concept: '#dc2626',
  argument: '#ea580c',
  debate: '#059669',
  school: '#0891b2',
  period: '#be185d',
  default: '#6b7280'
};

function getNodeColor(type: string) {
  return NetworkColors[type as keyof typeof NetworkColors] || NetworkColors.default;
}

function createAdvancedNetworkLayout(nodes: NetworkNode[], links: NetworkLink[], width: number, height: number) {
  // Create force simulation with sophisticated physics
  const simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(links)
      .id((d: any) => d.id)
      .distance(100)
      .strength(0.1))
    .force('charge', d3.forceManyBody()
      .strength(-300)
      .distanceMax(200))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide()
      .radius(25))
    .force('radial', d3.forceRadial(150, width / 2, height / 2)
      .strength(0.1));

  // Run simulation
  simulation.tick(300);

  return { nodes, links };
}

function drawAdvancedNetwork(svg: d3.Selection<SVGSVGElement, unknown, null, undefined>, 
                            data: CytoscapeData, 
                            width: number, 
                            height: number) {
  svg.selectAll('*').remove();

  // Create gradient definitions
  const defs = svg.append('defs');
  
  // Node gradient
  const nodeGradient = defs.append('radialGradient')
    .attr('id', 'nodeGradient')
    .attr('cx', '50%')
    .attr('cy', '50%')
    .attr('r', '50%');
  
  nodeGradient.append('stop')
    .attr('offset', '0%')
    .attr('stop-color', '#ffffff')
    .attr('stop-opacity', 0.9);
  
  nodeGradient.append('stop')
    .attr('offset', '100%')
    .attr('stop-color', '#e5e7eb')
    .attr('stop-opacity', 0.7);

  // Link gradient
  const linkGradient = defs.append('linearGradient')
    .attr('id', 'linkGradient')
    .attr('x1', '0%')
    .attr('y1', '0%')
    .attr('x2', '100%')
    .attr('y2', '0%');
  
  linkGradient.append('stop')
    .attr('offset', '0%')
    .attr('stop-color', '#6b7280')
    .attr('stop-opacity', 0.6);
  
  linkGradient.append('stop')
    .attr('offset', '100%')
    .attr('stop-color', '#9ca3af')
    .attr('stop-opacity', 0.3);

  // Background gradient
  const bgGradient = defs.append('radialGradient')
    .attr('id', 'networkBg')
    .attr('cx', '50%')
    .attr('cy', '50%')
    .attr('r', '70%');
  
  bgGradient.append('stop')
    .attr('offset', '0%')
    .attr('stop-color', '#f8fafc')
    .attr('stop-opacity', 0.1);
  
  bgGradient.append('stop')
    .attr('offset', '100%')
    .attr('stop-color', '#e2e8f0')
    .attr('stop-opacity', 0.05);

  // Draw background
  svg.append('rect')
    .attr('width', width)
    .attr('height', height)
    .attr('fill', 'url(#networkBg)')
    .attr('rx', 8)
    .attr('ry', 8);

  // Transform data
  const nodes: NetworkNode[] = data.elements.nodes.map(node => ({
    id: node.data.id,
    label: node.data.label || node.data.id,
    type: node.data.type || 'concept'
  }));

  const links: NetworkLink[] = data.elements.edges.map(edge => ({
    source: edge.data.source || '',
    target: edge.data.target || '',
    relation: edge.data.relation || '',
    strength: 1
  }));

  const { nodes: positionedNodes, links: positionedLinks } = createAdvancedNetworkLayout(nodes, links, width, height);

  // Draw links
  const linkGroup = svg.append('g').attr('class', 'links');
  
  linkGroup.selectAll('.link')
    .data(positionedLinks)
    .enter().append('line')
    .attr('class', 'link')
    .attr('x1', (d: any) => d.source.x)
    .attr('y1', (d: any) => d.source.y)
    .attr('x2', (d: any) => d.target.x)
    .attr('y2', (d: any) => d.target.y)
    .attr('stroke', 'url(#linkGradient)')
    .attr('stroke-width', 1.5)
    .attr('opacity', 0.6);

  // Draw nodes
  const nodeGroup = svg.append('g').attr('class', 'nodes');
  
  const node = nodeGroup.selectAll('.node')
    .data(positionedNodes)
    .enter().append('g')
    .attr('class', 'node')
    .attr('transform', (d: any) => `translate(${d.x}, ${d.y})`)
    .style('cursor', 'pointer');

  // Draw node circles
  node.append('circle')
    .attr('r', 15)
    .attr('fill', (d: any) => getNodeColor(d.type))
    .attr('stroke', '#ffffff')
    .attr('stroke-width', 2)
    .attr('opacity', 0.9);

  // Add node glow effect
  node.append('circle')
    .attr('r', 20)
    .attr('fill', (d: any) => getNodeColor(d.type))
    .attr('opacity', 0.2)
    .style('filter', 'blur(3px)');

  // Add node labels
  node.append('text')
    .attr('text-anchor', 'middle')
    .attr('dy', 25)
    .text((d: any) => d.label)
    .style('font-family', 'Georgia, serif')
    .style('font-size', '10px')
    .style('font-weight', '500')
    .style('fill', '#374151')
    .style('text-shadow', '0 1px 2px rgba(255,255,255,0.8)');

  // Add type indicators
  node.append('text')
    .attr('text-anchor', 'middle')
    .attr('dy', 35)
    .text((d: any) => d.type)
    .style('font-family', 'Georgia, serif')
    .style('font-size', '8px')
    .style('fill', '#6b7280')
    .style('text-transform', 'uppercase')
    .style('letter-spacing', '0.5px');

  // Add title
  svg.append('text')
    .attr('x', width / 2)
    .attr('y', 30)
    .attr('text-anchor', 'middle')
    .text('Advanced Knowledge Network')
    .style('font-family', 'Georgia, serif')
    .style('font-size', '18px')
    .style('font-weight', '600')
    .style('fill', '#1f2937');

  // Add subtitle
  svg.append('text')
    .attr('x', width / 2)
    .attr('y', 50)
    .attr('text-anchor', 'middle')
    .text(`${nodes.length} entities connected by ${links.length} relationships`)
    .style('font-family', 'Georgia, serif')
    .style('font-size', '12px')
    .style('fill', '#6b7280');
}

export default function AdvancedNetworkVisualization() {
  const svgRef = useRef<SVGSVGElement>(null);
  const { state } = useKGWorkspace();

  // Get filtered data (simplified for now)
  const networkData = useMemo(() => {
    // This would normally use the filtered data from the workspace
    // For now, we'll create a mock structure
    return {
      elements: {
        nodes: [],
        edges: []
      }
    } as CytoscapeData;
  }, [state]);

  useEffect(() => {
    if (!svgRef.current || !networkData) return;

    const width = 1000;
    const height = 600;
    
    const svg = d3.select(svgRef.current);
    svg.attr('viewBox', `0 0 ${width} ${height}`);

    drawAdvancedNetwork(svg, networkData, width, height);

  }, [networkData]);

  return (
    <div className="academic-card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2 text-sm font-semibold text-academic-text uppercase">
          <Network className="w-4 h-4 text-primary-600" />
          Advanced Network Analysis
        </div>
        <div className="text-xs text-academic-muted">
          Sophisticated force-directed layout with intelligent clustering
        </div>
      </div>

      <div className="overflow-x-auto -mx-4 px-4">
        <svg
          ref={svgRef}
          className="w-full h-[600px] border border-gray-200 rounded-lg bg-gradient-to-br from-slate-50 to-blue-50"
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
    </div>
  );
}
