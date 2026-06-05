#!/usr/bin/env python3
"""Apply adversarially-re-verified citation fixes to data/corpus/citations.jsonl.

Conservative + guarded:
- only confidence >= MIN_CONF; action in {remove, repoint}
- 'reject' is a no-op (leave citation as-is)
- 'repoint' requires new_passage_id to EXIST in passages.jsonl (else -> deferred)
- 'fix_description' decisions are routed out to a node-fix file (handled by apply_audit_fixes)
- line-preserving write, backup, changelog, idempotent
Usage: python3 scripts/apply_citation_fixes.py [--min-conf 0.8] [--dry-run]
"""
import json, os, glob, shutil, argparse, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def p(*a): return os.path.join(ROOT, *a)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--min-conf', type=float, default=0.8)
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    decisions = []
    for f in glob.glob(p('data/audit/cite_fix/*.json')):
        try: decisions.append(json.load(open(f)))
        except Exception as e: print("WARN", f, e)
    print(f"decisions: {len(decisions)} | actions:",
          collections.Counter(d.get('action') for d in decisions).most_common())

    pass_ids = {json.loads(l).get('passage_id') for l in open(p('data/corpus/passages.jsonl')) if l.strip()}
    cits = [json.loads(l) for l in open(p('data/corpus/citations.jsonl')) if l.strip()]
    # index citations by (node, passage)
    key = lambda c: (c.get('kg_node_id'), c.get('passage_id'))
    cmap = collections.defaultdict(list)
    for i, c in enumerate(cits): cmap[key(c)].append(i)

    changelog, deferred, desc_fixes = [], [], []
    to_remove, to_repoint = set(), {}
    for d in decisions:
        act = d.get('action'); conf = d.get('confidence') or 0
        nid = d.get('node_id'); bad = d.get('bad_passage_id')
        if act == 'reject': continue
        if conf < a.min_conf:
            deferred.append({**d, '_defer': f'confidence {conf} < {a.min_conf}'}); continue
        if act == 'fix_description':
            desc_fixes.append(d); continue
        if act == 'remove':
            if (nid, bad) in cmap: to_remove.add((nid, bad))
            else: deferred.append({**d, '_defer': 'target citation not found'})
        elif act == 'repoint':
            new = d.get('new_passage_id')
            if not new or new not in pass_ids:
                deferred.append({**d, '_defer': f'new_passage_id missing/not in corpus: {new}'}); continue
            if (nid, bad) in cmap: to_repoint[(nid, bad)] = new
            else: deferred.append({**d, '_defer': 'target citation not found'})

    # compute changelog (no rewrite yet)
    for k in to_remove:
        changelog.append({'op': 'remove', 'kg_node_id': k[0], 'passage_id': k[1]})
    for k, new in to_repoint.items():
        changelog.append({'op': 'repoint', 'kg_node_id': k[0], 'old_passage_id': k[1], 'new_passage_id': new})

    print(f"remove: {len(to_remove)}  repoint: {len(to_repoint)}  "
          f"desc_fixes(routed): {len(desc_fixes)}  deferred: {len(deferred)}")
    if a.dry_run:
        for c in changelog[:12]: print(" ", c)
        return
    os.makedirs(p('data/audit'), exist_ok=True)
    bak = p('data/corpus', 'citations.jsonl.bak-cite_fix')
    if not os.path.exists(bak):
        shutil.copy2(p('data/corpus/citations.jsonl'), bak); print("backup ->", bak)
    DUMP = dict(ensure_ascii=False, separators=(',', ':'), sort_keys=True)
    tmp = p('data/corpus', 'citations.jsonl.tmp')
    with open(p('data/corpus/citations.jsonl')) as src, open(tmp, 'w') as out:
        for line in src:
            if not line.strip():
                out.write(line); continue
            c = json.loads(line); k = (c.get('kg_node_id'), c.get('passage_id'))
            if k in to_remove:
                continue  # drop the unsupporting citation
            if k in to_repoint:
                out.write(json.dumps({**c, 'passage_id': to_repoint[k]}, **DUMP) + '\n')
            else:
                out.write(line if line.endswith('\n') else line + '\n')
    os.replace(tmp, p('data/corpus/citations.jsonl'))
    with open(p('data/audit/cite_fix_changelog.jsonl'), 'w') as f:
        for c in changelog: f.write(json.dumps(c, ensure_ascii=False) + '\n')
    with open(p('data/audit/cite_fix_deferred.jsonl'), 'w') as f:
        for d in deferred: f.write(json.dumps(d, ensure_ascii=False) + '\n')
    # route description fixes into a verdict dir for apply_audit_fixes.py --wave cite_descfix
    os.makedirs(p('data/audit/cite_descfix'), exist_ok=True)
    for d in desc_fixes:
        v = {'node_id': d['node_id'], 'dimension': 'citation_descfix', 'verdict': 'confirmed',
             'severity': d.get('severity', 'medium'), 'field': d.get('field') or 'description',
             'current': d.get('current'), 'proposed': d.get('proposed'),
             'fix_class': 'scholarly', 'final_confidence': d.get('confidence')}
        json.dump(v, open(p('data/audit/cite_descfix', d['node_id'] + '.json'), 'w'), ensure_ascii=False)
    print(f"applied {len(changelog)} citation changes; routed {len(desc_fixes)} description fixes "
          f"(run: python3 scripts/apply_audit_fixes.py --wave cite_descfix)")

if __name__ == '__main__':
    main()
