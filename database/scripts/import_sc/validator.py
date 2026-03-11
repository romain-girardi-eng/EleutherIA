"""Validator for the SC import pipeline.

Implements quality gates from the design doc §12:
  Gate 1 (pre-import): file/parse/content checks
  Gate 2 (dry-run):    statistics sanity checks
"""

from __future__ import annotations

import re

from .config import WORK_REGISTRY
from .models import SCWork

# ---------------------------------------------------------------------------
# Gate 1: Per-work validation
# ---------------------------------------------------------------------------


def validate_work(work: SCWork) -> list[str]:
    """Validate a single parsed SCWork. Returns list of error/warning messages.

    Empty list = valid. Messages prefixed with ERROR or WARN.
    """
    messages: list[str] = []

    # 1. Must have an entry in WORK_REGISTRY
    if work.file_name not in WORK_REGISTRY:
        messages.append(f"ERROR: {work.file_name} has no entry in WORK_REGISTRY")

    # 2. Header must have AUTEUR/OEUVRE fields
    if not work.author:
        messages.append(f"WARN: {work.file_name} missing AUTEUR in header")
    if not work.title:
        messages.append(f"WARN: {work.file_name} missing OEUVRE in header")

    # 3. Must have a node_id
    if not work.node_id:
        messages.append(f"ERROR: {work.file_name} has no node_id")

    # 4. Must have at least one paragraph
    if work.total_paragraphs == 0:
        messages.append(f"ERROR: {work.file_name} has 0 paragraphs after parsing")

    # 5. Paragraph count should be close to declared count
    if work.declared_paragraphs > 0:
        diff = abs(work.total_paragraphs - work.declared_paragraphs)
        pct = diff / work.declared_paragraphs * 100
        if pct > 10:
            messages.append(
                f"WARN: {work.file_name} paragraph count mismatch: "
                f"parsed {work.total_paragraphs} vs declared {work.declared_paragraphs} "
                f"({pct:.0f}% difference)"
            )

    # 6. No TRADUCTION markers should remain in text after cleaning
    for ch in work.chapters:
        for para in ch.paragraphs:
            if "--- TRADUCTION ---" in para.text:
                messages.append(
                    f"ERROR: {work.file_name} [{para.raw_ref}] still contains "
                    f"TRADUCTION marker after cleaning"
                )
                break
        else:
            continue
        break

    # 7. No empty text blocks
    empty_count = sum(
        1
        for ch in work.chapters
        for p in ch.paragraphs
        if not p.text.strip()
    )
    if empty_count > 0:
        messages.append(
            f"WARN: {work.file_name} has {empty_count} empty text block(s)"
        )

    # 8. Greek texts should contain Greek Unicode (U+0370-U+1FFF)
    if work.language == "grc":
        has_greek = False
        for ch in work.chapters:
            for p in ch.paragraphs:
                if re.search(r"[\u0370-\u1FFF]", p.text):
                    has_greek = True
                    break
            if has_greek:
                break
        if not has_greek:
            messages.append(
                f"WARN: {work.file_name} is tagged 'grc' but contains "
                f"no Greek Unicode characters"
            )

    # 9. No text block should exceed 100KB (likely parsing error)
    for ch in work.chapters:
        for p in ch.paragraphs:
            if len(p.text.encode("utf-8")) > 100_000:
                messages.append(
                    f"WARN: {work.file_name} [{p.raw_ref}] text exceeds "
                    f"100KB ({len(p.text.encode('utf-8'))} bytes)"
                )

    return messages


# ---------------------------------------------------------------------------
# Gate 1: Corpus-level validation
# ---------------------------------------------------------------------------


def validate_corpus(works: list[SCWork]) -> tuple[list[str], list[str]]:
    """Validate entire corpus. Returns (errors, warnings).

    Checks cross-work uniqueness and completeness.
    """
    errors: list[str] = []
    warnings: list[str] = []

    # 1. All 40 files should be present
    expected = set(WORK_REGISTRY.keys())
    found = {w.file_name for w in works}
    missing = expected - found
    if missing:
        for f in sorted(missing):
            errors.append(f"ERROR: Expected file not found: {f}")
    extra = found - expected
    if extra:
        for f in sorted(extra):
            warnings.append(f"WARN: Unexpected file found: {f}")

    # 2. All node_ids must be globally unique
    node_ids: dict[str, str] = {}
    for w in works:
        if w.node_id in node_ids:
            errors.append(
                f"ERROR: Duplicate node_id '{w.node_id}' in "
                f"{w.file_name} and {node_ids[w.node_id]}"
            )
        else:
            node_ids[w.node_id] = w.file_name

    # 3. All chapter node_ids must be globally unique
    chapter_ids: dict[str, str] = {}
    for w in works:
        for ch in w.chapters:
            from .mapper import _chapter_node_id

            ch_id = _chapter_node_id(w, ch)
            source = f"{w.file_name}:{ch.chapter_ref}"
            if ch_id in chapter_ids:
                errors.append(
                    f"ERROR: Duplicate chapter node_id '{ch_id}' in "
                    f"{source} and {chapter_ids[ch_id]}"
                )
            else:
                chapter_ids[ch_id] = source

    # 4. Per-work validation
    for w in works:
        msgs = validate_work(w)
        for msg in msgs:
            if msg.startswith("ERROR"):
                errors.append(msg)
            else:
                warnings.append(msg)

    return errors, warnings
