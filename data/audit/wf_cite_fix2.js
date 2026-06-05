export const meta = {
  name: 'kg-citation-fix-2',
  description: 'Re-run citation-mismatch re-verification for the 40 nodes the first pass missed (StructuredOutput-only, robust)',
  phases: [{ title: 'ReVerify', detail: 'independent re-check; decision is the StructuredOutput' }],
}
const PER = args?.per ?? 3
const TOTAL = args?.total ?? 40
const N = Math.ceil(TOTAL / PER)

const ITEM = {
  type: 'object',
  properties: {
    node_id: { type: 'string' },
    bad_passage_id: { type: ['string', 'null'] },
    action: { enum: ['remove', 'repoint', 'fix_description', 'reject'] },
    new_passage_id: { type: ['string', 'null'] },
    field: { type: ['string', 'null'] },
    current: { type: ['string', 'null'] },
    proposed: { type: ['string', 'null'] },
    severity: { enum: ['critical', 'high', 'medium', 'low'] },
    confidence: { type: 'number' },
    rationale: { type: 'string' },
  },
  required: ['node_id', 'action', 'confidence'],
}
const BATCH = { type: 'object', properties: { decisions: { type: 'array', items: ITEM } }, required: ['decisions'] }

function prompt(k) {
  const s = k * PER + 1, e = (k + 1) * PER
  return `You ADVERSARIALLY re-verify citation–claim mismatches in a free-will KG. A prior single-pass scan flagged these claim nodes as citing a passage that may not support them. cwd=repo root, use python3. Read data/audit/RULES.md.

Node_ids on lines ${s}..${e} of data/audit/cite_reverify_missing.txt (\`sed -n '${s},${e}p' data/audit/cite_reverify_missing.txt\`). For EACH: \`python3 scripts/audit_fetch.py node <id>\` and read the claim vs every cited passage's actual text.

For EACH citation that looks wrong, decide an action (a node may need several decisions):
- reject: the citation genuinely supports the claim (false-positive flag — be willing to overturn; many are).
- remove: a citation points to an unsupporting passage with no better target (give bad_passage_id).
- repoint: claim is sound but mis-cited AND you found a corpus passage that supports it (give bad_passage_id + new_passage_id; VERIFY the new passage exists/supports via \`audit_fetch.py corpus\` — NEVER invent an id).
- fix_description: the description overreaches the sources; give field='description' + surgical current/proposed (no fabricated text).
Be conservative — prefer 'reject' when unsure.

OUTPUT CONTRACT: Your ONLY deliverable is the StructuredOutput tool call with a 'decisions' array (one entry per (node, citation) decision). Do NOT write any files. Do NOT end your turn until you have called StructuredOutput. Call it exactly once at the end.`
}

phase('ReVerify')
const res = await parallel(Array.from({ length: N }, (_, k) => () =>
  agent(prompt(k), { label: `cite2:${k * PER + 1}-${(k + 1) * PER}`, phase: 'ReVerify', schema: BATCH })))
const D = res.filter(Boolean).flatMap(r => r.decisions || [])
log(`citation re-verify v2: ${D.length} decisions from ${res.filter(Boolean).length}/${N} batches`)
return { decisions: D }
