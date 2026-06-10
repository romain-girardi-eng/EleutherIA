"""Golden adversarial suite for the programmatic quote gate.

Replays the fabrication classes documented by the scholarly audit against
``_verify_answer_programmatically`` (the deterministic gate that strips
unverifiable ancient-language quotations from synthesized answers):

- fabricated Greek in blockquotes (audited fingerprints, verbatim);
- fabricated Latin in quotation format;
- quote-mark variants (straight, curly, guillemets, German low-9);
- elided quotations (genuine kept, fabricated tail dropped);
- prefix containment (genuine subspan kept, genuine-prefix + fabricated
  continuation dropped).

Every ancient string is loaded from ``data/eval/quote_gate_strings.json``,
machine-derived from the audit corpus by
``scripts/eval/build_gold_from_audit.py`` — no ancient text is composed here.
Offline: no network, no DB.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from eleutheria_graphrag.agents.graph_nodes import _verify_answer_programmatically
from eleutheria_graphrag.agents.state import ContextPack, EvidenceBundle, RAGState

from tests.eval.eval_lib.forbidden import (
    REPO_ROOT,
    find_forbidden_strings,
    load_forbidden_strings,
)

FIXTURES_PATH = REPO_ROOT / "data" / "eval" / "quote_gate_strings.json"
FIXTURES: dict[str, Any] = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))

GENUINE_GREEK: str = FIXTURES["genuine_greek"]["string"]
GENUINE_LATIN: str = FIXTURES["genuine_latin"]["string"]
FOREIGN_LATIN: str = FIXTURES["foreign_latin"]["string"]
FABRICATED_GREEK: list[str] = [e["string"] for e in FIXTURES["fabricated_greek"]]
# Prose lines tolerate short inline Greek; the sentence-length rule needs
# >= 4 unelided words to trigger.
FABRICATED_GREEK_LONG: list[str] = [
    s for s in FABRICATED_GREEK if "..." not in s and len(s.split()) >= 4
]

ANCHOR_EN = "The cited passage grounds this claim about what is up to us."


def _state(original_text: str, language: str = "grc") -> RAGState:
    state = RAGState(question="Eval fixture question on fate and freedom.")
    bundle = EvidenceBundle(
        bundle_id="bundle-1",
        work_id="work-1",
        work_title="Eval Fixture Work",
        author="Eval Fixture Author",
        canonical_ref="1",
        original_passage_id="p1",
        original_text=original_text,
        translation_text=ANCHOR_EN,
        language=language,
        token_estimate=40,
    )
    state.context_pack = ContextPack(
        bundle_refs={"bundle-1": "P1"},
        passage_bundles=[bundle],
    )
    return state


def test_fixture_integrity() -> None:
    assert GENUINE_GREEK and GENUINE_LATIN and FOREIGN_LATIN
    assert len(FABRICATED_GREEK) >= 5
    assert FABRICATED_GREEK_LONG, "need at least one >=4-word fabrication"
    for entry in FIXTURES["fabricated_greek"]:
        assert entry["source_file"].startswith("data/audit/")


class TestFabricatedGreekBlockquotes:
    @pytest.mark.parametrize("fabricated", FABRICATED_GREEK)
    def test_audited_fingerprint_is_dropped(self, fabricated: str) -> None:
        state = _state(GENUINE_GREEK)
        state.raw_answer = "\n".join(
            [
                f"> {fabricated} [P1]",
                f"{ANCHOR_EN} [P1]",
            ]
        )

        answer, citations = _verify_answer_programmatically(state)

        assert fabricated not in answer
        assert ANCHOR_EN in answer
        assert citations and citations[0].ref == "P1"
        assert not find_forbidden_strings(answer, load_forbidden_strings())

    def test_genuine_greek_blockquote_is_kept(self) -> None:
        state = _state(GENUINE_GREEK)
        state.raw_answer = f"> {GENUINE_GREEK} [P1]"

        answer, citations = _verify_answer_programmatically(state)

        assert GENUINE_GREEK in answer
        assert citations and citations[0].ref == "P1"
        assert not state.metadata.get("unsupported_quotes")


class TestFabricatedGreekProse:
    @pytest.mark.parametrize("fabricated", FABRICATED_GREEK_LONG)
    def test_sentence_length_run_in_prose_is_dropped(self, fabricated: str) -> None:
        state = _state(GENUINE_GREEK)
        state.raw_answer = "\n".join(
            [
                f"The author writes {fabricated} in this context [P1].",
                f"{ANCHOR_EN} [P1]",
            ]
        )

        answer, _ = _verify_answer_programmatically(state)

        assert fabricated not in answer
        assert ANCHOR_EN in answer

    def test_genuine_greek_in_prose_is_kept(self) -> None:
        state = _state(GENUINE_GREEK)
        state.raw_answer = f"The phrase {GENUINE_GREEK} carries the argument [P1]."

        answer, _ = _verify_answer_programmatically(state)

        assert GENUINE_GREEK in answer


QUOTE_MARK_TEMPLATES = [
    pytest.param('"{0}"', id="straight-double"),
    pytest.param("“{0}”", id="curly-double"),
    pytest.param("‘{0}’", id="curly-single"),
    pytest.param("«{0}»", id="guillemets"),
    pytest.param("‹{0}›", id="single-guillemets"),
    pytest.param("„{0}“", id="german-low9"),
]


class TestQuoteMarkVariants:
    @pytest.mark.parametrize("template", QUOTE_MARK_TEMPLATES)
    def test_fabricated_greek_dropped_in_every_mark_style(self, template: str) -> None:
        fabricated = FABRICATED_GREEK_LONG[0]
        state = _state(GENUINE_GREEK)
        quoted = template.format(fabricated)
        state.raw_answer = "\n".join(
            [
                f"The text reads {quoted} [P1].",
                f"{ANCHOR_EN} [P1]",
            ]
        )

        answer, _ = _verify_answer_programmatically(state)

        assert fabricated not in answer
        assert fabricated in state.metadata.get("unsupported_quotes", [])
        assert ANCHOR_EN in answer

    @pytest.mark.parametrize("template", QUOTE_MARK_TEMPLATES)
    def test_genuine_greek_kept_in_every_mark_style(self, template: str) -> None:
        state = _state(GENUINE_GREEK)
        quoted = template.format(GENUINE_GREEK)
        state.raw_answer = f"The text reads {quoted} [P1]."

        answer, _ = _verify_answer_programmatically(state)

        assert GENUINE_GREEK in answer


class TestElidedQuotations:
    @pytest.mark.parametrize("ellipsis", ["…", "..."], ids=["unicode", "ascii"])
    def test_genuine_elided_quote_is_kept(self, ellipsis: str) -> None:
        words = GENUINE_GREEK.split()
        elided = f"{' '.join(words[:3])} {ellipsis} {' '.join(words[-2:])}"
        state = _state(GENUINE_GREEK)
        state.raw_answer = f'> "{elided}" [P1]'

        answer, _ = _verify_answer_programmatically(state)

        assert elided in answer
        assert not state.metadata.get("unsupported_quotes")

    def test_elided_quote_with_fabricated_tail_is_dropped(self) -> None:
        words = GENUINE_GREEK.split()
        fabricated_tail = " ".join(FABRICATED_GREEK_LONG[0].split()[:3])
        elided = f"{' '.join(words[:3])} … {fabricated_tail}"
        state = _state(GENUINE_GREEK)
        state.raw_answer = "\n".join(
            [
                f'> "{elided}" [P1]',
                f"{ANCHOR_EN} [P1]",
            ]
        )

        answer, _ = _verify_answer_programmatically(state)

        assert elided not in answer
        assert ANCHOR_EN in answer


class TestPrefixContainment:
    def test_genuine_prefix_subspan_is_kept(self) -> None:
        subspan = " ".join(GENUINE_GREEK.split()[:5])
        state = _state(GENUINE_GREEK)
        state.raw_answer = f'The clause "{subspan}" opens the definition [P1].'

        answer, _ = _verify_answer_programmatically(state)

        assert subspan in answer

    def test_genuine_prefix_with_fabricated_continuation_is_dropped(self) -> None:
        prefix = " ".join(GENUINE_GREEK.split()[:3])
        continuation = " ".join(FABRICATED_GREEK_LONG[0].split()[:3])
        spliced = f"{prefix} {continuation}"
        state = _state(GENUINE_GREEK)
        state.raw_answer = "\n".join(
            [
                f'The text reads "{spliced}" [P1].',
                f"{ANCHOR_EN} [P1]",
            ]
        )

        answer, _ = _verify_answer_programmatically(state)

        assert spliced not in answer
        assert spliced in state.metadata.get("unsupported_quotes", [])
        assert ANCHOR_EN in answer


class TestStitchedSingleWords:
    """Isolated real words assembled into a fake quotation (combine_short_runs).

    Every word below exists verbatim in the evidence; only the assembled
    sequence is fabricated, so the blockquote must be checked as one ordered
    segment and dropped.
    """

    def test_real_words_stitched_out_of_order_are_dropped(self) -> None:
        words = GENUINE_GREEK.split()
        stitched = f"{words[-1]} — {words[4]} — {words[2]}"
        state = _state(GENUINE_GREEK)
        state.raw_answer = "\n".join(
            [
                f"> {stitched} [P1]",
                f"{ANCHOR_EN} [P1]",
            ]
        )

        answer, _ = _verify_answer_programmatically(state)

        assert stitched not in answer
        assert ANCHOR_EN in answer

    def test_contiguous_multiword_pieces_are_kept(self) -> None:
        words = GENUINE_GREEK.split()
        pieces = f"{' '.join(words[:3])} — {' '.join(words[3:5])}"
        state = _state(GENUINE_GREEK)
        state.raw_answer = f"> {pieces} [P1]"

        answer, _ = _verify_answer_programmatically(state)

        assert " ".join(words[:3]) in answer


class TestLatinQuotations:
    def test_foreign_latin_blockquote_is_dropped(self) -> None:
        state = _state(GENUINE_LATIN, language="lat")
        state.raw_answer = "\n".join(
            [
                f"> {FOREIGN_LATIN} [P1]",
                f"{ANCHOR_EN} [P1]",
            ]
        )

        answer, _ = _verify_answer_programmatically(state)

        assert FOREIGN_LATIN not in answer
        assert FOREIGN_LATIN in state.metadata.get("unsupported_quotes", [])
        assert ANCHOR_EN in answer

    def test_genuine_latin_blockquote_is_kept(self) -> None:
        state = _state(GENUINE_LATIN, language="lat")
        state.raw_answer = f"> {GENUINE_LATIN} [P1]"

        answer, _ = _verify_answer_programmatically(state)

        assert GENUINE_LATIN in answer
        assert not state.metadata.get("unsupported_quotes")

    def test_foreign_latin_in_curly_quotes_is_dropped(self) -> None:
        state = _state(GENUINE_LATIN, language="lat")
        state.raw_answer = "\n".join(
            [
                f"The author says ‘{FOREIGN_LATIN}’ [P1].",
                f"{ANCHOR_EN} [P1]",
            ]
        )

        answer, _ = _verify_answer_programmatically(state)

        assert FOREIGN_LATIN not in answer
        assert ANCHOR_EN in answer
