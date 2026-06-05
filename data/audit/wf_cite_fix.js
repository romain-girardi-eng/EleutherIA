export const meta = {
  name: 'kg-citation-fix',
  description: 'Adversarially re-verify the 53 citation-mismatch findings and decide a concrete, conservative fix (remove / re-point / fix-claim / reject)',
  phases: [{ title: 'ReVerify', detail: 'independent re-check of each claim vs its cited passage text' }],
}
const PER = args?.per ?? 4
const TOTAL = args?.total ?? 53
const N = Math.ceil(TOTAL / PER)

const ITEM = {
  type: 'object',
  properties: {
    node_id: { type: 'string' },
    bad_passage_id: { type: 'string', description: 'the citation whose passage does not support the claim' },
    action: { enum: ['remove', 'repoint', 'fix_description', 'reject'] },
    new_passage_id: { type: ['string', 'null'], description: 'for repoint: a corpus passage that DOES support the claim (verify it exists via audit_fetch corpus)' },
    field: { type: ['string', 'null'] },
    current: { type: ['string', 'null'] },
    proposed: { type: ['string', 'null'] },
    severity: { enum: ['critical', 'high', 'medium', 'low'] },
    confidence: { type: 'number' },
    rationale: { type: 'string' },
    sources: { type: 'array', items: { type: 'string' } },
  },
  required: ['node_id', 'action', 'confidence', 'rationale'],
}
const BATCH = { type: 'object', properties: { decisions: { type: 'array', items: ITEM } }, required: ['decisions'] }

function prompt(k) {
  const s = k * PER + 1, e = (k + 1) * PER
  return `You ADVERSARIALLY re-verify citation–claim mismatches in a free-will KG. A prior single-pass scan flagged these claim nodes as citing a passage that does not support them. Your job: independently re-check and decide a CONSERVATIVE fix. cwd=repo root, use python3. FIRST read data/audit/RULES.md.

Handle node_ids on lines ${s}..${e} of data/audit/cite_reverify_nodes.txt (\`sed -n '${s},${e}p' data/audit/cite_reverify_nodes.txt\`). For EACH:
1. \`python3 scripts/audit_fetch.py node <id>\` → the claim (label+description) and EVERY cited passage's actual text + canonical_ref + cts_urn.
2. Read carefully: does the cited primary text actually support the node's specific claim? (Watch for: wrong locus, passage on another topic, claim overreaching the text, citation to a translation/note not the original, or the prior scan being WRONG.)

Decide ONE action:
- reject: the citation genuinely DOES support the claim — the prior flag was a false positive (be willing to overturn it; many will be).
- remove: a specific citation clearly points to an unsupporting passage and there is no better target — give bad_passage_id.
- repoint: the claim is sound but cited to the wrong passage AND you can identify a corpus passage that genuinely supports it — give bad_passage_id + new_passage_id (VERIFY the new passage exists and supports the claim via \`audit_fetch.py corpus "<distinctive phrase>"\` or by reading it; NEVER invent a passage_id).
- fix_description: the DESCRIPTION makes a claim the sources don't support and the honest fix is to soften/correct the prose — give field='description' + surgical current/proposed (no fabricated text).

Be conservative: when uncertain, prefer 'reject' (leave as-is) over a destructive edit. confidence reflects how sure you are of the ACTION. Write each decision to data/audit/cite_fix/<node_id>.json. Return all via StructuredOutput.`
}

phase('ReVerify')
const res = await parallel(Array.from({ length: N }, (_, k) => () =>
  agent(prompt(k), { label: `cite:${k * PER + 1}-${(k + 1) * PER}`, phase: 'ReVerify', schema: BATCH })))
const D = res.filter(Boolean).flatMap(r => r.decisions || [])
const by = f => D.filter(f).length
log(`citation re-verify: ${D.length} decisions`)
return {
  counts: {
    decisions: D.length,
    reject: by(d => d.action === 'reject'), remove: by(d => d.action === 'remove'),
    repoint: by(d => d.action === 'repoint'), fix_description: by(d => d.action === 'fix_description'),
    high_conf_changes: by(d => d.action !== 'reject' && (d.confidence || 0) >= 0.8),
  },
  index: D.map(d => ({ node_id: d.node_id, action: d.action, confidence: d.confidence, bad: d.bad_passage_id, new: d.new_passage_id })),
}
