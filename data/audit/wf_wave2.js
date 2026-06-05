export const meta = {
  name: 'kg-audit-wave2',
  description: 'Wave 2 semantic integrity: citation-passage support (does cited text back the claim?) + anachronistic-label hedging, adversarially verified',
  phases: [{ title: 'CiteCheck', detail: 'does each claim node\'s cited passage actually support it?' },
           { title: 'Anachronism', detail: 'is each unhedged modern label asserted as ancient fact?' }],
}

const PER = args?.per ?? 6
const N_CM = Math.ceil((args?.n_cm ?? 214) / PER)
const N_AN = Math.ceil((args?.n_an ?? 132) / PER)

const ITEM = {
  type: 'object',
  properties: {
    node_id: { type: 'string' }, dimension: { type: 'string' },
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
const PRE = `cwd=repo root, use python3. FIRST read data/audit/RULES.md (binding). Judge ONLY real data via \`python3 scripts/audit_fetch.py node <id>\`. NEVER compose Greek/Latin. Write each node's verdict to data/audit/wave2/<dimension>__<node_id>.json (mkdir -p data/audit/wave2 first). needs_human over guessing.`

function cmPrompt(k) {
  const s = k * PER + 1, e = (k + 1) * PER
  return `You verify CITATION–CLAIM SUPPORT in a scholarly free-will KG. ${PRE}

Handle node_ids on lines ${s}..${e} of data/audit/wave2_citation_mismatch.txt (\`sed -n '${s},${e}p' data/audit/wave2_citation_mismatch.txt\`). For EACH: run \`python3 scripts/audit_fetch.py node <id>\` → you get the claim (label+description) and every cited passage's ACTUAL text (Greek/Latin/English).

Decide: does the cited primary text actually support the specific claim the node makes?
- rejected: the citation genuinely supports the claim (the normal, healthy case).
- confirmed: MISMATCH — the cited passage does not contain/support what the node asserts (wrong locus, passage about something else, claim overreaches the text, or citation points to a translation/note not the original). Set field='citation', fix_class='scholarly', proposed=null (citation-table fix is manual), and in issue name WHICH citation and WHY it fails. If instead the DESCRIPTION makes a checkably false claim, set field='description' with a surgical current/proposed.
- needs_human: genuinely ambiguous.
Severity: critical if the claim is a fabrication unsupported by ANY cited text; high if a key citation is wrong; medium if overreach. Return all verdicts via StructuredOutput.`
}

function anPrompt(k) {
  const s = k * PER + 1, e = (k + 1) * PER
  return `You audit ANACHRONISTIC MODERN LABELS in a free-will KG. ${PRE}

Handle node_ids on lines ${s}..${e} of data/audit/wave2_anachronism.txt (\`sed -n '${s},${e}p' data/audit/wave2_anachronism.txt\`). Each contains a modern label (compatibilism/incompatibilism/libertarian/determinism/agent-causation). For EACH: \`python3 scripts/audit_fetch.py node <id>\` and read how the label is used.

- rejected: the label is EITHER already hedged, OR the node is modern scholarship (e.g. a 'Bobzien 2001'/'Frede' node) legitimately analyzing ancient determinism, OR it names a school's actual position accurately — NOT an anachronism.
- confirmed: the label is asserted as plain HISTORICAL FACT about an ancient figure with no hedge. field='description', fix_class='scholarly'. proposed = a SURGICAL minimal edit: insert a hedge ("what modern scholars term ", "often characterized as ") right before the label. Give current = the short exact phrase to replace (<=200 chars) and proposed = the hedged phrase. Do NOT rewrite the whole description.
- needs_human if unclear.
Return all verdicts via StructuredOutput.`
}

phase('CiteCheck')
const cm = await parallel(Array.from({ length: N_CM }, (_, k) => () =>
  agent(cmPrompt(k), { label: `cite:${k * PER + 1}-${(k + 1) * PER}`, phase: 'CiteCheck', schema: BATCH })))
const cmV = cm.filter(Boolean).flatMap(r => r.verdicts || [])

phase('Anachronism')
const an = await parallel(Array.from({ length: N_AN }, (_, k) => () =>
  agent(anPrompt(k), { label: `anach:${k * PER + 1}-${(k + 1) * PER}`, phase: 'Anachronism', schema: BATCH })))
const anV = an.filter(Boolean).flatMap(r => r.verdicts || [])

const all = [...cmV, ...anV]
const by = f => all.filter(f).length
log(`Wave 2: ${all.length} verdicts`)
return {
  counts: {
    citation_mismatch: cmV.length, cm_confirmed: cmV.filter(v => v.verdict === 'confirmed').length,
    anachronism: anV.length, an_confirmed: anV.filter(v => v.verdict === 'confirmed').length,
    confirmed: by(v => v.verdict === 'confirmed'), needs_human: by(v => v.verdict === 'needs_human'),
  },
  index: all.map(v => ({ node_id: v.node_id, dimension: v.dimension, verdict: v.verdict, severity: v.severity, field: v.field })),
}
