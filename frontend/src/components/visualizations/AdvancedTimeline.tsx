import { useEffect, useRef, useMemo } from 'react';
import * as d3 from 'd3';
import { Clock, Users, BookOpen, Lightbulb } from 'lucide-react';
import { useKGWorkspace } from '../../context/KGWorkspaceContext';
import type { TimelineNodeSummary, TimelinePeriodSummary } from '../../types';

interface TimelineData {
  periods: TimelinePeriodSummary[];
  nodes: TimelineNodeSummary[];
  range: { minYear: number; maxYear: number };
}

const AcademicColors = {
  person: '#2563eb',      // Blue
  work: '#7c3aed',        // Purple  
  concept: '#dc2626',     // Red
  argument: '#ea580c',    // Orange
  debate: '#059669',      // Green
  school: '#0891b2',      // Cyan
  period: '#be185d',      // Pink
};

function formatYear(year?: number | null) {
  if (year === null || year === undefined) return '';
  if (year < 0) return `${Math.abs(year)} BCE`;
  if (year === 0) return '0';
  return `${year} CE`;
}

function getNodeIcon(type: string) {
  switch (type) {
    case 'person': return Users;
    case 'work': return BookOpen;
    case 'concept': return Lightbulb;
    default: return Clock;
  }
}

export default function AdvancedTimeline() {
  const svgRef = useRef<SVGSVGElement>(null);
  const { state: { timeline, loading } } = useKGWorkspace();

  const processedData = useMemo(() => {
    if (!timeline) return null;

    // Create a comprehensive timeline with all nodes positioned by year
    const allNodes = timeline.periods.flatMap(period => period.nodes);
    const nodesByYear = allNodes.reduce((acc, node) => {
      const year = node.startYear ?? 0;
      if (!acc[year]) acc[year] = [];
      acc[year].push(node);
      return acc;
    }, {} as Record<number, TimelineNodeSummary[]>);

    return {
      periods: timeline.periods,
      nodesByYear,
      range: timeline.range,
      allNodes
    };
  }, [timeline]);

  useEffect(() => {
    if (!svgRef.current || !processedData) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const width = 1200;
    const height = 400;
    const margin = { top: 60, right: 40, bottom: 80, left: 60 };

    svg.attr('viewBox', `0 0 ${width} ${height}`);

    // Create scales
    const xScale = d3.scaleLinear()
      .domain([processedData.range.minYear, processedData.range.maxYear])
      .range([margin.left, width - margin.right]);

    const yScale = d3.scaleBand()
      .domain(['timeline', 'periods', 'nodes'])
      .range([margin.top, height - margin.bottom])
      .padding(0.1);

    // Create timeline axis
    const xAxis = d3.axisBottom(xScale)
      .tickFormat(d => formatYear(d as number))
      .ticks(8);

    svg.append('g')
      .attr('transform', `translate(0, ${height - margin.bottom})`)
      .call(xAxis)
      .selectAll('text')
      .style('font-family', 'Georgia, serif')
      .style('font-size', '12px')
      .style('fill', '#374151');

    // Draw period blocks
    const periodGroup = svg.append('g').attr('class', 'periods');
    
    processedData.periods.forEach((period, i) => {
      const x1 = xScale(period.startYear ?? processedData.range.minYear);
      const x2 = xScale(period.endYear ?? processedData.range.maxYear);
      const y = yScale('periods')!;
      const height = yScale.bandwidth();

      const periodRect = periodGroup.append('rect')
        .attr('x', x1)
        .attr('y', y)
        .attr('width', Math.max(x2 - x1, 20))
        .attr('height', height)
        .attr('fill', AcademicColors.period)
        .attr('opacity', 0.3)
        .attr('rx', 4);

      // Add period label
      periodGroup.append('text')
        .attr('x', x1 + 10)
        .attr('y', y + height/2)
        .attr('dy', '0.35em')
        .text(period.label)
        .style('font-family', 'Georgia, serif')
        .style('font-size', '11px')
        .style('font-weight', '600')
        .style('fill', '#1f2937');

      // Add period stats
      const totalNodes = Object.values(period.counts).reduce((sum, count) => sum + count, 0);
      periodGroup.append('text')
        .attr('x', x1 + 10)
        .attr('y', y + height/2 + 15)
        .attr('dy', '0.35em')
        .text(`${totalNodes} entities`)
        .style('font-family', 'Georgia, serif')
        .style('font-size', '10px')
        .style('fill', '#6b7280');
    });

    // Draw nodes as a stream
    const nodeGroup = svg.append('g').attr('class', 'nodes');
    
    // Create a stream layout for nodes
    const nodeYears = Object.keys(processedData.nodesByYear).map(Number).sort((a, b) => a - b);
    
    nodeYears.forEach(year => {
      const nodes = processedData.nodesByYear[year];
      const x = xScale(year);
      const baseY = yScale('nodes')!;
      
      // Distribute nodes vertically
      nodes.forEach((node, i) => {
        const y = baseY + (i * 8) + 4;
        const IconComponent = getNodeIcon(node.type || 'concept');
        
        // Draw node circle
        nodeGroup.append('circle')
          .attr('cx', x)
          .attr('cy', y)
          .attr('r', 6)
          .attr('fill', AcademicColors[node.type as keyof typeof AcademicColors] || AcademicColors.concept)
          .attr('opacity', 0.8)
          .style('cursor', 'pointer');

        // Add node label
        nodeGroup.append('text')
          .attr('x', x + 10)
          .attr('y', y)
          .attr('dy', '0.35em')
          .text(node.label)
          .style('font-family', 'Georgia, serif')
          .style('font-size', '10px')
          .style('fill', '#374151')
          .style('cursor', 'pointer');
      });
    });

    // Add title
    svg.append('text')
      .attr('x', width / 2)
      .attr('y', 30)
      .attr('text-anchor', 'middle')
      .text('Philosophical Timeline: Evolution of Ideas')
      .style('font-family', 'Georgia, serif')
      .style('font-size', '18px')
      .style('font-weight', '600')
      .style('fill', '#1f2937');

  }, [processedData]);

  if (loading && !timeline) {
    return (
      <div className="academic-card">
        <div className="py-16 text-center text-academic-muted text-sm">Loading timeline…</div>
      </div>
    );
  }

  if (!timeline || timeline.periods.length === 0) {
    return (
      <div className="academic-card">
        <div className="py-16 text-center text-academic-muted text-sm">
          Timeline data is unavailable for the current filter selection.
        </div>
      </div>
    );
  }

  return (
    <div className="academic-card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2 text-sm font-semibold text-academic-text uppercase">
          <Clock className="w-4 h-4 text-primary-600" />
          Advanced Chronological Analysis
        </div>
        <div className="text-xs text-academic-muted">
          {formatYear(timeline.range.minYear)} → {formatYear(timeline.range.maxYear)}
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
      </div>
    </div>
  );
}
