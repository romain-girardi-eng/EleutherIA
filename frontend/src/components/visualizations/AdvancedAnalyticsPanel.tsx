import { useMemo } from 'react';
import { Activity, BarChart3, Layers, TrendingUp } from 'lucide-react';
import { useKGWorkspace } from '../../context/KGWorkspaceContext';

export default function AdvancedAnalyticsPanel() {
  const { state } = useKGWorkspace();

  const analytics = useMemo(() => {
    const totalNodes = state.timeline?.totals?.nodes ?? 0;
    const totalEdges = state.timeline?.totals?.edges ?? 0;
    const typeEntries = Object.entries(state.timeline?.totals?.byType ?? {}).sort((a, b) => (b[1] || 0) - (a[1] || 0));
    const maxTypeCount = typeEntries.length > 0 ? typeEntries[0][1] : 0;

    const periodHighlights = (state.timeline?.periods ?? [])
      .map((period) => ({
        key: period.key,
        label: period.label,
        total: Object.values(period.counts ?? {}).reduce((acc, value) => acc + value, 0),
        start: period.startYear,
        end: period.endYear,
      }))
      .sort((a, b) => b.total - a.total)
      .slice(0, 4);

    const argumentStats = state.argumentEvidence?.stats ?? null;
    const conceptStats = state.conceptClusters?.stats ?? null;

    const rowMap = new Map((state.influenceMatrix?.rows ?? []).map((row) => [row.key, row.label]));
    const columnMap = new Map((state.influenceMatrix?.columns ?? []).map((col) => [col.key, col.label]));

    const influenceHighlights = (state.influenceMatrix?.cells ?? [])
      .filter((cell) => cell.count > 0)
      .map((cell) => ({
        id: `${cell.rowKey}-${cell.columnKey}`,
        row: rowMap.get(cell.rowKey) ?? cell.rowKey,
        column: columnMap.get(cell.columnKey) ?? cell.columnKey,
        count: cell.count,
      }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 5);

    return {
      totalNodes,
      totalEdges,
      typeEntries,
      maxTypeCount,
      periodHighlights,
      argumentStats,
      conceptStats,
      influenceHighlights,
    };
  }, [
    state.timeline,
    state.argumentEvidence,
    state.conceptClusters,
    state.influenceMatrix,
  ]);

  const isLoading = !state.timeline || !state.influenceMatrix;

  if (isLoading) {
    return (
      <div className="academic-card">
        <div className="py-16 text-center text-academic-muted text-sm">
          Compiling analytics…
        </div>
      </div>
    );
  }

  return (
    <div className="academic-card space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm font-semibold text-academic-text uppercase">
          <Layers className="w-4 h-4 text-primary-600" />
          Knowledge Graph Analytics
        </div>
        <div className="text-xs text-academic-muted">
          Overview of entity composition, argumentative evidence, and influence flows.
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-lg border border-gray-200 bg-white/80 p-4 shadow-sm">
          <div className="text-xs uppercase tracking-wide text-academic-muted">Entities Mapped</div>
          <div className="mt-2 text-2xl font-semibold text-academic-text">{analytics.totalNodes.toLocaleString()}</div>
          <div className="mt-1 text-[11px] text-academic-muted">
            Unique people, works, concepts, arguments, and institutions represented in the KG.
          </div>
        </div>

        <div className="rounded-lg border border-gray-200 bg-white/80 p-4 shadow-sm">
          <div className="text-xs uppercase tracking-wide text-academic-muted">Documented Relations</div>
          <div className="mt-2 text-2xl font-semibold text-academic-text">{analytics.totalEdges.toLocaleString()}</div>
          <div className="mt-1 text-[11px] text-academic-muted">
            Directed edges encoding influence, reception, and argumentative dependencies.
          </div>
        </div>

        <div className="rounded-lg border border-gray-200 bg-white/80 p-4 shadow-sm">
          <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-academic-muted">
            <Activity className="w-3 h-3 text-primary-600" />
            Argument &amp; Evidence
          </div>
          <div className="mt-2 text-xl font-semibold text-academic-text">
            {(analytics.argumentStats?.totalArguments ?? 0).toLocaleString()} arguments
          </div>
          <div className="mt-1 text-[11px] text-academic-muted">
            {analytics.argumentStats
              ? `${analytics.argumentStats.totalAncientSources.toLocaleString()} ancient sources · ${analytics.argumentStats.totalModernReception.toLocaleString()} modern receptions`
              : 'Awaiting computation'}
          </div>
        </div>

        <div className="rounded-lg border border-gray-200 bg-white/80 p-4 shadow-sm">
          <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-academic-muted">
            <BarChart3 className="w-3 h-3 text-primary-600" />
            Concept Clusters
          </div>
          <div className="mt-2 text-xl font-semibold text-academic-text">
            {(analytics.conceptStats?.clusterCount ?? 0).toLocaleString()} clusters
          </div>
          <div className="mt-1 text-[11px] text-academic-muted">
            {analytics.conceptStats
              ? `${analytics.conceptStats.totalConcepts.toLocaleString()} concepts organised into thematic constellations`
              : 'Concept clustering unavailable for this slice'}
          </div>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-lg border border-gray-200 bg-white/70 p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div className="text-xs uppercase tracking-wide text-academic-muted font-semibold">
              Entity Composition by Type
            </div>
            <div className="text-[11px] text-academic-muted">
              Top {Math.min(analytics.typeEntries.length, 5)} of {analytics.typeEntries.length}
            </div>
          </div>

          <div className="space-y-3">
            {analytics.typeEntries.slice(0, 5).map(([type, count]) => (
              <div key={type}>
                <div className="flex items-center justify-between text-xs text-academic-text">
                  <span className="font-medium capitalize">{type}</span>
                  <span>{count.toLocaleString()}</span>
                </div>
                <div className="mt-1 h-2 w-full rounded-full bg-slate-100">
                  <div
                    className="h-2 rounded-full bg-gradient-to-r from-primary-400 to-primary-600"
                    style={{ width: `${maxTypeWidth(count, analytics.maxTypeCount)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-lg border border-gray-200 bg-white/70 p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div className="text-xs uppercase tracking-wide text-academic-muted font-semibold">
              High-Volume Periods
            </div>
            <div className="text-[11px] text-academic-muted">
              Most densely documented chronological slices
            </div>
          </div>

          <div className="space-y-3">
            {analytics.periodHighlights.map((period) => (
              <div key={period.key} className="flex items-center justify-between">
                <div>
                  <div className="text-xs font-semibold text-academic-text">{period.label}</div>
                  <div className="text-[10px] text-academic-muted">
                    {formatRange(period.start)} → {formatRange(period.end)}
                  </div>
                </div>
                <div className="text-xs text-academic-muted">
                  {period.total.toLocaleString()} entities
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="rounded-lg border border-gray-200 bg-white/70 p-5 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-academic-muted font-semibold">
            <TrendingUp className="w-3 h-3 text-primary-600" />
            Dominant Influence Paths
          </div>
          <div className="text-[11px] text-academic-muted">
            Highest intensity combinations of schools and relation types.
          </div>
        </div>

        {analytics.influenceHighlights.length === 0 ? (
          <div className="text-sm text-academic-muted py-6 text-center">
            Influence matrix data is unavailable for the current slice.
          </div>
        ) : (
          <div className="grid gap-2 md:grid-cols-2">
            {analytics.influenceHighlights.map((entry) => (
              <div key={entry.id} className="rounded-md border border-gray-200 bg-white/80 p-3">
                <div className="text-xs font-semibold text-academic-text">
                  {entry.row}
                </div>
                <div className="text-[11px] text-academic-muted">
                  Relation focus: {entry.column}
                </div>
                <div className="mt-1 text-xs text-primary-600 font-medium">
                  {entry.count.toLocaleString()} mapped edges
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function maxTypeWidth(count: number, max: number) {
  if (max <= 0) {
    return 0;
  }
  const width = (count / max) * 100;
  return Math.max(6, Math.min(width, 100));
}

function formatRange(value?: number | null) {
  if (value === null || value === undefined) {
    return '–';
  }
  if (value < 0) {
    return `${Math.abs(value)} BCE`;
  }
  if (value === 0) {
    return '0';
  }
  return `${value} CE`;
}
