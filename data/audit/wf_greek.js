export const meta = {
  name: 'kg-audit-greek-j2',
  description: 'J2 fabrication audit: verify the 173 nodes whose embedded Greek is absent from the corpus — legit corpus-gap / legit term / FABRICATED',
  phases: [{ title: 'Verify', detail: 'batched adversarial verification of unmatched Greek runs vs corpus + scholarship' }],
}

const TOTAL = args?.total ?? 173
const PER = args?.per ?? 5
const N = Math.ceil(TOTAL / PER)

const VERDICT_ITEM = {
  type: 'object',
  properties: {
    node_id: { type: 'string' },
    dimension: { const: 'J2_greek' },
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
    run_classifications: { type: 'array', items: { type: 'string' } },
  },
  required: ['node_id', 'dimension', 'verdict', 'severity', 'fix_class', 'final_confidence'],
}
const BATCH = { type: 'object', properties: { verdicts: { type: 'array', items: VERDICT_ITEM } }, required: ['verdicts'] }

function prompt(k) {
  const start = k * PER + 1
  const end = Math.min((k + 1) * PER, TOTAL)
  return `You audit ancient-Greek fabrication in a scholarly KG. cwd = repo root, use python3. FIRST read data/audit/RULES.md (binding). The corpus is PARTIAL (~174 works) so "absent from corpus" does NOT mean fabricated.

Handle nodes on lines ${start}..${end} of data/audit/greek_unmatched.jsonl. For EACH line:
1. \`sed -n '${'$'}{LINE}p' data/audit/greek_unmatched.jsonl\` → gives node_id + unmatched_runs (Greek strings not found verbatim in corpus).
2. \`python3 scripts/audit_fetch.py node <node_id>\` → full description + citations + cited-passage text.
3. For each unmatched run, classify:
   - legit_term: a Greek title / technical term / short stock phrase (e.g. Περὶ προνοίας, αὐτεξούσιον). Verify spelling only.
   - legit_corpus_gap: a real quotation from a work we simply do not hold. Confirm via WebSearch/WebFetch against TLG/Perseus/named critical editions/scholarship.
   - FABRICATED: composed, unverifiable ancient prose that no source attests — academic fraud.

Node verdict = worst case across its runs:
- any FABRICATED → verdict 'confirmed', severity 'critical', field 'description', fix_class 'scholarly', proposed = the description with the fabricated Greek REPLACED BY AN ENGLISH PARAPHRASE (NEVER invent replacement Greek; insert real Greek only if you found the exact sourced text). Put run_classifications.
- all legit with correct spelling → verdict 'rejected'.
- a real term with wrong accents/sigma AND you found the correct SOURCED form → verdict 'confirmed', fix_class 'mechanical', current=the wrong form, proposed=corrected form (surgical, sourced only).
- cannot decide → 'needs_human', proposed:null.

ZERO hallucination: never output Greek you cannot cite. For each node, write its full verdict to data/audit/wave1/greek__<node_id>.json (run \`mkdir -p data/audit/wave1\` first). Then return all ${end - start + 1} verdicts via StructuredOutput.`
}

phase('Verify')
const results = await parallel(Array.from({ length: N }, (_, k) => () =>
  agent(prompt(k), { label: `greek:${k * PER + 1}-${Math.min((k + 1) * PER, TOTAL)}`, phase: 'Verify', schema: BATCH })))
const verdicts = results.filter(Boolean).flatMap(r => r.verdicts || [])
const by = v => verdicts.filter(v).length
log(`greek J2: ${verdicts.length} nodes verified`)
return {
  counts: {
    nodes: verdicts.length,
    confirmed: by(v => v.verdict === 'confirmed'),
    fabricated: by(v => v.verdict === 'confirmed' && v.severity === 'critical'),
    rejected: by(v => v.verdict === 'rejected'),
    needs_human: by(v => v.verdict === 'needs_human'),
  },
  index: verdicts.map(v => ({ node_id: v.node_id, verdict: v.verdict, severity: v.severity, fix_class: v.fix_class })),
}
