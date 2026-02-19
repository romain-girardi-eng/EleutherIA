import { useState, useRef, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { Maximize2, Minimize2, ChevronRight } from 'lucide-react';
import { HeroSection } from '../components/ui/hero-section-2';
import { MorphingParticles } from '../components/MorphingParticles';

export default function HomePage() {
  const { t } = useTranslation();
  const [isNativeFullscreen, setIsNativeFullscreen] = useState(false);
  const [isCSSFullscreen, setIsCSSFullscreen] = useState(false);
  const particleContainerRef = useRef<HTMLDivElement>(null);

  // Lock page scroll — this page is a single full-screen canvas, no scrolling needed
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    document.documentElement.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = '';
      document.documentElement.style.overflow = '';
    };
  }, []);

  const toggleFullscreen = useCallback(() => {
    const container = particleContainerRef.current;
    if (!container) return;

    // Native fullscreen (all browsers except iOS)
    if ('requestFullscreen' in document.documentElement) {
      if (!document.fullscreenElement) {
        container.requestFullscreen().catch(() => {
          // API exists but failed (e.g. iOS WKWebView) → CSS fallback
          setIsCSSFullscreen(true);
        });
      } else {
        document.exitFullscreen();
      }
    } else {
      // iOS Safari: no fullscreen API → toggle CSS overlay
      setIsCSSFullscreen(prev => !prev);
    }
  }, []);

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsNativeFullscreen(!!document.fullscreenElement);
      if (!document.fullscreenElement) setIsCSSFullscreen(false);
    };
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  const isFullscreen = isNativeFullscreen || isCSSFullscreen;

  // Codex Index — Roman numerals + hairline rules, like an ancient manuscript's table of contents
  const ctaButtons = (
    <div className="flex flex-col w-full">
      <div className="h-px bg-white/10 md:bg-zinc-200" />

      {/* I — How It Works */}
      <a
        href="/how-it-works"
        className="group flex items-center gap-3 py-3 px-1 hover:bg-white/[0.04] md:hover:bg-amber-50/60 transition-colors duration-150"
      >
        <span className="font-mono text-[10px] w-6 text-white/25 md:text-zinc-300 group-hover:text-amber-500 tracking-widest flex-shrink-0 transition-colors duration-150 select-none">
          I
        </span>
        <div className="flex-1 min-w-0">
          <div className="text-xs font-semibold tracking-wide text-white md:text-zinc-800 group-hover:text-amber-500 md:group-hover:text-amber-700 transition-colors duration-150 leading-tight">
            {t('nav.howItWorks')}
          </div>
          <div className="text-[9px] text-white/30 md:text-zinc-400 mt-0.5 leading-tight">
            Architecture · embeddings · pipeline
          </div>
        </div>
        <ChevronRight className="w-3.5 h-3.5 flex-shrink-0 text-amber-400 md:text-amber-600 opacity-0 group-hover:opacity-100 -translate-x-1 group-hover:translate-x-0 transition-all duration-200" />
      </a>

      <div className="h-px bg-white/10 md:bg-zinc-200" />

      {/* II — Knowledge Graph */}
      <a
        href="/visualizer"
        className="group flex items-center gap-3 py-3 px-1 hover:bg-white/[0.04] md:hover:bg-orange-50/60 transition-colors duration-150"
      >
        <span className="font-mono text-[10px] w-6 text-white/25 md:text-zinc-300 group-hover:text-orange-400 tracking-widest flex-shrink-0 transition-colors duration-150 select-none">
          II
        </span>
        <div className="flex-1 min-w-0">
          <div className="text-xs font-semibold tracking-wide text-white md:text-zinc-800 group-hover:text-orange-500 md:group-hover:text-orange-700 transition-colors duration-150 leading-tight">
            {t('nav.visualizer')}
          </div>
          <div className="text-[9px] text-white/30 md:text-zinc-400 mt-0.5 leading-tight">
            2,193 nodes · 8,616 edges
          </div>
        </div>
        <ChevronRight className="w-3.5 h-3.5 flex-shrink-0 text-orange-400 md:text-orange-600 opacity-0 group-hover:opacity-100 -translate-x-1 group-hover:translate-x-0 transition-all duration-200" />
      </a>

      <div className="h-px bg-white/10 md:bg-zinc-200" />

      {/* III — GraphRAG Q&A */}
      <a
        href="/graphrag"
        className="group flex items-center gap-3 py-3 px-1 hover:bg-white/[0.04] md:hover:bg-violet-50/40 transition-colors duration-150"
      >
        <span className="font-mono text-[10px] w-6 text-white/25 md:text-zinc-300 group-hover:text-violet-400 tracking-widest flex-shrink-0 transition-colors duration-150 select-none">
          III
        </span>
        <div className="flex-1 min-w-0">
          <div className="text-xs font-semibold tracking-wide text-white md:text-zinc-800 group-hover:text-violet-500 md:group-hover:text-violet-700 transition-colors duration-150 leading-tight">
            {t('nav.graphrag')}
          </div>
          <div className="text-[9px] text-white/30 md:text-zinc-400 mt-0.5 leading-tight">
            5-stage RAG · AI-powered Q&A
          </div>
        </div>
        <ChevronRight className="w-3.5 h-3.5 flex-shrink-0 text-violet-400 md:text-violet-600 opacity-0 group-hover:opacity-100 -translate-x-1 group-hover:translate-x-0 transition-all duration-200" />
      </a>

      <div className="h-px bg-white/10 md:bg-zinc-200" />
    </div>
  );

  return (
    <div className="min-h-screen relative">
      {/* Main Content */}
      <main className="min-h-screen relative">
        <HeroSection
          logo={{ url: "/logo.svg", alt: "EleutherIA" }}
          title={
            <>
              {t('learn.hero.title')} <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-orange-400 to-amber-300">{t('learn.hero.titleHighlight')}</span>
            </>
          }
          subtitle={t('learn.hero.subtitle')}
          callToAction={{
            text: t('learn.hero.cta'),
            href: "/how-it-works",
          }}
          ctaArea={ctaButtons}
          backgroundComponent={
            <div
              ref={particleContainerRef}
              className={isCSSFullscreen ? "fixed inset-0 z-[9999] bg-zinc-950" : "absolute inset-0 bg-zinc-950"}
            >
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
      </main>
    </div>
  );
}
