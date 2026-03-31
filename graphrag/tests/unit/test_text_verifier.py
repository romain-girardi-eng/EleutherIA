"""Tests for the Greek/Latin text verification step."""

import pytest
from unittest.mock import AsyncMock

from eleutheria_graphrag.agents.text_verifier import (
    extract_greek_runs,
    is_known_term,
    verify_greek_text,
    sanitize_answer,
)


class TestExtractGreekRuns:
    def test_finds_greek_text(self):
        text = "Origen argues about αὐτεξούσιον in his work."
        runs = extract_greek_runs(text)
        assert len(runs) == 1
        assert "αὐτεξούσιον" in runs[0][0]

    def test_finds_longer_greek_passage(self):
        text = 'He writes: "ἔνεστι δ\' ὁρᾶν εἰ ταῦτα λέγοντες σώζουσιν" in De Fato.'
        runs = extract_greek_runs(text)
        assert len(runs) >= 1
        assert "ὁρᾶν" in runs[0][0]

    def test_no_greek(self):
        text = "This is plain English text about free will."
        runs = extract_greek_runs(text)
        assert len(runs) == 0

    def test_multiple_runs(self):
        text = "The terms εἱμαρμένη and προαίρεσις are key."
        runs = extract_greek_runs(text)
        assert len(runs) == 2


class TestIsKnownTerm:
    def test_known_single_word(self):
        assert is_known_term("αὐτεξούσιον")

    def test_known_multi_word(self):
        assert is_known_term("τὸ ἐφ' ἡμῖν")

    def test_known_latin(self):
        assert is_known_term("liberum arbitrium")

    def test_short_unknown_still_passes(self):
        # 3 words or fewer pass even if not in known list
        assert is_known_term("ψυχὴ καὶ σῶμα")

    def test_long_unknown_fails(self):
        # 5+ words that aren't known
        assert not is_known_term("ἔνεστι δ' ὁρᾶν εἰ ταῦτα λέγοντες σώζουσιν τὰς κοινὰς")


class TestVerifyGreekText:
    @pytest.mark.asyncio
    async def test_short_terms_pass_automatically(self):
        db = AsyncMock()
        answer = "Origen discusses αὐτεξούσιον and εἱμαρμένη."
        result = await verify_greek_text(answer, db)
        assert result.all_verified  # Short known terms, no DB check needed
        db.fetchrow.assert_not_called()

    @pytest.mark.asyncio
    async def test_long_text_verified_against_db(self):
        db = AsyncMock()
        db.fetchrow.return_value = {
            "passage_id": "p1",
            "title": "De Fato",
            "canonical_ref": "14",
        }
        answer = 'He writes: "ἔνεστι δ\' ὁρᾶν εἰ ταῦτα λέγοντες σώζουσιν τὰς κοινὰς περὶ τοῦ"'
        result = await verify_greek_text(answer, db)
        assert result.all_verified
        assert len(result.verified_extracts) >= 1

    @pytest.mark.asyncio
    async def test_fabricated_text_flagged(self):
        db = AsyncMock()
        db.fetchrow.return_value = None  # Not found in DB
        answer = 'Origen wrote: "ψυχὴ αὐτεξούσιος ἐστιν καὶ ἐλευθέρα πάντων τῶν δεσμῶν"'
        result = await verify_greek_text(answer, db)
        assert not result.all_verified
        assert len(result.unverified_extracts) >= 1


class TestSanitizeAnswer:
    @pytest.mark.asyncio
    async def test_removes_long_unverified(self):
        db = AsyncMock()
        db.fetchrow.return_value = None
        # 10+ Greek words — should be removed
        long_greek = "ψυχὴ αὐτεξούσιος ἐστιν καὶ ἐλευθέρα πάντων τῶν δεσμῶν τῆς εἱμαρμένης"
        answer = f'He wrote: "{long_greek}" which proves his point.'
        verification = await verify_greek_text(answer, db)
        sanitized = sanitize_answer(answer, verification)
        assert long_greek not in sanitized
        assert "[text removed: unverified ancient text]" in sanitized

    @pytest.mark.asyncio
    async def test_verified_text_kept(self):
        db = AsyncMock()
        db.fetchrow.return_value = {"passage_id": "p1", "title": "De Fato", "canonical_ref": "14"}
        greek = "ἔνεστι δ' ὁρᾶν εἰ ταῦτα λέγοντες σώζουσιν τὰς κοινὰς"
        answer = f'Alexander writes: "{greek}"'
        verification = await verify_greek_text(answer, db)
        sanitized = sanitize_answer(answer, verification)
        assert greek in sanitized  # Verified text stays
