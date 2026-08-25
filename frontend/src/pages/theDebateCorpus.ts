/**
 * theDebateCorpus — the data layer behind /the-debate.
 *
 * Split out of TheDebatePage so the page file exports only components, and so
 * the corpus addressing can be tested without mounting a scroll-snap deck.
 *
 * Works are addressed by `canonical_id`, NEVER by the `work_id` UUID. The UUID
 * is derived from the work record, so a re-ingest mints a new one: the 2026-06
 * set that used to be hardcoded died in the 2026-08-24 rebuild and every
 * passage card on the live page silently degraded to "No passage indexed for
 * this work yet" — the page's whole premise, gone, with no error.
 * `canonical_id` comes from the CTS URN and survives.
 *
 * Verified live against https://free-will.app, 2026-08-26:
 *   Chrysippus  tlg1264_tlg001_1st1k_grc1_grc
 *               SVF II Fragmenta Logica et Physica (88 passages, Greek)
 *   Alexander   tlg0732_tlg014_grc — De Fato (39 passages, Greek)
 *   Origen      work_de_principiis_origen_230s_v2w3x4y5_grc
 *               De Principiis III.1 (Περὶ αὐτεξουσίου), 25 passages, Greek.
 *               Replaces Contra Celsum, which holds 2 passages and is not
 *               where Origen argues the point.
 *   Augustine   urn_cts_latinlit_stoa0040_stoa003_lat — De Libero Arbitrio
 *               (171 passages). Corpus text is Perseus stoa0040.stoa003, not
 *               CCSL 29 — cite it as such.
 *   Boethius    urn_cts_latinlit_phi2089_phi002_lat — De consolatione
 *               philosophiae (129 passages). Prefer this over the …_phi002_eng
 *               row, which carries the same Latin text under language "eng".
 *
 * KNOWN CORPUS DEFECTS in these works — not render bugs:
 *   - Boethius rows are prefixed with a literal "Latin: " and carry OCR damage
 *     ("conprehendentimn", "iutueamur", stray {braces}).
 *   - Alexander De fato 15 reads `\u1f14\u03c7\u03b5\u03b9` with an injected "[...]" where Bruns
 *     185.21 has the sphere simile.
 *   - SVF II 931 contains a bad find/replace ("\u03c4\u03b1\u1f50Augustinus \u03c4\u1f78\u03bd").
 * These need a reviewed apply-script under scripts/, not a display-side hack.
 */

import { useEffect, useState } from 'react';
import { apiEndpoint } from '../api/baseUrl';

export type Accent = 'orange' | 'rose' | 'violet' | 'amber' | 'sky';

export interface Thinker {
  id: string;
  nav: string;
  name: string;
  dates: string;
  school: string;
  /** One-line framing of this thinker's move in the debate. */
  stance: string;
  /** Knowledge-Graph node id (GET /api/kg/nodes/:id). */
  nodeId: string;
  /** Stable corpus identifier (`canonical_id`, derived from the CTS URN).
   *  NOT the `work_id` UUID — that one is re-minted on every re-ingest. */
  workCanonicalId: string;
  /** Pretty work label + citation hint shown above the passage. */
  workLabel: string;
  /** Who this thinker is answering — drives the lineage graphic. */
  respondsTo: string | null;
  accent: Accent;
}

// Chronological order = narrative order.
export const THINKERS: Thinker[] = [
  {
    id: 'chrysippus',
    nav: 'Chrysippus',
    name: 'Chrysippus of Soli',
    dates: 'c. 279 – c. 206 BCE',
    school: 'Stoic',
    stance:
      'Sets the terms: everything is woven into fate (εἱμαρμένη), yet assent and what is "up to us" remain genuinely ours.',
    nodeId: 'person_chrysippus_280_206bce_i9j0k1l2',
    workCanonicalId: 'tlg1264_tlg001_1st1k_grc1_grc',
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
    workCanonicalId: 'tlg0732_tlg014_grc',
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
    workCanonicalId: 'work_de_principiis_origen_230s_v2w3x4y5_grc',
    workLabel: 'De Principiis III.1 — Περὶ αὐτεξουσίου (SC 268)',
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
    workCanonicalId: 'urn_cts_latinlit_stoa0040_stoa003_lat',
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
    workCanonicalId: 'urn_cts_latinlit_phi2089_phi002_lat',
    workLabel: 'De Consolatione Philosophiae, Bk V',
    respondsTo: 'Augustine',
    accent: 'sky',
  },
];

export interface KgNode {
  description?: string;
  school?: string;
}

export interface Passage {
  text_content?: string;
  reference?: string;
  citation?: string;
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
 * `work_id` is a deterministic UUID derived from the work record, so a
 * re-ingest mints a new one and every hardcoded UUID dies silently — which is
 * exactly how this page lost all five of its passages. `canonical_id` is
 * derived from the CTS URN and survives the rebuild, so it is what the
 * THINKERS table stores. One shared request serves all five sections.
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

export function usePassage(canonicalId: string): Loadable<ResolvedPassage> {
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
        const response = await fetch(
          `${apiEndpoint(`/api/works/${encodeURIComponent(workId)}/passages`)}?limit=1`,
          { headers: { Accept: 'application/json' } },
        );
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = (await response.json()) as PassagesResponse;
        return { passage: data.passages?.[0] ?? null, workId };
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
  }, [canonicalId]);
  return result;
}

