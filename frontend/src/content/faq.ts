/**
 * Grounded FAQ content for EleutherIA.
 *
 * Every answer is a faithful condensation of the repository's own documented facts:
 * README.md, .zenodo.json, data/stats.json, CLAUDE.md, and concept/person nodes in
 * data/kg/nodes.jsonl. No claim, date, statistic, or attribution here is invented.
 * Any ancient-Greek token is copied verbatim from the source data and is never
 * generated, paraphrased, or translated (see the project integrity policy).
 *
 * Authored in English. Scholarly prose is intentionally not localised here; UI chrome
 * may use the existing i18n layer, but term definitions and answers stay English
 * pending human-reviewed translation.
 *
 * CANONICAL DATA LIVES IN `faq.json` — that plain-JSON file is the single source of
 * truth, imported BOTH here (typed, for the React /faq page) AND by the SEO prerenderer
 * (`scripts/prerender-seo.mjs`), so the real answer text appears in the static HTML
 * served to crawlers. Edit the JSON, never duplicate the data here.
 */

import faqData from './faq.json';

export interface FaqEntry {
  /** The user-facing question. */
  question: string;
  /** A self-contained, citable answer (2-5 sentences), grounded in repo facts. */
  answer: string;
}

export const FAQ_ENTRIES: readonly FaqEntry[] = faqData as FaqEntry[];
