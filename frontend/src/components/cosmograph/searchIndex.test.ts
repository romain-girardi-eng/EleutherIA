import { describe, expect, it } from 'vitest';

import type { AtlasNodeMeta } from './AtlasHelpers';
import { foldText, getSearchIndex, groupHits, matchRange, searchNodes } from './searchIndex';

// Greek strings below are copied verbatim from data/kg/nodes.jsonl.
const ATTESTED_LABEL = 'Diogenes of Oenoanda fragm. XXXIII: no divination, hence no εἱμαρμένη';
const ATTESTED_GREEK_TERM = 'ἀργὸς λόγος';
const ATTESTED_TRANSLIT = 'ἐποχή (epochē)';

const stripMarks = (value: string) => value.normalize('NFD').replace(/\p{M}/gu, '');

function node(partial: Partial<AtlasNodeMeta> & Pick<AtlasNodeMeta, 'id' | 'label'>): AtlasNodeMeta {
  return {
    type: 'concept',
    typeKey: 'concept',
    typeLabel: 'Concept',
    layer: 'ancient',
    periodLabel: 'Unspecified',
    schoolLabel: 'Unattached',
    degree: 1,
    importance: 1,
    color: '#000000',
    opacity: 1,
    size: 3,
    description: '',
    greekTerm: '',
    latinTerm: '',
    ...partial,
  };
}

const NODES: AtlasNodeMeta[] = [
  node({ id: 'augustine', label: 'Augustine of Hippo', type: 'person', typeKey: 'person', degree: 400 }),
  node({ id: 'augustine-passage', label: 'Augustine, De libero arbitrio 3.1', type: 'passage', typeKey: 'passage', degree: 2 }),
  node({ id: 'lazy', label: 'Lazy argument', greekTerm: ATTESTED_GREEK_TERM, degree: 30 }),
  node({ id: 'suspension', label: 'Suspension of judgement', greekTerm: ATTESTED_TRANSLIT, degree: 12 }),
  node({ id: 'diogenes', label: ATTESTED_LABEL, type: 'argument', typeKey: 'argument', degree: 5 }),
  node({ id: 'bobzien', label: 'Susanne Bobzien', type: 'person', typeKey: 'person', layer: 'modern', degree: 80 }),
];

describe('foldText', () => {
  it('drops case, Latin macrons and punctuation', () => {
    expect(foldText('Epochē!')).toBe('epoche');
    expect(foldText('  De  libero-arbitrio ')).toBe('de libero arbitrio');
  });

  it('drops Greek accents and breathings and folds final sigma', () => {
    const folded = foldText(ATTESTED_GREEK_TERM);
    expect(folded).toBe(foldText(stripMarks(ATTESTED_GREEK_TERM)));
    expect(folded).not.toMatch(/\p{M}/u);
    expect(folded).not.toContain('\u03c2');
  });
});

describe('searchNodes', () => {
  const index = getSearchIndex(NODES);

  it('caches one index per node array', () => {
    expect(getSearchIndex(NODES)).toBe(index);
  });

  it('matches Greek terms typed without diacritics', () => {
    const { hits } = searchNodes(index, stripMarks(ATTESTED_GREEK_TERM), { limit: 5 });
    expect(hits[0]?.node.id).toBe('lazy');
  });

  it('matches a transliteration typed without macrons', () => {
    const { hits } = searchNodes(index, 'epoche', { limit: 5 });
    expect(hits.map((hit) => hit.node.id)).toContain('suspension');
  });

  it('matches word prefixes and multi-token queries', () => {
    expect(searchNodes(index, 'hipp', { limit: 5 }).hits[0]?.node.id).toBe('augustine');
    expect(searchNodes(index, 'hippo aug', { limit: 5 }).hits[0]?.node.id).toBe('augustine');
  });

  it('ranks a well-connected person above a passage with the same prefix', () => {
    const ids = searchNodes(index, 'augustine', { limit: 5 }).hits.map((hit) => hit.node.id);
    expect(ids.indexOf('augustine')).toBeLessThan(ids.indexOf('augustine-passage'));
  });

  it('counts matches per group before the cap and can restrict to one group', () => {
    const all = searchNodes(index, 'augustine', { limit: 1 });
    expect(all.hits).toHaveLength(1);
    expect(all.total).toBe(2);
    expect(all.groupTotals.get('passage')).toBe(1);
    const onlyPassages = searchNodes(index, 'augustine', { limit: 5, group: 'passage' });
    expect(onlyPassages.hits.map((hit) => hit.node.id)).toEqual(['augustine-passage']);
  });

  it('treats modern persons as scholars', () => {
    const { hits } = searchNodes(index, 'bobzien', { limit: 5 });
    expect(hits[0]?.group).toBe('scholar');
  });

  it('returns the most connected entries for an empty query', () => {
    const { hits } = searchNodes(index, '  ', { limit: 2 });
    expect(hits[0]?.node.id).toBe('augustine');
    expect(hits).toHaveLength(2);
  });

  it('groups hits contiguously, best group first', () => {
    const { hits } = searchNodes(index, 'augustine', { limit: 5 });
    expect(groupHits(hits).map((bucket) => bucket.group)).toEqual(['person', 'passage']);
  });
});

describe('matchRange', () => {
  it('maps a diacritic-free query back onto the accented label', () => {
    const word = ATTESTED_LABEL.slice(ATTESTED_LABEL.lastIndexOf(' ') + 1);
    const range = matchRange(ATTESTED_LABEL, stripMarks(word));
    expect(range).not.toBeNull();
    const [start, end] = range ?? [0, 0];
    expect(ATTESTED_LABEL.slice(start, end)).toBe(word);
  });

  it('prefers a word-initial occurrence', () => {
    const [start, end] = matchRange('Stoic providence and the Stoics', 'stoics') ?? [0, 0];
    expect('Stoic providence and the Stoics'.slice(start, end)).toBe('Stoics');
  });
});
