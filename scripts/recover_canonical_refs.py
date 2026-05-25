"""Recover faithful canonical references for a work's passages by text-aligning
them to the authoritative published edition (Perseus / First1KGreek TEI).

Scholarly contract (ZERO fabrication):
  - The canonical reference is *adopted verbatim* from the edition's own CTS
    citation hierarchy (Stephanus pages, Bekker numbers, book.chapter.section,
    prose/metre, ...). We never invent a reference.
  - Each DB passage is matched to the contiguous run of edition leaves whose
    text it reproduces. The passage then receives that run's reference, as a
    range "<first>-<last>" when it spans several leaves, or a single ref.
  - A text-match GATE protects against misattribution: if our stored text does
    not reproduce the edition's text, the work is reported as MISMATCH and left
    untouched (it may be the wrong work in the slot, or a non-TEI edition).

Only `cts_urn` and `canonical_ref` are rewritten; `passage_id` is never touched,
so passage_citations FKs are preserved.

Dry-run by default; --commit writes. Run from repo root (PYTHONPATH=.).
"""
from __future__ import annotations

import argparse
import asyncio
import os
import re
import sys
import unicodedata
from dataclasses import dataclass, field

import asyncpg
from dotenv import load_dotenv

from scripts.corpus_github_fetch import (
    _citation_depth,
    fetch_work_xml,
    parse_passages,
)
from lxml import etree

SCHEMA = "free_will"
ANCHOR = 8          # tokens used as head/tail anchors when locating a passage
MIN_GLOBAL_MATCH = 0.55  # fraction of passages that must align for a clean run


# --------------------------------------------------------------------------- #
# Text normalisation (accent-insensitive, punctuation-insensitive token stream)
# --------------------------------------------------------------------------- #

_TOKEN_RE = re.compile(r"[a-z0-9Ͱ-Ͽἀ-῿]+")


def norm_tokens(text: str) -> list[str]:
    """Lowercased, diacritic-stripped word tokens (Latin + Greek base letters)."""
    if not text:
        return []
    t = unicodedata.normalize("NFD", text)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.lower()
    # collapse final-sigma to medial for stable matching
    t = t.replace("ς", "σ")
    return _TOKEN_RE.findall(t)


# --------------------------------------------------------------------------- #
# Leaf model
# --------------------------------------------------------------------------- #

@dataclass
class Leaf:
    ref: str
    tokens: list[str]


@dataclass
class WorkResult:
    canonical_id: str
    work_urn: str
    status: str = "UNKNOWN"          # RECOVER | NOCHANGE | MISMATCH | NO_TEI | EMPTY
    n_passages: int = 0
    n_aligned: int = 0
    n_changed: int = 0
    note: str = ""
    updates: list[tuple] = field(default_factory=list)  # (passage_id, new_urn, new_cref, old_cref)
    samples: list[str] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# Edition fetch (resolve the right TEI version, deepest citation level)
# --------------------------------------------------------------------------- #

def fetch_leaves(work_urn: str) -> list[Leaf]:
    """Fetch TEI for *work_urn* and return its deepest-level citation leaves."""
    xml = fetch_work_xml(work_urn)  # raises URLError on 404 for all candidates
    root = etree.fromstring(xml, etree.XMLParser(recover=True, encoding="utf-8"))
    declared = _citation_depth(root)
    best: list[dict] = []
    # probe declared depth and one deeper; keep the deepest that yields > leaves
    for lvl in (declared, declared + 1, declared + 2):
        ps = parse_passages(xml, work_urn, level=lvl)
        if len(ps) > len(best):
            best = ps
    return [Leaf(ref=p["cts_urn"].rsplit(":", 1)[1], tokens=norm_tokens(p["text_content"]))
            for p in best if p.get("text_content")]


# --------------------------------------------------------------------------- #
# Edition resolution — discover available TEI versions on GitHub
# --------------------------------------------------------------------------- #

# preferred edition versions, best first (richest/most canonical citation scheme)
_VER_PREF = ["perseus-grc2", "perseus-grc1", "1st1K-grc1", "opp-grc1", "opp-grc2",
             "perseus-lat2", "perseus-lat1", "opp-lat1", "1st1K-lat1"]


def _ns_for_author(author: str) -> str:
    return "greekLit" if author.startswith("tlg") else "latinLit"


def _parse_base(urn: str | None) -> tuple[str, str, str, str | None] | None:
    """Parse a CTS URN into (namespace, author, work, version|None).

    Requires at least author.work. Returns None if the work part is missing.
    """
    if not urn or not urn.startswith("urn:cts:"):
        return None
    parts = urn.split(":")
    if len(parts) < 4:
        return None
    ns = parts[2]
    tail = parts[3].split(".")
    if len(tail) < 2:
        return None
    author, work = tail[0], tail[1]
    version = tail[2] if len(tail) >= 3 else None
    return ns, author, work, version


def candidate_edition_urns(work_cts: str | None, passage_cts: str | None,
                           tlg_code: str | None) -> list[str]:
    """Ordered list of full edition CTS work-URNs to try (best first)."""
    base = _parse_base(work_cts) or _parse_base(passage_cts)
    if not base and tlg_code and "." in tlg_code:
        a, w = tlg_code.split(".")[:2]
        base = (_ns_for_author(a), a, w, None)
    if not base:
        return []
    ns, author, work, version = base
    # Candidate versions: probe standard edition strings directly via raw GitHub
    # (CDN, no API rate limit). The stored version (if any) is tried first.
    std = ([v for v in _VER_PREF if "grc" in v] if ns == "greekLit"
           else [v for v in _VER_PREF if "lat" in v])
    seen: list[str] = []
    if version and version not in std:
        seen.append(version)
    seen += std
    return [f"urn:cts:{ns}:{author}.{work}.{v}" for v in dict.fromkeys(seen)]


# --------------------------------------------------------------------------- #
# Alignment
# --------------------------------------------------------------------------- #

def _find_anchor(flat: list[str], anchor: list[str], start: int) -> int:
    """Return index in *flat* (>= start) where *anchor* token run begins, or -1.

    Exact run first; then a fuzzy window allowing minor noise (>=60% of anchor
    tokens present in order-agnostic overlap within an anchor-length window).
    """
    if not anchor:
        return -1
    n = len(anchor)
    # exact contiguous
    first = anchor[0]
    i = start
    L = len(flat)
    while i <= L - n:
        if flat[i] == first and flat[i:i + n] == anchor:
            return i
        i += 1
    # fuzzy: slide a window, score token-set overlap
    aset = set(anchor)
    best_i, best_score = -1, 0.0
    win = max(n, 4)
    i = start
    while i <= L - win:
        w = flat[i:i + win]
        score = len(aset & set(w)) / len(aset)
        if score > best_score:
            best_score, best_i = score, i
        i += 1
    return best_i if best_score >= 0.6 else -1


def align(passages: list[tuple], leaves: list[Leaf]) -> tuple[list[tuple], int]:
    """Map each passage to a leaf-ref (range). Returns (per_passage_refs, n_aligned).

    passages: [(passage_id, seq, text, old_cref)] in document order.
    per_passage_refs: [(passage_id, ref_or_None, old_cref)].
    """
    flat: list[str] = []
    leaf_of: list[int] = []
    for li, lf in enumerate(leaves):
        for tok in lf.tokens:
            flat.append(tok)
            leaf_of.append(li)

    out: list[tuple] = []
    cursor = 0
    aligned = 0
    for pid, _seq, text, old_cref in passages:
        ptoks = norm_tokens(text)
        if not ptoks or not flat:
            out.append((pid, None, old_cref))
            continue
        head = ptoks[:ANCHOR]
        tail = ptoks[-ANCHOR:]
        s = _find_anchor(flat, head, cursor)
        if s < 0:
            s = _find_anchor(flat, head, 0)  # retry from start (out-of-order)
        if s < 0:
            out.append((pid, None, old_cref))
            continue
        e = _find_anchor(flat, tail, s)
        if e < 0:
            e = s + len(ptoks) - 1
        end_idx = min(e + len(tail) - 1, len(flat) - 1)
        start_leaf = leaf_of[s]
        end_leaf = leaf_of[max(s, min(end_idx, len(leaf_of) - 1))]
        if end_leaf < start_leaf:
            end_leaf = start_leaf
        ref = (leaves[start_leaf].ref if start_leaf == end_leaf
               else f"{leaves[start_leaf].ref}-{leaves[end_leaf].ref}")
        out.append((pid, ref, old_cref))
        aligned += 1
        cursor = end_idx + 1
    return out, aligned


def align_global(passages: list[tuple], leaves: list[Leaf],
                 thresh: float = 0.7) -> tuple[list[tuple], int]:
    """Order-independent alignment for cherry-picked / reordered subsets.

    For each passage, find the best-overlapping window in the edition's token
    stream (anchored on any of the passage's first tokens), independent of
    document order, and assign the leaf-range it covers. Accept only when the
    token-set overlap meets *thresh*; otherwise leave unaligned (flag).
    """
    flat: list[str] = []
    leaf_of: list[int] = []
    for li, lf in enumerate(leaves):
        for tok in lf.tokens:
            flat.append(tok)
            leaf_of.append(li)
    L = len(flat)
    pos: dict[str, list[int]] = {}
    for i, t in enumerate(flat):
        pos.setdefault(t, []).append(i)

    out: list[tuple] = []
    aligned = 0
    for pid, _seq, text, old_cref in passages:
        pt = norm_tokens(text)
        n = len(pt)
        if not pt or not flat:
            out.append((pid, None, old_cref))
            continue
        ptset = set(pt)
        starts: set[int] = set()
        for a in range(min(4, n)):              # anchor on any of first 4 tokens
            for p in pos.get(pt[a], ()):
                s0 = p - a
                if 0 <= s0 <= L - 1:
                    starts.add(s0)
        best_ov, best_s, best_e = 0.0, -1, -1
        for s0 in starts:
            e0 = min(s0 + n, L)
            ov = len(ptset & set(flat[s0:e0])) / len(ptset)
            if ov > best_ov:
                best_ov, best_s, best_e = ov, s0, e0 - 1
        if best_ov < thresh or best_s < 0:
            out.append((pid, None, old_cref))
            continue
        start_leaf = leaf_of[best_s]
        end_leaf = leaf_of[min(best_e, len(leaf_of) - 1)]
        if end_leaf < start_leaf:
            end_leaf = start_leaf
        ref = (leaves[start_leaf].ref if start_leaf == end_leaf
               else f"{leaves[start_leaf].ref}-{leaves[end_leaf].ref}")
        out.append((pid, ref, old_cref))
        aligned += 1
    return out, aligned


# --------------------------------------------------------------------------- #
# canonical_ref label
# --------------------------------------------------------------------------- #

def clean_title(title: str) -> str:
    """Short work tag for a canonical_ref. Strip parenthetical glosses; when the
    main title is non-Latin (e.g. Greek), prefer an ASCII gloss in parentheses
    so the reference stays legible ('Τίμαιος (Timaeus)' -> 'Timaeus')."""
    title = title or ""
    parens = re.findall(r"\(([^)]*)\)", title)
    main = re.sub(r"\([^)]*\)", "", title)
    main_ascii = main.encode("ascii", "ignore").decode().strip()
    if not main_ascii:  # main title is Greek/non-ASCII — use first ASCII gloss
        for p in parens:
            pa = p.encode("ascii", "ignore").decode().strip()
            if pa and pa.lower() != "english":
                return re.sub(r"\s+", " ", pa).strip(" ,;:-")
    return re.sub(r"\s+", " ", main).strip(" ,;:-")


def work_abbrev(old_cref: str, title: str) -> str:
    """Reuse an existing leading abbreviation (e.g. 'Enn.', 'De Opif.') if the
    stored canonical_ref already carries one; else derive a clean tag from title."""
    if old_cref:
        m = re.match(r"^([A-Za-z][\w.]*(?:\s+[A-Za-z][\w.]*){0,3}?\.)\s", old_cref)
        if m and not m.group(1)[0].isdigit():
            return m.group(1).strip()
    return clean_title(title)


# --------------------------------------------------------------------------- #
# Per-work driver
# --------------------------------------------------------------------------- #

async def process_work(conn, canonical_id: str, urn_override: str | None,
                       global_mode: bool = False, abbrev_override: str | None = None) -> WorkResult:
    row = await conn.fetchrow(
        f"""SELECT work_id, canonical_id, title, cts_urn, tlg_code
            FROM {SCHEMA}.ancient_works WHERE canonical_id=$1""", canonical_id)
    if not row:
        return WorkResult(canonical_id, "", status="NO_TEI", note="work not in ancient_works")
    work_id, title = row["work_id"], row["title"]
    work_cts, tlg_code = row["cts_urn"], row["tlg_code"]
    prows = await conn.fetch(
        f"""SELECT passage_id, sequence_number, text_content, canonical_ref, cts_urn
            FROM {SCHEMA}.passages WHERE work_id=$1 ORDER BY sequence_number""", work_id)
    passages = [(r["passage_id"], r["sequence_number"], r["text_content"], r["canonical_ref"])
                for r in prows]
    res = WorkResult(canonical_id, "", n_passages=len(passages))
    if not passages:
        res.status = "EMPTY"; return res

    # resolve edition URN(s): override wins; else try work-level cts_urn,
    # passage cts_urn, tlg_code — discovering GitHub editions when needed.
    first_passage_cts = next((r["cts_urn"] for r in prows if r["cts_urn"]), None)
    if urn_override:
        candidates = [urn_override]
    else:
        candidates = candidate_edition_urns(work_cts, first_passage_cts, tlg_code)
    if not candidates:
        res.status = "NO_TEI"; res.note = "no resolvable edition URN"; return res

    # try each candidate edition; keep the one that aligns best
    best = None  # (frac, n_aligned, per_passage, leaves, urn)
    tried_note = []
    for cand in candidates[:6]:
        try:
            leaves = fetch_leaves(cand)
        except Exception as exc:  # noqa: BLE001
            tried_note.append(f"{cand.rsplit('.',1)[-1]}:fetchfail")
            continue
        if not leaves:
            tried_note.append(f"{cand.rsplit('.',1)[-1]}:noleaves")
            continue
        aligner = align_global if global_mode else align
        per_passage, n_aligned = aligner(passages, leaves)
        frac = n_aligned / len(passages)
        if best is None or frac > best[0]:
            best = (frac, n_aligned, per_passage, leaves, cand)
        if frac >= 0.9:  # good enough, stop early
            break

    if best is None:
        res.status = "NO_TEI"
        res.note = f"no edition fetched ({'; '.join(tried_note) or 'none'})"
        return res

    frac, n_aligned, per_passage, leaves, edition_urn = best
    res.work_urn = edition_urn
    res.n_aligned = n_aligned
    # In global (in-place) mode we apply refs per-passage to whatever aligns
    # confidently and leave the rest untouched — the overall fraction may be low
    # (excerpt/summary passages), so the misattribution gate does not apply.
    if not global_mode and frac < MIN_GLOBAL_MATCH:
        res.status = "MISMATCH"
        res.note = (f"best edition {edition_urn} aligns only {n_aligned}/{len(passages)} "
                    f"({len(leaves)} leaves) — possible misattribution")
        res.samples.append("TEI[0]: " + " ".join(leaves[0].tokens[:14]))
        res.samples.append("DB[0] : " + " ".join(norm_tokens(passages[0][2])[:14]))
        return res
    work_urn = edition_urn

    abbrev = abbrev_override or work_abbrev(passages[0][3] or "", title)
    pmap = {r["passage_id"]: r for r in prows}
    unaligned: list[str] = []
    for pid, ref, old_cref in per_passage:
        if ref is None:
            unaligned.append(old_cref or "?")
            continue
        new_urn = f"{work_urn}:{ref}"
        new_cref = f"{abbrev} {ref}".strip() if abbrev else ref
        old = pmap[pid]
        if old["cts_urn"] != new_urn or (old["canonical_ref"] or "") != new_cref:
            res.updates.append((pid, new_urn, new_cref, old["canonical_ref"]))
    res.n_changed = len(res.updates)
    res.status = "RECOVER" if res.n_changed else "NOCHANGE"
    for u in res.updates[:5]:
        res.samples.append(f"{u[3]!r} -> {u[2]!r}")
    if unaligned:
        res.note = (f"{len(unaligned)} passage(s) UNALIGNED (left untouched): "
                    f"{unaligned[:6]}")
    return res


async def commit_updates(conn, res: WorkResult) -> None:
    async with conn.transaction():
        await conn.executemany(
            f"UPDATE {SCHEMA}.passages SET cts_urn=$2, canonical_ref=$3 WHERE passage_id=$1",
            [(pid, urn, cref) for pid, urn, cref, _old in res.updates])


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def _db_url() -> str:
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
    url = os.getenv("DATABASE_URL")
    if not url:
        sys.exit("ERROR: DATABASE_URL not set")
    return url.replace("postgresql://", "postgres://")


async def run(ids: list[str], commit: bool, urn_override: str | None,
              global_mode: bool = False, abbrev_override: str | None = None) -> None:
    conn = await asyncpg.connect(_db_url())
    try:
        for cid in ids:
            res = await process_work(conn, cid, urn_override, global_mode, abbrev_override)
            tag = f"[{res.status}]"
            print(f"\n{tag:11} {cid}")
            print(f"   urn={res.work_urn}  passages={res.n_passages} "
                  f"aligned={res.n_aligned} changed={res.n_changed}")
            if res.note:
                print(f"   note: {res.note}")
            for s in res.samples:
                print(f"     {s}")
            if commit and res.status == "RECOVER":
                await commit_updates(conn, res)
                print(f"   COMMITTED {res.n_changed} updates")
            elif res.status == "RECOVER":
                print("   (dry-run — use --commit to write)")
    finally:
        await conn.close()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--canonical-id", action="append", default=[],
                    help="work canonical_id (repeatable)")
    ap.add_argument("--from-file", help="file with one canonical_id per line")
    ap.add_argument("--urn-override", default=None,
                    help="force the edition CTS work-URN (single-work runs)")
    ap.add_argument("--commit", action="store_true")
    ap.add_argument("--global", dest="global_mode", action="store_true",
                    help="order-independent per-passage best-match (cherry-picked subsets)")
    ap.add_argument("--abbrev", default=None,
                    help="force the canonical_ref work abbreviation (e.g. 'PH', 'AM')")
    args = ap.parse_args()
    ids = list(args.canonical_id)
    if args.from_file:
        with open(args.from_file, encoding="utf-8") as fh:
            ids += [ln.strip() for ln in fh if ln.strip() and not ln.startswith("#")]
    if not ids:
        sys.exit("ERROR: provide --canonical-id or --from-file")
    asyncio.run(run(ids, args.commit, args.urn_override, args.global_mode, args.abbrev))


if __name__ == "__main__":
    main()
