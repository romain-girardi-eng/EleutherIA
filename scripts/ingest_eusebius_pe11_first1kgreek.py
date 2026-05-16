"""Ingestion section-grained de la Praeparatio Evangelica VI.11 d'Eusèbe de Césarée.

Source TEI : OpenGreekAndLatin/First1KGreek (`tlg2018.tlg001.1st1K-grc1.xml`)
édition Dindorf re-encodée par Digital Divide Data / Univ. Leipzig.

Contexte scholarly :
  Amand 1945, p. 366, asserte que PE VI.11 reproduit quasi-littéralement
  la Philocalia 23 d'Origène — témoin majeur de la transmission Origène→Eusèbe
  pour l'antifatalisme patristique. PE VI.11 n'est pas l'un des 6 témoins canoniques
  d'Amand (qui couvrent VI.6.4-21), mais a un statut spécial via Phil. 23.

Pattern reproduit identique à `ingest_eusebius_pe6_first1kgreek.py` (commit 309cbfb7) :
  1. Re-fetch TEI local si manquant
  2. Parse `body/div[edition]/div[book=6]/div[chap=11]/div[sec=N]` pour N=1..83
  3. Crée 83 passages atomiques `passage_eusebius_praep_ev_6_11_N` avec grec verbatim
  4. Ajoute `part_of` (→ work) + `authored_by` (→ person) edges
  5. Enrichit l'edge existant `work_origen_philocalia --precedes--> work_eusebius_PE`
     avec `metadata.amand_verbatim_assertion: "Phil. 23 ≈ PE VI.11"`

Spécificités VI.11 :
  - Tag `metadata.is_amand_pe_vi_11: true` (statut Phil. 23 transmission)
  - Tag `metadata.amand_p366_phil23_transmission: true`
  - PAS de mapping pivots Amand B1 (B1 cible VI.6.4-21, pas VI.11)
  - PAS de création de passages Philocalia 23 (TEI Philocalia pas dans First1KGreek)

Idempotent : déjà-faits skip. NE COMMIT PAS.
"""
from __future__ import annotations

import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from lxml import etree

# -----------------------------------------------------------------------------
# Paths and constants
# -----------------------------------------------------------------------------

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
PHILOCALIA_WORK_ID = "work_origen_philocalia"

TIMESTAMP = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f+00:00")
CREATED_BY = "eusebius_pe11_ingestion_2026-05-16"
SOURCE_TAG = "OpenGreekAndLatin/First1KGreek (TEI bypass for dead Scaife)"

NUM_SECTIONS = 83
BOOK_N = 6
CHAP_N = 11


# -----------------------------------------------------------------------------
# TEI fetch & parse
# -----------------------------------------------------------------------------


def ensure_tei_local() -> Path:
    if TEI_LOCAL.exists() and TEI_LOCAL.stat().st_size > 100_000:
        return TEI_LOCAL
    TEI_LOCAL.parent.mkdir(parents=True, exist_ok=True)
    print(f"  Fetching TEI from {TEI_URL}")
    with urllib.request.urlopen(TEI_URL, timeout=60) as resp:
        data = resp.read()
    TEI_LOCAL.write_bytes(data)
    print(f"  Saved {len(data):,} bytes to {TEI_LOCAL}")
    return TEI_LOCAL


def extract_section_greek(root: etree._Element, book_n: int, chap_n: int, sec_n: int) -> str | None:
    body = root.find(f".//{TEI_NS}body")
    if body is None:
        return None
    edition = body.find(f"./{TEI_NS}div")
    book = next((d for d in edition.findall(f"./{TEI_NS}div") if d.get("n") == str(book_n)), None)
    if book is None:
        return None
    chap = next((d for d in book.findall(f"./{TEI_NS}div") if d.get("n") == str(chap_n)), None)
    if chap is None:
        return None
    sec = next((d for d in chap.findall(f"./{TEI_NS}div") if d.get("n") == str(sec_n)), None)
    if sec is None:
        return None
    text = etree.tostring(sec, method="text", encoding="unicode")
    return " ".join(text.split())


# -----------------------------------------------------------------------------
# Node / edge factories
# -----------------------------------------------------------------------------


def build_passage_node(sec_n: int, greek_text: str) -> dict:
    pid = f"passage_eusebius_praep_ev_6_11_{sec_n}"
    metadata: dict = {
        "attestation_type": "direct",
        "author": "Eusebius of Caesarea",
        "canonical_ref": f"VI.11.{sec_n}",
        "char_length": len(greek_text),
        "word_count": len(greek_text.split()),
        "cts_urn": f"{CTS_URN_BASE}:6.11.{sec_n}",
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
        "contains_greek_to_verify": False,  # canonical TEI source
        "period": "Late Antiquity",
        # Specific VI.11 flags : Philocalia 23 transmission marker
        "is_amand_pe_vi_11": True,
        "amand_p366_phil23_transmission": True,
        "amand_note": (
            "Amand 1945, p. 366 : PE VI.11 reproduit quasi-littéralement la Philocalia 23 "
            "d'Origène — témoin majeur de la transmission Origène→Eusèbe pour l'antifatalisme."
        ),
    }
    return {
        "id": pid,
        "node_id": pid,
        "type": "passage",
        "label": f"Eusebius, Praeparatio Evangelica, VI.11.{sec_n}",
        "description": greek_text,
        "alternative_names": "[]",
        "period": "Late Antiquity",
        "role": None,
        "school": "Patristic",
        "metadata": json.dumps(metadata, ensure_ascii=False),
        "created_at": TIMESTAMP,
        "updated_at": TIMESTAMP,
    }


def build_edge(source: str, target: str, relation: str, metadata: dict | None = None) -> dict:
    md = metadata or {}
    md.setdefault("created_by", CREATED_BY)
    md.setdefault("wave", "patristic_ingestion_2026-05-16")
    return {
        "edge_id": str(uuid4()),
        "source": source,
        "source_id": source,
        "target": target,
        "target_id": target,
        "relation": relation,
        "weight": 1.0,
        "metadata": json.dumps(md, ensure_ascii=False),
        "created_at": TIMESTAMP,
    }


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------


def main() -> int:
    print("== Loading current KG ==")
    nodes = [json.loads(line) for line in NODES_PATH.read_text().splitlines() if line.strip()]
    edges = [json.loads(line) for line in EDGES_PATH.read_text().splitlines() if line.strip()]
    print(f"  Nodes loaded: {len(nodes)}")
    print(f"  Edges loaded: {len(edges)}")

    node_by_id = {n["id"]: i for i, n in enumerate(nodes)}

    # Phase 0: Verify prerequisites
    for required in (WORK_ID, PERSON_ID):
        if required not in node_by_id:
            print(f"  FATAL: required node {required} missing — abort")
            return 1

    # Phase 1: Parse TEI + insert section passages
    print(f"\n== PHASE 1 : INGEST SECTION-GRAINED PASSAGES VI.{CHAP_N}.1-{NUM_SECTIONS} ==")
    tei_path = ensure_tei_local()
    tree = etree.parse(str(tei_path))
    root = tree.getroot()

    inserted = 0
    skipped_existing = 0
    missing_tei = 0
    new_passage_ids: list[str] = []
    for sec_n in range(1, NUM_SECTIONS + 1):
        pid = f"passage_eusebius_praep_ev_6_11_{sec_n}"
        if pid in node_by_id:
            skipped_existing += 1
            new_passage_ids.append(pid)
            continue
        greek = extract_section_greek(root, BOOK_N, CHAP_N, sec_n)
        if not greek:
            print(f"  MISSING in TEI: VI.{CHAP_N}.{sec_n}")
            missing_tei += 1
            continue
        node = build_passage_node(sec_n, greek)
        nodes.append(node)
        node_by_id[pid] = len(nodes) - 1
        new_passage_ids.append(pid)
        inserted += 1
    print(f"  Inserted: {inserted} ; skipped-existing: {skipped_existing} ; missing-TEI: {missing_tei}")

    # Phase 2: Insert part_of edges (passage → work)
    print("\n== PHASE 2 : INSERT PART_OF EDGES (SECTION → WORK) ==")
    part_of_inserted = 0
    existing_part_of = set()
    for e in edges:
        if e.get("relation") == "part_of":
            existing_part_of.add((e.get("source_id") or e.get("source"), e.get("target_id") or e.get("target")))
    for pid in new_passage_ids:
        if (pid, WORK_ID) in existing_part_of:
            continue
        edge = build_edge(pid, WORK_ID, "part_of", {"auto_generated": True})
        edges.append(edge)
        existing_part_of.add((pid, WORK_ID))
        part_of_inserted += 1
    print(f"  part_of inserted: {part_of_inserted}")

    # Phase 3: Insert authored_by edges (passage → person)
    print("\n== PHASE 3 : INSERT AUTHORED_BY EDGES (SECTION → PERSON) ==")
    authored_inserted = 0
    existing_authored = set()
    for e in edges:
        if e.get("relation") == "authored_by":
            existing_authored.add((e.get("source_id") or e.get("source"), e.get("target_id") or e.get("target")))
    for pid in new_passage_ids:
        if (pid, PERSON_ID) in existing_authored:
            continue
        edge = build_edge(pid, PERSON_ID, "authored_by", {"auto_generated": True, "propagated_from_work": True})
        edges.append(edge)
        existing_authored.add((pid, PERSON_ID))
        authored_inserted += 1
    print(f"  authored_by inserted: {authored_inserted}")

    # Phase 4: Enrich existing Philocalia→PE precedes edge with verbatim assertion
    print("\n== PHASE 4 : ENRICH ORIGEN PHILOCALIA → EUSEBIUS PE PRECEDES EDGE ==")
    enriched = 0
    for e in edges:
        src = e.get("source_id") or e.get("source")
        tgt = e.get("target_id") or e.get("target")
        if (
            src == PHILOCALIA_WORK_ID
            and tgt == WORK_ID
            and e.get("relation") == "precedes"
        ):
            md_raw = e.get("metadata") or "{}"
            md = json.loads(md_raw) if isinstance(md_raw, str) else md_raw
            if not md.get("amand_verbatim_assertion"):
                md["amand_verbatim_assertion"] = "Phil. 23 ≈ PE VI.11"
                md["amand_p366_quasi_verbatim"] = True
                md["pe_vi_11_section_range"] = f"VI.11.1-{NUM_SECTIONS}"
                md["enriched_by"] = CREATED_BY
                md["enriched_at"] = TIMESTAMP
                e["metadata"] = json.dumps(md, ensure_ascii=False)
                enriched += 1
    print(f"  Enriched: {enriched} precedes edge(s)")
    if enriched == 0:
        print("  WARN: no existing precedes edge from Philocalia→PE found.")

    # Phase 5: Write back
    print("\n== PHASE 5 : WRITE BACK ==")
    with NODES_PATH.open("w") as f:
        for n in nodes:
            f.write(json.dumps(n, ensure_ascii=False) + "\n")
    with EDGES_PATH.open("w") as f:
        for ed in edges:
            f.write(json.dumps(ed, ensure_ascii=False) + "\n")
    print(f"  nodes.jsonl: {len(nodes)}")
    print(f"  edges.jsonl: {len(edges)}")
    print(f"\n== EUSEBIUS PE VI.{CHAP_N} INGESTION COMPLETE ==")
    return 0


if __name__ == "__main__":
    sys.exit(main())
