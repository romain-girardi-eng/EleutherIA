"""Download classical works as TEI XML from Perseus/OpenGreekAndLatin GitHub repos
and parse them into passage dicts keyed by CTS URN.

Constraints:
- lxml.etree ONLY — pyexpat (stdlib xml) is broken in this Python 3.14 build.
- HTTP via urllib.request (no third-party HTTP library required).
- No database access.
"""
from __future__ import annotations

import re
import urllib.error
import urllib.request
from typing import TYPE_CHECKING

from lxml import etree

if TYPE_CHECKING:
    pass

# ---------------------------------------------------------------------------
# GitHub raw URL helpers
# ---------------------------------------------------------------------------

_PERSEUS_GREEK = (
    "https://raw.githubusercontent.com/PerseusDL/canonical-greekLit/master/data"
)
_FIRST1K_GREEK = (
    "https://raw.githubusercontent.com/OpenGreekAndLatin/First1KGreek/master/data"
)
_PERSEUS_LATIN = (
    "https://raw.githubusercontent.com/PerseusDL/canonical-latinLit/master/data"
)


def _raw_url(base: str, author: str, work: str, version: str) -> str:
    filename = f"{author}.{work}.{version}.xml"
    return f"{base}/{author}/{work}/{filename}"


def github_xml_urls(work_urn: str) -> list[str]:
    """Return ordered candidate raw-GitHub URLs for a work URN.

    URN format: urn:cts:<namespace>:<author>.<work>.<version>
    e.g.        urn:cts:greekLit:tlg0004.tlg001.perseus-grc2

    greekLit:
      - version contains "1st1K" → First1KGreek first, canonical-greekLit second
      - otherwise              → canonical-greekLit first, First1KGreek second
    latinLit → canonical-latinLit only (single URL).
    """
    parts = work_urn.split(":")
    # parts: ["urn", "cts", namespace, "author.work.version"]
    namespace = parts[2]
    tail = parts[3]  # e.g. "tlg0004.tlg001.perseus-grc2"
    tail_parts = tail.split(".", 2)
    author, work, version = tail_parts[0], tail_parts[1], tail_parts[2]

    if namespace == "latinLit":
        return [_raw_url(_PERSEUS_LATIN, author, work, version)]

    # greekLit
    if "1st1K" in version or "1st1k" in version.lower():
        primary, fallback = _FIRST1K_GREEK, _PERSEUS_GREEK
    else:
        primary, fallback = _PERSEUS_GREEK, _FIRST1K_GREEK

    return [
        _raw_url(primary, author, work, version),
        _raw_url(fallback, author, work, version),
    ]


# ---------------------------------------------------------------------------
# HTTP fetch
# ---------------------------------------------------------------------------

def fetch_work_xml(work_urn: str) -> bytes:
    """Fetch raw TEI XML bytes for *work_urn*, trying candidate URLs in order.

    Raises urllib.error.URLError if no candidate succeeds.
    """
    candidates = github_xml_urls(work_urn)
    last_exc: Exception | None = None
    for url in candidates:
        try:
            with urllib.request.urlopen(url, timeout=30) as resp:
                if resp.status == 200:
                    return resp.read()
        except urllib.error.HTTPError as exc:
            last_exc = exc
            continue
        except urllib.error.URLError as exc:
            last_exc = exc
            continue
    raise urllib.error.URLError(
        f"All candidate URLs failed for {work_urn!r}. Last error: {last_exc}"
    )


# ---------------------------------------------------------------------------
# TEI XML parser
# ---------------------------------------------------------------------------

# TEI namespace
_TEI_NS = "http://www.tei-c.org/ns/1.0"
_NS = {"tei": _TEI_NS}

# Tags to strip (remove element + all its descendants from text)
_STRIP_TAGS = {
    f"{{{_TEI_NS}}}{tag}"
    for tag in ("note", "bibl", "head", "milestone", "gap", "del", "supplied",
                "abbr", "expan", "ex", "am", "app", "rdg", "lem")
}


def _iter_numbered_divs(parent: etree._Element) -> list[etree._Element]:
    """Return direct children that are numbered <div> elements."""
    return [
        ch for ch in parent
        if ch.tag == f"{{{_TEI_NS}}}div" and ch.get("n") is not None
    ]


def _iter_lines(parent: etree._Element) -> list[etree._Element]:
    """Return direct <l> children with @n."""
    return [
        ch for ch in parent
        if ch.tag == f"{{{_TEI_NS}}}l" and ch.get("n") is not None
    ]


def _collect_text(element: etree._Element) -> str:
    """Extract visible text from *element*, skipping stripped-tag descendants.

    Uses a simple recursive walk so we never touch pyexpat-based APIs.
    """
    parts: list[str] = []

    def _walk(el: etree._Element) -> None:
        if el.tag in _STRIP_TAGS:
            # Include tail text (text after the closing tag) but skip content
            if el.tail:
                parts.append(el.tail)
            return
        if el.text:
            parts.append(el.text)
        for child in el:
            _walk(child)
        if el.tail:
            parts.append(el.tail)

    # Walk children of the element (not the element's own text via _walk,
    # since _walk also appends el.tail which we don't want at root level)
    if element.text:
        parts.append(element.text)
    for child in element:
        _walk(child)

    # Collapse whitespace
    text = re.sub(r"\s+", " ", "".join(parts)).strip()
    return text


def _citation_depth(root: etree._Element) -> int:
    """Count cRefPattern entries in refsDecl to determine citation depth."""
    patterns = root.findall(".//tei:refsDecl[@n='CTS']/tei:cRefPattern", _NS)
    if not patterns:
        # Fallback: try without namespace or without n=CTS
        patterns = root.findall(".//tei:refsDecl/tei:cRefPattern", _NS)
    return max(len(patterns), 1)


def _find_content_root(root: etree._Element) -> etree._Element | None:
    """Return the element whose direct children are the first citation level.

    TEI structure: <text><body>[<div type="edition"|"textpart">*]<div n="1">...

    We skip unnumbered wrapper divs (type="edition", type="translation", etc.)
    and descend until we reach an element whose numbered-div children are the
    first level of citation (@type="textpart" or simply having @n).

    If the body has *only* a single child div with @n set to a non-numeric
    string (like "work", "poem") — a work-level wrapper — we descend into it.
    """
    body = root.find(".//tei:text/tei:body", _NS)
    if body is None:
        return None

    def _descend(el: etree._Element) -> etree._Element:
        div_children = [ch for ch in el if ch.tag == f"{{{_TEI_NS}}}div"]
        if not div_children:
            return el
        # All children numbered → this is the content root
        numbered = [ch for ch in div_children if ch.get("n") is not None]
        if numbered:
            # Check if the numbered children look like citation divs
            # (they have @type="textpart" or contain numbered sub-divs / lines)
            # vs. a single non-numeric wrapper (e.g. n="work", n="poem")
            if len(numbered) == 1:
                n_val = numbered[0].get("n", "")
                # Non-numeric single child → it's a wrapper, descend into it
                if not n_val.lstrip("-").isdigit():
                    return _descend(numbered[0])
            return el
        # No numbered children → unnumbered wrappers, descend into first
        return _descend(div_children[0])

    return _descend(body)


def _walk_to_depth(
    el: etree._Element,
    depth: int,
    current_depth: int,
    ref_parts: list[str],
    results: list[dict],
    work_urn: str,
) -> None:
    """Recursively walk div tree, collecting passages at *depth*.

    depth=1 → numbered <div> children of content_root.
    depth=2 → their numbered <div> children, etc.
    At the leaf depth, also checks for <l> elements if no numbered divs found.
    """
    if current_depth == depth:
        text = _collect_text(el)
        if text:
            ref = ".".join(ref_parts)
            results.append({
                "cts_urn": f"{work_urn}:{ref}",
                "text_content": text,
            })
        return

    # Try numbered <div> children
    children = _iter_numbered_divs(el)
    if children:
        for child in children:
            n = child.get("n", "")
            _walk_to_depth(
                child, depth, current_depth + 1, ref_parts + [n], results, work_urn
            )
        return

    # At this depth level, if no divs but there are <l> lines, treat them as leaves
    if current_depth == depth - 1:
        lines = _iter_lines(el)
        if lines:
            for line in lines:
                n = line.get("n", "")
                text = _collect_text(line)
                if text:
                    ref = ".".join(ref_parts + [n])
                    results.append({
                        "cts_urn": f"{work_urn}:{ref}",
                        "text_content": text,
                    })
            return

    # No children found: collect this element's text as a leaf if non-empty
    text = _collect_text(el)
    if text:
        ref = ".".join(ref_parts)
        results.append({
            "cts_urn": f"{work_urn}:{ref}",
            "text_content": text,
        })


def parse_passages(
    xml_bytes: bytes,
    work_urn: str,
    level: int | None = None,
) -> list[dict]:
    """Parse TEI XML bytes into a list of passage dicts.

    Each dict has:
      - "cts_urn": "{work_urn}:{ref}" where ref is the dotted @n path
      - "text_content": cleaned passage text (TEI noise stripped, whitespace collapsed)

    Args:
        xml_bytes: Raw TEI XML.
        work_urn:  CTS work URN (without trailing colon/ref).
        level:     Citation depth override. None → read from refsDecl.

    Returns:
        List of passage dicts in document order, only non-empty texts.
    """
    # Parse with lxml (bundles its own expat — safe on broken pyexpat builds)
    parser = etree.XMLParser(recover=True, encoding="utf-8")
    root = etree.fromstring(xml_bytes, parser)

    depth = level if level is not None else _citation_depth(root)

    results: list[dict] = []

    content_root = _find_content_root(root)
    if content_root is None:
        return []

    _walk_to_depth(content_root, depth, 0, [], results, work_urn)
    return results


# ---------------------------------------------------------------------------
# High-level convenience
# ---------------------------------------------------------------------------

def fetch_work_passages(
    work_urn: str,
    level: int | None = None,
) -> list[dict]:
    """Fetch and parse a classical work into passage dicts.

    Combines fetch_work_xml + parse_passages. No database access.
    """
    xml_bytes = fetch_work_xml(work_urn)
    return parse_passages(xml_bytes, work_urn, level=level)
