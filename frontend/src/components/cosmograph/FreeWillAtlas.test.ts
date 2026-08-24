import { describe, expect, it } from 'vitest';

import {
  atlasConstellationKey,
  isAtlasFocusReady,
  pickAtlasLandingEdges,
  pickAtlasLandingNodeIds,
  pickAtlasSearchProjectionEdges,
  pickAtlasSearchProjectionNodeIds,
} from './FreeWillAtlas';

describe('curated Atlas landing projection', () => {
  const nodes = [
    { id: 'concept_autexousion', type: 'concept', importance: 100 },
    { id: 'person_kane_robert_1938_2022', type: 'person', importance: 500 },
    ...Array.from({ length: 8 }, (_, index) => ({
      id: `direct_${index}`,
      type: index % 2 === 0 ? 'person' : 'passage',
      importance: index,
    })),
    ...Array.from({ length: 8 }, (_, index) => ({
      id: `second_${index}`,
      type: 'argument',
      importance: 20 - index,
    })),
  ];
  const edges = [
    ...Array.from({ length: 8 }, (_, index) => ({
      source: 'concept_autexousion',
      target: `direct_${index}`,
    })),
    ...Array.from({ length: 8 }, (_, index) => ({
      source: `direct_${index}`,
      target: `second_${index}`,
    })),
  ];

  it('keeps anchors, prioritises the direct ring, and honours the hard cap', () => {
    const selected = pickAtlasLandingNodeIds(nodes, edges, 7);
    expect(selected.size).toBe(7);
    expect(selected.has('concept_autexousion')).toBe(true);
    expect(selected.has('person_kane_robert_1938_2022')).toBe(false);
    expect([...selected].filter((id) => id.startsWith('second_'))).toHaveLength(0);
  });

  it('is deterministic even when the input order changes', () => {
    const forward = [...pickAtlasLandingNodeIds(nodes, edges, 12)].sort();
    const reversed = [...pickAtlasLandingNodeIds([...nodes].reverse(), [...edges].reverse(), 12)].sort();
    expect(reversed).toEqual(forward);
  });

  it('keeps a deterministic, bounded backbone without parallel visual edges', () => {
    const selected = new Set(['a', 'b', 'c', 'd']);
    const anchors = new Set(['a']);
    const candidateEdges = [
      { id: 'weak-parallel', source: 'a', target: 'b', relation: 'mentions' },
      { id: 'strong-parallel', source: 'a', target: 'b', relation: 'interprets' },
      { id: 'bc', source: 'b', target: 'c', relation: 'part_of' },
      { id: 'cd', source: 'c', target: 'd', relation: 'discusses' },
      { id: 'ac', source: 'a', target: 'c', relation: 'cites' },
      { id: 'outside', source: 'a', target: 'outside', relation: 'part_of' },
    ];

    const forward = pickAtlasLandingEdges(selected, candidateEdges, anchors, 4);
    const reverse = pickAtlasLandingEdges(selected, [...candidateEdges].reverse(), anchors, 4);

    expect(forward.map((edge) => edge.id)).toEqual(reverse.map((edge) => edge.id));
    expect(forward).toHaveLength(4);
    expect(forward.some((edge) => edge.id === 'strong-parallel')).toBe(true);
    expect(forward.some((edge) => edge.id === 'weak-parallel')).toBe(false);
    expect(forward.every((edge) => selected.has(edge.source) && selected.has(edge.target))).toBe(true);
  });

  it('assigns the central question and scholarly traditions to stable constellations', () => {
    expect(atlasConstellationKey({ id: 'concept_ancient_free_will_debate_structure' })).toBe('core');
    expect(atlasConstellationKey({ id: 'person_chrysippus_of_soli' })).toBe('stoic');
    expect(atlasConstellationKey({ id: 'concept_clinamen_atomic_swerve' })).toBe('epicurean');
    expect(atlasConstellationKey({ id: 'person_alexander_aphrodisias' })).toBe('peripatetic');
    expect(atlasConstellationKey({ id: 'person_origen_alexandria' })).toBe('christian');
    expect(atlasConstellationKey({ id: 'person_plotinus', periodLabel: 'Late Antiquity' })).toBe('late_antique');
    expect(atlasConstellationKey({ id: 'scholar_bobzien', layer: 'modern' })).toBe('reception');
    expect(atlasConstellationKey({ id: 'person_aristotle' })).toBe('agency');
  });
});

describe('bounded Atlas search projection', () => {
  const nodes = [
    { id: 'target', type: 'publication', importance: 10 },
    { id: 'bridge_2', type: 'argument', importance: 20 },
    { id: 'bridge_1', type: 'concept', importance: 30 },
    { id: 'anchor', type: 'person', importance: 100 },
    { id: 'important_neighbour', type: 'person', importance: 90 },
    { id: 'passage_neighbour', type: 'passage', importance: 500 },
    { id: 'second_ring', type: 'concept', importance: 40 },
    { id: 'outside', type: 'person', importance: 1000 },
  ];
  const edges = [
    { id: 'target-bridge2', source: 'target', target: 'bridge_2', relation: 'advanced_in' },
    { id: 'bridge2-bridge1', source: 'bridge_2', target: 'bridge_1', relation: 'part_of' },
    { id: 'bridge1-anchor', source: 'bridge_1', target: 'anchor', relation: 'interprets' },
    { id: 'target-important', source: 'target', target: 'important_neighbour', relation: 'authored_by' },
    { id: 'target-passage', source: 'target', target: 'passage_neighbour', relation: 'mentions' },
    { id: 'important-second', source: 'important_neighbour', target: 'second_ring', relation: 'discusses' },
    { id: 'outside-loop', source: 'outside', target: 'outside', relation: 'mentions' },
  ];

  it('keeps the result, shortest anchor path, and important neighbours inside the budget', () => {
    const projection = pickAtlasSearchProjectionNodeIds(
      'target',
      nodes,
      edges,
      new Set(['anchor']),
      6,
    );

    expect(projection.anchorId).toBe('anchor');
    expect(projection.anchorPath).toEqual(['target', 'bridge_2', 'bridge_1', 'anchor']);
    expect(projection.nodeIds.size).toBeLessThanOrEqual(6);
    expect(projection.nodeIds.has('target')).toBe(true);
    expect(projection.nodeIds.has('important_neighbour')).toBe(true);
    expect(projection.nodeIds.has('outside')).toBe(false);
  });

  it('is byte-order deterministic and retains one visible edge for every route hop', () => {
    const forward = pickAtlasSearchProjectionNodeIds(
      'target', nodes, edges, new Set(['anchor']), 6,
    );
    const reverse = pickAtlasSearchProjectionNodeIds(
      'target', [...nodes].reverse(), [...edges].reverse(), new Set(['anchor']), 6,
    );
    expect([...reverse.nodeIds].sort()).toEqual([...forward.nodeIds].sort());
    expect(reverse.anchorPath).toEqual(forward.anchorPath);

    const visible = pickAtlasSearchProjectionEdges(forward, [
      ...edges,
      { id: 'weak-route-parallel', source: 'bridge_1', target: 'anchor', relation: 'mentions' },
    ]);
    const visiblePairs = new Set(visible.map((edge) =>
      [edge.source, edge.target].sort().join('|')));
    expect(visiblePairs.has('bridge_2|target')).toBe(true);
    expect(visiblePairs.has('bridge_1|bridge_2')).toBe(true);
    expect(visiblePairs.has('anchor|bridge_1')).toBe(true);
    expect(visible.some((edge) => edge.id === 'weak-route-parallel')).toBe(false);
  });

  it('keeps an unanchored component local instead of expanding the complete graph', () => {
    const projection = pickAtlasSearchProjectionNodeIds(
      'important_neighbour',
      nodes,
      edges.filter((edge) => !edge.id.startsWith('target-bridge') && !edge.id.startsWith('bridge')),
      new Set(['anchor']),
      4,
    );
    expect(projection.anchorId).toBeNull();
    expect(projection.anchorPath).toEqual(['important_neighbour']);
    expect(projection.nodeIds.size).toBeLessThanOrEqual(4);
  });

  it('does not commit camera ownership until semantic ID and renderer index agree', () => {
    const active = new Set(['target']);
    expect(isAtlasFocusReady('target', active, undefined)).toBe(false);
    expect(isAtlasFocusReady('outside', active, 0)).toBe(false);
    expect(isAtlasFocusReady('target', active, -1)).toBe(false);
    expect(isAtlasFocusReady('target', active, 0)).toBe(true);
  });
});
