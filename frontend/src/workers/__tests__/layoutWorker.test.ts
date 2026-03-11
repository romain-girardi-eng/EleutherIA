// frontend/src/workers/__tests__/layoutWorker.test.ts
import { describe, it, expect } from 'vitest';
import { computeLayout } from '../layoutWorker';
import Graph from 'graphology';
import type { KGNodeAttributes, KGEdgeAttributes } from '@/types/sigma';

function makeTestGraph(): Graph<KGNodeAttributes, KGEdgeAttributes> {
  const g = new Graph<KGNodeAttributes, KGEdgeAttributes>();
  g.addNode('a', { label: 'A', nodeType: 'person', x: 0, y: 0, size: 10, color: '#000', originalId: 'a' });
  g.addNode('b', { label: 'B', nodeType: 'concept', x: 0, y: 0, size: 8, color: '#000', originalId: 'b' });
  g.addNode('c', { label: 'C', nodeType: 'school', x: 0, y: 0, size: 9, color: '#000', originalId: 'c' });
  g.addEdge('a', 'b', { relation: 'discusses', category: 'semantic', size: 1 });
  g.addEdge('a', 'c', { relation: 'member_of', category: 'affiliation', size: 1 });
  return g;
}

describe('computeLayout', () => {
  it('assigns distinct positions to nodes', () => {
    const graph = makeTestGraph();
    computeLayout(graph, { iterations: 50 });

    const posA = { x: graph.getNodeAttribute('a', 'x'), y: graph.getNodeAttribute('a', 'y') };
    const posB = { x: graph.getNodeAttribute('b', 'x'), y: graph.getNodeAttribute('b', 'y') };

    const dist = Math.sqrt((posA.x - posB.x) ** 2 + (posA.y - posB.y) ** 2);
    expect(dist).toBeGreaterThan(0.1);
  });

  it('does not throw for empty graph', () => {
    const graph = new Graph<KGNodeAttributes, KGEdgeAttributes>();
    expect(() => computeLayout(graph, { iterations: 10 })).not.toThrow();
  });
});
