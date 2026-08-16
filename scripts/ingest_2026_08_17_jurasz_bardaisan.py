#!/usr/bin/env python3
"""Ingest Jurasz 2023 on Bardaisan's hermeneutics of Scripture.

Source
------
Izabela Jurasz, « Bardesane et l'herméneutique des Écritures : l'étude des
nouveaux témoignages », *Vigiliae Christianae* 77 (2023) 69-95, Brill.
DOI 10.1163/15700720-bja10060.
Local copy: ~/Downloads/bardesane-et-lhermeneutique-des-ecritures-letude-des-pmv18gqm.pdf

Every claim below is attributed to the scholar who makes it, with the page it is
made on. Where the article reports a DISAGREEMENT it is modelled as two nodes,
not flattened into one: Jurasz accepts Eusebius of Emesa's attribution of the
Genesis exegesis to Bardaisan; ter Haar Romeny rejects it. The graph records
both and the ``critiques`` edge between them.

No Syriac, Greek, Armenian or Latin is generated. The one Greek phrase reused
here (ἕτερος καὶ ἕτερος) is quoted from p. 87 of the article, which itself quotes
ter Haar Romeny's edition, and it is stored as a quoted term inside an English
description, not as an ancient-text payload.

This script REFUSES to write unless ``scripts/check_ingestion_rules.py
--new-only`` passes on the delta it builds.

Usage:
    python3 scripts/ingest_2026_08_17_jurasz_bardaisan.py [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"
EDGES_PATH = ROOT / "data" / "kg" / "edges.jsonl"

NOW = "2026-08-17 00:00:00+00:00"
DOI = "10.1163/15700720-bja10060"
SRC = f"doi:{DOI} (Jurasz, Vigiliae Christianae 77 [2023] 69-95)"
PROV = {"source": SRC, "ingested_at": NOW, "ingest_script": Path(__file__).name}

# Already in the graph — attach, never re-create (rule R2).
BARDAISAN = "person_bardesanes_the_syrian_3r8s0u76"
JURASZ = "scholar_jurasz_i"
LLP = "work_bardesanes_liber_legum_regionum"
ORIGEN = "person_origen_alexandria_185_254ce_s9t0u1v2"


def node(nid, typ, label, desc, period, md=None, school=None):
    return {
        "alternative_names": "[]",
        "created_at": NOW,
        "description": desc,
        "id": nid,
        "label": label,
        "metadata": {**(md or {}), "provenance": PROV},
        "node_id": nid,
        "period": period,
        "role": None,
        "school": school,
        "type": typ,
        "updated_at": NOW,
    }


def edge(src, rel, tgt, why, weight=0.9):
    return {
        "created_at": NOW,
        "edge_id": f"jurasz2023-{src}-{rel}-{tgt}",
        "metadata": {"provenance": PROV, "note": why},
        "relation": rel,
        "source": src,
        "source_id": src,
        "target": tgt,
        "target_id": tgt,
        "weight": weight,
    }


def build() -> tuple[list[dict], list[dict]]:
    N: list[dict] = []
    E: list[dict] = []

    # ---------------- persons: ancient ----------------------------------
    N.append(node(
        "person_ephrem_syrus_d373", "person", "Ephrem the Syrian",
        "Ephrem the Syrian (c. 306-373), deacon and hymnographer of Nisibis and Edessa. His "
        "Memrā against Bardaisan and the Hymns against Heresies are the principal Syriac "
        "witnesses to Bardaisan's teaching and to the bardesanite reading of Scripture; Jurasz "
        "treats strophes 74 and 80-83 of the Memrā as the fullest surviving report of a "
        "bardesanite exegesis (of John 8:51-52).",
        "Late Antiquity",
        {"birth_date": "c. 306 CE", "death_date": "373 CE", "language": "syr",
         "cited_pages": "71-72, 78-86"}))

    N.append(node(
        "person_eusebius_emesa_300_360", "person", "Eusebius of Emesa",
        "Eusebius of Emesa (c. 300-360), Syrian-born exegete writing in Greek, associated with the "
        "Antiochene tradition of literal interpretation. His Commentary on the Octateuch and Kings "
        "survives only in fragments, transmitted through the exegetical catenae, Procopius of Gaza "
        "and a sixth-century Armenian translation. Fragment 22 of the Commentary on Genesis "
        "preserves a report of Bardaisan's reading of the two divine commands to Noah.",
        "Late Antiquity",
        {"birth_date": "c. 300 CE", "death_date": "c. 360 CE", "language": "grc",
         "cited_pages": "86-90"}))

    # ---------------- persons: modern scholars ---------------------------
    N.append(node(
        "scholar_ter_haar_romeny_rb", "person", "Robert B. ter Haar Romeny",
        "Syriac and biblical scholar; editor of the sixty-one surviving fragments of Eusebius of "
        "Emesa's Commentary on Genesis in *A Syrian in Greek Dress* (TEG 6, Peeters, 1997). He "
        "holds that Eusebius' ascription of the two-speakers reading of Genesis to Bardaisan is "
        "mistaken.",
        "Contemporary", {"language": "eng"}))

    N.append(node(
        "scholar_camplani_a", "person", "Alberto Camplani",
        "Historian of Syriac and Egyptian Christianity (Sapienza, Rome). His « Bardaisan and the "
        "Bible » (2017) and « Rivisitando Bardesane » (1998) assembled the dossier of Bardaisan's "
        "biblical references on which Jurasz builds.",
        "Contemporary", {"language": "ita"}))

    # ---------------- ancient works --------------------------------------
    N.append(node(
        "work_ephrem_memra_contra_bardaisan", "work",
        "Ephrem the Syrian, Memrā against Bardaisan",
        "Verse homily (memrā) of Ephrem the Syrian against Bardaisan and his followers. Strophes "
        "74 and 80-83 summarise the bardesanite exegesis of John 8:51-52 ('if anyone keeps my word "
        "he will never see death'), read as promising the resurrection of souls rather than of "
        "bodies. Jurasz treats it as the one Syriac text that reports a bardesanite exegetical "
        "method rather than merely a doctrine.",
        "Late Antiquity",
        {"author": "Ephrem the Syrian", "language": "syr", "cited_pages": "72, 78-86"}))

    N.append(node(
        "work_eusebius_emesa_commentary_genesis", "work",
        "Eusebius of Emesa, Commentary on Genesis (fragments)",
        "Lost commentary, the first part of Eusebius of Emesa's Commentary on the Octateuch and "
        "Kings, surviving in sixty-one fragments edited by ter Haar Romeny (1997). Fragment 22, "
        "transmitted in Greek, Armenian and Syriac, discusses the discrepancy between the divine "
        "commands to Noah at Genesis 6:19-20 and 7:2-3 and reports Bardaisan's explanation of it.",
        "Late Antiquity",
        {"author": "Eusebius of Emesa", "language": "grc",
         "edition": "R.B. ter Haar Romeny, A Syrian in Greek Dress, TEG 6, Leuven: Peeters, 1997, 265-271",
         "cited_pages": "86-90"}))

    N.append(node(
        "work_adamantius_dialogue_true_faith", "work",
        "Dialogue on the True Faith in God (Adamantius, Ps.-Origen)",
        "Greek dialogue transmitted under the name of Origen (Adamantius), in which orthodox "
        "speakers debate Marcionites, Valentinians and a bardesanite named Marinus. Jurasz reads "
        "Marinus' interventions as evidence for a fourth-century, Platonising and body-hostile "
        "development of Bardaisan's teaching. Books IV-V draw extensively on Methodius, including "
        "his On Free Will.",
        "Late Antiquity",
        {"author": "Pseudo-Origen (Adamantius)", "language": "grc", "cited_pages": "91-95"}))

    # ---------------- modern publications --------------------------------
    N.append(node(
        "pub_jurasz_2023_bardesane_hermeneutique", "publication",
        "Jurasz 2023 — Bardesane et l'herméneutique des Écritures : l'étude des nouveaux témoignages",
        "Izabela Jurasz, « Bardesane et l'herméneutique des Écritures : l'étude des nouveaux "
        "témoignages », Vigiliae Christianae 77 (2023) 69-95. Widens the dossier on Bardaisan's use "
        "of Scripture beyond the Syriac material by adding the testimony of Eusebius of Emesa "
        "(preserved in Armenian, Greek and Syriac) and the speeches of the bardesanite Marinus in "
        "the Adamantius Dialogue, and argues that Bardaisan and his followers practised literal "
        "exegesis in the Antiochene tradition.",
        "Contemporary",
        {"author": "Izabela Jurasz", "author_id": JURASZ, "year": 2023, "type": "article",
         "journal": "Vigiliae Christianae", "volume": "77", "page_range": "69-95",
         "publisher": "Brill", "doi": DOI,
         "orcid": "0000-0002-3224-6705",
         "note": "Brill copyright line reads 2022 (online-first); the issue is VC 77 (2023).",
         "verified_reference": "Izabela Jurasz, « Bardesane et l'herméneutique des Écritures : "
                               "l'étude des nouveaux témoignages », Vigiliae Christianae 77 (2023) "
                               "69-95, doi:10.1163/15700720-bja10060"}))

    N.append(node(
        "pub_ter_haar_romeny_1997_syrian_greek_dress", "publication",
        "ter Haar Romeny 1997 — A Syrian in Greek Dress",
        "R.B. ter Haar Romeny, A Syrian in Greek Dress. The Use of Greek, Hebrew, and Syriac "
        "Biblical Texts in Eusebius of Emesa's Commentary on Genesis, Traditio Exegetica Graeca 6, "
        "Leuven: Peeters, 1997. Edition of the sixty-one Genesis fragments; Fragment 22 and its "
        "discussion at 265-271 are the basis of Jurasz's new dossier.",
        "Contemporary",
        {"author": "Robert B. ter Haar Romeny", "author_id": "scholar_ter_haar_romeny_rb",
         "year": 1997, "type": "monograph", "series": "Traditio Exegetica Graeca 6",
         "publisher": "Peeters", "place": "Leuven", "page_range": "265-271",
         "verified_reference": "R.B. ter Haar Romeny, A Syrian in Greek Dress, TEG 6, Leuven: "
                               "Peeters, 1997 (cited by Jurasz 2023, 86-90 nn. 54-59)"}))

    N.append(node(
        "pub_camplani_2017_bardaisan_and_the_bible", "publication",
        "Camplani 2017 — Bardaisan and the Bible",
        "Alberto Camplani, « Bardaisan and the Bible », in A. Van den Kerchove & L.G. Soares "
        "Santoprete (eds.), Gnose et manichéisme : entre les oasis d'Égypte et la route de la soie. "
        "Hommage à Jean-Daniel Dubois, BEHE 176, Turnhout: Brepols, 2017, 699-715.",
        "Contemporary",
        {"author": "Alberto Camplani", "author_id": "scholar_camplani_a", "year": 2017,
         "type": "chapter", "series": "BEHE 176", "publisher": "Brepols", "place": "Turnhout",
         "page_range": "699-715",
         "verified_reference": "Alberto Camplani, « Bardaisan and the Bible », in Gnose et "
                               "manichéisme, BEHE 176, Turnhout: Brepols, 2017, 699-715 (cited by "
                               "Jurasz 2023, 70-72 nn. 1-8)"}))

    # ---------------- scholarly arguments --------------------------------
    args = [
        ("scholarly_argument_jurasz_bardaisan_literal_exegesis_antiochene",
         "Jurasz: Bardaisan and his followers practised literal exegesis in the Antiochene tradition",
         "Jurasz's central thesis. Taken together, the bardesanite exegesis of John 8:51-52 reported "
         "by Ephrem, the reading of the two divine commands to Noah reported by Eusebius of Emesa, "
         "and Marinus' appeal to faith and Scripture as the only sources of Christian doctrine in "
         "the Adamantius Dialogue all show the same procedure: the text is read literally, and "
         "doctrinal conclusions are drawn from the letter rather than from allegory. Jurasz places "
         "this in the tradition of the school of Antioch.",
         "69-70, 94-95"),
        ("scholarly_argument_jurasz_eusebius_emesa_fr22_new_testimony",
         "Jurasz: Eusebius of Emesa, Fragment 22 is an unstudied testimony to bardesanite exegesis",
         "Fragment 22 of Eusebius of Emesa's Commentary on Genesis reports that Bardaisan explained "
         "the discrepancy between the command to take pairs of every animal (Gen 6:19-20) and the "
         "command to take seven pairs of clean animals (Gen 7:2-3) by positing two different divine "
         "speakers, inferred from the different names given to God in the Hebrew text. The Greek "
         "fragment has 'one (heteros) ... and the other (heteros)'; the Armenian version expands "
         "the point with a list of divine names (El, Yah, Adonai, Elohim). Jurasz observes that "
         "this testimony had never been examined in the scholarship on Bardaisan.",
         "86-90"),
        ("scholarly_argument_jurasz_marinus_platonising_bardesanism",
         "Jurasz: Marinus in the Adamantius Dialogue attests a later, Platonising bardesanism",
         "The bardesanite Marinus in the Adamantius Dialogue represents a later and possibly local "
         "version of Bardaisan's teaching: Platonising and hostile to the body, holding the "
         "resurrection of souls and not of bodies. Jurasz argues there is a strong probability that "
         "Ephrem knew of this development, which would explain the length of his explanations of "
         "the body and the incarnation in the Memrā. She also notes that one exegesis attributed to "
         "Marinus at Dialogue V, 21 is falsely bardesanite, which shows how difficult his speeches "
         "are to use as evidence.",
         "91-95"),
        ("scholarly_argument_ter_haar_romeny_bardaisan_attribution_erroneous",
         "ter Haar Romeny: Eusebius' ascription of the two-speakers reading to Bardaisan is mistaken",
         "Against the attribution, ter Haar Romeny argues that Bardaisan speaks explicitly of a "
         "single God in the Book of the Laws of the Countries (LLP 1-2), and that he is reported as "
         "an anti-Marcionite polemicist, which presupposes opposition to a dualist theology. He "
         "looks for another source for the exegesis in the Apocryphon of John and Ophite teaching "
         "(Irenaeus, Haer. I, 30, 4-11), where archons bear the divine names of the Jewish "
         "Scriptures — though there the number of such powers is not limited to two. He proposes "
         "that the Armenian list of Hebrew divine names is Eusebius' own display of learning.",
         "87, 89 nn. 58-59"),
        ("scholarly_argument_camplani_bardaisan_biblical_references_method_open",
         "Camplani: Bardaisan's biblical references are numerous but his exegetical method is barely documented",
         "Camplani assembled a surprisingly long list of biblical texts known to Bardaisan from the "
         "Syriac testimonies — Genesis allusions in Theodore bar Konai, the image of God in the Book "
         "of the Laws of the Countries, the Ancient of Days of Daniel 7:9 in Philoxenus of Mabbug, "
         "citations of Matthew 27:47 / Psalm 22:2 and John 8:51-52, the parable of the tares of "
         "Matthew 13:24-43, Adam and Christ in Romans 5:18-19 and 1 Corinthians 15:22-23 — and "
         "concluded that his biblical text stood close to the old Syriac gospel version and the "
         "Diatessaron. He also observed that these testimonies rarely indicate the exegetical method "
         "itself, which is the gap Jurasz sets out to fill.",
         "70-72"),
    ]
    meta_for = {
        "scholarly_argument_jurasz_bardaisan_literal_exegesis_antiochene": (JURASZ, "pub_jurasz_2023_bardesane_hermeneutique"),
        "scholarly_argument_jurasz_eusebius_emesa_fr22_new_testimony": (JURASZ, "pub_jurasz_2023_bardesane_hermeneutique"),
        "scholarly_argument_jurasz_marinus_platonising_bardesanism": (JURASZ, "pub_jurasz_2023_bardesane_hermeneutique"),
        "scholarly_argument_ter_haar_romeny_bardaisan_attribution_erroneous": ("scholar_ter_haar_romeny_rb", "pub_ter_haar_romeny_1997_syrian_greek_dress"),
        "scholarly_argument_camplani_bardaisan_biblical_references_method_open": ("scholar_camplani_a", "pub_camplani_2017_bardaisan_and_the_bible"),
    }
    for nid_, label, desc, pages in args:
        scholar, work = meta_for[nid_]
        N.append(node(nid_, "argument", label, desc, "Contemporary",
                      {"argument_type": "modern_scholarly_position",
                       "scholar_id": scholar, "scholarly_work_id": work,
                       "page_range": pages, "confidence": 0.95,
                       "citation_verified": True,
                       "verified_reference": f"Jurasz 2023, {pages}" if scholar == JURASZ
                                             else f"cited and discussed in Jurasz 2023, {pages}"}))

    # ---------------- edges ----------------------------------------------
    E += [
        edge("pub_jurasz_2023_bardesane_hermeneutique", "authored_by", JURASZ, "article byline", 1.0),
        edge("pub_ter_haar_romeny_1997_syrian_greek_dress", "authored_by", "scholar_ter_haar_romeny_rb", "monograph byline", 1.0),
        edge("pub_camplani_2017_bardaisan_and_the_bible", "authored_by", "scholar_camplani_a", "chapter byline", 1.0),
        edge("work_ephrem_memra_contra_bardaisan", "authored_by", "person_ephrem_syrus_d373", "author of the memrā", 1.0),
        edge("work_eusebius_emesa_commentary_genesis", "authored_by", "person_eusebius_emesa_300_360", "author of the commentary", 1.0),
    ]
    for a, _l, _d, _p in args:
        scholar, work = meta_for[a]
        E.append(edge(a, "created_by", scholar, "claim advanced by this scholar", 1.0))
        E.append(edge(a, "advanced_in", work, "claim published here", 1.0))
        E.append(edge(a, "discusses", BARDAISAN, "the subject of the claim", 0.95))

    E += [
        # The disagreement, kept as a disagreement.
        edge("scholarly_argument_jurasz_eusebius_emesa_fr22_new_testimony", "critiques",
             "scholarly_argument_ter_haar_romeny_bardaisan_attribution_erroneous",
             "Jurasz reopens the attribution ter Haar Romeny had rejected (Jurasz 2023, 87-90)", 0.95),
        edge("scholarly_argument_ter_haar_romeny_bardaisan_attribution_erroneous", "cites_primary_source",
             LLP, "LLP 1-2 is Romeny's evidence that Bardaisan taught one God", 0.95),
        edge("scholarly_argument_jurasz_bardaisan_literal_exegesis_antiochene", "extends",
             "scholarly_argument_camplani_bardaisan_biblical_references_method_open",
             "Jurasz fills the methodological gap Camplani identified", 0.9),
        # Ancient witnesses to Bardaisan.
        edge("work_ephrem_memra_contra_bardaisan", "critiques", BARDAISAN,
             "the memrā is directed against Bardaisan", 1.0),
        edge("work_eusebius_emesa_commentary_genesis", "discusses", BARDAISAN,
             "Fragment 22 reports Bardaisan's reading of the commands to Noah", 0.9),
        edge("work_adamantius_dialogue_true_faith", "discusses", BARDAISAN,
             "the bardesanite Marinus speaks for Bardaisan's school in the dialogue", 0.85),
        edge("scholarly_argument_jurasz_marinus_platonising_bardesanism", "cites_primary_source",
             "work_adamantius_dialogue_true_faith", "Dialogue IV-V, esp. V, 16. 21", 0.95),
        edge("scholarly_argument_jurasz_eusebius_emesa_fr22_new_testimony", "cites_primary_source",
             "work_eusebius_emesa_commentary_genesis", "Fragment 22 (ed. ter Haar Romeny, 265-266)", 0.95),
        edge("scholarly_argument_camplani_bardaisan_biblical_references_method_open", "cites_primary_source",
             "work_ephrem_memra_contra_bardaisan", "Memrā 1-2, 41-42, 74, 80-83", 0.9),
        edge("person_ephrem_syrus_d373", "critiques", BARDAISAN, "Ephrem's lifelong polemical target", 1.0),
        # Pseudo-Origen: the dialogue circulates under Origen's name.
        edge("work_adamantius_dialogue_true_faith", "discusses", ORIGEN,
             "transmitted under Origen's name (Adamantius); the ascription is not accepted", 0.7),
    ]
    return N, E


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    new_nodes, new_edges = build()

    # --- pre-flight: the ingestion rules must pass on the delta ------------
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as fh:
        json.dump({"nodes": new_nodes, "edges": new_edges}, fh, ensure_ascii=False)
        delta = fh.name
    print(f"proposing {len(new_nodes)} nodes / {len(new_edges)} edges — gating with check_ingestion_rules\n")
    rc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_ingestion_rules.py"), "--new-only", delta],
        cwd=ROOT,
    ).returncode
    if rc != 0:
        print("\nREFUSED: the delta violates a BLOCK rule. Nothing written.")
        return 1

    if args.dry_run:
        print("\n--dry-run: gate passed, nothing written")
        return 0

    with NODES_PATH.open("a", encoding="utf-8") as fh:
        for n in new_nodes:
            fh.write(json.dumps(n, ensure_ascii=False) + "\n")
    with EDGES_PATH.open("a", encoding="utf-8") as fh:
        for e in new_edges:
            fh.write(json.dumps(e, ensure_ascii=False) + "\n")
    print(f"\nappended {len(new_nodes)} nodes and {len(new_edges)} edges")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
