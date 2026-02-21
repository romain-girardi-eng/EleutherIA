/**
 * Tests for Citation Normalizer Service
 */

import { describe, it, expect } from 'vitest';
import {
  normalizeReferenceLabels,
  normalizeAuthorWorkForms,
  normalizeGreekLatinPunctuation,
  downtoneOverclaiming,
  normalizeClaim,
  normalizePartialClaims,
} from '../src/services/citation-normalizer';
import { ClaimUnit, SourceCitationLike } from '../src/types';

function makeSource(id: number, nodeId: string, author?: string): SourceCitationLike {
  return {
    id,
    nodeId,
    nodeLabel: `Source ${nodeId}`,
    nodeType: 'concept',
    content: '',
    metadata: { author },
  };
}

function makeClaim(text: string, status: ClaimUnit['status'] = 'partial', markers: number[] = []): ClaimUnit {
  return {
    claimId: 'test',
    text,
    sourceNodeIds: [],
    citationMarkers: markers,
    claimType: 'interpretive',
    status,
  };
}

describe('normalizeReferenceLabels', () => {
  it('should expand De Orat. to De Oratione', () => {
    expect(normalizeReferenceLabels('In De Orat. 6, Origen argues...'))
      .toBe('In De Oratione 6, Origen argues...');
  });

  it('should expand Eth. Nic. to Nicomachean Ethics', () => {
    expect(normalizeReferenceLabels('Aristotle, Eth. Nic. III'))
      .toBe('Aristotle, Nicomachean Ethics III');
  });

  it('should leave text without abbreviations unchanged', () => {
    const text = 'Chrysippus argues for compatibilism.';
    expect(normalizeReferenceLabels(text)).toBe(text);
  });

  it('should handle multiple expansions', () => {
    const result = normalizeReferenceLabels('See De An. and Eth. Nic. for details.');
    expect(result).toContain('De Anima');
    expect(result).toContain('Nicomachean Ethics');
  });
});

describe('normalizeAuthorWorkForms', () => {
  it('should normalize Aristoteles to Aristotle', () => {
    const sources = [makeSource(1, 'a', 'Aristotle')];
    expect(normalizeAuthorWorkForms('Aristoteles argues...', sources))
      .toBe('Aristotle argues...');
  });

  it('should normalize Chrysippos to Chrysippus', () => {
    const sources = [makeSource(1, 'a', 'Chrysippus')];
    expect(normalizeAuthorWorkForms('Chrysippos held that...', sources))
      .toBe('Chrysippus held that...');
  });

  it('should leave canonical forms unchanged', () => {
    const sources = [makeSource(1, 'a', 'Plato')];
    const text = 'Plato argues in the Republic.';
    expect(normalizeAuthorWorkForms(text, sources)).toBe(text);
  });
});

describe('normalizeGreekLatinPunctuation', () => {
  it('should normalize smart quotes', () => {
    expect(normalizeGreekLatinPunctuation('\u201CHello\u201D'))
      .toBe('"Hello"');
  });

  it('should normalize em-dash to en-dash', () => {
    expect(normalizeGreekLatinPunctuation('Stoics\u2014Epicureans'))
      .toBe('Stoics\u2013Epicureans');
  });

  it('should normalize multiple spaces', () => {
    expect(normalizeGreekLatinPunctuation('too  many   spaces'))
      .toBe('too many spaces');
  });

  it('should normalize ano teleia spacing', () => {
    expect(normalizeGreekLatinPunctuation('word·next'))
      .toBe('word· next');
  });
});

describe('downtoneOverclaiming', () => {
  it('should replace "proves" with "argues"', () => {
    expect(downtoneOverclaiming('Chrysippus proves that fate exists.'))
      .toBe('Chrysippus argues that fate exists.');
  });

  it('should replace "certainly" with "likely"', () => {
    expect(downtoneOverclaiming('This certainly shows...'))
      .toBe('This likely shows...');
  });

  it('should replace "without doubt"', () => {
    expect(downtoneOverclaiming('Without doubt, the Stoics...'))
      .toBe('plausibly, the Stoics...');
  });

  it('should leave modest language unchanged', () => {
    const text = 'The evidence suggests a possible connection.';
    expect(downtoneOverclaiming(text)).toBe(text);
  });
});

describe('normalizeClaim', () => {
  it('should apply all transforms', () => {
    const sources = [makeSource(1, 'a', 'Chrysippus')];
    const claim = makeClaim('Chrysippos proves  in De Orat. that fate exists [1].', 'partial', [1]);
    const result = normalizeClaim(claim, sources);
    expect(result.text).toContain('Chrysippus');
    expect(result.text).toContain('argues');
    expect(result.text).toContain('De Oratione');
    expect(result.text).not.toContain('  ');
  });

  it('should not introduce new citation markers', () => {
    const sources = [makeSource(1, 'a')];
    const claim = makeClaim('Claim [1].', 'partial', [1]);
    const result = normalizeClaim(claim, sources);
    // Should still only have [1]
    const markers = result.text.match(/\[\d+\]/g) || [];
    expect(markers).toEqual(['[1]']);
  });
});

describe('normalizePartialClaims', () => {
  it('should only normalize partial claims', () => {
    const sources = [makeSource(1, 'a', 'Chrysippus')];
    const claims = [
      makeClaim('Chrysippos proves [1].', 'partial', [1]),
      makeClaim('Supported claim [1].', 'supported', [1]),
      makeClaim('Unsupported claim.', 'unsupported'),
    ];
    const result = normalizePartialClaims(claims, sources);
    // Partial claim should be normalized
    expect(result[0].text).toContain('Chrysippus');
    expect(result[0].text).toContain('argues');
    // Supported claim unchanged
    expect(result[1].text).toBe('Supported claim [1].');
    // Unsupported claim unchanged
    expect(result[2].text).toBe('Unsupported claim.');
  });
});
