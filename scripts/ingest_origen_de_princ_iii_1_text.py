"""Ingest Origen De Principiis III.1 §§1-24 text into the 27 passage shells.

Sources (local DOCTORAT corpus — see the local scholarly-sources index):
- SC 268 bilingual (Crouzel-Simonetti 1980)
    `02_Corpus/Sources chrétiennes txt/03_Origene/bilingue/SC268_Origenes_Traite_des_Principes_livre_3_bilingue.txt`
    Latin (Rufinus) + French translation
- SC 268 Greek extracts (Philocalia 21 reconstruction)
    `02_Corpus/Sources chrétiennes txt/03_Origene/source/SC268_Origenes_Traite_des_Principes_Extraits_grecs_livre_3_source.txt`
    Polytonic Greek + French translation

For each shell `passage_origen_pa_3_1_<N>` (N=1..2, 4..24), this script:
  - Sets description = French (SC 268, primary per project conv.)
  - Sets description_la = Rufinus Latin (SC 268)
  - Sets description_grc = polytonic Greek (where Philocalia preserves it)
  - Preserves description_en (English shell summary — useful navigation)
  - Clears needs_text_ingestion + needs_evidence flags
  - Sets source_quality = "critical_edition_sc268_crouzel_simonetti_1980"
  - Adds critical-edition citation metadata

Idempotent: re-running on already-ingested shells re-writes the same content.

Does NOT touch the pre-existing passage_origen_pa_3_1_3 / _en (already populated).
Does NOT touch passage_origen_philocalia_21_<n> sub-anchors (those need SC 226 RTF
which is a separate ingestion path; flagged for follow-up).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
NODES_PATH = REPO_ROOT / "data" / "kg" / "nodes.jsonl"

SC268_BILINGUE = Path(
    "[local-path] SHAL/02_Corpus/Sources chrétiennes txt/"
    "03_Origene/bilingue/SC268_Origenes_Traite_des_Principes_livre_3_bilingue.txt"
)
SC268_GREEK = Path(
    "[local-path] SHAL/02_Corpus/Sources chrétiennes txt/"
    "03_Origene/source/SC268_Origenes_Traite_des_Principes_Extraits_grecs_livre_3_source.txt"
)

# Markers to strip (SC page references appear inline, e.g. "--- 16 ---")
PAGE_MARKER = re.compile(r"---\s*\d+\s*---")
HEADER_BLOCK_RE = re.compile(r"^\[liv\.:\s*(\d+),\s*chap\.[^:]*:\s*(\d+),\s*par\.:\s*(\d+)\]")


def _clean(text: str) -> str:
    """Strip SC page markers, squeeze whitespace, fix common OCR artifacts."""
    text = PAGE_MARKER.sub(" ", text)
    text = re.sub(r"\s+", " ", text).strip()
    # Re-introduce a space after sentence terminators that lost it through OCR
    text = re.sub(r"([\.\!\?])([A-ZΑ-Ω])", r"\1 \2", text)
    return text


def parse_sc_file(path: Path, section_marker: str) -> dict[tuple[int, int], dict[str, str]]:
    """Parse SC bilingual/extracts file. Returns {(chap, par): {section_marker: str, "french": str}}.

    Multiple blocks for the same (chap, par) are concatenated.
    """
    raw = path.read_text(encoding="utf-8")
    blocks = raw.split("==================================================")
    out: dict[tuple[int, int], dict[str, str]] = {}

    for block in blocks:
        lines = block.strip().split("\n")
        if not lines:
            continue
        # Find the header line
        header = None
        for line in lines:
            m = HEADER_BLOCK_RE.match(line)
            if m:
                header = (int(m.group(2)), int(m.group(3)))
                break
        if header is None:
            continue

        # Extract LATIN/SOURCE/FRANCAIS/TRADUCTION sections
        text = "\n".join(lines)
        # Sections marked by --- LATIN --- / --- SOURCE --- / --- FRANCAIS --- / --- TRADUCTION ---
        section_pat = re.compile(r"---\s*(LATIN|SOURCE|FRANCAIS|TRADUCTION)\s*---")
        parts = section_pat.split(text)
        # parts is [pre, label1, body1, label2, body2, ...]
        primary_body = ""
        french_body = ""
        for i in range(1, len(parts) - 1, 2):
            label = parts[i].strip().upper()
            body = parts[i + 1]
            # Strip subsequent header lines that bleed into the body
            body = re.sub(r"\[liv\.[^\]]+\]", "", body)
            body = _clean(body)
            if label in {"LATIN", "SOURCE"}:
                primary_body = (primary_body + " " + body).strip() if primary_body else body
            elif label in {"FRANCAIS", "TRADUCTION"}:
                french_body = (french_body + " " + body).strip() if french_body else body

        slot = out.setdefault(header, {section_marker: "", "french": ""})
        if primary_body:
            slot[section_marker] = (slot[section_marker] + " " + primary_body).strip() if slot[section_marker] else primary_body
        if french_body:
            slot["french"] = (slot["french"] + " " + french_body).strip() if slot["french"] else french_body

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


SC_268_EDITION = "GCS-aware critical edition: H. Crouzel, M. Simonetti (eds.), Origène, Traité des Principes, Tome III: Livre III, Sources Chrétiennes 268, Paris: Cerf, 1980."
SC_226_REFERENCE = "Greek (Philocalia 21): É. Junod (ed.), Origène, Philocalie 21–27 (Sur le libre arbitre), Sources Chrétiennes 226, Paris: Cerf, 1976."


def main() -> int:
    print(f"Parsing {SC268_BILINGUE.name} …")
    latin_fr = parse_sc_file(SC268_BILINGUE, "latin")
    print(f"  parsed {len(latin_fr)} (chap, par) blocks (Latin+French)")
    print(f"Parsing {SC268_GREEK.name} …")
    greek_fr = parse_sc_file(SC268_GREEK, "greek")
    print(f"  parsed {len(greek_fr)} (chap, par) blocks (Greek+French)")

    nodes = load_jsonl(NODES_PATH)
    print(f"Loaded {len(nodes):,} nodes")

    updated = 0
    skipped_no_text = 0
    not_a_shell = 0
    by_id = {n["id"]: n for n in nodes}

    for n in range(1, 25):
        nid = f"passage_origen_pa_3_1_{n}"
        node = by_id.get(nid)
        if node is None:
            print(f"  [missing] {nid}")
            continue
        # Skip pre-existing §3 (it has substantive content already, leave intact)
        if n == 3:
            print(f"  [skip-preexist] {nid} (rich pre-existing content)")
            continue

        latin = (latin_fr.get((1, n)) or {}).get("latin", "")
        french = (latin_fr.get((1, n)) or {}).get("french", "")
        greek = (greek_fr.get((1, n)) or {}).get("greek", "")
        # Greek-file french as fallback if bilingual file French is missing
        if not french:
            french = (greek_fr.get((1, n)) or {}).get("french", "")

        if not (latin or greek):
            print(f"  [skip-no-text] {nid}: no Latin or Greek found in SC files")
            skipped_no_text += 1
            continue

        # Preserve the English shell summary
        en_summary = node.get("description_en") or node.get("description") or ""

        # Set primary description = French (project convention)
        if french:
            node["description"] = french
        # English summary preserved
        node["description_en"] = en_summary
        # Latin (Rufinus, SC 268)
        if latin:
            node["description_la"] = latin
        # Greek (Philocalia 21 via SC 268 Greek extracts)
        if greek:
            node["description_grc"] = greek
            has_greek = True
        else:
            has_greek = False

        # Update metadata
        md = parse_node_metadata(node)
        md["source_quality"] = "critical_edition_sc268_crouzel_simonetti_1980"
        md["principal_edition"] = SC_268_EDITION
        md["greek_witness_via"] = "Philocalia 21" if has_greek else None
        if has_greek:
            md["greek_edition_reference"] = SC_226_REFERENCE
        md.pop("needs_text_ingestion", None)
        md.pop("editions_to_consult", None)
        md["ingested_from"] = {
            "sc268_bilingue_file": str(SC268_BILINGUE),
            "sc268_greek_extracts_file": str(SC268_GREEK) if has_greek else None,
        }
        node["metadata"] = json.dumps(md, ensure_ascii=False)

        # Drop top-level needs_evidence flag (the passage is now anchored to a critical edition)
        node.pop("needs_evidence", None)

        # Boost confidence — we have a critical edition
        node["confidence"] = max(node.get("confidence", 0.0) or 0.0, 0.95)

        updated += 1
        marker = "GRC+LAT+FR" if has_greek else "LAT+FR"
        print(f"  [updated:{marker}] {nid}  (lat={len(latin)} fr={len(french)} grc={len(greek)} chars)")

    print(f"\nUpdated: {updated}  |  Skipped (no text): {skipped_no_text}")
    dump_jsonl(NODES_PATH, nodes)
    print(f"Wrote {NODES_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
