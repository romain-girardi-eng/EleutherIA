import { useEffect, useRef, useMemo } from 'react';
import * as d3 from 'd3';
import { Clock } from 'lucide-react';
import { useKGWorkspace } from '../../context/KGWorkspaceContext';
import type { TimelineNodeSummary } from '../../types';

const AcademicColors = {
  person: '#2563eb',      // Blue
  work: '#7c3aed',        // Purple  
  concept: '#dc2626',     // Red
  argument: '#ea580c',    // Orange
  debate: '#059669',      // Green
  school: '#0891b2',      // Cyan
  period: '#be185d',      // Pink
};

type TimelineChartNode = TimelineNodeSummary & {
  year: number;
  laneType: string;
  groupIndex: number;
  groupSize: number;
};

function formatYear(year?: number | null) {
  if (year === null || year === undefined) return '';
  if (year < 0) return `${Math.abs(year)} BCE`;
  if (year === 0) return '0';
  return `${year} CE`;
}

export default function AdvancedTimeline() {
  const svgRef = useRef<SVGSVGElement>(null);
  const { state: { timeline, loading } } = useKGWorkspace();

  const processedData = useMemo(() => {
    if (!timeline) return null;

    const chartNodes: TimelineChartNode[] = [];
    timeline.periods.forEach((period) => {
      period.nodes.forEach((node) => {
        const year = node.startYear ?? node.endYear;
        if (year === null || year === undefined) {
          return;
        }

        chartNodes.push({
          ...node,
          year,
          laneType: node.type || 'concept',
          groupIndex: 0,
          groupSize: 1,
        });
      });
    });

    const typeCounts = timeline.totals?.byType || {};
    const orderedTypes = Object.entries(typeCounts)
      .sort((a, b) => (b[1] || 0) - (a[1] || 0))
      .map(([type]) => type);

    const extraTypes = Array.from(
      new Set(chartNodes.map((node) => node.laneType).filter(Boolean)),
    ).filter((type) => !orderedTypes.includes(type));

    const typeOrder = [...orderedTypes, ...extraTypes];
    if (typeOrder.length === 0) {
      typeOrder.push('concept');
    }

    const groupBuckets = new Map<string, TimelineChartNode[]>();
    chartNodes.forEach((node) => {
      const key = `${node.laneType}:${node.year}`;
      const bucket = groupBuckets.get(key);
      if (bucket) {
        bucket.push(node);
      } else {
        groupBuckets.set(key, [node]);
      }
    });

    groupBuckets.forEach((bucket) => {
      bucket.sort((a, b) => (a.label || '').localeCompare(b.label || ''));
      bucket.forEach((node, index) => {
        node.groupIndex = index;
        node.groupSize = bucket.length;
      });
    });

    const highlightNodes = chartNodes
      .slice()
      .sort((a, b) => (b.relationCount || 0) - (a.relationCount || 0))
      .slice(0, 8);

    const periodSummaries = timeline.periods.map((period) => ({
      ...period,
      total: Object.values(period.counts || {}).reduce((sum, value) => sum + value, 0),
    }));

    return {
      periods: timeline.periods,
      nodes: chartNodes,
      range: timeline.range,
      typeOrder,
      highlightNodes,
      periodSummaries,
    };
  }, [timeline]);

  useEffect(() => {
    if (!svgRef.current || !processedData) {
      return;
    }

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const containerElement = svgRef.current.parentElement as HTMLElement | null;
    const containerSelection = containerElement ? d3.select(containerElement) : null;

    const minYear =
      processedData.range.minYear ??
      (processedData.nodes.length
        ? d3.min(processedData.nodes, (node) => node.year) ?? -400
        : -400);
    const maxYear =
      processedData.range.maxYear ??
      (processedData.nodes.length
        ? d3.max(processedData.nodes, (node) => node.year) ?? 600
        : 600);

    const width = 1200;
    const laneHeight = 60;
    const margin = { top: 90, right: 48, bottom: 70, left: 140 };
    const laneAreaHeight = Math.max(processedData.typeOrder.length, 1) * laneHeight;
    const height = margin.top + laneAreaHeight + margin.bottom;

    svg.attr('viewBox', `0 0 ${width} ${height}`);

    const xScale = d3
      .scaleLinear()
      .domain([minYear, maxYear])
      .nice()
      .range([margin.left, width - margin.right]);

    const yScale = d3
      .scaleBand<string>()
      .domain(processedData.typeOrder)
      .range([margin.top, margin.top + laneAreaHeight])
      .paddingInner(0.4);

    const highlightIds = new Set(processedData.highlightNodes.map((node) => node.id));

    const defs = svg.append('defs');
    const gradient = defs
      .append('linearGradient')
      .attr('id', 'timelineGradient')
      .attr('x1', '0%')
      .attr('x2', '100%')
      .attr('y1', '0%')
      .attr('y2', '0%');
    gradient.append('stop').attr('offset', '0%').attr('stop-color', '#eef2ff').attr('stop-opacity', 0.3);
    gradient.append('stop').attr('offset', '100%').attr('stop-color', '#ede9fe').attr('stop-opacity', 0.2);

    const cardBackground = svg
      .append('rect')
      .attr('x', margin.left - 20)
      .attr('y', margin.top - 70)
      .attr('width', width - margin.left - margin.right + 40)
      .attr('height', laneAreaHeight + 120)
      .attr('fill', 'url(#timelineGradient)');

    cardBackground.lower();

    const periodGroup = svg.append('g').attr('class', 'timeline-periods');
    processedData.periods.forEach((period, index) => {
      const start = period.startYear ?? minYear;
      const end = period.endYear ?? maxYear;
      const x1 = xScale(start);
      const x2 = xScale(end);
      const widthPx = Math.max(x2 - x1, 24);

      periodGroup
        .append('rect')
        .attr('x', x1)
        .attr('y', margin.top - 60)
        .attr('width', widthPx)
        .attr('height', 36)
        .attr('rx', 8)
        .attr('fill', index % 2 === 0 ? '#c7d2fe' : '#bfdbfe')
        .attr('opacity', 0.25);

      periodGroup
        .append('text')
        .attr('x', x1 + widthPx / 2)
        .attr('y', margin.top - 38)
        .attr('text-anchor', 'middle')
        .text(period.label)
        .style('font-family', 'Georgia, serif')
        .style('font-size', '11px')
        .style('font-weight', '600')
        .style('fill', '#1f2937');
    });

    const lanes = svg.append('g').attr('class', 'timeline-lanes');
    processedData.typeOrder.forEach((type, index) => {
      const y = yScale(type);
      if (y === undefined) {
        return;
      }

      lanes
        .append('rect')
        .attr('x', margin.left)
        .attr('y', y)
        .attr('width', width - margin.left - margin.right)
        .attr('height', yScale.bandwidth())
        .attr('fill', index % 2 === 0 ? '#f8fafc' : '#eef2ff')
        .attr('opacity', 0.5);

      lanes
        .append('text')
        .attr('x', margin.left - 16)
        .attr('y', y + yScale.bandwidth() / 2)
        .attr('text-anchor', 'end')
        .attr('dy', '0.35em')
        .text(type.charAt(0).toUpperCase() + type.slice(1))
        .style('font-family', 'Georgia, serif')
        .style('font-size', '12px')
        .style('font-weight', '600')
        .style('fill', '#1f2937');
    });

    const xAxis = d3
      .axisBottom(xScale)
      .tickFormat((d) => formatYear(typeof d === 'number' ? d : Number(d)))
      .ticks(10);

    svg
      .append('g')
      .attr('transform', `translate(0, ${margin.top + laneAreaHeight})`)
      .call(xAxis)
      .selectAll('text')
      .style('font-family', 'Georgia, serif')
      .style('font-size', '11px')
      .style('fill', '#374151');

    svg
      .append('text')
      .attr('x', width / 2)
      .attr('y', 28)
      .attr('text-anchor', 'middle')
      .text('Philosophical Developments Across Time')
      .style('font-family', 'Georgia, serif')
      .style('font-size', '18px')
      .style('font-weight', '600')
      .style('fill', '#1f2937');

    svg
      .append('text')
      .attr('x', width / 2)
      .attr('y', 46)
      .attr('text-anchor', 'middle')
      .text('Each lane captures a category of entities; circle size reflects relationship activity.')
      .style('font-family', 'Georgia, serif')
      .style('font-size', '12px')
      .style('fill', '#6b7280');

    const getNodeY = (node: TimelineChartNode) => {
      const lane = yScale(node.laneType);
      const baseY = lane !== undefined ? lane + yScale.bandwidth() / 2 : margin.top;
      const spread = Math.min(14, (yScale.bandwidth() - 10) / Math.max(node.groupSize, 1));
      const offset = (node.groupIndex - (node.groupSize - 1) / 2) * spread;
      return baseY + offset;
    };

    const tooltip =
      containerSelection?.selectAll<HTMLDivElement, unknown>('.timeline-tooltip')
        .data([null])
        .join('div')
        .attr(
          'class',
          'timeline-tooltip pointer-events-none absolute z-20 hidden rounded-md border border-gray-200 bg-white px-3 py-2 shadow-lg text-[11px]',
        )
        .style('min-width', '200px') || null;

    const nodesGroup = svg.append('g').attr('class', 'timeline-nodes');

    const nodeSelection = nodesGroup
      .selectAll('circle')
      .data(processedData.nodes)
      .enter()
      .append('circle')
      .attr('cx', (d) => xScale(d.year))
      .attr('cy', (d) => getNodeY(d))
      .attr('r', (d) => {
        const highlight = highlightIds.has(d.id);
        const base = highlight ? 7 : 5;
        const importance = Math.min(3, (d.relationCount || 0) / 4);
        return base + importance;
      })
      .attr('fill', (d) => AcademicColors[d.type as keyof typeof AcademicColors] || AcademicColors.concept)
      .attr('stroke', (d) => (highlightIds.has(d.id) ? '#111827' : '#ffffff'))
      .attr('stroke-width', (d) => (highlightIds.has(d.id) ? 2 : d.groupSize > 3 ? 1 : 1.25))
      .attr('opacity', (d) => (d.groupSize > 4 ? 0.65 : d.groupSize > 2 ? 0.75 : 0.85))
      .style('cursor', 'pointer');

    if (tooltip && containerElement) {
      nodeSelection
        .on('mouseenter', (event, d) => {
          const [x, y] = d3.pointer(event, containerElement);
          tooltip
            .classed('hidden', false)
            .style('left', `${x + 18}px`)
            .style('top', `${Math.max(0, y - 12)}px`)
            .html(
              `<div class="font-semibold text-academic-text mb-1">${d.label}</div>
               <div class="text-academic-muted">${formatYear(d.year)} · ${d.period || 'No period label'}</div>
               ${d.school ? `<div class="text-academic-muted">School: ${d.school}</div>` : ''}
               ${
                 d.relationCount
                   ? `<div class="text-academic-muted">Connections: ${d.relationCount}</div>`
                   : ''
               }`,
            );
        })
        .on('mouseleave', () => {
          tooltip.classed('hidden', true);
        });
    }

    nodesGroup
      .selectAll('text.highlight-label')
      .data(processedData.highlightNodes)
      .enter()
      .append('text')
      .attr('class', 'highlight-label')
      .attr('x', (d) => xScale(d.year) + 10)
      .attr('y', (d) => getNodeY(d) - 10)
      .text((d) => d.label)
      .style('font-family', 'Georgia, serif')
      .style('font-size', '10px')
      .style('fill', '#374151')
      .style('font-weight', '500');

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

      <div className="overflow-x-auto -mx-4 px-4 relative">
        <svg
          ref={svgRef}
          className="w-full h-[520px] border border-gray-200 rounded-lg bg-gradient-to-r from-blue-50/40 to-purple-50/30"
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

      {processedData && processedData.highlightNodes.length > 0 && (
        <div className="mt-6 grid gap-6 lg:grid-cols-2 text-xs">
          <div>
            <h4 className="font-semibold text-academic-text mb-3 uppercase tracking-wide text-[11px]">
              Key Highlights
            </h4>
            <ul className="space-y-2">
              {processedData.highlightNodes.map((node) => (
                <li
                  key={node.id}
                  className="flex items-center justify-between rounded-md border border-gray-200 bg-white/70 px-3 py-2"
                >
                  <div>
                    <div className="text-sm font-medium text-academic-text">{node.label}</div>
                    <div className="text-[11px] text-academic-muted">
                      {formatYear(node.year)} · {node.period || 'No period'}
                    </div>
                    {node.school && (
                      <div className="text-[11px] text-academic-muted">
                        {node.school}
                      </div>
                    )}
                  </div>
                  <div className="text-[10px] uppercase tracking-wide text-primary-600">
                    {node.type}
                  </div>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h4 className="font-semibold text-academic-text mb-3 uppercase tracking-wide text-[11px]">
              Period Activity
            </h4>
            <div className="grid grid-cols-2 gap-2">
              {processedData.periodSummaries.slice(0, 6).map((period) => (
                <div
                  key={period.key}
                  className="rounded-md border border-gray-200 bg-white/70 px-3 py-2"
                >
                  <div className="text-sm font-medium text-academic-text">{period.label}</div>
                  <div className="text-[11px] text-academic-muted">
                    {period.total} entities
                  </div>
                  <div className="text-[11px] text-academic-muted">
                    {formatYear(period.startYear)} → {formatYear(period.endYear)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
