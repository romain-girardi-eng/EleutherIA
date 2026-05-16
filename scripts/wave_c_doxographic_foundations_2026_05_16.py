#!/usr/bin/env python3
"""Wave C — Doxographic foundations — 2026-05-16

Insert 5 missing reference nodes into ``data/kg/nodes.jsonl``:

* ``collection_aetius_placita`` — Aétius, *Placita Philosophorum*
  (Diels DG 1879 + Mansfeld/Runia *Aetiana* 1997-2018). Doxographic pivot
  of the Hellenistic εἱμαρμένη / πρόνοια debate.
* ``collection_dk`` — Diels-Kranz, *Die Fragmente der Vorsokratiker*
  (Weidmann, 6e éd. 1951-1952). Reference edition of presocratic
  fragments.
* ``collection_ls`` — Long & Sedley, *The Hellenistic Philosophers*
  (Cambridge 1987, 2 vol.). Standard anthology / numbering for
  hellenistic fragments (LS sections).
* ``collection_dox_graeci_diels`` — Diels, *Doxographi Graeci*
  (Berlin Reimer 1879). Founding doxographic reconstruction.
* ``pub_amand_1973_fatalisme_liberte`` — Hakkert (Amsterdam 1973)
  reprint of Amand de Mendieta's 1945 Louvain thesis. Eponym of the
  snapshot ``2026-05-16-pre-amand-coherence-patches``.

All 5 nodes follow the existing node convention: keys sorted, ``id`` and
``node_id`` both present, ``alternative_names`` and ``metadata`` stored
as JSON strings (``ensure_ascii=False``), ISO timestamps with space sep.

Idempotent: re-running on an already-populated graph reports all-zero
counters and produces no diff.
"""

from __future__ import annotations

import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"
EDGES_PATH = ROOT / "data" / "kg" / "edges.jsonl"

WAVE_TAG = "wave_c_doxographic_foundations_2026_05_16"
SNAPSHOT_DIR = ROOT / "data" / "kg" / "snapshots" / f"2026-05-16-pre-{WAVE_TAG}"

NOW_ISO = datetime.now(UTC).isoformat(sep=" ")


# ---------------------------------------------------------------------------
# Node specs (5 inserts)
# ---------------------------------------------------------------------------


def _spec_aetius() -> dict[str, Any]:
    return {
        "node_id": "collection_aetius_placita",
        "type": "source_collection",
        "label": "Aétius, Placita Philosophorum",
        "alternative_names": [
            "Placita",
            "Aëtius",
            "Ps.-Plutarchi De Placitis Philosophorum",
        ],
        "period": "Hellenistic",
        "description": (
            "Compilation doxographique attribuée à Aétius (Ier siècle av. J.-C.), "
            "reconstituée par Hermann Diels (Doxographi Graeci, Berlin 1879) à partir "
            "de Pseudo-Plutarque (Placita) et de Jean Stobée (Eclogae I). Le rapprochement "
            "des deux épitomes parallèles permet de remonter à un archétype perdu, "
            "lui-même probablement dépendant d'une source théophrastéenne. Aétius "
            "constitue le pivot doxographique du débat hellénistique sur εἱμαρμένη, "
            "πρόνοια et τύχη : il transmet sous forme tabulaire les positions stoïciennes, "
            "épicuriennes, académiques et péripatéticiennes. Édition critique de "
            "référence désormais : Mansfeld & Runia, Aetiana (Brill, 4 vol., 1997 / 2009 / "
            "2010 / 2018, suite en cours), qui révise et complète Diels. Numérotation "
            "Aët. + livre/chapitre/section (e.g. Aët. I.27.5)."
        ),
        "metadata": {
            "editions": [
                "Diels, Doxographi Graeci, Berlin 1879 (princeps)",
                "Mansfeld & Runia, Aetiana I (Brill 1997), II (Brill 2009), III (Brill 2010), IV (Brill 2018)",
            ],
            "abbreviation": "Aët.",
            "language": "grc",
            "wave": WAVE_TAG,
        },
    }


def _spec_dk() -> dict[str, Any]:
    return {
        "node_id": "collection_dk",
        "type": "source_collection",
        "label": "Diels-Kranz, Die Fragmente der Vorsokratiker",
        "alternative_names": [
            "DK",
            "Fragmente der Vorsokratiker",
            "Diels-Kranz",
            "Vorsokratiker",
        ],
        "period": "Presocratic",
        "description": (
            "Édition de référence des fragments présocratiques. Hermann Diels (1903) "
            "puis Walther Kranz à partir de la 4e éd. (1934), réimpr. courante "
            "6e éd. Weidmann 1951-1952 (3 vol.). Numérotation DK = standard scholarly "
            "(e.g. DK 68 B 26 pour Démocrite). Trois sections par auteur : A "
            "(testimonia), B (fragments authentiques), C (imitations). Pour le débat "
            "libre arbitre, les pivots sont Démocrite (DK 68 — atomisme et nécessité), "
            "Héraclite (DK 22 — λόγος et tension des contraires), Parménide "
            "(DK 28 — nécessité ontologique du τὸ ἐόν), Empédocle (DK 31 — Amitié vs Haine "
            "comme principes de mouvement). À distinguer de Doxographi Graeci (DG) : "
            "DK = fragments primaires + testimonia ; DG = corpus doxographique."
        ),
        "metadata": {
            "editions": [
                "Diels-Kranz, 6e éd., Weidmann 1951-1952 (3 vol.)",
            ],
            "abbreviation": "DK",
            "language": "grc",
            "wave": WAVE_TAG,
        },
    }


def _spec_ls() -> dict[str, Any]:
    return {
        "node_id": "collection_ls",
        "type": "source_collection",
        "label": "Long & Sedley, The Hellenistic Philosophers",
        "alternative_names": [
            "LS",
            "Long-Sedley",
            "The Hellenistic Philosophers",
        ],
        "period": "Contemporary",
        "description": (
            "Anthologie de référence pour la philosophie hellénistique (A.A. Long & "
            "D.N. Sedley, 2 vol., Cambridge University Press 1987). Volume 1 = textes "
            "traduits en anglais avec commentaires philosophiques organisés par thème ; "
            "volume 2 = textes originaux grecs/latins avec notes textuelles et apparat "
            "critique sélectif. Numérotation LS = standard scholarly pour citer "
            "fragments stoïciens, épicuriens, sceptiques académiques et pyrrhoniens "
            "(e.g. LS 55N pour la causalité chrysippéenne). Sections-clés pour le KG : "
            "20 (clinamen épicurien), 38–40 (action et passion stoïciennes), 55–62 "
            "(causalité, destin et signe stoïciens), 68–70 (scepticisme académique), "
            "71–72 (Carnéade). Édition française partielle : Brunschwig & Pellegrin, "
            "Les philosophes hellénistiques (GF Flammarion 2001, 3 vol.)."
        ),
        "metadata": {
            "editions": [
                "Long & Sedley, Cambridge University Press 1987 (2 vol.)",
                "Brunschwig & Pellegrin, GF Flammarion 2001 (traduction française partielle)",
            ],
            "abbreviation": "LS",
            "language": "en",
            "wave": WAVE_TAG,
        },
    }


def _spec_dox_graeci() -> dict[str, Any]:
    return {
        "node_id": "collection_dox_graeci_diels",
        "type": "source_collection",
        "label": "Diels, Doxographi Graeci",
        "alternative_names": [
            "DG",
            "Doxographi Graeci",
        ],
        "period": "Modern",
        "description": (
            "Édition fondatrice de Hermann Diels (Berlin, Reimer 1879 ; réimpr. Berlin / "
            "de Gruyter 1965) reconstituant la tradition doxographique grecque par "
            "Quellenforschung : comparaison systématique de Stobée (Anthologium I), "
            "Pseudo-Plutarque (Placita), Théodoret (Graec. Aff. Cur.), Galien (Hist. Phil.) "
            "et de fragments doxographiques mineurs. Diels en dégage l'archétype Aétius "
            "et propose un stemma codicum doxographique. Méthodologie quellenforschend "
            "qui sous-tend toute la philologie hellénistique du XXe siècle. À distinguer "
            "de DK (Diels-Kranz, fragments présocratiques primaires) : DG = doxographies, "
            "rapports indirects sur les doctrines."
        ),
        "metadata": {
            "editions": [
                "Diels, Doxographi Graeci, Berlin Reimer 1879 (réimpr. de Gruyter 1965)",
            ],
            "abbreviation": "DG",
            "language": "grc",
            "wave": WAVE_TAG,
        },
    }


def _spec_amand_1973() -> dict[str, Any]:
    return {
        "node_id": "pub_amand_1973_fatalisme_liberte",
        "type": "publication",
        "label": "Amand de Mendieta, Fatalisme et liberté dans l'antiquité grecque (1973)",
        "alternative_names": [
            "Amand 1973",
            "Amand de Mendieta 1973",
            "Fatalisme et liberté",
        ],
        "period": "Modern",
        "description": (
            "Réédition par Hakkert (Amsterdam 1973, ISBN 9789025606466) de la thèse "
            "doctorale d'Emmanuel Amand de Mendieta soutenue à Louvain (1944), "
            "publiée par la Bibliothèque de l'Université de Louvain en 1945 (Recueil "
            "de travaux d'histoire et de philologie 3.19). Étude monumentale (640 p.) "
            "de la transmission de l'argumentation anti-fataliste de Carnéade à travers "
            "la chaîne Carnéade → Clitomaque → tradition Stoïco-Académique latine "
            "(Cicéron, Philodème) → tradition grecque (Pseudo-Plutarque De Fato, "
            "Aétius) → polémistes chrétiens (Eusèbe Praeparatio Evangelica VI, "
            "Origène Contra Celsum + Philocalia, Grégoire de Nysse De Hominis "
            "Opificio, Diodore de Tarse Contre les astrologues, Némésius De Natura "
            "Hominis, Théodoret Graec. Aff. Cur.). Reconstruction philologique "
            "minutieuse des « Carneadea » et des « antifatalia » communs dans la "
            "littérature patristique des IVe-Ve siècles. Référence pivot du KG "
            "EleutherIA — éponyme du snapshot pre-amand-coherence-patches "
            "(2026-05-16)."
        ),
        "metadata": {
            "author": "Emmanuel Amand de Mendieta",
            "year": 1973,
            "publisher": "Hakkert, Amsterdam",
            "isbn": "9789025606466",
            "first_edition": {
                "year": 1945,
                "publisher": (
                    "Bibliothèque de l'Université de Louvain "
                    "(Recueil de travaux d'histoire et de philologie 3.19)"
                ),
            },
            "bibtex_key": "amand-1973-fatalisme-et-liberte",
            "local_path_hint": (
                "/Users/romaingirardi/Desktop/DOCTORAT/Doctorat SHAL/"
                "04_Littérature_secondaire/01_Philosophie_antique/"
            ),
            "pages": 640,
            "wave": WAVE_TAG,
        },
    }


def all_specs() -> list[dict[str, Any]]:
    return [
        _spec_aetius(),
        _spec_dk(),
        _spec_ls(),
        _spec_dox_graeci(),
        _spec_amand_1973(),
    ]


# ---------------------------------------------------------------------------
# I/O helpers (mirror Wave B)
# ---------------------------------------------------------------------------


def load_nodes() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for line in NODES_PATH.read_text().splitlines():
        if not line.strip():
            continue
        out.append(json.loads(line))
    return out


def write_nodes(nodes: list[dict[str, Any]]) -> None:
    with NODES_PATH.open("w") as fh:
        for n in nodes:
            fh.write(json.dumps(n, ensure_ascii=False) + "\n")


def node_id(n: dict[str, Any]) -> str:
    return n.get("node_id") or n.get("id") or ""


def make_snapshot() -> None:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    snap_nodes = SNAPSHOT_DIR / "nodes.jsonl"
    snap_edges = SNAPSHOT_DIR / "edges.jsonl"
    if snap_nodes.exists() and snap_edges.exists():
        print(f"[snapshot] already exists at {SNAPSHOT_DIR.relative_to(ROOT)} — skip")
        return
    shutil.copy2(NODES_PATH, snap_nodes)
    shutil.copy2(EDGES_PATH, snap_edges)
    print(f"[snapshot] written to {SNAPSHOT_DIR.relative_to(ROOT)}")


# ---------------------------------------------------------------------------
# Build / normalize a node to match the existing nodes.jsonl convention.
# ---------------------------------------------------------------------------


def build_node(spec: dict[str, Any]) -> dict[str, Any]:
    """Return a node dict with the exact schema used in nodes.jsonl:
    keys sorted alphabetically; ``id`` + ``node_id`` both present; ``role``
    and ``school`` defaulted to None; ``alternative_names`` and
    ``metadata`` stored as JSON strings (``ensure_ascii=False``); ISO
    timestamps with space separator and ``+00:00`` offset.
    """
    nid = spec["node_id"]
    alt_names_raw = spec.get("alternative_names", [])
    md_raw = spec.get("metadata", {})

    node: dict[str, Any] = {
        "alternative_names": json.dumps(alt_names_raw, ensure_ascii=False),
        "created_at": NOW_ISO,
        "description": spec["description"],
        "id": nid,
        "label": spec["label"],
        "metadata": json.dumps(md_raw, ensure_ascii=False),
        "node_id": nid,
        "period": spec["period"],
        "role": None,
        "school": None,
        "type": spec["type"],
        "updated_at": NOW_ISO,
    }
    # Return with sorted keys (matches existing nodes' alphabetic ordering).
    return {k: node[k] for k in sorted(node)}


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def main() -> int:
    print(f"[wave-c] start :: wave={WAVE_TAG}")

    make_snapshot()

    nodes = load_nodes()
    print(f"[load] nodes={len(nodes):,}")

    existing_ids = {node_id(n) for n in nodes}

    collections_added = 0
    publications_added = 0
    amand_eponym_added = False

    for spec in all_specs():
        nid = spec["node_id"]
        if nid in existing_ids:
            print(f"[skip] {nid} already present")
            continue
        node = build_node(spec)
        nodes.append(node)
        existing_ids.add(nid)
        if spec["type"] == "source_collection":
            collections_added += 1
        elif spec["type"] == "publication":
            publications_added += 1
        if nid == "pub_amand_1973_fatalisme_liberte":
            amand_eponym_added = True
        print(f"[add] {nid} :: type={spec['type']} period={spec['period']}")

    if collections_added or publications_added:
        write_nodes(nodes)
        print(f"[write] nodes={len(nodes):,}")
    else:
        print("[write] no changes — skipping write")

    print(
        f"[wave-c] collections_added={collections_added}  "
        f"publications_added={publications_added}"
    )
    print(f"[wave-c] amand_eponym_added={amand_eponym_added}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
