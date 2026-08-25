/**
 * the-debate — shared types.
 *
 * These are deliberately *narrower* than the page's own `Thinker`: every
 * component here asks for the smallest shape it can work with, so the corpus
 * module in `pages/theDebateCorpus.ts` stays the single source of truth and
 * an object from there is structurally assignable to any of these.
 *
 * `tone` encodes the LANGUAGE OF THE SOURCE, nothing else. It is the one
 * colour decision on the page and it carries a finding: the argument is
 * Greek until Augustine and Latin after him. A hue that means nothing is
 * decoration; this one is data.
 */

/** Language of the primary source a station rests on. */
export type Tone = 'greek' | 'latin' | 'meta';

/** The minimum a station needs to render its heading block. */
export interface ThinkerLike {
  id: string;
  nav: string;
  name: string;
  dates: string;
  school: string;
  /** What this figure holds. One sentence, present tense. */
  stance: string;
  /** The modern disagreement about them. Named scholars. Never resolved. */
  contested: string;
  /** Who they actually argued against. Not "who they replied to". */
  opponent: string;
  /** Attested reuse of an argument, by figure `nav`. The Carneadean thread. */
  inheritsFrom?: string[];
  nodeId: string;
  workCanonicalId: string;
  workLabel: string;
  passageRef?: string;
  passageNote?: string;
  tone: Tone;
  coda?: boolean;
}

/** One facing-page unit: an original and its translation, with its apparatus. */
export interface Locus {
  /** Original-language text. NEVER truncated, by anyone, for any reason. */
  original: string;
  originalLang: 'grc' | 'la';
  /** English translation. May be truncated; say so when you do. */
  translation?: string;
  /** Human locus: "De consolatione philosophiae V.6". */
  reference?: string;
  /** CTS URN. The FAIR promise, made visible and copyable. */
  urn?: string;
  /** Editorial note about the transmission — the scholarship, not a caption. */
  note?: string;
}

/**
 * Async state for the locus. `empty` is distinct from `error`: one means the
 * corpus answered and had nothing, the other means it did not answer.
 */
export type LocusState =
  | { status: 'loading' }
  | { status: 'error' }
  | { status: 'empty' }
  | { status: 'ready'; locus: Locus };
