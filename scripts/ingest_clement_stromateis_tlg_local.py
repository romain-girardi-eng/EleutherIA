"""Ingestion section-grained de sélections Stromateis Clément d'Alexandrie depuis TLG XML.

Source critique locale (BACKUP du script archive.org PG 8/9):
  [local-path] SHAL/02_Corpus/TLG/
    TLG_tlg0555_Clemens_Alexandrinus_Stromata.xml

TLG identifier: tlg0555.tlg004 (perseus-grc2 edition). Format TEI.
Découpage Stählin GCS (book→chapter→section) — sections continues à travers livre.

Contexte scholarly:
  Amand 1945 Livre II Ch. III §III.B9 :
    - Strom. I.17.82-84 (Otto Stählin) = section anti-déterministe "μὴ κωλῦον αἴτιον" :
      Clément critique l'argument stoïcien "le non-empêchant est cause" en distinguant
      proairesis (choix volontaire) et physique nécessaire.
    - Strom. II.11.50-52 = chap. sur prophétie/foi (Amand "glissement chrétien faith/unbelief").

Cibles d'ingestion (6 sections):
  - Strom. I.17.82, 83, 84
  - Strom. II.11.50, 51, 52

Ces sections n'existent pas dans le KG actuel (0 passage Stromateis ingéré
avant ce script). Le script existant `scripts/ingest_clement_stromateis_pg8_9.py`
était une stub archive.org → pas exécuté. Cette version utilise directement le
TLG XML local (qualité critique, pas d'OCR).

Pipeline:
  1. Parse XML TLG via ElementTree
  2. Pour chaque (book, chap, section) cible : extrait texte grec verbatim
  3. Crée passage_clement_strom_{book}_{chap}_{section}
  4. Edges part_of (→ work_clement_stromateis) + authored_by (→ person_clement_alexandria)
  5. Edges evidenced_by depuis arguments Clément-Amand B9 vers passages appropriés

Idempotent. NE COMMIT PAS.
"""
from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

KG_ROOT = Path(__file__).resolve().parent.parent / "data" / "kg"
NODES_PATH = KG_ROOT / "nodes.jsonl"
EDGES_PATH = KG_ROOT / "edges.jsonl"

XML_SOURCE = Path(
    "[local-path] SHAL/02_Corpus/TLG/"
    "TLG_tlg0555_Clemens_Alexandrinus_Stromata.xml"
)

NS = {"tei": "http://www.tei-c.org/ns/1.0"}
WORK_ID = "work_clement_stromateis"
PERSON_ID = "person_clement_alexandria"
CTS_URN_BASE = "urn:cts:greekLit:tlg0555.tlg004.perseus-grc2"

TIMESTAMP = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f+00:00")
CREATED_BY = "clement_stromateis_tlg_ingestion_2026-05-16"
SOURCE_EDITION = "Stählin GCS (TLG perseus-grc2 TEI re-encoding)"
SOURCE_TAG = "TLG_tlg0555_Clemens_Alexandrinus_Stromata.xml (local corpus)"

# Target sections (book, chapter, section)
TARGETS: list[tuple[int, int, int]] = [
    (1, 17, 82),
    (1, 17, 83),
    (1, 17, 84),
    (2, 11, 50),
    (2, 11, 51),
    (2, 11, 52),
]

# Argument anchors (Amand B9)
ARG_ANCHORS: list[tuple[str, list[tuple[int, int, int]]]] = [
    # Strom. I.83.5 praise/blame argument (already exists)
    (
        "argument_clement_alex_strom_1_83_5_praise_blame",
        [(1, 17, 83)],
    ),
    # Strom. II.11.1-2 glissement faith/unbelief (Amand)
    (
        "argument_clement_alex_carneadean_glissement_faith_unbelief",
        [(2, 11, 50), (2, 11, 51), (2, 11, 52)],
    ),
    # Generic Grace–Freedom Synergy via Stoic Assent (Strom. II.6–15)
    (
        "argument_clement_grace_synergy_assent",
        [(2, 11, 50), (2, 11, 51), (2, 11, 52)],
    ),
]

# -----------------------------------------------------------------------------
# Parser
# -----------------------------------------------------------------------------


def text_of(el: ET.Element) -> str:
    parts: list[str] = []
    if el.text:
        parts.append(el.text)
    for child in el:
        parts.append(text_of(child))
        if child.tail:
            parts.append(child.tail)
    return "".join(parts)


def extract_section(
    edition: ET.Element, book_n: int, chap_n: int, sec_n: int
) -> str | None:
    for bd in edition.findall("tei:div", NS):
        if bd.get("subtype") == "book" and bd.get("n") == str(book_n):
            for cd in bd.findall("tei:div", NS):
                if cd.get("n") == str(chap_n):
                    for sd in cd.findall("tei:div", NS):
                        if sd.get("n") == str(sec_n):
                            t = text_of(sd)
                            return re.sub(r"\s+", " ", t).strip()
    return None


# -----------------------------------------------------------------------------
# Node + edge factories
# -----------------------------------------------------------------------------


def build_passage_node(book: int, chap: int, sec: int, greek: str) -> dict:
    pid = f"passage_clement_strom_{book}_{chap}_{sec}"
    label_ref = f"Strom. {to_roman(book)}.{chap}.{sec}"
    cts_section = f"{book}.{chap}.{sec}"

    metadata = {
        "attestation_type": "direct",
        "author": "Clement of Alexandria",
        "canonical_ref": label_ref,
        "char_length": len(greek),
        "word_count": len(greek.split()),
        "cts_urn": f"{CTS_URN_BASE}:{cts_section}",
        "language": "grc",
        "passage_role": "original",
        "school": "Christian Platonism",
        "work_title": "Stromateis",
        "book": book,
        "chapter": chap,
        "section": sec,
        "edition": SOURCE_EDITION,
        "edition_full": (
            "Otto Stählin, Clemens Alexandrinus, vol. 2 (Stromata I-VI), GCS 15 (1906) ; "
            "vol. 3 (Stromata VII-VIII), GCS 17 (1909) ; "
            "re-encoded TEI from Perseus (tlg0555.tlg004.perseus-grc2)"
        ),
        "source": SOURCE_TAG,
        "source_local_path": str(XML_SOURCE),
        "created_by": CREATED_BY,
        "contains_greek_to_verify": False,
        "period": "Patristic",
        "text_grc": greek,
        "is_amand_b9_clement_witness": True,
        "amand_note": (
            "Amand 1945 §III.B9 : Clément critique le déterminisme stoïcien "
            "« μὴ κωλῦον αἴτιον » (Strom. I.17.82-84) et opère un glissement "
            "chrétien faith/unbelief sur la libre adhésion (Strom. II.11)."
        ),
    }

    return {
        "id": pid,
        "node_id": pid,
        "type": "passage",
        "label": f"Clement of Alexandria, {label_ref}",
        "description": greek,
        "alternative_names": "[]",
        "period": "Patristic",
        "role": None,
        "school": "Christian Platonism",
        "metadata": json.dumps(metadata, ensure_ascii=False),
        "created_at": TIMESTAMP,
        "updated_at": TIMESTAMP,
    }


def to_roman(n: int) -> str:
    return {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI", 7: "VII", 8: "VIII"}.get(n, str(n))


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
    print("== CLEMENT STROMATEIS TLG INGESTION ==")
    print("\n== PHASE 0 : LOAD KG ==")
    nodes = [json.loads(line) for line in NODES_PATH.read_text().splitlines() if line.strip()]
    edges = [json.loads(line) for line in EDGES_PATH.read_text().splitlines() if line.strip()]
    node_by_id = {n["id"]: i for i, n in enumerate(nodes)}
    print(f"  Nodes: {len(nodes)} ; edges: {len(edges)}")

    for req in (WORK_ID, PERSON_ID):
        if req not in node_by_id:
            print(f"  FATAL: missing required node {req}")
            return 1

    print("\n== PHASE 1 : PARSE TLG XML ==")
    if not XML_SOURCE.exists():
        print(f"  FATAL: source XML not found: {XML_SOURCE}")
        return 1
    tree = ET.parse(str(XML_SOURCE))
    root = tree.getroot()
    body = root.find("tei:text", NS).find("tei:body", NS)
    edition = body.find("tei:div", NS)
    print(f"  XML parsed ({XML_SOURCE.stat().st_size:,} bytes)")

    print("\n== PHASE 2 : CREATE PASSAGE NODES ==")
    inserted = 0
    skipped = 0
    missing = 0
    new_pids: dict[tuple[int, int, int], str] = {}
    for (b, c, s) in TARGETS:
        pid = f"passage_clement_strom_{b}_{c}_{s}"
        new_pids[(b, c, s)] = pid
        if pid in node_by_id:
            skipped += 1
            continue
        greek = extract_section(edition, b, c, s)
        if not greek:
            print(f"  MISSING in TLG: Strom {to_roman(b)}.{c}.{s}")
            missing += 1
            continue
        node = build_passage_node(b, c, s, greek)
        nodes.append(node)
        node_by_id[pid] = len(nodes) - 1
        inserted += 1
        print(f"  + {pid} ({len(greek)} chars)")
    print(f"  Inserted: {inserted} ; skipped: {skipped} ; missing: {missing}")

    print("\n== PHASE 3 : PART_OF + AUTHORED_BY EDGES ==")
    existing_part_of = set()
    existing_authored = set()
    for e in edges:
        src = e.get("source_id") or e.get("source")
        tgt = e.get("target_id") or e.get("target")
        if e.get("relation") == "part_of":
            existing_part_of.add((src, tgt))
        elif e.get("relation") == "authored_by":
            existing_authored.add((src, tgt))

    part_of_inserted = authored_inserted = 0
    for pid in new_pids.values():
        if pid not in node_by_id:
            continue  # skip missing
        if (pid, WORK_ID) not in existing_part_of:
            edges.append(build_edge(pid, WORK_ID, "part_of", {"auto_generated": True}))
            existing_part_of.add((pid, WORK_ID))
            part_of_inserted += 1
        if (pid, PERSON_ID) not in existing_authored:
            edges.append(
                build_edge(
                    pid,
                    PERSON_ID,
                    "authored_by",
                    {"auto_generated": True, "propagated_from_work": True},
                )
            )
            existing_authored.add((pid, PERSON_ID))
            authored_inserted += 1
    print(f"  part_of: {part_of_inserted} ; authored_by: {authored_inserted}")

    print("\n== PHASE 4 : EVIDENCED_BY EDGES (AMAND B9 ARGUMENTS → STROM SECTIONS) ==")
    existing_evidenced = set()
    for e in edges:
        if e.get("relation") == "evidenced_by":
            src = e.get("source_id") or e.get("source")
            tgt = e.get("target_id") or e.get("target")
            existing_evidenced.add((src, tgt))
    ev_inserted = ev_skipped = 0
    missing_args = []
    for arg_id, targets in ARG_ANCHORS:
        if arg_id not in node_by_id:
            missing_args.append(arg_id)
            continue
        for tgt in targets:
            tgt_pid = new_pids.get(tgt)
            if not tgt_pid or tgt_pid not in node_by_id:
                continue
            if (arg_id, tgt_pid) in existing_evidenced:
                ev_skipped += 1
                continue
            edges.append(
                build_edge(
                    arg_id,
                    tgt_pid,
                    "evidenced_by",
                    {
                        "anchor_source": "amand1945_b9_clement_witness",
                        "anchor_via": "strom_tlg_section_grained",
                    },
                )
            )
            existing_evidenced.add((arg_id, tgt_pid))
            ev_inserted += 1
    print(f"  evidenced_by inserted: {ev_inserted} ; skipped: {ev_skipped}")
    if missing_args:
        print(f"  WARN: missing arg nodes: {missing_args}")

    print("\n== PHASE 5 : WRITE BACK ==")
    with NODES_PATH.open("w") as f:
        for n in nodes:
            f.write(json.dumps(n, ensure_ascii=False) + "\n")
    with EDGES_PATH.open("w") as f:
        for ed in edges:
            f.write(json.dumps(ed, ensure_ascii=False) + "\n")
    print(f"  nodes.jsonl: {len(nodes)}")
    print(f"  edges.jsonl: {len(edges)}")
    print("\n== CLEMENT STROMATEIS INGESTION COMPLETE ==")
    return 0


if __name__ == "__main__":
    sys.exit(main())
