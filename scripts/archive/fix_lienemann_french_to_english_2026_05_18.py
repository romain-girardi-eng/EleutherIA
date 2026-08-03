#!/usr/bin/env python3
"""Fix Lienemann 2012 citations: French translations → English translations.

Violation of citation standard caught 2026-05-18: my previous patch
(enrich_mitsis_lienemann_fulltext_2026_05_18.py) stored Lienemann's
German quotes alongside French translations. The project standard is
ORIGINAL + ENGLISH (see [[citation-original-plus-english]]).

This patch:
- Renames `translation_fr` → `translation_en` in each
  verified_critiques entry
- Replaces French translations with English ones (translated fresh
  from the German originals)
- Renames `quote_verbatim_de` → `quote_de` for consistency with the
  `quote_<lang>` convention
- Updates the description: French translation snippets removed; if a
  translation is shown inline, it's now English
- Pose marker `lienemann_citation_fix_2026_05_18`

Idempotent. Snapshot. Touches only the Lienemann node.
"""
from __future__ import annotations

import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"
SNAPSHOT_DIR = ROOT / "data" / "kg" / "snapshots" / "2026-05-18-pre-lienemann-citation-fix"

WAVE_TAG = "lienemann_citation_fix_2026_05_18"
NOW = datetime.now(UTC).isoformat(sep=" ")

ID_LIENEMANN = "pub_lienemann_2012_review_frede"
LIENEMANN_PDF_PATH = (
    "[local-path] SHAL/"
    "04_Littérature_secondaire/01_Philosophie_antique/lienemann2012.pdf"
)

# Fresh English translations of the 4 verified German quotes.
ENGLISH_TRANSLATIONS = {
    257: (
        "It is striking in Frede's interpretation that he treats the "
        "differences in cognitive and agential capacity between "
        "animals, children and adult humans as merely gradual. [...] "
        "This claim of Frede's is surprising, since according to the "
        "standard reading of Aristotle in NE III 1-7, praise and "
        "blame are tied to moral responsibility, which cannot "
        "meaningfully be attributed to children and animals."
    ),
    260: (
        "Sharples rightly remarks in the appended endnotes that "
        "Alexander himself does not provide such unambiguous "
        "evidence for the attribution of an indeterminist concept "
        "of freedom as Frede's presentation suggests."
    ),
    "266_kahn": (
        "One would nevertheless have wished, even for the oral "
        "lecture format, for more precise documentation of some "
        "claims: one example is the failure to mention Charles "
        "Kahn's 1988 article; another is the indeterminist "
        "concept of will that Frede attributes to Alexander, but "
        "of which it is questionable whether it corresponds to "
        "Alexander's own arguments."
    ),
    "266_verdienst": (
        "The merit of Frede's investigation is to substantiate "
        "this new perspective by means of reconstructions and "
        "cross-comparisons of various ancient, late-antique and "
        "imperial-age authors. [...] Frede's interpretations are "
        "particularly suited to bringing ancient positions to "
        "bear as systematically relevant conceptions in current "
        "debates."
    ),
}


def parse_metadata(raw: Any) -> dict[str, Any]:
    if raw is None or raw == "":
        return {}
    if isinstance(raw, dict):
        return raw
    return json.loads(raw)


def node_id_of_line(line: str) -> str:
    return json.loads(line).get("id") or ""


def snapshot() -> None:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(NODES_PATH, SNAPSHOT_DIR / NODES_PATH.name)


def fix_citation_entry(c: dict[str, Any]) -> dict[str, Any]:
    """Migrate a single verified_critiques entry to original+English format."""
    new = {}
    # Preserve standard fields
    for k in ("page", "thesis", "section"):
        if k in c:
            new[k] = c[k]
    # Rename quote_verbatim_de → quote_de
    if "quote_verbatim_de" in c:
        new["quote_de"] = c["quote_verbatim_de"]
    elif "quote_de" in c:
        new["quote_de"] = c["quote_de"]
    # Replace translation_fr with translation_en using lookup
    page = c.get("page")
    section = c.get("section", "")
    key = page
    if page == 266:
        if "Schluss" in section or "Kahn" in c.get("thesis", "") or "verdict" in c.get("thesis", "").lower():
            key = "266_kahn"
        elif "Verdienst" in section or "mérite" in c.get("thesis", "") or "merit" in c.get("thesis", ""):
            key = "266_verdienst"
    eng = ENGLISH_TRANSLATIONS.get(key)
    if eng:
        new["translation_en"] = eng
    elif "translation_en" in c:
        new["translation_en"] = c["translation_en"]
    return new


def main() -> int:
    node_lines = [
        line.rstrip("\n")
        for line in NODES_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    target_idx = None
    for i, ln in enumerate(node_lines):
        if node_id_of_line(ln) == ID_LIENEMANN:
            target_idx = i
            break
    if target_idx is None:
        print(f"ERROR: {ID_LIENEMANN} not found", file=sys.stderr)
        return 2

    node = json.loads(node_lines[target_idx])
    md = parse_metadata(node.get("metadata"))

    if md.get(WAVE_TAG):
        print(f"SKIP {ID_LIENEMANN} (already fixed)")
        return 0

    # 1. Fix verified_critiques entries
    crits = md.get("verified_critiques", [])
    md["verified_critiques"] = [fix_citation_entry(c) for c in crits]

    # 2. Strip French snippet from description (if any) and ensure
    #    description doesn't carry French translations of German quotes.
    desc = node.get("description") or ""
    # Description already has only the German quote inline. Add explicit
    # English translation note for the Sharples-on-Alexander quote since
    # that's the load-bearing citation.
    if "« Sharples rightly remarks" not in desc and "Sharples rightly remarks" not in desc:
        # Append English translation after the German verbatim block
        de_marker = "wie es Fredes Darstellung suggeriert » (p. 260)"
        if de_marker in desc:
            insertion = (
                " — *English: \"Sharples rightly remarks in the appended "
                "endnotes that Alexander himself does not provide such "
                "unambiguous evidence for the attribution of an "
                "indeterminist concept of freedom as Frede's presentation "
                "suggests\"*"
            )
            desc = desc.replace(de_marker, de_marker + insertion, 1)
            node["description"] = desc

    # 3. Marker
    md[WAVE_TAG] = (
        "Citation format fix: translation_fr → translation_en across all "
        "4 verified_critiques entries (per [[citation-original-plus-"
        "english]] standard). quote_verbatim_de renamed to quote_de "
        "for convention consistency. Inline description English "
        "translation added for the load-bearing Sharples-on-Alexander "
        "quote (p. 260)."
    )

    node["metadata"] = json.dumps(md, ensure_ascii=False)
    node["updated_at"] = NOW

    snapshot()
    print(f"snapshot: {SNAPSHOT_DIR}")
    node_lines[target_idx] = json.dumps(node, ensure_ascii=False)
    NODES_PATH.write_text("\n".join(node_lines) + "\n", encoding="utf-8")

    print(f"OK: fixed {ID_LIENEMANN}")
    print(f"   - {len(md['verified_critiques'])} citations migrated to original+English")
    return 0


if __name__ == "__main__":
    sys.exit(main())
