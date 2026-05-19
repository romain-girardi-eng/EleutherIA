#!/usr/bin/env python3
"""Apply 12 corrections identified by E2 lecteur agents on 2026-05-19.

Idempotent. Run twice → second run reports "nothing to apply" for each correction.

Usage:
  python3 scripts/apply_12_corrections_2026_05_19.py            # dry-run (default)
  python3 scripts/apply_12_corrections_2026_05_19.py --commit   # apply

Always snapshots nodes.jsonl + edges.jsonl to
  data/kg/snapshots/2026-05-19-pre-12-corrections/
before mutation.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
KG_DIR = REPO / "data" / "kg"
NODES_PATH = KG_DIR / "nodes.jsonl"
EDGES_PATH = KG_DIR / "edges.jsonl"
SNAPSHOT_DIR = KG_DIR / "snapshots" / "2026-05-19-pre-12-corrections"
TODAY = "2026-05-19"
MARKER = "corrections_2026_05_19"


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------
def load_jsonl(path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line:
                continue
            out.append(json.loads(line))
    return out


def write_jsonl(path: Path, items: list[dict[str, Any]]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        for item in items:
            fh.write(json.dumps(item, ensure_ascii=False) + "\n")
    tmp.replace(path)


def get_metadata(node_or_edge: dict[str, Any]) -> dict[str, Any]:
    """Metadata may be stored as a stringified JSON or as a dict, depending on
    the writer. Return as a dict (decoded copy)."""
    md = node_or_edge.get("metadata")
    if md is None or md == "":
        return {}
    if isinstance(md, dict):
        return dict(md)
    if isinstance(md, str):
        try:
            return json.loads(md)
        except json.JSONDecodeError:
            return {}
    return {}


def set_metadata(node_or_edge: dict[str, Any], md: dict[str, Any]) -> None:
    """Write metadata back using the same representation it was loaded with."""
    original = node_or_edge.get("metadata")
    if isinstance(original, dict) or original is None or original == "":
        # If the existing format was a dict (or empty), keep it as a string —
        # the file uses stringified metadata throughout. Default to string.
        node_or_edge["metadata"] = json.dumps(md, ensure_ascii=False)
    else:
        node_or_edge["metadata"] = json.dumps(md, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Snapshot
# ---------------------------------------------------------------------------
def snapshot() -> None:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    for src in (NODES_PATH, EDGES_PATH):
        dst = SNAPSHOT_DIR / src.name
        if not dst.exists():
            shutil.copy2(src, dst)


# ---------------------------------------------------------------------------
# Correction tracking
# ---------------------------------------------------------------------------
class Tracker:
    def __init__(self) -> None:
        self.applied: list[str] = []
        self.skipped: list[tuple[str, str]] = []
        self.touched_node_ids: set[str] = set()

    def applied_one(self, label: str) -> None:
        self.applied.append(label)

    def skipped_one(self, label: str, reason: str) -> None:
        self.skipped.append((label, reason))


def mark_touched(node: dict[str, Any], tracker: Tracker) -> None:
    md = get_metadata(node)
    md[MARKER] = True
    md.setdefault(f"{MARKER}_at", TODAY)
    set_metadata(node, md)
    tracker.touched_node_ids.add(node["id"])


def now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Edge helpers
# ---------------------------------------------------------------------------
def build_edge_id() -> str:
    return str(uuid.uuid4())


def find_edge(
    edges: list[dict[str, Any]],
    source: str,
    relation: str,
    target: str,
) -> dict[str, Any] | None:
    for e in edges:
        if e.get("source") == source and e.get("relation") == relation and e.get("target") == target:
            return e
    return None


def new_edge(source: str, relation: str, target: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    eid = build_edge_id()
    md = metadata or {}
    return {
        "created_at": now_iso(),
        "edge_id": eid,
        "metadata": json.dumps(md, ensure_ascii=False) if md else "{}",
        "relation": relation,
        "source": source,
        "source_id": source,
        "target": target,
        "target_id": target,
        "weight": 1.0,
    }


# ---------------------------------------------------------------------------
# Corrections
# ---------------------------------------------------------------------------
def correction_1_donini_mislabel(
    nodes_by_id: dict[str, dict[str, Any]],
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    tracker: Tracker,
) -> None:
    """Donini 1989 Ethos node points at a Huby 1991 review PDF.

    - Flag the existing Donini 1989 node with mislabel_warning + superseded_by.
    - Create pub_huby_1991_review_donini_ethos.
    - Wire authored_by → scholar_huby_pamela.
    """
    label = "1. Donini PDF mislabel (Huby 1991 review)"
    donini_node_id = "scholarly_work_donini_1989_ethos_aristotele_e_il_determinismo"
    huby_node_id = "pub_huby_1991_review_donini_ethos"
    huby_scholar = "scholar_huby_pamela"

    donini = nodes_by_id.get(donini_node_id)
    if donini is None:
        tracker.skipped_one(label, f"node_not_found: {donini_node_id}")
        return

    md = get_metadata(donini)
    already_flagged = md.get("mislabel_warning") and md.get("superseded_by") == huby_node_id
    huby_present = huby_node_id in nodes_by_id
    huby_edge_present = find_edge(edges, huby_node_id, "authored_by", huby_scholar) is not None

    if already_flagged and huby_present and huby_edge_present:
        tracker.skipped_one(label, "already applied (donini flagged + huby node + edge)")
        return

    if not already_flagged:
        md["mislabel_warning"] = (
            "This PDF is actually Huby 1991 review (CR 41/2 pp.370-371), "
            "NOT Donini 1989 Ethos"
        )
        md["superseded_by"] = huby_node_id
        set_metadata(donini, md)
        mark_touched(donini, tracker)

    if not huby_present:
        huby_node = {
            "alternative_names": "[]",
            "created_at": now_iso(),
            "description": (
                "Huby, P.M. (1991). Review of Pier Luigi Donini, "
                "Ethos: Aristotele e il determinismo (Alessandria, "
                "Edizioni dell'Orso, 1989). The Classical Review, 41/2, "
                "pp.370-371. Two-page review. The PDF mislabelled in DOCTORAT as "
                "Donini 1989 Ethos is in reality this review."
            ),
            "id": huby_node_id,
            "label": "Huby 1991 — Review of Donini, Ethos: Aristotele e il determinismo",
            "metadata": json.dumps(
                {
                    "type": "review",
                    "year": 1991,
                    "author": "Pamela M. Huby",
                    "title": "Review of Donini, Ethos: Aristotele e il determinismo",
                    "journal": "The Classical Review",
                    "volume": "41/2",
                    "page_range": "370-371",
                    "local_pdf_path": (
                        "/Users/romaingirardi/Desktop/DOCTORAT/Doctorat SHAL/"
                        "04_Littérature_secondaire/01_Philosophie_antique/"
                        "aristotle-and-determinism-pier-luigi-donini-ethos-"
                        "aristotele-e-il-determinismo-culture-antiche-studi-e-"
                        "testi-2-pp-vi154-alessandria-edizioni-dellorso-1989-"
                        "paper-l-30000.pdf"
                    ),
                    "supersedes_mislabelled_node": donini_node_id,
                    MARKER: True,
                    f"{MARKER}_at": TODAY,
                },
                ensure_ascii=False,
            ),
            "node_id": huby_node_id,
            "period": "Contemporary",
            "role": None,
            "school": None,
            "type": "publication",
            "updated_at": now_iso(),
        }
        nodes.append(huby_node)
        nodes_by_id[huby_node_id] = huby_node
        tracker.touched_node_ids.add(huby_node_id)

    if not huby_edge_present and huby_scholar in nodes_by_id:
        edges.append(
            new_edge(
                huby_node_id,
                "authored_by",
                huby_scholar,
                {MARKER: True, f"{MARKER}_at": TODAY},
            )
        )
    elif huby_scholar not in nodes_by_id:
        tracker.skipped_one(
            label + " (authored_by edge)",
            f"node_not_found: {huby_scholar}",
        )

    tracker.applied_one(label)


def correction_2_frede_dorothea(
    nodes_by_id: dict[str, dict[str, Any]],
    edges: list[dict[str, Any]],
    tracker: Tracker,
) -> None:
    """Re-attribute 5 scholarly_argument_frede_alexander_* args from Michael
    Frede to Dorothea Frede."""
    label = "2. Frede→Dorothea re-attribution (5 args)"
    target_scholar = "scholar_frede_dorothea"
    wrong_scholar = "scholar_frede_michael"

    frede_alex_ids = [
        n["id"]
        for n in nodes_by_id.values()
        if isinstance(n.get("id"), str) and n["id"].startswith("scholarly_argument_frede_alexander")
    ]

    if not frede_alex_ids:
        tracker.skipped_one(label, "no scholarly_argument_frede_alexander_* nodes")
        return
    if target_scholar not in nodes_by_id:
        tracker.skipped_one(label, f"node_not_found: {target_scholar}")
        return

    any_action = False
    for arg_id in sorted(frede_alex_ids):
        node = nodes_by_id[arg_id]
        md = get_metadata(node)
        already = md.get("corrected_to") == target_scholar
        # Rewire any created_by edges from wrong_scholar to target_scholar.
        rewired_here = False
        for e in edges:
            if (
                e.get("source") == arg_id
                and e.get("relation") == "created_by"
                and e.get("target") == wrong_scholar
            ):
                # Check the target re-wire isn't already there as a duplicate
                if not find_edge(edges, arg_id, "created_by", target_scholar):
                    e["target"] = target_scholar
                    e["target_id"] = target_scholar
                    emd = get_metadata(e)
                    emd["rewired_from"] = wrong_scholar
                    emd["rewired_at"] = TODAY
                    emd[MARKER] = True
                    set_metadata(e, emd)
                    rewired_here = True
                else:
                    # duplicate scenario — drop the wrong-pointing edge
                    e["_to_delete"] = True
                    rewired_here = True
        # Ensure a created_by edge to dorothea exists.
        if not find_edge(edges, arg_id, "created_by", target_scholar):
            edges.append(
                new_edge(
                    arg_id,
                    "created_by",
                    target_scholar,
                    {
                        "rewired_from": wrong_scholar,
                        "rewired_at": TODAY,
                        MARKER: True,
                    },
                )
            )
            rewired_here = True

        if not already:
            md["frede_attribution_corrected_at"] = TODAY
            md["originally_attributed_to"] = wrong_scholar
            md["corrected_to"] = target_scholar
            set_metadata(node, md)
            mark_touched(node, tracker)
            any_action = True
        elif rewired_here:
            mark_touched(node, tracker)
            any_action = True

    # ALSO: drop the wrong pub→scholar_frede_michael authored_by edge on
    # pub_frede_1982_dramatization (Dramatization is by Dorothea, not Michael).
    drama_edge = find_edge(edges, "pub_frede_1982_dramatization", "authored_by", wrong_scholar)
    if drama_edge is not None and not drama_edge.get("_to_delete"):
        drama_edge["_to_delete"] = True
        any_action = True

    # Sweep deletions
    if any(e.get("_to_delete") for e in edges):
        edges[:] = [e for e in edges if not e.get("_to_delete")]

    if any_action:
        tracker.applied_one(label)
    else:
        tracker.skipped_one(label, "already applied")


def correction_3_hall_melito(
    nodes_by_id: dict[str, dict[str, Any]],
    edges: list[dict[str, Any]],
    tracker: Tracker,
) -> None:
    label = "3. Hall/Melito deprecation"
    arg_id = "scholarly_argument_hall_free_will_and_determinism_in_m_0"
    node = nodes_by_id.get(arg_id)
    if node is None:
        tracker.skipped_one(label, f"node_not_found: {arg_id}")
        return
    md = get_metadata(node)
    if md.get("deprecated") is True:
        tracker.skipped_one(label, "already deprecated")
        return
    md["deprecated"] = True
    md["deprecation_reason"] = (
        "Hall 2021 does not discuss Melito; thesis cannot be attributed to her"
    )
    md["deprecated_at"] = TODAY
    set_metadata(node, md)
    mark_touched(node, tracker)

    # Remove created_by / discusses_by_pub edges for this arg.
    removed = 0
    for e in edges:
        if (
            e.get("source") == arg_id
            and e.get("relation") in ("created_by", "discusses_by_pub")
        ):
            e["_to_delete"] = True
            removed += 1
        # also incoming discusses from pubs (i.e. pub --discusses--> arg)
        if (
            e.get("target") == arg_id
            and e.get("relation") in ("discusses_by_pub",)
        ):
            e["_to_delete"] = True
            removed += 1
    edges[:] = [e for e in edges if not e.get("_to_delete")]
    tracker.applied_one(label)


def correction_4_boys_stones(
    nodes_by_id: dict[str, dict[str, Any]],
    edges: list[dict[str, Any]],
    tracker: Tracker,
) -> None:
    label = "4. Boys-Stones reformulations + Andresen re-attribution"

    primary_id = "scholarly_argument_boys_stones_primary_concern_problem_of_evi_5"
    three_id = "scholarly_argument_boys_stones_three_levels_of_providence_6"
    justin_id = "scholarly_argument_boys_stones_justin_martyr_as_middle_platon_7"
    andresen = "scholar_andresen_carl"

    if andresen not in nodes_by_id:
        tracker.skipped_one(label + " (Andresen re-attribution)", f"node_not_found: {andresen}")

    any_action = False

    # 4a: primary_concern — reformulate description faithfully to Boys-Stones p.444
    if primary_id in nodes_by_id:
        n = nodes_by_id[primary_id]
        md = get_metadata(n)
        if md.get("boys_stones_correction_2026_05_19") is None:
            n["description"] = (
                "Primary Platonist concern: divine responsibility for evil — "
                "Boys-Stones argues (p.444-445) that, by ignoring the metaphysical, "
                "the Stoics lost the means to appeal to a non-providential cause "
                "of the cosmos quite distinct from god, and lost with it the "
                "ability to distinguish things under god's general control from "
                "things for which he takes specific responsibility. The Platonist "
                "objection is therefore primarily theological (divine "
                "responsibility for evil under Stoic monism) rather than the "
                "defence of human moral responsibility."
            )
            md["boys_stones_correction_2026_05_19"] = (
                "reformulated based on E2 PDF verification (p.444-445 §7 "
                "Platonism against the Stoics)"
            )
            set_metadata(n, md)
            mark_touched(n, tracker)
            any_action = True
    else:
        tracker.skipped_one(label + " (primary_concern)", f"node_not_found: {primary_id}")

    # 4b: three_levels — reformulate to reflect Boys-Stones' scepticism
    if three_id in nodes_by_id:
        n = nodes_by_id[three_id]
        md = get_metadata(n)
        if md.get("boys_stones_correction_2026_05_19") is None:
            n["description"] = (
                "Scepticism about a Middle-Platonist 'doctrine of threefold "
                "providence' — Boys-Stones (p.446 §8) notes that, although the "
                "'doctrine of threefold providence' has obtained a certain "
                "currency in the literature, there are reasons to doubt that it "
                "is original. Ps.-Plutarch is the principal witness, but even he "
                "talks as if he is himself extending the term to the third level, "
                "and he has no near-contemporary support. Boys-Stones therefore "
                "treats the three-providences scheme as a rhetorical extension "
                "rather than a fixed Middle-Platonist doctrine."
            )
            md["boys_stones_correction_2026_05_19"] = (
                "reformulated based on E2 PDF verification (p.446 §8 The "
                "Doctrine of Three Providences)"
            )
            set_metadata(n, md)
            mark_touched(n, tracker)
            any_action = True
    else:
        tracker.skipped_one(label + " (three_levels)", f"node_not_found: {three_id}")

    # 4c: justin_martyr — re-attribute scholar to Andresen
    if justin_id in nodes_by_id and andresen in nodes_by_id:
        n = nodes_by_id[justin_id]
        md = get_metadata(n)
        if md.get("boys_stones_correction_2026_05_19") is None:
            # Rewire the created_by edge if it points to scholar_boys_stones_g
            rewired = False
            for e in edges:
                if (
                    e.get("source") == justin_id
                    and e.get("relation") == "created_by"
                    and e.get("target") == "scholar_boys_stones_g"
                ):
                    if not find_edge(edges, justin_id, "created_by", andresen):
                        e["target"] = andresen
                        e["target_id"] = andresen
                        emd = get_metadata(e)
                        emd["rewired_from"] = "scholar_boys_stones_g"
                        emd["rewired_at"] = TODAY
                        emd[MARKER] = True
                        set_metadata(e, emd)
                        rewired = True
                    else:
                        e["_to_delete"] = True
                        rewired = True
            if not find_edge(edges, justin_id, "created_by", andresen):
                edges.append(
                    new_edge(
                        justin_id,
                        "created_by",
                        andresen,
                        {
                            "rewired_from": "scholar_boys_stones_g",
                            "rewired_at": TODAY,
                            MARKER: True,
                        },
                    )
                )
                rewired = True
            md["boys_stones_correction_2026_05_19"] = (
                "reformulated based on E2 PDF verification; thesis re-attributed "
                "to Carl Andresen, 'Justin und der mittlere Platonismus' (ZNW "
                "1952-53), as Boys-Stones (p.434 n.9) merely cites Andresen"
            )
            md["originally_attributed_to"] = "scholar_boys_stones_g"
            md["corrected_to"] = andresen
            set_metadata(n, md)
            mark_touched(n, tracker)
            any_action = True
    elif justin_id not in nodes_by_id:
        tracker.skipped_one(label + " (justin_martyr)", f"node_not_found: {justin_id}")

    edges[:] = [e for e in edges if not e.get("_to_delete")]

    if any_action:
        tracker.applied_one(label)
    else:
        tracker.skipped_one(label, "already applied")


def correction_5_dihle(
    nodes_by_id: dict[str, dict[str, Any]],
    tracker: Tracker,
) -> None:
    label = "5. Dihle 4 reformulations"
    items: list[tuple[str, str, str]] = [
        (
            "argument_dihle_1982_hebrew_obedience_non_cognitive_will",
            "Argument de Dihle 1982 (Lect. IV, p. 75-83). Yahveh dans la "
            "tradition hebraique commande sans donner de raison rationnelle "
            "accessible a la deliberation; l'obeissance precede la "
            "comprehension. Dihle articule cette « volonte non-cognitive "
            "d'obeissance » a un niveau general (will/power/God-concept), sans "
            "passer en revue l'apparat lexical hebreu detaille (ratzon, kavod, "
            "'emunah, yir'ah, mibtah, Is. 7,9 ta'amenu/tdaminu) que la "
            "description originelle ajoutait improprement: ce vocabulaire "
            "specifique n'est pas thematise dans le Sather 1982. Dihle: « human "
            "knowledge or wisdom thus depends on the previous activity of the "
            "will, which has to turn towards God and to give an initial "
            "response to a very definite divine order » (p. 76).",
            "Removed Hebrew lexical apparatus (ratzon/kavod/'emunah/yir'ah/"
            "mibtah/Is.7:9) absent from Sather 1982; verified by e2_dihle_agent",
        ),
        (
            "argument_dihle_1982_indian_parallel_dharma_intellectualism",
            "Argument comparatif de Dihle 1982 (Lect. I, p. 5-7; ref. "
            "Megasthenes n. 19 p. 165). En tant qu'indianiste, Dihle signale "
            "que la pensee indienne classique etait percue par Galien et Celse "
            "comme cognate avec l'intellectualisme grec, par contraste avec le "
            "voluntarisme biblique. La mention indienne reste breve chez Dihle "
            "1982 (essentiellement via Galien, Celse, Megasthene) et ne se "
            "developpe pas en revue systematique du Vedanta, du bouddhisme et "
            "du jainisme: cet apparat (jnana, vidya, dharma) que la description "
            "originelle deployait n'est pas dans le Sather 1982.",
            "Removed Vedanta/Buddhist/Jain development (jnana/vidya/dharma) — "
            "Dihle 1982 only mentions India briefly via Galen/Celsus/"
            "Megasthenes p.5-7; verified by e2_dihle_agent",
        ),
        (
            "scholarly_argument_dihle_paul_s_concept_of_will_1",
            "Paul's concept of will — St. Paul opere implicitement avec une "
            "notion de volonte distincte a la fois de l'intellect et de "
            "l'emotion, fondant l'action morale sur l'obeissance au commandement "
            "divin plutot que sur la connaissance rationnelle. Dihle (p. 83) "
            "precise toutefois que Paul ne dispose pas encore d'un terme dedie "
            "pour cette notion: la chose est conceptuellement la, le mot ne "
            "l'est pas.",
            "Replaced 'revolutionarily' by 'sans terme dedie' per Dihle p.83; "
            "verified by e2_dihle_agent",
        ),
        (
            "scholar_position_dihle_will_christian_innovation",
            "Emergence of will as distinct faculty — la philosophie grecque a "
            "longtemps resiste a la formulation d'une theorie distincte de la "
            "volonte, fondant l'action humaine sur la connaissance et la "
            "raison. La notion d'une volonte autonome, distincte de la raison "
            "et du desir, emerge principalement avec Augustin (Lect. VI, p. "
            "123 et p. 144), comme une innovation specifiquement augustinienne, "
            "et non pas comme un trait diffus de la « tradition chretienne » "
            "en general.",
            "Specified Augustinian (not generic Christian) origin per Dihle "
            "Lect. VI p.123/144; verified by e2_dihle_agent",
        ),
    ]
    any_action = False
    for arg_id, new_desc, reformulation_note in items:
        n = nodes_by_id.get(arg_id)
        if n is None:
            tracker.skipped_one(label + f" ({arg_id})", "node_not_found")
            continue
        md = get_metadata(n)
        if md.get("dihle_reformulated_2026_05_19") is True:
            continue
        n["description"] = new_desc
        md["dihle_reformulated_2026_05_19"] = True
        md["dihle_reformulation_note"] = reformulation_note
        set_metadata(n, md)
        mark_touched(n, tracker)
        any_action = True
    if any_action:
        tracker.applied_one(label)
    else:
        tracker.skipped_one(label, "already applied")


def correction_6_belcastro_rewire(
    nodes_by_id: dict[str, dict[str, Any]],
    edges: list[dict[str, Any]],
    tracker: Tracker,
) -> None:
    label = "6. Belcastro 2 rewirings (predestinazione → 2016 article)"
    wrong_pub = "pub_belcastro_predestinazione_origene"
    correct_pub = "scholarly_work_belcastro_2016_la_predestinazione_nel_commento_alla_let"
    targets = [
        "scholarly_argument_belcastro_free_will_libero_arbitrio_and__2",
        "scholarly_argument_belcastro_relationship_between_divine_om_2",
    ]
    if correct_pub not in nodes_by_id:
        tracker.skipped_one(label, f"node_not_found: {correct_pub}")
        return
    any_action = False
    for arg_id in targets:
        if arg_id not in nodes_by_id:
            tracker.skipped_one(label + f" ({arg_id})", "node_not_found")
            continue
        # Find pub→arg edge from wrong_pub
        for e in edges:
            if (
                e.get("source") == wrong_pub
                and e.get("relation") == "discusses"
                and e.get("target") == arg_id
            ):
                if not find_edge(edges, correct_pub, "discusses", arg_id):
                    e["source"] = correct_pub
                    e["source_id"] = correct_pub
                    emd = get_metadata(e)
                    emd["rewired_from"] = wrong_pub
                    emd["rewired_at"] = TODAY
                    emd[MARKER] = True
                    set_metadata(e, emd)
                    any_action = True
                else:
                    e["_to_delete"] = True
                    any_action = True
        # Mark arg metadata
        n = nodes_by_id[arg_id]
        md = get_metadata(n)
        if md.get("belcastro_rewired_2026_05_19") is not True:
            md["belcastro_rewired_2026_05_19"] = True
            md["belcastro_rewired_from"] = wrong_pub
            md["belcastro_rewired_to"] = correct_pub
            set_metadata(n, md)
            mark_touched(n, tracker)
            any_action = True
    edges[:] = [e for e in edges if not e.get("_to_delete")]
    if any_action:
        tracker.applied_one(label)
    else:
        tracker.skipped_one(label, "already applied")


def correction_7_minns_duplicate(
    nodes_by_id: dict[str, dict[str, Any]],
    tracker: Tracker,
) -> None:
    label = "7. Minns duplicate deprecation"
    keep = "scholarly_argument_minns_free_will_and_determinism_in_j_0"
    drop = "scholarly_argument_minns_free_will_in_justin_martyr_0"
    if drop not in nodes_by_id:
        tracker.skipped_one(label, f"node_not_found: {drop}")
        return
    if keep not in nodes_by_id:
        tracker.skipped_one(label, f"node_not_found (keep): {keep}")
        return
    n = nodes_by_id[drop]
    md = get_metadata(n)
    if md.get("deprecated") is True and md.get("superseded_by") == keep:
        tracker.skipped_one(label, "already applied")
        return
    md["deprecated"] = True
    md["deprecated_at"] = TODAY
    md["deprecation_reason"] = (
        "Duplicate of " + keep + " (same methodological claim from Minns/Parvis Preface)"
    )
    md["superseded_by"] = keep
    set_metadata(n, md)
    mark_touched(n, tracker)
    tracker.applied_one(label)


def correction_8_belcastro_duplicate(
    nodes_by_id: dict[str, dict[str, Any]],
    tracker: Tracker,
) -> None:
    label = "8. Belcastro duplicate deprecation (philosophical_foundations)"
    keep = "scholarly_argument_belcastro_origen_s_philosophical_foundat_4"
    drop = "scholarly_argument_belcastro_philosophical_foundations_plat_5"
    if drop not in nodes_by_id:
        tracker.skipped_one(label, f"node_not_found: {drop}")
        return
    if keep not in nodes_by_id:
        tracker.skipped_one(label, f"node_not_found (keep): {keep}")
        return
    n = nodes_by_id[drop]
    md = get_metadata(n)
    if md.get("deprecated") is True and md.get("superseded_by") == keep:
        tracker.skipped_one(label, "already applied")
        return
    md["deprecated"] = True
    md["deprecated_at"] = TODAY
    md["deprecation_reason"] = (
        "Duplicate of " + keep + " (same locus, Belcastro 2016 p.212 n.11)"
    )
    md["superseded_by"] = keep
    set_metadata(n, md)
    mark_touched(n, tracker)
    tracker.applied_one(label)


def correction_9_dettwiler_date(
    nodes_by_id: dict[str, dict[str, Any]],
    tracker: Tracker,
) -> None:
    label = "9. Dettwiler Colossians date fix (60s → 70-80)"
    arg_id = "scholarly_argument_dettwiler_authenticity_of_colossians_0"
    n = nodes_by_id.get(arg_id)
    if n is None:
        tracker.skipped_one(label, f"node_not_found: {arg_id}")
        return
    md = get_metadata(n)
    if md.get("dettwiler_date_corrected_2026_05_19") is True:
        tracker.skipped_one(label, "already applied")
        return
    new_desc = (
        "authenticity of Colossians — The letter is likely post-Pauline, "
        "written in the 70s-80s of the 1st century by an anonymous author from "
        "Paul's close circle of collaborators, who sought to preserve and "
        "actualize Paul's heritage (Dettwiler 2008, p. 297)."
    )
    n["description"] = new_desc
    md["dettwiler_date_corrected_2026_05_19"] = True
    md["original_date_range"] = "60s of the 1st century"
    md["corrected_date_range"] = "70-80 (Dettwiler 2008 p.297)"
    set_metadata(n, md)
    mark_touched(n, tracker)
    tracker.applied_one(label)


def correction_10_sharples_reacq(
    nodes_by_id: dict[str, dict[str, Any]],
    tracker: Tracker,
) -> None:
    label = "10. Sharples 1983 re-acquisition priority"
    candidates = [
        "pub_sharples_1983_alexander_fate",
        "scholarly_work_sharples_1983_alex_de_fato",
    ]
    any_action = False
    for nid in candidates:
        n = nodes_by_id.get(nid)
        if n is None:
            continue
        md = get_metadata(n)
        if (
            md.get("needs_re_acquisition") is True
            and md.get("re_acquisition_priority") == "high"
            and md.get("re_acquisition_reason")
        ):
            continue
        # Ensure needs_re_acquisition flag set
        md["needs_re_acquisition"] = True
        md["re_acquisition_priority"] = "high"
        md["re_acquisition_reason"] = (
            "Sharples commentary on Alexander mobilized by Lienemann 2012 "
            "against Frede"
        )
        md["re_acquisition_flagged_at"] = TODAY
        set_metadata(n, md)
        mark_touched(n, tracker)
        any_action = True
    if any_action:
        tracker.applied_one(label)
    else:
        tracker.skipped_one(label, "already applied or no candidate node found")


def correction_11_sorabji_ocr(
    nodes_by_id: dict[str, dict[str, Any]],
    tracker: Tracker,
) -> None:
    label = "11. Sorabji 1980 OCR priority"
    candidates = [
        "pub_sorabji_1980_necessity_cause_blame",
        "scholarly_work_sorabji_1980_necessity",
    ]
    any_action = False
    for nid in candidates:
        n = nodes_by_id.get(nid)
        if n is None:
            continue
        md = get_metadata(n)
        if (
            md.get("needs_full_ocr") is True
            and md.get("ocr_priority") == "high"
            and md.get("ocr_command_suggestion")
        ):
            continue
        md["needs_full_ocr"] = True
        md["ocr_priority"] = "high"
        md["ocr_command_suggestion"] = (
            "ocrmypdf --force-ocr --language eng <input> <output>"
        )
        md["ocr_flagged_at"] = TODAY
        set_metadata(n, md)
        mark_touched(n, tracker)
        any_action = True
    if any_action:
        tracker.applied_one(label)
    else:
        tracker.skipped_one(label, "already applied or no candidate node found")


def correction_12_pouderon_orphans(
    nodes_by_id: dict[str, dict[str, Any]],
    tracker: Tracker,
) -> None:
    label = "12. Pouderon 5 orphan args flagging"
    pouderon_patch_path = KG_DIR / "e2_patches" / "pouderon.json"
    if not pouderon_patch_path.exists():
        tracker.skipped_one(label, "patch file missing")
        return
    with pouderon_patch_path.open("r", encoding="utf-8") as fh:
        patch = json.load(fh)

    # Identify orphans: not_found / low-confidence verifications or explicit "not_in_local"
    orphan_ids: list[tuple[str, str]] = []
    for arg_id, p in patch.get("patches", {}).items():
        is_orphan = False
        reason_parts = []
        if p.get("verification_confidence") in ("low", "not_found"):
            is_orphan = True
            reason_parts.append(
                f"E2 verification_confidence={p.get('verification_confidence')}"
            )
        ctx_lc = str(p.get("context", "")).lower()
        for marker in ("n'apparait pas", "n'apparaît pas", "aucun passage", "n'est pas formulé", "n'est pas formulée"):
            if marker in ctx_lc:
                is_orphan = True
                reason_parts.append("E2 reports source claim absent from consulted PDFs")
                break
        if p.get("not_in_local_corpus"):
            is_orphan = True
            reason_parts.append(str(p["not_in_local_corpus"]))
        if is_orphan:
            base = (
                "Source PDF (HLGC vol V Aneor 2016 epub or SC 470 Aristides "
                "Apologie) not in DOCTORAT — needs acquisition"
            )
            orphan_ids.append((arg_id, base + " | " + "; ".join(reason_parts)))

    if not orphan_ids:
        tracker.skipped_one(label, "no orphans identified from patch")
        return

    any_action = False
    for arg_id, reason in orphan_ids:
        n = nodes_by_id.get(arg_id)
        if n is None:
            tracker.skipped_one(label + f" ({arg_id})", "node_not_found")
            continue
        md = get_metadata(n)
        if md.get("e2_not_found_reason"):
            continue
        md["e2_not_found_reason"] = reason
        md["e2_not_found_flagged_at"] = TODAY
        set_metadata(n, md)
        mark_touched(n, tracker)
        any_action = True
    if any_action:
        tracker.applied_one(label + f" ({len(orphan_ids)} args)")
    else:
        tracker.skipped_one(label, "already applied")


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------
def run(commit: bool) -> int:
    nodes = load_jsonl(NODES_PATH)
    edges = load_jsonl(EDGES_PATH)
    nodes_by_id = {n["id"]: n for n in nodes}

    tracker = Tracker()

    correction_1_donini_mislabel(nodes_by_id, nodes, edges, tracker)
    correction_2_frede_dorothea(nodes_by_id, edges, tracker)
    correction_3_hall_melito(nodes_by_id, edges, tracker)
    correction_4_boys_stones(nodes_by_id, edges, tracker)
    correction_5_dihle(nodes_by_id, tracker)
    correction_6_belcastro_rewire(nodes_by_id, edges, tracker)
    correction_7_minns_duplicate(nodes_by_id, tracker)
    correction_8_belcastro_duplicate(nodes_by_id, tracker)
    correction_9_dettwiler_date(nodes_by_id, tracker)
    correction_10_sharples_reacq(nodes_by_id, tracker)
    correction_11_sorabji_ocr(nodes_by_id, tracker)
    correction_12_pouderon_orphans(nodes_by_id, tracker)

    print("\n=== 12-CORRECTIONS REPORT (2026-05-19) ===")
    print(f"Applied: {len(tracker.applied)}")
    for a in tracker.applied:
        print(f"  + {a}")
    print(f"\nSkipped: {len(tracker.skipped)}")
    for label, reason in tracker.skipped:
        print(f"  - {label}: {reason}")
    print(f"\nTotal nodes touched: {len(tracker.touched_node_ids)}")

    if not commit:
        print("\n[DRY-RUN] No files written. Re-run with --commit to apply.")
        return 0

    snapshot()
    write_jsonl(NODES_PATH, nodes)
    write_jsonl(EDGES_PATH, edges)
    print(f"\n[COMMITTED] Snapshot: {SNAPSHOT_DIR}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply 12 KG corrections (2026-05-19).")
    parser.add_argument("--commit", action="store_true", help="actually write changes")
    args = parser.parse_args()
    return run(commit=args.commit)


if __name__ == "__main__":
    sys.exit(main())
