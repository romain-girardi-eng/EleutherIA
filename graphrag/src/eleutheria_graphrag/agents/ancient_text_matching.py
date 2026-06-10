"""Shared accent-/sigma-/punctuation-insensitive matching for ancient text.

Single source of truth for the folding and word-bounded containment helpers
used by both the render-time quote gates (``graph_nodes``) and the
post-synthesis deterministic text verifier (``text_verifier``). Keeping one
implementation prevents the two gates from drifting apart — drift would mean
one gate passes text the other rejects.
"""

from __future__ import annotations

import re
import unicodedata

COMBINING_MARK_RE = re.compile(r"[\u0300-\u036F]")
NON_WORD_RUN_RE = re.compile(r"[^\w]+", re.UNICODE)

# Function words of the modern answer languages (en/fr/de/it; Greek answers
# are script-detected). A quotation-formatted Latin-script chunk containing
# none of these is treated as candidate ancient Latin and must be contained
# in the cited evidence. Tokens that double as common Latin words (in, a,
# an, at, is, et, de, ne, se, si, qui, non, per, plus, una, uno, est, e)
# are deliberately absent so fabricated Latin cannot hide behind them.
#
# Latin-homograph audit (2026-06-10):
# * "die" REMOVED — ablative singular of ``dies`` ("hoc die", "die ac
#   nocte") is frequent in classical Latin, so fabricated Latin containing
#   it skipped the gate. German chunks almost always carry another function
#   word (der/und/ist/...), so the false-positive cost is low.
# * Kept after judgment (each removal trades a rare Latin laundering vector
#   for frequent false positives that would drop legitimate modern lines in
#   enforce paths):
#   - "his"/"has" — forms of ``hic``, but indispensable English;
#   - "das" — 2 sg. of ``dare`` is rare vs. the ubiquitous German article;
#   - "des" — pres. subj. of ``dare`` is rare vs. the ubiquitous French
#     article;
#   - "fur" (folded "für") — Latin ``fur`` "thief" is rare in this corpus;
#   - "di" — nom. pl. of ``deus`` is real ("di immortales") but Italian
#     "di" is the single most frequent Italian word.
#
# Entries are in folded form (lowercase, combining marks stripped).
MODERN_STOPWORDS = frozenset(
    {
        # English
        "the",
        "of",
        "and",
        "to",
        "that",
        "it",
        "with",
        "as",
        "for",
        "this",
        "by",
        "are",
        "was",
        "were",
        "which",
        "from",
        "be",
        "not",
        "on",
        "or",
        "but",
        "into",
        "would",
        "has",
        "have",
        "had",
        "will",
        "their",
        "its",
        "who",
        "what",
        "when",
        "there",
        "been",
        "his",
        "her",
        "they",
        "we",
        "you",
        # French
        "le",
        "la",
        "les",
        "des",
        "du",
        "que",
        "dans",
        "pour",
        "sur",
        "avec",
        "pas",
        "sont",
        "cette",
        "ses",
        "leur",
        "mais",
        "au",
        "aux",
        "ce",
        "son",
        "sa",
        "nous",
        "vous",
        "elle",
        # German ("die" deliberately absent — valid Latin, see audit above)
        "der",
        "das",
        "und",
        "ist",
        "nicht",
        "mit",
        "von",
        "zu",
        "den",
        "dem",
        "ein",
        "eine",
        "auf",
        "fur",
        "als",
        "auch",
        "sich",
        "wird",
        "werden",
        "durch",
        "dass",
        "im",
        "aus",
        "bei",
        "nach",
        "wenn",
        "oder",
        "aber",
        "sind",
        # Italian
        "il",
        "lo",
        "gli",
        "di",
        "che",
        "con",
        "del",
        "della",
        "nel",
        "alla",
        "sono",
        "come",
        "anche",
        "questo",
        "questa",
        "piu",
    }
)


def fold_ancient_text(text: str) -> str:
    """Accent-, final-sigma- and punctuation-insensitive form for containment."""
    decomposed = unicodedata.normalize("NFD", text)
    stripped = COMBINING_MARK_RE.sub("", decomposed)
    folded = stripped.replace("ς", "σ").lower()
    return NON_WORD_RUN_RE.sub(" ", folded).strip()


def contains_word_bounded(haystack: str, needle: str) -> bool:
    """Containment that cannot match inside a longer word.

    Plain ``needle in haystack`` lets a folded segment match the prefix or
    suffix of a longer source word (e.g. a short article + noun passing
    against an unrelated compound that merely starts with the same letters),
    laundering fabricated text. Require non-word characters or string edges
    on both sides of the match.
    """
    if not needle:
        return False
    return (
        re.search(rf"(?<!\w){re.escape(needle)}(?!\w)", haystack, re.UNICODE)
        is not None
    )


def word_bounded_index(haystack: str, needle: str, start: int = 0) -> int:
    """Offset of the first word-bounded match of ``needle`` at/after ``start``.

    Same boundary semantics as :func:`contains_word_bounded`; returns ``-1``
    when no match exists. Used to verify that the segments of an elided
    quotation occur *in order* within a single source text.
    """
    if not needle:
        return -1
    match = re.compile(rf"(?<!\w){re.escape(needle)}(?!\w)", re.UNICODE).search(
        haystack, start
    )
    return match.start() if match else -1
