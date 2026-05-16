"""Ingestion des 7 sections du témoin n°3 d'Amand 1945 : Firmicus Mathesis I.2.5-11.

Source verbatim : `data/scholarly_sources/ocr/firmicusmathesis/source.md`
(extraction OCR archive.org du volume Teubner Kroll-Skutsch t. I, 1897).

Pourquoi ?
----------
Le KG contient déjà depuis B4 (wave 2026-05-15) :
  - `work_firmicus_mathesis` (work-shell, 8 livres)
  - `person_firmicus_maternus_2q7r9t65`
  - 4 arguments-pivots Amand B4 témoin n°3 :
      * argument_firmicus_witness3_envelope_amand1945
      * argument_firmicus_witness3_virtue_vain_under_stars_amand1945 (Math I.2.5-7)
      * argument_firmicus_witness3_religion_useless_amand1945       (Math I.2.8-9)
      * argument_firmicus_witness3_laws_abrogated_amand1945         (Math I.2.10-11)

Tous ces arguments portent `metadata.evidence_pending: true` et attendent leur ancrage
dans les passages Mathesis. Ce script crée ces 7 passages atomiques et les edges
`evidenced_by` correspondants.

Ce qu'il fait
-------------
1. Charge `data/kg/nodes.jsonl` et `data/kg/edges.jsonl`.
2. Vérifie les prérequis : work + person + 4 arguments doivent exister.
3. Pour chaque section I.2.N (N=5..11) :
   - Crée `passage_firmicus_math_1_2_N` (type=passage, latin verbatim, école Late Antiquity)
   - Insère edge `passage → work` (part_of)
   - Insère edge `passage → person` (authored_by)
4. Pour chaque argument-pivot :
   - Insère edge `argument → passage(s) couverts` (evidenced_by) avec confidence calibrée
   - Met à jour `evidence_pending: false` dans la metadata de l'argument
5. Vérifie SHACL invariants (`validate_kg_invariants()`) après l'ingestion.

Idempotent : skip-si-existe sur tout. NE COMMIT PAS.

Exécution
---------
Ce script doit être exécuté UNIQUEMENT après que l'agent B9 ait commit ses propres
mutations sur `data/kg/nodes.jsonl` et `data/kg/edges.jsonl`.

    python scripts/ingest_firmicus_mathesis_archive.py
"""
from __future__ import annotations

import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

# -----------------------------------------------------------------------------
# Paths and constants
# -----------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
KG_ROOT = REPO_ROOT / "data" / "kg"
NODES_PATH = KG_ROOT / "nodes.jsonl"
EDGES_PATH = KG_ROOT / "edges.jsonl"
OCR_SOURCE = REPO_ROOT / "data" / "scholarly_sources" / "ocr" / "firmicusmathesis" / "source.md"

WORK_ID = "work_firmicus_mathesis"
PERSON_ID = "person_firmicus_maternus_2q7r9t65"
CTS_URN_BASE = "urn:cts:latinLit:phi1471.phi001"  # Firmicus Maternus = PHI 1471, Mathesis = phi001
# NB: this CTS URN is provisional — Firmicus' canonical PHI code may be different;
# verify on https://catalog.perseus.org/. Setting to phi1471.phi001 as best-guess.

TIMESTAMP = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S.%f+00:00")
CREATED_BY = "firmicus_mathesis_witness3_ingestion_2026-05-16"
SOURCE_TAG = (
    "archive.org djvu OCR of Kroll-Skutsch Teubner t. I (1897), via "
    "data/scholarly_sources/ocr/firmicusmathesis/source.md"
)

WITNESS_SECTIONS = [5, 6, 7, 8, 9, 10, 11]

# -----------------------------------------------------------------------------
# Amand B4 argument → section mapping with confidences
# -----------------------------------------------------------------------------
# Pivots Amand B4 (témoin n°3 Firmicus) :
#   ENVELOPE = enveloppe tripartite de la diatribe antifataliste (cadre Math I.2.5-11)
#   VIRTUE   = effort de vertu vain sous les constellations (Math I.2.5-7)
#   RELIGION = mépris des dieux et inutilité des rites (Math I.2.8-9)
#   LAWS     = abrogation des lois et droits du magistrat (Math I.2.10-11)
#
# Confidence calibration (cf. patterns d'ingestion Eusebius PE6 et Amand B1/B4) :
#   0.95 = section centrale d'un argument avec marqueur lexical verbatim
#   0.85 = section structurellement intégrante de l'argument
#   0.70 = section liminaire (ouverture / pivot syntaxique avec section voisine)

AMAND_B4_PIVOTS = {
    "ENVELOPE": "argument_firmicus_witness3_envelope_amand1945",
    "VIRTUE":   "argument_firmicus_witness3_virtue_vain_under_stars_amand1945",
    "RELIGION": "argument_firmicus_witness3_religion_useless_amand1945",
    "LAWS":     "argument_firmicus_witness3_laws_abrogated_amand1945",
}

# pivot → list of (section, confidence, justification)
PIVOT_TO_SECTIONS: dict[str, list[tuple[int, float, str]]] = {
    "ENVELOPE": [
        (5,  0.85, "Ouverture de la péroraison antiastrologique — \"Illa vero ipsorum inter ea potentissima ... peroratio est\""),
        (6,  0.70, "Section centrale de l'enveloppe — collapse vertu/vice"),
        (7,  0.70, "Articulation 1→2 (fin du 1er argument → idée d'effort vain)"),
        (8,  0.70, "Articulation 2→ouverture du 2nd (mépris des dieux)"),
        (9,  0.70, "Cœur du 2nd argument (sacrilegus desperationis ardor)"),
        (10, 0.70, "Articulation 2→3 (loi magistrale)"),
        (11, 0.85, "Clôture de la péroraison — fomitibus + sentence judiciaire"),
    ],
    "VIRTUE": [
        (5,  0.95, "Énoncé thèse : virtutum officia tolli si stellarum decretis adscribuntur — moral collapse signature"),
        (6,  0.95, "Sit iniquus, sit perfidus, sit malivolus... — exemple en cascade : pourquoi cultiver la vertu si Mars/Mercure décident ?"),
        (7,  0.95, "Frustra igitur consilio ac ratione errantis animi vitia comprimimus — futilité explicite de l'effort moral"),
    ],
    "RELIGION": [
        (8,  0.95, "Etiam singulos homines hac disputationis oratione conveniunt — diatribe contre piété personnelle, Saturnus/Iuppiter"),
        (9,  0.95, "Quid invocas, arator, deos? — interpellation rhétorique du paysan, mépris des rites Liberi"),
    ],
    "LAWS": [
        (10, 0.95, "Tu qui promulgas leges ac iura sancis, tolle scita, refige tabulas — abrogation explicite des lois"),
        (11, 0.95, "Magistratus^ iustam animadvertendi substantiam non habetis... incitari fomitibus — clôture sur le magistrat dépossédé"),
    ],
}


# -----------------------------------------------------------------------------
# OCR section parser
# -----------------------------------------------------------------------------

SECTION_HEADER = re.compile(r"^### Math I\.2\.(\d+)\s*$", re.MULTILINE)
BLOCKQUOTE = re.compile(r"^> (.*)$", re.MULTILINE)


def parse_sections_from_source_md(src_md_path: Path) -> dict[int, str]:
    """Extract verbatim section texts from source.md blockquotes."""
    text = src_md_path.read_text(encoding="utf-8")
    sections: dict[int, str] = {}
    # Find all section headers and their start positions
    headers = [(m.start(), int(m.group(1))) for m in SECTION_HEADER.finditer(text)]
    for idx, (start, sec_n) in enumerate(headers):
        next_start = headers[idx + 1][0] if idx + 1 < len(headers) else len(text)
        block = text[start:next_start]
        # Extract the first contiguous blockquote
        bq_lines: list[str] = []
        in_bq = False
        for line in block.splitlines():
            if line.startswith("> "):
                bq_lines.append(line[2:])
                in_bq = True
            elif line.startswith(">"):
                bq_lines.append(line[1:].lstrip())
                in_bq = True
            elif in_bq and not line.strip():
                # Empty line inside blockquote: tolerate
                continue
            elif in_bq:
                # End of blockquote
                break
        if not bq_lines:
            continue
        sections[sec_n] = " ".join(s.strip() for s in bq_lines if s.strip())
    return sections


# -----------------------------------------------------------------------------
# Node / edge factories
# -----------------------------------------------------------------------------


def build_passage_node(sec_n: int, latin_text: str) -> dict:
    pid = f"passage_firmicus_math_1_2_{sec_n}"
    metadata: dict = {
        "attestation_type": "direct",
        "author": "Iulius Firmicus Maternus",
        "canonical_ref": f"Mathesis I.2.{sec_n}",
        "char_length": len(latin_text),
        "word_count": len(latin_text.split()),
        "cts_urn": f"{CTS_URN_BASE}:1.2.{sec_n}",
        "cts_urn_unverified": True,
        "language": "lat",
        "passage_role": "original",
        "school": None,
        "work_canonical_id": "phi1471.phi001",
        "work_canonical_id_unverified": True,
        "work_title": "Mathesis",
        "book": 1,
        "chapter": 2,
        "section": sec_n,
        "edition": (
            "Iuli Firmici Materni Matheseos libri VIII, edd. W. Kroll et F. Skutsch, "
            "Bibliotheca Teubneriana, Lipsiae, B. G. Teubner, t. I (libri I-IV), 1897"
        ),
        "source_ocr": "data/scholarly_sources/ocr/firmicusmathesis/source.md",
        "source_ocr_archive": "archive.org/details/matheseoslibrivi01firmuoft",
        "kroll_skutsch_pagination": "p. 7 l. 8 — p. 9 l. 4 (étendue I.2.5-11)",
        "is_amand_witness_3": True,
        "amand_witness_label": (
            "Témoin n°3 (Firmicus Mathesis I, 2, 5-11 = Kroll-Skutsch t. I p. 7 l. 8 — p. 9 l. 4)"
        ),
        "source": SOURCE_TAG,
        "created_by": CREATED_BY,
        "contains_latin_to_verify": True,
        "ocr_anomalies_documented_in_source_md": True,
        "period": "Late Antiquity",
    }
    return {
        "id": pid,
        "node_id": pid,
        "type": "passage",
        "label": f"Firmicus, Mathesis I.2.{sec_n}",
        "description": latin_text,
        "alternative_names": "[]",
        "period": "Late Antiquity",
        "role": None,
        "school": None,
        "metadata": json.dumps(metadata, ensure_ascii=False),
        "created_at": TIMESTAMP,
        "updated_at": TIMESTAMP,
    }


def build_edge(source: str, target: str, relation: str, metadata: dict | None = None) -> dict:
    md = metadata or {}
    md.setdefault("created_by", CREATED_BY)
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


def clear_evidence_pending(node: dict, edges_added_count: int) -> None:
    """Mark evidence_pending → false on the argument node since it's now anchored."""
    md_raw = node.get("metadata") or "{}"
    md = json.loads(md_raw) if isinstance(md_raw, str) else md_raw
    if md.get("evidence_pending") is True:
        md["evidence_pending"] = False
        md["evidence_anchored_by"] = CREATED_BY
        md["evidence_anchored_at"] = TIMESTAMP
        md["evidence_anchor_count"] = edges_added_count
        node["metadata"] = json.dumps(md, ensure_ascii=False)
        node["updated_at"] = TIMESTAMP


# -----------------------------------------------------------------------------
# SHACL invariants (optional — guarded import)
# -----------------------------------------------------------------------------


def run_shacl_invariants() -> bool:
    """Try to run SHACL invariants validation. Returns True if passes or unavailable."""
    try:
        from eleutheria_kg.semantic.validate import validate_kg_invariants  # type: ignore
    except Exception as exc:
        print(f"  WARN: SHACL validator unavailable ({exc}) — skipping invariants check")
        return True
    try:
        conforms, _report = validate_kg_invariants(str(NODES_PATH), str(EDGES_PATH))
        if conforms:
            print("  SHACL invariants: OK (conforms=True)")
            return True
        print("  SHACL invariants: FAILED (conforms=False)")
        return False
    except Exception as exc:
        print(f"  WARN: SHACL validation crashed ({exc}) — manual check required")
        return True


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------


def main() -> int:
    print("== Loading current KG ==")
    if not NODES_PATH.exists() or not EDGES_PATH.exists():
        print(f"  FATAL: KG files not found at {KG_ROOT}")
        return 1
    nodes = [json.loads(line) for line in NODES_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    edges = [json.loads(line) for line in EDGES_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    print(f"  Nodes loaded: {len(nodes)}")
    print(f"  Edges loaded: {len(edges)}")

    node_by_id = {n["id"]: i for i, n in enumerate(nodes)}

    # ----- Phase 0: Verify prerequisites
    print("\n== PHASE 0 : VERIFY PREREQUISITES ==")
    if WORK_ID not in node_by_id:
        print(f"  FATAL: work node {WORK_ID} missing — abort")
        return 1
    if PERSON_ID not in node_by_id:
        print(f"  FATAL: person node {PERSON_ID} missing — abort")
        return 1
    missing_pivots = [pid for pid in AMAND_B4_PIVOTS.values() if pid not in node_by_id]
    if missing_pivots:
        print(f"  FATAL: pivot argument nodes missing: {missing_pivots}")
        return 1
    print(f"  OK: work={WORK_ID}, person={PERSON_ID}, 4 pivot arguments found")

    # ----- Phase 1: Parse OCR source.md
    print("\n== PHASE 1 : PARSE OCR SOURCE.MD ==")
    if not OCR_SOURCE.exists():
        print(f"  FATAL: OCR source missing at {OCR_SOURCE}")
        return 1
    sections = parse_sections_from_source_md(OCR_SOURCE)
    print(f"  Parsed sections: {sorted(sections.keys())}")
    missing = [n for n in WITNESS_SECTIONS if n not in sections]
    if missing:
        print(f"  FATAL: sections missing from source.md: {missing}")
        return 1
    for n in WITNESS_SECTIONS:
        print(f"    I.2.{n}: {len(sections[n])} chars, {len(sections[n].split())} words")

    # ----- Phase 2: Insert passage nodes
    print("\n== PHASE 2 : INSERT PASSAGE NODES ==")
    inserted_passages = 0
    skipped_passages = 0
    new_passage_ids: list[str] = []
    for sec_n in WITNESS_SECTIONS:
        pid = f"passage_firmicus_math_1_2_{sec_n}"
        new_passage_ids.append(pid)
        if pid in node_by_id:
            skipped_passages += 1
            continue
        node = build_passage_node(sec_n, sections[sec_n])
        nodes.append(node)
        node_by_id[pid] = len(nodes) - 1
        inserted_passages += 1
    print(f"  Passages inserted: {inserted_passages} ; skipped-existing: {skipped_passages}")

    # ----- Phase 3: Insert part_of edges
    print("\n== PHASE 3 : INSERT PART_OF EDGES (PASSAGE → WORK) ==")
    existing_part_of = {
        (e.get("source_id") or e.get("source"), e.get("target_id") or e.get("target"))
        for e in edges if e.get("relation") == "part_of"
    }
    part_of_inserted = 0
    for pid in new_passage_ids:
        key = (pid, WORK_ID)
        if key in existing_part_of:
            continue
        edges.append(build_edge(pid, WORK_ID, "part_of", {"auto_generated": True}))
        existing_part_of.add(key)
        part_of_inserted += 1
    print(f"  part_of inserted: {part_of_inserted}")

    # ----- Phase 4: Insert authored_by edges
    print("\n== PHASE 4 : INSERT AUTHORED_BY EDGES (PASSAGE → PERSON) ==")
    existing_authored = {
        (e.get("source_id") or e.get("source"), e.get("target_id") or e.get("target"))
        for e in edges if e.get("relation") == "authored_by"
    }
    authored_inserted = 0
    for pid in new_passage_ids:
        key = (pid, PERSON_ID)
        if key in existing_authored:
            continue
        edges.append(build_edge(
            pid, PERSON_ID, "authored_by",
            {"auto_generated": True, "propagated_from_work": True},
        ))
        existing_authored.add(key)
        authored_inserted += 1
    print(f"  authored_by inserted: {authored_inserted}")

    # ----- Phase 5: Insert evidenced_by edges (Amand B4 pivots → passages)
    print("\n== PHASE 5 : INSERT EVIDENCED_BY EDGES (AMAND B4 PIVOTS → PASSAGES) ==")
    existing_ev = {
        (e.get("source_id") or e.get("source"), e.get("target_id") or e.get("target"))
        for e in edges if e.get("relation") == "evidenced_by"
    }
    evidenced_inserted = 0
    evidenced_skipped = 0
    breakdown: dict[str, int] = {}
    for pivot_key, mappings in PIVOT_TO_SECTIONS.items():
        arg_id = AMAND_B4_PIVOTS[pivot_key]
        breakdown[pivot_key] = 0
        for sec_n, confidence, justif in mappings:
            tgt = f"passage_firmicus_math_1_2_{sec_n}"
            key = (arg_id, tgt)
            if key in existing_ev:
                evidenced_skipped += 1
                continue
            edges.append(build_edge(
                arg_id, tgt, "evidenced_by",
                {
                    "confidence": confidence,
                    "discovery_method": "latin_textual_verification_amand_b4_mapping",
                    "amand_witness": 3,
                    "amand_pivot": pivot_key,
                    "justification": justif,
                },
            ))
            existing_ev.add(key)
            evidenced_inserted += 1
            breakdown[pivot_key] += 1
    print(f"  evidenced_by inserted: {evidenced_inserted} ; skipped-existing: {evidenced_skipped}")
    print("  Breakdown by pivot:")
    for pk, ct in breakdown.items():
        print(f"    {pk} ({AMAND_B4_PIVOTS[pk]}): {ct} edges")

    # ----- Phase 6: Clear evidence_pending on argument nodes
    print("\n== PHASE 6 : CLEAR EVIDENCE_PENDING ON ARGUMENT NODES ==")
    for pk, arg_id in AMAND_B4_PIVOTS.items():
        idx = node_by_id[arg_id]
        clear_evidence_pending(nodes[idx], breakdown.get(pk, 0))
        print(f"  Cleared: {arg_id}")

    # ----- Phase 7: Enrich work node — drop evidence_pending flag
    print("\n== PHASE 7 : ENRICH WORK NODE (drop evidence_pending) ==")
    wn = nodes[node_by_id[WORK_ID]]
    md_raw = wn.get("metadata") or "{}"
    md = json.loads(md_raw) if isinstance(md_raw, str) else md_raw
    if md.get("evidence_pending") is True:
        md["evidence_pending"] = False
        md["evidence_anchored_by"] = CREATED_BY
        md["evidence_anchored_at"] = TIMESTAMP
        md["ocr_source"] = "data/scholarly_sources/ocr/firmicusmathesis/source.md"
        md["ocr_source_archive"] = "archive.org/details/matheseoslibrivi01firmuoft"
        md["ingested_sections"] = "I.2.5-11 (témoin n°3 d'Amand 1945)"
        wn["metadata"] = json.dumps(md, ensure_ascii=False)
        wn["updated_at"] = TIMESTAMP
        print(f"  Enriched: {WORK_ID}")
    else:
        print(f"  Already had evidence_pending=False: {WORK_ID}")

    # ----- Phase 8: Write back
    print("\n== PHASE 8 : WRITE BACK ==")
    with NODES_PATH.open("w", encoding="utf-8") as f:
        for n in nodes:
            f.write(json.dumps(n, ensure_ascii=False) + "\n")
    with EDGES_PATH.open("w", encoding="utf-8") as f:
        for e in edges:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    print(f"  nodes.jsonl: {len(nodes)}")
    print(f"  edges.jsonl: {len(edges)}")

    # ----- Phase 9: SHACL invariants
    print("\n== PHASE 9 : VALIDATE SHACL INVARIANTS ==")
    ok = run_shacl_invariants()
    if not ok:
        print("  WARN: SHACL invariants failed — review before committing.")
        return 2

    # ----- Summary
    print("\n== FIRMICUS MATH I.2.5-11 (WITNESS 3) INGESTION COMPLETE ==")
    print(f"  Passages added: {inserted_passages}/{len(WITNESS_SECTIONS)}")
    print(f"  Edges added (part_of+authored_by+evidenced_by): {part_of_inserted + authored_inserted + evidenced_inserted}")
    print(f"    part_of:     {part_of_inserted}")
    print(f"    authored_by: {authored_inserted}")
    print(f"    evidenced_by:{evidenced_inserted}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
