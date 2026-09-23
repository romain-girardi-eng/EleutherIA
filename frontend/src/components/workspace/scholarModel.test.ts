import { describe, expect, it } from 'vitest';

import type { AtlasEdgeMeta, AtlasNodeMeta } from '../cosmograph/AtlasHelpers';
import {
  buildAdjacency,
  buildInfluenceMatrix,
  buildSearchIndex,
  cellKey,
  computeFacetCounts,
  findShortestPath,
  foldText,
  nextSort,
  searchRows,
  sharedNeighbours,
  sortRows,
} from './scholarModel';

function node(partial: Partial<AtlasNodeMeta> & { id: string }): AtlasNodeMeta {
  return {
    label: partial.id,
    type: 'person',
    typeKey: 'person',
    typeLabel: 'Person',
    layer: 'ancient',
    periodLabel: 'Unspecified',
    schoolLabel: 'Unattached',
    degree: 0,
    importance: 0,
    color: '#000',
    opacity: 1,
    size: 1,
    description: '',
    greekTerm: '',
    latinTerm: '',
    ...partial,
  };
}

function edge(source: string, target: string, relation = 'influenced'): AtlasEdgeMeta {
  return {
    id: `${source}-${target}-${relation}`,
    source,
    target,
    relation,
    relationLabel: relation,
    category: 'doctrinal',
    width: 1,
    opacity: 1,
    color: '#000',
  };
}

const META = [
  node({ id: 'chrysippus', label: 'Chrysippus', periodLabel: 'Hellenistic Greek', schoolLabel: 'Stoics', degree: 40, importance: 40 }),
  node({ id: 'epicurus', label: 'Epicurus', periodLabel: 'Hellenistic Greek', schoolLabel: 'Epicureans', degree: 30, importance: 30 }),
  node({ id: 'autexousion', label: 'Self-determination', typeKey: 'concept', typeLabel: 'Concept', greekTerm: 'αὐτεξούσιον', degree: 12, importance: 12 }),
  node({ id: 'frede', label: 'Michael Frede', layer: 'modern', periodLabel: 'Modern', degree: 5, importance: 5 }),
];

describe('scholar search', () => {
  it('matches polytonic Greek from an unaccented query', () => {
    expect(foldText('αὐτεξούσιος')).toBe('αυτεξουσιοσ');
    const hits = searchRows(buildSearchIndex(META), 'αυτεξουσιον');
    expect(hits.map((hit) => hit.row.node.id)).toEqual(['autexousion']);
  });

  it('ranks a label prefix above a mere haystack hit and requires every token', () => {
    const index = buildSearchIndex(META);
    expect(searchRows(index, 'hellenistic stoics').map((hit) => hit.row.node.id)).toEqual(['chrysippus']);
    const ranked = sortRows(searchRows(index, 'epi'), { key: 'relevance', direction: 'desc' });
    expect(ranked[0]?.id).toBe('epicurus');
  });

  it('counts each facet against the other active facets only', () => {
    const rows = searchRows(buildSearchIndex(META), '');
    const counts = computeFacetCounts(rows, { periods: ['Hellenistic Greek'], types: [], schools: ['Stoics'] });
    // Period counts ignore the period filter but honour the school filter.
    expect(counts.periods.get('Hellenistic Greek')).toBe(1);
    // School counts ignore the school filter but honour the period filter.
    expect(counts.schools.get('Epicureans')).toBe(1);
    expect(counts.types.get('scholar')).toBeUndefined();
    const all = computeFacetCounts(rows, { periods: [], types: [], schools: [] });
    expect(all.types.get('scholar')).toBe(1);
    expect(all.types.get('person')).toBe(3);
  });

  it('cycles sort direction and sinks unattached schools', () => {
    expect(nextSort({ key: 'relevance', direction: 'desc' }, 'label')).toEqual({ key: 'label', direction: 'asc' });
    expect(nextSort({ key: 'label', direction: 'asc' }, 'label')).toEqual({ key: 'label', direction: 'desc' });
    const rows = searchRows(buildSearchIndex(META), '');
    const desc = sortRows(rows, { key: 'school', direction: 'desc' }).map((entry) => entry.schoolLabel);
    expect(desc.slice(0, 2)).toEqual(['Stoics', 'Epicureans']);
    expect(desc.slice(2)).toEqual(['Unattached', 'Unattached']);
  });
});

describe('scholar graph helpers', () => {
  const edges = [
    edge('chrysippus', 'epicurus', 'critiques'),
    edge('epicurus', 'autexousion'),
    edge('autexousion', 'frede', 'discussed_by'),
    edge('chrysippus', 'autexousion'),
  ];

  it('finds the shortest path and records each edge direction', () => {
    const adjacency = buildAdjacency(edges);
    const path = findShortestPath(adjacency, 'frede', 'chrysippus');
    expect(path?.map((step) => [step.from, step.to, step.forward])).toEqual([
      ['frede', 'autexousion', false],
      ['autexousion', 'chrysippus', false],
    ]);
    expect(findShortestPath(adjacency, 'frede', 'chrysippus', 1)).toBeNull();
  });

  it('lists neighbours shared by at least two compared nodes', () => {
    const shared = sharedNeighbours(buildAdjacency(edges), ['chrysippus', 'epicurus']);
    expect(shared).toEqual([{ id: 'autexousion', memberIds: ['chrysippus', 'epicurus'] }]);
  });

  it('builds a directed school matrix that ignores unattached nodes', () => {
    const matrix = buildInfluenceMatrix(META, edges, 'all');
    expect(matrix.schools.sort()).toEqual(['Epicureans', 'Stoics']);
    expect(matrix.cells.get(cellKey('Stoics', 'Epicureans'))?.count).toBe(1);
    expect(matrix.cells.get(cellKey('Epicureans', 'Stoics'))).toBeUndefined();
    expect(matrix.total).toBe(1);
    expect(buildInfluenceMatrix(META, edges, 'structural').total).toBe(0);
  });
});
