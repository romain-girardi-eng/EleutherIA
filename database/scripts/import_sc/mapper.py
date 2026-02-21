"""Mapper: SCWork → database insertion payloads.

Transforms parsed SCWork objects into INSERT-ready dictionaries for:
  - ancient_works
  - passages
  - kg_nodes (Work + Chapter/Paragraph)
  - kg_edges
  - passage_citations

ZERO LLM involvement — pure data transformation.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
import uuid

from .models import SCChapter, SCWork


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _slugify(text: str, max_len: int = 80) -> str:
    """Convert text to a URL/ID-safe slug.

    Lowercase, strip accents, replace spaces/hyphens with underscores,
    remove non-alphanumeric characters. Max ``max_len`` chars.

    When truncation occurs, the last 9 characters are replaced with an
    underscore + 8-char MD5 hash of the original text so that different
    long strings that share a common prefix still produce unique slugs.
    """
    normalized = unicodedata.normalize("NFD", text)
    ascii_text = "".join(
        c for c in normalized if unicodedata.category(c) != "Mn" and ord(c) < 128
    )
    slug = ascii_text.lower()
    slug = re.sub(r"[\s\-]+", "_", slug)
    slug = re.sub(r"[^a-z0-9_]", "", slug)
    slug = re.sub(r"_+", "_", slug)
    slug = slug.strip("_")

    if len(slug) > max_len:
        hash_suffix = hashlib.md5(text.encode()).hexdigest()[:8]
        slug = slug[: max_len - 9] + "_" + hash_suffix

    return slug


def _chapter_node_id(work: SCWork, chapter: SCChapter) -> str:
    """Build the KG node_id for a chapter or paragraph node."""
    ref = chapter.chapter_ref

    if work.reference_format == "A":
        # Contre Celse: paragraph-level nodes
        return f"{work.node_id}_par{ref}"

    # Numeric chapter refs
    if ref.isdigit():
        return f"{work.node_id}_chap{ref}"

    # Named section (salutation, introduction, etc.)
    slug = _slugify(ref)
    if not slug:
        slug = f"s{chapter.paragraphs[0].sequence}" if chapter.paragraphs else "unnamed"
    return f"{work.node_id}_{slug}"


def _build_canonical_ref(
    book: str, chapter_ref: str | None, paragraph: str | None
) -> str:
    """Build canonical_ref string from components (e.g. '1.4' or '3.1.1')."""
    parts = [book]
    if chapter_ref is not None:
        parts.append(chapter_ref)
    if paragraph is not None:
        parts.append(paragraph)
    return ".".join(parts)


def _build_cts_urn(
    sc_number: str, book: str, chapter_ref: str | None, paragraph: str | None
) -> str:
    """Build pseudo-CTS URN: urn:sc:{sc_number}:{book}.{chapter}.{paragraph}"""
    ref = _build_canonical_ref(book, chapter_ref, paragraph)
    return f"urn:sc:{sc_number}:{ref}"


def _division_scheme(work: SCWork) -> str:
    """Determine the division scheme text for ancient_works."""
    if work.reference_format == "A":
        return "paragraph"
    elif work.reference_format == "B":
        return "book.chapter.paragraph"
    elif work.reference_format == "C":
        return "chapter"
    else:
        has_paragraphs = any(
            p.paragraph is not None
            for ch in work.chapters
            for p in ch.paragraphs
        )
        return "chapter.paragraph" if has_paragraphs else "chapter"


def _citation_levels(work: SCWork) -> list[str]:
    """Determine citation_levels array for ancient_works."""
    if work.reference_format == "A":
        return ["paragraph"]
    elif work.reference_format == "B":
        return ["book", "chapter", "paragraph"]
    elif work.reference_format == "C":
        return ["chapter"]
    else:
        has_paragraphs = any(
            p.paragraph is not None
            for ch in work.chapters
            for p in ch.paragraphs
        )
        return ["chapter", "paragraph"] if has_paragraphs else ["chapter"]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def to_ancient_work(work: SCWork, run_id: str) -> dict:
    """Map SCWork → ancient_works INSERT payload.

    Generates a new UUID for work_id. Returns a dict ready for INSERT.
    """
    work_uuid = uuid.uuid4()

    # Compute totals
    all_text = "\n\n".join(
        p.text for ch in work.chapters for p in ch.paragraphs if p.text.strip()
    )
    total_words = len(all_text.split()) if all_text else 0
    total_chars = len(all_text) if all_text else 0

    return {
        "work_id": work_uuid,
        "canonical_id": work.node_id,
        "kg_work_id": work.node_id,
        "title": work.title,
        "title_original": work.title_original or None,
        "author": work.author,
        "author_original": None,
        "language": work.language,
        "period": work.period,
        "date_composed": work.date_composed,
        "school": work.school,
        "source": "sources_chretiennes",
        "division_scheme": _division_scheme(work),
        "citation_levels": _citation_levels(work),
        "total_divisions": work.total_paragraphs,
        "total_words": total_words,
        "total_chars": total_chars,
        "metadata": {
            "sc_number": work.sc_number,
            "sc_edition": work.edition,
            "sc_volume": f"SC {work.sc_number}",
            "date_composed": work.date_composed,
            "corpus_file": work.file_name,
            "kg_work_node": work.node_id,
            "phase": 1,
            "run_id": run_id,
        },
    }


def to_passages(work: SCWork, work_uuid: uuid.UUID, run_id: str) -> list[dict]:
    """Map SCWork paragraphs → passages INSERT payloads.

    One row per SCParagraph. Each dict includes a pre-generated passage_id UUID.

    Uses the chapter's uniquified chapter_ref (from ``_unique_ref``) rather
    than the raw ``para.chapter`` to guarantee each ``canonical_ref`` is
    unique within the work (required by DB UNIQUE constraint).
    """
    book = work.book or "1"
    passages: list[dict] = []
    seen_refs: dict[str, int] = {}  # canonical_ref → count

    for chapter in work.chapters:
        for para in chapter.paragraphs:
            passage_id = uuid.uuid4()

            # Use the chapter's unique ref (which has _a/_b suffixes for
            # duplicates) rather than the raw para.chapter.
            if work.reference_format == "A":
                # Format A: paragraphs ARE chapters; chapter_ref is the
                # paragraph number (uniquified).
                chapter_ref = None
                paragraph_ref = chapter.chapter_ref
            else:
                # All other formats: chapter.chapter_ref is uniquified.
                chapter_ref = chapter.chapter_ref
                paragraph_ref = para.paragraph

            canonical_ref = _build_canonical_ref(book, chapter_ref, paragraph_ref)

            # Final safety: deduplicate any remaining collisions (e.g.,
            # multiple paragraphs with the same number within one chapter).
            count = seen_refs.get(canonical_ref, 0) + 1
            seen_refs[canonical_ref] = count
            if count > 1:
                suffix = chr(95 + count)  # 2→'_a', 3→'_b', ...
                canonical_ref = f"{canonical_ref}_{suffix}"
                seen_refs[canonical_ref] = 1

            cts_urn = _build_cts_urn(
                work.sc_number, book, chapter_ref, paragraph_ref
            )

            citation_hierarchy: dict = {"sc_number": work.sc_number, "book": book}
            if chapter_ref is not None:
                citation_hierarchy["chapter"] = chapter_ref
            if paragraph_ref is not None:
                citation_hierarchy["paragraph"] = paragraph_ref

            passages.append({
                "passage_id": passage_id,
                "work_id": work_uuid,
                "canonical_ref": canonical_ref,
                "cts_urn": cts_urn,
                "book": book,
                "chapter": chapter_ref,
                "section": paragraph_ref,
                "sequence_number": para.sequence,
                "text_content": para.text,
                "char_length": len(para.text),
                "word_count": len(para.text.split()),
                "citation_hierarchy": citation_hierarchy,
            })

    return passages


def to_work_kg_node(
    work: SCWork,
    work_uuid: uuid.UUID,
    passage_data: list[dict],
    run_id: str,
) -> dict:
    """Map SCWork → kg_nodes INSERT payload (Work type).

    Includes the page_index tree in metadata for agentic traversal.
    """
    page_index = _build_page_index(work, passage_data)
    sc_vol = f"SC {work.sc_number}"
    label = f"{work.author}, {work.title} ({sc_vol})"

    return {
        "node_id": work.node_id,
        "label": label,
        "type": "Work",
        "description": work.description,
        "period": work.period,
        "school": work.school,
        "role": None,
        "metadata": {
            "sc_number": work.sc_number,
            "sc_edition": work.edition,
            "sc_volume": sc_vol,
            "language": work.language,
            "date_composed": work.date_composed,
            "author": work.author,
            "work_id": str(work_uuid),
            "phase": 1,
            "run_id": run_id,
            "total_chapters": len(work.chapters),
            "total_paragraphs": work.total_paragraphs,
            "page_index": page_index,
        },
    }


def _build_page_index(work: SCWork, passage_data: list[dict]) -> list[dict]:
    """Build the page-index tree for a Work node's metadata.

    Maps each chapter to its KG node_id and the passage_ids it contains.
    """
    seq_to_pid: dict[int, str] = {
        p["sequence_number"]: str(p["passage_id"]) for p in passage_data
    }

    index: list[dict] = []
    book = work.book or "1"

    for chapter in work.chapters:
        node_id = _chapter_node_id(work, chapter)
        passage_ids = [
            seq_to_pid[p.sequence]
            for p in chapter.paragraphs
            if p.sequence in seq_to_pid
        ]

        # URN from first paragraph in the chapter
        first = chapter.paragraphs[0] if chapter.paragraphs else None
        sc_urn = ""
        if first:
            sc_urn = _build_cts_urn(
                work.sc_number, book, first.chapter, first.paragraph
            )

        if work.reference_format == "A":
            index.append({
                "paragraph_ref": chapter.chapter_ref,
                "node_id": node_id,
                "sc_urn": sc_urn,
                "passage_id": passage_ids[0] if passage_ids else None,
            })
        else:
            index.append({
                "chapter_ref": chapter.chapter_ref,
                "node_id": node_id,
                "sc_urn": sc_urn,
                "paragraph_count": chapter.paragraph_count,
                "passage_ids": passage_ids,
            })

    return index


def to_chapter_kg_nodes(
    work: SCWork, passage_data: list[dict], run_id: str
) -> list[dict]:
    """Map SCWork chapters → kg_nodes INSERT payloads (Passage type).

    Standard works: one KG node per chapter (description = concatenated paragraphs).
    Contre Celse (format A): one KG node per paragraph.
    """
    seq_to_pid: dict[int, str] = {
        p["sequence_number"]: str(p["passage_id"]) for p in passage_data
    }

    nodes: list[dict] = []
    book = work.book or "1"

    for chapter in work.chapters:
        node_id = _chapter_node_id(work, chapter)

        # Label
        if work.reference_format == "A":
            label = f"{work.author}, {work.title}, \u00a7{chapter.chapter_ref}"
        elif chapter.chapter_ref.isdigit():
            label = f"{work.author}, {work.title}, chap. {chapter.chapter_ref}"
        else:
            label = f"{work.author}, {work.title}, {chapter.chapter_ref}"

        # Passage IDs
        passage_ids = [
            seq_to_pid[p.sequence]
            for p in chapter.paragraphs
            if p.sequence in seq_to_pid
        ]

        # Canonical ref and URN from first paragraph
        first = chapter.paragraphs[0] if chapter.paragraphs else None
        canonical_ref = ""
        sc_urn = ""
        if first:
            canonical_ref = _build_canonical_ref(book, first.chapter, first.paragraph)
            sc_urn = _build_cts_urn(
                work.sc_number, book, first.chapter, first.paragraph
            )

        # Description = full text of the chapter
        description = chapter.full_text

        metadata: dict = {
            "sc_number": work.sc_number,
            "work_node_id": work.node_id,
            "canonical_ref": canonical_ref,
            "sc_urn": sc_urn,
            "language": work.language,
            "phase": 1,
            "run_id": run_id,
        }

        if work.reference_format == "A":
            metadata["paragraph"] = chapter.chapter_ref
            metadata["passage_id"] = passage_ids[0] if passage_ids else None
        else:
            metadata["chapter"] = chapter.chapter_ref
            metadata["paragraph_count"] = chapter.paragraph_count
            metadata["passage_ids"] = passage_ids

        nodes.append({
            "node_id": node_id,
            "label": label,
            "type": "Passage",
            "description": description,
            "period": work.period,
            "school": work.school,
            "role": None,
            "metadata": metadata,
        })

    return nodes


def to_kg_edges(
    work: SCWork, chapter_nodes: list[dict], run_id: str
) -> list[dict]:
    """Generate all KG edges for this work.

    Edge types:
      - has_chapter / has_section: Work → Chapter/Paragraph nodes
      - wrote: Person → Work (if author_kg_id exists)
      - continues: Work → next Work (if series_next exists)
      - belongs_to_corpus: Work → sources_chretiennes
    """
    edges: list[dict] = []

    # 1. Work → Chapter/Paragraph nodes
    relation = "has_section" if work.reference_format == "A" else "has_chapter"
    for ch_node in chapter_nodes:
        edges.append({
            "edge_id": uuid.uuid4(),
            "source_id": work.node_id,
            "target_id": ch_node["node_id"],
            "relation": relation,
            "metadata": {"phase": 1, "run_id": run_id},
        })

    # 2. Author → Work (if Person node exists in KG)
    if work.author_kg_id:
        edges.append({
            "edge_id": uuid.uuid4(),
            "source_id": work.author_kg_id,
            "target_id": work.node_id,
            "relation": "wrote",
            "metadata": {"phase": 1, "run_id": run_id},
        })

    # 3. Series continuation
    if work.series_next:
        edges.append({
            "edge_id": uuid.uuid4(),
            "source_id": work.node_id,
            "target_id": work.series_next,
            "relation": "continues",
            "metadata": {"phase": 1, "run_id": run_id},
        })

    # 4. Belongs to SC corpus
    edges.append({
        "edge_id": uuid.uuid4(),
        "source_id": work.node_id,
        "target_id": "sources_chretiennes",
        "relation": "belongs_to_corpus",
        "metadata": {"phase": 1, "run_id": run_id},
    })

    return edges


def to_passage_citations(
    passage_data: list[dict],
    chapter_nodes: list[dict],
    work: SCWork,
    run_id: str,
) -> list[dict]:
    """Link each passage row to its chapter/paragraph KG node.

    Confidence = 1.0 because these are direct primary source extractions.
    """
    citations: list[dict] = []

    # Build string(passage_id) → UUID lookup
    pid_to_uuid: dict[str, uuid.UUID] = {
        str(p["passage_id"]): p["passage_id"] for p in passage_data
    }

    for ch_node in chapter_nodes:
        node_id = ch_node["node_id"]
        meta = ch_node["metadata"]

        if work.reference_format == "A":
            # CC: single passage per paragraph node
            pid = meta.get("passage_id")
            if pid and pid in pid_to_uuid:
                citations.append({
                    "citation_id": uuid.uuid4(),
                    "passage_id": pid_to_uuid[pid],
                    "kg_node_id": node_id,
                    "citation_type": "primary_source",
                    "confidence": 1.0,
                })
        else:
            # Standard: multiple passages per chapter node
            for pid in meta.get("passage_ids", []):
                if pid in pid_to_uuid:
                    citations.append({
                        "citation_id": uuid.uuid4(),
                        "passage_id": pid_to_uuid[pid],
                        "kg_node_id": node_id,
                        "citation_type": "primary_source",
                        "confidence": 1.0,
                    })

    return citations


# ---------------------------------------------------------------------------
# Convenience: full pipeline
# ---------------------------------------------------------------------------


def map_work(work: SCWork, run_id: str) -> dict:
    """Run the full mapping pipeline for a single work.

    Returns a dict with all insertion payloads:
      - ancient_work: dict
      - passages: list[dict]
      - work_kg_node: dict
      - chapter_kg_nodes: list[dict]
      - kg_edges: list[dict]
      - passage_citations: list[dict]
    """
    aw = to_ancient_work(work, run_id)
    work_uuid = aw["work_id"]

    passages = to_passages(work, work_uuid, run_id)
    work_node = to_work_kg_node(work, work_uuid, passages, run_id)
    chapter_nodes = to_chapter_kg_nodes(work, passages, run_id)
    edges = to_kg_edges(work, chapter_nodes, run_id)
    citations = to_passage_citations(passages, chapter_nodes, work, run_id)

    return {
        "ancient_work": aw,
        "passages": passages,
        "work_kg_node": work_node,
        "chapter_kg_nodes": chapter_nodes,
        "kg_edges": edges,
        "passage_citations": citations,
    }
