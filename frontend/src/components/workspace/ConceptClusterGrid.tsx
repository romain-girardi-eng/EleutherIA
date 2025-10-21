import { memo } from 'react';
import { useKGWorkspace } from '../../context/KGWorkspaceContext';
import type { ConceptClusterSummary, ConceptClusterNode } from '../../types';
import { Sparkles } from 'lucide-react';

const WIDTH = 220;
const HEIGHT = 160;

function mapCoordinate(value: number, dimension: number) {
  const padding = 16;
  return ((value + 1) / 2) * (dimension - padding * 2) + padding;
}

function ClusterCard({
  cluster,
  onSelectNode,
}: {
  cluster: ConceptClusterSummary;
  onSelectNode: (node: ConceptClusterNode) => void;
}) {
  return (
    <div className="border border-gray-200 rounded-lg p-4 bg-white h-full flex flex-col">
      <div className="flex items-center justify-between mb-3">
        <div>
          <div className="text-xs uppercase text-academic-muted font-semibold">Concept Cluster</div>
          <div className="text-sm font-semibold text-academic-text">
            {cluster.label || `Cluster ${cluster.id.split('_').pop()}`}
          </div>
        </div>
        <div className="text-xs text-academic-muted">{cluster.size} concepts</div>
      </div>
      {cluster.keywords && cluster.keywords.length > 0 && (
        <div className="mb-3 flex flex-wrap gap-1.5">
          {cluster.keywords.map((keyword) => (
            <span
              key={keyword}
              className="text-[10px] uppercase tracking-wide bg-primary-50 text-primary-700 px-2 py-0.5 rounded-full"
            >
              {keyword}
            </span>
          ))}
        </div>
      )}
      <svg width={WIDTH} height={HEIGHT} className="flex-shrink-0">
        <rect x={0} y={0} width={WIDTH} height={HEIGHT} rx={8} ry={8} fill="#f8fafc" />
        {cluster.nodes.map((node) => {
          const cx = mapCoordinate(node.x, WIDTH);
          const cy = mapCoordinate(node.y, HEIGHT);
          return (
            <g key={node.id} transform={`translate(${cx}, ${cy})`}>
              <circle r={8} fill="#3b82f6" opacity={0.15} />
              <circle r={4} fill="#3b82f6" opacity={0.7} />
              <text
                x={0}
                y={-12}
                textAnchor="middle"
                className="text-[10px] fill-slate-600 pointer-events-none select-none"
              >
                {node.label}
              </text>
            </g>
          );
        })}
      </svg>
      <div className="mt-3 grid gap-1 text-xs text-academic-muted">
        {cluster.nodes.slice(0, 3).map((node) => (
          <button
            key={node.id}
            onClick={() => onSelectNode(node)}
            className="text-left truncate hover:text-primary-600 transition-colors"
          >
            {node.label}
            {node.school ? ` • ${node.school}` : ''}
          </button>
        ))}
        {cluster.nodes.length > 3 && (
          <div className="italic text-[11px] text-academic-muted">
            +{cluster.nodes.length - 3} more concepts
          </div>
        )}
      </div>
    </div>
  );
}

function ConceptClusterGridComponent() {
  const {
    state: { conceptClusters, loading },
    updateSelection,
  } = useKGWorkspace();

  if (loading && !conceptClusters) {
    return (
      <div className="academic-card">
        <div className="py-12 text-center text-academic-muted text-sm">Analyzing concept clusters…</div>
      </div>
    );
  }

  if (!conceptClusters || conceptClusters.clusters.length === 0) {
    return (
      <div className="academic-card">
        <div className="py-12 text-center text-academic-muted text-sm">
          No clustered concepts for the current slice.
        </div>
      </div>
    );
  }

  return (
    <div className="academic-card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2 text-sm font-semibold text-academic-text uppercase">
          <Sparkles className="w-4 h-4 text-primary-600" />
          Concept Constellations
        </div>
        <div className="text-xs text-academic-muted">
          {conceptClusters.stats.totalConcepts} concepts in {conceptClusters.stats.clusterCount} thematic clusters
        </div>
      </div>
      <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4">
        {conceptClusters.clusters.map((cluster) => (
          <ClusterCard
            key={cluster.id}
            cluster={cluster}
            onSelectNode={(node) =>
              updateSelection({
                nodes: [node.id],
                focusNodeId: node.id,
              })
            }
          />
        ))}
      </div>
    </div>
  );
}

export const ConceptClusterGrid = memo(ConceptClusterGridComponent);
export default ConceptClusterGrid;
