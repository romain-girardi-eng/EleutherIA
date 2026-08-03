#!/usr/bin/env python3
"""Phase B — Deduplicate publication nodes — 2026-05-18.

Audit detected 36 (surname, year) groups of publications with >1 node in
``data/kg/nodes.jsonl`` (the task spec mentioned 27 paires; our re-detection
found 36 raw groups, of which:

  - 15 are TRUE_DUPLICATE pairs (same publication, different IDs)
  - 1 contains a TRUE_DUPLICATE 3-way (Bobichon 2003 Dialogue Tryphon, 3 of 4)
  - 1 contains a TRUE_DUPLICATE pair inside a 3-way (Bobzien 1998: 2 pairs
    for 2 distinct publications; we merge each pair)
  - 18 are DISTINCT_PUBLICATIONS (same author+year, different works)
  - 2 are AMBIGUOUS (need human review — pub_long_1988 wrong-attribution,
    Crouzel 1962 typo pair w/o canonical pub_*).

For each TRUE_DUPLICATE we:
  1. Choose the canonical node (preference: ``pub_*`` over ``scholarly_work_*``,
     then longer description, then richer metadata blob).
  2. Merge metadata (canonical wins on conflict, non-empty shell fields fill
     canonical empties; lists are unioned).
  3. Take the longest description.
  4. Redirect ALL incident edges from each shell to the canonical, dedup'd by
     ``(source, target, relation)`` and dropping self-loops.
  5. Flag each shell ``metadata.deprecated = true``,
     ``metadata.superseded_by = <canonical_id>``,
     ``metadata.phase_b_merged_at = "2026-05-18"``.
     Shells are KEPT in the JSONL (preserves hypothetical citation links).
  6. Stamp ``metadata.phase_b_dedupe_2026_05_18 = true`` on every touched node.

DRY-RUN by default. Pass ``--commit`` to write to disk.

Snapshot location:
  data/kg/snapshots/2026-05-18-pre-phase-b-dedupe/{nodes,edges}.jsonl

Idempotence:
  - Shells already marked ``deprecated`` are detected and skipped.
  - Edges already redirected (i.e. canonical already has the equivalent edge)
    are de-duplicated by the (source, target, relation) signature.
  - Re-running with ``--commit`` after a successful run is a no-op.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
NODES_PATH = REPO_ROOT / "data" / "kg" / "nodes.jsonl"
EDGES_PATH = REPO_ROOT / "data" / "kg" / "edges.jsonl"
SNAPSHOT_DIR = REPO_ROOT / "data" / "kg" / "snapshots" / "2026-05-18-pre-phase-b-dedupe"

PATCH_MARKER = "phase_b_dedupe_2026_05_18"
MERGE_DATE = "2026-05-18"


# -----------------------------------------------------------------------------
# Decision matrix
# -----------------------------------------------------------------------------
# Each MERGE entry: {canonical, shells: [shell_ids...], reason: human-readable}
# DISTINCT entries are documented but not acted upon.
# AMBIGUOUS entries are flagged and require Romain's review.

MERGES: list[dict[str, Any]] = [
    # ------------------- 1-to-1 trivial duplicates (same title) -------------------
    {
        "name": "Bobzien 2000 — Did Epicurus Discover the Free Will Problem? (OSAP 19)",
        "canonical": "pub_bobzien_2000_epicurus_free_will",
        "shells": ["scholarly_work_bobzien_2000_inadvertent"],
        "reason": (
            "Same Phronesis/OSAP paper. Shell slug 'inadvertent' is misleading "
            "(that slug belongs to the 1998 paper); shell label/desc/meta confirm "
            "it's the 2000 Epicurus paper. Canonical pub_* has full Zotero metadata."
        ),
    },
    {
        "name": "Boys-Stones 2007 — Middle Platonists on Fate and Human Autonomy",
        "canonical": "pub_boysstones_2007_middle_platonists",
        "shells": ["scholarly_work_boys_stones_2007_middle_platonists_on_fate_and_human_auto"],
        "reason": (
            "Same chapter in BICS Suppl. 94 (Sharples & Sorabji eds.). Canonical "
            "pub_* has richer description and ICS publisher metadata. "
            "pub_boys_stones_2007_origen is a DISTINCT publication (Severan Culture vol.)."
        ),
    },
    {
        "name": "Byerly 2017 — Free Will Theodicies for Theological Determinists",
        "canonical": "pub_byerly_2017_freewill_theodicies_theological_determinists",
        "shells": ["scholarly_work_byerly_2017_free_will_theodicies_for_theological_det"],
        "reason": "Same Sophia 56 article. Canonical pub_* preferred per convention.",
    },
    {
        "name": "Chamberlain 1984 — The Meaning of Prohairesis in Aristotle's Ethics",
        "canonical": "pub_chamberlain_1984_prohairesis",
        "shells": ["scholarly_work_chamberlain_1984_the_meaning_of_prohairesis_in_aristotle_"],
        "reason": "Same article. pub_* canonical convention.",
    },
    {
        "name": "Crouzel 1956 — Théologie de l'image de Dieu chez Origène",
        "canonical": "pub_crouzel_1956_origine",
        "shells": ["scholarly_work_crouzel_1956_th_ologie_de_l_image_de_dieu_chez_orig_n"],
        "reason": "Same monograph (Aubier 1956). pub_* canonical convention.",
    },
    {
        "name": "Donini 2010 — Aristotle and Determinism",
        "canonical": "pub_donini_2010_aristotle_determinism",
        "shells": ["scholarly_work_donini_2010_aristotle_and_determinism"],
        "reason": "Same publication. pub_* canonical convention.",
    },
    {
        "name": "Eliasson 2008 — Notion of That Which Depends on Us in Plotinus",
        "canonical": "pub_eliasson_2008_notion_eph_hemin_plotinus",
        "shells": ["scholarly_work_eliasson_2008_the_notion_of_that_which_depends_on_us_i"],
        "reason": "Same Brill monograph. pub_* canonical convention.",
    },
    {
        "name": "Frankfurt 1971 — Freedom of the Will and the Concept of a Person",
        "canonical": "pub_frankfurt_1971_freedom_will_person",
        "shells": ["scholarly_work_frankfurt_1971_freedom_of_the_will_and_the_concept_of_a"],
        "reason": "Same J. Philos. 68/1 article. pub_* canonical convention.",
    },
    {
        "name": "Frede 1982 — The Dramatization of Determinism (Alexander De Fato)",
        "canonical": "pub_frede_1982_dramatization",
        "shells": ["scholarly_work_frede_1982_the_dramatization_of_determinism_alexand"],
        "reason": "Same Phronesis article. pub_* canonical convention.",
    },
    {
        "name": "Hausmann & Noller 2021 — Free Will: Historical and Analytic Perspectives",
        "canonical": "pub_hausmann_noller_2021_free_will_perspectives",
        "shells": ["scholarly_work_hausmann_2021_free_will_historical_and_analytic_perspe"],
        "reason": "Same Palgrave edited volume. pub_* canonical (records both editors).",
    },
    {
        "name": "Hick 1966 — Evil and the God of Love",
        "canonical": "pub_hick_1966_evil_god_of_love",
        "shells": ["scholarly_work_hick_1966_evil_and_the_god_of_love"],
        "reason": "Same Macmillan monograph. pub_* canonical convention.",
    },
    {
        "name": "Irwin 1992 — Who Discovered the Will?",
        "canonical": "pub_irwin_1992_who_discovered_will",
        "shells": ["scholarly_work_irwin_1992_who_discovered_the_will"],
        "reason": "Same Philosophical Perspectives article. pub_* canonical convention.",
    },
    {
        "name": "Jewett 2007 — Romans: A Commentary (Hermeneia)",
        "canonical": "scholarly_work_jewett_2007_romans_a_commentary_hermeneia_series",
        "shells": ["scholarly_work_jewett_2007_romans_a_commentary"],
        "reason": (
            "Same Hermeneia commentary; both are scholarly_work_* (no pub_* exists). "
            "Canonical = the one whose ID explicitly names the series."
        ),
    },
    {
        "name": "Kahn 1988 — Discovering the Will: From Aristotle to Augustine",
        "canonical": "pub_kahn_1988_discovering_will",
        "shells": ["scholarly_work_kahn_1988_discovering_will"],
        "reason": (
            "Same chapter in Dillon & Long (eds.) UCP 1988. Canonical has 5 verified_critiques, "
            "local_pdf_path, page-level critiques. Shell is bare. pub_long_1988_discovering_will "
            "is FLAGGED AMBIGUOUS — see notes."
        ),
    },
    {
        "name": "Karamanolis 2021 — The Philosophy of Early Christianity (2nd ed.)",
        "canonical": "pub_karamanolis_2021_philosophy_early_christianity",
        "shells": ["scholarly_work_karamanolis_2021_the_philosophy_of_early_christianity"],
        "reason": "Same Routledge 2nd ed. pub_* canonical convention.",
    },
    {
        "name": "Linjamaa 2019 — Ethics of The Tripartite Tractate (NHC I, 5)",
        "canonical": "pub_linjamaa_2019_ethics_tripartite_tractate",
        "shells": ["scholarly_work_linjamaa_2019_the_ethics_of_the_tripartite_tractate_nh"],
        "reason": "Same Brill NHMS 95 monograph. pub_* canonical convention.",
    },
    {
        "name": "Minns & Parvis 2009 — Justin, Philosopher and Martyr: Apologies (OECT)",
        "canonical": "pub_minns_parvis_2009_justin_apologies",
        "shells": ["scholarly_work_minns_2009_justin_philosopher_and_martyr_apologies"],
        "reason": "Same OECT edition. Canonical pub_* records both editors.",
    },
    {
        "name": "Nadelhoffer & Monroe 2022 — Advances in Exp. Phil. of Free Will",
        "canonical": "pub_nadelhoffer_monroe_2022_exp_phil_free_will",
        "shells": ["scholarly_work_nadelhoffer_2022_advances_in_experimental_philosophy_of_f"],
        "reason": "Same Bloomsbury edited volume. Canonical pub_* records both editors.",
    },
    {
        "name": "Ramelli 2014 — Alexander of Aphrodisias: a source of Origen's philosophy?",
        "canonical": "pub_ramelli_2014_alexander_origen",
        "shells": ["scholarly_work_ramelli_2014_alexander_of_aphrodisias_a_source_of_ori"],
        "reason": "Same article. pub_* canonical convention.",
    },
    {
        "name": "Salles 2005 — The Stoics on Determinism and Compatibilism",
        "canonical": "scholarly_work_salles_2005_the_stoics_on_determinism_and_compatibil",
        "shells": ["scholarly_work_salles_2005_stoics_determinism"],
        "reason": (
            "Same Ashgate edited volume; both scholarly_work_*. Canonical = the one "
            "with non-empty out-edges (4 vs 0) and full title in ID."
        ),
    },
    {
        "name": "Sharples 1983 — Alexander of Aphrodisias On Fate (Duckworth)",
        "canonical": "pub_sharples_1983_alexander_fate",
        "shells": ["scholarly_work_sharples_1983_alex_de_fato"],
        "reason": (
            "Same Duckworth 1983 edition+translation+commentary. Canonical pub_* "
            "carries the 26 outgoing edges; shell has 0."
        ),
    },
    {
        "name": "Sharples 2008 — L'accident du déterminisme: Alexandre d'Aphrodise",
        "canonical": "pub_sharples_2008_accident_determinisme",
        "shells": ["scholarly_work_sharples_2008_l_accident_du_d_terminisme_alexandre_d_a"],
        "reason": "Same French chapter. pub_* canonical convention.",
    },
    {
        "name": "Sommers 2010 — Experimental Philosophy and Free Will",
        "canonical": "pub_sommers_2010_experimental_philosophy",
        "shells": ["scholarly_work_sommers_2010_experimental_philosophy_and_free_will"],
        "reason": "Same Philosophy Compass article. pub_* canonical convention.",
    },
    {
        "name": "Sorabji 1980 — Necessity, Cause and Blame (Aristotle's Theory)",
        "canonical": "pub_sorabji_1980_necessity_cause_blame",
        "shells": ["scholarly_work_sorabji_1980_necessity"],
        "reason": "Same Duckworth monograph. pub_* canonical convention.",
    },
    {
        "name": "Still & Wilhite 2024 — The Apologists and Paul",
        "canonical": "pub_still_wilhite_2024_apologists_paul",
        "shells": ["scholarly_work_still_2024_the_apologists_and_paul"],
        "reason": "Same Bloomsbury edited volume. Canonical pub_* records both editors.",
    },
    {
        "name": "Voelke 1973 — L'idée de volonté dans le Stoïcisme",
        "canonical": "pub_voelke_1973_idee_volonte",
        "shells": ["scholarly_work_voelke_1973_l_id_e_de_volont_dans_le_sto_cisme"],
        "reason": "Same PUF monograph. pub_* canonical convention.",
    },
    # ------------------- multi-way merges -------------------
    {
        "name": "Bobichon 2003 — Justin Martyr: Dialogue avec Tryphon (Paradosis 47/1-2)",
        "canonical": "pub_bobichon_2003_justin_dialogue_tryphon",
        "shells": [
            "scholarly_work_bobichon_2003_justin_martyr_dialogue_avec_le_tryphon_d",
            "scholarly_work_bobichon_2003_justin_martyr_dialogue_avec_tryphon_diti",
        ],
        "reason": (
            "Three of the 4 nodes name the same 2-vol. Paradosis 47/1-2 edition "
            "(ISBN 9782827109586). Canonical pub_* has fullest description "
            "(1146 pp., apparatus, etc.). The 'volume 1' / 'volume 2' shells "
            "are not separate publications — they are the two parts of one "
            "edition counted twice. NOT merged: scholarly_work_bobichon_2003_uvres_"
            "de_justin_martyr_le_manuscrit_loan = the DISTINCT Scriptorium "
            "article on the British Library ms Loan 36/13 (pp. 157-172)."
        ),
    },
    {
        "name": "Bobzien 1998 — The Inadvertent Conception... (Phronesis 43/2)",
        "canonical": "pub_bobzien_1998_inadvertent",
        "shells": ["scholarly_work_bobzien_1998_the_inadvertent_conception_and_late_birt"],
        "reason": (
            "Same Phronesis 43/2 article. Canonical pub_* has 22 outgoing edges; "
            "shell has 1. NOT merged with the book pair (see next entry)."
        ),
    },
    {
        "name": "Bobzien 1998 — Determinism and Freedom in Stoic Philosophy (OUP book)",
        "canonical": "scholarly_work_bobzien_1998_determinism_and_freedom_in_stoic_philoso",
        "shells": ["scholarly_work_bobzien_1998_determinism"],
        "reason": (
            "Same OUP 1998 monograph; both scholarly_work_* (no pub_* exists). "
            "Canonical = the one with explicit full title + 1 outgoing edge. "
            "NOT merged with the Phronesis article — distinct publication, same year."
        ),
    },
    {
        "name": "Crouzel 1962 — Origène et la philosophie",
        "canonical": "scholarly_work_crouzel_1962_orig_ne_et_la_philosophie",
        "shells": ["scholarly_work_crouzel_1962_origene_et_la_philosophie"],
        "reason": (
            "Same Aubier 1962 monograph; one ID has typo (Origene vs Origène in slug). "
            "Both scholarly_work_*; canonical = the one with proper diacritic encoding "
            "(under_score = é placeholder). Edge counts equal (1 each)."
        ),
    },
    {
        "name": "Destrée, Salles & Zingano 2014 — What is Up to Us? (Academia Verlag)",
        "canonical": "pub_destree_salles_zingano_2014_what_is_up_to_us",
        "shells": ["scholarly_work_destr_e_2014_what_is_up_to_us_studies_on_agency_and_r"],
        "reason": (
            "Same edited volume. Canonical pub_* has 41 outgoing edges, full "
            "publisher (Academia Verlag), 3-editor name. Shell has 0 edges. "
            "NOT merged: pub_destree_2014_plato_er is a DISTINCT chapter "
            "(Destrée's own contribution on the myth of Er) — different work."
        ),
    },
    {
        "name": "Gourinat 2005 — La prohairesis chez Épictète (chapter)",
        "canonical": "pub_gourinat_2005_prohairesis",
        "shells": ["scholarly_work_gourinat_2005_la_prohairesis_chez_pict_te_d_cision_vol"],
        "reason": (
            "Same chapter. Canonical pub_* has 5 outgoing edges; shell has 1. "
            "NOT merged: pub_gourinat_2005_stoiciens is a DISTINCT monograph "
            "(Les Stoïciens, PUF) by the same author same year."
        ),
    },
]

# Distinct publications (documented for the report, no action)
DISTINCT_GROUPS: list[dict[str, Any]] = [
    {
        "name": "Boys-Stones 2007 — Severan Culture chapter (Cambridge UP)",
        "nodes": ["pub_boys_stones_2007_origen"],
        "note": "Different from the BICS chapter — different volume, different topic.",
    },
    {
        "name": "Destrée 2014 — Mythe d'Er chapter",
        "nodes": ["pub_destree_2014_plato_er"],
        "note": "Destrée's own chapter, not the edited volume.",
    },
    {
        "name": "Dettwiler 2008 — 3 chapters (Colossiens, Éphésiens, 2 Thessaloniciens)",
        "nodes": [
            "scholarly_work_dettwiler_2008_l_p_tre_aux_colossiens",
            "scholarly_work_dettwiler_2008_l_p_tre_aux_eph_siens",
            "scholarly_work_dettwiler_2008_la_deuxi_me_p_tre_aux_thessaloniciens",
        ],
        "note": "Three distinct chapters in Labor et Fides 2008 volume (pp. 287-299, 301-314, 315-326).",
    },
    {
        "name": "Dettwiler 2009 — 2 distinct articles",
        "nodes": [
            "scholarly_work_dettwiler_2009_d_mystification_c_leste_la_fonction_argu",
            "scholarly_work_dettwiler_2009_enthousiasme_religieux_dans_rm",
        ],
        "note": "Cerf 'Démystification céleste' vs Peeters 'Enthousiasme religieux dans Rm 6?'.",
    },
    {
        "name": "Dettwiler 2012 — 2 distinct chapters (Colossiens, Éphésiens)",
        "nodes": [
            "scholarly_work_dettwiler_2012_ep_tre_aux_colossiens",
            "scholarly_work_dettwiler_2012_ep_tre_aux_eph_siens",
        ],
        "note": "Two chapters in Bayard & Labor et Fides 2012 volume (pp. 891-910, 845-867).",
    },
    {
        "name": "Dodson 2017 — 2 distinct publications",
        "nodes": [
            "scholarly_work_dodson_2017_paul_and_seneca_in_dialogue",
            "scholarly_work_dodson_2017_paul_and_the_greco_roman_philosophical_t",
        ],
        "note": "Brill 'Paul and Seneca in Dialogue' (ISBN 9789004341357) vs T&T Clark/Bloomsbury 'Paul and the Greco-Roman Philosophical Tradition' (322 pp).",
    },
    {
        "name": "Fürst 2019 — 2 distinct edited volumes (Adamantiana 13 & 21)",
        "nodes": [
            "pub_furst_2019_concepts_origenism_ad13",
            "pub_furst_2019_perspectives_origen_ad21",
        ],
        "note": "Two separate volumes of the Adamantiana series.",
    },
    {
        "name": "Gourinat 2005 — Les Stoïciens (monograph)",
        "nodes": ["pub_gourinat_2005_stoiciens"],
        "note": "PUF monograph, distinct from the prohairesis chapter.",
    },
]

# Ambiguous — flag for Romain, do not touch
AMBIGUOUS_GROUPS: list[dict[str, Any]] = [
    {
        "name": "Long 1988 — Discovering the Will (likely wrong attribution)",
        "nodes": ["pub_long_1988_discovering_will"],
        "issue": (
            "Label 'Discovering the Will: From Aristotle to Augustine (Long)' — but "
            "this title is Kahn's 1988 chapter. A. A. Long was an EDITOR of the volume "
            "'The Question of Eclecticism' (1988), not the author of this chapter. "
            "Recommend: mark this node with metadata.wrong_attribution = true and "
            "either delete or repoint its single edge to pub_kahn_1988_discovering_will. "
            "DO NOT auto-merge — needs Romain to confirm whether Long actually wrote a "
            "separate piece with similar title."
        ),
    },
]


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------


def parse_metadata(node: dict[str, Any]) -> dict[str, Any]:
    md = node.get("metadata")
    if md is None or md == "":
        return {}
    if isinstance(md, dict):
        return md
    try:
        return json.loads(md)
    except (json.JSONDecodeError, TypeError):
        return {}


def serialise_metadata(node: dict[str, Any], md: dict[str, Any]) -> None:
    node["metadata"] = json.dumps(md, ensure_ascii=False)


def is_already_deprecated(node: dict[str, Any]) -> bool:
    md = parse_metadata(node)
    return bool(md.get("deprecated"))


def merge_metadata(canon_md: dict[str, Any], shell_md: dict[str, Any]) -> dict[str, Any]:
    """Canonical wins on conflict; shell fills canonical empties; lists are unioned."""
    out = dict(canon_md)
    for k, v in shell_md.items():
        if k not in out or out[k] in (None, "", [], {}):
            out[k] = v
        elif isinstance(out[k], list) and isinstance(v, list):
            seen = set()
            unioned: list[Any] = []
            for item in list(out[k]) + list(v):
                key = json.dumps(item, sort_keys=True, ensure_ascii=False, default=str)
                if key not in seen:
                    seen.add(key)
                    unioned.append(item)
            out[k] = unioned
    return out


def longest_desc(*candidates: str | None) -> str:
    valid = [c for c in candidates if c and isinstance(c, str)]
    if not valid:
        return ""
    return max(valid, key=len)


def edge_signature(edge: dict[str, Any]) -> tuple[str, str, str]:
    src = edge.get("source") or edge.get("source_id") or ""
    tgt = edge.get("target") or edge.get("target_id") or ""
    rel = edge.get("relation") or ""
    return (src, tgt, rel)


# -----------------------------------------------------------------------------
# Core
# -----------------------------------------------------------------------------


def snapshot() -> None:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    if not (SNAPSHOT_DIR / NODES_PATH.name).exists():
        shutil.copy2(NODES_PATH, SNAPSHOT_DIR / NODES_PATH.name)
    if not (SNAPSHOT_DIR / EDGES_PATH.name).exists():
        shutil.copy2(EDGES_PATH, SNAPSHOT_DIR / EDGES_PATH.name)


def load_nodes_index() -> tuple[list[str], dict[str, int]]:
    """Return (raw_lines, id->line_index). Preserves byte exactness for unmodified lines."""
    raw_lines = NODES_PATH.read_text(encoding="utf-8").splitlines()
    idx: dict[str, int] = {}
    for i, line in enumerate(raw_lines):
        if not line.strip():
            continue
        try:
            n = json.loads(line)
        except json.JSONDecodeError:
            continue
        nid = n.get("id") or n.get("node_id")
        if nid:
            idx[nid] = i
    return raw_lines, idx


def load_edges() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for line in EDGES_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            out.append(json.loads(line))
    return out


def repoint_edge(edge: dict[str, Any], shell_id: str, canonical_id: str) -> bool:
    """Repoint source/source_id/target/target_id from shell_id to canonical_id.

    Returns True if the edge was modified.
    """
    modified = False
    for field in ("source", "source_id"):
        if edge.get(field) == shell_id:
            edge[field] = canonical_id
            modified = True
    for field in ("target", "target_id"):
        if edge.get(field) == shell_id:
            edge[field] = canonical_id
            modified = True
    return modified


def run(commit: bool) -> int:
    if not NODES_PATH.exists() or not EDGES_PATH.exists():
        print(f"ERROR: missing {NODES_PATH} or {EDGES_PATH}", file=sys.stderr)
        return 2

    print(f"Phase B Dedupe — {'COMMIT' if commit else 'DRY-RUN'} — {MERGE_DATE}\n")

    raw_lines, id_to_line = load_nodes_index()
    edges = load_edges()

    # ---- Plan + validate ----
    plan: list[dict[str, Any]] = []
    skipped: list[str] = []
    missing: list[str] = []

    for merge in MERGES:
        canonical_id = merge["canonical"]
        if canonical_id not in id_to_line:
            missing.append(f"  [MISSING canonical] {merge['name']}: {canonical_id}")
            continue
        canonical_line = raw_lines[id_to_line[canonical_id]]
        canonical_node = json.loads(canonical_line)

        active_shells: list[str] = []
        for shell_id in merge["shells"]:
            if shell_id not in id_to_line:
                missing.append(f"  [MISSING shell]    {merge['name']}: {shell_id}")
                continue
            shell_node = json.loads(raw_lines[id_to_line[shell_id]])
            if is_already_deprecated(shell_node):
                skipped.append(f"  [ALREADY DEPRECATED] {shell_id}")
                continue
            active_shells.append(shell_id)

        if not active_shells:
            continue

        plan.append({
            "name": merge["name"],
            "canonical_id": canonical_id,
            "canonical_node": canonical_node,
            "shells": active_shells,
            "reason": merge["reason"],
        })

    if missing:
        print("WARNINGS:")
        for m in missing:
            print(m)
        print()
    if skipped:
        print("Idempotence — already done:")
        for s in skipped:
            print(s)
        print()

    if not plan:
        print("No merges to apply. (Already done, or canonical/shell missing.)")
        return 0

    # ---- Compute edge redirects + per-shell touch ----
    canonical_edge_sigs: dict[str, set[tuple[str, str, str]]] = {}
    for entry in plan:
        cid = entry["canonical_id"]
        canonical_edge_sigs[cid] = {
            edge_signature(e)
            for e in edges
            if cid in (e.get("source"), e.get("source_id"), e.get("target"), e.get("target_id"))
        }

    edges_redirected = 0
    edges_dropped_dup = 0
    edges_dropped_selfloop = 0
    new_edges: list[dict[str, Any]] = []

    shell_to_canonical: dict[str, str] = {}
    for entry in plan:
        for s in entry["shells"]:
            shell_to_canonical[s] = entry["canonical_id"]

    for edge in edges:
        sig = edge_signature(edge)
        src, tgt, rel = sig
        needs_redirect = src in shell_to_canonical or tgt in shell_to_canonical
        if not needs_redirect:
            new_edges.append(edge)
            continue

        new_edge = dict(edge)
        # nested metadata is a string — keep as is

        for shell_id, canonical_id in shell_to_canonical.items():
            repoint_edge(new_edge, shell_id, canonical_id)

        new_sig = edge_signature(new_edge)
        # Drop self-loops
        if new_sig[0] == new_sig[1]:
            edges_dropped_selfloop += 1
            continue

        # Dedup against canonical's existing edges + edges we already wrote
        cid_relevant = None
        for cid in canonical_edge_sigs:
            if cid in (new_sig[0], new_sig[1]):
                cid_relevant = cid
                break
        if cid_relevant and new_sig in canonical_edge_sigs[cid_relevant]:
            edges_dropped_dup += 1
            continue
        if cid_relevant:
            canonical_edge_sigs[cid_relevant].add(new_sig)

        edges_redirected += 1
        new_edges.append(new_edge)

    # ---- Apply node updates ----
    nodes_updated: dict[int, str] = {}  # line_index -> new json
    for entry in plan:
        cid = entry["canonical_id"]
        canonical_line_idx = id_to_line[cid]
        canonical_node = json.loads(raw_lines[canonical_line_idx])
        canonical_md = parse_metadata(canonical_node)

        # Track descriptions and metadata from shells
        descs = [canonical_node.get("description") or ""]
        for shell_id in entry["shells"]:
            shell_node = json.loads(raw_lines[id_to_line[shell_id]])
            shell_md = parse_metadata(shell_node)
            descs.append(shell_node.get("description") or "")
            canonical_md = merge_metadata(canonical_md, shell_md)

        # Pick longest description
        best_desc = longest_desc(*descs)
        if best_desc and best_desc != canonical_node.get("description"):
            canonical_node["description"] = best_desc

        canonical_md[PATCH_MARKER] = True
        canonical_md["phase_b_merged_at"] = MERGE_DATE
        existing_merged_in = canonical_md.get("merged_in") or []
        if not isinstance(existing_merged_in, list):
            existing_merged_in = [existing_merged_in]
        for s in entry["shells"]:
            if s not in existing_merged_in:
                existing_merged_in.append(s)
        canonical_md["merged_in"] = existing_merged_in
        serialise_metadata(canonical_node, canonical_md)
        nodes_updated[canonical_line_idx] = json.dumps(canonical_node, ensure_ascii=False)

        for shell_id in entry["shells"]:
            sidx = id_to_line[shell_id]
            shell_node = json.loads(raw_lines[sidx])
            shell_md = parse_metadata(shell_node)
            shell_md["deprecated"] = True
            shell_md["deprecated_at"] = MERGE_DATE
            shell_md["deprecated_reason"] = (
                f"Phase B dedupe 2026-05-18: merged into canonical {cid}. "
                f"Reason: {entry['reason'][:200]}"
            )
            shell_md["superseded_by"] = cid
            shell_md["phase_b_merged_at"] = MERGE_DATE
            shell_md[PATCH_MARKER] = True
            serialise_metadata(shell_node, shell_md)
            nodes_updated[sidx] = json.dumps(shell_node, ensure_ascii=False)

    # ---- Report ----
    print(f"Plan: {len(plan)} merges, {sum(len(p['shells']) for p in plan)} shells")
    print(f"  Nodes to update: {len(nodes_updated)}")
    print(f"  Edges to redirect: {edges_redirected}")
    print(f"  Edges dropped (duplicate signature): {edges_dropped_dup}")
    print(f"  Edges dropped (self-loop): {edges_dropped_selfloop}")
    print()
    print("Per-merge breakdown:")
    for entry in plan:
        cid = entry["canonical_id"]
        n_shells = len(entry["shells"])
        n_edges = sum(
            1 for e in edges
            if any(
                s in (e.get("source"), e.get("source_id"), e.get("target"), e.get("target_id"))
                for s in entry["shells"]
            )
        )
        print(f"  - {entry['name']}")
        print(f"    canonical: {cid}")
        print(f"    shells:    {n_shells} -> {entry['shells']}")
        print(f"    edges incident on shells: {n_edges}")

    if AMBIGUOUS_GROUPS:
        print("\nAMBIGUOUS — Romain must review:")
        for a in AMBIGUOUS_GROUPS:
            print(f"  - {a['name']}")
            for n in a["nodes"]:
                print(f"      node: {n}")
            print(f"      issue: {a['issue']}")

    if DISTINCT_GROUPS:
        print(f"\nDISTINCT_PUBLICATIONS (no action): {len(DISTINCT_GROUPS)} groups documented.")

    if not commit:
        print("\nDRY-RUN — no files modified.")
        print(f"Pass --commit to apply and snapshot to {SNAPSHOT_DIR.relative_to(REPO_ROOT)}/.")
        return 0

    # ---- Commit ----
    snapshot()

    new_node_lines = list(raw_lines)
    for idx, new_line in nodes_updated.items():
        new_node_lines[idx] = new_line

    NODES_PATH.write_text("\n".join(new_node_lines) + "\n", encoding="utf-8")

    with EDGES_PATH.open("w", encoding="utf-8") as f:
        for edge in new_edges:
            f.write(json.dumps(edge, ensure_ascii=False) + "\n")

    print(f"\nCOMMIT done. Snapshot saved to {SNAPSHOT_DIR.relative_to(REPO_ROOT)}/.")
    print(f"  nodes.jsonl: {len(nodes_updated)} lines re-serialised, "
          f"{len(raw_lines) - len(nodes_updated)} bytes-exact preserved.")
    print(f"  edges.jsonl: {len(edges)} -> {len(new_edges)} edges "
          f"({edges_dropped_dup} dup, {edges_dropped_selfloop} self-loop dropped).")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Write changes to disk (default: dry-run).",
    )
    args = parser.parse_args(argv)
    return run(commit=args.commit)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
