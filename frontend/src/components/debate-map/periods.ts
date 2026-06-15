// Chronological ordering helpers for the 12-century argument map.
// Maps the project's historical period labels and free-form date strings to a
// comparable numeric "century anchor" so KG nodes can be laid out on a timeline
// even when they only carry a coarse `period` and not a precise `dates` field.

export interface DatedLike {
  period?: string | null;
  dates?: string | null;
}

const PERIOD_ANCHORS: ReadonlyArray<[RegExp, number]> = [
  [/presocratic/i, -550],
  [/classical/i, -400],
  [/hellenistic/i, -250],
  [/(roman republic)/i, -100],
  [/(roman imperial|imperial|roman)/i, 150],
  [/(second temple|second-temple)/i, -50],
  [/(patristic|early christian)/i, 250],
  [/(late antiquity|late antique)/i, 450],
  [/byzantine/i, 700],
  [/medieval/i, 1200],
  [/(renaissance|early modern)/i, 1550],
  [/modern/i, 1850],
  [/contemporary/i, 1980],
];

/**
 * Parse a free-form date string ("4th c. BCE", "c. 280 BCE", "354 CE",
 * "c. 477–526 CE") into an approximate signed year. BCE → negative.
 * Returns null when nothing parseable is found.
 */
export function parseApproxYear(raw: string | null | undefined): number | null {
  if (!raw) return null;
  const text = raw.trim();

  // Ordinal century, e.g. "3rd c. BCE", "2nd century CE"
  const century = text.match(/(\d+)\s*(?:st|nd|rd|th)?\s*c(?:entury|\.)?\s*(BCE|BC|CE|AD)/i);
  if (century) {
    const value = parseInt(century[1], 10) * 100 - 50; // mid-century anchor
    return /b/i.test(century[2]) ? -value : value;
  }

  // Bare year, e.g. "280 BCE", "c. 354 CE", "524 AD"
  const year = text.match(/(\d{1,4})\s*(BCE|BC|CE|AD)/i);
  if (year) {
    const value = parseInt(year[1], 10);
    return /b/i.test(year[2]) ? -value : value;
  }

  return null;
}

/** Best-effort century anchor for any dated KG node. Lower = earlier. */
export function chronologicalAnchor(node: DatedLike): number {
  const fromDates = parseApproxYear(node.dates ?? null);
  if (fromDates !== null) return fromDates;

  const period = node.period ?? '';
  for (const [pattern, anchor] of PERIOD_ANCHORS) {
    if (pattern.test(period)) return anchor;
  }
  return Number.POSITIVE_INFINITY; // undated nodes sink to the end
}

/**
 * Convert a signed year into the timeline `dateRange` label the existing
 * ConceptEvolutionTimeline component already knows how to sort
 * ("Nth c. BCE" / "Nth c. CE").
 */
export function yearToCenturyLabel(year: number): string {
  if (!Number.isFinite(year)) return 'Undated';
  const era = year < 0 ? 'BCE' : 'CE';
  const abs = Math.abs(year);
  const century = Math.max(1, Math.ceil(abs / 100));
  const suffix =
    century % 10 === 1 && century % 100 !== 11
      ? 'st'
      : century % 10 === 2 && century % 100 !== 12
        ? 'nd'
        : century % 10 === 3 && century % 100 !== 13
          ? 'rd'
          : 'th';
  return `${century}${suffix} c. ${era}`;
}

/** Human-friendly span across the whole subgraph (earliest → latest century). */
export function describeSpan(anchors: number[]): { earliest: string; latest: string; centuries: number } {
  const finite = anchors.filter((a) => Number.isFinite(a));
  if (finite.length === 0) return { earliest: '—', latest: '—', centuries: 0 };
  const min = Math.min(...finite);
  const max = Math.max(...finite);
  const centuries = Math.max(1, Math.round((max - min) / 100));
  return { earliest: yearToCenturyLabel(min), latest: yearToCenturyLabel(max), centuries };
}
