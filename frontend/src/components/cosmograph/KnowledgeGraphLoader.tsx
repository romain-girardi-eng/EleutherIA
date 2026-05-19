import { useEffect, useMemo, useRef, useState } from 'react';
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion';
import { useTranslation } from 'react-i18next';

interface KnowledgeGraphLoaderProps {
  /** Path under /public to the optimized MP4 (no audio). */
  videoMp4Src?: string;
  /** Optional WebM fallback path under /public (no audio). */
  videoWebmSrc?: string;
  /** Poster image shown while video buffers and for reduced-motion users. */
  posterSrc?: string;
  /** Fires once when the video has played through. The video is meant to
   *  cover the data-fetch latency; the parent uses this to know that the
   *  loader has paid its full visual debt and can be torn down as soon as
   *  the underlying data is ready. */
  onVideoEnded?: () => void;
}

const EASE_OUT_EXPO = [0.16, 1, 0.3, 1] as const;
const EASE_OUT_QUART = [0.25, 1, 0.5, 1] as const;

const NODE_COUNT = 17_746;
const EDGE_COUNT = 42_925;

export function KnowledgeGraphLoader({
  videoMp4Src = '/loader-kg.mp4',
  videoWebmSrc = '/loader-kg.webm',
  posterSrc = '/loader-kg-poster.jpg',
  onVideoEnded,
}: KnowledgeGraphLoaderProps) {
  const { t } = useTranslation();
  const prefersReducedMotion = useReducedMotion();
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [videoReady, setVideoReady] = useState(false);

  const messages = useMemo(
    () => [
      t(
        'cosmograph.loading.cycle.weaving',
        'Weaving 17.7k voices into a single graph…',
      ),
      t(
        'cosmograph.loading.cycle.tracing',
        'Tracing causal chains across two millennia…',
      ),
      t(
        'cosmograph.loading.cycle.aligning',
        'Aligning Stoics, Peripatetics, and Church Fathers…',
      ),
      t(
        'cosmograph.loading.cycle.binding',
        'Binding ancient texts to modern scholarship…',
      ),
      t(
        'cosmograph.loading.cycle.unfolding',
        'Unfolding the Atlas of free will…',
      ),
    ],
    [t],
  );

  const [messageIndex, setMessageIndex] = useState(0);
  useEffect(() => {
    if (prefersReducedMotion) return;
    setMessageIndex(Math.floor(Math.random() * messages.length));
    const id = window.setInterval(() => {
      setMessageIndex((prev) => (prev + 1) % messages.length);
    }, 2600);
    return () => window.clearInterval(id);
  }, [messages.length, prefersReducedMotion]);

  // `onVideoEnded` typically comes from the parent as `() => setX(true)` —
  // a NEW reference on every parent render. We hold it in a ref so its
  // identity doesn't trigger the autoplay effect to re-run (which would
  // call `el.play()` on an already-ended video and restart it from frame
  // zero — the loop-on-loop bug). The ref also serves as a guard: once
  // the video has ended we lock it down so nothing tries to play again.
  const endedRef = useRef(false);
  const onVideoEndedRef = useRef(onVideoEnded);
  useEffect(() => {
    onVideoEndedRef.current = onVideoEnded;
  }, [onVideoEnded]);

  // Coax autoplay on Safari/iOS the moment the element is ready.
  //
  // The .catch() path used to be our only autoplay-blocked signal, but
  // iOS Safari doesn't always reject the play() promise — it can resolve
  // silently while keeping the element paused, leaving a tap-to-play
  // chrome overlay on top of the poster. We add a hard watchdog: 1.4 s
  // after the canplay event, if the video hasn't actually advanced past
  // frame 0, treat that as blocked and unblock the parent so the loader
  // can come down. The user never gets stuck on a play-button poster.
  useEffect(() => {
    const el = videoRef.current;
    if (!el || prefersReducedMotion) return;
    let watchdog: number | null = null;
    const markBlocked = () => {
      if (endedRef.current) return;
      endedRef.current = true;
      onVideoEndedRef.current?.();
    };
    const tryPlay = () => {
      if (endedRef.current || el.ended) return;
      const startTime = el.currentTime;
      const promise = el.play();
      if (watchdog !== null) window.clearTimeout(watchdog);
      watchdog = window.setTimeout(() => {
        if (endedRef.current) return;
        if (el.paused || el.currentTime <= startTime + 0.05) {
          markBlocked();
        }
      }, 1400);
      void promise?.catch(() => {
        if (watchdog !== null) window.clearTimeout(watchdog);
        window.setTimeout(markBlocked, 300);
      });
    };
    if (el.readyState >= 2) tryPlay();
    else el.addEventListener('canplay', tryPlay, { once: true });
    return () => {
      el.removeEventListener('canplay', tryPlay);
      if (watchdog !== null) window.clearTimeout(watchdog);
    };
  }, [prefersReducedMotion]);

  // Reduced-motion users have no video to wait for — fire the gate immediately
  // so the parent can tear the loader down the moment the data is ready.
  useEffect(() => {
    if (prefersReducedMotion && !endedRef.current) {
      endedRef.current = true;
      onVideoEndedRef.current?.();
    }
  }, [prefersReducedMotion]);

  return (
    <motion.div
      role="status"
      aria-busy="true"
      aria-live="polite"
      aria-label={t('cosmograph.loading.title', 'Building the Atlas…')}
      className="absolute inset-0 z-40 flex items-center justify-center overflow-hidden bg-[#020617]"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5, ease: EASE_OUT_QUART }}
    >
      {/* Layered radial backdrops (parchemin-or + cyan accent) */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(251,191,36,0.10),transparent_55%),radial-gradient(circle_at_18%_18%,rgba(34,211,238,0.10),transparent_42%),radial-gradient(circle_at_82%_82%,rgba(244,114,182,0.07),transparent_44%)]"
      />
      {/* Drifting starfield grain — subtle, only when motion allowed */}
      {!prefersReducedMotion && (
        <motion.div
          aria-hidden
          className="pointer-events-none absolute inset-0 bg-[radial-gradient(rgba(255,255,255,0.08)_1px,transparent_1px)] [background-size:42px_42px] opacity-30 mix-blend-screen"
          initial={{ opacity: 0 }}
          animate={{ opacity: 0.25 }}
          transition={{ duration: 1.6, ease: EASE_OUT_QUART }}
        />
      )}

      {/* Cinema stage */}
      <motion.div
        className="relative z-10 flex w-[min(92vw,960px)] flex-col items-center"
        initial={{ opacity: 0, y: 18, scale: 0.97 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.8, ease: EASE_OUT_EXPO, delay: 0.05 }}
      >
        {/* Eyebrow */}
        <motion.p
          className="mb-4 text-[10px] font-semibold uppercase tracking-[0.32em] text-amber-200/90 sm:text-[11px]"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: EASE_OUT_QUART, delay: 0.18 }}
        >
          {t('cosmograph.loading.eyebrow', 'Knowledge graph')}
        </motion.p>

        {/* Video frame with golden halo + vignette mask */}
        <div className="relative w-full">
          {/* Pulsing golden halo */}
          {!prefersReducedMotion && (
            <motion.div
              aria-hidden
              className="pointer-events-none absolute -inset-10 rounded-[2.25rem] bg-[radial-gradient(ellipse_at_center,rgba(251,191,36,0.28),transparent_62%)] blur-2xl"
              animate={{ opacity: [0.55, 0.95, 0.55], scale: [0.96, 1.02, 0.96] }}
              transition={{
                duration: 4.2,
                ease: 'easeInOut',
                repeat: Infinity,
              }}
            />
          )}

          <div className="relative aspect-[16/9] w-full overflow-hidden rounded-[1.75rem] border border-amber-200/15 bg-slate-950 shadow-[0_40px_120px_-20px_rgba(2,6,23,0.85),0_0_0_1px_rgba(251,191,36,0.06)]">
            {prefersReducedMotion ? (
              <img
                src={posterSrc}
                alt=""
                aria-hidden="true"
                className="absolute inset-0 h-full w-full object-contain"
              />
            ) : (
              <video
                ref={videoRef}
                className="silent-video absolute inset-0 h-full w-full object-contain"
                poster={posterSrc}
                muted
                playsInline
                autoPlay
                preload="auto"
                aria-hidden="true"
                onCanPlay={() => setVideoReady(true)}
                onLoadedData={() => setVideoReady(true)}
                onEnded={(e) => {
                  if (endedRef.current) return;
                  endedRef.current = true;
                  // Pause explicitly so any stray play() call (e.g. from the
                  // browser's media controls or a stale effect re-run) can't
                  // rewind us back to frame 0. The last frame stays visible.
                  e.currentTarget.pause();
                  onVideoEndedRef.current?.();
                }}
              >
                <source src={videoWebmSrc} type="video/webm" />
                <source src={videoMp4Src} type="video/mp4" />
              </video>
            )}

            {/* Hairline gold border (inside) */}
            <div
              aria-hidden
              className="pointer-events-none absolute inset-0 rounded-[1.75rem] ring-1 ring-inset ring-amber-200/10"
            />
            {/* First-paint shimmer until video frames are decoded */}
            {!prefersReducedMotion && !videoReady && (
              <motion.div
                aria-hidden
                className="pointer-events-none absolute inset-0 bg-gradient-to-r from-transparent via-amber-200/10 to-transparent"
                initial={{ x: '-100%' }}
                animate={{ x: '100%' }}
                transition={{ duration: 1.6, ease: 'easeInOut', repeat: Infinity }}
              />
            )}
          </div>
        </div>

        {/* Caption block — below the video frame so it never crops */}
        <motion.div
          className="mt-7 flex flex-col items-center text-center"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: EASE_OUT_EXPO, delay: 0.32 }}
        >
          <h2 className="text-balance text-2xl font-semibold leading-tight tracking-tight text-white sm:text-3xl">
            {t('cosmograph.loading.title', 'Building the Atlas…')}
          </h2>

          <div className="mt-2 min-h-[1.5rem] sm:min-h-[1.75rem]">
            <AnimatePresence mode="wait">
              <motion.p
                key={messageIndex}
                className="text-sm leading-6 text-amber-100/85 sm:text-[15px]"
                initial={{ opacity: 0, y: 6, filter: 'blur(4px)' }}
                animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
                exit={{ opacity: 0, y: -6, filter: 'blur(4px)' }}
                transition={{ duration: 0.55, ease: EASE_OUT_QUART }}
              >
                {messages[messageIndex]}
              </motion.p>
            </AnimatePresence>
          </div>
        </motion.div>

        {/* Stats + indeterminate progress */}
        <motion.div
          className="mt-6 flex w-full flex-col items-center gap-4"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: EASE_OUT_QUART, delay: 0.42 }}
        >
          <div className="flex items-center gap-3 text-[11px] uppercase tracking-[0.22em] text-slate-300/80 sm:text-xs">
            <span className="tabular-nums text-amber-200/90">
              {NODE_COUNT.toLocaleString()}
            </span>
            <span className="text-slate-500/80">
              {t('cosmograph.loading.statNodes', 'nodes')}
            </span>
            <span aria-hidden className="h-1 w-1 rounded-full bg-amber-200/40" />
            <span className="tabular-nums text-amber-200/90">
              {EDGE_COUNT.toLocaleString()}
            </span>
            <span className="text-slate-500/80">
              {t('cosmograph.loading.statEdges', 'relations')}
            </span>
          </div>

          {/* Indeterminate progress bar */}
          <div className="relative h-px w-full max-w-md overflow-hidden bg-white/[0.06]">
            {!prefersReducedMotion && (
              <motion.div
                aria-hidden
                className="absolute inset-y-0 w-1/3 bg-gradient-to-r from-transparent via-amber-300 to-transparent"
                initial={{ x: '-100%' }}
                animate={{ x: '300%' }}
                transition={{
                  duration: 2.4,
                  ease: 'easeInOut',
                  repeat: Infinity,
                }}
              />
            )}
            {prefersReducedMotion && (
              <div className="absolute inset-y-0 left-0 w-1/2 bg-amber-300/60" />
            )}
          </div>
        </motion.div>
      </motion.div>
    </motion.div>
  );
}

export default KnowledgeGraphLoader;
