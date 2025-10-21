import { useMemo, useState } from 'react';
import type { FormEvent } from 'react';
import { Route } from 'lucide-react';
import { useKGWorkspace } from '../../context/KGWorkspaceContext';
import type { KGPathResponse } from '../../types';

interface CatalogEntry {
  id: string;
  label: string;
  type?: string;
}

function useNodeCatalog(): CatalogEntry[] {
  const {
    state: { timeline, argumentEvidence, conceptClusters },
  } = useKGWorkspace();

  return useMemo(() => {
    const catalog = new Map<string, CatalogEntry>();

    timeline?.periods.forEach((period) => {
      period.nodes.forEach((node) => {
        if (!catalog.has(node.id)) {
          catalog.set(node.id, { id: node.id, label: node.label || '', type: node.type });
        }
      });
    });

    argumentEvidence?.arguments.forEach((argument) => {
      if (!catalog.has(argument.id)) {
        catalog.set(argument.id, { id: argument.id, label: argument.label, type: 'argument' });
      }
    });

    argumentEvidence?.nodes.forEach((node) => {
      if (!catalog.has(node.id)) {
        catalog.set(node.id, { id: node.id, label: node.label || '', type: node.group });
      }
    });

    conceptClusters?.clusters.forEach((cluster) => {
      cluster.nodes.forEach((node) => {
        if (!catalog.has(node.id)) {
          catalog.set(node.id, { id: node.id, label: node.label || '', type: node.type });
        }
      });
    });

    return Array.from(catalog.values()).sort((a, b) => a.label.localeCompare(b.label));
  }, [timeline, argumentEvidence, conceptClusters]);
}

export default function PathInspectorPanel() {
  const { computePath, updateSelection } = useKGWorkspace();
  const catalog = useNodeCatalog();
  const [sourceId, setSourceId] = useState('');
  const [targetId, setTargetId] = useState('');
  const [result, setResult] = useState<KGPathResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const lookupId = (input: string) => {
    if (!input) return input;
    const found = catalog.find((entry) => entry.id === input || entry.label === input);
    return found ? found.id : input;
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    const resolvedSource = lookupId(sourceId.trim());
    const resolvedTarget = lookupId(targetId.trim());

    if (!resolvedSource || !resolvedTarget) {
      setError('Please choose both source and target nodes.');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await computePath({
        sourceId: resolvedSource,
        targetId: resolvedTarget,
        maxDepth: 6,
        allowBidirectional: true,
      });
      setResult(response);
      if (response.nodes && response.nodes.length > 0) {
        updateSelection({
          nodes: response.nodes.map((node) => node.id),
          focusNodeId: response.nodes[0]?.id ?? null,
        });
      }
    } catch (err: any) {
      console.error('Failed to compute path', err);
      setError(err?.message || 'Failed to compute path');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="academic-card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2 text-sm font-semibold text-academic-text uppercase">
          <Route className="w-4 h-4 text-primary-600" />
          Path Inspector
        </div>
        <div className="text-xs text-academic-muted">Resolve narrative walks between any two entities</div>
      </div>

      <form onSubmit={handleSubmit} className="grid gap-3 md:grid-cols-2">
        <div>
          <label className="block text-xs font-semibold text-academic-muted uppercase mb-1">Source</label>
          <input
            list="kg-node-catalog"
            value={sourceId}
            onChange={(event) => setSourceId(event.target.value)}
            className="w-full px-3 py-2 border border-gray-200 rounded-md text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none"
            placeholder="Start typing a node label or ID…"
          />
        </div>
        <div>
          <label className="block text-xs font-semibold text-academic-muted uppercase mb-1">Target</label>
          <input
            list="kg-node-catalog"
            value={targetId}
            onChange={(event) => setTargetId(event.target.value)}
            className="w-full px-3 py-2 border border-gray-200 rounded-md text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none"
            placeholder="Start typing a node label or ID…"
          />
        </div>
        <datalist id="kg-node-catalog">
          {catalog.map((entry) => (
            <option key={entry.id} value={entry.id}>
              {entry.label}
            </option>
          ))}
        </datalist>
        <div className="md:col-span-2 flex items-center gap-3">
          <button
            type="submit"
            disabled={loading || !sourceId || !targetId}
            className="academic-button"
          >
            {loading ? 'Tracing…' : 'Find Path'}
          </button>
          {error && <div className="text-sm text-red-500">{error}</div>}
          {result?.warnings && (
            <div className="text-xs text-amber-600">
              {result.warnings.map((warning, index) => (
                <div key={index}>{warning}</div>
              ))}
            </div>
          )}
        </div>
      </form>

      {result && result.length > 0 && (
        <div className="mt-4 border border-gray-200 rounded-lg divide-y divide-gray-200">
          {result.nodes.map((node, index) => (
            <div key={node.id} className="p-3 bg-white">
              <div className="flex items-center justify-between text-sm">
                <div className="font-semibold text-academic-text">
                  {index + 1}. {node.label}
                </div>
                <div className="text-xs text-academic-muted">
                  {node.type}
                  {node.period ? ` • ${node.period}` : ''}
                </div>
              </div>
              {node.description && <div className="text-xs text-academic-muted mt-1">{node.description}</div>}
              {result.edges[index] && (
                <div className="mt-2 text-xs text-primary-700">
                  ↳ {formatRelation(result.edges[index].relation)} → {result.edges[index].target}
                </div>
              )}
            </div>
          ))}
          {result.summary && (
            <div className="p-3 bg-primary-50 text-xs text-primary-700 font-medium">{result.summary}</div>
          )}
        </div>
      )}
    </div>
  );
}

function formatRelation(relation?: string | null) {
  if (!relation) return 'related_to';
  return relation.replace(/_/g, ' ').toLowerCase();
}
