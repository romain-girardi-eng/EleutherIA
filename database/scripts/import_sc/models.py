"""Data models for Sources Chrétiennes import pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SCParagraph:
    """A single paragraph block from a source file (delimited by ===== lines)."""

    raw_ref: str  # e.g., "[par.: 1]" or "[chap.: 4, par.: 2-3]"
    chapter: str | None  # Parsed chapter number or name (e.g., "4", "salutation")
    paragraph: str | None  # Parsed paragraph number (e.g., "1", "2-3", None)
    text: str  # Cleaned original text (Greek or Latin)
    sequence: int  # 0-indexed within work
    section_title: str | None = None  # e.g., "TITLE" if extracted from ### TITLE ###


@dataclass
class SCChapter:
    """A chapter-level grouping of paragraphs."""

    chapter_ref: str  # e.g., "1", "salutation", "III.1"
    paragraphs: list[SCParagraph] = field(default_factory=list)

    @property
    def full_text(self) -> str:
        """Concatenation of all paragraph texts, separated by double newline."""
        return "\n\n".join(p.text for p in self.paragraphs if p.text.strip())

    @property
    def paragraph_count(self) -> int:
        return len(self.paragraphs)


@dataclass
class SCWork:
    """A parsed source file representing one work or book."""

    file_path: str
    file_name: str  # Just the filename (no directory)
    sc_number: str  # e.g., "507", "10bis", "132"
    author: str  # From file header AUTEUR field
    title: str  # From file header OEUVRE field
    title_original: str  # From file header TITRE ORIGINAL field (may be empty)
    book: str  # From file header LIVRE field
    declared_paragraphs: int  # From file header PARAGRAPHES field
    language: str  # "grc" or "lat"
    chapters: list[SCChapter] = field(default_factory=list)

    # Populated from WORK_REGISTRY:
    node_id: str = ""
    edition: str = ""
    date_composed: str = ""
    description: str = ""
    period: str = ""
    school: str = ""
    reference_format: str = ""  # "A", "B", "C", or "D"
    author_kg_id: str | None = None
    series_prev: str | None = None
    series_next: str | None = None

    @property
    def total_paragraphs(self) -> int:
        return sum(ch.paragraph_count for ch in self.chapters)

    @property
    def canonical_id(self) -> str:
        return self.node_id
