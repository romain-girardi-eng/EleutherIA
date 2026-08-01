import { useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ArrowLeft,
  GitBranch,
  Layers,
  Network,
  Scroll,
  TrendingUp,
} from 'lucide-react';

import ConceptEvolutionTimeline from '../components/ConceptEvolutionTimeline';
import ArgumentMapper from '../components/ArgumentMapper';
import {
  useDebateSubgraph,
  useDebateAdapters,
  DEBATE_RELATIONS,
} from '../components/debate-map/useDebateSubgraph';

/**
 * DebateMapPage — interactive 12-century argument map for a single concept.
 *
 * Intended route (wired by the integrator in App.tsx):
 *   <Route path="/debate/:conceptId" element={<DebateMapPage />} />
 *
 * Seed-friendly with concept ids such as the autexousion / eph-hemin nodes,
 * e.g. /debate/concept_autexousion or /debate/concept_eph_hemin.
 *
 * It fetches the concept node and its argues_for / responds_to / precedes /
 * critiques subgraph from the live KG, then drives two already-built (but
 * previously unrouted) components against real data:
 *   - ConceptEvolutionTimeline (chronological formulations across centuries)
 *   - ArgumentMapper (premise → conclusion + objections + responses per argument)
 */

type View = 'timeline' | 'arguments';

const RELATION_LEGEND: ReadonlyArray<{ key: (typeof DEBATE_RELATIONS)[number]; label: string; dot: string }> = [
  { key: 'argues_for', label: 'argues for', dot: 'bg-green-500' },
  { key: 'responds_to', label: 'responds to', dot: 'bg-blue-500' },
  { key: 'critiques', label: 'critiques', dot: 'bg-red-500' },
  { key: 'precedes', label: 'precedes', dot: 'bg-amber-500' },
];

function PageSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="h-40 rounded-2xl bg-stone-200/50" />
      <div className="h-72 rounded-2xl bg-stone-100" />
      <div className="h-72 rounded-2xl bg-stone-100" />
    </div>
  );
}

export default function DebateMapPage() {
  const { conceptId } = useParams<{ conceptId: string }>();
  const { data, loading, error } = useDebateSubgraph(conceptId);
  const { evolution, arguments: argumentMaps } = useDebateAdapters(data);

  const [view, setView] = useState<View>('timeline');

  const counts = useMemo(() => {
    if (!data) return { nodes: 0, edges: 0, arguments: 0 };
    return {
      nodes: data.related.length + 1,
      edges: data.edges.length,
      arguments: argumentMaps.length,
    };
  }, [data, argumentMaps]);

  return (
    <div className="min-h-screen w-full pt-28 pb-16 bg-transparent">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        {/* Back link */}
        <Link
          to="/visualizer"
          className="inline-flex items-center gap-2 text-sm font-medium text-primary-700 hover:text-primary-900 transition-colors mb-6"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to the graph
        </Link>

        {loading && <PageSkeleton />}

        {!loading && error && (
          <div className="rounded-2xl border border-amber-300/50 bg-white/80 p-8 text-center shadow-sm">
            <Network className="w-10 h-10 mx-auto text-amber-500 mb-3" />
            <h1 className="text-xl font-display font-bold text-stone-800 mb-2">
              Could not load this debate
            </h1>
            <p className="text-stone-600">{error}</p>
            <p className="text-sm text-stone-500 mt-2 italic">
              Concept id: <code className="font-mono">{conceptId}</code>
            </p>
          </div>
        )}

        {!loading && data && evolution && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="space-y-8"
          >
            {/* ── Hero header ── */}
            <header className="rounded-2xl bg-gradient-to-br from-primary-700 via-primary-600 to-primary-800 text-white p-5 sm:p-8 shadow-xl">
              <div className="flex items-start gap-4">
                <div className="p-3 bg-white/15 rounded-xl">
                  <Scroll className="w-8 h-8" />
                </div>
                <div className="flex-1">
                  <p className="uppercase tracking-widest text-xs text-white/70 mb-1">
                    Argument map · {data.span.centuries} centuries
                  </p>
                  <h1 className="text-3xl md:text-4xl font-display font-bold mb-2">
                    {data.concept.label}
                    {data.concept.greek_term && (
                      <span className="ml-3 text-2xl text-white/80 font-serif italic">
                        {data.concept.greek_term}
                      </span>
                    )}
                  </h1>
                  {data.concept.description && (
                    <p className="text-white/85 max-w-3xl leading-relaxed">
                      {data.concept.description.length > 280
                        ? `${data.concept.description.slice(0, 279).trimEnd()}…`
                        : data.concept.description}
                    </p>
                  )}
                  <div className="mt-4 flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-white/85">
                    <span className="inline-flex items-center gap-2">
                      <Layers className="w-4 h-4" /> {counts.nodes} nodes
                    </span>
                    <span className="inline-flex items-center gap-2">
                      <GitBranch className="w-4 h-4" /> {counts.edges} relations
                    </span>
                    <span className="inline-flex items-center gap-2">
                      <TrendingUp className="w-4 h-4" /> {data.span.earliest} → {data.span.latest}
                    </span>
                  </div>
                </div>
              </div>

              {/* Relation legend */}
              <div className="mt-6 flex flex-wrap gap-4 border-t border-white/15 pt-4">
                {RELATION_LEGEND.map((r) => (
                  <span key={r.key} className="inline-flex items-center gap-2 text-sm text-white/85">
                    <span className={`w-3 h-3 rounded-full ${r.dot}`} />
                    {r.label}
                  </span>
                ))}
              </div>
            </header>

            {/* ── View toggle ── */}
            <div className="flex items-center gap-2 rounded-full bg-white/70 border border-stone-200 p-1 w-fit shadow-sm">
              <button
                type="button"
                onClick={() => setView('timeline')}
                className={`inline-flex items-center gap-2 min-h-11 px-5 py-2 rounded-full text-sm font-medium transition-colors ${
                  view === 'timeline'
                    ? 'bg-primary-600 text-white shadow'
                    : 'text-stone-600 hover:text-stone-900'
                }`}
              >
                <TrendingUp className="w-4 h-4" />
                Evolution
              </button>
              <button
                type="button"
                onClick={() => setView('arguments')}
                className={`inline-flex items-center gap-2 min-h-11 px-5 py-2 rounded-full text-sm font-medium transition-colors ${
                  view === 'arguments'
                    ? 'bg-primary-600 text-white shadow'
                    : 'text-stone-600 hover:text-stone-900'
                }`}
              >
                <GitBranch className="w-4 h-4" />
                Arguments ({counts.arguments})
              </button>
            </div>

            {/* ── Content ── */}
            <AnimatePresence mode="wait">
              {view === 'timeline' ? (
                <motion.section
                  key="timeline"
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.25 }}
                >
                  {evolution.timeline.length > 0 ? (
                    <ConceptEvolutionTimeline evolution={evolution} />
                  ) : (
                    <EmptyState message="No dated formulations were found for this concept yet." />
                  )}
                </motion.section>
              ) : (
                <motion.section
                  key="arguments"
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.25 }}
                  className="space-y-10"
                >
                  {argumentMaps.length > 0 ? (
                    argumentMaps.map((mapping) => (
                      <ArgumentMapper key={mapping.id} argument={mapping} />
                    ))
                  ) : (
                    <EmptyState message="No arguments are attached to this concept via argues_for yet." />
                  )}
                </motion.section>
              )}
            </AnimatePresence>
          </motion.div>
        )}
      </div>
    </div>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="rounded-2xl border border-dashed border-stone-300 bg-white/60 p-10 text-center">
      <Network className="w-8 h-8 mx-auto text-stone-400 mb-3" />
      <p className="text-stone-600">{message}</p>
    </div>
  );
}
