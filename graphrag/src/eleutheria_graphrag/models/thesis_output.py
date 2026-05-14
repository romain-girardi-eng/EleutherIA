"""
Thesis-grade structured output schema.

The synthesizer emits a ``ThesisDraft`` (sections / footnotes / bibliography)
which the renderer converts to Markdown, LaTeX, BibTeX, Zotero JSON or RIS.

Two invariants enforced by Pydantic validation:

1. Every footnote carries at least one citation (no orphan footnotes).
2. The draft must contain at least one footnote and one bibliography entry
   (no claim is allowed to float unsourced).
"""

from __future__ import annotations

import re
import unicodedata
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

CitationKind = Literal["primary", "secondary"]


_ASCII_FALLBACK = {
    "ß": "ss",
    "æ": "ae",
    "œ": "oe",
    "ø": "o",
    "ð": "d",
    "þ": "th",
    "Æ": "Ae",
    "Œ": "Oe",
    "Ø": "O",
    "Þ": "Th",
}


def slugify_ascii(value: str) -> str:
    """Slug-safe ASCII fragment used for BibTeX keys.

    Strips diacritics, replaces non-alphanumerics with hyphens and lowercases.
    Empty input falls back to ``"anon"`` so a key is always generated.
    """

    if not value:
        return "anon"
    folded = "".join(_ASCII_FALLBACK.get(ch, ch) for ch in value)
    decomposed = unicodedata.normalize("NFKD", folded)
    ascii_only = decomposed.encode("ascii", "ignore").decode("ascii")
    ascii_only = re.sub(r"[^A-Za-z0-9]+", "-", ascii_only).strip("-").lower()
    return ascii_only or "anon"


class Citation(BaseModel):
    """A single textual reference attached to a footnote.

    ``passage_id`` should reference a row in the corpus ``passages`` table or
    a knowledge-graph node id. Greek quotations must be verbatim (no
    AI-reconstructed text).
    """

    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

    passage_id: str = Field(
        ..., min_length=1, description="Corpus passage id or KG node id"
    )
    cts_urn: str | None = Field(None, description="Canonical Text Services URN")
    work_label: str = Field(..., min_length=1, description="Work title")
    author: str | None = Field(None, description="Ancient or modern author")
    edition: str | None = Field(
        None, description="Critical edition (e.g. 'Bywater 1894')"
    )
    translation: str | None = Field(None, description="Translation (e.g. 'Ross 1925')")
    page_or_section: str | None = Field(
        None, description="Page or section (e.g. '1110a4-6' or 'p. 234')"
    )
    quote_greek: str | None = Field(
        None, description="Verbatim ancient quotation (Greek / Latin)"
    )
    quote_translation: str | None = Field(
        None, description="English translation of the quote"
    )
    scholar_id: str | None = Field(
        None,
        description="Secondary-scholar identifier when the citation is to modern scholarship",
    )


class Footnote(BaseModel):
    """Numbered footnote referenced from one or more paragraphs."""

    model_config = ConfigDict(from_attributes=True)

    n: int = Field(..., ge=1, description="Footnote number (1-indexed)")
    text: str = Field(..., min_length=1, description="Footnote prose")
    citations: list[Citation] = Field(
        ..., min_length=1, description="Backing citations"
    )


class Paragraph(BaseModel):
    """A paragraph of synthesized prose with explicit footnote anchors."""

    model_config = ConfigDict(from_attributes=True)

    text: str = Field(..., min_length=1)
    footnote_refs: list[int] = Field(
        default_factory=list,
        description="Footnote numbers referenced by this paragraph (in order)",
    )


class Section(BaseModel):
    """A top-level or nested section of the draft."""

    model_config = ConfigDict(from_attributes=True)

    heading: str = Field(..., min_length=1)
    level: int = Field(1, ge=1, le=6, description="Markdown heading depth (1 = top)")
    paragraphs: list[Paragraph] = Field(default_factory=list)


class BibliographyEntry(BaseModel):
    """A bibliography entry.

    ``bibtex_key`` is auto-derived from the author / year / title when the
    caller leaves it blank. It is always ASCII so it survives LaTeX / BibTeX.
    """

    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

    kind: CitationKind = Field(
        ..., description="primary (ancient source) or secondary (modern)"
    )
    author: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    year: int | None = Field(None, description="Publication year")
    edition: str | None = Field(None, description="Edition / editor info")
    publisher: str | None = Field(None, description="Publisher (modern works)")
    pages: str | None = Field(None, description="Page range")
    url: str | None = Field(None, description="DOI / URL")
    cts_urn: str | None = Field(None, description="CTS URN for primary sources")
    bibtex_key: str = Field("", description="ASCII BibTeX key; auto-derived if blank")

    @model_validator(mode="after")
    def _derive_bibtex_key(self) -> BibliographyEntry:
        if self.bibtex_key:
            # Force ASCII safety even if the caller supplied a value.
            cleaned = slugify_ascii(self.bibtex_key)
            object.__setattr__(self, "bibtex_key", cleaned)
            return self
        author_slug = slugify_ascii(self.author.split(",")[0])
        title_slug = slugify_ascii(self.title.split(":")[0])[:32]
        year_slug = str(self.year) if self.year else "nd"
        key = f"{author_slug}-{title_slug}-{year_slug}".strip("-")
        object.__setattr__(self, "bibtex_key", key or "ref")
        return self


class ThesisDraft(BaseModel):
    """Root schema emitted by the synthesizer.

    Strict rules:

    * at least one footnote AND one bibliography entry,
    * every ``footnote_refs`` entry in a paragraph must point to an existing
      footnote number,
    * BibTeX keys are unique (suffix collisions get a numeric tail).
    """

    model_config = ConfigDict(from_attributes=True)

    title: str = Field(..., min_length=1)
    abstract: str | None = None
    sections: list[Section] = Field(..., min_length=1)
    footnotes: list[Footnote] = Field(..., min_length=1)
    bibliography: list[BibliographyEntry] = Field(..., min_length=1)
    methodology_notes: list[str] = Field(default_factory=list)
    flagged_claims: list[str] = Field(default_factory=list)

    @field_validator("footnotes")
    @classmethod
    def _check_footnote_numbering(cls, footnotes: list[Footnote]) -> list[Footnote]:
        seen: set[int] = set()
        for note in footnotes:
            if note.n in seen:
                raise ValueError(f"duplicate footnote number: {note.n}")
            seen.add(note.n)
        return footnotes

    @model_validator(mode="after")
    def _check_footnote_refs(self) -> ThesisDraft:
        valid_numbers = {note.n for note in self.footnotes}
        for section in self.sections:
            for paragraph in section.paragraphs:
                for ref in paragraph.footnote_refs:
                    if ref not in valid_numbers:
                        raise ValueError(
                            f"paragraph references missing footnote n={ref}; "
                            f"available={sorted(valid_numbers)}"
                        )
        # Disambiguate duplicate bibtex keys deterministically.
        counts: dict[str, int] = {}
        for entry in self.bibliography:
            base = entry.bibtex_key
            seen = counts.get(base, 0)
            if seen:
                object.__setattr__(entry, "bibtex_key", f"{base}-{seen + 1}")
            counts[base] = seen + 1
        return self


def thesis_draft_json_schema() -> dict:
    """JSON Schema for ``response_format=json_schema`` LLM calls.

    Pydantic emits ``$defs`` references; the helper returns the schema as-is —
    consumers (Fireworks / OpenAI) accept that shape.
    """

    return ThesisDraft.model_json_schema()


__all__ = [
    "BibliographyEntry",
    "Citation",
    "CitationKind",
    "Footnote",
    "Paragraph",
    "Section",
    "ThesisDraft",
    "slugify_ascii",
    "thesis_draft_json_schema",
]
