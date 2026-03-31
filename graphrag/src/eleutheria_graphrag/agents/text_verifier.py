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
    misattributed_extracts: list[MisattributedExtract] = field(default_factory=list)
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


@dataclass
class MisattributedExtract:
    """A Greek/Latin extract found in the DB but attributed to the wrong work."""

    text: str
    claimed_work: str  # What the LLM said
    actual_work: str   # What the DB says
    actual_ref: str | None
    position: int
    action: str = "corrected"


# Pattern to detect work attribution near a Greek passage
# Matches: "Phaedo 43a", "De Principiis III.1", "Republic X.617e", etc.
_WORK_ATTR_RE = re.compile(
    r"(?:(?:in|from|of|in his|Plato'?s?|Origen'?s?)\s+)?"
    r"([A-Z][a-zA-Z\s]+?)"  # Work title
    r"(?:\s+(?:[IVXLC]+\.?|\d+)[.\s]*(?:\d+[a-z]?)?)?",  # Optional ref number
    re.UNICODE,
)


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
            actual_title = found.get("title", "")
            actual_ref = found.get("canonical_ref")

            # Check attribution: look for work titles near the Greek text
            # (in the 200 chars before the Greek passage)
            context_before = answer[max(0, position - 200):position]
            claimed_work = _extract_claimed_work(context_before)

            if claimed_work and actual_title and not _titles_match(claimed_work, actual_title):
                result.misattributed_extracts.append(MisattributedExtract(
                    text=greek_text[:100],
                    claimed_work=claimed_work,
                    actual_work=actual_title,
                    actual_ref=actual_ref,
                    position=position,
                ))
                result.all_verified = False
                logger.warning(
                    "MISATTRIBUTED: LLM claims '%s' but DB says '%s' for: %s",
                    claimed_work, actual_title, greek_text[:60],
                )
            else:
                result.verified_extracts.append(VerifiedExtract(
                    text=greek_text,
                    passage_id=found["passage_id"],
                    work_title=actual_title,
                    canonical_ref=actual_ref,
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

    if result.misattributed_extracts:
        logger.warning(
            "Found %d misattributed Greek/Latin extracts",
            len(result.misattributed_extracts),
        )

    return result


def sanitize_answer(answer: str, verification: VerificationResult) -> str:
    """Remove or flag unverified/misattributed Greek/Latin text.

    Unverified extracts:
    - > 8 words: remove and replace with [text removed: unverified]
    - 5-8 words: add [unverified] marker

    Misattributed extracts:
    - Add correction note: [correction: this passage is from X, not Y]
    """
    if verification.all_verified:
        return answer

    sanitized = answer

    # Collect all actions with positions
    actions: list[tuple[int, str, str]] = []  # (position, type, replacement)

    for extract in verification.unverified_extracts:
        if extract.word_count > 8:
            actions.append((
                extract.position,
                "replace",
                "[text removed: unverified ancient text]",
            ))
            extract.action = "removed"
        elif extract.word_count > _MAX_TERM_WORDS:
            end_pos = extract.position + len(extract.text)
            actions.append((
                end_pos,
                "insert",
                " [unverified]",
            ))
            extract.action = "flagged"

    for extract in verification.misattributed_extracts:
        end_pos = extract.position + len(extract.text)
        correction = f" [correction: this passage is from {extract.actual_work}"
        if extract.actual_ref:
            correction += f" {extract.actual_ref}"
        correction += f", not {extract.claimed_work}]"
        actions.append((
            end_pos,
            "insert",
            correction,
        ))
        extract.action = "corrected"

    # Apply from end to start to preserve positions
    for pos, action_type, text in sorted(actions, key=lambda a: a[0], reverse=True):
        if action_type == "replace":
            # Find the original text at this position
            for uv in verification.unverified_extracts:
                if uv.position == pos:
                    sanitized = (
                        sanitized[:pos]
                        + text
                        + sanitized[pos + len(uv.text):]
                    )
                    break
        elif action_type == "insert":
            sanitized = sanitized[:pos] + text + sanitized[pos:]

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


# Common ancient work titles for attribution detection
_WORK_TITLES = {
    "phaedo", "phaedrus", "republic", "laws", "timaeus", "crito",
    "symposium", "apology", "meno", "gorgias", "protagoras", "theaetetus",
    "de principiis", "contra celsum", "de oratione", "commentary on romans",
    "philocalia", "exhortation to martyrdom",
    "de fato", "academica", "de natura deorum", "de divinatione",
    "de rerum natura",
    "nicomachean ethics", "de anima", "metaphysics", "physics",
    "discourses", "enchiridion", "meditations",
    "letters to lucilius", "de providentia", "de ira",
    "consolation of philosophy",
    "stromata", "protrepticus",
    "de libero arbitrio", "confessions", "city of god",
    "against heresies", "adversus haereses",
}


def _extract_claimed_work(context: str) -> str | None:
    """Extract the work title the LLM claims a passage is from.

    Looks for patterns like "Phaedo 43a", "in his De Principiis", etc.
    """
    context_lower = context.lower()
    for title in _WORK_TITLES:
        if title in context_lower:
            # Find the original case version
            idx = context_lower.rfind(title)
            return context[idx:idx + len(title)]
    return None


def _titles_match(claimed: str, actual: str) -> bool:
    """Check if a claimed work title matches the actual title from the DB.

    Handles partial matches: "Phaedo" matches "Phaedo (Φαίδων)",
    "De Principiis" matches "De Principiis (Περὶ Ἀρχῶν) - Origen".
    """
    claimed_lower = claimed.lower().strip()
    actual_lower = actual.lower().strip()

    # Direct containment
    if claimed_lower in actual_lower or actual_lower in claimed_lower:
        return True

    # First word match (e.g., "Crito" matches "Crito (Κρίτων)")
    claimed_first = claimed_lower.split()[0] if claimed_lower else ""
    actual_first = actual_lower.split()[0] if actual_lower else ""
    if claimed_first and actual_first and (
        claimed_first == actual_first
        or claimed_first in actual_lower
    ):
        return True

    return False
