"""Regression tests for the anti-fabrication gate's collateral damage (2026-08).

A double audit of two production answers found the quote-verification gate
deleting *attested* ancient text and amputating answers:

1. byte-level false positives — U+02BC vs U+2019 apostrophes, and OCR
   dittographies inside the reference the quote is checked against;
2. incoherent blocks — the original withheld, its translation kept silently;
3. terminal amputation — answers ending on ``[removed: …]`` and announced
   enumerations delivering fewer items than announced.

Ancient-language fixtures are NEVER composed here: they are the existing
audit-derived repo fixtures (``test_programmatic_verify_quotes``, sourced from
``data/eval/must_not_appear.jsonl``) or mechanical transformations of them
(slicing, punctuation insertion, character-run duplication).
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from eleutheria_graphrag.agents.ancient_text_matching import (
    MATCH_EXACT,
    MATCH_FUZZY,
    MATCH_NORMALIZED,
    PreparedReference,
    collapse_dittography,
    containment_class,
    legacy_fold_ancient_text,
    normalize_ancient_text,
)
from eleutheria_graphrag.agents.graph_nodes import _verify_answer_programmatically
from eleutheria_graphrag.agents.text_verifier import (
    REASON_REFERENCE_MISMATCH,
    REASON_UNATTESTED,
    WITHHELD_ITEM_NOTE,
    WITHHELD_ORIGINAL_MARKER,
    _folded_segments,
    enforce_answer,
    verify_ancient_text,
)

from .test_programmatic_verify_quotes import (
    BUNDLE_GREEK,
    BUNDLE_TRANSLATION,
    FOREIGN_GREEK,
    _state_with_bundle,
)

_PLACEHOLDER = "*[removed: unverified ancient text]*"

_WORDS = BUNDLE_GREEK.split()
# Mechanical punctuation insertion: the SAME elision written with the two
# apostrophe characters the corpus actually mixes. U+02BC (in the reference,
# as the corpus and the KG nodes carry it) is a modifier LETTER — a \w
# character — while the ASCII apostrophe of the rendered answer is
# punctuation. That asymmetry is exactly what used to delete accurate quotes.
QUOTE_ASCII_APOSTROPHE = f"{_WORDS[0]}' {' '.join(_WORDS[1:])}"
REFERENCE_MODIFIER_APOSTROPHE = f"{_WORDS[0]}ʼ {' '.join(_WORDS[1:])}"

# Mechanical character-run duplication: the longest word of the bundle text
# followed by an echo of its own last four characters — the OCR dittography
# shape found in the audited KG node ("ἐξουσίας σίας").
_LONGEST = max(_WORDS, key=len)
_ECHO = _LONGEST[-4:]
REFERENCE_WITH_DITTOGRAPHY = BUNDLE_GREEK.replace(_LONGEST, f"{_LONGEST} {_ECHO}", 1)


class TestNormalizer:
    def test_apostrophe_variants_fold_identically(self):
        assert normalize_ancient_text(QUOTE_ASCII_APOSTROPHE) == (
            normalize_ancient_text(REFERENCE_MODIFIER_APOSTROPHE)
        )

    def test_legacy_fold_is_the_false_positive_being_fixed(self):
        # Documents the bug class: before normalization the two spellings of
        # the same elision were different strings.
        assert legacy_fold_ancient_text(QUOTE_ASCII_APOSTROPHE) != (
            legacy_fold_ancient_text(REFERENCE_MODIFIER_APOSTROPHE)
        )

    def test_whitespace_runs_collapse(self):
        spaced = BUNDLE_GREEK.replace(" ", "   ", 1)
        assert normalize_ancient_text(spaced) == normalize_ancient_text(BUNDLE_GREEK)

    def test_accent_stripping_preserved(self):
        assert normalize_ancient_text(BUNDLE_GREEK) == normalize_ancient_text(
            BUNDLE_GREEK.upper().lower()
        )


class TestCollapseDittography:
    def test_clean_text_untouched(self):
        folded = normalize_ancient_text(BUNDLE_GREEK)
        assert collapse_dittography(folded) == folded

    def test_suffix_echo_removed(self):
        noisy = normalize_ancient_text(REFERENCE_WITH_DITTOGRAPHY)
        assert collapse_dittography(noisy) == normalize_ancient_text(BUNDLE_GREEK)

    def test_repeated_token_removed(self):
        doubled = normalize_ancient_text(
            BUNDLE_GREEK.replace(_LONGEST, f"{_LONGEST} {_LONGEST}", 1)
        )
        assert collapse_dittography(doubled) == normalize_ancient_text(BUNDLE_GREEK)

    def test_in_word_duplication_removed(self):
        doubled = normalize_ancient_text(
            BUNDLE_GREEK.replace(_LONGEST, f"{_LONGEST}{_LONGEST}", 1)
        )
        assert collapse_dittography(doubled) == normalize_ancient_text(BUNDLE_GREEK)

    def test_prefix_echo_is_not_collapsed(self):
        # A shorter token that is a PREFIX of its neighbour is ordinary
        # language (an article before a longer word), never treated as noise.
        prefix = _LONGEST[:4]
        noisy = normalize_ancient_text(
            BUNDLE_GREEK.replace(_LONGEST, f"{_LONGEST} {prefix}", 1)
        )
        assert normalize_ancient_text(prefix) in collapse_dittography(noisy)

    def test_collapse_is_bounded(self):
        # Three echoes: the budget stops at two, so a text that is
        # systematically different can never be collapsed into agreement.
        noisy = normalize_ancient_text(BUNDLE_GREEK)
        for word in _WORDS[:3]:
            noisy = noisy.replace(
                normalize_ancient_text(word),
                f"{normalize_ancient_text(word)} {normalize_ancient_text(word)}",
                1,
            )
        collapsed = collapse_dittography(noisy)
        assert len(collapsed.split()) > len(
            normalize_ancient_text(BUNDLE_GREEK).split()
        )


class TestContainmentClass:
    def _segments(self, text: str) -> tuple[list[str], list[str]]:
        return (
            _folded_segments(text),
            _folded_segments(text, fold=legacy_fold_ancient_text),
        )

    def test_exact_containment(self):
        segments, legacy = self._segments(BUNDLE_GREEK)
        reference = PreparedReference(BUNDLE_GREEK)
        assert (
            containment_class(segments, reference, legacy_segments=legacy)
            == MATCH_EXACT
        )

    def test_normalized_pass(self):
        segments, legacy = self._segments(QUOTE_ASCII_APOSTROPHE)
        reference = PreparedReference(REFERENCE_MODIFIER_APOSTROPHE)
        assert (
            containment_class(segments, reference, legacy_segments=legacy)
            == MATCH_NORMALIZED
        )

    def test_fuzzy_pass_on_reference_dittography(self):
        segments, legacy = self._segments(BUNDLE_GREEK)
        reference = PreparedReference(REFERENCE_WITH_DITTOGRAPHY)
        assert (
            containment_class(segments, reference, legacy_segments=legacy)
            == MATCH_FUZZY
        )

    def test_absent_span_never_matches(self):
        segments, legacy = self._segments(FOREIGN_GREEK)
        reference = PreparedReference(BUNDLE_GREEK)
        assert containment_class(segments, reference, legacy_segments=legacy) is None


class TestSecondChanceAttestation:
    @pytest.mark.asyncio
    async def test_apostrophe_variant_survives_against_evidence(self):
        db = AsyncMock()
        db.fetch.return_value = []
        answer = f"Justin writes {QUOTE_ASCII_APOSTROPHE} [P1]."
        result = await verify_ancient_text(
            answer, db, evidence_texts=[REFERENCE_MODIFIER_APOSTROPHE]
        )
        assert result.all_verified
        assert result.verified_spans[0].reason == MATCH_NORMALIZED
        db.fetch.assert_not_called()

    @pytest.mark.asyncio
    async def test_accurate_quote_survives_reference_dittography(self):
        db = AsyncMock()
        db.fetch.return_value = []
        result = await verify_ancient_text(
            f"Justin writes {BUNDLE_GREEK} [P1].",
            db,
            evidence_texts=[REFERENCE_WITH_DITTOGRAPHY],
        )
        assert result.all_verified
        assert result.verified_spans[0].reason == MATCH_FUZZY

    @pytest.mark.asyncio
    async def test_dittography_rescue_works_through_the_db_probe(self):
        db = AsyncMock()
        db.fetch.return_value = [
            {
                "passage_id": "p1",
                "title": "Apologia Prima",
                "canonical_ref": "43",
                "text_content": REFERENCE_WITH_DITTOGRAPHY,
            }
        ]
        result = await verify_ancient_text(f"Justin writes {BUNDLE_GREEK}.", db)
        assert result.all_verified
        span = result.verified_spans[0]
        assert span.status == "db_passage"
        assert span.reason == MATCH_FUZZY

    @pytest.mark.asyncio
    async def test_absent_greek_still_dies_as_unattested(self):
        db = AsyncMock()
        db.fetch.return_value = []
        result = await verify_ancient_text(f"Origen wrote {FOREIGN_GREEK}.", db)
        assert not result.all_verified
        assert result.unverified_spans[0].reason == REASON_UNATTESTED

    @pytest.mark.asyncio
    async def test_candidate_rows_without_the_span_are_a_reference_mismatch(self):
        db = AsyncMock()
        db.fetch.return_value = [
            {
                "passage_id": "p9",
                "title": "Apologia Prima",
                "canonical_ref": "43",
                "text_content": BUNDLE_GREEK,
            }
        ]
        result = await verify_ancient_text(f"Origen wrote {FOREIGN_GREEK}.", db)
        assert not result.all_verified
        assert result.unverified_spans[0].reason == REASON_REFERENCE_MISMATCH

    @pytest.mark.asyncio
    async def test_reason_reaches_metadata(self):
        db = AsyncMock()
        db.fetch.return_value = []
        result = await verify_ancient_text(f"Origen wrote {FOREIGN_GREEK}.", db)
        meta = result.to_metadata()
        assert meta["unverified_texts"][0]["reason"] == REASON_UNATTESTED
        assert meta["unverified_spans"][0]["reason"] == REASON_UNATTESTED

    @pytest.mark.asyncio
    async def test_removal_is_logged_once_with_its_reason(self, caplog):
        db = AsyncMock()
        db.fetch.return_value = []
        with caplog.at_level("INFO", logger="eleutheria_graphrag.agents.text_verifier"):
            await verify_ancient_text(f"Origen wrote {FOREIGN_GREEK}.", db)
        removals = [
            record
            for record in caplog.records
            if record.levelname == "INFO"
            and "text-gate: removed" in record.getMessage()
        ]
        assert len(removals) == 1
        assert REASON_UNATTESTED in removals[0].getMessage()


class TestPairedTranslationPolicy:
    @pytest.mark.asyncio
    async def test_withheld_original_keeps_its_translation_with_a_marker(self):
        db = AsyncMock()
        db.fetch.return_value = []
        answer = "\n".join(
            [
                "Justin frames the question this way [P1].",
                f'> Original: "{FOREIGN_GREEK}" [P1]',
                f'> Translation: "{BUNDLE_TRANSLATION}" [P1]',
                "The argument continues [P1].",
            ]
        )
        result = await verify_ancient_text(answer, db)
        enforced = enforce_answer(answer, result)

        assert FOREIGN_GREEK not in enforced
        # No bare placeholder for the withheld original …
        assert _PLACEHOLDER not in enforced
        # … and the translation is explicitly marked, never silent.
        assert BUNDLE_TRANSLATION in enforced
        assert WITHHELD_ORIGINAL_MARKER in enforced

    @pytest.mark.asyncio
    async def test_lone_original_without_translation_keeps_the_placeholder(self):
        db = AsyncMock()
        db.fetch.return_value = []
        answer = "\n".join(
            [
                "Justin frames the question this way [P1].",
                f'> Original: "{FOREIGN_GREEK}" [P1]',
                "The argument continues [P1].",
            ]
        )
        result = await verify_ancient_text(answer, db)
        enforced = enforce_answer(answer, result)
        assert FOREIGN_GREEK not in enforced
        assert _PLACEHOLDER in enforced

    def test_render_gate_marks_the_surviving_translation(self):
        state = _state_with_bundle()
        state.raw_answer = "\n".join(
            [
                f"> {FOREIGN_GREEK} [P1]",
                f'> "{BUNDLE_TRANSLATION}" [P1]',
            ]
        )
        answer, _citations = _verify_answer_programmatically(state)
        assert FOREIGN_GREEK not in answer
        assert BUNDLE_TRANSLATION in answer
        assert WITHHELD_ORIGINAL_MARKER in answer

    def test_render_gate_leaves_intact_blocks_alone(self):
        state = _state_with_bundle()
        state.raw_answer = "\n".join(
            [
                f"> {BUNDLE_GREEK} [P1]",
                f'> "{BUNDLE_TRANSLATION}" [P1]',
            ]
        )
        answer, _citations = _verify_answer_programmatically(state)
        assert WITHHELD_ORIGINAL_MARKER not in answer


class TestTerminalPlaceholders:
    @pytest.mark.asyncio
    async def test_answer_never_ends_on_a_placeholder(self):
        db = AsyncMock()
        db.fetch.return_value = []
        answer = "\n".join(
            [
                "A sound opening claim [P1].",
                f"Origen wrote {FOREIGN_GREEK} [P2].",
            ]
        )
        result = await verify_ancient_text(answer, db)
        enforced = enforce_answer(answer, result)
        assert not enforced.rstrip().endswith(_PLACEHOLDER)
        assert _PLACEHOLDER not in enforced
        assert "A sound opening claim" in enforced
        assert WITHHELD_ITEM_NOTE in enforced

    @pytest.mark.asyncio
    async def test_header_of_an_emptied_trailing_block_goes_too(self):
        db = AsyncMock()
        db.fetch.return_value = []
        answer = "\n".join(
            [
                "A sound opening claim [P1].",
                "",
                "### A Fourth Consideration",
                f"Origen wrote {FOREIGN_GREEK} [P2].",
            ]
        )
        result = await verify_ancient_text(answer, db)
        enforced = enforce_answer(answer, result)
        assert "A Fourth Consideration" not in enforced
        assert _PLACEHOLDER not in enforced

    @pytest.mark.asyncio
    async def test_mid_answer_placeholder_is_preserved(self):
        db = AsyncMock()
        db.fetch.return_value = []
        answer = "\n".join(
            [
                "A sound opening claim [P1].",
                f"Origen wrote {FOREIGN_GREEK} [P2].",
                "A sound closing claim.",
            ]
        )
        result = await verify_ancient_text(answer, db)
        enforced = enforce_answer(answer, result)
        assert _PLACEHOLDER in enforced
        assert enforced.rstrip().endswith("A sound closing claim.")


class TestEnumerationNote:
    @pytest.mark.asyncio
    async def test_broken_enumeration_is_declared_once(self):
        db = AsyncMock()
        db.fetch.return_value = []
        answer = "\n".join(
            [
                "Four things can be said about this passage [P1].",
                "First, the question is posed in Stoic terms [P1].",
                f"Second, Origen answers with {FOREIGN_GREEK} [P2].",
                "Third, the reception recasts it [P1].",
                "Fourth, the debate persists [P1].",
            ]
        )
        result = await verify_ancient_text(answer, db)
        enforced = enforce_answer(answer, result)
        assert enforced.count(WITHHELD_ITEM_NOTE) == 1
        assert "Fourth, the debate persists" in enforced

    @pytest.mark.asyncio
    async def test_no_note_when_nothing_is_missing(self):
        db = AsyncMock()
        answer = f"Justin writes {BUNDLE_GREEK} [P1]."
        result = await verify_ancient_text(answer, db, evidence_texts=[BUNDLE_GREEK])
        assert enforce_answer(answer, result) == answer
        assert WITHHELD_ITEM_NOTE not in answer
