import { describe, expect, it } from 'vitest';

import { computeNodeSize } from './AtlasHelpers';

describe('Atlas visual hierarchy', () => {
  it('keeps leaf evidence quiet while preserving a strong monotonic hub ladder', () => {
    const maxDegree = 4_000;
    const leaf = computeNodeSize(1, maxDegree);
    const connector = computeNodeSize(100, maxDegree);
    const hub = computeNodeSize(maxDegree, maxDegree);

    expect(computeNodeSize(0, maxDegree)).toBeCloseTo(2.4);
    expect(leaf).toBeGreaterThanOrEqual(2.4);
    expect(leaf).toBeLessThan(connector);
    expect(connector).toBeLessThan(hub);
    expect(hub).toBeCloseTo(28);
  });
});
