#!/usr/bin/env python3
"""Recovery bonus — 4 items acquired by recovery agent on 2026-05-18.

Background recovery agent failed on the 4 stubborn monographs (Kobusch 2018,
Hengstermann 2016, Magris 2008, Origeniana XIII 2024) but compensated with
4 OA substitutes filed in DOCTORAT:

1. **Magris 2021 Verbum Vitae article** (CC BY-ND, 26 p.) — thematically
   adjacent to Magris 2008 *Destino, provvidenza, predestinazione*.
2. **Magris 2008 TOC** (PDF Morcelliana, 66 KB) — sommaire du livre principal.
3. **Fürst (ed.) 2019 Adamantiana 21** *Perspectives on Origen and the
   History of his Reception* (CC BY-NC-ND, 375 p., OA complet sur OAPEN)
   — contient introduction de Kobusch + chapitres Edwards, Ramelli,
   Karfíková, Martens, Pollmann. **Excellent proxy** pour les manques
   Kobusch 2018 et Origeniana XIII 2024.
4. **Fürst 2019 Adamantiana 13 intro** "Concepts of Origenism: Freedom
   between Pre-existence and Apokatastasis" (CC BY-NC-ND, 35 p.) — chapitre
   introductif au volume Origenes-Forschung.

Operations:
- CREATE 1 scholar node (Magris)
- CREATE 3 publication nodes
- WIRE authored_by + selected discusses/engages_with edges

Idempotent. Snapshot.
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
SNAPSHOT_DIR = ROOT / "data" / "kg" / "snapshots" / "2026-05-18-pre-recovery-bonus"
DOCTORAT_BASE = Path(
    "/Users/romaingirardi/Desktop/DOCTORAT/Doctorat SHAL/04_Littérature_secondaire"
)

WAVE_TAG = "recovery_bonus_2026_05_18"
NOW = datetime.now(UTC).isoformat(sep=" ")

# Existing IDs
ID_FUERST_SCHOLAR = "scholar_furst_alfons"
ID_KOBUSCH_SCHOLAR = "scholar_kobusch_theo"
ID_ORIGEN = "person_origen_alexandria_185_254ce_s9t0u1v2"
ID_PUB_FUERST_2022 = "pub_furst_2022_wege_freiheit"
ID_PUB_KOBUSCH_2018 = "pub_kobusch_2018_selbstwerdung"

# New IDs
ID_MAGRIS_SCHOLAR = "scholar_magris_aldo"
ID_PUB_MAGRIS_2021 = "pub_magris_2021_filosofizzazione_cristianesimo"
ID_PUB_FUERST_2019_AD13 = "pub_furst_2019_concepts_origenism_ad13"
ID_PUB_FUERST_2019_AD21 = "pub_furst_2019_perspectives_origen_ad21"


NEW_SCHOLARS: list[dict[str, Any]] = [
    {
        "id": ID_MAGRIS_SCHOLAR, "node_id": ID_MAGRIS_SCHOLAR, "type": "person",
        "label": "Aldo Magris",
        "description": (
            "Aldo Magris, historien italien des religions et philosophe, "
            "ancien professeur d'histoire des religions à l'Université "
            "de Trieste (retraité). Spécialiste des conceptions "
            "antiques et tardo-antiques du destin, de la providence et "
            "de la prédestination, dans une perspective comparative "
            "Antiquité gréco-romaine / Antiquité tardive / "
            "Christianisme primitif / Gnosticisme. Auteur de *L'idea "
            "di destino* (Del Bianco 1984-85, 2 vols) puis de *Destino, "
            "provvidenza, predestinazione. Dal mondo antico al "
            "Cristianesimo* (Morcelliana 2008, 2ᵉ éd. 2016), refonte et "
            "extension du premier. A également publié *Trattati antichi "
            "sul destino* (Claup 2016) — éditions commentées de Cicéron "
            "*De Fato*, Ps-Plutarque *De Fato*, Alexandre d'Aphrodise "
            "*De Fato*. Vue continentale italienne souvent négligée "
            "dans la littérature anglo-allemande dominante."
        ),
        "period": "Modern", "role": "scholar", "school": None,
        "alternative_names": json.dumps([], ensure_ascii=False),
        "metadata": json.dumps({
            "role": "scholar", "period": "Modern", "surname": "Magris",
            "given_names": "Aldo",
            "specialty": "History of religions, ancient and late-antique conceptions of fate/providence/predestination, Gnosticism",
            "affiliations": ["Università di Trieste (retraité)"],
            "key_works": [
                "L'idea di destino (Del Bianco 1984-85, 2 vols)",
                "Destino, provvidenza, predestinazione. Dal mondo antico al Cristianesimo (Morcelliana 2008, 2ᵉ éd. 2016)",
                "Trattati antichi sul destino (Claup 2016)",
                "Free Will According to the Gnostics (in Brill 2020 Fate, Providence and Free Will)",
                "La filosofizzazione del cristianesimo (Verbum Vitae 39/3, 2021)",
            ],
            "wave": WAVE_TAG,
        }, ensure_ascii=False),
        "created_at": NOW, "updated_at": NOW,
    },
]


NEW_PUBLICATIONS: list[dict[str, Any]] = [
    {
        "id": ID_PUB_MAGRIS_2021, "node_id": ID_PUB_MAGRIS_2021, "type": "publication",
        "label": "Magris 2021 — La filosofizzazione del cristianesimo (Verbum Vitae)",
        "description": (
            "Aldo Magris, « La filosofizzazione del cristianesimo: "
            "predestinazione, libero arbitrio, teodicea », *Verbum "
            "Vitae* 39/3 (2021), 26 p. CC BY-ND. Article OA "
            "thématiquement adjacent à *Destino, provvidenza, "
            "predestinazione* (Morcelliana 2008). Traite la "
            "philosophisation du christianisme à travers les trois "
            "axes : providence divine, libre arbitre, théodicée. "
            "Substitut OA partiel pour le livre principal Magris 2008 "
            "(non acquis en OA — voir TOC séparé)."
        ),
        "period": "Modern", "role": None, "school": None,
        "alternative_names": json.dumps([], ensure_ascii=False),
        "metadata": json.dumps({
            "type": "article", "year": 2021,
            "author": "Aldo Magris", "author_id": ID_MAGRIS_SCHOLAR,
            "title": "La filosofizzazione del cristianesimo: predestinazione, libero arbitrio, teodicea",
            "journal": "Verbum Vitae", "volume": 39, "number": 3,
            "publisher": "Wydawnictwo KUL", "language": "it",
            "license": "CC BY-ND",
            "bibtex_key": "magris-2021-filosofizzazione-cristianesimo",
            "local_pdf_path": str(DOCTORAT_BASE / "07_Libre_arbitre_theologie" / "magris_2021_filosofizzazione_cristianesimo.pdf"),
            "url": "https://czasopisma.kul.pl/index.php/vv/article/view/12162",
            "related_book": "Magris 2008 Destino, provvidenza, predestinazione (Morcelliana, non-OA — TOC seul acquis)",
            "wave": WAVE_TAG,
        }, ensure_ascii=False),
        "created_at": NOW, "updated_at": NOW,
    },
    {
        "id": ID_PUB_FUERST_2019_AD13, "node_id": ID_PUB_FUERST_2019_AD13, "type": "publication",
        "label": "Fürst 2019 — Concepts of Origenism from Late Antiquity to Modern Times (Adamantiana 13, intro)",
        "description": (
            "Alfons Fürst, « Concepts of Origenism from Late Antiquity "
            "to Modern Times — Freedom between Pre-existence and "
            "Apokatastasis », chapitre introductif au vol. *Origenes "
            "Cusanus* (Adamantiana 13), Münster: Aschendorff, 2019, "
            "35 p. CC BY-NC-ND (financement EU Marie Skłodowska-Curie "
            "n°676258). Synthèse fürstienne sur la trajectoire "
            "conceptuelle origéniste — préexistence des âmes ↔ liberté "
            "↔ apocatastase — à travers la longue durée (Antiquité "
            "tardive → moderne). Pertinent comme cadre programmatique "
            "pour comprendre Fürst 2022 *Wege zur Freiheit*."
        ),
        "period": "Modern", "role": None, "school": None,
        "alternative_names": json.dumps([], ensure_ascii=False),
        "metadata": json.dumps({
            "type": "book_chapter", "year": 2019,
            "author": "Alfons Fürst", "author_id": ID_FUERST_SCHOLAR,
            "title": "Concepts of Origenism from Late Antiquity to Modern Times — Freedom between Pre-existence and Apokatastasis",
            "book_title": "Origenes Cusanus",
            "series": "Adamantiana 13",
            "publisher": "Aschendorff Verlag", "publisher_location": "Münster",
            "pages": 35, "language": "en",
            "license": "CC BY-NC-ND",
            "funding": "EU Marie Skłodowska-Curie grant 676258",
            "bibtex_key": "furst-2019-concepts-origenism-ad13",
            "local_pdf_path": str(DOCTORAT_BASE / "05_Origene" / "fuerst_2019_concepts_of_origenism_adamantiana13_intro.pdf"),
            "url": "https://library.oapen.org/handle/20.500.12657/88025",
            "wave": WAVE_TAG,
        }, ensure_ascii=False),
        "created_at": NOW, "updated_at": NOW,
    },
    {
        "id": ID_PUB_FUERST_2019_AD21, "node_id": ID_PUB_FUERST_2019_AD21, "type": "publication",
        "label": "Fürst (ed.) 2019 — Perspectives on Origen and the History of his Reception (Adamantiana 21)",
        "description": (
            "Alfons Fürst (ed.), *Perspectives on Origen and the "
            "History of his Reception*, Münster: Aschendorff, 2019, "
            "Adamantiana 21, 375 p. CC BY-NC-ND (OA complet sur OAPEN, "
            "financement EU Marie Skłodowska-Curie n°676258). **Volume "
            "majeur pour la thèse Romain** : couvre déterminisme et "
            "liberté, origénisme moderne, héritage philosophique "
            "d'Origène. **Contient l'introduction de Theo Kobusch** "
            "(proxy pour Kobusch 2018 non acquis), chapitres de Pui "
            "Him Ip, Mark J. Edwards, Anders-Christian Jacobsen, Karla "
            "Pollmann, Lenka Karfíková, Elena Rapetti, Peter W. "
            "Martens. Issu d'une conférence Oxford 2019. **Excellent "
            "proxy pour le manque Origeniana XIII 2024 (Peeters non-OA)** "
            "puisque même éditeur + auteurs largement chevauchants."
        ),
        "period": "Modern", "role": None, "school": None,
        "alternative_names": json.dumps(["Adamantiana 21"], ensure_ascii=False),
        "metadata": json.dumps({
            "type": "edited_volume", "year": 2019,
            "editor": "Alfons Fürst", "editor_id": ID_FUERST_SCHOLAR,
            "title": "Perspectives on Origen and the History of his Reception",
            "series": "Adamantiana 21",
            "publisher": "Aschendorff Verlag", "publisher_location": "Münster",
            "pages": 375, "language": "en",
            "license": "CC BY-NC-ND",
            "funding": "EU Marie Skłodowska-Curie grant 676258",
            "bibtex_key": "furst-2019-perspectives-origen-ad21",
            "local_pdf_path": str(DOCTORAT_BASE / "05_Origene" / "fuerst_2021_perspectives_origen_adamantiana21.pdf"),
            "url": "https://library.oapen.org/bitstream/id/8b7b29e0-c91a-4221-ad26-39bfb07baf88/9783402137529.pdf",
            "contributors": [
                "Theo Kobusch (introduction — proxy for Kobusch 2018 monograph)",
                "Pui Him Ip",
                "Mark J. Edwards",
                "Anders-Christian Jacobsen",
                "Karla Pollmann",
                "Lenka Karfíková",
                "Elena Rapetti",
                "Peter W. Martens",
            ],
            "thematic_axes": [
                "determinism and freedom",
                "modern Origenism",
                "philosophical legacy of Origen",
            ],
            "proxy_role": (
                "Excellent OA substitute for the failed acquisitions "
                "Kobusch 2018 (Mohr Siebeck, Selbstwerdung) and "
                "Origeniana XIII 2024 (Peeters BETL 338) — same "
                "editor + overlapping contributors"
            ),
            "wave": WAVE_TAG,
        }, ensure_ascii=False),
        "created_at": NOW, "updated_at": NOW,
    },
]


NEW_EDGES: list[dict[str, Any]] = [
    # Authorship
    {"source": ID_PUB_MAGRIS_2021, "target": ID_MAGRIS_SCHOLAR, "relation": "authored_by", "confidence": 1.0, "metadata": {"wave": WAVE_TAG}},
    {"source": ID_PUB_FUERST_2019_AD13, "target": ID_FUERST_SCHOLAR, "relation": "authored_by", "confidence": 1.0, "metadata": {"wave": WAVE_TAG}},
    {"source": ID_PUB_FUERST_2019_AD21, "target": ID_FUERST_SCHOLAR, "relation": "authored_by", "confidence": 1.0, "metadata": {"wave": WAVE_TAG, "role": "editor"}},
    # Domain
    {"source": ID_PUB_FUERST_2019_AD13, "target": ID_ORIGEN, "relation": "discusses", "confidence": 1.0, "metadata": {"wave": WAVE_TAG}},
    {"source": ID_PUB_FUERST_2019_AD21, "target": ID_ORIGEN, "relation": "discusses", "confidence": 1.0, "metadata": {"wave": WAVE_TAG}},
    # Programmatic/precursor
    {
        "source": ID_PUB_FUERST_2019_AD13, "target": ID_PUB_FUERST_2022,
        "relation": "extends", "confidence": 0.85,
        "metadata": {"wave": WAVE_TAG, "summary": "Fürst 2019 Adamantiana 13 intro = programmatic precursor to Fürst 2022 Wege zur Freiheit"},
    },
    {
        "source": ID_PUB_FUERST_2019_AD21, "target": ID_PUB_KOBUSCH_2018,
        "relation": "engages_with", "confidence": 0.6,
        "metadata": {
            "wave": WAVE_TAG,
            "engagement_type": "kobusch_intro_as_proxy",
            "summary": "Adamantiana 21 contains Theo Kobusch's introduction — functions as accessible proxy for the (non-OA) Kobusch 2018 *Selbstwerdung und Personalität* monograph",
        },
    },
]


def parse_metadata(raw: Any) -> dict[str, Any]:
    if raw is None or raw == "":
        return {}
    if isinstance(raw, dict):
        return raw
    return json.loads(raw)


def node_id_of_line(line: str) -> str:
    return json.loads(line).get("id") or ""


def edge_sig(e: dict[str, Any]) -> tuple[str, str, str]:
    return (
        e.get("source") or e.get("source_id") or "",
        e.get("target") or e.get("target_id") or "",
        e.get("relation") or "",
    )


def snapshot() -> None:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(NODES_PATH, SNAPSHOT_DIR / NODES_PATH.name)
    shutil.copy2(EDGES_PATH, SNAPSHOT_DIR / EDGES_PATH.name)


def main() -> int:
    node_lines = [
        line.rstrip("\n")
        for line in NODES_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    edge_lines = [
        line.rstrip("\n")
        for line in EDGES_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    edge_sigs = {edge_sig(json.loads(ln)) for ln in edge_lines}
    nodes_by_id = {node_id_of_line(ln): i for i, ln in enumerate(node_lines)}

    changes: list[str] = []

    for spec in NEW_SCHOLARS:
        if spec["id"] in nodes_by_id:
            print(f"SKIP (exists): {spec['id']}")
            continue
        node_lines.append(json.dumps(spec, ensure_ascii=False))
        nodes_by_id[spec["id"]] = len(node_lines) - 1
        changes.append(f"NEW SCHOLAR {spec['id']}")

    for spec in NEW_PUBLICATIONS:
        if spec["id"] in nodes_by_id:
            print(f"SKIP (exists): {spec['id']}")
            continue
        node_lines.append(json.dumps(spec, ensure_ascii=False))
        nodes_by_id[spec["id"]] = len(node_lines) - 1
        changes.append(f"NEW PUB    {spec['id']}")

    for e in NEW_EDGES:
        sig = edge_sig(e)
        if sig in edge_sigs:
            print(f"SKIP edge (exists): {sig[0]} --{sig[2]}--> {sig[1]}")
            continue
        edge_lines.append(json.dumps(e, ensure_ascii=False))
        edge_sigs.add(sig)
        changes.append(f"NEW EDGE   {sig[0][:40]:40s} --{sig[2]:13s}--> {sig[1][:40]}")

    if not changes:
        print("OK: nothing to apply")
        return 0

    snapshot()
    print(f"snapshot: {SNAPSHOT_DIR}")
    NODES_PATH.write_text("\n".join(node_lines) + "\n", encoding="utf-8")
    EDGES_PATH.write_text("\n".join(edge_lines) + "\n", encoding="utf-8")
    for c in changes:
        print(c)
    return 0


if __name__ == "__main__":
    sys.exit(main())
