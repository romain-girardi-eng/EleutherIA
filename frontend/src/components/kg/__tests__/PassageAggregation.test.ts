// frontend/src/components/kg/__tests__/PassageAggregation.test.ts
import { describe, it, expect } from 'vitest';
import Graph from 'graphology';
import { aggregatePassages, expandWorkPassages, collapseWorkPassages } from '../PassageAggregation';
import type { KGNodeAttributes, KGEdgeAttributes } from '@/types/sigma';

function makeGraphWithPassages(): Graph<KGNodeAttributes, KGEdgeAttributes> {
  const g = new Graph<KGNodeAttributes, KGEdgeAttributes>();
  g.addNode('work_1', { label: 'De Fato', nodeType: 'work', x: 0, y: 0, size: 8, color: '#C79A31', originalId: 'work_1' });
  g.addNode('p1', { label: 'De Fato 1.1', nodeType: 'passage', x: 1, y: 1, size: 4, color: '#8992A6', originalId: 'p1' });
  g.addNode('p2', { label: 'De Fato 1.2', nodeType: 'passage', x: 2, y: 2, size: 4, color: '#8992A6', originalId: 'p2' });
  g.addNode('p3', { label: 'De Fato 2.1', nodeType: 'passage', x: 3, y: 3, size: 4, color: '#8992A6', originalId: 'p3' });
  g.addNode('person_1', { label: 'Cicero', nodeType: 'person', x: 5, y: 5, size: 11, color: '#6E85E9', originalId: 'person_1' });
  g.addEdgeWithKey('e1', 'work_1', 'p1', { relation: 'contains', category: 'structural', size: 1 });
  g.addEdgeWithKey('e2', 'work_1', 'p2', { relation: 'contains', category: 'structural', size: 1 });
  g.addEdgeWithKey('e3', 'work_1', 'p3', { relation: 'contains', category: 'structural', size: 1 });
  g.addEdgeWithKey('e4', 'person_1', 'work_1', { relation: 'wrote', category: 'authorship', size: 1 });
  return g;
}

describe('aggregatePassages', () => {
  it('hides passage nodes and updates work badge count', () => {
    const graph = makeGraphWithPassages();
    const hidden = aggregatePassages(graph);
    expect(hidden.size).toBe(3);
    expect(graph.getNodeAttribute('work_1', 'passageCount')).toBe(3);
    expect(graph.getNodeAttribute('work_1', 'isAggregate')).toBe(true);
  });

  it('does not hide non-passage nodes', () => {
    const graph = makeGraphWithPassages();
    const hidden = aggregatePassages(graph);
    expect(hidden.has('person_1')).toBe(false);
    expect(hidden.has('work_1')).toBe(false);
  });
});

describe('expandWorkPassages', () => {
  it('restores hidden passages for a specific work', () => {
    const graph = makeGraphWithPassages();
    const hidden = aggregatePassages(graph);
    expect(hidden.has('p1')).toBe(true);
    const restored = expandWorkPassages(graph, 'work_1', hidden);
    expect(restored).toEqual(['p1', 'p2', 'p3']);
    expect(hidden.has('p1')).toBe(false);
    expect(graph.getNodeAttribute('work_1', 'passagesExpanded')).toBe(true);
  });
});

describe('collapseWorkPassages', () => {
  it('re-hides passages for a specific work', () => {
    const graph = makeGraphWithPassages();
    const hidden = aggregatePassages(graph);
    expandWorkPassages(graph, 'work_1', hidden);
    collapseWorkPassages(graph, 'work_1', hidden);
    expect(hidden.has('p1')).toBe(true);
    expect(hidden.has('p2')).toBe(true);
    expect(hidden.has('p3')).toBe(true);
    expect(graph.getNodeAttribute('work_1', 'passagesExpanded')).toBe(false);
  });
});
