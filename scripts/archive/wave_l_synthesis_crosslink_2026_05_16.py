#!/usr/bin/env python3
"""Wave L — Synthesis cross-link — 2026-05-16.

Auto-link orphan ``synthesis`` nodes (177 total, ~89 with fewer than
3 outgoing semantic edges, ~41 with zero) to existing person /
argument / concept / work / debate / school / controversy / group
nodes by extracting referenced entities from each synthesis
description.

Procedure (per Wave L spec) :

1. Build a label index of all eligible target nodes (types in
   ``ALLOWED_TARGET_TYPES``), keyed by ``label`` and by each
   ``alternative_name``. Labels and alt-names < 5 chars are dropped
   to avoid noise. Greek diacritics are preserved (Unicode NFKD
   normalisation just lower-cases; we do NOT strip combining marks
   so that ``εἱμαρμένη`` stays distinct from ``ειμαρμενη``).
2. For each synthesis node with fewer than 3 outgoing semantic edges
   (``LINK_RELATIONS``), scan its ``description`` for word-boundary-
   delimited occurrences of indexed labels.
3. Score candidates : prefer longer labels (more specific) and
   higher-degree target nodes (more central / authoritative).
4. Keep the top ``MAX_LINKS_PER_SYNTHESIS`` distinct candidates per
   synthesis after deduplication (no two candidates whose labels
   overlap by >= 80 %).
5. Insert ``discusses`` edges synthesis -> target. ``discusses``
   ontology already allows ``synthesis`` as a source type (verified
   2026-05-16), so no ontology widening is required.
6. Every edge is tagged ``confidence: 0.5`` and
   ``auto_linked_from_description: true`` so curators can audit /
   revert in bulk.
7. Strict idempotency : edge signature
   ``(source, "discusses", target)`` is checked against the existing
   edge set before insertion. A second run logs zero additions.

Write a 20-edge random review sample to
``data/kg/reports/wave_l_manual_review_sample_2026_05_16.json`` so
the user can audit a sample for false positives.

Romain est seul auteur. Aucune mention de Claude / IA / Co-Author.
"""

from __future__ import annotations

import json
import random
import re
import shutil
import sys
import unicodedata
import uuid
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"
EDGES_PATH = ROOT / "data" / "kg" / "edges.jsonl"
REPORTS_DIR = ROOT / "data" / "kg" / "reports"

WAVE_TAG = "wave_l_synthesis_crosslink_2026_05_16"
SNAPSHOT_DIR = ROOT / "data" / "kg" / "snapshots" / f"2026-05-16-pre-{WAVE_TAG}"
REVIEW_SAMPLE_PATH = REPORTS_DIR / "wave_l_manual_review_sample_2026_05_16.json"

NOW_ISO = datetime.now(UTC).isoformat(sep=" ")

# Node types eligible as cross-link targets. Passages excluded (too
# many noisy substring matches). Publications excluded (separate
# concern, Wave O). Syntheses excluded (no synthesis -> synthesis).
ALLOWED_TARGET_TYPES: frozenset[str] = frozenset(
    {
        "person",
        "argument",
        "concept",
        "work",
        "debate",
        "school",
        "controversy",
        "group",
    }
)

# Relations counted as "semantic outgoing" when deciding whether a
# synthesis is thin (< 3 edges). Structural / housekeeping relations
# (e.g. part_of, translation_of) don't count.
LINK_RELATIONS: frozenset[str] = frozenset(
    {
        "discusses",
        "cites",
        "engages_with",
        "interprets",
        "critiques",
        "supports",
        "synthesizes",
        "influences",
        "evidenced_by",
        "cites_primary_source",
        "references",
    }
)

# A label must be at least 5 chars (normalised) to be considered.
MIN_LABEL_LEN = 5

# Cap the number of new edges per synthesis to avoid over-connection.
MAX_LINKS_PER_SYNTHESIS = 5

# Below this threshold a synthesis is considered thin and gets
# auto-linked.
THIN_THRESHOLD = 3

# Labels that are too generic / collide with stopwords. Even with
# the >= 5-char minimum some labels (e.g. an English place name
# matching a function word in French) can produce false positives.
# Anything in this set is excluded from the index entirely.
LABEL_STOPWORDS: frozenset[str] = frozenset(
    {
        # Common short words / generic terms we never want to substring-match
        "logos",  # too generic, appears in many contexts
        "homer",  # rarely a meaningful link
        "moses",  # ditto
        "moise",  # ditto
        "moïse",
        "amour",
        "anima",
        "âme",
        "lumière",
        "argument",
        "school",
        "ecole",
        "école",
        "groupe",
        "person",
        "personne",
        "concept",
        "debate",
        "débat",
        "syllabus",
        # Generic short locative / patronymic fragments that would
        # alias dozens of distinct historical figures
        "marcus",
        "lucius",
        "titus",
        "gaius",
        "publius",
        "iulius",
        "iustinus",
        "iohannes",
        "ioannes",
        "saint",
        "papa",
        "pape",
        "πάπας",
        "rome",
        "roma",
        "athens",
        "athenae",
        "athènes",
        "alexandria",
        "alexandrie",
        "constantinople",
        "jerusalem",
        "jérusalem",
        "antioch",
        "antioche",
        "carthage",
        "milan",
        "patriarche",
        "patriarch",
        "emperor",
        "empereur",
        "imperator",
        "evêque",
        "évêque",
        "bishop",
        "episcopus",
        "hellenistic",
        "hellénistique",
        "classical",
        "classique",
        "patristic",
        "patristique",
        "medieval",
        "médiéval",
        # Common modern French words long enough to pass the length
        # guard but often clashing with proper names in indices.
        "siècle",
        "siecle",
        "livre",
        "chapitre",
        "auteur",
        "œuvre",
        "oeuvre",
        "tradition",
        "doctrine",
        "thèse",
        "these",
        # Single letters that are kept in label normalisation
        # because they're combined with combining marks.
    }
)

# Curated cross-lingual aliases. The KG stores most ancient person
# labels in English (e.g. "Carneades of Cyrene") but synthesis
# descriptions are mostly French and frequently use the French
# (and sometimes Greek / Latin) form. These manual aliases bridge
# that gap. Only well-attested major figures are listed — each one
# is unambiguous in context. node_id -> list of additional matchable
# strings.
MANUAL_ALIASES: dict[str, list[str]] = {
    # Ancient philosophers — verified node_ids
    "person_carneades_214_129bce_l2m3n4o5": [
        "Carnéade",
        "Carneade",
        "Carnéades",
        "Καρνεάδης",
    ],
    "person_chrysippus_280_206bce_i9j0k1l2": [
        "Chrysippe",
        "Χρύσιππος",
    ],
    "person_epicurus_341_270bce_j0k1l2m3": [
        "Épicure",
        "Epicure",
        "Ἐπίκουρος",
    ],
    "person_plato_428_348bce_a1b2c3d4": [
        "Platon",
        "Πλάτων",
    ],
    "person_aristotle_384_322bce_c2d4f6a8": [
        "Aristote",
        "Ἀριστοτέλης",
    ],
    "person_epictetus_of_hierapolis_3c385bc2": [
        "Épictète",
        "Epictete",
        "Ἐπίκτητος",
    ],
    "person_cicero_marcus_tullius_106_43bce_a8f3d2c1": [
        "Cicéron",
        "Ciceron",
        "Cicero",
        "Tullius Cicero",
    ],
    "person_augustine_hippo_d430": [
        "Augustin",
        "Augustinus",
        "Saint Augustin",
        "Augustin d'Hippone",
    ],
    "person_zeno_citium_334_262bce": [
        "Zénon",
        "Zenon",
        "Zénon de Cition",
        "Zeno of Citium",
        "Ζήνων",
    ],
    "person_cleanthes_assos_330_230bce": [
        "Cléanthe",
        "Cleanthes",
        "Κλεάνθης",
    ],
    "person_origen_alexandria_185_254ce_s9t0u1v2": [
        "Origène",
        "Origenes",
        "Ὠριγένης",
    ],
    "person_basil_great_d379": [
        "Basile",
        "Basile de Césarée",
        "Basile le Grand",
        "Βασίλειος",
    ],
    "person_eusebius_caesarea_d339": [
        "Eusèbe",
        "Eusèbe de Césarée",
        "Eusebius",
        "Εὐσέβιος",
    ],
    "person_john_chrysostom_d407": [
        "Chrysostome",
        "Jean Chrysostome",
        "Χρυσόστομος",
    ],
    "person_alexander_aphrodisias_fl200ce_n5o6p7q8": [
        "Alexandre d'Aphrodise",
        "Alexandre d'Aphrodisias",
        "Ἀλέξανδρος Ἀφροδισιεύς",
    ],
    "person_plotinus_d270": [
        "Plotin",
        "Plotinus",
        "Πλωτῖνος",
    ],
    "person_seneca_4bce_65ce_a1b2c3d4": [
        "Sénèque",
        "Seneque",
        "Lucius Annaeus Seneca",
    ],
    "person_posidonius_apameia_135_51bce": [
        "Posidonios",
        "Posidonios d'Apamée",
        "Posidonius",
        "Ποσειδώνιος",
    ],
    "person_panaetius_rhodes_185_109bce": [
        "Panétius",
        "Panaitios",
        "Panaetius",
        "Παναίτιος",
    ],
    "person_diogenes_laertius_3c_ce": [
        "Diogène Laërce",
        "Diogene Laerce",
        "Diogenes Laertius",
        "Διογένης Λαέρτιος",
    ],
    "person_maximus_confessor_d662": [
        "Maxime le Confesseur",
        "Maximus Confessor",
        "Μάξιμος ὁ Ὁμολογητής",
    ],
    "person_boethius_480_524ce_w3x4y5z6": [
        "Boèce",
        "Boethius",
    ],
    "person_pseudo_plutarch_2c_ce": [
        "Pseudo-Plutarque",
        "Pseudo-Plutarch",
    ],
    "person_porphyry": [
        "Porphyre",
        "Porphyrius",
        "Πορφύριος",
    ],
    "person_iamblichus_d325": [
        "Jamblique",
        "Iamblichus",
        "Ἰάμβλιχος",
    ],
    "person_proclus_412_485ce_f3d8b2a9": [
        "Proclus",
        "Proclos",
        "Πρόκλος",
    ],
    "person_philo_alexandria_a1b2c3d4": [
        "Philon",
        "Philon d'Alexandrie",
        "Philo Alexandrinus",
        "Φίλων",
    ],
    "person_justin_martyr_2c_ce": [
        "Justin Martyr",
        "Iustinus Martyr",
    ],
    "person_clement_alexandria": [
        "Clément d'Alexandrie",
        "Clemens Alexandrinus",
        "Κλήμης Ἀλεξανδρεύς",
    ],
    "person_tertullian_d220": [
        "Tertullien",
        "Tertullianus",
    ],
    "person_diodorus_cronus_48ef6200": [
        "Diodore Cronos",
        "Diodorus Cronos",
        "Διόδωρος Κρόνος",
    ],
    "person_diogenes_oenoanda_2c_ce": [
        "Diogène d'Œnoanda",
        "Diogène d'Oenoanda",
        "Diogenes Oenoandensis",
    ],
    "person_lucretius_99_55bce_k1l2m3n4": [
        "Lucrèce",
        "Lucretius",
        "T. Lucretius Carus",
    ],
    "person_marcus_aurelius_121_180ce": [
        "Marc Aurèle",
        "Marc-Aurèle",
        "Marcus Aurelius",
    ],
    "person_socrates_470_399bce_b2c3d4e5": [
        "Socrate",
        "Socrates",
        "Σωκράτης",
    ],
    # Modern scholars — verified
    "person_bobzien_susanne_contemporary": [
        "Bobzien",
        "Susanne Bobzien",
    ],
    "scholar_destr_e_p": [
        "Destrée",
        "Pierre Destrée",
    ],
    "scholar_frede_dorothea": [
        "Dorothea Frede",
    ],
    "scholar_amand_de_mendieta_e": [
        "Amand",
        "Amand de Mendieta",
        "David Amand",
    ],
    # Core concepts — verified
    "concept_heimarmene_fate_stoics_j0k1l2m3": [
        "εἱμαρμένη",
        "heimarmene",
        "heimarmenê",
    ],
    "concept_eph_hemin_in_our_power_aristotle_d4e5f6g7": [
        "ἐφ' ἡμῖν",
        "ἐφ ἡμῖν",
        "to eph hemin",
        "ce qui dépend de nous",
        "in nostra potestate",
    ],
    "concept_prohairesis_deliberate_choice_aristotle_c3d4e5f6": [
        "προαίρεσις",
        "prohairesis",
        "proairesis",
    ],
    "concept_autexousion_christian_freedom_u1v2w3x4": [
        "αὐτεξούσιον",
        "autexousion",
    ],
    "concept_synkatathesis_stoic_assent": [
        "συγκατάθεσις",
        "synkatathesis",
        "assentiment",
    ],
    "concept_clinamen_atomic_swerve_epicurus_m3n4o5p6": [
        "clinamen",
        "παρέγκλισις",
        "parenklisis",
    ],
    # Works — verified
    "work_de_fato_cicero_44bce_b9c4e5d2": [
        "De Fato Cicéron",
        "Cicero De Fato",
    ],
    "work_de_fato_alexander_c200ce_o6p7q8r9": [
        "De Fato Alexandre",
        "De Fato d'Alexandre",
    ],
    "work_plutarch_de_fato_complete": [
        "Pseudo-Plutarque De Fato",
    ],
    "work_epictetus_enchiridion": [
        "Enchiridion",
        "Manuel",
        "Ἐγχειρίδιον",
    ],
    "work_epictetus_discourses": [
        "Διατριβαί",
        "Entretiens",
    ],
}

# Common multi-word label suffix patterns to strip when deriving a
# head-token. Order matters : longer patterns first.
HEAD_STRIP_PATTERNS: tuple[str, ...] = (
    " of cyrene",
    " of soli",
    " of samos",
    " of citium",
    " of athens",
    " of rhodes",
    " of tyre",
    " of larissa",
    " of carthage",
    " of jerusalem",
    " of alexandria",
    " of constantinople",
    " of nyssa",
    " of nazianzus",
    " of antioch",
    " of caesarea",
    " of milan",
    " of stridon",
    " of laodicea",
    " of cyrrhus",
    " of aphrodisias",
    " of mopsuestia",
    " of poitiers",
    " of madaura",
    " of madaure",
    " of cilicia",
    " of paphlagonia",
    " of pisidia",
    " of seleucia",
    " of soli",
    " of cyzicus",
    " of phlius",
    " of pitane",
    " of chaeronea",
    " of cyrene",
    " of elis",
    " of stagira",
    " of hippo",
    " of hierapolis",
    " of apamea",
    " of pergamon",
    " of nicomedia",
    " of damascus",
    " of byzantium",
    " d'alexandrie",
    " d'athenes",
    " d'athènes",
    " de cyrène",
    " de cyrene",
    " de citium",
    " de soles",
    " de soli",
    " de samos",
    " de rhodes",
    " de tyre",
    " de tyr",
    " de jérusalem",
    " de jerusalem",
    " de carthage",
    " de constantinople",
    " de chéronée",
    " de cheronee",
    " de nazianze",
    " de nysse",
    " de césarée",
    " de cesaree",
    " d'aphrodise",
    " d'aphrodisias",
    " l'épicurien",
    " l'epicurien",
    " le cynique",
    " le stoïcien",
    " le stoicien",
    " le philosophe",
    " le confesseur",
    " ier",
    " i^er",
    " i de constantinople",
    " ii de constantinople",
)


# ---------------------------------------------------------------------------
# IO helpers
# ---------------------------------------------------------------------------


def load_nodes() -> list[dict[str, Any]]:
    with NODES_PATH.open() as fh:
        return [json.loads(line) for line in fh if line.strip()]


def load_edges() -> list[dict[str, Any]]:
    with EDGES_PATH.open() as fh:
        return [json.loads(line) for line in fh if line.strip()]


def write_edges(edges: list[dict[str, Any]]) -> None:
    with EDGES_PATH.open("w") as fh:
        for e in edges:
            fh.write(json.dumps(e, ensure_ascii=False) + "\n")


def node_id(n: dict[str, Any]) -> str:
    """Return the canonical node identifier used in edges.

    Some legacy synthesis nodes have ``node_id`` set to a different
    value from ``id`` (e.g. ``node_id = "concept_cic_fat_index"``
    but ``id = "synthesis_cic_fat_index"``). Existing edges and the
    RDF exporter use the ``id`` field, so we mirror that to keep
    edges joinable and SHACL invariants conformant.
    """
    return n.get("id") or n.get("node_id") or ""


def edge_signature(e: dict[str, Any]) -> tuple[str, str, str]:
    src = e.get("source") or e.get("source_id") or ""
    tgt = e.get("target") or e.get("target_id") or ""
    rel = e.get("relation") or ""
    return (src, rel, tgt)


def make_snapshot() -> None:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    snap_nodes = SNAPSHOT_DIR / "nodes.jsonl"
    snap_edges = SNAPSHOT_DIR / "edges.jsonl"
    if snap_nodes.exists() and snap_edges.exists():
        print(f"[snapshot] already exists at {SNAPSHOT_DIR.relative_to(ROOT)} - skip")
        return
    shutil.copy2(NODES_PATH, snap_nodes)
    shutil.copy2(EDGES_PATH, snap_edges)
    print(f"[snapshot] written to {SNAPSHOT_DIR.relative_to(ROOT)}")


# ---------------------------------------------------------------------------
# Normalisation & label index
# ---------------------------------------------------------------------------


def norm_text(s: str) -> str:
    """NFKD-normalise and lower-case. Keeps Greek diacritics intact
    (NFKD on a precomposed Greek char *does* split, but lower-casing
    leaves the decomposed sequence ; ``re.search`` with ``\\b``
    handles the combining marks transparently because Python's
    ``re`` treats them as part of the word run)."""
    return unicodedata.normalize("NFKD", s).lower()


def is_eligible_label(label: str) -> bool:
    n = norm_text(label)
    if len(n) < MIN_LABEL_LEN:
        return False
    if n in LABEL_STOPWORDS:
        return False
    # Require at least one alpha character (filter out e.g. "123.4").
    return re.search(r"[^\W\d_]", n) is not None


def derive_head_tokens(label: str, node_type: str) -> list[str]:
    """Derive shorter, more matchable forms from a label.

    For ``person`` nodes : strip common locative suffixes ("of
    Cyrene", "de Tyr") and "Saint"/"Pope" prefixes. For ``work``
    nodes : if the label is "Author, Work Title", peel off the
    author prefix.

    For ``concept``/``argument`` nodes the full label is usually
    the right key, so we do not derive head tokens (would create
    spurious matches on e.g. "fate" as a substring of many things).

    Returns the list of *additional* forms to index alongside the
    canonical label. Each form is later filtered through
    ``is_eligible_label`` again so length & stopword guards apply.
    """
    if node_type not in {"person", "work"}:
        return []
    n = norm_text(label)
    derived: list[str] = []
    if node_type == "person":
        cur = n
        # Strip "saint "/"sainte "/"st. " prefix
        cur = re.sub(r"^(saint|sainte|st\.?|pope|pape|papa|empereur|emperor)\s+", "", cur)
        # Strip locative suffixes
        for pat in HEAD_STRIP_PATTERNS:
            if cur.endswith(pat):
                cur = cur[: -len(pat)].rstrip()
                break
        # If the result is multi-word, also keep just the last token
        # (e.g. "diogenes laertius" -> also "laertius"). But ONLY if
        # the last token is itself >= 6 chars to avoid trivia.
        if cur and cur != n:
            derived.append(cur)
        parts = cur.split()
        if len(parts) > 1 and len(parts[-1]) >= 6:
            derived.append(parts[-1])
    elif node_type == "work":
        # If label contains ", " split and keep the part after it
        # (typically the work title)
        if ", " in n:
            after = n.split(", ", 1)[1].strip()
            if after:
                derived.append(after)
    # Strip leading articles
    cleaned: list[str] = []
    for d in derived:
        d2 = re.sub(r"^(le|la|les|l'|the|der|die|das|il|i|gli|le)\s+", "", d).strip()
        if d2:
            cleaned.append(d2)
    return cleaned


def parse_alt_names(raw: Any) -> list[str]:
    if isinstance(raw, list):
        return [a for a in raw if isinstance(a, str)]
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [a for a in parsed if isinstance(a, str)]
        except json.JSONDecodeError:
            return []
    return []


def build_label_index(
    nodes_by_id: dict[str, dict[str, Any]],
    edge_counts: dict[str, int],
) -> dict[str, list[tuple[str, str, str, int]]]:
    """Return mapping ``normalised_label -> list of (node_id, type,
    original_label, edge_count)``. Multiple nodes can share a
    label."""
    idx: dict[str, list[tuple[str, str, str, int]]] = defaultdict(list)
    for nid, n in nodes_by_id.items():
        t = n.get("type")
        if t not in ALLOWED_TARGET_TYPES:
            continue
        candidates: list[str] = []
        label = n.get("label") or ""
        if label:
            candidates.append(label)
        candidates.extend(parse_alt_names(n.get("alternative_names")))
        # Derive shorter matchable forms (e.g. "Carneades" from
        # "Carneades of Cyrene") for person & work nodes.
        head_forms: list[str] = []
        if label and t in {"person", "work"}:
            head_forms.extend(derive_head_tokens(label, t or ""))
        for alt in parse_alt_names(n.get("alternative_names")):
            if t in {"person", "work"}:
                head_forms.extend(derive_head_tokens(alt, t or ""))
        # Inject curated cross-lingual aliases (French/Greek/Latin
        # forms not present in the node's stored alternative_names).
        head_forms.extend(MANUAL_ALIASES.get(nid, []))
        for lbl in candidates + head_forms:
            if not is_eligible_label(lbl):
                continue
            key = norm_text(lbl)
            # Avoid registering the same (node, key) twice (head
            # form might coincide with the canonical label).
            existing_for_key = idx[key]
            if any(entry[0] == nid for entry in existing_for_key):
                continue
            idx[key].append((nid, t or "", lbl, edge_counts.get(nid, 0)))
    return idx


# ---------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------


def find_matches(
    desc: str,
    label_index: dict[str, list[tuple[str, str, str, int]]],
    self_id: str,
) -> list[tuple[str, str, str, int, int]]:
    """For a given description, return matched (node_id, type,
    matched_label, label_len, target_degree) tuples. Each match is
    counted at most once per node_id (longest match wins for that
    node)."""
    desc_n = norm_text(desc)
    seen_nodes: dict[str, tuple[str, str, int, int]] = {}
    for nl, entries in label_index.items():
        # word-boundary match, anchored
        if not re.search(rf"\b{re.escape(nl)}\b", desc_n):
            continue
        for nid, ntype, original, degree in entries:
            if nid == self_id:
                continue
            prev = seen_nodes.get(nid)
            # Keep the longest matched label per target.
            if prev is None or len(nl) > prev[2]:
                seen_nodes[nid] = (ntype, original, len(nl), degree)
    return [
        (nid, ntype, original, lbl_len, degree)
        for nid, (ntype, original, lbl_len, degree) in seen_nodes.items()
    ]


def jaccard(a: str, b: str) -> float:
    sa = set(a.split())
    sb = set(b.split())
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def rank_and_cap(
    matches: list[tuple[str, str, str, int, int]],
    cap: int,
) -> list[tuple[str, str, str, int, int]]:
    """Rank by (label_length DESC, target_degree DESC), then drop
    candidates whose normalised label overlaps with an already-kept
    one by Jaccard >= 0.8 (avoids linking both "Aristote" and
    "Aristotelian" / similar near-duplicates)."""
    ranked = sorted(matches, key=lambda m: (-m[3], -m[4], m[0]))
    kept: list[tuple[str, str, str, int, int]] = []
    kept_norm_labels: list[str] = []
    for m in ranked:
        nl = norm_text(m[2])
        if any(jaccard(nl, kn) >= 0.8 for kn in kept_norm_labels):
            continue
        kept.append(m)
        kept_norm_labels.append(nl)
        if len(kept) >= cap:
            break
    return kept


# ---------------------------------------------------------------------------
# Edge construction
# ---------------------------------------------------------------------------


def build_edge(
    source: str,
    target: str,
    matched_label: str,
) -> dict[str, Any]:
    metadata = {
        "wave": WAVE_TAG,
        "confidence": 0.5,
        "auto_linked_from_description": True,
        "matched_label": matched_label,
    }
    return {
        "created_at": NOW_ISO,
        "edge_id": str(uuid.uuid4()),
        "metadata": json.dumps(metadata, ensure_ascii=False),
        "relation": "discusses",
        "source": source,
        "source_id": source,
        "target": target,
        "target_id": target,
        "weight": 0.6,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    print(f"[wave-l] start :: wave={WAVE_TAG}")

    make_snapshot()

    nodes = load_nodes()
    edges = load_edges()
    print(f"[load] nodes={len(nodes):,} ; edges={len(edges):,}")

    nodes_by_id: dict[str, dict[str, Any]] = {node_id(n): n for n in nodes}

    # Count outgoing edges per source (semantic + non-semantic).
    edge_counts: dict[str, int] = defaultdict(int)
    edge_counts_semantic: dict[str, int] = defaultdict(int)
    edges_sigs: set[tuple[str, str, str]] = set()
    for e in edges:
        src = e.get("source") or e.get("source_id") or ""
        rel = e.get("relation") or ""
        tgt = e.get("target") or e.get("target_id") or ""
        if src:
            edge_counts[src] += 1
            if rel in LINK_RELATIONS:
                edge_counts_semantic[src] += 1
        edges_sigs.add((src, rel, tgt))

    syntheses = [n for n in nodes if n.get("type") == "synthesis"]
    print(f"[wave-l] syntheses_audited={len(syntheses)}")

    # Identify thin syntheses : fewer than THIN_THRESHOLD outgoing
    # semantic edges.
    thin_syntheses = [
        s
        for s in syntheses
        if edge_counts_semantic.get(node_id(s), 0) < THIN_THRESHOLD
    ]
    print(f"[wave-l] thin_syntheses={len(thin_syntheses)}")

    label_index = build_label_index(nodes_by_id, edge_counts)
    print(f"[wave-l] label_index_size={len(label_index)}")

    new_edges: list[dict[str, Any]] = []
    skipped_existing = 0
    per_synth_added: dict[str, int] = {}
    inserted_samples: list[dict[str, Any]] = []

    for s in thin_syntheses:
        sid = node_id(s)
        desc = s.get("description") or ""
        if not desc:
            continue
        matches = find_matches(desc, label_index, sid)
        if not matches:
            continue
        # Existing semantic outgoing — leave room for at most
        # MAX_LINKS_PER_SYNTHESIS new edges (we don't push past the
        # cap even on a second / third run because the cap is per
        # *new* insertion ; existing edges remain).
        kept = rank_and_cap(matches, MAX_LINKS_PER_SYNTHESIS)
        added_here = 0
        for nid, ntype, matched_label, _lbl_len, _degree in kept:
            sig = (sid, "discusses", nid)
            if sig in edges_sigs:
                skipped_existing += 1
                continue
            edge = build_edge(source=sid, target=nid, matched_label=matched_label)
            new_edges.append(edge)
            edges_sigs.add(sig)
            added_here += 1
            inserted_samples.append(
                {
                    "synthesis_id": sid,
                    "synthesis_label": (s.get("label") or "")[:120],
                    "target_id": nid,
                    "target_type": ntype,
                    "matched_label": matched_label,
                }
            )
        if added_here:
            per_synth_added[sid] = added_here

    print(f"[wave-l] discusses_edges_added={len(new_edges)}  edges_skipped_existing={skipped_existing}")

    if thin_syntheses:
        avg = sum(per_synth_added.get(node_id(s), 0) for s in thin_syntheses) / len(
            thin_syntheses
        )
        print(f"[wave-l] avg_edges_per_thin_synthesis={avg:.2f}")
    else:
        print("[wave-l] avg_edges_per_thin_synthesis=0.00")

    # Top 10 high-yield syntheses
    top = sorted(per_synth_added.items(), key=lambda kv: -kv[1])[:10]
    if top:
        print("[wave-l] top 10 high-yield syntheses:")
        for sid, n_added in top:
            label = (nodes_by_id[sid].get("label") or "")[:90]
            print(f"  {n_added:>2}x  {sid:<60}  {label}")

    # Persist edges
    if new_edges:
        edges.extend(new_edges)
        write_edges(edges)
        print(f"[write] edges={len(edges):,} (+{len(new_edges)})")
    else:
        print("[write] no changes - file untouched")

    # Manual review sample. To stay idempotent across re-runs the
    # sample is drawn from ALL ``auto_linked_from_description=true``
    # edges currently in the graph (not just the ones added this
    # call). The seed is deterministic so the same edge-set produces
    # the same sample.
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    all_auto_linked: list[dict[str, Any]] = []
    for e in edges:
        if e.get("relation") != "discusses":
            continue
        meta_raw = e.get("metadata")
        if isinstance(meta_raw, str):
            try:
                meta = json.loads(meta_raw)
            except json.JSONDecodeError:
                continue
        elif isinstance(meta_raw, dict):
            meta = meta_raw
        else:
            continue
        if not meta.get("auto_linked_from_description"):
            continue
        if meta.get("wave") != WAVE_TAG:
            continue
        src = e.get("source") or e.get("source_id") or ""
        tgt = e.get("target") or e.get("target_id") or ""
        src_node = nodes_by_id.get(src) or {}
        tgt_node = nodes_by_id.get(tgt) or {}
        all_auto_linked.append(
            {
                "synthesis_id": src,
                "synthesis_label": (src_node.get("label") or "")[:120],
                "target_id": tgt,
                "target_type": tgt_node.get("type") or "",
                "matched_label": meta.get("matched_label") or "",
            }
        )
    rng = random.Random(20260516)
    if all_auto_linked:
        sample = rng.sample(all_auto_linked, k=min(20, len(all_auto_linked)))
    else:
        sample = []
    review_payload = {
        "wave": WAVE_TAG,
        "generated_at": NOW_ISO,
        "total_inserted_this_run": len(new_edges),
        "total_auto_linked_in_graph": len(all_auto_linked),
        "sample_size": len(sample),
        "instructions": (
            "Each entry is one auto-inserted discusses edge "
            "(synthesis -> target). Flag false positives so the wave-L "
            "script can be re-run with the bad matched_labels added to "
            "LABEL_STOPWORDS. Confidence is 0.5 by default and the "
            "metadata flag `auto_linked_from_description: true` makes "
            "bulk-revert easy."
        ),
        "samples": sample,
    }
    REVIEW_SAMPLE_PATH.write_text(
        json.dumps(review_payload, ensure_ascii=False, indent=2) + "\n"
    )
    print(
        f"[wave-l] manual_review_sample_written={REVIEW_SAMPLE_PATH.relative_to(ROOT)}"
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
