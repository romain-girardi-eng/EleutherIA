/**
 * TheDebatePage — scrollytelling narrative of the ancient free-will debate
 *
 * A self-contained scroll-snap page that walks through five thinkers in
 * chronological dialogue — each one answering, refining, or overturning the
 * positions of the figures before. For every thinker the page shows:
 *   1. the live Knowledge-Graph node description  (GET /api/kg/nodes/:id)
 *   2. one genuine corpus passage in its original language
 *                                                 (GET /api/works/:id/passages)
 *   3. a "who answers whom" lineage graphic
 *
 * Architecture reuses components/how-it-works: ScrollSection + DotNavigator.
 * No routing changes — mount under /the-debate when wiring App.tsx.
 *
 * Verified node + work ids (live against https://free-will.app, 2026-06):
 *   Chrysippus  person_chrysippus_280_206bce_i9j0k1l2
 *               work cc6548c0-… SVF II (88 passages, Greek)
 *   Alexander   person_alexander_aphrodisias_fl200ce_n5o6p7q8
 *               work bd95cd7c-… De Fato (39 passages, Greek)
 *   Origen      person_origen_alexandria_185_254ce_s9t0u1v2
 *               work 6dcedf04-… Contra Celsum (Greek/GCS)
 *   Augustine   person_augustine_hippo_d430
 *               work bb522ce4-… De Libero Arbitrio (25 passages, Latin)
 *   Boethius    person_boethius_480_524ce_w3x4y5z6
 *               work a9adc7e8-… Consolatio Philosophiae (129 passages, Latin)
 */

import {
  useState,
  useEffect,
  useRef,
  useCallback,
  useMemo,
} from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  ArrowRight,
  Quote,
  BookOpen,
  Network,
  Sparkles,
  ArrowDownRight,
  ExternalLink,
} from 'lucide-react';

import {
  BackgroundMesh,
  DotNavigator,
  ScrollHint,
  ScrollSection,
} from '../components/how-it-works';
import type { DotNavSection } from '../components/how-it-works';
import { cn } from '../utils/cn';
import { apiEndpoint } from '../api/baseUrl';

// ─── Config ──────────────────────────────────────────────────────────────────

type Accent = 'orange' | 'rose' | 'violet' | 'amber' | 'sky';

interface Thinker {
  id: string;
  nav: string;
  name: string;
  dates: string;
  school: string;
  /** One-line framing of this thinker's move in the debate. */
  stance: string;
  /** Knowledge-Graph node id (GET /api/kg/nodes/:id). */
  nodeId: string;
  /** Corpus work id with original-language passages. */
  workId: string;
  /** Pretty work label + citation hint shown above the passage. */
  workLabel: string;
  /** Who this thinker is answering — drives the lineage graphic. */
  respondsTo: string | null;
  accent: Accent;
}

// Chronological order = narrative order.
const THINKERS: Thinker[] = [
  {
    id: 'chrysippus',
    nav: 'Chrysippus',
    name: 'Chrysippus of Soli',
    dates: 'c. 279 – c. 206 BCE',
    school: 'Stoic',
    stance:
      'Sets the terms: everything is woven into fate (εἱμαρμένη), yet assent and what is "up to us" remain genuinely ours.',
    nodeId: 'person_chrysippus_280_206bce_i9j0k1l2',
    workId: 'cc6548c0-5186-5255-8af8-6f10512234de',
    workLabel: 'Fragments — Stoicorum Veterum Fragmenta II',
    respondsTo: null,
    accent: 'orange',
  },
  {
    id: 'alexander',
    nav: 'Alexander',
    name: 'Alexander of Aphrodisias',
    dates: 'fl. c. 200 CE',
    school: 'Peripatetic',
    stance:
      'The great rebuttal: if all is fated, deliberation, praise and blame collapse. Defends an open future against the Stoics.',
    nodeId: 'person_alexander_aphrodisias_fl200ce_n5o6p7q8',
    workId: 'bd95cd7c-1d6e-5b3e-8197-aeee2d57f42e',
    workLabel: 'De Fato (Περὶ Εἱμαρμένης)',
    respondsTo: 'Chrysippus',
    accent: 'rose',
  },
  {
    id: 'origen',
    nav: 'Origen',
    name: 'Origen of Alexandria',
    dates: 'c. 185 – c. 253/254 CE',
    school: 'Christian Platonist',
    stance:
      'Recasts the debate theologically: divine foreknowledge does not cause; the soul’s self-determination (αὐτεξούσιον) grounds moral responsibility.',
    nodeId: 'person_origen_alexandria_185_254ce_s9t0u1v2',
    workId: '6dcedf04-ab1f-5f57-8125-019fcaeaf943',
    workLabel: 'Contra Celsum (GCS, Koetschau)',
    respondsTo: 'Alexander',
    accent: 'violet',
  },
  {
    id: 'augustine',
    nav: 'Augustine',
    name: 'Augustine of Hippo',
    dates: '354 – 430 CE',
    school: 'Latin Patristic',
    stance:
      'Pushes back from within Christianity: free choice (liberum arbitrium) is real, but grace precedes and enables the good will.',
    nodeId: 'person_augustine_hippo_d430',
    workId: 'bb522ce4-300b-5879-9c16-6987b5061919',
    workLabel: 'De Libero Arbitrio',
    respondsTo: 'Origen',
    accent: 'amber',
  },
  {
    id: 'boethius',
    nav: 'Boethius',
    name: 'Boethius',
    dates: 'c. 477 – c. 524 CE',
    school: 'Late-Antique Platonist',
    stance:
      'The synthesis: from eternity God sees all at once (nunc stans), so foreknowledge and a free future are reconciled, not opposed.',
    nodeId: 'person_boethius_480_524ce_w3x4y5z6',
    workId: 'a9adc7e8-bd12-5f08-b637-2839b91db257',
    workLabel: 'De Consolatione Philosophiae, Bk V',
    respondsTo: 'Augustine',
    accent: 'sky',
  },
];

// ─── Accent palette (static class strings so Tailwind keeps them) ────────────

const ACCENT: Record<
  Accent,
  {
    text: string;
    chipBg: string;
    chipBorder: string;
    dot: string;
    rule: string;
    glow: string;
  }
> = {
  orange: {
    text: 'text-orange-300',
    chipBg: 'bg-orange-500/10',
    chipBorder: 'border-orange-400/30',
    dot: 'bg-orange-400',
    rule: 'from-orange-400/70',
    glow: 'rgba(249,115,22,0.18)',
  },
  rose: {
    text: 'text-rose-300',
    chipBg: 'bg-rose-500/10',
    chipBorder: 'border-rose-400/30',
    dot: 'bg-rose-400',
    rule: 'from-rose-400/70',
    glow: 'rgba(244,63,94,0.18)',
  },
  violet: {
    text: 'text-violet-300',
    chipBg: 'bg-violet-500/10',
    chipBorder: 'border-violet-400/30',
    dot: 'bg-violet-400',
    rule: 'from-violet-400/70',
    glow: 'rgba(139,92,246,0.18)',
  },
  amber: {
    text: 'text-amber-300',
    chipBg: 'bg-amber-500/10',
    chipBorder: 'border-amber-400/30',
    dot: 'bg-amber-400',
    rule: 'from-amber-400/70',
    glow: 'rgba(245,158,11,0.18)',
  },
  sky: {
    text: 'text-sky-300',
    chipBg: 'bg-sky-500/10',
    chipBorder: 'border-sky-400/30',
    dot: 'bg-sky-400',
    rule: 'from-sky-400/70',
    glow: 'rgba(56,189,248,0.18)',
  },
};

// ─── Data hooks ──────────────────────────────────────────────────────────────

interface KgNode {
  description?: string;
  school?: string;
}

interface Passage {
  text_content?: string;
  reference?: string;
  citation?: string;
  language?: string;
}

interface PassagesResponse {
  passages?: Passage[];
  total?: number;
}

type Loadable<T> =
  | { state: 'loading' }
  | { state: 'error' }
  | { state: 'ready'; data: T };

function useKgNode(nodeId: string): Loadable<KgNode> {
  const [result, setResult] = useState<Loadable<KgNode>>({ state: 'loading' });
  useEffect(() => {
    let mounted = true;
    setResult({ state: 'loading' });
    fetch(apiEndpoint(`/api/kg/nodes/${encodeURIComponent(nodeId)}`), {
      headers: { Accept: 'application/json' },
    })
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json() as Promise<KgNode>;
      })
      .then((data) => {
        if (mounted) setResult({ state: 'ready', data });
      })
      .catch(() => {
        if (mounted) setResult({ state: 'error' });
      });
    return () => {
      mounted = false;
    };
  }, [nodeId]);
  return result;
}

function usePassage(workId: string): Loadable<Passage | null> {
  const [result, setResult] = useState<Loadable<Passage | null>>({
    state: 'loading',
  });
  useEffect(() => {
    let mounted = true;
    setResult({ state: 'loading' });
    fetch(`${apiEndpoint(`/api/works/${encodeURIComponent(workId)}/passages`)}?limit=1`, {
      headers: { Accept: 'application/json' },
    })
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json() as Promise<PassagesResponse>;
      })
      .then((data) => {
        if (mounted) {
          const passage = data.passages?.[0] ?? null;
          setResult({ state: 'ready', data: passage });
        }
      })
      .catch(() => {
        if (mounted) setResult({ state: 'error' });
      });
    return () => {
      mounted = false;
    };
  }, [workId]);
  return result;
}

// ─── Section ─────────────────────────────────────────────────────────────────

function DebateSection({ thinker, index }: { thinker: Thinker; index: number }) {
  const node = useKgNode(thinker.nodeId);
  const passage = usePassage(thinker.workId);
  const accent = ACCENT[thinker.accent];

  const description =
    node.state === 'ready'
      ? (node.data.description ?? '').trim()
      : '';

  return (
    <ScrollSectionLocal id={thinker.id} glow={accent.glow}>
      <BackgroundMesh
        variant="dots"
        color="rgba(255,255,255,1)"
        opacity={0.025}
      />

      <div className="relative z-10 w-full max-w-6xl mx-auto px-4 sm:px-6 py-20">
        {/* ── Header ── */}
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="mb-6 flex flex-wrap items-center gap-3"
        >
          <span
            className={cn(
              'inline-flex items-center gap-2 text-xs font-body uppercase tracking-[0.18em] border rounded-full px-4 py-1.5',
              accent.text,
              accent.chipBg,
              accent.chipBorder,
            )}
          >
            <span className="font-mono">{String(index + 1).padStart(2, '0')}</span>
            {thinker.school}
          </span>
          {thinker.respondsTo && (
            <span className="inline-flex items-center gap-1.5 text-xs font-body text-white/40">
              <ArrowDownRight className="w-3.5 h-3.5" />
              answers {thinker.respondsTo}
            </span>
          )}
        </motion.div>

        <div className="grid lg:grid-cols-[1.55fr_1fr] gap-10 lg:gap-14 items-start">
          {/* ── Left: identity + description ── */}
          <div>
            <motion.h2
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
              className="font-display text-4xl sm:text-5xl lg:text-6xl text-white leading-[1.05]"
            >
              {thinker.name}
            </motion.h2>

            <motion.div
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: 0.1 }}
              className="mt-2 flex items-center gap-3 font-body text-sm text-white/45"
            >
              <span
                className={cn('w-1.5 h-1.5 rounded-full', accent.dot)}
                aria-hidden
              />
              <span>{thinker.dates}</span>
            </motion.div>

            <motion.p
              initial={{ opacity: 0, y: 14 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: 0.18 }}
              className={cn(
                'mt-6 font-display text-lg sm:text-xl leading-relaxed',
                accent.text,
              )}
            >
              {thinker.stance}
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 14 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: 0.26 }}
              className="mt-6 max-w-2xl"
            >
              <div
                className={cn(
                  'h-px w-16 mb-5 bg-gradient-to-r to-transparent',
                  accent.rule,
                )}
              />
              {node.state === 'loading' && (
                <div className="space-y-2.5" aria-hidden>
                  {[0, 1, 2, 3].map((i) => (
                    <div
                      key={i}
                      className="h-3.5 rounded bg-white/[0.06] animate-pulse"
                      style={{ width: `${[96, 88, 92, 70][i]}%` }}
                    />
                  ))}
                </div>
              )}
              {node.state === 'error' && (
                <p className="font-body text-sm text-white/35 italic">
                  Description unavailable — explore this figure in the graph.
                </p>
              )}
              {node.state === 'ready' && (
                <p className="font-body text-[0.95rem] sm:text-base text-white/70 leading-relaxed">
                  {description.length > 620
                    ? `${description.slice(0, 620).trimEnd()}…`
                    : description}
                </p>
              )}

              <div className="mt-6 flex flex-wrap gap-3">
                <Link
                  to={`/visualizer?node=${encodeURIComponent(thinker.nodeId)}`}
                  className="inline-flex items-center gap-2 min-h-11 px-4 py-2 rounded-full border border-white/15 bg-white/[0.04] text-white/70 hover:text-white hover:bg-white/[0.08] text-xs font-body transition-colors"
                >
                  <Network className="w-3.5 h-3.5" />
                  Open in graph
                </Link>
                <Link
                  to={`/texts/${encodeURIComponent(thinker.workId)}`}
                  className="inline-flex items-center gap-2 min-h-11 px-4 py-2 rounded-full border border-white/15 bg-white/[0.04] text-white/70 hover:text-white hover:bg-white/[0.08] text-xs font-body transition-colors"
                >
                  <BookOpen className="w-3.5 h-3.5" />
                  Read the work
                  <ExternalLink className="w-3 h-3 opacity-60" />
                </Link>
              </div>
            </motion.div>
          </div>

          {/* ── Right: live passage + lineage ── */}
          <div className="space-y-6">
            <motion.figure
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.7, delay: 0.12 }}
              className="rounded-2xl border border-white/10 bg-white/[0.04] backdrop-blur-sm p-6"
            >
              <figcaption className="flex items-center gap-2 mb-4 text-[0.7rem] font-body uppercase tracking-[0.16em] text-white/40">
                <Quote className={cn('w-3.5 h-3.5', accent.text)} />
                {thinker.workLabel}
              </figcaption>

              {passage.state === 'loading' && (
                <div className="space-y-2.5" aria-hidden>
                  {[0, 1, 2].map((i) => (
                    <div
                      key={i}
                      className="h-4 rounded bg-white/[0.06] animate-pulse"
                      style={{ width: `${[100, 94, 78][i]}%` }}
                    />
                  ))}
                </div>
              )}

              {passage.state === 'error' && (
                <p className="font-body text-sm text-white/35 italic">
                  Passage temporarily unavailable.
                </p>
              )}

              {passage.state === 'ready' && passage.data && (
                <PassageBody passage={passage.data} accentText={accent.text} />
              )}

              {passage.state === 'ready' && !passage.data && (
                <p className="font-body text-sm text-white/35 italic">
                  No passage indexed for this work yet.
                </p>
              )}
            </motion.figure>

            <motion.div
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.7, delay: 0.2 }}
            >
              <LineageGraphic activeId={thinker.id} />
            </motion.div>
          </div>
        </div>
      </div>
    </ScrollSectionLocal>
  );
}

// Render one corpus passage. Many passages prefix the original text with an
// editorial sigil ("Latin:", "Greek (…):") — surface it as a label, keep the
// text verbatim. No fabrication: only what the API returns is shown.
function PassageBody({
  passage,
  accentText,
}: {
  passage: Passage;
  accentText: string;
}) {
  const raw = (passage.text_content ?? '').trim();
  const truncated = raw.length > 460 ? `${raw.slice(0, 460).trimEnd()}…` : raw;
  const ref = passage.reference || passage.citation;

  return (
    <>
      <blockquote className="font-display text-lg sm:text-xl text-white/90 leading-relaxed">
        {truncated}
      </blockquote>
      {ref && !isOpaqueRef(ref) && (
        <p
          className={cn(
            'mt-4 font-body text-xs uppercase tracking-wider',
            accentText,
          )}
        >
          {ref}
        </p>
      )}
    </>
  );
}

// Passage references are sometimes raw UUIDs — don't show those.
function isOpaqueRef(ref: string): boolean {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-/i.test(ref);
}

// ─── Lineage graphic: who answers whom ───────────────────────────────────────

function LineageGraphic({ activeId }: { activeId: string }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.025] p-5">
      <p className="text-[0.7rem] font-body uppercase tracking-[0.16em] text-white/35 mb-4">
        The chain of replies
      </p>
      <ol className="space-y-0">
        {THINKERS.map((t, i) => {
          const isActive = t.id === activeId;
          const accent = ACCENT[t.accent];
          const isLast = i === THINKERS.length - 1;
          return (
            <li key={t.id} className="relative pl-7">
              {/* Connector */}
              {!isLast && (
                <span
                  className="absolute left-[0.32rem] top-4 bottom-0 w-px bg-white/12"
                  aria-hidden
                />
              )}
              {/* Node */}
              <span
                className={cn(
                  'absolute left-0 top-1.5 w-2.5 h-2.5 rounded-full ring-2 ring-zinc-950 transition-all',
                  isActive ? accent.dot : 'bg-white/20',
                  isActive && 'scale-125',
                )}
                aria-hidden
              />
              <div className="pb-4">
                <p
                  className={cn(
                    'font-body text-sm transition-colors',
                    isActive
                      ? cn(accent.text, 'font-semibold')
                      : 'text-white/45',
                  )}
                >
                  {t.nav}
                </p>
                {t.respondsTo && (
                  <p className="font-body text-[0.7rem] text-white/30">
                    ↳ replies to {t.respondsTo}
                  </p>
                )}
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}

// ─── Local ScrollSection wrapper (adds a soft accent glow) ───────────────────

function ScrollSectionLocal({
  id,
  glow,
  children,
}: {
  id: string;
  glow: string;
  children: React.ReactNode;
}) {
  return (
    <ScrollSectionShell id={id}>
      <div
        className="pointer-events-none absolute -top-1/4 right-0 w-[55%] h-[120%] blur-3xl opacity-60"
        style={{
          background: `radial-gradient(ellipse at center, ${glow}, transparent 70%)`,
        }}
        aria-hidden
      />
      {children}
    </ScrollSectionShell>
  );
}

// Thin wrapper over the shared ScrollSection so the dark theme + snap behaviour
// stay identical to how-it-works without prop noise at each call site.
function ScrollSectionShell({
  id,
  children,
}: {
  id: string;
  children: React.ReactNode;
}) {
  return (
    <ScrollSection id={id} className="bg-zinc-950" noInner>
      {children}
    </ScrollSection>
  );
}

// ─── Page ────────────────────────────────────────────────────────────────────

export default function TheDebatePage() {
  const [activeId, setActiveId] = useState('intro');
  const containerRef = useRef<HTMLDivElement>(null);
  const [navHeight, setNavHeight] = useState(48);

  const navSections: DotNavSection[] = useMemo(
    () => [
      { id: 'intro', label: 'The Debate' },
      ...THINKERS.map((t) => ({ id: t.id, label: t.nav })),
      { id: 'outro', label: 'Trace it' },
    ],
    [],
  );

  // Sit flush below the site navigation bar.
  useEffect(() => {
    const nav = document.getElementById('navigation');
    if (!nav) return;
    setNavHeight(nav.offsetHeight);
    const ro = new ResizeObserver(() => setNavHeight(nav.offsetHeight));
    ro.observe(nav);
    return () => ro.disconnect();
  }, []);

  // Sync dot navigation with the scrolled section.
  useEffect(() => {
    const opts: IntersectionObserverInit = {
      root: containerRef.current,
      threshold: 0.5,
    };
    const observer = new IntersectionObserver((entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) setActiveId(entry.target.id);
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
      className="overflow-y-scroll relative bg-zinc-950"
      style={
        {
          scrollSnapType: 'y mandatory',
          scrollBehavior: 'smooth',
          marginTop: `${navHeight}px`,
          height: `calc(100dvh - ${navHeight}px)`,
          '--snap-h': `calc(100dvh - ${navHeight}px)`,
        } as React.CSSProperties
      }
    >
      <DotNavigator
        sections={navSections}
        activeId={activeId}
        onNavigate={scrollTo}
      />

      {/* ── Intro ── */}
      <ScrollSection id="intro" className="bg-zinc-950" noInner>
        <BackgroundMesh
          variant="grid"
          color="rgba(255,255,255,1)"
          opacity={0.03}
        />
        <div
          className="relative z-10 flex flex-col items-center justify-center text-center px-6 max-w-4xl mx-auto"
          style={{ minHeight: 'var(--snap-h, 100dvh)' }}
        >
          <motion.span
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55, delay: 0.1 }}
            className="inline-flex items-center gap-2 text-xs font-body uppercase tracking-[0.2em] text-orange-300 border border-orange-400/30 bg-orange-500/10 rounded-full px-4 py-1.5 mb-8"
          >
            <Sparkles className="w-3.5 h-3.5" />
            A nine-century argument
          </motion.span>

          <motion.h1
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.75, delay: 0.2, ease: [0.22, 1, 0.36, 1] }}
            className="font-display text-5xl sm:text-6xl lg:text-7xl text-white leading-[1.06] mb-7"
          >
            Are we{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-orange-400 via-rose-400 to-violet-400">
              free
            </span>
            , or fated?
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.65, delay: 0.34 }}
            className="font-body text-lg sm:text-xl text-white/55 max-w-2xl leading-relaxed mb-10"
          >
            Follow one question through five thinkers who answered each other
            across the Greco-Roman and early-Christian world — each reply read
            from the original source, each figure drawn live from the knowledge
            graph.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55, delay: 0.46 }}
            className="flex flex-wrap items-center justify-center gap-x-3 gap-y-2 font-body text-sm text-white/40"
          >
            {THINKERS.map((t, i) => (
              <span key={t.id} className="inline-flex items-center gap-3">
                <span className={cn(ACCENT[t.accent].text)}>{t.nav}</span>
                {i < THINKERS.length - 1 && (
                  <ArrowRight className="w-3.5 h-3.5 text-white/20" />
                )}
              </span>
            ))}
          </motion.div>

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1 }}
            className="absolute bottom-8 left-1/2 -translate-x-1/2"
          >
            <ScrollHint theme="dark" label="Scroll to begin" />
          </motion.div>
        </div>
      </ScrollSection>

      {/* ── Five thinkers ── */}
      {THINKERS.map((thinker, index) => (
        <DebateSection key={thinker.id} thinker={thinker} index={index} />
      ))}

      {/* ── Outro ── */}
      <ScrollSection id="outro" className="bg-zinc-950" noInner>
        <BackgroundMesh
          variant="dots"
          color="rgba(255,255,255,1)"
          opacity={0.025}
        />
        <div
          className="relative z-10 flex flex-col items-center justify-center text-center px-6 max-w-3xl mx-auto"
          style={{ minHeight: 'var(--snap-h, 100dvh)' }}
        >
          <motion.h2
            initial={{ opacity: 0, y: 18 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
            className="font-display text-4xl sm:text-5xl lg:text-6xl text-white leading-tight mb-6"
          >
            The argument never closed.
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.12 }}
            className="font-body text-lg text-white/55 max-w-xl mb-10"
          >
            Boethius did not end it — he handed it to the Middle Ages. Trace
            every reply, concept, and citation in the full graph, or put the
            question to the corpus yourself.
          </motion.p>
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.55, delay: 0.2 }}
            className="flex flex-wrap justify-center gap-4"
          >
            <Link
              to="/visualizer"
              className="inline-flex items-center gap-2 px-7 py-3.5 rounded-full bg-orange-500 hover:bg-orange-400 text-white font-body font-semibold transition-colors"
            >
              <Network className="w-4 h-4" />
              Explore the graph
            </Link>
            <Link
              to="/graphrag"
              className="inline-flex items-center gap-2 px-7 py-3.5 rounded-full border border-white/20 bg-white/[0.06] hover:bg-white/[0.12] text-white font-body font-medium transition-colors"
            >
              <Sparkles className="w-4 h-4" />
              Ask the corpus
              <ArrowRight className="w-4 h-4" />
            </Link>
          </motion.div>
        </div>
      </ScrollSection>
    </div>
  );
}
