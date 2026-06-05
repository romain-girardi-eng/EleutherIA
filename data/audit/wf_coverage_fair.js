export const meta = {
  name: 'kg-coverage-fair',
  description: 'Coverage-gap analysis vs canonical free-will scholarship + FAIR/state-of-the-art KG benchmark (diagnostic recommendations)',
  phases: [{ title: 'Coverage', detail: 'missing persons/works/arguments by sub-domain vs Bobzien/Frede/Sorabji' },
           { title: 'FAIR', detail: 'best-practice audit: linked-data, provenance, SKOS/CIDOC, persistent IDs' }],
}

const GAP = {
  type: 'object',
  properties: {
    subdomain: { type: 'string' },
    missing: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          kind: { enum: ['person', 'work', 'argument', 'debate', 'concept'] },
          name: { type: 'string' },
          why_canonical: { type: 'string', description: 'why this is a notable gap for the free-will/fate/moral-responsibility debate' },
          source: { type: 'string', description: 'scholarly source attesting its importance' },
          priority: { enum: ['high', 'medium', 'low'] },
        },
        required: ['kind', 'name', 'why_canonical', 'priority'],
      },
    },
  },
  required: ['subdomain', 'missing'],
}
const FAIROUT = {
  type: 'object',
  properties: {
    recommendations: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          area: { type: 'string', description: 'e.g. Wikidata linking, PROV-O provenance, SKOS, persistent IDs, SHACL coverage' },
          finding: { type: 'string' }, recommendation: { type: 'string' },
          effort: { enum: ['low', 'medium', 'high'] }, impact: { enum: ['high', 'medium', 'low'] },
        },
        required: ['area', 'finding', 'recommendation', 'impact'],
      },
    },
  },
  required: ['recommendations'],
}

const SUBS = [
  { key: 'presocratic_classical', desc: 'Presocratics + Plato + Aristotle on voluntary action, eph\' hemin, prohairesis, the sea-battle' },
  { key: 'hellenistic_stoic_epicurean', desc: 'Stoics (Zeno→Chrysippus→Posidonius), Epicurus/swerve, Academic skeptics (Carneades), the lazy argument, confatalia' },
  { key: 'peripatetic_imperial', desc: 'Alexander of Aphrodisias, Middle Platonists, Plotinus/Neoplatonists, Cicero, the De Fato tradition' },
  { key: 'patristic_christian', desc: 'Greek + Latin Fathers on autexousion/liberum arbitrium: Justin, Origen, Gregory of Nyssa, Augustine, Maximus, anti-astrology/anti-fatalism' },
  { key: 'late_antique_boethius', desc: 'Boethius, Proclus, Nemesius, foreknowledge/eternity, late-antique fate debates' },
  { key: 'modern_reception', desc: 'Modern scholars of ancient free will: Bobzien, Frede, Sorabji, Sharples, Dihle, Long, Salles, Destrée, Fürst' },
]

phase('Coverage')
const PRE = `cwd=repo root, use python3. The KG documents ancient debates on free will / fate / moral responsibility + modern reception. To see what's ALREADY present, use \`python3 scripts/audit_fetch.py list person\` / \`list work\` / \`list argument\` / \`list concept\` (each prints node_id+label). Use WebSearch/WebFetch against canonical scholarship to find what's MISSING. Ground every gap in a real scholarly source; do not pad with trivia.`
const gaps = await parallel(SUBS.map(s => () =>
  agent(`${PRE}\n\nSub-domain: **${s.desc}**. List the genuinely NOTABLE persons, works, arguments, debates, or concepts that a top-tier scholarly KG of this debate should contain but that are ABSENT or thin here. Cross-check the existing node lists first (don't report things already present). Prioritize by importance to the free-will/fate/moral-responsibility question specifically. Return via StructuredOutput.`,
    { label: `cov:${s.key}`, phase: 'Coverage', schema: GAP })))

phase('FAIR')
const fair = await parallel([
  `${PRE}\n\nAudit this KG against FAIR + linked-data best practice. Known baseline (data/audit/fair_baseline.json): persons with Wikidata QID 8% (and ~38% of those were wrong, now fixed); works with CTS URN 12%; arguments passage-grounded only ~8% (rest carry needs_evidence). Assess: Wikidata/VIAF linking coverage, persistent identifiers (CTS URN, DOI), and external-vocabulary alignment. Give concrete, prioritized recommendations (area/finding/recommendation/effort/impact). Return via StructuredOutput.`,
  `${PRE}\n\nAudit this KG against semantic-web / scholarly-KG state of the art: PROV-O provenance on claim nodes, SKOS concept-scheme rigor for concepts/terms, CIDOC-CRM event modelling, and SHACL validation coverage. The repo already has an RDF/SHACL semantic layer (knowledge graph/src/eleutheria_kg/semantic/). Identify gaps vs best practice and give concrete prioritized recommendations. Return via StructuredOutput.`,
].map((pr, i) => () => agent(pr, { label: `fair:${i}`, phase: 'FAIR', schema: FAIROUT })))

const G = gaps.filter(Boolean)
const F = fair.filter(Boolean)
return {
  coverage_gaps: G.flatMap(g => (g.missing || []).map(m => ({ subdomain: g.subdomain, ...m }))),
  fair_recommendations: F.flatMap(f => f.recommendations || []),
  counts: {
    total_gaps: G.reduce((a, g) => a + (g.missing || []).length, 0),
    high_priority_gaps: G.reduce((a, g) => a + (g.missing || []).filter(m => m.priority === 'high').length, 0),
    fair_recs: F.reduce((a, f) => a + (f.recommendations || []).length, 0),
  },
}
