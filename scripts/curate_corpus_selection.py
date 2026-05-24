#!/usr/bin/env python3
"""One-off curation aid: dedup the corpus works and tag free-will relevance.

Reads the live ancient_works list (passed as JSON on stdin or read from
/tmp/corpus_works.json) and produces data/corpus/curation_triage.tsv — one row
per ORIGINAL work entry with: decision (keep | merge | cut | review), the
canonical entry it belongs to, passage count, and a reason. Dedup is by
(normalized author, normalized title-stem), canonical = the entry with the most
passages. Free-will relevance is rule-based with explicit override sets; the
'review' rows are the judgment calls for human spot-check.

Not part of the reproducible pipeline — a curation worksheet generator.
"""
from __future__ import annotations

import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

from scripts.corpus_lib import write_jsonl

ROOT = Path(__file__).resolve().parents[1]
SRC = Path("/tmp/corpus_works.json")
OUT = ROOT / "data" / "corpus" / "curation_triage.tsv"
MANIFEST = ROOT / "data" / "corpus" / "manifest.jsonl"

# Authors whose works are out of free-will scope for the lean core.
# NOTE: written in NORMALIZED form (norm_author strips "of <place>").
CUT_AUTHORS = {
    "ignatius", "melito", "apollinaris",
}
# Title keywords marking incidental (martyrdom/paschal/liturgical) works to cut.
CUT_TITLE_KW = (
    "peri pascha", "pascha", "martyrium", "didache", "anima et corpore",
    "eclogae",
)
# Clear free-will / fate / providence / responsibility core (author-level keep).
# NORMALIZED form (norm_author strips "of <place>").
KEEP_AUTHORS = {
    "aristotle", "alexander", "aspasius", "chrysippus",
    "cleanthes", "cicero", "epictetus", "epicurus", "lucretius",
    "marcus aurelius", "plato", "plotinus", "plutarch", "porphyrius",
    "seneca", "sextus empiricus", "simplicius", "calcidius", "alcinous",
    "diogenes laertius", "aulus gellius", "philo",
    "origen", "augustine", "boethius", "methodius", "justin martyr",
    "pseudo-justin", "john chrysostom",
}
# Title keywords that force keep even on a borderline author/short text.
KEEP_TITLE_KW = (
    "de fato", "libero arbitrio", "αὐτεξουσ", "autexous", "heimarmen",
    "de providentia", "providence", "de divinatione", "consolatione",
    "de natura deorum", "peri archon", "de principiis", "philocalia",
)


def norm_author(a: str | None) -> str:
    a = (a or "").lower().strip()
    a = re.sub(r"\bof [a-z]+\b", "", a)            # "of Hierapolis"
    a = re.sub(r"\bd\.?\s*\d+.*$", "", a)          # "d. 524"
    a = re.sub(r"\(.*?\)", "", a)
    a = a.replace("titus lucretius carus", "lucretius")
    a = a.replace("marcus tullius cicero", "cicero")
    a = a.replace("aristotle stagira", "aristotle")
    a = re.sub(r"\s+", " ", a).strip()
    return a


def title_stem(t: str | None) -> str:
    t = (t or "").lower()
    t = re.sub(r"^[a-zα-ω\-\s\.]+,\s*", "", t)     # drop "Author, " prefix
    t = re.sub(r"\(.*?\)", "", t)                   # drop parentheticals
    t = re.sub(r"\b(livre|liber|book|fr\.?|excerpta|graeca|texte grec)\b.*$", "", t)
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"[^a-z0-9 ]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


# (author_norm, keyword-in-stem) -> canonical stem. Collapses cross-language /
# variant titles of the SAME work. Order matters; first match wins.
TITLE_ALIASES = [
    ("epictetus", "discourse", "discourses"),
    ("epictetus", "diatrib", "discourses"),
    ("epictetus", "enchiridion", "discourses"),
    ("marcus aurelius", "meditation", "meditations"),
    ("marcus aurelius", "eis heauton", "meditations"),
    ("aristotle", "nicomachean ethic", "nicomachean ethics"),
    ("aristotle", "ethica nicomachea", "nicomachean ethics"),
    ("aristotle", "nikomacheia", "nicomachean ethics"),
    ("plato", "republic", "republic"),
    ("plato", "politeia", "republic"),
    ("plato", "timaeus", "timaeus"),
    ("plato", "timaios", "timaeus"),
    ("origen", "contra celsum", "contra celsum"),
    ("origen", "contre celse", "contra celsum"),
    ("origen", "celsum", "contra celsum"),
    ("origen", "principiis", "de principiis"),
    ("origen", "peri archon", "de principiis"),
    ("origen", "archon", "de principiis"),
    ("origen", "philocalia", "philocalia"),
    ("", "philocalia", "philocalia"),
    ("justin martyr", "apologia prima", "apologia i"),
    ("justin martyr", "apologia i", "apologia i"),
    ("justin martyr", "first apology", "apologia i"),
    ("justin martyr", "apologia secunda", "apologia ii"),
    ("justin martyr", "dialog", "dialogus cum tryphone"),
    ("plotinus", "ennea", "enneades"),
    ("plotinus", "heimarmene", "enneades"),
    ("seneca", "providentia", "de providentia"),
    ("cicero", "de fato", "de fato"),
    ("augustine", "libero arbitrio voluntatis", "de libero arbitrio"),
]


def alias_stem(author_n: str, stem: str) -> str:
    for a, kw, canon in TITLE_ALIASES:
        if (not a or a in author_n) and kw in stem:
            # don't collapse Augustine's distinct grace works into DLA
            if author_n == "augustine" and "gratia" in stem and "voluntatis" not in stem:
                continue
            return canon
    return stem


def decide_keep(author_full: str, title: str) -> tuple[str, str]:
    """Final lean-core decision. Uses the FULL author (norm strips 'of <place>',
    which collides Clement of Alexandria with Clement of Rome). Everything in the
    cited corpus is free-will-relevant by default; only the explicitly named
    out-of-scope works are cut (per the approved review split)."""
    af = (author_full or "").lower()
    tl = (title or "").lower()
    # explicit review-cut decisions (approved):
    if "gregory of nazianzus" in af:
        return "cut", "Trinitarian orations, not free will"
    if "clement of rome" in af:
        return "cut", "church order, not free will"
    if "barnab" in tl:
        return "cut", "typology/covenant, not free will"
    if "septuagint" in af:
        return "cut", "single incidental passage"
    # out-of-scope authors (martyrdom/paschal) + liturgical titles:
    if any(a in af for a in ("ignatius", "melito", "apollinaris")):
        return "cut", "martyrdom/paschal author, out of scope"
    if any(k in tl for k in CUT_TITLE_KW):
        return "cut", "liturgical/martyrdom title"
    return "keep", "free-will-relevant (cited)"


def main() -> int:
    rows = json.loads(SRC.read_text(encoding="utf-8"))
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        an = norm_author(r["author"])
        groups[(an, alias_stem(an, title_stem(r["title"])))].append(r)

    out_lines = ["decision\tcanonical\tpassages\tauthor\ttitle\treason"]
    counts = defaultdict(int)
    distinct_keep = distinct_cut = 0
    manifest_rows: list[dict] = []
    for key, members in sorted(groups.items()):
        members.sort(key=lambda r: r["passages"], reverse=True)
        canonical = members[0]
        base_decision, reason = decide_keep(canonical["author"], canonical["title"])
        if base_decision == "keep":
            distinct_keep += 1
            cts = canonical.get("cts_urn") or ""
            manifest_rows.append({
                "canonical_id": canonical["canonical_id"],
                "author": canonical.get("author") or "",
                "title": canonical.get("title") or "",
                "period": canonical.get("period") or "",
                "cts_urn": cts,
                "source": f"scaife:{cts}" if cts else "",
                "passages": canonical["passages"],
                "status": "in_corpus" if canonical["passages"] >= 5 else "thin_needs_ingestion",
            })
        else:
            distinct_cut += 1
        for i, m in enumerate(members):
            if i == 0:
                decision, canon, rsn = base_decision, "self", reason
            else:
                decision = "merge" if base_decision == "keep" else "cut"
                canon = canonical["canonical_id"]
                rsn = f"dup of canonical ({canonical['passages']} pass.)"
            counts[decision] += 1
            out_lines.append(
                f"{decision}\t{canon}\t{m['passages']}\t{m['author'] or ''}\t{m['title'] or ''}\t{rsn}"
            )

    OUT.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    manifest_rows.sort(key=lambda r: r["canonical_id"])
    write_jsonl(MANIFEST, manifest_rows)
    print(f"original entries: {len(rows)}  |  distinct works: {len(groups)}")
    print(f"distinct decisions -> keep: {distinct_keep}  cut: {distinct_cut}")
    print(f"row-level decisions: {dict(counts)}")
    thin = sum(1 for r in manifest_rows if r["status"] == "thin_needs_ingestion")
    print(f"wrote {OUT}")
    print(f"wrote {MANIFEST}: {len(manifest_rows)} lean-core works ({thin} thin/needs-ingestion)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
