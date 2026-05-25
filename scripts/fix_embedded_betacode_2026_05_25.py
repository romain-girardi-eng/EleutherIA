"""Transliterate embedded raw-betacode Greek tokens to Unicode (in place).

Some Latin works (Cicero De Div/De Nat Deorum, Seneca, Augustine) quote Greek
terms encoded in TLG betacode (e.g. 'ei(marme/nhn', '*a)pa/qeia', 'peri\\ lo/gou')
instead of Unicode Greek. This converts ONLY whitespace-bounded tokens that are
unambiguous betacode (carry a betacode breathing/accent marker, consist solely of
betacode characters, and transliterate to a valid polytonic-Greek word). Latin
words are never touched. The faithful encoded accent is preserved (no fabrication).

Dry-run by default; --commit writes. Run from repo root (PYTHONPATH=.).
"""
from __future__ import annotations

import argparse
import asyncio
import os
import re
import sys
import unicodedata

import asyncpg
from dotenv import load_dotenv

SCHEMA = "free_will"
# Only classical Latin/Greek works that genuinely embed Greek in betacode — never
# English-summary nodes (where '/' means 'or' and would be mis-transliterated).
_ALLOW = {
    "urn_cts_latinlit_stoa0040_stoa001_v_xii_xiv_lat",  # Augustine, City of God
    "urn_cts_latinlit_phi1017_phi015_lat",              # Seneca
    "urn_cts_latinlit_phi0474_phi053_lat",              # Cicero, De Divinatione
    "urn_cts_latinlit_phi0474_phi050_lat",              # Cicero, De Natura Deorum
    "urn_cts_greeklit_tlg0007_tlg136_grc",              # Plutarch, De Stoic. Repugn.
}
_LET = {"a": "α", "b": "β", "g": "γ", "d": "δ", "e": "ε", "z": "ζ", "h": "η",
        "q": "θ", "i": "ι", "k": "κ", "l": "λ", "m": "μ", "n": "ν", "c": "ξ",
        "o": "ο", "p": "π", "r": "ρ", "s": "σ", "t": "τ", "u": "υ", "f": "φ",
        "x": "χ", "y": "ψ", "w": "ω"}
_DIA = {")": "̓", "(": "̔", "/": "́", "\\": "̀", "=": "͂", "|": "ͅ", "+": "̈"}
_MARK = set(_DIA) | {"*"}
_GREEK_RANGE = re.compile(r"[Ͱ-Ͽἀ-῿]")


def translit(tok: str) -> str:
    res = ""
    pre_cap = False
    pre_dia = ""
    seen_letter = False
    i, n = 0, len(tok)
    while i < n:
        ch = tok[i]
        if ch == "*":
            pre_cap = True; i += 1; continue
        if ch in _DIA and not seen_letter:
            pre_dia += _DIA[ch]; i += 1; continue
        low = ch.lower()
        if low in _LET:
            base = _LET[low].upper() if (pre_cap or ch.isupper()) else _LET[low]
            post = ""; j = i + 1
            while j < n and tok[j] in _DIA:
                post += _DIA[tok[j]]; j += 1
            if low == "s" and not pre_cap and (j >= n or not tok[j].isalpha()):
                base = "ς"
            res += unicodedata.normalize("NFC", base + pre_dia + post)
            pre_cap = False; pre_dia = ""; seen_letter = True; i = j; continue
        res += ch; pre_cap = False; pre_dia = ""; i += 1
    return res


_PUNCT = ".,;:·—'\"’”)(][】"
_BETA_TOKEN = re.compile(r"^[*]?[A-Za-z()/\\=|+*]+$")


def fix_text(t: str) -> tuple[str, list[tuple[str, str]]]:
    """Return (new_text, [(old_tok, new_tok), ...])."""
    changes: list[tuple[str, str]] = []
    out_parts: list[str] = []
    for tok in re.split(r"(\s+)", t):
        if tok.isspace() or not tok:
            out_parts.append(tok); continue
        lead = ""; trail = ""
        core = tok
        while core and core[0] in _PUNCT:
            lead += core[0]; core = core[1:]
        while core and core[-1] in _PUNCT:
            trail = core[-1] + trail; core = core[:-1]
        # Latin enclitic '-que' is sometimes glued to a betacode word ('*fai/nwnque')
        suffix = ""
        if core.endswith("que") and re.search(r"[/\\=]", core[:-3]):
            core, suffix = core[:-3], "que"
        # must carry a betacode ACCENT ('/','\\','=') — breathing/paren alone is not
        # enough (rejects Latin 'e(iiciens'); all-betacode chars; have a vowel; and
        # NO bare uppercase ASCII (Latin apex 'U/bi'/English 'Fear/' — betacode
        # capitals are '*'-prefixed, never bare uppercase).
        if (core and _BETA_TOKEN.match(core) and re.search(r"[/\\=]", core)
                and any(c.lower() in _LET for c in core)
                and not re.search(r"(?<!\*)[A-Z]", core)):
            g = translit(core)  # Greek part only (suffix is the Latin enclitic)
            new = g + suffix
            # accept only if the Greek part is genuine Greek (no leftover ascii/markers)
            if g != core and not re.search(r"[A-Za-z()/\\=|+*]", g) and _GREEK_RANGE.search(g):
                changes.append((core + suffix, new))
                out_parts.append(lead + new + trail); continue
        out_parts.append(tok)
    return "".join(out_parts), changes


def _db_url() -> str:
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
    url = os.getenv("DATABASE_URL")
    if not url:
        sys.exit("ERROR: DATABASE_URL not set")
    return url.replace("postgresql://", "postgres://")


async def run(commit: bool) -> None:
    conn = await asyncpg.connect(_db_url())
    try:
        rows = await conn.fetch(f"""
            SELECT p.passage_id, p.text_content, w.canonical_id
            FROM {SCHEMA}.passages p JOIN {SCHEMA}.ancient_works w ON w.work_id=p.work_id
            WHERE p.text_content ~ '[a-z][)(/\\\\=]|[)(/\\\\=][a-z]|\\*[)(/=\\\\]'""")
        updates = []
        for r in rows:
            if r["canonical_id"] not in _ALLOW:
                continue
            new, changes = fix_text(r["text_content"])
            if changes:
                updates.append((r["passage_id"], new, len(new), len(new.split()), r["canonical_id"], changes))
        print(f"passages with betacode tokens to transliterate: {len(updates)}\n")
        for pid, _new, _c, _w, cid, changes in updates:
            print(f"  {cid[:38]:38} {[f'{a}->{b}' for a, b in changes][:5]}")
        if commit and updates:
            async with conn.transaction():
                await conn.executemany(
                    f"""UPDATE {SCHEMA}.passages SET text_content=$2, char_length=$3, word_count=$4
                        WHERE passage_id=$1""",
                    [(pid, new, c, w) for pid, new, c, w, _cid, _ch in updates])
            print(f"\nCOMMITTED {len(updates)} passages")
        elif updates:
            print("\n(dry-run — use --commit to write)")
    finally:
        await conn.close()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--commit", action="store_true")
    asyncio.run(run(ap.parse_args().commit))


if __name__ == "__main__":
    main()
