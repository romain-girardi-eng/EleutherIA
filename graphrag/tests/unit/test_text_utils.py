"""Tests for sentence-aware truncation utilities."""

from __future__ import annotations

import json

from eleutheria_graphrag.agents.text_utils import (
    TRUNCATION_SUFFIX,
    truncate_json,
    truncate_text,
)

# ---------------------------------------------------------------------------
# truncate_text
# ---------------------------------------------------------------------------


class TestTruncateText:
    def test_short_text_unchanged(self):
        text = "Hello world."
        assert truncate_text(text, 100) == text

    def test_exact_length_unchanged(self):
        text = "Hello world."
        assert truncate_text(text, len(text)) == text

    def test_none_returns_empty(self):
        assert truncate_text(None, 100) == ""

    def test_empty_returns_empty(self):
        assert truncate_text("", 100) == ""

    def test_cuts_at_sentence_boundary(self):
        text = "First sentence. Second sentence. Third sentence."
        result = truncate_text(text, 35)
        assert result.endswith(TRUNCATION_SUFFIX)
        # Should cut after "First sentence." (16 chars + space)
        assert "First sentence." in result
        assert "Third" not in result

    def test_falls_back_to_whitespace(self):
        text = "word1 word2 word3 word4 word5 word6"
        result = truncate_text(text, 20)
        assert result.endswith(TRUNCATION_SUFFIX)
        assert "word1" in result

    def test_greek_text_preserved(self):
        """Greek diacritics must not be corrupted by truncation."""
        text = (
            "Ἀρχῶν τῶν ὄντων τὸ ἄπειρον. "
            "ἐξ ὧν δὲ ἡ γένεσίς ἐστι τοῖς οὖσι. "
            "κατὰ τὸ χρεών."
        )
        result = truncate_text(text, 50)
        assert result.endswith(TRUNCATION_SUFFIX)
        # The Greek text should not be garbled mid-character
        assert "Ἀρχῶν" in result

    def test_greek_semicolon_as_sentence_end(self):
        """Greek question mark (;) and middle dot (·) should be sentence ends."""
        text = "τί ἐστιν ἀρετή; ἡ ἀρετή ἐστιν ἀγαθόν· τοῦτο σαφές."
        result = truncate_text(text, 40)
        assert result.endswith(TRUNCATION_SUFFIX)
        # Should cut after the Greek question mark
        assert "τί ἐστιν ἀρετή;" in result

    def test_very_small_budget(self):
        text = "Hello world, this is a test."
        result = truncate_text(text, 8)
        # With budget < suffix length, just hard-cut
        assert len(result) <= 8 + len(TRUNCATION_SUFFIX)

    def test_multiline_text(self):
        text = "First paragraph.\n\nSecond paragraph. More text here.\n\nThird."
        result = truncate_text(text, 40)
        assert "First paragraph." in result
        assert result.endswith(TRUNCATION_SUFFIX)


# ---------------------------------------------------------------------------
# truncate_json
# ---------------------------------------------------------------------------


class TestTruncateJson:
    def test_small_list_unchanged(self):
        data = [{"a": 1}, {"b": 2}]
        result = truncate_json(data, 10000)
        assert json.loads(result) == data

    def test_list_truncation_produces_valid_json(self):
        data = [{"text": "x" * 100} for _ in range(20)]
        result = truncate_json(data, 500)
        parsed = json.loads(result)  # Must parse without error
        assert isinstance(parsed, list)
        assert len(parsed) < 20

    def test_empty_list_fallback(self):
        data = [{"text": "x" * 1000}]
        result = truncate_json(data, 10)
        assert result == "[]"

    def test_dict_fallback(self):
        data = {"key": "x" * 1000}
        result = truncate_json(data, 50)
        assert result.endswith(TRUNCATION_SUFFIX)

    def test_unicode_preserved_in_json(self):
        data = [{"greek": "τὸ ἐφ' ἡμῖν"}]
        result = truncate_json(data, 10000)
        parsed = json.loads(result)
        assert parsed[0]["greek"] == "τὸ ἐφ' ἡμῖν"
