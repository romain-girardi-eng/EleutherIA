"""Regression tests: honest grounding score, word-boundary quote containment,
em-dash run recombination, and integrity_status context-pack filtering.

All Greek fixtures are exact copies (imported or programmatically sliced)
from ``test_programmatic_verify_quotes`` — never composed.
"""

from __future__ import annotations

import json

import pytest
from pydantic_graph import End

from eleutheria_graphrag.agents.graph_nodes import (
    MODERN_STOPWORDS,
    ProgrammaticVerify,
    _contains_word_bounded,
    _fold_ancient_text,
    _make_evidence_from_node,
    _node_integrity_status,
    _unsupported_latin_quotation,
    _verify_answer_programmatically,
)
from eleutheria_graphrag.agents.state import RAGState

from .conftest import make_ctx, make_deps
from .test_programmatic_verify_quotes import (
    BUNDLE_GREEK,
    BUNDLE_TRANSLATION,
    FOREIGN_LATIN,
    _state_with_bundle,
)

BUNDLE_WORDS = BUNDLE_GREEK.split()


# ------------------------------------------------------- grounding honesty


class TestGroundingScoreHonesty:
    @pytest.mark.asyncio
    async def test_grounding_is_ref_resolution_ratio_not_blanket_100(self):
        state = _state_with_bundle()
        # Two refs claimed in the draft; only P1 resolves to evidence.
        state.raw_answer = "\n".join(
            [
                f'Justin writes "{BUNDLE_TRANSLATION}" [P1].',
                "A claim resting on a phantom reference [P9].",
            ]
        )
        ctx = make_ctx(state, make_deps())

        result = await ProgrammaticVerify().run(ctx)

        assert isinstance(result, End)
        # Old behavior: citations exist => grounding=100. Honest: 1/2 refs.
        assert state.self_rag_evaluation.grounding == 50
        assert state.metadata["grounding"]["method"] == "ref_resolution"
        assert state.metadata["grounding"]["requested_refs"] == 2
        assert state.metadata["grounding"]["resolved_refs"] == 1

    @pytest.mark.asyncio
    async def test_grounding_100_when_all_refs_resolve(self):
        state = _state_with_bundle()
        state.raw_answer = f'Justin writes "{BUNDLE_TRANSLATION}" [P1].'
        ctx = make_ctx(state, make_deps())

        await ProgrammaticVerify().run(ctx)

        assert state.self_rag_evaluation.grounding == 100

    @pytest.mark.asyncio
    async def test_grounding_0_without_refs_or_citations_not_25(self):
        state = RAGState(question="What is fate?")
        state.raw_answer = "Plain prose without any reference markers."
        ctx = make_ctx(state, make_deps())

        await ProgrammaticVerify().run(ctx)

        # Old behavior hard-coded 25 here.
        assert state.self_rag_evaluation.grounding == 0


# --------------------------------------------------- word-boundary containment


class TestWordBoundaryContainment:
    def test_folded_prefix_of_longer_source_word_is_not_contained(self):
        word = BUNDLE_WORDS[5]  # real source word, copied verbatim
        prefix = word[:-1]  # programmatic slice — proper prefix
        folded_source = _fold_ancient_text(BUNDLE_GREEK)

        assert _contains_word_bounded(folded_source, _fold_ancient_text(word))
        assert not _contains_word_bounded(
            folded_source, _fold_ancient_text(prefix)
        )

    def test_blockquote_with_prefix_of_real_word_is_dropped(self):
        state = _state_with_bundle()
        prefix = BUNDLE_WORDS[5][:-1]
        state.raw_answer = "\n".join(
            [
                f"> {prefix} [P1]",
                f'> "{BUNDLE_TRANSLATION}" [P1]',
            ]
        )

        answer, _ = _verify_answer_programmatically(state)

        assert prefix not in answer
        assert BUNDLE_TRANSLATION in answer

    def test_full_genuine_quote_still_kept(self):
        state = _state_with_bundle()
        state.raw_answer = f"> {BUNDLE_GREEK} [P1]"

        answer, citations = _verify_answer_programmatically(state)

        assert BUNDLE_GREEK in answer
        assert citations and citations[0].ref == "P1"


# ------------------------------------------------- em-dash run recombination


class TestEmDashRunRecombination:
    def test_blockquote_assembled_from_isolated_real_words_is_dropped(self):
        # Both words exist in the source but are NOT contiguous — an em-dash
        # splits them into separate single-word runs that each used to pass.
        fake = f"{BUNDLE_WORDS[0]} — {BUNDLE_WORDS[5]}"
        state = _state_with_bundle()
        state.raw_answer = "\n".join(
            [
                f"> {fake} [P1]",
                f'> "{BUNDLE_TRANSLATION}" [P1]',
            ]
        )

        answer, _ = _verify_answer_programmatically(state)

        assert fake not in answer
        assert BUNDLE_WORDS[0] not in answer
        assert BUNDLE_TRANSLATION in answer

    def test_contiguous_words_split_by_em_dash_are_kept(self):
        # The same two-run shape but the words ARE contiguous in the source:
        # the recombined segment is a genuine span.
        genuine = f"{BUNDLE_WORDS[4]} — {BUNDLE_WORDS[5]}"
        state = _state_with_bundle()
        state.raw_answer = f"> {genuine} [P1]"

        answer, _ = _verify_answer_programmatically(state)

        assert genuine in answer

    def test_elision_to_single_word_tail_is_kept(self):
        # Legitimate elided quotation ending in a single word: the unicode
        # ellipsis breaks contiguity on purpose, so each side is checked as
        # its own segment.
        elided = f"{' '.join(BUNDLE_WORDS[:3])} … {BUNDLE_WORDS[6]}"
        state = _state_with_bundle()
        state.raw_answer = f"> {elided} [P1]"

        answer, _ = _verify_answer_programmatically(state)

        assert elided in answer

    def test_prose_line_short_terms_unaffected_by_recombination(self):
        # Prose lines (min_words=4) keep tolerating isolated short Greek
        # terms — recombination applies to quotation-formatted lines only.
        term = BUNDLE_WORDS[2]
        state = _state_with_bundle()
        state.raw_answer = (
            f"Justin's verb {term} and the noun {BUNDLE_WORDS[5]} recur [P1]."
        )

        answer, _ = _verify_answer_programmatically(state)

        assert term in answer


# ------------------------------------------------ integrity_status filtering


class TestIntegrityStatusFiltering:
    def test_flagged_node_description_is_stripped(self):
        node = {
            "id": "n1",
            "label": "Suspect node",
            "type": "argument",
            "description": "Unverified Greek-bearing description.",
            "metadata": {"integrity_status": "greek_unverified"},
        }

        ev = _make_evidence_from_node("n1", node)

        assert ev.description == ""
        assert ev.label == "Suspect node"  # node stays traversable

    def test_flagged_passage_text_content_is_blocked(self):
        node = {
            "id": "p-bad",
            "label": "Flagged passage",
            "type": "passage",
            "description": "Fabricated quotation pending fix.",
            "metadata": {
                "integrity_status": "fabrication_confirmed_pending_fix",
            },
        }

        ev = _make_evidence_from_node("p-bad", node)

        assert ev.description == ""
        assert ev.text_content is None

    def test_unflagged_node_description_is_packed(self):
        node = {
            "id": "n2",
            "label": "Clean node",
            "type": "argument",
            "description": "A verified description.",
            "metadata": {},
        }

        ev = _make_evidence_from_node("n2", node)

        assert ev.description == "A verified description."

    def test_node_integrity_status_is_defensive(self):
        assert _node_integrity_status({}) == ""
        assert _node_integrity_status({"metadata": None}) == ""
        assert _node_integrity_status({"metadata": "not-a-dict"}) == ""
        assert _node_integrity_status({"metadata": {"integrity_status": None}}) == ""
        assert (
            _node_integrity_status(
                {"metadata": {"integrity_status": "greek_unverified"}}
            )
            == "greek_unverified"
        )

    def test_string_metadata_with_marker_fails_closed(self):
        # Regression: a flagged node whose metadata got stringified upstream
        # used to fail OPEN and slip back into the context pack.
        node = {"metadata": "integrity_status: greek_unverified (truncated"}
        assert _node_integrity_status(node) != ""

    def test_stringified_json_dict_is_parsed(self):
        node = {"metadata": json.dumps({"integrity_status": "greek_unverified"})}
        assert _node_integrity_status(node) == "greek_unverified"

    def test_stringified_json_dict_without_flag_stays_open(self):
        node = {"metadata": json.dumps({"integrity_status": ""})}
        assert _node_integrity_status(node) == ""

    def test_stringified_json_non_dict_with_marker_fails_closed(self):
        node = {"metadata": '["integrity_status"]'}
        assert _node_integrity_status(node) != ""

    def test_plain_malformed_metadata_without_marker_stays_open(self):
        # Don't nuke the whole KG over malformed-but-unflagged metadata.
        assert _node_integrity_status({"metadata": 42}) == ""
        assert _node_integrity_status({"metadata": "free-text note"}) == ""


# -------------------------------------------- Latin homographs in stopwords


class TestModernStopwordsLatinHomographs:
    def test_die_removed_from_stopwords(self):
        # Regression: "die" (ablative of ``dies``) let fabricated Latin
        # containing it skip the blockquote Latin gate.
        assert "die" not in MODERN_STOPWORDS
        assert "der" in MODERN_STOPWORDS  # German detection keeps working
        assert "das" in MODERN_STOPWORDS  # documented-kept homograph

    def test_latin_line_with_die_no_longer_skips_the_gate(self):
        # "die" appended to the audit-derived Latin negative fixture —
        # mechanical concatenation of existing fixtures, nothing composed.
        line = f"> {FOREIGN_LATIN} die [P1]"
        assert _unsupported_latin_quotation(line, ["P1"], {}, {}) is not None


class TestLatinGateNeedsPositiveEvidence:
    def test_english_content_word_line_is_not_latin(self):
        # Regression: an English blockquote line carrying no modern function
        # word passed the negative stopword test and was dropped as
        # unsupported Latin.
        line = "> Moral responsibility requires alternative possibilities [P1]"
        assert _unsupported_latin_quotation(line, ["P1"], {}, {}) is None

    def test_real_latin_still_flagged(self):
        line = f"> {FOREIGN_LATIN} [P1]"
        assert _unsupported_latin_quotation(line, ["P1"], {}, {}) is not None
