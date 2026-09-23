import { describe, expect, it } from 'vitest';

import type { AtlasNodeMeta } from '../cosmograph/AtlasHelpers';
import {
  buildSchoolMatrix,
  CHRONOS_SCALE,
  densityIntensity,
  eraAtYear,
  fractionToYear,
  periodBounds,
  periodIntersectsWindow,
  SCHOOL_NONE,
  SCHOOL_OTHER,
  snapYear,
  timelineFromGraph,
  yearToFraction,
} from './chronosTimeline';

function node(id: string, label: string, periodLabel: string, schoolLabel = 'Unattached'): AtlasNodeMeta {
  return {
    id,
    label,
    periodLabel,
    type: 'person',
    typeKey: 'person',
    typeLabel: 'Person',
    layer: 'ancient',
    schoolLabel,
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

describe('Chronos piecewise time scale', () => {
  it('maps the scale ends and segment joins to their cumulative shares', () => {
    expect(yearToFraction(-1000)).toBe(0);
    expect(yearToFraction(2030)).toBeCloseTo(1);
    expect(yearToFraction(-650)).toBeCloseTo(CHRONOS_SCALE[0].share);
    expect(yearToFraction(650)).toBeCloseTo(CHRONOS_SCALE[0].share + CHRONOS_SCALE[1].share);
  });

  it('is monotonic and invertible across the breaks', () => {
    let previous = -1;
    for (let year = -1000; year <= 2030; year += 37) {
      const fraction = yearToFraction(year);
      expect(fraction).toBeGreaterThan(previous);
      expect(fractionToYear(fraction)).toBeCloseTo(year, 6);
      previous = fraction;
    }
  });

  it('gives antiquity the bulk of the width', () => {
    expect(yearToFraction(650) - yearToFraction(-650)).toBeGreaterThan(0.7);
  });

  it('snaps brushed years to a density-appropriate grain', () => {
    expect(snapYear(-323.4)).toBe(-320);
    expect(snapYear(1512)).toBe(1500);
  });

  it('finds the era under a year and nothing before the first band', () => {
    expect(eraAtYear(-200)?.key).toBe('hellenistic');
    expect(eraAtYear(100)?.key).toBe('romanImperial');
    expect(eraAtYear(-900)).toBeNull();
  });

  it('uses a log intensity so sparse periods stay visible', () => {
    expect(densityIntensity(0, 100)).toBe(0);
    expect(densityIntensity(100, 100)).toBe(1);
    expect(densityIntensity(13, 14000)).toBeGreaterThan(0.2);
  });
});

describe('Chronos school x period matrix', () => {
  it('orders schools by volume, folds the tail and keeps unattached loci apart', () => {
    const timeline = timelineFromGraph(
      [
        node('a', 'A', 'Hellenistic', 'Stoic'),
        node('b', 'B', 'Hellenistic', 'Stoic'),
        node('c', 'C', 'Roman Imperial', 'Stoic'),
        node('d', 'D', 'Roman Imperial', 'Epicurean'),
        node('e', 'E', 'Classical Greek', 'Peripatetic'),
        node('f', 'F', 'Unspecified'),
      ],
      0,
      null,
      null,
    );
    const matrix = buildSchoolMatrix(timeline, 1);
    expect(matrix.columns.map((period) => period.label)).toEqual([
      'Classical Greek', 'Hellenistic', 'Roman Imperial', 'Unspecified',
    ]);
    expect(matrix.rows.map((row) => row.key)).toEqual(['Stoic', SCHOOL_OTHER, SCHOOL_NONE]);
    expect(matrix.rows[0].cells).toEqual([0, 2, 1, 0]);
    expect(matrix.rows[1].members).toEqual(['Epicurean', 'Peripatetic']);
    expect(matrix.rows[1].cells).toEqual([1, 0, 1, 0]);
    expect(matrix.rows[2].cells).toEqual([0, 0, 0, 1]);
    expect(matrix.max).toBe(2);
  });
});
