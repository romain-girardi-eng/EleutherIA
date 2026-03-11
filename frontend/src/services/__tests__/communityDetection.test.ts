// frontend/src/services/__tests__/communityDetection.test.ts
import { describe, it, expect } from 'vitest';
import Graph from 'graphology';
import { detectCommunities } from '../communityDetection';
import type { KGNodeAttributes, KGEdgeAttributes } from '@/types/sigma';

function makeTwoClusterGraph(): Graph<KGNodeAttributes, KGEdgeAttributes> {
  const g = new Graph<KGNodeAttributes, KGEdgeAttributes>();
  const attrs = (label: string) => ({ label, nodeType: 'person' as const, x: 0, y: 0, size: 10, color: '#000', originalId: label });
  g.addNode('a', attrs('A'));
  g.addNode('b', attrs('B'));
  g.addNode('c', attrs('C'));
  g.addEdge('a', 'b', { relation: 'influences', category: 'intellectual' as const, size: 1 });
  g.addEdge('b', 'c', { relation: 'influences', category: 'intellectual' as const, size: 1 });
  g.addEdge('a', 'c', { relation: 'influences', category: 'intellectual' as const, size: 1 });
  g.addNode('d', attrs('D'));
  g.addNode('e', attrs('E'));
  g.addNode('f', attrs('F'));
  g.addEdge('d', 'e', { relation: 'influences', category: 'intellectual' as const, size: 1 });
  g.addEdge('e', 'f', { relation: 'influences', category: 'intellectual' as const, size: 1 });
  g.addEdge('d', 'f', { relation: 'influences', category: 'intellectual' as const, size: 1 });
  g.addEdge('c', 'd', { relation: 'responds_to', category: 'argumentative' as const, size: 1 });
  return g;
}

describe('detectCommunities', () => {
  it('assigns community attribute to all nodes', () => {
    const graph = makeTwoClusterGraph();
    const communities = detectCommunities(graph);
    graph.forEachNode((nodeId) => {
      expect(graph.getNodeAttribute(nodeId, 'community')).toBeDefined();
    });
    expect(communities.size).toBeGreaterThanOrEqual(1);
  });

  it('falls back to type-based communities for degenerate results', () => {
    const g = new Graph<KGNodeAttributes, KGEdgeAttributes>();
    g.addNode('a', { label: 'A', nodeType: 'person', x: 0, y: 0, size: 10, color: '#000', originalId: 'a' });
    const communities = detectCommunities(g);
    expect(communities.size).toBe(1);
  });
});
