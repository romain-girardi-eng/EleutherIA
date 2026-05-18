import { lazy, Suspense, useState, useRef, useEffect, useLayoutEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { Maximize2, Minimize2, ChevronRight } from 'lucide-react';
import { HeroSection } from '../components/ui/hero-section-2';

const MorphingParticles = lazy(() =>
  import('../components/MorphingParticles').then((module) => ({
    default: module.MorphingParticles,
  })),
);

function ParticleFallback() {
  return (
    <div className="absolute inset-0 bg-parchment-50 md:bg-zinc-950" />
  );
}

export default function HomePage() {
  const { t } = useTranslation();
  const [isNativeFullscreen, setIsNativeFullscreen] = useState(false);
  const [isCSSFullscreen, setIsCSSFullscreen] = useState(false);
  const [showParticles, setShowParticles] = useState(false);
  const particleContainerRef = useRef<HTMLDivElement>(null);

  // Lock page scroll — single full-screen canvas, no scrolling.
  // iOS Safari (incl. iOS 17/18) leaks scroll via three vectors that all
  // need to be closed simultaneously:
  //   1. `100dvh` resizes when the URL bar collapses → use `100svh`
  //      (smallest viewport, never reflows) instead.
  //   2. `overflow:hidden` alone doesn't stop rubber-band → pin body
  //      with `position:fixed; inset:0`.
  //   3. `touch-action` does NOT inherit, so killing it on body only
  //      blocks gestures starting on body itself — children still
  //      accept them. The Hero section sets `touch-action:none` on its
  //      own root to close that path.
  // Block also prevents the scroll-leak that happens when React mounts
  // (useLayoutEffect lands before first paint).
  useLayoutEffect(() => {
    const body = document.body;
    const html = document.documentElement;

    const prev = {
      bodyOverflow: body.style.overflow,
      bodyPosition: body.style.position,
      bodyTop: body.style.top,
      bodyLeft: body.style.left,
      bodyRight: body.style.right,
      bodyBottom: body.style.bottom,
      bodyWidth: body.style.width,
      bodyHeight: body.style.height,
      bodyOverscroll: body.style.overscrollBehavior,
      bodyTouchAction: body.style.touchAction,
      htmlOverflow: html.style.overflow,
      htmlOverscroll: html.style.overscrollBehavior,
      htmlHeight: html.style.height,
      htmlTouchAction: html.style.touchAction,
    };

    window.scrollTo(0, 0);

    html.style.height = '100svh';
    html.style.overflow = 'hidden';
    html.style.overscrollBehavior = 'none';
    body.style.height = '100svh';
    body.style.overflow = 'hidden';
    body.style.position = 'fixed';
    body.style.top = '0';
    body.style.left = '0';
    body.style.right = '0';
    body.style.bottom = '0';
    body.style.width = '100%';
    body.style.overscrollBehavior = 'none';
    // touch-action is NOT pinned at the document level here — see the
    // matching note in App.tsx. Cascading `none` would kill tap→click on
    // descendant buttons (the burger). The Hero section keeps its own
    // `touch-none` so rubber-band on the hero canvas stays blocked.

    return () => {
      html.style.height = prev.htmlHeight;
      html.style.overflow = prev.htmlOverflow;
      html.style.overscrollBehavior = prev.htmlOverscroll;
      html.style.touchAction = prev.htmlTouchAction;
      body.style.height = prev.bodyHeight;
      body.style.overflow = prev.bodyOverflow;
      body.style.position = prev.bodyPosition;
      body.style.top = prev.bodyTop;
      body.style.left = prev.bodyLeft;
      body.style.right = prev.bodyRight;
      body.style.bottom = prev.bodyBottom;
      body.style.width = prev.bodyWidth;
      body.style.overscrollBehavior = prev.bodyOverscroll;
      body.style.touchAction = prev.bodyTouchAction;
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

  useEffect(() => {
    const connection = (navigator as Navigator & {
      connection?: { saveData?: boolean; effectiveType?: string };
    }).connection;
    const isSlowConnection =
      connection?.saveData === true ||
      connection?.effectiveType === 'slow-2g' ||
      connection?.effectiveType === '2g';
    const canRenderParticles =
      window.matchMedia('(min-width: 1024px) and (hover: hover)').matches &&
      !window.matchMedia('(prefers-reduced-motion: reduce)').matches &&
      !isSlowConnection;

    if (!canRenderParticles) {
      setShowParticles(false);
      return;
    }

    const startParticles = () => setShowParticles(true);
    let timeoutId: ReturnType<typeof globalThis.setTimeout> | undefined;
    let idleId: number | undefined;

    if ('requestIdleCallback' in window) {
      idleId = window.requestIdleCallback(startParticles, { timeout: 5000 });
    } else {
      timeoutId = globalThis.setTimeout(startParticles, 4000);
    }

    return () => {
      if (idleId !== undefined) window.cancelIdleCallback(idleId);
      if (timeoutId !== undefined) globalThis.clearTimeout(timeoutId);
    };
  }, []);

  const isFullscreen = isNativeFullscreen || isCSSFullscreen;

  // Codex Index — Roman numerals + hairline rules, like an ancient manuscript's table of contents
  const ctaButtons = (
    <div className="flex flex-col w-full">
      <div className="h-px bg-zinc-200" />

      {/* I — How It Works */}
      <a
        href="/how-it-works"
        className="group flex items-center gap-3 py-3 px-1 hover:bg-amber-50/60 transition-colors duration-150"
      >
        <span className="font-mono text-[10px] w-6 text-zinc-300 group-hover:text-amber-500 tracking-widest flex-shrink-0 transition-colors duration-150 select-none">
          I
        </span>
        <div className="flex-1 min-w-0">
          <div className="text-xs font-semibold tracking-wide text-zinc-800 group-hover:text-amber-700 transition-colors duration-150 leading-tight">
            {t('nav.howItWorks')}
          </div>
          <div className="text-[9px] text-zinc-400 mt-0.5 leading-tight">
            Architecture · retrieval · pipeline
          </div>
        </div>
        <ChevronRight className="w-3.5 h-3.5 flex-shrink-0 text-amber-600 opacity-0 group-hover:opacity-100 -translate-x-1 group-hover:translate-x-0 transition-all duration-200" />
      </a>

      <div className="h-px bg-zinc-200" />

      {/* II — Knowledge Graph */}
      <a
        href="/visualizer"
        className="group flex items-center gap-3 py-3 px-1 hover:bg-orange-50/60 transition-colors duration-150"
      >
        <span className="font-mono text-[10px] w-6 text-zinc-300 group-hover:text-orange-500 tracking-widest flex-shrink-0 transition-colors duration-150 select-none">
          II
        </span>
        <div className="flex-1 min-w-0">
          <div className="text-xs font-semibold tracking-wide text-zinc-800 group-hover:text-orange-700 transition-colors duration-150 leading-tight">
            {t('nav.visualizer')}
          </div>
          <div className="text-[9px] text-zinc-400 mt-0.5 leading-tight">
            2,193 nodes · 8,616 edges
          </div>
        </div>
        <ChevronRight className="w-3.5 h-3.5 flex-shrink-0 text-orange-600 opacity-0 group-hover:opacity-100 -translate-x-1 group-hover:translate-x-0 transition-all duration-200" />
      </a>

      <div className="h-px bg-zinc-200" />

      {/* III — GraphRAG Q&A */}
      <a
        href="/graphrag"
        className="group flex items-center gap-3 py-3 px-1 hover:bg-violet-50/40 transition-colors duration-150"
      >
        <span className="font-mono text-[10px] w-6 text-zinc-300 group-hover:text-violet-500 tracking-widest flex-shrink-0 transition-colors duration-150 select-none">
          III
        </span>
        <div className="flex-1 min-w-0">
          <div className="text-xs font-semibold tracking-wide text-zinc-800 group-hover:text-violet-700 transition-colors duration-150 leading-tight">
            {t('nav.graphrag')}
          </div>
          <div className="text-[9px] text-zinc-400 mt-0.5 leading-tight">
            5-stage RAG · AI-powered Q&A
          </div>
        </div>
        <ChevronRight className="w-3.5 h-3.5 flex-shrink-0 text-violet-600 opacity-0 group-hover:opacity-100 -translate-x-1 group-hover:translate-x-0 transition-all duration-200" />
      </a>

      <div className="h-px bg-zinc-200" />
    </div>
  );

  return (
    // Lock to `100svh` (smallest viewport) rather than `100dvh`: dvh
    // grows when iOS Safari's URL bar collapses, causing the section
    // to reflow during scroll gestures — the user reads that as scroll.
    // svh stays put. Trade-off: a thin band may remain at the bottom
    // when the URL bar is gone, which is fine for a single-screen page.
    <div className="h-[100svh] overflow-hidden relative touch-none overscroll-none">
      <main className="h-[100svh] overflow-hidden relative touch-none overscroll-none">
        <HeroSection
          logo={{ url: "/logo-880.webp", alt: "EleutherIA" }}
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
              className={isCSSFullscreen ? "fixed inset-0 z-[9999] bg-zinc-950" : "absolute inset-0 bg-parchment-50 md:bg-zinc-950"}
            >
              {showParticles ? (
                <Suspense fallback={<ParticleFallback />}>
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
                </Suspense>
              ) : (
                <ParticleFallback />
              )}
              {showParticles && (
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
              )}
            </div>
          }
          contactInfo={[
            { type: 'doi', label: t('learn.hero.doi'), href: 'https://doi.org/10.5281/zenodo.17379489' },
            { type: 'website', label: t('learn.hero.license') },
            { type: 'github', label: t('learn.hero.openSource'), href: 'https://github.com' },
          ]}
        />
      </main>
    </div>
  );
}
