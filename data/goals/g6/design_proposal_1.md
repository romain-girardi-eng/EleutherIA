# Design Proposal #1 — "Scholar-RAG": The Argument-Graph-Walking Dialectician

> **Headline.** Scholar-RAG is a *vectorless, agentic, edge-first* graph-RAG whose retrieval and
> synthesis are both organised around **the disagreement layer as the primary index** — it walks
> `opposes / critiques / responds_to / participates_in / contributes_to` edges to assemble a
> **bipolar dialectical map** (debate → contending positions → page-grounded scholarship → contested
> bilingual primary text), then a reasoning model writes scholar-grade prose *from that map* with
> cite-as-you-write, and the provenance ledger falls out as a byproduct rather than generating the prose.
>
> **Single most important novel idea.** **The Dialectical Map (DMap) is a first-class typed
> intermediate object** — a bipolar argumentation framework materialised directly from the KG's
> `opposes/critiques/responds_to` edges, scored by a deterministic gradual-semantics pass (DF-QuAD)
> that yields *who-holds-what + how-contested*, never *what-is-true*. It is simultaneously (1) the
> retrieval target ("fetch the DMap for this question"), (2) the synthesis context (the model reasons
> over an explicit fault-line topology, not a flat node dump), and (3) the verification oracle (the
> completeness critic checks the answer against the DMap's edges, the anachronism gate checks that
> every position labelled "libertarian/compatibilist" carries the attribution the DMap records). One
> object kills F1–F12 at once because it is structurally *unable* to be edge-blind: it has no rows
> except edges.

---

## 0. Reconciliation note (the stack conflict the G6 doc vs. research left open)

The **goal doc** says "STACK = Fireworks + opencode; Kimi K2.7 via Fireworks WHEN AVAILABLE; do NOT
use Moonshot direct." The **model_resolution.md** (live-tested 2026-06-16) found Fireworks has **no
K2.7** (404), and the only genuinely-K2.7 quality is `kimi-k2.7-code-highspeed` on **Moonshot direct**.

Resolution adopted by this design: **the architecture is model-agnostic, and synthesis quality is a
config knob, not a wiring assumption.** Concretely:

- **Production default stays on the stack the goal doc mandates**: Fireworks `kimi-k2p6` (tool-calling
  + synthesis), reachable through the existing `services/llm_service.py` provider chain. This honours
  "do NOT use Moonshot direct" for the default deployment.
- A **`SCHOLAR_SYNTHESIS_MODEL` override** is added (one env var, one resolution point) so that when a
  general-purpose K2.7 lands on Fireworks it is a one-line swap (`kimi-k2p7`), and so that an
  operator who *chooses* to opt into Moonshot direct for the synthesis-only call can set
  `SCHOLAR_SYNTHESIS_MODEL=moonshot:kimi-k2.7-code-highspeed` with the temp=1 clamp from
  model_resolution.md §(c). The default ships Fireworks; Moonshot is opt-in, not baked in.
- **Retrieval (tool-calling loop) and synthesis are decoupled models.** Retrieval needs reliable
  function-calling (Fireworks K2p6, today's best on-stack). Synthesis needs the deepest reasoner.
  Splitting them lets the K2.7 swap touch only the synthesis call site, exactly as the goal asks
  ("make the K2.7 swap a one-line change").

This is the only place the design diverges from a literal reading of the goal doc, and it diverges
*toward* the goal's own stated intent (model-agnostic, one-line swap, on-stack default).

---

## 1. Question → scholarly-answer-shape planner

### 1.1 The six shapes (replace the keyword facet buckets at `graph_nodes.py:1082-1271`)

A single LLM planning call (cheap, Fireworks K2p6, `max_tokens≈1500`, JSON-mode) classifies the
question into **one primary shape + optional secondary shape**, and — critically — *emits the graph
patterns to fetch*, not a fixed list of section titles. The shape is a **retrieval program**, not a
template.

| Shape | Trigger | Graph pattern the shape compiles to (the DAG) | Answer skeleton it licenses |
|-------|---------|-----------------------------------------------|------------------------------|
| `survey_of_debates` | "open debates", "current state of the question", "what's contested" | enter via `debate`/`controversy` nodes → `participates_in`/`contributes_to` → `opposes`/`critiques` fault-lines → contested passages | one section per **fault line**, not per entity |
| `concept_genealogy` | "origin/emergence of X", "history of the notion of" | concept node → `precedes`/`influenced_by` chain + `discusses` from reception → competing datings | chronological, with the dating *dispute* foregrounded |
| `transmission_trace` | "did A know B", "source of A's argument", "how did X reach Y" | person → `influenced_by`/`participates_in` chains + `cites_primary_source` + rival-source `opposes` | source-stemma narrative + the scholarly dispute over it |
| `position_comparison` | "X vs Y on Z", "how does A differ from B" | two anchor nodes → `opposes`/`contrasts_with`/`agrees_with` between them → grounding passages each side | symmetric two-column dialectic |
| `primary_text_exegesis` | a passage/locus is named, "what does Cicero say in Fat. 41" | passage → `_en` pair → `discusses`/`interprets` from reception → `critiques` among interpreters | quote-first, philological, interpretation-history |
| `doxographical_synthesis` | "what did the Stoics think about", broad doctrinal | school/person cluster → `member_of` → doctrine concepts → `critiques` from rivals | doctrine exposition + ancient counter-positions |

The classifier prompt is given the **inventory header** of available structures (counts of debate
nodes, the `opposes` edge list shape) so it knows the graph *has* a disagreement layer to target.
Default when ambiguous: `survey_of_debates` (the failing trigger question lands here — it currently
mis-routes to `Definition/Textual Basis/Counterpoint`, F6).

### 1.2 The plan object (`ResearchPlan`, new, in `state.py`)

```python
class GraphPattern(BaseModel):
    intent: str                    # "find fault lines in discovery-of-will debate"
    entry: Literal["debate","concept","person","passage","school","position"]
    seed_query: str                # lexical/lemmatic seed to locate entry nodes
    edge_program: list[str]        # ordered relations to walk: ["participates_in","opposes","contributes_to"]
    depth: int = 2
    want_bilingual: bool = True

class ResearchPlan(BaseModel):
    primary_shape: AnswerShape
    secondary_shape: AnswerShape | None
    patterns: list[GraphPattern]   # the DAG (3-6 patterns), executed in topological order
    answer_skeleton: list[str]     # adaptive section hints, NOT a fixed template
    budget_tier: Literal["quick","standard","deep"]   # drives §6 budgets
```

The plan **drives** retrieval: each `GraphPattern` becomes a retrieval sub-task (§2), and
`answer_skeleton` is a *hint* the synthesiser may override — never a hard template. This is
Adaptive-RAG routing (research §4) generalised from 3 regimes to 6 scholarly shapes.

---

## 2. Argument-structure-first VECTORLESS retrieval (how it stops being edge-blind)

### 2.1 The root fix: stop discarding edges (F1)

`evidence_collector._ingest_get_neighbors` (`evidence_collector.py:178-192`) currently keeps only
`edge_node_id` and **drops `relation` + `direction`** — even though `EdgeSummary` already carries them
correctly (confirmed in `get_neighbors.py:107-116`). The fix is a new typed edge store that survives
into state and into the prompt:

```python
# state.py — new container on RAGState
class DialecticalEdge(BaseModel):
    source_id: str
    target_id: str
    relation: str           # opposes | critiques | responds_to | participates_in | contributes_to | ...
    direction: str
    source_label: str
    target_label: str
    source_type: str
    target_type: str

# RAGState gets:  dialectical_edges: list[DialecticalEdge] = field(default_factory=list)
```

`_ingest_get_neighbors` populates this from every `EdgeSummary`. `populate_state`
(`evidence_collector.py:102-139`) writes `dialectical_edges` alongside the existing containers. This
alone makes "0 edges used" impossible: the edges now physically exist in state.

### 2.2 Two new tools (the relational channel — research §2 dual-channel)

The current 8 tools are entity-centric. Add **two debate-aware tools** so the planner has an
affordance for the disagreement layer (fixes F3, and the dead `query_scholarly_consensus` ref at
`scholarly_agent.py:640`):

**Tool A — `find_debates`** (new, `agents/tools/find_debates.py`)
- *Purpose:* enter the graph through its 33 `debate`/`controversy`/`position` nodes — the answer
  scaffolding the current pipeline never touches.
- *Args:* `query: str` (lexical/lemmatic over debate labels+descriptions), `period_filter`
  (exclude Medieval/Modern when the question is about antiquity), `limit`.
- *Returns:* `[{debate_id, label, summary, participant_count, opposing_edge_count, grounded_passage_count}]`
  — ranked by `opposing_edge_count` (most-contested first) so the model sees the live fault lines up top.
- *Vectorless:* pure ts_rank + label match over the debate subset; no embeddings.

**Tool B — `map_dialectic`** (new, `agents/tools/map_dialectic.py`) — **the core retrieval primitive**
- *Purpose:* given a seed node (a debate, a position, a scholar, a concept), return the **bipolar
  argumentation subgraph** around it: the contending positions and the typed edges between them.
- *Args:* `seed_node_id`, `relations` (default `["opposes","critiques","responds_to","contrasts_with","refutes","agrees_with","supports"]`),
  `expand_participants: bool` (also pull `participates_in`/`contributes_to`), `hops: int = 2`,
  `attach_grounding: bool = True` (auto-pull each position's `created_by`/`advanced_in` publication +
  `cites_primary_source`/`contributes_to` passages).
- *Returns:* a `DMapFragment` — nodes tagged `{pro|con|neutral|primary_evidence}` relative to the seed,
  every edge typed, each scholarly node carrying its publication + page when present.
- *Vectorless:* pure adjacency walk over `outgoing_edges`/`incoming_edges` (already in `Deps`), bounded
  by `hops` and PageRank-sorted (reuses the existing sort in `get_neighbors`).

`map_dialectic` is what makes Scholar-RAG *argument-structure-first*: the model's natural retrieval
move for any contested question becomes "find the debate, then map its dialectic," not "search nodes,
read descriptions."

### 2.3 Hierarchical, model-driven escalation (research §3, A-RAG)

Keep the ReAct loop but order the tools coarse→fine and **teach the loop the debate-first habit** in
`react_loop.py:566-600` (`NATIVE_SYSTEM_PROMPT_TEMPLATE`). The new system-prompt spine:

> "For any question about a controversy or 'open debate', FIRST call `find_debates`, THEN
> `map_dialectic` on each relevant debate to surface who opposes whom. Only after you have the
> dialectical structure should you `read_passages` (always fetching the `_en` translation alongside the
> original) to ground each position. Never paraphrase a position you have not located via an edge."

Coarse→fine ladder, model picks the rung: `find_debates` / `search_nodes` → `map_dialectic` /
`get_neighbors` → `get_node_detail` → `read_passages` (full, bilingual). Never truncate at a tool
boundary (A-RAG: read deep only on demand).

### 2.4 Anaphora-chained hops (research §sec, Query Grounding)

`map_dialectic` returns node IDs the model can bind into the next call: "map the discovery-of-will
debate" → returns `frede_position` → "map the dialectic of `frede_position`" → returns the four
`opposes` edges (Dihle, Bobzien, Irwin, Blackson). The edge program in the `ResearchPlan` is executed
with resolved references, building the reply chains the affordance inventory §8 enumerates.

### 2.5 Bilingual pairing is automatic (fixes affordance §4)

Whenever `read_passages` returns `passage_X`, the collector auto-fetches `passage_X_en` via the
existing `has_translation` edge and stores them as a **paired bundle** (original + English on one
`EvidenceBundle`). No model call; pure edge follow. 2,953 pairs become reachable; 0→all.

---

## 3. Evidence dossier assembly — the Dialectical Map (DMap)

The dossier is **not** the current `ScholarlyDossier` of generic facets. It is a single typed
**`DialecticalMap`** assembled from the retrieval phase, with subagent distillation (research §6).

### 3.1 Structure

```python
class Position(BaseModel):              # one contending stance
    position_id: str                    # scholar_position_* / scholarly_argument_* / ancient person/arg
    holder: str                         # "Frede 2011" / "Alexander of Aphrodisias"
    holder_type: Literal["modern_scholar","ancient_author","school"]
    claim: str                          # the position stated in ONE sentence, attributed
    page_grounding: str | None          # "Frede 2011, p. 44" when a publication+page is on the node
    publication_id: str | None
    base_strength: float                # τ ∈ [0,1] from node confidence / citation count
    primary_support: list[str]          # paired bilingual bundle_ids grounding this position

class FaultLine(BaseModel):             # one axis of disagreement
    fault_line_id: str
    question: str                       # "When did a notion of 'will' emerge?"
    debate_node_id: str | None
    positions: list[Position]
    edges: list[DialecticalEdge]        # the opposes/critiques/responds_to among the positions
    contested_passages: list[str]       # bundle_ids the positions fight over
    contestedness: float                # DF-QuAD aggregate (see §3.3)

class DialecticalMap(BaseModel):
    question_frame: str
    shape: AnswerShape
    fault_lines: list[FaultLine]
    orphan_evidence: list[str]          # passages/nodes not yet attached to a fault line
    coverage_gaps: list[str]            # debates the planner named but retrieval didn't fill
    provenance: dict[str, EvidenceBundle]   # full untruncated bilingual passages, by id
```

### 3.2 Untruncated, bilingual, page-grounded, provenanced

- **Untruncated:** `provenance` holds full `EvidenceBundle`s. The 220-char `truncate_text` calls
  (`graph_nodes.py:4192/4211/4308/4401`) are deleted, not relocated. Nothing in the synthesis path may
  call truncation.
- **Bilingual:** every `primary_support` bundle is an original+`_en` pair (§2.5).
- **Page-grounded:** `Position.page_grounding` reads the publication/page already stored on
  `scholar_position_*` and `scholarly_argument_*` nodes (affordance §3 — e.g. "Sharples 1983, p. 22").
- **Provenance:** each `Position` and `FaultLine` carries its source node IDs and edge IDs; this *is*
  the ledger substrate (§4.4).

### 3.3 Gradual-semantics scoring (research §5, ArgLLMs / DF-QuAD) — represent, never assert

For each `FaultLine`, run **deterministic DF-QuAD** over its `edges`: `supports/agrees_with` raise a
position's strength, `opposes/critiques/refutes` lower it, propagated from `base_strength`. The output
is **not a winner** — it is a `contestedness` score (high when strong positions attack each other) and
per-position aggregate strengths. This drives presentation order ("the most contested fault lines
first") and, crucially, keeps the system *structurally hedged*: the map reports *who holds what and how
hard it's contested*, never *which side is correct*. This is the formal guarantee behind "attribute
positions, never assert."

### 3.4 Subagent distillation (research §6) — keep the synthesiser's context clean

Per `GraphPattern` (≈ per fault line), a retrieval subagent (Fireworks K2p6, the memory rule's
sonnet-tier orchestration analogue) runs the messy multi-call retrieval and returns **only** a
distilled `FaultLine` (positions + edges + bundle IDs, ≈1–2k tokens). The lead model never sees the
raw tool chatter — it sees a clean `DialecticalMap`. This is what lets the synthesis call fit a deep
reasoner's budget (§6) and keeps reasoning uncluttered.

---

## 4. Dialectical scholarly SYNTHESIS — the core (replaces the facet template)

This is the single LLM call (deep reasoner, §6) that **replaces** `_render_answer_fallback`
(`graph_nodes.py:3575-3733`), `_derive_claim_ledger_fallback`, and the ledger→prose dependency. It
takes the `DialecticalMap` and writes prose **from reasoning over the map**, with cite-as-you-write.

### 4.1 Why it replaces the template, structurally

The facet template existed because the pipeline had *no relational object to reason over* — so it
pasted node descriptions under fixed headers. The DMap *is* that relational object. With it present,
there is nothing for a template to do: section structure comes from `fault_lines`, claims come from
`positions`, grounding comes from `primary_support`. The template's three jobs (structure, claims,
grounding) are all now data on the map. We delete the template and route the inadequate-band branch
(`graph_nodes.py:5757-5759`, `scholarly_agent.py:1615-1618`) to **re-synthesis with a tightened
prompt**, never to a deterministic paste.

### 4.2 The synthesis prompt (concrete design)

Single call, `reasoning_content` enabled (Kimi K2.x reason-before-write is an *advantage* for
dialectic — model_resolution §b). Structure:

**System role:**
> You are a historian of ancient philosophy writing for a scholarly audience (Cambridge-Companion
> register). You reason over a *Dialectical Map*: a structured record of contending scholarly positions
> and the primary texts they fight over. You never assert which side is correct; you attribute every
> position to its holder and let the disagreement stand. You never write Greek or Latin that is not
> present verbatim in the provided passages. Modern labels ("libertarian", "compatibilist", "the will")
> are scholarly characterisations and must be attributed, never stated as ancient fact.

**Input blocks (the DMap, serialised):**
1. `## Question` + detected `shape`.
2. `## Fault Lines` — for each: the question it poses, the positions (holder + one-sentence claim +
   page), the typed edges between them (`Frede 2011 OPPOSES Dihle 1982`), the `contestedness` score,
   and the IDs of contested passages.
3. `## Primary Evidence` — full bilingual bundles (original + English), each with its `[ref]` marker.
4. `## Coverage gaps` — debates the planner named but retrieval under-filled (drives §4.3 self-gap).

**Reasoning steps the prompt mandates (chain-of-thought, surfaced in `reasoning_content`):**
1. **Thesis selection** — from the fault lines, state the *shape* of the answer (e.g. "the field is
   organised around four live disputes"), not a doctrinal verdict.
2. **Per fault line:** name the question; attribute each position to its holder *with its page*; cite
   the primary passage each side leans on (original + English inline); state the edge ("Bobzien
   *critiques* Frede on…"); report the contestedness; hedge the conclusion ("no consensus; the dispute
   turns on whether…").
3. **Cross-links:** note where fault lines interact (Frede's Epictetus-dating vs Bobzien's no-problem
   thesis).
4. **Honest closure:** what remains open; what the graph does *not* settle.

**Output contract (cite-as-you-write — research §8):**
- Every attributed position carries an inline `[ref]` to a `position_id` *and* the `passage_id` /
  `publication` grounding it, written as the sentence is written — not appended afterward.
- Adaptive structure: section per fault line for `survey_of_debates`; chronological for
  `concept_genealogy`; two-column for `position_comparison`. The `answer_skeleton` is a hint; the model
  shapes prose to the question.
- Tag each sentence-claim internally as `attributed_position | primary_grounding | interpretation` (the
  claim-auditability split, research §8) — emitted as lightweight inline markers the ledger pass reads.

### 4.3 The draft exposes its own gaps (research §1, GraphSearch reflection)

The synthesis call ends with a required `<gaps>` block: *"Which fault line / debate node / opposing
position in the map did I not address, and what edge or passage would close it?"* This is the
iterate-condition signal (§5). It is generated by the same reasoning pass that wrote the prose, so the
model knows exactly what it skipped.

### 4.4 Provenance ledger as byproduct (reverses F8)

After synthesis, a **deterministic** pass walks the inline `[ref]` markers and the
`attributed/grounding/interpretation` tags and *constructs* the `claim_ledger` from them — the ledger
is read **out of** the finished prose, not used to generate it. `DraftClaimLedger`
(`graph_nodes.py:5189-5429`) is demoted from a generative node to this extraction pass.
`build_render_prompt` (`graph_nodes.py:5471-5497`) is deleted; the synthesis prompt is built from the
`DialecticalMap`, not from `ledger_json`. This is the exact inversion the goal §6 demands.

---

## 5. Scholar-grade verification loop (iterate condition)

Three referees run after synthesis; any rejection triggers **targeted re-retrieval + RARR-style span
edit** (research §7), not wholesale regeneration. Replaces the citation-only `ProgrammaticVerify` /
CitationVerifierV2 audit (F11).

### 5.1 Adversarial citation referee (NLI-style entailment — research §8)

Reuse `citation_verifier_v2.py` (JSON bug now fixed) but feed it the DMap: for each
`attributed_position`/`primary_grounding` sentence, ask in isolation (CoVe, research §7) *"does the
cited passage/publication entail this sentence?"* answered against the `provenance` bundle, not free
memory. REJECTED → mark the span for RARR edit.

### 5.2 Completeness critic (new — the missing piece, F11)

This is **mechanically checkable against the DMap**, not a vibe: take the set of `fault_lines` and
high-`contestedness` `opposes`/`critiques` edges in the map; check the answer addresses each (by
`position_id` reference). Any fault line in the map but absent from the answer → a concrete gap →
re-synthesis or targeted retrieval to fill it. This is why the DMap-as-oracle idea matters:
"completeness" has a denominator.

### 5.3 Anti-anachronism gate (new — F11)

Deterministic + LLM hybrid. Scan the answer for the labels MEMORY flags ("invention of the will",
"libertarian", "compatibilism", "free will" applied to a pre-Stoic author). For each occurrence, check
the DMap: is the label carried on an *attributed* `Position` (a scholar's characterisation) or asserted
as ancient fact? If asserted → reject the span, re-write as attribution ("what Bobzien terms…"). This
operationalises the project's standing anti-anachronism rule as a gate, not a hope.

### 5.4 Iterate condition (research §1)

```
draft → {citation referee, completeness critic, anachronism gate} → verdict
  ACCEPT  if: citation-F1 ≥ τ_cite  AND  no missing fault line  AND  no asserted-anachronism span
  REJECT  → Query Expansion: turn each gap into a targeted retrieval (map_dialectic on the missed
            debate / read the missing passage) → augment the DMap → RARR-edit only the affected spans
            → re-verify.
  Stop after N_max iterations (budget tier, §6) or ACCEPT; degrade gracefully (see §7) — never to a template.
```

The loop only stops when evidence is sufficient — the literal cure for "0 edges, garbage answer."

---

## 6. K2.7 integration + budgets

### 6.1 Two model roles, one swap point

- **Retrieval model** (tool-calling loop, planner, subagents, verifier): Fireworks
  `accounts/fireworks/models/kimi-k2p6` — reliable function-calling, on-stack, today's best. Unchanged
  resolution path in `llm_service.py`.
- **Synthesis model** (the §4 call only): resolved from new env `SCHOLAR_SYNTHESIS_MODEL`, default
  `fireworks:kimi-k2p6`. One-line swap to `fireworks:kimi-k2p7` when it ships; opt-in
  `moonshot:kimi-k2.7-code-highspeed` for operators who accept Moonshot-direct (with the temp=1 clamp
  from model_resolution §c: `if provider==KIMI: payload["temperature"]=1.0`).

Touch points for the swap (exactly the four the goal names): `opencode.json`, `llm_service.py`
(provider config + temp clamp), `repl.py`, `llm_pricing.py` — plus the new `SCHOLAR_SYNTHESIS_MODEL`
resolver. Architecture stays model-agnostic.

### 6.2 Budget tiers (reconcile with the latency work, F9)

| Tier | Tool calls | Synthesis `max_tokens` | Verify iterations | When |
|------|-----------|------------------------|-------------------|------|
| `quick` | 12 | 6,000 | 0 | single-shape, well-grounded |
| `standard` | 24 | 9,000 | 1 | default |
| `deep` | 40 | 12,000 | 2 | `survey_of_debates` / `transmission_trace` cross-period |

Key reconciliations of the F9/F10 latency bugs:
- **Token cap vs char floor (F9):** the broken `8000`-token cap (`scholarly_agent.py:147-164`) that
  contradicts the `~10-15k`-char floor (`graph_nodes.py:3987-3993`) is replaced: the floor is
  **removed** (length is no longer a quality proxy — completeness against the DMap is). Reasoning models
  need ≥5,000 tokens *just for reasoning_content* (model_resolution §b); the tier budgets above already
  account for this. A correct 600-word debate survey is no longer rejected for being "too short."
- **Tool-call cap (F9):** raised to 40 on `deep` so a Bobzien⟂Frede + origins + Alexander + Carneadean
  survey can actually fetch its `map_dialectic` + bilingual `read_passages` calls.
- **Subagent distillation (§3.4)** keeps the deep synthesis call's *input* small despite deep
  retrieval — the latency win that makes the deep tier affordable.
- **Streaming heartbeat** (`scholarly_agent.py:1486,1569`): the synthesis call's `reasoning_content`
  phase is long (≈60–95s, model_resolution); raise `max_wait` for the synthesis node specifically and
  stream a "reasoning…" status so the model is not abandoned mid-thought into a fallback.
- **F10 deleted:** `_inject_passage_quotations` (bolting raw passage dumps onto broken prose) is
  removed — passages are now *in* the synthesis via the DMap, cited inline.

---

## 7. Migration plan + measurement (G2 eval)

### 7.1 Staged migration (each stage independently shippable, behind a flag)

`SCHOLAR_RAG=true` gates the new path; default off until stage 4 passes the eval.

1. **Stage 1 — Stop the bleeding (edges survive).** Add `DialecticalEdge` store; fix
   `_ingest_get_neighbors` to keep `relation`+`direction`; add edges layer to `_build_context_pack`
   (`graph_nodes.py:3447-3469`) and `ContextPack`. *Effect:* edges > 0 even on the old template. Smallest
   diff that moves success criterion (b).
2. **Stage 2 — Relational retrieval.** Ship `find_debates` + `map_dialectic` tools; register in
   `tools.py`; rewrite the `react_loop` system prompt to debate-first; auto-bilingual pairing. *Effect:*
   the disagreement layer becomes reachable (criteria a, c substrate).
3. **Stage 3 — DMap + dialectical synthesis.** Build the `DialecticalMap` assembler + DF-QuAD scorer;
   replace `_render_answer_fallback` and the ledger→prose flow with the §4 synthesis call; ledger as
   byproduct. Delete the 220-char truncations and the char-floor gate. *Effect:* genuine prose
   (criterion d).
4. **Stage 4 — Verification loop.** Completeness critic + anti-anachronism gate + RARR span-edit +
   iterate. Wire `SCHOLAR_SYNTHESIS_MODEL`. *Effect:* every claim traces to evidence (criterion e); K2.7
   swap-ready.

Old template code stays behind the flag for one release as a rollback, then is deleted (F4/F5/F6 gone).

### 7.2 Measurement — G2 eval harness (old vs new)

- **Quantitative (G2):** citation-F1 (the verifier now parses) + faithfulness/NLI entailment, run
  old-vs-new on the eval set. New target: edges-used > 0 on every relational query; citation-F1 up;
  zero asserted-anachronism spans.
- **New DMap-derived metrics** (cheap, deterministic): **fault-line coverage** = |fault lines
  addressed| / |fault lines in DMap| (the completeness critic's own ratio); **attribution rate** = %
  of position-claims carrying a holder+page; **template-paste rate** = 0 (regression guard: assert the
  facet template is never emitted).
- **Scholar-grade qualitative rubric** on the trigger question ("open debates today about free will in
  antiquity"), old vs new, scoring: (a) enumerates the real live debates (Stoic Bobzien⟂Frede;
  origins-of-the-will; Alexander libertarian; Carneadean transmission), (b) uses edges, (c) attributes
  each position with a citation, (d) genuine prose, (e) verified. This is the exact success criterion in
  GOAL-6 §"Success criteria."
- **Regression test (per the testing rule):** a fixture asserting that on the trigger question the new
  path produces ≥3 distinct fault lines, >0 `opposes`/`critiques` edges in the DMap, and 0 occurrences
  of the `"frames the issue as"` template string.

---

## Appendix — how each failure mode (F1–F12) is killed

| F | Failure | Killed by |
|---|---------|-----------|
| F1 | edges discarded at ingestion | §2.1 `DialecticalEdge` store; `_ingest_get_neighbors` keeps relation+direction |
| F2 | no edge slot in prompt | §2.1 + §3 DMap is the context; edges are first-class |
| F3 | no debate retrieval affordance | §2.2 `find_debates` + `map_dialectic` tools |
| F4 | facet template IS the answer | §4.1 template deleted; inadequate-band → re-synthesis, never paste |
| F5 | 220-char node-paste claims | §3.2 truncations deleted; full bilingual provenance |
| F6 | question-shape-blind facets | §1 six-shape planner emits graph patterns, not fixed sections |
| F7 | real synthesis overridden by gates | §4.2 synthesis is the path; §6.2 char-floor gate removed |
| F8 | ledger→prose dependency | §4.4 ledger extracted from prose as byproduct |
| F9 | latency caps force mechanical synthesis | §6.2 tiered budgets; subagent distillation; floor removed |
| F10 | post-hoc passage dumping | §6.2 `_inject_passage_quotations` removed; passages cited inline |
| F11 | verify audits citations only | §5.2 completeness critic + §5.3 anachronism gate (DMap-checked) |
| F12 | K2.7 not wired | §6.1 `SCHOLAR_SYNTHESIS_MODEL`, one-line swap, temp clamp |
