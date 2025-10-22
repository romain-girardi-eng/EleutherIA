import { useEffect, useRef, useMemo } from 'react';
import * as d3 from 'd3';
import { ArrowRight, TrendingUp, Users } from 'lucide-react';
import { useKGWorkspace } from '../../context/KGWorkspaceContext';

interface InfluenceFlowData {
  schools: Array<{ key: string; label: string; count: number }>;
  relations: Array<{ key: string; label: string; count: number }>;
  flows: Array<{
    source: string;
    target: string;
    value: number;
    relation: string;
  }>;
}

const FlowColors = {
  stoic: '#3b82f6',
  epicurean: '#8b5cf6',
  platonic: '#f59e0b',
  aristotelian: '#10b981',
  skeptic: '#ef4444',
  neoplatonic: '#06b6d4',
  default: '#6b7280'
};

function getSchoolColor(school: string) {
  const schoolLower = school.toLowerCase();
  if (schoolLower.includes('stoic')) return FlowColors.stoic;
  if (schoolLower.includes('epicurean')) return FlowColors.epicurean;
  if (schoolLower.includes('platonic')) return FlowColors.platonic;
  if (schoolLower.includes('aristotelian')) return FlowColors.aristotelian;
  if (schoolLower.includes('skeptic')) return FlowColors.skeptic;
  if (schoolLower.includes('neoplatonic')) return FlowColors.neoplatonic;
  return FlowColors.default;
}

function createSankeyLayout(data: InfluenceFlowData, width: number, height: number) {
  // Create nodes (schools)
  const nodes = data.schools.map(school => ({
    id: school.key,
    name: school.label,
    count: school.count,
    color: getSchoolColor(school.label)
  }));

  // Create links (influence flows)
  const links = data.flows.map(flow => ({
    source: flow.source,
    target: flow.target,
    value: flow.value,
    relation: flow.relation
  }));

  // Calculate node positions using D3's Sankey layout
  const sankey = d3.sankey<{ id: string; name: string; count: number; color: string }, { source: string; target: string; value: number; relation: string }>()
    .nodeId((d: any) => d.id)
    .nodeWidth(20)
    .nodePadding(10)
    .extent([[1, 1], [width - 1, height - 1]]);

  const { nodes: positionedNodes, links: positionedLinks } = sankey({
    nodes: nodes.map(d => ({ ...d })),
    links: links.map(d => ({ ...d }))
  });

  return { nodes: positionedNodes, links: positionedLinks };
}

function drawInfluenceFlow(svg: d3.Selection<SVGSVGElement, unknown, null, undefined>, 
                         data: InfluenceFlowData, 
                         width: number, 
                         height: number) {
  svg.selectAll('*').remove();

  // Create gradient definitions
  const defs = svg.append('defs');
  
  // Flow gradient
  const flowGradient = defs.append('linearGradient')
    .attr('id', 'flowGradient')
    .attr('x1', '0%')
    .attr('y1', '0%')
    .attr('x2', '100%')
    .attr('y2', '0%');
  
  flowGradient.append('stop')
    .attr('offset', '0%')
    .attr('stop-color', '#3b82f6')
    .attr('stop-opacity', 0.8);
  
  flowGradient.append('stop')
    .attr('offset', '100%')
    .attr('stop-color', '#8b5cf6')
    .attr('stop-opacity', 0.4);

  // Background gradient
  const bgGradient = defs.append('radialGradient')
    .attr('id', 'flowBg')
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
    .attr('fill', 'url(#flowBg)')
    .attr('rx', 8)
    .attr('ry', 8);

  const { nodes, links } = createSankeyLayout(data, width, height);

  // Draw links (flows)
  const linkGroup = svg.append('g').attr('class', 'links');
  
  const link = linkGroup.selectAll('.link')
    .data(links)
    .enter().append('path')
    .attr('class', 'link')
    .attr('d', d3.sankeyLinkHorizontal())
    .attr('stroke', 'url(#flowGradient)')
    .attr('stroke-width', (d: any) => Math.max(1, d.width))
    .attr('opacity', 0.6)
    .style('cursor', 'pointer');

  // Add link labels
  linkGroup.selectAll('.link-label')
    .data(links)
    .enter().append('text')
    .attr('class', 'link-label')
    .attr('x', (d: any) => (d.source.x1 + d.target.x0) / 2)
    .attr('y', (d: any) => (d.y0 + d.y1) / 2)
    .attr('dy', '0.35em')
    .attr('text-anchor', 'middle')
    .text((d: any) => d.relation)
    .style('font-family', 'Georgia, serif')
    .style('font-size', '10px')
    .style('fill', '#374151')
    .style('font-weight', '500');

  // Draw nodes (schools)
  const nodeGroup = svg.append('g').attr('class', 'nodes');
  
  const node = nodeGroup.selectAll('.node')
    .data(nodes)
    .enter().append('g')
    .attr('class', 'node')
    .style('cursor', 'pointer');

  // Draw node rectangles
  node.append('rect')
    .attr('x', (d: any) => d.x0)
    .attr('y', (d: any) => d.y0)
    .attr('height', (d: any) => d.y1 - d.y0)
    .attr('width', (d: any) => d.x1 - d.x0)
    .attr('fill', (d: any) => d.color)
    .attr('opacity', 0.8)
    .attr('rx', 4)
    .attr('ry', 4);

  // Add node labels
  node.append('text')
    .attr('x', (d: any) => d.x0 - 6)
    .attr('y', (d: any) => (d.y0 + d.y1) / 2)
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .text((d: any) => d.name)
    .style('font-family', 'Georgia, serif')
    .style('font-size', '12px')
    .style('font-weight', '600')
    .style('fill', '#1f2937');

  // Add node counts
  node.append('text')
    .attr('x', (d: any) => d.x1 + 6)
    .attr('y', (d: any) => (d.y0 + d.y1) / 2)
    .attr('dy', '0.35em')
    .attr('text-anchor', 'start')
    .text((d: any) => d.count)
    .style('font-family', 'Georgia, serif')
    .style('font-size', '10px')
    .style('fill', '#6b7280');

  // Add title
  svg.append('text')
    .attr('x', width / 2)
    .attr('y', 30)
    .attr('text-anchor', 'middle')
    .text('Philosophical Influence Flow')
    .style('font-family', 'Georgia, serif')
    .style('font-size', '18px')
    .style('font-weight', '600')
    .style('fill', '#1f2937');

  // Add subtitle
  svg.append('text')
    .attr('x', width / 2)
    .attr('y', 50)
    .attr('text-anchor', 'middle')
    .text('How ideas flow between philosophical schools')
    .style('font-family', 'Georgia, serif')
    .style('font-size', '12px')
    .style('fill', '#6b7280');
}

export default function InfluenceFlowDiagram() {
  const svgRef = useRef<SVGSVGElement>(null);
  const { state: { influenceMatrix, loading } } = useKGWorkspace();

  const flowData = useMemo(() => {
    if (!influenceMatrix) return null;

    // Transform matrix data into flow format
    const schools = influenceMatrix.rows.map(row => ({
      key: row.key,
      label: row.label,
      count: row.count || 0
    }));

    const relations = influenceMatrix.columns.map(col => ({
      key: col.key,
      label: col.label,
      count: col.count || 0
    }));

    const flows: Array<{ source: string; target: string; value: number; relation: string }> = [];
    
    influenceMatrix.cells.forEach(cell => {
      if (cell.count > 0) {
        flows.push({
          source: cell.rowKey,
          target: cell.columnKey,
          value: cell.count,
          relation: cell.columnKey.replace(/_/g, ' ')
        });
      }
    });

    return { schools, relations, flows };
  }, [influenceMatrix]);

  useEffect(() => {
    if (!svgRef.current || !flowData) return;

    const width = 1000;
    const height = 400;
    
    const svg = d3.select(svgRef.current);
    svg.attr('viewBox', `0 0 ${width} ${height}`);

    drawInfluenceFlow(svg, flowData, width, height);

  }, [flowData]);

  if (loading && !influenceMatrix) {
    return (
      <div className="academic-card">
        <div className="py-12 text-center text-academic-muted text-sm">Computing influence flow…</div>
      </div>
    );
  }

  if (!influenceMatrix || influenceMatrix.rows.length === 0 || influenceMatrix.columns.length === 0) {
    return (
      <div className="academic-card">
        <div className="py-12 text-center text-academic-muted text-sm">No influence data for current filters.</div>
      </div>
    );
  }

  return (
    <div className="academic-card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2 text-sm font-semibold text-academic-text uppercase">
          <TrendingUp className="w-4 h-4 text-primary-600" />
          Influence Flow Analysis
        </div>
        <div className="text-xs text-academic-muted">
          {influenceMatrix.totals.schoolsCovered} schools • {influenceMatrix.totals.relationsConsidered} relations •{' '}
          {influenceMatrix.totals.edgesMapped.toLocaleString()} mapped edges
        </div>
      </div>

      <div className="overflow-x-auto -mx-4 px-4">
        <svg
          ref={svgRef}
          className="w-full h-[400px] border border-gray-200 rounded-lg bg-gradient-to-r from-blue-50/30 to-purple-50/30"
        />
      </div>

      <div className="mt-4 flex flex-wrap gap-4 text-xs">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-blue-600"></div>
          <span>Stoic</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-purple-600"></div>
          <span>Epicurean</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-yellow-600"></div>
          <span>Platonic</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-green-600"></div>
          <span>Aristotelian</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-red-600"></div>
          <span>Skeptic</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-cyan-600"></div>
          <span>Neoplatonic</span>
        </div>
      </div>
    </div>
  );
}
