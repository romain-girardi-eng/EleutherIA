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
  ORIGIN_QUESTION,
  THINKERS,
  useKgNode,
  usePassage,
  type Passage,
  type Thinker,
  type Tone,
} from './theDebateCorpus';

// ─── Config ──────────────────────────────────────────────────────────────────

/**
 * Tone palette — hue carries information, it does not decorate.
 *
 * The page used to run five per-person accents (orange/rose/violet/amber/sky)
 * that existed in no design token and encoded nothing. Two tones tracking the
 * language of the SURVIVING TEXT do encode something: read down the page and
 * the colour itself shows the debate migrating out of Greek and into Latin at
 * Augustine. `meta` is the modern-scholarship band, which is not a ninth
 * thinker and must not be coloured like one.
 *
 * Static class strings so Tailwind's scanner keeps them.
 */
const TONE: Record<
  Tone,
  {
    text: string;
    chipBg: string;
    chipBorder: string;
    dot: string;
    rule: string;
    glow: string;
    label: string;
  }
> = {
  greek: {
    text: 'text-sky-200',
    chipBg: 'bg-sky-500/10',
    chipBorder: 'border-sky-300/30',
    dot: 'bg-sky-300',
    rule: 'from-sky-300/70',
    glow: 'bg-[radial-gradient(ellipse_at_center,rgba(56,189,248,0.16),transparent_70%)]',
    label: 'Greek',
  },
  latin: {
    text: 'text-orange-200',
    chipBg: 'bg-orange-500/10',
    chipBorder: 'border-orange-300/30',
    dot: 'bg-orange-300',
    rule: 'from-orange-300/70',
    glow: 'bg-[radial-gradient(ellipse_at_center,rgba(249,115,22,0.16),transparent_70%)]',
    label: 'Latin',
  },
  meta: {
    text: 'text-stone-200',
    chipBg: 'bg-white/[0.06]',
    chipBorder: 'border-white/20',
    dot: 'bg-white/60',
    rule: 'from-white/50',
    glow: 'bg-[radial-gradient(ellipse_at_center,rgba(255,255,255,0.07),transparent_70%)]',
    label: 'Modern scholarship',
  },
};

// ─── Data hooks ──────────────────────────────────────────────────────────────

// ─── Section ─────────────────────────────────────────────────────────────────

function DebateSection({ thinker, index }: { thinker: Thinker; index: number }) {
  const node = useKgNode(thinker.nodeId);
  const passage = usePassage(thinker.workCanonicalId, thinker.passageRef);
  const accent = TONE[thinker.tone];

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
          {/* The opponent, not a predecessor. The page used to print
              "answers {previous thinker}" for a chain that never existed. */}
          <span className="inline-flex items-center gap-1.5 text-xs font-body text-white/45">
            <ArrowDownRight className="w-3.5 h-3.5" aria-hidden="true" />
            against {thinker.opponent}
          </span>
          {thinker.coda && (
            <span className="rounded-full border border-white/15 px-3 py-1 text-[11px] font-body uppercase tracking-[0.16em] text-white/40">
              Coda
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
                  {['w-[96%]', 'w-[88%]', 'w-[92%]', 'w-[70%]'].map((w) => (
                    <div
                      key={w}
                      className={cn('h-3.5 rounded bg-white/[0.06] animate-pulse', w)}
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

              {/* The modern disagreement, attributed and left unresolved. The
                  page used to speak in a single authorial voice while the
                  knowledge graph behind it recorded the controversy. */}
              <div className="mt-6 border-l-2 border-white/12 pl-4">
                <p className="mb-1.5 font-body text-[0.7rem] uppercase tracking-[0.16em] text-white/35">
                  Still disputed
                </p>
                <p className="font-body text-[0.9rem] leading-relaxed text-white/55">
                  <WithGreek text={thinker.contested} />
                </p>
              </div>

              {thinker.inheritsFrom && thinker.inheritsFrom.length > 0 && (
                <p className="mt-4 font-body text-[0.8rem] text-white/40">
                  <span className="uppercase tracking-[0.14em] text-white/30">
                    Argument reused from{' '}
                  </span>
                  {thinker.inheritsFrom.join('; ')}
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
                  {['w-full', 'w-[94%]', 'w-[78%]'].map((w) => (
                    <div
                      key={w}
                      className={cn('h-4 rounded bg-white/[0.06] animate-pulse', w)}
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
                  {thinker.passageRef
                    ? `Locus ${thinker.passageRef} is not in the corpus under this work.`
                    : 'No passage indexed for this work yet.'}
                </p>
              )}

              {/* Several of these figures wrote nothing that survives. Saying
                  so under the quotation is the difference between a source and
                  a testimonium. */}
              {thinker.passageNote && (
                <p className="mt-4 border-t border-white/10 pt-3 font-body text-[0.78rem] leading-relaxed text-white/40">
                  {thinker.passageNote}
                </p>
              )}
            </motion.figure>

            <motion.div
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.7, delay: 0.2 }}
            >
              <OpponentRoster activeId={thinker.id} />
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
        className={cn(
          'font-garamond text-lg sm:text-xl leading-[1.85] text-white/90',
          // EB Garamond's `locl` feature fires on lang="la" and respells the
          // text epigraphically: `igitur` renders as `igitvr`, `volubilitatem`
          // as `volvbilitatem`. That is a defensible convention for an
          // inscription and a silent alteration of a critical edition, which
          // this project forbids. The tag stays for screen readers and
          // hyphenation; the substitution goes.
          lang === 'la' && "[font-feature-settings:'locl'_0]",
        )}
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

/**
 * Who each of them was arguing with.
 *
 * This replaces "The chain of replies", which asserted a sequence of answers
 * that the sources do not support in a single link. The vertical connector is
 * gone with it: a line between two names is a claim, and the claim was false.
 * What remains is a roster of positions with their real targets — plus the
 * attested reuse of arguments, which is the one thing that genuinely travelled.
 */

function OpponentRoster({ activeId }: { activeId: string }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.025] p-5">
      <p className="mb-4 font-body text-[0.7rem] uppercase tracking-[0.16em] text-white/35">
        Who each of them was arguing with
      </p>
      <ul className="space-y-3">
        {THINKERS.map((t) => {
          const isActive = t.id === activeId;
          const accent = TONE[t.tone];
          return (
            <li key={t.id} className="relative pl-6">
              <span
                className={cn(
                  'absolute left-0 top-1.5 h-2.5 w-2.5 rounded-full ring-2 ring-zinc-950 transition-transform',
                  isActive ? accent.dot : 'bg-white/20',
                  isActive && 'scale-125',
                )}
                aria-hidden
              />
              <p
                className={cn(
                  'font-body text-sm transition-colors',
                  isActive ? cn(accent.text, 'font-semibold') : 'text-white/45',
                )}
              >
                {t.nav}
              </p>
              <p className="font-body text-[0.72rem] leading-snug text-white/30">
                against {t.opponent}
              </p>
            </li>
          );
        })}
      </ul>
      <p className="mt-5 border-t border-white/10 pt-3 font-body text-[0.72rem] leading-relaxed text-white/30">
        Chronological order. Chronology is not causation: none of these figures
        is answering the one above.
      </p>
    </div>
  );
}

/**
 * The cross-cutting band — the section that makes this a scholarly object.
 *
 * Six answers to one question, deliberately irreconcilable and deliberately
 * unranked. The "origin of the will" is a contested modern paradigm, not a
 * finding: the page presents the positions and adjudicates none of them, which
 * is also how the graph's own `debate_origins_notion_of_will_modern_paradigm`
 * node is written.
 */
function OriginQuestionSection() {
  const tone = TONE.meta;
  return (
    <ScrollSectionLocal id="origins" glow={tone.glow}>
      <BackgroundMesh variant="grid" color="rgba(255,255,255,1)" opacity={0.03} />
      <div className="relative z-10 mx-auto w-full max-w-5xl px-4 py-20 sm:px-6">
        <motion.p
          initial={{ opacity: 0, y: -8 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className={cn(
            'mb-6 inline-flex items-center gap-2 rounded-full border px-4 py-1.5 font-body text-xs uppercase tracking-[0.18em]',
            tone.text,
            tone.chipBg,
            tone.chipBorder,
          )}
        >
          What scholars still argue about
        </motion.p>

        <motion.h2
          initial={{ opacity: 0, y: 18 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
          className="font-display text-3xl leading-[1.1] text-white sm:text-4xl lg:text-5xl"
        >
          {ORIGIN_QUESTION.question}
        </motion.h2>

        <ul className="mt-10 grid gap-x-10 gap-y-7 sm:grid-cols-2">
          {ORIGIN_QUESTION.answers.map((a, i) => (
            <motion.li
              key={a.answer}
              initial={{ opacity: 0, y: 14 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.06 * i }}
              className="border-l-2 border-white/12 pl-4"
            >
              <p className="font-display text-xl text-white">{a.answer}</p>
              <p className="mt-0.5 font-body text-[0.75rem] uppercase tracking-[0.14em] text-white/35">
                {a.scholar}
              </p>
              <p className="mt-2 font-body text-[0.92rem] leading-relaxed text-white/55">
                {a.claim}
              </p>
            </motion.li>
          ))}
        </ul>

        <motion.p
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="mt-12 flex flex-wrap items-center gap-4 border-t border-white/10 pt-6 font-body text-sm text-white/40"
        >
          <span>{ORIGIN_QUESTION.disclaimer}</span>
          <Link
            to={`/visualizer?node=${encodeURIComponent(ORIGIN_QUESTION.nodeId)}`}
            className="inline-flex min-h-11 items-center gap-2 rounded-full border border-white/15 bg-white/[0.04] px-4 py-2 text-xs text-white/70 transition-colors hover:bg-white/[0.08] hover:text-white"
          >
            <Network className="h-3.5 w-3.5" aria-hidden="true" />
            Open this debate in the graph
          </Link>
        </motion.p>
      </div>
    </ScrollSectionLocal>
  );
}

// ─── Local ScrollSection wrapper (adds a soft accent glow) ───────────────────

function ScrollSectionLocal({
  id,
  glow,
  children,
}: {
  id: string;
  /** A static Tailwind gradient class from TONE — not a colour string, so the
   *  page keeps the repo's no-inline-`style` rule. */
  glow: string;
  children: React.ReactNode;
}) {
  return (
    <ScrollSectionShell id={id}>
      <div
        className={cn(
          'pointer-events-none absolute -top-1/4 right-0 h-[120%] w-[55%] opacity-60 blur-3xl',
          glow,
        )}
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
      { id: 'origins', label: 'Still disputed' },
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
          className="relative z-10 mx-auto flex min-h-[var(--snap-h,100dvh)] max-w-4xl flex-col items-center justify-center px-6 text-center"
        >
          <motion.span
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55, delay: 0.1 }}
            className="inline-flex items-center gap-2 text-xs font-body uppercase tracking-[0.2em] text-orange-300 border border-orange-400/30 bg-orange-500/10 rounded-full px-4 py-1.5 mb-8"
          >
            <Sparkles className="w-3.5 h-3.5" />
            {/* 341 BCE (Epicurus) to 524 CE (Boethius). Not nine centuries,
                which is what the badge claimed for a shorter span. */}
            Eight centuries of argument
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
            Eight centuries of argument about fate, responsibility, and what —
            if anything — is up to us. Not a relay race toward an answer: a
            contested field, where positions were built, misread and re-armed
            across schools and religions. Every figure is drawn live from the
            knowledge graph; every claim names the scholars who dispute it.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55, delay: 0.46 }}
            className="flex flex-wrap items-center justify-center gap-x-3 gap-y-2 font-body text-sm text-white/40"
          >
            {THINKERS.map((t, i) => (
              <span key={t.id} className="inline-flex items-center gap-3">
                <span className={cn(TONE[t.tone].text)}>{t.nav}</span>
                {/* A middot, not an arrow. An arrow between two names is a
                    claim about influence, and it was the wrong claim. */}
                {i < THINKERS.length - 1 && (
                  <span className="text-white/20" aria-hidden="true">
                    ·
                  </span>
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

      {/* ── The figures ── */}
      {THINKERS.map((thinker, index) => (
        <DebateSection key={thinker.id} thinker={thinker} index={index} />
      ))}

      {/* ── The cross-cutting band: not a ninth thinker ── */}
      <OriginQuestionSection />

      {/* ── Outro ── */}
      <ScrollSection id="outro" className="bg-zinc-950" noInner>
        <BackgroundMesh
          variant="dots"
          color="rgba(255,255,255,1)"
          opacity={0.025}
        />
        <div
          className="relative z-10 mx-auto flex min-h-[var(--snap-h,100dvh)] max-w-3xl flex-col items-center justify-center px-6 text-center"
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
            No one here closed it. On Bobzien’s reading the problem barely
            survived the third century in this form, before returning as a
            theological one. What we inherited is not one continuous argument
            but a set of positions that keep being rebuilt — each of them, here,
            with its evidence attached.
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
