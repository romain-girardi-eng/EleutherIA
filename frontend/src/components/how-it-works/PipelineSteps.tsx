import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Network, BookOpen, Layers, Sparkles, ChevronRight } from 'lucide-react';
import { cn } from '../../utils/cn';

interface PipelineStep {
  number: number;
  title: string;
  subtitle: string;
  detail: string;
  icon: React.ReactNode;
  input: string;
  output: string;
}

const STEPS: PipelineStep[] = [
  {
    number: 1,
    title: 'Semantic Search',
    subtitle: 'Query → Top-k KG nodes',
    detail:
      'Your question is embedded into a 3,072-dimensional vector by Gemini. Qdrant returns the 10 most semantically similar Knowledge Graph nodes — not keyword matches, but conceptual proximity.',
    icon: <Search className="w-5 h-5" />,
    input: '"What did Stoics say about fate?"',
    output: 'Stoicism (0.89) · Fate (0.87) · Chrysippus (0.84) …',
  },
  {
    number: 2,
    title: 'Graph Traversal',
    subtitle: 'BFS from seed nodes',
    detail:
      "Starting from the 10 seed nodes, the engine follows KG edges — \"formulated\", \"opposes\", \"influenced\" — up to depth 2, expanding context to 25–50 related nodes without losing scholarly precision.",
    icon: <Network className="w-5 h-5" />,
    input: 'Seed: Stoicism, Fate, Chrysippus',
    output: '+Determinism  +Epictetus  +Compatibilism  +De Fato …',
  },
  {
    number: 3,
    title: 'Citation Extraction',
    subtitle: 'Gather ancient + modern sources',
    detail:
      'Each expanded node carries curated "ancient_sources" and "modern_scholarship" fields. These are extracted, deduplicated, and ranked by relevance — producing a tight bibliography with confidence scores.',
    icon: <BookOpen className="w-5 h-5" />,
    input: '25 expanded KG nodes',
    output: '10 ancient sources + 12 modern citations',
  },
  {
    number: 4,
    title: 'Context Building',
    subtitle: 'LOCAL · GLOBAL · BRIDGE',
    detail:
      'Context is organised into three levels: LOCAL (direct answers from immediate nodes), GLOBAL (community-level summaries), and BRIDGE (reasoning paths connecting distant concepts). ~3,000 chars, highly structured.',
    icon: <Layers className="w-5 h-5" />,
    input: 'Raw nodes + deduplicated citations',
    output: '~3,000 chars of structured, tiered context',
  },
  {
    number: 5,
    title: 'LLM Synthesis',
    subtitle: 'Gemini · Kimi K2.5 Thinking',
    detail:
      'Gemini 3 (or Kimi for extended reasoning) reads the context and writes a scholarly answer with inline [n] citations. Hard constraints: never fabricate Greek/Latin, always cite primary sources.',
    icon: <Sparkles className="w-5 h-5" />,
    input: 'Structured context + original question',
    output: 'Cited scholarly answer with [1] [2] [3] references',
  },
];

interface PipelineStepsProps {
  className?: string;
  /** Auto-advance interval in ms; 0 = manual only */
  autoPlay?: number;
  /** 'dark' (for dark bg) | 'light' (for light bg) */
  theme?: 'dark' | 'light';
}

export function PipelineSteps({ className, autoPlay = 0, theme = 'dark' }: PipelineStepsProps) {
  const [active, setActive] = useState(0);
  const [playing, setPlaying] = useState(autoPlay > 0);

  useEffect(() => {
    if (!playing || autoPlay === 0) return;
    const t = setInterval(() => setActive((p) => (p + 1) % STEPS.length), autoPlay);
    return () => clearInterval(t);
  }, [playing, autoPlay]);

  const step = STEPS[active];

  const trackBg = theme === 'dark' ? 'bg-white/10' : 'bg-stone-200';
  const trackFill = 'bg-orange-500';
  const circleBase = theme === 'dark' ? 'bg-white/10 text-white/50 border-white/15' : 'bg-stone-100 text-stone-400 border-stone-200';
  const circleActive = 'bg-orange-500 text-white border-orange-400 shadow-[0_0_16px_rgba(249,115,22,0.5)]';
  const circleDone = theme === 'dark' ? 'bg-white/20 text-white/80 border-white/20' : 'bg-stone-300 text-stone-700 border-stone-300';
  const titleColor = theme === 'dark' ? 'text-white' : 'text-stone-800';
  const subtitleColor = theme === 'dark' ? 'text-white/50' : 'text-stone-500';
  const panelBg = theme === 'dark' ? 'bg-white/6 border-white/12' : 'bg-parchment-50 border-parchment-300/60';
  const monoPanel = theme === 'dark' ? 'bg-zinc-950 text-green-400' : 'bg-stone-900 text-green-400';
  const labelColor = theme === 'dark' ? 'text-white/40' : 'text-stone-400';

  return (
    <div className={cn('w-full', className)}>
      {/* Progress bar + step buttons */}
      <div className="relative mb-8">
        {/* Track */}
        <div className={cn('absolute top-6 left-0 right-0 h-0.5', trackBg)}>
          <motion.div
            className={cn('h-full', trackFill)}
            initial={{ width: '0%' }}
            animate={{ width: `${((active) / (STEPS.length - 1)) * 100}%` }}
            transition={{ duration: 0.4 }}
          />
        </div>

        {/* Step circles */}
        <div className="relative flex justify-between">
          {STEPS.map((s, i) => {
            const state = i === active ? 'active' : i < active ? 'done' : 'idle';
            return (
              <button
                key={s.number}
                onClick={() => { setActive(i); setPlaying(false); }}
                className="flex flex-col items-center gap-2 group"
              >
                <div
                  className={cn(
                    'w-12 h-12 rounded-full border-2 flex items-center justify-center',
                    'transition-all duration-300',
                    state === 'active' ? circleActive : state === 'done' ? circleDone : circleBase,
                  )}
                >
                  {s.icon}
                </div>
                <span className={cn('text-xs font-body hidden sm:block text-center max-w-[72px] leading-tight', state === 'active' ? 'text-orange-400' : subtitleColor)}>
                  {s.title}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Detail panel */}
      <AnimatePresence mode="wait">
        <motion.div
          key={active}
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -16 }}
          transition={{ duration: 0.3 }}
          className={cn('rounded-2xl border p-8', panelBg)}
        >
          <div className="grid md:grid-cols-2 gap-8">
            {/* Description */}
            <div>
              <div className="flex items-center gap-3 mb-4">
                <span className="w-9 h-9 rounded-full bg-orange-500 text-white text-sm font-body font-semibold flex items-center justify-center flex-shrink-0">
                  {step.number}
                </span>
                <div>
                  <h3 className={cn('font-display text-xl', titleColor)}>
                    {step.title}
                  </h3>
                  <p className={cn('text-sm font-body', subtitleColor)}>{step.subtitle}</p>
                </div>
              </div>
              <p className={cn('font-body text-sm leading-relaxed', theme === 'dark' ? 'text-white/70' : 'text-stone-600')}>
                {step.detail}
              </p>

              {/* Nav buttons */}
              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => { setActive((p) => Math.max(0, p - 1)); setPlaying(false); }}
                  disabled={active === 0}
                  className="px-4 py-2 text-xs font-body rounded-lg border border-orange-500/40 text-orange-400 hover:bg-orange-500/10 disabled:opacity-30 transition-colors"
                >
                  ← Previous
                </button>
                <button
                  onClick={() => { setActive((p) => Math.min(STEPS.length - 1, p + 1)); setPlaying(false); }}
                  disabled={active === STEPS.length - 1}
                  className="px-4 py-2 text-xs font-body rounded-lg bg-orange-500 text-white hover:bg-orange-600 disabled:opacity-30 transition-colors flex items-center gap-1"
                >
                  Next <ChevronRight className="w-3 h-3" />
                </button>
              </div>
            </div>

            {/* Input / Output */}
            <div className="space-y-4">
              <div>
                <p className={cn('text-xs font-body uppercase tracking-widest mb-2', labelColor)}>
                  Input
                </p>
                <div className={cn('rounded-xl p-4 font-mono text-sm', monoPanel)}>
                  {step.input}
                </div>
              </div>
              <div className="flex justify-center">
                <ChevronRight className={cn('w-5 h-5 rotate-90', theme === 'dark' ? 'text-white/30' : 'text-stone-400')} />
              </div>
              <div>
                <p className={cn('text-xs font-body uppercase tracking-widest mb-2', labelColor)}>
                  Output
                </p>
                <div className={cn('rounded-xl p-4 font-mono text-sm', monoPanel)}>
                  {step.output}
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </AnimatePresence>

      {/* Auto-play toggle */}
      {autoPlay > 0 && (
        <button
          onClick={() => setPlaying((p) => !p)}
          className={cn('mt-4 text-xs font-body px-3 py-1.5 rounded-lg border transition-colors', theme === 'dark' ? 'border-white/20 text-white/50 hover:text-white/80 hover:border-white/40' : 'border-stone-300 text-stone-500 hover:text-stone-700')}
        >
          {playing ? '⏸ Pause' : '▶ Auto-play'}
        </button>
      )}
    </div>
  );
}
