#!/usr/bin/env python3
"""Deterministic fabrication pre-filter for embedded ancient Greek.

For every non-passage node whose description contains Greek, extract contiguous
Greek runs and test whether each appears (accent/sigma/punct-insensitive) in the
corpus passages. Unmatched runs are *fabrication candidates* for LLM review.
Read-only. Writes data/audit/greek_unmatched.jsonl + summary.
"""
import json, re, os, unicodedata, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def p(*a): return os.path.join(ROOT, *a)
def loadl(path):
    with open(p(path)) as f:
        for line in f:
            line = line.strip()
            if line: yield json.loads(line)

GREEK_CH = r'Ͱ-Ͽἀ-῿̀-ͯ'
# a "run" = Greek words (with combining marks/punct) spanning >= MIN_CHARS
RUN = re.compile(rf'[{GREEK_CH}][{GREEK_CH}\s\.,··;:’\'··\-—]+')
MIN_CHARS = 18

def strip(s):
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))  # drop accents
    s = s.lower().replace('ς', 'σ')
    s = re.sub(r'[^Ͱ-Ͽ]+', ' ', s)  # keep base Greek letters only
    return re.sub(r'\s+', ' ', s).strip()

# build normalized corpus blob
print("building normalized corpus blob...", flush=True)
corpus = []
for pp in loadl('data/corpus/passages.jsonl'):
    t = pp.get('text_content') or ''
    if re.search(rf'[{GREEK_CH}]', t):
        corpus.append(strip(t))
blob = ' ␟ '.join(corpus)
print(f"corpus greek passages: {len(corpus)}, blob chars: {len(blob)}", flush=True)

def extract_runs(desc):
    runs = []
    for m in RUN.finditer(desc):
        seg = m.group(0).strip(' .,··;:’\'·-—\n')
        if len(seg) >= MIN_CHARS:
            runs.append(seg)
    return runs

out = []
tot_nodes = tot_runs = tot_unmatched = 0
nodes_with_unmatched = 0
for n in loadl('data/kg/nodes.jsonl'):
    if n.get('type') == 'passage': continue
    desc = n.get('description') or ''
    if not re.search(rf'[{GREEK_CH}]', desc): continue
    runs = extract_runs(desc)
    if not runs: continue
    tot_nodes += 1; tot_runs += len(runs)
    unmatched = []
    for r in runs:
        nr = strip(r)
        if len(nr) < 12:  # too short after normalization
            continue
        # match if normalized run is substring of corpus blob
        if nr not in blob:
            # also try first 8 words (descriptions sometimes truncate/elide)
            head = ' '.join(nr.split()[:8])
            if len(head) < 12 or head not in blob:
                unmatched.append(r[:200])
    tot_unmatched += len(unmatched)
    if unmatched:
        nodes_with_unmatched += 1
        out.append({
            'node_id': n.get('node_id') or n.get('id'),
            'type': n.get('type'), 'label': n.get('label'),
            'period': n.get('period'),
            'n_runs': len(runs), 'n_unmatched': len(unmatched),
            'unmatched_runs': unmatched,
        })

os.makedirs(p('data/audit'), exist_ok=True)
out.sort(key=lambda x: -x['n_unmatched'])
with open(p('data/audit/greek_unmatched.jsonl'), 'w') as f:
    for x in out: f.write(json.dumps(x, ensure_ascii=False) + '\n')

print(f"\nnodes with embedded Greek runs: {tot_nodes}")
print(f"total Greek runs: {tot_runs}")
print(f"unmatched runs (fabrication candidates): {tot_unmatched}")
print(f"nodes with >=1 unmatched run: {nodes_with_unmatched}")
print(f"by type:", collections.Counter(x['type'] for x in out).most_common())
print("\ntop offenders:")
for x in out[:8]:
    print(f"  {x['n_unmatched']}/{x['n_runs']} unmatched | {x['type']} | {x['label']}")
