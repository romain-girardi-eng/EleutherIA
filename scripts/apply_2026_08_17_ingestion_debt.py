#!/usr/bin/env python3
"""Wave 5: pay down the debt that ``check_ingestion_rules.py`` reports.

Four defects, all found by the ingestion rules once they existed:

A. **Study notes and summaries typed as primary text.** 661 (cts_urn, role)
   groups collide. Part of that is real: alongside the Greek or Latin text of a
   locus sit vocabulary glosses, English summaries and markdown-wrapped excerpts
   carrying the SAME CTS URN and the SAME ``passage_role: original``. A summary
   of Augustine is then citable as if it were Augustine. They are demoted with a
   truthful ``passage_role`` — nothing is deleted, and the URN is kept because
   the node really is *about* that locus.

   NOT touched here: the 52 groups of more than three members. Those are not
   duplicates at all — they are a work-level URN stamped onto every passage of
   the work (1,335 Plotinus passages all carry
   ``urn:cts:greekLit:tlg2000.tlg001.perseus-grc1:1``). That is a different
   defect needing a policy decision about passage-level references, and it is
   reported rather than guessed at.

B. **40 translations with no resolvable ``original_node_id``.** Every one follows
   the ``X_en`` → ``X`` convention, and 37 are independently confirmed by sharing
   the original's CTS URN.

C. **204 works with no canonical id** (rule R3b). 59 can be derived from their
   own passages, which unanimously agree on one ``work_canonical_id``. The other
   145 have no passage children and are left alone.

D. **95 scholarly arguments on a competing schema**, recording their publication
   under ``e2_publication_id`` and their locus under ``page_or_loc`` instead of
   ``scholarly_work_id`` / ``page_range``. All 95 pointers resolve, so this is a
   pure rename; the original keys are kept alongside for traceability.

Usage:
    python3 scripts/apply_2026_08_17_ingestion_debt.py [--dry-run]
"""

from __future__ import annotations

import argparse
import collections
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"
EDGES_PATH = ROOT / "data" / "kg" / "edges.jsonl"

STAMP = "ingestion_debt_2026_08_17"
GREEK = re.compile(r"[Ͱ-Ͽἀ-῿]")
_LAT = """et non est cum quod autem enim sed in ad qui quae esse ut si nec ex de per hoc ipse
atque neque tamen etiam ita eius sunt potest anima deus nam quia vero omnia"""
_ENG = """the and of that is to in for with are this it as be by not from which on his her they
was were has have can does argues explains considers passage chapter book here"""
LAT_WORDS = frozenset(_LAT.split())
ENG_WORDS = frozenset(_ENG.split())

counts: dict[str, int] = {}
log: list[str] = []


def note(op: str, msg: str) -> None:
    log.append(f"[{op}] {msg}")
    counts[op] = counts.get(op, 0) + 1


def read_jsonl(p: Path) -> list[dict]:
    with p.open(encoding="utf-8") as fh:
        return [json.loads(x) for x in fh if x.strip()]


def write_jsonl(p: Path, rows: list[dict]) -> None:
    with p.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")


def nid(n: dict) -> str:
    return n.get("node_id") or n.get("id") or ""


def meta(n: dict) -> dict:
    v = n.get("metadata")
    if isinstance(v, str):
        try:
            v = json.loads(v)
        except json.JSONDecodeError:
            return {}
    return v if isinstance(v, dict) else {}


def set_meta(n: dict, d: dict) -> None:
    if isinstance(n.get("metadata"), str):
        n["metadata"] = json.dumps(d, ensure_ascii=False)
    else:
        n["metadata"] = d


def kind(n: dict) -> str:
    d = (n.get("description") or "").strip()
    md = meta(n)
    if d.lstrip().startswith("**Reference:**"):
        return "excerpt_wrapper"
    if re.match(r"^\s*(Greek|Latin)\s*:\s*[•\-]", d) or d.count("•") >= 3:
        return "vocab_gloss"
    if (md.get("passage_role") or "original") == "translation" or md.get("source") == "ai_translation":
        return "translation"
    if len(GREEK.findall(d)) / max(len(d), 1) > 0.12:
        return "greek_text"
    words = re.findall(r"[a-zA-Zà-ÿ']+", d.lower())
    lat = sum(1 for w in words if w in LAT_WORDS) / max(len(words), 1)
    eng = sum(1 for w in words if w in ENG_WORDS) / max(len(words), 1)
    if lat > 0.045 and lat > eng:
        return "latin_text"
    if eng > 0.05:
        return "english_prose"
    return "unclear"


DEMOTE = {
    "vocab_gloss": ("vocabulary_gloss",
                    "a list of glossed Greek or Latin terms with English equivalents — study notes "
                    "about the locus, not the text of it"),
    "excerpt_wrapper": ("excerpt",
                        "a markdown-wrapped partial excerpt ('**Reference:** … **Original Greek:**') "
                        "of a locus whose full text is carried by a sibling node"),
    "english_prose": ("summary",
                      "English prose summarising the locus, sharing the CTS URN and the 'original' "
                      "role with the node that carries the actual ancient text"),
}
TEXT_KINDS = {"greek_text", "latin_text"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    nodes = read_jsonl(NODES_PATH)
    edges = read_jsonl(EDGES_PATH)
    N = {nid(n): n for n in nodes}

    # ---- A. demote study notes / summaries sharing a locus with real text --
    groups: dict[tuple, list[str]] = collections.defaultdict(list)
    for k, n in N.items():
        if n.get("type") != "passage":
            continue
        md = meta(n)
        if md.get("cts_urn"):
            groups[(md["cts_urn"], md.get("passage_role") or "original")].append(k)

    for key, members in groups.items():
        if not (2 <= len(members) <= 3):
            continue  # >3 = work-level URN, a different defect (see docstring)
        kinds = {k: kind(N[k]) for k in members}
        if not any(v in TEXT_KINDS for v in kinds.values()):
            continue  # no text-bearing sibling: nothing to demote against
        for k, kd in kinds.items():
            if kd not in DEMOTE:
                continue
            role, why = DEMOTE[kd]
            md = meta(N[k])
            if md.get("passage_role") == role:
                continue
            sibling = next(x for x, v in kinds.items() if v in TEXT_KINDS)
            md[f"{STAMP}_role_change"] = (
                f"passage_role {md.get('passage_role') or 'original'!r} -> {role!r}: {why}. "
                f"The ancient text of {key[0]} is carried by {sibling}. Nothing was deleted and the "
                "CTS URN is kept: this node is genuinely about that locus, it is simply not the text."
            )
            md["passage_role"] = role
            set_meta(N[k], md)
            note("A_demote_non_text_passage", f"{k}: -> {role}")

    # ---- B. reconnect translations to their originals ---------------------
    for k, n in N.items():
        if n.get("type") != "passage":
            continue
        md = meta(n)
        if md.get("passage_role") != "translation":
            continue
        if md.get("original_node_id") in N:
            continue
        cand = k[:-3] if k.endswith("_en") else None
        if not cand or cand not in N:
            continue
        by_urn = md.get("cts_urn") and meta(N[cand]).get("cts_urn") == md.get("cts_urn")
        md["original_node_id"] = cand
        md[f"{STAMP}_original_relink"] = (
            f"original_node_id was absent or unresolvable; set to {cand} by the '<id>_en' convention"
            + (", independently confirmed by a shared cts_urn" if by_urn else "")
        )
        set_meta(N[k], md)
        note("B_relink_translation", f"{k} -> {cand}")

    # ---- C. derive a canonical id for works whose passages agree ----------
    kids: dict[str, list[str]] = collections.defaultdict(list)
    for e in edges:
        if e.get("relation") == "part_of" and N.get(e["target"], {}).get("type") == "work" \
           and N.get(e["source"], {}).get("type") == "passage":
            kids[e["target"]].append(e["source"])
    for w, n in N.items():
        if n.get("type") != "work":
            continue
        md = meta(n)
        if md.get("cts_urn") or md.get("work_canonical_id"):
            continue
        cs = {meta(N[p]).get("work_canonical_id") for p in kids.get(w, []) if meta(N[p]).get("work_canonical_id")}
        if len(cs) != 1:
            continue
        canon = cs.pop()
        md["work_canonical_id"] = canon
        md[f"{STAMP}_canonical_derived"] = (
            f"derived from the work's own {len(kids[w])} passages, which unanimously carry "
            f"work_canonical_id={canon}. Satisfies rule R3b so the work can be deduplicated by "
            "identity rather than by title."
        )
        set_meta(N[w], md)
        note("C_derive_work_canonical", f"{w} -> {canon}")

    # ---- D. normalise the competing argument schema ----------------------
    for k, n in N.items():
        if n.get("type") != "argument":
            continue
        md = meta(n)
        if md.get("scholarly_work_id"):
            continue
        pub = md.get("e2_publication_id")
        if not pub or pub not in N:
            continue
        md["scholarly_work_id"] = pub
        if not md.get("page_range") and md.get("page_or_loc"):
            md["page_range"] = md["page_or_loc"]
        md[f"{STAMP}_schema_normalised"] = (
            "publication and locus were recorded under the e2 wave's field names "
            "(e2_publication_id / page_or_loc); copied to the canonical scholarly_work_id / "
            "page_range. The original keys are kept for traceability."
        )
        set_meta(N[k], md)
        note("D_normalise_argument_schema", f"{k} -> {pub}")

    # ---- invariants -------------------------------------------------------
    ids = [nid(n) for n in nodes]
    assert len(ids) == len(set(ids)), "duplicate node ids"
    present = set(ids)
    assert not [e for e in edges if e["source"] not in present or e["target"] not in present], "dangling"
    for k, n in N.items():
        md = meta(n)
        if md.get("passage_role") == "translation" and md.get("original_node_id"):
            assert md["original_node_id"] in present, f"{k}: original_node_id dangling"

    print(f"nodes {len(nodes)}   edges {len(edges)}")
    for key in sorted(counts):
        print(f"  {key}: {counts[key]}")

    # report what is deliberately left
    big = {k: v for k, v in groups.items() if len(v) > 3}
    print(f"\nleft for a policy decision: {len(big)} work-level-URN groups covering "
          f"{sum(len(v) for v in big.values())} passages (largest: "
          f"{max((len(v), k[0]) for k, v in big.items())[1]})")

    if args.dry_run:
        print("\n--dry-run: nothing written")
        return 0

    write_jsonl(NODES_PATH, nodes)
    report = ROOT / "data" / "audit" / "2026-08-17_ingestion_debt_applied.md"
    report.write_text(
        "# Ingestion-rule debt — applied 2026-08-17\n\n" + "\n".join(f"- {x}" for x in log) + "\n",
        encoding="utf-8",
    )
    print(f"\nwrote {NODES_PATH}\nwrote {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
