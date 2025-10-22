import { useEffect, useMemo, useState } from 'react';
import CytoscapeVisualizerEnhanced from '../components/CytoscapeVisualizerEnhanced';
import { apiClient } from '../api/client';
import type { CytoscapeData } from '../types';
import { KGWorkspaceProvider, useKGWorkspace } from '../context/KGWorkspaceContext';
import WorkspaceHeader from '../components/workspace/WorkspaceHeader';
import WorkspaceFilterBar from '../components/workspace/WorkspaceFilterBar';
import TimelinePanel from '../components/workspace/TimelinePanel';
import ArgumentEvidenceBoard from '../components/workspace/ArgumentEvidenceBoard';
import ConceptClusterGrid from '../components/workspace/ConceptClusterGrid';
import InfluenceMatrixPanel from '../components/workspace/InfluenceMatrixPanel';
import PathInspectorPanel from '../components/workspace/PathInspectorPanel';
import AdvancedVisualizationDashboard from '../components/visualizations/AdvancedVisualizationDashboard';
import { filterCytoscapeData } from '../utils/cytoscapeFilters';

type VisualizerMode = 'observatory' | 'semativerse' | 'advanced';

export default function KGVisualizerPage() {
  return (
    <KGWorkspaceProvider>
      <KGVisualizerContent />
    </KGWorkspaceProvider>
  );
}

function KGVisualizerContent() {
  const {
    state,
    updateSelection,
  } = useKGWorkspace();
  const [mode, setMode] = useState<VisualizerMode>('advanced');
  const [cyData, setCyData] = useState<CytoscapeData | null>(null);
  const [cyLoading, setCyLoading] = useState<boolean>(true);
  const [cyError, setCyError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        setCyLoading(true);
        const data = await apiClient.getCytoscapeData();
        setCyData(data);
      } catch (err: unknown) {
        console.error('Failed to load Cytoscape data', err);
        const message = err instanceof Error ? err.message : 'Failed to load network visualization';
        setCyError(message);
      } finally {
        setCyLoading(false);
      }
    };
    void load();
  }, []);

  const filteredData = useMemo(
    () => filterCytoscapeData(cyData, state.filters, state.selection),
    [cyData, state.filters, state.selection],
  );

  const totals = state.timeline?.totals;
  const typeCounts = totals?.byType || {};

  return (
    <div className="space-y-6">
      <div className="academic-card">
        <div className="flex items-center justify-between">
          <div>
            <span className="text-xs uppercase text-academic-muted tracking-wide font-semibold">Mode</span>
            <div className="mt-1 flex overflow-hidden border border-gray-200 rounded-md">
              <button
                onClick={() => setMode('advanced')}
                className={`px-4 py-2 text-sm font-medium transition-colors ${
                  mode === 'advanced' ? 'bg-primary-600 text-white' : 'bg-white text-academic-text'
                }`}
              >
                Advanced
              </button>
              <button
                onClick={() => setMode('observatory')}
                className={`px-4 py-2 text-sm font-medium transition-colors ${
                  mode === 'observatory' ? 'bg-primary-600 text-white' : 'bg-white text-academic-text'
                }`}
              >
                Observatory
              </button>
              <button
                onClick={() => setMode('semativerse')}
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
          <TimelinePanel />
          <ArgumentEvidenceBoard />
          <div className="grid gap-6 xl:grid-cols-[2fr,1fr]">
            <ConceptClusterGrid />
            <PathInspectorPanel />
          </div>
          <InfluenceMatrixPanel />
          <div className="academic-card">
            <h3 className="text-lg font-semibold text-academic-text mb-3">Focused Network View</h3>
            <p className="text-sm text-academic-muted mb-4">
              The Cytoscape view mirrors the filters and selections across the observatory. Nodes are limited to the
              most connected entities within the current slice to keep the layout legible.
            </p>

            {cyError && (
              <div className="text-sm text-red-500 mb-4">
                {cyError}
              </div>
            )}

            <div className="relative border border-gray-200 rounded-lg h-[600px] overflow-hidden">
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
                    updateSelection({
                      nodes: [nodeId],
                      focusNodeId: nodeId,
                    })
                  }
                  onEdgeClick={() => undefined}
                  selectedNodeIds={state.selection.nodes}
                  focusNodeId={state.selection.focusNodeId}
                />
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
