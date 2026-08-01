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
    MODERN_STOPWORDS,
    contains_word_bounded,
    fold_ancient_text,
)

logger = logging.getLogger(__name__)

# Deletion is ON by default; ``=false`` opts back into report-only.
ENFORCE_ENV_VAR = "ELEUTHERIA_TEXT_VERIFIER_ENFORCE"
_REMOVED_LINE_MARKER = "*[removed: unverified ancient text]*"

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
                }
                for span in self.unverified_spans
            ],
            "verified_spans": [
                {
                    "text": span.text[:120],
                    "language": span.language,
                    "status": span.status,
                    **({"source_id": span.source_id} if span.source_id else {}),
                }
                for span in self.verified_spans
            ],
            "unverified_spans": [
                {"text": span.text[:120], "language": span.language}
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
    alone misclassified them as Latin).

    Residual limitation: a short quoted English phrase whose content words
    all fall outside the ~70-word lexicon (e.g. rare or technical English
    vocabulary) still passes as candidate Latin and shows up as report-only
    noise. The lexicon is deliberately tiny and homograph-audited rather
    than exhaustive — growing it risks rejecting genuine Latin.
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
    folded_sources = [
        folded
        for folded in (fold_ancient_text(text) for text in evidence_texts if text)
        if folded
    ]

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

        check = SpanCheck(
            text=span_text,
            language=language,
            position=position,
            status="unverified",
        )

        if any(
            all(contains_word_bounded(source, segment) for segment in segments)
            for source in folded_sources
        ):
            check.status = "bundle"
            result.bundle_whitelisted += 1
            result.verified_spans.append(check)
            continue

        result.db_checked += 1
        found = (
            await _search_passage_for_text(span_text, segments, db, schema)
            if db is not None
            else None
        )
        if found:
            check.status = str(found["source"])
            check.source_id = found.get("passage_id")
            check.source_title = found.get("title")
            result.verified_spans.append(check)
        else:
            result.unverified_spans.append(check)

    if result.unverified_spans:
        logger.warning(
            "Text verifier: %d unverified ancient-text span(s)",
            len(result.unverified_spans),
        )
        for span in result.unverified_spans:
            logger.warning("  UNVERIFIED (%s): %s", span.language, span.text[:100])

    return result


def enforce_answer(answer: str, result: VerificationResult) -> str:
    """Drop whole lines containing unverified spans (enforce mode only).

    The whole line goes, not just the span: stripping the quote marks or the
    span while keeping surrounding text would launder an unverifiable
    quotation into plain prose. Callers must gate this behind
    :func:`enforcement_enabled` — the default deployment is report-only.
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

    return "\n".join(
        _REMOVED_LINE_MARKER if index in drop else line
        for index, line in enumerate(lines)
    )


def _folded_segments(span_text: str) -> list[str]:
    """Fold each ellipsis-separated segment; drop sub-2-char leftovers."""
    segments: list[str] = []
    for part in _ELLIPSIS_RE.split(span_text):
        folded = fold_ancient_text(part)
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
) -> Any | None:
    """First candidate row whose text contains every folded segment."""
    for row in rows or []:
        text = row.get("text_content") or ""
        folded = fold_ancient_text(str(text))
        if all(contains_word_bounded(folded, segment) for segment in segments):
            return row
    return None


async def _search_passage_for_text(
    span_text: str,
    segments: list[str],
    db: Any,
    schema: str,
) -> dict[str, Any] | None:
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
    """
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
            hit = _fold_match(rows, segments)
            if hit is not None:
                return {
                    "passage_id": hit.get("passage_id"),
                    "title": hit.get("title"),
                    "canonical_ref": hit.get("canonical_ref"),
                    "source": "db_passage",
                }

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
            hit = _fold_match(rows, segments)
            if hit is not None:
                return {
                    "passage_id": hit.get("passage_id"),
                    "title": hit.get("title"),
                    "canonical_ref": None,
                    "source": "db_node",
                }

    return None


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
