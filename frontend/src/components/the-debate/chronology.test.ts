import { describe, expect, it } from 'vitest';

import {
  arcPath,
  chronoScale,
  fractionOf,
  ghostsWithin,
  intervalLabel,
  largestSilence,
  type ChronoGhost,
  type ChronoStation,
} from './chronology';

/**
 * The eight stations, dated by WORK rather than by life. These are the numbers
 * the rail's whole claim rests on, so they are the fixture: if the dates move,
 * the shape of the argument moves, and this test says so out loud.
 */
const STATIONS: ChronoStation[] = [
  { id: 'epicurus', label: 'Epicurus', year: -300, yearLabel: 'c. 300 BCE', tone: 'greek' },
  { id: 'chrysippus', label: 'Chrysippus', year: -250, yearLabel: 'c. 250 BCE', tone: 'greek' },
  { id: 'carneades', label: 'Carneades', year: -155, yearLabel: 'c. 155 BCE', tone: 'greek' },
  { id: 'epictetus', label: 'Epictetus', year: 108, yearLabel: 'c. 108 CE', tone: 'greek' },
  { id: 'alexander', label: 'Alexander', year: 200, yearLabel: 'c. 200 CE', tone: 'greek' },
  { id: 'origen', label: 'Origen', year: 229, yearLabel: 'c. 229 CE', tone: 'greek' },
  { id: 'augustine', label: 'Augustine', year: 388, yearLabel: '388 CE', tone: 'latin' },
  { id: 'boethius', label: 'Boethius', year: 524, yearLabel: '524 CE', tone: 'latin' },
];

const GHOSTS: ChronoGhost[] = [
  { id: 'cicero', label: 'Cicero', year: -44, yearLabel: '44 BCE' },
  { id: 'plotinus', label: 'Plotinus', year: 254, yearLabel: 'c. 254 CE' },
  { id: 'nemesius', label: 'Nemesius', year: 390, yearLabel: 'c. 390 CE' },
];

describe('chronoScale', () => {
  it('spans the stations and nothing else', () => {
    const scale = chronoScale(STATIONS);
    expect(scale).toEqual({ start: -300, end: 524, span: 824 });
  });

  it('survives a single station without dividing by zero', () => {
    expect(chronoScale([STATIONS[0]]).span).toBe(1);
  });

  it('survives an empty rail', () => {
    expect(chronoScale([]).span).toBe(1);
  });
});

describe('fractionOf', () => {
  const scale = chronoScale(STATIONS);

  it('anchors the ends', () => {
    expect(fractionOf(-300, scale)).toBe(0);
    expect(fractionOf(524, scale)).toBe(1);
  });

  it('places a ghost inside the span', () => {
    expect(fractionOf(-44, scale)).toBeCloseTo(0.3107, 4);
  });

  it('clamps a year outside the span rather than drawing off the rail', () => {
    expect(fractionOf(-900, scale)).toBe(0);
    expect(fractionOf(1500, scale)).toBe(1);
  });
});

describe('the intervals are not equal, which is the point', () => {
  const scale = chronoScale(STATIONS);
  const gaps = STATIONS.slice(1).map(
    (s, i) => fractionOf(s.year, scale) - fractionOf(STATIONS[i].year, scale),
  );

  it('refuses the even spacing the old lineage graphic asserted', () => {
    const even = 1 / (STATIONS.length - 1);
    const worst = Math.max(...gaps.map((g) => Math.abs(g - even)));
    expect(worst).toBeGreaterThan(0.15);
  });

  it('crowds Alexander and Origen into under five per cent of the rail', () => {
    const alexander = fractionOf(200, scale);
    const origen = fractionOf(229, scale);
    expect(origen - alexander).toBeLessThan(0.05);
  });
});

describe('largestSilence', () => {
  it('finds the 263 years between Carneades and Epictetus', () => {
    const silence = largestSilence(STATIONS);
    expect(silence).not.toBeNull();
    expect(silence?.fromId).toBe('carneades');
    expect(silence?.toId).toBe('epictetus');
    expect(silence?.years).toBe(263);
  });

  it('reports it as roughly a third of the whole span', () => {
    expect(largestSilence(STATIONS)?.share).toBeCloseTo(263 / 824, 4);
  });

  it('is order-independent: the caller may pass any order', () => {
    const shuffled = [...STATIONS].reverse();
    expect(largestSilence(shuffled)?.years).toBe(263);
  });

  it('finds the 450-year gap when only the original five are passed', () => {
    const five = STATIONS.filter((s) =>
      ['chrysippus', 'alexander', 'origen', 'augustine', 'boethius'].includes(s.id),
    );
    const silence = largestSilence(five);
    expect(silence?.years).toBe(450);
    expect(silence?.share).toBeGreaterThan(0.55);
  });

  it('returns null when there is nothing to be silent between', () => {
    expect(largestSilence([STATIONS[0]])).toBeNull();
  });
});

describe('ghostsWithin', () => {
  it('puts Cicero, and only Cicero, in the silence', () => {
    const silence = largestSilence(STATIONS);
    expect(ghostsWithin(GHOSTS, silence, STATIONS).map((g) => g.id)).toEqual([
      'cicero',
    ]);
  });

  it('returns nothing when there is no silence', () => {
    expect(ghostsWithin(GHOSTS, null, STATIONS)).toEqual([]);
  });
});

describe('arcPath', () => {
  it('starts and ends on the rail, and bulges away from it', () => {
    const d = arcPath(132, 600, 200, true);
    expect(d.startsWith('M 132 600')).toBe(true);
    expect(d.endsWith('132 200')).toBe(true);
    const control = Number(d.split('Q ')[1].split(' ')[0]);
    expect(control).toBeLessThan(132);
  });

  it('reaches further for a longer reuse', () => {
    const near = arcPath(132, 300, 280, true);
    const far = arcPath(132, 700, 100, true);
    const ctrl = (d: string) => Number(d.split('Q ')[1].split(' ')[0]);
    expect(ctrl(far)).toBeLessThan(ctrl(near));
  });

  it('swaps the axes when the rail is horizontal', () => {
    expect(arcPath(52, 100, 400, false).startsWith('M 100 52')).toBe(true);
  });
});

describe('intervalLabel', () => {
  it('does not write "1 years"', () => {
    expect(intervalLabel(1)).toBe('1 year');
    expect(intervalLabel(263)).toBe('263 years');
  });
});
