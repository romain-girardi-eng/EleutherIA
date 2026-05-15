"""Regression tests for the robust JSON extractor.

Each fixture reproduces a real failure mode observed in Kimi K2.6 outputs
during the Wave 7 smoke test (Bobzien vs Frede query). The extractor must
recover a usable JSON value from every one of them.
"""

from __future__ import annotations

import pytest

from eleutheria_graphrag.services.json_extractor import (
    JSONExtractionError,
    extract_json,
    extract_json_object,
)


def test_plain_json_object() -> None:
    raw = '{"claims": [{"claim": "x"}]}'
    assert extract_json(raw) == {"claims": [{"claim": "x"}]}


def test_strips_json_code_fence() -> None:
    raw = '```json\n{"claims": []}\n```'
    assert extract_json(raw) == {"claims": []}


def test_strips_bare_code_fence() -> None:
    raw = '```\n{"k": 1}\n```'
    assert extract_json(raw) == {"k": 1}


def test_handles_unterminated_fence() -> None:
    raw = '```json\n{"k": 1}'
    assert extract_json(raw) == {"k": 1}


def test_handles_leading_json_marker() -> None:
    raw = 'json:\n{"k": 1}'
    assert extract_json(raw) == {"k": 1}


def test_recovers_from_leading_reasoning_prose() -> None:
    """The classic Kimi failure: the model narrates before emitting JSON."""
    raw = (
        "The user wants me to build a claim ledger for a scholarly answer "
        "about Stoic compatibilism. Here is the structured output:\n\n"
        '{"claims": [{"claim": "Bobzien argues..."}]}'
    )
    parsed = extract_json(raw)
    assert isinstance(parsed, dict)
    assert parsed["claims"][0]["claim"] == "Bobzien argues..."


def test_recovers_from_trailing_prose() -> None:
    raw = '{"claims": []}\n\nLet me know if you want me to expand any item.'
    assert extract_json(raw) == {"claims": []}


def test_recovers_smart_quotes() -> None:
    raw = "{“claim”: “x”}"
    assert extract_json(raw) == {"claim": "x"}


def test_strips_trailing_commas() -> None:
    raw = '{"claims": [{"claim": "x",},],}'
    assert extract_json(raw) == {"claims": [{"claim": "x"}]}


def test_strips_control_characters() -> None:
    raw = '{"k": "value\x01with\x02control"}'
    parsed = extract_json(raw)
    assert isinstance(parsed, dict)
    assert "value" in parsed["k"]


def test_python_literal_fallback() -> None:
    """Last-resort recovery for Python-dict-style outputs."""
    raw = "{'k': 1, 'list': [True, None]}"
    parsed = extract_json(raw)
    assert parsed == {"k": 1, "list": [True, None]}


def test_bare_array_returned_as_items() -> None:
    raw = '[{"claim": "a"}, {"claim": "b"}]'
    obj = extract_json_object(raw)
    assert obj == {"items": [{"claim": "a"}, {"claim": "b"}]}


def test_raises_on_complete_garbage() -> None:
    with pytest.raises(JSONExtractionError):
        extract_json("absolutely nothing parseable here at all")


def test_raises_on_empty() -> None:
    with pytest.raises(JSONExtractionError):
        extract_json("")


def test_extract_json_object_rejects_scalar() -> None:
    with pytest.raises(JSONExtractionError):
        extract_json_object("42")


def test_balanced_scan_ignores_braces_in_strings() -> None:
    """Braces inside string literals must not confuse the balanced scan."""
    raw = '{"text": "he said {hello}"} trailing prose with stray { brace'
    parsed = extract_json(raw)
    assert parsed == {"text": "he said {hello}"}


def test_nested_fenced_json_with_prose() -> None:
    raw = (
        "Thinking... I'll produce the ledger.\n\n"
        "```json\n"
        '{\n  "claims": [\n    {"claim": "x", "evidence_ids": []}\n  ]\n}\n'
        "```\n\nDone."
    )
    parsed = extract_json(raw)
    assert parsed["claims"][0]["claim"] == "x"
