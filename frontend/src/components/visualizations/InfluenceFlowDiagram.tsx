import { useEffect, useRef, useMemo } from 'react';
import * as d3 from 'd3';
import { TrendingUp } from 'lucide-react';
import { useKGWorkspace } from '../../context/KGWorkspaceContext';

interface MatrixAxis {
  key: string;
  label: string;
}

interface MatrixCell {
  row: string;
  col: string;
  value: number;
}

function drawInfluenceMatrix(svg: d3.Selection<SVGSVGElement, unknown, null, undefined>,
                            rows: MatrixAxis[],
                            cols: MatrixAxis[],
                            cells: MatrixCell[],
                            width: number,
                            height: number) {
  svg.selectAll('*').remove();

  const margin = { top: 120, right: 40, bottom: 40, left: 160 };
  const cellWidth = (width - margin.left - margin.right) / cols.length;
  const cellHeight = (height - margin.top - margin.bottom) / rows.length;

  // Create scales
  const colorScale = d3.scaleSequential(d3.interpolateBlues)
    .domain([0, d3.max(cells, d => d.value) || 1]);

  // Draw background
  svg.append('rect')
    .attr('width', width)
    .attr('height', height)
    .attr('fill', '#f8fafc')
    .attr('rx', 8);

  // Create matrix group
  const matrix = svg.append('g')
    .attr('transform', `translate(${margin.left}, ${margin.top})`);

  // Draw cells
  cells.forEach(cell => {
    const rowIndex = rows.findIndex(r => r.key === cell.row);
    const colIndex = cols.findIndex(c => c.key === cell.col);

    if (rowIndex === -1 || colIndex === -1) return;

    matrix.append('rect')
      .attr('x', colIndex * cellWidth)
      .attr('y', rowIndex * cellHeight)
      .attr('width', cellWidth - 2)
      .attr('height', cellHeight - 2)
      .attr('fill', colorScale(cell.value))
      .attr('stroke', '#e5e7eb')
      .attr('stroke-width', 1)
      .style('cursor', 'pointer')
      .on('mouseover', function() {
        d3.select(this).attr('stroke', '#3b82f6').attr('stroke-width', 2);
      })
      .on('mouseout', function() {
        d3.select(this).attr('stroke', '#e5e7eb').attr('stroke-width', 1);
      });

    // Add value text if significant
    if (cell.value > 0) {
      matrix.append('text')
        .attr('x', colIndex * cellWidth + cellWidth / 2)
        .attr('y', rowIndex * cellHeight + cellHeight / 2)
        .attr('text-anchor', 'middle')
        .attr('dy', '0.35em')
        .text(cell.value)
        .style('font-family', 'Georgia, serif')
        .style('font-size', '12px')
        .style('font-weight', '600')
        .style('fill', cell.value > (d3.max(cells, d => d.value) || 1) / 2 ? '#ffffff' : '#1f2937')
        .style('pointer-events', 'none');
    }
  });

  // Add row labels
  rows.forEach((row, i) => {
    matrix.append('text')
      .attr('x', -10)
      .attr('y', i * cellHeight + cellHeight / 2)
      .attr('text-anchor', 'end')
      .attr('dy', '0.35em')
      .text(row.label)
      .style('font-family', 'Georgia, serif')
      .style('font-size', '11px')
      .style('fill', '#374151');
  });

  // Add column labels
  cols.forEach((col, i) => {
    matrix.append('text')
      .attr('x', i * cellWidth + cellWidth / 2)
      .attr('y', -10)
      .attr('text-anchor', 'middle')
      .text(col.label)
      .style('font-family', 'Georgia, serif')
      .style('font-size', '11px')
      .style('fill', '#374151')
      .attr('transform', `rotate(-45, ${i * cellWidth + cellWidth / 2}, -10)`);
  });

  // Add title
  svg.append('text')
    .attr('x', width / 2)
    .attr('y', 30)
    .attr('text-anchor', 'middle')
    .text('Influence Matrix: Schools × Relation Types')
    .style('font-family', 'Georgia, serif')
    .style('font-size', '18px')
    .style('font-weight', '600')
    .style('fill', '#1f2937');
}

export default function InfluenceFlowDiagram() {
  const svgRef = useRef<SVGSVGElement>(null);
  const { state: { influenceMatrix } } = useKGWorkspace();

  const matrixData = useMemo(() => {
    if (!influenceMatrix) return null;

    // Map InfluenceMatrixCell to MatrixCell format
    const cells: MatrixCell[] = influenceMatrix.cells.map(cell => ({
      row: cell.rowKey,
      col: cell.columnKey,
      value: cell.count
    }));

    return {
      rows: influenceMatrix.rows,
      cols: influenceMatrix.columns,
      cells
    };
  }, [influenceMatrix]);

  useEffect(() => {
    if (!svgRef.current || !matrixData) return;

    const width = 1000;
    const height = 600;

    const svg = d3.select(svgRef.current);
    svg.attr('viewBox', `0 0 ${width} ${height}`);

    drawInfluenceMatrix(svg, matrixData.rows, matrixData.cols, matrixData.cells, width, height);

  }, [matrixData]);

  if (!influenceMatrix) {
    return (
      <div className="academic-card">
        <div className="py-16 text-center text-academic-muted text-sm">
          Influence matrix data unavailable for current filters.
        </div>
      </div>
    );
  }

  return (
    <div className="academic-card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2 text-sm font-semibold text-academic-text uppercase">
          <TrendingUp className="w-4 h-4 text-primary-600" />
          Influence Matrix Analysis
        </div>
        <div className="text-xs text-academic-muted">
          Heatmap of philosophical influences across schools and relation types
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
          <div className="w-3 h-3 rounded-full" style={{background: 'linear-gradient(to right, #eff6ff, #1e40af)'}}></div>
          <span>Influence Strength (Light → Strong)</span>
        </div>
      </div>
    </div>
  );
}
