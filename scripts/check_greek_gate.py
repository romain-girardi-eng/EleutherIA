#!/usr/bin/env python3
"""Zero-fabrication gate for ancient Greek in KG node descriptions.

Fails (exit 1) when a node description contains a Greek run that is
(a) not found in the corpus (accent/sigma-insensitive),
(b) not in the adjudicated allowlist (data/audit/greek_allowlist.json), and
(c) not attested in the local TLG E corpus (scripts/tlg_search.py, if present).

Default scope: nodes whose lines differ from git HEAD (fast, pre-commit).
`--all` scans every node (CI / periodic).

Usage:
  python3 scripts/check_greek_gate.py            # changed nodes vs HEAD
  python3 scripts/check_greek_gate.py --all      # full scan
  python3 scripts/check_greek_gate.py --no-tlg   # skip TLG fallback
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NODES = os.path.join(ROOT, 'data', 'kg', 'nodes.jsonl')
PASSAGES = os.path.join(ROOT, 'data', 'corpus', 'passages.jsonl')
ALLOWLIST = os.path.join(ROOT, 'data', 'audit', 'greek_allowlist.json')
TLG_SEARCH = os.path.join(ROOT, 'scripts', 'tlg_search.py')

GREEK_CH = r'Ͱ-Ͽἀ-῿̀-ͯ'
RUN = re.compile(rf"[{GREEK_CH}][{GREEK_CH}\s\.,··;:’'··\-—]+")
MIN_CHARS = 18


def strip(s: str) -> str:
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c)).lower().replace('ς', 'σ')
    s = re.sub(r'[^Ͱ-Ͽ]+', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def run_hash(run: str) -> str:
    return hashlib.sha1(strip(run).encode()).hexdigest()[:16]


def extract_runs(desc: str):
    out = []
    for m in RUN.finditer(desc):
        seg = m.group(0).strip(" .,··;:’'·-—\n")
        if len(seg) >= MIN_CHARS:
            out.append(seg)
    return out


def changed_node_lines():
    """Node JSON lines added/modified in nodes.jsonl vs HEAD (staged or not)."""
    try:
        diff = subprocess.run(
            ['git', 'diff', 'HEAD', '--unified=0', '--', NODES],
            capture_output=True, text=True, cwd=ROOT, check=True,
        ).stdout
    except subprocess.CalledProcessError:
        return None  # no HEAD (fresh repo) — caller falls back to full scan
    lines = []
    for line in diff.split('\n'):
        if line.startswith('+') and not line.startswith('+++'):
            payload = line[1:].strip()
            if payload:
                lines.append(payload)
    return lines


def tlg_attested(run_text: str) -> bool:
    if not os.path.exists(TLG_SEARCH):
        return False
    words = strip(run_text).split()
    needle = ' '.join(words[:9])
    if len(needle.replace(' ', '')) < 10:
        return False
    r = subprocess.run(
        [sys.executable, TLG_SEARCH, 'search', run_text, '--max', '1'],
        capture_output=True, text=True,
    )
    return bool(r.stdout.strip())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--all', action='store_true', help='scan all nodes, not just changed ones')
    ap.add_argument('--no-tlg', action='store_true', help='skip the TLG E fallback check')
    args = ap.parse_args()

    if args.all:
        raw_lines = [l.strip() for l in open(NODES) if l.strip()]
    else:
        raw_lines = changed_node_lines()
        if raw_lines is None:
            raw_lines = [l.strip() for l in open(NODES) if l.strip()]
        if not raw_lines:
            print('greek-gate: no node changes — OK')
            return 0

    candidates = []  # (node_id, run)
    for raw in raw_lines:
        try:
            n = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if n.get('type') == 'passage':
            continue
        desc = n.get('description') or ''
        if not re.search(rf'[{GREEK_CH}]', desc):
            continue
        nid = n.get('node_id') or n.get('id')
        for run in extract_runs(desc):
            candidates.append((nid, run))

    if not candidates:
        print('greek-gate: no Greek runs in scope — OK')
        return 0

    allow = json.load(open(ALLOWLIST)).get('allow', {}) if os.path.exists(ALLOWLIST) else {}
    allow_hashes = {nid: {e['hash'] for e in entries} for nid, entries in allow.items()}

    print(f'greek-gate: checking {len(candidates)} Greek runs '
          f'({len({c[0] for c in candidates})} nodes) against corpus...', flush=True)
    blob = []
    for line in open(PASSAGES):
        t = json.loads(line).get('text_content') or ''
        if re.search(rf'[{GREEK_CH}]', t):
            blob.append(strip(t))
    blob = ' ␟ '.join(blob)

    failures = []
    for nid, run in candidates:
        norm = strip(run)
        if norm in blob:
            continue
        if run_hash(run) in allow_hashes.get(nid, set()):
            continue
        if not args.no_tlg and tlg_attested(run):
            print(f'  note: {nid}: run attested in TLG E but not corpus/allowlist '
                  f'— add to allowlist with provenance: {run[:50]!r}')
            failures.append((nid, run, 'tlg_only'))
            continue
        failures.append((nid, run, 'unattested'))

    if failures:
        print(f'\ngreek-gate: FAIL — {len(failures)} unverified Greek run(s):')
        for nid, run, kind in failures:
            print(f'  [{kind}] {nid}: {run[:80]!r}')
        print('\nEvery Greek quotation must be verbatim from the corpus, a named edition, '
              'or TLG E, with provenance. Verify the source, then either fix the text or '
              'add an allowlist entry (data/audit/greek_allowlist.json) citing the edition.')
        return 1
    print('greek-gate: OK')
    return 0


if __name__ == '__main__':
    sys.exit(main())
