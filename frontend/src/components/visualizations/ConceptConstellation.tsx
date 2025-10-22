import { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { Sparkles } from 'lucide-react';
import { useKGWorkspace } from '../../context/KGWorkspaceContext';
import type { ConceptClusterSummary } from '../../types';

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
  neutral: '#6b7280',
};

function drawConstellation(
  svg: d3.Selection<SVGSVGElement, unknown, null, undefined>,
  data: ConstellationData,
  width: number,
  height: number,
) {
  svg.selectAll('*').remove();

  const defs = svg.append('defs');

  const nodeGradient = defs
    .append('radialGradient')
    .attr('id', 'constellationNode')
    .attr('cx', '50%')
    .attr('cy', '50%')
    .attr('r', '50%');
  nodeGradient.append('stop').attr('offset', '0%').attr('stop-color', '#ffffff').attr('stop-opacity', 0.8);
  nodeGradient.append('stop').attr('offset', '100%').attr('stop-color', '#dbeafe').attr('stop-opacity', 0.3);

  const linkGradient = defs
    .append('linearGradient')
    .attr('id', 'constellationLink')
    .attr('x1', '0%')
    .attr('y1', '0%')
    .attr('x2', '100%')
    .attr('y2', '0%');
  linkGradient.append('stop').attr('offset', '0%').attr('stop-color', ConstellationColors.primary).attr('stop-opacity', 0.45);
  linkGradient.append('stop').attr('offset', '100%').attr('stop-color', ConstellationColors.secondary).attr('stop-opacity', 0.2);

  const backgroundGradient = defs
    .append('radialGradient')
    .attr('id', 'constellationBackground')
    .attr('cx', '50%')
    .attr('cy', '50%')
    .attr('r', '75%');
  backgroundGradient.append('stop').attr('offset', '0%').attr('stop-color', '#f8fafc').attr('stop-opacity', 0.15);
  backgroundGradient.append('stop').attr('offset', '100%').attr('stop-color', '#e0f2fe').attr('stop-opacity', 0.1);

  svg
    .append('rect')
    .attr('width', width)
    .attr('height', height)
    .attr('fill', 'url(#constellationBackground)')
    .attr('rx', 16);

  const clusterCount = data.clusters.length;
  const cols = clusterCount > 3 ? Math.ceil(Math.sqrt(clusterCount)) : clusterCount;
  const rows = Math.max(1, Math.ceil(clusterCount / Math.max(cols, 1)));
  const padding = 60;
  const effectiveCols = Math.max(cols, 1);
  const effectiveRows = Math.max(rows, 1);
  const cellWidth = (width - padding * 2) / effectiveCols;
  const cellHeight = (height - padding * 2) / effectiveRows;
  const baseRadius = Math.max(40, Math.min(cellWidth, cellHeight) / 2 - 30);

  data.clusters.forEach((cluster, index) => {
    const row = Math.floor(index / effectiveCols);
    const col = index % effectiveCols;
    const cx =
      clusterCount === 1
        ? width / 2
        : padding + col * cellWidth + cellWidth / 2;
    const cy =
      clusterCount === 1
        ? height / 2
        : padding + row * cellHeight + cellHeight / 2;

    const clusterGroup = svg.append('g').attr('transform', `translate(${cx}, ${cy})`);

    clusterGroup
      .append('circle')
      .attr('r', baseRadius + 28)
      .attr('fill', index % 2 === 0 ? '#e0e7ff' : '#ede9fe')
      .attr('opacity', 0.25);

    clusterGroup
      .append('circle')
      .attr('r', baseRadius + 6)
      .attr('stroke', '#c7d2fe')
      .attr('stroke-dasharray', '6 6')
      .attr('fill', 'none')
      .attr('opacity', 0.6);

    clusterGroup
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('y', -baseRadius - 24)
      .text(cluster.label || `Cluster ${index + 1}`)
      .style('font-family', 'Georgia, serif')
      .style('font-size', '13px')
      .style('font-weight', '600')
      .style('fill', '#1f2937');

    clusterGroup
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('y', -baseRadius - 8)
      .text(`${cluster.size} concepts`)
      .style('font-family', 'Georgia, serif')
      .style('font-size', '11px')
      .style('fill', '#6b7280');

    const keywords = (cluster.keywords || []).slice(0, 3);
    if (keywords.length > 0) {
      clusterGroup
        .append('text')
        .attr('text-anchor', 'middle')
        .attr('y', baseRadius + 28)
        .text(keywords.join(' • '))
        .style('font-family', 'Georgia, serif')
        .style('font-size', '11px')
        .style('fill', '#4338ca');
    }

    const nodes = (cluster.nodes || []).slice(0, 32);
    if (nodes.length === 0) {
      clusterGroup
        .append('text')
        .attr('text-anchor', 'middle')
        .attr('y', 8)
        .text('No concepts in cluster')
        .style('font-family', 'Georgia, serif')
        .style('font-size', '11px')
        .style('fill', '#6b7280');
      return;
    }
    const positions = nodes.map((node, nodeIndex) => {
      const angle = (2 * Math.PI * nodeIndex) / Math.max(nodes.length, 1);
      const radialBand = 0.55 + ((nodeIndex % 5) / 5) * 0.4;
      const radius = baseRadius * Math.min(1, radialBand);
      return {
        node,
        x: radius * Math.cos(angle),
        y: radius * Math.sin(angle),
        angle,
      };
    });

    if (positions.length > 1) {
      const linkGroup = clusterGroup.append('g').attr('class', 'cluster-links');
      positions.forEach((position, idx) => {
        const next = positions[(idx + 1) % positions.length];
        linkGroup
          .append('line')
          .attr('x1', position.x)
          .attr('y1', position.y)
          .attr('x2', next.x)
          .attr('y2', next.y)
          .attr('stroke', 'url(#constellationLink)')
          .attr('stroke-width', 1.2)
          .attr('opacity', 0.6);
      });
    }

    const nodeGroup = clusterGroup.append('g').attr('class', 'cluster-nodes');
    const nodesSelection = nodeGroup
      .selectAll('g.node')
      .data(positions)
      .enter()
      .append('g')
      .attr('class', 'node')
      .attr('transform', (d) => `translate(${d.x}, ${d.y})`);

    nodesSelection
      .append('circle')
      .attr('r', 12)
      .attr('fill', 'url(#constellationNode)')
      .attr('stroke', '#1d4ed8')
      .attr('stroke-width', 1.2)
      .attr('opacity', 0.9);

    nodesSelection
      .append('circle')
      .attr('r', 18)
      .attr('fill', ConstellationColors.primary)
      .attr('opacity', 0.12);

    nodesSelection
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', 28)
      .text((d) => d.node.label)
      .style('font-family', 'Georgia, serif')
      .style('font-size', '10px')
      .style('font-weight', '500')
      .style('fill', '#1f2937');

    nodesSelection
      .append('title')
      .text(
        (d) =>
          `${d.node.label}\n${d.node.period || 'No period specified'}${
            d.node.school ? ` · ${d.node.school}` : ''
          }${d.node.keywords?.length ? `\nKeywords: ${d.node.keywords.join(', ')}` : ''}`,
      );
  });

  svg
    .append('text')
    .attr('x', width / 2)
    .attr('y', 34)
    .attr('text-anchor', 'middle')
    .text('Concept Constellations')
    .style('font-family', 'Georgia, serif')
    .style('font-size', '16px')
    .style('font-weight', '600')
    .style('fill', '#1f2937');

  svg
    .append('text')
    .attr('x', width / 2)
    .attr('y', height - 26)
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

    const width = 960;
    const height = 520;
    
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
          className="w-full h-[520px] border border-gray-200 rounded-lg bg-gradient-to-br from-slate-50 to-blue-50"
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
