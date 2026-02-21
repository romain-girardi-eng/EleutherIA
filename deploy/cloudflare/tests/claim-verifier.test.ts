/**
 * Tests for Claim Verifier Service
 */

import { describe, it, expect } from 'vitest';
import {
  extractClaims,
  attachClaimSources,
  buildVerificationContext,
  classifyClaim,
  summarizeVerification,
} from '../src/services/claim-verifier';
import { SourceCitationLike, ClaimUnit } from '../src/types';

function makeSource(id: number, nodeId: string, content: string = ''): SourceCitationLike {
  return {
    id,
    nodeId,
    nodeLabel: `Source ${nodeId}`,
    nodeType: 'concept',
    content,
    metadata: {},
  };
}

describe('extractClaims', () => {
  it('should split answer into sentence-level claims', () => {
    const answer = 'Chrysippus argues for compatibilism [1]. The Stoics believed in fate [2]. This is significant.';
    const claims = extractClaims(answer);
    expect(claims.length).toBe(3);
  });

  it('should extract citation markers per claim', () => {
    const answer = 'First claim [1] [2]. Second claim [3].';
    const claims = extractClaims(answer);
    const first = claims.find(c => c.text.includes('First'));
    const second = claims.find(c => c.text.includes('Second'));
    expect(first?.citationMarkers).toEqual([1, 2]);
    expect(second?.citationMarkers).toEqual([3]);
  });

  it('should skip markdown headers', () => {
    const answer = '## Section Header\nActual claim here [1].';
    const claims = extractClaims(answer);
    expect(claims.every(c => !c.text.startsWith('#'))).toBe(true);
  });

  it('should detect quote claims with Greek text', () => {
    const answer = 'Chrysippus uses the term εἱμαρμένη to refer to fate [1].';
    const claims = extractClaims(answer);
    expect(claims[0].claimType).toBe('quote');
  });

  it('should detect paraphrase claims', () => {
    const answer = 'According to Bobzien, the Stoics maintained a compatibilist position [2].';
    const claims = extractClaims(answer);
    expect(claims[0].claimType).toBe('paraphrase');
  });

  it('should detect historical claims', () => {
    const answer = 'In the 3rd century BCE, Chrysippus developed his theory of fate [1].';
    const claims = extractClaims(answer);
    expect(claims[0].claimType).toBe('historical');
  });

  it('should skip very short fragments', () => {
    const answer = 'Short. Also short. This is a real claim with enough content [1].';
    const claims = extractClaims(answer);
    // Only the last sentence should survive (>10 chars)
    expect(claims.length).toBeGreaterThanOrEqual(1);
    expect(claims.some(c => c.text.includes('real claim'))).toBe(true);
  });
});

describe('attachClaimSources', () => {
  it('should attach source nodeIds based on citation markers', () => {
    const claims: ClaimUnit[] = [{
      claimId: 'c1',
      text: 'Some claim [1] [2].',
      sourceNodeIds: [],
      citationMarkers: [1, 2],
      claimType: 'interpretive',
    }];
    const sources = [makeSource(1, 'node_a'), makeSource(2, 'node_b')];
    const attached = attachClaimSources(claims, sources);
    expect(attached[0].sourceNodeIds).toEqual(['node_a', 'node_b']);
  });

  it('should handle missing source IDs gracefully', () => {
    const claims: ClaimUnit[] = [{
      claimId: 'c1',
      text: 'Claim [99].',
      sourceNodeIds: [],
      citationMarkers: [99],
      claimType: 'interpretive',
    }];
    const sources = [makeSource(1, 'node_a')];
    const attached = attachClaimSources(claims, sources);
    expect(attached[0].sourceNodeIds).toEqual([]);
  });
});

describe('buildVerificationContext', () => {
  it('should build context from cited sources', () => {
    const claim: ClaimUnit = {
      claimId: 'c1',
      text: 'Some claim.',
      sourceNodeIds: ['node_a'],
      citationMarkers: [1],
      claimType: 'interpretive',
    };
    const sources = [makeSource(1, 'node_a', 'Chrysippus on fate')];
    const context = buildVerificationContext(claim, sources);
    expect(context).toContain('Chrysippus on fate');
  });

  it('should return empty string for claims with no matching sources', () => {
    const claim: ClaimUnit = {
      claimId: 'c1',
      text: 'Some claim.',
      sourceNodeIds: ['nonexistent'],
      citationMarkers: [],
      claimType: 'interpretive',
    };
    const context = buildVerificationContext(claim, []);
    expect(context.trim()).toBe('');
  });
});

describe('classifyClaim', () => {
  it('should classify high scores as supported', () => {
    expect(classifyClaim(0.95)).toBe('supported');
    expect(classifyClaim(0.78)).toBe('supported');
  });

  it('should classify medium scores as partial', () => {
    expect(classifyClaim(0.60)).toBe('partial');
    expect(classifyClaim(0.50)).toBe('partial');
  });

  it('should classify low scores as unsupported', () => {
    expect(classifyClaim(0.30)).toBe('unsupported');
    expect(classifyClaim(0.0)).toBe('unsupported');
    expect(classifyClaim(0.49)).toBe('unsupported');
  });
});

describe('summarizeVerification', () => {
  it('should count claims by status', () => {
    const claims: ClaimUnit[] = [
      { claimId: '1', text: 'a', sourceNodeIds: [], citationMarkers: [], claimType: 'interpretive', status: 'supported', score: 0.9 },
      { claimId: '2', text: 'b', sourceNodeIds: [], citationMarkers: [], claimType: 'interpretive', status: 'supported', score: 0.85 },
      { claimId: '3', text: 'c', sourceNodeIds: [], citationMarkers: [], claimType: 'interpretive', status: 'partial', score: 0.6 },
      { claimId: '4', text: 'd', sourceNodeIds: [], citationMarkers: [], claimType: 'interpretive', status: 'unsupported', score: 0.2 },
    ];
    const summary = summarizeVerification(claims);
    expect(summary.total).toBe(4);
    expect(summary.supported).toBe(2);
    expect(summary.partial).toBe(1);
    expect(summary.unsupported).toBe(1);
  });

  it('should handle empty claims list', () => {
    const summary = summarizeVerification([]);
    expect(summary.total).toBe(0);
    expect(summary.supported).toBe(0);
  });
});
