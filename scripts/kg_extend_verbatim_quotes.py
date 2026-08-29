#!/usr/bin/env python3
"""Extend audited scholarly-argument nodes with a long verbatim extract.

Every node of ``data/kg/nodes.jsonl`` whose metadata carries a
``scholarly_audit`` block (audit waves 1-2) cites its evidence as
``[<file.md>:<line>-<line>] (Author YEAR, p. NN)``.  This script re-opens the
cited markdown extraction in the thesis fonds, locates the evidence quote,
expands it to the enclosing argumentative unit (the paragraph, then the
neighbouring paragraphs) and records the extract with its printed pages.

Hard rules enforced here:

* a verbatim extract never exceeds ``MAX_WORDS`` (500) words, counted after
  whitespace normalisation; when the unit is longer, the extract is cut at a
  sentence boundary below the cap;
* the extract never crosses a section heading, never includes footnote blocks
  (unless the evidence itself is a footnote), running heads or download
  banners, and stays within one printed page of the anchor page;
* the text is a copy of the file (NFC, line-wrap hyphenation joined); no
  character is "fixed";
* printed pages come from ``page_map.json`` through the fonds' canonical
  accessor ``page_map_io.citation_for_line`` — never from the PDF index.

Deterministic, no model call. Dry-run by default: it writes a preview JSON and
a markdown summary; ``--apply`` rewrites ``nodes.jsonl`` (unchanged lines are
kept byte for byte).  ``--manifest`` also emits a secondary-evidence manifest
for ``scripts/ingest_secondary_evidence_manifest.py``.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import statistics
import sys
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
NODES_PATH = REPO_ROOT / "data" / "kg" / "nodes.jsonl"
OUT_DIR = REPO_ROOT / "data" / "quality" / "kg_scholarly_audit"
DEFAULT_THESIS_ROOT = Path(
    os.environ.get(
        "ELEUTHERIA_THESIS_ROOT",
        "/Users/romaingirardi/Desktop/DOCTORAT/Doctorat SHAL",
    )
)
LIT_SUBDIR = "04_Littérature_secondaire"
STAMP = "2026-08-29"

MAX_WORDS = 500
MIN_WORDS = 40
PAGE_WINDOW = 1  # the extract may spill onto the previous / next page only
MIN_PAGE_CONFIDENCE = 0.90
TWO_COLUMN_MAX_RATIO = 0.22
GARBLED_MAX_RATIO = 0.20
NATIVE_METHODS = frozenset(
    {"native", "native_pymupdf_page_preserving", "text_pdf_pymupdf"}
)
SKIP_DIR_PARTS = frozenset({"_duplicates", "11_Archives"})  # plus hidden dirs
CURATED_MARKERS = ("Extractions_articles/", "EXTRACTION")

MANIFEST_SCHEMA_VERSION = "1.0.0"
REVIEWED = "reviewed"  # the only review_status the verifier treats as reviewed

_BANNER_RES = (
    re.compile(r"Downloaded from Brill\.com.*$"),
    re.compile(r"via Universit[ée] de Nice.*$"),
    re.compile(r"This content downloaded from.*$"),
    re.compile(r"All use subject to https?://about\.jstor\.org/terms.*$"),
    re.compile(r"https?://www\.jstor\.org/\S+.*$"),
    re.compile(r"^\s*Brought to you by \|.*$"),
    re.compile(r"^\s*Authenticated\s*$"),
    re.compile(r"^\s*Download Date \|.*$"),
    re.compile(r"^\d{7}\. \(Brill: \d+\).*page \d+\.$"),
    re.compile(r".*is collaborating with JSTOR to digitize.*$"),
    re.compile(r"^\s*(?:Stable URL|Accessed|Published by|Source|Author\(s\)):.*$"),
    re.compile(r"^\s*JSTOR is a not-for-profit service.*$"),
    re.compile(r"^\s*Your use of the JSTOR archive indicates.*$"),
    re.compile(r"^\s*https?://about\.jstor\.org/terms\s*$"),
)
_COVER_PAGE_RE = re.compile(
    r"JSTOR is a not-for-profit service|Stable URL: https?://www\.jstor\.org"
)
_SECTION_WORDS_RE = re.compile(
    r"^\s*(?:pour en savoir plus|bibliograph(?:ie|y)|references|notes|literatur"
    r"(?:verzeichnis)?|conclusions?|introduction|r[ée]sum[ée]|abstract|summary"
    r"|appendix|anmerkungen|sources|index|zusammenfassung|works cited"
    r"|select(?:ed)? bibliography|further reading|abbreviations)\b",
    re.IGNORECASE,
)
_FOOTNOTE_START_RE = re.compile(
    r"^\s{0,24}(\d{1,3})(?:[.)]?[\t    ]+\S|[\t ]\s*$|(?<=\d\d)(?=[A-Z][a-z]{3,}))"
)
_SECTION_NUMBER_RE = re.compile(r"^\s*(?:\d+(?:\.\d+)+\.?|[IVXLC]+\.)\s*$")
_ROMAN_RE = re.compile(r"^\s*([ivxlcdm]{1,7})\s*$", re.IGNORECASE)
_PURE_NUMBER_RE = re.compile(r"^\s*(?:\d{1,4}|[ivxlcdm]{1,7}|[IVXLCDM]{1,7})\s*$")
_TERMINAL_RE = re.compile(r"[.!?:;»”\"'’)\]]\s*$")
_HEADING_NUMBERED_RE = re.compile(
    r"^\s*(?:#{1,6}\s+|(?:\d+(?:\.\d+)*\.?|[IVXLC]+\.|[A-Z]\.)\s+)(?=[A-ZÀ-Ý«\"“])"
)
_SENTENCE_END_RE = re.compile(r"(?<=[.!?])[\"'”’)\]]*\s+(?=[A-ZÀ-Ý«“\"'‘0-9])")
_CITATION_RE = re.compile(r"\[(.+?\.(?:md|txt)):(\d+)(?:-(\d+))?\]")
_WORD_RE = re.compile(r"\S+")


# ---------------------------------------------------------------------------
# Text normalisation
# ---------------------------------------------------------------------------


def word_count(text: str) -> int:
    return len(_WORD_RE.findall(text))


def _fold(text: str) -> str:
    """Search key: NFC, typographic quotes folded, hyphenation and markup gone."""
    text = unicodedata.normalize("NFC", text)
    text = text.replace("­", "")
    text = re.sub(r"\*\*|__|\*", "", text)
    text = (
        text.replace("‘", "'")
        .replace("’", "'")
        .replace("“", '"')
        .replace("”", '"')
        .replace("«", '"')
        .replace("»", '"')
        .replace("–", "-")
        .replace("—", "-")
    )
    text = re.sub(r"(\w)-\s*(?=\w)", r"\1", text)  # hyphenation / compounds
    text = re.sub(r"[   \t]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


def join_lines(lines: list[str], compounds: set[str] | None = None) -> str:
    """Join physical lines into flowing text; hyphenated line ends are mended.

    A line-end hyphen is kept when the file itself attests the hyphenated
    compound inside a line (``two-ways``); otherwise the word is re-joined.
    """
    out = ""
    for raw in lines:
        piece = unicodedata.normalize("NFC", raw).replace("\x0c", "").strip()
        if not piece:
            continue
        if not out:
            out = piece
            continue
        if (out.endswith("­") or re.search(r"\w-$", out)) and re.match(
            r"[a-zà-ÿ]", piece
        ):
            out = out.rstrip("­")
            if out.endswith("-"):
                left = re.search(r"([\w']+)-$", out)
                right = re.match(r"[\w']+", piece)
                attested = (
                    compounds is not None
                    and left is not None
                    and right is not None
                    and f"{left.group(1)}-{right.group(0)}".lower() in compounds
                )
                if not attested:
                    out = out[:-1]
            out += piece
        else:
            out += " " + piece
    out = out.replace("­", "")
    return re.sub(r"[ \t   ]+", " ", out).strip()


def truncate_at_sentence(text: str, limit: int = MAX_WORDS) -> str:
    """Cut ``text`` to at most ``limit`` words, ending at a sentence boundary."""
    if word_count(text) <= limit:
        return text
    words = text.split()
    head = " ".join(words[:limit])
    ends = [m.end() for m in _SENTENCE_END_RE.finditer(head + " X")]
    ends = [e for e in ends if e <= len(head) + 1]
    if not ends:
        cut = head.rfind(". ")
        return head[: cut + 1].strip() if cut > 0 else head
    return head[: ends[-1]].strip()


# ---------------------------------------------------------------------------
# Source structure
# ---------------------------------------------------------------------------


@dataclass
class Unit:
    """A paragraph, footnote or heading: the atoms the extract is built from."""

    kind: str  # "paragraph" | "note" | "heading"
    lines: list[int]  # 0-based line indices, in order
    page: int  # 0-based physical page index in the file
    text: str
    words: int

    @property
    def start(self) -> int:
        return self.lines[0]

    @property
    def end(self) -> int:
        return self.lines[-1]


@dataclass
class SourceDoc:
    lines: list[str]
    frontmatter: dict[str, str] = field(default_factory=dict)
    page_of_line: list[int] = field(default_factory=list)
    kind_of_line: list[str] = field(default_factory=list)
    clean_lines: list[str] = field(default_factory=list)
    units: list[Unit] = field(default_factory=list)
    unit_of_line: dict[int, int] = field(default_factory=dict)
    fold_text: str = ""
    fold_line_starts: list[int] = field(default_factory=list)
    fold_line_index: list[int] = field(default_factory=list)
    compounds: set[str] = field(default_factory=set)
    page_numbers: dict[int, int | str] = field(default_factory=dict)

    @property
    def page_count(self) -> int:
        return (self.page_of_line[-1] + 1) if self.page_of_line else 0

    def is_native(self) -> bool:
        method = self.frontmatter.get("extraction_method", "")
        if not self.frontmatter:
            return True  # plain .txt extractions carry no frontmatter
        if any(k.startswith("ocr_") for k in self.frontmatter):
            return False
        return method in NATIVE_METHODS


def parse_frontmatter(lines: list[str]) -> tuple[dict[str, str], int]:
    if not lines or lines[0].strip() != "---":
        return {}, 0
    meta: dict[str, str] = {}
    for idx in range(1, min(len(lines), 60)):
        if lines[idx].strip() == "---":
            return meta, idx + 1
        key, sep, value = lines[idx].partition(":")
        if sep:
            meta[key.strip()] = value.strip()
    return {}, 0


def _strip_banner(line: str) -> tuple[str, bool]:
    stripped = line
    hit = False
    for pattern in _BANNER_RES:
        new = pattern.sub("", stripped)
        if new != stripped:
            hit = True
            stripped = new
    return stripped.rstrip(), hit


def _formfeed_line_is_body(rest: str) -> bool:
    """A form-feed line normally carries the running head; treat its text as
    body only when it is long, mostly lower case and free of page numbers."""
    if word_count(rest) < 12:
        return False
    letters = [c for c in rest if c.isalpha()]
    if letters and sum(c.isupper() for c in letters) / len(letters) > 0.5:
        return False
    return not re.search(r"(^|\s)\d{1,4}(\s|$)", rest.strip())


def _short(line: str, max_words: int = 8) -> bool:
    return 0 < word_count(line) <= max_words


def _footnote_number(line: str) -> int | None:
    match = _FOOTNOTE_START_RE.match(line)
    return int(match.group(1)) if match else None


def _roman_to_int(label: str) -> int | None:
    values = {"i": 1, "v": 5, "x": 10, "l": 50, "c": 100, "d": 500, "m": 1000}
    total = 0
    prev = 0
    for char in reversed(label.lower()):
        value = values.get(char)
        if value is None:
            return None
        total += value if value >= prev else -value
        prev = max(prev, value)
    return total if 0 < total < 5000 else None


def _looks_like_heading(line: str) -> bool:
    text = line.strip()
    if not text or word_count(text) > 10 or _TERMINAL_RE.search(text):
        return False
    if text.startswith("#") or _SECTION_NUMBER_RE.match(text):
        return True
    if word_count(text) <= 5 and _SECTION_WORDS_RE.match(text):
        return True
    if _HEADING_NUMBERED_RE.match(text):
        return True
    letters = [c for c in text if c.isalpha()]
    return len(letters) >= 3 and all(c.isupper() for c in letters)


def _running_page_numbers(
    lines: list[str],
    clean: list[str],
    kind: list[str],
    page_of_line: list[int],
    body_start: int,
) -> dict[int, int | str]:
    """Printed page numbers read off running heads/feet, kept only when the
    neighbouring pages confirm the sequence (page p-1 -> n-1 or p+1 -> n+1)."""
    candidates: dict[int, list[tuple[int, int | str]]] = defaultdict(list)
    number_re = re.compile(r"^\s*(\d{1,4})(?!\S)|(?<!\S)(\d{1,4})\s*$")
    pages: dict[int, list[int]] = defaultdict(list)
    for i in range(body_start, len(lines)):
        if kind[i] != "front":
            pages[page_of_line[i]].append(i)
    for page, idxs in pages.items():
        nonblank = [i for i in idxs if kind[i] != "blank"]
        top = set(nonblank[:3])
        bottom = set(nonblank[-3:])
        body = [i for i in idxs if kind[i] == "body"]
        edges = {body[0], body[-1]} if body else set()
        for i in idxs:
            if kind[i] == "ff":
                text = _strip_banner(lines[i][1:])[0]
            elif kind[i] in {"head", "foot"} and (i in top or i in bottom):
                text = clean[i]
            elif i in edges:
                text = clean[i]  # a folio glued to the first / last body line
            else:
                continue
            roman = _ROMAN_RE.match(text)
            if roman and kind[i] != "ff":
                value = _roman_to_int(roman.group(1))
                if value is not None:
                    candidates[page].append((value, roman.group(1).lower()))
                continue
            for match in number_re.finditer(text):
                value = int(match.group(1) or match.group(2))
                if 0 < value < 5000:
                    candidates[page].append((value, value))
    confirmed: dict[int, int | str] = {}
    for page, values in candidates.items():
        best: tuple[int, int | str] | None = None
        for value, label in dict.fromkeys(values):
            support = sum(
                1
                for delta in (-2, -1, 1, 2)
                if any(v == value + delta for v, _ in candidates.get(page + delta, []))
            )
            if support >= 2 and (best is None or support > best[0]):
                best = (support, label)
        if best is not None:
            confirmed[page] = best[1]
    return confirmed


def analyse(lines: list[str]) -> SourceDoc:
    """Classify every line (form feed, head, foot, banner, note, body) and
    segment the body into paragraphs / footnotes / headings."""

    doc = SourceDoc(lines=lines)
    doc.frontmatter, body_start = parse_frontmatter(lines)
    n = len(lines)
    page_of_line = [0] * n
    kind = ["body"] * n
    clean = list(lines)

    # 1. pages and banners ---------------------------------------------------
    page = 0
    for i, raw in enumerate(lines):
        if i < body_start:
            kind[i] = "front"
            clean[i] = ""
            page_of_line[i] = 0
            continue
        if raw.startswith("\x0c"):
            page += 1
            rest = raw[1:]
            rest, _ = _strip_banner(rest)
            if _formfeed_line_is_body(rest):
                kind[i] = "body"
                clean[i] = rest
            else:
                kind[i] = "ff"
                clean[i] = ""
            page_of_line[i] = page
            continue
        page_of_line[i] = page
        text, hit = _strip_banner(raw)
        clean[i] = text
        if hit and not text.strip():
            kind[i] = "banner"
        elif not text.replace("­", "").strip():
            kind[i] = "blank"
        elif not re.search(r"[^\W\d_]", text):
            kind[i] = "foot"  # digits / punctuation only: a folio, never prose
    doc.page_of_line = page_of_line

    # a JSTOR cover sheet is a whole page of banner, never body
    cover_pages = {
        page_of_line[i] for i in range(body_start, n) if _COVER_PAGE_RE.search(lines[i])
    }
    for i in range(body_start, n):
        if page_of_line[i] in cover_pages and kind[i] in {"body", "blank"}:
            kind[i] = "banner"

    # recurring short lines are running heads wherever they sit on the page
    recurring: Counter[str] = Counter()
    for i in range(body_start, n):
        if kind[i] == "body" and _short(clean[i], max_words=16):
            recurring[_fold(clean[i])] += 1
    running_heads = {key for key, count in recurring.items() if count >= 3 and key}

    # 2. per-page head / foot / notes ----------------------------------------
    pages: dict[int, list[int]] = defaultdict(list)
    for i in range(body_start, n):
        pages[page_of_line[i]].append(i)

    prev_note_open = False
    for _pg, idxs in sorted(pages.items()):
        body_idx = [i for i in idxs if kind[i] == "body"]
        if not body_idx:
            prev_note_open = False
            continue
        long_idx = [i for i in body_idx if word_count(clean[i]) >= 10]
        first_long = long_idx[0] if long_idx else body_idx[-1] + 1

        # footnote block: first numbered note (after the first long body line)
        # from which the note numbers only grow
        starts: list[tuple[int, int]] = []
        for pos, i in enumerate(body_idx):
            num = _footnote_number(clean[i])
            if num is None or i <= first_long:
                continue
            if _PURE_NUMBER_RE.match(clean[i]):
                nxt = body_idx[pos + 1] if pos + 1 < len(body_idx) else None
                if nxt is None or word_count(clean[nxt]) < 3:
                    continue
            starts.append((i, num))
        block_start: int | None = None
        for pos, (i, num) in enumerate(starts):
            following = [m for _, m in starts[pos + 1 :]]
            increasing = all(
                a < b for a, b in zip([num, *following], following, strict=False)
            )
            after_mid = body_idx.index(i) >= len(body_idx) // 2
            if increasing and (after_mid or len(following) >= 1):
                block_start = i
                break
        if block_start is not None:
            if prev_note_open:
                # tail of a note continued from the previous page
                j = body_idx.index(block_start) - 1
                while j >= 0:
                    cand = clean[body_idx[j]].strip()
                    if not cand or cand[0].isupper() or _footnote_number(cand):
                        break
                    kind[body_idx[j]] = "note"
                    j -= 1
            for i in body_idx:
                if i >= block_start:
                    kind[i] = "note"
            last_note = [i for i in body_idx if kind[i] == "note"][-1]
            prev_note_open = not _TERMINAL_RE.search(clean[last_note])
        else:
            prev_note_open = False

        # running heads / feet: short lines before the first or after the
        # last long line of the page (a footer printed under the notes too)
        body_idx = [i for i in idxs if kind[i] == "body"]
        text_idx = [i for i in idxs if kind[i] in {"body", "note"}]
        if not body_idx:
            continue
        long_idx = [i for i in text_idx if word_count(clean[i]) >= 10]
        first_long = long_idx[0] if long_idx else body_idx[-1] + 1
        last_long = long_idx[-1] if long_idx else body_idx[0] - 1
        for i in text_idx:
            folded = _fold(clean[i])
            if kind[i] == "note" and (i < last_long or _footnote_number(clean[i])):
                continue
            if (i < first_long or i > last_long) and (
                _PURE_NUMBER_RE.match(clean[i])
                or folded in running_heads
                or (
                    _short(clean[i])
                    and not _TERMINAL_RE.search(clean[i])
                    and not _looks_like_heading(clean[i])
                    and (
                        re.search(r"(^\s*\d{1,4}\b|\b\d{1,4}\s*$)", clean[i])
                        or i > last_long
                    )
                )
            ):
                kind[i] = "head" if i < first_long else "foot"
            elif folded in running_heads and kind[i] == "body":
                kind[i] = "head"
    doc.kind_of_line = kind
    doc.clean_lines = clean

    # 3. units ----------------------------------------------------------------
    compound_re = re.compile(r"(?<![\w-])([a-zà-ÿ]+-[a-zà-ÿ]+)(?![\w-])")
    for i in range(body_start, n):
        if kind[i] in {"body", "note"}:
            for match in compound_re.finditer(clean[i].lower()):
                doc.compounds.add(match.group(1))
    doc.page_numbers = _running_page_numbers(
        lines, clean, kind, page_of_line, body_start
    )
    for pg, idxs in pages.items():
        number = doc.page_numbers.get(pg)
        body = [i for i in idxs if kind[i] == "body"]
        if not isinstance(number, int) or not body:
            continue
        first, last = body[0], body[-1]
        clean[first] = re.sub(rf"^(\s*){number}\s+(?=\S)", r"\1", clean[first])
        clean[last] = re.sub(rf"(?<=\S)\s+{number}\s*$", "", clean[last])
    units: list[Unit] = []
    indent_of = [len(c) - len(c.lstrip(" ")) for c in clean]
    page_indent: dict[int, int] = {}
    page_linelen: dict[int, float] = {}
    for pg, idxs in pages.items():
        body = [i for i in idxs if kind[i] == "body"]
        if body:
            page_indent[pg] = Counter(indent_of[i] for i in body).most_common(1)[0][0]
            page_linelen[pg] = statistics.median(len(clean[i].strip()) for i in body)

    def starts_paragraph(i: int, prev: int | None) -> bool:
        text = clean[i].strip()
        if prev is None:
            return True
        pg = page_of_line[i]
        if pg == page_of_line[prev] and any(
            kind[j] == "blank" for j in range(prev + 1, i)
        ):
            return True
        if pg != page_of_line[prev]:
            # across a page break: a sentence that runs on continues the
            # paragraph; a closed sentence opens a new unit
            return not text[:1].islower() and bool(
                _TERMINAL_RE.search(clean[prev].strip())
            )
        if indent_of[i] >= page_indent.get(pg, 0) + 2 and not text[:1].islower():
            return True
        prev_text = clean[prev].strip()
        prev_short = len(prev_text) < 0.6 * page_linelen.get(page_of_line[prev], 80)
        return bool(
            _TERMINAL_RE.search(prev_text)
            and prev_short
            and re.match(r"[A-ZÀ-Ý«“\"'‘]", text)
        )

    current: list[int] = []
    current_kind = ""
    prev_body: int | None = None

    def flush() -> None:
        nonlocal current, current_kind
        if current:
            text = join_lines([clean[i] for i in current], doc.compounds)
            units.append(
                Unit(
                    kind=current_kind,
                    lines=list(current),
                    page=page_of_line[current[0]],
                    text=text,
                    words=word_count(text),
                )
            )
        current = []
        current_kind = ""

    for i in range(body_start, n):
        k = kind[i]
        if k == "body":
            after_number = bool(
                units
                and units[-1].kind == "heading"
                and units[-1].end == prev_body
                and _SECTION_NUMBER_RE.match(units[-1].text)
            )
            title_like = (
                after_number
                and 0 < word_count(clean[i]) <= 10
                and not _TERMINAL_RE.search(clean[i])
            )
            if (title_like or _looks_like_heading(clean[i])) and (
                prev_body is None
                or kind[i - 1] != "body"
                or _TERMINAL_RE.search(clean[prev_body])
                or after_number
            ):
                flush()
                current, current_kind = [i], "heading"
                flush()
                prev_body = i
                continue
            if current_kind != "paragraph" or starts_paragraph(i, prev_body):
                flush()
                current_kind = "paragraph"
            current.append(i)
            prev_body = i
        elif k == "note":
            if current_kind != "note" or _footnote_number(clean[i]) is not None:
                flush()
                current_kind = "note"
            current.append(i)
        elif k == "blank":
            if current_kind == "note":
                flush()
        # ff / head / foot / banner lines are transparent: a paragraph may
        # continue across them (page break inside a sentence).
    flush()
    doc.units = units
    for idx, unit in enumerate(units):
        for line in unit.lines:
            doc.unit_of_line[line] = idx

    # 4. flat search index (line-end hyphenation mended across lines) --------
    parts: list[str] = []
    starts_: list[int] = []
    total = 0
    for i in range(n):
        if kind[i] not in {"body", "note"}:
            continue
        piece = _fold(clean[i])
        if not piece:
            continue
        if parts and re.search(r"\w-$", parts[-1]) and re.match(r"[a-zà-ÿ]", piece):
            parts[-1] = parts[-1][:-1]
            total -= 1
            sep = ""
        else:
            sep = " " if parts else ""
        parts.append(sep)
        total += len(sep)
        starts_.append(total)
        doc.fold_line_index.append(i)
        parts.append(piece)
        total += len(piece)
    doc.fold_text = "".join(parts)
    doc.fold_line_starts = starts_
    return doc


def load_source(path: Path) -> SourceDoc:
    text = path.read_text(encoding="utf-8", errors="replace")
    return analyse(text.split("\n"))


# ---------------------------------------------------------------------------
# Locating evidence
# ---------------------------------------------------------------------------


def _line_at_offset(doc: SourceDoc, offset: int) -> int:
    from bisect import bisect_right

    pos = bisect_right(doc.fold_line_starts, offset) - 1
    return doc.fold_line_index[max(pos, 0)]


def locate_quote(
    doc: SourceDoc, quote: str, hint_lines: tuple[int, int] | None
) -> tuple[int, int, str] | None:
    """Return the 0-based (first, last, method) line range holding ``quote``.

    The whole folded quote is searched first, then shrinking prefixes and
    suffixes (12 down to 5 words: two-column layouts and footnote calls break
    long runs).  When nothing matches but the audit cited body lines, those
    lines are trusted as the anchor (``method="cited_lines"``).
    """
    key = _fold(quote)
    if not key:
        return None
    words = key.split()
    candidates: list[str] = [key]
    for size in (12, 10, 8, 6, 5):
        if len(words) > size:
            candidates.append(" ".join(words[:size]))
            candidates.append(" ".join(words[-size:]))
    hint_center = None
    if hint_lines:
        hint_center = (hint_lines[0] + hint_lines[1]) // 2
    for cand in candidates:
        # the joined text may have mended a hyphen the quote did not
        variants = {cand, cand.replace("- ", "")}
        hits: list[int] = []
        for variant in variants:
            start = 0
            while True:
                pos = doc.fold_text.find(variant, start)
                if pos < 0:
                    break
                hits.append(pos)
                start = pos + 1
                if len(hits) > 50:
                    break
        if not hits:
            continue
        chosen = hits[0]
        if hint_center is not None:
            chosen = min(hits, key=lambda p: abs(_line_at_offset(doc, p) - hint_center))
            far = abs(_line_at_offset(doc, chosen) - hint_center) > 400
            cited_ok = hint_lines is not None and all(
                doc.kind_of_line[i] in {"body", "note"}
                for i in range(hint_lines[0], hint_lines[1] + 1)
                if 0 <= i < len(doc.kind_of_line)
            )
            if far and len(hits) > 1 and cited_ok and hint_lines is not None:
                # several far-away hits and a line citation: trust the citation
                return hint_lines[0], hint_lines[1], "cited_lines"
        first = _line_at_offset(doc, chosen)
        last = _line_at_offset(doc, chosen + len(cand) - 1)
        method = "full_quote" if cand == key else f"probe_{len(cand.split())}w"
        return first, last, method
    if hint_lines and 0 <= hint_lines[0] <= hint_lines[1] < len(doc.kind_of_line):
        kinds = {doc.kind_of_line[i] for i in range(hint_lines[0], hint_lines[1] + 1)}
        if kinds <= {"body", "note"}:
            return hint_lines[0], hint_lines[1], "cited_lines"
    return None


# ---------------------------------------------------------------------------
# Expansion
# ---------------------------------------------------------------------------


@dataclass
class Extract:
    text: str
    words: int
    first_line: int  # 0-based
    last_line: int
    unit_indexes: list[int]
    truncated: bool
    anchor_kind: str


def _sentence_window(unit_text: str, anchor_key: str, limit: int) -> tuple[str, bool]:
    """When one unit alone is over the cap: keep the sentences around the
    anchor, growing forward then backward while under ``limit``."""
    sentences = re.split(_SENTENCE_END_RE, unit_text)
    sentences = [s.strip() for s in sentences if s.strip()]
    if not sentences:
        return truncate_at_sentence(unit_text, limit), True
    anchor_words = anchor_key.split()
    probes = [
        " ".join(anchor_words[:8]),
        " ".join(anchor_words[:5]),
        " ".join(anchor_words[-5:]),
    ]
    folded = [_fold(sent) for sent in sentences]
    anchor_idx = next(
        (
            idx
            for probe in probes
            if probe
            for idx, sent in enumerate(folded)
            if probe in sent
        ),
        -1,
    )
    if anchor_idx < 0:
        anchor_set = set(anchor_words)
        anchor_idx = max(
            range(len(sentences)),
            key=lambda idx: len(anchor_set & set(folded[idx].split())),
        )
    lo = hi = anchor_idx
    total = word_count(sentences[anchor_idx])
    while True:
        grew = False
        if hi + 1 < len(sentences) and total + word_count(sentences[hi + 1]) <= limit:
            hi += 1
            total += word_count(sentences[hi])
            grew = True
        if lo - 1 >= 0 and total + word_count(sentences[lo - 1]) <= limit:
            lo -= 1
            total += word_count(sentences[lo])
            grew = True
        if not grew:
            break
    text = " ".join(sentences[lo : hi + 1])
    if word_count(text) > limit:
        text = truncate_at_sentence(text, limit)
    return text, True


def expand(
    doc: SourceDoc,
    anchors: list[tuple[int, int]],
    *,
    limit: int = MAX_WORDS,
    page_window: int = PAGE_WINDOW,
) -> Extract | None:
    """Grow from the unit(s) holding the anchors to neighbouring paragraphs."""
    anchor_units: list[int] = []
    for first, last in anchors:
        for line in range(first, last + 1):
            idx = doc.unit_of_line.get(line)
            if idx is not None and idx not in anchor_units:
                anchor_units.append(idx)
    if not anchor_units:
        return None
    primary = anchor_units[0]
    unit = doc.units[primary]
    anchor_page = unit.page
    lo_page, hi_page = anchor_page - page_window, anchor_page + page_window

    if unit.kind == "note":
        # the evidence is a footnote: the note itself is the unit
        text = unit.text
        truncated = False
        if unit.words > limit:
            text = truncate_at_sentence(text, limit)
            truncated = True
        return Extract(
            text=text,
            words=word_count(text),
            first_line=unit.start,
            last_line=unit.end,
            unit_indexes=[primary],
            truncated=truncated,
            anchor_kind="note",
        )

    if unit.words > limit:
        first, last = anchors[0]
        key = _fold(join_lines([doc.clean_lines[i] for i in range(first, last + 1)]))
        text, _ = _sentence_window(unit.text, key, limit)
        return Extract(
            text=text,
            words=word_count(text),
            first_line=unit.start,
            last_line=unit.end,
            unit_indexes=[primary],
            truncated=True,
            anchor_kind="paragraph",
        )

    chosen = [primary]
    total = unit.words

    def admissible(idx: int) -> bool:
        cand = doc.units[idx]
        if cand.kind != "paragraph":
            return False
        return (
            lo_page <= cand.page <= hi_page
            and doc.page_of_line[cand.end] <= hi_page
            and doc.page_of_line[cand.start] >= lo_page
        )

    def try_add(idx: int) -> bool:
        nonlocal total
        # footnote blocks sit between body paragraphs: step over them
        step = 1 if idx > primary else -1
        while 0 <= idx < len(doc.units) and doc.units[idx].kind == "note":
            idx += step
        if idx < 0 or idx >= len(doc.units) or idx in chosen:
            return False
        if doc.units[idx].kind == "heading":
            return False
        if not admissible(idx):
            return False
        if total + doc.units[idx].words > limit:
            return False
        chosen.append(idx)
        total += doc.units[idx].words
        return True

    # units holding the other evidence quotes come first, closest first
    others = sorted(
        (i for i in anchor_units[1:] if i != primary),
        key=lambda i: abs(i - primary),
    )
    for idx in others:
        step = 1 if idx > primary else -1
        cursor = primary + step
        ok = True
        while cursor != idx + step:
            if cursor not in chosen and not try_add(cursor):
                ok = False
                break
            cursor += step
        if not ok:
            break

    forward_open = backward_open = True
    while forward_open or backward_open:
        if forward_open:
            forward_open = try_add(max(chosen) + 1)
        if backward_open:
            backward_open = try_add(min(chosen) - 1)

    ordered = sorted(chosen)
    text = "\n\n".join(doc.units[i].text for i in ordered)
    return Extract(
        text=text,
        words=word_count(text),
        first_line=doc.units[ordered[0]].start,
        last_line=doc.units[ordered[-1]].end,
        unit_indexes=ordered,
        truncated=False,
        anchor_kind="paragraph",
    )


# ---------------------------------------------------------------------------
# Fonds access
# ---------------------------------------------------------------------------


def load_page_map_io(thesis_root: Path) -> ModuleType | None:
    path = thesis_root / "10_Scripts" / "page_map_io.py"
    if not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location("page_map_io", path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


@dataclass(frozen=True)
class PageInfo:
    printed: Any  # int | str | None
    physical: int | None
    method: str
    disagreement: bool


class Fonds:
    """Resolve citation file names to files of ``04_Littérature_secondaire``."""

    def __init__(self, thesis_root: Path, page_map_io: ModuleType | None) -> None:
        self.root = thesis_root / LIT_SUBDIR
        self.page_map_io = page_map_io
        self.page_map: dict[str, Any] = {}
        if page_map_io is not None:
            self.page_map = page_map_io.load_page_map(self.root / "page_map.json")
        self.by_basename: dict[str, list[str]] = defaultdict(list)
        self.by_rel: dict[str, str] = {}
        if self.root.is_dir():
            for dirpath, dirnames, filenames in os.walk(self.root):
                dirnames[:] = [
                    d
                    for d in dirnames
                    if d not in SKIP_DIR_PARTS and not d.startswith(".")
                ]
                for name in filenames:
                    if not name.endswith((".md", ".txt")):
                        continue
                    rel = _nfc(os.path.relpath(os.path.join(dirpath, name), self.root))
                    self.by_rel[rel] = rel
                    self.by_basename[_nfc(name)].append(rel)
        self.page_map_audit: dict[str, Any] = {}
        if page_map_io is not None:
            self.page_map_audit = page_map_io.load_page_map_audit(
                self.root / "page_map_audit.json"
            )
        self._docs: dict[str, SourceDoc] = {}
        self._sha: dict[str, str] = {}

    def resolve(self, cited: str) -> str | None:
        cited = _nfc(cited.strip().lstrip("[").rstrip("]"))
        if cited in self.by_rel:
            return cited
        base = os.path.basename(cited)
        cands = self.by_basename.get(base, [])
        if not cands:
            return None
        if len(cands) == 1:
            return cands[0]
        folder = os.path.dirname(cited)
        for cand in cands:
            if folder and cand.startswith(folder):
                return cand
        return sorted(cands)[0]

    def doc(self, rel: str) -> SourceDoc:
        if rel not in self._docs:
            self._docs[rel] = load_source(self.root / rel)
        return self._docs[rel]

    def sha256(self, rel: str) -> str:
        if rel not in self._sha:
            self._sha[rel] = hashlib.sha256((self.root / rel).read_bytes()).hexdigest()
        return self._sha[rel]

    def audit_status(self, rel: str) -> str:
        if self.page_map_io is None:
            return ""
        entry, _ = self.page_map_io.lookup_page_entry(self.page_map_audit, rel)
        return str((entry or {}).get("status") or "")

    def page_for_line(self, rel: str, line_no_1based: int) -> PageInfo:
        """Printed + physical page for a 1-based line.

        ``page_map_io.citation_for_line`` is the canonical accessor; its
        printed page is accepted at confidence >= 0.90 when the page-map
        audit of the file passed.  Otherwise the folio read off the running
        head/foot of the same physical page (confirmed by the neighbouring
        pages) is used; an unaudited page map comes last.  A disagreement
        between an audited page map and the running head is flagged.
        """
        doc = self.doc(rel)
        idx = max(0, min(line_no_1based - 1, len(doc.page_of_line) - 1))
        file_page = doc.page_of_line[idx] if doc.page_of_line else 0
        head = doc.page_numbers.get(file_page)
        cit = None
        if self.page_map_io is not None and self.page_map:
            cit = self.page_map_io.citation_for_line(self.page_map, rel, line_no_1based)
        physical = cit.pdf_page if cit is not None and cit.pdf_page else None
        if physical is None and doc.page_count > 1:
            physical = file_page + 1
        pm_conf = (
            cit is not None
            and cit.printed_page is not None
            and cit.confidence >= MIN_PAGE_CONFIDENCE
        )
        audit = self.audit_status(rel)
        if pm_conf and audit == "passed":
            agree = head is None or str(cit.printed_page) == str(head)
            method = "page_map" if head is None else "page_map+running_head"
            return PageInfo(cit.printed_page, physical, method, not agree)
        if head is not None:
            return PageInfo(head, physical, "running_head", False)
        if pm_conf and not audit:
            return PageInfo(cit.printed_page, physical, "page_map_unaudited", False)
        return PageInfo(None, physical, "none", False)

    def printed_page(self, rel: str, line_no_1based: int) -> Any:
        return self.page_for_line(rel, line_no_1based).printed

    def pdf_page(self, rel: str, line_no_1based: int) -> int | None:
        return self.page_for_line(rel, line_no_1based).physical


def format_pages(start: Any, end: Any) -> str | None:
    if start is None or end is None:
        return None
    if str(start) == str(end):
        return f"p. {start}"
    return f"pp. {start}-{end}"


# ---------------------------------------------------------------------------
# Node processing
# ---------------------------------------------------------------------------


def parse_citation(citation: str) -> tuple[str, tuple[int, int]] | None:
    match = _CITATION_RE.search(citation or "")
    if not match:
        return None
    first = int(match.group(2))
    last = int(match.group(3) or first)
    return match.group(1), (first, last)


def work_file_hints(scratch_dir: Path | None) -> dict[str, str]:
    """``scholarly_work_id -> relative md path`` from the audit cluster files."""
    hints: dict[str, str] = {}
    if scratch_dir is None or not scratch_dir.is_dir():
        return hints
    idx = scratch_dir / "works_index.json"
    if idx.is_file():
        try:
            for row in json.loads(idx.read_text(encoding="utf-8")):
                if row.get("work") and row.get("file"):
                    hints[row["work"]] = row["file"]
        except OSError, ValueError:
            pass
    for name in ("wave2_clusters.json", "wave3_clusters.json"):
        path = scratch_dir / name
        if not path.is_file():
            continue
        try:
            clusters = json.loads(path.read_text(encoding="utf-8"))
        except OSError, ValueError:
            continue
        for cluster in clusters:
            for part in str(cluster.get("hint", "")).split(";"):
                work, sep, file_ = part.partition("→")
                if sep and work.strip() and file_.strip():
                    hints.setdefault(work.strip(), file_.strip())
    return hints


@dataclass
class NodeResult:
    node_id: str
    status: str  # "extended" | "skipped"
    reason: str = ""
    fields: dict[str, Any] = field(default_factory=dict)
    rel: str | None = None
    extract: Extract | None = None
    evidence_citation: str = ""
    audit_wave: Any = None
    publication_id: str = ""
    anchor_methods: list[str] = field(default_factory=list)
    page_methods: list[str] = field(default_factory=list)
    page_disagreement: bool = False


def layout_quality(doc: SourceDoc, first: int, last: int) -> dict[str, float]:
    """Two signals that an extract is unusable: interleaved two-column lines
    (long lines with an internal run of spaces) and OCR garbage (tokens
    without letters or digits)."""
    body = [
        doc.clean_lines[i].strip()
        for i in range(first, last + 1)
        if doc.kind_of_line[i] in {"body", "note"}
    ]
    long_lines = [line for line in body if len(line) >= 50]
    gapped = sum(1 for line in long_lines if re.search(r"\S {4,}\S", line))
    two_column = gapped / len(long_lines) if long_lines else 0.0
    tokens = " ".join(body).split()
    bad = sum(
        1
        for tok in tokens
        if not re.search(r"[^\W_]", tok)
        or len(re.findall(r"[^\w\s'’\-.,;:()]", tok)) >= 2
    )
    garbled = bad / len(tokens) if tokens else 0.0
    return {"two_column_ratio": two_column, "garbled_ratio": garbled}


def process_node(
    node: dict[str, Any], fonds: Fonds, hints: dict[str, str]
) -> NodeResult:
    node_id = str(node.get("id"))
    meta = node.get("metadata") or {}
    audit = meta.get("scholarly_audit") or {}
    evidence = [e for e in audit.get("evidence", []) if isinstance(e, dict)]
    result = NodeResult(node_id=node_id, status="skipped", audit_wave=audit.get("wave"))
    result.publication_id = str(meta.get("scholarly_work_id") or "")
    if not evidence:
        result.reason = "no_evidence"
        return result

    # candidate files: cited first, then the cluster hint for the work
    located: list[tuple[str, tuple[int, int], str]] = []
    methods: list[str] = []
    unresolved: list[str] = []
    for item in evidence:
        citation = str(item.get("citation") or "")
        quote = str(item.get("quote") or "")
        parsed = parse_citation(citation)
        rels: list[tuple[str, tuple[int, int] | None]] = []
        if parsed:
            rel = fonds.resolve(parsed[0])
            if rel:
                rels.append((rel, (parsed[1][0] - 1, parsed[1][1] - 1)))
            else:
                unresolved.append(parsed[0])
        hint = hints.get(result.publication_id)
        if hint:
            hint_rel = fonds.resolve(hint)
            if hint_rel and all(hint_rel != r for r, _ in rels):
                rels.append((hint_rel, None))
        if not quote.strip():
            continue
        for rel, hint_lines in rels:
            try:
                doc = fonds.doc(rel)
            except OSError:
                continue
            span = locate_quote(doc, quote, hint_lines)
            if span is not None:
                located.append((rel, (span[0], span[1]), citation))
                methods.append(span[2])
                break

    if not located:
        if unresolved and len(unresolved) == len(evidence):
            result.reason = "file_not_in_fonds"
        else:
            result.reason = "evidence_not_located"
        return result

    rel = located[0][0]
    result.rel = rel
    result.evidence_citation = located[0][2]
    if any(marker in rel for marker in CURATED_MARKERS):
        result.reason = "curated_extraction_not_publication_text"
        return result
    doc = fonds.doc(rel)
    if not doc.is_native():
        result.reason = "ocr_or_non_native_extraction"
        return result
    anchors = [span for r, span, _ in located if r == rel]
    extract = expand(doc, anchors)
    if extract is None:
        result.reason = "anchor_outside_body"
        return result
    if extract.words < MIN_WORDS:
        result.reason = "extract_below_min_words"
        return result
    if extract.words > MAX_WORDS:
        extract.text = truncate_at_sentence(extract.text, MAX_WORDS)
        extract.words = word_count(extract.text)
        extract.truncated = True
    layout = layout_quality(doc, extract.first_line, extract.last_line)
    if layout["two_column_ratio"] > TWO_COLUMN_MAX_RATIO:
        result.reason = "two_column_layout"
        return result
    if layout["garbled_ratio"] > GARBLED_MAX_RATIO:
        result.reason = "text_garbled"
        return result
    result.extract = extract
    result.anchor_methods = methods

    first_1, last_1 = extract.first_line + 1, extract.last_line + 1
    page_start = fonds.page_for_line(rel, first_1)
    page_end = fonds.page_for_line(rel, last_1)
    result.page_methods = [page_start.method, page_end.method]
    result.page_disagreement = page_start.disagreement or page_end.disagreement
    quote_pages = format_pages(page_start.printed, page_end.printed)
    result.fields = {
        "quote_verbatim": extract.text,
        "quote_words": extract.words,
        "quote_pages": quote_pages,
        "quote_lines": f"L{first_1}-L{last_1}",
        "quote_source_file": rel,
        "quote_source_sha256": fonds.sha256(rel),
        "quote_verbatim_previous": meta.get("quote_verbatim"),
        "quote_extended_at": STAMP,
    }
    result.status = "extended"
    return result


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------


def manifestation_id_for(rel: str, publication_id: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", _nfc(rel).lower()).strip("_")
    digest = hashlib.sha256(f"{rel}\n{publication_id}".encode()).hexdigest()[:10]
    base = f"shal_md_{slug}"[:100].rstrip("_")
    return f"{base}_{digest}"


def _printed_label(value: Any) -> str | None:
    if value is None:
        return None
    label = str(value).strip()
    return (
        label if re.fullmatch(r"(?:[1-9]\d*[a-z]?|[ivxlcdm]+)", label, re.I) else None
    )


def build_manifest(
    results: list[NodeResult],
    fonds: Fonds,
    *,
    reviewed_by: str,
    reviewed_at: str,
    text_sha: Any,
) -> dict[str, Any]:
    """Group extracts by manifestation and split them at page boundaries.

    ``secondary_evidence_pages`` is keyed by ``(manifestation_id,
    physical_page)`` and the verifier concatenates one row per printed page of
    a node's page reference, so a two-page extract becomes two rows and two
    extracts on one page are merged into one row (line-range union, joined
    with an ellipsis if the union would exceed the cap).
    """
    by_manifestation: dict[str, dict[str, Any]] = {}
    page_rows: dict[tuple[str, int], dict[str, Any]] = {}
    extracts_index: list[dict[str, Any]] = []

    for res in results:
        if res.status != "extended" or res.extract is None or res.rel is None:
            continue
        rel = res.rel
        doc = fonds.doc(rel)
        ext = res.extract
        mid = manifestation_id_for(rel, res.publication_id)
        by_manifestation.setdefault(
            mid,
            {
                "manifestation_id": mid,
                "publication_id": res.publication_id,
                "source_locator": f"shal-fonds:{LIT_SUBDIR}/{rel}",
                "source_path": f"sources/{mid}.md",
                "source_sha256": fonds.sha256(rel),
                "media_type": "text/markdown",
                "rights_status": "copyrighted",
                "reuse_status": "quotation_only",
                "extraction_status": "partial",
                "review_status": REVIEWED,
                "reviewed_by": reviewed_by,
                "reviewed_at": reviewed_at,
                "manifest_metadata": {
                    "fonds_file": f"{LIT_SUBDIR}/{rel}",
                    "extraction_method": doc.frontmatter.get(
                        "extraction_method", "txt"
                    ),
                    "source_pdf": doc.frontmatter.get("source_pdf"),
                    "built_by": "scripts/kg_extend_verbatim_quotes.py",
                    "built_at": STAMP,
                },
                "pages": [],
            },
        )
        # lines of the extract grouped by physical page
        lines_by_page: dict[int, list[int]] = defaultdict(list)
        for idx in ext.unit_indexes:
            for line in doc.units[idx].lines:
                lines_by_page[doc.page_of_line[line]].append(line)
        if ext.truncated:
            # a truncated extract maps to the page of its first unit only
            first_page = doc.page_of_line[ext.first_line]
            lines_by_page = {first_page: [ext.first_line, ext.last_line]}
        physical_pages: list[int] = []
        for file_page, lines in sorted(lines_by_page.items()):
            line_1 = min(lines) + 1
            info = fonds.page_for_line(rel, line_1)
            physical = info.physical or (file_page + 1)
            physical_pages.append(physical)
            printed = _printed_label(info.printed)
            if ext.truncated:
                piece_text = ext.text
            else:
                piece_text = "\n\n".join(
                    doc.units[idx].text
                    for idx in ext.unit_indexes
                    if doc.page_of_line[doc.units[idx].start] == file_page
                    or doc.page_of_line[doc.units[idx].end] == file_page
                )
                if not piece_text.strip():
                    piece_text = join_lines(
                        [doc.clean_lines[i] for i in sorted(lines)], doc.compounds
                    )
            key = (mid, physical)
            row = page_rows.get(key)
            entry = {
                "node_id": res.node_id,
                "audit_wave": res.audit_wave,
                "evidence_citation": res.evidence_citation,
                "quote_lines": f"L{min(lines) + 1}-L{max(lines) + 1}",
            }
            if row is None:
                page_rows[key] = {
                    "physical_page": physical,
                    "printed_page": printed,
                    "page_locator": f"L{min(lines) + 1}-L{max(lines) + 1}",
                    "text_content": piece_text,
                    "extraction_status": "extracted",
                    "review_status": REVIEWED,
                    "reviewed_by": reviewed_by,
                    "reviewed_at": reviewed_at,
                    "extraction_metadata": {
                        "node_id": res.node_id,
                        "audit_wave": res.audit_wave,
                        "evidence_citation": res.evidence_citation,
                        "extracts": [entry],
                        "_lines": sorted(set(lines)),
                    },
                }
            else:
                meta = row["extraction_metadata"]
                meta["extracts"].append(entry)
                union = sorted(set(meta["_lines"]) | set(lines))
                merged = join_lines(
                    [
                        doc.clean_lines[i]
                        for i in union
                        if doc.kind_of_line[i] in {"body", "note"}
                    ],
                    doc.compounds,
                )
                if word_count(merged) <= MAX_WORDS:
                    row["text_content"] = merged
                    meta["_lines"] = union
                else:
                    joined = row["text_content"] + "\n\n[…]\n\n" + piece_text
                    row["text_content"] = (
                        joined
                        if word_count(joined) <= MAX_WORDS
                        else truncate_at_sentence(joined, MAX_WORDS)
                    )
                    meta["merged_with_ellipsis"] = True
                row["page_locator"] = (
                    f"L{min(meta['_lines'] + list(lines)) + 1}-L{max(meta['_lines'] + list(lines)) + 1}"
                )
                meta["node_id"] = ", ".join(e["node_id"] for e in meta["extracts"])
        extracts_index.append(
            {
                "node_id": res.node_id,
                "manifestation_id": mid,
                "publication_id": res.publication_id,
                "printed_pages": res.fields.get("quote_pages"),
                "page_locator": res.fields.get("quote_lines"),
                "physical_pages": physical_pages,
                "words": ext.words,
                "audit_wave": res.audit_wave,
                "evidence_citation": res.evidence_citation,
            }
        )

    for (mid, physical), row in sorted(page_rows.items()):
        row["extraction_metadata"].pop("_lines", None)
        row["text_path"] = f"pages/{mid}_p{physical:04d}.txt"
        row["text_sha256"] = text_sha(row["text_content"])
        by_manifestation[mid]["pages"].append(row)

    return {
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "generated_at": STAMP,
        "generator": "scripts/kg_extend_verbatim_quotes.py",
        "manifestation_id_rule": (
            "shal_md_<slug of the fonds md path>_<sha256(path\\npublication_id)[:10]>; "
            "publication_id = node.metadata.scholarly_work_id (the first field "
            "citation_verifier_v2._publication_id reads); the verifier resolves "
            "a node through publication_id + its page reference, never through "
            "the manifestation id"
        ),
        "artifacts": sorted(
            by_manifestation.values(), key=lambda a: a["manifestation_id"]
        ),
        "extracts": extracts_index,
    }


def write_manifest_bundle(
    manifest: dict[str, Any], fonds: Fonds, bundle_dir: Path
) -> None:
    """Materialise ``sources/`` and ``pages/`` next to a manifest copy so
    ``ingest_secondary_evidence_manifest.py`` can hash-check it in dry run."""
    bundle_dir.mkdir(parents=True, exist_ok=True)
    (bundle_dir / "sources").mkdir(exist_ok=True)
    (bundle_dir / "pages").mkdir(exist_ok=True)
    for artifact in manifest["artifacts"]:
        rel = artifact["manifest_metadata"]["fonds_file"].split("/", 1)[1]
        shutil.copyfile(fonds.root / rel, bundle_dir / artifact["source_path"])
        for page in artifact["pages"]:
            (bundle_dir / page["text_path"]).write_text(
                page["text_content"], encoding="utf-8"
            )
    (bundle_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# Reporting / applying
# ---------------------------------------------------------------------------


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _first_words(text: str, count: int) -> str:
    return " ".join(text.split()[:count])


def _last_words(text: str, count: int) -> str:
    return " ".join(text.split()[-count:])


def write_summary(results: list[NodeResult], path: Path, preview_path: Path) -> None:
    extended = [r for r in results if r.status == "extended"]
    skipped = [r for r in results if r.status != "extended"]
    reasons = Counter(r.reason for r in skipped)
    words = sorted(r.fields["quote_words"] for r in extended)
    buckets = Counter()
    for w in words:
        if w < 100:
            buckets["40-99"] += 1
        elif w < 200:
            buckets["100-199"] += 1
        elif w < 300:
            buckets["200-299"] += 1
        elif w < 400:
            buckets["300-399"] += 1
        else:
            buckets["400-500"] += 1
    with_pages = sum(1 for r in extended if r.fields.get("quote_pages"))
    truncated = sum(1 for r in extended if r.extract and r.extract.truncated)
    notes = sum(1 for r in extended if r.extract and r.extract.anchor_kind == "note")
    lines = [
        f"# Verbatim extension preview — {STAMP}",
        "",
        f"Preview: `{_relative(preview_path)}` (dry run, nodes.jsonl untouched).",
        "",
        "## Counts",
        "",
        f"- audited nodes: {len(results)}",
        f"- extended: {len(extended)} (with printed pages: {with_pages}; "
        f"truncated at a sentence boundary: {truncated}; footnote units: {notes})",
        f"- skipped: {len(skipped)}",
    ]
    for reason, count in reasons.most_common():
        lines.append(f"  - {reason}: {count}")
    if words:
        lines += [
            "",
            "## Word-length distribution",
            "",
            f"- min {words[0]}, median {int(statistics.median(words))}, "
            f"mean {statistics.mean(words):.0f}, max {words[-1]}",
        ]
        for bucket in ("40-99", "100-199", "200-299", "300-399", "400-500"):
            lines.append(f"- {bucket}: {buckets.get(bucket, 0)}")
    lines += ["", "## Examples", ""]
    step = max(1, len(extended) // 5)
    for res in extended[::step][:5]:
        f = res.fields
        lines += [
            f"### {res.node_id}",
            "",
            f"- file: `{f['quote_source_file']}`",
            f"- pages: {f['quote_pages'] or 'None'} — lines {f['quote_lines']} — {f['quote_words']} words",
            f"- first 60 words: {_first_words(f['quote_verbatim'], 60)}",
            f"- last 30 words: {_last_words(f['quote_verbatim'], 30)}",
            "",
        ]
    lines += ["## Skipped nodes", ""]
    for res in skipped:
        lines.append(
            f"- {res.node_id}: {res.reason}" + (f" ({res.rel})" if res.rel else "")
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def apply_to_nodes(preview: dict[str, dict[str, Any]], nodes_path: Path) -> int:
    backup = nodes_path.with_name(f"nodes.jsonl.bak-verbatim-extension-{STAMP}")
    shutil.copyfile(nodes_path, backup)
    out: list[str] = []
    changed = 0
    with nodes_path.open(encoding="utf-8") as handle:
        for raw in handle:
            line = raw.rstrip("\n")
            if not line.strip():
                out.append(raw)
                continue
            node = json.loads(line)
            fields = preview.get(str(node.get("id")))
            if not fields:
                out.append(raw)
                continue
            meta = node.setdefault("metadata", {})
            if not isinstance(meta, dict):
                out.append(raw)
                continue
            meta.update(fields)
            out.append(json.dumps(node, ensure_ascii=False) + "\n")
            changed += 1
    nodes_path.write_text("".join(out), encoding="utf-8")
    return changed


def load_audited_nodes(nodes_path: Path) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    with nodes_path.open(encoding="utf-8") as handle:
        for raw in handle:
            if not raw.strip():
                continue
            node = json.loads(raw)
            meta = node.get("metadata")
            if isinstance(meta, dict) and "scholarly_audit" in meta:
                nodes.append(node)
    return nodes


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--nodes", type=Path, default=NODES_PATH)
    parser.add_argument("--thesis-root", type=Path, default=DEFAULT_THESIS_ROOT)
    parser.add_argument(
        "--clusters-dir",
        type=Path,
        default=None,
        help="Directory holding works_index.json / wave*_clusters.json hints.",
    )
    parser.add_argument(
        "--preview",
        type=Path,
        default=OUT_DIR / f"{STAMP}_verbatim_extension_preview.json",
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=OUT_DIR / f"{STAMP}_verbatim_extension_summary.md",
    )
    parser.add_argument("--manifest", type=Path, default=None)
    parser.add_argument(
        "--manifest-bundle",
        type=Path,
        default=None,
        help="Also write manifest + sources/ + pages/ here for the ingest dry run.",
    )
    parser.add_argument("--reviewed-by", default="romain_g")
    parser.add_argument("--apply", action="store_true", help="Rewrite nodes.jsonl.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    page_map_io = load_page_map_io(args.thesis_root)
    if page_map_io is None:
        print(
            f"warning: page_map_io.py not found under {args.thesis_root}",
            file=sys.stderr,
        )
    fonds = Fonds(args.thesis_root, page_map_io)
    hints = work_file_hints(args.clusters_dir)
    nodes = load_audited_nodes(args.nodes)
    results = [process_node(node, fonds, hints) for node in nodes]

    preview = {
        "generated_at": STAMP,
        "generator": "scripts/kg_extend_verbatim_quotes.py",
        "max_words": MAX_WORDS,
        "min_words": MIN_WORDS,
        "extended": {r.node_id: r.fields for r in results if r.status == "extended"},
        "diagnostics": {
            r.node_id: {
                "anchor_methods": r.anchor_methods,
                "anchor_kind": r.extract.anchor_kind if r.extract else None,
                "truncated": bool(r.extract and r.extract.truncated),
                "page_methods": r.page_methods,
                "page_disagreement": r.page_disagreement,
            }
            for r in results
            if r.status == "extended"
        },
        "skipped": {
            r.node_id: {"reason": r.reason, "file": r.rel}
            for r in results
            if r.status != "extended"
        },
    }
    args.preview.parent.mkdir(parents=True, exist_ok=True)
    args.preview.write_text(
        json.dumps(preview, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    write_summary(results, args.summary, args.preview)
    extended = len(preview["extended"])
    print(
        f"audited={len(results)} extended={extended} skipped={len(preview['skipped'])}"
    )
    print(f"preview: {args.preview}\nsummary: {args.summary}")

    if args.manifest:
        sys.path.insert(0, str(REPO_ROOT / "database" / "src"))
        from eleutheria_database.services.text_integrity import text_sha256

        reviewed_at = datetime.now(UTC).replace(microsecond=0).isoformat()
        manifest = build_manifest(
            results,
            fonds,
            reviewed_by=args.reviewed_by,
            reviewed_at=reviewed_at,
            text_sha=text_sha256,
        )
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        rows = sum(len(a["pages"]) for a in manifest["artifacts"])
        print(
            f"manifest: {args.manifest} ({len(manifest['artifacts'])} artifacts, "
            f"{rows} page rows, {len(manifest['extracts'])} extracts)"
        )
        if args.manifest_bundle:
            write_manifest_bundle(manifest, fonds, args.manifest_bundle)
            print(f"bundle: {args.manifest_bundle}")

    if args.apply:
        changed = apply_to_nodes(preview["extended"], args.nodes)
        print(f"applied to {changed} node(s) in {args.nodes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
