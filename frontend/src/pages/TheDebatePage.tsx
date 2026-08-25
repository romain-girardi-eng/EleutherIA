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
 * Works are addressed by `canonical_id`, NEVER by the `work_id` UUID. The
 * UUID is derived from the work record, so a re-ingest mints a new one: the
 * 2026-06 set that used to be hardcoded here died in the 2026-08-24 rebuild
 * and every passage card on the live page silently degraded to "No passage
 * indexed for this work yet" — the page's whole premise, gone, with no error.
 * `canonical_id` comes from the CTS URN and survives. `usePassage` resolves
 * it through one shared `/api/works` lookup.
 *
 * Verified live against https://free-will.app, 2026-08-26:
 *   Chrysippus  person_chrysippus_280_206bce_i9j0k1l2
 *               tlg1264_tlg001_1st1k_grc1_grc
 *               SVF II Fragmenta Logica et Physica (88 passages, Greek)
 *   Alexander   person_alexander_aphrodisias_fl200ce_n5o6p7q8
 *               tlg0732_tlg014_grc — De Fato (39 passages, Greek)
 *   Origen      person_origen_alexandria_185_254ce_s9t0u1v2
 *               work_de_principiis_origen_230s_v2w3x4y5_grc
 *               De Principiis III.1 (Περὶ αὐτεξουσίου), 25 passages, Greek.
 *               Replaces Contra Celsum, which holds 2 passages and is not
 *               where Origen argues the point.
 *   Augustine   person_augustine_hippo_d430
 *               urn_cts_latinlit_stoa0040_stoa003_lat
 *               De Libero Arbitrio (171 passages, Latin). Corpus text is
 *               Perseus stoa0040.stoa003, not CCSL 29 — cite it as such.
 *   Boethius    person_boethius_480_524ce_w3x4y5z6
 *               urn_cts_latinlit_phi2089_phi002_lat — De consolatione
 *               philosophiae (129 passages). Prefer this over the
 *               …_phi002_eng row, which carries the same Latin text under
 *               language "eng".
 *
 * KNOWN CORPUS DEFECTS in these works — do not mistake them for render bugs:
 *   - Boethius rows are prefixed with a literal "Latin: " and carry OCR
 *     damage ("conprehendentimn", "iutueamur", stray {braces}).
 *   - Alexander De fato 15 reads `ἔχει` with an injected "[...]" where
 *     Bruns 185.21 has `ἔχειν, ὡς τῇ σφαίρᾳ`.
 *   - SVF II 931 contains "ταὐAugustinus τὸν", a bad find/replace.
 * These need a reviewed apply-script under scripts/, not a display-side hack.
 */

import {
  useState,
  useEffect,
  useRef,
  useCallback,
  useMemo,
} from 'react';
import { MotionConfig, motion, useReducedMotion } from 'framer-motion';
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
import {
  THINKERS,
  useKgNode,
  usePassage,
  type Accent,
  type Passage,
  type Thinker,
} from './theDebateCorpus';

// ─── Config ──────────────────────────────────────────────────────────────────

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

// ─── Section ─────────────────────────────────────────────────────────────────

function DebateSection({ thinker, index }: { thinker: Thinker; index: number }) {
  const node = useKgNode(thinker.nodeId);
  const passage = usePassage(thinker.workCanonicalId);
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
              <WithGreek text={thinker.stance} />
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
                <ExpandableDescription text={description} limit={620} />
              )}

              <div className="mt-6 flex flex-wrap gap-3">
                <Link
                  to={`/visualizer?node=${encodeURIComponent(thinker.nodeId)}`}
                  className="inline-flex items-center gap-2 min-h-11 px-4 py-2 rounded-full border border-white/15 bg-white/[0.04] text-white/70 hover:text-white hover:bg-white/[0.08] text-xs font-body transition-colors"
                >
                  <Network className="w-3.5 h-3.5" />
                  Open in graph
                </Link>
                {/* Hidden until the canonical id resolves — linking to an
                    unresolved work is how the dead-UUID failure looked. */}
                {passage.state === 'ready' && (
                  <Link
                    to={`/texts/${encodeURIComponent(passage.data.workId)}`}
                    className="inline-flex items-center gap-2 min-h-11 px-4 py-2 rounded-full border border-white/15 bg-white/[0.04] text-white/70 hover:text-white hover:bg-white/[0.08] text-xs font-body transition-colors"
                  >
                    <BookOpen className="w-3.5 h-3.5" />
                    Read the work
                    <ExternalLink className="w-3 h-3 opacity-60" />
                  </Link>
                )}
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

              {passage.state === 'ready' && passage.data.passage && (
                <PassageBody passage={passage.data.passage} accentText={accent.text} />
              )}

              {passage.state === 'ready' && !passage.data.passage && (
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

/**
 * Knowledge-graph descriptions state the scholarly disagreement LAST — the
 * counter-position is the closing sentence. A hard 620-character cut therefore
 * decapitated it every time: on Alexander it fell just before "Frede… considers
 * the position philosophically incoherent". Truncating a passage that records a
 * controversy into one that asserts a consensus is a scholarly defect, not a
 * layout choice, so the remainder stays one click away and the cut lands on a
 * word boundary.
 */
function ExpandableDescription({ text, limit }: { text: string; limit: number }) {
  const [expanded, setExpanded] = useState(false);
  const needsCut = text.length > limit;
  const head = useMemo(() => {
    if (!needsCut) return text;
    const slice = text.slice(0, limit);
    const lastSpace = slice.lastIndexOf(' ');
    return (lastSpace > limit * 0.6 ? slice.slice(0, lastSpace) : slice).trimEnd();
  }, [text, limit, needsCut]);

  return (
    <div className="font-body text-[0.95rem] sm:text-base text-white/70 leading-relaxed">
      <p>{needsCut && !expanded ? `${head}…` : text}</p>
      {needsCut && (
        <button
          type="button"
          onClick={() => setExpanded((v) => !v)}
          aria-expanded={expanded}
          className="mt-2 min-h-11 font-body text-xs uppercase tracking-wider text-white/60 underline decoration-white/25 underline-offset-4 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/40"
        >
          {expanded ? 'Show less' : 'Read the full entry'}
        </button>
      )}
    </div>
  );
}

/**
 * Wrap Greek runs so they are both readable and machine-legible.
 *
 * The stance lines quote Greek inline (εἱμαρμένη, αὐτεξούσιον) inside prose set
 * in Instrument Serif / DM Sans, neither of which has Greek coverage — so the
 * polytonic silently fell back to Georgia mid-sentence, in a different face and
 * a different colour of grey. EB Garamond covers both scripts, and `lang="grc"`
 * is what tells a screen reader and a search engine what they are looking at.
 */
const GREEK_RUN = /([Ͱ-Ͽἀ-῿][Ͱ-Ͽἀ-῿\s'’·]*)/g;
// Separate, NON-global copy: `.test()` on a /g regex advances lastIndex, so
// reusing GREEK_RUN to classify the split parts would skip every other match.
const HAS_GREEK = /[Ͱ-Ͽἀ-῿]/;

export function WithGreek({ text }: { text: string }) {
  const parts = useMemo(() => text.split(GREEK_RUN), [text]);
  return (
    <>
      {parts.map((part, i) =>
        HAS_GREEK.test(part) ? (
          <span key={i} lang="grc" className="font-garamond">
            {part}
          </span>
        ) : (
          part
        ),
      )}
    </>
  );
}

// Some corpus rows prefix the original text with an editorial sigil
// ("Latin:", "Greek (…):"). Surface it as a label; never alter the text itself.
const SIGIL = /^\s*(Latin|Greek|Latin \([^)]*\)|Greek \([^)]*\))\s*:\s*/i;

/** Best-effort script detection, for the `lang` attribute only. */
function scriptOf(text: string, declared?: string): 'grc' | 'la' | undefined {
  if (/[Ͱ-Ͽἀ-῿]/.test(text)) return 'grc';
  if (declared === 'lat' || declared === 'la') return 'la';
  return undefined;
}

// Render one corpus passage. No fabrication: only what the API returns is shown.
function PassageBody({
  passage,
  accentText,
}: {
  passage: Passage;
  accentText: string;
}) {
  const rawWithSigil = (passage.text_content ?? '').trim();
  const sigil = SIGIL.exec(rawWithSigil)?.[1];
  const raw = sigil ? rawWithSigil.replace(SIGIL, '') : rawWithSigil;
  const [expanded, setExpanded] = useState(false);
  const needsCut = raw.length > 460;
  const head = useMemo(() => {
    if (!needsCut) return raw;
    const slice = raw.slice(0, 460);
    const lastSpace = slice.lastIndexOf(' ');
    return (lastSpace > 300 ? slice.slice(0, lastSpace) : slice).trimEnd();
  }, [raw, needsCut]);
  const ref = passage.reference || passage.citation;
  // Instrument Serif (font-display) carries no Greek, so polytonic dropped
  // silently to Georgia mid-sentence. EB Garamond covers Greek and Latin.
  const lang = scriptOf(raw, passage.language);

  return (
    <>
      <blockquote
        lang={lang}
        className="font-garamond text-lg sm:text-xl text-white/90 leading-[1.85]"
      >
        {needsCut && !expanded ? `${head}…` : raw}
      </blockquote>
      {needsCut && (
        <button
          type="button"
          onClick={() => setExpanded((v) => !v)}
          aria-expanded={expanded}
          className="mt-3 min-h-11 font-body text-xs uppercase tracking-wider text-white/60 underline decoration-white/25 underline-offset-4 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/40"
        >
          {expanded ? 'Show less' : 'Read the whole passage'}
        </button>
      )}
      {(ref || sigil) && (
        <p
          className={cn(
            'mt-4 font-body text-xs uppercase tracking-wider',
            accentText,
          )}
        >
          {[sigil, ref && !isOpaqueRef(ref) ? ref : null]
            .filter(Boolean)
            .join(' · ')}
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

  // This is the most motion-heavy page in the app and honoured no motion
  // preference at all: entrance animations, an infinite scroll-hint pulse and
  // two unconditional smooth scrolls. MotionConfig covers every framer-motion
  // element at once; the scroll calls have to be guarded by hand.
  const reduceMotion = useReducedMotion();

  const scrollTo = useCallback(
    (id: string) => {
      const el = document.getElementById(id);
      if (el && containerRef.current) {
        containerRef.current.scrollTo({
          top: el.offsetTop,
          behavior: reduceMotion ? 'auto' : 'smooth',
        });
      }
    },
    [reduceMotion],
  );

  return (
    <MotionConfig reducedMotion="user">
    <div
      ref={containerRef}
      className="overflow-y-scroll relative bg-zinc-950"
      style={
        {
          scrollSnapType: 'y mandatory',
          scrollBehavior: reduceMotion ? 'auto' : 'smooth',
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
            {/* c. 279 BCE (Chrysippus) to 524 CE (Boethius) is 803 years. */}
            An eight-century argument
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
    </MotionConfig>
  );
}
