"""Sentence-aware truncation utilities for the GraphRAG pipeline.

These replace character-level slicing (``text[:800]``) that corrupts
Greek/Latin diacritics, mid-word characters, and markdown formatting.
"""

from __future__ import annotations

import json
import re

# Sentence-ending punctuation: Latin (. ? !), Greek (· ;)
_SENTENCE_END_RE = re.compile(r"[.;·?!]\s")

TRUNCATION_SUFFIX = " [...]"


def truncate_text(text: str | None, max_chars: int) -> str:
    """Truncate *text* at the last sentence boundary before *max_chars*.

    Falls back to the last whitespace boundary if no sentence-ending
    punctuation is found.  Returns the original string unchanged when
    it already fits within the budget.

    A ``" [...]"`` suffix is appended to signal that the text was cut.
    """
    if not text:
        return ""
    if len(text) <= max_chars:
        return text

    budget = max_chars - len(TRUNCATION_SUFFIX)
    if budget <= 0:
        return text[:max_chars]

    window = text[:budget]

    # Try to cut at the last sentence boundary
    last_sentence = -1
    for m in _SENTENCE_END_RE.finditer(window):
        last_sentence = m.end()

    if last_sentence > 0:
        return text[:last_sentence].rstrip() + TRUNCATION_SUFFIX

    # Fallback: cut at last whitespace
    last_space = window.rfind(" ")
    if last_space > 0:
        return text[:last_space].rstrip() + TRUNCATION_SUFFIX

    # Last resort: hard cut at budget
    return window + TRUNCATION_SUFFIX


def truncate_json(data: list | dict, max_chars: int) -> str:
    """Serialize *data* to JSON, trimming trailing list items if too long.

    For lists: removes trailing items one-by-one until the serialized
    JSON fits within *max_chars*.  This guarantees structurally valid
    JSON (no broken mid-object slicing).

    For non-list data: serializes normally and falls back to
    ``truncate_text`` if too long.
    """
    raw = json.dumps(data, ensure_ascii=False)
    if len(raw) <= max_chars:
        return raw

    if isinstance(data, list):
        items = list(data)
        while items:
            items.pop()
            raw = json.dumps(items, ensure_ascii=False)
            if len(raw) <= max_chars:
                return raw
        return "[]"

    # For dicts or other structures, fall back to text truncation
    return truncate_text(raw, max_chars)
