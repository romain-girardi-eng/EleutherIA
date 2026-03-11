"""Fetch Alexander of Aphrodisias, De Fato (39 chapters) from Scaife CTS API.

Outputs clean Greek text to /tmp/de_fato_clean_sections.json.

Usage:
    python database/scripts/fetch_de_fato_cts.py
"""

from __future__ import annotations

import json
import re
import sys
import time
from xml.etree import ElementTree as ET

import requests

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CTS_BASE = "https://scaife-cts.perseus.org/api/cts"
WORK_URN = "urn:cts:greekLit:tlg0732.tlg014.1st1K-grc1"
OUTPUT_PATH = "/tmp/de_fato_clean_sections.json"
RATE_LIMIT_SECONDS = 0.5

# CTS / TEI namespaces
NS_CTS = "http://chs.harvard.edu/xmlns/cts"
NS_TEI = "http://www.tei-c.org/ns/1.0"

# Bruns page ranges per section (approximation from the 1892 Supplementum Aristotelicum edition)
# Sections map to Bruns pages 164-212
BRUNS_START = 164
BRUNS_END = 212

# Greek Unicode range (Greek + Greek Extended blocks)
GREEK_RE = re.compile(r"[\u0370-\u03FF\u1F00-\u1FFF]")


# ---------------------------------------------------------------------------
# XML Cleaning
# ---------------------------------------------------------------------------

def _strip_notes(elem: ET.Element) -> None:
    """Remove <note> elements (footnotes, marginal markers) in-place."""
    for note in elem.findall(f".//{{{NS_TEI}}}note"):
        parent = _find_parent(elem, note)
        if parent is not None:
            # Preserve tail text
            if note.tail:
                prev = list(parent).index(note) - 1 if list(parent).index(note) > 0 else -1
                if prev >= 0:
                    sibling = list(parent)[prev]
                    sibling.tail = (sibling.tail or "") + note.tail
                else:
                    parent.text = (parent.text or "") + note.tail
            parent.remove(note)


def _find_parent(root: ET.Element, target: ET.Element) -> ET.Element | None:
    """Find parent of *target* within *root* (ElementTree has no parent map)."""
    for parent in root.iter():
        for child in parent:
            if child is target:
                return parent
    return None


def _extract_text(elem: ET.Element) -> str:
    """Recursively extract text from a TEI element, applying tag-specific rules.

    Rules:
    - <note>           → already removed by _strip_notes
    - <pb n="N"/>      → skip (page break marker)
    - <lb n="N"/>      → skip (line break marker)
    - <gap reason="omitted"/>  → "[...]"
    - <add cause="omitted">   → keep inner text
    - <del>            → skip entirely
    - <sic>            → keep inner text
    - all other tags   → keep inner text
    """
    parts: list[str] = []

    if elem.text:
        parts.append(elem.text)

    for child in elem:
        tag = child.tag.replace(f"{{{NS_TEI}}}", "")

        if tag == "pb":
            # Skip page break; preserve tail
            pass
        elif tag == "lb":
            # Skip line break; preserve tail
            pass
        elif tag == "gap":
            parts.append("[...]")
        elif tag == "del":
            # Skip deleted text entirely
            pass
        elif tag in ("add", "sic", "p", "div", "seg", "hi", "q", "said"):
            # Keep inner text
            parts.append(_extract_text(child))
        else:
            # Default: keep inner text
            parts.append(_extract_text(child))

        # Tail text after this child element
        if child.tail:
            parts.append(child.tail)

    return "".join(parts)


def clean_text(raw: str) -> str:
    """Post-process extracted text: normalise whitespace."""
    text = re.sub(r"\s+", " ", raw).strip()
    # Clean up spaces before punctuation
    text = re.sub(r"\s+([,;:.\?])", r"\1", text)
    # Clean up double spaces around [...]
    text = re.sub(r"\s+\[\.\.\.\]\s+", " [...] ", text)
    return text


# ---------------------------------------------------------------------------
# CTS API Helpers
# ---------------------------------------------------------------------------

def get_valid_reff() -> list[str]:
    """Call GetValidReff to retrieve all section URNs."""
    url = f"{CTS_BASE}?request=GetValidReff&urn={WORK_URN}&level=1"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()

    root = ET.fromstring(resp.content)
    urns: list[str] = []
    for urn_elem in root.iter(f"{{{NS_CTS}}}urn"):
        text = (urn_elem.text or "").strip()
        if text:
            urns.append(text)
    return urns


def get_passage(urn: str) -> str:
    """Call GetPassage and return cleaned Greek text."""
    url = f"{CTS_BASE}?request=GetPassage&urn={urn}"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()

    root = ET.fromstring(resp.content)

    # Navigate: <reply> → <passage> → <TEI> → <text> → <body> → <div> → <div> → <p>
    passage_elem = root.find(f".//{{{NS_CTS}}}passage")
    if passage_elem is None:
        raise ValueError(f"No <passage> element found for {urn}")

    tei = passage_elem.find(f".//{{{NS_TEI}}}TEI")
    if tei is None:
        raise ValueError(f"No <TEI> element found for {urn}")

    # Remove notes first (in-place)
    _strip_notes(tei)

    # Find the <p> elements within the textpart div
    paragraphs = tei.findall(f".//{{{NS_TEI}}}p")
    if not paragraphs:
        raise ValueError(f"No <p> elements found for {urn}")

    # Extract and join paragraph texts
    texts = [_extract_text(p) for p in paragraphs]
    raw = "\n\n".join(texts)
    return clean_text(raw)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def greek_char_ratio(text: str) -> float:
    """Fraction of alphabetic characters that are Greek."""
    alpha_chars = [c for c in text if c.isalpha()]
    if not alpha_chars:
        return 0.0
    greek_count = sum(1 for c in alpha_chars if GREEK_RE.match(c))
    return greek_count / len(alpha_chars)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("Fetching Alexander of Aphrodisias, De Fato")
    print(f"Source: {CTS_BASE}")
    print(f"Work URN: {WORK_URN}")
    print("=" * 60)

    # Step 1: Get all section URNs
    print("\n[1/3] Fetching valid references...")
    urns = get_valid_reff()
    print(f"  Found {len(urns)} sections")
    if len(urns) != 39:
        print(f"  WARNING: Expected 39 sections, got {len(urns)}")

    # Step 2: Fetch each section
    print("\n[2/3] Fetching passage texts...")
    sections: list[dict] = []
    pages_per_section = (BRUNS_END - BRUNS_START) / len(urns)

    for i, urn in enumerate(urns):
        section_n = i + 1
        bruns_start = int(BRUNS_START + i * pages_per_section)
        bruns_end = int(BRUNS_START + (i + 1) * pages_per_section)
        bruns_pages = f"{bruns_start}-{bruns_end}"

        try:
            greek_text = get_passage(urn)
        except Exception as exc:
            print(f"  ERROR section {section_n}: {exc}")
            sys.exit(1)

        word_count = len(greek_text.split())
        char_length = len(greek_text)
        ratio = greek_char_ratio(greek_text)

        sections.append({
            "section_n": section_n,
            "canonical_ref": f"De Fato {section_n}",
            "cts_urn": urn,
            "bruns_pages": bruns_pages,
            "greek_text": greek_text,
            "word_count": word_count,
            "char_length": char_length,
            "greek_ratio": round(ratio, 3),
        })

        status = "OK" if ratio > 0.85 else "WARN"
        print(f"  [{status}] Section {section_n:2d}: {word_count:4d} words, "
              f"{char_length:5d} chars, Greek ratio: {ratio:.1%}")

        if i < len(urns) - 1:
            time.sleep(RATE_LIMIT_SECONDS)

    # Step 3: Validate and save
    print("\n[3/3] Validation...")
    warnings = 0
    for s in sections:
        if s["greek_ratio"] < 0.85:
            print(f"  WARN: Section {s['section_n']} has low Greek ratio: "
                  f"{s['greek_ratio']:.1%}")
            warnings += 1
        if s["word_count"] < 10:
            print(f"  WARN: Section {s['section_n']} is very short: "
                  f"{s['word_count']} words")
            warnings += 1

    # Save JSON
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(sections, f, ensure_ascii=False, indent=2)

    # Summary
    total_words = sum(s["word_count"] for s in sections)
    total_chars = sum(s["char_length"] for s in sections)
    print(f"\n{'=' * 60}")
    print("Summary")
    print(f"{'=' * 60}")
    print(f"  Sections:     {len(sections)}")
    print(f"  Total words:  {total_words:,}")
    print(f"  Total chars:  {total_chars:,}")
    print(f"  Warnings:     {warnings}")
    print(f"  Output:       {OUTPUT_PATH}")
    print(f"{'=' * 60}")

    if warnings > 0:
        print("\nReview warnings before proceeding to Phase 3.")


if __name__ == "__main__":
    main()
