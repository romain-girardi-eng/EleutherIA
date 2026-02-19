import { useState, useRef, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { Maximize2, Minimize2, ArrowRight, Network, Sparkles } from 'lucide-react';
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

  const ctaButtons = (
    <>
      {/* Primary CTA */}
      <a
        href="/how-it-works"
        className="group flex items-center justify-between w-full rounded-xl bg-gradient-to-r from-orange-500 to-amber-400 px-5 py-3.5 text-white font-semibold text-sm hover:from-orange-400 hover:to-amber-300 hover:shadow-[0_0_24px_rgba(249,115,22,0.35)] transition-all duration-200"
      >
        <span>{t('learn.hero.cta')}</span>
        <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-0.5" />
      </a>

      {/* Secondary pair — minimal bordered cards */}
      <div className="grid grid-cols-2 gap-2">
        <a
          href="/visualizer"
          className="group flex flex-col gap-0.5 rounded-xl px-4 py-3 border border-white/15 md:border-zinc-200 bg-white/5 md:bg-white hover:border-orange-400 md:hover:border-orange-400 transition-colors duration-200"
        >
          <div className="flex items-center gap-1.5">
            <Network className="w-3.5 h-3.5 text-orange-400 md:text-orange-500 flex-shrink-0" />
            <span className="font-semibold text-xs text-white md:text-zinc-800 group-hover:text-orange-400 md:group-hover:text-orange-600 transition-colors">{t('nav.visualizer')}</span>
          </div>
          <span className="text-[9px] text-white/35 md:text-zinc-400">2,193 nodes · 8,616 edges</span>
        </a>
        <a
          href="/graphrag"
          className="group flex flex-col gap-0.5 rounded-xl px-4 py-3 border border-white/15 md:border-zinc-200 bg-white/5 md:bg-white hover:border-violet-400 md:hover:border-violet-400 transition-colors duration-200"
        >
          <div className="flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-violet-400 md:text-violet-500 flex-shrink-0" />
            <span className="font-semibold text-xs text-white md:text-zinc-800 group-hover:text-violet-400 md:group-hover:text-violet-600 transition-colors">{t('nav.graphrag')}</span>
          </div>
          <span className="text-[9px] text-white/35 md:text-zinc-400">5-stage RAG · AI-powered</span>
        </a>
      </div>
    </>
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
