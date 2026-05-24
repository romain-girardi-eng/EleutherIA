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
from urllib.parse import quote

import requests

try:
    # lxml is faster and doesn't depend on the system expat shared library,
    # which is broken on some Python 3.14 builds against macOS libexpat.
    from lxml import etree as _ET_IMPL

    class _ETCompat:
        """Thin shim so the rest of the module uses ET.Element / ET.fromstring."""

        @staticmethod
        def fromstring(data: bytes) -> _ET_IMPL._Element:  # type: ignore[name-defined]
            return _ET_IMPL.fromstring(data)

        Element = _ET_IMPL._Element  # type: ignore[attr-defined]

    ET: _ETCompat = _ETCompat()  # type: ignore[assignment]
except ImportError:
    from xml.etree import ElementTree as ET  # type: ignore[assignment]

CTS_BASE = "https://scaife-cts.perseus.org/api/cts"
SCAIFE_LIBRARY_BASE = "https://scaife.perseus.org/library"
RATE_LIMIT_SECONDS = 0.5

NS_CTS = "http://chs.harvard.edu/xmlns/cts"
NS_TEI = "http://www.tei-c.org/ns/1.0"

GREEK_RE = re.compile(r"[\u0370-\u03FF\u1F00-\u1FFF]")
LATIN_RE = re.compile(r"[a-zA-ZÀ-ÿ]")

SOURCE_AUTO = "auto"
SOURCE_CTS = "cts"
SOURCE_LIBRARY = "library"


def _encode_library_urn(urn: str) -> str:
    return quote(urn, safe=":.-_")


def build_cts_url(
    cts_base: str,
    request: str,
    urn: str | None = None,
    level: int | None = None,
) -> str:
    params = [f"request={request}"]
    if urn is not None:
        params.append(f"urn={quote(urn, safe=':.-_')}")
    if level is not None:
        params.append(f"level={level}")
    return f"{cts_base}?{'&'.join(params)}"


def build_library_reffs_url(library_base: str, urn: str, level: int) -> str:
    encoded = _encode_library_urn(urn)
    return f"{library_base.rstrip('/')}/{encoded}/cts-api-xml/reffs/?level={level}"


def build_library_passage_url(library_base: str, urn: str) -> str:
    encoded = _encode_library_urn(urn)
    return f"{library_base.rstrip('/')}/{encoded}/cts-api-xml/"


def _fetch_xml(url: str) -> ET.Element:
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return ET.fromstring(resp.content)


def _local_name(elem: ET.Element) -> str:
    return elem.tag.rsplit("}", 1)[-1]


def _find_first_by_local_name(root: ET.Element, name: str) -> ET.Element | None:
    for elem in root.iter():
        if _local_name(elem) == name:
            return elem
    return None


def _parse_valid_reff_xml(root: ET.Element) -> list[str]:
    urns: list[str] = []
    for urn_elem in root.iter():
        if _local_name(urn_elem) != "urn":
            continue
        text = (urn_elem.text or "").strip()
        if text:
            urns.append(text)
    return urns


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


def discover_editions(
    work_urn: str,
    *,
    cts_base: str = CTS_BASE,
    library_base: str = SCAIFE_LIBRARY_BASE,
    source: str = SOURCE_AUTO,
) -> None:
    """List available editions for a work URN."""
    if source == SOURCE_LIBRARY:
        print(f"Fetching library references for {work_urn}...")
        _discover_with_valid_reff(work_urn, cts_base, library_base, source)
        return

    url = build_cts_url(cts_base, "GetCapabilities")
    print(f"Fetching capabilities for {work_urn}...")
    try:
        root = _fetch_xml(url)
    except Exception as exc:
        if source == SOURCE_CTS:
            raise
        print(f"  CTS capabilities failed: {exc}")
        print("  Falling back to Scaife library GetValidReff endpoints...")
        _discover_with_valid_reff(work_urn, cts_base, library_base, SOURCE_LIBRARY)
        return

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
        _discover_with_valid_reff(work_urn, cts_base, library_base, source)


def _discover_with_valid_reff(
    work_urn: str,
    cts_base: str,
    library_base: str,
    source: str,
) -> None:
    found = False
    for level in [1, 2, 3]:
        try:
            urns = get_valid_reff(
                work_urn,
                level=level,
                cts_base=cts_base,
                library_base=library_base,
                source=source,
            )
        except Exception:
            continue
        if urns:
            print(f"  GetValidReff level={level}: {len(urns)} refs")
            print(f"    First: {urns[0]}")
            print(f"    Last:  {urns[-1]}")
            found = True
    if not found:
        print(f"  No references found for {work_urn}")


def get_valid_reff(
    work_urn: str,
    level: int = 1,
    *,
    cts_base: str = CTS_BASE,
    library_base: str = SCAIFE_LIBRARY_BASE,
    source: str = SOURCE_AUTO,
) -> list[str]:
    if source in (SOURCE_AUTO, SOURCE_CTS):
        url = build_cts_url(cts_base, "GetValidReff", urn=work_urn, level=level)
        try:
            urns = _parse_valid_reff_xml(_fetch_xml(url))
            if urns or source == SOURCE_CTS:
                return urns
        except Exception:
            if source == SOURCE_CTS:
                raise

    url = build_library_reffs_url(library_base, work_urn, level)
    return _parse_valid_reff_xml(_fetch_xml(url))


def _parse_passage_xml(root: ET.Element, urn: str) -> str:
    passage_elem = root.find(f".//{{{NS_CTS}}}passage")
    if passage_elem is None:
        passage_elem = _find_first_by_local_name(root, "passage")
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


def get_passage(
    urn: str,
    *,
    cts_base: str = CTS_BASE,
    library_base: str = SCAIFE_LIBRARY_BASE,
    source: str = SOURCE_AUTO,
) -> str:
    if source in (SOURCE_AUTO, SOURCE_CTS):
        url = build_cts_url(cts_base, "GetPassage", urn=urn)
        try:
            text = _parse_passage_xml(_fetch_xml(url), urn)
            if text or source == SOURCE_CTS:
                return text
        except Exception:
            if source == SOURCE_CTS:
                raise

    url = build_library_passage_url(library_base, urn)
    return _parse_passage_xml(_fetch_xml(url), urn)


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
    parser.add_argument(
        "--source",
        choices=[SOURCE_AUTO, SOURCE_CTS, SOURCE_LIBRARY],
        default=SOURCE_AUTO,
        help="API source: old CTS, Scaife library, or old CTS with library fallback",
    )
    parser.add_argument("--cts-base", default=CTS_BASE, help=argparse.SUPPRESS)
    parser.add_argument("--library-base", default=SCAIFE_LIBRARY_BASE, help=argparse.SUPPRESS)
    args = parser.parse_args()

    if args.discover:
        discover_editions(
            args.discover,
            cts_base=args.cts_base,
            library_base=args.library_base,
            source=args.source,
        )
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
    print(f"Source: {args.source}")
    print("=" * 60)

    # Step 1: Get all section URNs
    print(f"\n[1/3] Fetching valid references (level={args.level})...")
    urns = get_valid_reff(
        work_urn,
        level=args.level,
        cts_base=args.cts_base,
        library_base=args.library_base,
        source=args.source,
    )
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
            text = get_passage(
                urn,
                cts_base=args.cts_base,
                library_base=args.library_base,
                source=args.source,
            )
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
