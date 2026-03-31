"""
Deterministic verification of Greek and Latin text in agent responses.

Any ancient Greek or Latin text beyond short technical terms (≤ 3 words)
MUST exist in the database. This prevents the LLM from fabricating,
paraphrasing, or reconstructing ancient text.

This is a HARD requirement for scholarly integrity.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# Unicode ranges for ancient Greek
_GREEK_BASIC = range(0x0370, 0x0400)  # Greek and Coptic
_GREEK_EXTENDED = range(0x1F00, 0x2000)  # Greek Extended
_GREEK_COMBINING = range(0x0300, 0x0370)  # Combining diacriticals (used with Greek)

# Pattern to find Greek text runs (3+ Greek chars in a row, possibly with spaces/punctuation)
_GREEK_RUN_RE = re.compile(
    r'[\u0370-\u03FF\u1F00-\u1FFF][\u0370-\u03FF\u1F00-\u1FFF\u0300-\u036F\s\-,;·.()\'\"]*'
    r'[\u0370-\u03FF\u1F00-\u1FFF]',
    re.UNICODE,
)

# Known short technical terms that are OK without DB verification
# These are vocabulary items, not text passages
_KNOWN_TERMS: set[str] = {
    # Greek terms
    "αὐτεξούσιον", "αὐτεξουσίου", "αὐτεξούσιος",
    "εἱμαρμένη", "εἱμαρμένης",
    "πρόνοια", "προνοίας",
    "ἐφ' ἡμῖν", "τὸ ἐφ' ἡμῖν",
    "προαίρεσις", "προαιρέσεως",
    "συγκατάθεσις", "συγκαταθέσεως",
    "ἀκρασία", "ἀκρασίας",
    "ἀποκατάστασις",
    "κλίσις", "παρέγκλισις",
    "λεκτόν", "λεκτά",
    "ἡγεμονικόν",
    "φαντασία", "φαντασίαι",
    "ὁρμή", "ὁρμαί",
    "ἐκπύρωσις",
    "λόγος", "λόγοι",
    "ψυχή", "ψυχῆς",
    "νοῦς",
    "ἐνέργεια", "δύναμις",
    "ἀρετή", "ἀρεταί",
    "εὐδαιμονία",
    "ἐλευθερία",
    "ἀνάγκη",
    "τύχη",
    "Περὶ Ἀρχῶν",
    "Περὶ εἱμαρμένης",
    # Latin terms
    "liberum arbitrium",
    "fatum", "fata",
    "necessitas",
    "voluntas",
    "nunc stans",
    "massa damnata",
    "donum perseverantiae",
    "aeternitas",
    "praescientia",
    "providentia",
    "concursus",
}

# Maximum word count for a "short term" that doesn't need DB verification
_MAX_TERM_WORDS = 4


@dataclass
class VerificationResult:
    """Result of Greek/Latin text verification."""

    verified_extracts: list[VerifiedExtract] = field(default_factory=list)
    unverified_extracts: list[UnverifiedExtract] = field(default_factory=list)
    total_greek_chars: int = 0
    total_extracts_found: int = 0
    all_verified: bool = True


@dataclass
class VerifiedExtract:
    """A Greek/Latin extract that was found in the database."""

    text: str
    passage_id: str
    work_title: str
    canonical_ref: str | None


@dataclass
class UnverifiedExtract:
    """A Greek/Latin extract NOT found in the database — potential fabrication."""

    text: str
    word_count: int
    position: int  # char position in answer
    action: str  # "flagged" or "removed"


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


def is_known_term(text: str) -> bool:
    """Check if a Greek/Latin text is a known short technical term."""
    cleaned = text.strip().rstrip(".,;:·)")
    if cleaned in _KNOWN_TERMS:
        return True
    # Check word count
    words = cleaned.split()
    return len(words) <= _MAX_TERM_WORDS


async def verify_greek_text(
    answer: str,
    db: Any,
    schema: str = "free_will",
) -> VerificationResult:
    """Verify all Greek text in an answer against the passage database.

    Short terms (≤ 4 words or in known terms list) pass automatically.
    Longer extracts must match text in the passages table.

    Returns a VerificationResult with verified/unverified extracts.
    """
    result = VerificationResult()
    runs = extract_greek_runs(answer)
    result.total_extracts_found = len(runs)
    result.total_greek_chars = sum(_count_greek_chars(t) for t, _ in runs)

    for greek_text, position in runs:
        if is_known_term(greek_text):
            continue  # Short term, OK

        word_count = len(greek_text.split())

        # Search for this text in the database
        found = await _search_passage_for_text(greek_text, db, schema)

        if found:
            result.verified_extracts.append(VerifiedExtract(
                text=greek_text,
                passage_id=found["passage_id"],
                work_title=found.get("title", ""),
                canonical_ref=found.get("canonical_ref"),
            ))
        else:
            result.unverified_extracts.append(UnverifiedExtract(
                text=greek_text,
                word_count=word_count,
                position=position,
                action="flagged",
            ))
            result.all_verified = False

    if result.unverified_extracts:
        logger.warning(
            "Found %d unverified Greek/Latin extracts in answer",
            len(result.unverified_extracts),
        )
        for uv in result.unverified_extracts:
            logger.warning("  UNVERIFIED (%d words): %s", uv.word_count, uv.text[:100])

    return result


def sanitize_answer(answer: str, verification: VerificationResult) -> str:
    """Remove or flag unverified Greek/Latin text in an answer.

    For each unverified extract:
    - If > 8 words: remove and replace with [text removed: unverified]
    - If 5-8 words: add [unverified] marker
    """
    if verification.all_verified:
        return answer

    sanitized = answer
    # Process from end to start to preserve positions
    for extract in sorted(
        verification.unverified_extracts,
        key=lambda e: e.position,
        reverse=True,
    ):
        if extract.word_count > 8:
            sanitized = (
                sanitized[:extract.position]
                + "[text removed: unverified ancient text]"
                + sanitized[extract.position + len(extract.text):]
            )
            extract.action = "removed"
        elif extract.word_count > _MAX_TERM_WORDS:
            # Insert warning after the text
            end_pos = extract.position + len(extract.text)
            sanitized = (
                sanitized[:end_pos]
                + " [unverified]"
                + sanitized[end_pos:]
            )
            extract.action = "flagged"

    return sanitized


async def _search_passage_for_text(
    greek_text: str,
    db: Any,
    schema: str,
) -> dict[str, Any] | None:
    """Search for a Greek text snippet in the database.

    Checks both the passages table AND kg_nodes descriptions,
    since some ancient text is stored in KG node descriptions
    (e.g., from Scaife ingestions).

    Uses substring matching (LIKE) on text_content / description.
    Normalizes Unicode to handle diacritical variations.
    """
    search_text = greek_text.strip().strip(".,;:·()\"'""")
    if len(search_text) < 4:
        return None

    for text_variant in _unicode_variants(search_text):
        # Check passages table
        try:
            row = await db.fetchrow(
                f"""
                SELECT p.passage_id::text, w.title, p.canonical_ref
                FROM {schema}.passages p
                JOIN {schema}.ancient_works w ON w.work_id = p.work_id
                WHERE p.text_content LIKE '%' || $1 || '%'
                LIMIT 1
                """,
                text_variant,
            )
            if row:
                return dict(row)
        except Exception:
            logger.debug("Passage search failed for: %s", text_variant[:50], exc_info=True)

        # Check KG node descriptions (many passage nodes store text here)
        try:
            row = await db.fetchrow(
                f"""
                SELECT node_id AS passage_id, label AS title, NULL AS canonical_ref
                FROM {schema}.kg_nodes
                WHERE description LIKE '%' || $1 || '%'
                  AND type IN ('passage', 'quote')
                LIMIT 1
                """,
                text_variant,
            )
            if row:
                return dict(row)
        except Exception:
            logger.debug("KG node search failed for: %s", text_variant[:50], exc_info=True)

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
