"""Dialectical scholarly synthesis — the Scholar-RAG M4 core (ARCHITECTURE §4).

This module is the cutover seam. On the Scholar-RAG path it REPLACES the facet
template + ``DraftClaimLedger -> build_render_prompt -> RenderGroundedAnswer ->
_render_answer_fallback`` chain (failure-map F4/F5/F7/F8) with ONE LLM call over a
:class:`ControversyMap` that emits *cite-as-you-write* prose, plus a deterministic
post-pass that parses the inline markers back into a :class:`ClaimLedgerItem` list
(the provenance ledger is now a BYPRODUCT of the prose, not its input — F8 reversed).

Four pieces live here so the whole synthesis seam reads in one place:

1. The prompt — :data:`DIALECTICAL_SYNTHESIS_SYSTEM` + :data:`DIALECTICAL_SYNTHESIS_TEMPLATE`
   (replaces ``RENDER_ANSWER_PROMPT``; the hardcoded Bobzien⟂Frede example is gone —
   the dialectic comes from the serialised map's first-class edge rows).
2. :func:`serialize_controversy_map` — the ``## QUESTION`` header over the M3
   ``## Controversy Frames`` layer (edges as ``A --opposes--> B`` rows, bilingual
   passages untruncated). Reuses the M3 serialiser so there is one edge-slot truth.
3. :func:`synthesize_dialectical` — the single call (``DialecticalSynthesis.run`` body).
4. :func:`build_provenance_ledger` — the marker -> ledger parser (demotes
   ``DraftClaimLedger`` from generative pre-step to this post-pass).

Plus the new gates that replace the ~10k-char floor (failure-map F4/F9):
:func:`evaluate_content_gate` (a SUBSTANCE gate: ≥1 grounded primary cite + enough
markers that RESOLVE through the map; an invoked fault line is a recorded metric,
not a blocker) and :func:`synthesize_degraded` (a prose-stated reasoned hedge —
NEVER a node-paste).

VECTORLESS throughout. Greek/Latin only ever flows verbatim from the map's
passages (the prompt forbids inventing it). Gated by ``ELEUTHERIA_SCHOLAR_RAG`` at
the call site; this module is import-safe and inert until a consumer invokes it.

MODEL: the synthesis tier. :func:`resolve_scholar_synthesis_model` defaults to
``gpt-5.6-sol`` on the Codex proxy — a TRUE thinking model that returns its
chain-of-thought in ``reasoning_content`` and a clean finished answer in
``content``; ``SCHOLAR_SYNTHESIS_MODEL`` overrides it. The synthesis routes
``reasoning_content`` (a side-channel on ``LLMService``) to the trace, NEVER
into the answer; the answer is ``content`` only.
"""

from __future__ import annotations

import logging
import math
import os
import re
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

from eleutheria_graphrag.agents.ancient_text_matching import (
    contains_word_bounded,
    fold_ancient_text,
)
from eleutheria_graphrag.agents.controversy_map import (
    collect_triage_items,
    condense_source_rank,
    fit_controversy_frames_layer,
    render_controversy_frames_layer,
)
from eleutheria_graphrag.agents.edge_markers import (
    normalise_relation,
    parse_edge_marker,
)
from eleutheria_graphrag.agents.prompt_budget import (
    PromptComposition,
    excerpt_within_budget,
    passage_token_cap,
    plan_prompt_budget,
    query_terms,
)
from eleutheria_graphrag.agents.prompts import delimit_retrieved_text
from eleutheria_graphrag.agents.relevance_triage import (
    relevance_triage_enabled,
    score_relevance,
)
from eleutheria_graphrag.agents.state import (
    ClaimLedgerItem,
    ClaimStatus,
    ControversyMap,
    GroundedPosition,
    PassageRef,
    synthesis_context_budget,
)
from eleutheria_graphrag.agents.text_verifier import (
    _folded_segments,
    extract_greek_runs,
    extract_quoted_latin_spans,
    is_known_term,
)
from eleutheria_graphrag.services.llm_service import resolve_gemini_model
from eleutheria_graphrag.services.token_budget import estimate_tokens

logger = logging.getLogger(__name__)


# ── 1. The synthesis prompt (replaces RENDER_ANSWER_PROMPT) ──────────────────

DIALECTICAL_SYNTHESIS_SYSTEM = """\
You are a historian of ancient philosophy writing for a specialist audience \
(Cambridge-Companion register). You reason DIALECTICALLY over a CONTROVERSY MAP: a \
structured record of contending scholarly positions and the primary texts they \
fight over.

ANSWER THE QUESTION'S SCOPE. The retrieved map is a pool of candidate evidence, \
not a table of contents. Select only positions and passages that materially answer \
the user's question. For a focused question on Cicero's testimony about Chrysippus, \
do not add independent chapters on Augustine, grace, or the history of the will \
merely because those frames were retrieved. Later witnesses belong only where they \
resolve a stated source-critical issue. State missing evidence rather than filling \
the gap with neighbouring topics. Follow the user's requested language and depth.

THINK AS A RESEARCHER. Begin with the evidence needed for the question. Distinguish
what the ancient text says, an attributed modern interpretation, and your own
reasoned inference. A focused textual question may be answered by a precise
paraphrase anchored to its conventional locus; do not force a historiographical
controversy or a second source into a straightforward identification.

WHERE INTERPRETATION IS CONTESTED, ENTER A DIALOGUE WITH OTHER SCHOLARS. Attribute
each borrowed interpretation to a named modern scholar and its actual source.
Compare positions only where a real disagreement is attested in the dossier;
never manufacture opposition merely to populate a dialectical template. Explain
when scholars address different questions or use the same term differently.

DEFEND A VERDICT WHEN THE QUESTION ASKS FOR ONE. For an assessment or comparison,
state the best-supported conclusion, the evidence carrying it, and the strongest
relevant objection. If the evidence cannot support a preference, say precisely
why: warranted uncertainty is a scholarly conclusion, not a failure. A broad
survey may close by identifying what remains open. Never imply that a dispute
is settled just because one reconstruction is persuasive. Use a separate Verdict
section only when it clarifies a substantial assessment, not for a brief factual
answer. Modern analytical categories must remain distinguished from ancient
self-descriptions.

DISCLOSE THE RANK OF YOUR SOURCES. A position line in the map may carry a SOURCE RANK \
in brackets after its citation — "[MA thesis]", "[PhD dissertation]", "[online essay, \
not peer-reviewed]", "[preprint]". On the FIRST citation of such a source you MUST \
disclose that rank in the prose ("Moon's unpublished MA thesis (2016: 42) …"; "in a \
non-peer-reviewed online essay, Nagasawa argues …"), and you must NEVER weigh it as \
equal to a monograph or a peer-reviewed article: grey literature may orient, \
corroborate, or supply a bibliography, but it can never be the authority that decides \
a contested point — say so when you use it. A position carrying NO rank bracket is \
UNSTATED, not established: never upgrade it in your prose to "peer-reviewed", \
"standard", "the standard treatment", or "established scholarship".

Modern categories — "libertarian free will", "compatibilism", "incompatibilism", \
"hard/soft determinism", "the will" as a faculty, "the free-will problem", \
"indeterminist" — are scholarly CHARACTERISATIONS. They may appear ONLY inside an \
attributed position ("what Bobzien terms…", "on Frede's reading…"), NEVER asserted \
in your own voice as ancient fact.

You never write Greek or Latin that is not present verbatim in the provided
passages. If the wording is unavailable, use a modern-language paraphrase and
state the limit; never reconstruct or complete fragmentary text.

CITE ANCIENT TEXTS BY THEIR CONVENTIONAL LOCUS. Author, work, book/chapter/section,
fragment number, or a canonical scheme such as Bekker or Stephanus is sufficient.
A missing edition/PDF page does not make an ancient source inauthentic. Identify
the edition or witness when wording or variants matter. A related passage from a
different work cannot substitute for the requested locus.

QUOTE WHEN WORDING MATTERS. For a philological claim or a contested formulation,
quote the relevant words exactly from the dossier, with their [passage_<id>: ...]
marker. A source-grounded paraphrase with the same precise marker is appropriate
otherwise. There is no quota of quotations per paragraph or per controversy.
When using a provided published translation, preserve its wording and language;
never fabricate an English quotation when only a French translation is supplied.
A modern-language paraphrase is not a quotation from a published translator.

CITE AS YOU WRITE. Every interpretive sentence carries an inline marker drawn from \
the map you are given, using exactly these forms:
  [P_<id>: <holder> <year>, <publication> p.<n>]   for an attributed scholar position
  [edge: <relation> P_<from>->P_<to>]               for a dialectical link you invoke
  [passage_<id>: <author>, <ref>]                   for a quoted/cited primary passage
Every attributed modern interpretation must carry its [P_<id>: …] scholar marker;
a direct reading of an ancient passage instead carries its [passage_<id>: …] marker. \
Use only ids that appear in the map. Never invent an id, a scholar, a publication, or \
a page number — if a position has no page in the map, cite it at work level only.

QUOTE THE SCHOLARS THEMSELVES WHEN THE MAP SUPPLIES THEIR WORDS. Some position \
lines carry a QUOTE_VERBATIM line: the scholar's OWN words, verbatim from the cited \
publication. When the position you are stating has one, PREFER quoting it (whole or \
as a continuous excerpt — never a spliced patchwork) over paraphrasing, with the \
citation and page: 'Bobzien is explicit: "…" [P_<id>: Bobzien 1998, p. 133]'. A real \
quotation with a page reference is worth more to a specialist reader than any \
paraphrase. Quote each QUOTE_VERBATIM at most once, where it carries most weight.

NODE IDENTIFIERS ARE PROVENANCE MARKERS, NEVER QUOTABLE TEXT. An id or slug \
(``argument_frede_2011_alexander_libertarian_dead_end``, ``P_…``, ``passage_…``) is a \
database handle, not anybody's words: never lift a word or phrase out of one and \
present it as a scholar's expression. You may quote a scholar ONLY with words that \
appear verbatim inside that position's QUOTE_VERBATIM line in the map. If a position \
has no QUOTE_VERBATIM line, attribute it as paraphrase ("Frede regards it as a dead \
end") — never as "in his phrase", "his term", "what he calls", or inside quotation \
marks.

OUTPUT ONLY THE FINISHED SCHOLARLY PROSE. Do NOT narrate your process. Never write \
"Let me check", "Let's double-check the Greek", "Matches the text", "I will now", \
"First, I…", "Verifying…", or any self-check / meta-commentary. Your reasoning is \
private scratch; the reader sees only the essay.\
"""

# The reasoning steps are MANDATED in the user prompt so they drive reasoning_content
# on K2.x (the model weighs before writing).
DIALECTICAL_SYNTHESIS_TEMPLATE = """\
{map_markdown}

------------------------------------------------------------------------------
REASON (this becomes your private scratch; it is not the answer):

1. SCOPE SELECTION. Identify the question's named subjects, period, passages, and \
requested comparison. Select directly relevant frames; exclude merely associated \
topics. Then perform THESIS SELECTION: state the SHAPE of the answer — which fault \
lines actually dominate the live scholarship. Then DECIDE WHAT THE QUESTION WANTS: an \
ASSESSMENT (how original / is X a Y / which reading holds / how does X compare) or a \
SURVEY ("what are the positions on…"). If it wants an assessment, settle now on the \
thesis YOU will defend and on the strongest objection you will have to answer.
2. MAP RELEVANT DISAGREEMENTS. Identify attested opposing positions only when the
question concerns an interpretive dispute. If only one position is available,
state that coverage limit where relevant; do not invent a counterpoint.
3. LOCATE THE PRIMARY ANCHOR. Per position, find the dossier passage it argues over \
and pick the STRONGEST quotable one (one carrying real original-language text, not a \
metadata block) to quote verbatim in the prose. If none, mark "interpretation without \
surfaced primary grounding" and hedge harder.
4. WEIGH — AND DETECT TALKING-PAST. Note where positions GENUINELY conflict vs. talk \
past each other (different object of choice, different dating of "the will", different \
sense of the term). Note who responds_to whom. Where the question asks for an \
assessment, weigh the readings AGAINST EACH OTHER and record which way the evidence \
leans and why; where it asks for a survey, leave the dispute open.
4bis. RANK THE SOURCES. Note every position whose citation carries a source-rank \
bracket ([MA thesis], [PhD dissertation], [online essay, not peer-reviewed]); those \
must be disclosed as such on first citation and can never carry a contested point.
4ter. HARVEST THE SCHOLAR QUOTES. List every position in your plan that carries a \
QUOTE_VERBATIM line and decide WHERE each quotation will appear in the prose — the \
scholar's own words, quoted once, at the point where that position carries weight.
5. CHECK ANACHRONISM. Flag every modern label; voice it as "what X calls…", never \
"the Stoics held compatibilism." This holds inside the Verdict too.
6. PLAN STRUCTURE FROM THE FRAMES PRESENT — one movement per fault line for a \
survey; chronological for a genealogy; point-by-point for a comparison. Never a fixed \
Definition/Textual-Basis/Counterpoint template.

------------------------------------------------------------------------------
WRITE the scholarly answer ({shape}). Be complete with respect to the QUESTION, \
not the size of the retrieved map. Respect an explicit word limit in the question. \
For a focused factual or textual question, use only the paragraphs needed to \
answer it; there is no minimum length or section count. An explicitly broad survey may be a long-form, \
example-rich essay. Do not consume the output budget for its own sake. Requirements:

- Open with a THESIS SENTENCE that answers the actual question: {question}
- One movement per relevant issue, with headings derived from the question. \
Exclude frames that do not help answer it; retrieval does not establish relevance.
- For a relevant interpretive dispute, name the contending MODERN SCHOLARS and
explain their actual disagreement. Each borrowed interpretation carries its
[P_<id>: …] marker; direct readings of ancient texts carry [passage_<id>: …].
Invoke [edge: …] only for attested relations that matter here. Use concrete
examples when they add distinct evidence; avoid repetition.
- ANCHOR primary-source claims to an exact conventional locus with the
[passage_<id>: …] marker. Quote only when the wording matters; copy any Greek or
Latin EXACTLY from the supplied passage, never reconstruct it. Preserve the
language and attribution of any published translation. Do not force extra
quotations or an edition page into a question that only needs a conventional locus.
- Where scholars genuinely conflict vs. merely talk past each other (different sense \
of "the will", different dating), SAY which — this is the scholar's added value.
- Hedge with the field's own markers ("Bobzien argues…, though Frede contends…").
- DISCLOSE SOURCE RANK on first citation of any position whose line carries a \
bracketed rank ([MA thesis], [PhD dissertation], [online essay, not peer-reviewed]), \
and never let such a source decide a contested point. An unranked position is \
UNSTATED, not established.
- For an assessment, close with a defended conclusion and its strongest relevant
objection. If the evidence underdetermines the answer, explain that limit rather
than inventing a preference. For a survey, identify the remaining open issues.
For a short textual question, answer directly without a mandatory Verdict section.

Write ONLY the essay. Do not include any planning, verification, or self-checking \
text; do not restate these instructions; do not narrate what you are doing.
{coverage_note}\
"""


# ── 2. Map serialiser (QUESTION header over the M3 edge-first frame layer) ────


def serialize_controversy_map(
    cmap: ControversyMap, *, budget_tokens: int | None = None
) -> str:
    """Render the ControversyMap as the structured markdown the prompt consumes.

    A ``## QUESTION`` header (question + detected shape) over the M3
    ``## Controversy Frames`` layer (:func:`render_controversy_frames_layer`):
    edges are explicit ``A --opposes--> B`` rows, so the prompt is structurally
    unable to be edge-blind; passages are bilingual; standalone exegesis units
    and coverage gaps follow. One serialiser, one edge-slot truth.

    ``budget_tokens`` fits the whole layer into a token budget
    (:func:`fit_controversy_frames_layer`); without it every passage still
    carries the per-passage source cap, so a full-book passage node can never
    dump a whole book into the prompt.
    """
    layer, _ = _serialize_map_with_stats(cmap, budget_tokens=budget_tokens)
    return layer


def _serialize_map_with_stats(
    cmap: ControversyMap,
    *,
    budget_tokens: int | None = None,
    relevance: Mapping[str, float] | None = None,
) -> tuple[str, dict[str, int]]:
    """:func:`serialize_controversy_map` plus the fitting stats (for the log)."""
    shape = getattr(cmap.shape, "value", cmap.shape)
    out = [f"## QUESTION  {cmap.question_frame}   (detected shape: {shape})", ""]
    if budget_tokens is None:
        frames_layer = render_controversy_frames_layer(cmap)
        stats: dict[str, int] = {}
    else:
        frames_layer, stats = fit_controversy_frames_layer(
            cmap, budget_tokens, relevance=relevance
        )
    if frames_layer:
        out.append(frames_layer)
    return "\n".join(out).rstrip() + "\n", stats


def build_synthesis_prompt(
    cmap: ControversyMap,
    *,
    budget_tier: str = "standard",
    coverage_note: str = "",
    answer_tokens: int = 0,
    relevance: Mapping[str, float] | None = None,
) -> tuple[str, PromptComposition]:
    """Assemble the dialectical synthesis user prompt UNDER the tier budget.

    THE fix for the prompt-size blowout. The tier budget
    (:func:`synthesis_context_budget`) used to govern only the context pack —
    which this prompt does not even consume — while the map it DOES consume was
    unbudgeted, so a "250k tier" query shipped a ~1.2M-token prompt. Here the
    fixed sections (system prompt, template instructions, answer reserve, safety
    margin) are priced FIRST and the map gets the remainder, floored so it can
    never collapse to nothing.

    ``relevance`` is the optional triage side dict
    (:func:`triage_controversy_map`): it only reprioritises what the fitter sheds
    first, never what the prompt says. ``None`` keeps the lexical ordering.

    Returns ``(user_prompt, composition)``; the composition carries the
    per-section token accounting for the INFO log line.
    """
    tier_budget = synthesis_context_budget(budget_tier)
    instructions = DIALECTICAL_SYNTHESIS_TEMPLATE.format(
        map_markdown="",
        shape=getattr(cmap.shape, "value", cmap.shape),
        question=cmap.question_frame,
        coverage_note=coverage_note,
    )
    comp = plan_prompt_budget(
        tier_budget=tier_budget,
        system_prompt=DIALECTICAL_SYNTHESIS_SYSTEM,
        instructions=instructions,
        answer_tokens=answer_tokens,
    )
    map_markdown, stats = _serialize_map_with_stats(
        cmap, budget_tokens=comp.variable_budget, relevance=relevance
    )
    safe_map_markdown = delimit_retrieved_text(
        map_markdown, data_id="dialectical-synthesis:controversy-map"
    )
    comp.map_tokens = estimate_tokens(safe_map_markdown)
    user_prompt = DIALECTICAL_SYNTHESIS_TEMPLATE.format(
        map_markdown=safe_map_markdown,
        shape=getattr(cmap.shape, "value", cmap.shape),
        question=cmap.question_frame,
        coverage_note=coverage_note,
    )
    logger.info(
        "%s [tier=%s, contested passages %d/%d @%s tok, exegesis %d/%d @%s tok, "
        "positions %d/%d @%s tok]",
        comp.log_line(),
        budget_tier,
        stats.get("passages_kept", 0),
        stats.get("passages_total", 0),
        stats.get("cap_tokens", 0),
        stats.get("exegesis_kept", 0),
        stats.get("exegesis_total", 0),
        stats.get("exegesis_cap_tokens", 0),
        stats.get("positions_kept", 0),
        stats.get("positions_total", 0),
        stats.get("position_cap_tokens", 0),
    )
    return user_prompt, comp


def synthesis_brief(state: Any) -> str:
    """A caller-supplied writing brief appended to the synthesis instructions.

    Read from ``state.metadata['synthesis_brief']`` (the lead-researcher
    pipeline sets it: goal, standard and the dossier inventory the writer must
    cite). Priced with the fixed instruction section, so the map budget shrinks
    by exactly its size. Empty when no brief was supplied — every other path is
    byte-for-byte unchanged.
    """
    metadata = getattr(state, "metadata", None)
    brief = metadata.get("synthesis_brief") if isinstance(metadata, dict) else None
    if not isinstance(brief, str) or not brief.strip():
        return ""
    return "\n\n" + brief.strip()


# ── 2a. Relevance triage (optional stage, between the map and the fitter) ────


async def triage_controversy_map(
    cmap: ControversyMap, llm: Any
) -> dict[str, float] | None:
    """Score the fitter's units for pertinence, or return ``None``.

    The seam for :mod:`eleutheria_graphrag.agents.relevance_triage`: runs
    BETWEEN map assembly and :func:`build_synthesis_prompt`, so the fitter can
    shed by semantic relevance instead of by round-robin position alone. Returns
    ``None`` — the "keep the existing ordering" signal — when the stage is
    disabled, when the map has nothing to score, or when every batch failed.

    NEVER raises: a triage failure must cost a slightly worse prompt ordering,
    never an answer.
    """
    if not relevance_triage_enabled():
        return None
    try:
        items = collect_triage_items(cmap)
        if not items:
            return None
        result = await score_relevance(cmap.question_frame, items, llm)
    except Exception as exc:  # noqa: BLE001 — never fail a query on triage
        logger.warning("relevance triage stage failed (%s); keeping lexical order", exc)
        return None
    return result.scores or None


# ── 3. The synthesis call (ONE LLM call) ─────────────────────────────────────


@dataclass
class SynthesisResult:
    """Output of the dialectical synthesis: prose + its parsed provenance index."""

    prose: str
    reasoning_trace: str = ""  # reasoning_content (M6); empty until then
    model_used: str = ""
    ledger: list[ClaimLedgerItem] = field(default_factory=list)
    degraded: bool = False  # True when the degraded-mode hedge produced the prose
    # F4 instrumentation: which rung of the fallback chain produced the prose
    # (0 = gpt-5.6-sol head, 1 = claude-opus-5, 2 = gemini), how many
    # rungs were tried, and whether the budget-eaten answer-only re-call fired.
    # Surfaced in state.metadata so the fallback/recovery rate is visible per
    # query WITHOUT changing the prod log level (failure-map F6).
    rung_index: int = 0
    rungs_tried: int = 1
    recovered_via_recall: bool = False
    fell_back: bool = False  # True when a rung past the primary head produced it


# M6: the synthesis fallback chain.
#
# The synthesis runs on a TRUE THINKING model: gpt-5.6-sol (Codex proxy) returns
# its chain-of-thought in ``reasoning_content`` and a CLEAN finished scholarly
# answer in ``content`` (finish_reason=stop) — so the answer budget
# (max_tokens) applies to ``content`` only and reasoning spends separate tokens.
# ``reasoning_effort`` (CODEX_REASONING_EFFORT, default "high") bounds the
# chain-of-thought so it cannot eat the whole budget.
#
# The chain degrades gpt-5.6-sol -> claude-opus-5 -> gemini-3.1-pro-preview:
# each rung is a full-quality synthesis head on a DIFFERENT provider, so an
# account-level or proxy-level outage on one cannot empty the answer.
_SCHOLAR_SYNTHESIS_DEFAULT = "gpt-5.6-sol"
# The ReAct retrieval loop shares the synthesis head (it needs tool calling,
# which both proxies support natively).
_SCHOLAR_SYNTHESIS_AGENT_LOOP_MODEL = "gpt-5.6-sol"
_SCHOLAR_SYNTHESIS_CONTENT_FALLBACK = "claude-opus-5"
#: Literal fallback for the Gemini rung, used ONLY when nothing configures the
#: provider's model. The live id comes from :func:`resolve_gemini_model`
#: (``GEMINI_MODEL``), so the rung always names a model the configured Gemini
#: backend actually serves — a proxy rung must not be asked for the native-only
#: ``-preview`` id.
_SCHOLAR_SYNTHESIS_GEMINI_FALLBACK = "gemini-3.1-pro-preview"

# Models that return their chain-of-thought in a SEPARATE ``reasoning_content``
# field, leaving ``content`` a clean finished answer. For these the defensive
# ``strip_reasoning_leak`` post-pass is a NO-OP: the content is already clean,
# so running the stripper could only risk truncating a real answer.
_REASONING_SEPARATED_MODELS: frozenset[str] = frozenset(
    {
        "gpt-5.6-sol",
        "claude-opus-5",
    }
)


def model_separates_reasoning(model_id: str) -> bool:
    """True when ``model_id`` returns its chain-of-thought in ``reasoning_content``
    (so ``content`` is already clean and ``strip_reasoning_leak`` must NOT run)."""
    if not isinstance(model_id, str):
        return False
    return model_id.strip() in _REASONING_SEPARATED_MODELS


def resolve_scholar_synthesis_model() -> str:
    """Resolve the synthesis model id.

    Reads ``SCHOLAR_SYNTHESIS_MODEL`` (form ``provider:model`` or a bare model
    id) and returns a ``model_override`` string accepted by
    ``LLMService.generate``/``stream``, which routes it by prefix
    (``gpt-*`` → Codex proxy, ``claude-*`` → Claude proxy, ``gemini-*`` →
    Gemini direct).
    """
    default = _SCHOLAR_SYNTHESIS_DEFAULT
    raw = (os.getenv("SCHOLAR_SYNTHESIS_MODEL") or "").strip()
    return raw or default


def scholar_synthesis_fallback_chain() -> list[str]:
    """The synthesis ``model_override`` fallback chain.

    ``<resolved gpt-5.6-sol> -> claude-opus-5 -> <resolved gemini>``: three
    full-quality synthesis heads on three DIFFERENT providers, so an account
    suspension or a downed proxy on one rung cannot empty the answer. The Gemini
    rung reads :func:`resolve_gemini_model` rather than a hardcoded id, so the
    override always names a model the CONFIGURED Gemini backend serves
    (subscription proxy or native API).

    The caller (M6 synthesis node) tries each override in order; each is a
    string ``LLMService.generate(model_override=...)`` already routes by
    prefix. Deduped, order preserved.
    """
    chain = [
        resolve_scholar_synthesis_model(),
        _SCHOLAR_SYNTHESIS_CONTENT_FALLBACK,
        resolve_gemini_model(_SCHOLAR_SYNTHESIS_GEMINI_FALLBACK),
    ]
    seen: set[str] = set()
    out: list[str] = []
    for m in chain:
        if m and m not in seen:
            seen.add(m)
            out.append(m)
    return out


# ── M6 budgets (ARCHITECTURE §6) — the flag-ON quality tier ──────────────────
#
# The Scholar-RAG path runs a higher tool-call budget and render-token cap than
# the legacy path. These are the §6 numbers, env-overridable. The synthesis node
# (M6 routing seam) reads them when ELEUTHERIA_SCHOLAR_RAG is on; the legacy path
# is untouched. The char-floor (graph_nodes.py:3987-3993) is REPLACED by the M4
# content gate (passes_content_gate) — length is no longer a quality proxy.

# Per-tier tool-call ceiling (raised for survey/transmission so a Bobzien⟂Frede +
# origins + Alexander + Carneadean survey can fetch its build_controversy_frame +
# bilingual read_passages calls). The real stop condition is the M5 completeness
# critic, not this blunt count.
_SCHOLAR_TOOL_CALL_BUDGETS: dict[str, int] = {
    "quick": 12,
    "standard": 24,
    "deep": 45,
}

# Per-tier synthesis render cap. >=5000 mandatory: reasoning eats the budget.
# Streaming cap must match the blocking path (the two must agree — §6); the M6
# wiring raises scholarly_agent._stream_render_max_tokens to this for flag-ON.
# Raised (F4): a thinking model shares max_tokens between reasoning_content and
# content, so a bigger total budget — together with the reasoning_effort cap
# (scholar_reasoning_effort) that bounds the chain-of-thought — leaves an
# enforced answer reserve so the primary model rarely empties.
_SCHOLAR_RENDER_TOKENS: dict[str, int] = {
    "quick": 9000,
    "standard": 12000,
    "deep": 14000,
}

# F4: the reasoning-budget cap for the thinking-model synthesis. gpt-5.6-sol on
# the Codex proxy honours a top-level ``reasoning_effort``
# ("low"|"medium"|"high"), verified live: it bounds the scratchpad so a long
# chain-of-thought cannot eat the whole ``max_tokens`` and empty the answer.
#
# By DEFAULT this returns ``None`` so the LLMService synthesis tier decides
# (``CODEX_REASONING_EFFORT``, default "high" — full academic quality).
# ``SCHOLAR_SYNTHESIS_REASONING_EFFORT`` pins it per-call when an operator wants
# to trade depth for a bigger answer reserve. The claude-opus-5 rung and the
# deterministic map hedge remain the floor.
_VALID_REASONING_EFFORTS: frozenset[str] = frozenset({"none", "low", "medium", "high"})


def scholar_reasoning_effort() -> str | None:
    """Explicit reasoning-budget cap for the synthesis, or ``None``.

    ``None`` (the default) defers to the LLMService synthesis tier. Set
    ``SCHOLAR_SYNTHESIS_REASONING_EFFORT`` to one of
    ``none|low|medium|high`` to pin it. An unrecognised value is ignored.

    NOTE — the pin only ever reaches the **Codex proxy**. LLMService resolves
    the value for any provider but attaches it exclusively for Codex
    (``LLMService._apply_reasoning_effort``): the claude-opus-5 and Gemini
    rungs of the fallback chain ignore it entirely, so lowering the effort
    here trades depth for answer budget on the primary rung ONLY. The
    reciprocal guard against a reasoning run eating the whole budget is the
    Codex synthesis ``max_tokens`` floor (``CODEX_SYNTHESIS_MAX_TOKENS``).
    """
    raw = (os.getenv("SCHOLAR_SYNTHESIS_REASONING_EFFORT") or "").strip().lower()
    if raw in _VALID_REASONING_EFFORTS:
        return raw
    return None


def scholar_tool_call_budget(budget_tier: str) -> int:
    """Flag-ON tool-call ceiling by tier (§6). ``ELEUTHERIA_SCHOLAR_MAX_TOOL_CALLS``
    overrides all tiers when set > 0."""
    raw = os.getenv("ELEUTHERIA_SCHOLAR_MAX_TOOL_CALLS")
    if raw:
        try:
            value = int(raw)
        except ValueError:
            value = 0
        if value > 0:
            return value
    return _SCHOLAR_TOOL_CALL_BUDGETS.get(budget_tier, 24)


# The synthesis runs a TRUE thinking model (gpt-5.6-sol): ~150–220 s of
# generation (large reasoning_content + answer) is normal, and a hard query can
# push past that. The shared LLM client times out at 120 s, which would cancel a
# healthy slow synthesis into the legacy facet-template fallback — the worst
# outcome. Give the synthesis LLM call a dedicated, generous per-request HTTP
# timeout (budget for up to ~300 s of generation) so it ALWAYS completes. This
# overrides ONLY the synthesis call; every other LLM call keeps the 120 s client
# timeout. ``ELEUTHERIA_SCHOLAR_SYNTHESIS_TIMEOUT`` overrides (seconds, clamped).
_SCHOLAR_SYNTHESIS_TIMEOUT_DEFAULT = 360.0


def scholar_synthesis_timeout() -> float:
    """Per-call HTTP timeout (seconds) for the dialectical synthesis LLM call.

    Defaults to 360 s — comfortably above the ~150–220 s thinking-model
    run and the ~300 s generation budget — so a slow-but-healthy synthesis is
    NEVER cut into the facet-template fallback. Override with
    ``ELEUTHERIA_SCHOLAR_SYNTHESIS_TIMEOUT`` (clamped to [120, 900])."""
    raw = os.getenv("ELEUTHERIA_SCHOLAR_SYNTHESIS_TIMEOUT")
    if raw:
        try:
            return max(120.0, min(900.0, float(raw)))
        except ValueError:
            pass
    return _SCHOLAR_SYNTHESIS_TIMEOUT_DEFAULT


def scholar_render_max_tokens(budget_tier: str) -> int:
    """Flag-ON synthesis render cap by tier (§6); clamped to [8000, 24000].

    Streaming and blocking paths MUST agree on this value (§6). Overridable with
    ``ELEUTHERIA_SCHOLAR_RENDER_MAX_TOKENS``. The ceiling was raised 20000→24000
    and the per-tier defaults lifted (F4): a thinking head shares max_tokens between
    reasoning_content and content, so a larger total budget — paired with the
    ``scholar_reasoning_effort`` cap that bounds the chain-of-thought — leaves an
    enforced answer reserve so the answer rarely empties. The claude-opus-5
    fallback rung and the deterministic map hedge remain the floor.
    """
    raw = os.getenv("ELEUTHERIA_SCHOLAR_RENDER_MAX_TOKENS")
    if raw:
        try:
            return max(8000, min(24000, int(raw)))
        except ValueError:
            pass
    return _SCHOLAR_RENDER_TOKENS.get(budget_tier, 12000)


async def synthesize_dialectical(
    state: Any,
    cmap: ControversyMap,
    llm: Any,
    *,
    max_tokens: int = 12000,  # >=5000 mandatory: reasoning eats the budget
    budget_tier: str = "standard",
) -> SynthesisResult:
    """Core G6 synthesis. Reason over the ControversyMap, emit cite-as-you-write prose.

    The live ``DialecticalSynthesis.run`` body. No facet template and no pre-built
    ledger feed it: the prose IS the source of truth; :func:`build_provenance_ledger`
    indexes it afterwards. Inputs:
      - ``cmap``: the M3 dossier (frames + exegesis units + coverage gaps), fully
        grounded, full bilingual passages, page-grounded positions, raw
        ``incident_edge_count`` order.
      - ``llm``: the shared ``LLMService``; model chosen by
        :func:`resolve_scholar_synthesis_model`.
    Output: prose + reasoning trace + the extracted ledger.

    Never raises into the pipeline: an empty/failed call yields an empty-prose
    result the caller routes to :func:`synthesize_degraded`.

    ``budget_tier`` defaults from ``state.research_plan`` (the M2 plan) when the
    caller did not pin one — so a ``deep`` plan routes to the thinking model.
    """
    if budget_tier == "standard":
        plan = getattr(state, "research_plan", None)
        plan_tier = getattr(plan, "budget_tier", None)
        if plan_tier:
            budget_tier = plan_tier

    model_chain = scholar_synthesis_fallback_chain()
    model_id = model_chain[0]

    coverage_note = ""
    if cmap.coverage_gaps:
        coverage_note = (
            "\n- One frame or more was thinly retrieved (see COVERAGE GAPS). State "
            "that coverage limit explicitly in prose; do not pad it with unrelated "
            "material."
        )
    coverage_note += synthesis_brief(state)

    # Optional relevance triage: a fast utility model scores the fitter's units
    # so the prompt keeps the MOST PERTINENT positions/passages when the budget
    # squeezes. ``None`` (stage off or failed) = the existing lexical ordering.
    relevance = await triage_controversy_map(cmap, llm)

    user_prompt, _composition = build_synthesis_prompt(
        cmap,
        budget_tier=budget_tier,
        coverage_note=coverage_note,
        answer_tokens=max_tokens,
        relevance=relevance,
    )

    reasoning_effort = scholar_reasoning_effort()

    # Try each rung of the fallback chain in order; first non-empty prose wins
    # (head is gpt-5.6-sol, a true
    # thinking model whose ``content`` is already a clean finished answer).
    prose = ""
    reasoning_trace = ""
    rung_index = 0
    rungs_tried = 0
    for idx, candidate in enumerate(model_chain):
        rungs_tried = idx + 1
        try:
            # The answer budget (max_tokens) applies to ``content`` only — thinking
            # models spend SEPARATE tokens on reasoning_content, so the answer is not
            # starved. Keep temperature at 0.3.
            # reasoning_effort bounds the thinking model's chain-of-thought so it
            # cannot eat the whole budget and empty the answer (F4); the Gemini and
            # non-reasoning content rungs simply ignore it.
            raw = await llm.generate(
                user_prompt,
                system_prompt=DIALECTICAL_SYNTHESIS_SYSTEM,
                temperature=0.3,
                max_tokens=max_tokens,
                thinking_mode=(budget_tier == "deep"),
                model_override=candidate,
                reasoning_effort=reasoning_effort,
                # Dedicated generous per-call HTTP timeout: a slow thinking-model
                # synthesis must NEVER be cut by the 120 s client timeout into the
                # facet-template fallback (see scholar_synthesis_timeout docstring).
                request_timeout=scholar_synthesis_timeout(),
            )
            prose = (raw or "").strip()
        except Exception as exc:  # pragma: no cover - defensive, never raise upstream
            logger.warning(
                "dialectical synthesis call failed on %s (%s); trying next rung",
                candidate,
                exc,
            )
            prose = ""
        if prose:
            model_id = candidate
            rung_index = idx
            # The chain-of-thought (reasoning_content) is a SIDE-CHANNEL on the
            # LLMService — route it to the trace, NEVER into the answer.
            reasoning_trace = getattr(llm, "last_reasoning_content", "") or ""
            break

    # Defensive chain-of-thought strip — ONLY for providers that inline reasoning
    # into ``content``. For a true thinking model (gpt-5.6-sol,
    # claude-opus-5) ``content`` is already clean (reasoning is in
    # reasoning_content), so the stripper is a NO-OP that could only risk
    # truncating a clean answer — skip it.
    model_used = getattr(llm, "last_model_used", "") or model_id
    if prose and not model_separates_reasoning(model_used):
        prose = strip_reasoning_leak(prose)

    ledger = build_provenance_ledger(prose, cmap) if prose else []

    if rung_index > 0 and prose:
        logger.info(
            "dialectical synthesis used fallback rung %d/%d (%s) — primary head "
            "did not produce prose",
            rung_index,
            len(model_chain),
            model_used,
        )

    return SynthesisResult(
        prose=prose,
        reasoning_trace=reasoning_trace,
        model_used=model_used,
        ledger=ledger,
        rung_index=rung_index,
        rungs_tried=max(rungs_tried, 1),
        fell_back=rung_index > 0 and bool(prose),
    )


# ── 3a. STREAMING synthesis — reasoning_content LIVE on its own channel ──────
#
# Identical inputs/prompt/budgets/timeout to ``synthesize_dialectical``, but it
# drives the LLM via ``llm.stream_segmented`` so the chain-of-thought arrives as
# deltas and can be surfaced LIVE in the AGENT REASONING workspace. The reasoning
# segments are forwarded to ``on_reasoning`` (a callback the caller wires to an
# SSE ``synthesis_reasoning`` event); the answer segments are accumulated into the
# clean ``content`` prose. The reasoning text NEVER enters the answer (separate
# channels by construction). The head emits reasoning deltas first, then content
# deltas. Same fallback chain, same 360 s timeout; on a
# rung that yields no answer it tries the next. Never raises into the pipeline.

ReasoningCallback = Callable[[str], Awaitable[None]]

# A stream is "too thin" below this many chars: it almost certainly truncated
# mid-thought (budget eaten by reasoning) rather than a finished short answer.
_THIN_PROSE_FLOOR = 400

# Appended to the user prompt on the targeted NON-STREAMING re-call when a thinking
# model burned its whole budget on reasoning_content and emitted no/too-little
# answer. It orders the model to STOP reasoning and emit the finished essay now —
# so the answer (not the scratchpad) consumes the budget on this second pass.
_STOP_REASONING_DIRECTIVE = (
    "\n\n------------------------------------------------------------------------------"
    "\nSTOP REASONING. Output ONLY the finished scholarly essay now, in full, with the "
    "inline [P_*]/[edge:*]/[passage_*] markers. Do not think further."
)


async def _recall_answer_only(
    llm: Any,
    candidate: str,
    user_prompt: str,
    *,
    max_tokens: int,
) -> str:
    """ONE targeted NON-STREAMING re-call on ``candidate`` to force a finished essay.

    The budget-eaten recovery: when a thinking model burned its whole max_tokens on
    ``reasoning_content`` and emitted no/too-thin ``content``, re-ask the SAME model
    in blocking mode with an explicit STOP-REASONING directive appended and a
    generous answer budget, so the budget now flows to the answer. Returns the
    cleaned prose (empty on any error — the caller then advances to the next rung).
    Never raises into the pipeline.
    """
    try:
        raw = await llm.generate(
            user_prompt + _STOP_REASONING_DIRECTIVE,
            system_prompt=DIALECTICAL_SYNTHESIS_SYSTEM,
            temperature=0.3,
            # A generous answer budget so the essay (not the scratchpad) fills it.
            max_tokens=max(max_tokens, 8000),
            model_override=candidate,
            # Bound the chain-of-thought on the recovery pass too, so the budget
            # flows to the answer rather than re-empting on reasoning (F4).
            reasoning_effort=scholar_reasoning_effort(),
            request_timeout=scholar_synthesis_timeout(),
        )
    except Exception as exc:  # pragma: no cover - defensive, never raise upstream
        logger.warning(
            "answer-only synthesis re-call failed on %s (%s); advancing rung",
            candidate,
            exc,
        )
        return ""
    recovered = (raw or "").strip()
    if recovered and not model_separates_reasoning(
        getattr(llm, "last_model_used", "") or candidate
    ):
        recovered = strip_reasoning_leak(recovered)
    return recovered


async def synthesize_dialectical_stream(
    state: Any,
    cmap: ControversyMap,
    llm: Any,
    *,
    on_reasoning: ReasoningCallback | None = None,
    max_tokens: int = 12000,
    budget_tier: str = "standard",
) -> SynthesisResult:
    """Streaming twin of :func:`synthesize_dialectical` (M6 live-reasoning path).

    Streams the synthesis so ``reasoning_content`` deltas can be surfaced LIVE.
    For each reasoning delta, ``on_reasoning(delta)`` is awaited (the caller emits
    a ``synthesis_reasoning`` SSE event); answer deltas are accumulated into the
    final prose. Returns the same :class:`SynthesisResult` as the blocking path
    (prose = the streamed ``content`` ONLY; reasoning_trace = the full
    chain-of-thought). The reasoning text is held STRICTLY apart from the answer.
    """
    if budget_tier == "standard":
        plan = getattr(state, "research_plan", None)
        plan_tier = getattr(plan, "budget_tier", None)
        if plan_tier:
            budget_tier = plan_tier

    model_chain = scholar_synthesis_fallback_chain()
    model_id = model_chain[0]

    coverage_note = ""
    if cmap.coverage_gaps:
        coverage_note = (
            "\n- One frame or more was thinly retrieved (see COVERAGE GAPS). State "
            "that coverage limit explicitly in prose; do not pad it with unrelated "
            "material."
        )
    coverage_note += synthesis_brief(state)

    # Optional relevance triage: a fast utility model scores the fitter's units
    # so the prompt keeps the MOST PERTINENT positions/passages when the budget
    # squeezes. ``None`` (stage off or failed) = the existing lexical ordering.
    relevance = await triage_controversy_map(cmap, llm)

    user_prompt, _composition = build_synthesis_prompt(
        cmap,
        budget_tier=budget_tier,
        coverage_note=coverage_note,
        answer_tokens=max_tokens,
        relevance=relevance,
    )

    reasoning_effort = scholar_reasoning_effort()

    prose = ""
    reasoning_trace = ""
    rung_index = 0
    rungs_tried = 0
    recovered_via_recall = False
    for idx, candidate in enumerate(model_chain):
        rungs_tried = idx + 1
        answer_parts: list[str] = []
        reasoning_parts: list[str] = []
        try:
            async for channel, delta in llm.stream_segmented(
                user_prompt,
                system_prompt=DIALECTICAL_SYNTHESIS_SYSTEM,
                temperature=0.3,
                max_tokens=max_tokens,
                model_override=candidate,
                reasoning_effort=reasoning_effort,
                request_timeout=scholar_synthesis_timeout(),
            ):
                if channel == "reasoning":
                    # LIVE reasoning — surface on its OWN channel, NEVER the answer.
                    reasoning_parts.append(delta)
                    if on_reasoning is not None and delta:
                        await on_reasoning(delta)
                elif channel == "answer" and delta:
                    answer_parts.append(delta)
        except Exception as exc:  # pragma: no cover - defensive, never raise upstream
            logger.warning(
                "dialectical streaming synthesis errored on %s (%s); "
                "salvaging %d streamed answer chars",
                candidate,
                exc,
                sum(len(p) for p in answer_parts),
            )
        # Salvage whatever streamed BEFORE the error: a late-stream failure (e.g.
        # a malformed final chunk) must never discard a fully-streamed answer.
        prose = "".join(answer_parts).strip()
        candidate_reasoning = "".join(reasoning_parts) or (
            getattr(llm, "last_reasoning_content", "") or ""
        )

        # Budget-eaten signature: a thinking model shares max_tokens
        # between reasoning_content and content. When reasoning ran long, the
        # answer comes back EMPTY or TOO THIN while reasoning is non-empty (and
        # finish_reason == "length"). One targeted NON-STREAMING re-call on the
        # SAME candidate, ordering it to STOP reasoning and emit the essay now,
        # recovers the head's quality before advancing to the next rung.
        too_thin = len(prose) < _THIN_PROSE_FLOOR
        had_reasoning = bool(candidate_reasoning.strip())
        budget_eaten = (getattr(llm, "last_finish_reason", "") == "length") or (
            too_thin and had_reasoning
        )
        if too_thin and had_reasoning and budget_eaten:
            recovered = await _recall_answer_only(
                llm,
                candidate,
                user_prompt,
                max_tokens=max_tokens,
            )
            if recovered:
                logger.info(
                    "dialectical synthesis recovered %d chars via answer-only "
                    "re-call on %s (reasoning had eaten the budget)",
                    len(recovered),
                    candidate,
                )
                prose = recovered
                recovered_via_recall = True

        if prose:
            model_id = candidate
            rung_index = idx
            # Prefer the accumulated reasoning deltas; fall back to the
            # side-channel the segmented stream also populates.
            reasoning_trace = candidate_reasoning
            break

    model_used = getattr(llm, "last_model_used", "") or model_id
    # The answer is ``content`` only. For a reasoning-separated model the content
    # is already clean; for any other rung run the defensive stripper.
    if prose and not model_separates_reasoning(model_used):
        prose = strip_reasoning_leak(prose)

    ledger = build_provenance_ledger(prose, cmap) if prose else []

    if (rung_index > 0 or recovered_via_recall) and prose:
        logger.info(
            "dialectical streaming synthesis: rung %d/%d (%s), recall=%s",
            rung_index,
            len(model_chain),
            model_used,
            recovered_via_recall,
        )

    return SynthesisResult(
        prose=prose,
        reasoning_trace=reasoning_trace,
        model_used=model_used,
        ledger=ledger,
        rung_index=rung_index,
        rungs_tried=max(rungs_tried, 1),
        recovered_via_recall=recovered_via_recall,
        fell_back=rung_index > 0 and bool(prose),
    )


# ── 3b. Defensive chain-of-thought stripper (the reasoning-leak post-clean) ──
#
# Even with the prompt forbidding it, K2.x sometimes emits a trailing self-check
# ("Let's double check the Greek quotes… Matches the text.") or a leading planning
# preamble. This deterministic post-pass cuts those so they never reach the reader.
# It is conservative: it only removes lines/blocks that are unmistakably meta — a
# scholarly sentence about Bobzien is never touched.

# Phrases that open a meta-reasoning / self-verification block (case-insensitive,
# matched at the START of a line/sentence). Kept tight to avoid eating real prose.
_REASONING_LEAK_OPENERS: tuple[str, ...] = (
    "let's double",
    "let's check",
    "let's verify",
    "let me double",
    "let me check",
    "let me verify",
    "let me confirm",
    "let me re-read",
    "let me reread",
    "let me make sure",
    "let me ensure",
    "i'll double",
    "i will double",
    "i'll verify",
    "i will verify",
    "i'll check",
    "i will check",
    "now let me",
    "now i'll",
    "now i will",
    "first, i",
    "first i'll",
    "verifying the",
    "checking the",
    "double-checking",
    "double checking",
    "to verify",
    "as a check",
    "self-check",
    "(checking",
)

# Short trailing confirmations the model emits after a self-check.
_REASONING_LEAK_CONFIRMATIONS: tuple[str, ...] = (
    "matches the text",
    "matches the passage",
    "this matches",
    "that matches",
    "the quote matches",
    "all citations resolve",
    "all markers resolve",
    "everything checks out",
    "looks correct",
    "looks good",
    "the greek is correct",
    "the latin is correct",
    "verified.",
    "confirmed.",
)

_LEAK_HEADING_RE = re.compile(
    r"^\s*#{0,6}\s*(verification|self-?check|fact[- ]?check|checks?|"
    r"double[- ]?check|notes? to self|sanity check)\b",
    re.IGNORECASE,
)


def _is_reasoning_leak_line(line: str) -> bool:
    stripped = line.strip().lstrip("-*>").strip()
    if not stripped:
        return False
    low = stripped.lower()
    if _LEAK_HEADING_RE.match(line):
        return True
    if any(low.startswith(opener) for opener in _REASONING_LEAK_OPENERS):
        return True
    # A short line (not a real scholarly sentence) that is a bare confirmation.
    return len(stripped) <= 80 and any(
        conf in low for conf in _REASONING_LEAK_CONFIRMATIONS
    )


def strip_reasoning_leak(prose: str) -> str:
    """Cut residual chain-of-thought / self-verification from the finished prose.

    Defensive: the prompt already forbids meta-reasoning, but K2.x occasionally
    leaks a trailing "Let's double check the Greek… Matches the text." block or a
    leading "First, I'll…" preamble. This removes such lines/blocks
    deterministically. A genuine scholarly sentence (about a scholar, a text, a
    fault line) is never matched. Idempotent; never raises.
    """
    if not prose or not prose.strip():
        return prose
    lines = prose.splitlines()
    kept: list[str] = []
    in_leak_block = False
    for line in lines:
        if _is_reasoning_leak_line(line):
            # Open a leak block: drop this line and following non-blank lines that
            # are themselves meta or short confirmations, until a blank line or a
            # line that is clearly real prose (carries a citation marker / >100 ch).
            in_leak_block = True
            continue
        if in_leak_block:
            low = line.strip().lower()
            if not low:
                in_leak_block = False  # blank line closes the leak block
                continue
            # Real prose resumes (citation marker or a substantial sentence): keep.
            if (
                "[p_" in low
                or "[passage_" in low
                or "[edge" in low
                or "-->" in low
                or len(line.strip()) > 100
            ):
                in_leak_block = False
                kept.append(line)
                continue
            # Still inside the meta block — drop short bridging confirmations.
            if _is_reasoning_leak_line(line) or len(line.strip()) <= 80:
                continue
            in_leak_block = False
            kept.append(line)
        else:
            kept.append(line)
    cleaned = "\n".join(kept)
    # Collapse the runs of blank lines the excisions may have left.
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


# ── 4. Provenance ledger as a BYPRODUCT (reverses F8) — deterministic post-pass


# The edge body is read by the ONE shared parser (:mod:`edge_markers`): it
# tolerates the spellings the models actually produce (spaces around the
# arrow, a line break inside the marker, ``-->``/``→``, a hyphenated relation,
# punctuation before the bracket) so the ledger, the content gate and the
# referee resolve exactly the links the publication scrubber removes.
_MARKER_RE = re.compile(r"\[(?P<kind>P|[Ee]dge|EDGE|passage)_?(?P<body>[^\]]+)\]")

# Modern-label lexicon (MEMORY Phase 11/12). Tags claims as needing attribution;
# the M5 anti-anachronism gate consumes the same list.
ANACHRONISTIC_LEXICON: tuple[str, ...] = (
    "libertarian",
    "compatibilism",
    "compatibilist",
    "incompatibilism",
    "incompatibilist",
    "hard determinism",
    "soft determinism",
    "the will",
    "free-will problem",
    "free will problem",
    "invention of the will",
    "indeterminist",
)


def _classify_claim(sentence: str, kind: str) -> str:
    """Tag each extracted claim so the M5 referee applies the right type rules."""
    low = sentence.lower()
    if kind == "passage":
        return "assertion"  # grounded-in-text; substring + NLI check downstream
    if kind in {"P", "edge"}:
        return "attributed_position"
    if any(tok in low for tok in ANACHRONISTIC_LEXICON):
        return "interpretation"
    return "interpretation"


# A marker the model wrapped over a line break (``[edge: opposes\nP_a->P_b]``).
# Sentence splitting cuts on newlines, so the marker is re-joined first or it
# would straddle two units and every marker-reading consumer would miss it.
_WRAPPED_MARKER_RE = re.compile(r"\[(?:P|[Ee]dge|EDGE|passage)_?[^\[\]]*\n[^\[\]]*\]")


def _unwrap_markers(prose: str) -> str:
    return _WRAPPED_MARKER_RE.sub(lambda m: re.sub(r"\s*\n\s*", " ", m.group(0)), prose)


def _split_sentences(prose: str) -> list[str]:
    """Split prose into ledger units. Cheap, deterministic.

    Splits on newlines AS WELL AS sentence boundaries. List-shaped prose (the
    deterministic map hedge is bullet lines with no terminal punctuation) would
    otherwise collapse into ONE unit, so every passage id in the block would be
    checked against every quote in the block and the quote gate would drop
    every citation as INSUFFICIENT. A marker wrapped over a line break is
    re-joined first (whitespace only — the publication gate matches ledger
    claims to prose sentences whitespace-insensitively).
    """
    parts = re.split(r"\n+|(?<=[.!?])\s+(?=[A-ZΑ-Ω])", _unwrap_markers(prose))
    return [p.strip() for p in parts if p and p.strip()]


def _edge_marker_key(body: str) -> tuple[str, str, str] | None:
    """``(relation, from_id, to_id)`` of a marker body, or ``None``.

    Thin wrapper over :func:`edge_markers.parse_edge_marker` so the ledger and
    the referee share one grammar with the publication scrubber.
    """
    edge = parse_edge_marker(body)
    return edge.key if edge is not None else None


def _attested_edge_index(cmap: ControversyMap) -> dict[tuple[str, str, str], str]:
    index: dict[tuple[str, str, str], str] = {}
    for frame in cmap.frames:
        for link in frame.links:
            if not getattr(link, "attested", True):
                continue
            key = (normalise_relation(link.relation), link.from_id, link.to_id)
            index[key] = getattr(link, "edge_id", "") or "|".join(key)
    return index


def _has_attested_arrow(prose: str, cmap: ControversyMap) -> bool:
    """Whether prose contains an arrow row matching an attested map link."""

    return _count_attested_arrows(prose, cmap) > 0


def _count_attested_arrows(prose: str, cmap: ControversyMap) -> int:
    """How many attested map links prose invokes as ``A --relation--> B`` rows.

    Counts LINKS, not rows: a link written twice is one fault line invoked.
    """

    count = 0
    for frame in cmap.frames:
        positions = {position.position_id: position for position in frame.positions}
        for link in frame.links:
            if not getattr(link, "attested", True):
                continue
            source = positions.get(link.from_id)
            target = positions.get(link.to_id)
            source_names = {
                link.from_id,
                getattr(link, "from_holder", ""),
                getattr(source, "holder", ""),
            }
            target_names = {
                link.to_id,
                getattr(link, "to_holder", ""),
                getattr(target, "holder", ""),
            }
            for source_name in filter(None, source_names):
                for target_name in filter(None, target_names):
                    pattern = (
                        rf"{re.escape(source_name)}\s*--\s*"
                        rf"{re.escape(link.relation)}\s*-->\s*"
                        rf"{re.escape(target_name)}"
                    )
                    if re.search(pattern, prose, re.IGNORECASE):
                        count += 1
                        break
                else:
                    continue
                break
    return count


def position_marker_id(pos: GroundedPosition) -> str:
    """The STABLE inline-marker id for a position (``[P_<id>]``).

    This is the only place the raw ``position_id`` is allowed to surface: it
    keeps the inline cite-as-you-write marker stable and clickable. The
    human-readable reference (:func:`format_scholar_reference`) must NEVER leak
    this id — see B4.
    """
    return pos.position_id or ""


def format_scholar_reference(pos: GroundedPosition) -> str:
    """A human-readable modern-scholarship reference for a position.

    "<Holder>, <Publication>, <page>" using only what the map carries (never
    invents a page). Used to make scholar positions FIRST-CLASS CITABLE items in
    the citation payload (the frontend CitationGenerator can export them), not
    only ancient passages.

    Returns ``""`` (NOT the ``position_id``) when nothing human-readable is
    available — a raw node id must never leak into a citation label. Callers
    decide what to do with an empty reference (resolve elsewhere, or omit).
    """
    holder = (pos.holder or "").strip()
    parts: list[str] = [holder] if holder else []
    if pos.publication:
        parts.append(pos.publication.strip())
    if pos.page_grounding:
        parts.append(pos.page_grounding.strip())
    return ", ".join(p for p in parts if p)


def _quoted_ancient_runs(sentence: str) -> list[str]:
    """Ancient-language runs QUOTED in ``sentence`` (inline markers stripped).

    Reuses the deterministic extractors of :mod:`text_verifier`: Greek runs plus
    quoted Latin-script spans that pass its candidate-Latin heuristic. The
    ``[P_*]``/``[edge:*]``/``[passage_*]`` markers are removed first — an author
    or work name inside a marker is metadata, not quoted text. 1-2-word
    vocabulary (:func:`is_known_term`) is a free pass: a technical term used in
    prose is not a quotation of the cited passage.
    """
    body = _MARKER_RE.sub(" ", sentence)
    runs = [text for text, _ in extract_greek_runs(body)]
    runs += [text for text, _ in extract_quoted_latin_spans(body)]
    return [run for run in runs if not is_known_term(run)]


def _run_contained_in(runs: list[str], original_text: str) -> bool:
    """True when at least one quoted run is verbatim in ``original_text``.

    Same accent-/sigma-/punctuation-insensitive, word-boundary-aligned compare
    the text verifier uses (``fold_ancient_text`` + ``contains_word_bounded``),
    with ellipsis-elided quotations handled segment-by-segment. Fails CLOSED: an
    empty ``original_text`` (a metadata-only passage ref) can never support
    quoted ancient text.
    """
    folded_source = fold_ancient_text(original_text or "")
    if not folded_source:
        return False
    for run in runs:
        segments = _folded_segments(run)
        if segments and all(
            contains_word_bounded(folded_source, segment) for segment in segments
        ):
            return True
    return False


def build_provenance_ledger(prose: str, cmap: ControversyMap) -> list[ClaimLedgerItem]:
    """Parse inline ``[P_*]``/``[edge:*]``/``[passage_*]`` markers out of the
    finished prose and resolve each to its ControversyMap entry.

    Emits a :class:`ClaimLedgerItem` list for the UI reference map and the M5
    referee. Markers resolving to a real map id become ``SUPPORTED``; markers that
    DON'T resolve are emitted ``UNVERIFIED`` (a hallucinated id) for the referee to
    hard-reject. The prose is the source of truth; this is its index.

    A resolving id alone is NOT provenance: for a ``[passage_*]`` marker whose
    sentence QUOTES ancient text, that text must be contained verbatim in the
    resolved passage's ``original_text`` (deterministic fold-compare). A miss is
    emitted ``INSUFFICIENT`` at confidence 0.0 so the citation is dropped
    downstream — LLM-composed Greek/Latin can never ship as a verified citation.
    """
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
        passage_by_id[pid] = pr
    attested_edges = _attested_edge_index(cmap)

    items: list[ClaimLedgerItem] = []
    for sentence in _split_sentences(prose):
        for m in _MARKER_RE.finditer(sentence):
            kind = m.group("kind")
            if kind.lower() == "edge":
                kind = "edge"
            body = m.group("body").strip()
            # body forms:  P_<id>: ...   |  edge: <rel> ...   |  passage_<id>: ...
            ref_id = body.split(":", 1)[0].strip().lstrip("_")
            evidence_class = _classify_claim(sentence, kind)

            resolved = False
            quote_mismatch = False
            quote_original: str | None = None
            quote_translation: str | None = None
            evidence_ids: list[str] = []

            if (
                kind == "P"
                and ref_id in pos_by_id
                and pos_by_id[ref_id].evidence_tier == "citable"
            ):
                resolved = True
                pos = pos_by_id[ref_id]
                # The claim belongs to the position record, not to a generic
                # biography of its holder. CitationVerifierV2 re-fetches this
                # position id and requires its publication + page evidence.
                evidence_ids = [pos.position_id]
                # Carry the modern-scholarship reference so the citation payload
                # can surface it as a FIRST-CLASS citable item (scholar+work+page),
                # not only ancient passages. quote_translation is the UI's display
                # string; for a position it holds the formatted scholar reference.
                quote_translation = format_scholar_reference(pos)
            elif (
                kind == "passage"
                and ref_id in passage_by_id
                and passage_by_id[ref_id].evidence_tier == "citable"
            ):
                resolved = True
                pr = passage_by_id[ref_id]
                evidence_ids = [pr.passage_id]
                quote_original = pr.original_text  # FULL, not truncated
                quote_translation = pr.english_text
                # ANTI-HALLUCINATION GATE. A resolving id is NOT provenance: the
                # Greek/Latin the sentence actually quotes must be present
                # verbatim in THIS passage's original text. On a miss the item is
                # emitted INSUFFICIENT with confidence 0.0, so _dialectical_citations
                # (SUPPORTED-only) drops the bogus citation. Sentences with no
                # ancient-language run are metadata-level claims — left untouched.
                quoted_runs = _quoted_ancient_runs(sentence)
                if quoted_runs and not _run_contained_in(quoted_runs, pr.original_text):
                    quote_mismatch = True
                    logger.warning(
                        "Provenance ledger: quoted ancient text not contained in "
                        "passage %s — dropping citation (quoted: %r)",
                        pr.passage_id,
                        quoted_runs[0][:80],
                    )
            elif kind == "edge":
                edge_key = _edge_marker_key(body)
                if edge_key in attested_edges:
                    resolved = True
                    evidence_ids = [attested_edges[edge_key]]

            items.append(
                ClaimLedgerItem(
                    claim=sentence,
                    evidence_ids=evidence_ids,
                    evidence_class=evidence_class,
                    quote_original=quote_original,
                    quote_translation=quote_translation,
                    support_type=(
                        "passage"
                        if kind == "passage"
                        else ("edge" if kind == "edge" else "position")
                    ),
                    confidence=0.8 if (resolved and not quote_mismatch) else 0.0,
                    status=(
                        ClaimStatus.INSUFFICIENT
                        if quote_mismatch
                        else (
                            ClaimStatus.SUPPORTED
                            if resolved
                            else ClaimStatus.UNVERIFIED
                        )
                    ),
                )
            )
    return items


# ── 5. Content gate — a SUBSTANCE gate (replaces the ~10k-char floor, F4/F9) ──
#
# The gate answers one question: does this prose carry enough evidence that
# RESOLVES through the ControversyMap to be worth auditing? It is not a style
# check. An earlier version also demanded ≥1 attested fault line ([edge:…] or an
# ``A --rel--> B`` row matching an attested link). That requirement was a
# template artefact, not a safety property: fabrication is caught by the ledger
# (an unresolvable marker never counts), the ancient-text verifier and the
# citation judge. It blocked a fully cited lead answer whose facet frames only
# carried unattested tension links. The fault line is now a recorded metric.

#: One precise primary locus can support a focused textual answer. A citation
#: count is not an academic authenticity test; every cited claim is audited next.
CONTENT_GATE_MIN_RESOLVED_FLOOR = 1
#: Default share of the answer's markers that must resolve (see the env override).
CONTENT_GATE_MIN_RESOLVED_RATIO = 0.25
#: ``content_gate.warnings`` entry when the prose invokes no attested fault line.
NO_ATTESTED_FAULT_LINE = "no_attested_fault_line"


def content_gate_min_resolved_ratio() -> float:
    """Share of markers that must resolve — ``ELEUTHERIA_CONTENT_GATE_MIN_RESOLVED_RATIO``.

    Defaults to :data:`CONTENT_GATE_MIN_RESOLVED_RATIO`; an unparsable or
    out-of-range value (outside ``0..1``) keeps the default.
    """
    raw = (os.getenv("ELEUTHERIA_CONTENT_GATE_MIN_RESOLVED_RATIO") or "").strip()
    if not raw:
        return CONTENT_GATE_MIN_RESOLVED_RATIO
    try:
        value = float(raw)
    except ValueError:
        return CONTENT_GATE_MIN_RESOLVED_RATIO
    if not 0.0 <= value <= 1.0:
        return CONTENT_GATE_MIN_RESOLVED_RATIO
    return value


def content_gate_min_resolved(total_markers: int) -> int:
    """``max(1, ceil(ratio * total_markers))`` — the resolved-marker threshold."""
    return max(
        CONTENT_GATE_MIN_RESOLVED_FLOOR,
        math.ceil(content_gate_min_resolved_ratio() * max(0, total_markers)),
    )


@dataclass(frozen=True)
class ContentGateResult:
    """The substance gate's verdict plus the counts it was decided on."""

    passed: bool
    #: ``None`` on a pass; otherwise ``template_detected`` |
    #: ``empty_prose`` | ``no_grounded_passage`` | ``too_few_resolved_markers``.
    reason: str | None
    total_markers: int
    #: SUPPORTED passage or position ledger items (edges never count here).
    resolved_markers: int
    min_resolved: int
    grounded_passages: int
    #: Fault lines the prose invokes at all: ``[edge:…]`` markers + attested
    #: arrow rows. ``attested_edges_invoked`` keeps only those the map attests.
    dialectical_edges_invoked: int
    attested_edges_invoked: int
    warnings: tuple[str, ...] = ()

    def as_record(self) -> dict[str, Any]:
        """The fields the pipeline records under ``metadata.content_gate``."""
        return {
            "total_markers": self.total_markers,
            "resolved_markers": self.resolved_markers,
            "min_resolved": self.min_resolved,
            "grounded_passages": self.grounded_passages,
            "dialectical_edges_invoked": self.dialectical_edges_invoked,
            "attested_edges_invoked": self.attested_edges_invoked,
            "warnings": list(self.warnings),
        }


def evaluate_content_gate(
    prose: str,
    cmap: ControversyMap,
    *,
    ledger: list[ClaimLedgerItem] | None = None,
) -> ContentGateResult:
    """Decide the SUBSTANCE gate over prose and its map (ARCHITECTURE §4.5).

    Passes when, in this order of rejection:

    1. the dead facet-template string is absent (``template_detected``);
    2. ≥1 primary citation RESOLVES to a passage in ``cmap`` — a fabricated
       ``[passage_…]`` id never counts (``no_grounded_passage``);
    3. ≥ :func:`content_gate_min_resolved` markers resolve — SUPPORTED passage
       or position items, so a paste of invented ids fails however long it is
       (``too_few_resolved_markers``).

    A correct 600-word survey passes; a node-paste template never does. An
    answer that invokes no attested fault line still passes: the count is
    recorded and :data:`NO_ATTESTED_FAULT_LINE` is appended to ``warnings``.
    ``ledger`` lets a caller that already rebuilt the ledger avoid a second parse.
    """
    if not prose.strip():
        return ContentGateResult(
            passed=False,
            reason="empty_prose",
            total_markers=0,
            resolved_markers=0,
            min_resolved=content_gate_min_resolved(0),
            grounded_passages=0,
            dialectical_edges_invoked=0,
            attested_edges_invoked=0,
            warnings=(NO_ATTESTED_FAULT_LINE,),
        )
    template_detected = "frames the issue as" in prose
    items = build_provenance_ledger(prose, cmap) if ledger is None else ledger
    total_markers = len(items)
    grounded_passages = sum(
        1
        for item in items
        if item.support_type == "passage" and item.status == ClaimStatus.SUPPORTED
    )
    resolved_markers = grounded_passages + sum(
        1
        for item in items
        if item.support_type == "position" and item.status == ClaimStatus.SUPPORTED
    )
    edge_items = [item for item in items if item.support_type == "edge"]
    attested_arrows = _count_attested_arrows(prose, cmap)
    dialectical_edges_invoked = len(edge_items) + attested_arrows
    attested_edges_invoked = (
        sum(1 for item in edge_items if item.status == ClaimStatus.SUPPORTED)
        + attested_arrows
    )
    min_resolved = content_gate_min_resolved(total_markers)
    warnings: tuple[str, ...] = (
        (NO_ATTESTED_FAULT_LINE,) if attested_edges_invoked == 0 else ()
    )

    reason: str | None
    if template_detected:
        # the dead facet-template string must never silently pass
        reason = "template_detected"
    elif grounded_passages == 0:
        reason = "no_grounded_passage"
    elif resolved_markers < min_resolved:
        reason = "too_few_resolved_markers"
    else:
        reason = None
    return ContentGateResult(
        passed=reason is None,
        reason=reason,
        total_markers=total_markers,
        resolved_markers=resolved_markers,
        min_resolved=min_resolved,
        grounded_passages=grounded_passages,
        dialectical_edges_invoked=dialectical_edges_invoked,
        attested_edges_invoked=attested_edges_invoked,
        warnings=warnings,
    )


def passes_content_gate(prose: str, cmap: ControversyMap) -> bool:
    """Boolean form of :func:`evaluate_content_gate` (referee + tests)."""
    return evaluate_content_gate(prose, cmap).passed


# ── 6. Degraded mode — a reasoned hedge, NEVER a template (ARCHITECTURE §4.5) ─


async def synthesize_degraded(cmap: ControversyMap, llm: Any) -> str:
    """When synthesis fails or the content gate trips: a SHORTER reasoned answer
    over whatever frames assembled, explicitly stating its coverage limit in prose.

    Never a node-paste (this is the ``_render_answer_fallback`` replacement). On any
    LLM error returns an honest empty string for the caller to surface — still never
    a template.
    """
    gaps = "; ".join(cmap.coverage_gaps) if cmap.coverage_gaps else "none recorded"
    # The hedge is the SAFETY BELT: it must not be able to overflow the window
    # the head just overflowed. Budget it like the head, minus its answer cap.
    hedge_budget = plan_prompt_budget(
        tier_budget=synthesis_context_budget("quick"),
        system_prompt=DIALECTICAL_SYNTHESIS_SYSTEM,
        instructions="",
        answer_tokens=4000,
    )
    degraded_prompt = (
        delimit_retrieved_text(
            serialize_controversy_map(cmap, budget_tokens=hedge_budget.variable_budget),
            data_id="dialectical-synthesis:degraded-map",
        )
        + "\n\nWrite a SHORT, honest scholarly answer over only the frames that "
        "assembled. State explicitly which fault lines were thinly covered in this "
        f"run (gaps: {gaps}). Attribute every position; ground in quoted text where "
        "available; do not pad. This is a scholar's hedge, not a survey."
    )
    # The safety belt must NOT empty the same way the head did. A thinking head
    # shares max_tokens between reasoning_content and content, so a hedge on it can
    # be eaten by reasoning exactly like the head. Use the CONTENT (non-reasoning)
    # model — its whole budget goes to ``content`` — with a real answer budget.
    model_id = _SCHOLAR_SYNTHESIS_CONTENT_FALLBACK
    try:
        raw = await llm.generate(
            degraded_prompt,
            system_prompt=DIALECTICAL_SYNTHESIS_SYSTEM,
            temperature=0.3,
            max_tokens=4000,
            model_override=model_id,
            reasoning_effort=scholar_reasoning_effort(),
            request_timeout=scholar_synthesis_timeout(),
        )
        return strip_reasoning_leak((raw or "").strip())
    except Exception as exc:  # pragma: no cover - defensive, never raise upstream
        logger.warning("degraded synthesis call failed (%s); empty result", exc)
        return ""


# ── 7. Deterministic map-derived hedge — the FINAL non-empty guarantee ────────
#
# The absolute floor of the synthesis-robustness guarantee: NO LLM call. When a
# populated ControversyMap exists but every LLM rung AND the degraded hedge came
# back empty (e.g. both proxies 429/error and Gemini 429s too), this
# serialises the map's contending positions + their grounded passages into
# readable, attributed prose DIRECTLY — so a populated map ALWAYS yields a real
# answer instead of falling through to the legacy bare "insufficient evidence"
# sentence. Carries the inline [P_*]/[edge:*]/[passage_*] markers so
# build_provenance_ledger indexes it exactly like an LLM answer. Returns "" only
# for a genuinely empty map (no frames, no positions, no exegesis units).


def _hedge_passage_block(pr: PassageRef, *, terms: frozenset[str] = frozenset()) -> str:
    """One quoted-passage line for the deterministic hedge, with its marker.

    The hedge is READ BY A HUMAN, so the same per-passage cap applies: a
    full-book passage node contributes its relevant window (cut only at
    sentence/line boundaries), never the whole book.
    """
    who = ", ".join(p for p in (pr.author, pr.canonical_ref or pr.work) if p)
    marker = (
        f"[passage_{pr.passage_id}: {who}]" if who else f"[passage_{pr.passage_id}]"
    )
    cap = passage_token_cap()
    original, _ = excerpt_within_budget(
        (pr.original_text or "").strip(), cap, terms=terms
    )
    english, _ = excerpt_within_budget(
        (pr.english_text or "").strip(), cap, terms=terms
    )
    if original and english:
        return f'  {marker} "{original}" — "{english}"'
    if original:
        return f"  {marker} {original}"
    if english:
        return f"  {marker} {english}"
    return f"  {marker}"


def deterministic_map_hedge(cmap: ControversyMap) -> str:
    """Build a non-empty, attributed scholarly hedge directly from ``cmap`` — NO LLM.

    The final guarantee in the robustness chain: a populated map ALWAYS yields a
    real answer. Serialises each frame's contending positions (named holders, with
    their [P_*] markers and the [edge:*] disagreements between them) and the
    grounded primary passages they argue over (quoted original + English, with
    [passage_*] markers) into readable prose. Honest about being a structural
    fallback rendered without the synthesis model. Returns "" for an empty map.
    """
    has_content = any(
        frame.positions or frame.contested_passages for frame in cmap.frames
    ) or bool(cmap.exegesis_units)
    if not has_content:
        return ""

    lines: list[str] = []
    terms = query_terms(cmap.question_frame)
    question = (cmap.question_frame or "").strip()
    if question:
        lines.append(
            f"On the question — {question} — the controversy map surfaced the "
            "following contending scholarly positions and the primary texts they "
            "argue over. (This answer is a structural rendering of the assembled "
            "evidence; the synthesis model was unavailable on this run, so the "
            "fault lines are stated without further interpretive weighing.)"
        )
    else:
        lines.append(
            "The controversy map surfaced the following contending scholarly "
            "positions and the primary texts they argue over. (This answer is a "
            "structural rendering of the assembled evidence; the synthesis model "
            "was unavailable on this run.)"
        )

    for frame in cmap.frames:
        if not (frame.positions or frame.contested_passages):
            continue
        title = (frame.title or frame.frame_id or "Fault line").strip()
        lines.append("")
        lines.append(f"## {title}")

        for pos in frame.positions:
            holder = (pos.holder or "a scholar").strip()
            if pos.evidence_tier != "citable":
                lines.append(
                    f"- {holder}: {pos.evidence_notice or 'discovery-only source; not evidence'}"
                )
                continue
            marker = f"[P_{pos.position_id}: {format_scholar_reference(pos) or holder}]"
            claim = (pos.claim or "").strip()
            # An empty holder_node_id means the "holder" was derived from the
            # node's own label, not resolved to a real person — asserting that
            # such a string "holds that …" invents an attribution. Name the
            # position instead.
            attributed = bool(pos.holder_node_id)
            # Even the structural fallback discloses a curated source rank: a
            # reader must never take grey literature for peer-reviewed work.
            rank = condense_source_rank(getattr(pos, "source_rank", None))
            rank_note = f" [{rank}]" if rank else ""
            formulation_note = (
                f" [same thesis in {pos.same_thesis_formulation_count} formulations]"
                if pos.same_thesis_formulation_count > 1
                else ""
            )
            if claim and attributed:
                lines.append(
                    f"- {holder} holds that {claim}{rank_note}{formulation_note} {marker}"
                )
            elif claim:
                lines.append(
                    f"- {holder} is the position that {claim}{rank_note}"
                    f"{formulation_note} {marker}"
                )
            else:
                lines.append(
                    f"- {holder} is recorded as a contending position{rank_note}"
                    f"{formulation_note} {marker}"
                )

        for link in frame.links:
            frm = (link.from_holder or link.from_id).strip()
            to = (link.to_holder or link.to_id).strip()
            rel = (link.relation or "opposes").strip()
            if not getattr(link, "attested", True):
                lines.append(
                    f"  Unattested relationship debt retained for discovery only: "
                    f"{frm} / {rel} / {to}; it is not asserted here."
                )
                continue
            edge_marker = f"[edge: {rel} P_{link.from_id}->P_{link.to_id}]"
            gloss = f" — {link.gloss.strip()}" if link.gloss else ""
            lines.append(f"  Here {frm} {rel} {to}{gloss} {edge_marker}")

        for pr in frame.contested_passages:
            lines.append(_hedge_passage_block(pr, terms=terms))

        for pr in frame.flagged_passages:
            where = " ".join(
                part for part in (pr.author, pr.work, pr.canonical_ref) if part
            )
            lines.append(
                f"  Discovery-only text {where or pr.passage_id}: "
                f"{pr.evidence_notice or 'flagged text; do not quote'}"
            )

    if cmap.exegesis_units:
        lines.append("")
        lines.append("## Further primary evidence")
        for pr in cmap.exegesis_units:
            lines.append(_hedge_passage_block(pr, terms=terms))

    if cmap.coverage_gaps:
        lines.append("")
        gaps = "; ".join(g for g in cmap.coverage_gaps if g)
        lines.append(
            f"Coverage limit: the following fault lines were thinly retrieved on "
            f"this run — {gaps}."
        )

    return "\n".join(lines).strip()


# ── 5. The REFEREE stage (the institutionalized audit) ───────────────────────
#
# WHY THIS EXISTS. Two external audits of production answers found the SAME
# recurring defects: a mapped-but-unjudged question ("I shall argue for no
# verdict") where the question demanded a defended position; scholars exploited
# in the argument but never introduced (dangling references); camp assignments
# the cited material does not support; grey literature cited as if peer
# reviewed; announced enumerations left incomplete ("three reasons", two given);
# and loci cited where the map actually supplied the primary text. §1's prompt
# now forbids all six — but a prompt rule is a hope, not a gate.
#
# This stage turns those audit criteria into a BOUNDED post-synthesis pass:
#   1. ONE referee call on the synthesis-tier model, over the answer AS THE
#      READER WILL SEE IT (i.e. after the ancient-text gate), returning strict
#      JSON: {"passes": bool, "revisions": [{"issue", "instruction"}]} (<=5).
#   2. If it fails, ONE revision call: the synthesis model receives its own
#      answer plus the concrete instructions and returns the corrected FULL
#      answer. The revision system prompt FORBIDS new ancient-language text —
#      a revision may reorganise, complete, hedge, disclose and attribute, never
#      introduce a quotation the original answer did not already carry — and the
#      caller re-runs the deterministic text gate on the result anyway.
#
# HARD BOUNDS. Exactly one referee call and at most one revision call. Every
# failure path (timeout, transport error, malformed JSON, empty prose) KEEPS THE
# ORIGINAL ANSWER and logs a warning. The stage can improve an answer or cost
# ~1-3 min; it can never empty one.
#
# OFF BY DEFAULT: ``ELEUTHERIA_REFEREE``.

#: Hard ceiling on the revision instructions carried out of the referee. Five
#: concrete local fixes is a revision; twenty is a rewrite.
MAX_REFEREE_REVISIONS = 5

_REFEREE_TIMEOUT_DEFAULT = 90.0
_REVISION_TIMEOUT_DEFAULT = 240.0

#: Prompt budget (tokens) for the evidence dossier shown to the referee. The
#: referee needs the map to judge camp assignments and available primary texts,
#: but it reads an answer, not the whole corpus.
_REFEREE_MAP_TOKENS_DEFAULT = 30000

#: ``max_tokens`` for the referee call. The referee verdict itself is a small
#: JSON object, but the synthesis tier is a THINKING head reached through an
#: OpenAI-compatible proxy where reasoning tokens are billed INSIDE
#: ``max_tokens`` (the F4 failure mode): a modest cap let the chain-of-thought
#: eat the whole budget and the completion came back with 0 chars
#: ("referee returned unparseable output (0 chars)"). The floor here is the
#: same order as ``scholar_render_max_tokens`` so the answer reserve survives
#: the scratchpad; :data:`_REFEREE_MAX_TOKENS_RETRY_FACTOR` doubles it for the
#: single retry :func:`run_referee` fires on an empty completion.
_REFEREE_MAX_TOKENS = 12000
_REFEREE_MAX_TOKENS_RETRY_FACTOR = 2


def referee_enabled() -> bool:
    """Whether the post-synthesis referee stage runs. ``ELEUTHERIA_REFEREE``, default off."""
    return (os.getenv("ELEUTHERIA_REFEREE") or "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def referee_timeout() -> float:
    """Per-call timeout (seconds) for the referee call. Clamped to [30, 300]."""
    raw = os.getenv("ELEUTHERIA_REFEREE_TIMEOUT")
    if raw:
        try:
            return max(30.0, min(300.0, float(raw)))
        except ValueError:
            pass
    return _REFEREE_TIMEOUT_DEFAULT


def revision_timeout() -> float:
    """Per-call timeout (seconds) for the single revision call. Clamped to [60, 600]."""
    raw = os.getenv("ELEUTHERIA_REVISION_TIMEOUT")
    if raw:
        try:
            return max(60.0, min(600.0, float(raw)))
        except ValueError:
            pass
    return _REVISION_TIMEOUT_DEFAULT


def referee_map_budget() -> int:
    """Token budget for the dossier excerpt shown to the referee. [2000, 200000]."""
    raw = os.getenv("ELEUTHERIA_REFEREE_MAP_TOKENS")
    if raw:
        try:
            return max(2000, min(200000, int(raw)))
        except ValueError:
            pass
    return _REFEREE_MAP_TOKENS_DEFAULT


REFEREE_SYSTEM = """\
You are a REFEREE for a journal of ancient philosophy, reading a submitted answer \
against the evidence dossier it was written from. You do not rewrite; you return a \
verdict and, if you fail it, a short list of CONCRETE, LOCAL corrections the author \
can make without new research.

Judge the submission on exactly these six criteria:

(a) DEFENDED VERDICT. Does the question ask for an assessment, a comparison, or a \
judgement (how original / how indebted / is X a Y / which reading holds / how does X \
compare)? If so, the answer MUST close with a defended verdict: the author's own \
position, ARGUED from the mapped evidence, with the strongest objection named, \
attributed, and answered. Mapping the fault lines and then declining to judge ("I \
shall argue for no verdict") FAILS this criterion. A question that genuinely asks for \
a survey passes without a verdict.

(b) DANGLING REFERENCES. Is any scholar exploited in the argument — leaned on, \
answered, or set against another — without ever being introduced (who they are, what \
they argued, where)? A name that does real argumentative work must be introduced on \
first use.

(c) UNSUPPORTED CAMP ASSIGNMENT. Is any scholar placed in a camp, or credited with a \
thesis, that the cited material in the dossier does not support? Check every \
"X argues that…" against what the dossier records X as holding.

(d) SOURCE RANK. The dossier marks non-monograph / non-peer-reviewed sources with a \
bracketed rank after the citation ([MA thesis], [PhD dissertation], [online essay, not \
peer-reviewed]). Is each such source's rank DISCLOSED on first citation, and is it \
kept from carrying a contested point? (A source with no bracket is unstated — the \
answer must not call it peer-reviewed or standard either.)

(e) ANNOUNCED ENUMERATIONS. Where the answer announces a count ("three reasons", "two \
strands", "on four grounds"), are all the announced members actually delivered?

(f) PRIMARY TEXT. Where the dossier supplies the original-language text of a passage, \
does the answer QUOTE it (original + English) rather than merely citing the locus?

Do NOT invent defects. Do NOT ask for new research, new sources, or new quotations: \
every instruction must be satisfiable from the answer and the dossier already in \
front of you. Do NOT request stylistic changes.

Return STRICT JSON and nothing else:
{"passes": true}
or
{"passes": false, "revisions": [{"issue": "<which criterion failed, and where>", \
"instruction": "<one concrete, local correction>"}]}
At most 5 revisions, ordered by severity. No markdown fence, no commentary.\
"""

REFEREE_TEMPLATE = """\
QUESTION PUT TO THE AUTHOR:
{question}

------------------------------------------------------------------------------
EVIDENCE DOSSIER THE AUTHOR WROTE FROM (positions, dialectical edges, primary texts;
a bracketed rank after a citation is that source's bibliographic rank):

{dossier}

------------------------------------------------------------------------------
SUBMITTED ANSWER:

{answer}

------------------------------------------------------------------------------
Return the strict JSON verdict now.\
"""

REVISION_SYSTEM = """\
You are the author of the scholarly answer below, revising it after a referee report. \
Return the CORRECTED FULL ANSWER — the complete essay, not a diff, not a note on what \
you changed, not a preamble.

WHAT YOU MAY DO: reorganise; add the defended verdict the referee asked for, argued \
from material already in your answer; introduce a scholar you had left dangling; \
complete an enumeration you announced; disclose a source's rank; soften or attribute \
a claim; correct a camp assignment; move an existing quotation to where it does the \
work.

WHAT YOU MAY NOT DO — ABSOLUTE: you may NOT introduce any ancient-language text \
(Greek or Latin) that is not ALREADY PRESENT VERBATIM in the answer you are revising. \
Not a word, not a phrase, not a completion of a fragment. If a correction seems to \
require Greek or Latin you do not already have, make it in English instead. You may \
not invent a scholar, a publication, a page number, or a citation marker: reuse only \
the [P_*] / [edge:*] / [passage_*] markers already present in your answer.

Keep every existing citation marker attached to the sentence it already supports. \
Keep the anachronism discipline: modern categories stay inside attributed positions. \
Output ONLY the finished essay.\
"""

REVISION_TEMPLATE = """\
QUESTION:
{question}

------------------------------------------------------------------------------
REFEREE REPORT — apply every one of these corrections:

{instructions}

------------------------------------------------------------------------------
YOUR ANSWER, TO BE RETURNED CORRECTED IN FULL:

{answer}

------------------------------------------------------------------------------
Write the corrected full answer now. No new Greek or Latin.\
"""


@dataclass(frozen=True)
class RefereeRevision:
    """One concrete, local correction the referee asked for."""

    issue: str
    instruction: str


@dataclass
class RefereeVerdict:
    """Parsed referee output: pass/fail plus the (bounded) revision list."""

    passes: bool
    revisions: list[RefereeRevision] = field(default_factory=list)
    model_used: str = ""

    @property
    def summary(self) -> str:
        """One-line, reader-facing summary of what the referee asked for."""
        if self.passes or not self.revisions:
            return "Referee review passed: no corrections required."
        issues = "; ".join(r.issue for r in self.revisions if r.issue)
        return f"Referee review asked for {len(self.revisions)} correction(s): {issues}"


def _coerce_bool(value: Any) -> bool | None:
    """Strictly coerce a JSON ``passes`` value; ``None`` when it is not boolean-ish."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "yes", "pass", "passes"}:
            return True
        if lowered in {"false", "no", "fail", "fails"}:
            return False
    return None


def parse_referee_verdict(raw: str) -> RefereeVerdict | None:
    """Parse the referee's strict-JSON output; ``None`` when it is unusable.

    ``None`` is the KEEP-THE-ORIGINAL-ANSWER signal: a malformed verdict must
    never be read as "revise" (which would risk a rewrite driven by noise) nor
    as "pass" (which would silently claim an audit that did not happen).
    """
    from eleutheria_graphrag.services.json_extractor import (
        JSONExtractionError,
        extract_json_object,
    )

    try:
        payload = extract_json_object(raw or "")
    except JSONExtractionError, ValueError, TypeError:
        return None
    passes = _coerce_bool(payload.get("passes"))
    if passes is None:
        return None
    revisions: list[RefereeRevision] = []
    raw_revisions = payload.get("revisions")
    if isinstance(raw_revisions, list):
        for entry in raw_revisions:
            if not isinstance(entry, Mapping):
                continue
            instruction = str(entry.get("instruction") or "").strip()
            if not instruction:
                continue
            issue = str(entry.get("issue") or "").strip() or "unspecified defect"
            revisions.append(RefereeRevision(issue=issue, instruction=instruction))
            if len(revisions) >= MAX_REFEREE_REVISIONS:
                break
    # A "fail" with no actionable instruction is not actionable: treat it as a
    # pass rather than firing a revision call with an empty brief.
    if not passes and not revisions:
        passes = True
    return RefereeVerdict(passes=passes, revisions=revisions)


async def run_referee(
    question: str,
    answer_text: str,
    llm: Any,
    *,
    cmap: ControversyMap | None = None,
    model: str | None = None,
) -> RefereeVerdict | None:
    """ONE referee call over the finished answer. ``None`` = keep the original.

    Never raises: a timeout, transport error, empty response or malformed JSON
    all return ``None`` and log a warning, and the caller keeps the answer the
    synthesis produced.

    ONE exception to "one call": a completion that comes back BLANK is the F4
    signature — the synthesis tier is a thinking head whose reasoning tokens
    count inside ``max_tokens``, so the scratchpad can consume the whole
    budget and leave no content. A blank completion therefore buys exactly one
    immediate retry at :data:`_REFEREE_MAX_TOKENS_RETRY_FACTOR` × the budget.
    Every other failure still costs one call.
    """
    import asyncio

    prose = (answer_text or "").strip()
    if not prose:
        return None
    dossier = "(no structured dossier available for this run)"
    if cmap is not None:
        try:
            serialized_dossier = serialize_controversy_map(
                cmap, budget_tokens=referee_map_budget()
            ).strip()
            dossier = (
                delimit_retrieved_text(
                    serialized_dossier, data_id="dialectical-referee:dossier"
                )
                if serialized_dossier
                else dossier
            )
        except Exception as exc:  # noqa: BLE001 — the referee is best-effort
            logger.warning("referee dossier serialisation failed (%s)", exc)
    candidate = model or scholar_synthesis_fallback_chain()[0]
    user_prompt = REFEREE_TEMPLATE.format(
        question=(question or "").strip(),
        dossier=dossier,
        answer=prose,
    )
    timeout = referee_timeout()

    async def _call(budget: int) -> str:
        return await asyncio.wait_for(
            llm.generate(
                user_prompt,
                system_prompt=REFEREE_SYSTEM,
                temperature=0.0,
                max_tokens=budget,
                model_override=candidate,
                request_timeout=timeout,
            ),
            timeout=timeout,
        )

    try:
        raw = await _call(_REFEREE_MAX_TOKENS)
        verdict = parse_referee_verdict(raw or "")
        if verdict is None:
            # An empty completion and JSON truncated mid-object are the same
            # F4 failure — the thinking head spent the budget before the
            # verdict closed — so both buy the one doubled-budget retry.
            logger.warning(
                "referee completion unusable (%d chars); retrying with larger budget",
                len((raw or "").strip()),
            )
            raw = await _call(_REFEREE_MAX_TOKENS * _REFEREE_MAX_TOKENS_RETRY_FACTOR)
            verdict = parse_referee_verdict(raw or "")
    except Exception as exc:  # noqa: BLE001 — never fail an answer on the referee
        logger.warning("referee call failed (%s); keeping the original answer", exc)
        return None
    if verdict is None:
        logger.warning(
            "referee returned unparseable output (%d chars); keeping the original answer",
            len(raw or ""),
        )
        return None
    verdict.model_used = getattr(llm, "last_model_used", "") or candidate
    return verdict


async def apply_referee_revisions(
    question: str,
    answer_text: str,
    revisions: list[RefereeRevision],
    llm: Any,
    *,
    max_tokens: int = 12000,
    model: str | None = None,
) -> str:
    """ONE revision call. Returns the corrected FULL answer, or ``""`` on any failure.

    ``""`` is the KEEP-THE-ORIGINAL signal. The revision system prompt forbids
    ancient-language text absent from the original answer; the caller re-runs the
    deterministic text gate on whatever comes back regardless.
    """
    import asyncio

    prose = (answer_text or "").strip()
    if not prose or not revisions:
        return ""
    instructions = "\n".join(
        f"{i}. [{rev.issue}] {rev.instruction}"
        for i, rev in enumerate(revisions[:MAX_REFEREE_REVISIONS], start=1)
    )
    candidate = model or scholar_synthesis_fallback_chain()[0]
    user_prompt = REVISION_TEMPLATE.format(
        question=(question or "").strip(),
        instructions=instructions,
        answer=prose,
    )
    timeout = revision_timeout()
    try:
        raw = await asyncio.wait_for(
            llm.generate(
                user_prompt,
                system_prompt=REVISION_SYSTEM,
                temperature=0.2,
                # The revision re-emits the FULL answer from a thinking head
                # that spends part of max_tokens on reasoning: floor the budget
                # at the same render cap the synthesis itself was given (F4),
                # never at the old 8000 that truncated long essays.
                max_tokens=max(max_tokens, scholar_render_max_tokens("standard")),
                model_override=candidate,
                reasoning_effort=scholar_reasoning_effort(),
                request_timeout=timeout,
            ),
            timeout=timeout,
        )
    except Exception as exc:  # noqa: BLE001 — never fail an answer on the revision
        logger.warning("revision call failed (%s); keeping the original answer", exc)
        return ""
    revised = (raw or "").strip()
    if revised and not model_separates_reasoning(
        getattr(llm, "last_model_used", "") or candidate
    ):
        revised = strip_reasoning_leak(revised)
    # A revision that came back drastically shorter than the original is a
    # truncation or a refusal, not a correction — keep the original.
    if len(revised) < max(_THIN_PROSE_FLOOR, int(len(prose) * 0.5)):
        logger.warning(
            "revision returned %d chars against an original of %d; keeping the original",
            len(revised),
            len(prose),
        )
        return ""
    return revised
