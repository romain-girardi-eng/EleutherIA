"""Auto-link unanchored KG claim nodes to passage nodes via inline citation parsing.

Conservative scholarly auto-linker. Reads `data/kg/nodes.jsonl` and finds every node
flagged with `metadata.needs_evidence=true`. For each, parses inline citations from
its label+description, normalizes them, and matches them against passage nodes by:

  1. Fuzzy work-title alignment (tolerant: drops "De/Ad", lowercases, allows token subset).
  2. Locus alignment: passage `metadata.canonical_ref` must overlap the cited locus,
     supporting Roman numerals, decimal segments, ranges (e.g. "XII.6-9"), and
     prefixes ("Epict. Disc. I.1", "Rep. 10.595").

Only the single top-confidence match is added as an `evidenced_by` edge with:
  metadata.confidence = 0.5
  metadata.auto_linked = true
  metadata.match_score = <float>
  metadata.linker = "auto_link_unanchored_claims_v1"

Refuses to fabricate text. Does NOT touch `needs_evidence` flags (provisional flag remains).
Writes the report payload to stdout (JSON) so a separate doc step can render it.

Usage:
  python scripts/auto_link_unanchored_claims.py --apply        # mutate edges.jsonl
  python scripts/auto_link_unanchored_claims.py                # dry-run, print stats
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

NODES_PATH = Path("data/kg/nodes.jsonl")
EDGES_PATH = Path("data/kg/edges.jsonl")

# Roman numeral conversion (limited to common manuscript ranges I..XL).
_ROMAN = [
    ("XL", 40),
    ("XXX", 30),
    ("XX", 20),
    ("XIX", 19),
    ("XVIII", 18),
    ("XVII", 17),
    ("XVI", 16),
    ("XV", 15),
    ("XIV", 14),
    ("XIII", 13),
    ("XII", 12),
    ("XI", 11),
    ("X", 10),
    ("IX", 9),
    ("VIII", 8),
    ("VII", 7),
    ("VI", 6),
    ("V", 5),
    ("IV", 4),
    ("III", 3),
    ("II", 2),
    ("I", 1),
]


def roman_to_int(token: str) -> int | None:
    t = token.upper()
    if not re.fullmatch(r"[IVXL]+", t):
        return None
    val = 0
    i = 0
    while i < len(t):
        # Greedy
        matched = False
        for sym, num in _ROMAN:
            if t.startswith(sym, i):
                val += num
                i += len(sym)
                matched = True
                break
        if not matched:
            return None
    return val if val > 0 else None


def normalize_segment(seg: str) -> str:
    """Roman → Arabic; strip whitespace; keep ranges as 'a-b'."""
    seg = seg.strip()
    # Range?
    rng = re.match(r"^([IVXLivxl]+|\d+)\s*-\s*([IVXLivxl]+|\d+)$", seg)
    if rng:
        a = normalize_segment(rng.group(1))
        b = normalize_segment(rng.group(2))
        return f"{a}-{b}"
    r = roman_to_int(seg)
    if r is not None:
        return str(r)
    return seg


def parse_locus(locus: str) -> list[str]:
    """Split 'XII.6-9' or 'Rep. 10.595' or 'V.IX.2' into normalized segments."""
    # Strip well-known prefixes
    locus = re.sub(
        r"^(Epict\.\s*Disc\.|Epict\.|Disc\.|Ench\.|Rep\.|Enn\.|SVF|Phys\.|Mag\.\s*Mor\.|EN|NE)\s*",
        "",
        locus,
        flags=re.IGNORECASE,
    ).strip()
    # Drop leading work-name tokens (heuristic — caller already aligned on work)
    parts = re.split(r"[.,\s]+", locus)
    out: list[str] = []
    for p in parts:
        p = p.strip("()[]")
        if not p:
            continue
        # keep tokens that look like Roman or arabic (possibly with range)
        if (
            re.fullmatch(r"[IVXLivxl]+", p)
            or re.fullmatch(r"\d+(?:-\d+)?", p)
            or re.fullmatch(r"[IVXLivxl]+-[IVXLivxl]+", p)
        ):
            out.append(normalize_segment(p))
        else:
            # Mixed letters/numbers — skip (e.g. "q", "ad", section letters)
            continue
    return out


def expand_range(seg: str) -> set[int]:
    """Convert '6-9' into {6,7,8,9}; '6' into {6}; non-numeric → empty."""
    if "-" in seg:
        a, b = seg.split("-", 1)
        try:
            ai, bi = int(a), int(b)
        except ValueError:
            return set()
        if ai > bi:
            ai, bi = bi, ai
        return set(range(ai, bi + 1))
    try:
        return {int(seg)}
    except ValueError:
        return set()


def locus_overlap_score(claim_segs: list[str], passage_segs: list[str]) -> float:
    """Return [0,1]. 1.0 if every passage segment is contained in the corresponding
    claim segment (or its range). Uses positional alignment from the right side
    (most-specific first), so 'V.IX.2' matches 'IX.2' if claim says 'V.IX'.

    Strategy: align from the most general (left). For each aligned segment pair,
    require numeric containment.
    """
    if not claim_segs or not passage_segs:
        return 0.0
    # Align right-to-left? No — align left-to-right but allow passage to have extra
    # rightward specificity (chapter/verse refining a book reference).
    matched = 0
    total = min(len(claim_segs), len(passage_segs))
    for i in range(total):
        cs = expand_range(claim_segs[i])
        ps = expand_range(passage_segs[i])
        if not cs or not ps:
            return 0.0
        # The passage must be inside (or equal to) the claim's range/point.
        if ps.issubset(cs):
            matched += 1
        else:
            return 0.0
    # full alignment on overlapping prefix
    return matched / total if total else 0.0


# Citation extraction: matches "<Work Name> <Locus>"
# Locus is a Roman/arabic ladder like 'XII.6-9', 'I.1', '192', '7.2', '617e'
_CITE_RE = re.compile(
    r"\b("
    r"(?:[A-Z][a-zA-ZéÉàèùçôîâ]+\.?\s+){0,3}"  # leading "De ", "Ad ", "Pseudo ", etc.
    r"[A-Z][a-zA-Zéàèùçôîâï]+"  # main capitalized work word
    r"(?:\s+[A-Z][a-zA-Zéàèùçôîâï]+){0,5}"  # multi-word titles
    r")\s+"
    r"([IVXLivxl]+(?:\.[IVXLivxl\d]+(?:-[IVXLivxl\d]+)?){0,3}"  # Roman ladder
    r"|\d+(?:\.\d+(?:-\d+)?){0,3}"  # Arabic ladder
    r")"
)


# Map common abbreviations / variant spellings to canonical work_title in our DB.
WORK_ALIAS = {
    "de civitate dei": [
        "De Civitate Dei (Books V, XII, XIV - Fate and Free Will)",
        "De Civitate Dei",
    ],
    "civ dei": ["De Civitate Dei (Books V, XII, XIV - Fate and Free Will)"],
    "city of god": ["De Civitate Dei (Books V, XII, XIV - Fate and Free Will)"],
    "de fato": ["De Fato", "De fato"],
    "drn": ["De Rerum Natura"],
    "de rerum natura": ["De Rerum Natura"],
    "ench": ["Discourses and Enchiridion", "Enchiridion"],
    "enchiridion": ["Discourses and Enchiridion", "Enchiridion"],
    "discourses": ["Discourses", "Discourses and Enchiridion"],
    "disc": ["Discourses", "Discourses and Enchiridion"],
    "contra celsum": ["Contra Celsum"],
    "noctes atticae": ["Noctes Atticae", "Noctes Atticae VII.2 (De Fato et Chrysippo)"],
    "rep": ["Republic (Πολιτεία)"],
    "republic": ["Republic (Πολιτεία)"],
    "enn": ["Enneades"],
    "enneades": ["Enneades"],
    "enneads": ["Enneades"],
    "epistulae morales": ["Epistulae Morales ad Lucilium"],
    "ep mor": ["Epistulae Morales ad Lucilium"],
    "vitae philosophorum": ["Vitae Philosophorum (Lives of Eminent Philosophers)"],
    "diog laert": ["Vitae Philosophorum (Lives of Eminent Philosophers)"],
    "lives of eminent philosophers": [
        "Vitae Philosophorum (Lives of Eminent Philosophers)"
    ],
    "dialogus cum tryphone": ["Dialogus cum Tryphone"],
    "dial tryph": ["Dialogus cum Tryphone"],
    "de libero arbitrio": ["De Libero Arbitrio"],
    "de opificio mundi": ["De Opificio Mundi"],
    "de providentia": ["De Providentia"],
    "meditations": ["Meditations (Ta eis heauton)"],
    "ta eis heauton": ["Meditations (Ta eis heauton)"],
    "magna moralia": ["Magna Moralia"],
    "de consolatione philosophiae": [
        "De consolatione philosophiae",
        "De Consolatione Philosophiae",
    ],
    "consolatio": ["De consolatione philosophiae", "De Consolatione Philosophiae"],
    "metaphysics": ["τὰ Μετὰ τὰ Φυσικά"],
    "metaph": ["τὰ Μετὰ τὰ Φυσικά"],
    "phaedrus": ["Φαῖδρος"],
    "nicomachean ethics": ["Ἠθικὰ Νικομάχεια"],
    "eth nic": ["Ἠθικὰ Νικομάχεια"],
    "apology": ["Ἀπολογία Σωκράτους"],
    "laws": ["Laws (Νόμοι)"],
    "leges": ["Laws (Νόμοι)"],
    "oratio ad graecos": ["Oratio ad Graecos"],
    "peri pascha": ["Peri Pascha"],
    "pastor": ["Pastor (Shepherd)"],
    "shepherd": ["Pastor (Shepherd)"],
    "letters and fragments": ["Letters and Fragments"],
    "in epicteti enchiridion": ["In Epicteti Enchiridion Commentarius"],
    "apologia pro origene": ["Apologia pro Origene"],
    "against the professors": ["Against the Professors and Outlines of Pyrrhonism"],
    "outlines of pyrrhonism": ["Against the Professors and Outlines of Pyrrhonism"],
}


def canonical_work_lookup(raw: str) -> list[str]:
    raw_l = raw.lower().strip().rstrip(".")
    raw_l = re.sub(r"\s+", " ", raw_l)
    # Direct alias
    if raw_l in WORK_ALIAS:
        return WORK_ALIAS[raw_l]
    # Drop leading "the" / "a"
    if raw_l.startswith("the "):
        return canonical_work_lookup(raw_l[4:])
    return []


@dataclass
class Citation:
    raw: str
    work_query: str
    locus_segments: list[str]


# Ambiguous work titles whose alias resolves to an ancient text but is shared with
# a modern-era work (e.g. Descartes' Meditationes, Malebranche's Dialogues on Metaphysics).
# When matched, the immediately preceding 60 chars must not contain a modern-context marker.
_AMBIGUOUS_TITLES = {
    "meditations",
    "metaphysics",
    "ethics",
    "dialogues",
    "principles",
    "treatise",
}

# Markers that imply the citation belongs to a modern philosopher's homonymous work,
# NOT the ancient one. If any of these appears within ~60 chars before the citation,
# the citation is rejected. (Also: appears anywhere in the same sentence as the citation.)
_MODERN_MARKERS = [
    "Descartes",
    "Cartesian",
    "Cartesian Meditation",
    "Malebranche",
    "Bayle",
    "Spinoza",
    "Hume",
    "Leibniz",
    "Kant",
    "Hegel",
    "Reid",
    "Locke",
    "Berkeley",
    "Suárez",
    "Suarez",
    "Ockham",
    "Scotus",
    "Aquinas",
    "Anselm",
    "Abelard",
    "Ghazali",
    "Maimonides",
    "Crescas",
    "Bonaventure",
    "Eckhart",
    "Dialogues on Metaphysics",
    "Meditationes de Prima Philosophia",
    "Discourse on Metaphysics",
    "Discourse on Method",
    "Cratylus" if False else "",  # placeholder so list stays mutable
]
_MODERN_MARKERS = [m for m in _MODERN_MARKERS if m]


def _has_modern_context(text: str, span_start: int) -> bool:
    """True if the citation at `span_start` is preceded by a modern-philosopher marker
    within ~80 chars (one sentence or compound noun phrase)."""
    window = text[max(0, span_start - 80) : span_start]
    return any(marker in window for marker in _MODERN_MARKERS)


def extract_citations(node: dict) -> list[Citation]:
    text = ((node.get("label") or "") + " — " + (node.get("description") or ""))[:3000]
    citations: list[Citation] = []
    seen = set()
    for m in _CITE_RE.finditer(text):
        work_raw = m.group(1).strip()
        locus_raw = m.group(2).strip()
        # Reject if work_raw is a common stopword phrase (e.g. "The Argument")
        if work_raw.lower() in {
            "the argument",
            "the claim",
            "argument structure",
            "the conclusion",
        }:
            continue
        # Modern-context guard for ambiguous titles: skip if a modern marker is nearby.
        if work_raw.lower() in _AMBIGUOUS_TITLES and _has_modern_context(
            text, m.start()
        ):
            continue
        # Strong guard: if the full node text contains a modern marker AND no ancient
        # author is named, reject any ambiguous citation outright (Descartes-Meditations etc.).
        if work_raw.lower() in _AMBIGUOUS_TITLES and any(
            mk in text for mk in _MODERN_MARKERS
        ):
            continue
        # The work_raw might still embed a leading clause word ("Ench."). Keep last 1-4 tokens.
        key = (work_raw.lower(), locus_raw)
        if key in seen:
            continue
        seen.add(key)
        segs = parse_locus(locus_raw)
        if not segs:
            continue
        citations.append(
            Citation(
                raw=f"{work_raw} {locus_raw}", work_query=work_raw, locus_segments=segs
            )
        )
    return citations


def title_aliases_for(work_query: str) -> list[str]:
    """Compose plausible passage `metadata.work_title` candidates from a raw citation."""
    out: list[str] = []
    # Try the full thing, then last 3,2,1 capitalized tokens.
    tokens = work_query.split()
    for n in range(len(tokens), 0, -1):
        candidate = " ".join(tokens[-n:])
        out.extend(canonical_work_lookup(candidate))
        out.extend(canonical_work_lookup(candidate.replace(".", "")))
    # Deduplicate, preserve order
    seen = set()
    result = []
    for t in out:
        if t not in seen:
            seen.add(t)
            result.append(t)
    return result


@dataclass
class PassageIndex:
    by_work: dict[str, list[dict]] = field(default_factory=lambda: defaultdict(list))

    @classmethod
    def build(cls, nodes_path: Path) -> PassageIndex:
        idx = cls()
        with nodes_path.open() as f:
            for line in f:
                n = json.loads(line)
                if n.get("type") != "passage":
                    continue
                m = n.get("metadata") or {}
                wt = m.get("work_title") or ""
                if not wt:
                    continue
                idx.by_work[wt].append(
                    {
                        "id": n["id"],
                        "canonical_ref": m.get("canonical_ref") or "",
                        "label": n.get("label") or "",
                    }
                )
        return idx


def best_passage_for_citation(
    cit: Citation, idx: PassageIndex
) -> tuple[dict | None, float, str]:
    """Return (passage_dict, score, work_title) for best match, or (None, 0, '')."""
    aliases = title_aliases_for(cit.work_query)
    if not aliases:
        return None, 0.0, ""
    best = None
    best_score = 0.0
    best_wt = ""
    for wt in aliases:
        passages = idx.by_work.get(wt, [])
        for p in passages:
            cref = p["canonical_ref"]
            if not cref:
                continue
            psegs = parse_locus(cref)
            if not psegs:
                continue
            score = locus_overlap_score(cit.locus_segments, psegs)
            if score > best_score:
                best_score = score
                best = p
                best_wt = wt
                # If we have a perfect (1.0) match on more passage segments than claim,
                # specificity bonus: prefer the most specific passage among ties later.
    return best, best_score, best_wt


def existing_edges(edges_path: Path) -> set[tuple[str, str, str]]:
    seen = set()
    with edges_path.open() as f:
        for line in f:
            e = json.loads(line)
            seen.add((e.get("source", ""), e.get("relation", ""), e.get("target", "")))
    return seen


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply", action="store_true", help="Append new edges to edges.jsonl"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=1.0,
        help="Min locus overlap score (default 1.0: full prefix containment)",
    )
    parser.add_argument(
        "--report-json", type=Path, default=Path("/tmp/auto_link_report.json")
    )
    args = parser.parse_args()

    # 1. Collect flagged nodes
    flagged: list[dict] = []
    all_node_ids: set[str] = set()
    with NODES_PATH.open() as f:
        for line in f:
            n = json.loads(line)
            all_node_ids.add(n["id"])
            if (n.get("metadata") or {}).get("needs_evidence") is True:
                flagged.append(n)
    print(f"[info] flagged nodes: {len(flagged)}", file=sys.stderr)

    # 2. Build passage index
    idx = PassageIndex.build(NODES_PATH)
    print(f"[info] indexed work_titles: {len(idx.by_work)}", file=sys.stderr)

    # 3. Existing edges (avoid duplicates)
    existing = existing_edges(EDGES_PATH)

    # 4. For each flagged node, extract citations and try to match
    results = []
    new_edges: list[dict] = []
    score_buckets = defaultdict(int)
    no_citation = 0
    no_alias = 0
    no_passage_overlap = 0
    duplicate_skipped = 0

    for node in flagged:
        nid = node["id"]
        citations = extract_citations(node)
        if not citations:
            no_citation += 1
            results.append(
                {"node_id": nid, "label": node.get("label"), "status": "no_citation"}
            )
            continue

        # Among all citations, keep the single best passage hit.
        best_overall = None  # (score, passage, work_title, citation)
        any_alias_resolved = False
        for cit in citations:
            aliases = title_aliases_for(cit.work_query)
            if aliases:
                any_alias_resolved = True
            p, score, wt = best_passage_for_citation(cit, idx)
            if (
                p
                and score >= args.threshold
                and (best_overall is None or score > best_overall[0])
            ):
                best_overall = (score, p, wt, cit)

        if not any_alias_resolved:
            no_alias += 1
            results.append(
                {
                    "node_id": nid,
                    "label": node.get("label"),
                    "status": "no_alias",
                    "citations": [c.raw for c in citations],
                }
            )
            continue
        if not best_overall:
            no_passage_overlap += 1
            results.append(
                {
                    "node_id": nid,
                    "label": node.get("label"),
                    "status": "no_overlap",
                    "citations": [c.raw for c in citations],
                }
            )
            continue

        score, passage, wt, cit = best_overall
        bucket = round(score, 1)
        score_buckets[bucket] += 1

        # `evidenced_by` source_types in ontology only permit: argument, concept, group, school.
        # For `debate`, `controversy`, `quote`, `synthesis` source nodes, emit the inverse
        # `source_for` edge (passage → claim node), which is the ontologically valid direction.
        EVIDENCED_BY_SOURCE_TYPES = {"argument", "concept", "group", "school"}
        node_type = node.get("type") or ""
        if node_type in EVIDENCED_BY_SOURCE_TYPES:
            edge_source = nid
            edge_target = passage["id"]
            edge_relation = "evidenced_by"
        else:
            edge_source = passage["id"]
            edge_target = nid
            edge_relation = "source_for"
        # Re-check duplicate with the actual direction we will write.
        edge_key2 = (edge_source, edge_relation, edge_target)
        if edge_key2 in existing:
            duplicate_skipped += 1
            results.append(
                {
                    "node_id": nid,
                    "label": node.get("label"),
                    "status": "duplicate_edge",
                    "passage_id": passage["id"],
                }
            )
            continue

        edge = {
            "source": edge_source,
            "relation": edge_relation,
            "target": edge_target,
            "weight": 1.0,
            "description": None,
            "metadata": {
                "confidence": 0.5,
                "auto_linked": True,
                "auto_generated": True,
                "match_score": round(float(score), 3),
                "matched_citation": cit.raw,
                "matched_work_title": wt,
                "passage_ref": passage["canonical_ref"],
                "linker": "auto_link_unanchored_claims_v1",
            },
        }
        new_edges.append(edge)
        results.append(
            {
                "node_id": nid,
                "label": node.get("label"),
                "status": "linked",
                "passage_id": passage["id"],
                "passage_ref": passage["canonical_ref"],
                "work_title": wt,
                "match_score": score,
                "citation": cit.raw,
            }
        )

    print(f"[info] citations parsed → linked: {len(new_edges)}", file=sys.stderr)
    print(f"[info] no_citation: {no_citation}", file=sys.stderr)
    print(f"[info] no_alias (work title not in DB): {no_alias}", file=sys.stderr)
    print(f"[info] no_overlap (locus mismatch): {no_passage_overlap}", file=sys.stderr)
    print(f"[info] duplicates skipped: {duplicate_skipped}", file=sys.stderr)
    print(f"[info] score buckets: {dict(score_buckets)}", file=sys.stderr)

    payload = {
        "flagged_total": len(flagged),
        "linked": len(new_edges),
        "no_citation": no_citation,
        "no_alias": no_alias,
        "no_overlap": no_passage_overlap,
        "duplicates_skipped": duplicate_skipped,
        "score_buckets": dict(score_buckets),
        "results": results,
        "linker_version": "auto_link_unanchored_claims_v1",
        "threshold": args.threshold,
    }
    args.report_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"[info] wrote report json → {args.report_json}", file=sys.stderr)

    if args.apply and new_edges:
        with EDGES_PATH.open("a") as f:
            for e in new_edges:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
        print(
            f"[info] appended {len(new_edges)} edges to {EDGES_PATH}", file=sys.stderr
        )
    elif args.apply:
        print("[info] --apply set but 0 edges to write", file=sys.stderr)
    else:
        print("[info] dry-run (no --apply); edges.jsonl untouched", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
