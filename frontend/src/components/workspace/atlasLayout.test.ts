import { describe, expect, it } from 'vitest';

import {
  MIN_LAYOUT_COVERAGE,
  atlasLayoutFromPositions,
  parseAtlasLayout,
  resolveAtlasPositions,
  serializeAtlasLayout,
  type AtlasLayoutRecord,
} from './atlasLayout';

function layout(entries: Array<[string, number, number]>): AtlasLayoutRecord {
  return {
    releaseId: 'release-a',
    ids: entries.map(([id]) => id),
    positions: new Float32Array(entries.flatMap(([, x, y]) => [x, y])),
  };
}

describe('atlas frozen layout', () => {
  it('round-trips through its serialized form', () => {
    const record = layout([['a', 1.5, -2], ['b', 300, 42]]);
    const parsed = parseAtlasLayout(JSON.parse(JSON.stringify(serializeAtlasLayout(record))));
    expect(parsed?.releaseId).toBe('release-a');
    expect(parsed?.ids).toEqual(['a', 'b']);
    expect([...(parsed?.positions ?? [])]).toEqual([1.5, -2, 300, 42]);
  });

  it('rejects malformed or inconsistent payloads', () => {
    expect(parseAtlasLayout(null)).toBeNull();
    expect(parseAtlasLayout({ version: 2 })).toBeNull();
    const serialized = serializeAtlasLayout(layout([['a', 0, 0]]));
    expect(parseAtlasLayout({ ...serialized, ids: ['a', 'b'] })).toBeNull();
  });

  it('places nodes added after the layout beside their placed neighbours', () => {
    const nodes = Array.from({ length: 20 }, (_, index) => ({ id: `n${index}` }));
    const record = layout(nodes.slice(0, 19).map(({ id }, index) => [id, index * 10, 0]));
    const positions = resolveAtlasPositions(record, nodes, [
      { source: 'n19', target: 'n0' },
      { source: 'n2', target: 'n19' },
    ]);
    const added = positions?.get('n19');
    expect(added).toBeDefined();
    // Mean of n0 (0, 0) and n2 (20, 0), within the small deterministic offset.
    expect(Math.abs((added?.[0] ?? Infinity) - 10)).toBeLessThan(2);
    expect(Math.abs(added?.[1] ?? Infinity)).toBeLessThan(2);
    expect(resolveAtlasPositions(record, nodes, [])?.get('n19')).toEqual(
      resolveAtlasPositions(record, nodes, [])?.get('n19'),
    );
  });

  it('refuses a layout that no longer describes the release', () => {
    const nodes = Array.from({ length: 10 }, (_, index) => ({ id: `n${index}` }));
    const known = Math.floor(nodes.length * MIN_LAYOUT_COVERAGE) - 1;
    const record = layout(nodes.slice(0, known).map(({ id }, index) => [id, index, index]));
    expect(resolveAtlasPositions(record, nodes, [])).toBeNull();
  });

  it('captures renderer positions in point order', () => {
    const record = atlasLayoutFromPositions('r', [{ id: 'a' }, { id: 'b' }], [1, 2, 3, 4]);
    expect(record?.ids).toEqual(['a', 'b']);
    expect([...(record?.positions ?? [])]).toEqual([1, 2, 3, 4]);
    expect(atlasLayoutFromPositions('r', [{ id: 'a' }], [Number.NaN, 0])).toBeNull();
  });
});
