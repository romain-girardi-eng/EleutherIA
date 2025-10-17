import { useState, useEffect } from 'react';
import CytoscapeVisualizer from '../components/CytoscapeVisualizer';
import { apiClient } from '../api/client';
import type { CytoscapeData } from '../types';

export default function KGVisualizerPage() {
  const [data, setData] = useState<CytoscapeData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch cytoscape data and stats in parallel
      const [cytoscapeData, kgStats] = await Promise.all([
        apiClient.getCytoscapeData(),
        apiClient.getKGStats(),
      ]);

      setData(cytoscapeData);
      setStats(kgStats);
    } catch (err: any) {
      console.error('Error loading KG data:', err);
      setError(err.message || 'Failed to load knowledge graph data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="spinner w-16 h-16 mx-auto mb-4"></div>
          <p className="text-academic-muted">Loading knowledge graph...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="academic-card">
        <div className="text-center py-12">
          <div className="text-red-600 text-5xl mb-4">⚠</div>
          <h2 className="text-2xl font-semibold mb-2">Error Loading Data</h2>
          <p className="text-academic-muted mb-4">{error}</p>
          <button onClick={loadData} className="academic-button">
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="academic-card">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-serif font-bold mb-2">Knowledge Graph Visualizer</h1>
            <p className="text-academic-muted">
              Interactive network visualization of ancient philosophical debates
            </p>
          </div>

          {stats && (
            <div className="flex space-x-6 text-center">
              <div>
                <div className="text-2xl font-bold text-primary-600">{stats.total_nodes}</div>
                <div className="text-sm text-academic-muted">Nodes</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-primary-600">{stats.total_edges}</div>
                <div className="text-sm text-academic-muted">Edges</div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Legend */}
      <div className="academic-card">
        <h3 className="font-semibold mb-3">Node Types</h3>
        <div className="flex flex-wrap gap-4">
          <LegendItem color="#0284c7" label="Person" />
          <LegendItem color="#7dd3fc" label="Work" />
          <LegendItem color="#fbbf24" label="Concept" />
          <LegendItem color="#f87171" label="Argument" />
          <LegendItem color="#a78bfa" label="Debate" />
        </div>
      </div>

      {/* Visualizer */}
      <div className="academic-card p-0 overflow-hidden" style={{ height: '600px' }}>
        <CytoscapeVisualizer
          data={data}
          onNodeClick={(nodeId) => console.log('Node clicked:', nodeId)}
          onEdgeClick={(edgeId) => console.log('Edge clicked:', edgeId)}
        />
      </div>

      {/* Instructions */}
      <div className="academic-card bg-blue-50 border-blue-200">
        <h3 className="font-semibold mb-2">How to Use</h3>
        <ul className="text-sm text-academic-text space-y-1 list-disc list-inside">
          <li>Click and drag to pan the graph</li>
          <li>Scroll to zoom in/out</li>
          <li>Click on nodes to see details</li>
          <li>Use the controls in the bottom-right to navigate</li>
        </ul>
      </div>
    </div>
  );
}

function LegendItem({ color, label }: { color: string; label: string }) {
  return (
    <div className="flex items-center space-x-2">
      <div className="w-4 h-4 rounded-full" style={{ backgroundColor: color }}></div>
      <span className="text-sm text-academic-muted">{label}</span>
    </div>
  );
}
