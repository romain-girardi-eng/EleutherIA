/**
 * Glossary of core concepts in the ancient free-will / fate / moral-responsibility debate.
 *
 * GROUNDING NOTE — Every entry is anchored to an existing EleutherIA knowledge-graph
 * node (`data/kg/nodes.jsonl`) through `id`. Definitions and original-language terms
 * are independently source-collated under the fail-closed audits in `docs/academic/`;
 * they are not assumed to inherit the factual status of a legacy node description.
 * Content is English-only at this stage and remains excluded from entity indexing
 * until the corresponding publication manifest records independent approval.
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
  /** Source-collated Greek/Latin form — omitted where no ancient equivalent exists. */
  originalTerm?: string;
  /** Concise source-collated definition, with disputed interpretations attributed. */
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
