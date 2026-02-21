/**
 * Tests for Claim Repair Service
 */

import { describe, it, expect } from 'vitest';
import { applyRepairs } from '../src/services/claim-repair';
import { ClaimUnit, ClaimRepairResult } from '../src/types';

function makeClaim(id: string, text: string): ClaimUnit {
  return {
    claimId: id,
    text,
    sourceNodeIds: [],
    citationMarkers: [],
    claimType: 'interpretive',
    status: 'unsupported',
  };
}

describe('applyRepairs', () => {
  it('should replace rewritten claims in the answer', () => {
    const answer = 'First claim. Second claim here. Third claim.';
    const claims = [
      makeClaim('c1', 'First claim.'),
      makeClaim('c2', 'Second claim here.'),
    ];
    const repairs = new Map<string, ClaimRepairResult>();
    repairs.set('c2', {
      claimId: 'c2',
      action: 'rewrite',
      originalText: 'Second claim here.',
      rewrittenText: 'Corrected second claim.',
      mappedNodeIds: ['node_a'],
    });

    const result = applyRepairs(answer, claims, repairs);
    expect(result).toContain('First claim.');
    expect(result).toContain('Corrected second claim.');
    expect(result).toContain('Third claim.');
    expect(result).not.toContain('Second claim here.');
  });

  it('should remove claims marked for removal', () => {
    const answer = 'Good claim [1]. Bad claim. Another good claim [2].';
    const claims = [makeClaim('c1', 'Bad claim.')];
    const repairs = new Map<string, ClaimRepairResult>();
    repairs.set('c1', {
      claimId: 'c1',
      action: 'remove',
      originalText: 'Bad claim.',
      mappedNodeIds: [],
    });

    const result = applyRepairs(answer, claims, repairs);
    expect(result).not.toContain('Bad claim.');
    expect(result).toContain('Good claim [1].');
    expect(result).toContain('Another good claim [2].');
  });

  it('should clean up whitespace artifacts after removal', () => {
    const answer = 'Line one.\n\nRemove this.\n\n\nLine three.';
    const claims = [makeClaim('c1', 'Remove this.')];
    const repairs = new Map<string, ClaimRepairResult>();
    repairs.set('c1', {
      claimId: 'c1',
      action: 'remove',
      originalText: 'Remove this.',
      mappedNodeIds: [],
    });

    const result = applyRepairs(answer, claims, repairs);
    expect(result).not.toContain('Remove this.');
    // Should collapse excessive newlines
    expect(result).not.toContain('\n\n\n');
  });

  it('should handle empty repairs map (no changes)', () => {
    const answer = 'Original answer text.';
    const result = applyRepairs(answer, [], new Map());
    expect(result).toBe('Original answer text.');
  });

  it('should handle multiple removals', () => {
    const answer = 'Keep [1]. Remove A. Keep again [2]. Remove B.';
    const claims = [
      makeClaim('c1', 'Remove A.'),
      makeClaim('c2', 'Remove B.'),
    ];
    const repairs = new Map<string, ClaimRepairResult>();
    repairs.set('c1', { claimId: 'c1', action: 'remove', originalText: 'Remove A.', mappedNodeIds: [] });
    repairs.set('c2', { claimId: 'c2', action: 'remove', originalText: 'Remove B.', mappedNodeIds: [] });

    const result = applyRepairs(answer, claims, repairs);
    expect(result).not.toContain('Remove A.');
    expect(result).not.toContain('Remove B.');
    expect(result).toContain('Keep [1].');
    expect(result).toContain('Keep again [2].');
  });

  it('should ignore claims not in the repairs map', () => {
    const answer = 'Claim A. Claim B.';
    const claims = [makeClaim('c1', 'Claim A.')];
    const repairs = new Map<string, ClaimRepairResult>();
    // No repair for c1

    const result = applyRepairs(answer, claims, repairs);
    expect(result).toBe('Claim A. Claim B.');
  });

  it('should handle keep action (no change)', () => {
    const answer = 'Kept claim. Other text.';
    const claims = [makeClaim('c1', 'Kept claim.')];
    const repairs = new Map<string, ClaimRepairResult>();
    repairs.set('c1', {
      claimId: 'c1',
      action: 'keep',
      originalText: 'Kept claim.',
      mappedNodeIds: ['node_a'],
    });

    const result = applyRepairs(answer, claims, repairs);
    expect(result).toContain('Kept claim.');
  });
});
