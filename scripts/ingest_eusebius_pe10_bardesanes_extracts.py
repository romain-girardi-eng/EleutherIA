"""Ingestion section-grained de Praeparatio Evangelica VI.10 d'Eusèbe — Bardesane extracts.

Source TEI : OpenGreekAndLatin/First1KGreek (`tlg2018.tlg001.1st1K-grc1.xml`)
édition Dindorf re-encodée Univ. Leipzig.

Contexte scholarly :
  PE VI.10 contient les **extraits grecs préservés** du *Liber Legum Regionum* de Bardesane
  d'Édesse (154-222 CE), témoin secondaire crucial d'Amand 1945 pour la critique antifatale
  bardésanienne (libre arbitre vs déterminisme astral). Le syriaque original (Br. M. Add.
  14658) reste hors scope de ce script (rarement online). Les 50 sections de PE VI.10
  sont extraites verbatim du TEI canonique.

Pattern identique à `ingest_eusebius_pe11_first1kgreek.py`. Spécificités :
  - Tag `metadata.is_bardesanes_extract: true` sur toutes les sections (le chapitre VI.10
    entier est l'extrait bardésanien selon le découpage eusébien)
  - Tag `metadata.bardesanes_amand_witness: "secondary"` (témoin Amand secondaire,
    pas dans les 6 témoins B1 canoniques VI.6.4-21)
  - Edge `person_bardesanes_*` → `passage_eusebius_praep_ev_6_10_*` via `attested_by`
    SI le nœud Bardesane existe (audit avant)

Idempotent : déjà-faits skip. NE COMMIT PAS. Romain valide avant exécution.
"""
from __future__ import annotations

import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from lxml import etree

KG_ROOT = Path(__file__).resolve().parent.parent / "data" / "kg"
NODES_PATH = KG_ROOT / "nodes.jsonl"
EDGES_PATH = KG_ROOT / "edges.jsonl"

TEI_URL = (
    "https://raw.githubusercontent.com/OpenGreekAndLatin/First1KGreek/master/"
    "data/tlg2018/tlg001/tlg2018.tlg001.1st1K-grc1.xml"
)
TEI_LOCAL = Path("/tmp/eusebius_pe_tei/pe_1st1K_grc1.xml")
TEI_NS = "{http://www.tei-c.org/ns/1.0}"
CTS_URN_BASE = "urn:cts:greekLit:tlg2018.tlg001.1st1K-grc1"
WORK_ID = "work_eusebius_praeparatio_evangelica"
PERSON_ID = "person_eusebius_caesarea_d339"

TIMESTAMP = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f+00:00")
CREATED_BY = "eusebius_pe10_bardesanes_ingestion_2026-05-16"
SOURCE_TAG = "OpenGreekAndLatin/First1KGreek (TEI bypass for dead Scaife)"

NUM_SECTIONS = 50
BOOK_N = 6
CHAP_N = 10


def ensure_tei_local() -> Path:
    if TEI_LOCAL.exists() and TEI_LOCAL.stat().st_size > 100_000:
        return TEI_LOCAL
    TEI_LOCAL.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(TEI_URL, timeout=60) as resp:
        TEI_LOCAL.write_bytes(resp.read())
    return TEI_LOCAL


def extract_section_greek(root, book_n, chap_n, sec_n):
    body = root.find(f".//{TEI_NS}body")
    edition = body.find(f"./{TEI_NS}div") if body is not None else None
    book = next((d for d in edition.findall(f"./{TEI_NS}div") if d.get("n") == str(book_n)), None) if edition is not None else None
    chap = next((d for d in book.findall(f"./{TEI_NS}div") if d.get("n") == str(chap_n)), None) if book is not None else None
    sec = next((d for d in chap.findall(f"./{TEI_NS}div") if d.get("n") == str(sec_n)), None) if chap is not None else None
    if sec is None:
        return None
    text = etree.tostring(sec, method="text", encoding="unicode")
    return " ".join(text.split())


def build_passage_node(sec_n: int, greek_text: str) -> dict:
    pid = f"passage_eusebius_praep_ev_6_10_{sec_n}"
    metadata = {
        "attestation_type": "direct",
        "author": "Eusebius of Caesarea (excerpting Bardesanes via Diodorus of Tarsus)",
        "canonical_ref": f"VI.10.{sec_n}",
        "char_length": len(greek_text),
        "word_count": len(greek_text.split()),
        "cts_urn": f"{CTS_URN_BASE}:6.10.{sec_n}",
        "language": "grc",
        "passage_role": "original",
        "school": "Patristic",
        "work_canonical_id": "tlg2018.tlg001.1st1K-grc1",
        "work_title": "Praeparatio Evangelica",
        "book": BOOK_N,
        "chapter": CHAP_N,
        "section": sec_n,
        "edition": "Dindorf t. I (Leipzig 1867), re-encoded TEI by Digital Divide Data / Univ. Leipzig",
        "source_tei": "OpenGreekAndLatin/First1KGreek tlg2018.tlg001.1st1K-grc1.xml",
        "source_tei_url": TEI_URL,
        "source": SOURCE_TAG,
        "created_by": CREATED_BY,
        "contains_greek_to_verify": False,
        "period": "Late Antiquity",
        "is_bardesanes_extract": True,
        "bardesanes_amand_witness": "secondary",
        "bardesanes_note": (
            "Extrait grec du Liber Legum Regionum de Bardesane (154-222 CE), "
            "préservé par Eusèbe dans PE VI.10 (chapitre entier). Le syriaque "
            "original (Br. M. Add. 14658) hors scope de l'ingestion automatique."
        ),
    }
    return {
        "id": pid,
        "node_id": pid,
        "type": "passage",
        "label": f"Eusebius (excerpting Bardesanes), Praeparatio Evangelica, VI.10.{sec_n}",
        "description": greek_text,
        "alternative_names": "[]",
        "period": "Late Antiquity",
        "role": None,
        "school": "Patristic",
        "metadata": json.dumps(metadata, ensure_ascii=False),
        "created_at": TIMESTAMP,
        "updated_at": TIMESTAMP,
    }


def build_edge(source, target, relation, metadata=None):
    md = metadata or {}
    md.setdefault("created_by", CREATED_BY)
    md.setdefault("wave", "patristic_ingestion_2026-05-16")
    return {
        "edge_id": str(uuid4()),
        "source": source, "source_id": source,
        "target": target, "target_id": target,
        "relation": relation, "weight": 1.0,
        "metadata": json.dumps(md, ensure_ascii=False),
        "created_at": TIMESTAMP,
    }


def main() -> int:
    nodes = [json.loads(line) for line in NODES_PATH.read_text().splitlines() if line.strip()]
    edges = [json.loads(line) for line in EDGES_PATH.read_text().splitlines() if line.strip()]
    node_by_id = {n["id"]: i for i, n in enumerate(nodes)}

    for required in (WORK_ID, PERSON_ID):
        if required not in node_by_id:
            print(f"FATAL: required node {required} missing")
            return 1

    tei_path = ensure_tei_local()
    tree = etree.parse(str(tei_path))
    root = tree.getroot()

    inserted = 0
    new_passage_ids = []
    for sec_n in range(1, NUM_SECTIONS + 1):
        pid = f"passage_eusebius_praep_ev_6_10_{sec_n}"
        if pid in node_by_id:
            new_passage_ids.append(pid)
            continue
        greek = extract_section_greek(root, BOOK_N, CHAP_N, sec_n)
        if not greek:
            print(f"  MISSING in TEI: VI.{CHAP_N}.{sec_n}")
            continue
        node = build_passage_node(sec_n, greek)
        nodes.append(node)
        node_by_id[pid] = len(nodes) - 1
        new_passage_ids.append(pid)
        inserted += 1
    print(f"Inserted: {inserted}")

    existing_part_of = {(e.get("source_id") or e.get("source"), e.get("target_id") or e.get("target"))
                       for e in edges if e.get("relation") == "part_of"}
    existing_authored = {(e.get("source_id") or e.get("source"), e.get("target_id") or e.get("target"))
                        for e in edges if e.get("relation") == "authored_by"}

    for pid in new_passage_ids:
        if (pid, WORK_ID) not in existing_part_of:
            edges.append(build_edge(pid, WORK_ID, "part_of", {"auto_generated": True}))
            existing_part_of.add((pid, WORK_ID))
        if (pid, PERSON_ID) not in existing_authored:
            edges.append(build_edge(pid, PERSON_ID, "authored_by",
                                    {"auto_generated": True, "propagated_from_work": True}))
            existing_authored.add((pid, PERSON_ID))

    # Try to link to Bardesanes person node if exists (attested_by)
    bardes_candidates = [n["id"] for n in nodes if "bardes" in n["id"].lower() and n.get("type") == "person"]
    if bardes_candidates:
        bardes_id = bardes_candidates[0]
        existing_attests = {(e.get("source_id") or e.get("source"), e.get("target_id") or e.get("target"))
                           for e in edges if e.get("relation") == "attests"}
        # passage Eusebius --attests--> person? No, that's wrong direction.
        # Use influences_by or doxographic note in metadata instead.
        # For now, just print existence
        print(f"  Bardesanes person node found: {bardes_id}")
        print("  Note: skipped automatic edge — Bardesane→PE VI.10 relation needs scholarly decision.")
    else:
        print("  No Bardesanes person node — consider creating one before linking.")

    with NODES_PATH.open("w") as f:
        for n in nodes:
            f.write(json.dumps(n, ensure_ascii=False) + "\n")
    with EDGES_PATH.open("w") as f:
        for e in edges:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    print(f"DONE: nodes={len(nodes)} edges={len(edges)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
