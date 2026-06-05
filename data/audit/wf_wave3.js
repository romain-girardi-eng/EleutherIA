export const meta = {
  name: 'kg-audit-wave3',
  description: 'Wave 3 breadth: hallucination/bibliography/anachronism audit of 845 publications + concepts + ancient arguments, deep web-grounded single-pass (scanner self-verifies)',
  phases: [{ title: 'Audit', detail: 'batched deep audit + self-verification, per-node verdicts' }],
}
const PER = args?.per ?? 8
const TOTAL = args?.total ?? 845
const N = Math.ceil(TOTAL / PER)

const ITEM = {
  type: 'object',
  properties: {
    node_id: { type: 'string' },
    dimension: { enum: ['J1_false_fact', 'J3_biblio', 'J4_misattribution', 'J5_anachronism', 'J2_greek'] },
    verdict: { enum: ['confirmed', 'rejected', 'needs_human'] },
    severity: { enum: ['critical', 'high', 'medium', 'low'] },
    issue: { type: 'string' }, evidence: { type: 'string' },
    field: { type: 'string' }, current: { type: ['string', 'null'] }, proposed: { type: ['string', 'null'] },
    fix_class: { enum: ['mechanical', 'scholarly'] },
    final_confidence: { type: 'number' }, sources: { type: 'array', items: { type: 'string' } }, rationale: { type: 'string' },
  },
  required: ['node_id', 'dimension', 'verdict', 'severity', 'fix_class', 'final_confidence'],
}
const BATCH = { type: 'object', properties: { verdicts: { type: 'array', items: ITEM } }, required: ['verdicts'] }

function prompt(k) {
  const s = k * PER + 1, e = (k + 1) * PER
  return `You are a rigorous classical-philosophy + philology scholar auditing EleutherIA KG nodes (publications, concepts, ancient arguments) for hallucination. cwd=repo root, use python3. FIRST read data/audit/RULES.md (binding).

Handle node_ids on lines ${s}..${e} of data/audit/wave3_nodes.txt (\`sed -n '${s},${e}p' data/audit/wave3_nodes.txt\`). For EACH: \`python3 scripts/audit_fetch.py node <id>\` → description + citations + cited-passage text.

You are BOTH finder and verifier in one pass: when you suspect a problem, independently confirm it via WebSearch/WebFetch against authoritative sources before issuing a 'confirmed' verdict. Check:
- J1_false_fact: wrong dates/attributions, false "first to…", invented works, fabricated wikidata QID, wrong author of a publication.
- J3_biblio: fabricated/wrong publisher, year, series number (SC/GCS/CCSL/PL/Loeb), DOI, ISBN, page range, translator/editor.
- J4_misattribution: doctrine/work/claim assigned to the wrong person.
- J5_anachronism: UNHEDGED modern label (compatibilism/libertarian/determinism/agent-causation) asserted as ancient historical fact (publications/modern-scholarship nodes are exempt — they legitimately use these terms).
- J2_greek: embedded Greek/Latin that you can verify is composed/unsourced (corpus check + web).

Per node emit a verdict:
- confirmed: real problem + a SOURCED fix. For description edits, give a SURGICAL current (exact substring <=300 chars) + proposed (corrected substring). For metadata, field='metadata.<key>'. fix_class mechanical|scholarly.
- rejected: node is correct (the common case).
- needs_human: real concern, no safe sourced fix (proposed:null).
ZERO hallucination: never propose Greek/Latin you cannot cite; never guess a date/edition. Write each node's verdict to data/audit/wave3/<dimension>__<node_id>.json (mkdir -p data/audit/wave3 first). Return all verdicts via StructuredOutput.`
}

phase('Audit')
const res = await parallel(Array.from({ length: N }, (_, k) => () =>
  agent(prompt(k), { label: `w3:${k * PER + 1}-${(k + 1) * PER}`, phase: 'Audit', schema: BATCH })))
const V = res.filter(Boolean).flatMap(r => r.verdicts || [])
const by = f => V.filter(f).length
log(`Wave 3: ${V.length} verdicts`)
return {
  counts: {
    verdicts: V.length, confirmed: by(v => v.verdict === 'confirmed'),
    rejected: by(v => v.verdict === 'rejected'), needs_human: by(v => v.verdict === 'needs_human'),
    critical: by(v => v.verdict === 'confirmed' && v.severity === 'critical'),
    by_dim: ['J1_false_fact', 'J3_biblio', 'J4_misattribution', 'J5_anachronism', 'J2_greek']
      .map(d => `${d}:${by(v => v.verdict === 'confirmed' && v.dimension === d)}`).join(' '),
  },
  index: V.map(v => ({ node_id: v.node_id, dimension: v.dimension, verdict: v.verdict, severity: v.severity, field: v.field })),
}
