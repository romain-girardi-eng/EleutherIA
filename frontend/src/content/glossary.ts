/**
 * Glossary of core concepts in the ancient free-will / fate / moral-responsibility debate.
 *
 * GROUNDING NOTE — Every entry is a faithful condensation of an existing `concept`
 * node in the EleutherIA knowledge graph (`data/kg/nodes.jsonl`). The `id` field is
 * that source node's id; `definition` summarises that node's `description` without
 * adding facts not present in the source. Every Greek or Latin token (`originalTerm`,
 * and any inline Greek/Latin in a definition) is copied verbatim, byte-for-byte, from
 * the same source data — none is generated, reconstructed, or translated. Content is
 * English-only at this stage and pending human review for other locales.
 *
 * CANONICAL DATA LIVES IN `glossary.json` — that plain-JSON file is the single source
 * of truth, imported BOTH here (typed, for the React page) AND by the SEO prerenderer
 * (`scripts/prerender-seo.mjs`), so the real definition text appears in the prerendered
 * static HTML that AI crawlers read. Edit the JSON, never duplicate the data here.
 */

import glossaryData from './glossary.json';

export interface GlossaryEntry {
  /** Source KG node id (type === 'concept') in data/kg/nodes.jsonl. */
  id: string;
  /** Clean English / transliterated headline for the term. */
  term: string;
  /** Original Greek/Latin form, copied verbatim from the source node — omitted if none. */
  originalTerm?: string;
  /** 2–4 sentence definition condensed faithfully from the source node's description. */
  definition: string;
  /** Philosophical school, if present in the source node metadata. */
  school?: string;
  /** Historical period, if present in the source node metadata. */
  period?: string;
  /** A few related concept/person node ids, where cheaply derivable. */
  relatedIds: string[];
  /** In-app URL to view this node in the graph visualizer. */
  nodeUrl: string;
}

/**
 * Sorted, nodeUrl-augmented glossary entries (sort order baked into the JSON).
 */
export const glossary: ReadonlyArray<GlossaryEntry> = glossaryData as GlossaryEntry[];
