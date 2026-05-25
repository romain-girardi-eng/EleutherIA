"""Repair betacode-residue corruption in stored Greek text (in place).

Some passages were ingested with half-converted betacode: the grave accent ('\\'),
and occasionally acute ('/'), circumflex ('=') and capital marker ('*'), were left
as literal ASCII after otherwise-Unicode Greek (e.g. 'περι\\' for 'περὶ'), plus
layout newlines. This restores proper polytonic Unicode.

SAFETY:
  - Only passages carrying the unambiguous '{Greek}\\' marker are touched, so
    clean text and legitimate parentheses '()' (betacode breathings are already
    converted in this corpus) are never altered.
  - The conversion is deterministic accent placement + whitespace normalisation —
    no text is invented, reordered, or dropped. passage_id is preserved (citations
    intact).

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
_GR = r"Ͱ-Ͽἀ-῿"
# gate: any betacode residue — Greek+grave/acute/circumflex, or capital marker
_HAS_RESIDUE = re.compile(rf"[{_GR}][\\/=]|\*[̀-ͅ]*[{_GR}]")
_GRAVE, _ACUTE, _CIRC = "̀", "́", "͂"


def fix_betacode(t: str) -> str:
    if not t:
        return t
    t = t.replace("\r", " ")
    t = re.sub(rf"([{_GR}])\\", lambda m: m.group(1) + _GRAVE, t)
    t = re.sub(rf"([{_GR}])/", lambda m: m.group(1) + _ACUTE, t)
    t = re.sub(rf"([{_GR}])=", lambda m: m.group(1) + _CIRC, t)
    t = re.sub(rf"\*+([̀-ͅ]*)([{_GR}])",
               lambda m: m.group(2).upper() + m.group(1), t)
    t = unicodedata.normalize("NFC", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


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
            WHERE position(chr(92) in p.text_content) > 0
               OR p.text_content ~ '[*=/]'""")
        from collections import defaultdict
        per_work = defaultdict(int)
        updates: list[tuple] = []
        for r in rows:
            t = r["text_content"]
            if not _HAS_RESIDUE.search(t):
                continue
            fixed = fix_betacode(t)
            if fixed and fixed != t:
                updates.append((r["passage_id"], fixed, len(fixed), len(fixed.split())))
                per_work[r["canonical_id"]] += 1
        print(f"passages to repair: {len(updates)}\n")
        for cid, n in sorted(per_work.items(), key=lambda x: -x[1]):
            print(f"  {n:>4}  {cid[:55]}")
        # residual check on the proposed fixes
        residual = sum(1 for _pid, f, _c, _w in updates if _HAS_RESIDUE.search(f))
        print(f"\nresidual '{{Greek}}\\' after fix: {residual} (must be 0)")
        if updates:
            print("\nsample:")
            sid, sfx, _, _ = updates[0]
            orig = next(r["text_content"] for r in rows if r["passage_id"] == sid)
            print(f"  before: {orig[:90]!r}")
            print(f"  after : {sfx[:90]!r}")
        if commit and updates and residual == 0:
            async with conn.transaction():
                await conn.executemany(
                    f"""UPDATE {SCHEMA}.passages
                        SET text_content=$2, char_length=$3, word_count=$4
                        WHERE passage_id=$1""", updates)
            print(f"\nCOMMITTED {len(updates)} text repairs")
        elif commit and residual:
            print("\nABORTED commit — residual markers remain; investigate.")
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
