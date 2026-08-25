import { describe, expect, it } from 'vitest';

import type { AtlasNodeMeta } from '../cosmograph/AtlasHelpers';
import {
  periodBounds,
  periodIntersectsWindow,
  timelineFromGraph,
} from './chronosTimeline';

function node(id: string, label: string, periodLabel: string): AtlasNodeMeta {
  return {
    id,
    label,
    periodLabel,
    type: 'person',
    typeKey: 'person',
    typeLabel: 'Person',
    layer: 'ancient',
    schoolLabel: 'Unattached',
    degree: 1,
    importance: 1,
    color: '#000000',
    opacity: 1,
    size: 6,
    description: '',
    greekTerm: '',
    latinTerm: '',
  };
}

describe('Chronos fact-safety contract', () => {
  it('has explicit bounds for represented editorial periods and no guessed unknown bounds', () => {
    expect(periodBounds('Early Modern')).toEqual([1500, 1800]);
    expect(periodBounds('Second Temple Judaism')).toEqual([-516, 70]);
    expect(periodBounds('Unspecified')).toEqual([null, null]);
    expect(periodBounds('A future unregistered period')).toEqual([null, null]);
  });

  it('does not place unknown periods inside a user-selected date window', () => {
    expect(periodIntersectsWindow([null, null], null, null)).toBe(true);
    expect(periodIntersectsWindow([null, null], -400, 200)).toBe(false);
  });

  it('never converts a period boundary into a node-specific date', () => {
    const timeline = timelineFromGraph(
      [
        node('leibniz', 'Gottfried Wilhelm Leibniz', 'Early Modern'),
        node('unknown', 'Undated dossier', 'Unspecified'),
      ],
      0,
      null,
      null,
    );
    const earlyModern = timeline.periods.find((period) => period.label === 'Early Modern');
    const unknown = timeline.periods.find((period) => period.label === 'Unspecified');
    expect(earlyModern?.startYear).toBe(1500);
    expect(earlyModern?.nodes[0].startYear).toBeNull();
    expect(unknown?.startYear).toBeNull();
    expect(unknown?.nodes[0].startYear).toBeNull();
  });
});
