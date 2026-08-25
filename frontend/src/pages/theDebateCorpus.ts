/**
 * theDebateCorpus — the data behind /the-debate.
 *
 * ─── Why this is a field and not a chain ────────────────────────────────────
 *
 * The page used to run Chrysippus → Alexander → Origen → Augustine → Boethius
 * as a chain of replies, each answering the one before. Every link is false:
 *
 *   - Chrysippus is never named in Alexander's De fato; the target is an
 *     unnamed Stoic contemporary (Sharples 1983 p. 22 n. 148; Bobzien 1998
 *     §8.1), and Alexander ignores the co-fated argument, which is Chrysippus's
 *     actual answer (Sharples p. 14).
 *   - Frede 2011 p. 113: Origen's remarks on freedom are "certainly not meant
 *     to be directed against the Stoics"; his targets are astrology and Gnosis.
 *   - Frede 2011 p. 174 reverses the Augustine link: Augustine differs from
 *     Origen "not by moving further away from Stoicism but by adhering to it
 *     much more closely".
 *   - There is no Boethius↔Augustine edge in this project's own graph, Frede
 *     2011 never mentions Boethius, and Augustine already makes the
 *     "foreknowledge is not causation" move (Sorabji 1980 p. 122 n. 6).
 *
 * Kahn 1988 p. 237 named the vice, writing about Dihle: "an Hegelian, even a
 * providential structure, as if the history of Greek thought… amounted to the
 * gradual accumulation of a set of problems to which [X]'s theory of the will
 * was to offer the definitive solution." So the model here is three strata,
 * not one queue: what each figure HOLDS (`stance`), who they were actually
 * arguing WITH (`opponent`), what genuinely travelled between them
 * (`inheritsFrom` — the attested Carneadean thread, not an invented dialogue),
 * and what modern scholars still dispute about them (`contested`, never
 * adjudicated here).
 *
 * ─── Addressing the corpus ──────────────────────────────────────────────────
 *
 * Works are addressed by `canonical_id`, NEVER by the `work_id` UUID. The UUID
 * is derived from the work record, so a re-ingest mints a new one: the 2026-06
 * set that used to be hardcoded died in the 2026-08-24 rebuild and every
 * passage card on the live page silently degraded to "No passage indexed for
 * this work yet" — the page's whole premise, gone, with no error.
 *
 * Every id and locus below verified live against https://free-will.app on
 * 2026-08-26. `passageRef` pins the actual locus classicus: without it the API
 * returns a work's FIRST passage, which for the Consolatio means Book I rather
 * than the Book V argument the stance describes.
 *
 * ─── Known corpus defects in these works — not render bugs ──────────────────
 *   - Boethius rows are prefixed with a literal "Latin: " and carry OCR damage
 *     ("conprehendentimn", "iutueamur") and stray {duplicated} braces.
 *   - Alexander De fato 15 reads `ἔχει` where Bruns 185.16–18 has `ἔχειν`,
 *     which the syntax requires. Verified against TLG0732 and the decoded
 *     Bruns text on disk. The `[...]` in the same passage is NOT a defect: it
 *     re-notates the `***` lacuna sign Bruns himself prints — do not "restore"
 *     it. The work carries 212 token divergences overall and needs
 *     re-ingestion from Bruns rather than patching.
 *   - SVF II 931 reads `ταὐAugustinus τὸν`, a line-join artifact: the printed
 *     line breaks `ταὐ-τὸν` and the next fragment opens `Augustinus de civ.
 *     dei V 8`. Correct reading `ταὐτὸν`, attested at TLG1264 and TLG5026.
 * These need a reviewed apply-script under scripts/, not a display-side hack.
 */

import { useEffect, useState } from 'react';
import { apiEndpoint } from '../api/baseUrl';

/**
 * Hue encodes the SOURCE LANGUAGE, not the individual.
 *
 * Five per-person accents encoded nothing and existed in no design token. Two
 * tones that track the language of the surviving text do carry information:
 * read down the page and the colour itself shows the debate migrating from
 * Greek into Latin. `meta` is the modern-scholarship band, which is not a
 * ninth thinker and must not look like one.
 */
export type Tone = 'greek' | 'latin' | 'meta';

export interface Thinker {
  id: string;
  nav: string;
  name: string;
  dates: string;
  school: string;
  /** Approximate mid-point of activity, negative for BCE. Drives the rail. */
  year: number;
  /** What this figure holds — never what they "prepare" or "anticipate". */
  stance: string;
  /** Who they were actually arguing against. Required: a position with no
   *  opponent invites the reader to supply the wrong one. */
  opponent: string;
  /** The modern disagreement about them, attributed and left unresolved. */
  contested: string;
  /** Attested reuse of arguments. NOT "answers": only what sources support. */
  inheritsFrom?: string[];
  /** Knowledge-Graph node id (GET /api/kg/nodes/:id). */
  nodeId: string;
  /** Stable corpus identifier (`canonical_id`, derived from the CTS URN). */
  workCanonicalId: string;
  workLabel: string;
  /** Exact locus. Without it the API serves the work's first passage. */
  passageRef?: string;
  /** Surfaced verbatim: several of these figures left nothing of their own. */
  passageNote?: string;
  tone: Tone;
  /** Boethius is a coda, not a conclusion — see Sorabji 1980 p. 125. */
  coda?: boolean;
}

// Chronological order. Chronology is NOT causation — see the header.
export const THINKERS: Thinker[] = [
  {
    id: 'epicurus',
    nav: 'Epicurus',
    name: 'Epicurus',
    dates: '341 – 270 BCE',
    school: 'Epicurean',
    year: -300,
    stance:
      'The first to treat determinism as a problem rather than a background truth. If every motion follows from a prior motion, nothing is left over that is ours — so the atoms must, somewhere, swerve.',
    opponent: 'the Democritean chain of causes',
    contested:
      'Huby (1967): Epicurus, not the Stoics, opened the controversy — unlike Aristotle, he saw that there was a problem at all. Bobzien devoted a whole article (2000) to answering "no" to the question whether he discovered the free-will problem. And on the swerve itself almost everyone agrees with Sharples: it seems to buy freedom at the price of randomness.',
    nodeId: 'person_epicurus_341_270bce_j0k1l2m3',
    workCanonicalId: 'urn_cts_latinlit_phi0550_phi001_lat',
    workLabel: 'Lucretius, De Rerum Natura II.250–274',
    passageRef: '2.250-274',
    passageNote:
      'Epicurus’ own statement of the swerve is lost. What survives is Lucretius, two centuries later, in Latin verse.',
    tone: 'latin',
  },
  {
    id: 'chrysippus',
    nav: 'Chrysippus',
    name: 'Chrysippus of Soli',
    dates: 'c. 280 – c. 207 BCE',
    school: 'Stoic',
    year: -240,
    stance:
      'Nothing happens without a cause, our assent included — and for Chrysippus that is exactly why praise and blame stick. The cylinder rolls because it was pushed, and because it is a cylinder.',
    opponent: 'the Lazy Argument',
    contested:
      'Bobzien reads the cylinder as causal attribution, not a power to do otherwise. Gourinat doubts Chrysippus ever used the Greek phrase "up to us" at all. Sorabji thinks the ancients were right to regard the whole manoeuvre as unsuccessful; Salles reads him as anticipating Frankfurt; Brennan says the machinery cheats.',
    nodeId: 'person_chrysippus_280_206bce_i9j0k1l2',
    workCanonicalId: 'urn_cts_latinlit_phi0474_phi054_lat',
    workLabel: 'Cicero, De fato 43',
    passageRef: 'Fat. 43',
    passageNote:
      'Chrysippus’ own words are lost. The cylinder reaches us through Cicero, writing in Latin a century and a half later, and reporting a Stoic he is arguing with.',
    tone: 'latin',
  },
  {
    id: 'carneades',
    nav: 'Carneades',
    name: 'Carneades of Cyrene',
    dates: '214 – 129 BCE',
    school: 'Academic',
    year: -160,
    stance:
      'The Academic refuses both camps at once: Epicurus never needed the swerve. Grant that no motion is uncaused, and you can still deny that everything has external antecedent causes — because our own willing does not.',
    opponent: 'the Stoics and the Epicureans together',
    contested:
      'Sorabji places this first among the ancient replies to the foreknowledge argument. What nobody can settle is how much of it is Carneades: he wrote nothing, and every word we have is Cicero’s.',
    nodeId: 'person_carneades_214_129bce_l2m3n4o5',
    workCanonicalId: 'urn_cts_latinlit_phi0474_phi054_lat',
    workLabel: 'Cicero, De fato 23',
    passageRef: 'Fat. 23',
    passageNote:
      'Carneades published nothing at all. This is Cicero reporting him — and it is the only reason we have any of it.',
    tone: 'latin',
  },
  {
    id: 'epictetus',
    nav: 'Epictetus',
    name: 'Epictetus',
    dates: 'c. 50 – c. 135 CE',
    school: 'Stoic',
    year: 100,
    stance:
      'Freedom relocated inward. No power on earth can compel the faculty that judges its own impressions — and what is up to us is not the power to have done otherwise, but the one thing that cannot be taken.',
    opponent: 'everything outside the self',
    contested:
      'Frede (2011 p. 77): "here we have our first actual notion of a free will" — though on his own reading only the wise person has one. Bobzien denies there is a free-will problem here at all. Blackson argues Frede mistakes the object of choice, so the dating fails either way.',
    nodeId: 'person_epictetus_of_hierapolis_3c385bc2',
    workCanonicalId: 'epictetus_of_hierapolis_epictetus_discourses',
    workLabel: 'Discourses I.1',
    passageRef: 'Discourses I.1',
    passageNote:
      'Epictetus wrote nothing either. The Discourses are notes taken by his student Arrian.',
    tone: 'greek',
  },
  {
    id: 'alexander',
    nav: 'Alexander',
    name: 'Alexander of Aphrodisias',
    dates: 'fl. c. 200 CE',
    school: 'Peripatetic',
    year: 200,
    stance:
      'Against an unnamed Stoic of his own day: unless the same agent in the same circumstances could have chosen otherwise, deliberation, praise and blame are theatre.',
    opponent: 'an unnamed Stoic contemporary — possibly Philopator',
    inheritsFrom: ['Carneades, through Cicero'],
    contested:
      'Bobzien calls this the earliest unambiguous free-will problem in antiquity — and an accident of Aristotle exegesis rather than a discovery. Michael Frede calls the resulting position a hopeless tangle. Sharples, who edited the text, warns that Alexander repeatedly treats determinism as though it were fatalism, and that his reports of the Stoics need considerable caution.',
    nodeId: 'person_alexander_aphrodisias_fl200ce_n5o6p7q8',
    workCanonicalId: 'tlg0732_tlg014_grc',
    workLabel: 'De fato 15',
    passageRef: 'De Fato 15',
    tone: 'greek',
  },
  {
    id: 'origen',
    nav: 'Origen',
    name: 'Origen of Alexandria',
    dates: 'c. 185 – c. 253/254 CE',
    school: 'Christian Platonist',
    year: 230,
    stance:
      'The first treatise in Greek actually titled On Free Decision. Self-determination is what makes divine judgement just — and foreknowledge, Origen argues, is not a cause. His contemporary Plotinus reaches a comparable position independently.',
    opponent: 'astral determinism and Gnostic predestination',
    inheritsFrom: ['Carneades, through Cicero and Alexander'],
    contested:
      'Frede: the argument "proceeds along standard Stoic lines", with terminology taken almost invariably from Epictetus. Fürst: Origen is the first thinker to make freedom the principle of being itself — a reading Fürst himself concedes is not the standard one, and which he directs by name against Frede.',
    nodeId: 'person_origen_alexandria_185_254ce_s9t0u1v2',
    workCanonicalId: 'work_de_principiis_origen_230s_v2w3x4y5_grc',
    workLabel: 'De Principiis III.1 — On Free Decision (Greek, via Philocalia 21)',
    tone: 'greek',
  },
  {
    id: 'augustine',
    nav: 'Augustine',
    name: 'Augustine of Hippo',
    dates: '354 – 430 CE',
    school: 'Latin Patristic',
    year: 395,
    stance:
      'Written against the Manichees between 388 and 395: evil comes from choice, not from a second god. The doctrine of grace that later overshadowed the book was not yet in it — and foreknowledge no more compels the future than your memory compels the past.',
    opponent: 'the Manichees',
    contested:
      'Dihle (1982 p. 144): Augustine invented our modern notion of will, by turning a Roman legal term into a psychological one. Frede: he invented nothing — he stayed closer to the Stoics than Origen did. Gauthier, further still: not one trait of Augustine’s "will" is absent from the Stoics.',
    nodeId: 'person_augustine_hippo_d430',
    workCanonicalId: 'urn_cts_latinlit_stoa0040_stoa003_lat',
    workLabel: 'De libero arbitrio III.4.11',
    passageRef: '3.4.11',
    passageNote:
      'Corpus text is the Perseus edition (stoa0040.stoa003), not CSEL 74 or CCSL 29 — cite it as such.',
    tone: 'latin',
  },
  {
    id: 'boethius',
    nav: 'Boethius',
    name: 'Boethius',
    dates: 'c. 477 – c. 524/526 CE',
    school: 'Late-Antique Platonist',
    year: 524,
    coda: true,
    stance:
      'Awaiting execution, he moves the problem out of time altogether: what is foreknowledge to us is simple present sight to an eternal God, and sight does not compel.',
    opponent: 'the argument from divine foreknowledge',
    contested:
      'Sorabji (1980 p. 125): the timeless-knowledge move comes from Iamblichus, Proclus and Ammonius; what is Boethius’ own is the application to determinism and the seeing analogy — and "it is only when we reach Aquinas" that the answer is complete. Frede’s book on free will does not mention him at all.',
    nodeId: 'person_boethius_480_524ce_w3x4y5z6',
    workCanonicalId: 'urn_cts_latinlit_phi2089_phi002_lat',
    workLabel: 'De consolatione philosophiae V, prosa 6',
    passageRef: 'Cons. 5.P6',
    tone: 'latin',
  },
];

/**
 * The cross-cutting band: who, if anyone, first had a notion of free will.
 *
 * Six positions, deliberately irreconcilable, deliberately unranked. This is
 * the section that makes the page a scholarly object rather than a narrative:
 * the "origin of the will" is a contested modern paradigm, and the graph
 * records each position with its evidence rather than picking one. The KG's
 * own `debate_origins_notion_of_will_modern_paradigm` node is written the same
 * way and says explicitly that it does not assert an invention at any point.
 */
export interface ContestedAnswer {
  /** The answer itself — a figure, or a refusal of the question. */
  answer: string;
  scholar: string;
  claim: string;
}

export const ORIGIN_QUESTION = {
  question: 'Who first had a notion of free will?',
  nodeId: 'debate_origins_notion_of_will_modern_paradigm',
  answers: [
    {
      answer: 'Epicurus',
      scholar: 'Huby (1967)',
      claim: 'He was the first to see that determinism was a problem at all.',
    },
    {
      answer: 'Epictetus',
      scholar: 'Frede (2011)',
      claim:
        'The first actual notion of a free will — though only the wise possess it.',
    },
    {
      answer: 'Alexander',
      scholar: 'Bobzien (1998)',
      claim:
        'The earliest unambiguous evidence — assembled by accident out of a misreading of Aristotle, and marginal in its own day.',
    },
    {
      answer: 'Augustine',
      scholar: 'Dihle (1982)',
      claim:
        'The inventor of our modern notion of will, by way of a Latin legal term.',
    },
    {
      answer: 'Nobody in antiquity',
      scholar: 'Gauthier',
      claim:
        'Every trait of Augustine’s "will" is already Stoic; the concept arrives eleven centuries after Aristotle.',
    },
    {
      answer: 'The wrong question',
      scholar: 'Kahn (1988)',
      claim:
        'Not one problem but a labyrinth of them — and treating it as one produces a providential story rather than a history.',
    },
  ] satisfies ContestedAnswer[],
  disclaimer:
    'This site does not adjudicate. The graph records each position with its evidence.',
};

// ─── Data hooks ──────────────────────────────────────────────────────────────

export interface KgNode {
  description?: string;
  school?: string;
}

export interface Passage {
  text_content?: string;
  reference?: string;
  citation?: string;
  canonical_ref?: string;
  language?: string;
}

interface PassagesResponse {
  passages?: Passage[];
  total?: number;
}

export type Loadable<T> =
  | { state: 'loading' }
  | { state: 'error' }
  | { state: 'ready'; data: T };

export function useKgNode(nodeId: string): Loadable<KgNode> {
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

interface WorkSummary {
  work_id?: string;
  canonical_id?: string | null;
}

interface WorksResponse {
  works?: WorkSummary[];
}

/**
 * Resolve `canonical_id` → `work_id`, once per page load.
 *
 * One shared request serves every section.
 */
let workIndexPromise: Promise<Map<string, string>> | null = null;

/** Test seam — drop the memo between cases. */
export function resetWorkIndexCache(): void {
  workIndexPromise = null;
}

export function loadWorkIndex(): Promise<Map<string, string>> {
  workIndexPromise ??= fetch(`${apiEndpoint('/api/works')}?limit=500`, {
    headers: { Accept: 'application/json' },
  })
    .then((r) => {
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return r.json() as Promise<WorksResponse>;
    })
    .then((data) => {
      const index = new Map<string, string>();
      for (const work of data.works ?? []) {
        if (work.canonical_id && work.work_id) {
          index.set(work.canonical_id, work.work_id);
        }
      }
      return index;
    })
    .catch((err: unknown) => {
      // Never memoise a failure — a transient outage would otherwise leave
      // the page permanently passage-less for the rest of the session.
      workIndexPromise = null;
      throw err;
    });
  return workIndexPromise;
}

export interface ResolvedPassage {
  passage: Passage | null;
  /** Resolved `work_id`, so the "Read the work" link can address /texts/:id. */
  workId: string;
}

/** Passages are fetched in pages of this size while hunting for a locus. */
const PAGE_SIZE = 100;
/** Hard bound on the hunt: the longest work here holds 300 passages. */
const MAX_PAGES = 5;

/**
 * Fetch the passage a section actually means.
 *
 * With no `passageRef` the API's first passage is used, which is what the page
 * did before — and why Boethius was illustrated by the opening poem of Book I
 * instead of the Book V argument about eternity that the section is about.
 * When a ref IS given and cannot be found, this resolves to `passage: null`
 * rather than falling back to an arbitrary one: showing the wrong locus under
 * a precise citation is worse than showing none.
 */
async function fetchPassage(
  workId: string,
  passageRef: string | undefined,
): Promise<Passage | null> {
  for (let page = 0; page < (passageRef ? MAX_PAGES : 1); page += 1) {
    const limit = passageRef ? PAGE_SIZE : 1;
    const response = await fetch(
      `${apiEndpoint(`/api/works/${encodeURIComponent(workId)}/passages`)}?limit=${limit}&offset=${page * PAGE_SIZE}`,
      { headers: { Accept: 'application/json' } },
    );
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = (await response.json()) as PassagesResponse;
    const passages = data.passages ?? [];
    if (!passageRef) return passages[0] ?? null;
    const match = passages.find((p) => p.canonical_ref === passageRef);
    if (match) return match;
    if (passages.length < PAGE_SIZE) break;
  }
  return null;
}

export function usePassage(
  canonicalId: string,
  passageRef?: string,
): Loadable<ResolvedPassage> {
  const [result, setResult] = useState<Loadable<ResolvedPassage>>({
    state: 'loading',
  });
  useEffect(() => {
    let mounted = true;
    setResult({ state: 'loading' });
    loadWorkIndex()
      .then(async (index) => {
        const workId = index.get(canonicalId);
        if (!workId) throw new Error(`unknown_canonical_id:${canonicalId}`);
        return { passage: await fetchPassage(workId, passageRef), workId };
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
  }, [canonicalId, passageRef]);
  return result;
}
