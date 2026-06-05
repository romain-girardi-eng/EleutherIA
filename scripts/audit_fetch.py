#!/usr/bin/env python3
"""Evidence fetcher for KG audit agents. Read-only.

Gives an auditor the *real* data behind a node so it never judges from memory:
  node   <id>            -> node + its citations + the cited passages' text
  batch  <id1,id2,...>   -> compact bundle (label/type/period/desc/n_cit) per id
  corpus <substring>     -> passages whose text contains the (Greek/Latin) substring
  list   <type> [k=v...] -> node_ids matching filters (period=, needs_evidence=1, greek=1)
"""
import json, sys, os, re, signal
try:
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)  # quiet `| head` tracebacks
except (AttributeError, ValueError):
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def p(*a): return os.path.join(ROOT, *a)
def loadl(path):
    with open(p(path)) as f:
        for line in f:
            line = line.strip()
            if line: yield json.loads(line)
def jmeta(d):
    m = d.get('metadata')
    if isinstance(m, str):
        try: return json.loads(m)
        except Exception: return {}
    return m if isinstance(m, dict) else {}

GREEK = re.compile(r'[Ͱ-Ͽἀ-῿]')

def _nodes():
    return {(n.get('node_id') or n.get('id')): n for n in loadl('data/kg/nodes.jsonl')}
def _passages():
    return {pp.get('passage_id'): pp for pp in loadl('data/corpus/passages.jsonl')}
def _cits():
    return list(loadl('data/corpus/citations.jsonl'))

def cmd_node(nid):
    nodes = _nodes(); passages = _passages(); cits = _cits()
    n = nodes.get(nid)
    if not n: print(json.dumps({'error': 'node not found', 'id': nid})); return
    m = jmeta(n)
    out = {
        'node_id': nid, 'type': n.get('type'), 'label': n.get('label'),
        'period': n.get('period'), 'school': n.get('school'),
        'alternative_names': n.get('alternative_names'),
        'description': n.get('description'),
        'metadata': {k: m.get(k) for k in (
            'cts_urn','edition','sc_number','wikidata_qid','birth_date','death_date',
            'floruit','translator','translation_source','edition_full','isbn','doi',
            'author','work_title','needs_evidence','source') if k in m},
        'citations': [],
    }
    for c in cits:
        if c.get('kg_node_id') == nid:
            pp = passages.get(c.get('passage_id'))
            out['citations'].append({
                'passage_id': c.get('passage_id'),
                'confidence': c.get('confidence'),
                'citation_type': c.get('citation_type'),
                'canonical_ref': (pp or {}).get('canonical_ref'),
                'cts_urn': (pp or {}).get('cts_urn'),
                'text': ((pp or {}).get('text_content') or '')[:600] if pp else None,
                'passage_exists': pp is not None,
            })
    print(json.dumps(out, ensure_ascii=False, indent=2))

def cmd_batch(idcsv):
    ids = [x for x in re.split(r'[, \n]+', idcsv) if x]
    nodes = _nodes(); cits = _cits()
    ncit = {}
    for c in cits: ncit[c.get('kg_node_id')] = ncit.get(c.get('kg_node_id'), 0) + 1
    for nid in ids:
        n = nodes.get(nid)
        if not n: print(json.dumps({'node_id': nid, 'error': 'not found'})); continue
        desc = n.get('description') or ''
        print(json.dumps({
            'node_id': nid, 'type': n.get('type'), 'label': n.get('label'),
            'period': n.get('period'), 'school': n.get('school'),
            'n_citations': ncit.get(nid, 0), 'has_greek': bool(GREEK.search(desc)),
            'metadata': jmeta(n), 'description': desc,
        }, ensure_ascii=False))

def cmd_corpus(sub):
    sub = sub.strip()
    hits = 0
    for pp in _passages().values():
        if sub and sub in (pp.get('text_content') or ''):
            print(json.dumps({
                'passage_id': pp.get('passage_id'),
                'canonical_ref': pp.get('canonical_ref'),
                'cts_urn': pp.get('cts_urn'),
                'snippet': (pp.get('text_content') or '')[:200],
            }, ensure_ascii=False))
            hits += 1
            if hits >= 20: break
    if hits == 0:
        print(json.dumps({'found': False, 'substring': sub[:80],
                          'note': 'NOT present verbatim in corpus passages'}))

def cmd_list(args):
    typ = args[0] if args else None
    kv = dict(a.split('=', 1) for a in args[1:] if '=' in a)
    cits = _cits()
    ncit = {}
    for c in cits: ncit[c.get('kg_node_id')] = ncit.get(c.get('kg_node_id'), 0) + 1
    for n in _nodes().values():
        if typ and n.get('type') != typ: continue
        m = jmeta(n); desc = n.get('description') or ''
        if 'period' in kv and (n.get('period') or '') != kv['period']: continue
        if kv.get('needs_evidence') == '1' and not m.get('needs_evidence'): continue
        if kv.get('greek') == '1' and not GREEK.search(desc): continue
        print(json.dumps({'node_id': n.get('node_id') or n.get('id'),
                          'label': n.get('label'), 'period': n.get('period'),
                          'n_citations': ncit.get(n.get('node_id') or n.get('id'), 0),
                          'desc_len': len(desc)}, ensure_ascii=False))

def cmd_slice(typ, k, n):
    """Print node_ids for batch k (0-based) of size n, in stable file order."""
    ids = [(x.get('node_id') or x.get('id')) for x in _nodes_ordered() if x.get('type') == typ]
    k, n = int(k), int(n)
    sl = ids[k * n:(k + 1) * n]
    print(','.join(sl))

def _nodes_ordered():
    return list(loadl('data/kg/nodes.jsonl'))

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'node': cmd_node(sys.argv[2])
    elif cmd == 'batch': cmd_batch(' '.join(sys.argv[2:]))
    elif cmd == 'corpus': cmd_corpus(' '.join(sys.argv[2:]))
    elif cmd == 'list': cmd_list(sys.argv[2:])
    elif cmd == 'slice': cmd_slice(sys.argv[2], sys.argv[3], sys.argv[4])
    else: print(__doc__)
