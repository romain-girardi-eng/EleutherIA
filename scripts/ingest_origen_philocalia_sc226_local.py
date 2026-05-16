"""Ingestion section-grained de la Philocalie 23 d'Origène depuis SC 226 Junod (1976).

Source critique locale (BACKUP des scripts archive.org):
  [local-path] SHAL/02_Corpus/
    SC 226 - Origène, Philocalie 21-27 (Sur le libre arbitre).rtf

Édition: Éric Junod, *Origène. Philocalie 21-27 (Sur le libre arbitre)*, SC 226, Cerf 1976.
Grec critique + traduction française parallèle. Conversion RTF→TXT via macOS `textutil`.

Contexte scholarly:
  Amand 1945, p. 366 — Philocalia 23 ≈ PE VI.11 verbatim. Cette ingestion permet
  d'ancrer la dissertation antifataliste d'Origène (Comm. Gen. III, transmise par
  Basile et Grégoire de Nazianze c. 358/360) côté Origène, en parallèle des 83
  sections PE VI.11 déjà ingérées.

Structure SC 226:
  - Phil 23 contient 22 paragraphes (§§1-22) + 4 sous-titres (titulus ante §§1, 12, 14, 22)
  - Découpage Junod (§§ continus) différent du découpage Dindorf utilisé pour PE VI.11
    (sec §§1-83)
  - Alignment heuristique PE→Phil via opening words: 70/83 sections PE matchent verbatim

Pipeline:
  1. Parse RTF→TXT (déjà converti à /tmp/sc226_philocalia.txt)
  2. Découpe en blocs (titulus + paragraphes), sépare grec/français
  3. Crée 22 passages `passage_origen_philocalia_23_N` (N=1..22)
  4. Crée 4 passages titulus `passage_origen_philocalia_23_titulus_N` (N=1,12,14,22)
  5. Edges part_of (passage → work) + authored_by (passage → person)
  6. Edges evidenced_by depuis 6 arguments Origène-Amand vers les § Phil 23 appropriés
  7. Edges parallel_to: Phil 23 §M ↔ PE VI.11 sec.N pour 70 sections verbatim

Idempotent: déjà-faits skip. NE COMMIT PAS.
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

KG_ROOT = Path(__file__).resolve().parent.parent / "data" / "kg"
NODES_PATH = KG_ROOT / "nodes.jsonl"
EDGES_PATH = KG_ROOT / "edges.jsonl"

RTF_SOURCE = Path(
    "[local-path] SHAL/02_Corpus/"
    "SC 226 - Origène, Philocalie 21-27 (Sur le libre arbitre).rtf"
)
TXT_LOCAL = Path("/tmp/sc226_philocalia.txt")

WORK_ID = "work_origen_philocalia"
PERSON_ID = "person_origen_alexandria_185_254ce_s9t0u1v2"

TIMESTAMP = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f+00:00")
CREATED_BY = "origen_philocalia_23_sc226_ingestion_2026-05-16"
SOURCE_EDITION = "SC 226 (Junod 1976)"
SOURCE_TAG = "SC 226 Junod 1976 - RTF local corpus (Doctorat SHAL)"

# Arguments Origène-Amand à ancrer via evidenced_by
ARG_ANCHORS = [
    # (argument_id, list of phil 23 paragraph keys to anchor to)
    # antiastrology dissertation envelope: all of Phil 23
    (
        "argument_origen_witness_antiastrological_dissertation_envelope_amand1945",
        ["titulus_1", "1", "2", "3", "4", "5", "11"],
    ),
    # moral attack (not physical): praise/blame core = §1, §10
    (
        "argument_origen_witness_antiastrology_moral_attack_amand1945",
        ["1", "2", "10"],
    ),
    # problem 1 prescience: titulus §1 + §§1-11 (problem stated, then resolved via Comm. Celse §§12-13)
    (
        "argument_origen_witness_diss_problem1_prescience_amand1945",
        ["titulus_1", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"],
    ),
    # Argos Logos refutation via Judas/Oedipus prophecies = §§7-9 area
    (
        "argument_origen_witness_diss_argos_logos_refutation_amand1945",
        ["7", "8", "9"],
    ),
    # problem 2 signs not causes: titulus §14 + §§14-18
    (
        "argument_origen_witness_diss_problem2_signs_not_causes_amand1945",
        ["titulus_14", "14", "15", "16", "17", "18"],
    ),
    # problem 3 human ignorance: §§17-20
    (
        "argument_origen_witness_diss_problem3_human_ignorance_amand1945",
        ["17", "18", "19", "20"],
    ),
    # problem 4 angelic knowledge: §§20-21 (final response)
    (
        "argument_origen_witness_diss_problem4_angelic_knowledge_amand1945",
        ["20", "21"],
    ),
    # Pseudo-Clementine citation: §22 (titulus 22 + content)
    (
        "argument_origen_witness_diss_part3_pseudo_clementine_amand1945",
        ["titulus_22", "22"],
    ),
    # Carneadean transposition praise/blame: §1 (core: ἐφ' ἡμῖν / praise / blame)
    (
        "argument_origen_witness_carneades_transposition_praise_blame_amand1945",
        ["1", "2"],
    ),
    # Carneadean transposition theological consequences: §1 (Christ, Church economy)
    (
        "argument_origen_witness_carneades_transposition_theological_consequences_amand1945",
        ["1"],
    ),
    # Carneadean transposition God-as-evil: §2-3
    (
        "argument_origen_witness_carneades_transposition_god_as_evil_amand1945",
        ["2", "3"],
    ),
    # Carneadean transposition prayer useless: §3-4 (anti-Marcionite/Gnostic excursus)
    (
        "argument_origen_witness_carneades_transposition_prayer_useless_amand1945",
        ["3", "4"],
    ),
    # Gnostic excursus: §3
    (
        "argument_origen_witness_carneades_transposition_gnostic_excursus_amand1945",
        ["3"],
    ),
]

# -----------------------------------------------------------------------------
# Parser
# -----------------------------------------------------------------------------

GREEK_CHARS_RE = re.compile(r"[Ͱ-Ͽἀ-῿]")
CONTENT_RE = re.compile(r"^\s*\d+\s*\t\s*\t?(.+?)\s*$")
PAGE_MARKER_RE = re.compile(r"--- \d+ ---")
HEADER_RE = re.compile(r"^cap\.:\s*23,\s*(par\.:\s*(\d+)|titulus ante par\.:\s*(\d+))")
SENTINEL_RE = re.compile(r"^cap\.:\s*2[4-7]")


def ensure_txt_local() -> Path:
    """Convert RTF→TXT via textutil if not already done."""
    if TXT_LOCAL.exists() and TXT_LOCAL.stat().st_size > 10_000:
        return TXT_LOCAL
    import subprocess

    print(f"  Converting {RTF_SOURCE.name} via textutil...")
    subprocess.run(
        ["textutil", "-convert", "txt", "-output", str(TXT_LOCAL), str(RTF_SOURCE)],
        check=True,
    )
    print(f"  Saved {TXT_LOCAL.stat().st_size:,} bytes")
    return TXT_LOCAL


def parse_phil_23() -> dict[str, dict[str, str]]:
    """Return mapping key→{'greek':..., 'french':...} where key is 'N' or 'titulus_N'."""
    txt_path = ensure_txt_local()
    text = txt_path.read_text()
    lines = text.split("\n")

    block_starts: list[tuple[int, str, int]] = []
    for i, line in enumerate(lines):
        m = HEADER_RE.match(line)
        if m:
            if m.group(2):
                block_starts.append((i, "par", int(m.group(2))))
            else:
                block_starts.append((i, "titulus", int(m.group(3))))
        elif SENTINEL_RE.match(line):
            block_starts.append((i, "end", -1))
            break
    if not block_starts or block_starts[-1][1] != "end":
        block_starts.append((len(lines), "end", -1))

    by_greek: dict[str, list[str]] = defaultdict(list)
    by_french: dict[str, list[str]] = defaultdict(list)

    # Paragraph blocks (normal)
    for idx in range(len(block_starts) - 1):
        start_line, kind, par_n = block_starts[idx]
        if kind == "end":
            break
        end_line = block_starts[idx + 1][0]
        in_content = False
        for ln in lines[start_line:end_line]:
            if "Previous paragraph" in ln or "Next paragraph" in ln:
                in_content = True
                continue
            if "cap.:" in ln or "chap.:" in ln:
                continue
            if not in_content:
                continue
            if PAGE_MARKER_RE.search(ln):
                continue
            m2 = CONTENT_RE.match(ln)
            if not m2:
                continue
            chunk = re.sub(r"\s+", " ", m2.group(1).strip()).rstrip("\t").strip()
            if not chunk:
                continue
            key = f"titulus_{par_n}" if kind == "titulus" else str(par_n)
            if GREEK_CHARS_RE.search(chunk):
                by_greek[key].append(chunk)
            else:
                by_french[key].append(chunk)

    return {k: {"greek": " ".join(by_greek[k]), "french": " ".join(by_french[k])} for k in by_greek}


# -----------------------------------------------------------------------------
# Alignment Phil ↔ PE VI.11
# -----------------------------------------------------------------------------


def normalize_greek(s: str) -> str:
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    s = re.sub(r"[^Ͱ-Ͽ\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def align_pe_to_phil(
    nodes: list[dict], phil: dict[str, dict[str, str]]
) -> dict[int, str]:
    """For each PE VI.11.N section, find the Phil 23 key whose Greek contains its opening."""
    pe: dict[int, str] = {}
    for n in nodes:
        nid = n.get("id", "")
        m = re.match(r"passage_eusebius_praep_ev_6_11_(\d+)$", nid)
        if m:
            sec = int(m.group(1))
            pe[sec] = n.get("description", "").strip().lstrip('"“').strip()

    phil_norm = {k: normalize_greek(v["greek"]) for k, v in phil.items()}

    mapping: dict[int, str] = {}
    for pe_sec, pe_text in pe.items():
        norm = normalize_greek(pe_text)
        words = norm.split()
        if len(words) < 4:
            continue
        needle_long = " ".join(words[:6])
        needle_short = " ".join(words[:4])
        hit_key: str | None = None
        for k, v in phil_norm.items():
            if needle_long in v:
                hit_key = k
                break
        if not hit_key:
            for k, v in phil_norm.items():
                if needle_short in v:
                    hit_key = k
                    break
        if hit_key:
            mapping[pe_sec] = hit_key
    return mapping


# -----------------------------------------------------------------------------
# Node + edge factories
# -----------------------------------------------------------------------------


def build_passage_node(key: str, greek: str, french: str) -> dict:
    """Build passage node. key is either 'N' (paragraph) or 'titulus_N'."""
    is_titulus = key.startswith("titulus_")
    par_n = int(key.split("_")[1]) if is_titulus else int(key)
    if is_titulus:
        pid = f"passage_origen_philocalia_23_titulus_{par_n}"
        label_ref = f"23 (titulus ante §{par_n})"
        cts_section = f"23.titulus.{par_n}"
        section_label = f"Titulus ante par. {par_n}"
    else:
        pid = f"passage_origen_philocalia_23_{par_n}"
        label_ref = f"23.{par_n}"
        cts_section = f"23.{par_n}"
        section_label = f"§ {par_n}"

    description = greek if greek else french

    metadata = {
        "attestation_type": "direct",
        "author": "Origen of Alexandria",
        "compiler_note": (
            "Philocalia compiled by Basil of Caesarea and Gregory of Nazianzus c. 358/360 "
            "from Origen's lost Commentary on Genesis, tome III"
        ),
        "canonical_ref": label_ref,
        "char_length": len(description),
        "word_count": len(description.split()),
        "cts_urn": f"urn:cts:greekLit:tlg2042.tlg028:{cts_section}",
        "language": "grc",
        "passage_role": "original",
        "school": "Christian Platonism",
        "work_title": "Philocalia",
        "chapter": 23,
        "section_label": section_label,
        "edition": SOURCE_EDITION,
        "edition_full": (
            "Éric Junod, Origène. Philocalie 21-27 (Sur le libre arbitre), "
            "Sources Chrétiennes 226, Paris: Cerf, 1976"
        ),
        "source": SOURCE_TAG,
        "source_local_path": str(RTF_SOURCE),
        "created_by": CREATED_BY,
        "contains_greek_to_verify": False,
        "period": "Patristic",
        "text_grc": greek,
        "text_fra": french,
        "is_titulus": is_titulus,
        "is_amand_phil_23_transmission": True,
        "amand_note": (
            "Amand 1945, p. 366 : Philocalia 23 ≈ PE VI.11 verbatim — "
            "transmission canonique de l'antifatalisme origénien chez Eusèbe."
        ),
    }
    if is_titulus:
        metadata["titulus_ante_paragraph"] = par_n

    return {
        "id": pid,
        "node_id": pid,
        "type": "passage",
        "label": f"Origen, Philocalia {label_ref}",
        "description": description,
        "alternative_names": "[]",
        "period": "Patristic",
        "role": None,
        "school": "Christian Platonism",
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


def key_to_pid(key: str) -> str:
    if key.startswith("titulus_"):
        n = key.split("_")[1]
        return f"passage_origen_philocalia_23_titulus_{n}"
    return f"passage_origen_philocalia_23_{key}"


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------


def main() -> int:
    print("== PHIL 23 SC 226 INGESTION ==")
    print("\n== PHASE 0 : LOAD KG ==")
    nodes = [json.loads(line) for line in NODES_PATH.read_text().splitlines() if line.strip()]
    edges = [json.loads(line) for line in EDGES_PATH.read_text().splitlines() if line.strip()]
    node_by_id = {n["id"]: i for i, n in enumerate(nodes)}
    print(f"  Nodes loaded: {len(nodes)} ; edges: {len(edges)}")

    # verify prerequisites
    for req in (WORK_ID, PERSON_ID):
        if req not in node_by_id:
            print(f"  FATAL: required node {req} missing")
            return 1

    print("\n== PHASE 1 : PARSE SC 226 RTF ==")
    phil = parse_phil_23()
    print(f"  Phil 23 keys parsed: {len(phil)}")
    for k in sorted(phil.keys(), key=lambda x: (x.startswith("titulus_"), int(x.split("_")[-1]) if x != "titulus_22" else 22, int(x.split("_")[1]) if x.startswith("titulus_") else int(x))):
        g, f = phil[k]["greek"], phil[k]["french"]
        print(f"    {k}: grc={len(g)} fra={len(f)}")

    print("\n== PHASE 2 : CREATE PASSAGE NODES ==")
    inserted = 0
    skipped = 0
    new_passage_ids: list[str] = []
    new_key_to_pid: dict[str, str] = {}
    for key in phil:
        pid = key_to_pid(key)
        new_key_to_pid[key] = pid
        if pid in node_by_id:
            skipped += 1
            new_passage_ids.append(pid)
            continue
        node = build_passage_node(key, phil[key]["greek"], phil[key]["french"])
        nodes.append(node)
        node_by_id[pid] = len(nodes) - 1
        new_passage_ids.append(pid)
        inserted += 1
    print(f"  Inserted: {inserted} ; skipped-existing: {skipped}")

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
    for pid in new_passage_ids:
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

    print("\n== PHASE 4 : EVIDENCED_BY EDGES (ORIGEN-AMAND ARGUMENTS → PHIL 23) ==")
    existing_evidenced = set()
    for e in edges:
        if e.get("relation") == "evidenced_by":
            src = e.get("source_id") or e.get("source")
            tgt = e.get("target_id") or e.get("target")
            existing_evidenced.add((src, tgt))
    ev_inserted = ev_skipped = 0
    missing_args = []
    for arg_id, keys in ARG_ANCHORS:
        if arg_id not in node_by_id:
            missing_args.append(arg_id)
            continue
        for key in keys:
            tgt_pid = new_key_to_pid.get(key)
            if not tgt_pid:
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
                        "anchor_source": "amand1945_dissertation_structure",
                        "anchor_via": "phil23_sc226_section_grained",
                    },
                )
            )
            existing_evidenced.add((arg_id, tgt_pid))
            ev_inserted += 1
    print(f"  evidenced_by inserted: {ev_inserted} ; skipped: {ev_skipped}")
    if missing_args:
        print(f"  WARN: missing arg nodes: {missing_args}")

    print("\n== PHASE 5 : PARALLEL_TO EDGES (PHIL 23 ↔ PE VI.11) ==")
    mapping = align_pe_to_phil(nodes, phil)
    print(f"  PE→Phil verbatim matches: {len(mapping)} (out of 83 PE sections)")
    existing_parallel = set()
    for e in edges:
        if e.get("relation") == "parallel_to":
            src = e.get("source_id") or e.get("source")
            tgt = e.get("target_id") or e.get("target")
            existing_parallel.add((src, tgt))
            existing_parallel.add((tgt, src))
    par_inserted = par_skipped = 0
    for pe_sec, phil_key in sorted(mapping.items()):
        pe_pid = f"passage_eusebius_praep_ev_6_11_{pe_sec}"
        phil_pid = new_key_to_pid.get(phil_key) or key_to_pid(phil_key)
        if (phil_pid, pe_pid) in existing_parallel:
            par_skipped += 1
            continue
        edges.append(
            build_edge(
                phil_pid,
                pe_pid,
                "parallel_to",
                {
                    "alignment_method": "opening_words_normalized_greek_substring",
                    "alignment_window_words": 6,
                    "phil_edition": SOURCE_EDITION,
                    "pe_edition": "Dindorf t. I (Leipzig 1867) re-encoded First1KGreek",
                    "amand_p366_verbatim_assertion": "Phil. 23 ≈ PE VI.11",
                    "confidence": "high (verbatim match on first 6 normalized words)",
                },
            )
        )
        existing_parallel.add((phil_pid, pe_pid))
        existing_parallel.add((pe_pid, phil_pid))
        par_inserted += 1
    print(f"  parallel_to inserted: {par_inserted} ; skipped: {par_skipped}")

    print("\n== PHASE 6 : WRITE BACK ==")
    with NODES_PATH.open("w") as f:
        for n in nodes:
            f.write(json.dumps(n, ensure_ascii=False) + "\n")
    with EDGES_PATH.open("w") as f:
        for ed in edges:
            f.write(json.dumps(ed, ensure_ascii=False) + "\n")
    print(f"  nodes.jsonl: {len(nodes)}")
    print(f"  edges.jsonl: {len(edges)}")
    print("\n== PHIL 23 INGESTION COMPLETE ==")
    return 0


if __name__ == "__main__":
    sys.exit(main())
