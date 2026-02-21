/**
 * Tests for Citation Integrity Service
 */

import { describe, it, expect } from 'vitest';
import {
  extractCitationMarkers,
  validateCitationRange,
  findOrphanSources,
  renumberCitations,
  assertCitationIntegrity,
  stripOutOfRangeMarkers,
} from '../src/services/citation-integrity';
import { SourceCitationLike } from '../src/types';

function makeSource(id: number, nodeId: string): SourceCitationLike {
  return {
    id,
    nodeId,
    nodeLabel: `Source ${nodeId}`,
    nodeType: 'concept',
    content: `Description of ${nodeId}`,
    metadata: {},
  };
}

describe('extractCitationMarkers', () => {
  it('should extract all unique markers', () => {
    const markers = extractCitationMarkers('Chrysippus argues [1] that fate [2] is compatible [1] with moral responsibility [3].');
    expect(markers).toEqual([1, 2, 3]);
  });

  it('should return empty array for no markers', () => {
    expect(extractCitationMarkers('No citations here.')).toEqual([]);
  });

  it('should handle large marker numbers', () => {
    const markers = extractCitationMarkers('Some claim [18] with another [3].');
    expect(markers).toEqual([3, 18]);
  });

  it('should ignore non-numeric brackets', () => {
    // [Source 1] is not a bare [1] marker — only [2] is a citation marker
    expect(extractCitationMarkers('[Source 1] is not [a] citation [2].')).toEqual([2]);
  });

  it('should extract bare numeric markers', () => {
    expect(extractCitationMarkers('Claim [1] and another [2].')).toEqual([1, 2]);
  });
});

describe('validateCitationRange', () => {
  it('should pass when all markers are in range', () => {
    const result = validateCitationRange('Claim [1] and [2] and [3].', 3);
    expect(result.ok).toBe(true);
    expect(result.outOfRange).toEqual([]);
  });

  it('should fail with out-of-range markers', () => {
    const result = validateCitationRange('Claim [1] and [18].', 10);
    expect(result.ok).toBe(false);
    expect(result.outOfRange).toEqual([18]);
  });

  it('should detect marker [0] as out of range', () => {
    const result = validateCitationRange('Claim [0] here.', 5);
    expect(result.ok).toBe(false);
    expect(result.outOfRange).toEqual([0]);
  });

  it('should handle empty answer', () => {
    const result = validateCitationRange('', 5);
    expect(result.ok).toBe(true);
    expect(result.outOfRange).toEqual([]);
  });
});

describe('findOrphanSources', () => {
  it('should find sources not cited in answer', () => {
    const sources = [makeSource(1, 'a'), makeSource(2, 'b'), makeSource(3, 'c')];
    const orphans = findOrphanSources('Only cite [1] and [3].', sources);
    expect(orphans).toEqual(['b']);
  });

  it('should return empty when all sources are cited', () => {
    const sources = [makeSource(1, 'a'), makeSource(2, 'b')];
    const orphans = findOrphanSources('Cite [1] and [2].', sources);
    expect(orphans).toEqual([]);
  });
});

describe('renumberCitations', () => {
  it('should renumber markers based on appearance order', () => {
    const sources = [makeSource(1, 'a'), makeSource(2, 'b'), makeSource(3, 'c')];
    const result = renumberCitations('First [3] then [1].', sources);
    expect(result.answer).toBe('First [1] then [2].');
    expect(result.sources).toHaveLength(2);
    expect(result.sources[0].nodeId).toBe('c');
    expect(result.sources[1].nodeId).toBe('a');
  });

  it('should strip out-of-range markers', () => {
    const sources = [makeSource(1, 'a'), makeSource(2, 'b')];
    const result = renumberCitations('Claim [1] and bogus [18].', sources);
    expect(result.answer).toBe('Claim [1] and bogus.');
    expect(result.sources).toHaveLength(1);
  });

  it('should handle answer with no markers', () => {
    const sources = [makeSource(1, 'a')];
    const result = renumberCitations('No markers here.', sources);
    expect(result.answer).toBe('No markers here.');
    expect(result.sources).toEqual([]);
  });
});

describe('assertCitationIntegrity', () => {
  it('should pass for valid citations', () => {
    const sources = [makeSource(1, 'a'), makeSource(2, 'b')];
    const result = assertCitationIntegrity('Claim [1] and [2].', sources);
    expect(result.passed).toBe(true);
    expect(result.outOfRange).toEqual([]);
  });

  it('should fail for out-of-range citations', () => {
    const sources = [makeSource(1, 'a'), makeSource(2, 'b')];
    const result = assertCitationIntegrity('Claim [1] and [18].', sources);
    expect(result.passed).toBe(false);
    expect(result.outOfRange).toContain(18);
  });

  it('should detect orphan sources', () => {
    const sources = [makeSource(1, 'a'), makeSource(2, 'b'), makeSource(3, 'c')];
    const result = assertCitationIntegrity('Only [1] cited.', sources);
    expect(result.orphanSources).toContain('b');
    expect(result.orphanSources).toContain('c');
  });
});

describe('stripOutOfRangeMarkers', () => {
  it('should remove out-of-range markers', () => {
    const result = stripOutOfRangeMarkers('Claim [1] and [18] here.', 10);
    expect(result).toBe('Claim [1] and here.');
  });

  it('should keep valid markers', () => {
    const result = stripOutOfRangeMarkers('Claim [1] and [2].', 5);
    expect(result).toBe('Claim [1] and [2].');
  });
});

// =============================================================================
// REGRESSION: Out-of-range citation bug (the [18] with 10 sources scenario)
// =============================================================================
describe('Regression: [18] out-of-range with 10 sources', () => {
  it('should detect and fix the [18]-with-10-sources bug', () => {
    const sources = Array.from({ length: 10 }, (_, i) =>
      makeSource(i + 1, `node_${i + 1}`)
    );

    const buggyAnswer = `Origen argues for free will [1] based on his reading of scripture [3].
He develops a theory of rational choice [5] that influenced later thinkers [18].
His concept of autexousion [7] is central to his argument [10].`;

    // Pre-check should fail
    const preCheck = assertCitationIntegrity(buggyAnswer, sources);
    expect(preCheck.passed).toBe(false);
    expect(preCheck.outOfRange).toContain(18);

    // Strip should fix it
    const fixed = stripOutOfRangeMarkers(buggyAnswer, sources.length);
    expect(fixed).not.toContain('[18]');
    expect(fixed).toContain('[1]');
    expect(fixed).toContain('[10]');

    // Renumber should also fix it
    const renumbered = renumberCitations(buggyAnswer, sources);
    expect(renumbered.answer).not.toContain('[18]');
    const finalCheck = assertCitationIntegrity(renumbered.answer, renumbered.sources);
    expect(finalCheck.passed).toBe(true);
  });

  it('should handle multiple out-of-range markers', () => {
    const sources = Array.from({ length: 5 }, (_, i) =>
      makeSource(i + 1, `node_${i + 1}`)
    );

    const answer = 'Claim [1] and [7] and [12] and [3].';
    const result = assertCitationIntegrity(answer, sources);
    expect(result.passed).toBe(false);
    expect(result.outOfRange).toEqual([7, 12]);

    const fixed = stripOutOfRangeMarkers(answer, sources.length);
    expect(fixed).not.toContain('[7]');
    expect(fixed).not.toContain('[12]');
    expect(fixed).toContain('[1]');
    expect(fixed).toContain('[3]');
  });
});
