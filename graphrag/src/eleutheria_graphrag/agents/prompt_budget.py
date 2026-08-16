"""Whole-prompt budgeting for the dialectical synthesis (prompt-size containment).

WHY THIS EXISTS. ``synthesis_context_budget`` (state.py) sizes the CONTEXT PACK
by planner tier — 120k / 250k / ceiling tokens. But the Scholar-RAG synthesis
prompt is not built from the pack at all: it is
``DIALECTICAL_SYNTHESIS_SYSTEM + DIALECTICAL_SYNTHESIS_TEMPLATE(map_markdown)``,
and ``map_markdown`` embeds every contested passage's FULL original + English
text. A handful of full-book passage nodes (the corpus holds passage nodes whose
``text_content`` is 80-123k chars — ``passage_eusebius_praep_ev_book_13`` and
kin) therefore pushed a "250k tier" query to a ~1.2M-token prompt: the Codex rung
was skipped for exceeding its window, claude-opus-5 400'd
("~1,174,000 tokens > 1,000,000"), and only a later salvage rung answered, after
minutes of waste.

The fix here is threefold:

1. **Whole-prompt budgeting.** :func:`plan_prompt_budget` computes the FIXED
   sections (system prompt, template instructions, answer reserve, safety
   margin) FIRST and hands the variable section (the map) only the REMAINDER of
   the tier budget — with a floor so the map can never collapse to nothing.
2. **Source caps.** :func:`excerpt_within_budget` caps any single verbatim block
   by SELECTING a relevant excerpt window at line/sentence boundaries — never by
   cutting mid-quote — so a whole-book dump becomes the passage's relevant
   lines ± context. :func:`cap_description` does the same, harder, for KG node
   descriptions that leak into position claims.
3. **One estimator.** Everything prices with
   :func:`eleutheria_graphrag.services.token_budget.estimate_tokens`, the same
   conservative ``len // 3`` the LLM provider-routing gate uses.

QUALITY-FIRST. Nothing here truncates a quotation mid-word or mid-sentence: the
unit of selection is a line or a sentence, and an elision is marked explicitly
so the model can never stitch two non-adjacent spans into one fake quote. The
provenance/quote-containment gate still verifies against the UNCUT
``PassageRef.original_text`` (this module never mutates the map), so excerpting
the prompt cannot turn a real citation into an unverifiable one.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field

from eleutheria_graphrag.services.token_budget import estimate_tokens, format_tokens

__all__ = [
    "ELISION_MARKER",
    "PromptComposition",
    "cap_description",
    "excerpt_within_budget",
    "plan_prompt_budget",
]


# ── caps ─────────────────────────────────────────────────────────────────────

#: Per-passage verbatim cap (original AND English each get this budget). ~1200
#: tokens is ~3600 chars of Greek — several dense Stoic paragraphs, far more
#: than any answer quotes — while a full book (80-123k chars) is 20-40x over it.
PASSAGE_TOKEN_CAP_DEFAULT = 1200

#: Absolute floor for a per-passage cap when the remainder is squeezed. Below
#: this a "passage" stops being quotable evidence, so we drop whole passages
#: instead of shaving every one into uselessness.
PASSAGE_TOKEN_FLOOR = 250

#: Per-node description contribution cap (position claims sourced from KG
#: ``description`` fields, which for curated nodes can run to whole essays).
NODE_DESCRIPTION_TOKEN_CAP = 2000

#: Reserve on top of the answer budget for tokenizer variance, the chat
#: envelope, and tool/system overhead the estimator does not see.
SAFETY_MARGIN_TOKENS = 4000

#: The map never collapses to zero: even a pathological fixed-section cost
#: leaves this much for the controversy map.
MAP_FLOOR_TOKENS = 24_000

#: Marker inserted where an excerpt window omits text. Explicit and countable so
#: the model cannot silently weld two non-adjacent spans into one quotation.
ELISION_MARKER = "[… {n} characters elided …]"


def _env_int(name: str, default: int, *, minimum: int) -> int:
    raw = os.getenv(name)
    if raw:
        try:
            value = int(raw)
        except ValueError:
            return default
        if value >= minimum:
            return value
    return default


def passage_token_cap() -> int:
    """Per-passage verbatim cap; ``ELEUTHERIA_PASSAGE_TOKEN_CAP`` overrides."""
    return _env_int(
        "ELEUTHERIA_PASSAGE_TOKEN_CAP",
        PASSAGE_TOKEN_CAP_DEFAULT,
        minimum=PASSAGE_TOKEN_FLOOR,
    )


# ── excerpt selection (never a mid-quote cut) ────────────────────────────────

_UNIT_SPLIT_RE = re.compile(r"(?<=[.;:!?·;])\s+|\n+")
_TERM_RE = re.compile(r"\w{4,}", re.UNICODE)

_STOP_TERMS: frozenset[str] = frozenset(
    {
        "what",
        "when",
        "where",
        "which",
        "with",
        "that",
        "this",
        "does",
        "think",
        "about",
        "from",
        "have",
        "their",
        "there",
        "were",
        "they",
        "them",
        "then",
        "into",
        "over",
        "than",
        "such",
        "some",
        "also",
    }
)


def query_terms(question: str) -> frozenset[str]:
    """Lowercased content terms of a question, for excerpt-window scoring."""
    return frozenset(
        tok
        for tok in _TERM_RE.findall((question or "").lower())
        if tok not in _STOP_TERMS
    )


def _split_units(text: str) -> list[str]:
    """Split into selection units: lines, then sentence/colon boundaries.

    A unit is the smallest span an excerpt is allowed to start or end on, so a
    quotation is never cut mid-word or mid-clause.
    """
    units = [u.strip() for u in _UNIT_SPLIT_RE.split(text) if u and u.strip()]
    return units or ([text.strip()] if text.strip() else [])


def _word_boundary_cut(text: str, max_tokens: int) -> str:
    """Last-resort cut for an unpunctuated dump: whole words only, elision marked.

    Reached only when the text carries no sentence/line boundary to cut on (a
    passage node holding a whole book as one undelimited blob). Words are never
    split, and the omitted tail is counted in the marker so the reader — and the
    model — knows the span is not continuous with anything that follows.
    """
    words = text.split()
    kept: list[str] = []
    used = 0
    for word in words:
        cost = max(len(word) // 3, 1) + 1
        if kept and used + cost > max_tokens:
            break
        kept.append(word)
        used += cost
    body = " ".join(kept)
    elided = len(text) - len(body)
    if elided <= 0:
        return body
    return f"{body} {ELISION_MARKER.format(n=elided)}"


def _score_unit(unit: str, terms: frozenset[str]) -> int:
    if not terms:
        return 0
    low = unit.lower()
    return sum(1 for term in terms if term in low)


def excerpt_within_budget(
    text: str,
    max_tokens: int,
    *,
    terms: frozenset[str] = frozenset(),
) -> tuple[str, bool]:
    """Fit ``text`` into ``max_tokens`` by SELECTING an excerpt window.

    Returns ``(excerpt, was_excerpted)``. When the text already fits it is
    returned verbatim and unflagged. Otherwise units (sentences / lines) are
    scored against ``terms`` (the question's content words), the window is
    anchored on the best-scoring unit, and it grows outward — the cited lines
    plus their context — until the budget is spent. The omitted head/tail are
    replaced by an explicit :data:`ELISION_MARKER` so no two non-adjacent spans
    ever read as one continuous quotation.

    Never cuts inside a unit: with a budget too small even for the anchor unit,
    that one unit is still returned whole (a real sentence beats a shredded one).
    """
    text = text or ""
    if max_tokens <= 0 or not text.strip():
        return ("", bool(text.strip()))
    if estimate_tokens(text) <= max_tokens:
        return (text, False)

    units = _split_units(text)
    if len(units) <= 1:
        # Not a sentence — an unpunctuated dump. Fall back to a WORD-boundary
        # cut (still never mid-word) with the elision marked, rather than let a
        # single "unit" overflow the whole prompt.
        return (_word_boundary_cut(text, max_tokens), True)

    scores = [_score_unit(u, terms) for u in units]
    anchor = max(range(len(units)), key=lambda i: (scores[i], -i))

    lo = hi = anchor
    used = estimate_tokens(units[anchor])
    if used > max_tokens:
        # Even the anchor sentence alone overflows: keep it word-bounded.
        return (_word_boundary_cut(units[anchor], max_tokens), True)
    # Grow outward, alternating, preferring the higher-scoring side.
    while True:
        prev_ok = lo > 0
        next_ok = hi < len(units) - 1
        if not prev_ok and not next_ok:
            break
        prev_cost = estimate_tokens(units[lo - 1]) + 1 if prev_ok else None
        next_cost = estimate_tokens(units[hi + 1]) + 1 if next_ok else None
        take_prev = False
        if prev_ok and next_ok:
            take_prev = scores[lo - 1] > scores[hi + 1]
        elif prev_ok:
            take_prev = True
        if take_prev:
            assert prev_cost is not None
            if used + prev_cost > max_tokens:
                break
            used += prev_cost
            lo -= 1
        else:
            if next_cost is None or used + next_cost > max_tokens:
                # The preferred side no longer fits; try the other one once.
                if prev_ok and prev_cost is not None and used + prev_cost <= max_tokens:
                    used += prev_cost
                    lo -= 1
                    continue
                break
            used += next_cost
            hi += 1

    head_elided = sum(len(u) for u in units[:lo])
    tail_elided = sum(len(u) for u in units[hi + 1 :])
    parts: list[str] = []
    if head_elided:
        parts.append(ELISION_MARKER.format(n=head_elided))
    parts.append(" ".join(units[lo : hi + 1]))
    if tail_elided:
        parts.append(ELISION_MARKER.format(n=tail_elided))
    return (" ".join(parts), True)


def cap_description(
    text: str,
    max_tokens: int = NODE_DESCRIPTION_TOKEN_CAP,
    *,
    terms: frozenset[str] = frozenset(),
) -> str:
    """Cap a KG node description / position claim's contribution to a prompt.

    Descriptions are prose ABOUT the evidence, not the evidence itself, so a cap
    here costs nothing citable. Same unit-boundary selection as
    :func:`excerpt_within_budget`.
    """
    excerpt, _ = excerpt_within_budget(text, max_tokens, terms=terms)
    return excerpt


# ── whole-prompt budgeting ───────────────────────────────────────────────────


@dataclass
class PromptComposition:
    """Per-section token accounting for one assembled prompt.

    ``variable_budget`` is what the map (the only unbounded section) was allowed
    to spend; the rest is the fixed cost computed before it.
    """

    tier_budget: int
    system: int = 0
    instructions: int = 0
    answer_reserve: int = 0
    safety_margin: int = 0
    variable_budget: int = 0
    map_tokens: int = 0
    pack_tokens: int = 0
    ledger_tokens: int = 0
    notes: list[str] = field(default_factory=list)

    @property
    def fixed(self) -> int:
        return (
            self.system + self.instructions + self.answer_reserve + self.safety_margin
        )

    @property
    def total(self) -> int:
        """Total PROMPT tokens (answer reserve and margin are not prompt text)."""
        return (
            self.system
            + self.instructions
            + self.map_tokens
            + (self.pack_tokens + self.ledger_tokens)
        )

    def log_line(self) -> str:
        """The one-line INFO composition summary."""
        return (
            f"synthesis prompt: total≈{format_tokens(self.total)} "
            f"(map {format_tokens(self.map_tokens)}, "
            f"pack {format_tokens(self.pack_tokens)}, "
            f"ledger {format_tokens(self.ledger_tokens)}, "
            f"system {format_tokens(self.system + self.instructions)}; "
            f"tier budget {format_tokens(self.tier_budget)})"
        )


def plan_prompt_budget(
    *,
    tier_budget: int,
    system_prompt: str,
    instructions: str,
    answer_tokens: int = 0,
    safety_margin: int = SAFETY_MARGIN_TOKENS,
    floor: int = MAP_FLOOR_TOKENS,
) -> PromptComposition:
    """Fixed sections first, remainder to the variable section.

    ``variable_budget = tier_budget - system - instructions - answer_tokens -
    safety_margin``, floored at ``floor`` so the map never collapses to zero
    (a prompt with no evidence is worse than a slightly over-budget one, and the
    floor is small enough that the provider window still holds it).
    """
    comp = PromptComposition(
        tier_budget=max(0, tier_budget),
        system=estimate_tokens(system_prompt),
        instructions=estimate_tokens(instructions),
        answer_reserve=max(0, answer_tokens),
        safety_margin=max(0, safety_margin),
    )
    remainder = comp.tier_budget - comp.fixed
    if remainder < floor:
        comp.notes.append(
            f"variable budget floored at {format_tokens(floor)} "
            f"(remainder was {format_tokens(max(0, remainder))})"
        )
        remainder = floor
    comp.variable_budget = remainder
    return comp
