"""F3 regression: the quotable-original-text scorer ranks clean Greek AND Latin
ahead of metadata/gloss junk — the adversarial gap the rigor pass surfaced.

Before the fix, ``_quotable_chars`` counted ONLY Greek, so (a) clean Latin
(Cicero De Fato, Boethius, Augustine) scored 0 and sank into the same partition
as ``**Reference:**`` blocks, and (b) ``Greek: • … - gloss`` bullet rows scored
positive and were treated as fully quotable (dumping gloss markdown into prose).
"""

from __future__ import annotations

from eleutheria_graphrag.agents.tools.build_controversy_frame import (
    BuildControversyFrameTool,
)

_q = BuildControversyFrameTool._quotable_chars


def test_clean_greek_scores_by_greek_count() -> None:
    assert _q("τὰ ἐφ' ἡμῖν καὶ τὰ οὐκ ἐφ' ἡμῖν", "grc") > 5


def test_clean_latin_is_quotable_not_demoted_with_junk() -> None:
    # Cicero De Fato — clean Latin must score > 0 (was 0, sank with junk).
    score = _q("Si omnia fato fiunt, nihil est in nostra potestate.", "lat")
    assert score > 5


def test_reference_block_scores_negative() -> None:
    block = "**Reference:** Discourses I.1.1\n**Author:** Epictetus\n**Work:** Diss."
    assert _q(block, "grc") == -1


def test_greek_gloss_bullet_row_is_excluded() -> None:
    # The F9 gloss-bullet format must NOT be treated as quotable continuous text.
    gloss = "Greek: • ἐφ' ἡμῖν καὶ οὐκ ἐφ' [ἡμῖν] - up to us and not up to us"
    assert _q(gloss, "grc") == -1


def test_english_companion_text_is_not_treated_as_quotable_original() -> None:
    # An English companion (no Greek, not language=la) must not score as quotable.
    assert _q("This is an English paraphrase of the passage.", "eng") == 0


def test_clean_greek_leads_over_reference_block_and_gloss() -> None:
    greek = _q("ἡ προαίρεσις ἐλευθέρα ἐστὶ φύσει", "grc")
    block = _q("**Reference:** x **Author:** y", "grc")
    gloss = _q("Greek: • λόγος - reason", "grc")
    assert greek > 0 > block and greek > 0 > gloss
