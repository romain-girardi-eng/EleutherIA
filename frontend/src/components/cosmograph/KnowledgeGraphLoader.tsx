import { useEffect, useState } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { useKgStats } from '../../hooks/useKgStats';
import { formatCompact } from '../../lib/formatCompact';

export type KnowledgeGraphLoadPhase = 'data' | 'render';

interface KnowledgeGraphLoaderProps {
  /** Path under /public to the optimized MP4 (no audio). */
  videoMp4Src?: string;
  /** Optional WebM fallback path under /public (no audio). */
  videoWebmSrc?: string;
  /** Poster image shown while video buffers and whenever the film is skipped. */
  posterSrc?: string;
  /** What the page is actually waiting for, when the host knows it. */
  phase?: KnowledgeGraphLoadPhase;
}

const EASE_OUT_QUART = [0.25, 1, 0.5, 1] as const;
const SLOW_AFTER_S = 6;
const VERY_SLOW_AFTER_S = 18;

type NetworkInformationLike = { saveData?: boolean; effectiveType?: string };

/**
 * The 2 MB film competes with the graph download for bandwidth. It only
 * plays where it cannot slow the real work down: wide, fine-pointer
 * screens, no data-saver, no slow connection, no reduced-motion preference.
 */
function canAffordFilm(): boolean {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return false;
  const connection = (navigator as Navigator & { connection?: NetworkInformationLike }).connection;
  if (connection?.saveData) return false;
  if (connection?.effectiveType && /(^|-)(2g|3g)$/.test(connection.effectiveType)) return false;
  return window.matchMedia('(min-width: 768px) and (pointer: fine)').matches;
}

function useElapsedSeconds(): number {
  const [seconds, setSeconds] = useState(0);
  useEffect(() => {
    const started = performance.now();
    const id = window.setInterval(() => {
      setSeconds(Math.floor((performance.now() - started) / 1000));
    }, 1000);
    return () => window.clearInterval(id);
  }, []);
  return seconds;
}

export function KnowledgeGraphLoader({
  videoMp4Src = '/loader-kg.mp4',
  videoWebmSrc = '/loader-kg.webm',
  posterSrc = '/loader-kg-poster.jpg',
  phase,
}: KnowledgeGraphLoaderProps) {
  const { t, i18n } = useTranslation();
  const kgStats = useKgStats();
  const prefersReducedMotion = useReducedMotion();
  const [playFilm] = useState(() => !prefersReducedMotion && canAffordFilm());
  const elapsed = useElapsedSeconds();

  // Only the node total is quoted: the stats endpoint counts relations on a
  // different basis from the links actually drawn, so an edge figure here
  // would not match what appears on screen.
  const statsKnown = Number.isFinite(kgStats.nodes);
  const nodesCompact = formatCompact(kgStats.nodes, i18n.language);

  const step =
    phase === 'render'
      ? t('cosmograph.loading.stepRender', 'Drawing the graph on screen…')
      : phase === 'data'
        ? statsKnown
          ? t('cosmograph.loading.stepDataCounts', {
              nodes: nodesCompact,
              defaultValue: 'Downloading {{nodes}} nodes and their relations…',
            })
          : t('cosmograph.loading.stepData', 'Downloading nodes and relations…')
        : statsKnown
          ? t('cosmograph.loading.stepBothCounts', {
              nodes: nodesCompact,
              defaultValue: 'Downloading {{nodes}} nodes and their relations, then drawing them…',
            })
          : t('cosmograph.loading.stepBoth', 'Downloading the graph, then drawing it…');

  const patience =
    elapsed >= VERY_SLOW_AFTER_S
      ? t('cosmograph.loading.verySlow', {
          seconds: elapsed,
          defaultValue: 'Still working ({{seconds}} s). A slow connection or an older graphics card can make this take longer.',
        })
      : elapsed >= SLOW_AFTER_S
        ? t('cosmograph.loading.slow', { seconds: elapsed, defaultValue: 'Still working ({{seconds}} s)…' })
        : null;

  return (
    <motion.div
      role="status"
      aria-busy="true"
      aria-label={t('cosmograph.loading.title', 'Loading the knowledge graph')}
      className="absolute inset-0 z-40 flex items-center justify-center overflow-hidden bg-[#f7f2e9] px-4 text-stone-900"
      // A short fade-in delay keeps fast loads from flashing a loader at all.
      initial={{ opacity: 0 }}
      animate={{ opacity: 1, transition: { duration: 0.3, delay: 0.15, ease: EASE_OUT_QUART } }}
      exit={{ opacity: 0, transition: { duration: 0.25, ease: EASE_OUT_QUART } }}
    >
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(161,98,7,0.10),transparent_55%),radial-gradient(circle_at_18%_18%,rgba(15,118,110,0.09),transparent_42%),radial-gradient(circle_at_82%_82%,rgba(194,65,12,0.07),transparent_44%)]"
      />

      <div className="relative z-10 flex w-[min(100%,960px)] flex-col items-center">
        <div className="relative w-full max-w-[min(100%,52rem)]">
          <div className="relative aspect-[16/9] w-full overflow-hidden rounded-[1.5rem] border border-amber-200/15 bg-slate-950 shadow-[0_40px_120px_-20px_rgba(2,6,23,0.6)] sm:rounded-[1.75rem]">
            {playFilm ? (
              <video
                className="silent-video absolute inset-0 h-full w-full object-contain"
                poster={posterSrc}
                muted
                playsInline
                autoPlay
                preload="auto"
                aria-hidden="true"
              >
                <source src={videoWebmSrc} type="video/webm" />
                <source src={videoMp4Src} type="video/mp4" />
              </video>
            ) : (
              <img
                src={posterSrc}
                alt=""
                aria-hidden="true"
                decoding="async"
                className="absolute inset-0 h-full w-full object-contain"
              />
            )}
          </div>
        </div>

        <div className="mt-6 flex flex-col items-center text-center sm:mt-7">
          <h2 className="text-balance font-display text-2xl font-semibold leading-tight tracking-tight text-stone-950 sm:text-3xl">
            {t('cosmograph.loading.title', 'Loading the knowledge graph')}
          </h2>
          <p className="mt-2 max-w-md text-balance font-body text-sm leading-6 text-stone-600 sm:text-[15px]" aria-live="polite">
            {step}
          </p>
          <p className="mt-1 min-h-[1.25rem] max-w-md text-balance font-body text-[13px] leading-5 text-stone-500" aria-live="polite">
            {patience}
          </p>
        </div>

        <div
          role="progressbar"
          aria-label={t('cosmograph.loading.progressLabel', 'Loading progress')}
          aria-valuetext={step}
          className="relative mt-5 h-px w-full max-w-md overflow-hidden bg-stone-300"
        >
          {prefersReducedMotion ? (
            <div className="absolute inset-y-0 left-0 w-full bg-orange-700/35" />
          ) : (
            <motion.div
              aria-hidden
              className="absolute inset-y-0 w-1/3 bg-gradient-to-r from-transparent via-orange-700 to-transparent"
              initial={{ x: '-100%' }}
              animate={{ x: '300%' }}
              transition={{ duration: 2.2, ease: 'easeInOut', repeat: Infinity }}
            />
          )}
        </div>
      </div>
    </motion.div>
  );
}

export default KnowledgeGraphLoader;
