export const meta = {
  name: 'kg-audit-wave1',
  description: 'Zero-hallucination integrity audit (Wave 1): Greek fabrication + person/work facts, attribution & bibliography, each adversarially verified against corpus + scholarship',
  phases: [
    { title: 'Scan', detail: 'batch-triage persons + works for false facts / misattribution / bad bibliography' },
    { title: 'Verify', detail: 'adversarial per-item verification vs corpus + web; Greek fabrication candidates' },
    { title: 'Synthesize', detail: 'aggregate verdicts, write ledger' },
  ],
}

const N_GREEK = args?.n_greek ?? 173
const N_PERSON = args?.n_person_batches ?? 21
const N_WORK = args?.n_work_batches ?? 11
const BS = args?.batch_size ?? 22

const FINDINGS = {
  type: 'object',
  properties: {
    batch_total: { type: 'number', description: 'nodes examined in this batch' },
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          node_id: { type: 'string' },
          dimension: { enum: ['J1_false_fact', 'J2_greek', 'J3_biblio', 'J4_misattribution', 'J5_anachronism'] },
          severity: { enum: ['critical', 'high', 'medium', 'low'] },
          issue: { type: 'string' },
          evidence: { type: 'string', description: 'exact quote from the node showing the problem' },
          field: { type: 'string', description: 'description | metadata.birth_date | metadata.edition | ...' },
          current: { type: ['string', 'null'] },
          proposed: { type: ['string', 'null'] },
          fix_class: { enum: ['mechanical', 'scholarly'] },
          scanner_confidence: { type: 'number' },
        },
        required: ['node_id', 'dimension', 'severity', 'issue', 'field', 'fix_class', 'scanner_confidence'],
      },
    },
  },
  required: ['findings'],
}

const VERDICT = {
  type: 'object',
  properties: {
    node_id: { type: 'string' },
    dimension: { type: 'string' },
    verdict: { enum: ['confirmed', 'rejected', 'needs_human'] },
    severity: { enum: ['critical', 'high', 'medium', 'low'] },
    issue: { type: 'string' },
    evidence: { type: 'string' },
    field: { type: 'string' },
    current: { type: ['string', 'null'] },
    proposed: { type: ['string', 'null'] },
    fix_class: { enum: ['mechanical', 'scholarly'] },
    final_confidence: { type: 'number' },
    sources: { type: 'array', items: { type: 'string' } },
    rationale: { type: 'string' },
  },
  required: ['node_id', 'dimension', 'verdict', 'severity', 'fix_class', 'final_confidence'],
}

const PREAMBLE = `cwd is the repo root. FIRST read data/audit/RULES.md (short, binding). Judge against REAL data via \`python3 scripts/audit_fetch.py ...\`, never memory. Use WebSearch/WebFetch to confirm specific dates, editions (SC/GCS/CCSL/PL/Loeb), Wikidata QIDs, translators, or whether a Greek quote is genuine. NEVER compose ancient Greek/Latin. When unsure, prefer a low-confidence flag (scanner) or needs_human (verifier) over a guess.`

function scanPrompt(type, k) {
  return `You are a rigorous classical-philosophy + philology scholar auditing EleutherIA KG ${type} nodes for hallucination. ${PREAMBLE}

Your batch: run \`python3 scripts/audit_fetch.py slice ${type} ${k} ${BS}\` to get your node_ids (comma-separated). For EACH id run \`python3 scripts/audit_fetch.py node <id>\` and read description + citations + cited passage text.

Flag ONLY genuine problems (high precision — do not nitpick prose style):
- J1_false_fact: wrong birth/death/floruit dates beyond accepted scholarly range; false "first to…" claims; invented works/doctrines; wrong school/teacher/influence; fabricated/incorrect wikidata QID.
- J4_misattribution: a doctrine, work, or claim attributed to the wrong person.
- J2_greek: embedded Greek/Latin that looks composed or cannot be sourced (check with \`audit_fetch.py corpus\` + web).
- J3_biblio: a fabricated or wrong edition / bibliographic reference (SC/GCS/CCSL/PL/Loeb number, DOI, ISBN, translator). Verify the specific number/name via web.
- J5_anachronism: an UNHEDGED modern label (compatibilism/libertarian/determinism/…) asserted as ancient historical fact.

For each problem emit one finding with the exact field, current value, and a grounded proposed value (or proposed:null + low confidence if you cannot source a fix). Set batch_total to how many nodes you examined. Clean nodes produce no finding. Return via StructuredOutput.`
}

function verifyPrompt(f) {
  return `You are an ADVERSARIAL verifier. A scanner flagged this finding:
${JSON.stringify(f)}

Your job is to try to REFUTE it, then issue a verdict. ${PREAMBLE}

Steps: run \`python3 scripts/audit_fetch.py node ${f.node_id}\` to see the real node + evidence. Independently check the specific claim against authoritative scholarship (Wikidata, Perseus/TLG, SEP, Brill/OUP, critical-edition metadata) via WebSearch/WebFetch.

Verdict:
- confirmed: the problem is real AND you can ground the correction in a citable source — give exact field/current/proposed + sources.
- rejected: scanner was wrong, node is actually correct — explain in rationale.
- needs_human: a real concern you cannot safely resolve (ambiguous scholarship / no source) — proposed:null.
ZERO hallucination: never propose ancient Greek/Latin you cannot cite. Default to needs_human over guessing a fix.

Finally write your full verdict JSON to data/audit/wave1/${f.dimension}__${f.node_id}.json (run \`mkdir -p data/audit/wave1\` first). Then return the verdict via StructuredOutput.`
}

function greekPrompt(i) {
  return `A deterministic prefilter found Greek run(s) in ONE node's description that are NOT present verbatim in our (partial, ~174-work) corpus. Decide, per run, if it is: legit_corpus_gap (a real quote from a work we don't hold), legit_term (a Greek title / technical term / short phrase), or FABRICATED (composed, unverifiable ancient prose = academic fraud). ${PREAMBLE}

Get your node: \`sed -n '${i}p' data/audit/greek_unmatched.jsonl\` (gives node_id + unmatched_runs). Full node: \`python3 scripts/audit_fetch.py node <node_id>\`.
Per unmatched run: try \`python3 scripts/audit_fetch.py corpus "<distinctive 4-6 word chunk>"\`; then WebSearch the Greek (plus a transliteration/English) against TLG/Perseus/scholarship and named editions.

Node verdict = worst case across its runs:
- Any run FABRICATED → verdict confirmed, severity critical, field 'description', fix_class scholarly, proposed = the description with the fabricated Greek REPLACED BY AN ENGLISH PARAPHRASE or removed (NEVER invent replacement Greek; only insert real Greek if you found the exact sourced text).
- All runs legit_term/legit_corpus_gap with correct spelling → verdict rejected.
- A real term with wrong accents/sigma AND you found the correct sourced form → verdict confirmed, fix_class mechanical, proposed = corrected form (sourced only).
- Cannot decide → needs_human.

Write your full verdict JSON to data/audit/wave1/greek__<node_id>.json (mkdir -p first). Return via StructuredOutput.`
}

// ---- Phase 1+2: persons & works (scan -> adversarial verify, pipelined) ----
phase('Scan')
const scanJobs = []
for (let k = 0; k < N_PERSON; k++) scanJobs.push({ type: 'person', k })
for (let k = 0; k < N_WORK; k++) scanJobs.push({ type: 'work', k })

const pwResults = await pipeline(
  scanJobs,
  job => agent(scanPrompt(job.type, job.k), { label: `scan:${job.type}:${job.k}`, phase: 'Scan', schema: FINDINGS, model: 'sonnet' }),
  (scan, job) => parallel(((scan && scan.findings) || []).map(f => () =>
    agent(verifyPrompt(f), { label: `verify:${f.dimension}:${(f.node_id || '').slice(0, 28)}`, phase: 'Verify', schema: VERDICT })
  )),
)
const pwVerdicts = pwResults.flat().filter(Boolean)
log(`person/work: ${pwVerdicts.length} findings verified`)

// ---- Greek fabrication candidates: direct adversarial verification ----------
phase('Verify')
const greekVerdicts = (await parallel(
  Array.from({ length: N_GREEK }, (_, i) => () =>
    agent(greekPrompt(i + 1), { label: `greek:${i + 1}`, phase: 'Verify', schema: VERDICT })),
)).filter(Boolean)
log(`greek: ${greekVerdicts.length}/${N_GREEK} verified`)

// ---- Phase 3: synthesize -----------------------------------------------------
phase('Synthesize')
const all = [...pwVerdicts, ...greekVerdicts]
const trim = v => ({
  node_id: v.node_id, dimension: v.dimension, verdict: v.verdict, severity: v.severity,
  field: v.field, fix_class: v.fix_class, final_confidence: v.final_confidence,
})
const counts = {
  scan_jobs: scanJobs.length,
  person_work_findings: pwVerdicts.length,
  greek_checked: greekVerdicts.length,
  verdicts: all.length,
  confirmed: all.filter(v => v.verdict === 'confirmed').length,
  needs_human: all.filter(v => v.verdict === 'needs_human').length,
  rejected: all.filter(v => v.verdict === 'rejected').length,
  confirmed_critical: all.filter(v => v.verdict === 'confirmed' && v.severity === 'critical').length,
  confirmed_high: all.filter(v => v.verdict === 'confirmed' && v.severity === 'high').length,
}
log(`Wave 1 done: ${JSON.stringify(counts)}`)
return { counts, index: all.map(trim) }
