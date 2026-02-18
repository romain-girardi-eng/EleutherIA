import { useState, useRef, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { Maximize2, Minimize2 } from 'lucide-react';
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

  return (
    <div className="min-h-screen relative">
      {/* Aurora effect */}
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

      {/* Main Content */}
      <main className="min-h-screen relative z-10">
        <HeroSection
          logo={{ url: "/logo.svg", alt: "EleutherIA" }}
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
            href: "/how-it-works",
          }}
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
