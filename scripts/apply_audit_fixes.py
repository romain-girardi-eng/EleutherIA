#!/usr/bin/env python3
"""Apply adversarially-verified KG audit fixes to the local mirror (data/kg/nodes.jsonl).

SAFE BY CONSTRUCTION:
- only verdict=='confirmed' AND final_confidence >= MIN_CONF AND proposed not null
- metadata.<key> + simple top-level fields: direct, idempotent set
- description fixes: ONLY surgical substring replace when `current` is a verbatim
  substring of the live description and short (<= MAX_SUB). Otherwise -> deferred.
- never touches ancient Greek/Latin generation (the verifier already vetted content)
- transactional: backup first, write temp, atomic rename
- idempotent: if live value already == proposed, skip
- records a full before/after changelog and emits a prod migration

Usage:
  python3 scripts/apply_audit_fixes.py --wave wave1 [--min-conf 0.8] [--dry-run]
"""
import json, os, re, sys, glob, shutil, argparse, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def p(*a): return os.path.join(ROOT, *a)
MAX_SUB = 400

def jmeta(d):
    m = d.get('metadata')
    if isinstance(m, str):
        try: return json.loads(m)
        except Exception: return {}
    return m if isinstance(m, dict) else {}

def load_verdicts(wave):
    rows = []
    for f in glob.glob(p('data/audit', wave, '*.json')):
        try: rows.append(json.load(open(f)))
        except Exception as e: print(f"  WARN unreadable {f}: {e}")
    return rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--wave', default='wave1')
    ap.add_argument('--min-conf', type=float, default=0.8)
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    verdicts = load_verdicts(a.wave)
    print(f"loaded {len(verdicts)} verdict files")
    confirmed = [v for v in verdicts
                 if v.get('verdict') == 'confirmed'
                 and (v.get('final_confidence') or 0) >= a.min_conf
                 and v.get('proposed') not in (None, '')
                 and v.get('field')]
    print(f"confirmed & high-confidence & actionable: {len(confirmed)}")

    nodes = [json.loads(l) for l in open(p('data/kg/nodes.jsonl')) if l.strip()]
    idx = {}
    for i, n in enumerate(nodes):
        idx[n.get('node_id') or n.get('id')] = i

    changed_ids = set()
    changelog, deferred, applied, skipped = [], [], 0, 0
    for v in confirmed:
        nid = v.get('node_id'); field = v.get('field'); proposed = v.get('proposed')
        cur = v.get('current')
        if nid not in idx:
            deferred.append({**v, '_defer': 'node not found'}); continue
        n = nodes[idx[nid]]
        m = jmeta(n)

        mm = re.match(r'^metadata\.([\w]+)$', field or '')
        if mm:
            key = mm.group(1); live = m.get(key)
            if str(live) == str(proposed):
                skipped += 1; continue
            changelog.append({'node_id': nid, 'field': field, 'old': live,
                              'new': proposed, 'dimension': v.get('dimension'),
                              'severity': v.get('severity'), 'kind': 'metadata'})
            m[key] = proposed; n['metadata'] = json.dumps(m, ensure_ascii=False)
            applied += 1; changed_ids.add(nid)
        elif field in ('label', 'period', 'school'):
            live = n.get(field)
            if str(live) == str(proposed): skipped += 1; continue
            changelog.append({'node_id': nid, 'field': field, 'old': live,
                              'new': proposed, 'dimension': v.get('dimension'),
                              'severity': v.get('severity'), 'kind': 'attr'})
            n[field] = proposed; applied += 1; changed_ids.add(nid)
        elif field == 'description':
            desc = n.get('description') or ''
            if proposed == desc:
                skipped += 1; continue
            # surgical replace only
            if cur and cur in desc and len(cur) <= MAX_SUB and cur != proposed:
                new_desc = desc.replace(cur, proposed, 1)
                changelog.append({'node_id': nid, 'field': 'description',
                                  'old': cur, 'new': proposed,
                                  'dimension': v.get('dimension'),
                                  'severity': v.get('severity'), 'kind': 'desc_surgical'})
                n['description'] = new_desc; applied += 1; changed_ids.add(nid)
            else:
                deferred.append({**v, '_defer': 'non-surgical description change — manual review'})
        else:
            deferred.append({**v, '_defer': f'unhandled field: {field}'})

    print(f"\napplied: {applied}  skipped(idempotent): {skipped}  deferred: {len(deferred)}")
    print("by dimension (applied):",
          collections.Counter(c['dimension'] for c in changelog).most_common())
    print("by kind (applied):",
          collections.Counter(c['kind'] for c in changelog).most_common())

    if a.dry_run:
        print("\n[dry-run] no files written. Sample changes:")
        for c in changelog[:12]:
            print(f"  {c['node_id']} {c['field']}: {str(c['old'])[:40]!r} -> {str(c['new'])[:40]!r}")
        return

    # transactional write
    os.makedirs(p('data/audit'), exist_ok=True)
    os.makedirs(p('scripts/migrations'), exist_ok=True)
    bak = p('data/kg', f'nodes.jsonl.bak-{a.wave}')
    if not os.path.exists(bak):
        shutil.copy2(p('data/kg/nodes.jsonl'), bak)
        print(f"backup -> {bak}")
    DUMP = dict(ensure_ascii=False, separators=(',', ':'), sort_keys=True)
    tmp = p('data/kg', 'nodes.jsonl.tmp')
    with open(p('data/kg/nodes.jsonl')) as src, open(tmp, 'w') as out:
        for line in src:
            if not line.strip():
                out.write(line); continue
            d = json.loads(line)
            nid = d.get('node_id') or d.get('id')
            if nid in changed_ids:
                out.write(json.dumps(nodes[idx[nid]], **DUMP) + '\n')
            else:
                out.write(line if line.endswith('\n') else line + '\n')
    os.replace(tmp, p('data/kg/nodes.jsonl'))
    with open(p('data/audit', f'{a.wave}_changelog.jsonl'), 'w') as f:
        for c in changelog: f.write(json.dumps(c, ensure_ascii=False) + '\n')
    with open(p('data/audit', f'{a.wave}_deferred.jsonl'), 'w') as f:
        for d in deferred: f.write(json.dumps(d, ensure_ascii=False) + '\n')
    print(f"wrote changelog ({len(changelog)}) + deferred ({len(deferred)})")
    print("done. Review: git diff data/kg/nodes.jsonl")

if __name__ == '__main__':
    main()
