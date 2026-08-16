"""
Deterministic verification of ancient Greek and Latin text in agent responses.

Ancient text in a rendered answer must come from somewhere real. The check is
whitelist-first: any span already present — accent-, final-sigma- and
punctuation-insensitively, word-boundary-aligned — in the evidence gathered
for the current query is verified WITHOUT touching the database. Only the
remainder triggers a bounded DB probe: candidate rows are fetched by a
rare-token anchor (exact orthography, so the LIKE stays cheap and bounded),
then fold-compared in Python. The accent-insensitivity lives entirely in the
Python fold-compare — never in an un-indexable SQL expression over 69k rows.

Outcomes are recorded under ``metadata.text_verification``. Enforcement is now
the DEFAULT: a line carrying an unverified ancient-text span is dropped unless
``ELEUTHERIA_TEXT_VERIFIER_ENFORCE`` is explicitly falsy (report-only).
"""

from __future__ import annotations

import logging
import os
import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from eleutheria_graphrag.agents.ancient_text_matching import (
    MATCH_EXACT,
    MODERN_STOPWORDS,
    PreparedReference,
    containment_class,
    contains_word_bounded,
    fold_ancient_text,
    legacy_fold_ancient_text,
    looks_like_latin,
    prepare_references,
)

logger = logging.getLogger(__name__)

# Deletion is ON by default; ``=false`` opts back into report-only.
ENFORCE_ENV_VAR = "ELEUTHERIA_TEXT_VERIFIER_ENFORCE"
_REMOVED_LINE_MARKER = "*[removed: unverified ancient text]*"

# Reason classes reported for every gate decision (INFO-logged, and carried in
# ``metadata.text_verification`` so an audit can separate real fabrication from
# byte-level noise):
#   unattested         — nothing in the corpus even contains an anchor token;
#   reference-mismatch — a plausible reference exists, the span is not in it;
#   normalized-pass    — kept only thanks to Unicode normalization;
#   fuzzy-pass         — kept only after OCR dittography was collapsed OUT OF
#                        THE REFERENCE.
REASON_UNATTESTED = "unattested"
REASON_REFERENCE_MISMATCH = "reference-mismatch"

# Appended to a surviving translation when its paired original was withheld.
WITHHELD_ORIGINAL_MARKER = "*(original text withheld pending verification)*"

# Deterministic, i18n-neutral note appended when the gate amputated the end of
# the answer or broke an announced enumeration.
WITHHELD_ITEM_NOTE = (
    "(One further point was withheld because its supporting quotation "
    "could not be verified.)"
)

# Unicode ranges for ancient Greek
_GREEK_BASIC = range(0x0370, 0x0400)  # Greek and Coptic
_GREEK_EXTENDED = range(0x1F00, 0x2000)  # Greek Extended

_GREEK_CHAR_RE = re.compile(r"[Ͱ-Ͽἀ-῿]")

# Paired quotation marks (same pairs as the graph_nodes render-time quote
# gate): straight/curly double, curly single, guillemets (double and
# single), German low-9 variants. One capture group per pair.
_QUOTED_SPAN_RE = re.compile(
    r"[\"“](.+?)[\"”]"
    r"|‘(.+?)’"
    r"|«\s*(.+?)\s*»"
    r"|‹\s*(.+?)\s*›"
    r"|„(.+?)[“”]"
    r"|‚(.+?)[‘’]"
)

_ELLIPSIS_RE = re.compile(r"…|⋯|\.{3,}")

_TOKEN_STRIP_CHARS = ".,;:·()[]\"'«»‹›„“”‘’‚!?—–…"

# Pattern to find Greek text runs (3+ Greek chars in a row, possibly with spaces/punctuation)
_GREEK_RUN_RE = re.compile(
    r"[\u0370-\u03FF\u1F00-\u1FFF][\u0370-\u03FF\u1F00-\u1FFF\u0300-\u036F\s\-,;·.()\'\"]*"
    r"[\u0370-\u03FF\u1F00-\u1FFF]",
    re.UNICODE,
)

# Curated SINGLE-WORD technical vocabulary that never needs verification.
# Multi-word phrases were deliberately dropped from this list: anything
# beyond two words is quotation-shaped and goes through the whitelist/DB
# path (two-word technical phrases — "ἐφ' ἡμῖν", "liberum arbitrium",
# "nunc stans" — already pass via the ``_MAX_TERM_WORDS`` free pass).
_KNOWN_TERMS: set[str] = {
    # Greek terms
    "αὐτεξούσιον",
    "αὐτεξουσίου",
    "αὐτεξούσιος",
    "εἱμαρμένη",
    "εἱμαρμένης",
    "πρόνοια",
    "προνοίας",
    "προαίρεσις",
    "προαιρέσεως",
    "συγκατάθεσις",
    "συγκαταθέσεως",
    "ἀκρασία",
    "ἀκρασίας",
    "ἀποκατάστασις",
    "κλίσις",
    "παρέγκλισις",
    "λεκτόν",
    "λεκτά",
    "ἡγεμονικόν",
    "φαντασία",
    "φαντασίαι",
    "ὁρμή",
    "ὁρμαί",
    "ἐκπύρωσις",
    "λόγος",
    "λόγοι",
    "ψυχή",
    "ψυχῆς",
    "νοῦς",
    "ἐνέργεια",
    "δύναμις",
    "ἀρετή",
    "ἀρεταί",
    "εὐδαιμονία",
    "ἐλευθερία",
    "ἀνάγκη",
    "τύχη",
    # Latin terms
    "fatum",
    "fata",
    "necessitas",
    "voluntas",
    "aeternitas",
    "praescientia",
    "providentia",
    "concursus",
}

# Spans of at most this many words are vocabulary, not quotation: free pass.
# Lowered from 4 to 2 — three-word Greek already reads as a quotation.
_MAX_TERM_WORDS = 2

# Common ENGLISH content words (folded form). MODERN_STOPWORDS only carries
# function words, so a quoted English phrase made of content words ("moral
# responsibility requires causal freedom") used to be classified as candidate
# ancient Latin and flagged as report-only noise. None of these strings is a
# valid classical Latin word-form (homograph-audited the same way as
# MODERN_STOPWORDS — e.g. "divine" was deliberately left out: it is a real
# Latin vocative/adverb).
_ENGLISH_CONTENT_WORDS = frozenset(
    {
        "action",
        "agency",
        "agent",
        "against",
        "ancient",
        "argument",
        "arguments",
        "because",
        "between",
        "cause",
        "causes",
        "causal",
        "century",
        "choice",
        "choices",
        "christian",
        "claim",
        "claims",
        "compatibilism",
        "concept",
        "could",
        "debate",
        "determinism",
        "deterministic",
        "doctrine",
        "early",
        "effect",
        "event",
        "events",
        "every",
        "fate",
        "fated",
        "foreknowledge",
        "free",
        "freedom",
        "god",
        "however",
        "human",
        "incompatibilism",
        "knowledge",
        "moral",
        "nature",
        "necessity",
        "passage",
        "philosopher",
        "philosophers",
        "philosophy",
        "possible",
        "power",
        "reason",
        "responsibility",
        "responsible",
        "scholar",
        "scholars",
        "should",
        "soul",
        "stoic",
        "stoics",
        "theory",
        "therefore",
        "things",
        "through",
        "treatise",
        "whether",
        "without",
        "world",
    }
)

# Reject a quoted span as English (not candidate Latin) when more than this
# fraction of its alphabetic tokens is in _ENGLISH_CONTENT_WORDS. Strictly
# greater-than: a single incidental hit in a long genuine Latin quote can
# never trip it.
_ENGLISH_CONTENT_RATIO = 0.4

# DB probe bounds: at most _MAX_ANCHORS anchor tokens per span, at most
# _CANDIDATE_LIMIT candidate rows per (anchor, table) probe.
_ANCHOR_MIN_CHARS = 4
_MAX_ANCHORS = 2
_CANDIDATE_LIMIT = 25


@dataclass
class SpanCheck:
    """One ancient-text span found in the answer and its verification outcome."""

    text: str
    language: str  # "greek" | "latin"
    position: int  # char offset in the answer
    status: str  # "bundle" | "db_passage" | "db_node" | "unverified"
    source_id: str | None = None
    source_title: str | None = None
    # "exact" | "normalized-pass" | "fuzzy-pass" for kept spans,
    # "unattested" | "reference-mismatch" for removed ones.
    reason: str = MATCH_EXACT


@dataclass
class VerificationResult:
    """Aggregate outcome of one answer's ancient-text verification."""

    verified_spans: list[SpanCheck] = field(default_factory=list)
    unverified_spans: list[SpanCheck] = field(default_factory=list)
    db_checked: int = 0
    bundle_whitelisted: int = 0

    @property
    def all_verified(self) -> bool:
        return not self.unverified_spans

    def to_metadata(self) -> dict[str, Any]:
        """Shape recorded under ``metadata.text_verification``.

        Emits BOTH the detailed span lists and the aggregate contract the
        downstream consumers read (``verified``/``unverified`` integer
        counts + ``unverified_texts``): the share renderer
        (``backend/routes/share.py``), the /answer quality metrics
        (``backend/routes/graphrag_extras.py``) and the frontend banner
        (``MessageBubble.tsx`` via ``TextVerificationReport``) all key off
        the aggregate fields — without them the unverified-ancient-text
        surface is silently dead end-to-end.
        """
        return {
            "verified": len(self.verified_spans),
            "unverified": len(self.unverified_spans),
            "unverified_texts": [
                {
                    "text": span.text[:120],
                    "language": span.language,
                    "action": "flagged",
                    "reason": span.reason,
                }
                for span in self.unverified_spans
            ],
            "verified_spans": [
                {
                    "text": span.text[:120],
                    "language": span.language,
                    "status": span.status,
                    "reason": span.reason,
                    **({"source_id": span.source_id} if span.source_id else {}),
                }
                for span in self.verified_spans
            ],
            "unverified_spans": [
                {
                    "text": span.text[:120],
                    "language": span.language,
                    "reason": span.reason,
                }
                for span in self.unverified_spans
            ],
            "db_checked": self.db_checked,
            "bundle_whitelisted": self.bundle_whitelisted,
        }


def enforcement_enabled() -> bool:
    """Whether unverified spans may alter prose (default: ENFORCE).

    The report-only default shipped unverified Greek/Latin to readers with only
    a metadata annotation. The default is now enforcement: a line carrying an
    ancient-text span that could not be verified against the evidence bundle or
    the corpus is dropped. Set ``ELEUTHERIA_TEXT_VERIFIER_ENFORCE=false`` to go
    back to report-only.
    """
    raw = os.getenv(ENFORCE_ENV_VAR, "true").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def extract_greek_runs(text: str) -> list[tuple[str, int]]:
    """Extract all Greek text runs from a string, with their positions.

    Returns list of (greek_text, char_position) tuples.
    Only returns runs with 2+ Greek characters.
    """
    runs: list[tuple[str, int]] = []
    for match in _GREEK_RUN_RE.finditer(text):
        greek_text = match.group().strip()
        if _count_greek_chars(greek_text) >= 2:
            runs.append((greek_text, match.start()))
    return runs


def extract_quoted_latin_spans(text: str) -> list[tuple[str, int]]:
    """Quoted Latin-script spans that look like candidate ancient Latin.

    Only QUOTED spans (any paired quote marks, incl. guillemets and German
    low-9 quotes) are extracted: unquoted Latin prose is statistically
    indistinguishable from English here, and the blockquote Latin gate in
    ``graph_nodes`` already covers quotation-formatted lines. A span counts
    as candidate Latin when none of its folded words is a modern function
    word (en/fr/de/it) — the same heuristic as the render-time gate — AND
    at most :data:`_ENGLISH_CONTENT_RATIO` of its alphabetic tokens is in
    the small :data:`_ENGLISH_CONTENT_WORDS` lexicon (quoted English phrases
    built from content words carry no function words, so the stopword check
    alone misclassified them as Latin) AND it passes the POSITIVE lexical
    screen :func:`looks_like_latin` (a strong Latin function word, or two
    tokens with a Latin-specific ending, and no unambiguous English function
    word).

    The positive screen is what stopped English phrases outside the content
    lexicon from being classified as Latin and deleted from answers
    ("same causes, same effects", "Prohairesis in Epictetus" — production,
    2026-08). Its cost is recall: Latin written entirely in content words
    with no Latin ending is no longer extracted. That trade is deliberate —
    silently deleting an English phrase from a scholarly answer is worse
    than not verifying an unusual Latin one.
    """
    spans: list[tuple[str, int]] = []
    for match in _QUOTED_SPAN_RE.finditer(text):
        quote = next(group for group in match.groups() if group is not None)
        if _GREEK_CHAR_RE.search(quote):
            continue  # Greek-bearing quotes are handled by the run extractor
        words = fold_ancient_text(quote).split()
        if len(words) <= _MAX_TERM_WORDS:
            continue
        if any(word in MODERN_STOPWORDS for word in words):
            continue
        alpha_words = [word for word in words if word.isalpha()]
        if not alpha_words:
            continue
        english_hits = sum(1 for word in alpha_words if word in _ENGLISH_CONTENT_WORDS)
        if english_hits / len(alpha_words) > _ENGLISH_CONTENT_RATIO:
            continue
        if not looks_like_latin(words):
            continue
        spans.append((quote, match.start()))
    return spans


def is_known_term(text: str) -> bool:
    """Free pass: 1-2-word spans (vocabulary, technical phrases, titles) and
    curated single-word technical terms. Anything longer is quotation-shaped
    and must be verified against evidence or the corpus."""
    cleaned = text.strip().strip(_TOKEN_STRIP_CHARS)
    if not cleaned:
        return True
    if cleaned in _KNOWN_TERMS:
        return True
    return len(cleaned.split()) <= _MAX_TERM_WORDS


async def verify_ancient_text(
    answer: str,
    db: Any,
    *,
    evidence_texts: Sequence[str] = (),
    schema: str | None = None,
) -> VerificationResult:
    """Verify every ancient-text span in ``answer``.

    ``schema`` defaults to ``ELEUTHERIA_DB_SCHEMA`` — the same env var the
    rest of the graphrag DB layer reads (``graph_helpers``, ``graph_nodes``,
    the agent tools) — falling back to ``free_will``. Resolved at call time
    so tests and deployments can repoint it without re-importing.

    Per-span resolution order:

    1. free pass — 1-2-word vocabulary and curated single-word terms;
    2. whitelist — the span appears (folded, word-boundary-aligned) in one
       of ``evidence_texts`` (the bundles/evidence already gathered for this
       query): verified with NO DB query;
    3. bounded DB probe — anchor-token candidate fetch, folded comparison
       in Python (see :func:`_search_passage_for_text`);
    4. otherwise the span is recorded as unverified. Nothing is deleted
       here — enforcement is the caller's decision (see
       :func:`enforce_answer` / :func:`enforcement_enabled`).
    """
    if schema is None:
        schema = os.getenv("ELEUTHERIA_DB_SCHEMA", "free_will")
    result = VerificationResult()
    references = prepare_references(list(evidence_texts))

    spans: list[tuple[str, int, str]] = [
        (text, position, "greek") for text, position in extract_greek_runs(answer)
    ]
    spans += [
        (text, position, "latin")
        for text, position in extract_quoted_latin_spans(answer)
    ]

    for span_text, position, language in spans:
        if is_known_term(span_text):
            continue
        segments = _folded_segments(span_text)
        if not segments:
            continue
        legacy_segments = _folded_segments(span_text, fold=legacy_fold_ancient_text)

        check = SpanCheck(
            text=span_text,
            language=language,
            position=position,
            status="unverified",
        )

        matched = _first_match(segments, legacy_segments, references)
        if matched is not None:
            check.status = "bundle"
            check.reason = matched
            result.bundle_whitelisted += 1
            result.verified_spans.append(check)
            _log_decision(check, kept=True)
            continue

        result.db_checked += 1
        found, candidates_seen = (
            await _search_passage_for_text(
                span_text, segments, legacy_segments, db, schema
            )
            if db is not None
            else (None, False)
        )
        if found:
            check.status = str(found["source"])
            check.source_id = found.get("passage_id")
            check.source_title = found.get("title")
            check.reason = str(found.get("reason") or MATCH_EXACT)
            result.verified_spans.append(check)
            _log_decision(check, kept=True)
        else:
            check.reason = (
                REASON_REFERENCE_MISMATCH
                if candidates_seen or _anchor_seen_in_references(span_text, references)
                else REASON_UNATTESTED
            )
            result.unverified_spans.append(check)
            _log_decision(check, kept=False)

    if result.unverified_spans:
        logger.warning(
            "Text verifier: %d unverified ancient-text span(s)",
            len(result.unverified_spans),
        )
        for span in result.unverified_spans:
            logger.warning(
                "  UNVERIFIED (%s, %s): %s",
                span.language,
                span.reason,
                span.text[:100],
            )

    return result


def _log_decision(check: SpanCheck, *, kept: bool) -> None:
    """One INFO line per gate decision, carrying the reason class.

    Audits distinguish real fabrication (``unattested``) from a reference the
    span simply is not in (``reference-mismatch``) and from the two rescue
    classes (``normalized-pass`` / ``fuzzy-pass``) that used to be silent
    deletions.
    """
    logger.info(
        "text-gate: %s ancient-text span (%s, reason=%s, source=%s): %s",
        "kept" if kept else "removed",
        check.language,
        check.reason,
        check.status,
        check.text[:100],
    )


def _first_match(
    segments: list[str],
    legacy_segments: list[str],
    references: Sequence[PreparedReference],
) -> str | None:
    """Strongest match class of the span across the prepared references."""
    for reference in references:
        matched = containment_class(
            segments, reference, legacy_segments=legacy_segments
        )
        if matched is not None:
            return matched
    return None


def _anchor_seen_in_references(
    span_text: str, references: Sequence[PreparedReference]
) -> bool:
    """Whether some evidence reference at least shares an anchor token.

    Separates ``reference-mismatch`` (a plausible source exists, the span is
    not in it) from ``unattested`` (the span's rarest words appear nowhere).
    """
    anchors = [fold_ancient_text(anchor) for anchor in _anchor_tokens(span_text)]
    return any(
        contains_word_bounded(reference.folded, anchor)
        for reference in references
        for anchor in anchors
        if anchor
    )


def enforce_answer(answer: str, result: VerificationResult) -> str:
    """Drop whole lines containing unverified spans (enforce mode only).

    The whole line goes, not just the span: stripping the quote marks or the
    span while keeping surrounding text would launder an unverifiable
    quotation into plain prose. Callers must gate this behind
    :func:`enforcement_enabled` — the default deployment is report-only.

    Three policies repair the collateral damage the raw line-drop caused (see
    module docstring of the tests):

    * **Paired removal.** When the withheld line is the ORIGINAL half of a
      quotation block, its translation is not left dangling as a translation
      of text the answer just declared unverifiable: the original line is
      removed outright (no placeholder) and the surviving translation carries
      :data:`WITHHELD_ORIGINAL_MARKER`. Never a translation without an
      original *silently*.
    * **No terminal placeholders.** Trailing placeholder blocks — and the
      headers they were the whole content of — are stripped, so an answer
      never ends on ``[removed: …]``.
    * **Honest enumeration.** When the removal amputated the end of the answer
      or broke an announced enumeration, one deterministic line
      (:data:`WITHHELD_ITEM_NOTE`) says so.
    """
    if result.all_verified:
        return answer

    lines = answer.split("\n")
    offsets: list[int] = []
    cursor = 0
    for line in lines:
        offsets.append(cursor)
        cursor += len(line) + 1

    drop: set[int] = set()
    for span in result.unverified_spans:
        start = span.position
        end = span.position + len(span.text)
        for index, line_start in enumerate(offsets):
            line_end = line_start + len(lines[index])
            if start <= line_end and end >= line_start:
                drop.add(index)

    rendered = _apply_removals(lines, drop)
    rendered, truncated = _strip_terminal_placeholders(rendered)
    if truncated or _enumeration_broken(lines, rendered):
        rendered = _append_withheld_note(rendered)
    return "\n".join(rendered)


# ── Removal rendering: paired original/translation ───────────────────────────

_BLOCKQUOTE_RE = re.compile(r"^\s*>")
_ORIGINAL_LABEL_RE = re.compile(
    r"^\s*>?\s*(?:\*\*|__)?\s*(?:original|greek|latin|text)\b\s*(?:\*\*|__)?\s*:",
    re.IGNORECASE,
)
_TRANSLATION_LABEL_RE = re.compile(
    r"^\s*>?\s*(?:\*\*|__)?\s*(?:translation|english|trans\.?)\b\s*(?:\*\*|__)?\s*:",
    re.IGNORECASE,
)


def _block_bounds(lines: Sequence[str], index: int) -> tuple[int, int]:
    """Half-open bounds of the blockquote block containing ``index``."""
    start = index
    while start > 0 and _BLOCKQUOTE_RE.match(lines[start - 1]):
        start -= 1
    end = index + 1
    while end < len(lines) and _BLOCKQUOTE_RE.match(lines[end]):
        end += 1
    return start, end


def _paired_translation_index(
    lines: Sequence[str], index: int, drop: set[int]
) -> int | None:
    """Index of the surviving translation paired with the withheld original.

    Pairing is scoped to the enclosing blockquote block, which is how the
    renderer emits quotations (``> Original: …`` / ``> Translation: …``, or an
    unlabelled ancient line followed by its English line). Explicit labels win;
    otherwise the surviving line of the block that carries no Greek is taken as
    the translation.
    """
    if not _BLOCKQUOTE_RE.match(lines[index]):
        return None
    start, end = _block_bounds(lines, index)
    candidates = [
        position
        for position in range(start, end)
        if position != index and position not in drop and lines[position].strip() != ">"
    ]
    for position in candidates:
        if _TRANSLATION_LABEL_RE.match(lines[position]):
            return position
    if _ORIGINAL_LABEL_RE.match(lines[index]):
        return None
    for position in candidates:
        if not _GREEK_CHAR_RE.search(lines[position]) and not _ORIGINAL_LABEL_RE.match(
            lines[position]
        ):
            return position
    return None


def _apply_removals(lines: list[str], drop: set[int]) -> list[str]:
    """Render the removals, keeping paired translations coherent."""
    annotate: set[int] = set()
    suppress: set[int] = set()
    for index in sorted(drop):
        paired = _paired_translation_index(lines, index, drop)
        if paired is not None:
            annotate.add(paired)
            suppress.add(index)

    rendered: list[str] = []
    for index, line in enumerate(lines):
        if index in suppress:
            continue
        if index in drop:
            rendered.append(_REMOVED_LINE_MARKER)
            continue
        if index in annotate:
            rendered.append(f"{line.rstrip()} {WITHHELD_ORIGINAL_MARKER}")
            continue
        rendered.append(line)
    return rendered


# ── Terminal amputation ──────────────────────────────────────────────────────


def _is_header_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith("#"):
        return True
    return len(stripped) <= 80 and stripped.endswith(":") and stripped.count(" ") <= 8


def _strip_terminal_placeholders(lines: list[str]) -> tuple[list[str], bool]:
    """Remove trailing placeholder blocks — and headers left heading nothing.

    An answer must never END on ``[removed: unverified ancient text]``: that
    reads as an amputation rather than an answer. Returns the surviving lines
    and whether anything was stripped from the end.
    """
    kept = list(lines)
    truncated = False
    while kept:
        last = kept[-1]
        if not last.strip():
            kept.pop()
            continue
        if last.strip() == _REMOVED_LINE_MARKER:
            kept.pop()
            truncated = True
            continue
        if truncated and _is_header_line(last):
            kept.pop()
            continue
        break
    return kept, truncated


# ── Broken enumerations ──────────────────────────────────────────────────────

_ORDINAL_ITEM_RE = re.compile(
    r"^\s*(?:[-*>]\s*)?(?:\*\*|__)?\s*"
    r"(?:first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth)(?:ly)?\b",
    re.IGNORECASE,
)
_NUMBERED_ITEM_RE = re.compile(r"^\s*\d+[.)]\s+")
_NUMBER_WORDS = {
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}
_ANNOUNCED_COUNT_RE = re.compile(
    r"\b(two|three|four|five|six|seven|eight|nine|ten)\b(?:\s+\w+){0,3}?\s+"
    r"\b(points?|things?|reasons?|arguments?|considerations?|objections?|"
    r"observations?|responses?|replies|claims?|theses|steps?|factors?|ways?|"
    r"senses?|moves?|strands?|grounds?)\b",
    re.IGNORECASE,
)


def _enumerated_items(lines: Sequence[str]) -> int:
    return sum(
        1
        for line in lines
        if _ORDINAL_ITEM_RE.match(line) or _NUMBERED_ITEM_RE.match(line)
    )


def _announced_count(lines: Sequence[str]) -> int:
    counts = [
        _NUMBER_WORDS[match.group(1).lower()]
        for line in lines
        for match in _ANNOUNCED_COUNT_RE.finditer(line)
    ]
    return max(counts) if counts else 0


def _enumeration_broken(before: Sequence[str], after: Sequence[str]) -> bool:
    """Whether the gate left an announced enumeration short of its items."""
    delivered_before = _enumerated_items(before)
    delivered_after = _enumerated_items(after)
    if delivered_after < delivered_before:
        return True
    announced = _announced_count(after)
    return bool(announced and delivered_after < announced <= delivered_before)


def _append_withheld_note(lines: list[str]) -> list[str]:
    if any(line.strip() == WITHHELD_ITEM_NOTE for line in lines):
        return lines
    kept = list(lines)
    while kept and not kept[-1].strip():
        kept.pop()
    if kept:
        kept.append("")
    kept.append(WITHHELD_ITEM_NOTE)
    return kept


def _folded_segments(
    span_text: str,
    fold: Any = fold_ancient_text,
) -> list[str]:
    """Fold each ellipsis-separated segment; drop sub-2-char leftovers.

    ``fold`` is the normalizer to apply — the default canonical one, or
    :func:`legacy_fold_ancient_text` when the caller needs the pre-fix form to
    classify a rescue as ``normalized-pass``. Both runs split identically, so
    the two lists stay index-aligned.
    """
    segments: list[str] = []
    for part in _ELLIPSIS_RE.split(span_text):
        folded = fold(part)
        if len(re.sub(r"\W+", "", folded)) >= 2:
            segments.append(folded)
    return segments


def _anchor_tokens(span_text: str) -> list[str]:
    """Longest distinct tokens of the span, in original orthography.

    The anchor must match the corpus byte-for-byte for the LIKE probe to
    hit; only ONE word of the span needs to match exactly — the rest of the
    accent/sigma/punctuation tolerance lives in the Python fold-compare.
    Longest first: longer tokens are rarer, keeping candidate sets small.
    """
    tokens = [token.strip(_TOKEN_STRIP_CHARS) for token in span_text.split()]
    tokens = [token for token in tokens if len(token) >= _ANCHOR_MIN_CHARS]
    tokens.sort(key=len, reverse=True)
    return list(dict.fromkeys(tokens))[:_MAX_ANCHORS]


def _fold_match(
    rows: Sequence[Any],
    segments: list[str],
    legacy_segments: list[str],
) -> tuple[Any, str] | None:
    """First candidate row containing the span, with its match class.

    The candidate is compared under the canonical normalizer and, failing
    that, against its dittography-collapsed form: byte noise in the corpus row
    must not condemn an accurate quote.
    """
    for row in rows or []:
        text = row.get("text_content") or ""
        matched = containment_class(
            segments,
            PreparedReference(str(text)),
            legacy_segments=legacy_segments,
        )
        if matched is not None:
            return row, matched
    return None


async def _search_passage_for_text(
    span_text: str,
    segments: list[str],
    legacy_segments: list[str],
    db: Any,
    schema: str,
) -> tuple[dict[str, Any] | None, bool]:
    """Bounded corpus probe for one span.

    A LIKE over the *folded* form of 69k passages is un-indexable, so the
    probe instead fetches up to ``_CANDIDATE_LIMIT`` candidate rows per
    anchor token (exact orthography) from the passages table and from
    passage/quote kg_nodes, then fold-compares the candidates in Python.
    Audit-flagged kg_nodes (non-empty ``metadata.integrity_status``) are
    excluded: a node flagged ``greek_unverified`` /
    ``fabrication_confirmed_pending_fix`` must never count as verification.
    Worst case: ``_MAX_ANCHORS × unicode-variants × 2 tables`` LIKE queries,
    each capped at ``_CANDIDATE_LIMIT`` rows.

    Returns ``(hit, candidates_seen)``. ``candidates_seen`` records whether ANY
    candidate row came back: a span whose rarest tokens hit nothing in the
    corpus is ``unattested``, while a span that lost against real candidate
    rows is a ``reference-mismatch`` — two very different audit findings.
    """
    candidates_seen = False
    for anchor in _anchor_tokens(span_text):
        for variant in _unicode_variants(anchor):
            try:
                rows = await db.fetch(
                    f"""
                    SELECT p.passage_id::text AS passage_id,
                           w.title,
                           p.canonical_ref,
                           p.text_content
                    FROM {schema}.passages p
                    JOIN {schema}.ancient_works w ON w.work_id = p.work_id
                    WHERE p.text_content LIKE '%' || $1 || '%'
                    LIMIT {_CANDIDATE_LIMIT}
                    """,
                    variant,
                )
            except Exception:
                logger.debug(
                    "Passage probe failed for anchor: %s", variant[:40], exc_info=True
                )
                rows = []
            candidates_seen = candidates_seen or bool(rows)
            match = _fold_match(rows, segments, legacy_segments)
            if match is not None:
                hit, reason = match
                return {
                    "passage_id": hit.get("passage_id"),
                    "title": hit.get("title"),
                    "canonical_ref": hit.get("canonical_ref"),
                    "source": "db_passage",
                    "reason": reason,
                }, candidates_seen

            try:
                rows = await db.fetch(
                    f"""
                    SELECT node_id AS passage_id,
                           label AS title,
                           description AS text_content
                    FROM {schema}.kg_nodes
                    WHERE description LIKE '%' || $1 || '%'
                      AND type IN ('passage', 'quote')
                      AND (metadata->>'integrity_status' IS NULL
                           OR metadata->>'integrity_status' = '')
                    LIMIT {_CANDIDATE_LIMIT}
                    """,
                    variant,
                )
            except Exception:
                logger.debug(
                    "KG node probe failed for anchor: %s", variant[:40], exc_info=True
                )
                rows = []
            candidates_seen = candidates_seen or bool(rows)
            match = _fold_match(rows, segments, legacy_segments)
            if match is not None:
                hit, reason = match
                return {
                    "passage_id": hit.get("passage_id"),
                    "title": hit.get("title"),
                    "canonical_ref": None,
                    "source": "db_node",
                    "reason": reason,
                }, candidates_seen

    return None, candidates_seen


def _unicode_variants(text: str) -> list[str]:
    """Return Unicode normalization variants of a string."""
    variants = [text]
    nfc = unicodedata.normalize("NFC", text)
    if nfc != text:
        variants.append(nfc)
    nfd = unicodedata.normalize("NFD", text)
    if nfd != text and nfd != nfc:
        variants.append(nfd)
    return variants


def _count_greek_chars(text: str) -> int:
    """Count Greek characters in a string."""
    count = 0
    for ch in text:
        cp = ord(ch)
        if cp in _GREEK_BASIC or cp in _GREEK_EXTENDED:
            count += 1
    return count
