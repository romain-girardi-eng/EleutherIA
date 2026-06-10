"""Regression tests for deterministic quote verification and full-text evidence."""

import json
from pathlib import Path

from eleutheria_graphrag.agents.ancient_text_matching import fold_ancient_text
from eleutheria_graphrag.agents.evidence_collector import EvidenceCollector
from eleutheria_graphrag.agents.graph_nodes import (
    _build_context_pack,
    _combined_greek_misses,
    _segments_supported_by_text,
    _verify_answer_programmatically,
)
from eleutheria_graphrag.agents.state import (
    ContextPack,
    EvidenceBundle,
    RAGState,
    RetrievalBudget,
)
from eleutheria_graphrag.agents.tools.read_passages import (
    PassageSummary,
    ReadPassagesResult,
)
from eleutheria_graphrag.agents.tools.search_passages import _passage_hit_from_row

BUNDLE_GREEK = "εἰ γὰρ εἵμαρται τόνδε τινὰ ἀγαθὸν εἶναι"
BUNDLE_TRANSLATION = "For if it were fated that this man be good"

_MUST_NOT_APPEAR = (
    Path(__file__).resolve().parents[3] / "data" / "eval" / "must_not_appear.jsonl"
)


def _audit_derived_foreign_greek(min_words: int = 8) -> str:
    """Pick a long audit-recorded fabricated Greek string as the negative fixture.

    Never compose ancient Greek in-repo: the 'foreign' string must come
    verbatim from the machine-derived must-not-appear set (itself built from
    the scholarly-audit queues), exactly like the G3 eval harness.
    """
    for line in _MUST_NOT_APPEAR.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if (
            record.get("language") == "grc"
            and record.get("scan_answers")
            and len(record["string"].split()) >= min_words
        ):
            return record["string"]
    raise RuntimeError("no audit-derived Greek string long enough for the fixture")


FOREIGN_GREEK = _audit_derived_foreign_greek()
SHORT_GREEK = FOREIGN_GREEK.split()[2]
BUNDLE_LATIN = (
    "Omnis autem enuntiatio aut vera aut falsa est. Motus ergo sine causa nullus est."
)
FOREIGN_LATIN = "praesertim cum vos iidem fato fieri dicatis omnia"


def _state_with_bundle() -> RAGState:
    state = RAGState(question="Quote Justin on fate.")
    bundle = EvidenceBundle(
        bundle_id="bundle-1",
        work_id="work-1",
        work_title="Apologia Prima",
        author="Justin Martyr",
        canonical_ref="43",
        original_passage_id="p1",
        original_text=BUNDLE_GREEK,
        translation_text=BUNDLE_TRANSLATION,
        token_estimate=20,
    )
    state.context_pack = ContextPack(
        bundle_refs={"bundle-1": "P1"},
        passage_bundles=[bundle],
    )
    return state


def _state_with_latin_bundle() -> RAGState:
    state = RAGState(question="Quote Chrysippus on motion without cause.")
    bundle = EvidenceBundle(
        bundle_id="bundle-1",
        work_id="work-1",
        work_title="De Fato",
        author="Cicero",
        canonical_ref="20",
        original_passage_id="p1",
        original_text=BUNDLE_LATIN,
        translation_text="Every proposition is either true or false.",
        language="lat",
        token_estimate=20,
    )
    state.context_pack = ContextPack(
        bundle_refs={"bundle-1": "P1"},
        passage_bundles=[bundle],
    )
    return state


class TestBlockquoteGreekContainment:
    def test_fabricated_greek_blockquote_with_valid_ref_is_dropped(self):
        state = _state_with_bundle()
        state.raw_answer = "\n".join(
            [
                f"> {FOREIGN_GREEK} [P1]",
                f'> "{BUNDLE_TRANSLATION}" [P1]',
            ]
        )

        answer, citations = _verify_answer_programmatically(state)

        assert FOREIGN_GREEK not in answer
        assert FOREIGN_GREEK in state.metadata.get("unsupported_quotes", [])
        assert BUNDLE_TRANSLATION in answer
        assert citations and citations[0].ref == "P1"

    def test_genuine_bundle_greek_blockquote_is_kept(self):
        state = _state_with_bundle()
        state.raw_answer = "\n".join(
            [
                f"> {BUNDLE_GREEK} [P1]",
                f'> "{BUNDLE_TRANSLATION}" [P1]',
            ]
        )

        answer, citations = _verify_answer_programmatically(state)

        assert BUNDLE_GREEK in answer
        assert citations and citations[0].ref == "P1"
        assert not state.metadata.get("unsupported_quotes")

    def test_subspan_of_bundle_greek_is_kept(self):
        state = _state_with_bundle()
        subspan = " ".join(BUNDLE_GREEK.split()[:3])
        state.raw_answer = f"> {subspan} [P1]"

        answer, _ = _verify_answer_programmatically(state)

        assert subspan in answer

    def test_two_multiword_fragments_stitched_with_dash_are_dropped(self):
        # Both fragments are verbatim in the source, but the line is not one
        # contiguous span — stitching genuine multi-word fragments is the
        # same fabrication class as stitching single words.
        state = _state_with_bundle()
        words = BUNDLE_GREEK.split()
        stitched = f"{' '.join(words[:2])} — {' '.join(words[-2:])}"
        state.raw_answer = "\n".join(
            [
                f"> {stitched} [P1]",
                f'> "{BUNDLE_TRANSLATION}" [P1]',
            ]
        )

        answer, _ = _verify_answer_programmatically(state)

        assert stitched not in answer
        assert state.metadata.get("unsupported_quotes")
        assert BUNDLE_TRANSLATION in answer

    def test_greek_blockquote_without_ref_on_its_own_line_is_kept(self):
        state = _state_with_bundle()
        state.raw_answer = "\n".join(
            [
                f"> {BUNDLE_GREEK}",
                ">",
                f'> "{BUNDLE_TRANSLATION}" [P1]',
            ]
        )

        answer, _ = _verify_answer_programmatically(state)

        assert BUNDLE_GREEK in answer


class TestQuotedSpanLineDropping:
    def test_unsupported_quoted_span_drops_line_not_laundered(self):
        state = _state_with_bundle()
        fabricated = "a completely unattested wording of the fate doctrine"
        state.raw_answer = "\n".join(
            [
                f'Justin claims "{fabricated}" [P1].',
                f'Justin writes "{BUNDLE_TRANSLATION}" [P1].',
            ]
        )

        answer, _ = _verify_answer_programmatically(state)

        assert fabricated not in answer
        assert fabricated in state.metadata.get("unsupported_quotes", [])
        assert BUNDLE_TRANSLATION in answer

    def test_short_greek_quote_is_checked_not_free_passed(self):
        state = _state_with_bundle()
        state.raw_answer = "\n".join(
            [
                f'The soul ("{SHORT_GREEK}") grounds the argument [P1].',
                f'Justin writes "{BUNDLE_TRANSLATION}" [P1].',
            ]
        )

        answer, _ = _verify_answer_programmatically(state)

        assert SHORT_GREEK not in answer

    def test_short_non_greek_quote_keeps_free_pass(self):
        state = _state_with_bundle()
        state.raw_answer = 'Justin uses the word "fated" here [P1].'

        answer, _ = _verify_answer_programmatically(state)

        assert '"fated"' in answer


class TestBlockquoteLatinContainment:
    def test_fabricated_latin_blockquote_with_valid_ref_is_dropped(self):
        state = _state_with_latin_bundle()
        state.raw_answer = "\n".join(
            [
                f"> {FOREIGN_LATIN} [P1]",
                f'> "{BUNDLE_LATIN}" [P1]',
            ]
        )

        answer, _ = _verify_answer_programmatically(state)

        assert FOREIGN_LATIN not in answer
        assert FOREIGN_LATIN in state.metadata.get("unsupported_quotes", [])
        assert "Motus ergo sine causa nullus est" in answer

    def test_genuine_unquoted_latin_blockquote_is_kept(self):
        state = _state_with_latin_bundle()
        state.raw_answer = f"> {BUNDLE_LATIN} [P1]"

        answer, _ = _verify_answer_programmatically(state)

        assert "Motus ergo sine causa nullus est" in answer
        assert not state.metadata.get("unsupported_quotes")

    def test_latin_blockquote_with_dash_attribution_is_kept(self):
        state = _state_with_latin_bundle()
        state.raw_answer = f"> {BUNDLE_LATIN} — Cicero, De Fato 20 [P1]"

        answer, _ = _verify_answer_programmatically(state)

        assert "Motus ergo sine causa nullus est" in answer

    def test_unquoted_english_blockquote_is_not_mistaken_for_latin(self):
        state = _state_with_bundle()
        state.raw_answer = f"> {BUNDLE_TRANSLATION} [P1]"

        answer, _ = _verify_answer_programmatically(state)

        assert BUNDLE_TRANSLATION in answer


class TestRegularLineGreekRuns:
    def test_fabricated_unquoted_greek_in_prose_line_is_dropped(self):
        state = _state_with_bundle()
        state.raw_answer = "\n".join(
            [
                f"Origen's phrase {FOREIGN_GREEK} shows freedom [P1].",
                f'Justin writes "{BUNDLE_TRANSLATION}" [P1].',
            ]
        )

        answer, _ = _verify_answer_programmatically(state)

        assert FOREIGN_GREEK not in answer
        assert FOREIGN_GREEK in state.metadata.get("unsupported_quotes", [])
        assert BUNDLE_TRANSLATION in answer

    def test_short_inline_greek_term_in_prose_line_is_kept(self):
        state = _state_with_bundle()
        short_term = " ".join(FOREIGN_GREEK.split()[5:8])
        state.raw_answer = f"The phrase {short_term} recurs in Justin [P1]."

        answer, _ = _verify_answer_programmatically(state)

        assert short_term in answer

    def test_supported_unquoted_greek_in_prose_line_is_kept(self):
        state = _state_with_bundle()
        state.raw_answer = f"Justin's words {BUNDLE_GREEK} ground the claim [P1]."

        answer, _ = _verify_answer_programmatically(state)

        assert BUNDLE_GREEK in answer


class TestQuoteMarkCoverage:
    def test_fabricated_greek_in_guillemets_is_dropped(self):
        state = _state_with_bundle()
        state.raw_answer = "\n".join(
            [
                f"Justin writes «{FOREIGN_GREEK}» [P1].",
                f'Justin writes "{BUNDLE_TRANSLATION}" [P1].',
            ]
        )

        answer, _ = _verify_answer_programmatically(state)

        assert FOREIGN_GREEK not in answer

    def test_genuine_greek_in_guillemets_is_kept(self):
        state = _state_with_bundle()
        state.raw_answer = f"Justin writes «{BUNDLE_GREEK}» [P1]."

        answer, _ = _verify_answer_programmatically(state)

        assert BUNDLE_GREEK in answer

    def test_fabricated_latin_in_curly_single_quotes_is_dropped(self):
        state = _state_with_latin_bundle()
        state.raw_answer = "\n".join(
            [
                f"Cicero says ‘{FOREIGN_LATIN}’ [P1].",
                f'Cicero concludes "{BUNDLE_LATIN}" [P1].',
            ]
        )

        answer, _ = _verify_answer_programmatically(state)

        assert FOREIGN_LATIN not in answer
        assert "Motus ergo sine causa nullus est" in answer

    def test_fabricated_latin_in_german_low_quotes_is_dropped(self):
        state = _state_with_latin_bundle()
        state.raw_answer = "\n".join(
            [
                f"Er schreibt „{FOREIGN_LATIN}“ [P1].",
                f'Cicero concludes "{BUNDLE_LATIN}" [P1].',
            ]
        )

        answer, _ = _verify_answer_programmatically(state)

        assert FOREIGN_LATIN not in answer


class TestElidedQuotations:
    def test_elided_greek_quote_with_unicode_ellipsis_is_kept(self):
        state = _state_with_bundle()
        words = BUNDLE_GREEK.split()
        elided = f"{' '.join(words[:3])} … {' '.join(words[-2:])}"
        state.raw_answer = f'> "{elided}" [P1]'

        answer, _ = _verify_answer_programmatically(state)

        assert elided in answer
        assert not state.metadata.get("unsupported_quotes")

    def test_elided_greek_quote_with_ascii_ellipsis_is_kept(self):
        state = _state_with_bundle()
        words = BUNDLE_GREEK.split()
        elided = f"{' '.join(words[:3])} ... {' '.join(words[-2:])}"
        state.raw_answer = f'> "{elided}" [P1]'

        answer, _ = _verify_answer_programmatically(state)

        assert elided in answer

    def test_unquoted_elided_greek_blockquote_run_is_kept(self):
        state = _state_with_bundle()
        words = BUNDLE_GREEK.split()
        elided = f"{' '.join(words[:3])} ... {' '.join(words[-2:])}"
        state.raw_answer = f"> {elided} [P1]"

        answer, _ = _verify_answer_programmatically(state)

        assert elided in answer

    def test_elided_quote_with_foreign_segment_is_dropped(self):
        state = _state_with_bundle()
        words = BUNDLE_GREEK.split()
        foreign_tail = " ".join(FOREIGN_GREEK.split()[5:8])
        elided = f"{' '.join(words[:3])} … {foreign_tail}"
        state.raw_answer = "\n".join(
            [
                f'> "{elided}" [P1]',
                f'> "{BUNDLE_TRANSLATION}" [P1]',
            ]
        )

        answer, _ = _verify_answer_programmatically(state)

        assert elided not in answer
        assert BUNDLE_TRANSLATION in answer

    def test_reordered_elided_segments_fail_segment_check(self):
        """Real segments quoted out of source order are a stitched fabrication."""
        words = BUNDLE_GREEK.split()
        head = " ".join(words[:3])
        tail = " ".join(words[-2:])

        assert _segments_supported_by_text([head, tail], BUNDLE_GREEK)
        assert not _segments_supported_by_text([tail, head], BUNDLE_GREEK)

    def test_reordered_elided_segments_fail_combined_greek_check(self):
        words = BUNDLE_GREEK.split()
        head = " ".join(words[:3])
        tail = " ".join(words[-2:])
        folded_sources = [fold_ancient_text(BUNDLE_GREEK)]

        assert _combined_greek_misses(f"> {head} … {tail} [P1]", folded_sources) == []
        misses = _combined_greek_misses(f"> {tail} … {head} [P1]", folded_sources)
        assert misses

    def test_reordered_elided_greek_quote_is_dropped(self):
        state = _state_with_bundle()
        words = BUNDLE_GREEK.split()
        reordered = f"{' '.join(words[-2:])} … {' '.join(words[:3])}"
        state.raw_answer = "\n".join(
            [
                f'> "{reordered}" [P1]',
                f'> "{BUNDLE_TRANSLATION}" [P1]',
            ]
        )

        answer, _ = _verify_answer_programmatically(state)

        assert reordered not in answer
        assert BUNDLE_TRANSLATION in answer

    def test_elided_latin_quote_on_prose_line_is_kept(self):
        state = _state_with_latin_bundle()
        words = BUNDLE_LATIN.split()
        elided = f"{' '.join(words[:3])} … {' '.join(words[-4:])}"
        state.raw_answer = f'Cicero concludes "{elided}" [P1].'

        answer, _ = _verify_answer_programmatically(state)

        assert elided in answer


class TestCitationSemantics:
    def test_citation_note_reflects_ref_resolution_and_quote_check(self):
        state = _state_with_bundle()
        state.raw_answer = f"> {BUNDLE_GREEK} [P1]"

        _, citations = _verify_answer_programmatically(state)

        assert citations[0].verified is True
        note = (citations[0].verification_note or "").lower()
        assert "quote" in note or "quoted" in note


class TestFullTextEvidence:
    def test_evidence_collector_stores_full_passage_text(self):
        long_text = ("fate providence necessity assent " * 60).strip()
        assert len(long_text) > 800
        collector = EvidenceCollector()
        result = ReadPassagesResult(
            node_id="person_origen",
            node_label="Origen",
            passages=[
                PassageSummary(
                    passage_id="p1",
                    work_title="De Principiis",
                    author="Origen",
                    canonical_ref="III.1.1",
                    text_content=long_text,
                    confidence=0.95,
                ),
            ],
        )

        collector.ingest("read_passages", {"node_id": "person_origen"}, result)

        assert collector.evidence_bundles[0].original_text == long_text

    def test_search_passage_hit_keeps_full_text(self):
        row = {
            "passage_id": "p9",
            "title": "On Fate",
            "text_content": "x" * 2000,
            "rank": 1.0,
        }

        hit = _passage_hit_from_row(row)

        assert len(hit.text_content) == 2000

    def test_context_pack_includes_full_bundle_text(self):
        long_text = ("fate providence necessity assent " * 120).strip()
        assert len(long_text) > 1600
        state = RAGState(question="What is fate?")
        state.evidence_bundles = [
            EvidenceBundle(
                bundle_id="bundle-1",
                work_id="work-1",
                work_title="On Fate",
                author="Chrysippus",
                original_passage_id="p1",
                original_text=long_text,
                token_estimate=RetrievalBudget.estimate_tokens(long_text),
            )
        ]

        pack = _build_context_pack(state)

        assert long_text in pack.prompt_context
