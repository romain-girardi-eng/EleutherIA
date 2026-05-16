"""Robust JSON extraction from LLM outputs.

Frontier models — and especially Kimi K2.6 served via Fireworks — sometimes
emit JSON wrapped in Markdown fences, prefixed with reasoning prose, or with
trailing commentary. This module is the single source of truth for recovering
a parseable JSON value from such outputs.

The recovery cascade, in order:

1. Direct ``json.loads`` after stripping whitespace and a leading ``json``
   marker.
2. Strip Markdown code fences (``` ... ``` or ```json ... ```), with or
   without a closing fence.
3. Apply lightweight repair: smart quotes, trailing commas, ``NaN`` literals,
   control characters.
4. Slice from the first ``{``/``[`` to the matching last ``}``/``]`` and
   retry, including repaired variants.
5. Walk the string and balance brace/bracket depth while ignoring string
   contents, to recover when the model emits a balanced JSON object
   followed by trailing prose.
6. As a last resort, attempt a guarded ``ast.literal_eval`` for outputs
   that look like Python dict literals.

All recovery steps are pure — no side effects, no network. The public API
is :func:`extract_json`; :func:`extract_json_object` enforces an object
result.
"""

from __future__ import annotations

import ast
import json
import re
from typing import Any

_CODE_FENCE_RE = re.compile(r"```(?:json|JSON)?\s*([\s\S]*?)```")
_TRAILING_COMMA_RE = re.compile(r",(\s*[}\]])")
_NAN_RE = re.compile(r":\s*NaN\b")
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


class JSONExtractionError(ValueError):
    """Raised when no recovery strategy yields valid JSON."""


def _repair(text: str) -> str:
    repaired = (
        text.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    )
    repaired = _TRAILING_COMMA_RE.sub(r"\1", repaired)
    repaired = _NAN_RE.sub(": null", repaired)
    repaired = _CONTROL_CHAR_RE.sub("", repaired)
    return repaired


def _try_loads(candidate: str) -> Any:
    try:
        return json.loads(candidate)
    except json.JSONDecodeError, ValueError:
        repaired = _repair(candidate)
        if repaired != candidate:
            try:
                return json.loads(repaired)
            except json.JSONDecodeError, ValueError:
                return None
        return None


def _strip_leading_marker(text: str) -> str:
    stripped = text.strip()
    # Models sometimes prefix with a bare "json" or "json:" marker.
    if stripped[:4].lower() == "json":
        rest = stripped[4:]
        if not rest or rest[0] in ":\n\t ":
            return rest.lstrip(": \n\t")
    return stripped


def _fence_payloads(text: str) -> list[str]:
    payloads: list[str] = []
    for match in _CODE_FENCE_RE.finditer(text):
        payloads.append(match.group(1).strip())
    # Fallback when the closing fence is missing.
    if not payloads and text.lstrip().startswith("```"):
        without_open = re.sub(r"^```(?:json|JSON)?\s*", "", text.lstrip(), count=1)
        without_open = without_open.rstrip()
        if without_open.endswith("```"):
            without_open = without_open[:-3].rstrip()
        if without_open:
            payloads.append(without_open)
    return payloads


def _bracket_slices(text: str) -> list[str]:
    """Return naive first-to-last slices for ``{...}`` and ``[...]``."""
    slices: list[str] = []
    if (start := text.find("{")) != -1 and (end := text.rfind("}")) > start:
        slices.append(text[start : end + 1])
    if (start := text.find("[")) != -1 and (end := text.rfind("]")) > start:
        slices.append(text[start : end + 1])
    return slices


def _balanced_scan(text: str) -> list[str]:
    """Return every balanced top-level ``{...}`` / ``[...]`` substring.

    Tracks string state so braces/brackets inside string literals don't
    confuse the depth counter. This recovers JSON that is followed by
    trailing natural-language prose.
    """
    out: list[str] = []
    for opener, closer in (("{", "}"), ("[", "]")):
        depth = 0
        start: int | None = None
        in_string = False
        escape = False
        for index, char in enumerate(text):
            if escape:
                escape = False
                continue
            if char == "\\" and in_string:
                escape = True
                continue
            if char == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if char == opener:
                if depth == 0:
                    start = index
                depth += 1
            elif char == closer:
                if depth == 0:
                    continue
                depth -= 1
                if depth == 0 and start is not None:
                    out.append(text[start : index + 1])
                    start = None
    return out


def _python_literal(text: str) -> Any:
    """Last-resort: parse Python dict/list literals (single quotes, True, etc.)."""
    try:
        value = ast.literal_eval(text)
    except ValueError, SyntaxError, MemoryError, TypeError:
        return None
    if isinstance(value, dict | list | str | int | float | bool) or value is None:
        return value
    return None


def extract_json(raw: str | bytes) -> Any:
    """Recover a JSON value from arbitrary LLM output.

    Raises :class:`JSONExtractionError` if every recovery strategy fails.
    """
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", errors="replace")
    if raw is None:
        raise JSONExtractionError("empty input")
    text = _strip_leading_marker(raw)
    if not text:
        raise JSONExtractionError("empty input")

    # 1) direct parse
    result = _try_loads(text)
    if result is not None:
        return result

    # 2) markdown code fences
    for payload in _fence_payloads(text):
        result = _try_loads(payload)
        if result is not None:
            return result

    # 3) bracket slice (first { ... last })
    for candidate in _bracket_slices(text):
        result = _try_loads(candidate)
        if result is not None:
            return result

    # 4) balanced scan (handles trailing prose)
    for candidate in _balanced_scan(text):
        result = _try_loads(candidate)
        if result is not None:
            return result

    # 5) python literal eval
    for candidate in (text, *_bracket_slices(text)):
        result = _python_literal(candidate)
        if result is not None:
            return result

    raise JSONExtractionError("no JSON value recovered from input")


def extract_json_object(raw: str | bytes) -> dict[str, Any]:
    """Recover and require a JSON object (``dict``)."""
    value = extract_json(raw)
    if isinstance(value, list):
        # Common Kimi pattern: the model emits a bare array when the schema
        # is ``{"foo": [...]}``. Wrap it under a conventional key so callers
        # can re-validate.
        return {"items": value}
    if not isinstance(value, dict):
        raise JSONExtractionError(f"expected JSON object, got {type(value).__name__}")
    return value


__all__ = [
    "JSONExtractionError",
    "extract_json",
    "extract_json_object",
]
