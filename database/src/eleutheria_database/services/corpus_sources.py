"""Fallback corpus loaders for non-Scaife primary-text sources.

The Scaife CTS API is still the preferred source when it is reachable, but
the publication corpus cannot depend on one TLS endpoint. This module emits
the same ``ScaifePayload`` shape as the Scaife service so downstream ingestion
remains idempotent and unchanged.

Supported fallbacks:
- PHI Latin Texts (latin.packhum.org) for public Latin literary texts.
- JSON mirror manifests for institutionally exported TLG, Stoa plain text,
  PG/PL OCR, or any other source that has already been normalized offline.
"""

from __future__ import annotations

import json
import re
import urllib.request
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

PHI_BASE = "https://latin.packhum.org"
DEFAULT_TIMEOUT_SECONDS = 30

PHI_REF_RE = re.compile(r"^(?:fr)?\d+(?:\.\d+)+$", re.I)
LOCINFO_RE = re.compile(r"var\s+locInfo\s*=\s*(\{.*?\})\s*;", re.S)


class PhiSection(dict):
    """Typed-by-convention section dictionary used before Scaife dataclasses."""


class _PhiTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[tuple[str, str]] = []
        self._in_td = False
        self._current_cell: list[str] = []
        self._current_row: list[str] = []

    def handle_starttag(self, tag: str, _attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "tr":
            self._current_row = []
        elif tag.lower() == "td":
            self._in_td = True
            self._current_cell = []

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "td" and self._in_td:
            text = " ".join("".join(self._current_cell).split())
            self._current_row.append(unescape(text))
            self._current_cell = []
            self._in_td = False
        elif tag == "tr" and self._current_row:
            left = self._current_row[0] if self._current_row else ""
            right = self._current_row[1] if len(self._current_row) > 1 else ""
            if left or right:
                self.rows.append((left, right))
            self._current_row = []

    def handle_data(self, data: str) -> None:
        if self._in_td:
            self._current_cell.append(data)


def _read_resource(uri: str, timeout: int = DEFAULT_TIMEOUT_SECONDS) -> str:
    if uri.startswith(("http://", "https://")):
        req = urllib.request.Request(
            uri,
            headers={
                "Accept": "text/html,application/json,text/plain",
                "User-Agent": "EleutherIA-CorpusLoader/1.0",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    return Path(uri).expanduser().read_text(encoding="utf-8")


def parse_phi_pages(html: str) -> list[str]:
    """Extract PHI pagination labels from a `/loc/<author>/<work>/0` page."""
    match = LOCINFO_RE.search(html)
    if not match:
        return ["0"]
    data = json.loads(match.group(1))
    pages = data.get("pages")
    return [str(p) for p in pages] if isinstance(pages, list) and pages else ["0"]


def parse_phi_text_table(html: str) -> list[tuple[str, str]]:
    parser = _PhiTableParser()
    parser.feed(html)
    return parser.rows


def sections_from_phi_rows(rows: list[tuple[str, str]]) -> list[PhiSection]:
    """Chunk PHI table rows into citation-level sections.

    PHI places the running citation in the right column only when a new
    section begins; subsequent rows usually carry line numbers or blanks.
    """
    sections: list[PhiSection] = []
    current_ref: str | None = None
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_ref, current_lines
        if current_ref and current_lines:
            text = " ".join(" ".join(current_lines).split())
            if text:
                sections.append(PhiSection(canonical_ref=current_ref, text=text))
        current_ref = None
        current_lines = []

    for left, right in rows:
        if not left:
            continue
        marker = right.strip()
        if PHI_REF_RE.match(marker):
            flush()
            current_ref = marker
            current_lines = [left]
        elif current_ref:
            current_lines.append(left)

    flush()
    return sections


def _section_to_dataclass(
    *,
    section: dict[str, Any],
    section_n: int,
    work_urn: str,
    language: str,
    ref_prefix: str,
    source_name: str,
):
    from eleutheria_database.services.scaife import ScaifeSection, char_ratio

    raw_ref = str(section.get("canonical_ref") or section.get("ref") or section_n)
    canonical_ref = f"{ref_prefix} {raw_ref}".strip() if ref_prefix else raw_ref
    text = str(section.get("text") or section.get("text_content") or "").strip()
    cts_urn = str(section.get("cts_urn") or "")
    if not cts_urn:
        cts_urn = f"{work_urn}:{raw_ref}" if work_urn.startswith("urn:") else raw_ref
    return ScaifeSection(
        section_n=section_n,
        canonical_ref=canonical_ref,
        cts_urn=cts_urn,
        text=text,
        word_count=len(text.split()),
        char_length=len(text),
        char_ratio=round(char_ratio(text, language), 3),
        language=language,
        source_name=source_name,
    )


def fetch_phi_latin_work(
    *,
    work_urn: str,
    author_num: int | str,
    work_num: int | str,
    ref_prefix: str = "",
    base_url: str = PHI_BASE,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
):
    """Fetch a PHI Latin work and return a Scaife-compatible payload."""
    from eleutheria_database.services.scaife import ScaifePayload

    base = base_url.rstrip("/")
    loc_html = _read_resource(f"{base}/loc/{author_num}/{work_num}/0", timeout=timeout)
    pages = parse_phi_pages(loc_html)

    sections: list[dict[str, Any]] = []
    seen_refs: set[str] = set()
    for page_idx, _page_label in enumerate(pages):
        html = _read_resource(
            f"{base}/dx/text/{author_num}/{work_num}/{page_idx}",
            timeout=timeout,
        )
        for section in sections_from_phi_rows(parse_phi_text_table(html)):
            ref = str(section["canonical_ref"])
            if ref in seen_refs:
                continue
            seen_refs.add(ref)
            sections.append(section)

    dataclass_sections = [
        _section_to_dataclass(
            section=section,
            section_n=i + 1,
            work_urn=work_urn,
            language="lat",
            ref_prefix=ref_prefix,
            source_name="phi_latin_texts",
        )
        for i, section in enumerate(sections)
    ]
    return ScaifePayload(
        work_urn=work_urn,
        language="lat",
        ref_prefix=ref_prefix,
        level=1,
        sections=dataclass_sections,
        errors=0,
        source_name="phi_latin_texts",
        source_url=f"{base}/loc/{author_num}/{work_num}/0",
    )


def fetch_json_mirror_work(
    *,
    work_urn: str,
    uri: str,
    language: str,
    ref_prefix: str = "",
    source_name: str = "json_mirror",
):
    """Load a normalized JSON mirror manifest.

    Accepted shapes:
    - ``[{canonical_ref/ref, text/text_content, cts_urn?}, ...]``
    - ``{"sections": [...], "source_name": "...", "source_url": "..."}``
    """
    from eleutheria_database.services.scaife import ScaifePayload

    raw = json.loads(_read_resource(uri))
    if isinstance(raw, dict):
        raw_sections = raw.get("sections") or []
        source_name = str(raw.get("source_name") or source_name)
        source_url = str(raw.get("source_url") or uri)
    else:
        raw_sections = raw
        source_url = uri
    if not isinstance(raw_sections, list):
        raise ValueError("JSON mirror must contain a list of sections")

    sections = [
        _section_to_dataclass(
            section=section,
            section_n=i + 1,
            work_urn=work_urn,
            language=language,
            ref_prefix=ref_prefix,
            source_name=source_name,
        )
        for i, section in enumerate(raw_sections)
        if isinstance(section, dict)
    ]
    return ScaifePayload(
        work_urn=work_urn,
        language=language,
        ref_prefix=ref_prefix,
        level=1,
        sections=sections,
        errors=0,
        source_name=source_name,
        source_url=source_url,
    )


__all__ = [
    "PHI_BASE",
    "fetch_json_mirror_work",
    "fetch_phi_latin_work",
    "parse_phi_pages",
    "parse_phi_text_table",
    "sections_from_phi_rows",
]
