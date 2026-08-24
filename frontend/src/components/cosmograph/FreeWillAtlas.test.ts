import { describe, expect, it } from 'vitest';

import {
  atlasConstellationKey,
  pickAtlasLandingEdges,
  pickAtlasLandingNodeIds,
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
