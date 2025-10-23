import { useContext, useEffect, useMemo, useState } from 'react';
import CytoscapeVisualizerEnhanced from '../components/CytoscapeVisualizerEnhanced';
import { apiClient } from '../api/client';
import type { CytoscapeData, CommunityMeta } from '../types';
import { KGWorkspaceProvider, KGWorkspaceContext } from '../context/KGWorkspaceContext';
import WorkspaceHeader from '../components/workspace/WorkspaceHeader';
import WorkspaceFilterBar from '../components/workspace/WorkspaceFilterBar';
import TimelinePanel from '../components/workspace/TimelinePanel';
import ArgumentEvidenceBoard from '../components/workspace/ArgumentEvidenceBoard';
import ConceptClusterGrid from '../components/workspace/ConceptClusterGrid';
import InfluenceMatrixPanel from '../components/workspace/InfluenceMatrixPanel';
import PathInspectorPanel from '../components/workspace/PathInspectorPanel';
import AdvancedVisualizationDashboard from '../components/visualizations/AdvancedVisualizationDashboard';
import { filterCytoscapeData } from '../utils/cytoscapeFilters';
import { ShineBorder } from '../components/ui/shine-border';

type VisualizerMode = 'observatory' | 'semativerse' | 'advanced';

export default function KGVisualizerPage() {
  const [mode, setMode] = useState<VisualizerMode>('observatory');

  // Only wrap with KGWorkspaceProvider if we're in a mode that needs it
  if (mode === 'semativerse') {
    return <KGVisualizerContent mode={mode} onModeChange={setMode} />;
  }

  return (
    <KGWorkspaceProvider>
      <KGVisualizerContent mode={mode} onModeChange={setMode} />
    </KGWorkspaceProvider>
  );
}

interface KGVisualizerContentProps {
  mode: VisualizerMode;
  onModeChange: (mode: VisualizerMode) => void;
}

function KGVisualizerContent({ mode, onModeChange }: KGVisualizerContentProps) {
  // Try to get workspace context - will be null if not in provider (semativerse mode)
  const workspaceContext = useContext(KGWorkspaceContext);
  const state = workspaceContext?.state;
  const updateSelection = workspaceContext?.updateSelection;
  const [cyData, setCyData] = useState<CytoscapeData | null>(null);
  const [cyLoading, setCyLoading] = useState<boolean>(true);
  const [cyError, setCyError] = useState<string | null>(null);
  const [communityAlgorithm, setCommunityAlgorithm] = useState<string>('auto');
  const [communityMeta, setCommunityMeta] = useState<CommunityMeta | null>(null);

  useEffect(() => {
    let isMounted = true;

    const load = async () => {
      try {
        setCyLoading(true);
        setCyError(null);
        const data = await apiClient.getCytoscapeData({ algorithm: communityAlgorithm });
        if (!isMounted) return;
        setCyData(data);
        setCommunityMeta(data.meta?.community ?? null);
      } catch (err: unknown) {
        console.error('Failed to load Cytoscape data', err);
        if (!isMounted) return;
        const message = err instanceof Error ? err.message : 'Failed to load network visualization';
        setCyError(message);
        setCommunityMeta(null);
      } finally {
        if (isMounted) {
          setCyLoading(false);
        }
      }
    };

    void load();

    return () => {
      isMounted = false;
    };
  }, [communityAlgorithm]);

  const filteredData = useMemo(
    () => filterCytoscapeData(
      cyData,
      state?.filters || { nodeTypes: [], periods: [], schools: [], relations: [], searchTerm: '' },
      state?.selection
    ),
    [cyData, state?.filters, state?.selection],
  );

  const totals = state?.timeline?.totals;
  const typeCounts = totals?.byType || {};

  const availabilityMap = useMemo(() => {
    const map = new Map<string, boolean>();
    communityMeta?.availableAlgorithms.forEach((option) => {
      map.set(option.name.toLowerCase(), option.available);
    });
    return map;
  }, [communityMeta]);

  const algorithmOptions: Array<{ value: string; label: string; description: string; disabled?: boolean }> = [
    {
      value: 'auto',
      label: 'Auto (recommended)',
      description: 'Try Leiden → Louvain → Greedy based on available libraries.',
    },
    {
      value: 'leiden',
      label: 'Leiden algorithm',
      description: 'Well-connected communities, fastest on large graphs (python-igraph + leidenalg).',
      disabled: availabilityMap.get('leiden') === false,
    },
    {
      value: 'louvain',
      label: 'Louvain algorithm',
      description: 'Classic modularity clustering (python-louvain).',
      disabled: availabilityMap.get('louvain') === false,
    },
    {
      value: 'greedy',
      label: 'Greedy modularity',
      description: 'Pure Python fallback using NetworkX.',
      disabled: availabilityMap.get('greedy') === false,
    },
    {
      value: 'none',
      label: 'No community overlay',
      description: 'Disable community detection; color nodes by type.',
    },
  ];

  const selectedAlgorithm = algorithmOptions.find((option) => option.value === communityAlgorithm) ?? algorithmOptions[0];

  return (
    <div className="space-y-6">
      <div className="academic-card">
        <div className="flex items-center justify-between">
          <div>
            <span className="text-xs uppercase text-academic-muted tracking-wide font-semibold">Mode</span>
            <div className="mt-1 flex overflow-hidden border border-gray-200 rounded-md">
              <button
                onClick={() => onModeChange('advanced')}
                className={`px-4 py-2 text-sm font-medium transition-colors ${
                  mode === 'advanced' ? 'bg-primary-600 text-white' : 'bg-white text-academic-text'
                }`}
              >
                Advanced
              </button>
              <button
                onClick={() => onModeChange('observatory')}
                className={`px-4 py-2 text-sm font-medium transition-colors ${
                  mode === 'observatory' ? 'bg-primary-600 text-white' : 'bg-white text-academic-text'
                }`}
              >
                Observatory
              </button>
              <button
                onClick={() => onModeChange('semativerse')}
                className={`px-4 py-2 text-sm font-medium transition-colors ${
                  mode === 'semativerse' ? 'bg-primary-600 text-white' : 'bg-white text-academic-text'
                }`}
              >
                Semativerse
              </button>
            </div>
          </div>
          <div className="text-xs text-academic-muted max-w-sm text-right">
            Advanced mode features sophisticated academic visualizations. Observatory provides traditional analytics.
            Semativerse offers 3D exploration when credentials are provided.
          </div>
        </div>
      </div>

      <div className="academic-card">
        <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-6">
          <div className="flex-1 space-y-3">
            <div>
              <span className="text-xs uppercase text-academic-muted tracking-wide font-semibold">Community Detection</span>
              <div className="mt-2 flex flex-col sm:flex-row sm:items-center gap-3">
                <select
                  value={communityAlgorithm}
                  onChange={(event) => setCommunityAlgorithm(event.target.value)}
                  className="w-full sm:w-64 border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                >
                  {algorithmOptions.map((option) => (
                    <option
                      key={option.value}
                      value={option.value}
                      disabled={Boolean(option.disabled)}
                    >
                      {option.label}
                      {option.disabled ? ' (unavailable)' : ''}
                    </option>
                  ))}
                </select>
                <div className="text-xs text-academic-muted">
                  {cyLoading ? (
                    <span>Updating communities…</span>
                  ) : communityMeta ? (
                    <span>
                      Active:&nbsp;
                      <span className="font-semibold text-academic-text capitalize">
                        {communityMeta.algorithmUsed}
                      </span>
                      {communityMeta.algorithmUsed !== communityMeta.algorithmRequested &&
                        communityMeta.algorithmRequested !== 'auto' &&
                        communityMeta.algorithmRequested !== 'none' && (
                          <span className="text-amber-600">
                            {' '}
                            (fallback from {communityMeta.algorithmRequested})
                          </span>
                        )}
                    </span>
                  ) : (
                    <span>Communities disabled.</span>
                  )}
                </div>
              </div>
              <p className="text-xs text-academic-muted mt-2 leading-relaxed">
                {selectedAlgorithm.description}
              </p>
            </div>

            {communityMeta && (
              <div className="text-xs text-academic-muted bg-gray-50 border border-gray-100 rounded-md p-3 leading-relaxed">
                {communityMeta.algorithmUsed !== 'none' ? (
                  <>
                    <span className="font-semibold text-academic-text capitalize">{communityMeta.algorithmUsed}</span>
                    {typeof communityMeta.quality === 'number' && (
                      <span>
                        {' '}• Modularity {communityMeta.quality.toFixed(4)}
                      </span>
                    )}
                    {communityMeta.communities.length > 0 && (
                      <span>
                        {' '}• {communityMeta.communities.length} communities detected
                      </span>
                    )}
                    . Use the graph controls to toggle between coloring by node type or community palette.
                  </>
                ) : (
                  <span>
                    Community detection is disabled—nodes will retain their type-based colors. Switch algorithms above to explore clustered views.
                  </span>
                )}
              </div>
            )}
          </div>

          <div className="lg:w-72 bg-gray-50 border border-gray-100 rounded-lg p-4 text-xs text-academic-muted space-y-3">
            <div>
              <h4 className="font-semibold text-academic-text mb-2 flex items-center gap-2">
                <span className="text-sm">Algorithm status</span>
              </h4>
              <ul className="space-y-2">
                {(communityMeta?.availableAlgorithms ?? []).map((option) => (
                  <li key={option.name} className="leading-snug">
                    <span
                      className={`inline-flex items-center gap-2 font-medium ${option.available ? 'text-emerald-600' : 'text-gray-500'}`}
                    >
                      <span className="text-base">{option.available ? '●' : '○'}</span>
                      {option.name.charAt(0).toUpperCase() + option.name.slice(1)}
                    </span>
                    <div className="text-[11px] text-gray-500 mt-1">
                      {option.description}
                    </div>
                  </li>
                ))}
                {communityMeta?.availableAlgorithms?.length === 0 && (
                  <li className="text-[11px] text-gray-500">
                    Waiting for availability information…
                  </li>
                )}
              </ul>
            </div>
            <p className="text-[11px] text-gray-500">
              Tip: After switching algorithms, use the graph controls (color palette section) to color nodes by community and surface cohesion patterns instantly.
            </p>
          </div>
        </div>
      </div>

      {mode === 'advanced' ? (
        <AdvancedVisualizationDashboard
          networkData={cyData}
          networkLoading={cyLoading}
          networkError={cyError}
        />
      ) : mode === 'semativerse' ? (
        <>
          <div className="academic-card bg-purple-50 border-purple-200">
            <p className="text-sm text-academic-text">
              <strong>Semativerse</strong> visualization is used with permission from its co-creators{' '}
              <strong>Benjamin Mathias</strong> and <strong>Romain Girardi</strong>. Contact the development team for
              access credentials.
            </p>
          </div>
          <div className="academic-card p-8 flex items-center justify-center">
            <div className="text-center">
              <div className="text-6xl mb-4">🌌</div>
              <h3 className="text-2xl font-semibold mb-2">Semativerse Integration</h3>
              <p className="text-academic-muted max-w-md">
                Use Semativerse for 3D/VR exploration of the Ancient Free Will Database. Authentication is required.
              </p>
            </div>
          </div>
        </>
      ) : (
        <>
          <WorkspaceHeader
            totalNodes={totals?.nodes || 0}
            totalEdges={totals?.edges || 0}
            byType={typeCounts}
          />
          <WorkspaceFilterBar />

          {/* Cytoscape Network View - Moved to Top */}
          <div className="academic-card">
            <h3 className="text-lg font-semibold text-academic-text mb-3">Interactive Network View</h3>
            <p className="text-sm text-academic-muted mb-4">
              The Cytoscape view mirrors the filters and selections across the observatory. Nodes are limited to the
              most connected entities within the current slice to keep the layout legible.
            </p>

            {cyError && (
              <div className="text-sm text-red-500 mb-4">
                {cyError}
              </div>
            )}

            <ShineBorder
              className="w-full p-0 bg-white dark:bg-black min-w-0"
              borderRadius={12}
              borderWidth={2}
              duration={12}
              color={["#769687", "#8baf9f", "#a8c3b7"]}
            >
              <div className="relative rounded-lg h-[600px] overflow-hidden">
                {cyLoading ? (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="text-center">
                      <div className="spinner w-12 h-12 mx-auto mb-2"></div>
                      <div className="text-sm text-academic-muted">Loading network...</div>
                    </div>
                  </div>
                ) : (
                  <CytoscapeVisualizerEnhanced
                    data={filteredData}
                    onNodeClick={(nodeId) =>
                      updateSelection?.({
                        nodes: [nodeId],
                        focusNodeId: nodeId,
                      })
                    }
                    onEdgeClick={() => undefined}
                    selectedNodeIds={state?.selection?.nodes || []}
                    focusNodeId={state?.selection?.focusNodeId}
                  />
                )}
              </div>
            </ShineBorder>
          </div>

          <TimelinePanel />
          <ArgumentEvidenceBoard />
          <div className="grid gap-6 xl:grid-cols-[2fr,1fr]">
            <ConceptClusterGrid />
            <PathInspectorPanel />
          </div>
          <InfluenceMatrixPanel />
        </>
      )}
    </div>
  );
}
