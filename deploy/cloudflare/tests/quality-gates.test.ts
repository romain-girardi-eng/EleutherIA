/**
 * Tests for Quality Gates Service
 */

import { describe, it, expect } from 'vitest';
import {
  computeUnsupportedRatio,
  hasFabricatedQuotes,
  shouldFallbackInsufficientEvidence,
  evaluateQualityGates,
  buildInsufficientEvidenceAnswer,
} from '../src/services/quality-gates';
import { ClaimVerificationSummary, ClaimUnit } from '../src/types';

describe('computeUnsupportedRatio', () => {
  it('should compute correct ratio', () => {
    const summary: ClaimVerificationSummary = {
      total: 10, supported: 7, partial: 1, unsupported: 2,
    };
    expect(computeUnsupportedRatio(summary)).toBeCloseTo(0.2);
  });

  it('should return 0 for zero total', () => {
    const summary: ClaimVerificationSummary = {
      total: 0, supported: 0, partial: 0, unsupported: 0,
    };
    expect(computeUnsupportedRatio(summary)).toBe(0);
  });

  it('should return 1.0 when all unsupported', () => {
    const summary: ClaimVerificationSummary = {
      total: 5, supported: 0, partial: 0, unsupported: 5,
    };
    expect(computeUnsupportedRatio(summary)).toBe(1.0);
  });
});

describe('hasFabricatedQuotes', () => {
  it('should detect Greek text not in sources', () => {
    const answer = 'As Chrysippus says, "τὸ ἐφ᾽ ἡμῖν ἐστιν ἡ αἵρεσις" (what is in our power is choice) [1].';
    const sources = ['Chrysippus discusses fate and determinism.'];
    expect(hasFabricatedQuotes(answer, sources)).toBe(true);
  });

  it('should not flag quoted text that appears in sources', () => {
    const answer = 'The text states "τὸ ἐφ᾽ ἡμῖν" (what is in our power) [1].';
    const sources = ['τὸ ἐφ᾽ ἡμῖν is a key Stoic concept discussed by Chrysippus.'];
    expect(hasFabricatedQuotes(answer, sources)).toBe(false);
  });

  it('should not flag English-only text', () => {
    const answer = 'He says "fate is real" according to Chrysippus [1].';
    const sources = ['Chrysippus on fate.'];
    // No Greek in the quote, so not a fabricated Greek quote
    expect(hasFabricatedQuotes(answer, sources)).toBe(false);
  });

  it('should not flag very short fragments', () => {
    const answer = 'The term "τό" appears frequently [1].';
    const sources = ['Some content.'];
    // Fragment is too short (<5 chars)
    expect(hasFabricatedQuotes(answer, sources)).toBe(false);
  });
});

describe('shouldFallbackInsufficientEvidence', () => {
  it('should trigger on fabricated quotes', () => {
    const summary: ClaimVerificationSummary = {
      total: 10, supported: 10, partial: 0, unsupported: 0,
    };
    expect(shouldFallbackInsufficientEvidence(summary, true, false)).toBe(true);
  });

  it('should trigger on out-of-range citations', () => {
    const summary: ClaimVerificationSummary = {
      total: 10, supported: 10, partial: 0, unsupported: 0,
    };
    expect(shouldFallbackInsufficientEvidence(summary, false, true)).toBe(true);
  });

  it('should trigger when unsupported ratio exceeds threshold', () => {
    const summary: ClaimVerificationSummary = {
      total: 10, supported: 5, partial: 2, unsupported: 3,
    };
    // 3/10 = 0.30 > 0.20 threshold
    expect(shouldFallbackInsufficientEvidence(summary, false, false)).toBe(true);
  });

  it('should not trigger when everything is good', () => {
    const summary: ClaimVerificationSummary = {
      total: 10, supported: 8, partial: 1, unsupported: 1,
    };
    // 1/10 = 0.10 < 0.20 threshold
    expect(shouldFallbackInsufficientEvidence(summary, false, false)).toBe(false);
  });
});

describe('evaluateQualityGates', () => {
  it('should return comprehensive gate results', () => {
    const summary: ClaimVerificationSummary = {
      total: 10, supported: 7, partial: 2, unsupported: 1,
    };
    const result = evaluateQualityGates(summary, 'Test answer.', ['source content'], false);
    expect(result.unsupportedRatio).toBeCloseTo(0.1);
    expect(result.fabricatedQuoteDetected).toBe(false);
    expect(result.outOfRangeCitations).toBe(false);
    expect(result.insufficientEvidenceTriggered).toBe(false);
  });

  it('should trigger insufficiency on high unsupported ratio', () => {
    const summary: ClaimVerificationSummary = {
      total: 5, supported: 1, partial: 1, unsupported: 3,
    };
    const result = evaluateQualityGates(summary, 'Test.', [], false);
    expect(result.insufficientEvidenceTriggered).toBe(true);
    expect(result.unsupportedRatio).toBeCloseTo(0.6);
  });
});

describe('buildInsufficientEvidenceAnswer', () => {
  it('should produce a structured fallback answer', () => {
    const claims: ClaimUnit[] = [{
      claimId: 'c1',
      text: 'A verified claim [1].',
      sourceNodeIds: ['a'],
      citationMarkers: [1],
      claimType: 'interpretive',
    }];
    const result = buildInsufficientEvidenceAnswer('What is X?', claims, 5);
    expect(result).toContain('Insufficient Evidence');
    expect(result).toContain('What is X?');
    expect(result).toContain('A verified claim');
    expect(result).toContain('Limitations');
  });

  it('should handle no supported claims', () => {
    const result = buildInsufficientEvidenceAnswer('What is Y?', [], 3);
    expect(result).toContain('Insufficient Evidence');
    expect(result).not.toContain('What We Can Confirm');
  });
});
