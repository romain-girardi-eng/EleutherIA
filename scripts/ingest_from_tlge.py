#!/usr/bin/env python3
"""Ingest a work from the local TLG E disk into the corpus mirror.

Decodes TLG<author>.TXT with `tlgu` (citation-aware beta-code converter),
segments the requested work at its natural citation level (the second-to-last
citation field: CAG/Bruns page, SC section, ...), and stages corpus-mirror
passage records. Text is byte-faithful to the TLG digitization of the printed
critical edition; editorial angle brackets are normalized to ⟨ ⟩.

Staging only by default — review the staged passages.jsonl, then re-run with
--apply to append to data/corpus/passages.jsonl + manifest.

Usage:
  python3 scripts/ingest_from_tlge.py --author 4089 --work 001 \
      --wcid urn_cts_greeklit_tlg4089_tlg001_grc --refprefix "Curatio" \
      --title "Graecarum affectionum curatio" --person "Theodoret" \
      --period "Late Antiquity" --edition "Canivet, SC 57, 1958" [--apply]

Requires: tlgu binary (env TLGU_BIN, default /tmp/tlgu; source:
github.com/cltk/grc_software_tlgu, build: cc -O2 -o tlgu tlgu.c).
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TLGE = os.environ.get('TLGE_DIR', '[local-path]')
TLGU = os.environ.get('TLGU_BIN', '/tmp/tlgu')
GREEK = re.compile(r'[Ͱ-Ͽἀ-῿]')
ARTIFACT = re.compile(r'[<>{}@$%#*]|\d{4,}')


def decode_work(author: str, work: str) -> str:
    src = os.path.join(TLGE, f'TLG{author}.TXT')
    if not os.path.exists(src):
        sys.exit(f'not found: {src}')
    if not os.path.exists(TLGU):
        sys.exit(f'tlgu binary not found at {TLGU} (set TLGU_BIN)')
    tmp = tempfile.mkdtemp(prefix='tlge_')
    out = os.path.join(tmp, f'tlg{author}')
    subprocess.run([TLGU, '-W', '-v', '-w', '-x', '-y', '-z', src, out],
                   check=True, capture_output=True)
    path = f'{out}-{work}.txt'
    if not os.path.exists(path):
        sys.exit(f'work {work} not produced — available: '
                 f'{sorted(os.listdir(tmp))}')
    return path


def join_lines(lines):
    out = ''
    for l in lines:
        l = re.sub(r'[{}]', '', l.strip())
        if out.endswith('-'):
            out = out[:-1] + l
        else:
            out = (out + ' ' + l).strip()
    out = out.replace('<', '⟨').replace('>', '⟩')
    return re.sub(r'\s+', ' ', out).strip()


def segment(path: str):
    """Group decoded lines by the second-to-last citation field (unit)."""
    sections, order = {}, []
    for line in open(path):
        m = re.match(r'^([^\t]*)\t(.*)$', line.rstrip('\n'))
        if not m:
            continue
        cit, txt = m.groups()
        parts = cit.split('.')
        if len(parts) < 2:
            continue
        unit = '.'.join(p for p in parts[:-1] if p)  # drop line level
        if not unit or unit.endswith('t') or parts[-2] == 't':
            continue  # running titles
        if unit not in sections:
            sections[unit] = []
            order.append(unit)
        sections[unit].append(txt)
    return [(u, join_lines(sections[u])) for u in order]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--author', required=True, help='TLG author number, e.g. 4016')
    ap.add_argument('--work', required=True, help='work number, e.g. 003')
    ap.add_argument('--wcid', required=True, help='work_canonical_id for corpus records')
    ap.add_argument('--refprefix', required=True, help='canonical_ref prefix, e.g. "In De Int."')
    ap.add_argument('--title', required=True)
    ap.add_argument('--person', required=True, help='author display name for manifest')
    ap.add_argument('--period', required=True)
    ap.add_argument('--edition', required=True, help='edition statement (from TLG canon)')
    ap.add_argument('--min-chars', type=int, default=25)
    ap.add_argument('--apply', action='store_true')
    args = ap.parse_args()

    urn_base = f'urn:cts:greekLit:tlg{args.author}.tlg{args.work}'
    path = decode_work(args.author, args.work)
    rows, skipped = [], 0
    for unit, txt in segment(path):
        if len(txt) < args.min_chars or not GREEK.search(txt):
            skipped += 1
            continue
        rows.append({
            'passage_id': str(uuid.uuid4()),
            'canonical_ref': f'{args.refprefix} {unit}',
            'cts_urn': f'{urn_base}:{unit}',
            'sequence_number': len(rows) + 1,
            'text_content': txt,
            'work_canonical_id': args.wcid,
        })
    bad = sum(1 for r in rows if ARTIFACT.search(r['text_content']))
    lens = sorted(len(r['text_content']) for r in rows) or [0]
    print(f'{args.wcid}: {len(rows)} passages (skipped {skipped} short/non-Greek), '
          f'artifact-flagged {bad}, len med {lens[len(lens)//2]}')

    stage = os.path.join(ROOT, 'data', 'audit', 'primary_fetch',
                         f'ingest_tlge_{args.author}_{args.work}')
    os.makedirs(stage, exist_ok=True)
    with open(os.path.join(stage, 'passages.jsonl'), 'w') as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    json.dump({'wcid': args.wcid, 'urn': urn_base, 'n_passages': len(rows),
               'edition_statement': args.edition,
               'source': f'local TLG E disk TLG{args.author}.TXT work {args.work}'},
              open(os.path.join(stage, 'verdict.json'), 'w'),
              ensure_ascii=False, indent=1)
    print(f'staged: {stage}/passages.jsonl')

    if not args.apply:
        return
    pids = {json.loads(l)['passage_id']
            for l in open(os.path.join(ROOT, 'data/corpus/passages.jsonl'))}
    wcids = {json.loads(l).get('work_canonical_id')
             for l in open(os.path.join(ROOT, 'data/corpus/passages.jsonl'))}
    if args.wcid in wcids:
        sys.exit(f'ABORT: work_canonical_id {args.wcid} already in corpus')
    assert not any(r['passage_id'] in pids for r in rows)
    with open(os.path.join(ROOT, 'data/corpus/passages.jsonl'), 'a') as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    with open(os.path.join(ROOT, 'data/corpus/manifest.jsonl'), 'a') as f:
        f.write(json.dumps({'author': args.person, 'canonical_id': args.wcid,
                            'cts_urn': urn_base, 'ingest_class': 'tlg_e_local',
                            'passages': len(rows), 'period': args.period,
                            'source': f'tlg-e:TLG{args.author}.{args.work} ({args.edition})',
                            'status': 'in_corpus', 'title': args.title},
                           ensure_ascii=False) + '\n')
    with open(os.path.join(ROOT, 'data/audit/primary_wave/ingest_changelog.jsonl'), 'a') as f:
        f.write(json.dumps({'work': args.wcid, 'action': 'append', 'n': len(rows),
                            'edition': args.edition}, ensure_ascii=False) + '\n')
    print(f'APPLIED: {len(rows)} passages appended')


if __name__ == '__main__':
    main()
