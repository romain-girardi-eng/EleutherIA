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
:func:`passes_content_gate` (a CONTENT gate: ≥1 fault line + ≥1 primary cite) and
:func:`synthesize_degraded` (a prose-stated reasoned hedge — NEVER a node-paste).

VECTORLESS throughout. Greek/Latin only ever flows verbatim from the map's
passages (the prompt forbids inventing it). Gated by ``ELEUTHERIA_SCHOLAR_RAG`` at
the call site; this module is import-safe and inert until a consumer invokes it.

MODEL: Fireworks-only for now (Romain's constraint). :func:`resolve_scholar_synthesis_model`
defaults to ``fireworks:deepseek-v4-pro`` — a TRUE thinking model that returns its
chain-of-thought in ``reasoning_content`` and a clean finished answer in ``content``
(it reads ``SCHOLAR_SYNTHESIS_MODEL`` but does not enable Moonshot here). The
synthesis routes ``reasoning_content`` (a side-channel on ``LLMService``) to the
trace, NEVER into the answer; the answer is ``content`` only. The agent ReAct
retrieval loop stays on the non-reasoning k2p6 instruct model.
"""

from __future__ import annotations

import logging
import os
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from eleutheria_graphrag.agents.ancient_text_matching import (
    contains_word_bounded,
    fold_ancient_text,
)
from eleutheria_graphrag.agents.controversy_map import (
    render_controversy_frames_layer,
)
from eleutheria_graphrag.agents.state import (
    ClaimLedgerItem,
    ClaimStatus,
    ControversyMap,
    GroundedPosition,
    PassageRef,
)
from eleutheria_graphrag.agents.text_verifier import (
    _folded_segments,
    extract_greek_runs,
    extract_quoted_latin_spans,
    is_known_term,
)

logger = logging.getLogger(__name__)


# ── 1. The synthesis prompt (replaces RENDER_ANSWER_PROMPT) ──────────────────

DIALECTICAL_SYNTHESIS_SYSTEM = """\
You are a historian of ancient philosophy writing for a specialist audience \
(Cambridge-Companion register). You reason DIALECTICALLY over a CONTROVERSY MAP: a \
structured record of contending scholarly positions and the primary texts they \
fight over.

YOU ENTER A SCHOLARLY CONVERSATION. A real scholar's answer is not a summary of \
ancient doctrines — it is a DIALOGUE WITH OTHER SCHOLARS. Every interpretive move \
you make NAMES A MODERN SCHOLAR and sets their reading against another's: "Bobzien \
(1998: 234) argues … whereas Frede (2011: 44) holds …; Sharples (1983: 22) reads the \
same text differently again." You attribute every interpretive claim to a named \
scholar with a page reference, and you ground every claim about an ancient author in \
a quoted primary passage. Naming the contending scholars and their disagreement is \
NOT optional decoration — it is the substance of the answer. You hedge where the \
evidence underdetermines the question; you never adjudicate a dispute the field has \
not settled.

Modern categories — "libertarian free will", "compatibilism", "incompatibilism", \
"hard/soft determinism", "the will" as a faculty, "the free-will problem", \
"indeterminist" — are scholarly CHARACTERISATIONS. They may appear ONLY inside an \
attributed position ("what Bobzien terms…", "on Frede's reading…"), NEVER asserted \
in your own voice as ancient fact.

You never write Greek or Latin that is not present verbatim in the provided passages. \
If a phrase is not in the map, paraphrase it in English instead. You quote contested \
primary text in the original AND English at the point the scholars argue over it.

GROUND IN QUOTED PRIMARY TEXT, NOT JUST A LOCUS. The map's CONTESTED PRIMARY TEXT / \
STANDALONE PRIMARY TEXT blocks carry the original-language passage AND its English \
translation. When a position has such a passage, you MUST QUOTE THE STRONGEST one \
verbatim — original first, then the English — at the point you state that position, \
and carry its [passage_<id>: …] marker. Quoting the actual Greek/Latin (copied EXACTLY \
from the block, with its diacritics) is REQUIRED, not optional: a locus citation \
("Diss. 1.1") WITHOUT the quoted text is insufficient wherever the map supplies the \
text. Aim to quote at least two distinct primary passages per dominant fault line when \
the map provides them. Quote ONLY passages present in the map; never reconstruct or \
complete fragmentary text.

CITE AS YOU WRITE. Every interpretive sentence carries an inline marker drawn from \
the map you are given, using exactly these forms:
  [P_<id>: <holder> <year>, <publication> p.<n>]   for an attributed scholar position
  [edge: <relation> P_<from>->P_<to>]               for a dialectical link you invoke
  [passage_<id>: <author>, <ref>]                   for a quoted/cited primary passage
Every paragraph of interpretation MUST carry at least one [P_<id>: …] scholar marker. \
Use only ids that appear in the map. Never invent an id, a scholar, a publication, or \
a page number — if a position has no page in the map, cite it at work level only.

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

1. THESIS SELECTION. From the frames, state the SHAPE of the answer — which fault \
lines actually dominate the live scholarship — NOT a doctrinal verdict.
2. MAP THE FAULT LINES. Per frame: name the >=2 opposing positions and the edge that \
opposes them. A frame with only one surfaced position is incomplete — say so.
3. LOCATE THE PRIMARY ANCHOR. Per position, find the dossier passage it argues over \
and pick the STRONGEST quotable one (one carrying real original-language text, not a \
metadata block) to quote verbatim in the prose. If none, mark "interpretation without \
surfaced primary grounding" and hedge harder.
4. WEIGH, DON'T DECIDE — AND DETECT TALKING-PAST. Note where positions GENUINELY \
conflict vs. talk past each other (different object of choice, different dating of \
"the will", different sense of the term). Note who responds_to whom. DO NOT pick a \
winner.
5. CHECK ANACHRONISM. Flag every modern label; voice it as "what X calls…", never \
"the Stoics held compatibilism."
6. PLAN STRUCTURE FROM THE FRAMES PRESENT — one movement per fault line for a \
survey; chronological for a genealogy; point-by-point for a comparison. Never a fixed \
Definition/Textual-Basis/Counterpoint template.

------------------------------------------------------------------------------
WRITE the scholarly answer ({shape}). This is a FULL, DETAILED, EXAMPLE-RICH survey, \
not a sketch. Be COMPLETE: cover EVERY fault line the map contains — leave none out. \
Aim for a long-form essay (several substantial paragraphs per fault line); use the \
whole space available. Requirements:

- Open with a THESIS SENTENCE that answers the actual question: {question}
- One movement per fault line; cover ALL frames present; adaptive headings DERIVED \
FROM FRAME TITLES. Do not collapse or skip a frame.
- In EACH movement: name the contending MODERN SCHOLARS and stage their disagreement \
explicitly ("Bobzien (1998: 234) argues …, whereas Frede (2011: 44) reads … and Dihle \
(1982: 123) instead …"). Every interpretive paragraph carries ≥1 inline [P_<id>: …] \
scholar marker AS YOU WRITE IT, plus the [edge: …] for the disagreement and the \
[passage_<id>: …] for its primary anchor. Give MULTIPLE concrete examples per frame.
- QUOTE THE PRIMARY TEXT, do not just cite a locus. For each position that has a \
contested/standalone passage in the map, quote the STRONGEST one verbatim — original \
language first, then its English — with its [passage_<id>: …] marker, at the point you \
state the position. Quote at least two distinct primary passages per dominant fault \
line when the map supplies them. Copy the Greek/Latin EXACTLY from the block; never \
reconstruct or paraphrase it into the original language.
- Where scholars genuinely conflict vs. merely talk past each other (different sense \
of "the will", different dating), SAY which — this is the scholar's added value.
- Hedge with the field's own markers ("Bobzien argues…, though Frede contends…").
- Close with a synthetic conclusion stating what remains GENUINELY OPEN, and resist \
any anachronistic verdict.

Write ONLY the essay. Do not include any planning, verification, or self-checking \
text; do not restate these instructions; do not narrate what you are doing.
{coverage_note}\
"""


# ── 2. Map serialiser (QUESTION header over the M3 edge-first frame layer) ────


def serialize_controversy_map(cmap: ControversyMap) -> str:
    """Render the ControversyMap as the structured markdown the prompt consumes.

    A ``## QUESTION`` header (question + detected shape) over the M3
    ``## Controversy Frames`` layer (:func:`render_controversy_frames_layer`):
    edges are explicit ``A --opposes--> B`` rows, so the prompt is structurally
    unable to be edge-blind; passages are bilingual and untruncated; standalone
    exegesis units and coverage gaps follow. One serialiser, one edge-slot truth.
    """
    shape = getattr(cmap.shape, "value", cmap.shape)
    out = [f"## QUESTION  {cmap.question_frame}   (detected shape: {shape})", ""]
    frames_layer = render_controversy_frames_layer(cmap)
    if frames_layer:
        out.append(frames_layer)
    return "\n".join(out).rstrip() + "\n"


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
    # (0 = primary deepseek head, 1 = kimi content model, 2 = gemini), how many
    # rungs were tried, and whether the budget-eaten answer-only re-call fired.
    # Surfaced in state.metadata so the fallback/recovery rate is visible per
    # query WITHOUT changing the prod log level (failure-map F6).
    rung_index: int = 0
    rungs_tried: int = 1
    recovered_via_recall: bool = False
    fell_back: bool = False  # True when a rung past the primary head produced it


# M6: the synthesis fallback chain (ARCHITECTURE §K2.7). Fireworks-only TODAY —
# the Moonshot K2.7 rungs are commented one-line-ready (see resolve_*_model and
# scholar_synthesis_fallback_chain). The live chain degrades within Fireworks/
# Gemini, never to Moonshot, per Romain's constraint.
#
# The synthesis runs on a TRUE THINKING model: ``deepseek-v4-pro`` returns its
# chain-of-thought in ``reasoning_content`` and a CLEAN finished scholarly answer
# in ``content`` (finish_reason=stop) — fixing the k2p6 failure where a
# non-reasoning instruct model emitted its scratchpad INLINE in ``content`` and
# hit max_tokens while still planning (finish_reason=length). The answer budget
# (max_tokens) now applies to ``content`` only; reasoning spends separate tokens.
#
# ONE-LINE K2-THINKING SWAP (enable once it lands on this Fireworks account —
# kimi-k2-thinking is currently 404 here, not enabled):
#   - set _SCHOLAR_SYNTHESIS_DEFAULT = "accounts/fireworks/models/kimi-k2-thinking"
#   (it also returns reasoning_content; no other wiring change needed).
_SCHOLAR_SYNTHESIS_DEFAULT = "accounts/fireworks/models/deepseek-v4-pro"
# _SCHOLAR_SYNTHESIS_DEFAULT = "accounts/fireworks/models/kimi-k2-thinking"  # when enabled
# k2p6 (non-reasoning instruct) is kept ONLY for the agent ReAct retrieval loop,
# not for synthesis — it inlines its scratchpad into content (the root-cause bug).
_SCHOLAR_SYNTHESIS_AGENT_LOOP_MODEL = "accounts/fireworks/models/kimi-k2p7-code"
# The SECOND rung of the synthesis chain: a CONTENT (non-reasoning) model. deepseek
# shares its max_tokens between reasoning_content and content, so a long reasoning
# run can eat the whole budget → finish_reason=length with ZERO content deltas →
# empty prose. kimi-k2p7-code does NOT separate reasoning (model_separates_reasoning
# is False), so the entire budget flows to ``content`` — it RELIABLY WRITES PROSE.
# It is the real empty-answer guarantee: an empty deepseek result advances here.
# Its inline scratchpad (if any) is cleaned by strip_reasoning_leak (runs because
# model_separates_reasoning(kimi-k2p7-code) is False).
_SCHOLAR_SYNTHESIS_CONTENT_FALLBACK = "accounts/fireworks/models/kimi-k2p7-code"
_SCHOLAR_SYNTHESIS_GEMINI_FALLBACK = "gemini-3.1-pro-preview"

# Fireworks reasoning models that return their chain-of-thought in a SEPARATE
# ``reasoning_content`` field, leaving ``content`` a clean finished answer. For
# these the defensive ``strip_reasoning_leak`` post-pass is a NO-OP: the content
# is already clean, so running the stripper could only risk truncating a real
# answer. Non-reasoning models (k2p6) still get the stripper.
_REASONING_SEPARATED_MODELS: frozenset[str] = frozenset(
    {
        "accounts/fireworks/models/deepseek-v4-pro",
        "accounts/fireworks/models/kimi-k2-thinking",
    }
)


def model_separates_reasoning(model_id: str) -> bool:
    """True when ``model_id`` returns its chain-of-thought in ``reasoning_content``
    (so ``content`` is already clean and ``strip_reasoning_leak`` must NOT run)."""
    if not isinstance(model_id, str):
        return False
    return model_id.strip() in _REASONING_SEPARATED_MODELS


def resolve_scholar_synthesis_model() -> str:
    """Resolve the synthesis model id (M6 swap lands HERE, one line).

    Reads ``SCHOLAR_SYNTHESIS_MODEL`` (form ``provider:model`` or a bare model
    id). FIREWORKS-ONLY for now (Romain's constraint overrides the blueprint's
    Moonshot opt-in): any non-Fireworks request resolves to the Fireworks
    kimi-k2p6 default. Returns a ``model_override`` string accepted by
    ``LLMService.generate``/``stream`` (``accounts/fireworks/...`` → Fireworks).

    M6: lift the Fireworks guard + return ``(provider, model_id)`` once K2.7 is
    available on Fireworks. Until then this is a single-line change surface.
    """
    default = _SCHOLAR_SYNTHESIS_DEFAULT
    raw = (os.getenv("SCHOLAR_SYNTHESIS_MODEL") or "").strip()
    if not raw:
        return default
    provider, _, model_id = raw.partition(":")
    if not model_id:  # bare model id
        provider, model_id = "", provider
    if provider and provider.lower() != "fireworks":
        # Fireworks-only: ignore Moonshot/other opt-ins until M6 wires K2.7.
        logger.debug(
            "SCHOLAR_SYNTHESIS_MODEL=%s ignored (Fireworks-only); using default", raw
        )
        return default
    return model_id or default


def scholar_synthesis_fallback_chain() -> list[str]:
    """The synthesis ``model_override`` fallback chain (ARCHITECTURE §K2.7).

    TODAY, Fireworks-only (Romain's constraint — no Moonshot rung). The live chain
    is ``<resolved deepseek-v4-pro> -> fireworks/kimi-k2p7-code -> gemini-3.1-pro-preview``:
    a true thinking head (clean answer in ``content``, scratch in ``reasoning_content``)
    whose budget-eaten empty result advances to a CONTENT (non-reasoning) model that
    gives its WHOLE budget to ``content`` and reliably writes prose — the real
    empty-answer guarantee — before degrading to Gemini. Never Moonshot. When
    kimi-k2-thinking is enabled on this Fireworks account, the resolved head simply
    becomes that id.

    The caller (M6 synthesis node) tries each override in order; each is a string
    ``LLMService.generate(model_override=...)`` already routes (Fireworks ids by
    prefix, the Gemini id as a bare model). Deduped, order preserved.
    """
    chain = [
        resolve_scholar_synthesis_model(),
        _SCHOLAR_SYNTHESIS_CONTENT_FALLBACK,
        _SCHOLAR_SYNTHESIS_GEMINI_FALLBACK,
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
# Raised (F4): deepseek-v4-pro shares max_tokens between reasoning_content and
# content, so a bigger total budget — together with the reasoning_effort cap
# (scholar_reasoning_effort) that bounds the chain-of-thought — leaves an
# enforced answer reserve so the primary model rarely empties.
_SCHOLAR_RENDER_TOKENS: dict[str, int] = {
    "quick": 9000,
    "standard": 12000,
    "deep": 14000,
}

# F4: the reasoning-budget cap passed to the Fireworks thinking model so a long
# chain-of-thought cannot eat the whole max_tokens and empty the answer. Verified
# against the live Fireworks API: deepseek-v4-pro honours a top-level
# ``reasoning_effort`` ("none"|"low"|"medium"|"high"); "low" keeps the thinking
# model's quality (reasoning stays SEPARATE in reasoning_content, content stays a
# clean finished answer) while bounding the scratchpad so the answer reserve
# survives. ``SCHOLAR_SYNTHESIS_REASONING_EFFORT`` overrides; an empty/"default"
# value disables the cap (provider default). The kimi content-model fallback rung
# and the deterministic map hedge remain the floor.
_SCHOLAR_REASONING_EFFORT_DEFAULT = "low"
_VALID_REASONING_EFFORTS: frozenset[str] = frozenset({"none", "low", "medium", "high"})


def scholar_reasoning_effort() -> str | None:
    """Reasoning-budget cap for the Fireworks thinking-model synthesis (F4).

    Defaults to ``"low"`` — bounds deepseek-v4-pro's ``reasoning_content`` so it
    cannot consume the whole ``max_tokens`` and return empty ``content``. Override
    with ``SCHOLAR_SYNTHESIS_REASONING_EFFORT``; ``""``/``"default"`` returns
    ``None`` (no cap, provider default). An unrecognised value also returns the
    default. Only the Fireworks/OpenRouter payloads consume it; Gemini ignores it.
    """
    raw = (os.getenv("SCHOLAR_SYNTHESIS_REASONING_EFFORT") or "").strip().lower()
    if raw == "default":
        return None  # explicit opt-out: provider default, no cap
    if not raw:
        return _SCHOLAR_REASONING_EFFORT_DEFAULT
    if raw in _VALID_REASONING_EFFORTS:
        return raw
    return _SCHOLAR_REASONING_EFFORT_DEFAULT


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


# The synthesis runs a TRUE thinking model (deepseek-v4-pro): ~150–220 s of
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

    Defaults to 360 s — comfortably above the ~150–220 s deepseek-v4-pro thinking
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
    and the per-tier defaults lifted (F4): deepseek shares max_tokens between
    reasoning_content and content, so a larger total budget — paired with the
    ``scholar_reasoning_effort`` cap that bounds the chain-of-thought — leaves an
    enforced answer reserve so the answer rarely empties. The kimi content-model
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
        :func:`resolve_scholar_synthesis_model` (Fireworks-only for now).
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

    map_markdown = serialize_controversy_map(cmap)
    user_prompt = DIALECTICAL_SYNTHESIS_TEMPLATE.format(
        map_markdown=map_markdown,
        shape=getattr(cmap.shape, "value", cmap.shape),
        question=cmap.question_frame,
        coverage_note=coverage_note,
    )

    reasoning_effort = scholar_reasoning_effort()

    # Try each rung of the fallback chain in order; first non-empty prose wins
    # (ARCHITECTURE §K2.7 — Fireworks-only today; head is deepseek-v4-pro, a true
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
            # starved. Keep temperature at 0.3 (KIMI is clamped to 1.0 in the payload).
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
    # into ``content`` (e.g. k2p6). For a true thinking model (deepseek-v4-pro,
    # kimi-k2-thinking) ``content`` is already clean (reasoning is in
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
# channels by construction). deepseek emits reasoning deltas first, then content
# deltas. Same fallback chain (Fireworks-only today), same 360 s timeout; on a
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

    map_markdown = serialize_controversy_map(cmap)
    user_prompt = DIALECTICAL_SYNTHESIS_TEMPLATE.format(
        map_markdown=map_markdown,
        shape=getattr(cmap.shape, "value", cmap.shape),
        question=cmap.question_frame,
        coverage_note=coverage_note,
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

        # Budget-eaten signature: a thinking model (deepseek) shares max_tokens
        # between reasoning_content and content. When reasoning ran long, the
        # answer comes back EMPTY or TOO THIN while reasoning is non-empty (and
        # finish_reason == "length"). One targeted NON-STREAMING re-call on the
        # SAME candidate, ordering it to STOP reasoning and emit the essay now,
        # recovers deepseek's quality before advancing to the content rung.
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


_MARKER_RE = re.compile(r"\[(?P<kind>P|edge|passage)_?(?P<body>[^\]]+)\]")

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


def _split_sentences(prose: str) -> list[str]:
    # Cheap, deterministic. Keeps the marker attached to its sentence.
    parts = re.split(r"(?<=[.!?])\s+(?=[A-ZΑ-Ω])", prose)
    return [p.strip() for p in parts if p.strip()]


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

    items: list[ClaimLedgerItem] = []
    for sentence in _split_sentences(prose):
        for m in _MARKER_RE.finditer(sentence):
            kind = m.group("kind")
            body = m.group("body").strip()
            # body forms:  P_<id>: ...   |  edge: <rel> ...   |  passage_<id>: ...
            ref_id = body.split(":", 1)[0].strip().lstrip("_")
            evidence_class = _classify_claim(sentence, kind)

            resolved = False
            quote_mismatch = False
            quote_original: str | None = None
            quote_translation: str | None = None
            evidence_ids: list[str] = []

            if kind == "P" and ref_id in pos_by_id:
                resolved = True
                pos = pos_by_id[ref_id]
                evidence_ids = [pos.holder_node_id or pos.position_id]
                # Carry the modern-scholarship reference so the citation payload
                # can surface it as a FIRST-CLASS citable item (scholar+work+page),
                # not only ancient passages. quote_translation is the UI's display
                # string; for a position it holds the formatted scholar reference.
                quote_translation = format_scholar_reference(pos)
            elif kind == "passage" and ref_id in passage_by_id:
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
                # edges resolve structurally; the completeness critic (M5) checks them.
                resolved = True

            items.append(
                ClaimLedgerItem(
                    claim=sentence,
                    evidence_ids=evidence_ids,
                    evidence_class=evidence_class,
                    quote_original=quote_original,
                    quote_translation=quote_translation,
                    support_type="passage" if kind == "passage" else "position",
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


# ── 5. Content gate (replaces the ~10k-char floor, failure-map F4/F9) ─────────


def passes_content_gate(prose: str, cmap: ControversyMap) -> bool:
    """Replace the length floor with a CONTENT gate (ARCHITECTURE §4.5).

    A correct 600-word survey passes; a node-paste template never does. Requires
    ≥1 fault line invoked (an ``[edge:…]`` / ``--relation-->`` marker) AND ≥1
    primary citation that RESOLVES to a passage in ``cmap`` (a fabricated
    ``[passage_…]`` id does not count), and rejects the dead facet-template string
    outright (it must never silently return).
    """
    if not prose.strip():
        return False
    # anti-template guard: the dead facet-template string must never appear
    if "frames the issue as" in prose:
        return False
    has_edge = bool(re.search(r"\[edge[:_]", prose)) or bool(
        re.search(r"--\s*\w+\s*-->", prose)
    )
    if not has_edge:
        return False
    # ≥1 primary citation grounded in the map (resolves to a real passage id),
    # so a paste citing a fabricated passage id cannot satisfy the gate.
    ledger = build_provenance_ledger(prose, cmap)
    has_grounded_passage = any(
        item.support_type == "passage" and item.status == ClaimStatus.SUPPORTED
        for item in ledger
    )
    return has_grounded_passage


# ── 6. Degraded mode — a reasoned hedge, NEVER a template (ARCHITECTURE §4.5) ─


async def synthesize_degraded(cmap: ControversyMap, llm: Any) -> str:
    """When synthesis fails or the content gate trips: a SHORTER reasoned answer
    over whatever frames assembled, explicitly stating its coverage limit in prose.

    Never a node-paste (this is the ``_render_answer_fallback`` replacement). On any
    LLM error returns an honest empty string for the caller to surface — still never
    a template.
    """
    gaps = "; ".join(cmap.coverage_gaps) if cmap.coverage_gaps else "none recorded"
    degraded_prompt = (
        serialize_controversy_map(cmap)
        + "\n\nWrite a SHORT, honest scholarly answer over only the frames that "
        "assembled. State explicitly which fault lines were thinly covered in this "
        f"run (gaps: {gaps}). Attribute every position; ground in quoted text where "
        "available; do not pad. This is a scholar's hedge, not a survey."
    )
    # The safety-belt must NOT empty the same way the head did. deepseek shares its
    # max_tokens between reasoning_content and content, so a hedge on deepseek can
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
# back empty (e.g. all Fireworks rungs 429/error and Gemini 429s too), this
# serialises the map's contending positions + their grounded passages into
# readable, attributed prose DIRECTLY — so a populated map ALWAYS yields a real
# answer instead of falling through to the legacy bare "insufficient evidence"
# sentence. Carries the inline [P_*]/[edge:*]/[passage_*] markers so
# build_provenance_ledger indexes it exactly like an LLM answer. Returns "" only
# for a genuinely empty map (no frames, no positions, no exegesis units).


def _hedge_passage_block(pr: PassageRef) -> str:
    """One quoted-passage line for the deterministic hedge, with its marker."""
    who = ", ".join(p for p in (pr.author, pr.canonical_ref or pr.work) if p)
    marker = (
        f"[passage_{pr.passage_id}: {who}]" if who else f"[passage_{pr.passage_id}]"
    )
    original = (pr.original_text or "").strip()
    english = (pr.english_text or "").strip()
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
            marker = f"[P_{pos.position_id}: {format_scholar_reference(pos) or holder}]"
            claim = (pos.claim or "").strip()
            if claim:
                lines.append(f"- {holder} holds that {claim} {marker}")
            else:
                lines.append(
                    f"- {holder} is recorded as a contending position {marker}"
                )

        for link in frame.links:
            frm = (link.from_holder or link.from_id).strip()
            to = (link.to_holder or link.to_id).strip()
            rel = (link.relation or "opposes").strip()
            edge_marker = f"[edge: {rel} P_{link.from_id}->P_{link.to_id}]"
            gloss = f" — {link.gloss.strip()}" if link.gloss else ""
            lines.append(f"  Here {frm} {rel} {to}{gloss} {edge_marker}")

        for pr in frame.contested_passages:
            lines.append(_hedge_passage_block(pr))

    if cmap.exegesis_units:
        lines.append("")
        lines.append("## Further primary evidence")
        for pr in cmap.exegesis_units:
            lines.append(_hedge_passage_block(pr))

    if cmap.coverage_gaps:
        lines.append("")
        gaps = "; ".join(g for g in cmap.coverage_gaps if g)
        lines.append(
            f"Coverage limit: the following fault lines were thinly retrieved on "
            f"this run — {gaps}."
        )

    return "\n".join(lines).strip()
