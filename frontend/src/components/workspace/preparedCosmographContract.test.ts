import { describe, expect, it } from 'vitest';

import {
  enqueueCosmographPreparation,
  preparedCosmographContract,
} from './preparedCosmographContract';

describe('prepared Cosmograph data contract', () => {
  it('always supplies the required point and link identity mappings', () => {
    expect(preparedCosmographContract({ backgroundColor: '#fffdf9' }, true)).toEqual({
      backgroundColor: '#fffdf9',
      pointIdBy: 'id',
      pointIndexBy: 'idx',
      linkSourceBy: 'source',
      linkSourceIndexBy: 'sourceidx',
      linkTargetBy: 'target',
      linkTargetIndexBy: 'targetidx',
    });
  });

  it('overrides stale mappings with the schema emitted by the data kit', () => {
    expect(preparedCosmographContract({
      pointIdBy: 'legacy_id',
      pointIndexBy: 'legacy_index',
      linkSourceBy: 'legacy_source',
      linkSourceIndexBy: 'legacy_source_index',
      linkTargetBy: 'legacy_target',
      linkTargetIndexBy: 'legacy_target_index',
    }, true)).toMatchObject({
      pointIdBy: 'id',
      pointIndexBy: 'idx',
      linkSourceBy: 'source',
      linkSourceIndexBy: 'sourceidx',
      linkTargetBy: 'target',
      linkTargetIndexBy: 'targetidx',
    });
  });

  it('does not advertise link mappings when no prepared link table exists', () => {
    const config = preparedCosmographContract({}, false);
    expect(config).toMatchObject({ pointIdBy: 'id', pointIndexBy: 'idx' });
    expect(config).not.toHaveProperty('linkSourceBy');
    expect(config).not.toHaveProperty('linkTargetBy');
  });

  it('serializes different data preparations instead of coalescing their results', async () => {
    const events: string[] = [];
    let releaseFirst!: () => void;
    const firstGate = new Promise<void>((resolve) => { releaseFirst = resolve; });

    const first = enqueueCosmographPreparation(async () => {
      events.push('first:start');
      await firstGate;
      events.push('first:end');
      return 'atlas-slice';
    });
    const second = enqueueCosmographPreparation(async () => {
      events.push('second:start');
      events.push('second:end');
      return 'search-slice';
    });

    await Promise.resolve();
    expect(events).toEqual(['first:start']);
    releaseFirst();
    await expect(Promise.all([first, second])).resolves.toEqual([
      'atlas-slice',
      'search-slice',
    ]);
    expect(events).toEqual([
      'first:start',
      'first:end',
      'second:start',
      'second:end',
    ]);
  });
});
