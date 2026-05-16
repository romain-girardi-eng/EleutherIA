"""Ingest Junod 1976 (SC 226) Philocalia 21-27 text with maximum rigor.

Two distinct enrichments in one pass:

Part A — 4 Philocalia 21 sub-anchor shells (§§5, 7, 18, 23 of Philocalia 21 =
De Princ III.1.5/7/18/23 in Koetschau numbering)
    The SC 226 RTF as exported is incomplete: it contains only chapters 23,
    25, 26, 27 (the title "Philocalie 21-27" notwithstanding). Chapter 21 is
    NOT present in this OCR export. For these 4 shells we therefore use SC 268's
    Greek extracts (Crouzel-Simonetti 1980, which IS Junod's Philocalia 21 text
    re-typeset by SC 268's editors) as the Greek witness, with explicit
    metadata noting (a) the RTF gap and (b) that the Greek is Junod-derived
    via SC 268.

Part B — Enrich existing Philocalia 23/25/26/27 passages
    There are 26 passages already in the KG for chapters 23/25/26/27 (created
    by an earlier ingestion). They carry Greek text in `description` but lack:
      - `description_grc` (Greek properly typed)
      - `description_fr` (French translation from Junod)
      - source_quality + principal_edition metadata
    This pass parses SC 226 RTF, matches each existing passage by (chap, par),
    moves Greek to `description_grc`, adds French to a new `description_fr`
    AND replaces `description` with the French (project convention: French
    primary). Original Greek is preserved as `description_grc`.

Citation: É. Junod (ed.), Origène, Philocalie 21–27 (Sur le libre arbitre),
Sources Chrétiennes 226, Paris: Cerf, 1976.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
NODES_PATH = REPO_ROOT / "data" / "kg" / "nodes.jsonl"

SC226_RTF = Path(
    "/Users/romaingirardi/Desktop/DOCTORAT/Doctorat SHAL/02_Corpus/SC 226 - Origène, Philocalie 21-27 (Sur le libre arbitre).rtf"
)
SC226_TXT = Path("/tmp/sc226_junod.txt")  # produced by `textutil -convert txt`
SC268_GREEK = Path(
    "/Users/romaingirardi/Desktop/DOCTORAT/Doctorat SHAL/02_Corpus/Sources chrétiennes txt/"
    "03_Origene/source/SC268_Origenes_Traite_des_Principes_Extraits_grecs_livre_3_source.txt"
)

PAGE_MARKER = re.compile(r"---\s*\d+\s*---")
HEADER_BLOCK_RE = re.compile(r"cap\.\s*:\s*(\d+),\s*par\.\s*:\s*(\d+)")
TITULUS_RE = re.compile(r"cap\.\s*:\s*(\d+),\s*titulus ante par\.\s*:\s*(\d+)")
SC268_HEADER_RE = re.compile(r"\[liv\.:\s*(\d+),\s*chap\.[^:]*:\s*(\d+),\s*par\.:\s*(\d+)\]")
JUNK_LINE_RE = re.compile(r"^\s*(Origenes|Origène|Philocalia|Philocalie|<<.*Previous.*Next.*>>|<<.*Précédent.*Suivant.*>>)\s*$")

JUNOD_EDITION = (
    "É. Junod (ed.), Origène, Philocalie 21–27 (Sur le libre arbitre), "
    "Sources Chrétiennes 226, Paris: Cerf, 1976."
)
SC268_EDITION = (
    "H. Crouzel & M. Simonetti (eds.), Origène, Traité des Principes, Tome III: "
    "Livre III, Sources Chrétiennes 268, Paris: Cerf, 1980 (Greek extracts = "
    "Philocalia 21 reconstruction)."
)


def _strip_line_number(line: str) -> str:
    """Junod-style line numbers (1-30 in margin) appear as leading tokens.
    Drop a leading purely-numeric token if present."""
    parts = line.split("\t", 1)
    if len(parts) == 2 and parts[0].strip().isdigit():
        return parts[1]
    return line


def _clean_text(s: str) -> str:
    s = PAGE_MARKER.sub(" ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def parse_sc226_rtf_txt(path: Path) -> dict[tuple[int, int], dict[str, str]]:
    """Parse SC 226 (Junod) TXT export. Returns {(chap, par): {"greek", "french"}}.

    The RTF export has a peculiar layout: each (chap, par) appears TWICE — once
    with Greek+French interleaved with line numbers, once again with the French
    translation. We extract by accumulating Greek lines (chars in Greek block)
    and French lines (chars in Latin/French block) separately.
    """
    raw = path.read_text(encoding="utf-8")
    lines = raw.split("\n")
    out: dict[tuple[int, int], dict[str, str]] = {}

    current_key: tuple[int, int] | None = None
    is_french_block = False  # The RTF puts Greek first then French for each block

    GREEK_CHARS = re.compile(r"[Α-Ωα-ωἀ-ᾼ]")

    block_buffer: dict[str, list[str]] = {"greek": [], "french": []}

    def flush_block():
        if current_key is None:
            return
        slot = out.setdefault(current_key, {"greek": "", "french": ""})
        gk = _clean_text(" ".join(block_buffer["greek"]))
        fr = _clean_text(" ".join(block_buffer["french"]))
        if gk:
            slot["greek"] = (slot["greek"] + " " + gk).strip() if slot["greek"] else gk
        if fr:
            slot["french"] = (slot["french"] + " " + fr).strip() if slot["french"] else fr
        block_buffer["greek"].clear()
        block_buffer["french"].clear()

    for raw_line in lines:
        line = raw_line.rstrip("\r\n")
        if JUNK_LINE_RE.match(line):
            continue
        m_par = HEADER_BLOCK_RE.search(line)
        m_tit = TITULUS_RE.search(line)
        if m_tit:
            flush_block()
            current_key = (int(m_tit.group(1)), 0)  # par=0 = titulus (chapter title)
            is_french_block = False
            continue
        if m_par:
            flush_block()
            current_key = (int(m_par.group(1)), int(m_par.group(2)))
            is_french_block = False
            continue
        if current_key is None:
            continue
        cleaned = _strip_line_number(line).strip()
        if not cleaned:
            continue
        # Detect language by character set
        is_greek = bool(GREEK_CHARS.search(cleaned))
        if is_greek:
            block_buffer["greek"].append(cleaned)
        else:
            # French (or Latin lemma) — strip any HTML/RTF junk
            cleaned = re.sub(r"<[^>]+>", " ", cleaned)
            cleaned = _clean_text(cleaned)
            if cleaned and not cleaned.startswith("---"):
                block_buffer["french"].append(cleaned)

    flush_block()
    return out


def parse_sc268_greek(path: Path) -> dict[tuple[int, int], dict[str, str]]:
    """Parse SC 268 Greek extracts file. Same shape as parse_sc226."""
    raw = path.read_text(encoding="utf-8")
    blocks = raw.split("==================================================")
    out: dict[tuple[int, int], dict[str, str]] = {}
    for block in blocks:
        m = SC268_HEADER_RE.search(block)
        if not m:
            continue
        chap, par = int(m.group(2)), int(m.group(3))
        section_pat = re.compile(r"---\s*(SOURCE|TRADUCTION)\s*---")
        parts = section_pat.split(block)
        greek = french = ""
        for i in range(1, len(parts) - 1, 2):
            label = parts[i].strip().upper()
            body = parts[i + 1]
            body = re.sub(r"\[liv\.[^\]]+\]", "", body)
            body = _clean_text(body)
            if label == "SOURCE":
                greek = (greek + " " + body).strip() if greek else body
            elif label == "TRADUCTION":
                french = (french + " " + body).strip() if french else body
        slot = out.setdefault((chap, par), {"greek": "", "french": ""})
        if greek:
            slot["greek"] = (slot["greek"] + " " + greek).strip() if slot["greek"] else greek
        if french:
            slot["french"] = (slot["french"] + " " + french).strip() if slot["french"] else french
    return out


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def dump_jsonl(path: Path, items: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def parse_node_metadata(node: dict[str, Any]) -> dict[str, Any]:
    md = node.get("metadata")
    if md is None or md == "":
        return {}
    if isinstance(md, dict):
        return md
    try:
        return json.loads(md)
    except (json.JSONDecodeError, TypeError):
        return {}


def main() -> int:
    print(f"Parsing SC 226 Junod ({SC226_TXT.name}) …")
    junod = parse_sc226_rtf_txt(SC226_TXT)
    print(f"  parsed {len(junod)} (chap, par) blocks from RTF export")
    chapters_found = sorted({c for c, _ in junod})
    print(f"  chapters in RTF: {chapters_found}")
    if 21 not in chapters_found:
        print("  ⚠ Philocalia chapter 21 is NOT in this RTF export (gap noted in metadata).")

    print(f"Parsing SC 268 Greek extracts ({SC268_GREEK.name}) …")
    sc268_greek = parse_sc268_greek(SC268_GREEK)
    print(f"  parsed {len(sc268_greek)} (chap, par) blocks (SC 268 reconstruction of Philocalia 21)")

    nodes = load_jsonl(NODES_PATH)
    by_id = {n["id"]: n for n in nodes}
    print(f"Loaded {len(nodes):,} nodes")

    # ==========================================================================
    # PART A — Philocalia 21 sub-anchors (§§5, 7, 18, 23)
    # ==========================================================================
    print("\n=== Part A: Philocalia 21 sub-anchor shells ===")
    part_a_updated = 0
    for n_par in [5, 7, 18, 23]:
        nid = f"passage_origen_philocalia_21_{n_par}"
        node = by_id.get(nid)
        if node is None:
            print(f"  [missing] {nid}")
            continue
        # Pull SC 268 Greek for De Princ III.1.<n> (= Philocalia 21.<n>)
        sc268_entry = sc268_greek.get((1, n_par))
        if not sc268_entry or not sc268_entry.get("greek"):
            print(f"  [skip-no-sc268-greek] {nid}")
            continue
        # Preserve existing English summary
        en_summary = node.get("description_en") or node.get("description") or ""
        node["description"] = sc268_entry["french"] or node.get("description") or ""
        node["description_en"] = en_summary
        node["description_grc"] = sc268_entry["greek"]
        md = parse_node_metadata(node)
        md["source_quality"] = "critical_edition_sc268_greek_extracts_junod_derived"
        md["principal_edition"] = JUNOD_EDITION
        md["greek_witness_via"] = "Philocalia 21 (Junod 1976) reconstructed in SC 268 Greek extracts"
        md["principal_edition_sc268"] = SC268_EDITION
        md["junod_sc226_rtf_status"] = (
            "RTF export at " + str(SC226_RTF) + " contains only Philocalia 23, 25, 26, 27 — "
            "chapter 21 is not in this OCR export. Greek text is therefore taken from SC 268's "
            "Greek-extracts companion file, which is itself Crouzel-Simonetti's typesetting of "
            "Junod's Philocalia 21 critical text."
        )
        md.pop("needs_text_ingestion", None)
        md.pop("editions_to_consult", None)
        node["metadata"] = json.dumps(md, ensure_ascii=False)
        node.pop("needs_evidence", None)
        node["confidence"] = max(node.get("confidence", 0.0) or 0.0, 0.95)
        part_a_updated += 1
        print(f"  [updated] {nid}  (grc={len(sc268_entry['greek'])} fr={len(sc268_entry.get('french') or '')} chars)")

    # ==========================================================================
    # PART B — Enrich existing Philocalia 23/25/26/27 passages with Junod French
    # ==========================================================================
    print("\n=== Part B: Enrich existing Philocalia 23/25/26/27 passages with Junod ===")
    part_b_updated = 0
    part_b_missing_junod = 0
    part_b_no_existing_text = 0

    for n in nodes:
        nid = n["id"]
        if not nid.startswith("passage_origen_philocalia_"):
            continue
        # Parse the chap.par from ID; skip the 4 sub-anchors handled in Part A
        # ID patterns: passage_origen_philocalia_<chap>_<par> or _<chap>_titulus_1
        suffix = nid[len("passage_origen_philocalia_"):]
        m = re.match(r"(\d+)_(\d+)$", suffix)
        m_tit = re.match(r"(\d+)_titulus_1$", suffix)
        if m:
            chap, par = int(m.group(1)), int(m.group(2))
        elif m_tit:
            chap, par = int(m_tit.group(1)), 0
        else:
            continue
        if chap == 21:
            continue  # handled in Part A
        if chap not in chapters_found:
            continue  # no Junod text available for this chapter

        junod_entry = junod.get((chap, par))
        if not junod_entry:
            part_b_missing_junod += 1
            continue

        greek_junod = junod_entry.get("greek", "")
        french_junod = junod_entry.get("french", "")

        existing_greek = n.get("description") or ""
        # Existing passages had Greek in `description`. We move it to description_grc
        # and prefer Junod's French as the new `description`.
        # If existing `description` was clearly Greek (chars test) and we have Junod Greek,
        # we prefer Junod Greek but preserve existing as alt.
        GREEK_RE = re.compile(r"[Α-Ωα-ωἀ-ᾼ]")
        existing_is_greek = bool(GREEK_RE.search(existing_greek))

        if not (greek_junod or french_junod):
            continue

        # Set description = Junod French if available, else keep existing
        if french_junod:
            n["description"] = french_junod
        # Set description_grc = Junod Greek (longest, authoritative) or fall back to existing
        if greek_junod:
            n["description_grc"] = greek_junod
            if existing_is_greek and existing_greek and existing_greek != greek_junod:
                md = parse_node_metadata(n)
                md.setdefault("alt_greek_pre_junod_ingest", existing_greek)
                n["metadata"] = md  # will re-serialize below
        elif existing_is_greek and not n.get("description_grc"):
            n["description_grc"] = existing_greek

        # description_en: keep what's there (likely an editorial summary)
        # Update metadata
        md = parse_node_metadata(n)
        md["source_quality"] = "critical_edition_sc226_junod_1976"
        md["principal_edition"] = JUNOD_EDITION
        md["greek_witness"] = "Junod 1976 SC 226 (direct)"
        md["ingested_from"] = {"sc226_txt_export": str(SC226_TXT), "sc226_rtf_source": str(SC226_RTF)}
        md.pop("needs_text_ingestion", None)
        n["metadata"] = json.dumps(md, ensure_ascii=False)
        n.pop("needs_evidence", None)
        n["confidence"] = max(n.get("confidence", 0.0) or 0.0, 0.95)
        part_b_updated += 1
        if part_b_updated <= 5:
            print(f"  [enriched] {nid}  (grc={len(greek_junod)} fr={len(french_junod)} chars)")

    if part_b_updated > 5:
        print(f"  ... ({part_b_updated - 5} more)")
    print(f"\nPart A updates: {part_a_updated}")
    print(f"Part B updates: {part_b_updated}")
    print(f"Part B skipped (no Junod entry for chap/par): {part_b_missing_junod}")

    dump_jsonl(NODES_PATH, nodes)
    print(f"\nWrote {NODES_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
