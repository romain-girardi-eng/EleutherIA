import { memo, useMemo } from 'react';

interface WorkspaceHeaderProps {
  totalNodes: number;
  totalEdges: number;
  byType: Record<string, number>;
}

const TYPE_LABELS: Record<string, string> = {
  person: 'Persons',
  work: 'Works',
  concept: 'Concepts',
  argument: 'Arguments',
  debate: 'Debates',
  reformulation: 'Reformulations',
  quote: 'Quotes',
};

function WorkspaceHeaderComponent({ totalNodes, totalEdges, byType }: WorkspaceHeaderProps) {
  const typeEntries = useMemo(() => {
    return Object.entries(byType || {})
      .filter(([, count]) => count > 0)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 6);
  }, [byType]);

  return (
    <div className="academic-card">
      <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-6">
        <div>
          <h1 className="text-3xl font-serif font-bold mb-2 text-academic-text">Knowledge Graph Observatory</h1>
          <p className="text-academic-muted max-w-2xl">
            Coordinated views of the Ancient Free Will Database surface the historical arc of arguments,
            trace textual evidence, and reveal reception dynamics without drowning in a force-directed hairball.
          </p>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
          <StatCard label="Nodes" value={totalNodes} />
          <StatCard label="Edges" value={totalEdges} />
          {typeEntries.map(([type, count]) => (
            <StatCard key={type} label={TYPE_LABELS[type] || type} value={count} subtle />
          ))}
        </div>
      </div>
    </div>
  );
}

interface StatCardProps {
  label: string;
  value: number;
  subtle?: boolean;
}

function StatCard({ label, value, subtle = false }: StatCardProps) {
  return (
    <div
      className={`px-4 py-3 rounded-lg border ${
        subtle ? 'border-gray-200 bg-white/70' : 'border-primary-200 bg-primary-50'
      }`}
    >
      <div className="text-xs uppercase tracking-wide text-academic-muted">{label}</div>
      <div className="text-2xl font-semibold text-academic-text">{value.toLocaleString()}</div>
    </div>
  );
}

export const WorkspaceHeader = memo(WorkspaceHeaderComponent);
export default WorkspaceHeader;
