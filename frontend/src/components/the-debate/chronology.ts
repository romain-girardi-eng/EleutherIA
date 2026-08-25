/**
 * the-debate — chronology as data, not as layout.
 *
 * The old lineage graphic spaced its dots evenly. To a reader who knows the
 * period, equal spacing asserts equal intervals, and the intervals here are
 * anything but equal: the argument runs from the Garden to a cell in Pavia
 * across eight centuries, and its longest stretch is a silence.
 *
 * Every number below is derived from the station years the caller passes in.
 * Nothing is hardcoded, so the graphic cannot drift away from the data — if a
 * figure is added or a date corrected, the rail re-proportions and the named
 * silence is recomputed. The gap is the argument, so the gap is computed.
 */

import type { Tone } from './types';

export interface ChronoStation {
  id: string;
  label: string;
  /** Year of the WORK, negative for BCE. Lives are not the argument; texts are. */
  year: number;
  /** How the year is written for a reader: "c. 250 BCE". */
  yearLabel: string;
  tone: Tone;
}

/** A figure in the knowledge graph the page had to leave out. */
export interface ChronoGhost {
  id: string;
  label: string;
  year: number;
  yearLabel: string;
  /** One clause on why they matter here. Optional, and usually worth it. */
  note?: string;
}

/** Attested reuse: `from` reuses an argument of `to`. Direction is backwards. */
export interface ChronoArc {
  from: string;
  to: string;
}

export interface ChronoScale {
  start: number;
  end: number;
  span: number;
}

/** The longest run of the rail with no station on it. */
export interface ChronoSilence {
  fromId: string;
  toId: string;
  fromLabel: string;
  toLabel: string;
  years: number;
  /** Fraction of the whole rail, 0–1. */
  share: number;
  startFraction: number;
  endFraction: number;
}

const clamp01 = (n: number): number => Math.min(1, Math.max(0, n));

/** Scale runs from the earliest to the latest station. Ghosts never extend it. */
export function chronoScale(stations: readonly ChronoStation[]): ChronoScale {
  if (stations.length === 0) return { start: 0, end: 1, span: 1 };
  const years = stations.map((s) => s.year);
  const start = Math.min(...years);
  const end = Math.max(...years);
  const span = end - start;
  return { start, end, span: span === 0 ? 1 : span };
}

export function fractionOf(year: number, scale: ChronoScale): number {
  return clamp01((year - scale.start) / scale.span);
}

/**
 * The silence. Returns the widest interval between two consecutive stations,
 * or null when there are fewer than two. Ghosts do not break a silence: they
 * are precisely what stands in it, unread on this page.
 */
export function largestSilence(
  stations: readonly ChronoStation[],
): ChronoSilence | null {
  if (stations.length < 2) return null;
  const scale = chronoScale(stations);
  const ordered = [...stations].sort((a, b) => a.year - b.year);

  let widest: ChronoSilence | null = null;
  for (let i = 1; i < ordered.length; i += 1) {
    const before = ordered[i - 1];
    const after = ordered[i];
    const years = after.year - before.year;
    if (widest && years <= widest.years) continue;
    widest = {
      fromId: before.id,
      toId: after.id,
      fromLabel: before.label,
      toLabel: after.label,
      years,
      share: years / scale.span,
      startFraction: fractionOf(before.year, scale),
      endFraction: fractionOf(after.year, scale),
    };
  }
  return widest;
}

/** Ghosts that fall inside a given silence, in chronological order. */
export function ghostsWithin(
  ghosts: readonly ChronoGhost[],
  silence: ChronoSilence | null,
  stations: readonly ChronoStation[],
): ChronoGhost[] {
  if (!silence) return [];
  const scale = chronoScale(stations);
  return ghosts
    .filter((g) => {
      const f = fractionOf(g.year, scale);
      return f > silence.startFraction && f < silence.endFraction;
    })
    .sort((a, b) => a.year - b.year);
}

/**
 * A taut bracket from one point on the rail back to an earlier one, bulging
 * away from the line. The bulge grows with the distance reached back, so a
 * four-century reuse visibly reaches further than a thirty-year one.
 */
export function arcPath(
  railAxis: number,
  fromPos: number,
  toPos: number,
  vertical: boolean,
  minBulge = 18,
  maxBulge = 76,
): string {
  const reach = Math.abs(fromPos - toPos);
  const bulge = Math.min(maxBulge, Math.max(minBulge, reach * 0.32));
  const mid = (fromPos + toPos) / 2;
  const ctrl = railAxis - bulge;
  return vertical
    ? `M ${railAxis} ${fromPos} Q ${ctrl} ${mid} ${railAxis} ${toPos}`
    : `M ${fromPos} ${railAxis} Q ${mid} ${ctrl} ${toPos} ${railAxis}`;
}

/** Human interval, for the screen-reader equivalent of the rail. */
export function intervalLabel(years: number): string {
  return years === 1 ? '1 year' : `${years} years`;
}
