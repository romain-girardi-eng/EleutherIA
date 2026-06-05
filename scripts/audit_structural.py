#!/usr/bin/env python3
"""Deterministic structural/mechanical audit of the local KG mirror.

Read-only. Computes every defect that does NOT require a value judgement
(FK integrity, ontology vocabulary, source/target type constraints, inverse
coverage, duplicate candidates, polytonic sigma errors, CTS-URN format,
isolated/uncited claim nodes). Writes findings + strata for the LLM workflow.
"""
import json, re, collections, os, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def p(*a): return os.path.join(ROOT, *a)

def load_jsonl(path):
    out = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out

def jmeta(d):
    m = d.get('metadata')
    if isinstance(m, str):
        try: return json.loads(m)
        except Exception: return {}
    return m if isinstance(m, dict) else {}

nodes = load_jsonl(p('data/kg/nodes.jsonl'))
edges = load_jsonl(p('data/kg/edges.jsonl'))
cits  = load_jsonl(p('data/corpus/citations.jsonl'))
passages = load_jsonl(p('data/corpus/passages.jsonl'))
ET = json.load(open(p('knowledge graph/ontology/edge_types.json')))['edge_types']

node_by_id = {}
for n in nodes:
    nid = n.get('node_id') or n.get('id')
    node_by_id[nid] = n
node_type = {nid: n.get('type') for nid, n in node_by_id.items()}
pass_ids = {pp.get('passage_id') for pp in passages}

findings = []
def add(dim, severity, fix_class, ref_kind, ref, issue, evidence='', proposed=None):
    findings.append({
        'dim': dim, 'severity': severity, 'fix_class': fix_class,
        'ref_kind': ref_kind, 'ref': ref, 'issue': issue,
        'evidence': (evidence or '')[:300], 'proposed': proposed,
    })

# 1. FK / dangling -----------------------------------------------------------
for c in cits:
    if c.get('kg_node_id') not in node_by_id:
        add('fk_orphan_citation', 'high', 'mechanical', 'citation',
            f"{c.get('kg_node_id')}::{c.get('passage_id')}",
            'citation.kg_node_id not in nodes', proposed='delete_citation')
    if c.get('passage_id') not in pass_ids:
        add('fk_orphan_citation', 'high', 'mechanical', 'citation',
            f"{c.get('kg_node_id')}::{c.get('passage_id')}",
            'citation.passage_id not in passages', proposed='delete_citation')

for e in edges:
    s = e.get('source') or e.get('source_id'); t = e.get('target') or e.get('target_id')
    if s not in node_by_id:
        add('dangling_edge', 'high', 'mechanical', 'edge', e.get('edge_id'),
            f'edge.source {s} not a node', proposed='delete_edge')
    if t not in node_by_id:
        add('dangling_edge', 'high', 'mechanical', 'edge', e.get('edge_id'),
            f'edge.target {t} not a node', proposed='delete_edge')

# 2. Ontology vocabulary + source/target type constraints --------------------
edge_pairs = set()  # (source, relation, target) for inverse check
for e in edges:
    rel = e.get('relation'); s = e.get('source') or e.get('source_id'); t = e.get('target') or e.get('target_id')
    edge_pairs.add((s, rel, t))
    spec = ET.get(rel)
    if spec is None:
        add('off_ontology_relation', 'high', 'mechanical', 'edge', e.get('edge_id'),
            f'relation `{rel}` not in edge_types.json', proposed='remap_or_delete')
        continue
    st, tt = node_type.get(s), node_type.get(t)
    if st and spec.get('source_types') and st not in spec['source_types']:
        add('edge_type_violation', 'high', 'mechanical', 'edge', e.get('edge_id'),
            f'`{rel}` source type {st} not in {spec["source_types"]}',
            evidence=f'{s} -> {t}', proposed='fix_or_delete')
    if tt and spec.get('target_types') and tt not in spec['target_types']:
        add('edge_type_violation', 'high', 'mechanical', 'edge', e.get('edge_id'),
            f'`{rel}` target type {tt} not in {spec["target_types"]}',
            evidence=f'{s} -> {t}', proposed='fix_or_delete')

# 3. Inverse coverage (only flag if inverses are generally materialized) ------
inv_total = inv_missing = 0
inv_missing_sample = []
for e in edges:
    rel = e.get('relation'); spec = ET.get(rel)
    if not spec: continue
    inv = spec.get('inverse')
    if not inv or inv == rel: continue
    s = e.get('source') or e.get('source_id'); t = e.get('target') or e.get('target_id')
    inv_total += 1
    if (t, inv, s) not in edge_pairs:
        inv_missing += 1
        if len(inv_missing_sample) < 5:
            inv_missing_sample.append((s, rel, t, inv))
inv_ratio = (inv_missing / inv_total) if inv_total else 0

# 4. Duplicate node candidates (same type + normalized label) ----------------
def norm(s):
    s = unicodedata.normalize('NFKD', (s or '')).encode('ascii','ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+',' ', s).strip()
by_key = collections.defaultdict(list)
for n in nodes:
    if n.get('type') == 'passage': continue
    by_key[(n.get('type'), norm(n.get('label')))].append(n.get('node_id') or n.get('id'))
for (typ, key), ids in by_key.items():
    if key and len(ids) > 1:
        add('duplicate_node_candidate', 'medium', 'scholarly', 'node', ids[0],
            f'{len(ids)} {typ} nodes share normalized label "{key}"',
            evidence=','.join(ids[:6]), proposed='confirm_merge')

# 5. Polytonic sigma errors (high precision) ---------------------------------
GREEK = re.compile(r'[Ͱ-Ͽἀ-῿]')
# medial final-sigma: ς immediately followed by a Greek letter
MEDIAL_FINAL = re.compile(r'ς(?=[Ͱ-Ͽἀ-῿])')
# final medial-sigma: σ at end of a Greek word (followed by non-letter / end)
FINAL_MEDIAL = re.compile(r'σ(?![Ͱ-Ͽἀ-῿̀-ͯ])')
def sigma_issues(text):
    iss = []
    if MEDIAL_FINAL.search(text): iss.append('final_sigma_midword')
    if FINAL_MEDIAL.search(text): iss.append('medial_sigma_wordend')
    return iss
for n in nodes:
    if n.get('type') == 'passage': continue
    desc = n.get('description') or ''
    if GREEK.search(desc):
        iss = sigma_issues(desc)
        for i in iss:
            add('polytonic_sigma', 'medium', 'mechanical', 'node', n.get('node_id') or n.get('id'),
                i, evidence=desc[:160], proposed='fix_sigma')

# 6. CTS-URN format ----------------------------------------------------------
CTS = re.compile(r'^urn:cts:[a-zA-Z]+Lit:[a-z]+\d+(\.[a-z]+\d+)*(\.[A-Za-z0-9_-]+)?(:[\w\.\-]+)?$')
for n in nodes:
    m = jmeta(n)
    urn = m.get('cts_urn')
    if urn and not CTS.match(urn):
        add('cts_urn_format', 'low', 'mechanical', 'node', n.get('node_id') or n.get('id'),
            'malformed CTS URN', evidence=urn, proposed='fix_urn')

# 7. Isolated / uncited claim-bearing nodes ----------------------------------
CLAIM_TYPES = {'argument','concept','position','doctrine','debate','controversy',
               'synthesis','argument_reconstruction','conceptual_evolution','controversy'}
deg = collections.Counter()
for e in edges:
    s = e.get('source') or e.get('source_id'); t = e.get('target') or e.get('target_id')
    deg[s]+=1; deg[t]+=1
cited_nodes = {c.get('kg_node_id') for c in cits}
for n in nodes:
    nid = n.get('node_id') or n.get('id'); typ = n.get('type')
    if typ in CLAIM_TYPES:
        m = jmeta(n)
        if deg[nid] == 0:
            add('isolated_claim_node', 'medium', 'scholarly', 'node', nid,
                f'{typ} node has 0 edges', evidence=(n.get('label') or '')[:120])
        if typ in {'argument','synthesis'} and nid not in cited_nodes and not m.get('needs_evidence'):
            add('uncited_claim_node', 'medium', 'scholarly', 'node', nid,
                f'{typ} node has no passage citation and not flagged needs_evidence',
                evidence=(n.get('label') or '')[:120])

# ---- strata for the LLM workflow (description-bearing scholarly nodes) ------
DESC_TYPES = {'argument','person','publication','work','concept','synthesis',
              'debate','school','position','doctrine','controversy','source_collection',
              'event','conceptual_evolution','modern_interpretation','quote','group',
              'argument_framework'}
strata = []
for n in nodes:
    if n.get('type') not in DESC_TYPES: continue
    nid = n.get('node_id') or n.get('id')
    m = jmeta(n)
    desc = n.get('description') or ''
    strata.append({
        'node_id': nid, 'type': n.get('type'), 'label': n.get('label'),
        'period': n.get('period'), 'school': n.get('school'),
        'desc_len': len(desc), 'degree': deg[nid],
        'n_citations': sum(1 for c in cits if c.get('kg_node_id')==nid),
        'has_greek': bool(GREEK.search(desc)),
        'needs_evidence': bool(m.get('needs_evidence')),
    })
os.makedirs(p('data/audit'), exist_ok=True)
with open(p('data/audit/strata.jsonl'),'w') as f:
    for s in strata: f.write(json.dumps(s, ensure_ascii=False)+'\n')
with open(p('data/audit/mechanical_findings.jsonl'),'w') as f:
    for x in findings: f.write(json.dumps(x, ensure_ascii=False)+'\n')

# ---- summary ---------------------------------------------------------------
by_dim = collections.Counter(x['dim'] for x in findings)
print("=== MECHANICAL FINDINGS ===")
for d,c in by_dim.most_common(): print(f"  {d}: {c}")
print(f"  TOTAL: {len(findings)}")
print(f"\ninverse coverage: {inv_missing}/{inv_total} missing ({inv_ratio:.1%}) "
      f"-> {'inverses NOT stored as edges (computed) — not a defect' if inv_ratio>0.6 else 'partial materialization — real gaps'}")
if inv_missing_sample: print("  sample:", inv_missing_sample[:3])
print(f"\nstrata (description-bearing scholarly nodes): {len(strata)}")
st_by_type = collections.Counter(s['type'] for s in strata)
print("  by type:", dict(st_by_type.most_common()))
greek_nodes = sum(1 for s in strata if s['has_greek'])
print(f"  with embedded Greek in description: {greek_nodes}")
print(f"  flagged needs_evidence: {sum(1 for s in strata if s['needs_evidence'])}")
