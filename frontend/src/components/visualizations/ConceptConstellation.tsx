import { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { Sparkles } from 'lucide-react';
import { useKGWorkspace } from '../../context/KGWorkspaceContext';
import type { ConceptClusterSummary, ConceptClusterNode } from '../../types';

interface ConstellationData {
  clusters: ConceptClusterSummary[];
  stats: {
    totalConcepts: number;
    clusterCount: number;
  };
}

const ConstellationColors = {
  primary: '#3b82f6',
  secondary: '#8b5cf6', 
  accent: '#f59e0b',
  highlight: '#ef4444',
  neutral: '#6b7280'
};

function createConstellationLayout(nodes: ConceptClusterNode[], width: number, height: number) {
  // Create a force simulation for constellation positioning
  const simulation = d3.forceSimulation(nodes as any)
    .force('charge', d3.forceManyBody().strength(-300))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius(20))
    .stop();

  // Run simulation to get positions
  for (let i = 0; i < 100; ++i) simulation.tick();

  return nodes.map(node => ({
    ...node,
    x: (node as any).x,
    y: (node as any).y
  }));
}

function drawConstellation(svg: d3.Selection<SVGSVGElement, unknown, null, undefined>, 
                          data: ConstellationData, 
                          width: number, 
                          height: number) {
  svg.selectAll('*').remove();

  // Create gradient definitions
  const defs = svg.append('defs');
  
  // Star gradient
  const starGradient = defs.append('radialGradient')
    .attr('id', 'starGradient')
    .attr('cx', '50%')
    .attr('cy', '50%')
    .attr('r', '50%');
  
  starGradient.append('stop')
    .attr('offset', '0%')
    .attr('stop-color', ConstellationColors.primary)
    .attr('stop-opacity', 0.8);
  
  starGradient.append('stop')
    .attr('offset', '100%')
    .attr('stop-color', ConstellationColors.secondary)
    .attr('stop-opacity', 0.3);

  // Connection gradient
  const connectionGradient = defs.append('linearGradient')
    .attr('id', 'connectionGradient')
    .attr('x1', '0%')
    .attr('y1', '0%')
    .attr('x2', '100%')
    .attr('y2', '100%');
  
  connectionGradient.append('stop')
    .attr('offset', '0%')
    .attr('stop-color', ConstellationColors.accent)
    .attr('stop-opacity', 0.6);
  
  connectionGradient.append('stop')
    .attr('offset', '100%')
    .attr('stop-color', ConstellationColors.primary)
    .attr('stop-opacity', 0.2);

  // Draw constellation background
  svg.append('rect')
    .attr('width', width)
    .attr('height', height)
    .attr('fill', 'url(#constellationBg)')
    .attr('rx', 8)
    .attr('ry', 8);

  // Create constellation background gradient
  const bgGradient = defs.append('radialGradient')
    .attr('id', 'constellationBg')
    .attr('cx', '50%')
    .attr('cy', '50%')
    .attr('r', '70%');
  
  bgGradient.append('stop')
    .attr('offset', '0%')
    .attr('stop-color', '#f8fafc')
    .attr('stop-opacity', 0.1);
  
  bgGradient.append('stop')
    .attr('offset', '100%')
    .attr('stop-color', '#1e293b')
    .attr('stop-opacity', 0.05);

  // Draw connections between related concepts
  const connectionsGroup = svg.append('g').attr('class', 'connections');
  
  data.clusters.forEach((cluster, clusterIndex) => {
    const nodes = createConstellationLayout(cluster.nodes, width, height);
    
    // Draw connections within cluster
    nodes.forEach((node, i) => {
      nodes.slice(i + 1).forEach(otherNode => {
        const distance = Math.sqrt(
          Math.pow(node.x - otherNode.x, 2) + Math.pow(node.y - otherNode.y, 2)
        );
        
        if (distance < 80) { // Only connect nearby nodes
          connectionsGroup.append('line')
            .attr('x1', node.x)
            .attr('y1', node.y)
            .attr('x2', otherNode.x)
            .attr('y2', otherNode.y)
            .attr('stroke', 'url(#connectionGradient)')
            .attr('stroke-width', 1)
            .attr('opacity', 0.4);
        }
      });
    });

    // Draw constellation nodes
    const nodesGroup = svg.append('g').attr('class', `cluster-${clusterIndex}`);

    nodes.forEach((node) => {
      const nodeGroup = nodesGroup.append('g')
        .attr('class', 'constellation-node')
        .attr('transform', `translate(${node.x}, ${node.y})`)
        .style('cursor', 'pointer');

      // Draw star shape
      const starPoints = 5;
      const outerRadius = 12;
      const innerRadius = 6;
      
      const starPath = d3.lineRadial()
        .angle((d: any) => d.angle)
        .radius((d: any) => d.radius)
        .curve(d3.curveLinearClosed);

      const starData = Array.from({ length: starPoints * 2 }, (_, i) => ({
        angle: (i * Math.PI) / starPoints,
        radius: i % 2 === 0 ? outerRadius : innerRadius
      }));

      nodeGroup.append('path')
        .attr('d', starPath(starData as any))
        .attr('fill', 'url(#starGradient)')
        .attr('stroke', ConstellationColors.primary)
        .attr('stroke-width', 1)
        .attr('opacity', 0.8);

      // Add glow effect
      nodeGroup.append('circle')
        .attr('r', outerRadius + 4)
        .attr('fill', ConstellationColors.primary)
        .attr('opacity', 0.1)
        .style('filter', 'blur(2px)');

      // Add node label
      nodeGroup.append('text')
        .attr('text-anchor', 'middle')
        .attr('dy', outerRadius + 20)
        .text(node.label)
        .style('font-family', 'Georgia, serif')
        .style('font-size', '10px')
        .style('font-weight', '500')
        .style('fill', '#374151')
        .style('text-shadow', '0 1px 2px rgba(255,255,255,0.8)');

      // Add school indicator if available
      if (node.school) {
        nodeGroup.append('text')
          .attr('text-anchor', 'middle')
          .attr('dy', outerRadius + 32)
          .text(node.school)
          .style('font-family', 'Georgia, serif')
          .style('font-size', '8px')
          .style('fill', '#6b7280')
          .style('font-style', 'italic');
      }
    });
  });

  // Add constellation title
  svg.append('text')
    .attr('x', width / 2)
    .attr('y', 30)
    .attr('text-anchor', 'middle')
    .text('Concept Constellations')
    .style('font-family', 'Georgia, serif')
    .style('font-size', '16px')
    .style('font-weight', '600')
    .style('fill', '#1f2937');

  // Add stats
  svg.append('text')
    .attr('x', width / 2)
    .attr('y', height - 20)
    .attr('text-anchor', 'middle')
    .text(`${data.stats.totalConcepts} concepts across ${data.stats.clusterCount} thematic clusters`)
    .style('font-family', 'Georgia, serif')
    .style('font-size', '12px')
    .style('fill', '#6b7280');
}

export default function ConceptConstellation() {
  const svgRef = useRef<SVGSVGElement>(null);
  const { state: { conceptClusters, loading } } = useKGWorkspace();

  useEffect(() => {
    if (!svgRef.current || !conceptClusters) return;

    const width = 800;
    const height = 500;
    
    const svg = d3.select(svgRef.current);
    svg.attr('viewBox', `0 0 ${width} ${height}`);

    drawConstellation(svg, conceptClusters, width, height);

  }, [conceptClusters]);

  if (loading && !conceptClusters) {
    return (
      <div className="academic-card">
        <div className="py-12 text-center text-academic-muted text-sm">Analyzing concept constellations…</div>
      </div>
    );
  }

  if (!conceptClusters || conceptClusters.clusters.length === 0) {
    return (
      <div className="academic-card">
        <div className="py-12 text-center text-academic-muted text-sm">
          No clustered concepts for the current slice.
        </div>
      </div>
    );
  }

  return (
    <div className="academic-card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2 text-sm font-semibold text-academic-text uppercase">
          <Sparkles className="w-4 h-4 text-primary-600" />
          Concept Constellations
        </div>
        <div className="text-xs text-academic-muted">
          {conceptClusters.stats.totalConcepts} concepts in {conceptClusters.stats.clusterCount} thematic clusters
        </div>
      </div>

      <div className="overflow-x-auto -mx-4 px-4">
        <svg
          ref={svgRef}
          className="w-full h-[500px] border border-gray-200 rounded-lg bg-gradient-to-br from-slate-50 to-blue-50"
        />
      </div>

      <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
        {conceptClusters.clusters.slice(0, 4).map((cluster, index) => (
          <div key={cluster.id} className="text-center">
            <div className="text-xs font-semibold text-academic-text mb-1">
              {cluster.label || `Cluster ${index + 1}`}
            </div>
            <div className="text-xs text-academic-muted">
              {cluster.size} concepts
            </div>
            {cluster.keywords && cluster.keywords.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1 justify-center">
                {cluster.keywords.slice(0, 2).map((keyword) => (
                  <span
                    key={keyword}
                    className="text-[9px] uppercase tracking-wide bg-primary-50 text-primary-700 px-1.5 py-0.5 rounded-full"
                  >
                    {keyword}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
