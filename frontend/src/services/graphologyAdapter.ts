// frontend/src/services/graphologyAdapter.ts
import Graph from 'graphology';
import type { CytoscapeData } from '@/types';
import type { KGNodeAttributes, KGEdgeAttributes } from '@/types/sigma';
import { RELATION_TO_CATEGORY, TYPE_SIZES } from '@/types/sigma';
import { getGraphTypeTheme } from '@/components/graphrag/graphTheme';

/**
 * Convert CytoscapeData from the API into a Graphology graph
 * with typed node/edge attributes ready for Sigma.js rendering.
 */
export function buildGraph(
  cyData: CytoscapeData,
): Graph<KGNodeAttributes, KGEdgeAttributes> {
  const graph = new Graph<KGNodeAttributes, KGEdgeAttributes>();

  const nodes = cyData.elements?.nodes ?? [];
  const edges = cyData.elements?.edges ?? [];

  for (const node of nodes) {
    const { id, label, type, description, period, metadata } = node.data;
    if (!id) continue;

    const nodeType = type ?? 'default';
    const theme = getGraphTypeTheme(nodeType);

    graph.addNode(id, {
      label: label ?? id,
      type: nodeType,
      x: Math.random() * 1000,
      y: Math.random() * 1000,
      size: TYPE_SIZES[nodeType] ?? TYPE_SIZES.default,
      color: theme.color,
      period: period as string | undefined,
      description: description as string | undefined,
      metadata: (metadata as unknown as Record<string, unknown>) ?? undefined,
      originalId: id,
    });
  }

  for (const edge of edges) {
    const { id, source, target, relation, description } = edge.data;
    if (!source || !target) continue;
    if (!graph.hasNode(source) || !graph.hasNode(target)) continue;

    const rel = (relation as string) ?? 'related_to';
    const category = RELATION_TO_CATEGORY[rel] ?? 'structural';

    const edgeKey = id ?? `${source}-${rel}-${target}`;
    if (graph.hasEdge(edgeKey)) continue;

    graph.addEdgeWithKey(edgeKey, source, target, {
      relation: rel,
      category,
      description: description as string | undefined,
      size: 1,
    });
  }

  return graph;
}
