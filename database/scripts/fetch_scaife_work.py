#!/usr/bin/env python3
"""
Generic Scaife CTS fetcher for ancient Greek and Latin texts.

Fetches a work from the Perseus/Scaife CTS API, strips TEI XML markup,
validates character ratios, and outputs clean JSON ready for DB ingestion.

Usage:
    # Fetch Nemesius De Natura Hominis
    python database/scripts/fetch_scaife_work.py \
        --urn "urn:cts:greekLit:tlg4090.tlg001.1st1K-grc1" \
        --lang grc \
        --ref-prefix "De Nat. Hom." \
        --output /tmp/nemesius_de_nat_hom.json

    # Fetch with deeper reference levels (e.g., Book.Chapter)
    python database/scripts/fetch_scaife_work.py \
        --urn "urn:cts:greekLit:tlg0059.tlg030.perseus-grc2" \
        --lang grc \
        --ref-prefix "Rep." \
        --level 2 \
        --output /tmp/plato_republic.json

    # List available editions for a work group
    python database/scripts/fetch_scaife_work.py \
        --discover "urn:cts:greekLit:tlg4090.tlg001"
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from xml.etree import ElementTree as ET

import requests

CTS_BASE = "https://scaife-cts.perseus.org/api/cts"
RATE_LIMIT_SECONDS = 0.5

NS_CTS = "http://chs.harvard.edu/xmlns/cts"
NS_TEI = "http://www.tei-c.org/ns/1.0"

GREEK_RE = re.compile(r"[\u0370-\u03FF\u1F00-\u1FFF]")
LATIN_RE = re.compile(r"[a-zA-ZÀ-ÿ]")


def _find_parent(root: ET.Element, target: ET.Element) -> ET.Element | None:
    for parent in root.iter():
        for child in parent:
            if child is target:
                return parent
    return None


def _strip_notes(elem: ET.Element) -> None:
    for note in elem.findall(f".//{{{NS_TEI}}}note"):
        parent = _find_parent(elem, note)
        if parent is not None:
            if note.tail:
                prev = list(parent).index(note) - 1 if list(parent).index(note) > 0 else -1
                if prev >= 0:
                    sibling = list(parent)[prev]
                    sibling.tail = (sibling.tail or "") + note.tail
                else:
                    parent.text = (parent.text or "") + note.tail
            parent.remove(note)


def _extract_text(elem: ET.Element) -> str:
    parts: list[str] = []
    if elem.text:
        parts.append(elem.text)
    for child in elem:
        tag = child.tag.replace(f"{{{NS_TEI}}}", "")
        if tag in ("pb", "lb", "milestone"):
            pass  # skip markers
        elif tag == "gap":
            parts.append("[...]")
        elif tag == "del":
            pass  # skip deleted text
        else:
            parts.append(_extract_text(child))
        if child.tail:
            parts.append(child.tail)
    return "".join(parts)


def clean_text(raw: str) -> str:
    text = re.sub(r"\s+", " ", raw).strip()
    text = re.sub(r"\s+([,;:.\?])", r"\1", text)
    text = re.sub(r"\s+\[\.\.\.\]\s+", " [...] ", text)
    return text


def char_ratio(text: str, lang: str) -> float:
    alpha_chars = [c for c in text if c.isalpha()]
    if not alpha_chars:
        return 0.0
    if lang == "grc":
        count = sum(1 for c in alpha_chars if GREEK_RE.match(c))
    elif lang == "lat":
        count = sum(1 for c in alpha_chars if LATIN_RE.match(c))
    else:
        return 1.0  # skip validation for unknown languages
    return count / len(alpha_chars)


def discover_editions(work_urn: str) -> None:
    """List available editions for a work URN."""
    url = f"{CTS_BASE}?request=GetCapabilities"
    print(f"Fetching capabilities for {work_urn}...")
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    root = ET.fromstring(resp.content)

    # Search for matching work groups
    found = False
    for elem in root.iter():
        urn = elem.attrib.get("urn", "")
        if work_urn in urn:
            label = ""
            for lab in elem.findall(f".//{{{NS_CTS}}}label"):
                label = (lab.text or "").strip()
                break
            print(f"  {urn:70s} {label}")
            found = True

    if not found:
        print(f"  No editions found for {work_urn}")
        # Try GetValidReff as a fallback
        for level in [1, 2, 3]:
            try:
                test_url = f"{CTS_BASE}?request=GetValidReff&urn={work_urn}&level={level}"
                resp = requests.get(test_url, timeout=15)
                if resp.status_code == 200:
                    root = ET.fromstring(resp.content)
                    urns = [u.text.strip() for u in root.iter(f"{{{NS_CTS}}}urn") if u.text]
                    if urns:
                        print(f"  GetValidReff level={level}: {len(urns)} refs")
                        print(f"    First: {urns[0]}")
                        print(f"    Last:  {urns[-1]}")
            except Exception:
                pass


def get_valid_reff(work_urn: str, level: int = 1) -> list[str]:
    url = f"{CTS_BASE}?request=GetValidReff&urn={work_urn}&level={level}"
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
    url = f"{CTS_BASE}?request=GetPassage&urn={urn}"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    root = ET.fromstring(resp.content)

    passage_elem = root.find(f".//{{{NS_CTS}}}passage")
    if passage_elem is None:
        raise ValueError(f"No <passage> element for {urn}")

    tei = passage_elem.find(f".//{{{NS_TEI}}}TEI")
    if tei is None:
        # Fallback: look for body directly
        body = passage_elem.find(f".//{{{NS_TEI}}}body")
        if body is None:
            raise ValueError(f"No <TEI> or <body> element for {urn}")
        _strip_notes(body)
        paragraphs = body.findall(f".//{{{NS_TEI}}}p") or body.findall(f".//{{{NS_TEI}}}l")
        if not paragraphs:
            return clean_text(_extract_text(body))
        texts = [_extract_text(p) for p in paragraphs]
        return clean_text("\n\n".join(texts))

    _strip_notes(tei)
    # Try <p>, <l> (verse lines), or fall back to <div>
    paragraphs = tei.findall(f".//{{{NS_TEI}}}p")
    if not paragraphs:
        paragraphs = tei.findall(f".//{{{NS_TEI}}}l")
    if not paragraphs:
        # Fall back to extracting all text from the body
        body = tei.find(f".//{{{NS_TEI}}}body")
        if body is not None:
            return clean_text(_extract_text(body))
        return clean_text(_extract_text(tei))

    texts = [_extract_text(p) for p in paragraphs]
    return clean_text("\n\n".join(texts))


def extract_ref(urn: str, work_urn: str) -> str:
    """Extract the reference part from a full URN."""
    # The ref is everything after the work URN + ":"
    if ":" in urn:
        parts = urn.rsplit(":", 1)
        if len(parts) == 2:
            return parts[1]
    return urn.replace(work_urn, "").lstrip(":.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch work from Scaife CTS API")
    parser.add_argument("--urn", help="Full edition URN (e.g., urn:cts:greekLit:tlg4090.tlg001.1st1K-grc1)")
    parser.add_argument("--lang", choices=["grc", "lat"], default="grc", help="Expected language")
    parser.add_argument("--ref-prefix", default="", help="Reference prefix (e.g., 'De Nat. Hom.')")
    parser.add_argument("--level", type=int, default=1, help="CTS reference level depth")
    parser.add_argument("--output", help="Output JSON file path")
    parser.add_argument("--discover", help="Discover editions for a work URN")
    parser.add_argument("--min-ratio", type=float, default=0.70, help="Minimum char ratio threshold")
    args = parser.parse_args()

    if args.discover:
        discover_editions(args.discover)
        return

    if not args.urn or not args.output:
        parser.error("--urn and --output are required (or use --discover)")

    work_urn = args.urn
    lang = args.lang
    lang_name = {"grc": "Greek", "lat": "Latin"}.get(lang, lang)

    print("=" * 60)
    print(f"Fetching: {work_urn}")
    print(f"Language: {lang_name}")
    print(f"Level: {args.level}")
    print("=" * 60)

    # Step 1: Get all section URNs
    print(f"\n[1/3] Fetching valid references (level={args.level})...")
    urns = get_valid_reff(work_urn, level=args.level)
    print(f"  Found {len(urns)} sections")

    if not urns:
        print("ERROR: No sections found. Try a different --level or check the URN.")
        sys.exit(1)

    # Step 2: Fetch each section
    print("\n[2/3] Fetching passage texts...")
    sections: list[dict] = []
    errors = 0

    for i, urn in enumerate(urns):
        ref = extract_ref(urn, work_urn)
        canonical_ref = f"{args.ref_prefix} {ref}".strip() if args.ref_prefix else ref

        try:
            text = get_passage(urn)
        except Exception as exc:
            print(f"  ERROR {ref}: {exc}")
            errors += 1
            continue

        word_count = len(text.split())
        char_length = len(text)
        ratio = char_ratio(text, lang)

        sections.append({
            "section_n": i + 1,
            "canonical_ref": canonical_ref,
            "cts_urn": urn,
            "text": text,
            "word_count": word_count,
            "char_length": char_length,
            "char_ratio": round(ratio, 3),
            "language": lang,
        })

        status = "OK" if ratio > args.min_ratio else "WARN"
        if i < 5 or i >= len(urns) - 3 or ratio <= args.min_ratio or word_count < 10:
            print(f"  [{status}] {canonical_ref:20s}: {word_count:4d} words, "
                  f"{char_length:5d} chars, ratio: {ratio:.1%}")
        elif i == 5:
            print(f"  ... ({len(urns) - 8} more sections) ...")

        if i < len(urns) - 1:
            time.sleep(RATE_LIMIT_SECONDS)

    # Step 3: Validate and save
    print("\n[3/3] Validation...")
    warnings = 0
    for s in sections:
        if s["char_ratio"] < args.min_ratio:
            print(f"  WARN: {s['canonical_ref']} has low {lang_name} ratio: {s['char_ratio']:.1%}")
            warnings += 1
        if s["word_count"] < 5:
            print(f"  WARN: {s['canonical_ref']} is very short: {s['word_count']} words")
            warnings += 1

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(sections, f, ensure_ascii=False, indent=2)

    total_words = sum(s["word_count"] for s in sections)
    total_chars = sum(s["char_length"] for s in sections)
    print(f"\n{'=' * 60}")
    print("Summary")
    print(f"{'=' * 60}")
    print(f"  Sections:     {len(sections)}")
    print(f"  Errors:       {errors}")
    print(f"  Total words:  {total_words:,}")
    print(f"  Total chars:  {total_chars:,}")
    print(f"  Warnings:     {warnings}")
    print(f"  Output:       {args.output}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
