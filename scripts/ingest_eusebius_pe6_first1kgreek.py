"""Ingestion section-grained de la Praeparatio Evangelica VI.6 d'Eusèbe de Césarée.

Source TEI : OpenGreekAndLatin/First1KGreek (`tlg2018.tlg001.1st1K-grc1.xml`)
édition Dindorf re-encodée par Digital Divide Data / Univ. Leipzig.

Pourquoi ? Le KG contenait jusqu'ici 15 passages monolithiques (`passage_eusebius_praep_ev_book_*`),
un par livre, sans aucun grain pour ancrer le **témoin n°4 d'Amand 1945** (PE VI.6.4-21,
= Dindorf t. I p. 275 l. 28 — p. 279 l. 18). Et 15 edges `part_of` orphelins pointaient
depuis des `node_id` fantômes (`passage_basil_hex_*`, vestiges d'un clonage Basile→Eusèbe).

Ce script :
  1. Répare les 15 edges orphelins `part_of` (passage_basil_hex_* → passage_eusebius_praep_ev_book_*).
  2. Crée 74 nouveaux passages atomiques `passage_eusebius_praep_ev_6_6_N` (N=1..74)
     avec texte grec verbatim extrait du TEI.
  3. Flague le book_06 monolithique (`metadata.legacy_monolithic: true`,
     `metadata.superseded_by_sections: "6.6.1-74"`) — pas de suppression.
  4. Ancre les arguments-pivots Amand B1 (carnéadiens reconstruits) sur les sections VI.6.X
     pour le sous-ensemble du témoin n°4 (sections 4-21) via `evidenced_by`, avec confidences
     calibrées d'après l'attestation lexicale dans le grec lui-même.

Pattern de bypass Scaife (cassé en TLS) réutilisable : fetch TEI XML brut depuis
https://raw.githubusercontent.com/OpenGreekAndLatin/First1KGreek/master/data/{author_urn}/{work_urn}/...

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

TIMESTAMP = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f+00:00")
CREATED_BY = "eusebius_pe6_ingestion_2026-05-15"
SOURCE_TAG = "OpenGreekAndLatin/First1KGreek (TEI bypass for dead Scaife)"

# Witness 4 range per Amand 1945 (Dindorf p. 275 l. 28 — p. 279 l. 18)
AMAND_WITNESS_4_RANGE = set(range(4, 22))  # VI.6.4 to VI.6.21 inclusive

# Approximate Dindorf pagination crosswalk for the witness-4 sections.
# Amand cites Dindorf t. I p. 275 l. 28 — p. 279 l. 18 for VI.6.4-21 (≈ 18 sections / ≈ 4.5 pages).
# We approximate each section's page (3-4 sections/page in Dindorf ~25-line columns).
# Flagged `unverified` since not directly visually verified on Dindorf PDF.
DINDORF_PAGE_BY_SECTION = {
    4: "275", 5: "275", 6: "275", 7: "275",
    8: "276", 9: "276", 10: "276", 11: "276",
    12: "277", 13: "277", 14: "277", 15: "277",
    16: "278", 17: "278", 18: "278",
    19: "278-279", 20: "279", 21: "279",
}


# -----------------------------------------------------------------------------
# Amand-B1 pivot → section mapping (Greek-attested only)
# -----------------------------------------------------------------------------
#
# Rule: an `evidenced_by` edge is created ONLY when the Greek text of the section
# verifiably attests the lexical / argumentative marker of the pivot.
# Confidence calibration:
#   0.85 = pivot marker explicit + structurally central
#   0.75 = pivot marker explicit but secondary
#   0.65 = pivot inferred from immediate context + Amand-asserted
#
# Pivots Amand B1 :
#   I    = argument_carneadean_general_theme_amand1945     (moral collapse / κακῶν δογμάτων / ὄλεθρον)
#   II   = argument_carneadean_legislation_amand1945       (laws/punishments → νόμοι, ποιναί, κολάσεις)
#   III  = argument_carneadean_virtue_vice_amand1945       (praise/blame, ἀρετή/κακία/ἔπαινος/ψόγος)
#   IV   = argument_carneadean_incentives_amand1945        (νουθεσία/διδασκαλία/προτροπή/παραίνεσις)
#   V    = argument_carneadean_action_futility_amand1945   (ἀργία/ῥᾳθυμία/φιλοπονία)
#   VI   = argument_carneadean_piety_amand1945             (εὐσέβεια, εὐχή, θεοί)
#   self-refutation = argument_carneadean_stoic_pragmatic_self_refutation_amand1945
#                     (Alex §18 + Eus PE VI.6.16-17 — explicitly named in B1 description)

AMAND_B1_PIVOT_IDS = {
    "I": "argument_carneadean_general_theme_amand1945",
    "II": "argument_carneadean_legislation_amand1945",
    "III": "argument_carneadean_virtue_vice_amand1945",
    "IV": "argument_carneadean_incentives_amand1945",
    "V": "argument_carneadean_action_futility_amand1945",
    "VI": "argument_carneadean_piety_amand1945",
    "SELF_REF": "argument_carneadean_stoic_pragmatic_self_refutation_amand1945",
}

# Mapping based on direct Greek lexical verification (see survey output).
# Pivot → list of (section_n, confidence, justification_marker).
PIVOT_TO_SECTIONS: dict[str, list[tuple[int, float, str]]] = {
    "I": [
        (4, 0.85, "κακῶν δογμάτων ὄλεθρον — frame line of the whole tirade"),
        (7, 0.80, "εἰς οἷον κακῶν δογμάτων βυθὸν — repetition of frame"),
    ],
    "II": [
        (18, 0.85, "νόμους ἀνατρέποι ἂν οὗτος ὁ λόγος — explicit subversion of νόμοι"),
    ],
    "III": [
        (5, 0.75, "ἀναθετέον τὰς προθυμίας τοῖς ἄστροις — virtue/vice attribution displaced"),
        (6, 0.85, "οὐ προσήκει καταμέμφεσθαι ... οὐδὲ τοὺς σπουδαίους θαυμάζειν — praise/blame collapse"),
        (16, 0.70, "ἐπαινεῖν τοὺς κατορθοῦντας + ἐπιτιμᾶν — virtue/blame in self-refutation context"),
    ],
    "IV": [
        (12, 0.85, "νουθετοῦντι καὶ διδάσκοντι — futility of correction"),
        (13, 0.85, "τί με νουθετεῖς — first person voicing of incentive futility"),
        (14, 0.75, "ἄνευ τῆς σῆς διδασκαλίας — instruction declared otiose"),
        (15, 0.80, "παραινεῖν καὶ διδάσκειν — Stoic teacher's own act drawn into the fate"),
    ],
    "V": [
        (9, 0.85, "πῶς οὐκ ἄν τις ἐθελήσειε τὸ ῥᾷον αἱρεῖσθαι — laziness preferred to effort"),
        (10, 0.80, "τί με χρὴ παρέχειν ἐμαυτῷ πράγματα — folk-Stoic quietism"),
        (16, 0.85, "ἀπορρᾳθυμῶν ... μηδαμῶς φιλοπονήσω — explicit ἀργία motif"),
    ],
    "VI": [
        (19, 0.85, "τὴν πρὸς τὸ θεῖον εὐσέβειαν ἀνατρέποι — piety overturned"),
    ],
    "SELF_REF": [
        (16, 0.85, "Stoic teacher's pragmatic self-refutation — explicitly named in Amand B1 rapport"),
        (17, 0.75, "continuation of self-refutation argument (αὐθεκούσιον vs εἱμαρμένη)"),
    ],
}


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
    """Extract verbatim Greek text from `body/div[edition]/div[book=N]/div[chap=N]/div[sec=N]`."""
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
    pid = f"passage_eusebius_praep_ev_6_6_{sec_n}"
    is_witness4 = sec_n in AMAND_WITNESS_4_RANGE
    metadata: dict = {
        "attestation_type": "direct",
        "author": "Eusebius of Caesarea",
        "canonical_ref": f"VI.6.{sec_n}",
        "char_length": len(greek_text),
        "word_count": len(greek_text.split()),
        "cts_urn": f"{CTS_URN_BASE}:6.6.{sec_n}",
        "language": "grc",
        "passage_role": "original",
        "school": "Patristic",
        "work_canonical_id": "tlg2018.tlg001.1st1K-grc1",
        "work_title": "Praeparatio Evangelica",
        "book": 6,
        "chapter": 6,
        "section": sec_n,
        "edition": "Dindorf t. I (Leipzig 1867), re-encoded TEI by Digital Divide Data / Univ. Leipzig",
        "source_tei": "OpenGreekAndLatin/First1KGreek tlg2018.tlg001.1st1K-grc1.xml",
        "source_tei_url": TEI_URL,
        "source": SOURCE_TAG,
        "created_by": CREATED_BY,
        "contains_greek_to_verify": False,  # canonical TEI source
        "period": "Late Antiquity",
    }
    if is_witness4:
        metadata["is_amand_witness_4"] = True
        metadata["amand_witness_label"] = (
            "Témoin n°4 (Eusèbe PE VI.6.4-21 = Dindorf t. I p. 275 l. 28 — p. 279 l. 18)"
        )
        metadata["dindorf_pagination"] = DINDORF_PAGE_BY_SECTION.get(sec_n)
        metadata["dindorf_pagination_unverified"] = True
    return {
        "id": pid,
        "node_id": pid,
        "type": "passage",
        "label": f"Eusebius, Praeparatio Evangelica, VI.6.{sec_n}",
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
    edge_by_id = {e.get("edge_id", e.get("id", "")): i for i, e in enumerate(edges)}

    # Phase 0: Verify prerequisites
    if WORK_ID not in node_by_id:
        print(f"  FATAL: work node {WORK_ID} missing — abort")
        return 1
    if PERSON_ID not in node_by_id:
        print(f"  FATAL: person node {PERSON_ID} missing — abort")
        return 1

    # Phase 1: Fix orphan book→work part_of edges
    print("\n== PHASE 1 : REPAIR ORPHAN PART_OF EDGES ==")
    repaired = 0
    book_id_pattern_legacy = "passage_basil_hex_"
    book_id_pattern_real = "passage_eusebius_praep_ev_book_"
    for e in edges:
        src = e.get("source_id") or e.get("source")
        tgt = e.get("target_id") or e.get("target")
        if tgt == WORK_ID and src.startswith(book_id_pattern_legacy) and e.get("relation") == "part_of":
            # Parse book number from suffix
            try:
                bn = int(src.removeprefix(book_id_pattern_legacy))
            except ValueError:
                continue
            new_src = f"{book_id_pattern_real}{bn:02d}"
            if new_src not in node_by_id:
                print(f"  SKIP (new src missing): {new_src}")
                continue
            e["source"] = new_src
            e["source_id"] = new_src
            existing_md = json.loads(e.get("metadata") or "{}")
            existing_md["repaired_by"] = CREATED_BY
            existing_md["repaired_at"] = TIMESTAMP
            existing_md["repair_note"] = (
                "Source id was a stale node_id (passage_basil_hex_*), node_id residual of a clone op."
            )
            e["metadata"] = json.dumps(existing_md, ensure_ascii=False)
            repaired += 1
    print(f"  Edges repaired: {repaired}")

    # Phase 2: Flag book_06 as legacy monolithic
    print("\n== PHASE 2 : FLAG BOOK_06 AS LEGACY MONOLITHIC ==")
    book06_id = "passage_eusebius_praep_ev_book_06"
    if book06_id in node_by_id:
        bn = nodes[node_by_id[book06_id]]
        md_raw = bn.get("metadata") or "{}"
        md = json.loads(md_raw) if isinstance(md_raw, str) else md_raw
        if not md.get("legacy_monolithic"):
            md["legacy_monolithic"] = True
            md["superseded_by_sections"] = "passage_eusebius_praep_ev_6_6_1 .. passage_eusebius_praep_ev_6_6_74"
            md["legacy_flagged_by"] = CREATED_BY
            md["legacy_flagged_at"] = TIMESTAMP
            bn["metadata"] = json.dumps(md, ensure_ascii=False)
            bn["updated_at"] = TIMESTAMP
            print(f"  Flagged: {book06_id}")
        else:
            print(f"  Already flagged: {book06_id}")
    else:
        print(f"  Missing: {book06_id} — skip flag")

    # Phase 3: Parse TEI + insert section passages
    print("\n== PHASE 3 : INGEST SECTION-GRAINED PASSAGES VI.6.1-74 ==")
    tei_path = ensure_tei_local()
    tree = etree.parse(str(tei_path))
    root = tree.getroot()

    inserted = 0
    skipped_existing = 0
    missing_tei = 0
    new_passage_ids: list[str] = []
    for sec_n in range(1, 75):
        pid = f"passage_eusebius_praep_ev_6_6_{sec_n}"
        if pid in node_by_id:
            skipped_existing += 1
            new_passage_ids.append(pid)
            continue
        greek = extract_section_greek(root, 6, 6, sec_n)
        if not greek:
            print(f"  MISSING in TEI: VI.6.{sec_n}")
            missing_tei += 1
            continue
        node = build_passage_node(sec_n, greek)
        nodes.append(node)
        node_by_id[pid] = len(nodes) - 1
        new_passage_ids.append(pid)
        inserted += 1
    print(f"  Inserted: {inserted} ; skipped-existing: {skipped_existing} ; missing-TEI: {missing_tei}")

    # Phase 4: Insert part_of edges (passage → work) for the new sections
    print("\n== PHASE 4 : INSERT PART_OF EDGES (SECTION → WORK) ==")
    part_of_inserted = 0
    # We'll de-duplicate by (src, rel, tgt) tuple
    existing_part_of = set()
    for e in edges:
        if e.get("relation") == "part_of":
            existing_part_of.add((e.get("source_id") or e.get("source"), e.get("target_id") or e.get("target")))
    for pid in new_passage_ids:
        if (pid, WORK_ID) in existing_part_of:
            continue
        edge = build_edge(pid, WORK_ID, "part_of", {"auto_generated": True})
        edges.append(edge)
        edge_by_id[edge["edge_id"]] = len(edges) - 1
        existing_part_of.add((pid, WORK_ID))
        part_of_inserted += 1
    print(f"  part_of inserted: {part_of_inserted}")

    # Phase 5: Insert authored_by edges (passage → person)
    print("\n== PHASE 5 : INSERT AUTHORED_BY EDGES (SECTION → PERSON) ==")
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
        edge_by_id[edge["edge_id"]] = len(edges) - 1
        existing_authored.add((pid, PERSON_ID))
        authored_inserted += 1
    print(f"  authored_by inserted: {authored_inserted}")

    # Phase 6: Insert evidenced_by edges (Amand B1 pivots → sections)
    print("\n== PHASE 6 : INSERT EVIDENCED_BY EDGES (AMAND B1 PIVOTS → PE VI.6.X) ==")
    evidenced_inserted = 0
    evidenced_skipped_existing = 0
    evidenced_missing_node = 0
    breakdown: dict[str, int] = {}

    existing_ev = set()
    for e in edges:
        if e.get("relation") == "evidenced_by":
            existing_ev.add((e.get("source_id") or e.get("source"), e.get("target_id") or e.get("target")))

    for pivot_key, mappings in PIVOT_TO_SECTIONS.items():
        arg_id = AMAND_B1_PIVOT_IDS[pivot_key]
        if arg_id not in node_by_id:
            print(f"  WARN: pivot node missing: {arg_id} ({pivot_key})")
            evidenced_missing_node += len(mappings)
            continue
        breakdown[pivot_key] = 0
        for sec_n, confidence, justif in mappings:
            tgt = f"passage_eusebius_praep_ev_6_6_{sec_n}"
            if tgt not in node_by_id:
                print(f"  SKIP (tgt missing): {tgt}")
                continue
            if (arg_id, tgt) in existing_ev:
                evidenced_skipped_existing += 1
                continue
            edge = build_edge(
                arg_id, tgt, "evidenced_by",
                {
                    "confidence": confidence,
                    "discovery_method": "greek_lexical_verification_amand_b1_mapping",
                    "amand_witness": 4,
                    "amand_pivot": pivot_key,
                    "justification": justif,
                },
            )
            edges.append(edge)
            edge_by_id[edge["edge_id"]] = len(edges) - 1
            existing_ev.add((arg_id, tgt))
            evidenced_inserted += 1
            breakdown[pivot_key] += 1
    print(f"  evidenced_by inserted: {evidenced_inserted} ; skipped-existing: {evidenced_skipped_existing} ; missing-pivot-node: {evidenced_missing_node}")
    print("  Breakdown by pivot:")
    for pk, ct in breakdown.items():
        print(f"    {pk} ({AMAND_B1_PIVOT_IDS[pk]}): {ct} edges")

    # Phase 7: Enrich work node with source_tei
    print("\n== PHASE 7 : ENRICH WORK NODE METADATA WITH SOURCE_TEI ==")
    wn = nodes[node_by_id[WORK_ID]]
    md_raw = wn.get("metadata") or "{}"
    md = json.loads(md_raw) if isinstance(md_raw, str) else md_raw
    if "source_tei" not in md:
        md["source_tei"] = "OpenGreekAndLatin/First1KGreek tlg2018.tlg001.1st1K-grc1.xml"
        md["source_tei_url"] = TEI_URL
        md["source_tei_edition"] = "Dindorf t. I-IV (Leipzig 1867), re-encoded TEI by Digital Divide Data / Univ. Leipzig"
        md["enriched_by"] = CREATED_BY
        md["enriched_at"] = TIMESTAMP
        wn["metadata"] = json.dumps(md, ensure_ascii=False)
        wn["updated_at"] = TIMESTAMP
        print(f"  Enriched: {WORK_ID}")
    else:
        print(f"  Already has source_tei: {WORK_ID}")

    # Phase 8: Write back
    print("\n== PHASE 8 : WRITE BACK ==")
    with NODES_PATH.open("w") as f:
        for n in nodes:
            f.write(json.dumps(n, ensure_ascii=False) + "\n")
    with EDGES_PATH.open("w") as f:
        for ed in edges:
            f.write(json.dumps(ed, ensure_ascii=False) + "\n")
    print(f"  nodes.jsonl: {len(nodes)}")
    print(f"  edges.jsonl: {len(edges)}")
    print("\n== EUSEBIUS PE VI.6 INGESTION COMPLETE ==")
    return 0


if __name__ == "__main__":
    sys.exit(main())
