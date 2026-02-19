/**
 * HowItWorksPage — scroll-snap educational landing page
 *
 * Sections:
 *   1. Hero          — dark, particles, title, scroll hint
 *   2. The Problem   — parchment, compare cards, key stats
 *   3. Knowledge Graph — white, KG diagram, node types
 *   4. GraphRAG Pipeline — dark, 5-stage interactive pipeline
 *   5. Hybrid Search — parchment, 3 methods + RRF
 *   6. FAIR Data     — warm orange, FAIR badges
 *   7. CTA           — dark, links to explore
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  Network, Search, BookOpen, Brain, Sparkles,
  ChevronRight, GitBranch, Globe, CheckCircle2, Languages,
  ArrowRight, Quote, Users, Target, RotateCcw, Layers,
} from 'lucide-react';

import {
  AuroraStrip,
  BackgroundMesh,
  CompareCards,
  DotNavigator,
  FAIRBadges,
  GitHubPill,
  GlassCard,
  PipelineSteps,
  ScrollHint,
  ScrollSection,
} from '../components/how-it-works';
import type { DotNavSection } from '../components/how-it-works';

import { MorphingParticles } from '../components/MorphingParticles';

// ─── Section definitions ────────────────────────────────────────────────────

const NAV_SECTIONS: DotNavSection[] = [
  { id: 'hero',          label: 'Home' },
  { id: 'problem',       label: 'The Problem' },
  { id: 'kg',            label: 'Knowledge Graph' },
  { id: 'pipeline',      label: 'GraphRAG Pipeline' },
  { id: 'search',        label: 'Hybrid Search' },
  { id: 'fair',          label: 'FAIR Data' },
  { id: 'cta',           label: 'Start Exploring' },
];

// ─── Main Page ───────────────────────────────────────────────────────────────

export default function HowItWorksPage() {
  const [activeId, setActiveId] = useState('hero');
  const containerRef = useRef<HTMLDivElement>(null);

  // Intersection observer for nav sync
  useEffect(() => {
    const opts: IntersectionObserverInit = {
      root: containerRef.current,
      threshold: 0.5,
    };
    const observer = new IntersectionObserver((entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          setActiveId(entry.target.id);
        }
      }
    }, opts);

    NAV_SECTIONS.forEach(({ id }) => {
      const el = document.getElementById(id);
      if (el) observer.observe(el);
    });
    return () => observer.disconnect();
  }, []);

  const scrollTo = useCallback((id: string) => {
    const el = document.getElementById(id);
    if (el && containerRef.current) {
      containerRef.current.scrollTo({ top: el.offsetTop, behavior: 'smooth' });
    }
  }, []);

  return (
    <div
      ref={containerRef}
      className="overflow-y-scroll"
      style={{
        scrollSnapType: 'y mandatory',
        scrollBehavior: 'smooth',
        height: 'calc(100vh - 3rem)', /* subtract nav height */
      }}
    >
      {/* Dot navigation — fixed right side */}
      <DotNavigator
        sections={NAV_SECTIONS}
        activeId={activeId}
        onNavigate={scrollTo}
        theme="light"
      />

      {/* ── Section 1: Hero ─────────────────────────────────────────────── */}
      <ScrollSection id="hero" className="bg-zinc-950" noInner>
        {/* Particles background */}
        <div className="absolute inset-0">
          <MorphingParticles
            morphDuration={7}
            rotationSpeed={0.1}
            particleSize={0.45}
            lineOpacity={0.015}
            connectionDistance={14}
            colorScheme="warm"
            enableBloom
            bloomIntensity={0.18}
            enableHover
          />
        </div>

        {/* Subtle dot mesh overlay */}
        <BackgroundMesh variant="dots" color="rgba(255,255,255,1)" opacity={0.03} />

        {/* Dark radial scrim — kills particle bleed behind text */}
        <div
          aria-hidden="true"
          className="absolute inset-0 z-[2] pointer-events-none"
          style={{
            background: 'radial-gradient(ellipse 70% 60% at 50% 50%, rgba(0,0,0,0.72) 0%, rgba(0,0,0,0.3) 60%, transparent 100%)',
          }}
        />

        {/* Hero content */}
        <div className="relative z-10 flex flex-col items-center justify-center min-h-screen px-6 text-center">
          {/* Kicker */}
          <motion.div
            initial={{ opacity: 0, y: -12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="mb-6"
          >
            <span className="inline-flex items-center gap-2 text-xs font-body uppercase tracking-[0.2em] text-orange-400 border border-orange-500/30 bg-orange-500/10 rounded-full px-4 py-1.5">
              <Sparkles className="w-3.5 h-3.5" />
              Open Scholarship · FAIR Data
            </span>
          </motion.div>

          {/* Main title */}
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.35, ease: [0.22, 1, 0.36, 1] }}
            className="font-display text-5xl sm:text-6xl lg:text-7xl xl:text-8xl text-white leading-[1.08] max-w-5xl mx-auto mb-6 drop-shadow-[0_2px_24px_rgba(0,0,0,0.9)]"
          >
            How{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-orange-400 to-amber-300">
              EleutherIA
            </span>
            <br />
            Works
          </motion.h1>

          {/* Subtitle */}
          <motion.p
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.55, ease: [0.22, 1, 0.36, 1] }}
            className="font-body text-lg sm:text-xl text-white/85 max-w-2xl mx-auto mb-12 leading-relaxed drop-shadow-[0_1px_12px_rgba(0,0,0,0.95)]"
          >
            A Knowledge Graph, a hybrid search engine, and a 5-stage GraphRAG pipeline —
            built to make 1,200 years of ancient philosophy searchable and citable.
          </motion.p>

          {/* CTA row */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.7 }}
            className="flex flex-wrap items-center justify-center gap-4 mb-20"
          >
            <Link
              to="/graphrag"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-orange-500 hover:bg-orange-400 text-white font-body font-medium text-sm transition-colors"
            >
              <Sparkles className="w-4 h-4" />
              Try GraphRAG Q&A
            </Link>
            <GitHubPill variant="dark" />
          </motion.div>

          {/* Scroll hint */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.2 }}
            className="absolute bottom-10"
          >
            <ScrollHint theme="light" />
          </motion.div>
        </div>

        {/* Bottom transition strip */}
        <AuroraStrip position="bottom" palette="warm" height="180px" />
      </ScrollSection>

      {/* ── Section 2: The Problem ───────────────────────────────────────── */}
      <ScrollSection
        id="problem"
        className="bg-parchment-100"
      >
        <BackgroundMesh variant="grid" color="rgba(180,120,40,1)" opacity={0.04} />

        <div className="w-full max-w-6xl mx-auto px-4 sm:px-6 py-20">
          {/* Section label */}
          <SectionLabel icon={<BookOpen className="w-4 h-4" />} text="The Research Problem" />

          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
            className="font-display text-4xl sm:text-5xl lg:text-6xl text-stone-800 mb-4 leading-tight"
          >
            Ancient philosophy is{' '}
            <em className="text-orange-600 not-italic">scattered</em>
          </motion.h2>

          <motion.p
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.15 }}
            className="font-body text-lg text-stone-500 mb-12 max-w-2xl"
          >
            Across 189 works, 17,000+ passages, 2,193 philosophers, concepts, and arguments —
            none of it previously connected in a machine-readable graph.
          </motion.p>

          <CompareCards
            before={{
              label: 'Before EleutherIA',
              title: 'Months of manual research to answer a single question',
              items: [
                { text: 'No machine-readable connections between philosophers' },
                { text: 'Keyword search misses Greek synonyms and related concepts' },
                { text: 'Citations scattered across 189 separately-edited works' },
                { text: 'No confidence scores or provenance tracking' },
              ],
              metric: { value: '6–12 weeks', description: 'Estimated research time per question' },
            }}
            after={{
              label: 'With EleutherIA',
              title: 'Seconds — with cited, verifiable, scholarly answers',
              items: [
                { text: '2,193 nodes connected by 8,616 typed relationships' },
                { text: 'Hybrid search: keyword + lemmatic + semantic (RRF merged)' },
                { text: '17,000+ passages with CTS URN citations and confidence scores' },
                { text: 'FAIR-compliant, CC BY 4.0, DOI-minted on Zenodo' },
              ],
              metric: { value: '< 5 seconds', description: 'End-to-end answer time' },
            }}
          />

          {/* Stats row */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-12"
          >
            {[
              { icon: <Network className="w-5 h-5" />, value: '2,193', label: 'KG Nodes' },
              { icon: <GitBranch className="w-5 h-5" />, value: '8,616', label: 'Edges' },
              { icon: <BookOpen className="w-5 h-5" />, value: '189', label: 'Ancient Works' },
              { icon: <Quote className="w-5 h-5" />, value: '17k+', label: 'Passages' },
            ].map((stat) => (
              <div
                key={stat.label}
                className="bg-white/70 border border-parchment-300/60 rounded-xl p-5 text-center"
              >
                <div className="inline-flex items-center justify-center w-10 h-10 rounded-lg bg-orange-100 text-orange-600 mb-3">
                  {stat.icon}
                </div>
                <div className="font-display text-3xl text-stone-800 mb-1">{stat.value}</div>
                <div className="font-body text-xs text-stone-500 uppercase tracking-wider">{stat.label}</div>
              </div>
            ))}
          </motion.div>
        </div>
      </ScrollSection>

      {/* ── Section 3: Knowledge Graph ───────────────────────────────────── */}
      <ScrollSection id="kg" className="bg-white">
        <BackgroundMesh variant="dots" color="rgba(100,100,120,1)" opacity={0.05} />

        <div className="w-full max-w-6xl mx-auto px-4 sm:px-6 py-20">
          <SectionLabel icon={<Network className="w-4 h-4" />} text="Layer 1 — Knowledge Graph" />

          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <div>
              <motion.h2
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
                className="font-display text-4xl sm:text-5xl text-stone-800 mb-5 leading-tight"
              >
                A network of{' '}
                <span className="text-primary-700">1,200 years</span> of debate
              </motion.h2>

              <motion.p
                initial={{ opacity: 0, y: 12 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: 0.15 }}
                className="font-body text-base text-stone-500 mb-8 leading-relaxed"
              >
                From Heraclitus (6th c. BCE) to Boethius (6th c. CE) — every philosopher,
                concept, argument, and work connected by typed relationships: "formulated",
                "opposes", "influenced", "reformulated".
              </motion.p>

              {/* Node type grid */}
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                {[
                  { icon: <Users className="w-4 h-4" />, type: 'Persons',        count: 179, color: 'blue'   },
                  { icon: <Brain className="w-4 h-4" />, type: 'Concepts',        count: 121, color: 'violet' },
                  { icon: <Target className="w-4 h-4" />, type: 'Arguments',      count: 116, color: 'primary'},
                  { icon: <BookOpen className="w-4 h-4" />, type: 'Works',        count:  66, color: 'amber'  },
                  { icon: <RotateCcw className="w-4 h-4" />, type: 'Reformulations', count: 53, color: 'rose'},
                  { icon: <Quote className="w-4 h-4" />, type: 'Quotes',          count:  14, color: 'emerald'},
                ].map((nt) => (
                  <NodeTypeChip key={nt.type} {...nt} />
                ))}
              </div>
            </div>

            {/* Interactive mini-graph */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.7 }}
              className="relative"
            >
              <MiniKGDemo />
            </motion.div>
          </div>

          {/* Dual-layer callout */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="mt-12 grid sm:grid-cols-2 gap-5"
          >
            <GlassCard variant="parchment" padding="lg">
              <p className="text-xs font-body uppercase tracking-widest text-orange-600 mb-2">Primary Layer</p>
              <h4 className="font-display text-xl text-stone-800 mb-2">Ancient Sources</h4>
              <p className="font-body text-sm text-stone-600">
                Philosophers, concepts, arguments, and texts from 6th c. BCE – 6th c. CE,
                linked to verifiable CTS URN passages.
              </p>
            </GlassCard>
            <GlassCard variant="parchment" padding="lg">
              <p className="text-xs font-body uppercase tracking-widest text-primary-600 mb-2">Secondary Layer</p>
              <h4 className="font-display text-xl text-stone-800 mb-2">Modern Reception</h4>
              <p className="font-body text-sm text-stone-600">
                Contemporary scholars — Bobzien, Frede, Kane — and their interpretative
                frameworks mapped onto the primary layer.
              </p>
            </GlassCard>
          </motion.div>
        </div>
      </ScrollSection>

      {/* ── Section 4: GraphRAG Pipeline ─────────────────────────────────── */}
      <ScrollSection id="pipeline" className="bg-zinc-950">
        <BackgroundMesh variant="dots" color="rgba(255,255,255,1)" opacity={0.025} />

        <div className="w-full max-w-6xl mx-auto px-4 sm:px-6 py-20">
          <SectionLabel
            icon={<Sparkles className="w-4 h-4" />}
            text="Layer 3 — GraphRAG Q&A"
            theme="dark"
          />

          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
            className="font-display text-4xl sm:text-5xl text-white mb-4 leading-tight"
          >
            Five stages from{' '}
            <span className="text-orange-400">question</span> to{' '}
            <span className="text-orange-400">cited answer</span>
          </motion.h2>

          <motion.p
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.15 }}
            className="font-body text-base text-white/50 mb-12 max-w-2xl"
          >
            No hallucinations, no fabricated Greek text. Every answer is grounded in the
            knowledge graph and linked back to primary sources with confidence scores.
          </motion.p>

          <PipelineSteps theme="dark" autoPlay={5000} />
        </div>
      </ScrollSection>

      {/* ── Section 5: Hybrid Search ─────────────────────────────────────── */}
      <ScrollSection id="search" className="bg-parchment-50">
        <BackgroundMesh variant="crosses" color="rgba(160,100,30,1)" opacity={0.04} />

        <div className="w-full max-w-6xl mx-auto px-4 sm:px-6 py-20">
          <SectionLabel icon={<Search className="w-4 h-4" />} text="Layer 2 — Hybrid Search" />

          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
            className="font-display text-4xl sm:text-5xl text-stone-800 mb-4 leading-tight"
          >
            Three search engines,{' '}
            <span className="text-orange-600">one result</span>
          </motion.h2>

          <motion.p
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.15 }}
            className="font-body text-base text-stone-500 mb-12 max-w-2xl"
          >
            Full-text, lemmatic, and semantic searches run in parallel. Results are merged
            by Reciprocal Rank Fusion — items appearing in multiple lists score highest.
          </motion.p>

          {/* Method cards */}
          <div className="grid md:grid-cols-3 gap-5 mb-12">
            {[
              {
                icon: <Search className="w-5 h-5" />,
                title: 'Full-Text',
                speed: '< 100 ms',
                color: 'bg-blue-50 border-blue-200',
                iconColor: 'bg-blue-100 text-blue-600',
                desc: 'PostgreSQL tsvector + ts_rank. Exact keyword matches in 17k passages.',
                example: '"free will" → exact matches',
              },
              {
                icon: <Languages className="w-5 h-5" />,
                title: 'Lemmatic',
                speed: '< 500 ms',
                color: 'bg-violet-50 border-violet-200',
                iconColor: 'bg-violet-100 text-violet-600',
                desc: 'Pre-indexed Greek & Latin lemmas. Finds all morphological forms of a word.',
                example: 'λόγος → λόγου λόγῳ λόγον …',
              },
              {
                icon: <Brain className="w-5 h-5" />,
                title: 'Semantic',
                speed: '< 2 s',
                color: 'bg-amber-50 border-amber-200',
                iconColor: 'bg-amber-100 text-amber-700',
                desc: 'Gemini embeddings → Qdrant ANN search. Finds conceptual similarity across languages.',
                example: '"free will" → ἐφ\' ἡμῖν · liberum arbitrium',
              },
            ].map((m) => (
              <motion.div
                key={m.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
              >
                <div className={`rounded-2xl border p-6 h-full flex flex-col ${m.color}`}>
                  <div className={`inline-flex items-center justify-center w-10 h-10 rounded-lg mb-4 ${m.iconColor}`}>
                    {m.icon}
                  </div>
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-display text-xl text-stone-800">{m.title}</h4>
                    <span className="text-xs font-mono text-stone-400 bg-white/60 px-2 py-0.5 rounded-full border border-stone-200">
                      {m.speed}
                    </span>
                  </div>
                  <p className="font-body text-sm text-stone-600 mb-4 flex-1">{m.desc}</p>
                  <div className="mt-auto p-3 bg-white/50 rounded-xl font-mono text-xs text-stone-500 border border-stone-200/60">
                    {m.example}
                  </div>
                </div>
              </motion.div>
            ))}
          </div>

          {/* RRF formula */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.1 }}
          >
            <GlassCard variant="parchment" padding="lg">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <h4 className="font-display text-2xl text-stone-800 mb-2">
                    Reciprocal Rank Fusion
                  </h4>
                  <p className="font-body text-sm text-stone-500 max-w-sm">
                    Items found by all three engines rank highest. The formula penalises lower ranks
                    while rewarding cross-list agreement.
                  </p>
                </div>
                <div className="font-mono text-sm text-stone-700 bg-white/70 border border-parchment-300 rounded-xl px-6 py-4 whitespace-nowrap">
                  RRF(d) = Σ{' '}
                  <span className="text-orange-600 font-semibold">1 / (k + rank)</span>
                  {' '}· k = 60
                </div>
              </div>
            </GlassCard>
          </motion.div>
        </div>
      </ScrollSection>

      {/* ── Section 6: FAIR ───────────────────────────────────────────────── */}
      <ScrollSection id="fair" className="bg-amber-50">
        <BackgroundMesh variant="dots" color="rgba(200,130,20,1)" opacity={0.06} />

        <div className="w-full max-w-6xl mx-auto px-4 sm:px-6 py-20">
          <SectionLabel
            icon={<CheckCircle2 className="w-4 h-4" />}
            text="Open Scholarship"
            variant="amber"
          />

          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
            className="font-display text-4xl sm:text-5xl text-stone-800 mb-4 leading-tight"
          >
            FAIR-compliant from the{' '}
            <span className="text-amber-700">ground up</span>
          </motion.h2>

          <motion.p
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.15 }}
            className="font-body text-base text-stone-500 mb-12 max-w-2xl"
          >
            Findable, Accessible, Interoperable, Reusable — the international principles for
            scientific data management — are baked into every layer of the architecture.
          </motion.p>

          <FAIRBadges variant="light" />

          {/* Links row */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="flex flex-wrap gap-3 mt-10"
          >
            <a
              href="https://doi.org/10.5281/zenodo.17379490"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-amber-400/50 bg-amber-100/60 text-amber-800 text-sm font-body font-medium hover:bg-amber-200/60 transition-colors"
            >
              <Globe className="w-4 h-4" />
              DOI: 10.5281/zenodo.17379490
            </a>
            <GitHubPill variant="light" />
            <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-stone-300 bg-white/60 text-stone-600 text-sm font-body">
              CC BY 4.0
            </span>
          </motion.div>
        </div>
      </ScrollSection>

      {/* ── Section 7: CTA ────────────────────────────────────────────────── */}
      <ScrollSection id="cta" className="bg-zinc-950">
        <BackgroundMesh variant="dots" color="rgba(255,255,255,1)" opacity={0.025} />

        <div className="relative z-10 flex flex-col items-center justify-center min-h-screen px-6 text-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
          >
            <span className="inline-flex items-center gap-2 text-xs font-body uppercase tracking-[0.2em] text-orange-400 border border-orange-500/30 bg-orange-500/10 rounded-full px-4 py-1.5 mb-8">
              <Sparkles className="w-3.5 h-3.5" />
              Start Exploring
            </span>

            <h2 className="font-display text-5xl sm:text-6xl lg:text-7xl text-white mb-6 leading-tight max-w-4xl">
              1,200 years of thought,{' '}
              <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-orange-400 to-amber-300">
                one search away
              </span>
            </h2>

            <p className="font-body text-lg text-white/50 max-w-xl mx-auto mb-12">
              Ask a question about free will, fate, or moral responsibility in ancient
              philosophy — and receive a cited, scholarly answer in seconds.
            </p>

            {/* CTA buttons */}
            <div className="flex flex-wrap justify-center gap-4 mb-16">
              <Link
                to="/graphrag"
                className="inline-flex items-center gap-2 px-7 py-3.5 rounded-full bg-orange-500 hover:bg-orange-400 text-white font-body font-semibold transition-colors"
              >
                <Sparkles className="w-4 h-4" />
                Ask a question
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                to="/visualizer"
                className="inline-flex items-center gap-2 px-7 py-3.5 rounded-full border border-white/20 bg-white/8 hover:bg-white/15 text-white font-body font-medium transition-colors"
              >
                <Network className="w-4 h-4" />
                Explore the graph
              </Link>
              <Link
                to="/search"
                className="inline-flex items-center gap-2 px-7 py-3.5 rounded-full border border-white/20 bg-white/8 hover:bg-white/15 text-white font-body font-medium transition-colors"
              >
                <Search className="w-4 h-4" />
                Search passages
              </Link>
            </div>

            {/* Feature row */}
            <div className="flex flex-wrap justify-center gap-6 text-sm font-body">
              {[
                { icon: <CheckCircle2 className="w-4 h-4 text-emerald-400" />, text: 'Free & open access' },
                { icon: <CheckCircle2 className="w-4 h-4 text-emerald-400" />, text: 'No login required' },
                { icon: <CheckCircle2 className="w-4 h-4 text-emerald-400" />, text: 'All citations verifiable' },
                { icon: <CheckCircle2 className="w-4 h-4 text-emerald-400" />, text: 'CC BY 4.0' },
              ].map((f) => (
                <div key={f.text} className="flex items-center gap-2 text-white/50">
                  {f.icon}
                  <span>{f.text}</span>
                </div>
              ))}
            </div>

            {/* Bottom links */}
            <div className="mt-10 flex flex-wrap justify-center gap-3">
              <GitHubPill variant="dark" />
              <Link
                to="/about"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-white/15 text-white/50 hover:text-white/80 text-sm font-body transition-colors"
              >
                <Layers className="w-4 h-4" />
                About the project
              </Link>
            </div>
          </motion.div>
        </div>
      </ScrollSection>
    </div>
  );
}

// ─── Small helper components ─────────────────────────────────────────────────

function SectionLabel({
  icon,
  text,
  theme = 'light',
  variant,
}: {
  icon: React.ReactNode;
  text: string;
  theme?: 'light' | 'dark';
  variant?: 'amber';
}) {
  const base =
    variant === 'amber'
      ? 'text-amber-700 border-amber-400/50 bg-amber-100/60'
      : theme === 'dark'
        ? 'text-orange-400 border-orange-500/30 bg-orange-500/10'
        : 'text-orange-600 border-orange-400/40 bg-orange-50';

  return (
    <motion.div
      initial={{ opacity: 0, y: -8 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5 }}
      className="mb-5"
    >
      <span
        className={`inline-flex items-center gap-2 text-xs font-body uppercase tracking-[0.18em] border rounded-full px-4 py-1.5 ${base}`}
      >
        {icon}
        {text}
      </span>
    </motion.div>
  );
}

function NodeTypeChip({
  icon,
  type,
  count,
  color,
}: {
  icon: React.ReactNode;
  type: string;
  count: number;
  color: string;
}) {
  const colorMap: Record<string, string> = {
    blue:    'bg-blue-50 border-blue-200 text-blue-700',
    violet:  'bg-violet-50 border-violet-200 text-violet-700',
    primary: 'bg-primary-50 border-primary-200 text-primary-700',
    amber:   'bg-amber-50 border-amber-200 text-amber-700',
    rose:    'bg-rose-50 border-rose-200 text-rose-700',
    emerald: 'bg-emerald-50 border-emerald-200 text-emerald-700',
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      whileInView={{ opacity: 1, scale: 1 }}
      viewport={{ once: true }}
      transition={{ duration: 0.4 }}
      className={`rounded-xl border p-3 text-center ${colorMap[color]}`}
    >
      <div className="inline-flex items-center justify-center w-8 h-8 rounded-lg bg-white mb-2">
        {icon}
      </div>
      <div className="font-display text-xl">{count}</div>
      <div className="font-body text-xs mt-0.5 opacity-80">{type}</div>
    </motion.div>
  );
}

// Interactive mini Knowledge Graph demo
function MiniKGDemo() {
  const [hovered, setHovered] = useState<string | null>(null);

  const nodes = [
    { id: 'stoicism',      label: 'Stoicism',      x: 50, y: 18, type: 'school',    r: 9  },
    { id: 'chrysippus',    label: 'Chrysippus',    x: 18, y: 48, type: 'person',    r: 7  },
    { id: 'fate',          label: 'Fate (εἱμαρμένη)', x: 82, y: 48, type: 'concept', r: 7  },
    { id: 'compatibilism', label: 'Compatibilism', x: 50, y: 80, type: 'argument',  r: 8  },
    { id: 'epictetus',     label: 'Epictetus',     x: 22, y: 78, type: 'person',    r: 6  },
  ];

  const edges = [
    { from: 'stoicism',   to: 'chrysippus',    label: 'founder' },
    { from: 'stoicism',   to: 'fate',          label: 'core concept' },
    { from: 'chrysippus', to: 'compatibilism', label: 'formulated' },
    { from: 'fate',       to: 'compatibilism', label: 'addresses' },
    { from: 'stoicism',   to: 'epictetus',     label: 'influenced' },
    { from: 'epictetus',  to: 'compatibilism', label: 'defended' },
  ];

  const typeColors: Record<string, string> = {
    school:   '#c2410c',
    person:   '#7c3aed',
    concept:  '#d97706',
    argument: '#16a34a',
  };

  return (
    <div className="w-full aspect-square max-w-sm mx-auto bg-stone-50 border border-stone-200 rounded-2xl relative overflow-hidden shadow-lg">
      <svg className="w-full h-full" viewBox="0 0 100 100">
        {/* Edges */}
        {edges.map((edge, i) => {
          const from = nodes.find((n) => n.id === edge.from)!;
          const to   = nodes.find((n) => n.id === edge.to)!;
          const active =
            hovered === edge.from || hovered === edge.to;
          return (
            <line
              key={i}
              x1={from.x} y1={from.y}
              x2={to.x}   y2={to.y}
              stroke={active ? '#c2410c' : '#d1d5db'}
              strokeWidth={active ? 1.2 : 0.5}
              strokeDasharray={active ? undefined : '2,2'}
              className="transition-all duration-300"
            />
          );
        })}

        {/* Nodes */}
        {nodes.map((node) => (
          <g
            key={node.id}
            onMouseEnter={() => setHovered(node.id)}
            onMouseLeave={() => setHovered(null)}
            className="cursor-pointer"
          >
            <motion.circle
              cx={node.x} cy={node.y}
              r={hovered === node.id ? node.r + 2 : node.r}
              fill={typeColors[node.type]}
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.1 * nodes.indexOf(node), type: 'spring', stiffness: 200 }}
              className="transition-all duration-200"
            />
            <text
              x={node.x} y={node.y + node.r + 5}
              textAnchor="middle"
              fontSize="3.8"
              fill="#374151"
              fontWeight={hovered === node.id ? '700' : '400'}
            >
              {node.label}
            </text>
          </g>
        ))}
      </svg>

      {/* Legend */}
      <div className="absolute bottom-3 left-3 flex flex-wrap gap-2">
        {Object.entries(typeColors).map(([type, color]) => (
          <div key={type} className="flex items-center gap-1 text-xs font-body text-stone-500">
            <div className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
            <span className="capitalize">{type}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
