// frontend/src/services/communityDetection.ts
import louvain from 'graphology-communities-louvain';
import type Graph from 'graphology';
import type { KGNodeAttributes, KGEdgeAttributes } from '@/types/sigma';

export function detectCommunities(
  graph: Graph<KGNodeAttributes, KGEdgeAttributes>,
): Map<number, Set<string>> {
  if (graph.order === 0) return new Map();

  let useLouvain = true;

  if (graph.order <= 1 || graph.size === 0) {
    useLouvain = false;
  }

  if (useLouvain) {
    try {
      louvain.assign(graph, { resolution: 1.0 });
      const communitySet = new Set<number>();
      graph.forEachNode((_nodeId, attrs) => {
        communitySet.add(attrs.community as number);
      });
      if (communitySet.size <= 1 || communitySet.size > graph.order * 0.5) {
        useLouvain = false;
      }
    } catch {
      useLouvain = false;
    }
  }

  if (!useLouvain) {
    const typeIndex = new Map<string, number>();
    let nextId = 0;
    graph.forEachNode((nodeId, attrs) => {
      const t = attrs.nodeType ?? 'default';
      if (!typeIndex.has(t)) typeIndex.set(t, nextId++);
      graph.setNodeAttribute(nodeId, 'community', typeIndex.get(t)!);
    });
  }

  const result = new Map<number, Set<string>>();
  graph.forEachNode((nodeId, attrs) => {
    const c = attrs.community as number;
    if (!result.has(c)) result.set(c, new Set());
    result.get(c)!.add(nodeId);
  });

  return result;
}
