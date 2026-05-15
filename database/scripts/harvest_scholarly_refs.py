"""Harvest scholarly reference→source-locus pairs from local DOCTORAT library.

Scans .md and .txt summaries for citations of canonical fragment collections
(SVF, LS, DK, Usener, Edelstein-Kidd, Marcovich) and stores the surrounding
~200-char context so a cross-linker can later identify which KG passage each
ref maps to.

Output: data/doxographical_audit/scholarly_refs_index.json
   {
     "SVF I 216": [
       {"file": "...", "context": "...Stobée, Eclog. II, 7, 11g... (SVF I, 216)..."},
       ...
     ],
     ...
   }
"""

from __future__ import annotations

import json
import logging
import re
from collections import defaultdict
from pathlib import Path

logger = logging.getLogger("harvest_scholarly_refs")

DOCROOT = Path(
    "[local-path] SHAL/04_Littérature_secondaire"
)
OUTPUT = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "doxographical_audit"
    / "scholarly_refs_index.json"
)

# Regex set keyed by collection. Capture groups are full match → normalized later.
PATTERNS: dict[str, re.Pattern[str]] = {
    "SVF": re.compile(r"SVF\s*[,]?\s*([IVXLCDM]+)[\.,\s]+(\d+[a-z]?)"),
    "LS": re.compile(r"\bLS\s*(\d+)\s*([A-Z])\b"),
    "DK": re.compile(r"DK\s*(\d+)\s*([AB])\s*(\d+)"),
    "Usener": re.compile(r"Usener\s+(\d+)"),
    "EK": re.compile(r"\bEK\s*F?(\d+)"),
    "Marcovich": re.compile(r"Marcovich[^a-z]*(\d+)"),
    "Wehrli": re.compile(r"Wehrli[^a-z]*(\d+)"),
    "FHSG": re.compile(r"FHSG\s*(\d+)"),
    "Diels-Aetius": re.compile(r"Aet(?:ius|\.)\s+([IVX]+)\.(\d+)\.(\d+)"),
}

CONTEXT_RADIUS = 200


def normalize_ref(collection: str, m: re.Match[str]) -> str:
    if collection == "SVF":
        return f"SVF {m.group(1)}.{m.group(2)}"
    if collection == "LS":
        return f"LS {m.group(1)}{m.group(2)}"
    if collection == "DK":
        return f"DK {m.group(1)}{m.group(2)}{m.group(3)}"
    if collection == "Usener":
        return f"Usener {m.group(1)}"
    if collection == "EK":
        return f"EK F{m.group(1)}"
    if collection == "Marcovich":
        return f"Marcovich {m.group(1)}"
    if collection == "Wehrli":
        return f"Wehrli {m.group(1)}"
    if collection == "FHSG":
        return f"FHSG {m.group(1)}"
    if collection == "Diels-Aetius":
        return f"Aet. {m.group(1)}.{m.group(2)}.{m.group(3)}"
    return m.group(0)


def slice_context(text: str, start: int, end: int, radius: int = CONTEXT_RADIUS) -> str:
    a = max(0, start - radius)
    b = min(len(text), end + radius)
    return " ".join(text[a:b].split())  # collapse whitespace


def harvest(docroot: Path = DOCROOT) -> dict[str, list[dict[str, str]]]:
    index: dict[str, list[dict[str, str]]] = defaultdict(list)
    files = list(docroot.rglob("*.md")) + list(docroot.rglob("*.txt"))
    logger.info("Scanning %d files under %s", len(files), docroot)

    for fp in files:
        try:
            text = fp.read_text(encoding="utf-8", errors="ignore")
        except OSError, UnicodeDecodeError:
            continue
        if not text:
            continue
        for collection, pat in PATTERNS.items():
            for m in pat.finditer(text):
                ref = normalize_ref(collection, m)
                ctx = slice_context(text, m.start(), m.end())
                rel = str(fp.relative_to(docroot))
                index[ref].append(
                    {"file": rel, "context": ctx, "collection": collection}
                )

    # Deduplicate identical (file, context) pairs per ref
    pruned: dict[str, list[dict[str, str]]] = {}
    for ref, hits in index.items():
        seen: set[tuple[str, str]] = set()
        unique: list[dict[str, str]] = []
        for h in hits:
            key = (h["file"], h["context"][:80])
            if key in seen:
                continue
            seen.add(key)
            unique.append(h)
        pruned[ref] = unique
    return pruned


def main() -> int:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    idx = harvest()
    total_hits = sum(len(v) for v in idx.values())
    by_coll: dict[str, int] = defaultdict(int)
    for _ref, hits in idx.items():
        for h in hits:
            by_coll[h["collection"]] += 1
    OUTPUT.write_text(json.dumps(idx, ensure_ascii=False, indent=1, sort_keys=True))
    logger.info(
        "Wrote %d distinct refs (%d total hits) to %s", len(idx), total_hits, OUTPUT
    )
    logger.info("Breakdown by collection: %s", dict(by_coll))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
