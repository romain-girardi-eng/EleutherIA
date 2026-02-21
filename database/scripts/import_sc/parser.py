"""Parser for Sources Chrétiennes source files.

Reads .txt source files and produces SCWork objects.
ZERO LLM involvement — pure regex parsing. All text extracted verbatim.

Handles 4 reference format families:
  - Format A (Contre Celse): [par.: N]
  - Format B (De Principiis): [liv.: N, chap.: N, par.: N]
  - Format C (Justin/Apologistes): [première apologie, chap.: N]
  - Format D (catch-all): [chap.: N, par.: N-N], [salutation], [no: N],
                           [page: N], [cap.: N, par.: N-N], etc.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from .models import SCChapter, SCParagraph, SCWork

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BLOCK_SEPARATOR = "=" * 50
"""The line separator between paragraph blocks in source files."""

# Header field patterns
_HEADER_PATTERNS = {
    "sc_prefix": re.compile(r"^SC\s*(\S+)\s*$"),
    "auteur": re.compile(r"^AUTEUR\s*:\s*(.+)$", re.IGNORECASE),
    "oeuvre": re.compile(r"^OEUVRE\s*:\s*(.+)$", re.IGNORECASE),
    "titre_original": re.compile(r"^TITRE\s+ORIGINAL\s*:\s*(.+)$", re.IGNORECASE),
    "livre": re.compile(r"^LIVRE\s+(\S+)\s*$", re.IGNORECASE),
    "paragraphes": re.compile(r"^PARAGRAPHES?\s*:\s*(\d+)\s*$", re.IGNORECASE),
    "date": re.compile(r"^DATE\s*:\s*(.+)$", re.IGNORECASE),
    "traducteur": re.compile(r"^TRADUCTEUR\s*:\s*(.+)$", re.IGNORECASE),
}

# Reference line pattern — matches [anything]
_REF_LINE_RE = re.compile(r"^\[(.+)\]\s*$")

# Section title markers: ### TITLE ###
_SECTION_TITLE_RE = re.compile(r"###\s*(.+?)\s*###")

# Page number markers: --- 126 --- (inline or standalone)
_PAGE_MARKER_RE = re.compile(r"---\s*\d+\s*---")

# TRADUCTION / SOURCE / LATIN section markers
_TRADUCTION_MARKER_RE = re.compile(r"^---\s*TRADUCTION\s*---\s*$", re.MULTILINE)
_SOURCE_MARKER_RE = re.compile(r"^---\s*SOURCE\s*---\s*$", re.MULTILINE)
_LATIN_MARKER_RE = re.compile(r"^---\s*LATIN\s*---\s*$", re.MULTILINE)

# ---------------------------------------------------------------------------
# Format-specific reference parsers
# ---------------------------------------------------------------------------

# Format A: [par.: N]
_FMT_A_RE = re.compile(r"^par\.\s*:\s*(\d+)$")

# Format B: [liv.: N, chap.: N, par.: N]
_FMT_B_RE = re.compile(
    r"^liv\.\s*:\s*(\d+)\s*,\s*chap\.\s*:\s*(\d+)\s*,\s*par\.\s*:\s*(\d+)$"
)

# Format C: [work_title, chap.: N]  — e.g. [première apologie, chap.: 68]
_FMT_C_RE = re.compile(r"^.+,\s*chap\.\s*:\s*(\d+)$")

# Format D sub-patterns (tried in order):

# D1: [chap.: N, par.: N-N] or [chap.: N, par.: N]
_FMT_D_CHAP_PAR_RE = re.compile(
    r"^chap\.\s*:\s*(\d+)(?:\s*\([^)]*\))?\s*,\s*par\.\s*:\s*(\d[\d\-]*)$"
)

# D2: [chap.: N (French desc), par.: N-N] — Chrysostome variant
_FMT_D_CHAP_DESC_PAR_RE = re.compile(
    r"^chap\.\s*:\s*(\d+)\s*\([^)]+\)\s*,\s*par\.\s*:\s*(\d[\d\-]*)$"
)

# D3: [introduction, par.: N-N] or [conclusion, par.: N]
_FMT_D_NAMED_PAR_RE = re.compile(
    r"^([a-zéèêëàâîïôùûüç\s]+),\s*par\.\s*:\s*(\d[\d\-]*)$", re.IGNORECASE
)

# D4: [..., cap.: N, par.: N-N] — Aristides with cap. instead of chap.
_FMT_D_CAP_PAR_RE = re.compile(r"cap\.\s*:\s*(\d+)\s*,\s*par\.\s*:\s*(\d[\d\-]*)$")

# D5: [chap.: N] — chapter only, no paragraph
_FMT_D_CHAP_ONLY_RE = re.compile(r"^chap\.\s*:\s*(\d+)(?:\s*\([^)]*\))?$")

# D6: [no: N] or [no: N-N] — Melito Sur la Pâque
_FMT_D_NO_RE = re.compile(r"^no\s*:\s*(\d[\d\-]*)$")

# D7: [page: N] or [page: N-N] — Melito Eclogae
_FMT_D_PAGE_RE = re.compile(r"^page\s*:\s*(\d[\d\-]*)$")

# D8: [§ N] — paragraph marker
_FMT_D_SECTION_RE = re.compile(r"^§\s*(\d+)$")

# D9: [par.: N] — same as Format A, used by some Format D files (e.g., Pamphile)
_FMT_D_PAR_RE = re.compile(r"^par\.\s*:\s*(\d+)$")

# D-fallback: named sections like [salutation], [dédication], [Ὅρασις βʹ.], etc.
_FMT_D_NAMED_RE = re.compile(r"^([^\]]+)$")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def parse_file(file_path: str, registry_entry: dict) -> SCWork:
    """Parse a single SC source file into an SCWork object.

    Args:
        file_path: Absolute path to the source file.
        registry_entry: Dict from WORK_REGISTRY with metadata for this file.

    Returns:
        Fully populated SCWork with parsed chapters and paragraphs.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Source file not found: {file_path}")

    content = path.read_text(encoding="utf-8")
    format_type = registry_entry.get("reference_format", "D")

    # Step 1: Parse header
    header, body = _split_header_body(content)
    header_fields = _parse_header(header)

    # Step 2: Split into blocks
    blocks = _split_blocks(body)
    logger.info(
        "File %s: %d blocks found (header says %s paragraphs)",
        path.name,
        len(blocks),
        header_fields.get("paragraphes", "?"),
    )

    # Step 3: Parse each block into SCParagraph
    paragraphs: list[SCParagraph] = []
    for seq, block in enumerate(blocks):
        para = _parse_block(block, seq, format_type)
        if para is not None:
            paragraphs.append(para)

    # Step 4: Group into chapters
    chapters = _group_into_chapters(paragraphs, format_type)

    # Step 5: Build SCWork
    declared_paras = int(header_fields.get("paragraphes", "0") or "0")
    language = registry_entry.get("language", "grc")

    work = SCWork(
        file_path=str(path),
        file_name=path.name,
        sc_number=registry_entry.get("sc_number", header_fields.get("sc_number", "")),
        author=header_fields.get("auteur", ""),
        title=header_fields.get("oeuvre", ""),
        title_original=header_fields.get("titre_original", ""),
        book=header_fields.get("livre", "1"),
        declared_paragraphs=declared_paras,
        language=language,
        chapters=chapters,
        # From registry:
        node_id=registry_entry.get("node_id", ""),
        edition=registry_entry.get("edition", ""),
        date_composed=registry_entry.get("date_composed", ""),
        description=registry_entry.get("description", ""),
        period=registry_entry.get("period", ""),
        school=registry_entry.get("school", ""),
        reference_format=format_type,
        author_kg_id=registry_entry.get("author_kg_id"),
        series_prev=registry_entry.get("series_prev"),
        series_next=registry_entry.get("series_next"),
    )

    logger.info(
        "Parsed %s: %d paragraphs in %d chapters (declared: %d)",
        path.name,
        work.total_paragraphs,
        len(work.chapters),
        declared_paras,
    )

    return work


# ---------------------------------------------------------------------------
# Header parsing
# ---------------------------------------------------------------------------


def _split_header_body(content: str) -> tuple[str, str]:
    """Split file content into header section and body (paragraph blocks).

    The header ends at the first reference line [xxx] or block separator.
    """
    lines = content.split("\n")
    header_lines: list[str] = []

    for i, line in enumerate(lines):
        stripped = line.strip()
        # Header ends when we hit the first reference line
        if _REF_LINE_RE.match(stripped):
            # Include everything from this line onwards as body
            body = "\n".join(lines[i:])
            return "\n".join(header_lines), body
        header_lines.append(line)

    # Fallback: entire content is header (shouldn't happen)
    return content, ""


def _parse_header(header_text: str) -> dict[str, str]:
    """Extract structured fields from the file header."""
    fields: dict[str, str] = {}

    for line in header_text.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue

        # Check for SC prefix line (e.g., "SC 132")
        m = _HEADER_PATTERNS["sc_prefix"].match(stripped)
        if m:
            fields["sc_number"] = m.group(1)
            continue

        for key in ("auteur", "oeuvre", "titre_original", "traducteur", "date"):
            m = _HEADER_PATTERNS[key].match(stripped)
            if m:
                fields[key] = m.group(1).strip()
                break

        # LIVRE field
        m = _HEADER_PATTERNS["livre"].match(stripped)
        if m:
            fields["livre"] = m.group(1).strip()
            continue

        # PARAGRAPHES field
        m = _HEADER_PATTERNS["paragraphes"].match(stripped)
        if m:
            fields["paragraphes"] = m.group(1).strip()
            continue

    return fields


# ---------------------------------------------------------------------------
# Block splitting
# ---------------------------------------------------------------------------


def _split_blocks(body: str) -> list[str]:
    """Split the body into paragraph blocks using the ===== separator.

    Each block starts with a reference line [xxx] and contains the text.
    Empty blocks are filtered out.
    """
    # Split on the separator line (50+ = signs)
    raw_blocks = re.split(r"={50,}", body)

    # Filter out empty/whitespace-only blocks
    blocks = [b.strip() for b in raw_blocks if b.strip()]
    return blocks


# ---------------------------------------------------------------------------
# Block parsing
# ---------------------------------------------------------------------------


def _parse_block(block: str, sequence: int, format_type: str) -> SCParagraph | None:
    """Parse a single block into an SCParagraph.

    Returns None if the block is empty or contains no meaningful content.
    """
    lines = block.split("\n")

    # Find the reference line
    raw_ref = ""
    ref_content = ""
    text_start_idx = 0

    for i, line in enumerate(lines):
        stripped = line.strip()
        m = _REF_LINE_RE.match(stripped)
        if m:
            raw_ref = stripped  # e.g., "[par.: 1]"
            ref_content = m.group(1).strip()  # e.g., "par.: 1"
            text_start_idx = i + 1
            break

    if not raw_ref:
        # No reference found — skip this block
        logger.debug("Block %d: no reference line found, skipping", sequence)
        return None

    # Extract raw text (everything after the reference line)
    raw_text = "\n".join(lines[text_start_idx:])

    # Extract section titles before cleaning
    section_title = _extract_section_title(raw_text)

    # Clean the text
    cleaned = _clean_text(raw_text, format_type)

    if not cleaned.strip():
        logger.debug("Block %d (%s): empty after cleaning, skipping", sequence, raw_ref)
        return None

    # Parse the reference
    chapter, paragraph = _parse_reference(ref_content, format_type)

    return SCParagraph(
        raw_ref=raw_ref,
        chapter=chapter,
        paragraph=paragraph,
        text=cleaned,
        sequence=sequence,
        section_title=section_title,
    )


# ---------------------------------------------------------------------------
# Reference parsing
# ---------------------------------------------------------------------------


def _parse_reference(
    ref_content: str, format_type: str
) -> tuple[str | None, str | None]:
    """Parse reference content into (chapter, paragraph).

    Args:
        ref_content: The text inside [...], e.g. "par.: 1" or "chap.: 4, par.: 2-3"
        format_type: One of "A", "B", "C", "D"

    Returns:
        Tuple of (chapter, paragraph). Either may be None.
    """
    if format_type == "A":
        return _parse_ref_format_a(ref_content)
    elif format_type == "B":
        return _parse_ref_format_b(ref_content)
    elif format_type == "C":
        return _parse_ref_format_c(ref_content)
    else:  # Format D (catch-all)
        return _parse_ref_format_d(ref_content)


def _parse_ref_format_a(ref: str) -> tuple[str | None, str | None]:
    """Format A: [par.: N] — paragraph only, no chapters."""
    m = _FMT_A_RE.match(ref)
    if m:
        return None, m.group(1)
    # Fallback for named sections in Format A files
    return ref, None


def _parse_ref_format_b(ref: str) -> tuple[str | None, str | None]:
    """Format B: [liv.: N, chap.: N, par.: N]"""
    m = _FMT_B_RE.match(ref)
    if m:
        # chapter = "N" (from chap. field), paragraph = "N" (from par. field)
        # We ignore liv. since it matches the file's book number
        return m.group(2), m.group(3)
    # Fallback
    logger.warning("Format B ref did not match: %s", ref)
    return ref, None


def _parse_ref_format_c(ref: str) -> tuple[str | None, str | None]:
    """Format C: [work_title, chap.: N]"""
    m = _FMT_C_RE.match(ref)
    if m:
        return m.group(1), None
    # Fallback for named sections
    return ref, None


def _parse_ref_format_d(ref: str) -> tuple[str | None, str | None]:
    """Format D: cascading regex patterns for diverse reference styles."""
    # D1: [chap.: N, par.: N-N]
    m = _FMT_D_CHAP_PAR_RE.match(ref)
    if m:
        return m.group(1), m.group(2)

    # D2: [chap.: N (desc), par.: N-N] — already covered by D1 with optional group
    m = _FMT_D_CHAP_DESC_PAR_RE.match(ref)
    if m:
        return m.group(1), m.group(2)

    # D3: [introduction, par.: N-N]
    m = _FMT_D_NAMED_PAR_RE.match(ref)
    if m:
        return m.group(1).strip(), m.group(2)

    # D4: [..., cap.: N, par.: N-N] — Aristides
    m = _FMT_D_CAP_PAR_RE.search(ref)  # search, not match — prefix may be long
    if m:
        return m.group(1), m.group(2)

    # D5: [chap.: N]
    m = _FMT_D_CHAP_ONLY_RE.match(ref)
    if m:
        return m.group(1), None

    # D6: [no: N]
    m = _FMT_D_NO_RE.match(ref)
    if m:
        return None, m.group(1)

    # D7: [page: N]
    m = _FMT_D_PAGE_RE.match(ref)
    if m:
        return None, m.group(1)

    # D8: [§ N]
    m = _FMT_D_SECTION_RE.match(ref)
    if m:
        return None, m.group(1)

    # D9: [par.: N] — same as Format A
    m = _FMT_D_PAR_RE.match(ref)
    if m:
        return None, m.group(1)

    # Fallback: named section (salutation, dédication, etc.)
    m = _FMT_D_NAMED_RE.match(ref)
    if m:
        return m.group(1).strip(), None

    logger.warning("Could not parse reference: [%s]", ref)
    return ref, None


# ---------------------------------------------------------------------------
# Text cleaning pipeline
# ---------------------------------------------------------------------------


def _extract_section_title(raw_text: str) -> str | None:
    """Extract section titles marked with ### TITLE ### from the raw text.

    Returns all section titles concatenated, or None if none found.
    """
    titles = _SECTION_TITLE_RE.findall(raw_text)
    if titles:
        return " — ".join(t.strip() for t in titles)
    return None


def _clean_text(raw: str, format_type: str) -> str:
    """Apply the 6-step cleaning pipeline. ORDER MATTERS.

    1. Strip TRADUCTION sections (Format B only)
    2. Remove SOURCE/LATIN markers
    3. Remove section title markers (### TITLE ###)
    4. Remove page number markers (--- 126 ---)
    5. Rejoin hyphenated line breaks
    6. Normalize whitespace
    """
    text = raw

    # Step 1: Strip TRADUCTION sections (keeps only SOURCE text)
    # This applies to Format B (SC268) and any file with TRADUCTION markers
    if _TRADUCTION_MARKER_RE.search(text):
        # Keep only the part before --- TRADUCTION ---
        parts = _TRADUCTION_MARKER_RE.split(text)
        text = parts[0]

    # Step 2: Remove SOURCE / LATIN markers (the marker lines themselves)
    text = _SOURCE_MARKER_RE.sub("", text)
    text = _LATIN_MARKER_RE.sub("", text)

    # Step 3: Remove section title markers ### TITLE ###
    text = _SECTION_TITLE_RE.sub("", text)

    # Step 4: Remove page number markers --- 126 ---
    text = _PAGE_MARKER_RE.sub("", text)

    # Step 5: Rejoin hyphenated line breaks (word- \n continuation)
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)

    # Step 6: Normalize whitespace
    # Collapse 3+ newlines to 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Strip leading/trailing whitespace
    text = text.strip()

    return text


# ---------------------------------------------------------------------------
# Chapter grouping
# ---------------------------------------------------------------------------


def _group_into_chapters(
    paragraphs: list[SCParagraph], format_type: str
) -> list[SCChapter]:
    """Group parsed paragraphs into SCChapter objects.

    Grouping logic depends on format:
    - Format A: Each paragraph is its own "chapter" (Contre Celse exception)
    - Format B: Group by chapter number from [liv.: N, chap.: N, par.: N]
    - Format C: Group by chapter number from [title, chap.: N]
    - Format D: Group by chapter field; named sections get their own chapter
    """
    # Track used chapter_refs to disambiguate duplicates (e.g., CC I has
    # two [par.: 9] blocks). Second occurrence gets "_b", third "_c", etc.
    ref_counts: dict[str, int] = {}

    def _unique_ref(ref: str) -> str:
        count = ref_counts.get(ref, 0) + 1
        ref_counts[ref] = count
        if count == 1:
            return ref
        # _b, _c, _d, ...
        return f"{ref}_{chr(95 + count)}"  # 2→'a'+1='b', 3→'c', etc.

    if format_type == "A":
        # Contre Celse: each paragraph is its own chapter
        return [
            SCChapter(
                chapter_ref=_unique_ref(p.paragraph or str(p.sequence)),
                paragraphs=[p],
            )
            for p in paragraphs
        ]

    # For all other formats: group by chapter field
    chapters: list[SCChapter] = []
    current_chapter_ref: str | None = None
    current_chapter: SCChapter | None = None

    for para in paragraphs:
        chapter_key = para.chapter

        if chapter_key is None:
            # No chapter structure (e.g., [no: N], [page: N]) —
            # each paragraph is its own chapter, like Format A
            if current_chapter is not None:
                chapters.append(current_chapter)
                current_chapter = None
                current_chapter_ref = None
            ref = _unique_ref(para.paragraph or str(para.sequence))
            chapters.append(SCChapter(chapter_ref=ref, paragraphs=[para]))
        elif chapter_key != current_chapter_ref:
            # Start a new chapter
            if current_chapter is not None:
                chapters.append(current_chapter)
            current_chapter_ref = chapter_key
            current_chapter = SCChapter(
                chapter_ref=_unique_ref(chapter_key),
                paragraphs=[para],
            )
        else:
            # Add to existing chapter
            assert current_chapter is not None
            current_chapter.paragraphs.append(para)

    # Don't forget the last chapter
    if current_chapter is not None:
        chapters.append(current_chapter)

    return chapters
