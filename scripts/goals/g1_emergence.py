#!/usr/bin/env python3
"""G1 — Concept-emergence timelines (deterministic, READ-ONLY on the KG).

For a given free-will core *concept* node, collect every neighbor reached via the
attestation relations (``discusses``, ``employs``, ``advanced_in``, ``defines``,
plus the practical synonyms ``evidenced_by`` / ``grounded_in`` that link a concept
to primary passages), bucket those neighbors by chronological *period*, and emit a
dated attestation curve with, for each period, the *earliest grounded passage*
(its ``passage_id``) that attests the concept in that period.

A concept may be fragmented across several duplicate nodes. The optional
``--merge-map`` JSONL (the staged G1 proposal) is honoured: every alias id is
treated as the canonical id, so the curve is computed over the *merged* concept
without mutating ``nodes.jsonl`` / ``edges.jsonl``.

Strictly read-only. No node or edge is ever written.

Grounding contract: every emitted data point carries the ``passage_id`` (or, for a
non-passage neighbor, the neighbor node id + edge relation) that grounds it.

Usage:
    python3 scripts/goals/g1_emergence.py CONCEPT_ID [--merge-map FILE] \
        [--out data/goals/g1/emergence_<name>.json]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"
EDGES_PATH = ROOT / "data" / "kg" / "edges.jsonl"

# Relations that attest a concept (concept <- neighbor, or concept -> passage).
ATTEST_RELATIONS: frozenset[str] = frozenset(
    {"discusses", "employs", "advanced_in", "defines", "evidenced_by", "grounded_in"}
)

# Chronological order of the period buckets used across the KG.
PERIOD_ORDER: tuple[str, ...] = (
    "Presocratic",
    "Classical Greek",
    "Hellenistic",
    "Roman Republican",
    "Roman Imperial",
    "Late Antiquity",
    "Patristic",
    "Medieval",
    "Renaissance",
    "Early Modern",
    "Modern",
    "Contemporary",
)
# Coarse mid-point year per period, used only as a *fallback* sort key when no
# author-derived year is available. Patristic overlaps Roman Imperial / Late
# Antiquity in absolute time; we keep it after Late Antiquity for display but its
# fallback year reflects its real 2nd-5th c. CE span.
PERIOD_FALLBACK_YEAR: dict[str, int] = {
    "Presocratic": -550,
    "Classical Greek": -380,
    "Hellenistic": -250,
    "Roman Republican": -80,
    "Roman Imperial": 150,
    "Late Antiquity": 400,
    "Patristic": 250,
    "Medieval": 1100,
    "Renaissance": 1450,
    "Early Modern": 1650,
    "Modern": 1850,
    "Contemporary": 1980,
}


def _strip(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )


def _norm_author(s: str | None) -> str:
    if not s:
        return ""
    s = _strip(s).lower()
    s = re.sub(r"[^a-z ]", " ", s)
    # drop frequent qualifiers / toponyms that diverge between person & passage labels
    drop = {
        "of", "the", "saint", "st", "pseudo", "ps", "athens", "alexandria",
        "milan", "hippo", "nyssa", "aphrodisias", "stagira", "citium",
        "caesarea", "rome", "carthage", "d", "de", "le", "la",
    }
    toks = [t for t in s.split() if t and t not in drop]
    return " ".join(toks)


def _parse_year(s: Any) -> int | None:
    """Approximate year. For a range ('c. 100-114 CE') take the LOWER bound so
    'earliest attestation' stays conservative; BCE before CE."""
    if not s:
        return None
    s = str(s)
    nums = re.findall(r"\d+", s)
    if not nums:
        return None
    lo = min(int(n) for n in nums)
    if re.search(r"BCE|BC\b", s):
        return -lo
    return lo


def load_nodes() -> dict[str, dict[str, Any]]:
    nodes: dict[str, dict[str, Any]] = {}
    with NODES_PATH.open() as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            n = json.loads(line)
            md = n.get("metadata")
            if isinstance(md, str):
                try:
                    n["_meta"] = json.loads(md)
                except json.JSONDecodeError:
                    n["_meta"] = {}
            elif isinstance(md, dict):
                n["_meta"] = md
            else:
                n["_meta"] = {}
            nodes[n["id"]] = n
    return nodes


def build_author_years(nodes: dict[str, dict[str, Any]]) -> dict[str, int]:
    years: dict[str, int] = {}
    for n in nodes.values():
        if n.get("type") != "person":
            continue
        d = n["_meta"]
        yr = _parse_year(d.get("birth_date") or d.get("floruit") or d.get("dates"))
        if yr is None:
            yr = _parse_year(d.get("death_date"))
        if yr is None:
            continue
        key = _norm_author(n.get("label", ""))
        if key and (key not in years or yr < years[key]):
            years[key] = yr
    return years


def load_merge_map(path: Path | None) -> dict[str, str]:
    """alias_id -> canonical_id, read from the staged merge-proposal JSONL."""
    mapping: dict[str, str] = {}
    if path is None:
        return mapping
    with path.open() as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rec.get("action") == "merge":
                mapping[rec["from"]] = rec["to"]
    return mapping


def passage_year(
    node: dict[str, Any], author_years: dict[str, int]
) -> tuple[int | None, str]:
    """Best-effort absolute year for a passage node, plus the source of the estimate."""
    d = node.get("_meta", {})
    for k in ("date", "source_date", "year"):
        y = _parse_year(d.get(k))
        if y is not None:
            return y, f"passage_meta:{k}"
    author = d.get("author")
    y = author_years.get(_norm_author(author))
    if y is not None:
        return y, f"author:{author}"
    return None, "period_fallback"


def collect(
    concept_id: str, merge_map: dict[str, str]
) -> tuple[set[str], list[dict[str, Any]]]:
    """Return (canonical_ids, attesting_edges) for the merged concept."""
    aliases = {a for a, c in merge_map.items() if c == concept_id}
    canonical = {concept_id} | aliases
    edges: list[dict[str, Any]] = []
    with EDGES_PATH.open() as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            e = json.loads(line)
            if e.get("relation") not in ATTEST_RELATIONS:
                continue
            # Resolve aliases on both endpoints so merged ids collapse.
            src = merge_map.get(e["source"], e["source"])
            tgt = merge_map.get(e["target"], e["target"])
            if src in canonical:
                edges.append({"neighbor": e["target"], "relation": e["relation"],
                              "dir": "out", "edge_meta": e.get("metadata")})
            elif tgt in canonical:
                edges.append({"neighbor": e["source"], "relation": e["relation"],
                              "dir": "in", "edge_meta": e.get("metadata")})
    return canonical, edges


def build_curve(
    concept_id: str,
    nodes: dict[str, dict[str, Any]],
    author_years: dict[str, int],
    merge_map: dict[str, str],
) -> dict[str, Any]:
    canonical, edges = collect(concept_id, merge_map)

    # Group attestations by period. Every attestation records its grounding id.
    by_period: dict[str, list[dict[str, Any]]] = defaultdict(list)
    neighbor_ids: set[str] = set()
    for e in edges:
        nb = nodes.get(e["neighbor"])
        if nb is None:
            continue
        neighbor_ids.add(e["neighbor"])
        period = nb.get("period")
        if period is None:
            period = "Unknown"
        is_passage = nb.get("type") == "passage"
        if is_passage:
            yr, yr_src = passage_year(nb, author_years)
        else:
            yr, yr_src = None, "non_passage_neighbor"
        by_period[period].append(
            {
                "neighbor_id": e["neighbor"],
                "neighbor_type": nb.get("type"),
                "neighbor_label": nb.get("label"),
                "relation": e["relation"],
                "direction": e["dir"],
                "is_passage": is_passage,
                "passage_id": e["neighbor"] if is_passage else None,
                "estimated_year": yr,
                "year_source": yr_src,
                "edge_meta": e["edge_meta"],
            }
        )

    # For each period, pick the earliest *grounded passage* (passage neighbor).
    # Sort key: known year, else the period fallback year (keeps determinism).
    curve: list[dict[str, Any]] = []
    for period in sorted(
        by_period,
        key=lambda p: (PERIOD_ORDER.index(p) if p in PERIOD_ORDER else 999, p),
    ):
        items = by_period[period]
        passages = [it for it in items if it["is_passage"]]

        def sort_key(it: dict[str, Any]) -> tuple[int, str]:
            y = it["estimated_year"]
            if y is None:
                y = PERIOD_FALLBACK_YEAR.get(period, 9999)
            return (y, it["neighbor_id"])

        earliest_passage = min(passages, key=sort_key) if passages else None
        curve.append(
            {
                "period": period,
                "n_attestations": len(items),
                "n_passages": len(passages),
                "n_nonpassage": len(items) - len(passages),
                "earliest_grounded_passage": (
                    {
                        "passage_id": earliest_passage["passage_id"],
                        "label": earliest_passage["neighbor_label"],
                        "relation": earliest_passage["relation"],
                        "estimated_year": earliest_passage["estimated_year"],
                        "year_source": earliest_passage["year_source"],
                        "edge_meta": earliest_passage["edge_meta"],
                    }
                    if earliest_passage
                    else None
                ),
                "all_passage_ids": sorted(
                    it["passage_id"] for it in passages
                ),
                "nonpassage_neighbors": sorted(
                    {it["neighbor_id"] for it in items if not it["is_passage"]}
                ),
            }
        )

    return {
        "concept_id": concept_id,
        "canonical_label": nodes.get(concept_id, {}).get("label"),
        "merged_alias_ids": sorted(canonical - {concept_id}),
        "relations_used": sorted(ATTEST_RELATIONS),
        "total_attestations": sum(len(v) for v in by_period.values()),
        "total_distinct_neighbors": len(neighbor_ids),
        "periods": curve,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("concept_id")
    ap.add_argument("--merge-map", type=Path, default=None)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    nodes = load_nodes()
    if args.concept_id not in nodes:
        print(f"ERROR: concept id not found: {args.concept_id}", file=sys.stderr)
        return 2
    author_years = build_author_years(nodes)
    merge_map = load_merge_map(args.merge_map)
    result = build_curve(args.concept_id, nodes, author_years, merge_map)

    out = args.out or (
        ROOT / "data" / "goals" / "g1" / f"emergence_{args.concept_id}.json"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2))

    print(f"{result['concept_id']}  ({result['canonical_label']})")
    print(
        f"  {result['total_attestations']} attestations / "
        f"{result['total_distinct_neighbors']} neighbors / "
        f"{len(result['periods'])} periods"
    )
    for p in result["periods"]:
        eg = p["earliest_grounded_passage"]
        ground = eg["passage_id"] if eg else "(no passage — non-passage attestation only)"
        yr = eg["estimated_year"] if eg else None
        print(
            f"    {p['period']:<18} n={p['n_attestations']:>3} "
            f"(pass={p['n_passages']:>2}) earliest={ground} year={yr}"
        )
    print(f"  -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
