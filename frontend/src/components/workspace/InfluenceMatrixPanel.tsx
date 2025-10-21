import { memo, useMemo } from 'react';
import { Grid3x3 } from 'lucide-react';
import { useKGWorkspace } from '../../context/KGWorkspaceContext';

function getCellColor(value: number, max: number) {
  if (max === 0) {
    return 'rgba(99, 102, 241, 0.05)';
  }
  const intensity = Math.sqrt(value / max);
  const alpha = Math.min(0.75, 0.15 + 0.6 * intensity);
  return `rgba(14, 165, 233, ${alpha})`;
}

function formatRelationLabel(label: string) {
  return label.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

function InfluenceMatrixPanelComponent() {
  const {
    state: { influenceMatrix, loading },
    setFilters,
  } = useKGWorkspace();

  const maxValue = useMemo(() => {
    if (!influenceMatrix) return 0;
    return influenceMatrix.cells.reduce((max, cell) => Math.max(max, cell.count), 0);
  }, [influenceMatrix]);

  if (loading && !influenceMatrix) {
    return (
      <div className="academic-card">
        <div className="py-12 text-center text-academic-muted text-sm">Computing influence matrix…</div>
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

  const cellMap = new Map(
    influenceMatrix.cells.map((cell) => [`${cell.rowKey}::${cell.columnKey}`, cell])
  );

  const handleRowToggle = (school: string) => {
    setFilters((prev) => {
      const current = new Set(prev.schools);
      if (current.has(school)) {
        current.delete(school);
      } else {
        current.add(school);
      }
      return { ...prev, schools: Array.from(current) };
    });
  };

  const handleColumnToggle = (relation: string) => {
    setFilters((prev) => {
      const current = new Set(prev.relations);
      if (current.has(relation)) {
        current.delete(relation);
      } else {
        current.add(relation);
      }
      return { ...prev, relations: Array.from(current) };
    });
  };

  return (
    <div className="academic-card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2 text-sm font-semibold text-academic-text uppercase">
          <Grid3x3 className="w-4 h-4 text-primary-600" />
          Influence Matrix
        </div>
        <div className="text-xs text-academic-muted">
          {influenceMatrix.totals.schoolsCovered} schools • {influenceMatrix.totals.relationsConsidered} relations •{' '}
          {influenceMatrix.totals.edgesMapped.toLocaleString()} mapped edges
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full border-collapse">
          <thead>
            <tr>
              <th className="sticky left-0 top-0 z-10 bg-white text-xs text-academic-muted uppercase px-3 py-2 border border-gray-200 text-left">
                School
              </th>
              {influenceMatrix.columns.map((column) => (
                <th
                  key={column.key}
                  className="text-xs text-academic-muted uppercase px-3 py-2 border border-gray-200 bg-white hover:bg-primary-50 cursor-pointer"
                  onClick={() => handleColumnToggle(column.key)}
                >
                  {formatRelationLabel(column.label)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {influenceMatrix.rows.map((row) => (
              <tr key={row.key}>
                <th
                  className="sticky left-0 bg-white text-xs font-semibold text-academic-text px-3 py-2 border border-gray-200 text-left hover:bg-primary-50 cursor-pointer"
                  onClick={() => handleRowToggle(row.key)}
                >
                  {row.label}
                </th>
                {influenceMatrix.columns.map((column) => {
                  const cell = cellMap.get(`${row.key}::${column.key}`);
                  const value = cell?.count ?? 0;
                  return (
                    <td key={`${row.key}-${column.key}`} className="border border-gray-200 px-2 py-2 text-center">
                      <div
                        className="mx-auto rounded transition-transform hover:scale-[1.02]"
                        style={{
                          width: '100%',
                          height: '100%',
                          minHeight: '28px',
                          backgroundColor: getCellColor(value, maxValue),
                        }}
                      >
                        <div className="text-xs text-academic-text font-medium leading-6">{value}</div>
                      </div>
                      {cell && cell.sampleEdges && cell.sampleEdges.length > 0 && (
                        <div className="text-[10px] text-academic-muted mt-1 truncate">
                          {cell.sampleEdges.slice(0, 2).join(', ')}
                        </div>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export const InfluenceMatrixPanel = memo(InfluenceMatrixPanelComponent);
export default InfluenceMatrixPanel;
