/**
 * Locale-aware compact number formatter.
 *
 * Produces "20.2k" in en, "20,2 k" in fr/de/it, "20,2k" in el.
 * Returns '—' for non-finite or null/undefined inputs so partial
 * data never crashes copy.
 */
export function formatCompact(
  value: number | undefined | null,
  locale?: string,
): string {
  if (value == null || !Number.isFinite(value)) return '—';
  return new Intl.NumberFormat(locale, {
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(value);
}

/**
 * Locale-aware full integer formatter with grouping separators.
 * Use for exact stat blocks (e.g. "487 works", "69,277 passages").
 */
export function formatFull(
  value: number | undefined | null,
  locale?: string,
): string {
  if (value == null || !Number.isFinite(value)) return '—';
  return new Intl.NumberFormat(locale).format(value);
}
