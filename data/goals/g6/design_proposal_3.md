# Design Proposal #3 — Scholar-RAG: a vectorless, agentic, dialectical graph-RAG that researches like a scholar

> **Headline:** *Scholar-RAG retrieves the **fault lines** of a question (the `opposes`/`critiques`/`responds_to` edges and the debate nodes that anchor them) **before** it retrieves entities, assembles a bilingual evidence dossier per debate, and synthesises **dialectical prose where the provenance ledger is emitted inline as a byproduct** — the deterministic facet-template is deleted, not patched.*
>
> **Single most important novel idea — the Dialectical Dossier as the unit of retrieval AND synthesis.** Instead of "retrieve entities → pack node descriptions → template," the pipeline's atomic object is a **`Controversy` dossier**: a *bipolar argument frame* (one debate/fault-line) carrying its opposing scholar-positions, each position's page-grounded scholarly argument, the contested primary passages in original+English, and the explicit dialectical edges that connect them. Retrieval *produces* these frames; synthesis *reasons over* them and *cites from* them as it writes. The edge is no longer an afterthought the model can't see — **the edge is the seed of the unit**. This is what makes the answer (a) enumerate the real debates, (b) use edges > 0, (c) attribute every position with a citation, in one structural move.

---

## 0. Why diverge from the G6 sketch (and where)

The G6 sketch is six correct ideas in a line: shape-planner → edge-first retrieval → dossier → dialectical synthesis → verify → ledger-as-byproduct. I keep all six but make three opinionated changes, each argued:

1. **The dossier is bipolar-argument-framed, not facet-framed or sub-claim-framed.** The research SOTA (ArgLLMs #5, GraphSearch relational channel #2) and the KG affordance inventory both point the same way: this graph's *latent structure* is 33 debate nodes + 312 dialectical edges (244 `critiques` + 57 `responds_to` + 11 `opposes`). A sub-claim DAG (deep-research default, #6) would re-derive that structure from scratch by lexical search and mostly miss it (exactly F3). So the **retrieval target is the debate/controversy frame itself**, and sub-claims are *derived from* frames, not the reverse. This is the proposal's spine and the reason it beats a generic deep-research port.

2. **No bipolar-strength *numbers* in the user-facing answer (DF-QuAD stays internal, optional, and advisory).** ArgLLMs' gradual-semantics scoring is seductive but it would manufacture false precision ("Frede 0.62 vs Dihle 0.38") that is itself a kind of anachronistic assertion — antithetical to "attribute, never assert." I adopt the *bipolar structure* (supporters/attackers of a position, recursively) as the dossier's shape and as an internal *completeness signal* (a debate with attackers but no surfaced defenders is an incomplete dossier → triggers expansion), but the synthesis reports **who holds what and who attacks whom**, never a computed verdict strength. Dialectic-as-data for retrieval/critique; dialectic-as-prose for the answer.

3. **K2.7 on Moonshot for synthesis, but the architecture is provider-pinned at exactly one seam.** The GOAL doc pins the *retrieval/agent* stack to Fireworks+opencode (kimi-k2p6, tool-calling proven there); `model_resolution.md` proves Moonshot `kimi-k2.7-code-highspeed` is the best *synthesis* prose engine (temp=1, 262k ctx, reasoning_content). These are not in conflict — they are **two different roles**. Tool-calling ReAct retrieval stays on Fireworks K2.6 (where tool-calling works); the **single dialectical-synthesis call** routes to Moonshot K2.7. One model-router seam, two tiers. (§6.)

Everything else follows the sketch.

---

## 1. Question → scholarly-answer-shape planner

### 1.1 The six shapes (the planner's output type)

Replace the keyword-bucket facet picker (`_default_research_facets`, `graph_nodes.py:1082-1271`) with a one-shot **shape classifier** that returns a typed `ResearchPlan`. Six shapes, each a *retrieval program over the graph*, not a section template:

| Shape | Trigger intuition | Graph entry pattern | Answer skeleton (adaptive, not fixed) |
|---|---|---|---|
| `survey_of_debates` | "what are the open debates / controversies / disputes about X" | **debate/controversy nodes → participants → opposes/critiques** | one movement per live fault line |
| `concept_genealogy` | "origin / emergence / history of concept C" | concept node → `precedes`/`influenced_by` chain + the debate node *about* the genealogy | chronological-with-contested-datings |
| `transmission_trace` | "how did idea/argument move from A to B" | `participates_in` chains + `cites_primary_source` + `responds_to` | source → intermediaries → reception, with rival reconstructions |
| `position_comparison` | "compare X's and Y's view on Z" / "did X agree with Y" | two person/position nodes → shared concept → `opposes`/`agrees_with`/`contrasts_with` | X's position · Y's position · points of contact · scholarly read |
| `primary_text_exegesis` | "what does passage/work P say about Z" | work→passage tree-nav + `evidenced_by`/`discusses` back-edges | lemma → close reading → scholarly interpretations |
| `doxographical_synthesis` | "what did the Stoics / school S think about Z" | school node → `member_of` → per-member positions → internal disagreement | school consensus · internal variation · sources |

A seventh implicit shape, `factual_lookup` (Adaptive-RAG "no/single-step retrieval", #4), short-circuits to a single `get_node_detail` + a 2-sentence answer for "when did Chrysippus die" — matching cost to difficulty and protecting latency budget for the hard shapes.

### 1.2 How the plan drives retrieval (the DAG)

The planner emits a small **retrieval DAG**, not a flat list (deep-research survey #6, GraphSearch query decomposition #1):

```jsonc
{
  "shape": "survey_of_debates",
  "thesis_question": "Which scholarly disputes about ancient free will are live today?",
  "period_filter": ["Presocratic","Classical","Hellenistic","Imperial","LateAntiquity"], // excludes Medieval/Modern controversy nodes
  "seed_strategy": "enumerate_debate_nodes",          // ⇒ new tool find_debates
  "frames": [                                          // each frame = one dialectical dossier to build
    {"frame_id":"f1","hint":"discovery/origin of the will"},
    {"frame_id":"f2","hint":"Stoic compatibilism genuine?"},
    {"frame_id":"f3","hint":"Alexander libertarian?"},
    {"frame_id":"f4","hint":"Carneadean transmission (Amand vs Ramelli)"}
  ],
  "depth": "multi_step",
  "budget_hint": "deep"
}
```

The DAG nodes are not fully enumerated by the planner (it cannot know which debate nodes exist) — `frames[]` are *hints*; the **first retrieval step resolves hints to real debate node ids** via the new `find_debates` tool (§2.2), then each resolved frame spawns a dossier-builder. The plan thus *names the graph patterns to fetch* (G6 §1) without hard-coding ids. It is rebuildable/inspectable and goes into the `ResearchNotebook` so the verifier's completeness critic (§5) can diff *planned frames* vs *covered frames*.

**Implementation:** new node `PlanResearch` replacing `ClassifyQueryType`'s template role; one LLM call (Fireworks K2.6, cheap, JSON-mode); output validated into a new `ResearchPlan` pydantic model in `state.py`. `query_type`/`complexity` stay for back-compat budget math but no longer pick facets.

---

## 2. Argument-structure-first VECTORLESS retrieval (how it stops being edge-blind)

This is where F1/F2/F3 die. Three coordinated changes: **keep edges at ingestion**, **give the prompt an edge slot**, **give the agent debate-first tools + a debate-first system prompt**.

### 2.1 Fix F1 — stop discarding `relation`/`direction` at ingestion

`evidence_collector._ingest_get_neighbors` (`evidence_collector.py:178-192`) currently keeps only `edge_node_id`. The `EdgeSummary` already carries `relation` + `direction` + `weight` (`tools/get_neighbors.py:15-21`, confirmed). New: a first-class **edge store**.

- Add to `RAGState` (`state.py:387`): `dialectical_edges: list[DialecticalEdge]` where
  `DialecticalEdge = (source_id, relation, target_id, direction, weight, source_label, target_label)`.
- In `_ingest_get_neighbors`, for every edge whose `relation ∈ DIALECTICAL_RELATIONS`
  (`{opposes, critiques, responds_to, refutes, contrasts_with, agrees_with, supports, participates_in, contributes_to, has_position, advanced_in, engages_with, interprets}`), append a `DialecticalEdge` keyed on `(center_node_id, relation, edge_node_id)` — both endpoints retained.
- `populate_state` (`evidence_collector.py:102-139`) writes `state.dialectical_edges`.
- Same retention in `_ingest_explore_subgraph` (subgraph results that include edge lists) and the new debate tool.

Result: `opposes`/`critiques`/`responds_to` finally enter state. This single fix is the literal cure for "0 edges."

### 2.2 New retrieval tools (the debate/disagreement affordance F3 lacks)

Two new tools, registered in `tools.py`, surfaced in the ReAct registry and the system prompt:

**`find_debates(topic, period_filter?, limit?)`** — the missing relational entry point.
- Returns `debate`/`controversy` nodes ranked by lexical match on label/description **and by incoming dialectical-edge count** (a debate with 11 `opposes`/`critiques` in-edges outranks an isolated one). Each result carries: `debate_id`, `label`, `participant_ids` (from `participates_in`/`contributes_to`/`has_position` in-edges), `opposing_pairs` (the `opposes` edges among participants), `grounded_passage_ids`. This is the `enumerate_debate_nodes` seed-strategy of §1.2. It directly exposes the 33 debate nodes + 312 dialectical edges the facet template never touched.

**`build_controversy_frame(debate_id_or_position_id)`** — the dossier-unit retriever (the novel core, §3).
- Given a debate node OR a `scholar_position_*` node, traverses **one hop of dialectical edges in both directions** to assemble a bipolar frame: `{anchor, supporters[], attackers[], rebuttals[]}` over positions, plus each position's grounding (`scholar_position → created_by/advanced_in → publication`; `→ cites_primary_source → passage`), plus the **contested primary passages** (`debate ←contributes_to← passage`, `position →evidenced_by→ passage`), each auto-paired with its `_en` translation via `has_translation` (the 2,953 pairs the inventory flags as never-paired). Returns a fully-formed `ControversyFrame` (§3.2) — one tool call yields one ready-to-synthesise dossier unit.

Both tools are **pure KG traversal + tree-nav + `has_translation` join — no embeddings**, satisfying the vectorless constraint. They make the relational channel (GraphSearch #2) a first-class tool, not an emergent behaviour the model has to discover.

### 2.3 Coarse→fine, model-driven escalation (A-RAG #3) + dual-channel (#2)

Keep the 8 existing tools; layer them coarse→fine and teach escalation in the system prompt:

```
find_debates / search_nodes        (coarse: what fault lines / entities exist)
  → build_controversy_frame        (relational: one dossier unit, edges + positions + passages)
  → get_node_detail / get_neighbors (drill: a specific scholar's argument, more edges)
  → read_passages (FULL TEXT)       (finest: untruncated original + _en, only when needed)
```

Two retrieval channels run per frame (GraphSearch #2): the **relational channel** (`build_controversy_frame`, `get_neighbors` filtered to dialectical relations) AND the **lexical/lemmatic channel** (`search_passages`, `search_nodes`, tree-nav) for primary grounding the structural channel can't supply. Never truncate at a tool boundary (A-RAG): `read_passages` returns full `original_text` + `translation_text` (already does, `evidence_collector.py:201-224`).

### 2.4 The new system prompt (kills F3's blindness)

`NATIVE_SYSTEM_PROMPT_TEMPLATE` (`react_loop.py:566-600`) is rewritten to be **debate-first** and shape-aware. The load-bearing additions:

> "This knowledge graph encodes scholarly **disagreement** as edges: `opposes`, `critiques`, `responds_to`, `refutes`, `contrasts_with`. When a question asks about debates, controversies, origins, or comparisons, your FIRST move is `find_debates`, then `build_controversy_frame` on each fault line — do **not** start by reading entity descriptions. A debate is real only if you can name the *two sides* and the *edge* between them. For every scholarly position you surface, you must retrieve its grounding (the publication and the primary passage it cites) before reporting it. Attribute positions to named scholars; never assert a modern label ('libertarian', 'compatibilism', 'the will') as historical fact."

The dead `tools.get("query_scholarly_consensus")` ref (`scholarly_agent.py:640`) is repointed to `find_debates`.

### 2.5 Interleaved retrieval inside reasoning (Search-R1 #sec)

The ReAct loop already interleaves think/act. The only change: raise the dialectical-query budget. `_tool_call_budget` (`react_loop.py:91-115`) gets a per-shape allowance — `survey_of_debates`/`transmission_trace` need many `build_controversy_frame` + `read_passages` calls (F9); cap raised to ~45 for those shapes, with the **completeness critic (§5)** as the real stop condition rather than a blunt count.

---

## 3. Evidence dossier assembly

### 3.1 Principle

The dossier is **not** a flat evidence list packed into `## KG Metadata / ## Work Sections / ## Evidence Bundles` (the current edge-blind 3-layer pack, F2, `graph_nodes.py:3377-3484`). It is a list of **`ControversyFrame`s**, each self-contained and citation-ready. Context-Refinement (GraphSearch) prunes to the most informative evidence per frame before synthesis.

### 3.2 `ControversyFrame` structure (new pydantic model in `state.py`)

```python
class GroundedPosition(BaseModel):
    position_id: str
    holder: str                 # "Michael Frede" — never asserted as truth, always a holder
    holder_node_id: str
    claim: str                  # the scholar's thesis, in attributed voice
    publication: str            # "Frede 2011, A Free Will, pp. 153–174"
    publication_node_id: str
    page_grounding: str | None  # page/locus if present in node metadata
    primary_support: list[PassageRef]   # passages this position cites (original+EN)

class DialecticalLink(BaseModel):
    relation: str               # opposes | critiques | responds_to | refutes | agrees_with
    from_id: str; to_id: str
    from_holder: str; to_holder: str
    gloss: str | None           # one-line scholarly gloss of the disagreement

class PassageRef(BaseModel):
    passage_id: str
    work: str; author: str; canonical_ref: str
    original_text: str          # FULL, untruncated, polytonic diacritics preserved
    english_text: str | None    # the _en counterpart, auto-joined
    language: str
    cts_urn: str | None

class ControversyFrame(BaseModel):
    frame_id: str
    debate_node_id: str | None
    title: str                  # "When did a notion of 'the will' emerge?"
    period: str
    positions: list[GroundedPosition]      # the bipolar set (supporters + attackers)
    links: list[DialecticalLink]           # the opposes/critiques edges between them
    contested_passages: list[PassageRef]   # primary text both sides argue over
    completeness: FrameCompleteness        # see §5 — has ≥2 sides? has primary grounding?
```

### 3.3 Untruncation, bilingual pairing, page-grounding, provenance

- **Untruncated:** no `truncate_text(...,220)` anywhere (deletes F5 at the source). `original_text` and `english_text` are full strings. K2.7's 262k context (model_resolution §b) makes truncation unnecessary even for `survey_of_debates` with 4 frames × ~8 passages.
- **Bilingual:** `build_controversy_frame` joins each passage to its `_en` node via `has_translation` (2,953 pairs). `PassageRef` always carries both `original_text` and `english_text`. The citation policy (memory: *original + English, never French*) is structurally enforced.
- **Page-grounding:** `GroundedPosition.page_grounding` pulls page/locus from publication/argument node metadata (the inventory shows e.g. "Sharples 1983, p. 22", "Frede 2011, pp. 153–174" present on nodes). When absent → `null`, and the synthesis cites work-level only (never invents a page).
- **Provenance:** every field carries its source node id. This is the substrate from which the **provenance ledger is reconstructed as a byproduct** (§4.4), reversing F8/G6 §6.

### 3.4 Subagent isolation (deep-research #6) — optional, for the heavy shapes

For `survey_of_debates`/`transmission_trace` with ≥3 frames, each `build_controversy_frame` + drilldown runs as an **isolated retrieval subagent** (Fireworks K2.6 / sonnet-tier per the memory note: subagents are cheap-tier, main loop orchestrates). Each returns only its compact `ControversyFrame` (~1–2k tokens distilled), keeping the synthesis context clean and within K2.7 budget. Single-frame shapes (`position_comparison`, `primary_text_exegesis`) skip subagents and build inline. This is a *latency/quality* lever, not load-bearing for correctness.

---

## 4. Dialectical scholarly SYNTHESIS — THE CORE

This **replaces** the whole `DraftClaimLedger → build_render_prompt → RenderGroundedAnswer → _render_answer_fallback` chain (F4/F5/F6/F7/F8). One model (K2.7), one reasoning-then-prose call per answer, over the `ControversyFrame[]` dossier — *no* intermediate mechanical ledger feeding the prose.

### 4.1 Why one reasoning call replaces the template

The facet template existed because the old pipeline had no reasoning step it trusted — so it deterministically pasted node descriptions under fixed headers. K2.7 *has* a reasoning phase (`reasoning_content`, model_resolution §b): it weighs the dossier's opposing positions in scratch space, *then* writes prose. The "ledger" (F8) was a crutch to make prose look grounded; with cite-as-you-write (#8, §4.3) grounding is intrinsic to the prose, so the ledger crutch is deleted and re-derived afterward as a *check*, not an *input*.

### 4.2 The synthesis prompt (the actual design)

`RENDER_ANSWER_PROMPT` (`graph_nodes.py:580-680`) — which currently demands per-passage exegesis and contains a **hardcoded Bobzien⟂Frede example** (F7) — is replaced by `DIALECTICAL_SYNTHESIS_PROMPT`. Structure:

**System role.**
> You are a historian of ancient philosophy writing for a specialist audience (Cambridge Companion register). You reason **dialectically**: you represent scholarly disagreement as disagreement, attribute every interpretive claim to a named scholar, ground every claim about an ancient author in a quoted primary passage, and hedge where the evidence underdetermines the question. You never assert a modern category ("libertarian free will", "compatibilism", "the will" as a faculty) as a historical fact — you attribute it to the scholar who uses it. You never invent Greek or Latin; you quote only passages present in the dossier.

**Input.** The `ControversyFrame[]` dossier, serialised as structured markdown — **with the edges explicit**:

```
## FRAME f1 — "When did a notion of 'the will' emerge?" (period: Imperial–Late Antiquity)
POSITIONS:
  [P_dihle]  Albrecht Dihle (Dihle 1982, The Theory of Will, pp. 123–144):
             a discrete concept of will is a Christian innovation, crystallised in Augustine.
  [P_frede]  Michael Frede (Frede 2011, A Free Will, pp. 153–174):
             the notion originates earlier, with Epictetus and the late Stoa.
  [P_bobzien] Susanne Bobzien (Bobzien 1998, "The Inadvertent Conception"):
             there is no free-will *problem* in the ancients in the modern sense at all.
DIALECTIC:
  P_frede  --opposes-->  P_dihle        (Frede dates emergence earlier than Augustine)
  P_frede  --opposes-->  P_bobzien      (Frede: will exists in Epictetus; Bobzien: no such problem)
  irwin_arg --opposes--> P_frede        (Irwin: Aristotle may already have it)
  Fürst    --critiques--> Dihle
CONTESTED PRIMARY TEXT:
  [passage_alex_fat_12] Alexander, De Fato 12 —
    GR: Ἀναιρουμένου δὲ ὡς ἐδείχθη τοῦ βουλεύσασθαι...
    EN: Since deliberation is abolished on their account...
```

**Reasoning instructions (drives `reasoning_content`).** A 5-step dialectical procedure the model executes in scratch before writing:
1. **Map the fault lines.** For each frame, identify the ≥2 opposing positions and the edge that opposes them. A frame with only one position is *incomplete* — flag it (feeds §5).
2. **Locate the primary anchor.** For each position, find which dossier passage it argues over. If none, mark the claim as *interpretation without surfaced primary grounding* (hedge harder, lower confidence).
3. **Weigh, don't decide.** Note where positions genuinely conflict vs talk past each other (different `object_of_choice`, different dating); note who has responded to whom (`responds_to` chains). Do **not** pick a winner.
4. **Check anachronism.** Flag every modern label and ensure it is voiced as *"what X calls …"*, never *"the Stoics held compatibilism."*
5. **Plan structure.** Choose the answer's movements from the *frames present*, not a fixed template — one movement per live fault line for `survey_of_debates`; chronological for `concept_genealogy`; etc.

**Writing instructions (drives `content`).**
- Open with a **thesis sentence** that answers the actual question (for the trigger: "The liveliest current disputes are not about whether the ancients were free, but about *whether they had the concept at all*, and *when it emerged* — three fault lines dominate the literature.").
- One movement per fault line; **adaptive headings derived from frame titles**, not `Definition/Textual Basis/Counterpoint`.
- Every interpretive sentence carries an **inline citation as it is written** (§4.3).
- Quote contested primary text **in original + English** at the point the scholars argue over it.
- **Hedge** with the field's own markers ("Bobzien argues…, though Frede contends…"; "the evidence underdetermines whether…").
- Close with what remains genuinely open.

### 4.3 Cite-as-you-write (ALCE / #8) — the inversion of F8

The model emits citations **inline during generation**, drawing ids from the dossier it was given:

```
Frede argues that a notion of the will is already operative in Epictetus
[P_frede: Frede 2011, pp. 153–174], a dating Dihle rejects in favour of an
Augustinian origin [P_dihle: Dihle 1982] — the two positions stand in direct
opposition [edge: opposes P_frede→P_dihle]. The Stoic texts both sides invoke,
such as Alexander's report that abolishing deliberation abolishes τὸ ἐφ' ἡμῖν
[passage_alex_fat_12: Alexander, De Fato 12], do not settle the question…
```

Markers `[P_*: ...]`, `[edge: ...]`, `[passage_*: ...]` are **resolvable against the dossier** because every id came from it. This is the structural guarantee that "uses edges (>0)" and "attributes each position with a citation" are *satisfied by construction*, not hoped for.

### 4.4 Provenance ledger as a byproduct (reverses F8 / G6 §6)

After synthesis, a **deterministic post-pass** (`build_provenance_ledger`) parses the inline markers out of the finished prose and resolves each to its dossier entry, emitting the `ClaimLedgerItem[]` the rest of the system (UI reference map, `ProgrammaticVerify`) expects. The prose is the source of truth; the ledger is its index. `DraftClaimLedger` (`graph_nodes.py:5189-5429`) is deleted as a *pre*-synthesis step and reborn as this *post*-synthesis parser. `build_render_prompt`'s `ledger_json` input (`graph_nodes.py:5471-5488`) is removed.

### 4.5 No more silent template fallback (kills F4/F7)

`_render_answer_fallback` (the facet template, `graph_nodes.py:3575-3733`) and `_derive_claim_ledger_fallback` (the 220-char paste, `graph_nodes.py:4169+`) are **deleted**. The degraded mode when synthesis genuinely fails is *not* a template — it is a **shorter reasoned answer over whatever frames did assemble**, explicitly stating coverage limits ("The graph holds rich material on the discovery-of-will debate; coverage of the Carneadean-transmission dispute was thin in this run."). `_classify_render_quality`'s 10k-char floor (F7/F9) is replaced by a **content gate**, not a length gate: "does the answer name ≥1 fault line with both sides + ≥1 primary citation?" A correct 600-word debate survey now passes instead of being thrown away for the template.

---

## 5. Scholar-grade verification loop

Three referees + an iterate condition, run after synthesis (Chain-of-Verification #7, completeness #1, RARR-edit #8). All operate **against the dossier, not free memory**.

### 5.1 Adversarial citation referee (CitationVerifierV2, extended)

The existing v2 referee (`citation_verifier_v2.py`, JSON bug now fixed) already checks whether sampled citations support their sentence. Extension: because cite-as-you-write attaches ids, the referee now checks each `[passage_*]`/`[P_*]` marker via **NLI-style entailment** — *does the cited dossier passage actually entail the sentence's claim about it?* (ALCE precision/recall, #8). Markers that don't resolve to the dossier (a hallucinated id) are hard-rejected. Cap raised from 8 to "all attributed-position claims" for the synthesis path (these are the load-bearing claims).

### 5.2 Completeness critic (new — answers "which graph debate did it miss?")

The exact gap-driven loop the SOTA flags as the cure for "0 edges, garbage" (GraphSearch #1). It diffs **planned frames (§1.2) and the debate nodes `find_debates` returned** against **fault lines actually present in the prose** (parsed from `[edge:]`/frame markers). A planned/available debate with no movement in the answer is a **gap**; the critic emits a targeted expansion query ("build_controversy_frame on `debate_carneadean_antiastrology_tradition`") that **re-enters retrieval (§2)**. This is the iterate driver.

### 5.3 Anti-anachronism gate (new)

A focused CoVe check (#7): scan the prose for the flagged modern labels (`libertarian`, `compatibilism`, `incompatibilism`, `free will`, `the will`, `soft/hard determinism`, `invention of the will`) and verify each is **voiced as attributed** ("what Bobzien calls…", "in Frede's sense") rather than **asserted as historical fact**. An unattributed assertion is a violation → RARR-style **edit the offending span** (not regenerate the whole answer): rewrite "the Stoics were compatibilists" → "the Stoics held what modern scholars term compatibilism." This operationalises the memory rule (*never assert modern labels*) and the Phase-12 anachronism audit as a runtime gate.

### 5.4 Iterate condition

```
loop until ACCEPT or budget:
  draft = dialectical_synthesis(dossier)
  r1 = citation_referee(draft, dossier)        # every marker entailed & resolvable?
  r2 = completeness_critic(draft, plan, debates)  # any planned/available fault line missing?
  r3 = anachronism_gate(draft)                 # every modern label attributed?
  if r1.all_pass and r2.no_gaps and r3.clean: ACCEPT
  else:
    if r2.gaps:   expand_retrieval(r2.gap_queries)   # → new ControversyFrames, back to §2
    if r1.fails:  edit_unsupported_spans(r1.failures) # RARR edit, not regenerate
    if r3.fails:  edit_anachronistic_spans(r3.failures)
```

Bounded: max 2 expansion rounds (vs the current single 3-call sufficiency round, F9). The stop condition is **evidence sufficiency + completeness**, not a char count — the precise reversal of F9's length-driven premature fallback.

---

## 6. K2.7 integration + budgets

### 6.1 Two-tier, one seam (reconciles GOAL-Fireworks with model_resolution-Moonshot)

| Role | Model | Why | Where |
|---|---|---|---|
| Planner (shape classify) | Fireworks `kimi-k2p6`, JSON-mode, ~1k out | cheap, fast, tool/JSON proven on Fireworks | `PlanResearch` node |
| ReAct retrieval (tool-calling) | Fireworks `kimi-k2p6` | tool-calling documented Fireworks-only (`llm_service.py:873-874`) | `NativeAgentLoop` |
| Retrieval subagents (§3.4) | Fireworks `kimi-k2p6` (sonnet-tier) | cheap-tier per memory note | per-frame builders |
| **Dialectical synthesis** | **Moonshot `kimi-k2.7-code-highspeed`** | best scholarly prose, reasoning_content, 262k ctx (model_resolution §b/c) | `DialecticalSynthesis` node |
| Hard-query synthesis (deep tier) | Moonshot `kimi-k2.7-code` | richer reasoning, slower | when `budget_hint=="deep"` |
| Verification referees | Fireworks `kimi-k2p6` | cheap, isolated short checks | §5 |

Only the synthesis call leaves Fireworks. `llm_service.py` (`PROVIDER_CONFIGS`, `:75`/`:106-113`) gains a `MOONSHOT_MODEL`/`MOONSHOT_THINKING_MODEL` env (defaults `kimi-k2.7-code-highspeed` / `kimi-k2.7-code`), and `_openai_compatible_payload` **clamps `temperature=1.0` when `provider==KIMI`** (model_resolution §c — mandatory, else 400). Fallback chain per model_resolution: `kimi-k2.7-code-highspeed → kimi-k2.6 → fireworks/kimi-k2p6 → gemini-3.1-pro-preview`. The K2.7 swap is a one-line env change at exactly these points (matches GOAL's "model-agnostic, one-line swap" constraint).

### 6.2 Budgets (reconcile with the latency work, F9/F10)

- **Synthesis `max_tokens` = 8000** (model_resolution §c: reasoning eats most; 5000 floor). This *replaces* the 8k streaming cap that currently collides with a 10–15k *char* floor (F10) — because §4.5 deletes the char floor (content gate, not length gate), the collision is gone.
- **Reasoning is a feature, not a stall:** `_await_with_heartbeat`/`_stream_render` max_wait raised for the synthesis call (K2.7-code reasoning runs ~95s, highspeed ~55s, model_resolution §b) — and the heartbeat streams `reasoning_content` as a "thinking" trace so the UI shows progress instead of abandoning to fallback (F9).
- **Tool budget** per §2.5: shape-aware (~45 for survey/transmission), real stop = completeness critic.
- **Cost control:** only 1 synthesis + ≤2 expansion rounds hit K2.7; everything else stays on cheap Fireworks K2.6. The expensive tier is touched O(1) per query.

---

## 7. Migration plan + G2 measurement

### 7.1 Staged migration (behind `SCHOLAR_RAG=true`, default off until eval-green)

| Stage | Change | Files | Risk |
|---|---|---|---|
| **M0** | Edge store: keep `relation`/`direction`; add `DialecticalEdge` + `dialectical_edges` to state | `evidence_collector.py:178-192,102-139`; `state.py:387` | low, additive |
| **M1** | New tools `find_debates`, `build_controversy_frame`; register; debate-first system prompt; repoint dead `query_scholarly_consensus` | `agents/tools/*`, `tools.py`, `react_loop.py:566-600`, `scholarly_agent.py:640` | medium |
| **M2** | `ResearchPlan` model + `PlanResearch` node (replaces facet picker); 6 shapes | `state.py`, `graph_nodes.py:1082-1271` | medium |
| **M3** | `ControversyFrame` dossier assembly + bilingual `_en` join; edge slot in context pack | `state.py`, `graph_nodes.py:3377-3484`, `evidence_collector.py` | medium |
| **M4** | `DialecticalSynthesis` node (replaces `DraftClaimLedger`+`RenderGroundedAnswer`); cite-as-you-write prompt; `build_provenance_ledger` post-pass; **delete** facet template + 220-char paste | `graph_nodes.py:580-680,3575-3733,4169+,5189-5429,5471-5497` | **high** (core) |
| **M5** | Verification loop: extend referee (NLI/marker-resolve), add completeness critic + anachronism gate + iterate | `citation_verifier_v2.py`, `scholarly_agent.py:729-869` | medium |
| **M6** | K2.7 wiring: `MOONSHOT_MODEL` env, temp=1 clamp, fallback chain, heartbeat for reasoning | `llm_service.py:75,106-113`, `scholarly_agent.py:147-164,1486,1569` | low |
| **M7** | Flip default, delete dead template code, remove `_inject_passage_quotations` post-hoc patch (F10) | flag removal | low |

M0+M1 alone make edges visible (validate "edges > 0" early). M4 is the irreversible core. Each stage is independently testable; the flag lets old/new run side-by-side on the trigger question.

### 7.2 How G2 measures it

The G2 eval harness (citation-F1 + faithfulness, now that CitationVerifierV2 parses) measures Scholar-RAG **old-vs-new** on the same question set:

- **Citation-F1 (ALCE-style):** precision = fraction of inline `[passage_*]/[P_*]` markers whose dossier source entails the sentence; recall = fraction of attributed positions that carry a marker. Cite-as-you-write (§4.3) should drive both up sharply vs the edge-blind template (which scores ~0 on relational claims).
- **Faithfulness:** every Greek/Latin quote traces to a dossier passage id (anti-fabrication gate).
- **New rubric metrics (the scholar-grade dimensions the template can't score on):**
  - *Edge-use count* — distinct dialectical edges cited in the answer (target > 0; trigger expects ≥3 fault lines).
  - *Debate coverage* — planned/available debate nodes vs covered (completeness critic, §5.2).
  - *Attribution rate* — modern labels voiced as attributed vs asserted (anachronism gate, §5.3).
  - *Non-repetition* — n-gram self-overlap across sections (catches the "same node pasted 4×" failure).
- **The trigger question** ("big open debates about free will in antiquity") is the canonical regression test: success = enumerates discovery-of-will (Bobzien⟂Frede⟂Dihle), Stoic-compatibilism, Alexander-libertarian (Sharples), Carneadean-transmission (Amand⟂Ramelli); uses ≥3 `opposes`/`critiques` edges; every position cited; genuine non-repeating prose; passes all three referees. Frozen as a snapshot test so the template can never silently return.

---

## Anti-goals honored

No vector store / embeddings anywhere (every retrieval is KG traversal / lexical / lemmatic / tree-nav / `has_translation` join). No fixed answer template (adaptive movements from frames). No truncated node-description pasting (220-char paste deleted; full untruncated passages). No modern label asserted as fact (anachronism gate + attributed-voice prompt). Provenance ledger is a byproduct of synthesis, not its generator.
