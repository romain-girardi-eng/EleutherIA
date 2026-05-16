#!/usr/bin/env python3
"""Amand → Stoic provenance analyzer (deterministic, read-only).

For each of Amand 1945's six moral anti-fatalist pivots, score the plausibility
of a primary Stoic source (Chrysippus, Cleanthes, Posidonius, Panaetius) using
three cumulative tests:

  1. thematic   — keyword overlap on labels + descriptions (uses ``PIVOT_THEMES``)
  2. conceptual — shared ``concept_*`` nodes via 1-hop edge traversal
  3. textual    — Greek-lemma overlap on the Stoic's authored passages, with
                  Unicode-NFD diacritic stripping (uses ``PIVOT_GREEK_TERMS``)

Output:
  - 6×4 PairScore matrix as JSON (default:
    ``docs/papers/2026-05-amand-piste1-data/provenance-matrix-6x4.json``)
  - 24-line console summary (one row per (pivot, Stoic) pair)

The analyzer is strictly read-only on the KG. No edges or nodes are added.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import unicodedata
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "knowledge graph" / "src"))

NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"
EDGES_PATH = ROOT / "data" / "kg" / "edges.jsonl"
DEFAULT_OUT = ROOT / "docs" / "papers" / "2026-05-amand-piste1-data" / "provenance-matrix-6x4.json"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Canonical constants — frozen for reproducibility of the matrix
# ---------------------------------------------------------------------------

AMAND_MORAL_PIVOTS: tuple[str, ...] = (
    "argument_carneadean_general_theme_amand1945",
    "argument_carneadean_legislation_amand1945",
    "argument_carneadean_virtue_vice_amand1945",
    "argument_carneadean_incentives_amand1945",
    "argument_carneadean_action_futility_amand1945",
    "argument_carneadean_piety_amand1945",
)

STOIC_PRIMARY: tuple[str, ...] = (
    "person_chrysippus_280_206bce_i9j0k1l2",
    "person_cleanthes_assos_330_230bce",
    "person_posidonius_apameia_135_51bce",
    "person_panaetius_rhodes_185_109bce",
)

PIVOT_THEMES: dict[str, set[str]] = {
    "argument_carneadean_general_theme_amand1945": {
        "fatalism", "destiny", "εἱμαρμένη", "heimarmene", "responsibility", "necessity",
    },
    "argument_carneadean_legislation_amand1945": {
        "law", "νόμος", "nomos", "punishment", "legislation", "court", "judgment",
    },
    "argument_carneadean_virtue_vice_amand1945": {
        "virtue", "vice", "praise", "blame", "ἔπαινος", "ψόγος", "epainos", "psogos",
        "responsibility", "moral",
    },
    "argument_carneadean_incentives_amand1945": {
        "exhortation", "correction", "teaching", "νουθεσία", "παραίνεσις",
        "advice", "instruction",
    },
    "argument_carneadean_action_futility_amand1945": {
        "action", "effort", "ἀργία", "argia", "indolence", "laziness", "futility",
    },
    "argument_carneadean_piety_amand1945": {
        "piety", "εὐσέβεια", "eusebeia", "religion", "gods", "divine",
    },
}

PIVOT_GREEK_TERMS: dict[str, set[str]] = {
    "argument_carneadean_general_theme_amand1945": {"ειμαρμενη", "αναγκη", "πεπρωμενη"},
    "argument_carneadean_legislation_amand1945": {"νομος", "νομοι"},
    "argument_carneadean_virtue_vice_amand1945": {"αρετη", "κακια", "επαινος", "ψογος"},
    "argument_carneadean_incentives_amand1945": {"νουθεσια", "παραινεσις", "διδασκαλια"},
    "argument_carneadean_action_futility_amand1945": {"αργια", "ραθυμια"},
    "argument_carneadean_piety_amand1945": {"ευσεβεια", "θεοι"},
}


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class PairScore:
    pivot: str
    stoic: str
    thematic_hits: list[str] = field(default_factory=list)
    conceptual_hits: list[str] = field(default_factory=list)
    textual_hits: list[str] = field(default_factory=list)

    @property
    def total_score(self) -> int:
        return (
            (1 if self.thematic_hits else 0)
            + (1 if self.conceptual_hits else 0)
            + (1 if self.textual_hits else 0)
        )

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["total_score"] = self.total_score
        return d


# ---------------------------------------------------------------------------
# KG loading helpers (read-only; cached at module level for speed)
# ---------------------------------------------------------------------------

_NODES_CACHE: dict[str, dict[str, Any]] | None = None
_EDGES_CACHE: list[dict[str, Any]] | None = None


def _node_id(node: dict[str, Any]) -> str:
    nid = node.get("id") or node.get("node_id")
    if not isinstance(nid, str):
        raise ValueError(f"node has no string id: {node!r}")
    return nid


def load_nodes() -> dict[str, dict[str, Any]]:
    global _NODES_CACHE
    if _NODES_CACHE is None:
        cache: dict[str, dict[str, Any]] = {}
        with NODES_PATH.open() as f:
            for line in f:
                if not line.strip():
                    continue
                n = json.loads(line)
                cache[_node_id(n)] = n
        _NODES_CACHE = cache
        logger.info("loaded %d nodes from %s", len(cache), NODES_PATH)
    return _NODES_CACHE


def load_edges() -> list[dict[str, Any]]:
    global _EDGES_CACHE
    if _EDGES_CACHE is None:
        edges: list[dict[str, Any]] = []
        with EDGES_PATH.open() as f:
            for line in f:
                if not line.strip():
                    continue
                edges.append(json.loads(line))
        _EDGES_CACHE = edges
        logger.info("loaded %d edges from %s", len(edges), EDGES_PATH)
    return _EDGES_CACHE


# ---------------------------------------------------------------------------
# Test 1: thematic — keyword index over Stoic-authored corpus
# ---------------------------------------------------------------------------

def _authored_items(stoic_person: str) -> set[str]:
    """All node IDs ``authored_by`` the given person (passages, works, args)."""
    out: set[str] = set()
    for e in load_edges():
        if e.get("relation") == "authored_by" and e.get("target") == stoic_person:
            src = e.get("source")
            if isinstance(src, str):
                out.add(src)
    return out


def _node_text(node: dict[str, Any]) -> str:
    """Concatenated label + description for keyword scanning."""
    parts = [node.get("label") or "", node.get("description") or ""]
    return " ".join(p for p in parts if p)


def build_keyword_index() -> dict[str, dict[str, list[str]]]:
    """For each Stoic person, return ``{keyword: [node_ids mentioning it]}``.

    Scans labels + descriptions of (a) the person node itself and (b) every
    node authored by that person, using the union of all keywords declared in
    ``PIVOT_THEMES``. Case-insensitive ASCII match; Greek strings are matched
    as-is (with original diacritics) since pivot themes already use precise
    polytonic forms.
    """
    nodes = load_nodes()
    all_keywords: set[str] = set()
    for themes in PIVOT_THEMES.values():
        all_keywords |= themes

    index: dict[str, dict[str, list[str]]] = {}
    for stoic in STOIC_PRIMARY:
        kw_to_nodes: dict[str, list[str]] = defaultdict(list)
        scan_ids: set[str] = {stoic} | _authored_items(stoic)
        for nid in scan_ids:
            node = nodes.get(nid)
            if node is None:
                continue
            text = _node_text(node)
            lowered = text.lower()
            for kw in all_keywords:
                # Greek keywords contain non-ASCII → match on raw text.
                # ASCII keywords → match on lowered.
                if any(ord(c) > 127 for c in kw):
                    if kw in text:
                        kw_to_nodes[kw].append(nid)
                else:
                    if kw.lower() in lowered:
                        kw_to_nodes[kw].append(nid)
        index[stoic] = dict(kw_to_nodes)
    return index


def thematic_test(
    pivot: str,
    stoic_person: str,
    index: dict[str, dict[str, list[str]]],
) -> PairScore:
    score = PairScore(pivot=pivot, stoic=stoic_person)
    pivot_themes = PIVOT_THEMES.get(pivot, set())
    stoic_kw = index.get(stoic_person, {})
    for kw in sorted(pivot_themes):
        if stoic_kw.get(kw):
            score.thematic_hits.append(kw)
    return score


# ---------------------------------------------------------------------------
# Test 2: conceptual — shared concept_* via 1-hop traversal
# ---------------------------------------------------------------------------

# Edges that semantically link an entity to a concept it "engages with".
_CONCEPT_EDGE_RELATIONS: frozenset[str] = frozenset({
    "discusses", "creates", "extends", "employs", "developed_by",
    "interprets", "critiques", "supports", "responds_to",
    "evidenced_by", "cites_primary_source",
})


def build_concept_index() -> dict[str, set[str]]:
    """For each entity (Stoic person + pivot + every node), return concepts it touches.

    Walks 1-hop from each entity over ``_CONCEPT_EDGE_RELATIONS`` in either
    direction, collecting ``concept_*`` neighbors. For Stoic persons we also
    include concepts touched by anything they authored.
    """
    nodes = load_nodes()
    edges = load_edges()

    # Per-node concept set via direct 1-hop edges in either direction.
    per_node: dict[str, set[str]] = defaultdict(set)
    for e in edges:
        rel = e.get("relation")
        if rel not in _CONCEPT_EDGE_RELATIONS:
            continue
        src = e.get("source")
        tgt = e.get("target")
        if isinstance(src, str) and isinstance(tgt, str):
            if tgt.startswith("concept_") and src in nodes:
                per_node[src].add(tgt)
            if src.startswith("concept_") and tgt in nodes:
                per_node[tgt].add(src)

    # For Stoic persons, also aggregate concepts of every authored item.
    for stoic in STOIC_PRIMARY:
        agg = set(per_node.get(stoic, set()))
        for item in _authored_items(stoic):
            agg |= per_node.get(item, set())
        per_node[stoic] = agg

    return dict(per_node)


def conceptual_test(
    pivot: str,
    stoic_person: str,
    concepts: dict[str, set[str]],
) -> PairScore:
    score = PairScore(pivot=pivot, stoic=stoic_person)
    pivot_concepts = concepts.get(pivot, set())
    stoic_concepts = concepts.get(stoic_person, set())
    score.conceptual_hits = sorted(pivot_concepts & stoic_concepts)
    return score


# ---------------------------------------------------------------------------
# Test 3: textual — Greek lemma overlap on the Stoic's passages
# ---------------------------------------------------------------------------

def normalize_greek(text: str) -> str:
    """NFD-decompose, strip Mn combining marks (diacritics), lowercase.

    Idempotent and ASCII-safe (Latin passes through after lowercasing).
    """
    if not text:
        return ""
    decomposed = unicodedata.normalize("NFD", text)
    stripped = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    return stripped.lower()


def passages_for_person(person_id: str) -> list[dict[str, Any]]:
    """All passage nodes authored_by the given person.

    A node is treated as a passage if its id starts with ``passage_`` or its
    type field is ``passage``.
    """
    nodes = load_nodes()
    authored = _authored_items(person_id)
    out: list[dict[str, Any]] = []
    for nid in sorted(authored):
        n = nodes.get(nid)
        if n is None:
            continue
        if nid.startswith("passage_") or n.get("type") == "passage":
            out.append(n)
    return out


def textual_test(pivot: str, stoic_person: str) -> PairScore:
    score = PairScore(pivot=pivot, stoic=stoic_person)
    targets = {normalize_greek(t) for t in PIVOT_GREEK_TERMS.get(pivot, set())}
    if not targets:
        return score
    hits: set[str] = set()
    for passage in passages_for_person(stoic_person):
        body = normalize_greek(_node_text(passage))
        if not body:
            continue
        for term in targets:
            if term and term in body:
                hits.add(term)
    score.textual_hits = sorted(hits)
    return score


# ---------------------------------------------------------------------------
# Matrix + IO
# ---------------------------------------------------------------------------

def compute_matrix() -> list[list[PairScore]]:
    """Compute the full 6×4 matrix of PairScore objects.

    Rows = Amand pivots (order of ``AMAND_MORAL_PIVOTS``)
    Cols = Stoic philosophers (order of ``STOIC_PRIMARY``)
    """
    kw_index = build_keyword_index()
    concept_index = build_concept_index()
    matrix: list[list[PairScore]] = []
    for pivot in AMAND_MORAL_PIVOTS:
        row: list[PairScore] = []
        for stoic in STOIC_PRIMARY:
            t = thematic_test(pivot, stoic, kw_index)
            c = conceptual_test(pivot, stoic, concept_index)
            x = textual_test(pivot, stoic)
            merged = PairScore(
                pivot=pivot,
                stoic=stoic,
                thematic_hits=t.thematic_hits,
                conceptual_hits=c.conceptual_hits,
                textual_hits=x.textual_hits,
            )
            row.append(merged)
        matrix.append(row)
    return matrix


def dump_matrix(matrix: list[list[PairScore]], path: Path) -> None:
    """Serialize the matrix to JSON.

    Schema:
      {
        "generated_at": str (UTC ISO-8601),
        "amand_pivots": [...],
        "stoic_primary": [...],
        "matrix": [[PairScore.to_dict(), ...], ...]   # 6 × 4
      }
    """
    from datetime import UTC, datetime
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "amand_pivots": list(AMAND_MORAL_PIVOTS),
        "stoic_primary": list(STOIC_PRIMARY),
        "matrix": [[cell.to_dict() for cell in row] for row in matrix],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

_SHORT_NAMES = {
    "person_chrysippus_280_206bce_i9j0k1l2": "Chrysippus",
    "person_cleanthes_assos_330_230bce": "Cleanthes",
    "person_posidonius_apameia_135_51bce": "Posidonius",
    "person_panaetius_rhodes_185_109bce": "Panaetius",
}

_PIVOT_ROMAN = {
    "argument_carneadean_general_theme_amand1945": "I (general theme)",
    "argument_carneadean_legislation_amand1945": "II (legislation)",
    "argument_carneadean_virtue_vice_amand1945": "III (virtue/vice)",
    "argument_carneadean_incentives_amand1945": "IV (incentives)",
    "argument_carneadean_action_futility_amand1945": "V (action futility)",
    "argument_carneadean_piety_amand1945": "VI (piety)",
}


def print_console_summary(matrix: list[list[PairScore]]) -> None:
    print("=" * 78)
    print("AMAND → STOIC 6×4 PROVENANCE MATRIX")
    print("=" * 78)
    print(f"{'Pivot':<22} {'Stoic':<12} {'Th':>3} {'Co':>3} {'Tx':>3} {'Σ':>3}")
    print("-" * 78)
    for row in matrix:
        for cell in row:
            print(
                f"{_PIVOT_ROMAN[cell.pivot]:<22} "
                f"{_SHORT_NAMES[cell.stoic]:<12} "
                f"{int(bool(cell.thematic_hits)):>3} "
                f"{int(bool(cell.conceptual_hits)):>3} "
                f"{int(bool(cell.textual_hits)):>3} "
                f"{cell.total_score:>3}"
            )
    print("=" * 78)
    # Per-pivot 3/6 majority preview (≥1 vote per Stoic if total_score ≥ 1).
    print("\nPivot majority rule (≥1 score on ≥3 of 4 Stoics):")
    for row in matrix:
        pivot = row[0].pivot
        votes = sum(1 for cell in row if cell.total_score >= 1)
        verdict = "PASS" if votes >= 3 else "fail"
        print(f"  {_PIVOT_ROMAN[pivot]:<22} votes={votes}/4  → {verdict}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUT,
        help="Path to JSON output (default: docs/papers/2026-05-amand-piste1-data/provenance-matrix-6x4.json)",
    )
    args = parser.parse_args(argv)

    matrix = compute_matrix()
    dump_matrix(matrix, args.output)
    print_console_summary(matrix)
    logger.info("matrix written to %s", args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
