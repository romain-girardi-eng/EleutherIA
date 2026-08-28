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

Before a line is dropped, :func:`reattribute_unverified_spans` gives a span
that IS verbatim in exactly one corpus locus its correct citation instead of
deleting it (``reattributed_spans`` in the same metadata record), and keeps —
without any citation — two shapes of attested text that are not quotations: a
list of technical terms whose every item is attested, and a phrase of at most
four tokens that is verbatim in the corpus (``attested_spans``).
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
from eleutheria_graphrag.agents.state import Citation, EvidenceLayer

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
#   ambiguous-locus    — the span IS verbatim in the corpus, but in more than
#                        one distinct work+locus, so no single passage can be
#                        cited for it; removed, with the loci recorded.
#   term-list-attested — a comma/καὶ-separated list of technical terms: the
#                        run as a whole is in no passage, every item is; kept
#                        without citation (see "Attested runs kept" below).
#   short-phrase-attested — a run of at most four tokens verbatim in the
#                        corpus (in one locus or many); kept without citation.
REASON_UNATTESTED = "unattested"
REASON_REFERENCE_MISMATCH = "reference-mismatch"
REASON_AMBIGUOUS_LOCUS = "ambiguous-locus"
REASON_TERM_LIST_ATTESTED = "term-list-attested"
REASON_SHORT_PHRASE_ATTESTED = "short-phrase-attested"

# ``SpanCheck.status`` of the two kept-without-citation shapes.
STATUS_TERM_LIST = "term-list"
STATUS_SHORT_PHRASE = "short-phrase"

# ``Citation.verification_note`` of a citation the re-attribution pass added:
# the span it backs is verbatim in exactly one corpus locus. The publication
# gate reads this note (via ``text_verification.reattributed_citation_ids``)
# so the citation is not withheld as unaudited.
REATTRIBUTION_NOTE = "re-attributed by text verifier: span verbatim in corpus passage"

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
    # "bundle" | "db_passage" | "db_node" | "term-list" | "short-phrase"
    # | "unverified"
    status: str
    source_id: str | None = None
    source_title: str | None = None
    # "exact" | "normalized-pass" | "fuzzy-pass" | "term-list-attested"
    # | "short-phrase-attested" for kept spans, "unattested" |
    # "reference-mismatch" | "ambiguous-locus" for removed ones.
    reason: str = MATCH_EXACT
    # Distinct corpus loci holding the span verbatim when it was removed as
    # ``ambiguous-locus`` — the audit record of WHY it could not be cited.
    loci: list[str] = field(default_factory=list)
    # Kept as a term list: the items, each verbatim-attested on its own.
    items: list[str] = field(default_factory=list)
    # Kept as a short phrase: how many distinct loci hold it verbatim.
    loci_count: int = 0
    # List-shaped run removed: the first item that is attested nowhere.
    failed_item: str | None = None

    @property
    def kept_without_citation(self) -> bool:
        return self.status in {STATUS_TERM_LIST, STATUS_SHORT_PHRASE}


@dataclass
class AttestedLocus:
    """One corpus passage row holding a span verbatim (after folding)."""

    passage_id: str
    work_id: str
    canonical_ref: str
    title: str
    author: str
    cts_urn: str | None
    text_content: str
    reason: str  # match class: "exact" | "normalized-pass" | "fuzzy-pass"

    @property
    def locus_key(self) -> tuple[str, str]:
        return (self.work_id, self.canonical_ref)

    @property
    def label(self) -> str:
        ref = f" {self.canonical_ref}" if self.canonical_ref else ""
        return f"{self.author or 'Unknown'}, {self.title}{ref}"


@dataclass
class Reattribution:
    """A span kept because it is verbatim in exactly one corpus locus, with
    its citation corrected to that locus."""

    text: str
    language: str
    position: int
    locus: AttestedLocus
    to_ref: str  # the ``Citation.ref`` now backing the span
    from_ref: str | None = None  # the adjacent marker that was replaced
    from_id: str | None = None  # the citation id that marker resolved to
    citation_added: bool = False

    def to_metadata(self) -> dict[str, Any]:
        return {
            "text": self.text[:120],
            "language": self.language,
            "from_ref": self.from_ref,
            "from_id": self.from_id,
            "to_ref": self.to_ref,
            "to_passage_id": self.locus.passage_id,
            "to_label": self.locus.label,
            "reason": self.locus.reason,
            "citation_added": self.citation_added,
        }


@dataclass
class VerificationResult:
    """Aggregate outcome of one answer's ancient-text verification."""

    verified_spans: list[SpanCheck] = field(default_factory=list)
    unverified_spans: list[SpanCheck] = field(default_factory=list)
    db_checked: int = 0
    bundle_whitelisted: int = 0
    reattributed_spans: list[Reattribution] = field(default_factory=list)

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

        Spans kept without a citation (term lists, short attested phrases)
        are verified spans — they never count as ``unverified`` — and are
        listed again under ``attested_spans`` with the policy that kept them.
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
                    **({"loci": list(span.loci)} if span.loci else {}),
                    **_failed_item_field(span),
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
                    **_attested_policy_fields(span),
                }
                for span in self.verified_spans
            ],
            "unverified_spans": [
                {
                    "text": span.text[:120],
                    "language": span.language,
                    "reason": span.reason,
                    **({"loci": list(span.loci)} if span.loci else {}),
                    **_failed_item_field(span),
                }
                for span in self.unverified_spans
            ],
            "attested_spans": [
                {
                    "text": span.text[:120],
                    "language": span.language,
                    "status": span.status,
                    "reason": span.reason,
                    **_attested_policy_fields(span),
                }
                for span in self.verified_spans
                if span.kept_without_citation
            ],
            "reattributed_spans": [
                item.to_metadata() for item in self.reattributed_spans
            ],
            "db_checked": self.db_checked,
            "bundle_whitelisted": self.bundle_whitelisted,
        }


def _attested_policy_fields(span: SpanCheck) -> dict[str, Any]:
    if span.status == STATUS_TERM_LIST:
        return {"items": list(span.items)}
    if span.status == STATUS_SHORT_PHRASE:
        return {"loci_count": span.loci_count}
    return {}


def _failed_item_field(span: SpanCheck) -> dict[str, Any]:
    return {"failed_item": span.failed_item} if span.failed_item else {}


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


# ── Re-attribution: keep verbatim Greek cited under the wrong reference ──────
#
# The bounded anchor probe above answers "is this span somewhere in the
# corpus?"; it never checks WHICH passage the answer cited for it. A span the
# probe missed (common anchor tokens fill the candidate limit) or a span the
# model attached to the wrong reference used to be deleted outright. Deleting
# a genuine quotation because its reference is wrong loses good content: the
# pass below re-probes each unverified span with far more selective anchors
# (the whole span, then two-word windows), and when the span is verbatim —
# under the SAME fold-compare the verifier uses — in exactly one distinct
# work+locus, keeps it and rewrites its citation to that passage. Nothing
# that is not verbatim-attested is ever kept; a span attested in several
# distinct loci is still removed, with the loci recorded.

_REATTRIBUTION_CANDIDATE_LIMIT = 50
_MAX_REATTRIBUTION_ANCHORS = 3

_CLASSIC_REF_RE = re.compile(r"^P(\d+)$")
_CLASSIC_MARKER_RE = re.compile(r"\[P(\d+)\]")
_DIALECTICAL_MARKER_RE = re.compile(r"\[(?:P|passage)_[^\]]+\]")
# A citation marker immediately following a span (after any closing quote
# marks / brackets): ``[P3]``, ``[passage_<id>: …]``, ``[P_<id>: …]``.
# (No ``^``: ``re.match(line, pos)`` anchors at ``pos`` on its own, while
# ``^`` would only ever match at offset 0.)
_ADJACENT_MARKER_RE = re.compile(
    r"(?P<lead>[\s»\"”’)\]]*?)(?P<marker>\[(?P<kind>P|passage)_?(?P<body>[^\]]+)\])"
)
_CLOSING_CHARS = '»"”’)]'


@dataclass
class ReattributionOutcome:
    """What the re-attribution pass changed."""

    text: str
    citations: list[Citation] = field(default_factory=list)  # added
    reattributed: list[Reattribution] = field(default_factory=list)


def _span_anchors(span_text: str) -> list[str]:
    """Selective LIKE anchors for the locus probe, in original orthography.

    The whole span first (the most selective pattern there is), then the
    longest two-word windows: a two-word window is orders of magnitude rarer
    than the single tokens the bounded probe anchors on, so the candidate
    limit is no longer what decides whether a genuine passage is found.
    """
    words = [
        token.strip(_TOKEN_STRIP_CHARS)
        for part in _ELLIPSIS_RE.split(span_text)
        for token in part.split()
    ]
    words = [word for word in words if word]
    anchors: list[str] = []
    if not _ELLIPSIS_RE.search(span_text):
        whole = " ".join(span_text.split()).strip(_TOKEN_STRIP_CHARS).strip()
        if whole:
            anchors.append(whole)
    windows = [f"{a} {b}" for a, b in zip(words, words[1:], strict=False)]
    windows.sort(key=len, reverse=True)
    for window in windows:
        if len(anchors) >= _MAX_REATTRIBUTION_ANCHORS + 1:
            break
        if window not in anchors:
            anchors.append(window)
    return anchors


_ACUTE = "\u0301"  # combining acute
_GRAVE = "\u0300"  # combining grave
_GREEK_VOWELS = frozenset("αεηιουωΑΕΗΙΟΥΩ")


def _swap_final_accent(word: str, source: str, target: str) -> str:
    """``word`` with the accent of its FINAL syllable swapped, else unchanged."""
    decomposed = unicodedata.normalize("NFD", word)
    index = decomposed.rfind(source)
    if index < 0:
        return word
    if any(char in _GREEK_VOWELS for char in decomposed[index + 1 :]):
        return word  # the accent sits on an earlier syllable
    swapped = decomposed[:index] + target + decomposed[index + 1 :]
    return unicodedata.normalize("NFC", swapped)


def _final_accent_variants(text: str) -> list[str]:
    """``text`` plus its all-grave and all-acute final-syllable forms.

    An oxytone word carries a grave before another word and an acute before
    punctuation or in isolation; a model quoting lexical forms writes the
    acute where running corpus text has the grave (``δυνατόν καὶ μή`` against
    the corpus's ``δυνατὸν καὶ μὴ``). The fold-compare is accent-blind, but
    the LIKE anchor is not — so both accent forms are probed. One extra
    LIKE per anchor and direction, still bounded.
    """
    words = text.split()
    variants = [text]
    for source, target in ((_ACUTE, _GRAVE), (_GRAVE, _ACUTE)):
        variant = " ".join(_swap_final_accent(word, source, target) for word in words)
        if variant not in variants:
            variants.append(variant)
    return variants


def _anchor_probe_variants(anchor: str) -> list[str]:
    """Accent × Unicode-normalization forms of a locus-probe anchor."""
    return [
        variant
        for accent_form in _final_accent_variants(anchor)
        for variant in _unicode_variants(accent_form)
    ]


async def locate_verbatim_loci(
    span_text: str,
    db: Any,
    schema: str,
) -> list[AttestedLocus]:
    """Every corpus passage row holding ``span_text`` verbatim (folded compare).

    Passages table only — a re-attributed citation must point at a real
    passage with a work and a locus, never at a KG quote node. Bounded:
    at most ``(1 + _MAX_REATTRIBUTION_ANCHORS) × unicode-variants`` LIKE
    probes, each capped at ``_REATTRIBUTION_CANDIDATE_LIMIT`` rows.
    """
    segments = _folded_segments(span_text)
    if not segments:
        return []
    legacy_segments = _folded_segments(span_text, fold=legacy_fold_ancient_text)
    found: dict[str, AttestedLocus] = {}
    probed: set[str] = set()
    for anchor in _span_anchors(span_text):
        for variant in _anchor_probe_variants(anchor):
            if variant in probed:
                continue
            probed.add(variant)
            try:
                rows = await db.fetch(
                    f"""
                    SELECT p.passage_id::text AS passage_id,
                           p.work_id::text AS work_id,
                           p.canonical_ref,
                           p.cts_urn,
                           p.text_content,
                           w.title,
                           w.author
                    FROM {schema}.passages p
                    JOIN {schema}.ancient_works w ON w.work_id = p.work_id
                    WHERE p.text_content LIKE '%' || $1 || '%'
                    LIMIT {_REATTRIBUTION_CANDIDATE_LIMIT}
                    """,
                    variant,
                )
            except Exception:
                logger.debug(
                    "Locus probe failed for anchor: %s", variant[:40], exc_info=True
                )
                rows = []
            for row in rows or []:
                passage_id = str(row.get("passage_id") or "")
                if not passage_id or passage_id in found:
                    continue
                matched = containment_class(
                    segments,
                    PreparedReference(str(row.get("text_content") or "")),
                    legacy_segments=legacy_segments,
                )
                if matched is None:
                    continue
                found[passage_id] = AttestedLocus(
                    passage_id=passage_id,
                    work_id=str(row.get("work_id") or ""),
                    canonical_ref=str(row.get("canonical_ref") or ""),
                    title=str(row.get("title") or ""),
                    author=str(row.get("author") or ""),
                    cts_urn=row.get("cts_urn") or None,
                    text_content=str(row.get("text_content") or ""),
                    reason=matched,
                )
    return list(found.values())


# ── Attested runs kept without a citation ────────────────────────────────────
#
# Two shapes of ancient text are attested yet are not quotations, and the
# line drop destroyed good prose for them (production, 2026-08, an answer on
# De principiis III.1):
#
# * a LIST OF TECHNICAL TERMS — "ἕξις, φύσις, ψυχή" — is scholarly usage.
#   The run as a whole is in no passage; every lexeme is. Each item (at most
#   _TERM_LIST_MAX_ITEM_TOKENS folded tokens) is verified on its own through
#   the same whitelist / bounded-probe / locus-probe chain, and the run is
#   kept only when EVERY item is verbatim-attested somewhere. Two guards
#   keep this from laundering a sentence chunk by chunk: a run that IS
#   verbatim somewhere as a whole is quotation-shaped and never treated as
#   a list (it follows the unique/ambiguous rules), and an item carrying a
#   clause particle (εἰ, ὅτι, γάρ, μή, …) disqualifies the run.
# * a SHORT PHRASE of at most _SHORT_PHRASE_MAX_TOKENS folded tokens that is
#   verbatim in the corpus — "καὶ μὴ γενέσθαι", six loci — cannot be a
#   fabricated quotation (it exists), and it is too short to be a locatable
#   citation: such a phrase is idiom or technical formula, found in one
#   locus or in many, and its multi-locus attestation is the norm, not an
#   ambiguity. Kept, no re-attribution, no citation.
#
# Threshold: the free pass already trusts one- and two-word runs as
# vocabulary; three and four folded tokens is the band where a run is still
# phrase-sized (a negated infinitive, an article + noun + genitive). From
# five tokens on, a run reads as a quotation and keeps the re-attribution
# rules unchanged (unique locus → re-cited; several → removed; none →
# removed). Neither policy adds a citation, and nothing that is not
# verbatim-attested is ever kept.

_SHORT_PHRASE_MAX_TOKENS = 4
_TERM_LIST_MAX_ITEM_TOKENS = 3
_TERM_LIST_MIN_ITEMS = 2
_TERM_LIST_SPLIT_RE = re.compile(r"\s*[,;·]\s*|\s+κα[ὶί]\s+")
# Folded clause particles / conjunctions / negations: an item holding one is
# a clause fragment, not a term. (``η`` is deliberately absent — folded, it
# is also the feminine article.)
_CLAUSE_PARTICLES = frozenset(
    {
        "ει",
        "εαν",
        "οτι",
        "γαρ",
        "δε",
        "μεν",
        "αν",
        "ου",
        "ουκ",
        "ουχ",
        "ουχι",
        "μη",
        "μηδε",
        "ουδε",
        "ως",
        "ινα",
        "αλλα",
        "τε",
        "ουν",
        "αρα",
        "δη",
        "επει",
        "οταν",
        "οτε",
        "ωστε",
        "ειτε",
        "ουτε",
        "μητε",
    }
)


def folded_token_count(span_text: str) -> int:
    """Tokens of a span after the verifier's own normalization."""
    return len(fold_ancient_text(span_text).split())


def term_list_items(span_text: str) -> list[str]:
    """Items of a list-shaped run, or ``[]`` when the run is not a term list.

    A term list splits on ``,`` / ``;`` / ``·`` / ``καὶ`` into at least
    :data:`_TERM_LIST_MIN_ITEMS` items of at most
    :data:`_TERM_LIST_MAX_ITEM_TOKENS` folded tokens each, none of which
    carries a clause particle. Elided runs are quotation-shaped and never
    lists.
    """
    if _ELLIPSIS_RE.search(span_text):
        return []
    items: list[str] = []
    for raw in _TERM_LIST_SPLIT_RE.split(span_text.strip()):
        item = raw.strip().strip(_TOKEN_STRIP_CHARS).strip()
        tokens = fold_ancient_text(item).split()
        if not tokens:
            continue
        if len(tokens) > _TERM_LIST_MAX_ITEM_TOKENS:
            return []
        if any(token in _CLAUSE_PARTICLES for token in tokens):
            return []
        items.append(item)
    if len(items) < _TERM_LIST_MIN_ITEMS:
        return []
    return items


async def _item_attested(
    item: str,
    references: Sequence[PreparedReference],
    db: Any,
    schema: str,
) -> bool:
    """Whether one term-list item is verbatim somewhere: curated vocabulary,
    the query's evidence, the bounded probe, then the locus probe."""
    if item.strip().strip(_TOKEN_STRIP_CHARS) in _KNOWN_TERMS:
        return True
    segments = _folded_segments(item)
    if not segments:
        return False
    legacy_segments = _folded_segments(item, fold=legacy_fold_ancient_text)
    if _first_match(segments, legacy_segments, references) is not None:
        return True
    found, _ = await _search_passage_for_text(
        item, segments, legacy_segments, db, schema
    )
    if found:
        return True
    return bool(await locate_verbatim_loci(item, db, schema))


async def _first_unattested_item(
    items: Sequence[str],
    references: Sequence[PreparedReference],
    db: Any,
    schema: str,
) -> str | None:
    for item in items:
        if not await _item_attested(item, references, db, schema):
            return item
    return None


def _keep_without_citation(
    span: SpanCheck,
    result: VerificationResult,
    *,
    status: str,
    reason: str,
    items: Sequence[str] = (),
    loci_count: int = 0,
) -> None:
    span.status = status
    span.reason = reason
    span.items = list(items)
    span.loci_count = loci_count
    span.failed_item = None
    result.verified_spans.append(span)
    logger.info(
        "text-gate: kept ancient-text span without citation (%s, reason=%s, %s): %s",
        span.language,
        reason,
        f"items={len(items)}" if items else f"loci={loci_count}",
        span.text[:100],
    )


def _marker_scheme(answer: str, citations: Sequence[Citation]) -> str:
    """``"dialectical"`` (``[passage_<id>]`` markers) or ``"classic"`` (``[P<n>]``)."""
    if _DIALECTICAL_MARKER_RE.search(answer):
        return "dialectical"
    if _CLASSIC_MARKER_RE.search(answer):
        return "classic"
    if any(_CLASSIC_REF_RE.match(citation.ref) for citation in citations):
        return "classic"
    if any(citation.ref == citation.id for citation in citations if citation.ref):
        return "dialectical"
    return "classic"


def _next_classic_ref(answer: str, citations: Sequence[Citation]) -> str:
    numbers = [int(m.group(1)) for m in _CLASSIC_MARKER_RE.finditer(answer)]
    numbers += [
        int(m.group(1))
        for citation in citations
        for m in [_CLASSIC_REF_RE.match(citation.ref)]
        if m is not None
    ]
    return f"P{max(numbers, default=0) + 1}"


def _line_index_for(offsets: Sequence[int], lines: Sequence[str], position: int) -> int:
    for index, start in enumerate(offsets):
        if start <= position <= start + len(lines[index]):
            return index
    return len(lines) - 1


def _adjacent_marker(line: str, span_end: int) -> re.Match[str] | None:
    return _ADJACENT_MARKER_RE.match(line, span_end)


def _marker_ref_and_id(
    match: re.Match[str], citations_by_ref: dict[str, Citation]
) -> tuple[str, str | None]:
    """The ref a marker names and the citation id it resolves to (if any)."""
    kind = match.group("kind")
    body = match.group("body").strip()
    if kind == "P" and body.isdigit():
        ref = f"P{body}"
        citation = citations_by_ref.get(ref)
        return ref, (citation.id if citation is not None else None)
    ref_id = body.split(":", 1)[0].strip().lstrip("_")
    return ref_id, ref_id or None


async def reattribute_unverified_spans(
    answer: str,
    result: VerificationResult,
    db: Any,
    *,
    citations: Sequence[Citation] = (),
    schema: str | None = None,
    evidence_texts: Sequence[str] = (),
) -> ReattributionOutcome:
    """Rescue unverified spans that are attested in the corpus.

    For each span still unverified after :func:`verify_ancient_text`, in
    this order:

    * at most :data:`_SHORT_PHRASE_MAX_TOKENS` folded tokens and verbatim in
      at least one locus (one or many) — kept as a short attested phrase,
      no citation (``short-phrase-attested``);
    * verbatim in exactly ONE distinct work+locus — moved to the verified
      spans and cited to that passage: a marker adjacent to the span that
      resolves to a different passage is replaced, otherwise the new marker
      is appended right after the span; a ``Citation`` for the passage is
      added when the answer has none (``verified=True``,
      :data:`REATTRIBUTION_NOTE`);
    * verbatim in MORE than one distinct work+locus — untouched, but its
      reason becomes ``ambiguous-locus`` and the loci are recorded;
    * verbatim in NO passage but list-shaped (:func:`term_list_items`) with
      EVERY item attested — kept as a term list, no citation
      (``term-list-attested``);
    * verbatim in NO passage otherwise — untouched (removed as today,
      ``unattested`` / ``reference-mismatch``; for a list-shaped run the
      first item attested nowhere is recorded as ``failed_item``).

    ``evidence_texts`` are the query's evidence bundles, consulted (before
    any DB probe) when term-list items are verified one by one.

    Mutates ``result`` (span lists, ``reattributed_spans``) and returns the
    rewritten prose with the citations to add. Positions of the spans left
    unverified are shifted so :func:`enforce_answer` still drops the right
    lines. ``db=None`` is a no-op.
    """
    outcome = ReattributionOutcome(text=answer)
    if db is None or not result.unverified_spans:
        return outcome
    if schema is None:
        schema = os.getenv("ELEUTHERIA_DB_SCHEMA", "free_will")
    references = prepare_references(list(evidence_texts))

    citations_by_ref: dict[str, Citation] = {c.ref: c for c in citations if c.ref}
    known_ids: dict[str, Citation] = {c.id: c for c in citations}
    scheme = _marker_scheme(answer, citations)

    lines = answer.split("\n")
    offsets: list[int] = []
    cursor = 0
    for line in lines:
        offsets.append(cursor)
        cursor += len(line) + 1

    remaining: list[SpanCheck] = []
    # Later spans first so an insertion never moves a span not yet handled
    # on the same line.
    for span in sorted(result.unverified_spans, key=lambda s: s.position, reverse=True):
        loci = await locate_verbatim_loci(span.text, db, schema)
        distinct = {locus.locus_key: locus for locus in loci}
        if loci and folded_token_count(span.text) <= _SHORT_PHRASE_MAX_TOKENS:
            _keep_without_citation(
                span,
                result,
                status=STATUS_SHORT_PHRASE,
                reason=REASON_SHORT_PHRASE_ATTESTED,
                loci_count=len(distinct),
            )
            continue
        if not loci:
            # Attested nowhere as a whole: a term list is the one shape whose
            # items may vouch for it (a whole-run attestation, unique or
            # ambiguous, is quotation-shaped and follows the rules below).
            items = term_list_items(span.text)
            failed = (
                await _first_unattested_item(items, references, db, schema)
                if items
                else None
            )
            if items and failed is None:
                _keep_without_citation(
                    span,
                    result,
                    status=STATUS_TERM_LIST,
                    reason=REASON_TERM_LIST_ATTESTED,
                    items=items,
                )
                continue
            span.failed_item = failed
            remaining.append(span)
            continue
        if len(distinct) > 1:
            span.reason = REASON_AMBIGUOUS_LOCUS
            span.loci = sorted(
                f"{locus.label} ({locus.passage_id})" for locus in distinct.values()
            )
            remaining.append(span)
            _log_decision(span, kept=False)
            continue

        locus = next(iter(distinct.values()))
        # Prefer a row already cited by the answer when the locus has several
        # rows (original + commentary record of the same passage).
        for candidate in loci:
            if candidate.passage_id in known_ids:
                locus = candidate
                break

        index = _line_index_for(offsets, lines, span.position)
        line = lines[index]
        span_start = span.position - offsets[index]
        if line[span_start : span_start + len(span.text)] != span.text:
            span_start = line.find(span.text)
        if span_start < 0:
            remaining.append(span)
            continue
        span_end = span_start + len(span.text)

        adjacent = _adjacent_marker(line, span_end)
        from_ref: str | None = None
        from_id: str | None = None
        if adjacent is not None:
            from_ref, from_id = _marker_ref_and_id(adjacent, citations_by_ref)

        existing = known_ids.get(locus.passage_id)
        if existing is not None:
            to_ref = existing.ref
        elif scheme == "dialectical":
            to_ref = locus.passage_id
        else:
            to_ref = _next_classic_ref(outcome.text, [*citations, *outcome.citations])
        new_marker = (
            f"[passage_{locus.passage_id}]"
            if scheme == "dialectical"
            else f"[{to_ref}]"
        )

        if from_id == locus.passage_id or (adjacent is not None and from_ref == to_ref):
            new_line = line  # already cited to the attested passage
            from_ref = from_id = None
        elif (
            adjacent is not None
            and from_id is not None
            and (known_ids.get(from_id) is None or known_ids[from_id].type == "passage")
        ):
            new_line = (
                line[: adjacent.start("marker")]
                + new_marker
                + line[adjacent.end("marker") :]
            )
        else:
            insert_at = span_end
            while insert_at < len(line) and line[insert_at] in _CLOSING_CHARS:
                insert_at += 1
            new_line = f"{line[:insert_at]} {new_marker}{line[insert_at:]}"
            from_ref = from_id = None

        lines[index] = new_line
        delta = len(new_line) - len(line)
        if delta:
            line_start = offsets[index]
            for later in range(index + 1, len(offsets)):
                offsets[later] += delta
            for other in result.unverified_spans:
                if other is not span and other.position > line_start + span_end:
                    other.position += delta

        added = False
        if existing is None:
            outcome.citations.append(
                Citation(
                    ref=to_ref,
                    type="passage",
                    id=locus.passage_id,
                    label=locus.label,
                    layer=EvidenceLayer.PRIMARY,
                    verified=True,
                    verification_note=REATTRIBUTION_NOTE,
                    cts_urn=locus.cts_urn,
                )
            )
            known_ids[locus.passage_id] = outcome.citations[-1]
            citations_by_ref[to_ref] = outcome.citations[-1]
            added = True

        span.status = "db_passage"
        span.source_id = locus.passage_id
        span.source_title = locus.title
        span.reason = locus.reason
        result.verified_spans.append(span)
        result.reattributed_spans.append(
            Reattribution(
                text=span.text,
                language=span.language,
                position=span.position,
                locus=locus,
                to_ref=to_ref,
                from_ref=from_ref,
                from_id=from_id,
                citation_added=added,
            )
        )
        logger.info(
            "text-gate: re-attributed ancient-text span (%s) from %s to %s (%s): %s",
            span.language,
            from_ref or "no adjacent marker",
            to_ref,
            locus.label,
            span.text[:100],
        )

    result.unverified_spans = sorted(remaining, key=lambda s: s.position)
    outcome.text = "\n".join(lines)
    outcome.reattributed = list(result.reattributed_spans)
    return outcome
