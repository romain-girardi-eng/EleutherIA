/**
 * GlossaryPage — a grounded glossary of core terms in the ancient free-will,
 * fate, and moral-responsibility debate.
 *
 * Every entry is rendered from the shared, JSON-backed content module
 * (`src/content/glossary.ts` → `glossary.json`), which is the single source of
 * truth imported here AND by the SEO prerenderer so the definitions appear in the
 * prerendered static HTML.
 *
 * Integrity: all Greek/Latin (`originalTerm`, inline forms) is copied verbatim
 * from the knowledge-graph concept nodes; nothing is generated or translated.
 */

import { useMemo } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Network, BookOpen, ArrowRight } from 'lucide-react';
import { glossary } from '../content/glossary';
import type { GlossaryEntry } from '../content/glossary';

/** Stable anchor id for an entry, derived from its KG node id. */
const anchorFor = (entry: GlossaryEntry): string => `term-${entry.id}`;

export default function GlossaryPage() {
  // Group entries by historical period for a light scholarly ordering while
  // preserving the alphabetical sort baked into the data.
  const periods = useMemo(() => {
    const order = new Map<string, GlossaryEntry[]>();
    for (const entry of glossary) {
      const key = entry.period ?? 'Other';
      const bucket = order.get(key);
      if (bucket) bucket.push(entry);
      else order.set(key, [entry]);
    }
    return Array.from(order.keys()).sort((a, b) => a.localeCompare(b, 'en'));
  }, []);

  return (
    <div className="min-h-screen w-full pt-28 pb-20 bg-transparent">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">

        {/* Header */}
        <motion.header
          initial={{ opacity: 0, y: -16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="text-center mb-12"
        >
          <span className="inline-flex items-center gap-2 text-xs font-body uppercase tracking-[0.18em] text-orange-700 border border-orange-400/40 bg-orange-50 rounded-full px-4 py-1.5 mb-5">
            <BookOpen className="w-3.5 h-3.5" />
            Glossary
          </span>
          <h1 className="font-display text-4xl sm:text-5xl md:text-6xl font-bold text-stone-800 mb-4">
            Key Terms in the Ancient Free-Will Debate
          </h1>
          <p className="font-body text-base sm:text-lg text-stone-600 max-w-2xl mx-auto leading-relaxed">
            A grounded reference to the Greek and Latin concepts of fate, necessity,
            voluntary action, assent, and free will — each definition condensed from a
            concept node in the EleutherIA knowledge graph. Greek and Latin forms are
            quoted verbatim from the sources, never generated.
          </p>
        </motion.header>

        {/* Quick jump index */}
        <nav aria-label="Glossary terms" className="mb-12">
          <ul className="flex flex-wrap gap-2 justify-center">
            {glossary.map((entry) => (
              <li key={entry.id}>
                <a
                  href={`#${anchorFor(entry)}`}
                  className="inline-block text-xs font-body text-stone-600 hover:text-orange-700 border border-parchment-300/70 bg-white/60 hover:bg-orange-50 rounded-full px-3 py-1 transition-colors"
                >
                  {entry.term}
                </a>
              </li>
            ))}
          </ul>
        </nav>

        {/* Definitions, grouped by period */}
        <div className="space-y-12">
          {periods.map((period) => (
            <section key={period} aria-labelledby={`period-${period.replace(/\s+/g, '-')}`}>
              <h2
                id={`period-${period.replace(/\s+/g, '-')}`}
                className="font-body text-xs font-semibold uppercase tracking-[0.16em] text-orange-700/80 border-b border-parchment-300/60 pb-2 mb-6"
              >
                {period}
              </h2>
              <dl className="space-y-6">
                {glossary
                  .filter((entry) => (entry.period ?? 'Other') === period)
                  .map((entry, index) => (
                    <motion.div
                      key={entry.id}
                      id={anchorFor(entry)}
                      initial={{ opacity: 0, y: 14 }}
                      whileInView={{ opacity: 1, y: 0 }}
                      viewport={{ once: true, margin: '-60px' }}
                      transition={{ duration: 0.4, delay: Math.min(index * 0.04, 0.2) }}
                      className="scroll-mt-28 bg-parchment-100/60 backdrop-blur-sm rounded-2xl border border-parchment-300/50 p-5 sm:p-7 shadow-sm"
                    >
                      <dt className="mb-3">
                        <h3 className="font-display text-2xl sm:text-3xl font-bold text-stone-800 leading-tight">
                          {entry.term}
                        </h3>
                        {entry.originalTerm && (
                          <p
                            lang={/[A-Za-z]/.test(entry.originalTerm) ? 'la' : 'grc'}
                            className="font-display text-xl text-orange-700 mt-1"
                          >
                            {entry.originalTerm}
                          </p>
                        )}
                        {entry.school && (
                          <span className="inline-block mt-2 text-xs font-body uppercase tracking-wide text-stone-500 bg-white/70 border border-parchment-300/60 rounded-full px-2.5 py-0.5">
                            {entry.school}
                          </span>
                        )}
                      </dt>
                      <dd className="m-0">
                        <p className="font-body text-base text-stone-700 leading-relaxed">
                          {entry.definition}
                        </p>
                        <Link
                          to={entry.nodeUrl}
                          className="inline-flex items-center gap-1.5 mt-4 text-sm font-body font-medium text-orange-700 hover:text-orange-900 transition-colors"
                        >
                          <Network className="w-4 h-4" aria-hidden="true" />
                          View in graph
                          <ArrowRight className="w-3.5 h-3.5" aria-hidden="true" />
                        </Link>
                      </dd>
                    </motion.div>
                  ))}
              </dl>
            </section>
          ))}
        </div>

        {/* Footer CTA */}
        <div className="mt-16 text-center">
          <Link
            to="/graphrag"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-orange-800 hover:bg-orange-900 text-white font-body font-medium text-sm transition-colors"
          >
            Ask a research question
            <ArrowRight className="w-4 h-4" aria-hidden="true" />
          </Link>
        </div>
      </div>
    </div>
  );
}
