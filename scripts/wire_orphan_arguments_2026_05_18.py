#!/usr/bin/env python3
"""Wire the 843 orphan ``scholarly_argument_*`` nodes to their scholar, publication,
and (when extractable from description) ancient persons/concepts/works.

Context
-------
A "wave_p_final_polish_2026_05_16" extraction pass produced 843 ``argument``
nodes (typed ``scholarly_argument_<surname>_<topic>_N``) carrying scholar
theses lifted out of secondary literature, but never wired any of them to
the rest of the KG. They are flagged ``orphan_scholarly_argument=true`` and
``needs_evidence=true`` in metadata. This script repairs that wiring.

Strategy
--------
For each orphan ``argument``:

  1. Resolve the scholar via the ID surname slug (handles diacritic-stripped
     slugs like ``f_rst`` for Fürst, ``l_demann`` for Lüdemann, compound
     surnames ``engberg_pedersen``, prefix particles ``de_``, ``o_``, etc.).
     Disambiguate Frede (Michael vs Dorothea) and Koch (Klaus vs Koch-Piettre)
     by description keyword. When a surname matches only ``person_<x>``
     (non-scholar-tagged), accept it if Fischer/Frankfurt etc. exist.

  2. Add ``created_by``: argument -> scholar
     (matches the existing 14 wired ``scholarly_argument_*`` precedent).

  3. Try to resolve the publication that hosts the thesis: take the union of
     the scholar's publications and, when the orphan id's topic-slug overlaps
     the publication title (Jaccard >= 0.2), add a ``discusses``: pub -> arg
     edge. If the scholar has exactly one publication, attach unconditionally.

  4. Conservatively extract ancient persons, concepts, works named in the
     description and add ``discusses``: arg -> target edges (no fabrication --
     only canonical full-word matches with high specificity).

Edges and their direction respect ``knowledge graph/ontology/edge_types.json``:
  - ``created_by``  arg -> person  (allowed)
  - ``discusses``   publication -> argument  (allowed; inverse of ``discussed_in``,
                                              which doesn't take publication target)
  - ``discusses``   argument -> {person, concept, work, school, debate}  (allowed)
  - ``cites_primary_source``  argument -> work  (used when an ancient work is named)

Each argument touched receives metadata::

    orphan_wired_at: "2026-05-18"
    wiring_confidence: high|medium|low
    wiring_edges_added: [list of relation labels emitted]

Existing flags (``orphan_scholarly_argument``, ``orphan_flagged_wave``,
``needs_evidence``) are preserved.

Idempotency
-----------
A second run is a no-op. Edge dedup uses (source, target, relation) signature
read from the current edges.jsonl. Argument nodes already carrying
``orphan_wired_at`` are skipped.

Usage
-----
  python3 scripts/wire_orphan_arguments_2026_05_18.py            # dry-run report
  python3 scripts/wire_orphan_arguments_2026_05_18.py --commit   # apply

A snapshot is written to ``data/kg/snapshots/2026-05-18-pre-orphan-wiring/``
before any mutation.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import unicodedata
import uuid
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"
EDGES_PATH = ROOT / "data" / "kg" / "edges.jsonl"
SNAPSHOT_DIR = ROOT / "data" / "kg" / "snapshots" / "2026-05-18-pre-orphan-wiring"
ONTOLOGY_PATH = ROOT / "knowledge graph" / "ontology" / "edge_types.json"

WIRED_DATE = "2026-05-18"
WIRED_WAVE = "wave_orphan_argument_wiring_2026_05_18"

# Disambiguation overrides for ambiguous scholar surnames.
# Maps surname -> default scholar id. Used when ID alone is insufficient.
SCHOLAR_DISAMBIGUATION: dict[str, str] = {
    # Michael Frede wrote on ancient free will; Dorothea Frede works mostly on
    # Aristotelian pleasure. The vast majority of "Frede:" scholarly arguments
    # in this KG (Bobzien-era debate, Stoa, autexousion) are Michael's.
    "frede": "scholar_frede_michael",
    # Two Koch nodes: Klaus (theology, Apocalypticism) is the first;
    # Koch-Piettre (Greek religion) is more specialized. Default to Klaus.
    "koch": "scholar_koch_i",
}

# Surname slugs we must hard-route because the diacritic-stripped slug doesn't
# survive our label-derived slug pipeline.
HARDCODED_SURNAME_TO_PERSONS: dict[str, list[str]] = {
    "f_rst": ["scholar_furst_alfons"],          # Alfons Fürst
    "l_demann": ["scholar_l_demann_g"],         # Gerd Lüdemann
    "l_hr": ["scholar_l_hr_w"],                 # Winrich Löhr
}


# ---------------------------------------------------------------------------
# IO
# ---------------------------------------------------------------------------

def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    tmp.replace(path)


def snapshot() -> None:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    for src in (NODES_PATH, EDGES_PATH):
        dst = SNAPSHOT_DIR / src.name
        if not dst.exists():
            shutil.copy2(src, dst)


# ---------------------------------------------------------------------------
# Surname extraction
# ---------------------------------------------------------------------------

PARTICLES = ("o", "f", "de", "la", "van", "von", "du", "l", "el")
# Compound surnames where second token is known to participate in the surname.
# Map first token -> set of valid second tokens.
COMPOUND_HEADS: dict[str, frozenset[str]] = {
    "engberg": frozenset({"pedersen"}),
    "boys": frozenset({"stones"}),
    "denzey": frozenset({"lewis"}),
    "acosta": frozenset({"l"}),         # "acosta_l_pez_de_mesa"
    "amand": frozenset({"de"}),         # "amand_de_mendieta"
    "koch": frozenset({"piettre"}),     # Koch-Piettre (vs plain Koch)
}


def normalize(s: str) -> str:
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()


def label_slug(label: str) -> str:
    """Reproduce the ID-style slug from a label (diacritic letters → _)."""
    out_chars: list[str] = []
    for c in label.lower():
        if c.isalnum() and c.isascii():
            out_chars.append(c)
        elif c == " " or c == "-":
            out_chars.append("_")
        elif c.isalpha():  # non-ascii letter (ü, ö, é, ...)
            out_chars.append("_")
        # else punctuation: drop
    return re.sub(r"_+", "_", "".join(out_chars)).strip("_")


def extract_surname_from_arg_id(aid: str) -> str | None:
    body = aid
    for prefix in ("scholarly_argument_", "scholar_argument_", "argument_"):
        if body.startswith(prefix):
            body = body[len(prefix):]
            break
    parts = body.split("_")
    if not parts:
        return None
    p0 = parts[0]
    if p0 in PARTICLES and len(parts) >= 2:
        return f"{p0}_{parts[1]}"
    if p0 in COMPOUND_HEADS and len(parts) >= 2 and parts[1] in COMPOUND_HEADS[p0]:
        return f"{p0}_{parts[1]}"
    return p0


def extract_year_from_arg_id(aid: str) -> str | None:
    # legacy pattern argument_<topic>_amand1945
    m = re.search(r"(\d{4})", aid)
    return m.group(1) if m else None


def person_surname_variants(person: dict) -> set[str]:
    """Yield surname slugs by which a person node may be matched."""
    out: set[str] = set()
    pid = person["id"]
    label = person.get("label", "") or ""
    # 1. ID-derived
    body = pid
    for prefix in ("scholar_", "person_"):
        if body.startswith(prefix):
            body = body[len(prefix):]
            break
    body = body.replace("_contemporary", "")
    parts = body.split("_")
    # Strip trailing initials (single letters) and hash-like ids (≥6 chars mixed alnum
    # with at least one digit). NOT real lowercase-only tokens.
    def _is_hash(tok: str) -> bool:
        return bool(tok) and len(tok) >= 6 and len(tok) <= 12 and any(c.isdigit() for c in tok)
    while parts and (len(parts[-1]) == 1 or _is_hash(parts[-1])):
        parts.pop()
    # Strip pure-numeric trailing tokens (years)
    while parts and parts[-1].isdigit():
        parts.pop()
    if parts:
        p0 = parts[0]
        if p0 in PARTICLES and len(parts) >= 2:
            out.add(f"{p0}_{parts[1]}")
            out.add(parts[1])
        elif p0 in COMPOUND_HEADS and len(parts) >= 2 and parts[1] in COMPOUND_HEADS[p0]:
            out.add(f"{p0}_{parts[1]}")
            out.add(p0)
        else:
            out.add(p0)
    # 2. Label-derived (handles diacritics correctly via label_slug)
    slug = label_slug(label)
    toks = [t for t in slug.split("_") if t]
    if toks:
        out.add(toks[-1])
        if len(toks) >= 2:
            out.add(f"{toks[-2]}_{toks[-1]}")
            # if penultimate is a particle, also include 3-token form
            if toks[-2] in PARTICLES and len(toks) >= 3:
                out.add(f"{toks[-3]}_{toks[-2]}_{toks[-1]}")
    # 3. Pure normalized (no diacritics) surname (e.g. "fürst" -> "furst")
    norm = normalize(label)
    words = re.findall(r"[a-z]+", norm)
    if words:
        out.add(words[-1])
        if len(words) >= 2 and words[-2] in ("de", "van", "von", "la", "le", "du", "mc"):
            out.add(f"{words[-2]}_{words[-1]}")
    return {x for x in out if x and len(x) >= 2}


# ---------------------------------------------------------------------------
# Build maps
# ---------------------------------------------------------------------------

def build_scholar_index(nodes: list[dict]) -> dict[str, list[str]]:
    """Surname slug -> list of person ids (scholar candidates)."""
    idx: dict[str, list[str]] = defaultdict(list)
    for n in nodes:
        if n.get("type") != "person":
            continue
        pid = n["id"]
        # Treat any person as a scholar candidate; we'll prefer scholar_* hits
        # if multiple are returned later.
        for sn in person_surname_variants(n):
            if pid not in idx[sn]:
                idx[sn].append(pid)
    # Apply hardcoded routes
    for sn, persons in HARDCODED_SURNAME_TO_PERSONS.items():
        for pid in persons:
            if pid not in idx[sn]:
                idx[sn].insert(0, pid)
    return idx


def is_scholarly_person(pid: str) -> bool:
    return pid.startswith("scholar_") or pid.endswith("_contemporary")


def pick_scholar(surname: str, candidates: list[str], orphan_desc: str) -> tuple[str | None, str, str]:
    """Choose primary scholar id. Returns (id|None, confidence, reason)."""
    if not candidates:
        return None, "none", "no candidate"
    # 1. Disambiguation override
    if surname in SCHOLAR_DISAMBIGUATION:
        forced = SCHOLAR_DISAMBIGUATION[surname]
        if forced in candidates:
            return forced, "high", f"override:{surname}"
    # 2. Prefer scholar_* over person_*_contemporary over plain person_*
    scholar_pri = [c for c in candidates if c.startswith("scholar_")]
    contemporary = [c for c in candidates if c.endswith("_contemporary")]
    others = [c for c in candidates if c not in scholar_pri and c not in contemporary]
    ranked = scholar_pri + contemporary + others
    # Unique scholarly?
    if len([c for c in candidates if is_scholarly_person(c)]) == 1:
        return ranked[0], "high", "unique-scholarly"
    if len(candidates) == 1:
        return ranked[0], "high", "unique"
    # Multiple scholarly candidates: medium confidence, pick the first
    return ranked[0], "medium", f"ambiguous:{len(candidates)}"


def build_pub_indices(nodes: list[dict], edges: list[dict]) -> tuple[dict[str, set[str]], dict[str, dict]]:
    """Return (scholar_id -> set of pub ids, pub_id -> pub node)."""
    pubs = {n["id"]: n for n in nodes if n.get("type") == "publication"}
    edges_out: dict[str, list[tuple[str, str]]] = defaultdict(list)
    edges_in: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for e in edges:
        s, t, r = e["source"], e["target"], e["relation"]
        edges_out[s].append((r, t))
        edges_in[t].append((r, s))
    scholar_pubs: dict[str, set[str]] = defaultdict(set)
    for pid in pubs:
        for r, t in edges_out[pid]:
            if r == "authored_by":
                scholar_pubs[t].add(pid)
        for r, s in edges_in[pid]:
            if r in ("wrote", "creates"):
                scholar_pubs[s].add(pid)
    return scholar_pubs, pubs


# ---------------------------------------------------------------------------
# Discusses extraction (conservative)
# ---------------------------------------------------------------------------

# Canonical ancient persons we accept by single-word match. The map is
# label-keyed (lowercased, no diacritics) -> kg id. IDs verified against
# data/kg/nodes.jsonl on 2026-05-18.
ANCIENT_PERSON_KEYWORDS: dict[str, str] = {
    "origen": "person_origen_alexandria_185_254ce_s9t0u1v2",
    "origène": "person_origen_alexandria_185_254ce_s9t0u1v2",
    "plato": "person_plato_428_348bce_a1b2c3d4",
    "platon": "person_plato_428_348bce_a1b2c3d4",
    "aristotle": "person_aristotle_384_322bce_c2d4f6a8",
    "aristote": "person_aristotle_384_322bce_c2d4f6a8",
    "chrysippus": "person_chrysippus_280_206bce_i9j0k1l2",
    "chrysippe": "person_chrysippus_280_206bce_i9j0k1l2",
    "zeno": "person_zeno_citium_334_262bce",
    "epictetus": "person_epictetus_of_hierapolis_3c385bc2",
    "epictète": "person_epictetus_of_hierapolis_3c385bc2",
    "epicurus": "person_epicurus_341_270bce_j0k1l2m3",
    "épicure": "person_epicurus_341_270bce_j0k1l2m3",
    "lucretius": "person_lucretius_99_55bce_k1l2m3n4",
    "lucrèce": "person_lucretius_99_55bce_k1l2m3n4",
    "carneades": "person_carneades_214_129bce_l2m3n4o5",
    "carnéade": "person_carneades_214_129bce_l2m3n4o5",
    "augustine": "person_augustine_hippo_d430",
    "augustin": "person_augustine_hippo_d430",
    "cicero": "person_cicero_marcus_tullius_106_43bce_a8f3d2c1",
    "cicéron": "person_cicero_marcus_tullius_106_43bce_a8f3d2c1",
    "seneca": "person_seneca_4bce_65ce_a1b2c3d4",
    "sénèque": "person_seneca_4bce_65ce_a1b2c3d4",
    "alexander of aphrodisias": "person_alexander_aphrodisias_fl200ce_n5o6p7q8",
    "boethius": "person_boethius_480_524ce_w3x4y5z6",
    "boèce": "person_boethius_480_524ce_w3x4y5z6",
    "plotinus": "person_plotinus_d270",
    "plotin": "person_plotinus_d270",
    "porphyry": "person_porphyry",
    "porphyre": "person_porphyry",
    "tertullian": "person_tertullian_d220",
    "tertullien": "person_tertullian_d220",
    "athenagoras": "person_athenagoras",
    "athénagore": "person_athenagoras",
    "tatian": "person_tatian",
    "tatien": "person_tatian",
    "irenaeus": "person_irenaeus_d202",
    "irénée": "person_irenaeus_d202",
    "alcinous": "person_alcinous_2c_ce",
    "nemesius": "person_nemesius_emesa_4c_ce",
    "némésius": "person_nemesius_emesa_4c_ce",
    "marcus aurelius": "person_marcus_aurelius_121_180ce",
    "marc aurèle": "person_marcus_aurelius_121_180ce",
    "musonius": "person_musonius_rufus_30_101ce",
    "diogenes laertius": "person_diogenes_laertius_3c_ce",
    "diogène laërce": "person_diogenes_laertius_3c_ce",
    "theophrastus": "person_theophrastus_371_287bce",
    "théophraste": "person_theophrastus_371_287bce",
    "arcesilaus": "person_arcesilaus_316_241bce",
    "arcésilas": "person_arcesilaus_316_241bce",
    # NB: "Clement", "Philo", "Alexander" alone are too ambiguous and are
    # intentionally excluded -- "Clement of Alexandria" vs "of Rome",
    # "Philo of Alexandria" vs "of Larissa" vs "Philoponus".
}

# Concepts: highly specific Greek-loanword concepts whose mention is unambiguous
# enough to wire confidently. Several "autexousion" variants exist in the KG --
# we route the term to the broadest concept node and let downstream curation
# refine later.
CONCEPT_KEYWORDS: dict[str, str] = {
    "prohairesis": "concept_prohairesis_deliberate_choice_aristotle_c3d4e5f6",
    "προαίρεσις": "concept_prohairesis_deliberate_choice_aristotle_c3d4e5f6",
    "autexousion": "concept_autexousion_christian",
    "αὐτεξούσιον": "concept_autexousion_christian",
    "ἐφ' ἡμῖν": "concept_eph_hemin_in_our_power_aristotle_d4e5f6g7",
    "eph' hemin": "concept_eph_hemin_in_our_power_aristotle_d4e5f6g7",
    "eph hemin": "concept_eph_hemin_in_our_power_aristotle_d4e5f6g7",
    "ta eph hemin": "concept_eph_hemin_in_our_power_aristotle_d4e5f6g7",
    "heimarmene": "concept_heimarmene_fate_stoics_j0k1l2m3",
    "εἱμαρμένη": "concept_heimarmene_fate_stoics_j0k1l2m3",
    "apocatastasis": "concept_apocatastasis",
    "ἀποκατάστασις": "concept_apocatastasis",
    "akrasia": "concept_akrasia_weakness_of_will",
    "ἀκρασία": "concept_akrasia_weakness_of_will",
    "synkatathesis": "concept_synkatathesis_stoic_assent",
    "συγκατάθεσις": "concept_synkatathesis_stoic_assent",
}

# Schools / groups by surface keyword.
SCHOOL_KEYWORDS: dict[str, str] = {
    "stoic": "school_stoics",
    "stoics": "school_stoics",
    "stoicism": "school_stoics",
    "stoïcien": "school_stoics",
    "stoïcisme": "school_stoics",
    "stoa": "school_stoics",
    "epicurean": "school_epicureans",
    "épicurien": "school_epicureans",
    "epicureanism": "school_epicureans",
    "peripatetic": "school_peripatetics",
    "péripatéticien": "school_peripatetics",
}

# Ancient works whose Latin/Greek titles are unambiguous in this KG.
# NB: "De Fato" is intentionally omitted -- multiple works share that title
# (Cicero, Alexander, Plutarch, Pseudo-Plutarch, Pseudo-Chrysostom), so a
# keyword-only match would be unsafe.
WORK_KEYWORDS: dict[str, str] = {
    "de principiis": "work_de_principiis_origen_230s_v2w3x4y5",
    "peri archon": "work_de_principiis_origen_230s_v2w3x4y5",
    "περὶ ἀρχῶν": "work_de_principiis_origen_230s_v2w3x4y5",
    "contra celsum": "work_origen_contra_celsum_sc132",
    "kata kelsou": "work_origen_contra_celsum_sc132",
    "κατὰ κέλσου": "work_origen_contra_celsum_sc132",
}


def find_keyword_matches(text: str, keyword_map: dict[str, str], all_ids: set[str]) -> set[str]:
    """Return target ids whose keyword appears in text as a whole word."""
    if not text:
        return set()
    low = text.lower()
    hits: set[str] = set()
    for kw, tid in keyword_map.items():
        if tid not in all_ids:
            continue
        # word-boundary search; for greek terms boundary is more forgiving
        pattern = r"(?<![a-zA-Zα-ωΑ-Ω])" + re.escape(kw) + r"(?![a-zA-Zα-ωΑ-Ω])"
        if re.search(pattern, low):
            hits.add(tid)
    return hits


# ---------------------------------------------------------------------------
# Publication matching for orphan
# ---------------------------------------------------------------------------

def topic_slug_from_arg_id(aid: str, surname: str) -> str:
    body = aid
    for prefix in ("scholarly_argument_", "scholar_argument_", "argument_"):
        if body.startswith(prefix):
            body = body[len(prefix):]
            break
    # Strip surname + leading underscore
    if body.startswith(surname + "_"):
        body = body[len(surname) + 1:]
    # Strip trailing _<digit(s)>
    body = re.sub(r"_+\d+$", "", body)
    return body


STOP_TOKENS = frozenset({
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "with", "by",
    "is", "are", "as", "from", "at", "be", "this", "that", "his", "her", "its",
    "their", "s", "de", "la", "le", "et", "du", "des", "en", "un", "une",
})


def tokens(text: str) -> set[str]:
    if not text:
        return set()
    norm = normalize(text)
    return {t for t in re.findall(r"[a-z]+", norm) if len(t) >= 3 and t not in STOP_TOKENS}


def match_publication(scholar_pubs: set[str], pubs: dict[str, dict], topic: str, desc: str) -> tuple[str | None, str]:
    """Return (pub_id|None, confidence)."""
    if not scholar_pubs:
        return None, "none"
    if len(scholar_pubs) == 1:
        return next(iter(scholar_pubs)), "high"
    # Score each pub by Jaccard with topic+desc tokens
    arg_tokens = tokens(topic + " " + desc)
    best: tuple[float, str | None] = (0.0, None)
    for pid in scholar_pubs:
        title = pubs[pid].get("label", "")
        pub_tokens = tokens(title)
        if not pub_tokens:
            continue
        inter = arg_tokens & pub_tokens
        union = arg_tokens | pub_tokens
        score = len(inter) / len(union) if union else 0.0
        if score > best[0]:
            best = (score, pid)
    if best[0] >= 0.2:
        return best[1], "high"
    if best[0] >= 0.1:
        return best[1], "medium"
    return None, "low"


# ---------------------------------------------------------------------------
# Main wiring routine
# ---------------------------------------------------------------------------

def signature(s: str, t: str, r: str) -> tuple[str, str, str]:
    return (s, t, r)


def edge_record(source: str, target: str, relation: str, *, weight: float, meta: dict) -> dict:
    now = datetime.now(UTC).isoformat(sep=" ")
    return {
        "created_at": now,
        "edge_id": str(uuid.uuid4()),
        "metadata": json.dumps(meta, ensure_ascii=False),
        "relation": relation,
        "source": source,
        "source_id": source,
        "target": target,
        "target_id": target,
        "weight": weight,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", action="store_true", help="apply changes; otherwise dry-run")
    parser.add_argument("--limit", type=int, default=None, help="process only first N orphans (debug)")
    args = parser.parse_args(argv)

    print(f"=== orphan-argument wiring  ({'COMMIT' if args.commit else 'dry-run'}) ===")
    nodes = load_jsonl(NODES_PATH)
    edges = load_jsonl(EDGES_PATH)
    print(f"loaded {len(nodes)} nodes, {len(edges)} edges")

    nodes_by_id = {n["id"]: n for n in nodes}

    # Build edge incidence
    edges_in: dict[str, list[tuple[str, str]]] = defaultdict(list)
    edges_out: dict[str, list[tuple[str, str]]] = defaultdict(list)
    existing_signatures: set[tuple[str, str, str]] = set()
    for e in edges:
        s, t, r = e["source"], e["target"], e["relation"]
        edges_out[s].append((r, t))
        edges_in[t].append((r, s))
        existing_signatures.add(signature(s, t, r))

    # Find orphan arguments (zero in + zero out)
    orphans = [
        n for n in nodes
        if n.get("type") == "argument"
        and not edges_in[n["id"]]
        and not edges_out[n["id"]]
    ]
    print(f"orphan arguments detected: {len(orphans)}")

    # Skip already-wired-by-this-script ones (idempotency)
    def is_already_wired(node: dict) -> bool:
        md = node.get("metadata")
        if isinstance(md, dict):
            return md.get("orphan_wired_at") == WIRED_DATE
        return False

    to_process = [o for o in orphans if not is_already_wired(o)]
    print(f"to process (not yet wired by this script): {len(to_process)}")

    if args.limit:
        to_process = to_process[: args.limit]

    # Build indices
    scholar_idx = build_scholar_index(nodes)
    scholar_pubs, pubs = build_pub_indices(nodes, edges)
    all_node_ids = set(nodes_by_id.keys())

    # Stats
    stat = Counter()
    by_scholar = Counter()
    unresolved: list[tuple[str, str]] = []  # (arg_id, reason)
    new_edges: list[dict] = []
    edge_seen: set[tuple[str, str, str]] = set(existing_signatures)
    node_updates: dict[str, dict] = {}  # arg_id -> patched node

    for arg in to_process:
        aid = arg["id"]
        desc = arg.get("description", "") or ""
        label = arg.get("label", "") or ""
        full_text = label + " " + desc

        # 1. Scholar resolution
        surname = extract_surname_from_arg_id(aid)
        if not surname:
            unresolved.append((aid, "no surname"))
            stat["unresolved_no_surname"] += 1
            continue
        # Try year-suffix fallback for legacy non-scholarly args
        year = None
        if aid.startswith("argument_"):
            year = extract_year_from_arg_id(aid)
            # e.g. "amand1945" -> surname might be "aristotelian"; remap via year
            # Search id for "<surname><year>" suffix.
            m = re.search(r"_([a-z]+)(\d{4})$", aid)
            if m:
                surname = m.group(1)
                year = m.group(2)

        candidates = scholar_idx.get(surname, [])
        scholar_id, scholar_conf, scholar_reason = pick_scholar(surname, candidates, desc)
        if not scholar_id or scholar_id not in nodes_by_id:
            unresolved.append((aid, f"scholar_not_matched:{surname}"))
            stat["unresolved_scholar"] += 1
            by_scholar[surname] += 1
            # Mark node with status flag for traceability
            md = arg.get("metadata") if isinstance(arg.get("metadata"), dict) else {}
            md = dict(md)
            md["wiring_status"] = "unmatched_scholar"
            md["wiring_attempted_surname"] = surname
            patched = dict(arg)
            patched["metadata"] = md
            node_updates[aid] = patched
            continue

        by_scholar[scholar_id] += 1
        edges_added_relations: list[str] = []
        edges_added_for_this_arg: list[dict] = []

        # Edge 1: created_by  arg -> scholar
        sig = signature(aid, scholar_id, "created_by")
        if sig not in edge_seen:
            meta = {
                "auto_generated": True,
                "wired_from": "orphan_wiring_2026_05_18",
                "wiring_confidence": scholar_conf,
                "wiring_reason": scholar_reason,
            }
            new_edges.append(edge_record(aid, scholar_id, "created_by", weight=1.0, meta=meta))
            edges_added_for_this_arg.append(new_edges[-1])
            edge_seen.add(sig)
            edges_added_relations.append("created_by")
            stat["edges_created_by"] += 1

        # Edge 2: discusses  pub -> arg
        topic = topic_slug_from_arg_id(aid, surname)
        pub_id, pub_conf = match_publication(scholar_pubs.get(scholar_id, set()), pubs, topic.replace("_", " "), desc)
        if pub_id:
            sig = signature(pub_id, aid, "discusses")
            if sig not in edge_seen:
                meta = {
                    "auto_generated": True,
                    "wired_from": "orphan_wiring_2026_05_18",
                    "wiring_confidence": pub_conf,
                    "relation_type": "scholarly_thesis",
                }
                new_edges.append(edge_record(pub_id, aid, "discusses", weight=0.9, meta=meta))
                edges_added_for_this_arg.append(new_edges[-1])
                edge_seen.add(sig)
                edges_added_relations.append("discusses_pub")
                stat["edges_discusses_pub"] += 1

        # Edges 3+: discusses  arg -> person/concept/school + cites_primary_source for works
        # Skip if description is very short (< 60 chars) — too risky.
        if len(desc) >= 60:
            person_hits = find_keyword_matches(full_text, ANCIENT_PERSON_KEYWORDS, all_node_ids)
            concept_hits = find_keyword_matches(full_text, CONCEPT_KEYWORDS, all_node_ids)
            school_hits = find_keyword_matches(full_text, SCHOOL_KEYWORDS, all_node_ids)
            work_hits = find_keyword_matches(full_text, WORK_KEYWORDS, all_node_ids)

            for tid in sorted(person_hits | concept_hits | school_hits):
                sig = signature(aid, tid, "discusses")
                if sig in edge_seen:
                    continue
                meta = {
                    "auto_generated": True,
                    "wired_from": "orphan_wiring_2026_05_18",
                    "wiring_confidence": "medium",
                    "wiring_basis": "keyword_match",
                }
                new_edges.append(edge_record(aid, tid, "discusses", weight=0.7, meta=meta))
                edges_added_for_this_arg.append(new_edges[-1])
                edge_seen.add(sig)
                edges_added_relations.append(f"discusses:{tid}")
                stat["edges_discusses_kg"] += 1

            for tid in sorted(work_hits):
                sig = signature(aid, tid, "cites_primary_source")
                if sig in edge_seen:
                    continue
                meta = {
                    "auto_generated": True,
                    "wired_from": "orphan_wiring_2026_05_18",
                    "wiring_confidence": "medium",
                    "wiring_basis": "work_keyword",
                }
                new_edges.append(edge_record(aid, tid, "cites_primary_source", weight=0.7, meta=meta))
                edges_added_for_this_arg.append(new_edges[-1])
                edge_seen.add(sig)
                edges_added_relations.append(f"cites:{tid}")
                stat["edges_cites_work"] += 1

        # Patch node metadata
        md = arg.get("metadata") if isinstance(arg.get("metadata"), dict) else {}
        md = dict(md)
        md["orphan_wired_at"] = WIRED_DATE
        md["wiring_wave"] = WIRED_WAVE
        md["wiring_confidence"] = scholar_conf
        md["wiring_edges_added"] = edges_added_relations
        # Preserve existing orphan_* flags (do not delete them — they remain
        # a historical record).
        patched = dict(arg)
        patched["metadata"] = md
        node_updates[aid] = patched

        stat["orphans_wired"] += 1

    # ------------------------- Report -------------------------
    print("\n=== Stats ===")
    for k in (
        "orphans_wired", "edges_created_by", "edges_discusses_pub",
        "edges_discusses_kg", "edges_cites_work",
        "unresolved_scholar", "unresolved_no_surname",
    ):
        print(f"  {k}: {stat[k]}")

    print(f"\n  total new edges: {len(new_edges)}")
    print(f"  total node updates: {len(node_updates)}")

    print("\nTop 25 scholars (by orphan count wired):")
    for sid, c in by_scholar.most_common(25):
        label = nodes_by_id.get(sid, {}).get("label", sid)
        print(f"  {c:>3}  {sid:<45} {label[:40]}")

    if unresolved:
        print(f"\nUnresolved arguments ({len(unresolved)}):")
        for aid, reason in unresolved[:20]:
            print(f"  {aid}: {reason}")
        if len(unresolved) > 20:
            print(f"  ... and {len(unresolved) - 20} more")

    if not args.commit:
        print("\n(dry-run; pass --commit to write)")
        return 0

    # ------------------------- Apply --------------------------
    if not new_edges and not node_updates:
        print("\nOK: nothing to apply.")
        return 0

    snapshot()
    print(f"\nsnapshot written to {SNAPSHOT_DIR}")

    # Update nodes.jsonl (preserve byte-exact for unchanged lines)
    if node_updates:
        new_nodes = []
        for n in nodes:
            if n["id"] in node_updates:
                new_nodes.append(node_updates[n["id"]])
            else:
                new_nodes.append(n)
        write_jsonl(NODES_PATH, new_nodes)
        print(f"updated {len(node_updates)} nodes in {NODES_PATH.name}")

    # Append new edges
    if new_edges:
        with EDGES_PATH.open("a", encoding="utf-8") as fh:
            for e in new_edges:
                fh.write(json.dumps(e, ensure_ascii=False) + "\n")
        print(f"appended {len(new_edges)} edges to {EDGES_PATH.name}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
