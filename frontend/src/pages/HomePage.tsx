import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { Maximize2, Minimize2, ArrowRight, Network, Sparkles } from 'lucide-react';
import { HeroSection } from '../components/ui/hero-section-2';
import { MorphingParticles } from '../components/MorphingParticles';

export default function HomePage() {
  const { t } = useTranslation();
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

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  const ctaButtons = (
    <>
      <style>{`
        @property --lit-angle {
          syntax: '<angle>';
          initial-value: 0deg;
          inherits: false;
        }
        @keyframes lit-spin {
          to { --lit-angle: 360deg; }
        }
        .lit-border-wrap {
          background: conic-gradient(
            from var(--lit-angle),
            transparent 0%,
            transparent 25%,
            var(--c1) 44%,
            var(--c2) 56%,
            transparent 75%,
            transparent 100%
          );
          animation: lit-spin 3s linear infinite;
          padding: 1.5px;
          border-radius: 0.75rem;
          display: block;
        }
        .lit-border-wrap:hover {
          animation-duration: 0.75s;
        }
      `}</style>

      {/* Primary CTA */}
      <a
        href="/how-it-works"
        className="group flex items-center justify-between w-full rounded-xl bg-gradient-to-r from-orange-500 to-amber-400 px-5 py-3.5 text-white font-semibold text-sm tracking-wide hover:from-orange-400 hover:to-amber-300 hover:shadow-[0_0_28px_rgba(249,115,22,0.4)] hover:scale-[1.02] active:scale-[0.98] transition-all duration-200"
      >
        <span>{t('learn.hero.cta')}</span>
        <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-0.5" />
      </a>

      {/* Secondary pair */}
      <div className="grid grid-cols-2 gap-2.5">
        <a
          href="/visualizer"
          className="lit-border-wrap"
          style={{ '--c1': '#f97316', '--c2': '#22d3ee' } as React.CSSProperties}
        >
          <div className="rounded-[calc(0.75rem-1.5px)] px-3.5 py-2.5 flex flex-col gap-0.5 bg-zinc-900 md:bg-white h-full">
            <div className="flex items-center gap-1.5">
              <Network className="w-3.5 h-3.5 text-cyan-400 md:text-cyan-600" />
              <span className="font-semibold text-xs text-white md:text-zinc-800">{t('nav.visualizer')}</span>
            </div>
            <span className="text-[9px] leading-tight text-white/40 md:text-zinc-400">2,193 nodes · 8,616 edges</span>
          </div>
        </a>
        <a
          href="/graphrag"
          className="lit-border-wrap"
          style={{ '--c1': '#a78bfa', '--c2': '#f472b6' } as React.CSSProperties}
        >
          <div className="rounded-[calc(0.75rem-1.5px)] px-3.5 py-2.5 flex flex-col gap-0.5 bg-zinc-900 md:bg-white h-full">
            <div className="flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-violet-400 md:text-violet-600" />
              <span className="font-semibold text-xs text-white md:text-zinc-800">{t('nav.graphrag')}</span>
            </div>
            <span className="text-[9px] leading-tight text-white/40 md:text-zinc-400">5-stage RAG · AI-powered</span>
          </div>
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
              className="absolute inset-0 bg-zinc-950"
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
