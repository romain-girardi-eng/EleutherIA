"""Single publication verdict for GraphRAG answers: block or withhold.

The citation auditor, the streaming boundary, and both answer caches must make
the same decision.  Keeping that decision here prevents a rejected draft from
being withheld by one path but replayed by another.

Two classes of failure are handled differently:

* **Safety-class failures block the whole answer** — the content gate did not
  pass, the citation audit never ran or crashed (verifier exception, provider
  outage, zero auditable citations), unattested ancient text reached the prose
  unenforced, or the per-citation verdict record needed for withholding is
  missing.  Nothing is published.
* **Per-citation verdicts withhold sentences.**  A ``WEAK`` / ``REJECTED`` /
  ``MISSING`` / verifier-error verdict removes the sentences carrying that
  citation from the published prose (replaced by a bracketed marker), drops the
  citation from the public list and downgrades its ledger items to
  ``INSUFFICIENT`` with the reason.  Everything ``VERIFIED`` is published.

After the surgery the answer must still rest on verified evidence: a citation
whose every use was removed leaves the public list too, and an answer left
without a single cited claim is blocked.  A degraded synthesis (structural
hedge) is not a safety failure: it is published, flagged in ``warnings`` and
kept out of the answer caches.  A partial verdict is likewise published but
never cached (:func:`is_cacheable`): only a ``passed`` answer is replayed.

The published prose also never carries the dialectical ``[edge: …]``
markers: they are the synthesis's INTERNAL cite-as-you-write scheme (read by
the provenance ledger, the content gate and the referee off the draft), not a
reader-facing citation.  Every public boundary strips them here
(:func:`strip_edge_markers`), records how many under
``metadata.answer_metadata.residual_markers_stripped`` and keeps the links they
named under ``metadata.answer_metadata.dialectical_edges``.

This module deliberately distinguishes *internal draft* from *publishable
answer*.  Callers may keep an internal draft for diagnostics
(``withhold_prose=False``), but withholding is applied before the draft
crosses the public ``GraphRAGService``/SSE boundary.  A result that already
carries an applied verdict is re-checked against the recorded verdict: prose
rewritten after the gate (deep-mode polishing, counter-evidence resynthesis)
is withheld again from the recorded per-citation verdicts, never trusted.
"""

from __future__ import annotations

import hashlib
import logging
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from eleutheria_graphrag.agents.edge_markers import EdgeMarkerScrub, strip_edge_markers
from eleutheria_graphrag.agents.state import (
    Citation,
    ClaimLedgerItem,
    ClaimStatus,
    ScholarlyAnswer,
)

logger = logging.getLogger(__name__)

POLICY = "content_gate_and_sentence_withholding_v2"

#: Placeholder left where a sentence was withheld — same convention as the
#: ``*[removed: unverified ancient text]*`` marker of the text verifier.
WITHHELD_SENTENCE_MARKER = "*[withheld: citation not verified]*"

BADGE_HIGH = "High"
BADGE_PARTIAL = "Partial"
BADGE_BLOCKED = "Blocked"

#: Reason keys used for withheld citations (``withholding.reasons`` counts).
REASON_WEAK = "weak"
REASON_REJECTED = "rejected"
REASON_MISSING = "missing"
REASON_VERIFIER_ERROR = "verifier_error"
REASON_UNAUDITED = "unaudited"
#: A verified citation whose every prose/ledger use was withheld alongside a
#: failing one: it leaves the public list because nothing cites it any more.
REASON_ORPHANED = "orphaned"
#: Ledger-only reason: the claim's sentence was withheld because of a
#: co-cited failing citation, although the claim's own evidence is verified.
REASON_SENTENCE_WITHHELD = "sentence_withheld"

WARNING_SYNTHESIS_DEGRADED = "scholar_synthesis_degraded"

_STATUS_REASONS = {
    "WEAK": REASON_WEAK,
    "REJECTED": REASON_REJECTED,
    "MISSING": REASON_MISSING,
}

_BRACKET_RE = re.compile(r"\[([^\]]*)\]")
# The render prompt cites passages as ``[P1]`` and KG nodes as ``[N3]``,
# possibly combined (``[P3, N1]``) and possibly as ranges (``[P1-P3]``); the
# legacy renderer also emits bare numbers (``[2]``).
_REF_ITEM = r"[PN]?\d+(?:\s*[-–]\s*[PN]?\d+)?"
_PURE_REF_LIST_RE = re.compile(rf"^\s*{_REF_ITEM}(?:\s*[,;]\s*{_REF_ITEM})*\s*$")
_REF_ITEM_RE = re.compile(r"([PN]?)(\d+)(?:\s*[-–]\s*([PN]?)(\d+))?")
#: Longest range a marker may expand to (``[P1-P3]`` is three tokens; a
#: runaway ``[P1-P9999]`` is not a citation list).
_MAX_RANGE_SPAN = 100
_MARKER_BODY_RE = re.compile(r"^(?:P|edge|passage)_?(?P<body>.+)$", re.DOTALL)
# Candidate sentence boundary inside one line: terminal punctuation, then
# whitespace.  The separator is captured so it survives re-assembly; the
# character after it decides (``_opens_sentence``) whether the candidate is a
# real boundary.
_SENTENCE_SEP_RE = re.compile(r"((?:(?<=[.!?;·])|(?<=[.!?;·][)»”\"']))\s+)(?=\S)")
_SENTENCE_OPENERS = frozenset("«“\"'([*_")
# A run of bracket blocks at the start of a sentence part, e.g. ``[P1] `` in
# ``Chrysippus held X. [P1] Cleanthes held Y.``: the marker belongs to the
# sentence it follows, not to the one it precedes.
_LEADING_BRACKETS_RE = re.compile(r"^((?:\[[^\]]+\]\s*)+)")
_BRACKET_BLOCK_RE = re.compile(r"\[([^\]]+)\](\s*)")
#: Abbreviations conventionally followed by a numeral (``p. 330``,
#: ``vol. 2``, ``fr. 12``): the period ends the abbreviation, not a sentence.
_ABBREVIATIONS_BEFORE_NUMBER = frozenset(
    {
        "p", "pp", "n", "nn", "c", "ca", "ch", "chs", "col", "cols", "fr", "frr",
        "l", "ll", "vol", "vols", "no", "nos", "fol", "fols", "s", "ss", "sq",
        "sqq", "v", "vv", "lib", "ep", "epp", "fig", "figs", "art", "sect", "pt",
        "bk", "§",
    }
)  # fmt: skip
_WORD_BEFORE_PERIOD_RE = re.compile(r"(\S+)\.[)»”\"']?$")
_LINE_PREFIX_RE = re.compile(r"^(\s*(?:[-*+]|\d+[.)])\s+|\s*#+\s+)")
_WS_RE = re.compile(r"\s+")


@dataclass(frozen=True, slots=True)
class PublicationDecision:
    """Deterministic answer-publication decision.

    ``reasons`` are the safety-class (blocking) reasons.  ``warnings`` are
    non-blocking findings (a degraded synthesis).  ``withheld`` maps citation
    ids to the withholding reason derived from the recorded per-citation
    verdicts.  ``verdict_record`` is True when the audit recorded the ids it
    verified, so citations without a verdict can be told apart from verified
    ones at apply time.
    """

    publishable: bool
    reasons: tuple[str, ...]
    withheld: dict[str, str] = field(default_factory=dict)
    verdict_record: bool = False
    audit_warning: str | None = None
    warnings: tuple[str, ...] = ()

    @property
    def status(self) -> str:
        if not self.publishable:
            return "blocked"
        return "partial" if self.withheld else "passed"

    def as_metadata(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "publishable": self.publishable,
            "reasons": list(self.reasons),
            "warnings": list(self.warnings),
            "policy": POLICY,
        }


@dataclass(frozen=True, slots=True)
class WithholdingOutcome:
    """Result of removing withheld sentences from a prose text."""

    text: str
    withheld_sentences: int
    published_sentences: int
    #: Normalised text of every withheld sentence (blockquote lines included),
    #: used to downgrade the ledger claims those sentences carried.
    withheld_texts: tuple[str, ...] = ()


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _integer(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except TypeError, ValueError:
        return default


def _str_list(value: Any) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, str | bytes):
        return []
    return [str(item) for item in value if item is not None]


def _reason_for_verdict(entry: Mapping[str, Any]) -> str:
    if bool(entry.get("parse_error")):
        return REASON_VERIFIER_ERROR
    status = str(entry.get("status") or "").upper()
    return _STATUS_REASONS.get(status, REASON_REJECTED)


def evaluate_publication(
    metadata: Mapping[str, Any] | None,
) -> PublicationDecision:
    """Evaluate the final content gate and the citation audit.

    Blocking (safety-class) invariants:

    * the post-revision content gate ran and passed (or was explicitly marked
      not applicable for the legacy non-dialectical renderer);
    * the citation verifier ran to completion — a verifier exception, an
      unavailable verifier, or an audit aborted before any verdict blocks;
    * there was at least one auditable citation;
    * a partial audit is only tolerated when the audit recorded which
      citations it verified, so the rest can be withheld sentence by sentence;
    * per-citation failures are only tolerated when the audit recorded them
      by id (``failed_citations``) and, without a verified-id record, recorded
      as many ids as the aggregate counts announce;
    * unverified ancient text never reaches the prose unenforced.

    Every ``WEAK`` / ``REJECTED`` / ``MISSING`` / verifier-error verdict is
    returned in ``withheld`` for sentence-level withholding instead of
    blocking the answer.  A degraded synthesis is a ``warnings`` entry, not a
    block: the answer is published and kept out of the caches.
    """

    data = _mapping(metadata)
    reasons: list[str] = []
    warnings: list[str] = []

    synthesis = _mapping(data.get("scholar_synthesis"))
    if synthesis and (
        synthesis.get("degraded") or str(synthesis.get("status") or "") != "ok"
    ):
        warnings.append(WARNING_SYNTHESIS_DEGRADED)

    content = _mapping(data.get("content_gate"))
    content_status = str(content.get("status") or "")
    if content_status not in {"passed", "not_applicable"}:
        reasons.append("content_gate_not_passed")

    audit = _mapping(data.get("citation_verifier_v2"))
    audit_status = str(audit.get("status") or "")
    if audit_status not in {"passed", "failed"}:
        # The audit never completed: not configured, disabled, skipped, or
        # crashed.  There are no verdicts to withhold by.
        reasons.append("citation_audit_not_passed")
    if audit_status == "error" or bool(audit.get("infrastructure_failure")):
        reasons.append("citation_audit_infrastructure_failure")

    total_citations = _integer(audit.get("total_citations"), -1)
    audited = _integer(
        audit.get("audited_citations", audit.get("audited", -1)),
        -1,
    )
    report_total = _integer(audit.get("total"), -1)
    verified = _integer(audit.get("verified"), 0)
    weak = _integer(audit.get("weak"), 0)
    rejected = _integer(audit.get("rejected"), 0)
    missing = _integer(audit.get("missing"), 0)
    parse_errors = _integer(audit.get("parse_errors"), 0)
    aborted = bool(audit.get("aborted"))

    verdict_record = "verified_citations" in audit
    failed_entries = [
        entry
        for entry in (audit.get("failed_citations") or [])
        if isinstance(entry, Mapping) and entry.get("citation_id")
    ]

    audit_completed = audit_status in {"passed", "failed"}
    if total_citations <= 0:
        reasons.append("no_auditable_citations")
    elif (
        audit_completed
        and (audited != total_citations or report_total != total_citations)
        and not verdict_record
    ):
        # Without the verified-id record an unaudited citation cannot be told
        # apart from a verified one, so the partial audit cannot be applied.
        reasons.append("citation_audit_partial")

    if aborted and audited <= 0:
        # Aborted before a single verdict: nothing to withhold by.  An abort on
        # the rejection-rate threshold (audited > 0) is applied per sentence.
        reasons.append("citation_audit_aborted")

    failing_count = weak + rejected + missing + parse_errors
    non_verified = max(audited, 0) - verified if audited > 0 else 0
    expected_failures = max(failing_count, non_verified)
    failed_ids = {str(entry["citation_id"]) for entry in failed_entries}
    if expected_failures > 0 and (
        not failed_entries
        # Without a verified-id record every failure must be recorded by id:
        # an unrecorded one could not be withheld and would stay public.
        or (not verdict_record and len(failed_ids) < expected_failures)
    ):
        reasons.append("citation_verdicts_unrecorded")

    text_verification = _mapping(data.get("text_verification"))
    if (
        text_verification
        and _integer(text_verification.get("unverified"), 0) > 0
        and not bool(text_verification.get("enforced"))
    ):
        reasons.append("unverified_ancient_text_present")

    withheld: dict[str, str] = {}
    for entry in failed_entries:
        cid = str(entry["citation_id"])
        # A citation audited more than once keeps its harshest reason.
        reason = _reason_for_verdict(entry)
        current = withheld.get(cid)
        if current is None or _severity(reason) > _severity(current):
            withheld[cid] = reason

    warning = audit.get("warning")
    audit_warning = str(warning) if warning else None

    # Stable, de-duplicated order makes metadata and tests reproducible.
    unique_reasons = tuple(dict.fromkeys(reasons))
    return PublicationDecision(
        publishable=not unique_reasons,
        reasons=unique_reasons,
        withheld=withheld,
        verdict_record=verdict_record,
        audit_warning=audit_warning,
        warnings=tuple(dict.fromkeys(warnings)),
    )


def is_publishable(metadata: Mapping[str, Any] | None) -> bool:
    """Whether a result may cross a public boundary.

    An applied gate record is authoritative: it also carries verdicts that
    only exist after application (``all_sentences_withheld``).  Without one
    the metadata is evaluated afresh.
    """

    data = _mapping(metadata)
    gate = _mapping(data.get("publication_gate"))
    if gate.get("policy") == POLICY and gate.get("applied"):
        return bool(gate.get("publishable"))
    return evaluate_publication(data).publishable


def synthesis_is_authoritative(metadata: Mapping[str, Any] | None) -> bool:
    """Whether the prose is a real synthesis rather than a structural hedge.

    A degraded synthesis is published (with a warning) but never cached: the
    next asker deserves a fresh attempt at a real synthesis.
    """

    synthesis = _mapping(_mapping(metadata).get("scholar_synthesis"))
    if not synthesis:
        return True
    if synthesis.get("degraded"):
        return False
    return str(synthesis.get("status") or "") == "ok"


def publication_status(metadata: Mapping[str, Any] | None) -> str:
    """``passed`` / ``partial`` / ``blocked`` for a result at a boundary.

    An applied gate record is authoritative; otherwise the metadata is
    evaluated afresh, and an audit that left citations unverified (a partial
    audit under a verified-id record) counts as ``partial``.
    """

    data = _mapping(metadata)
    gate = _mapping(data.get("publication_gate"))
    if gate.get("policy") == POLICY and gate.get("applied"):
        status = str(gate.get("status") or "")
        return status if status in {"passed", "partial"} else "blocked"
    decision = evaluate_publication(data)
    if decision.status != "passed":
        return decision.status
    audit = _mapping(data.get("citation_verifier_v2"))
    audited = _integer(audit.get("audited_citations", audit.get("audited", -1)), -1)
    if decision.verdict_record and audited != _integer(audit.get("total_citations")):
        return "partial"
    return "passed"


def is_cacheable(metadata: Mapping[str, Any] | None) -> bool:
    """The answer-cache admission rule: fully verified *and* authoritative.

    Only a ``passed`` verdict is replayed.  A ``partial`` verdict is
    published but never cached: the withheld sentences may reflect a one-off
    verifier failure (provider flakiness, a transient ``WEAK``), and freezing
    that holed prose would serve it to every later asker; the next request
    recomputes instead.  A degraded synthesis is likewise never cached.
    """

    return publication_status(metadata) == "passed" and synthesis_is_authoritative(
        metadata
    )


def _severity(reason: str) -> int:
    order = (
        REASON_ORPHANED,
        REASON_UNAUDITED,
        REASON_VERIFIER_ERROR,
        REASON_WEAK,
        REASON_MISSING,
        REASON_REJECTED,
    )
    return order.index(reason) if reason in order else 0


# ---------------------------------------------------------------------------
# Sentence-level withholding
# ---------------------------------------------------------------------------


def _normalise(text: str) -> str:
    return _WS_RE.sub(" ", text).strip()


def _ref_tokens(block: str) -> list[str]:
    """Every reference token a pure reference list carries.

    ``[P3, N1]`` yields ``P3`` and ``N1``; ``[P1-P3]`` (hyphen or en dash)
    expands to ``P1``, ``P2``, ``P3``.  A range whose two ends carry different
    prefixes, or that runs backwards or beyond :data:`_MAX_RANGE_SPAN`, is
    kept as its two end tokens.
    """
    tokens: list[str] = []
    for prefix, start, end_prefix, end in _REF_ITEM_RE.findall(block):
        if not end:
            tokens.append(f"{prefix}{start}")
            continue
        prefix = prefix or end_prefix
        low, high = int(start), int(end)
        if (end_prefix and end_prefix != prefix) or not (
            low <= high <= low + _MAX_RANGE_SPAN
        ):
            tokens.append(f"{prefix}{start}")
            tokens.append(f"{end_prefix}{end}")
            continue
        tokens.extend(f"{prefix}{number}" for number in range(low, high + 1))
    return tokens


def _is_ref_marker(block: str) -> bool:
    """Whether a bracket body is a citation marker rather than prose."""
    stripped = block.strip()
    return bool(stripped) and (
        _PURE_REF_LIST_RE.match(block) is not None
        or _MARKER_BODY_RE.match(stripped) is not None
    )


def _sentence_cites(
    sentence: str,
    *,
    refs: frozenset[str],
    ids: frozenset[str],
) -> bool:
    """Whether ``sentence`` carries an inline marker for a withheld citation.

    Handles the renderer's ``[P1]`` / ``[N3]`` / ``[1, P2]`` / ``[P3, N1]``
    reference lists and ``[P1-P3]`` ranges (matched against ``Citation.ref``)
    and the dialectical ``[passage_<id>: …]`` / ``[P_<id>: …]`` markers
    (matched against the citation id).
    """
    for match in _BRACKET_RE.finditer(sentence):
        block = match.group(1)
        stripped = block.strip()
        if not stripped:
            continue
        if stripped in ids or stripped in refs:
            return True
        if _PURE_REF_LIST_RE.match(block):
            for token in _ref_tokens(block):
                if token in refs or token in ids:
                    return True
            continue
        marker = _MARKER_BODY_RE.match(stripped)
        if marker is None:
            continue
        ref_id = marker.group("body").split(":", 1)[0].strip().lstrip("_")
        if ref_id and (ref_id in ids or ref_id in refs):
            return True
    return False


def _sentence_matches_claim(sentence: str, claims: Sequence[str]) -> bool:
    norm = _normalise(sentence)
    if not norm:
        return False
    for claim in claims:
        if norm == claim:
            return True
        if len(norm) >= 20 and norm in claim:
            return True
    return False


def _claim_was_withheld(claim: str, withheld_texts: Sequence[str]) -> bool:
    """Whether a ledger claim is (part of) a sentence that was withheld."""
    norm = _normalise(claim)
    if not norm:
        return False
    for text in withheld_texts:
        if norm == text:
            return True
        if len(norm) >= 20 and norm in text:
            return True
        if len(text) >= 20 and text in norm:
            return True
    return False


def _is_blockquote(line: str) -> bool:
    return line.lstrip().startswith(">")


def withhold_sentences(
    text: str,
    *,
    refs: Iterable[str] = (),
    ids: Iterable[str] = (),
    claims: Iterable[str] = (),
) -> WithholdingOutcome:
    """Remove every sentence citing a withheld citation from ``text``.

    A sentence is withheld when it carries an inline marker for one of
    ``refs``/``ids`` or when it is (part of) one of the withheld ledger
    ``claims``.  Withheld sentences are replaced by
    :data:`WITHHELD_SENTENCE_MARKER`; consecutive markers collapse into one.
    A blockquote block (contiguous ``>`` lines) stands or falls as a whole:
    an original and its translation are never separated.  List bullets and
    headings keep their prefix.  Text that is not withheld is preserved
    byte-for-byte.  Applying the function again to its own output with the
    same arguments changes nothing (the marker carries no citation).
    """

    ref_set = frozenset(r for r in refs if r)
    id_set = frozenset(i for i in ids if i)
    claim_set = tuple(dict.fromkeys(_normalise(c) for c in claims if _normalise(c)))
    if not ref_set and not id_set and not claim_set:
        return WithholdingOutcome(text, 0, _count_sentences(text))

    def hit(sentence: str) -> bool:
        return _sentence_cites(
            sentence, refs=ref_set, ids=id_set
        ) or _sentence_matches_claim(sentence, claim_set)

    lines = text.split("\n")
    out_lines: list[str] = []
    withheld = 0
    published = 0
    withheld_texts: list[str] = []

    index = 0
    while index < len(lines):
        line = lines[index]
        if _is_blockquote(line):
            block_end = index
            while block_end + 1 < len(lines) and _is_blockquote(lines[block_end + 1]):
                block_end += 1
            block = lines[index : block_end + 1]
            block_sentences = [
                sentence
                for block_line in block
                for sentence in _split_line(block_line.lstrip()[1:])[0::2]
                if sentence.strip()
            ]
            if any(hit(sentence) for sentence in block_sentences):
                out_lines.append(WITHHELD_SENTENCE_MARKER)
                withheld += 1
                withheld_texts.extend(_normalise(s) for s in block_sentences)
            else:
                out_lines.extend(block)
                published += len(block_sentences)
            index = block_end + 1
            continue

        prefix_match = _LINE_PREFIX_RE.match(line)
        prefix = prefix_match.group(1) if prefix_match else ""
        body = line[len(prefix) :]
        parts = _split_line(body)
        rebuilt: list[str] = []
        for position, part in enumerate(parts):
            if position % 2 == 1:
                rebuilt.append(part)
                continue
            if not part.strip():
                rebuilt.append(part)
                continue
            if hit(part):
                rebuilt.append(WITHHELD_SENTENCE_MARKER)
                withheld += 1
                withheld_texts.append(_normalise(part))
            else:
                rebuilt.append(part)
                published += 1
        out_lines.append(prefix + _collapse_markers(rebuilt))
        index += 1

    return WithholdingOutcome(
        "\n".join(out_lines), withheld, published, tuple(withheld_texts)
    )


def _opens_sentence(char: str) -> bool:
    """Whether ``char`` may begin a sentence after a candidate boundary.

    Unicode-aware: polytonic Greek capitals (``Ἐ``), accented Latin capitals
    (``É``) and digits (``3 arguments``, ``2026``) open a sentence, not only
    ASCII/basic-Greek capitals.
    """
    return (
        char.isupper() or char.istitle() or char.isdigit() or char in _SENTENCE_OPENERS
    )


def _is_boundary(body: str, match: re.Match[str]) -> bool:
    """Whether a candidate separator really ends a sentence."""
    opener = body[match.end()]
    if not _opens_sentence(opener):
        return False
    if _inside_brackets(body, match.start()):
        # ``[P_frede: Frede, 2011 p. 44]`` / ``(Bobzien 1998, p. 330)``: a
        # marker or a parenthesis is never cut in two.
        return False
    if opener.isdigit():
        word = _WORD_BEFORE_PERIOD_RE.search(body[: match.start()])
        if word and word.group(1).lower() in _ABBREVIATIONS_BEFORE_NUMBER:
            return False
    return True


def _inside_brackets(body: str, position: int) -> bool:
    depth = 0
    for char in body[:position]:
        if char in "[(":
            depth += 1
        elif char in "])" and depth > 0:
            depth -= 1
    return depth > 0


def _split_line(body: str) -> list[str]:
    """Split one line into ``[sentence, sep, sentence, sep, ...]``.

    Re-joining the parts gives ``body`` back byte-for-byte.  A bracket marker
    block that opens a part (``. [P1] Cleanthes …``) is moved onto the
    preceding sentence, since it cites that sentence.
    """
    parts: list[str] = []
    position = 0
    for match in _SENTENCE_SEP_RE.finditer(body):
        if not _is_boundary(body, match):
            continue
        parts.append(body[position : match.start()])
        parts.append(match.group(1))
        position = match.end()
    parts.append(body[position:])
    return _attach_leading_markers(parts)


def _attach_leading_markers(parts: list[str]) -> list[str]:
    """Move citation markers opening a part onto the preceding sentence."""
    if len(parts) < 3:
        return parts
    result = [parts[0]]
    for index in range(1, len(parts), 2):
        sep, part = parts[index], parts[index + 1]
        leading = _LEADING_BRACKETS_RE.match(part)
        if leading is None or not result[-1].strip():
            result.extend((sep, part))
            continue
        blocks = _BRACKET_BLOCK_RE.findall(leading.group(1))
        if not all(_is_ref_marker(block) for block, _ws in blocks):
            result.extend((sep, part))
            continue
        markers = leading.group(1)
        rest = part[len(markers) :]
        if not rest:
            # The part was nothing but markers: it ends the previous sentence.
            result[-1] = result[-1] + sep + markers
            continue
        trailing_ws = markers[len(markers.rstrip()) :]
        result[-1] = result[-1] + sep + markers.rstrip()
        result.extend((trailing_ws, rest))
    return result


def _collapse_markers(parts: list[str]) -> str:
    """Re-assemble parts, collapsing runs of markers into a single marker."""
    result: list[str] = []
    pending_sep = ""
    last_was_marker = False
    for position, part in enumerate(parts):
        if position % 2 == 1:
            pending_sep = part
            continue
        if part == WITHHELD_SENTENCE_MARKER and last_was_marker:
            continue
        if result:
            result.append(pending_sep)
        result.append(part)
        pending_sep = ""
        last_was_marker = part == WITHHELD_SENTENCE_MARKER
    return "".join(result)


def _count_sentences(text: str) -> int:
    count = 0
    for line in text.split("\n"):
        if _is_blockquote(line):
            line = line.lstrip()[1:]
        else:
            prefix_match = _LINE_PREFIX_RE.match(line)
            if prefix_match:
                line = line[len(prefix_match.group(1)) :]
        count += sum(1 for part in _split_line(line)[0::2] if part.strip())
    return count


# ---------------------------------------------------------------------------
# Applying the verdict (one core for the model and the mapping forms)
# ---------------------------------------------------------------------------


def _ledger_cites(evidence_ids: Sequence[str], keys: Iterable[str]) -> bool:
    """Whether a ledger item cites one of ``keys`` (citation id or ref)."""
    for key in keys:
        if not key:
            continue
        suffix = f"::{key}"
        if any(eid == key or eid.endswith(suffix) for eid in evidence_ids):
            return True
    return False


def _ledger_reason(evidence_ids: Sequence[str], withheld: Mapping[str, str]) -> str:
    best: str | None = None
    for cid, reason in withheld.items():
        if _ledger_cites(evidence_ids, (cid,)) and (
            best is None or _severity(reason) > _severity(best)
        ):
            best = reason
    return best or ""


def _is_supported(item: Mapping[str, Any]) -> bool:
    status = item.get("status")
    return str(getattr(status, "value", status) or "").lower() == "supported"


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _initial_withheld(
    decision: PublicationDecision,
    citations: Sequence[Mapping[str, Any]],
    audit: Mapping[str, Any],
) -> dict[str, str]:
    """The decision's withheld set, extended with unaudited citations."""
    withheld = dict(decision.withheld)
    if decision.verdict_record:
        verified_ids = set(_str_list(audit.get("verified_citations")))
        for citation in citations:
            cid = str(citation.get("id") or "")
            if cid and cid not in verified_ids and cid not in withheld:
                withheld[cid] = REASON_UNAUDITED
    return withheld


@dataclass(slots=True)
class _Surgery:
    """Everything the withholding surgery decided for one prose text."""

    outcome: WithholdingOutcome
    withheld: dict[str, str]
    ledger_reasons: list[str]

    @property
    def emptied(self) -> str | None:
        """Blocking reason when nothing citable survived the surgery."""
        if not self.withheld:
            return None
        if self.outcome.published_sentences == 0:
            return "all_sentences_withheld"
        return None


def _refs_of(
    citations: Sequence[Mapping[str, Any]], withheld: Mapping[str, str]
) -> set[str]:
    refs: set[str] = set()
    for citation in citations:
        if str(citation.get("id") or "") in withheld:
            ref = str(citation.get("ref") or "")
            if ref:
                refs.add(ref)
    return refs


def _has_marker(text: str, citation: Mapping[str, Any]) -> bool:
    cid = str(citation.get("id") or "")
    ref = str(citation.get("ref") or "")
    return _sentence_cites(
        text, refs=frozenset({ref} if ref else ()), ids=frozenset({cid})
    )


def _ledger_backs(
    citation: Mapping[str, Any],
    ledger: Sequence[Mapping[str, Any]],
    ledger_reasons: Sequence[str],
) -> bool:
    keys = (str(citation.get("id") or ""), str(citation.get("ref") or ""))
    for item, reason in zip(ledger, ledger_reasons, strict=True):
        if reason or not _is_supported(item):
            continue
        if _ledger_cites(_str_list(item.get("evidence_ids")), keys):
            return True
    return False


def _surgery(
    text: str,
    citations: Sequence[Mapping[str, Any]],
    ledger: Sequence[Mapping[str, Any]],
    withheld: Mapping[str, str],
    extra_refs: Iterable[str] = (),
) -> _Surgery:
    """Withhold sentences, downgrade ledger items and drop orphaned citations.

    ``ledger_reasons`` is aligned with ``ledger``: the empty string for an
    item the gate leaves alone, otherwise the withholding reason.

    A verified citation is *orphaned* — withheld with reason ``orphaned`` —
    when the surgery removed its every use: an inline-cited citation whose
    markers all sat in withheld sentences (a mixed-citation sentence taken
    down by a failing co-citation), or a ledger-only citation whose every
    supported ledger claim was downgraded.  Ledger items citing an orphaned
    citation, and items whose claim sentence was withheld, are downgraded.
    """

    withheld = dict(withheld)
    # ``extra_refs``: refs of citations already dropped from the public list
    # by an earlier application (a re-check of rewritten prose).
    refs = _refs_of(citations, withheld) | {r for r in extra_refs if r}
    claims = [
        str(item.get("claim") or "")
        for item in ledger
        if _ledger_reason(_str_list(item.get("evidence_ids")), withheld)
    ]
    outcome = withhold_sentences(text, refs=refs, ids=withheld, claims=claims)

    inline_cited: set[str] = set()
    for citation in citations:
        cid = str(citation.get("id") or "")
        if not cid or cid in withheld or not _has_marker(text, citation):
            continue
        inline_cited.add(cid)
        if not _has_marker(outcome.text, citation):
            withheld[cid] = REASON_ORPHANED

    ledger_reasons: list[str] = []
    for item in ledger:
        reason = _ledger_reason(_str_list(item.get("evidence_ids")), withheld)
        if (
            not reason
            and _is_supported(item)
            and _claim_was_withheld(
                str(item.get("claim") or ""), outcome.withheld_texts
            )
        ):
            reason = REASON_SENTENCE_WITHHELD
        ledger_reasons.append(reason)

    untouched = [""] * len(ledger)
    for citation in citations:
        cid = str(citation.get("id") or "")
        if not cid or cid in withheld or cid in inline_cited:
            continue
        if _ledger_backs(citation, ledger, untouched) and not _ledger_backs(
            citation, ledger, ledger_reasons
        ):
            withheld[cid] = REASON_ORPHANED

    return _Surgery(outcome, withheld, ledger_reasons)


def _summarise(
    withheld: Mapping[str, str],
    citations: Sequence[Mapping[str, Any]],
    previous: Mapping[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Per-citation withholding entries and reason counts.

    ``previous`` is an earlier applied record: citations it withheld already
    left the public list, so their entries (and refs) are carried over.
    """
    withheld_citations: list[dict[str, Any]] = []
    seen: set[str] = set()
    for citation in citations:
        cid = str(citation.get("id") or "")
        if cid in withheld and cid not in seen:
            seen.add(cid)
            withheld_citations.append(
                {
                    "citation_id": cid,
                    "ref": str(citation.get("ref") or ""),
                    "reason": withheld[cid],
                }
            )
    for entry in _mapping(previous).get("withheld_citations") or []:
        if not isinstance(entry, Mapping):
            continue
        cid = str(entry.get("citation_id") or "")
        if cid in withheld and cid not in seen:
            seen.add(cid)
            withheld_citations.append(
                {
                    "citation_id": cid,
                    "ref": str(entry.get("ref") or ""),
                    "reason": withheld[cid],
                }
            )
    reasons: dict[str, int] = {}
    for reason in withheld.values():
        reasons[reason] = reasons.get(reason, 0) + 1
    return withheld_citations, dict(sorted(reasons.items()))


def _gate_metadata(
    decision: PublicationDecision,
    withheld: Mapping[str, str],
    citations: Sequence[Mapping[str, Any]],
    outcome: WithholdingOutcome | None,
    *,
    applied: bool,
    answer_digest: str | None = None,
    previous: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    withheld_citations, reasons = _summarise(withheld, citations, previous)
    status = decision.status
    if decision.publishable and withheld:
        status = "partial"
    record: dict[str, Any] = {
        **decision.as_metadata(),
        "status": status,
        "applied": applied,
        "withholding": {
            "withheld_sentences": outcome.withheld_sentences if outcome else 0,
            "published_sentences": outcome.published_sentences if outcome else 0,
            "withheld_citations": withheld_citations,
            "reasons": reasons,
            "audit_warning": decision.audit_warning,
        },
    }
    if answer_digest is not None:
        record["answer_digest"] = answer_digest
    return record


def _already_applied(metadata: Mapping[str, Any]) -> bool:
    gate = _mapping(metadata.get("publication_gate"))
    return bool(gate.get("applied")) and gate.get("policy") == POLICY


def _blocked(decision: PublicationDecision, reason: str) -> PublicationDecision:
    return PublicationDecision(
        publishable=False,
        reasons=(*decision.reasons, reason),
        withheld=decision.withheld,
        verdict_record=decision.verdict_record,
        audit_warning=decision.audit_warning,
        warnings=decision.warnings,
    )


def _badge(
    decision: PublicationDecision, withheld: Mapping[str, str], upstream: Any
) -> str:
    if withheld:
        return BADGE_PARTIAL
    if decision.warnings:
        # A degraded synthesis keeps the pipeline's own grade: nothing was
        # withheld, but the prose is a structural hedge, not a "High" answer.
        return str(upstream) if upstream else BADGE_HIGH
    return BADGE_HIGH


def _blocked_output(
    output: dict[str, Any],
    metadata: Mapping[str, Any],
    decision: PublicationDecision,
    withheld: Mapping[str, str],
    citations: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    output.update(
        {
            "answer": "",
            "citations": [],
            "claim_ledger": [],
            "passages_used": 0,
            "insufficient_evidence": True,
            "metadata": {
                **metadata,
                "quality_badge": BADGE_BLOCKED,
                "publication_gate": _gate_metadata(
                    decision,
                    withheld,
                    citations,
                    None,
                    applied=True,
                    previous=_previous_withholding(metadata),
                ),
            },
        }
    )
    if "polished_markdown" in output:
        output["polished_markdown"] = ""
    return output


def _previous_withholding(metadata: Mapping[str, Any]) -> dict[str, Any]:
    return _mapping(_mapping(metadata.get("publication_gate")).get("withholding"))


def _with_residual_markers(
    metadata: Mapping[str, Any], *scrubs: EdgeMarkerScrub
) -> dict[str, Any]:
    """Record the ``[edge: …]`` markers the boundary stripped from the prose.

    ``answer_metadata.residual_markers_stripped`` counts every marker removed
    across applications (a rewrite gated again adds its own); the links the
    markers named are kept, deduplicated, under
    ``answer_metadata.dialectical_edges`` so the dialectical information
    survives the prose being cleaned.  A replay that strips nothing leaves
    the record as it was.
    """
    answer_metadata = _mapping(metadata.get("answer_metadata"))
    count = sum(scrub.count for scrub in scrubs)
    if not count and "residual_markers_stripped" in answer_metadata:
        return dict(metadata)
    answer_metadata["residual_markers_stripped"] = (
        _integer(answer_metadata.get("residual_markers_stripped")) + count
    )
    edges: list[dict[str, str]] = [
        dict(edge)
        for edge in answer_metadata.get("dialectical_edges") or []
        if isinstance(edge, Mapping)
    ]
    seen = {(e.get("relation"), e.get("from_id"), e.get("to_id")) for e in edges}
    for scrub in scrubs:
        for edge in scrub.edges:
            if edge.key in seen:
                continue
            seen.add(edge.key)
            edges.append(
                {
                    "relation": edge.relation,
                    "from_id": edge.from_id,
                    "to_id": edge.to_id,
                }
            )
    if edges:
        answer_metadata["dialectical_edges"] = edges
    if count:
        logger.warning(
            "Publication gate stripped %d residual [edge: …] marker(s) from the "
            "public prose",
            count,
        )
    return {**metadata, "answer_metadata": answer_metadata}


def _rerelease(
    output: dict[str, Any],
    metadata: dict[str, Any],
    released: EdgeMarkerScrub,
    *polished: EdgeMarkerScrub,
) -> dict[str, Any]:
    """Return an already-gated result, its prose scrubbed once more.

    A record applied before the scrub existed (an old cache entry) still
    carries markers: they go now, and the recorded digest moves to the clean
    text so the next replay is a plain no-op.
    """
    output["answer"] = released.text
    metadata = _with_residual_markers(metadata, released, *polished)
    if released.count:
        gate = _mapping(metadata.get("publication_gate"))
        metadata["publication_gate"] = {
            **gate,
            "answer_digest": _digest(released.text),
        }
    output["metadata"] = metadata
    return output


def _publish_output(
    output: dict[str, Any],
    metadata: Mapping[str, Any],
    decision: PublicationDecision,
    surgery: _Surgery,
    citations: Sequence[Mapping[str, Any]],
    ledger: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    published_ledger: list[dict[str, Any]] = []
    for item, reason in zip(ledger, surgery.ledger_reasons, strict=True):
        if reason:
            item = {
                **item,
                "status": ClaimStatus.INSUFFICIENT.value,
                "status_reason": f"withheld: {reason}",
            }
        published_ledger.append(dict(item))
    # The withholding surgery matched sentences against the ledger's claim
    # texts, which carry the markers; the scrub therefore comes AFTER it and
    # BEFORE the digest, so a replay of the clean prose is a no-op.
    released = strip_edge_markers(surgery.outcome.text)
    scrubs = [released]
    if output.get("polished_markdown"):
        polished = withhold_sentences(
            str(output["polished_markdown"]),
            refs=_refs_of(citations, surgery.withheld)
            | _recorded_refs(_mapping(metadata.get("publication_gate"))),
            ids=surgery.withheld,
        )
        polished_scrub = strip_edge_markers(polished.text)
        output["polished_markdown"] = polished_scrub.text
        scrubs.append(polished_scrub)
    metadata = _with_residual_markers(metadata, *scrubs)
    output.update(
        {
            "answer": released.text,
            "citations": [
                dict(c)
                for c in citations
                if str(c.get("id") or "") not in surgery.withheld
            ],
            "claim_ledger": published_ledger,
            "metadata": {
                **metadata,
                "quality_badge": _badge(
                    decision, surgery.withheld, metadata.get("quality_badge")
                ),
                "publication_gate": _gate_metadata(
                    decision,
                    surgery.withheld,
                    citations,
                    surgery.outcome,
                    applied=True,
                    answer_digest=_digest(released.text),
                    previous=_previous_withholding(metadata),
                ),
            },
        }
    )
    return output


def _recorded_refs(gate: Mapping[str, Any]) -> set[str]:
    """Refs of the citations an applied record withheld (they left the list)."""
    withholding = _mapping(gate.get("withholding"))
    return {
        str(entry.get("ref"))
        for entry in withholding.get("withheld_citations") or []
        if isinstance(entry, Mapping) and entry.get("ref")
    }


def _recorded_decision(gate: Mapping[str, Any]) -> PublicationDecision:
    withholding = _mapping(gate.get("withholding"))
    return PublicationDecision(
        publishable=bool(gate.get("publishable")),
        reasons=tuple(_str_list(gate.get("reasons"))),
        withheld={
            str(entry.get("citation_id")): str(entry.get("reason") or REASON_REJECTED)
            for entry in withholding.get("withheld_citations") or []
            if isinstance(entry, Mapping) and entry.get("citation_id")
        },
        verdict_record=True,
        audit_warning=(
            str(withholding["audit_warning"])
            if withholding.get("audit_warning")
            else None
        ),
        warnings=tuple(_str_list(gate.get("warnings"))),
    )


def _reapply_recorded(
    output: dict[str, Any], metadata: dict[str, Any]
) -> dict[str, Any]:
    """Re-check a result that already carries an applied verdict.

    The recorded per-citation verdict is authoritative, the prose is not: a
    stage that rewrote the answer after the gate (polishing, resynthesis)
    gets its rewrite withheld from the same verdict.  Unchanged prose is
    returned untouched, so replay is idempotent.
    """

    gate = _mapping(metadata.get("publication_gate"))
    decision = _recorded_decision(gate)
    citations = [
        _mapping(c) for c in (output.get("citations") or []) if isinstance(c, Mapping)
    ]
    if not decision.publishable:
        return _blocked_output(output, metadata, decision, decision.withheld, citations)

    answer = str(output.get("answer") or "")
    polished = output.get("polished_markdown")
    released = strip_edge_markers(answer)
    # The digest was taken on the clean text; a record written before the
    # scrub existed digested the marked text.  Either way the prose is the
    # one the gate applied to.
    unchanged = gate.get("answer_digest") in {_digest(answer), _digest(released.text)}
    if unchanged and not polished:
        return _rerelease(output, metadata, released)

    ledger = [
        _mapping(c)
        for c in (output.get("claim_ledger") or [])
        if isinstance(c, Mapping)
    ]
    recorded_refs = _recorded_refs(gate)
    if unchanged:
        # Only the polished rewrite is new: withhold it from the recorded
        # verdict and leave the already-applied answer alone.
        refs = _refs_of(citations, decision.withheld) | recorded_refs
        polished_scrub = strip_edge_markers(
            withhold_sentences(str(polished), refs=refs, ids=decision.withheld).text
        )
        output["polished_markdown"] = polished_scrub.text
        return _rerelease(output, metadata, released, polished_scrub)

    surgery = _surgery(answer, citations, ledger, decision.withheld, recorded_refs)
    return _finish(output, metadata, decision, surgery, citations, ledger)


def _finish(
    output: dict[str, Any],
    metadata: Mapping[str, Any],
    decision: PublicationDecision,
    surgery: _Surgery,
    citations: Sequence[Mapping[str, Any]],
    ledger: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Publish the surgery's result, or block when nothing citable survived."""
    emptied = surgery.emptied
    if (
        emptied is None
        and surgery.withheld
        and not any(str(c.get("id") or "") not in surgery.withheld for c in citations)
    ):
        emptied = "no_cited_claims_survive"
    if emptied is not None:
        return _blocked_output(
            output, metadata, _blocked(decision, emptied), surgery.withheld, citations
        )
    return _publish_output(output, metadata, decision, surgery, citations, ledger)


def apply_publication_verdict(result: Mapping[str, Any]) -> dict[str, Any]:
    """Apply the publication verdict at a public boundary (mapping form).

    Used for ``GraphRAGService.query_dict`` results and the answer caches.  A
    blocked result loses prose, citations and ledger; otherwise sentences
    citing withheld citations are removed, those citations (and any citation
    orphaned by the removal) are dropped from the public list, their ledger
    items are downgraded to ``INSUFFICIENT`` with the reason, and the quality
    badge becomes ``High`` (nothing withheld) or ``Partial``.  An answer left
    without a single surviving cited claim is blocked.

    Idempotent: unchanged prose that already carries an applied verdict is
    returned as is; prose rewritten after the gate is withheld again from the
    recorded verdict.
    """

    output = dict(result)
    metadata = _mapping(output.get("metadata"))
    if _already_applied(metadata):
        return _reapply_recorded(output, metadata)

    decision = evaluate_publication(metadata)
    audit = _mapping(metadata.get("citation_verifier_v2"))
    citations = [
        _mapping(c) for c in (output.get("citations") or []) if isinstance(c, Mapping)
    ]
    ledger = [
        _mapping(c)
        for c in (output.get("claim_ledger") or [])
        if isinstance(c, Mapping)
    ]
    withheld = _initial_withheld(decision, citations, audit)

    if not decision.publishable:
        return _blocked_output(output, metadata, decision, withheld, citations)

    surgery = _surgery(str(output.get("answer") or ""), citations, ledger, withheld)
    return _finish(output, metadata, decision, surgery, citations, ledger)


def withhold_mapping_if_needed(result: Mapping[str, Any]) -> dict[str, Any]:
    """Backward-compatible alias of :func:`apply_publication_verdict`."""

    return apply_publication_verdict(result)


def _answer_as_mapping(answer: ScholarlyAnswer) -> dict[str, Any]:
    return {
        "answer": answer.answer,
        "citations": [c.model_dump() for c in answer.citations],
        "claim_ledger": [c.model_dump() for c in answer.claim_ledger],
        "passages_used": answer.passages_used,
        "insufficient_evidence": answer.insufficient_evidence,
        "metadata": {**answer.metadata, "quality_badge": answer.quality_badge},
    }


def annotate_publication_decision(
    answer: ScholarlyAnswer,
    *,
    withhold_prose: bool,
) -> ScholarlyAnswer:
    """Attach the shared verdict and, at a public boundary, apply it.

    ``withhold_prose=False`` keeps the internal draft for diagnostics: the
    verdict is recorded in ``metadata.publication_gate`` and a blocked draft
    has its citations marked unverified and supported claims downgraded, but
    the prose is untouched and ``applied`` stays False.

    ``withhold_prose=True`` publishes through :func:`apply_publication_verdict`
    — the model form and the mapping form cannot drift.
    """

    if withhold_prose:
        published = apply_publication_verdict(_answer_as_mapping(answer))
        metadata = dict(published["metadata"])
        badge = metadata.pop("quality_badge", answer.quality_badge)
        kept = {str(c.get("id") or "") for c in published["citations"]}
        ledger = [
            ClaimLedgerItem.model_validate(item) for item in published["claim_ledger"]
        ]
        return answer.model_copy(
            update={
                "answer": published["answer"],
                "citations": [c for c in answer.citations if c.id in kept]
                if published["citations"]
                else [],
                "claim_ledger": ledger,
                "passages_used": published["passages_used"],
                "insufficient_evidence": published["insufficient_evidence"],
                "metadata": metadata,
                "quality_badge": str(badge),
            }
        )

    decision = evaluate_publication(answer.metadata)
    audit = _mapping(answer.metadata.get("citation_verifier_v2"))
    citations = [c.model_dump() for c in answer.citations]
    withheld = _initial_withheld(decision, citations, audit)
    metadata = {
        **answer.metadata,
        "publication_gate": _gate_metadata(
            decision, withheld, citations, None, applied=False
        ),
    }
    if decision.publishable:
        return answer.model_copy(update={"metadata": metadata})

    reason = ", ".join(decision.reasons) or "publication gate blocked"
    unverified_citations: list[Citation] = [
        citation.model_copy(
            update={
                "verified": False,
                "verification_note": citation.verification_note
                or f"[WITHHELD] {reason}",
            }
        )
        for citation in answer.citations
    ]
    downgraded_ledger = [
        item.model_copy(
            update={
                "status": ClaimStatus.INSUFFICIENT,
                "status_reason": f"blocked: {reason}",
            }
        )
        if item.status is ClaimStatus.SUPPORTED
        else item
        for item in answer.claim_ledger
    ]
    return answer.model_copy(
        update={
            "metadata": metadata,
            "citations": unverified_citations,
            "claim_ledger": downgraded_ledger,
            "quality_badge": BADGE_BLOCKED,
            "insufficient_evidence": True,
        }
    )


__all__ = [
    "BADGE_BLOCKED",
    "BADGE_HIGH",
    "BADGE_PARTIAL",
    "POLICY",
    "REASON_ORPHANED",
    "REASON_SENTENCE_WITHHELD",
    "WARNING_SYNTHESIS_DEGRADED",
    "WITHHELD_SENTENCE_MARKER",
    "PublicationDecision",
    "WithholdingOutcome",
    "annotate_publication_decision",
    "apply_publication_verdict",
    "evaluate_publication",
    "is_cacheable",
    "is_publishable",
    "synthesis_is_authoritative",
    "withhold_mapping_if_needed",
    "withhold_sentences",
]
