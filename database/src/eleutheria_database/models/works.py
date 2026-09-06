"""
Pydantic models for ancient works and passages.

These models represent the core entities in the EleutherIA database:
- AncientWork: Canonical scholarly texts
- Passage: Hierarchical text units within works
- PassageCitation: Links between passages and knowledge graph nodes
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AncientWork(BaseModel):
    """
    A canonical ancient text with scholarly metadata.

    Supports CTS URN for canonical references and TEI XML markup.
    """

    model_config = ConfigDict(from_attributes=True)

    work_id: UUID
    canonical_id: str = Field(
        ..., description="Unique identifier, e.g., 'chrysippus_on_fate'"
    )
    title: str
    title_original: str | None = Field(None, description="Original Greek/Latin title")
    author: str
    author_original: str | None = Field(
        None, description="Original Greek/Latin author name"
    )
    language: str = Field(
        ..., description="Language code: grc, lat, eng, fra, hbo, ara"
    )
    period: str | None = Field(
        None, description="Historical period, e.g., 'Hellenistic'"
    )
    date_composed: str | None = Field(
        None, description="Approximate date, e.g., '3rd c. BCE'"
    )
    school: str | None = Field(None, description="Philosophical school, e.g., 'Stoic'")
    source: str | None = Field(None, description="Data source: perseus, tlg, sblgnt")
    source_url: str | None = None
    license: str | None = None
    division_scheme: str | None = Field(
        None, description="e.g., 'book.chapter.section'"
    )
    total_divisions: int | None = None
    total_words: int | None = None
    total_chars: int | None = None
    notes: str | None = None
    metadata: dict[str, Any] | None = None
    cts_urn: str | None = Field(None, description="Canonical Text Services URN")
    citation_levels: list[str] | None = Field(
        None, description="e.g., ['book', 'chapter', 'verse']"
    )
    has_morphology: bool = Field(False, description="Whether OGA lemmatization exists")
    created_at: datetime | None = None
    updated_at: datetime | None = None


class Passage(BaseModel):
    """
    A hierarchical text unit within an ancient work.

    Passages have structured references (book, chapter, section) and
    can be linked to knowledge graph nodes via PassageCitation.
    """

    model_config = ConfigDict(from_attributes=True)

    passage_id: UUID
    work_id: UUID
    canonical_ref: str = Field(
        ..., description="Reference, e.g., '3.191' or 'Matthew 5:3'"
    )
    cts_urn: str | None = Field(None, description="Full CTS URN for this passage")
    book: str | None = None
    chapter: str | None = None
    section: str | None = None
    subsection: str | None = None
    line_start: str | None = None
    line_end: str | None = None
    sequence_number: int = Field(..., ge=0, description="Order within work")
    text_content: str
    char_length: int | None = None
    word_count: int | None = None
    notes: str | None = None
    citation_hierarchy: dict[str, Any] | None = None
    morphology: dict[str, Any] | None = Field(None, description="Lemmatization data")
    created_at: datetime | None = None

    # Optional navigation
    previous_passage_id: UUID | None = None
    next_passage_id: UUID | None = None


class PassageCitation(BaseModel):
    """
    A link between a passage and a knowledge graph node.

    Citations have confidence scores (0.0-1.0) based on textual evidence strength.
    """

    model_config = ConfigDict(from_attributes=True)

    citation_id: UUID
    passage_id: UUID
    kg_node_id: str = Field(..., description="Knowledge graph node identifier")
    citation_type: str | None = Field(
        None, description="e.g., 'primary_source', 'secondary_source'"
    )
    confidence: float | None = Field(
        None, ge=0.0, le=1.0, description="Citation confidence"
    )
    notes: str | None = None
    created_at: datetime | None = None


class PassageRelationship(BaseModel):
    """
    An inter-passage relationship (quotation, allusion, parallel).
    """

    model_config = ConfigDict(from_attributes=True)

    relationship_id: UUID
    source_passage_id: UUID
    target_passage_id: UUID
    relationship_type: str = Field(
        ..., description="e.g., 'quotes', 'alludes_to', 'parallel'"
    )
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    created_at: datetime | None = None
