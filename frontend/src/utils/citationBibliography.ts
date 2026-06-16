import type { PassageCitation } from '../types';

/**
 * Leaked-id guard — mirrors the backend `_LEAKED_ID_RE` (routes.py). A label
 * that still matches one of these prefixes is a raw node id that escaped
 * resolution; it must NEVER be rendered to the user. The FE hides it.
 */
export const LEAKED_ID_RE =
  /^(?:b_[0-9a-f]+|scholarly_argument_|scholar_position_|concept_|person_|work_|argument_|publication_|pub_)/;

export function isLeakedId(value: string | null | undefined): boolean {
  const text = (value ?? '').trim();
  if (!text) return false;
  return LEAKED_ID_RE.test(text);
}

/** A render-ready citation for the inline answer + CitationGenerator export. */
export interface ResolvedCitation {
  id: string;
  /** Stable node/passage id used for click routing (kept, never rendered raw). */
  node_id?: string;
  text: string;
  source: string;
  citation: string;
  layer: 'primary' | 'secondary';
  cts_urn?: string;
  doi?: string;
}

/** A BibliographyEntry consumed by <BibliographyPanel>. */
export interface BibliographyEntry {
  citation_key: string;
  author: string;
  year?: number;
  title: string;
  full_citation_chicago: string;
  full_citation_apa?: string;
  full_citation_harvard?: string;
  bibtex: string;
  page_reference?: string;
  cts_urn?: string;
}

/** First author surname for sorting/keys, derived from a "Surname, ..." label. */
function authorSurname(label: string): string {
  const trimmed = label.trim();
  if (!trimmed) return '';
  // "Bobzien, S. (1998). ..." → "Bobzien"; "Cicero, De Fato 41-43" → "Cicero".
  return trimmed.split(/[,.(]/)[0].trim();
}

function parseYear(label: string, fallback?: number | null): number | undefined {
  if (typeof fallback === 'number' && Number.isFinite(fallback)) return fallback;
  const m = label.match(/\((\d{4})\)|\b(1[5-9]\d{2}|20\d{2})\b/);
  const year = m ? Number(m[1] ?? m[2]) : NaN;
  return Number.isFinite(year) ? year : undefined;
}

function bibtexKeyFromLabel(label: string, year?: number, fallbackId?: string): string {
  const surname = authorSurname(label).replace(/[^a-zA-Z0-9]/g, '');
  if (surname) return `${surname}${year ?? ''}`;
  const fromId = (fallbackId ?? 'ref').replace(/[^a-zA-Z0-9]/g, '_');
  return fromId || 'ref';
}

/**
 * Build the inline/export citation list from the backend's typed
 * `passage_citations`. Each kept entry carries a resolved label + the original
 * node id (for click routing). Entries whose label is still a raw leaked id are
 * dropped. Falls back to the legacy `ancient_sources` / `modern_scholarship`
 * string lists ONLY when no typed citations are present.
 */
export function buildResolvedCitations(
  passageCitations: PassageCitation[] | undefined,
  fallbackAncient: string[] | undefined,
  fallbackModern: string[] | undefined,
): ResolvedCitation[] {
  const typed = (passageCitations ?? []).filter(
    (c): c is PassageCitation => !!c && typeof c === 'object',
  );

  if (typed.length > 0) {
    const out: ResolvedCitation[] = [];
    typed.forEach((c, i) => {
      const label = (c.label ?? '').trim();
      if (!label || isLeakedId(label)) return; // never render a raw id
      const layer: 'primary' | 'secondary' =
        c.layer === 'secondary' ? 'secondary' : 'primary';
      out.push({
        id: `cit_${layer}_${c.id ?? i}`,
        node_id: c.id ?? undefined,
        text: label,
        source: label,
        citation: label,
        layer,
        cts_urn: c.cts_urn ?? undefined,
        doi: c.doi ?? undefined,
      });
    });
    if (out.length > 0) return out;
  }

  // Legacy fallback — string lists only, also guarded.
  const ancient = (fallbackAncient ?? [])
    .filter((s) => s && !isLeakedId(s))
    .map<ResolvedCitation>((s, i) => ({
      id: `ancient_${i}`,
      text: s,
      source: s,
      citation: s,
      layer: 'primary',
    }));
  const modern = (fallbackModern ?? [])
    .filter((s) => s && !isLeakedId(s))
    .map<ResolvedCitation>((s, i) => ({
      id: `modern_${i}`,
      text: s,
      source: s,
      citation: s,
      layer: 'secondary',
    }));
  return [...ancient, ...modern];
}

/**
 * Build a deduplicated, author-sorted BibliographyEntry[] from resolved
 * citations. Primary (ancient) entries surface their CTS URN; secondary
 * (modern) entries surface DOI + BibTeX. The full_citation_* strings reuse the
 * resolved label, which already follows the backend's citation formatting.
 */
export function buildBibliography(citations: ResolvedCitation[]): BibliographyEntry[] {
  const seen = new Set<string>();
  const entries: BibliographyEntry[] = [];

  for (const c of citations) {
    const label = c.citation.trim();
    if (!label || isLeakedId(label)) continue;
    const dedupeKey = label.toLowerCase();
    if (seen.has(dedupeKey)) continue;
    seen.add(dedupeKey);

    const author = authorSurname(label) || label;
    const year = parseYear(label);
    const citationKey = `${bibtexKeyFromLabel(label, year, c.node_id)}_${entries.length}`;
    const bibtexKey = bibtexKeyFromLabel(label, year, c.node_id);
    const bibtex = [
      `@misc{${bibtexKey},`,
      `  author = {${author}},`,
      `  title = {${label}},`,
      year !== undefined ? `  year = {${year}},` : '',
      c.doi ? `  doi = {${c.doi}},` : '',
      c.cts_urn ? `  note = {${c.cts_urn}}` : '  note = {Cited source}',
      '}',
    ]
      .filter(Boolean)
      .join('\n');

    entries.push({
      citation_key: citationKey,
      author,
      year,
      title: label,
      full_citation_chicago: label,
      full_citation_apa: label,
      full_citation_harvard: label,
      bibtex,
      cts_urn: c.cts_urn,
    });
  }

  return entries.sort((a, b) =>
    a.author.localeCompare(b.author, undefined, { sensitivity: 'base' }),
  );
}
