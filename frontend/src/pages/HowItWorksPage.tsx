/**
 * HowItWorksPage — scroll-snap educational landing page
 *
 * Sections:
 *   1. Hero             — parchment opener, route summary, scroll hint
 *   2. The Problem      — parchment, compare cards, key stats
 *   3. Knowledge Graph  — white, KG diagram, node types
 *   4. Retrieval        — dark, vectorless SQL/tree/lemma/citation routing
 *   5. GraphRAG Pipeline — dark, 5-stage interactive pipeline
 *   6. Architecture     — white, Agentic GraphRAG + corpus stats
 *   7. Hybrid Search    — parchment, 3 methods + RRF
 *   8. FAIR Data        — warm orange, FAIR badges
 *   9. CTA              — dark, links to explore
 */

import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { tArray } from '../i18n/utils';
import { useKgStats, formatCount } from '../hooks/useKgStats';
import {
  Network, Search, BookOpen, Brain, Sparkles,
  ChevronRight, GitBranch, Globe, CheckCircle2, Languages,
  ArrowRight, Quote, Users, Target, RotateCcw, Layers,
} from 'lucide-react';

import {
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

import DatabaseWithRestApi from '../components/ui/database-with-rest-api';
import AgenticGraphRAGDetails from '../components/AgenticGraphRAGDetails';

// ─── Section definitions ────────────────────────────────────────────────────

// ─── Main Page ───────────────────────────────────────────────────────────────

export default function HowItWorksPage() {
  const { t, i18n } = useTranslation();
  const stats = useKgStats();
  const fmt = (n: number) => formatCount(n, i18n.language);
  const resolveCounts = (text: string): string =>
    text
      .replace(/\{\{nodes\}\}/g, fmt(stats.nodes))
      .replace(/\{\{edges\}\}/g, fmt(stats.edges))
      .replace(/\{\{works\}\}/g, fmt(stats.works))
      .replace(/\{\{passages\}\}/g, fmt(stats.passages));
  const [activeId, setActiveId] = useState('hero');
  const containerRef = useRef<HTMLDivElement>(null);
  const [navHeight, setNavHeight] = useState(48);
  const navSections: DotNavSection[] = useMemo(() => [
    { id: 'hero', label: t('howItWorksPage.nav.hero') },
    { id: 'problem', label: t('howItWorksPage.nav.problem') },
    { id: 'kg', label: t('howItWorksPage.nav.kg') },
    { id: 'embeddings', label: t('howItWorksPage.nav.embeddings') },
    { id: 'pipeline', label: t('howItWorksPage.nav.pipeline') },
    { id: 'tech', label: t('howItWorksPage.nav.tech') },
    { id: 'search', label: t('howItWorksPage.nav.search') },
    { id: 'fair', label: t('howItWorksPage.nav.fair') },
    { id: 'cta', label: t('howItWorksPage.nav.cta') },
  ], [t]);

  // Measure the actual nav height so the scroll container sits flush below it
  useEffect(() => {
    const nav = document.getElementById('navigation');
    if (!nav) return;
    setNavHeight(nav.offsetHeight);
    const ro = new ResizeObserver(() => setNavHeight(nav.offsetHeight));
    ro.observe(nav);
    return () => ro.disconnect();
  }, []);

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

    navSections.forEach(({ id }) => {
      const el = document.getElementById(id);
      if (el) observer.observe(el);
    });
    return () => observer.disconnect();
  }, [navSections]);

  const scrollTo = useCallback((id: string) => {
    const el = document.getElementById(id);
    if (el && containerRef.current) {
      containerRef.current.scrollTo({ top: el.offsetTop, behavior: 'smooth' });
    }
  }, []);

  return (
    <div
      ref={containerRef}
      className="overflow-y-scroll relative"
      style={{
        scrollSnapType: 'y mandatory',
        scrollBehavior: 'smooth',
        marginTop: `${navHeight}px`,
        height: `calc(100dvh - ${navHeight}px)`,
        '--snap-h': `calc(100dvh - ${navHeight}px)`,
      } as React.CSSProperties}
    >
      {/* Dot navigation — fixed right side */}
      <DotNavigator
        sections={navSections}
        activeId={activeId}
        onNavigate={scrollTo}
      />

      {/* ── Section 1: Hero ─────────────────────────────────────────────── */}
      <ScrollSection id="hero" className="bg-parchment-100" noInner>
        <BackgroundMesh variant="grid" color="rgba(180,120,40,1)" opacity={0.045} />

        <div
          className="relative z-10 w-full max-w-6xl mx-auto px-4 sm:px-6 grid lg:grid-cols-[1.15fr_0.85fr] gap-10 lg:gap-16 items-center"
          style={{ minHeight: 'var(--snap-h, 100dvh)' }}
        >
          <div className="pt-14 pb-28 lg:pb-20">
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.55, delay: 0.12 }}
              className="mb-6"
            >
              <span className="inline-flex items-center gap-2 text-xs font-body uppercase tracking-[0.18em] text-orange-700 border border-orange-400/40 bg-orange-50 rounded-full px-4 py-1.5">
                <Sparkles className="w-3.5 h-3.5" />
                {t('howItWorksPage.hero.badge')}
              </span>
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.75, delay: 0.22, ease: [0.22, 1, 0.36, 1] }}
              className="font-display text-4xl sm:text-6xl lg:text-7xl text-stone-800 leading-[1.08] max-w-4xl mb-6"
            >
              {t('howItWorksPage.hero.titlePrefix')}{' '}
              <span className="text-orange-700">{t('howItWorksPage.hero.titleHighlight')}</span>
              <br />
              {' '}
              {t('howItWorksPage.hero.titleSuffix')}
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.65, delay: 0.36, ease: [0.22, 1, 0.36, 1] }}
              className="font-body text-lg sm:text-xl text-stone-600 max-w-2xl mb-10 leading-relaxed"
            >
              {t('howItWorksPage.hero.subtitle')}
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.55, delay: 0.5 }}
              className="flex flex-wrap items-center gap-4"
            >
              <Link
                to="/graphrag"
                className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-orange-800 hover:bg-orange-900 text-white font-body font-medium text-sm transition-colors"
              >
                <Sparkles className="w-4 h-4" />
                {t('howItWorksPage.hero.cta')}
              </Link>
              <GitHubPill variant="light" label={t('learn.hero.openSource')} />
            </motion.div>
          </div>

          <motion.div
            initial={{ opacity: 0, x: 24 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.7, delay: 0.38, ease: [0.22, 1, 0.36, 1] }}
            className="hidden lg:block border-l border-stone-300/70 pl-8"
          >
            <p className="text-xs font-body uppercase tracking-[0.18em] text-stone-400 mb-6">
              Vectorless GraphRAG route
            </p>
            <div className="space-y-5">
              {[
                { icon: <BookOpen className="w-4 h-4" />, title: 'Question', body: 'Greek, Latin, English, or a CTS reference' },
                { icon: <GitBranch className="w-4 h-4" />, title: 'Retrieval', body: 'SQLStrategy, lemmas, work tree, passage citations' },
                { icon: <Quote className="w-4 h-4" />, title: 'Evidence', body: 'Primary passages, KG context, proof chains' },
                { icon: <Sparkles className="w-4 h-4" />, title: 'Answer', body: 'Cited synthesis with verification' },
              ].map((item) => (
                <div key={item.title} className="grid grid-cols-[2.25rem_1fr] gap-3">
                  <div className="w-9 h-9 rounded-lg bg-orange-100 text-orange-700 border border-orange-200 flex items-center justify-center">
                    {item.icon}
                  </div>
                  <div>
                    <h2 className="font-display text-lg text-stone-800 leading-tight">{item.title}</h2>
                    <p className="font-body text-sm text-stone-500 leading-relaxed">{item.body}</p>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.9 }}
            className="absolute bottom-7 left-1/2 -translate-x-1/2"
          >
            <ScrollHint theme="dark" label={t('howItWorksPage.hero.scrollHint')} />
          </motion.div>
        </div>
      </ScrollSection>

      {/* ── Section 2: The Problem ───────────────────────────────────────── */}
      <ScrollSection
        id="problem"
        className="bg-parchment-100"
      >
        <BackgroundMesh variant="grid" color="rgba(180,120,40,1)" opacity={0.04} />

        <div className="w-full max-w-6xl mx-auto px-4 sm:px-6 py-20">
          {/* Section label */}
          <SectionLabel icon={<BookOpen className="w-4 h-4" />} text={t('howItWorksPage.problem.label')} />

          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
            className="font-display text-4xl sm:text-5xl lg:text-6xl text-stone-800 mb-4 leading-tight"
          >
            {t('howItWorksPage.problem.titlePrefix')}{' '}
            <em className="text-orange-600 not-italic">{t('howItWorksPage.problem.titleHighlight')}</em>
          </motion.h2>

          <motion.p
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.15 }}
            className="font-body text-lg text-stone-500 mb-12 max-w-2xl"
          >
            {t('howItWorksPage.problem.subtitle', {
              works: fmt(stats.works),
              passages: fmt(stats.passages),
              nodes: fmt(stats.nodes),
            })}
          </motion.p>

          <CompareCards
            before={{
              label: t('howItWorksPage.problem.before.label'),
              title: t('howItWorksPage.problem.before.title'),
              items: tArray(t, 'howItWorksPage.problem.before.items').map((text) => ({ text: resolveCounts(text) })),
              metric: { value: t('howItWorksPage.problem.before.metricValue'), description: t('howItWorksPage.problem.before.metricDescription') },
            }}
            after={{
              label: t('howItWorksPage.problem.after.label'),
              title: t('howItWorksPage.problem.after.title'),
              items: tArray(t, 'howItWorksPage.problem.after.items').map((text) => ({ text: resolveCounts(text) })),
              metric: { value: t('howItWorksPage.problem.after.metricValue'), description: t('howItWorksPage.problem.after.metricDescription') },
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
              { icon: <Network className="w-5 h-5" />, value: fmt(stats.nodes), label: t('home.stats.nodes') },
              { icon: <GitBranch className="w-5 h-5" />, value: fmt(stats.edges), label: t('home.stats.edges') },
              { icon: <BookOpen className="w-5 h-5" />, value: fmt(stats.works), label: t('home.stats.works') },
              { icon: <Quote className="w-5 h-5" />, value: fmt(stats.passages), label: t('home.stats.passages') },
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
          <SectionLabel icon={<Network className="w-4 h-4" />} text={t('howItWorksPage.knowledgeGraph.label')} />

          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <div>
              <motion.h2
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
                className="font-display text-4xl sm:text-5xl text-stone-800 mb-5 leading-tight"
              >
                {t('howItWorksPage.knowledgeGraph.titlePrefix')}{' '}
                <span className="text-primary-700">{t('howItWorksPage.knowledgeGraph.titleHighlight')}</span> {t('howItWorksPage.knowledgeGraph.titleSuffix')}
              </motion.h2>

              <motion.p
                initial={{ opacity: 0, y: 12 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: 0.15 }}
                className="font-body text-base text-stone-500 mb-8 leading-relaxed"
              >
                {t('howItWorksPage.knowledgeGraph.subtitle')}
              </motion.p>

              {/* Node type grid */}
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                {[
                  { icon: <Users className="w-4 h-4" />, type: t('kg.nodeTypes.persons'), nodeType: 'person', fallback: 179, color: 'blue' },
                  { icon: <Brain className="w-4 h-4" />, type: t('kg.nodeTypes.concepts'), nodeType: 'concept', fallback: 121, color: 'violet' },
                  { icon: <Target className="w-4 h-4" />, type: t('kg.nodeTypes.arguments'), nodeType: 'argument', fallback: 116, color: 'primary' },
                  { icon: <BookOpen className="w-4 h-4" />, type: t('kg.nodeTypes.works'), nodeType: 'work', fallback: 66, color: 'amber' },
                  { icon: <RotateCcw className="w-4 h-4" />, type: t('howItWorksPage.knowledgeGraph.nodeTypeLabels.reformulations'), nodeType: 'reformulation', fallback: 53, color: 'rose' },
                  { icon: <Quote className="w-4 h-4" />, type: t('howItWorksPage.knowledgeGraph.nodeTypeLabels.quotes'), nodeType: 'quote', fallback: 14, color: 'emerald' },
                ].map(({ nodeType, fallback, ...nt }) => {
                  const live = stats.nodeTypes[nodeType];
                  const count = Number.isFinite(live) ? live : fallback;
                  return (
                  <NodeTypeChip key={nt.type} {...nt} count={count} />
                  );
                })}
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
              <p className="text-xs font-body uppercase tracking-widest text-orange-600 mb-2">{t('howItWorksPage.knowledgeGraph.primaryLayer')}</p>
              <h4 className="font-display text-xl text-stone-800 mb-2">{t('howItWorksPage.knowledgeGraph.primaryTitle')}</h4>
              <p className="font-body text-sm text-stone-600">
                {t('howItWorksPage.knowledgeGraph.primaryBody')}
              </p>
            </GlassCard>
            <GlassCard variant="parchment" padding="lg">
              <p className="text-xs font-body uppercase tracking-widest text-primary-600 mb-2">{t('howItWorksPage.knowledgeGraph.secondaryLayer')}</p>
              <h4 className="font-display text-xl text-stone-800 mb-2">{t('howItWorksPage.knowledgeGraph.secondaryTitle')}</h4>
              <p className="font-body text-sm text-stone-600">
                {t('howItWorksPage.knowledgeGraph.secondaryBody')}
              </p>
            </GlassCard>
          </motion.div>
        </div>
      </ScrollSection>

      {/* ── Section 4: Vectorless Retrieval ──────────────────────────────── */}
      <ScrollSection id="embeddings" className="bg-zinc-950">
        <BackgroundMesh variant="dots" color="rgba(255,255,255,1)" opacity={0.025} />

        <div className="w-full max-w-6xl mx-auto px-4 sm:px-6 py-20">
          <SectionLabel icon={<GitBranch className="w-4 h-4" />} text={t('howItWorksPage.embeddings.label')} />

          <div className="grid lg:grid-cols-[2fr_3fr] gap-12 items-start mt-10">

            {/* ── Left column: explainer ── */}
            <div className="space-y-7">
              <motion.h2
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6 }}
                className="font-display text-4xl lg:text-5xl text-white leading-tight"
              >
                {t('howItWorksPage.embeddings.titleLine1')}<br />{t('howItWorksPage.embeddings.titleLine2')}
              </motion.h2>

              <motion.p
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: 0.1 }}
                className="font-body text-base text-white/65 leading-relaxed"
              >
                {t('howItWorksPage.embeddings.subtitle')}
              </motion.p>

              <motion.div
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: 0.15 }}
                className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm p-5 space-y-3"
              >
                <p className="text-xs font-body uppercase tracking-widest text-white/40">{t('howItWorksPage.embeddings.analogy')}</p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm font-body">
                  <div className="rounded-xl bg-blue-500/10 border border-blue-500/20 p-3">
                    <p className="text-blue-300 font-semibold mb-1">{t('howItWorksPage.embeddings.physicalSpace')}</p>
                    <p className="text-white/60 font-mono text-xs break-words">Query → terms + references</p>
                    <p className="text-white/60 font-mono text-xs break-words">Works → tree sections</p>
                    <p className="text-white/40 text-xs mt-1">{t('howItWorksPage.embeddings.physicalClose')}</p>
                  </div>
                  <div className="rounded-xl bg-orange-500/10 border border-orange-500/20 p-3">
                    <p className="text-orange-300 font-semibold mb-1">{t('howItWorksPage.embeddings.semanticSpace')}</p>
                    <p className="text-white/60 font-mono text-xs break-words">KG node → passage_citations</p>
                    <p className="text-white/60 font-mono text-xs break-words">Lemma → attested passages</p>
                    <p className="text-white/40 text-xs mt-1">{t('howItWorksPage.embeddings.semanticClose')}</p>
                  </div>
                </div>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 12 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: 0.2 }}
                className="flex items-baseline gap-3"
              >
                <span className="font-display text-5xl text-orange-400">0</span>
                <span className="font-body text-sm text-white/50 leading-snug">
                  {t('howItWorksPage.embeddings.dimensions')}<br />
                  <span className="text-white/30 text-xs">{t('howItWorksPage.embeddings.projected')}</span>
                </span>
              </motion.div>
            </div>

            <motion.div
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.7, delay: 0.05 }}
              className="grid sm:grid-cols-2 gap-4"
            >
              {[
                {
                  icon: <Languages className="w-5 h-5" />,
                  title: t('howItWorksPage.embeddings.cards.lemma.title'),
                  body: t('howItWorksPage.embeddings.cards.lemma.body'),
                },
                {
                  icon: <BookOpen className="w-5 h-5" />,
                  title: t('howItWorksPage.embeddings.cards.tree.title'),
                  body: t('howItWorksPage.embeddings.cards.tree.body'),
                },
                {
                  icon: <Quote className="w-5 h-5" />,
                  title: t('howItWorksPage.embeddings.cards.citations.title'),
                  body: t('howItWorksPage.embeddings.cards.citations.body'),
                },
                {
                  icon: <Network className="w-5 h-5" />,
                  title: t('howItWorksPage.embeddings.cards.graph.title'),
                  body: t('howItWorksPage.embeddings.cards.graph.body'),
                },
              ].map((card) => (
                <div
                  key={card.title}
                  className="rounded-2xl border border-white/10 bg-white/5 p-5 min-h-[180px]"
                >
                  <div className="w-10 h-10 rounded-xl bg-orange-500/15 text-orange-300 flex items-center justify-center mb-4">
                    {card.icon}
                  </div>
                  <h3 className="font-display text-xl text-white mb-2">{card.title}</h3>
                  <p className="font-body text-sm leading-relaxed text-white/60">{card.body}</p>
                </div>
              ))}
            </motion.div>

          </div>
        </div>
      </ScrollSection>

      {/* ── Section 5: GraphRAG Pipeline ─────────────────────────────────── */}
      <ScrollSection id="pipeline" className="bg-zinc-950">
        <BackgroundMesh variant="dots" color="rgba(255,255,255,1)" opacity={0.025} />

        <div className="w-full max-w-6xl mx-auto px-4 sm:px-6 py-20">
          <SectionLabel
            icon={<Sparkles className="w-4 h-4" />}
            text={t('howItWorksPage.pipeline.label')}
            theme="dark"
          />

          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
            className="font-display text-4xl sm:text-5xl text-white mb-4 leading-tight"
          >
            {t('howItWorksPage.pipeline.titlePrefix')}{' '}
            <span className="text-orange-400">{t('howItWorksPage.pipeline.titleQuestion')}</span> {t('howItWorksPage.pipeline.titleMiddle')}{' '}
            <span className="text-orange-400">{t('howItWorksPage.pipeline.titleAnswer')}</span>
          </motion.h2>

          <motion.p
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.15 }}
            className="font-body text-base text-white/50 mb-12 max-w-2xl"
          >
            {t('howItWorksPage.pipeline.subtitle')}
          </motion.p>

          <PipelineSteps theme="dark" autoPlay={5000} />
        </div>
      </ScrollSection>

      {/* ── Section 5: Architecture / Tech ──────────────────────────────── */}
      <ScrollSection id="tech" className="bg-white" noInner>
        <BackgroundMesh variant="dots" color="rgba(100,100,120,1)" opacity={0.04} />

        <div className="relative z-10 w-full max-w-6xl mx-auto px-4 sm:px-6 py-20">
          <SectionLabel icon={<Layers className="w-4 h-4" />} text={t('howItWorksPage.architecture.label')} />

          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
            className="font-display text-4xl sm:text-5xl text-stone-800 mb-4 leading-tight"
          >
            {t('howItWorksPage.architecture.titlePrefix')}{' '}
            <span className="text-violet-700">{t('howItWorksPage.architecture.titleHighlight')}</span>
          </motion.h2>

          <motion.p
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.15 }}
            className="font-body text-base text-stone-500 mb-12 max-w-2xl"
          >
            {t('howItWorksPage.architecture.subtitle')}
          </motion.p>

          {/* Pipeline visualisation */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="flex flex-col items-center mb-12"
          >
            <div className="w-full max-w-3xl">
              <DatabaseWithRestApi
                className="h-[420px] w-full"
                circleText="API"
                badgeTexts={{ first: 'Question', second: 'Context', third: 'Synthesis', fourth: 'Answer' }}
                buttonTexts={{ first: 'Knowledge Graph', second: 'AI Model' }}
                title="GraphRAG Pipeline: Database → AI Response"
                lightColor="#c2410c"
              />
            </div>
            <p className="text-sm font-body text-stone-400 text-center mt-6 max-w-2xl leading-relaxed">
              {t('howItWorksPage.architecture.pipelineCaption')}
            </p>
          </motion.div>

          {/* Agentic GraphRAG highlight + stats */}
          <div className="grid lg:grid-cols-2 gap-6 mb-10">
            {/* Agentic GraphRAG card */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="rounded-2xl border-2 border-violet-200 bg-gradient-to-br from-violet-50 to-indigo-50 p-7"
            >
              <div className="flex items-center gap-3 mb-4">
                <h3 className="font-display text-2xl text-violet-900">{t('howItWorksPage.architecture.agenticGraphragTitle')}</h3>
                <span className="text-xs font-body font-semibold bg-violet-200 text-violet-800 rounded-full px-3 py-1">
                  {t('howItWorksPage.architecture.paperBadge')}
                </span>
              </div>
              <p className="font-body text-sm text-stone-700 mb-5 leading-relaxed">
                {t('howItWorksPage.architecture.agenticGraphragBody')}
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-5 text-sm font-body">
                <div className="bg-white/70 rounded-xl p-4">
                  <p className="font-semibold text-violet-900 mb-1">LLM calls per query</p>
                  <p className="text-violet-700 font-mono font-bold text-lg">2 <span className="text-stone-400 font-normal text-xs">down from 10+</span></p>
                </div>
                <div className="bg-white/70 rounded-xl p-4">
                  <p className="font-semibold text-violet-900 mb-1">Context window</p>
                  <p className="text-violet-700 font-mono font-bold text-lg">~1M <span className="text-stone-400 font-normal text-xs">tokens (no truncation)</span></p>
                </div>
              </div>
              <a
                href="/how-it-works"
                className="inline-flex items-center gap-2 min-h-11 text-xs font-body text-violet-600 hover:text-violet-800 border border-violet-300 rounded-full px-4 py-1.5 hover:bg-violet-100 transition-colors"
              >
                {t('howItWorksPage.architecture.findingsLink')}
                <ChevronRight className="w-3.5 h-3.5" />
              </a>
            </motion.div>

            {/* Stats grid */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: 0.1 }}
              className="grid grid-cols-1 sm:grid-cols-2 gap-4 content-start"
            >
              {/* Philological */}
              <div className="rounded-2xl border-2 border-amber-200/60 bg-gradient-to-br from-parchment-50 to-amber-50 p-5">
                <h4 className="font-body font-semibold text-sm text-stone-800 mb-3 uppercase tracking-wide">{t('howItWorksPage.architecture.corpus')}</h4>
                <ul className="space-y-2 text-xs font-body text-stone-700">
                  {tArray<string[]>(t, 'howItWorksPage.architecture.corpusStats').map(([n, l]) => (
                    <li key={l} className="flex items-baseline gap-1.5">
                      <span className="font-mono font-bold text-sm text-orange-600">{resolveCounts(n)}</span>
                      <span className="opacity-80">{l}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Tech stack */}
              <div className="rounded-2xl border-2 border-amber-200/60 bg-gradient-to-br from-parchment-50 to-amber-50 p-5">
                <h4 className="font-body font-semibold text-sm text-stone-800 mb-3 uppercase tracking-wide">{t('howItWorksPage.architecture.stack')}</h4>
                <ul className="space-y-2 text-xs font-body text-stone-700">
                  {tArray(t, 'howItWorksPage.architecture.stackItems').map((item) => (
                    <li key={item} className="flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-orange-400 flex-shrink-0" />
                      {item}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Link to showcase */}
              <div className="col-span-2">
                <Link
                  to="/graphrag-showcase"
                  className="flex items-center justify-center gap-2 w-full py-3 rounded-xl bg-gradient-to-r from-orange-600 to-amber-600 text-white font-body font-medium text-sm hover:from-orange-700 hover:to-amber-700 transition-all"
                >
                  <Sparkles className="w-4 h-4" />
                  {t('howItWorksPage.architecture.seeInAction')}
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            </motion.div>
          </div>

          {/* Accordion details */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="rounded-2xl border border-stone-200 bg-stone-50/60 overflow-hidden"
          >
            <AgenticGraphRAGDetails />
          </motion.div>
        </div>
      </ScrollSection>

      {/* ── Section 6 (was 5): Hybrid Search ─────────────────────────────── */}
      <ScrollSection id="search" className="bg-parchment-50">
        <BackgroundMesh variant="crosses" color="rgba(160,100,30,1)" opacity={0.04} />

        <div className="w-full max-w-6xl mx-auto px-4 sm:px-6 py-20">
          <SectionLabel icon={<Search className="w-4 h-4" />} text={t('howItWorksPage.hybridSearch.label')} />

          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
            className="font-display text-4xl sm:text-5xl text-stone-800 mb-4 leading-tight"
          >
            {t('howItWorksPage.hybridSearch.titlePrefix')}{' '}
            <span className="text-orange-600">{t('howItWorksPage.hybridSearch.titleHighlight')}</span>
          </motion.h2>

          <motion.p
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.15 }}
            className="font-body text-base text-stone-500 mb-12 max-w-2xl"
          >
            {t('howItWorksPage.hybridSearch.subtitle')}
          </motion.p>

          {/* Method cards */}
          <div className="grid md:grid-cols-3 gap-5 mb-12">
            {[
              {
                icon: <Search className="w-5 h-5" />,
                title: t('howItWorksPage.hybridSearch.methods.fullText.title'),
                speed: '< 100 ms',
                color: 'bg-orange-50 border-orange-200',
                iconColor: 'bg-orange-100 text-orange-600',
                desc: t('howItWorksPage.hybridSearch.methods.fullText.description'),
                example: t('howItWorksPage.hybridSearch.methods.fullText.example'),
              },
              {
                icon: <Languages className="w-5 h-5" />,
                title: t('howItWorksPage.hybridSearch.methods.lemmatic.title'),
                speed: '< 500 ms',
                color: 'bg-rose-50 border-rose-200',
                iconColor: 'bg-rose-100 text-rose-600',
                desc: t('howItWorksPage.hybridSearch.methods.lemmatic.description'),
                example: t('howItWorksPage.hybridSearch.methods.lemmatic.example'),
              },
              {
                icon: <Brain className="w-5 h-5" />,
                title: t('howItWorksPage.hybridSearch.methods.semantic.title'),
                speed: '< 2 s',
                color: 'bg-amber-50 border-amber-200',
                iconColor: 'bg-amber-100 text-amber-700',
                desc: t('howItWorksPage.hybridSearch.methods.semantic.description'),
                example: t('howItWorksPage.hybridSearch.methods.semantic.example'),
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
                    {t('howItWorksPage.hybridSearch.rrfTitle')}
                  </h4>
                  <p className="font-body text-sm text-stone-500 max-w-sm">
                    {t('howItWorksPage.hybridSearch.rrfBody')}
                  </p>
                </div>
                <div className="font-mono text-xs sm:text-sm text-stone-700 bg-white/70 border border-parchment-300 rounded-xl px-4 sm:px-6 py-3 sm:py-4 overflow-x-auto max-w-full">
                  <span className="whitespace-nowrap">RRF(d) = Σ{' '}
                  <span className="text-orange-600 font-semibold">1 / (k + rank)</span>
                  {' '}· k = 60</span>
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
            text={t('howItWorksPage.fair.label')}
            variant="amber"
          />

          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
            className="font-display text-4xl sm:text-5xl text-stone-800 mb-4 leading-tight"
          >
            {t('howItWorksPage.fair.titlePrefix')}{' '}
            <span className="text-amber-700">{t('howItWorksPage.fair.titleHighlight')}</span>
          </motion.h2>

          <motion.p
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.15 }}
            className="font-body text-base text-stone-500 mb-12 max-w-2xl"
          >
            {t('howItWorksPage.fair.subtitle')}
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
              href="https://doi.org/10.5281/zenodo.17379489"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 min-h-11 px-4 py-2 rounded-full border border-amber-400/50 bg-amber-100/60 text-amber-800 text-sm font-body font-medium hover:bg-amber-200/60 transition-colors"
            >
              <Globe className="w-4 h-4" />
              DOI: 10.5281/zenodo.17379489
            </a>
            <GitHubPill variant="light" label={t('learn.hero.openSource')} />
            <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-stone-300 bg-white/60 text-stone-600 text-sm font-body">
              CC BY 4.0
            </span>
          </motion.div>
        </div>
      </ScrollSection>

      {/* ── Section 7: CTA ────────────────────────────────────────────────── */}
      <ScrollSection id="cta" className="bg-zinc-950">
        <BackgroundMesh variant="dots" color="rgba(255,255,255,1)" opacity={0.025} />

        <div className="relative z-10 flex flex-col items-center justify-center px-6 text-center" style={{ minHeight: 'var(--snap-h, 100dvh)' }}>
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
          >
            <span className="inline-flex items-center gap-2 text-xs font-body uppercase tracking-[0.2em] text-orange-400 border border-orange-500/30 bg-orange-500/10 rounded-full px-4 py-1.5 mb-8">
              <Sparkles className="w-3.5 h-3.5" />
              {t('howItWorksPage.cta.badge')}
            </span>

            <h2 className="font-display text-5xl sm:text-6xl lg:text-7xl text-white mb-6 leading-tight max-w-4xl">
              {t('howItWorksPage.cta.titlePrefix')}{' '}
              <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-orange-400 to-amber-300">
                {t('howItWorksPage.cta.titleHighlight')}
              </span>
            </h2>

            <p className="font-body text-lg text-white/50 max-w-xl mx-auto mb-12">
              {t('howItWorksPage.cta.subtitle')}
            </p>

            {/* CTA buttons */}
            <div className="flex flex-wrap justify-center gap-4 mb-16">
              <Link
                to="/graphrag"
                className="inline-flex items-center gap-2 px-7 py-3.5 rounded-full bg-orange-500 hover:bg-orange-400 text-white font-body font-semibold transition-colors"
              >
                <Sparkles className="w-4 h-4" />
                {t('howItWorksPage.cta.askQuestion')}
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                to="/visualizer"
                className="inline-flex items-center gap-2 px-7 py-3.5 rounded-full border border-white/20 bg-white/8 hover:bg-white/15 text-white font-body font-medium transition-colors"
              >
                <Network className="w-4 h-4" />
                {t('howItWorksPage.cta.exploreGraph')}
              </Link>
            </div>

            {/* Feature row */}
            <div className="flex flex-wrap justify-center gap-6 text-sm font-body">
              {tArray(t, 'howItWorksPage.cta.bullets').map((text) => (
                <div key={text} className="flex items-center gap-2 text-white/50">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span>{text}</span>
                </div>
              ))}
            </div>

            {/* Bottom links */}
            <div className="mt-10 flex flex-wrap justify-center gap-3">
              <GitHubPill variant="dark" label={t('learn.hero.openSource')} />
              <Link
                to="/about"
                className="inline-flex items-center gap-2 min-h-11 px-4 py-2 rounded-full border border-white/15 text-white/50 hover:text-white/80 text-sm font-body transition-colors"
              >
                <Layers className="w-4 h-4" />
                {t('howItWorksPage.cta.aboutProject')}
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
