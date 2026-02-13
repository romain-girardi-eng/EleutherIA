/**
 * Tests for Evidence Layering — primary/secondary partitioning + hierarchical context.
 */

import { describe, it, expect } from 'vitest';
import {
  isPrimaryEvidence,
  partitionEvidence,
  buildHierarchicalContext,
} from '../src/services/evidence-layering';
import { Evidence } from '../src/types/agentic';

function makeEvidence(overrides: Partial<Evidence>): Evidence {
  return {
    source: 'test',
    content: 'Test content',
    type: 'node',
    confidence: 0.8,
    isPrimary: true,
    ...overrides,
  };
}

describe('isPrimaryEvidence', () => {
  it('should classify bridge evidence as primary', () => {
    const e = makeEvidence({ type: 'bridge' });
    expect(isPrimaryEvidence(e)).toBe(true);
  });

  it('should classify passage evidence as primary', () => {
    const e = makeEvidence({ type: 'passage' });
    expect(isPrimaryEvidence(e)).toBe(true);
  });

  it('should classify community evidence as secondary', () => {
    const e = makeEvidence({ type: 'community' });
    expect(isPrimaryEvidence(e)).toBe(false);
  });

  it('should classify context evidence as secondary', () => {
    const e = makeEvidence({ type: 'context' });
    expect(isPrimaryEvidence(e)).toBe(false);
  });

  it('should classify philosopher nodes as primary', () => {
    const e = makeEvidence({ nodeType: 'philosopher', nodeLabel: 'Chrysippus' });
    expect(isPrimaryEvidence(e)).toBe(true);
  });

  it('should classify concept nodes as primary', () => {
    const e = makeEvidence({ nodeType: 'concept', nodeLabel: 'Stoic Fate' });
    expect(isPrimaryEvidence(e)).toBe(true);
  });

  it('should classify modern scholar mentions as secondary', () => {
    const e = makeEvidence({
      nodeType: 'philosopher',
      nodeLabel: 'Bobzien (modern scholar)',
      content: 'Modern interpretation of Stoic determinism',
    });
    expect(isPrimaryEvidence(e)).toBe(false);
  });

  it('should use period metadata for classification', () => {
    const e = makeEvidence({
      nodeType: 'unknown',
      isPrimary: false,
      metadata: { period: 'Hellenistic' },
    });
    expect(isPrimaryEvidence(e)).toBe(true);
  });
});

describe('partitionEvidence', () => {
  it('should partition mixed evidence correctly', () => {
    const evidence = [
      makeEvidence({ type: 'passage', content: 'Ancient text' }),
      makeEvidence({ type: 'community', content: 'Community summary' }),
      makeEvidence({ type: 'bridge', content: 'Bridge path' }),
      makeEvidence({ type: 'context', content: 'Context text' }),
      makeEvidence({ type: 'node', nodeType: 'philosopher', nodeLabel: 'Epictetus' }),
    ];

    const result = partitionEvidence(evidence);
    expect(result.primary.length).toBe(3); // passage, bridge, philosopher node
    expect(result.secondary.length).toBe(2); // community, context
  });

  it('should handle empty evidence', () => {
    const result = partitionEvidence([]);
    expect(result.primary).toEqual([]);
    expect(result.secondary).toEqual([]);
  });
});

describe('buildHierarchicalContext', () => {
  it('should build context with all three sections', () => {
    const primary = [
      makeEvidence({ nodeLabel: 'Chrysippus', content: 'Stoic philosopher' }),
    ];
    const secondary = [
      makeEvidence({ type: 'community', source: 'Stoic Community', content: 'Overview' }),
    ];
    const passages = [
      {
        passageId: 'p1',
        textContent: 'ἡ εἱμαρμένη ἐστὶν...',
        canonicalRef: 'De Fato 1.1',
        author: 'Chrysippus',
        workTitle: 'On Fate',
        language: 'grc' as const,
        confidence: 0.95,
      },
    ];

    const context = buildHierarchicalContext(primary, secondary, passages);

    expect(context).toContain('PRIMARY SOURCE TEXTS');
    expect(context).toContain('Chrysippus');
    expect(context).toContain('ANCIENT SOURCES');
    expect(context).toContain('MODERN SCHOLARSHIP');
  });

  it('should handle empty passages gracefully', () => {
    const primary = [makeEvidence({ nodeLabel: 'Test' })];
    const context = buildHierarchicalContext(primary, [], []);

    expect(context).toContain('ANCIENT SOURCES');
    expect(context).not.toContain('PRIMARY SOURCE TEXTS');
  });

  it('should include CTS URN when available', () => {
    const passages = [
      {
        passageId: 'p1',
        textContent: 'Some text',
        canonicalRef: 'De Fato 1.1',
        author: 'Chrysippus',
        workTitle: 'On Fate',
        language: 'grc' as const,
        ctsUrn: 'urn:cts:greekLit:tlg0012.tlg001:1.1',
        confidence: 0.9,
      },
    ];

    const context = buildHierarchicalContext([], [], passages);
    expect(context).toContain('urn:cts:greekLit');
  });
});
