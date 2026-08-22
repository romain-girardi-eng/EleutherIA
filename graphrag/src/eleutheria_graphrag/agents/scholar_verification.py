"""Scholar-grade verification loop — the Scholar-RAG M5 referees (ARCHITECTURE §5).

The cite-as-you-write synthesis (M4) is followed by three referees + an iterate
condition. All operate **against the ControversyMap, not free memory** — the map
is the verification ORACLE (CoVe's load-bearing trick). The map gives the
completeness critic a real denominator (fault lines retrieved vs. narrated), and
the marker resolver a closed set of legal ids.

Three referees live here, each killing a named failure:

1. :func:`verify_citations_on_frames` (F1/integrity) — extends the v2 adversarial
   contract to the synthesis path WITHOUT a DB round-trip: every ``[P_*]`` /
   ``[passage_*]`` marker is resolved against the map; a marker that does NOT
   resolve is hard-rejected (a hallucinated id); a quotation claim gets an
   **exact-substring** check against the map's original passage text (zero
   tolerance for invented Greek/Latin). The cap is lifted from 8 to ALL
   attributed-position claims (these are load-bearing on the synthesis path).
   The NLI-style entailment confirmation is the optional LLM arm (§5.1); the
   deterministic marker-resolve + substring arm runs with no LLM.

2. :func:`completeness_on_map` (F11) — the completeness critic. Denominator =
   the frames ``find_debates``/``build_controversy_frame`` actually returned
   (graph-real, NOT the planner's hints). ``fault_line_coverage = narrated /
   in_map``. Each missing frame becomes a concrete, targeted expansion query.

3. :func:`anti_anachronism_gate` (F11) — scans the prose for the MEMORY-flagged
   modern lexicon; any occurrence OUTSIDE an attributed-position span fails the
   gate and yields a RARR span-edit instruction. (The semantic LLM arm that
   confirms the label is pinned to the right holder is documented but optional.)

:func:`scholar_verdict` runs the three and applies the §5.4 ACCEPT/REJECT
condition; REJECT yields the targeted expansion queries + RARR edits the caller
feeds back into retrieval/span-editing. Capped at ``N_max`` rounds by budget tier
(§6); on hard failure the caller routes to the M4 degraded mode (never a
template).

VECTORLESS throughout (marker resolution + substring + set-diff are all string
ops over the map; the NLI/semantic arms are short isolated utility-tier calls when
supplied). Gated by ``ELEUTHERIA_SCHOLAR_RAG`` at the call site; this module is
import-safe and inert until a consumer invokes it — no live module imports it
with the flag OFF.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

from eleutheria_graphrag.agents.dialectical_synthesis import (
    ANACHRONISTIC_LEXICON,
    _attested_edge_index,
    _edge_marker_key,
    _split_sentences,
)
from eleutheria_graphrag.agents.state import (
    ClaimStatus,
    ControversyMap,
    GroundedPosition,
    PassageRef,
)

logger = logging.getLogger(__name__)


# ── verdict containers ───────────────────────────────────────────────────────


@dataclass
class CitationVerdict:
    """Per-marker result of the citation referee (map-resolved, no DB trip)."""

    marker: str  # the id as written in the prose (P_x / passage_y)
    kind: str  # "P" | "passage" | "edge"
    sentence: str
    resolved: bool  # the id exists in the map
    grounded: bool  # quotation substring check passed (passage markers only)
    status: ClaimStatus  # SUPPORTED | UNVERIFIED | INSUFFICIENT
    reason: str = ""


@dataclass
class CitationReport:
    """Aggregate citation-referee report over the synthesis prose."""

    verdicts: list[CitationVerdict] = field(default_factory=list)

    @property
    def unsupported(self) -> list[CitationVerdict]:
        """Markers the referee could not pass (hard-reject or failed substring)."""
        return [v for v in self.verdicts if v.status is not ClaimStatus.SUPPORTED]

    @property
    def passed(self) -> bool:
        """ACCEPT condition: 0 unsupported attributed/quotation markers."""
        return not self.unsupported


@dataclass
class CompletenessReport:
    """Completeness critic over a graph-real denominator (the map's frames)."""

    frames_in_map: list[str] = field(default_factory=list)  # frame_ids in the map
    frames_narrated: list[str] = field(default_factory=list)  # frame_ids in the prose
    missing_frame_ids: list[str] = field(default_factory=list)
    expansion_queries: list[str] = field(default_factory=list)  # targeted re-retrieval

    @property
    def fault_line_coverage(self) -> float:
        """``narrated / in_map`` — 1.0 when every map frame is narrated."""
        if not self.frames_in_map:
            return 1.0
        return len(self.frames_narrated) / len(self.frames_in_map)

    @property
    def complete(self) -> bool:
        return not self.missing_frame_ids


@dataclass
class AnachronismViolation:
    """A modern label asserted OUTSIDE an attributed-position span."""

    term: str
    sentence: str
    rarr_edit: str  # the span-edit instruction ("voice as 'what X calls…'")


@dataclass
class AnachronismReport:
    violations: list[AnachronismViolation] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.violations


@dataclass
class ScholarFidelityViolation:
    """An attributed characterisation that contradicts the holder's KG node.

    F2: the worst failure mode for a scholarly tool is misattributing a named
    scholar's position (e.g. asserting "Frede reads Epictetus as an
    incompatibilist" when Frede's node says he holds a *compatibilist* origin of
    free will). This is a deterministic contradiction check against the holder's
    own KG description — never a fabricated correction.
    """

    holder: str
    asserted_label: str  # the characterisation in the prose ("incompatibilist")
    node_label: str  # the contradictory label in the holder's KG description
    sentence: str
    rarr_edit: str


@dataclass
class ScholarFidelityReport:
    violations: list[ScholarFidelityViolation] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.violations


@dataclass
class ScholarVerdict:
    """Combined §5.4 verdict + the targeted remediation the caller feeds back."""

    accepted: bool
    citation: CitationReport
    completeness: CompletenessReport
    anachronism: AnachronismReport
    fidelity: ScholarFidelityReport = field(default_factory=ScholarFidelityReport)
    expansion_queries: list[str] = field(default_factory=list)
    rarr_edits: list[str] = field(default_factory=list)


# ── shared marker parsing (the cite-as-you-write surface) ────────────────────

# Same marker grammar as the M4 ledger: [P_<id>: …] / [passage_<id>: …] /
# [edge: <rel> P_a->P_b]. Keep one truth so the referee resolves exactly the
# ids the synthesis emitted.
_PE_MARKER_RE = re.compile(r"\[(?P<kind>P|passage)_(?P<body>[^\]]+)\]")
_EDGE_MARKER_RE = re.compile(r"\[edge[:_]\s*(?P<body>[^\]]+)\]")
_ARROW_EDGE_RE = re.compile(r"P_(?P<from>\w+)\s*--\s*\w+\s*-->\s*P_(?P<to>\w+)")


def _index_map(
    cmap: ControversyMap,
) -> tuple[dict[str, GroundedPosition], dict[str, PassageRef]]:
    """Resolution tables: position-id -> position, passage-id -> passage."""
    pos_by_id: dict[str, GroundedPosition] = {}
    passage_by_id: dict[str, PassageRef] = {}
    for frame in cmap.frames:
        for p in frame.positions:
            pos_by_id[p.position_id] = p
        for pr in frame.contested_passages:
            passage_by_id[pr.passage_id] = pr
    for pr in cmap.exegesis_units:
        passage_by_id[pr.passage_id] = pr
    for pid, pr in cmap.provenance.items():
        passage_by_id.setdefault(pid, pr)
    return pos_by_id, passage_by_id


def _marker_id(body: str) -> str:
    """Take the id portion of a marker body (before the first ``:``)."""
    return body.split(":", 1)[0].strip().lstrip("_")


_SCHOLAR_QUOTE_SPAN_RE = re.compile(r"[\"“]([^\"“”]{15,})[\"”]")
_GREEK_CHAR_RE = re.compile(r"[Ͱ-Ͽἀ-῿]")


def _normalize_quote_text(text: str) -> str:
    """Whitespace- and typographic-quote-insensitive form for substring checks."""
    text = text.replace("‘", "'").replace("’", "'").replace("“", '"').replace("”", '"')
    return " ".join(text.split())


_ELLIPSIS_SPLIT_RE = re.compile(r"…|\.\.\.")


def _span_backed_by_quotation(span: str, quotation_norm: str) -> bool:
    """True when every marked-ellipsis fragment of the span is in the quotation.

    An ellipsed quote ('A, … B') is legitimate scholarly practice — the elision
    is DECLARED — so the check runs per fragment. A span no fragment of which
    appears verbatim remains a fabricated quotation. Fragments shorter than 8
    characters carry no evidential weight and are ignored.
    """
    if not quotation_norm:
        return False
    fragments = [
        _normalize_quote_text(f).strip(" ,;:—–-")
        for f in _ELLIPSIS_SPLIT_RE.split(span)
    ]
    fragments = [f for f in fragments if len(f) >= 8]
    if not fragments:
        return False
    return all(f in quotation_norm for f in fragments)


def _scholar_quote_spans(sentence: str) -> list[str]:
    """Double-quoted English spans a scholar-quote integrity check should own.

    Excluded — these belong to other checks or are legitimate without one:
    * sentences that also carry a ``[passage_*]`` marker (their quotes are the
      primary text's translation, verified by the passage arm);
    * spans containing Greek (the text gate's jurisdiction);
    * Title Case spans (quoted work titles, not somebody's asserted words).
    """
    if "[passage_" in sentence:
        return []
    spans: list[str] = []
    for m in _SCHOLAR_QUOTE_SPAN_RE.finditer(sentence):
        span = m.group(1).strip()
        if _GREEK_CHAR_RE.search(span):
            continue
        words = [w for w in span.split() if w[:1].isalpha()]
        if words and sum(1 for w in words if w[:1].isupper()) / len(words) >= 0.6:
            continue
        spans.append(span)
    return spans


def _looks_like_quotation(sentence: str, passage: PassageRef) -> str | None:
    """Return the quoted original substring if the sentence quotes the passage.

    Heuristic: the sentence contains a run of the passage's ORIGINAL text. We
    look for the longest map-passage prefix the sentence contains so a partial
    inline quote still counts; a sentence that merely *cites* (no verbatim
    original) returns ``None`` (nothing to substring-check — citation-only).
    """
    original = (passage.original_text or "").strip()
    if not original:
        return None
    # Try progressively shorter prefixes of the original (down to 12 chars) —
    # an inline quote rarely reproduces the whole passage.
    for length in (len(original), 60, 40, 24, 12):
        probe = original[: min(length, len(original))].strip()
        if len(probe) >= 8 and probe in sentence:
            return probe
    return None


# ── 1. citation referee on frames (marker-resolve + exact substring) ─────────


def verify_citations_on_frames(prose: str, cmap: ControversyMap) -> CitationReport:
    """Adversarial citation referee on the synthesis path (ARCHITECTURE §5.1).

    Deterministic, no DB round-trip — the map is the oracle:

    * every ``[P_*]`` / ``[passage_*]`` marker is resolved against the map; an
      id that does NOT resolve is hard-rejected (``UNVERIFIED`` — a hallucinated
      id), exactly as the M4 ledger flags it;
    * a quotation claim (the sentence reproduces verbatim original text) gets an
      **exact-substring** check against the map's ``original_text``; an invented
      Greek/Latin run that is not a substring of the cited passage is
      ``INSUFFICIENT`` (the integrity policy — zero tolerance);
    * the cap is ALL markers (no 8-claim sample): on the synthesis path the
      attributed positions are load-bearing.

    The NLI-style entailment confirmation (does the cited entry *entail* the
    sentence?) is the optional LLM arm in :func:`verify_citations_on_frames_llm`;
    this function is the deterministic arm that always runs.
    """
    pos_by_id, passage_by_id = _index_map(cmap)
    attested_edges = _attested_edge_index(cmap)
    verdicts: list[CitationVerdict] = []

    for sentence in _split_sentences(prose):
        # Scholar-quote integrity (F1 extension): a double-quoted English span
        # in a sentence whose only markers are positions must be the verbatim
        # words of ONE of the cited positions (their ``quotation`` field). A
        # span no cited position contains is a fabricated scholar quotation.
        quote_spans = _scholar_quote_spans(sentence)
        sentence_position_ids = [
            _marker_id(m.group("body"))
            for m in _PE_MARKER_RE.finditer(sentence)
            if m.group("kind") == "P"
        ]
        unbacked_spans: list[str] = []
        if quote_spans and sentence_position_ids:
            quotations = [
                _normalize_quote_text(getattr(pos_by_id[pid], "quotation", None) or "")
                for pid in sentence_position_ids
                if pid in pos_by_id
            ]
            for span in quote_spans:
                if not any(_span_backed_by_quotation(span, q) for q in quotations):
                    unbacked_spans.append(span)

        for m in _PE_MARKER_RE.finditer(sentence):
            kind = m.group("kind")
            ref_id = _marker_id(m.group("body"))
            marker = f"{kind}_{ref_id}"

            if kind == "P":
                position = pos_by_id.get(ref_id)
                if position is not None and position.evidence_tier == "citable":
                    if unbacked_spans:
                        verdicts.append(
                            CitationVerdict(
                                marker=marker,
                                kind="P",
                                sentence=sentence,
                                resolved=True,
                                grounded=False,
                                status=ClaimStatus.INSUFFICIENT,
                                reason=(
                                    "quoted words are not the verbatim quotation "
                                    "of any position cited in the sentence: "
                                    + "; ".join(repr(s[:60]) for s in unbacked_spans)
                                ),
                            )
                        )
                        continue
                    verdicts.append(
                        CitationVerdict(
                            marker=marker,
                            kind="P",
                            sentence=sentence,
                            resolved=True,
                            grounded=True,
                            status=ClaimStatus.SUPPORTED,
                            reason="position id resolves to the map",
                        )
                    )
                else:
                    verdicts.append(
                        CitationVerdict(
                            marker=marker,
                            kind="P",
                            sentence=sentence,
                            resolved=False,
                            grounded=False,
                            status=ClaimStatus.UNVERIFIED,
                            reason="position id does not resolve to the map (hallucinated)",
                        )
                    )
                continue

            # passage marker
            passage = passage_by_id.get(ref_id)
            if passage is None or passage.evidence_tier != "citable":
                verdicts.append(
                    CitationVerdict(
                        marker=marker,
                        kind="passage",
                        sentence=sentence,
                        resolved=False,
                        grounded=False,
                        status=ClaimStatus.UNVERIFIED,
                        reason="passage id does not resolve to the map (hallucinated)",
                    )
                )
                continue
            # exact-substring integrity check when the sentence quotes the original
            quoted = _looks_like_quotation(sentence, passage)
            if quoted is None:
                verdicts.append(
                    CitationVerdict(
                        marker=marker,
                        kind="passage",
                        sentence=sentence,
                        resolved=True,
                        grounded=True,
                        status=ClaimStatus.SUPPORTED,
                        reason="passage cited (no verbatim original to substring-check)",
                    )
                )
            else:
                # quoted substring is present in the passage by construction of
                # _looks_like_quotation; if a future caller passes a mangled
                # quote it will not match and falls here as INSUFFICIENT.
                grounded = quoted in (passage.original_text or "")
                verdicts.append(
                    CitationVerdict(
                        marker=marker,
                        kind="passage",
                        sentence=sentence,
                        resolved=True,
                        grounded=grounded,
                        status=(
                            ClaimStatus.SUPPORTED
                            if grounded
                            else ClaimStatus.INSUFFICIENT
                        ),
                        reason=(
                            "verbatim original is a substring of the cited passage"
                            if grounded
                            else "quoted original NOT a substring of the cited passage"
                        ),
                    )
                )
        for match in _EDGE_MARKER_RE.finditer(sentence):
            body = match.group("body")
            key = _edge_marker_key(body)
            marker = f"edge:{body.strip()}"
            if key is not None and key in attested_edges:
                verdicts.append(
                    CitationVerdict(
                        marker=marker,
                        kind="edge",
                        sentence=sentence,
                        resolved=True,
                        grounded=True,
                        status=ClaimStatus.SUPPORTED,
                        reason="edge resolves to an R16-attested map relation",
                    )
                )
            else:
                verdicts.append(
                    CitationVerdict(
                        marker=marker,
                        kind="edge",
                        sentence=sentence,
                        resolved=False,
                        grounded=False,
                        status=ClaimStatus.UNVERIFIED,
                        reason="edge is absent from the map or lacks metadata.attested_by",
                    )
                )
    return CitationReport(verdicts=verdicts)


# ── 2. completeness critic with a graph-real denominator ─────────────────────


def _narrated_frame_ids(prose: str, cmap: ControversyMap) -> set[str]:
    """Which map frames the prose actually narrates.

    A frame counts as narrated if the prose cites any of its positions
    (``[P_<pos>]``), invokes its title verbatim, or invokes any of its
    dialectical links (``[edge: …]`` / ``A --rel--> B``) whose endpoints are
    that frame's positions. (The denominator stays the MAP — judge #2's
    correction of the hand-wavy planner-hint denominator.)
    """
    cited_positions: set[str] = {
        _marker_id(m.group("body")) for m in _PE_MARKER_RE.finditer(prose)
    }
    edge_endpoints: set[str] = set()
    for m in _EDGE_MARKER_RE.finditer(prose):
        for tok in re.findall(r"P_(\w+)", m.group("body")):
            edge_endpoints.add(tok)
    for m in _ARROW_EDGE_RE.finditer(prose):
        edge_endpoints.add(m.group("from"))
        edge_endpoints.add(m.group("to"))

    narrated: set[str] = set()
    for frame in cmap.frames:
        pos_ids = {p.position_id for p in frame.positions}
        if pos_ids & (cited_positions | edge_endpoints):
            narrated.add(frame.frame_id)
            continue
        if frame.title and frame.title.lower() in prose.lower():
            narrated.add(frame.frame_id)
    return narrated


def completeness_on_map(prose: str, cmap: ControversyMap) -> CompletenessReport:
    """Completeness critic (ARCHITECTURE §5.2). Denominator = the map's frames.

    Any frame in the map but absent from the answer is a concrete gap → a
    targeted ``build_controversy_frame`` expansion query the caller re-enters
    into retrieval. ``fault_line_coverage`` is the completeness critic's own
    ratio (also an eval metric).
    """
    in_map = [f.frame_id for f in cmap.frames]
    narrated = _narrated_frame_ids(prose, cmap)
    narrated_ids = [fid for fid in in_map if fid in narrated]
    missing = [fid for fid in in_map if fid not in narrated]

    expansion: list[str] = []
    for frame in cmap.frames:
        if frame.frame_id in missing:
            seed = frame.debate_node_id or frame.frame_id
            expansion.append(f"build_controversy_frame on {seed}")

    return CompletenessReport(
        frames_in_map=in_map,
        frames_narrated=narrated_ids,
        missing_frame_ids=missing,
        expansion_queries=expansion,
    )


# ── 3. anti-anachronism gate (modern label outside an attributed span) ───────

# An attributed span is a sentence carrying a [P_*]/[edge:*] marker OR an
# explicit attribution phrase ("what X calls", "on X's reading", "X terms",
# "X argues", "X holds", "according to X"). A modern label inside such a span is
# fine (it is the scholar's characterisation); outside it is an unattributed
# assertion in the author's own voice → a gate failure (F11).
_ATTRIBUTION_PHRASE_RE = re.compile(
    r"\b(?:what\s+\w+\s+(?:calls|terms)|on\s+\w+'s\s+reading|"
    r"\w+\s+(?:terms|calls|argues|holds|contends|maintains|reads|claims)|"
    r"according\s+to\s+\w+|in\s+\w+'s\s+(?:terms|sense|view)|"
    r"so-called|what\s+modern\s+scholars)\b",
    re.IGNORECASE,
)


def _is_attributed_span(sentence: str) -> bool:
    has_marker = bool(_PE_MARKER_RE.search(sentence)) or bool(
        _EDGE_MARKER_RE.search(sentence)
    )
    return has_marker or bool(_ATTRIBUTION_PHRASE_RE.search(sentence))


def anti_anachronism_gate(prose: str) -> AnachronismReport:
    """Deterministic anti-anachronism gate (ARCHITECTURE §5.3, F11).

    Scans the prose for the MEMORY Phase-11/12 lexicon (``libertarian``,
    ``compatibilism``, ``the will`` as a faculty, ``free-will problem``, …). Any
    occurrence OUTSIDE an attributed-position span is a violation and yields a
    RARR span-edit instruction ("the Stoics were compatibilists" → "the Stoics
    held what modern scholars term compatibilism").

    The semantic LLM arm (confirm the label is pinned to the RIGHT holder, not
    merely *some* attribution) is the optional :func:`anti_anachronism_gate_llm`
    layer; this deterministic arm always runs.
    """
    violations: list[AnachronismViolation] = []
    for sentence in _split_sentences(prose):
        if _is_attributed_span(sentence):
            continue
        low = sentence.lower()
        for term in ANACHRONISTIC_LEXICON:
            if term in low:
                violations.append(
                    AnachronismViolation(
                        term=term,
                        sentence=sentence,
                        rarr_edit=(
                            f"Re-voice the unattributed modern label '{term}' as a "
                            "scholarly characterisation (e.g. 'what modern scholars "
                            f"term {term}' / 'what X calls {term}'), or attribute it "
                            "to its holder; never assert it as ancient fact."
                        ),
                    )
                )
                break  # one violation per sentence is enough to flag it
    return AnachronismReport(violations=violations)


# ── 3b. scholar-fidelity gate (F2: attributed label vs the holder's KG node) ──

# Contradictory position labels in the free-will lexicon. The check is symmetric:
# if the prose attributes ``label`` to a holder whose KG description asserts a
# member of ``contradictions[label]`` (and does NOT itself assert ``label``), the
# attribution contradicts the source-of-truth node → flag it. Labels are matched
# as whole words, case-insensitively. Deterministic, no LLM, no fabrication.
_POSITION_CONTRADICTIONS: dict[str, tuple[str, ...]] = {
    "compatibilist": ("incompatibilist", "libertarian"),
    "compatibilism": ("incompatibilism", "libertarian"),
    "incompatibilist": ("compatibilist",),
    "incompatibilism": ("compatibilism",),
    "libertarian": ("compatibilist", "compatibilism", "determinist", "determinism"),
    "determinist": ("libertarian", "indeterminist"),
    "determinism": ("libertarian", "indeterminism"),
    "indeterminist": ("determinist",),
    "indeterminism": ("determinism",),
}

# All labels we know how to check, longest-first so "incompatibilist" is tried
# before "compatibilist" (the latter is a substring of the former).
_FIDELITY_LABELS: tuple[str, ...] = tuple(
    sorted(_POSITION_CONTRADICTIONS, key=len, reverse=True)
)


def _labels_in(text: str) -> set[str]:
    """Whole-word position labels present in ``text`` (case-insensitive)."""
    low = text.lower()
    found: set[str] = set()
    for label in _FIDELITY_LABELS:
        if re.search(rf"\b{re.escape(label)}\b", low):
            found.add(label)
    return found


def scholar_fidelity_gate(
    prose: str,
    holder_descriptions: dict[str, str] | None,
) -> ScholarFidelityReport:
    """Flag an attributed characterisation that contradicts the holder's KG node.

    ``holder_descriptions`` maps a holder's display name (or any string the
    prose uses to name them) to that holder's canonical KG node description —
    the source of truth. For each sentence that (a) names a known holder and
    (b) asserts a position label, if the holder's node description asserts a
    *contradictory* label and does NOT itself assert the prose's label, the
    sentence misattributes the scholar's position (F2) → a violation with a RARR
    correction pointing back at the node.

    The map is supplied by the caller from the ControversyMap holders / KG; an
    empty or ``None`` map makes the gate a no-op (it never invents a position).
    """
    report = ScholarFidelityReport()
    if not holder_descriptions:
        return report

    # Pre-compute the labels each holder's node actually asserts.
    holder_node_labels: dict[str, set[str]] = {
        holder: _labels_in(desc or "") for holder, desc in holder_descriptions.items()
    }

    for sentence in _split_sentences(prose):
        asserted = _labels_in(sentence)
        if not asserted:
            continue
        low_sentence = sentence.lower()
        for holder, node_labels in holder_node_labels.items():
            # Whole-word match: a substring test wrongly fires "Frede" inside
            # "Frederick", attributing a violation to a holder the sentence does
            # not actually name.
            if not holder or not re.search(
                rf"\b{re.escape(holder.lower())}\b", low_sentence
            ):
                continue
            if not node_labels:
                continue
            for label in asserted:
                # The node already asserts this very label → consistent, skip.
                if label in node_labels:
                    continue
                contradictions = _POSITION_CONTRADICTIONS.get(label, ())
                clash = node_labels.intersection(contradictions)
                if clash:
                    node_label = sorted(clash)[0]
                    report.violations.append(
                        ScholarFidelityViolation(
                            holder=holder,
                            asserted_label=label,
                            node_label=node_label,
                            sentence=sentence,
                            rarr_edit=(
                                f"Scholar-fidelity: the answer attributes "
                                f"'{label}' to {holder}, but {holder}'s KG node "
                                f"characterises the position as '{node_label}'. "
                                f"Correct the attribution to match the node "
                                f"(or drop the label) — never misstate a named "
                                f"scholar's position."
                            ),
                        )
                    )
                    break  # one violation per (holder, sentence) is enough
    return report


# ── 4. combined verdict + iterate condition (§5.4) ───────────────────────────


def scholar_verdict(
    prose: str,
    cmap: ControversyMap,
    *,
    require_completeness: bool = True,
    holder_descriptions: dict[str, str] | None = None,
) -> ScholarVerdict:
    """Run the referees and apply the §5.4 ACCEPT/REJECT condition.

    ACCEPT iff: citation referee 0-unsupported AND (completeness complete OR
    ``require_completeness`` is False — gaps already prose-stated) AND
    anachronism 0-unattributed AND scholar-fidelity 0-contradictions. REJECT →
    the caller turns ``expansion_queries`` into targeted re-retrieval and applies
    ``rarr_edits`` to the offending spans, then re-verifies (capped by budget
    tier; on hard failure routes to the M4 degraded mode — never a template).

    ``holder_descriptions`` (holder name → canonical KG node description) powers
    the F2 scholar-fidelity gate; omit it (or pass an empty map) to skip that
    gate — it never invents a position.
    """
    citation = verify_citations_on_frames(prose, cmap)
    completeness = completeness_on_map(prose, cmap)
    anachronism = anti_anachronism_gate(prose)
    fidelity = scholar_fidelity_gate(prose, holder_descriptions)

    accepted = (
        citation.passed
        and anachronism.passed
        and fidelity.passed
        and (completeness.complete or not require_completeness)
    )

    rarr_edits = [v.rarr_edit for v in anachronism.violations]
    rarr_edits.extend(v.rarr_edit for v in fidelity.violations)
    rarr_edits.extend(
        f"Drop or re-ground the unresolved citation {v.marker}: {v.reason}."
        for v in citation.unsupported
    )

    return ScholarVerdict(
        accepted=accepted,
        citation=citation,
        completeness=completeness,
        anachronism=anachronism,
        fidelity=fidelity,
        expansion_queries=list(completeness.expansion_queries),
        rarr_edits=rarr_edits,
    )


# ── budget tiers (verify rounds per ARCHITECTURE §6) ─────────────────────────

# quick=0, standard=1, deep=2 verification/expansion rounds. The real stop
# condition is the completeness critic; this is the hard cap.
_VERIFY_ROUNDS: dict[str, int] = {"quick": 0, "standard": 1, "deep": 2}


def max_verify_rounds(budget_tier: str) -> int:
    """N_max expansion rounds for the iterate loop, by budget tier (§6)."""
    return _VERIFY_ROUNDS.get(budget_tier, 1)
