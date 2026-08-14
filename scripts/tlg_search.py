#!/usr/bin/env python3
"""Search the local TLG E corpus (beta code) for a Greek phrase. Read-only.

Accent/breathing/case-insensitive: the Unicode Greek needle is reduced to base
letters and transliterated to beta-code base letters; author .TXT files are
reduced the same way (citation bytes and diacritic symbols stripped), so no
full beta-code decoding of the 618MB corpus is needed. A per-author normalized
cache (~/.cache/tlge_norm) is built lazily on first use.

Usage:
  tlg_search.py search '<greek unicode phrase>' [--max N] [--authors 0557,2042]
  tlg_search.py author <tlg number>     # show author name from AUTHTAB.DIR
"""
import argparse
import os
import re
import sys
import unicodedata

TLGE = os.environ.get('TLGE_DIR', os.path.expanduser('~/Desktop/Romain/TLGE'))
CACHE = os.path.expanduser('~/.cache/tlge_norm')

GREEK_TO_BETA = {
    'α': 'a', 'β': 'b', 'γ': 'g', 'δ': 'd', 'ε': 'e', 'ζ': 'z', 'η': 'h',
    'θ': 'q', 'ι': 'i', 'κ': 'k', 'λ': 'l', 'μ': 'm', 'ν': 'n', 'ξ': 'c',
    'ο': 'o', 'π': 'p', 'ρ': 'r', 'σ': 's', 'ς': 's', 'τ': 't', 'υ': 'u',
    'φ': 'f', 'χ': 'x', 'ψ': 'y', 'ω': 'w', 'ϝ': 'v',
}


def needle_to_beta_base(s: str) -> str:
    s = unicodedata.normalize('NFD', s).lower()
    out = []
    for ch in s:
        if unicodedata.combining(ch):
            continue
        if ch in GREEK_TO_BETA:
            out.append(GREEK_TO_BETA[ch])
        elif ch.isspace() or ch in "'’ʼ.,;·:!?-—()[]<>«»\"":
            out.append(' ')
        # any other char (latin letters, digits) breaks Greek — treat as space
        else:
            out.append(' ')
    return re.sub(r'\s+', ' ', ''.join(out)).strip()


def normalize_txt_bytes(raw: bytes):
    """Reduce a TLG .TXT author file to (base_letter_string, offset_map).

    Keeps only a-z (lowercased A-Z) and spaces; citation bytes (>=0x80),
    diacritics, markup and digits become spaces. offset_map[i] = byte offset in
    the raw file of normalized char i (for context extraction).
    """
    out = []
    offs = []
    prev_space = True
    diacritics = frozenset(b"()/\\=|+*'")  # in-word beta-code marks: delete, don't split
    for i, b in enumerate(raw):
        if 0x41 <= b <= 0x5A or 0x61 <= b <= 0x7A:
            out.append(chr(b | 0x20))
            offs.append(i)
            prev_space = False
        elif b in diacritics:
            continue
        else:
            if not prev_space:
                out.append(' ')
                offs.append(i)
                prev_space = True
    return ''.join(out), offs


def author_table():
    """tlg number -> author name, parsed from AUTHTAB.DIR (best effort)."""
    path = os.path.join(TLGE, 'AUTHTAB.DIR')
    table = {}
    try:
        raw = open(path, 'rb').read()
    except OSError:
        return table
    for m in re.finditer(rb'TLG(\d{4})', raw):
        num = m.group(1).decode()
        tail = raw[m.end():m.end() + 80]
        name = bytes(c for c in tail if 0x20 <= c < 0x7F).decode('ascii', 'replace')
        name = re.sub(r'\s+', ' ', name).strip(' *&1')
        if num not in table and name:
            table[num] = name[:60]
    return table


def beta_context_to_unicode(raw: bytes, start: int, end: int) -> str:
    seg = bytes(b for b in raw[max(0, start):end] if b < 0x80)
    txt = seg.decode('ascii', 'replace')
    txt = re.sub(r'[@{}<>\$&%#"\d]+', ' ', txt)
    txt = re.sub(r'\s+', ' ', txt).strip()
    try:
        import beta_code
        return beta_code.beta_code_to_greek(txt.lower())
    except Exception:
        return txt


def iter_author_files(only=None):
    for fn in sorted(os.listdir(TLGE)):
        m = re.fullmatch(r'TLG(\d{4})\.TXT', fn, re.I)
        if not m:
            continue
        if only and m.group(1) not in only:
            continue
        yield m.group(1), os.path.join(TLGE, fn)


def load_norm(num, path):
    os.makedirs(CACHE, exist_ok=True)
    cpath = os.path.join(CACHE, f'{num}.norm')
    opath = os.path.join(CACHE, f'{num}.offs')
    src_mtime = os.path.getmtime(path)
    if os.path.exists(cpath) and os.path.getmtime(cpath) >= src_mtime:
        norm = open(cpath, encoding='ascii').read()
        import array
        offs = array.array('I')
        with open(opath, 'rb') as f:
            offs.frombytes(f.read())
        return norm, offs
    raw = open(path, 'rb').read()
    norm, offs_list = normalize_txt_bytes(raw)
    import array
    offs = array.array('I', offs_list)
    with open(cpath, 'w', encoding='ascii') as f:
        f.write(norm)
    with open(opath, 'wb') as f:
        f.write(offs.tobytes())
    return norm, offs


def cmd_search(phrase, max_hits, authors):
    needle = needle_to_beta_base(phrase)
    if len(needle.replace(' ', '')) < 8:
        print(f'needle too short/empty after normalization: {needle!r}', file=sys.stderr)
        sys.exit(2)
    names = author_table()
    only = set(authors.split(',')) if authors else None
    hits = 0
    print(f'# needle(beta-base): {needle!r}', file=sys.stderr)
    for num, path in iter_author_files(only):
        norm, offs = load_norm(num, path)
        start = 0
        while True:
            j = norm.find(needle, start)
            if j < 0:
                break
            raw = open(path, 'rb').read()
            b0 = offs[j]
            b1 = offs[min(j + len(needle), len(offs) - 1)]
            ctx = beta_context_to_unicode(raw, b0 - 120, b1 + 120)
            print(f'TLG{num} ({names.get(num, "?")}) @byte {b0}')
            print(f'  ...{ctx}...')
            hits += 1
            if hits >= max_hits:
                print(f'# stopped at --max {max_hits}', file=sys.stderr)
                return
            start = j + 1
    print(f'# total hits: {hits}', file=sys.stderr)
    if hits == 0:
        sys.exit(1)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('search')
    s.add_argument('phrase')
    s.add_argument('--max', type=int, default=5)
    s.add_argument('--authors', default='')
    a = sub.add_parser('author')
    a.add_argument('num')
    args = ap.parse_args()
    if args.cmd == 'search':
        cmd_search(args.phrase, args.max, args.authors)
    else:
        print(author_table().get(args.num.zfill(4), 'not found'))


if __name__ == '__main__':
    main()
