"""Ingest Robinson 1893 critical text of Philocalia 21 (= Origen, De Princ III.1)
into the 4 Philocalia 21 sub-anchor shells.

The SC 226 RTF (Junod 1976) chapter 21 is missing from the OCR export, and the
SC 226 PDF Greek text layer is OCR-mangled (Acrobat Paper Capture 2015-2016 on
polytonic Greek). Robinson 1893 is the only complete pre-Junod critical edition
of the Philocalia (Cambridge University Press); Junod 1976 SC 226 is essentially
a re-edition of Robinson with updated apparatus. The Sematika local file at
`[local-path]` contains a clean
polytonic-Greek extraction of Robinson 1893 (with inline critical apparatus).

This script:
  1. Extracts Robinson's chapter 21 (lines 3294-3871 of Sematika file) — 23 sections.
  2. Splits each section into "pure Greek text" + "critical apparatus" via heuristic
     (apparatus contains MS sigla AB/ABC/ABD/Ru./cat/Hier., numeric line refs, and
     reading variants — recognizable by mixed-script Latin + Greek + digits).
  3. Maps Robinson §N → Koetschau De Princ III.1.§N+1 (Robinson §1 = Koetschau §§1-2 merged).
  4. Updates the 4 Philocalia 21 sub-anchor shells (passage_origen_philocalia_21_{5,7,18,23})
     with Robinson Greek + apparatus + Junod 1976 SC 226 / Robinson 1893 dual citation.

Idempotent.

CITATION CHAIN (maximum rigor):
  Robinson 1893 (Cambridge UP, manuscripts ABCDEF + catena)
     → Junod 1976 SC 226 (modern standard, re-edits Robinson)
     → Crouzel-Simonetti 1980 SC 268 (Latin-side edition; uses Junod's Greek for Philocalia 21 extracts)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
NODES_PATH = REPO_ROOT / "data" / "kg" / "nodes.jsonl"

SEMATIKA_PHILOC = Path("[local-path]")
CHAPTER_21_START_LINE = 3294  # 1-indexed; "XXI. Περὶ αὐτεξουσίου..."
CHAPTER_21_END_LINE = 3871    # exclusive (line 3872 = "XXII. ...")

# Map Robinson section → Koetschau (= De Princ III.1) section number.
# Robinson merges Koetschau §§1-2 into Robinson §1; thereafter Robinson §N = Koetschau §N+1.
ROBINSON_TO_KOETSCHAU = {1: [1, 2]} | {n: [n + 1] for n in range(2, 24)}

# Shell IDs we are updating (Koetschau numbering)
TARGET_KOETSCHAU = {5, 7, 18, 23}


ROBINSON_EDITION = (
    "J. A. Robinson (ed.), The Philocalia of Origen, Cambridge: Cambridge University Press, 1893."
)
JUNOD_EDITION = (
    "É. Junod (ed.), Origène, Philocalie 21–27 (Sur le libre arbitre), "
    "Sources Chrétiennes 226, Paris: Cerf, 1976."
)

# Manuscript sigla used in Robinson's apparatus
MS_SIGLA = "(?:AB|ABC|ABD|ABCD|ABCDF|ABCDEF|ABCE|BCD|BD|BCE|cat|Ru\.|Hier\.|Koe\.|Coisl\.|Eus\.|C[a-z]?|[AB]\([A-Z]\)|U\+[0-9A-Fa-f]+)"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def dump_jsonl(path: Path, items: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def parse_md(node: dict[str, Any]) -> dict[str, Any]:
    md = node.get("metadata")
    if md is None or md == "":
        return {}
    if isinstance(md, dict):
        return md
    try:
        return json.loads(md)
    except (json.JSONDecodeError, TypeError):
        return {}


def extract_chapter_21(path: Path, start: int, end: int) -> str:
    """Lines [start, end) one-indexed. Returns one long Greek string."""
    with path.open("r", encoding="utf-8") as f:
        lines = f.readlines()
    return "".join(lines[start - 1:end - 1])


def split_robinson_sections(chapter_text: str) -> dict[int, str]:
    """Robinson section markers appear inline as " N. " where N is 1-23.

    Strategy: walk through the text token-by-token, watch for " <digits>. <Greek>"
    transitions. The opening (XXI. heading + section 1) starts BEFORE any inline §
    marker — section 1's marker is the title break before "Ἐπεὶ δὲ ἐν τῷ κηρύγματι".

    We use a deliberate marker: the patterns "ABD ῥητῶν..." (end of title) and " 1. "
    or " 2. " etc.
    """
    # Easier approach: use known section-opening phrases.
    # Robinson section 1 starts with "Ἐπεὶ δὲ ἐν τῷ κηρύγματι"
    # Subsequent sections open with their numeric marker.
    # We locate each marker position.
    sections: dict[int, tuple[int, int]] = {}
    text = chapter_text

    # Robinson §1 explicit opening
    m1 = re.search(r"Ἐπεὶ\s+δὲ\s+ἐν\s+τῷ\s+κηρύγματι", text)
    if not m1:
        raise RuntimeError("Robinson §1 opening not found")

    # For §§2-23, find " N. <Capital Greek>"
    markers: list[tuple[int, int]] = [(1, m1.start())]
    for n in range(2, 24):
        # Match " N. <Greek capital>"  — the digit must be preceded by whitespace
        # and followed by . then space then Greek capital (Α-Ω + diacritics)
        # We deduplicate by accepting only the FIRST occurrence after the previous marker
        pat = re.compile(rf"\b{n}\.\s+([Α-ΩἈ-Ὦ])")
        m = None
        for cand in pat.finditer(text):
            if cand.start() > markers[-1][1]:
                m = cand
                break
        if m is None:
            print(f"  [!] section {n} marker not found via primary pattern")
            continue
        markers.append((n, m.start()))

    # Build sections by slicing
    section_texts: dict[int, str] = {}
    for i, (sec, pos) in enumerate(markers):
        end_pos = markers[i + 1][1] if i + 1 < len(markers) else len(text)
        section_texts[sec] = text[pos:end_pos].strip()
    return section_texts


# Heuristic regex to identify inline critical-apparatus FRAGMENTS:
# - Latin-letter MS sigla (AB, ABC, ABD, Ru., cat, etc.)
# - Numeric line refs (e.g. "16, 17", "26", "1 Ru. 1. 108")
# - Latin scholia (e.g. "rursus incipit C", "deest folium in C", "restitui;")
APPARATUS_RUN = re.compile(
    r"(?:"
    r"\s\d+(?:,\s\d+)*\s+[Α-ωἀ-ᾼ]+\s+(?:AB|ABC|ABD|ABCD|BC|BD|cat|Ru\.|Hier\.|Koe\.)\b[^.]{0,80}\.?|"
    r"\b(?:deest folium|rursus incipit|restitui|post|ante|om\.|hic desinit|cat|plura habent|cf\.|U\+[0-9A-Fa-f]+)\b[^.]{0,120}\.?"
    r")"
)


def clean_greek(raw: str) -> tuple[str, list[str]]:
    """Strip inline critical-apparatus tokens; return (cleaned_greek, apparatus_fragments).

    Cleaning steps:
      - Remove the leading " N. " section marker
      - Remove Latin-letter MS sigla and apparatus runs
      - Remove line-reference numbers
      - Collapse whitespace
    """
    text = raw
    # 1. Strip leading section marker " N. "
    text = re.sub(r"^\s*\d+\.\s+", "", text)

    # 2. Capture apparatus runs (heuristic) and remove them
    fragments: list[str] = []
    def _cap(m: re.Match) -> str:
        fragments.append(m.group(0).strip())
        return " "
    text = APPARATUS_RUN.sub(_cap, text)

    # 3. Strip remaining Latin-letter manuscript sigla runs (standalone)
    text = re.sub(r"\b(?:AB|ABC|ABD|ABCD|BC|BD|cat|Ru\.|Hier\.|Koe\.|Coisl\.)\b", " ", text)
    # 4. Strip U+XXXX placeholders
    text = re.sub(r"U\+[0-9A-Fa-f]+", " ", text)
    # 5. Strip biblical-reference cross-refs in Latin (e.g. "Ro ix 21", "2 Tim ii 21", "Mt v")
    text = re.sub(r"\b\d?\s?(?:Ro|Cor|Tim|Ge|Ex|Mt|Lk|Jn|Ru|cf|cat|Heb|Phil|Eph|Gal|Col|Th|Pe|Ja|Re|Acts)\s+[ivxlcdmIVXLCDM]+(?:\s+\d+(?:,\s?\d+)?)?", " ", text)
    # 6. Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text, fragments


def main() -> int:
    print(f"Reading Sematika Philocalia chapter 21 (lines {CHAPTER_21_START_LINE}-{CHAPTER_21_END_LINE - 1}) …")
    chapter_text = extract_chapter_21(SEMATIKA_PHILOC, CHAPTER_21_START_LINE, CHAPTER_21_END_LINE)
    print(f"  raw chapter length: {len(chapter_text)} chars")

    sections = split_robinson_sections(chapter_text)
    print(f"  detected Robinson sections: {sorted(sections.keys())}")

    nodes = load_jsonl(NODES_PATH)
    by_id = {n["id"]: n for n in nodes}
    print(f"Loaded {len(nodes):,} nodes")

    # Build Koetschau→Robinson reverse map for our 4 targets
    koe_to_rob: dict[int, int] = {}
    for rob, koes in ROBINSON_TO_KOETSCHAU.items():
        for k in koes:
            koe_to_rob[k] = rob

    updated = 0
    for koe_par in sorted(TARGET_KOETSCHAU):
        rob_par = koe_to_rob.get(koe_par)
        if rob_par is None:
            print(f"  [skip] Koetschau §{koe_par} has no Robinson counterpart")
            continue
        nid = f"passage_origen_philocalia_21_{koe_par}"
        node = by_id.get(nid)
        if node is None:
            print(f"  [missing] {nid}")
            continue
        raw = sections.get(rob_par, "")
        if not raw:
            print(f"  [no-robinson-text] §{rob_par} → {nid}")
            continue
        greek_clean, apparatus = clean_greek(raw)

        # Update fields
        node["description_grc"] = greek_clean
        node["description_grc_robinson_with_apparatus"] = raw  # preserve full Robinson with inline apparatus
        # Keep existing French description from Phase 1 (SC 268 French)
        # Keep existing description_en (shell summary)

        md = parse_md(node)
        md["source_quality"] = "critical_edition_robinson_1893_via_sematika_corresponds_to_junod_1976"
        md["primary_source_used"] = ROBINSON_EDITION
        md["principal_edition_modern"] = JUNOD_EDITION
        md["robinson_1893_section"] = rob_par
        md["robinson_to_koetschau_mapping"] = f"Robinson §{rob_par} = Koetschau §{koe_par}"
        md["critical_apparatus_robinson"] = apparatus
        md["manuscript_sigla_recorded"] = "A B C D E F (Robinson 1893 collation: A=Vat. gr. 388, B=Ven. gr. 47, C=Coisl. 116, D=Lugd.-Bat. Voss. gr. F 17, E=Paris. gr. 615, F=Patm. 270)"
        md["junod_sc226_status_note"] = (
            "Junod 1976 SC 226 chapter 21 is a re-edition of Robinson 1893 with minor "
            "updates to the apparatus. SC 226 RTF OCR-export missing chapter 21; SC 226 "
            "PDF Greek text-layer OCR-mangled (Acrobat Paper Capture 2015). Robinson 1893 "
            "(Cambridge UP) is the textual basis here, citable as Robinson 1893 directly "
            "or via the modern Junod 1976 SC 226 re-edition."
        )
        md.pop("needs_text_ingestion", None)
        node["metadata"] = json.dumps(md, ensure_ascii=False)
        node.pop("needs_evidence", None)
        node["confidence"] = max(node.get("confidence", 0.0) or 0.0, 0.97)
        updated += 1
        print(f"  [updated] {nid}  Robinson §{rob_par} → Koetschau §{koe_par}  "
              f"(grc_clean={len(greek_clean)} app_fragments={len(apparatus)} raw={len(raw)} chars)")

    print(f"\nUpdated {updated}/{len(TARGET_KOETSCHAU)} Philocalia 21 sub-anchor shells")
    dump_jsonl(NODES_PATH, nodes)
    print(f"Wrote {NODES_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
