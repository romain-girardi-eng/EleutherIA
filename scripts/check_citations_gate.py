#!/usr/bin/env python3
"""Zero-fabrication gate for SECONDARY (modern-scholarship) citations.

The Greek gate (``check_greek_gate.py``) protects ancient-language text, but
modern bibliographic references were ungated — which let a fabricated
citation (Bobzien, "Did Origen Invent the Free Will Problem?" 2014, a splice
of her real 2000 Epicurus paper) reach production. This gate closes that gap.

It fails (exit 1) when, among the nodes in scope:
  (a) a publication node carries an ISBN whose checksum is invalid, or
  (b) a ``modern_scholarship`` reference string is not present in the
      verified-citations manifest (``data/audit/citations_manifest.json``).

The manifest is the audited-clean bibliography. Any NEW reference must be
verified (real publication, accurate author/title/year/venue) and added to
the manifest in the same commit — making fabrication-by-accretion impossible.

Default scope: nodes whose lines differ from git HEAD (fast, pre-commit).
``--all`` scans every node (CI / periodic).

Usage:
  python3 scripts/check_citations_gate.py            # changed nodes vs HEAD
  python3 scripts/check_citations_gate.py --all      # full scan
  python3 scripts/check_citations_gate.py --rebuild-manifest  # regenerate from current clean data
"""
import argparse
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NODES = os.path.join(ROOT, 'data', 'kg', 'nodes.jsonl')
MANIFEST = os.path.join(ROOT, 'data', 'audit', 'citations_manifest.json')


def normalize(ref: str) -> str:
    """Match key for a citation: lowercase, alphanumerics only."""
    return re.sub(r'[^a-z0-9]', '', (ref or '').lower())


def get_meta(n: dict) -> dict:
    m = n.get('metadata')
    if isinstance(m, str):
        try:
            return json.loads(m)
        except (json.JSONDecodeError, ValueError):
            return {}
    return m or {}


def modern_scholarship_refs(n: dict):
    ms = n.get('modern_scholarship') or get_meta(n).get('modern_scholarship')
    if isinstance(ms, str):
        try:
            ms = json.loads(ms)
        except (json.JSONDecodeError, ValueError):
            ms = [ms]
    if not isinstance(ms, list):
        return
    for r in ms:
        if isinstance(r, dict):
            r = r.get('citation') or r.get('text') or r.get('title')
        if isinstance(r, str) and r.strip():
            yield r.strip()


def isbn_valid(raw: str):
    """True/False for a single ISBN-10/13; None if not a parseable single ISBN.

    A field may legitimately hold several ISBNs (hbk/pbk/ebk) or a placeholder
    like 'UNKNOWN'; those return None (not a failure).
    """
    d = re.sub(r'[^0-9Xx]', '', raw or '')
    if len(d) == 13 and d.isdigit():
        return sum((1 if i % 2 == 0 else 3) * int(c) for i, c in enumerate(d)) % 10 == 0
    if len(d) == 10:
        total = 0
        for i, c in enumerate(d):
            total += (10 if c in 'Xx' else int(c)) * (10 - i)
        return total % 11 == 0
    return None


def publication_isbns(n: dict):
    if n.get('type') != 'publication':
        return
    isbn = get_meta(n).get('isbn')
    if not isbn:
        return
    # only check when the field is a single ISBN token
    if isinstance(isbn, str) and ',' not in isbn and ';' not in isbn:
        yield isbn


def changed_node_lines():
    try:
        diff = subprocess.run(
            ['git', 'diff', 'HEAD', '--unified=0', '--', NODES],
            capture_output=True, text=True, cwd=ROOT, check=True,
        ).stdout
    except subprocess.CalledProcessError:
        return None
    out = []
    for line in diff.split('\n'):
        if line.startswith('+') and not line.startswith('+++'):
            payload = line[1:].strip()
            if payload:
                out.append(payload)
    return out


def iter_nodes(raw_lines):
    for raw in raw_lines:
        try:
            yield json.loads(raw)
        except json.JSONDecodeError:
            continue


def load_manifest() -> set:
    if not os.path.exists(MANIFEST):
        return set()
    data = json.load(open(MANIFEST, encoding='utf-8'))
    return set(data.get('verified', {}).keys())


def rebuild_manifest() -> int:
    """Regenerate the manifest from EVERY modern_scholarship ref currently in
    nodes.jsonl. Run this only after a fabrication audit has cleaned the data —
    it trusts the current state as ground truth."""
    refs = {}
    for n in iter_nodes(l.strip() for l in open(NODES, encoding='utf-8') if l.strip()):
        for ref in modern_scholarship_refs(n):
            refs[normalize(ref)] = ref
    os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
    payload = {
        '_doc': 'Audited-clean modern-scholarship citations. Keys are normalized '
                '(lowercase alphanumerics). Add a new entry only after verifying the '
                'publication is real and the citation accurate. See check_citations_gate.py.',
        'verified': dict(sorted(refs.items(), key=lambda kv: kv[1].lower())),
    }
    json.dump(payload, open(MANIFEST, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'citations-gate: manifest rebuilt with {len(refs)} verified references')
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--all', action='store_true', help='scan all nodes, not just changed ones')
    ap.add_argument('--rebuild-manifest', action='store_true',
                    help='regenerate the verified manifest from current (post-audit) data')
    args = ap.parse_args()

    if args.rebuild_manifest:
        return rebuild_manifest()

    if args.all:
        raw_lines = [l.strip() for l in open(NODES, encoding='utf-8') if l.strip()]
    else:
        raw_lines = changed_node_lines()
        if raw_lines is None:
            raw_lines = [l.strip() for l in open(NODES, encoding='utf-8') if l.strip()]
        if not raw_lines:
            print('citations-gate: no node changes — OK')
            return 0

    manifest = load_manifest()
    bad_isbn = []        # (node_id, isbn)
    unverified = []      # (node_id, ref)

    for n in iter_nodes(raw_lines):
        nid = n.get('node_id') or n.get('id')
        for isbn in publication_isbns(n):
            if isbn_valid(isbn) is False:
                bad_isbn.append((nid, isbn))
        for ref in modern_scholarship_refs(n):
            if normalize(ref) not in manifest:
                unverified.append((nid, ref))

    failed = False
    if bad_isbn:
        failed = True
        print('citations-gate: INVALID ISBN CHECKSUM(S):', file=sys.stderr)
        for nid, isbn in bad_isbn:
            print(f'  {nid}: {isbn}', file=sys.stderr)

    if unverified:
        failed = True
        print('citations-gate: UNVERIFIED modern_scholarship reference(s) — not in '
              'data/audit/citations_manifest.json:', file=sys.stderr)
        for nid, ref in unverified:
            print(f'  {nid}: {ref}', file=sys.stderr)
        print('\n  Each new secondary citation must be verified as a real, accurately\n'
              '  cited publication, then added to the manifest:\n'
              '    python3 scripts/check_citations_gate.py --rebuild-manifest\n'
              '  (only after confirming every new reference is genuine).', file=sys.stderr)

    if failed:
        return 1
    print(f'citations-gate: OK ({len(manifest)} verified references in manifest)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
