"""Shared accent-/sigma-/punctuation-insensitive matching for ancient text.

Single source of truth for the folding and word-bounded containment helpers
used by both the render-time quote gates (``graph_nodes``) and the
post-synthesis deterministic text verifier (``text_verifier``). Keeping one
implementation prevents the two gates from drifting apart — drift would mean
one gate passes text the other rejects.

Two byte-level noise classes used to make the gates delete *attested* ancient
text (2026-08 double audit of two production answers):

1. **Apostrophe/koronis variants.** Elision in Greek is written with any of
   U+2019, U+02BC, U+1FBD, U+1FBF, ASCII ``'``… Only some of them are
   ``\\w`` characters, so ``ἐφ᾽ ἡμῖν`` folded one way in the answer and
   another way in the reference and the containment check failed on a quote
   that was verbatim correct. :func:`normalize_ancient_text` unifies the whole
   family *before* folding.
2. **OCR dittography in the REFERENCE.** Corpus/KG text carries duplicated
   fragments (``ἐξουσίας σίας``); an accurate quote spanning the duplication
   point is not contained in the noisy reference.
   :func:`collapse_dittography` removes that noise from the *reference only*,
   as a bounded second chance (see its docstring for the trade-off).
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Sequence

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


# Every character used in this corpus to write elision/koronis/apostrophe.
# They are NOT interchangeable for ``\w``: U+02BC and U+02B9 are modifier
# LETTERS (category Lm, therefore word characters), while U+2019/U+1FBD/ASCII
# ``'`` are punctuation or symbols. Unifying them before the fold is what
# makes ``ἐφ᾽ ἡμῖν`` compare equal to ``ἐφ' ἡμῖν``.
APOSTROPHE_VARIANTS = "'‘’‛ʼʽʹʺ᾽᾿῾´΄′`"
_APOSTROPHE_RE = re.compile(f"[{re.escape(APOSTROPHE_VARIANTS)}]")

# Match classes returned by :func:`containment_class`, weakest last.
MATCH_EXACT = "exact"
MATCH_NORMALIZED = "normalized-pass"
MATCH_FUZZY = "fuzzy-pass"

# Dittography tolerance bounds (reference side only).
_DITTO_MIN_CHARS = 3
_MAX_DITTO_COLLAPSES = 2
_INWORD_DITTO_RE = re.compile(r"(\w{3,}?)\1")


def normalize_ancient_text(text: str) -> str:
    """Canonical comparison form for ancient text.

    NFC first (so pre-composed and decomposed inputs agree), then the
    apostrophe/koronis family is unified, then the historical fold: combining
    marks dropped, final sigma merged into medial sigma, lowercased, runs of
    non-word characters collapsed to single spaces, ends trimmed.

    Both sides of every containment check must go through this function: a
    normalization applied to only one side is worse than none.
    """
    unified = _APOSTROPHE_RE.sub("'", unicodedata.normalize("NFC", text))
    decomposed = unicodedata.normalize("NFD", unified)
    stripped = COMBINING_MARK_RE.sub("", decomposed)
    folded = stripped.replace("ς", "σ").lower()
    return NON_WORD_RUN_RE.sub(" ", folded).strip()


def legacy_fold_ancient_text(text: str) -> str:
    """The pre-normalization fold, kept ONLY to classify match reasons.

    A span that matches under :func:`normalize_ancient_text` but not under
    this one was rescued by the apostrophe unification — the gate logs it as
    ``normalized-pass`` so audits can measure the false-positive class that
    used to delete it.
    """
    decomposed = unicodedata.normalize("NFD", text)
    stripped = COMBINING_MARK_RE.sub("", decomposed)
    folded = stripped.replace("ς", "σ").lower()
    return NON_WORD_RUN_RE.sub(" ", folded).strip()


def fold_ancient_text(text: str) -> str:
    """Accent-, final-sigma- and punctuation-insensitive form for containment.

    Alias of :func:`normalize_ancient_text`, kept as the historical name used
    across the gates.
    """
    return normalize_ancient_text(text)


def _collapse_in_word(token: str) -> str:
    """Collapse an immediately repeated 3+ character sequence inside a token."""
    previous = ""
    while previous != token:
        previous = token
        token = _INWORD_DITTO_RE.sub(r"\1", token)
    return token


def collapse_dittography(folded: str) -> str:
    """Remove OCR dittography from an ALREADY-FOLDED reference text.

    Three noise shapes, all of them adjacent duplications produced by OCR of
    critical editions:

    * a repeated 3+ character sequence inside one token (``εξουσιασσιασ``);
    * the same token twice in a row (``του του``);
    * a token that is a proper *suffix* of the token before it
      (``εξουσιας σίας`` — the real audit case).

    Deliberate limits. Only the suffix shape is tolerated (not prefix, not
    "the longer token absorbs the shorter one"): ``καιρός`` following ``καί``
    is an ordinary Greek sequence, and a prefix rule would silently delete the
    article. At most :data:`_MAX_DITTO_COLLAPSES` tokens are removed per
    reference, so a text that is *systematically* different from the quote can
    never be collapsed into agreement.

    Residual trade-off, accepted knowingly: a quote that elides one genuine
    word which happens to be a suffix of its predecessor (``αὐτοῖς τοῖς`` →
    ``αὐτοῖς``) passes the fuzzy arm. That introduces no fabricated text — it
    tolerates an unmarked elision of attested text — whereas the alternative
    (deleting accurate quotes) is the damage this function exists to stop.
    Every rescue is logged as ``fuzzy-pass`` for audit.
    """
    tokens = folded.split()
    if not tokens:
        return folded
    collapsed: list[str] = []
    removals = 0
    for raw_token in tokens:
        token = raw_token
        if removals < _MAX_DITTO_COLLAPSES:
            token = _collapse_in_word(raw_token)
            if token != raw_token:
                removals += 1
        if collapsed and removals < _MAX_DITTO_COLLAPSES:
            previous = collapsed[-1]
            is_echo = len(token) >= _DITTO_MIN_CHARS and (
                token == previous
                or (len(previous) > len(token) and previous.endswith(token))
            )
            if is_echo:
                removals += 1
                continue
        collapsed.append(token)
    return " ".join(collapsed)


class PreparedReference:
    """A reference text folded once and reusable across many span checks.

    ``folded`` / ``legacy`` are computed eagerly (cheap, always needed);
    ``collapsed`` — the dittography-free variant — is computed on first use,
    because it is only consulted when the exact and normalized arms already
    failed.
    """

    __slots__ = ("_collapsed", "folded", "legacy")

    def __init__(self, text: str) -> None:
        self.folded = normalize_ancient_text(text or "")
        self.legacy = legacy_fold_ancient_text(text or "")
        self._collapsed: str | None = None

    @property
    def collapsed(self) -> str:
        if self._collapsed is None:
            self._collapsed = collapse_dittography(self.folded)
        return self._collapsed


def prepare_references(texts: Sequence[str]) -> list[PreparedReference]:
    """Prepared, non-empty references for a batch of raw source texts."""
    prepared = [PreparedReference(text) for text in texts if text]
    return [reference for reference in prepared if reference.folded]


def containment_class(
    segments: Sequence[str],
    reference: PreparedReference,
    *,
    legacy_segments: Sequence[str] | None = None,
) -> str | None:
    """Strongest class under which ``segments`` are contained in ``reference``.

    ``segments`` are normalized folds of the quoted span (already split on
    ellipses by the caller); ``legacy_segments`` are the same segments under
    :func:`legacy_fold_ancient_text`, used only to tell ``exact`` from
    ``normalized-pass``. Returns ``None`` when the span is genuinely absent.
    """
    if not segments:
        return None
    if (
        legacy_segments is not None
        and len(legacy_segments) == len(segments)
        and all(
            contains_word_bounded(reference.legacy, segment)
            for segment in legacy_segments
        )
    ):
        return MATCH_EXACT
    if all(contains_word_bounded(reference.folded, segment) for segment in segments):
        return MATCH_EXACT if legacy_segments is None else MATCH_NORMALIZED
    collapsed = reference.collapsed
    if collapsed != reference.folded and all(
        contains_word_bounded(collapsed, segment) for segment in segments
    ):
        return MATCH_FUZZY
    return None


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
