"""De-mangle non-standard canonical_refs in place (no fabrication — only reformat
locus data already present in the ref string).

Three classes (detected by ref shape):

  A. french_sc   French SC-importer refs ('1.chap.: 4, verset: 9b-14',
                 '2.liv.: 2 (gloss), chap.: 36', 'SC 379, chap.: 7, par.: 1, §17')
                 -> structured '{book}.{chapter}[.{section}]' matching the corpus
                 '1.x.y' convention. Parts: liv.->book, chap.->chapter,
                 verset./par.->section; leading 'N.' or default '1' as book.
                 FLAG (leave) when fragm. present, no chapter, or papyrus/Barlaam
                 prose (book/scheme not safely recoverable).

  B. summary_locus_pre   'Origen, De Principiis III.1.3: Self-Determining Judgment'
                 -> keep the citation before the description colon.

  C. summary_locus_paren 'Lucretius on the swerve (DRN II.251-293)'
                 -> the parenthetical locus.

Only canonical_ref is rewritten; cts_urn and passage_id are untouched.
Dry-run by default; --commit writes. Run from repo root (PYTHONPATH=.).
"""
from __future__ import annotations

import argparse
import asyncio
import os
import re
import sys
from collections import defaultdict

import asyncpg
from dotenv import load_dotenv

SCHEMA = "free_will"


def is_descriptive(s: str) -> bool:
    s = (s or "").strip()
    wc = len(s.split())
    if not s:
        return False
    if ": " in s and wc >= 4:
        return True
    if wc > 6:
        return True
    if not re.search(r"\d", s) and wc >= 3:
        return True
    return False


_FRENCH = re.compile(r"(liv\.?:|chap\.?:|verset:|par\.?:|fragm\.?:|§|\bSC\s*\d)", re.I)


def _grab(label: str, s: str) -> str | None:
    m = re.search(label + r"\s*([0-9][0-9a-z]*(?:-[0-9][0-9a-z]*)?)", s, re.I)
    return m.group(1) if m else None


def demangle_french(s: str) -> str | None:
    """Return structured ref or None (=flag) for a French SC ref."""
    if re.search(r"fragm\.?:", s, re.I):
        return None  # Melito-style fragment refs — scheme not safe to auto-build
    if re.search(r"papyrolog|Roman de Barlaam", s, re.I):
        return None  # Aristides papyrus prose
    book = _grab(r"liv\.?:", s)
    chap = _grab(r"chap\.?:", s)
    sect = _grab(r"verset:", s) or _grab(r"par\.?:", s)
    if not chap:
        return None  # e.g. Contra Celsum 'SC 150, par.: 65' — book ambiguous
    if not book:
        m = re.match(r"^\s*(\d+)\.", s)  # leading 'N.' part marker
        book = m.group(1) if m else "1"
    ref = f"{book}.{chap}"
    if sect:
        ref += f".{sect}"
    return ref


_HAS_LOCUS = re.compile(r"\d|\b[IVXLC]{1,5}\b")


def _looks_citation(x: str) -> bool:
    return bool(_HAS_LOCUS.search(x)) and len(x) <= 45


def demangle_summary(s: str) -> str | None:
    """Category B/C: keep the locus, drop the prose description."""
    # B: 'Author, Work Locus: Description' — keep the citation before the colon
    if ": " in s:
        head = s.split(": ", 1)[0].strip()
        if _looks_citation(head):
            return head
    # locus-before-gloss: 'De Fato 14 (gloss)' / 'EN III.1, 1110a4-8 (gloss)'
    before = re.split(r"\s*\(", s, 1)[0].strip()
    if "(" in s and _looks_citation(before) and before != s:
        return before
    # C: 'Description (Work Locus)' — last parenthetical that is itself a locus
    parens = [p.strip() for p in re.findall(r"\(([^)]*)\)", s) if _HAS_LOCUS.search(p)]
    parens = [p for p in parens if p.lower() != "english"]
    if parens:
        return parens[-1]
    return None


def compute_new_ref(s: str) -> tuple[str, str | None]:
    """Return (category, new_ref|None)."""
    if re.search(r"papyrolog|Roman de Barlaam|fragments? papyr", s, re.I):
        return "flag", None  # papyrus/Barlaam prose — no clean locus scheme
    if _FRENCH.search(s):
        return "french_sc", demangle_french(s)
    return "summary", demangle_summary(s)


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
            SELECT p.passage_id, p.canonical_ref, w.canonical_id
            FROM {SCHEMA}.passages p JOIN {SCHEMA}.ancient_works w ON w.work_id=p.work_id""")
        updates: list[tuple] = []
        flagged: list[tuple] = []
        per_work = defaultdict(lambda: {"fix": 0, "flag": 0, "samples": []})
        for r in rows:
            s = r["canonical_ref"]
            if not is_descriptive(s):
                continue
            cat, new = compute_new_ref(s)
            w = per_work[r["canonical_id"]]
            if new and new != s:
                updates.append((r["passage_id"], new))
                w["fix"] += 1
                if len(w["samples"]) < 3:
                    w["samples"].append(f"{s[:60]!r} -> {new!r}")
            else:
                flagged.append((r["canonical_id"], s))
                w["flag"] += 1
        print(f"to fix: {len(updates)}   to flag (left as-is): {len(flagged)}\n")
        for cid, w in sorted(per_work.items(), key=lambda x: -x[1]["fix"]):
            print(f"  fix={w['fix']:>3} flag={w['flag']:>2}  {cid[:48]}")
            for smp in w["samples"]:
                print(f"        {smp}")
        if commit and updates:
            async with conn.transaction():
                await conn.executemany(
                    f"UPDATE {SCHEMA}.passages SET canonical_ref=$2 WHERE passage_id=$1",
                    updates)
            print(f"\nCOMMITTED {len(updates)} canonical_ref updates")
        elif updates:
            print("\n(dry-run — use --commit to write)")
        # dump flagged for the review file
        if flagged:
            byw = defaultdict(list)
            for cid, s in flagged:
                byw[cid].append(s)
            with open("/tmp/demangle_flagged.txt", "w", encoding="utf-8") as fh:
                for cid, ss in sorted(byw.items()):
                    fh.write(f"## {cid} ({len(ss)})\n")
                    for s in ss:
                        fh.write(f"   {s}\n")
            print(f"\nflagged detail -> /tmp/demangle_flagged.txt ({len(flagged)} refs)")
    finally:
        await conn.close()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--commit", action="store_true")
    args = ap.parse_args()
    asyncio.run(run(args.commit))


if __name__ == "__main__":
    main()
