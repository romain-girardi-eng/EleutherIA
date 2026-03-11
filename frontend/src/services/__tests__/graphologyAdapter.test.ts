// frontend/src/services/__tests__/graphologyAdapter.test.ts
import { describe, it, expect } from 'vitest';
import { buildGraph } from '../graphologyAdapter';
import type { CytoscapeData } from '@/types';

const mockCyData: CytoscapeData = {
  elements: {
    nodes: [
      { data: { id: 'person_chrysippus', label: 'Chrysippus', type: 'person' } },
      { data: { id: 'school_stoics', label: 'Stoics', type: 'school' } },
      { data: { id: 'work_de_fato', label: 'De Fato', type: 'work' } },
      { data: { id: 'passage_1', label: 'De Fato 1.1', type: 'passage' } },
      { data: { id: 'passage_2', label: 'De Fato 1.2', type: 'passage' } },
    ],
    edges: [
      { data: { id: 'e1', source: 'person_chrysippus', target: 'school_stoics', relation: 'member_of' } },
      { data: { id: 'e2', source: 'work_de_fato', target: 'passage_1', relation: 'contains' } },
      { data: { id: 'e3', source: 'work_de_fato', target: 'passage_2', relation: 'contains' } },
    ],
  },
};

describe('buildGraph', () => {
  it('converts CytoscapeData to Graphology graph', () => {
    const graph = buildGraph(mockCyData);
    expect(graph.order).toBe(5);
    expect(graph.size).toBe(3);
  });

  it('maps node attributes correctly', () => {
    const graph = buildGraph(mockCyData);
    const attrs = graph.getNodeAttributes('person_chrysippus');
    expect(attrs.label).toBe('Chrysippus');
    expect(attrs.nodeType).toBe('person');
    expect(attrs.size).toBe(11);
    expect(attrs.color).toBe('#6E85E9');
    expect(attrs.originalId).toBe('person_chrysippus');
  });

  it('maps edge category from relation', () => {
    const graph = buildGraph(mockCyData);
    const attrs = graph.getEdgeAttributes('e1');
    expect(attrs.relation).toBe('member_of');
    expect(attrs.category).toBe('affiliation');
  });

  it('defaults unknown relations to structural category', () => {
    const data: CytoscapeData = {
      elements: {
        nodes: [
          { data: { id: 'a', label: 'A', type: 'concept' } },
          { data: { id: 'b', label: 'B', type: 'concept' } },
        ],
        edges: [
          { data: { id: 'e', source: 'a', target: 'b', relation: 'unknown_relation' } },
        ],
      },
    };
    const graph = buildGraph(data);
    expect(graph.getEdgeAttributes('e').category).toBe('structural');
  });
});
