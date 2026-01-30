import { memo, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import AccordionPanel from '../mobile/AccordionPanel';
import { BarChart3 } from 'lucide-react';

interface WorkspaceHeaderProps {
  totalNodes: number;
  totalEdges: number;
  byType: Record<string, number>;
}

function WorkspaceHeaderComponent({ totalNodes, totalEdges, byType }: WorkspaceHeaderProps) {
  const { t } = useTranslation();

  const getTypeLabel = (type: string): string => {
    const labels: Record<string, string> = {
      person: t('workspace.types.persons'),
      work: t('workspace.types.works'),
      concept: t('workspace.types.concepts'),
      argument: t('workspace.types.arguments'),
      debate: t('workspace.types.debates'),
      reformulation: t('workspace.types.reformulations'),
      quote: t('workspace.types.quotes'),
    };
    return labels[type] || type;
  };

  const typeEntries = useMemo(() => {
    return Object.entries(byType || {})
      .filter(([, count]) => count > 0)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 6);
  }, [byType]);

  const totalItems = totalNodes + totalEdges;

  return (
    <AccordionPanel
      title={t('workspace.title')}
      icon={<BarChart3 className="w-5 h-5" />}
      badge={t('workspace.itemsCount', { count: totalItems })}
      defaultExpanded={true}
    >
      <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-6">
        <div>
          <p className="text-academic-muted max-w-2xl">
            {t('workspace.description')}
          </p>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
          <StatCard label={t('workspace.nodes')} value={totalNodes} />
          <StatCard label={t('workspace.edges')} value={totalEdges} />
          {typeEntries.map(([type, count]) => (
            <StatCard key={type} label={getTypeLabel(type)} value={count} subtle />
          ))}
        </div>
      </div>
    </AccordionPanel>
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
