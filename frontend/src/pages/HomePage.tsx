import { useState, useRef, useEffect, lazy, Suspense, useCallback } from 'react';
import { motion, AnimatePresence, type Variants } from 'framer-motion';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  Network, Search, BookOpen, ChevronRight, MessageSquare,
  Cpu, Layers, GitBranch, Sparkles, Globe, CheckCircle2,
  ArrowRight, Play, Pause, RotateCcw, PanelLeftClose, PanelLeft,
  BookMarked, Users, Languages, Quote, Target, Brain, Loader2,
  Maximize2, Minimize2
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { HeroSection } from '../components/ui/hero-section-2';
import { MorphingParticles } from '../components/MorphingParticles';
import { FeatureCarousel, type FeatureCardData } from '../components/ui/feature-carousel';

// Direct import to bypass dynamic import caching issues
import EmbeddingsVisualization3D from '../components/EmbeddingsVisualization3D';
// Lazy load the embedding journey (not used on initial load)
const EmbeddingJourneyUltra = lazy(() => import('../components/EmbeddingJourneyUltra'));

// Animation variants
const fadeInUp: Variants = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] } }
};

const staggerContainer: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
};

const staggerItem: Variants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 }
};

export default function HomePage() {
  const { t } = useTranslation();
  const [activeSection, setActiveSection] = useState('overview');
  const [isMenuCollapsed, setIsMenuCollapsed] = useState(true); // Collapsed by default
  const [isFullscreen, setIsFullscreen] = useState(false);
  const particleContainerRef = useRef<HTMLDivElement>(null);

  const toggleFullscreen = useCallback(() => {
    const container = particleContainerRef.current;
    if (!container) return;

    if (!document.fullscreenElement) {
      container.requestFullscreen();
    } else {
      document.exitFullscreen();
    }
  }, []);

  // Listen for fullscreen changes (ESC key, etc.)
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  // Feature cards for the carousel
  const featureCards: FeatureCardData[] = [
    {
      id: 'kg',
      to: '/visualizer',
      title: t('home.features.kg.title'),
      description: t('home.features.kg.description'),
      icon: <Network className="w-8 h-8" />,
      gradient: 'from-blue-400 via-blue-300 to-indigo-200',
      accentColor: 'rgba(59, 130, 246, 0.4)',
      stats: { value: '576', label: t('learn.overview.stats.nodes') },
    },
    {
      id: 'search',
      to: '/search',
      title: t('home.features.search.title'),
      description: t('home.features.search.description'),
      icon: <Search className="w-8 h-8" />,
      gradient: 'from-indigo-400 via-purple-300 to-violet-200',
      accentColor: 'rgba(99, 102, 241, 0.4)',
      stats: { value: '3', label: 'Search Modes' },
    },
    {
      id: 'graphrag',
      to: '/graphrag',
      title: t('home.features.graphrag.title'),
      description: t('home.features.graphrag.description'),
      icon: <MessageSquare className="w-8 h-8" />,
      gradient: 'from-violet-400 via-purple-300 to-pink-200',
      accentColor: 'rgba(139, 92, 246, 0.4)',
      stats: { value: '5', label: 'Stage Pipeline' },
    },
    {
      id: 'texts',
      to: '/texts',
      title: t('home.features.texts.title'),
      description: t('home.features.texts.description'),
      icon: <BookOpen className="w-8 h-8" />,
      gradient: 'from-amber-400 via-orange-300 to-yellow-200',
      accentColor: 'rgba(245, 158, 11, 0.4)',
      stats: { value: '487', label: t('learn.overview.stats.works') },
    },
  ];

  // Navigation sections with translations
  const sections = [
    { id: 'overview', label: t('learn.nav.overview'), icon: Globe },
    { id: 'knowledge-graph', label: t('learn.nav.knowledgeGraph'), icon: Network },
    { id: 'embeddings', label: t('learn.nav.embeddings'), icon: Brain },
    { id: 'graphrag', label: t('learn.nav.graphrag'), icon: Sparkles },
    { id: 'hybrid-search', label: t('learn.nav.hybridSearch'), icon: Search },
    { id: 'ancient-texts', label: t('learn.nav.ancientTexts'), icon: BookOpen },
    { id: 'fair', label: t('learn.nav.fair'), icon: CheckCircle2 },
    { id: 'glossary', label: t('learn.nav.glossary'), icon: BookMarked },
  ];
  const containerRef = useRef<HTMLDivElement>(null);

  // Update active section based on scroll
  useEffect(() => {
    const handleScroll = () => {
      const container = containerRef.current;
      if (!container) return;

      const scrollPosition = container.scrollTop + 200;

      for (const section of sections) {
        const element = document.getElementById(section.id);
        if (element) {
          const { offsetTop, offsetHeight } = element;
          if (scrollPosition >= offsetTop && scrollPosition < offsetTop + offsetHeight) {
            setActiveSection(section.id);
            break;
          }
        }
      }
    };

    const container = containerRef.current;
    container?.addEventListener('scroll', handleScroll);
    return () => container?.removeEventListener('scroll', handleScroll);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- sections is stable (same IDs); adding it causes re-runs on every translation change
  }, []);

  const scrollToSection = (id: string) => {
    const element = document.getElementById(id);
    if (element && containerRef.current) {
      containerRef.current.scrollTo({
        top: element.offsetTop - 100,
        behavior: 'smooth'
      });
    }
  };

  return (
    <div className="min-h-screen relative">
      {/* Layer 1: Aurora effect */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none z-[1]">
        <div
          className={`
            [--white-gradient:repeating-linear-gradient(100deg,var(--white)_0%,var(--white)_7%,var(--transparent)_10%,var(--transparent)_12%,var(--white)_16%)]
            [--aurora:repeating-linear-gradient(100deg,var(--blue-500)_10%,var(--indigo-300)_15%,var(--blue-300)_20%,var(--violet-200)_25%,var(--blue-400)_30%)]
            [background-image:var(--white-gradient),var(--aurora)]
            [background-size:300%,_200%]
            [background-position:50%_50%,50%_50%]
            filter blur-[10px] invert
            after:content-[""] after:absolute after:inset-0 after:[background-image:var(--white-gradient),var(--aurora)]
            after:[background-size:200%,_100%]
            after:animate-aurora after:[background-attachment:fixed] after:mix-blend-difference
            pointer-events-none
            absolute -inset-[10px] opacity-70 will-change-transform
          `}
        />
      </div>

      {/* Fixed Navigation Sidebar - Collapsible */}
      <nav
        className={`fixed left-0 top-12 bottom-0 bg-white border-r border-academic-border shadow-lg z-[100] hidden lg:flex flex-col overflow-y-auto overflow-x-hidden transition-all duration-300 ease-out
          ${isMenuCollapsed ? 'w-[72px]' : 'w-64'}`}
      >
        {/* Collapse Toggle Button - Always visible at top */}
        <div className={`flex items-center border-b border-academic-border ${isMenuCollapsed ? 'justify-center p-3' : 'justify-between p-4'}`}>
          {!isMenuCollapsed && (
            <h2 className="text-lg font-semibold text-academic-text flex items-center gap-2 min-w-0">
              <BookOpen className="w-5 h-5 text-primary-600 flex-shrink-0" />
              <span className="truncate">{t('learn.nav.title')}</span>
            </h2>
          )}
          <button
            onClick={() => setIsMenuCollapsed(!isMenuCollapsed)}
            className="p-2 rounded-lg hover:bg-gray-100 text-academic-muted hover:text-academic-text transition-colors flex-shrink-0"
            title={isMenuCollapsed ? 'Expand' : 'Collapse'}
            aria-label={isMenuCollapsed ? 'Expand menu' : 'Collapse menu'}
          >
            {isMenuCollapsed ? (
              <PanelLeft className="w-5 h-5" />
            ) : (
              <PanelLeftClose className="w-5 h-5" />
            )}
          </button>
        </div>

        <div className={`flex-1 overflow-y-auto ${isMenuCollapsed ? 'p-3' : 'p-4'}`}>

          <ul className="space-y-1">
            {sections.map((section) => {
              const Icon = section.icon;
              return (
                <li key={section.id}>
                  <button
                    onClick={() => scrollToSection(section.id)}
                    title={isMenuCollapsed ? section.label : undefined}
                    className={`w-full rounded-lg text-sm font-medium transition-all duration-200 flex items-center
                      ${isMenuCollapsed ? 'p-3 justify-center' : 'px-3 py-2 gap-3'}
                      ${activeSection === section.id
                        ? 'bg-primary-100 text-primary-700'
                        : 'text-academic-muted hover:bg-gray-100 hover:text-academic-text'
                      }`}
                  >
                    <Icon className="w-5 h-5 flex-shrink-0" />
                    {!isMenuCollapsed && (
                      <span className="whitespace-nowrap">{section.label}</span>
                    )}
                  </button>
                </li>
              );
            })}
          </ul>

          <div className={`mt-8 pt-6 border-t border-academic-border`}>
            <Link
              to="/graphrag"
              title={isMenuCollapsed ? t('learn.nav.tryGraphRAG') : undefined}
              className={`flex items-center rounded-lg bg-primary-600 text-white text-sm font-medium hover:bg-primary-700 transition-colors
                ${isMenuCollapsed ? 'p-3 justify-center' : 'gap-2 px-3 py-2'}`}
            >
              <Sparkles className="w-5 h-5 flex-shrink-0" />
              {!isMenuCollapsed && (
                <>
                  <span className="whitespace-nowrap">{t('learn.nav.tryGraphRAG')}</span>
                  <ChevronRight className="w-4 h-4 ml-auto" />
                </>
              )}
            </Link>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main
        ref={containerRef}
        className={`min-h-screen overflow-y-auto scroll-smooth transition-[margin] duration-300 ease-out relative z-10
          ${isMenuCollapsed ? 'lg:ml-[72px]' : 'lg:ml-64'}`}
      >
        {/* Hero Section - Full viewport height */}
        <HeroSection
          logo={{
            url: "/logo.svg",
            alt: "EleutherIA"
          }}
          slogan={t('learn.hero.slogan')}
          title={
            <>
              {t('learn.hero.title')} <br />
              <span className="text-primary-600">{t('learn.hero.titleHighlight')}</span>
            </>
          }
          subtitle={t('learn.hero.subtitle')}
          callToAction={{
            text: t('learn.hero.cta'),
            href: "#overview",
          }}
          backgroundComponent={
            <div
              ref={particleContainerRef}
              className="absolute inset-0 bg-zinc-950"
            >
              {/* Morphing particles - uses adaptive particle count based on device */}
              <MorphingParticles
                morphDuration={7}
                rotationSpeed={0.12}
                particleSize={0.5}
                lineOpacity={0.02}
                connectionDistance={16}
                colorScheme="warm"
                enableBloom={true}
                bloomIntensity={0.2}
                enableHover={true}
              />
              {/* Fullscreen button - inside particle container */}
              <button
                onClick={toggleFullscreen}
                className="absolute bottom-4 right-4 z-50 p-2 rounded-lg bg-black/40 hover:bg-black/60 border border-white/20 hover:border-white/40 transition-all duration-200 group backdrop-blur-sm"
                title={isFullscreen ? 'Exit Fullscreen' : 'Fullscreen Particles'}
              >
                {isFullscreen ? (
                  <Minimize2 className="w-5 h-5 text-white/70 group-hover:text-white" />
                ) : (
                  <Maximize2 className="w-5 h-5 text-white/70 group-hover:text-white" />
                )}
              </button>
            </div>
          }
          contactInfo={[
            { type: 'doi', label: t('learn.hero.doi'), href: 'https://doi.org/10.5281/zenodo.17379490' },
            { type: 'website', label: t('learn.hero.license') },
            { type: 'github', label: t('learn.hero.openSource'), href: 'https://github.com' },
          ]}
        />

        {/* Quick Start - Feature Carousel */}
        <section id="quick-start" className="relative py-16 overflow-visible bg-white/60 backdrop-blur-sm">
          <div className="max-w-7xl mx-auto px-4 overflow-visible">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="text-center mb-8"
            >
              <h2 className="text-3xl md:text-4xl font-bold text-academic-text mb-4">
                {t('home.quickStart', 'Quick Start')}
              </h2>
              <p className="text-lg text-academic-muted max-w-2xl mx-auto">
                {t('home.quickStartDescription', 'Explore the core features of EleutherIA')}
              </p>
            </motion.div>
            <div className="overflow-visible">
              <FeatureCarousel cards={featureCards} autoPlayInterval={5000} />
            </div>
          </div>
        </section>

        {/* Overview Section */}
        <section id="overview" className="py-20 px-6 bg-white/60 backdrop-blur-sm">
          <div className="max-w-6xl mx-auto">
            <SectionHeader
              icon={<Globe className="w-8 h-8" />}
              title={t('learn.overview.title')}
              subtitle={t('learn.overview.subtitle')}
            />

            {/* The Problem/Solution */}
            <div className="grid md:grid-cols-2 gap-8 mt-12">
              <motion.div
                variants={fadeInUp}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true }}
                className="relative"
              >
                <div className="absolute -top-4 -left-4 w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
                  <span className="text-2xl">!</span>
                </div>
                <Card variant="outlined" padding="lg" className="h-full border-red-200 bg-red-50/30">
                  <CardHeader>
                    <CardTitle className="text-red-700">{t('learn.overview.challenge.title')}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-academic-muted mb-4">
                      {t('learn.overview.challenge.intro')}
                    </p>
                    <ul className="space-y-3">
                      {(t('learn.overview.challenge.items', { returnObjects: true }) as string[]).map((item, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-academic-muted">
                          <span className="text-red-400 mt-1">•</span>
                          {item}
                        </li>
                      ))}
                    </ul>
                    <div className="mt-6 p-4 bg-red-100/50 rounded-lg">
                      <p className="text-sm font-medium text-red-800">
                        {t('learn.overview.challenge.timeRequired')} <span className="text-2xl">{t('learn.overview.challenge.timeDays')}</span>
                      </p>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>

              <motion.div
                variants={fadeInUp}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true }}
                className="relative"
              >
                <div className="absolute -top-4 -left-4 w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                  <CheckCircle2 className="w-6 h-6 text-green-600" />
                </div>
                <Card variant="outlined" padding="lg" className="h-full border-green-200 bg-green-50/30">
                  <CardHeader>
                    <CardTitle className="text-green-700">{t('learn.overview.solution.title')}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-academic-muted mb-4">
                      {t('learn.overview.solution.intro')}
                    </p>
                    <ul className="space-y-3">
                      {(t('learn.overview.solution.items', { returnObjects: true }) as string[]).map((item, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-academic-muted">
                          <CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                          {item}
                        </li>
                      ))}
                    </ul>
                    <div className="mt-6 p-4 bg-green-100/50 rounded-lg">
                      <p className="text-sm font-medium text-green-800">
                        {t('learn.overview.solution.timeRequired')} <span className="text-2xl">{t('learn.overview.solution.timeSeconds')}</span>
                      </p>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            </div>

            {/* Statistics Grid */}
            <motion.div
              variants={staggerContainer}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true }}
              className="grid grid-cols-2 md:grid-cols-4 gap-6 mt-16"
            >
              <StatCard icon={<Network />} value="576" label={t('learn.overview.stats.nodes')} color="blue" />
              <StatCard icon={<GitBranch />} value="897" label={t('learn.overview.stats.relationships')} color="violet" />
              <StatCard icon={<BookOpen />} value="487" label={t('learn.overview.stats.works')} color="primary" />
              <StatCard icon={<Quote />} value="69,277" label={t('learn.overview.stats.passages')} color="amber" />
            </motion.div>

            {/* Three Pillars */}
            <div className="mt-20">
              <h3 className="text-2xl font-bold text-center text-academic-text mb-10">
                {t('learn.overview.pillars.title')}
              </h3>

              <div className="grid md:grid-cols-3 gap-8">
                <PillarCard
                  icon={<Network className="w-10 h-10" />}
                  title={t('learn.overview.pillars.kg.title')}
                  description={t('learn.overview.pillars.kg.description')}
                  features={t('learn.overview.pillars.kg.features', { returnObjects: true }) as string[]}
                  color="blue"
                />
                <PillarCard
                  icon={<BookOpen className="w-10 h-10" />}
                  title={t('learn.overview.pillars.texts.title')}
                  description={t('learn.overview.pillars.texts.description')}
                  features={t('learn.overview.pillars.texts.features', { returnObjects: true }) as string[]}
                  color="primary"
                />
                <PillarCard
                  icon={<Sparkles className="w-10 h-10" />}
                  title={t('learn.overview.pillars.ai.title')}
                  description={t('learn.overview.pillars.ai.description')}
                  features={t('learn.overview.pillars.ai.features', { returnObjects: true }) as string[]}
                  color="violet"
                />
              </div>
            </div>
          </div>
        </section>

        {/* Knowledge Graph Section */}
        <section id="knowledge-graph" className="py-20 px-6 bg-white/60 backdrop-blur-sm">
          <div className="max-w-6xl mx-auto">
            <SectionHeader
              icon={<Network className="w-8 h-8" />}
              title={t('learn.knowledgeGraph.title')}
              subtitle={t('learn.knowledgeGraph.subtitle')}
            />

            {/* What is a Knowledge Graph */}
            <motion.div
              variants={fadeInUp}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true }}
              className="mt-12"
            >
              <Card variant="elevated" padding="xl">
                <CardContent>
                  <div className="grid md:grid-cols-2 gap-12 items-center">
                    <div>
                      <h3 className="text-2xl font-bold text-academic-text mb-4">
                        What is a Knowledge Graph?
                      </h3>
                      <p className="text-academic-muted mb-6 leading-relaxed">
                        A knowledge graph is a network of interconnected information where:
                      </p>
                      <div className="space-y-4">
                        <div className="flex items-start gap-3">
                          <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center flex-shrink-0">
                            <div className="w-4 h-4 rounded-full bg-blue-500" />
                          </div>
                          <div>
                            <p className="font-medium text-academic-text">Nodes = Entities</p>
                            <p className="text-sm text-academic-muted">People, concepts, arguments, works</p>
                          </div>
                        </div>
                        <div className="flex items-start gap-3">
                          <div className="w-10 h-10 rounded-lg bg-violet-100 flex items-center justify-center flex-shrink-0">
                            <ArrowRight className="w-5 h-5 text-violet-500" />
                          </div>
                          <div>
                            <p className="font-medium text-academic-text">Edges = Relationships</p>
                            <p className="text-sm text-academic-muted">"formulated", "opposes", "influenced"</p>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Interactive Mini Graph */}
                    <div className="relative h-80">
                      <KnowledgeGraphDemo />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>

            {/* Node Types */}
            <div className="mt-16">
              <h3 className="text-xl font-bold text-academic-text mb-8 text-center">
                Types of Nodes
              </h3>
              <motion.div
                variants={staggerContainer}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true }}
                className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4"
              >
                <NodeTypeCard icon={<Users />} type="Persons" count={179} color="blue" example="Aristotle, Chrysippus" />
                <NodeTypeCard icon={<Brain />} type="Concepts" count={121} color="violet" example="ἐφ' ἡμῖν, fate" />
                <NodeTypeCard icon={<Target />} type="Arguments" count={116} color="primary" example="Lazy Argument" />
                <NodeTypeCard icon={<BookOpen />} type="Works" count={66} color="amber" example="De Fato" />
                <NodeTypeCard icon={<RotateCcw />} type="Reformulations" count={53} color="rose" example="Stoic → Christian" />
                <NodeTypeCard icon={<Quote />} type="Quotes" count={14} color="emerald" example="Primary evidence" />
              </motion.div>
            </div>

            {/* Timeline */}
            <div className="mt-20">
              <h3 className="text-xl font-bold text-academic-text mb-8 text-center">
                1,200 Years of Philosophical Debate
              </h3>
              <TimelineVisualization />
            </div>
          </div>
        </section>

        {/* Embeddings Section - Enhanced with 3D Visualization */}
        <section id="embeddings" className="py-20 px-6 bg-gradient-to-b from-white/60 via-slate-800/90 to-slate-900">
          <div className="max-w-6xl mx-auto">
            <SectionHeader
              icon={<Brain className="w-8 h-8" />}
              title={t('learn.embeddings.title')}
              subtitle={t('learn.embeddings.subtitle')}
            />

            <EmbeddingsExplanation />

            {/* The Embedding Journey - Animated Process Visualization */}
            <motion.div
              initial={{ opacity: 0, y: 40 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.8 }}
              className="mt-16"
            >
              <div className="text-center mb-8">
                <h3 className="text-2xl font-bold text-white mb-3">
                  Watch Text Become a Vector
                </h3>
                <p className="text-white/60 max-w-2xl mx-auto">
                  Experience the magical journey of how philosophical text transforms into a
                  3,072-dimensional embedding. Click Play to watch the 6-stage process.
                </p>
              </div>

              <div className="relative rounded-3xl overflow-hidden shadow-2xl border border-white/10">
                <Suspense
                  fallback={
                    <div className="h-[550px] bg-slate-950 flex items-center justify-center">
                      <div className="text-center">
                        <Loader2 className="w-12 h-12 text-cyan-400 animate-spin mx-auto mb-4" />
                        <p className="text-white/60">Loading embedding journey...</p>
                      </div>
                    </div>
                  }
                >
                  <EmbeddingJourneyUltra className="h-[600px]" />
                </Suspense>
              </div>
            </motion.div>

            {/* 3D Interactive Semantic Space */}
            <motion.div
              initial={{ opacity: 0, y: 40 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.8 }}
              className="mt-16"
            >
              <div className="text-center mb-8">
                <h3 className="text-2xl font-bold text-white mb-3">
                  Explore the Semantic Space
                </h3>
                <p className="text-white/60 max-w-2xl mx-auto">
                  Each glowing point represents a philosophical concept. Concepts with similar meanings
                  cluster together in 3D space. Drag to rotate, scroll to zoom.
                </p>
              </div>

              <div className="relative rounded-3xl overflow-hidden shadow-2xl border border-white/10">
                <Suspense
                  fallback={
                    <div className="h-[600px] bg-slate-900 flex items-center justify-center">
                      <div className="text-center">
                        <Loader2 className="w-12 h-12 text-blue-400 animate-spin mx-auto mb-4" />
                        <p className="text-white/60">Loading 3D visualization...</p>
                      </div>
                    </div>
                  }
                >
                  <EmbeddingsVisualization3D className="h-[600px]" />
                </Suspense>
              </div>

              {/* Legend */}
              <div className="mt-6 flex flex-wrap justify-center gap-6 text-sm">
                <div className="flex items-center gap-2 text-white/70">
                  <div className="w-3 h-3 rounded-full bg-blue-400" />
                  Stoic Concepts
                </div>
                <div className="flex items-center gap-2 text-white/70">
                  <div className="w-3 h-3 rounded-full bg-violet-400" />
                  Epicurean Concepts
                </div>
                <div className="flex items-center gap-2 text-white/70">
                  <div className="w-3 h-3 rounded-full bg-green-400" />
                  Aristotelian Concepts
                </div>
                <div className="flex items-center gap-2 text-white/70">
                  <div className="w-3 h-3 rounded-full bg-pink-400" />
                  Platonic Concepts
                </div>
                <div className="flex items-center gap-2 text-white/70">
                  <div className="w-3 h-3 rounded-full bg-amber-400" />
                  Core Free Will Concepts
                </div>
              </div>
            </motion.div>
          </div>
        </section>

        {/* GraphRAG Section */}
        <section id="graphrag" className="py-20 px-6 bg-white/60 backdrop-blur-sm">
          <div className="max-w-6xl mx-auto">
            <SectionHeader
              icon={<Sparkles className="w-8 h-8" />}
              title={t('learn.graphrag.title')}
              subtitle={t('learn.graphrag.subtitle')}
            />

            <GraphRAGPipelineDemo />
          </div>
        </section>

        {/* Hybrid Search Section */}
        <section id="hybrid-search" className="py-20 px-6 bg-white/60 backdrop-blur-sm">
          <div className="max-w-6xl mx-auto">
            <SectionHeader
              icon={<Search className="w-8 h-8" />}
              title={t('learn.hybridSearch.title')}
              subtitle={t('learn.hybridSearch.subtitle')}
            />

            <HybridSearchExplanation />
          </div>
        </section>

        {/* Ancient Texts Section */}
        <section id="ancient-texts" className="py-20 px-6 bg-white/60 backdrop-blur-sm">
          <div className="max-w-6xl mx-auto">
            <SectionHeader
              icon={<BookOpen className="w-8 h-8" />}
              title={t('learn.ancientTexts.title')}
              subtitle={t('learn.ancientTexts.subtitle')}
            />

            <AncientTextsShowcase />
          </div>
        </section>

        {/* FAIR Principles Section */}
        <section id="fair" className="py-20 px-6 bg-white/60 backdrop-blur-sm">
          <div className="max-w-6xl mx-auto">
            <SectionHeader
              icon={<CheckCircle2 className="w-8 h-8" />}
              title={t('learn.fair.title')}
              subtitle={t('learn.fair.subtitle')}
            />

            <FAIRPrinciplesDisplay />
          </div>
        </section>

        {/* Glossary Section */}
        <section id="glossary" className="py-20 px-6 bg-white/60 backdrop-blur-sm">
          <div className="max-w-6xl mx-auto">
            <SectionHeader
              icon={<BookMarked className="w-8 h-8" />}
              title={t('learn.glossary.title')}
              subtitle={t('learn.glossary.subtitle')}
            />

            <GlossarySection />
          </div>
        </section>

      </main>
    </div>
  );
}

// ============ HELPER COMPONENTS ============

function SectionHeader({ icon, title, subtitle }: { icon: React.ReactNode; title: string; subtitle: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      className="text-center mb-12"
    >
      <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-primary-100 text-primary-600 mb-4">
        {icon}
      </div>
      <h2 className="text-3xl md:text-4xl font-bold text-academic-text mb-3">{title}</h2>
      <p className="text-lg text-academic-muted max-w-2xl mx-auto">{subtitle}</p>
    </motion.div>
  );
}

function StatCard({ icon, value, label, color }: { icon: React.ReactNode; value: string; label: string; color: string }) {
  const colorClasses: Record<string, string> = {
    blue: 'bg-blue-100 text-blue-600',
    violet: 'bg-violet-100 text-violet-600',
    primary: 'bg-primary-100 text-primary-600',
    amber: 'bg-amber-100 text-amber-600',
  };

  return (
    <motion.div variants={staggerItem}>
      <Card variant="elevated" padding="lg" className="text-center hover:shadow-xl transition-shadow">
        <CardContent>
          <div className={`inline-flex items-center justify-center w-12 h-12 rounded-xl ${colorClasses[color]} mb-3`}>
            {icon}
          </div>
          <div className="text-3xl font-bold text-academic-text mb-1">{value}</div>
          <div className="text-sm text-academic-muted">{label}</div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

function PillarCard({ icon, title, description, features, color }: {
  icon: React.ReactNode;
  title: string;
  description: string;
  features: string[];
  color: string;
}) {
  const colorClasses: Record<string, { bg: string; border: string; icon: string }> = {
    blue: { bg: 'bg-blue-50', border: 'border-blue-200', icon: 'bg-blue-100 text-blue-600' },
    primary: { bg: 'bg-primary-50', border: 'border-primary-200', icon: 'bg-primary-100 text-primary-600' },
    violet: { bg: 'bg-violet-50', border: 'border-violet-200', icon: 'bg-violet-100 text-violet-600' },
  };

  return (
    <motion.div
      variants={fadeInUp}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true }}
    >
      <Card variant="outlined" padding="lg" className={`h-full ${colorClasses[color].bg} ${colorClasses[color].border}`}>
        <CardContent>
          <div className={`inline-flex items-center justify-center w-16 h-16 rounded-2xl ${colorClasses[color].icon} mb-4`}>
            {icon}
          </div>
          <h3 className="text-xl font-bold text-academic-text mb-3">{title}</h3>
          <p className="text-sm text-academic-muted mb-4 leading-relaxed">{description}</p>
          <ul className="space-y-2">
            {features.map((feature, i) => (
              <li key={i} className="flex items-center gap-2 text-sm text-academic-muted">
                <CheckCircle2 className="w-4 h-4 text-green-500 flex-shrink-0" />
                {feature}
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>
    </motion.div>
  );
}

function NodeTypeCard({ icon, type, count, color, example }: {
  icon: React.ReactNode;
  type: string;
  count: number;
  color: string;
  example: string;
}) {
  const colorClasses: Record<string, string> = {
    blue: 'bg-blue-100 text-blue-600 border-blue-200',
    violet: 'bg-violet-100 text-violet-600 border-violet-200',
    primary: 'bg-primary-100 text-primary-600 border-primary-200',
    amber: 'bg-amber-100 text-amber-600 border-amber-200',
    rose: 'bg-rose-100 text-rose-600 border-rose-200',
    emerald: 'bg-emerald-100 text-emerald-600 border-emerald-200',
  };

  return (
    <motion.div variants={staggerItem}>
      <div className={`p-4 rounded-xl border ${colorClasses[color]} text-center`}>
        <div className="inline-flex items-center justify-center w-10 h-10 rounded-lg bg-white mb-2">
          {icon}
        </div>
        <div className="font-bold text-academic-text">{count}</div>
        <div className="text-sm font-medium">{type}</div>
        <div className="text-xs text-academic-muted mt-1 truncate">{example}</div>
      </div>
    </motion.div>
  );
}

// Interactive Knowledge Graph Demo
function KnowledgeGraphDemo() {
  const nodes = [
    { id: 'stoicism', label: 'Stoicism', x: 50, y: 20, type: 'school' },
    { id: 'chrysippus', label: 'Chrysippus', x: 20, y: 50, type: 'person' },
    { id: 'fate', label: 'Fate', x: 80, y: 50, type: 'concept' },
    { id: 'compatibilism', label: 'Compatibilism', x: 50, y: 80, type: 'argument' },
  ];

  const edges = [
    { from: 'stoicism', to: 'chrysippus', label: 'founder' },
    { from: 'stoicism', to: 'fate', label: 'core concept' },
    { from: 'chrysippus', to: 'compatibilism', label: 'formulated' },
    { from: 'fate', to: 'compatibilism', label: 'addresses' },
  ];

  const [hoveredNode, setHoveredNode] = useState<string | null>(null);

  const typeColors: Record<string, string> = {
    school: '#3b82f6',
    person: '#8b5cf6',
    concept: '#f59e0b',
    argument: '#10b981',
  };

  return (
    <div className="w-full h-full bg-gray-50 rounded-2xl border border-gray-200 relative overflow-hidden">
      <svg className="w-full h-full" viewBox="0 0 100 100">
        {/* Edges */}
        {edges.map((edge, i) => {
          const from = nodes.find(n => n.id === edge.from)!;
          const to = nodes.find(n => n.id === edge.to)!;
          return (
            <g key={i}>
              <line
                x1={from.x}
                y1={from.y}
                x2={to.x}
                y2={to.y}
                stroke="#cbd5e1"
                strokeWidth="0.5"
                strokeDasharray={hoveredNode && (hoveredNode === edge.from || hoveredNode === edge.to) ? '0' : '2,2'}
                className="transition-all duration-300"
                style={{
                  stroke: hoveredNode && (hoveredNode === edge.from || hoveredNode === edge.to) ? '#3b82f6' : '#cbd5e1',
                  strokeWidth: hoveredNode && (hoveredNode === edge.from || hoveredNode === edge.to) ? 1 : 0.5,
                }}
              />
            </g>
          );
        })}

        {/* Nodes */}
        {nodes.map((node) => (
          <g
            key={node.id}
            onMouseEnter={() => setHoveredNode(node.id)}
            onMouseLeave={() => setHoveredNode(null)}
            className="cursor-pointer"
          >
            <motion.circle
              cx={node.x}
              cy={node.y}
              r={hoveredNode === node.id ? 8 : 6}
              fill={typeColors[node.type]}
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.2 * nodes.indexOf(node), type: 'spring' }}
              className="transition-all duration-200"
            />
            <text
              x={node.x}
              y={node.y + 14}
              textAnchor="middle"
              fontSize="4"
              fill="#374151"
              fontWeight={hoveredNode === node.id ? 'bold' : 'normal'}
            >
              {node.label}
            </text>
          </g>
        ))}
      </svg>

      {/* Legend */}
      <div className="absolute bottom-2 left-2 flex gap-3 text-xs">
        {Object.entries(typeColors).map(([type, color]) => (
          <div key={type} className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
            <span className="capitalize text-gray-600">{type}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// Timeline Visualization
function TimelineVisualization() {
  const periods = [
    { era: 'Presocratic', years: '6th-5th c. BCE', philosophers: ['Heraclitus', 'Democritus'], color: 'bg-gray-400' },
    { era: 'Classical', years: '5th-4th c. BCE', philosophers: ['Aristotle', 'Plato'], color: 'bg-blue-500' },
    { era: 'Hellenistic', years: '4th-1st c. BCE', philosophers: ['Chrysippus', 'Epicurus', 'Carneades'], color: 'bg-violet-500' },
    { era: 'Imperial', years: '1st-3rd c. CE', philosophers: ['Epictetus', 'Marcus Aurelius'], color: 'bg-primary-500' },
    { era: 'Late Antiquity', years: '3rd-6th c. CE', philosophers: ['Plotinus', 'Augustine'], color: 'bg-amber-500' },
  ];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      whileInView={{ opacity: 1 }}
      viewport={{ once: true }}
      className="relative"
    >
      {/* Timeline line */}
      <div className="absolute top-8 left-0 right-0 h-1 bg-gray-200 rounded-full" />

      <div className="flex justify-between">
        {periods.map((period, i) => (
          <motion.div
            key={period.era}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: i * 0.1 }}
            className="flex flex-col items-center text-center w-1/5"
          >
            <div className={`w-4 h-4 rounded-full ${period.color} mb-4 z-10 relative`}>
              <div className={`absolute inset-0 ${period.color} rounded-full animate-ping opacity-30`} />
            </div>
            <h4 className="font-bold text-sm text-academic-text">{period.era}</h4>
            <p className="text-xs text-academic-muted mb-2">{period.years}</p>
            <div className="space-y-1">
              {period.philosophers.map((p) => (
                <span key={p} className="block text-xs text-primary-600">{p}</span>
              ))}
            </div>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}

// Embeddings Explanation
function EmbeddingsExplanation() {
  const [step, setStep] = useState(0);

  const steps = [
    {
      title: 'Text Input',
      description: 'Any text can be converted to an embedding',
      visual: (
        <div className="p-4 bg-gray-100 rounded-lg font-mono text-sm">
          "The Stoics believed fate is compatible with freedom"
        </div>
      )
    },
    {
      title: 'AI Processing',
      description: 'Google Gemini reads the text and encodes its meaning',
      visual: (
        <div className="flex items-center justify-center gap-4">
          <div className="p-3 bg-blue-100 rounded-lg">
            <Brain className="w-8 h-8 text-blue-600 animate-pulse" />
          </div>
          <ArrowRight className="w-6 h-6 text-gray-400" />
          <div className="p-3 bg-violet-100 rounded-lg">
            <Cpu className="w-8 h-8 text-violet-600" />
          </div>
        </div>
      )
    },
    {
      title: 'Vector Output',
      description: '3,072 numbers that capture the meaning',
      visual: (
        <div className="p-4 bg-gray-900 rounded-lg font-mono text-xs text-green-400 overflow-x-auto">
          [0.156, -0.234, 0.891, 0.023, -0.456, 0.789, 0.012, ...]
          <span className="text-gray-500 ml-2">// 3,072 dimensions</span>
        </div>
      )
    }
  ];

  return (
    <motion.div
      variants={fadeInUp}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true }}
      className="mt-12"
    >
      {/* GPS Analogy */}
      <Card variant="elevated" padding="xl" className="mb-12">
        <CardContent>
          <div className="grid md:grid-cols-2 gap-8 items-center">
            <div>
              <h3 className="text-2xl font-bold text-academic-text mb-4">
                Think of Embeddings as GPS for Ideas
              </h3>
              <p className="text-academic-muted mb-6 leading-relaxed">
                Just like GPS coordinates tell you where a city is in physical space,
                embeddings tell you where an idea is in <span className="font-medium text-academic-text">semantic space</span>.
              </p>
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                  <p className="font-medium text-blue-800 mb-2">Physical World</p>
                  <p className="text-sm text-blue-600">Paris → (48.86, 2.35)</p>
                  <p className="text-sm text-blue-600">London → (51.51, -0.13)</p>
                  <p className="text-xs text-blue-500 mt-2">Close = Similar location</p>
                </div>
                <div className="p-4 bg-violet-50 rounded-lg border border-violet-200">
                  <p className="font-medium text-violet-800 mb-2">Semantic World</p>
                  <p className="text-sm text-violet-600">"Free will" → [0.89, ...]</p>
                  <p className="text-sm text-violet-600">"Liberty" → [0.91, ...]</p>
                  <p className="text-xs text-violet-500 mt-2">Close = Similar meaning</p>
                </div>
              </div>
            </div>
            <div className="relative h-64 bg-gradient-to-br from-blue-100 to-violet-100 rounded-2xl p-6">
              <SemanticSpaceVisualization />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Step by Step Process */}
      <div className="grid md:grid-cols-3 gap-6">
        {steps.map((s, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: i * 0.2 }}
          >
            <Card
              variant={step === i ? 'gradient' : 'default'}
              padding="lg"
              className="h-full cursor-pointer hover:shadow-lg transition-all"
              onClick={() => setStep(i)}
            >
              <CardContent>
                <div className="flex items-center gap-3 mb-4">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm
                    ${step === i ? 'bg-primary-600 text-white' : 'bg-gray-200 text-gray-600'}`}>
                    {i + 1}
                  </div>
                  <h4 className="font-bold text-academic-text">{s.title}</h4>
                </div>
                <p className="text-sm text-academic-muted mb-4">{s.description}</p>
                {s.visual}
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Why it matters */}
      <div className="mt-12 grid md:grid-cols-2 gap-8">
        <Card variant="outlined" padding="lg" className="border-red-200 bg-red-50/30">
          <CardContent>
            <h4 className="font-bold text-red-700 mb-3 flex items-center gap-2">
              <Search className="w-5 h-5" />
              Keyword Search
            </h4>
            <p className="text-sm text-academic-muted mb-4">
              Only finds exact word matches. Misses synonyms and related concepts.
            </p>
            <div className="space-y-2 text-sm">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-green-500" />
                <span>Finds: "free will"</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-4 h-4 text-red-500">✗</span>
                <span className="text-academic-muted">Misses: "liberty", "ἐφ' ἡμῖν", "liberum arbitrium"</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card variant="outlined" padding="lg" className="border-green-200 bg-green-50/30">
          <CardContent>
            <h4 className="font-bold text-green-700 mb-3 flex items-center gap-2">
              <Brain className="w-5 h-5" />
              Semantic Search
            </h4>
            <p className="text-sm text-academic-muted mb-4">
              Finds texts by meaning, regardless of exact words used.
            </p>
            <div className="space-y-2 text-sm">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-green-500" />
                <span>Finds: "free will", "liberty", "ἐφ' ἡμῖν"</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-green-500" />
                <span>Finds: "liberum arbitrium", "moral agency"</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </motion.div>
  );
}

// Semantic Space Visualization
function SemanticSpaceVisualization() {
  const concepts = [
    { label: 'Free Will', x: 50, y: 30, size: 'lg' },
    { label: 'Liberty', x: 60, y: 35, size: 'md' },
    { label: 'ἐφ\' ἡμῖν', x: 45, y: 40, size: 'sm' },
    { label: 'Fate', x: 70, y: 60, size: 'md' },
    { label: 'Astronomy', x: 20, y: 80, size: 'sm' },
  ];

  const sizeClasses = {
    lg: 'w-24 text-sm',
    md: 'w-20 text-xs',
    sm: 'w-16 text-2xs',
  };

  return (
    <div className="relative w-full h-full">
      {concepts.map((concept, i) => (
        <motion.div
          key={concept.label}
          initial={{ opacity: 0, scale: 0 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: i * 0.2, type: 'spring' }}
          className={`absolute ${sizeClasses[concept.size as keyof typeof sizeClasses]}
            p-2 bg-white rounded-lg shadow-md text-center font-medium
            ${concept.label === 'Astronomy' ? 'opacity-50' : ''}`}
          style={{ left: `${concept.x}%`, top: `${concept.y}%`, transform: 'translate(-50%, -50%)' }}
        >
          {concept.label}
        </motion.div>
      ))}

      {/* Connection lines */}
      <svg className="absolute inset-0 w-full h-full" style={{ pointerEvents: 'none' }}>
        <line x1="50%" y1="30%" x2="60%" y2="35%" stroke="#3b82f6" strokeWidth="2" opacity="0.5" />
        <line x1="50%" y1="30%" x2="45%" y2="40%" stroke="#3b82f6" strokeWidth="2" opacity="0.5" />
        <line x1="60%" y1="35%" x2="45%" y2="40%" stroke="#3b82f6" strokeWidth="1" opacity="0.3" />
      </svg>
    </div>
  );
}

// GraphRAG Pipeline Demo
function GraphRAGPipelineDemo() {
  const [activeStep, setActiveStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  const steps = [
    {
      number: 1,
      title: 'Semantic Search',
      description: 'Convert question to embedding → Find similar nodes in knowledge graph',
      detail: 'Your question becomes a 3,072-number vector. We compare it to all 576 KG nodes and find the top 10 most similar.',
      icon: <Search className="w-6 h-6" />,
      color: 'blue',
      example: {
        input: '"What did Stoics say about fate?"',
        output: 'Found: Stoicism (0.89), Fate (0.87), Chrysippus (0.84)...'
      }
    },
    {
      number: 2,
      title: 'Graph Traversal',
      description: 'Expand from starting nodes → Follow relationships to related concepts',
      detail: 'From the 10 starting nodes, we follow edges like "formulated", "opposes", "influenced" to find ~25-50 related nodes.',
      icon: <Network className="w-6 h-6" />,
      color: 'violet',
      example: {
        input: 'Starting: Stoicism, Fate, Chrysippus',
        output: 'Expanded: +Determinism, +Epictetus, +Compatibilism...'
      }
    },
    {
      number: 3,
      title: 'Citation Extraction',
      description: 'Gather ancient sources and modern scholarship from expanded nodes',
      detail: 'Each KG node has "ancient_sources" and "modern_scholarship" fields. We extract and deduplicate all citations.',
      icon: <BookOpen className="w-6 h-6" />,
      color: 'amber',
      example: {
        input: '25 expanded nodes',
        output: '10 ancient sources + 12 modern citations'
      }
    },
    {
      number: 4,
      title: 'Context Building',
      description: 'Organize into LOCAL (direct), GLOBAL (thematic), BRIDGE (paths)',
      detail: 'Three-level context: LOCAL = direct answers, GLOBAL = community summaries, BRIDGE = reasoning paths.',
      icon: <Layers className="w-6 h-6" />,
      color: 'primary',
      example: {
        input: 'Raw nodes and citations',
        output: '~3,000 chars of structured context'
      }
    },
    {
      number: 5,
      title: 'AI Synthesis',
      description: 'LLM generates scholarly answer with inline citations',
      detail: 'Gemini reads the context and generates an answer, following strict rules: cite sources, never fabricate Greek/Latin text.',
      icon: <Sparkles className="w-6 h-6" />,
      color: 'emerald',
      example: {
        input: 'Context + question',
        output: 'Cited answer with [1], [2] references'
      }
    }
  ];

  useEffect(() => {
    if (isPlaying) {
      const timer = setInterval(() => {
        setActiveStep((prev) => (prev + 1) % steps.length);
      }, 3000);
      return () => clearInterval(timer);
    }
  }, [isPlaying, steps.length]);

  const colorClasses: Record<string, { bg: string; border: string; text: string }> = {
    blue: { bg: 'bg-blue-100', border: 'border-blue-300', text: 'text-blue-600' },
    violet: { bg: 'bg-violet-100', border: 'border-violet-300', text: 'text-violet-600' },
    amber: { bg: 'bg-amber-100', border: 'border-amber-300', text: 'text-amber-600' },
    primary: { bg: 'bg-primary-100', border: 'border-primary-300', text: 'text-primary-600' },
    emerald: { bg: 'bg-emerald-100', border: 'border-emerald-300', text: 'text-emerald-600' },
  };

  return (
    <motion.div
      variants={fadeInUp}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true }}
      className="mt-12"
    >
      {/* Controls */}
      <div className="flex justify-center gap-4 mb-8">
        <button
          onClick={() => setIsPlaying(!isPlaying)}
          className="px-4 py-2 bg-primary-600 text-white rounded-lg flex items-center gap-2 hover:bg-primary-700 transition-colors"
        >
          {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
          {isPlaying ? 'Pause' : 'Play Animation'}
        </button>
        <button
          onClick={() => setActiveStep(0)}
          className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg flex items-center gap-2 hover:bg-gray-300 transition-colors"
        >
          <RotateCcw className="w-4 h-4" />
          Reset
        </button>
      </div>

      {/* Pipeline visualization */}
      <div className="relative">
        {/* Progress line */}
        <div className="absolute top-8 left-0 right-0 h-1 bg-gray-200 rounded-full hidden md:block">
          <motion.div
            className="h-full bg-primary-500 rounded-full"
            initial={{ width: '0%' }}
            animate={{ width: `${((activeStep + 1) / steps.length) * 100}%` }}
            transition={{ duration: 0.5 }}
          />
        </div>

        {/* Steps */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          {steps.map((step, i) => (
            <motion.div
              key={step.number}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              onClick={() => setActiveStep(i)}
              className="cursor-pointer"
            >
              <div className={`relative ${activeStep === i ? 'scale-105' : ''} transition-transform`}>
                {/* Step circle */}
                <div className={`w-16 h-16 mx-auto rounded-2xl flex items-center justify-center mb-4 transition-all
                  ${activeStep >= i
                    ? `${colorClasses[step.color].bg} ${colorClasses[step.color].border} border-2 ${colorClasses[step.color].text}`
                    : 'bg-gray-100 border-2 border-gray-200 text-gray-400'}`}
                >
                  {step.icon}
                </div>

                <h4 className={`text-sm font-bold text-center mb-1 ${activeStep === i ? 'text-academic-text' : 'text-academic-muted'}`}>
                  {step.title}
                </h4>
                <p className="text-xs text-academic-muted text-center hidden md:block">
                  {step.description}
                </p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Detail Panel */}
      <AnimatePresence mode="wait">
        <motion.div
          key={activeStep}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          className="mt-8"
        >
          <Card variant="elevated" padding="xl" className={`${colorClasses[steps[activeStep].color].bg} border ${colorClasses[steps[activeStep].color].border}`}>
            <CardContent>
              <div className="grid md:grid-cols-2 gap-8">
                <div>
                  <h3 className="text-xl font-bold text-academic-text mb-3">
                    Stage {steps[activeStep].number}: {steps[activeStep].title}
                  </h3>
                  <p className="text-academic-muted leading-relaxed">
                    {steps[activeStep].detail}
                  </p>
                </div>
                <div className="space-y-4">
                  <div className="p-4 bg-white/50 rounded-lg">
                    <p className="text-xs font-medium text-academic-muted mb-2">INPUT</p>
                    <p className="font-mono text-sm">{steps[activeStep].example.input}</p>
                  </div>
                  <div className="flex justify-center">
                    <ArrowRight className="w-5 h-5 text-academic-muted rotate-90 md:rotate-0" />
                  </div>
                  <div className="p-4 bg-white/50 rounded-lg">
                    <p className="text-xs font-medium text-academic-muted mb-2">OUTPUT</p>
                    <p className="font-mono text-sm">{steps[activeStep].example.output}</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </AnimatePresence>
    </motion.div>
  );
}

// Hybrid Search Explanation
function HybridSearchExplanation() {
  return (
    <motion.div
      variants={fadeInUp}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true }}
      className="mt-12"
    >
      <div className="grid md:grid-cols-3 gap-6 mb-12">
        <SearchMethodCard
          title="Full-Text Search"
          icon={<Search className="w-6 h-6" />}
          speed="< 100ms"
          description="Exact keyword matching in passages. Fast and precise."
          strength="Speed & Precision"
          example='Query: "free will" → Finds exact matches'
          color="blue"
        />
        <SearchMethodCard
          title="Lemmatic Search"
          icon={<Languages className="w-6 h-6" />}
          speed="< 500ms"
          description="Finds all forms of a word (λόγος → λόγου, λόγῳ...)"
          strength="Morphological Awareness"
          example='Query: "λόγος" → Finds all 10+ Greek forms'
          color="violet"
        />
        <SearchMethodCard
          title="Semantic Search"
          icon={<Brain className="w-6 h-6" />}
          speed="< 2s"
          description="Finds texts by meaning using embeddings"
          strength="Conceptual Understanding"
          example={`Query: "free will" → Also finds "liberty", "ἐφ' ἡμῖν"`}
          color="primary"
        />
      </div>

      {/* RRF Explanation */}
      <Card variant="elevated" padding="xl">
        <CardContent>
          <h3 className="text-xl font-bold text-academic-text mb-4 text-center">
            Reciprocal Rank Fusion (RRF)
          </h3>
          <p className="text-academic-muted text-center mb-8 max-w-2xl mx-auto">
            Results from all three methods are merged using a formula that boosts items appearing in multiple lists.
            Items found by all three methods rank highest.
          </p>

          <div className="flex flex-col md:flex-row items-center justify-center gap-8">
            <div className="text-center">
              <div className="w-20 h-20 rounded-full bg-blue-100 flex items-center justify-center mx-auto mb-2">
                <span className="text-2xl font-bold text-blue-600">1</span>
              </div>
              <p className="text-sm">Full-text</p>
            </div>
            <span className="text-3xl text-gray-400">+</span>
            <div className="text-center">
              <div className="w-20 h-20 rounded-full bg-violet-100 flex items-center justify-center mx-auto mb-2">
                <span className="text-2xl font-bold text-violet-600">2</span>
              </div>
              <p className="text-sm">Lemmatic</p>
            </div>
            <span className="text-3xl text-gray-400">+</span>
            <div className="text-center">
              <div className="w-20 h-20 rounded-full bg-primary-100 flex items-center justify-center mx-auto mb-2">
                <span className="text-2xl font-bold text-primary-600">3</span>
              </div>
              <p className="text-sm">Semantic</p>
            </div>
            <span className="text-3xl text-gray-400">=</span>
            <div className="text-center">
              <div className="w-20 h-20 rounded-full bg-emerald-100 flex items-center justify-center mx-auto mb-2">
                <CheckCircle2 className="w-8 h-8 text-emerald-600" />
              </div>
              <p className="text-sm font-medium">Best Results</p>
            </div>
          </div>

          <div className="mt-8 p-4 bg-gray-100 rounded-lg font-mono text-sm text-center">
            RRF Score = Σ (1 / (k + rank)) where k = 60
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

function SearchMethodCard({ title, icon, speed, description, strength, example, color }: {
  title: string;
  icon: React.ReactNode;
  speed: string;
  description: string;
  strength: string;
  example: string;
  color: string;
}) {
  const colorClasses: Record<string, { bg: string; border: string; icon: string }> = {
    blue: { bg: 'bg-blue-50', border: 'border-blue-200', icon: 'bg-blue-100 text-blue-600' },
    violet: { bg: 'bg-violet-50', border: 'border-violet-200', icon: 'bg-violet-100 text-violet-600' },
    primary: { bg: 'bg-primary-50', border: 'border-primary-200', icon: 'bg-primary-100 text-primary-600' },
  };

  return (
    <Card variant="outlined" padding="lg" className={`${colorClasses[color].bg} ${colorClasses[color].border}`}>
      <CardContent>
        <div className={`inline-flex items-center justify-center w-12 h-12 rounded-xl ${colorClasses[color].icon} mb-4`}>
          {icon}
        </div>
        <h4 className="font-bold text-academic-text mb-2">{title}</h4>
        <p className="text-sm text-academic-muted mb-4">{description}</p>
        <div className="space-y-2 text-xs">
          <div className="flex justify-between">
            <span className="text-academic-muted">Speed:</span>
            <span className="font-medium">{speed}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-academic-muted">Strength:</span>
            <span className="font-medium">{strength}</span>
          </div>
        </div>
        <div className="mt-4 p-2 bg-white/50 rounded text-xs font-mono">
          {example}
        </div>
      </CardContent>
    </Card>
  );
}

// Ancient Texts Showcase
function AncientTextsShowcase() {
  const works = [
    { school: 'Stoic', works: ['Epictetus - Discourses', 'Marcus Aurelius - Meditations', 'Chrysippus (fragments)'], color: 'blue' },
    { school: 'Aristotelian', works: ['Nicomachean Ethics', 'De Interpretatione', 'Alexander of Aphrodisias'], color: 'violet' },
    { school: 'Epicurean', works: ['Epicurus - Letters', 'Lucretius - De Rerum Natura'], color: 'amber' },
    { school: 'Christian', works: ['Augustine (25+ works)', 'Origen', 'Gregory of Nyssa'], color: 'primary' },
    { school: 'Biblical', works: ['Complete SBLGNT (27 books)', 'LXX Septuagint (17 books)'], color: 'rose' },
  ];

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true }}
      className="mt-12"
    >
      <div className="grid md:grid-cols-5 gap-4 mb-12">
        {works.map((category) => (
          <motion.div key={category.school} variants={staggerItem}>
            <Card variant="default" padding="md" className="h-full">
              <CardContent>
                <h4 className="font-bold text-academic-text mb-3">{category.school}</h4>
                <ul className="space-y-1 text-xs text-academic-muted">
                  {category.works.map((work) => (
                    <li key={work} className="flex items-start gap-1">
                      <span className="text-primary-500">•</span>
                      {work}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* CTS URN Example */}
      <Card variant="elevated" padding="xl">
        <CardContent>
          <h3 className="text-xl font-bold text-academic-text mb-4">
            Canonical Citation System (CTS URN)
          </h3>
          <p className="text-academic-muted mb-6">
            Every passage has a permanent, machine-readable identifier following scholarly standards:
          </p>
          <div className="p-4 bg-gray-900 rounded-lg font-mono text-sm text-green-400 overflow-x-auto">
            urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.1
            <div className="mt-2 text-gray-400 text-xs">
              └── namespace: textgroup: work: edition: passage
            </div>
          </div>
          <p className="text-xs text-academic-muted mt-4">
            Compatible with Perseus, TLG, and PHI standards for interoperability.
          </p>
        </CardContent>
      </Card>
    </motion.div>
  );
}

// FAIR Principles Display
function FAIRPrinciplesDisplay() {
  const principles = [
    {
      letter: 'F',
      title: 'Findable',
      description: 'Persistent identifiers (CTS URNs, UUIDs), machine-readable metadata, indexed and searchable',
      icon: <Search className="w-6 h-6" />,
      color: 'blue'
    },
    {
      letter: 'A',
      title: 'Accessible',
      description: 'Open API with no authentication for reads, Swagger documentation, JSON responses',
      icon: <Globe className="w-6 h-6" />,
      color: 'violet'
    },
    {
      letter: 'I',
      title: 'Interoperable',
      description: 'CTS URN, JSON/RDF formats, TEI XML preservation, compatible with Perseus/TLG/PHI',
      icon: <GitBranch className="w-6 h-6" />,
      color: 'primary'
    },
    {
      letter: 'R',
      title: 'Reusable',
      description: 'CC BY 4.0 license, documented provenance, Zenodo DOI, traceable citations',
      icon: <RotateCcw className="w-6 h-6" />,
      color: 'emerald'
    },
  ];

  const colorClasses: Record<string, { bg: string; text: string; letter: string }> = {
    blue: { bg: 'bg-blue-100', text: 'text-blue-600', letter: 'bg-blue-500 text-white' },
    violet: { bg: 'bg-violet-100', text: 'text-violet-600', letter: 'bg-violet-500 text-white' },
    primary: { bg: 'bg-primary-100', text: 'text-primary-600', letter: 'bg-primary-500 text-white' },
    emerald: { bg: 'bg-emerald-100', text: 'text-emerald-600', letter: 'bg-emerald-500 text-white' },
  };

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true }}
      className="mt-12 grid md:grid-cols-2 lg:grid-cols-4 gap-6"
    >
      {principles.map((p) => (
        <motion.div key={p.letter} variants={staggerItem}>
          <Card variant="elevated" padding="lg" className="h-full hover:shadow-xl transition-shadow">
            <CardContent>
              <div className="flex items-center gap-3 mb-4">
                <div className={`w-12 h-12 rounded-xl ${colorClasses[p.color].letter} flex items-center justify-center text-2xl font-bold`}>
                  {p.letter}
                </div>
                <div className={`p-2 rounded-lg ${colorClasses[p.color].bg}`}>
                  <div className={colorClasses[p.color].text}>{p.icon}</div>
                </div>
              </div>
              <h4 className="font-bold text-academic-text mb-2">{p.title}</h4>
              <p className="text-sm text-academic-muted">{p.description}</p>
            </CardContent>
          </Card>
        </motion.div>
      ))}
    </motion.div>
  );
}

// Glossary Section
function GlossarySection() {
  const terms = [
    { term: 'Embedding', definition: 'A list of numbers (3,072) that represents the meaning of text. Similar meanings have similar vectors.' },
    { term: 'Vector', definition: 'A list of numbers. In EleutherIA, each text is represented by 3,072 numbers.' },
    { term: 'Semantic Search', definition: 'Finding texts by meaning, not just keywords. "Free will" also finds "liberty" and "ἐφ\' ἡμῖν".' },
    { term: 'Knowledge Graph', definition: 'A network of interconnected concepts. Nodes = entities, Edges = relationships.' },
    { term: 'GraphRAG', definition: 'Graph-based Retrieval-Augmented Generation. Combines KG + search + AI for Q&A.' },
    { term: 'Lemma', definition: 'The dictionary form of a word. "λόγου" → "λόγος". Enables finding all word forms.' },
    { term: 'RRF', definition: 'Reciprocal Rank Fusion. A formula for combining multiple ranked lists into one.' },
    { term: 'CTS URN', definition: 'Canonical Text Services Uniform Resource Name. Standard citation format for ancient texts.' },
    { term: 'FAIR', definition: 'Findable, Accessible, Interoperable, Reusable. International principles for open data.' },
    { term: 'LLM', definition: 'Large Language Model. The AI that synthesizes answers from context.' },
    { term: 'Cosine Similarity', definition: 'Measure of vector similarity. 1.0 = identical, 0.0 = completely different.' },
    { term: 'Qdrant', definition: 'Vector database optimized for storing and searching embeddings efficiently.' },
  ];

  const [searchTerm, setSearchTerm] = useState('');
  const filteredTerms = terms.filter(t =>
    t.term.toLowerCase().includes(searchTerm.toLowerCase()) ||
    t.definition.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <motion.div
      variants={fadeInUp}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true }}
      className="mt-12"
    >
      {/* Search */}
      <div className="max-w-md mx-auto mb-8">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search glossary..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          />
        </div>
      </div>

      {/* Terms */}
      <div className="grid md:grid-cols-2 gap-4">
        {filteredTerms.map((item) => (
          <motion.div
            key={item.term}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="p-4 bg-white border border-gray-200 rounded-xl hover:shadow-md transition-shadow"
          >
            <h4 className="font-bold text-academic-text mb-2">{item.term}</h4>
            <p className="text-sm text-academic-muted">{item.definition}</p>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}
