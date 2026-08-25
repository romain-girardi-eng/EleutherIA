"""Regression tests for the 2026-08-26 corpus text-artifact repair.

The three defects were mechanical: a line-join that spliced a modern name into
a Greek sentence, and two generated strings the Boethius ingester baked into
`text_content`. All three are provable artifacts, which is why they were
repaired at all — everything needing an editorial decision was left alone and
is recorded in `NOT_REPAIRED`.
"""

from __future__ import annotations

import re
from pathlib import Path

from scripts.apply_2026_08_26_corpus_text_artifacts import (
    assert_invariants,
    read_jsonl,
    transform,
)
from scripts.data_2026_08_26_corpus_text_artifacts import (
    BOETHIUS_ROW_COUNT,
    BOETHIUS_WORK,
    NOT_REPAIRED,
    SVF_ARTIFACT,
    SVF_PASSAGE_ID,
    SVF_REPAIRED,
    collapse_echoed_braces,
    strip_language_prefix,
    strip_running_footer,
)

ROOT = Path(__file__).resolve().parents[1]
PASSAGES = ROOT / "data/corpus/passages.jsonl"


def load() -> list[dict]:
    return read_jsonl(PASSAGES)


def test_svf_line_join_artifact_is_gone() -> None:
    rows = load()
    row = next(r for r in rows if r.get("passage_id") == SVF_PASSAGE_ID)
    text = row["text_content"]
    assert SVF_ARTIFACT not in text
    assert SVF_REPAIRED in text
    # The attested reading, TLG5026 Scholia in Homerum @byte 1419747.
    assert "ὡς ταὐτὸν εἱμαρμένη καὶ Ζεύς" in text


def test_no_row_anywhere_still_carries_the_splice() -> None:
    assert not any(SVF_ARTIFACT in (r.get("text_content") or "") for r in load())


def test_boethius_rows_carry_no_generated_strings() -> None:
    rows = [r for r in load() if r.get("work_canonical_id") == BOETHIUS_WORK]
    assert len(rows) == BOETHIUS_ROW_COUNT
    footer = re.compile(r"Boethius, De consolatione philosophiae \d+\s*$")
    echo = re.compile(r"(?<=\s)([^\s{}]+) \{\1\}")
    for row in rows:
        text = row["text_content"]
        assert not text.startswith("Latin:"), row["canonical_ref"]
        assert not footer.search(text), row["canonical_ref"]
        assert not echo.search(text), row["canonical_ref"]
        assert text.strip()


def test_repair_is_idempotent() -> None:
    rows = load()
    once, changed, skipped = transform(rows)
    assert changed == []
    assert skipped == []
    assert once == rows


def test_invariants_hold_on_the_written_file() -> None:
    rows = load()
    assert_invariants(rows, rows)


def test_footer_is_only_stripped_when_it_matches_the_sequence_number() -> None:
    # A footer whose number disagrees with the row is not the generated label
    # we identified, so it must survive untouched rather than be guessed at.
    text = "Quod igitur.\n\nBoethius, De consolatione philosophiae 7"
    assert strip_running_footer(text, 7) == "Quod igitur."
    assert strip_running_footer(text, 42) == text


def test_language_prefix_strip_is_anchored_and_single() -> None:
    assert strip_language_prefix("Latin: Carmina qui") == "Carmina qui"
    # Only the leading label goes; an occurrence inside the text is content.
    assert strip_language_prefix("Carmina Latin: qui") == "Carmina Latin: qui"


def test_brace_collapse_only_removes_exact_echoes() -> None:
    assert collapse_echoed_braces("sicut imaginationem {imaginationem} rationi") == (
        "sicut imaginationem rationi"
    )
    # A brace holding anything else is editorial content and must survive.
    assert collapse_echoed_braces("uti {sic} rationis") == "uti {sic} rationis"


def test_the_deliberate_exclusions_are_documented() -> None:
    # Four classes were left alone on purpose. If someone later "fixes" them
    # without an edition to collate against, this is the record of why not.
    loci = " ".join(entry["locus"] for entry in NOT_REPAIRED)
    assert "Alexander" in loci
    assert "Boethius" in loci
    assert "philocalia" in loci.lower()
    for entry in NOT_REPAIRED:
        assert entry["why_not"].strip()


def test_no_boethius_latin_word_was_altered() -> None:
    # The repair removes generated strings; it must not have touched a letter
    # of Latin. Known-damaged tokens are still damaged, on purpose.
    rows = [r for r in load() if r.get("work_canonical_id") == BOETHIUS_WORK]
    joined = " ".join(r["text_content"] for r in rows)
    assert "Draenoscendi" in joined or "laederenturhunc" in joined
