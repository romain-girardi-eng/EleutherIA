/**
 * FAQPage — frequently asked questions about EleutherIA.
 *
 * Every answer is rendered from the shared, JSON-backed content module
 * (`src/content/faq.ts` → `faq.json`), the single source of truth imported here
 * AND by the SEO prerenderer so the Q&A text appears in the prerendered static
 * HTML (and as FAQPage JSON-LD) that AI crawlers read.
 *
 * Integrity: answers are grounded in the repository's own documented facts; any
 * ancient-Greek token is quoted verbatim, never generated or translated.
 */

import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { HelpCircle, ArrowRight } from 'lucide-react';
import { FAQ_ENTRIES } from '../content/faq';
import type { FaqEntry } from '../content/faq';

/**
 * Stable, human-readable anchor id from a question.
 * Mirrored in src/seo/seo.ts and scripts/prerender-seo.mjs so the prerendered
 * FAQPage JSON-LD question @ids match these in-page section ids.
 */
const faqAnchor = (question: string): string =>
  question
    .toLowerCase()
    .replace(/['’"“”]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 64);

export default function FAQPage() {
  return (
    <div className="min-h-screen w-full pt-28 pb-20 bg-transparent">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">

        {/* Header */}
        <motion.header
          initial={{ opacity: 0, y: -16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="text-center mb-12"
        >
          <span className="inline-flex items-center gap-2 text-xs font-body uppercase tracking-[0.18em] text-orange-700 border border-orange-400/40 bg-orange-50 rounded-full px-4 py-1.5 mb-5">
            <HelpCircle className="w-3.5 h-3.5" />
            FAQ
          </span>
          <h1 className="font-display text-4xl sm:text-5xl md:text-6xl font-bold text-stone-800 mb-4">
            Frequently Asked Questions
          </h1>
          <p className="font-body text-base sm:text-lg text-stone-600 max-w-2xl mx-auto leading-relaxed">
            What EleutherIA is, what it contains, how its citation-grounded GraphRAG
            works, and answers to common questions about ancient debates on free will,
            fate, and moral responsibility.
          </p>
        </motion.header>

        {/* Quick jump index */}
        <nav aria-label="Questions" className="mb-12">
          <ul className="space-y-1.5">
            {FAQ_ENTRIES.map((entry: FaqEntry) => (
              <li key={entry.question}>
                <a
                  href={`#${faqAnchor(entry.question)}`}
                  className="text-sm font-body text-stone-600 hover:text-orange-700 transition-colors"
                >
                  {entry.question}
                </a>
              </li>
            ))}
          </ul>
        </nav>

        {/* Answers */}
        <div className="space-y-5">
          {FAQ_ENTRIES.map((entry: FaqEntry, index: number) => (
            <motion.section
              key={entry.question}
              id={faqAnchor(entry.question)}
              initial={{ opacity: 0, y: 14 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-60px' }}
              transition={{ duration: 0.4, delay: Math.min(index * 0.03, 0.18) }}
              aria-labelledby={`${faqAnchor(entry.question)}-q`}
              className="scroll-mt-28 bg-parchment-100/60 backdrop-blur-sm rounded-2xl border border-parchment-300/50 p-5 sm:p-7 shadow-sm"
            >
              <h2
                id={`${faqAnchor(entry.question)}-q`}
                className="font-display text-xl sm:text-2xl font-bold text-stone-800 leading-snug mb-3"
              >
                {entry.question}
              </h2>
              <p className="font-body text-base text-stone-700 leading-relaxed">
                {entry.answer}
              </p>
            </motion.section>
          ))}
        </div>

        {/* Footer CTA */}
        <div className="mt-16 text-center">
          <Link
            to="/graphrag"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-orange-800 hover:bg-orange-900 text-white font-body font-medium text-sm transition-colors"
          >
            Ask your own question
            <ArrowRight className="w-4 h-4" aria-hidden="true" />
          </Link>
        </div>
      </div>
    </div>
  );
}
