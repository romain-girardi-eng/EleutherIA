# G6 Design Proposal #2 — Scholar-RAG: a vectorless agentic graph-RAG that researches like a scholar

**Headline:** Replace the deterministic facet-template render with a **dialectical synthesis driven by a pre-assembled "controversy graph"** — an explicit bipolar argumentation structure (positions, `opposes`/`critiques`/`responds_to` edges, page-grounded attributions, contested passages) that the agent *builds first as data* and the model then *reasons over and narrates*, so that the prose is a function of the relational evidence and the provenance ledger falls out as a byproduct rather than being its generator.

**Single most important novel idea — the Controversy Graph as the unit of synthesis.** Today the unit of synthesis is the *node* (a label + a 220-char description), and the renderer is edge-blind because edges were never the unit. Proposal #2 changes the unit of synthesis from "a list of nodes" to "a set of **Controversy Graphs**": each is a small, self-contained bipolar argument framework — `{claim, supporters[], attackers[], opposes/critiques/responds_to edges between them, the primary passages each side contests, a DF-QuAD-style strength on each position}`, with every position page-grounded and attributed. The retrieval phase's explicit *goal* is to populate these structures (not to collect nodes); the synthesis phase's explicit *input* is these structures (not a node list). This single reframing dissolves F1–F8 at once: edges can no longer be dropped (they are the skeleton of the unit), the prompt can no longer be edge-blind (the unit is edges), the template can no longer paste node descriptions (there is no facet template — there is a controversy to narrate), and the ledger is reconstructed *from* the narrated controversy graph rather than generating it.

---

## 0. Where this diverges from the G6 sketch, and why

The G6 sketch lists six parts as a pipeline (plan → argument-first retrieval → dossier → synthesis → verify → ledger-as-byproduct). Proposal #2 keeps all six but makes two deliberate departures, argued below:

1. **The "argument framework" (research_sota #5, ArgLLMs / DF-QuAD) is promoted from an optional representation to the *central data structure of the whole pipeline*.** The sketch treats the dossier and the disagreement layer as two separate things the synthesis reads. I fuse them: the dossier **is** a list of Controversy Graphs. This is the only structural choice that makes "attribute positions, never assert" *mechanically enforceable* rather than a prompt instruction — a position is a typed object with a holder, a strength, and a citation; the model narrates objects, it cannot assert a label as fact because the label only ever appears *inside* an attributed position object. It also makes the anti-anachronism gate trivial (any modern label like "libertarian"/"compatibilism" that appears outside a `held_by` attribution is a gate failure, checkable on the graph, not the prose).

2. **On the model: I follow `model_resolution.md` (Moonshot `kimi-k2.7-code-highspeed`) over the goal-doc's "Fireworks-only / no Moonshot direct" line, but make it config-gated and reversible.** The goal doc and `model_resolution.md` are in direct tension: the doc says use Fireworks K2.6 now and swap to K2.7 "when available on Fireworks"; the resolution doc empirically found K2.7 exists *only on Moonshot direct* (Fireworks 404s) and produces the best scholarly prose. I resolve this by making the synthesis tier a single config point (`SCHOLAR_SYNTH_MODEL`) with a fallback chain that starts at Moonshot K2.7-highspeed and falls through to Fireworks K2p6 to Gemini — so the architecture is model-agnostic (satisfies the doc's hard constraint) while the *default* uses the empirically-best model (satisfies the resolution doc). This is the honest reconciliation; see §6.

Everything else (vectorless, agentic/model-driven, iterative retrieval kept, no embeddings) is held exactly as the constraints demand.

---

## 1. Question → scholarly-answer-shape planner

### The shapes

Six shapes, each a *named target output structure* plus a *graph-pattern recipe* plus a *retrieval-depth budget*. This replaces `_default_research_facets` (`graph_nodes.py:1082-1271`) entirely.

| Shape | Trigger (intent, not keyword) | Output skeleton | Primary graph pattern |
|---|---|---|---|
| **survey-of-debates** | "what are the open debates / controversies / disputes about X" | N Controversy Graphs, one per live debate, ranked by graph centrality | `debate`/`controversy` nodes → `participates_in`/`contributes_to` → positions → `opposes`/`critiques`/`responds_to` |
| **position-comparison** | "X vs Y", "how does A differ from B", "did Bobzien agree with Frede" | 1–3 Controversy Graphs scoped to the named parties | named scholar/school nodes → their `scholar_position_*`/`scholarly_argument_*` → dialectical edges between them |
| **concept-genealogy** | "origin/emergence/history of concept C", "who invented the will" | a genealogy spine (chronological) + the historiographical Controversy Graph *about* that genealogy | concept node → `precedes`/`influences`/`develops` chain + the meta-debate node (e.g. `debate_origins_notion_of_will_modern_paradigm`) |
| **transmission-trace** | "how did argument A reach author Z", "Carneades' influence on Origen" | a participant chain + the transmission Controversy Graph (Amand⟂Ramelli) | `participates_in` chain on a transmission `debate` node + `opposes` edges over the source-attribution dispute |
| **primary-text-exegesis** | "what does passage P / author A in work W say about C" | passage-anchored exegesis: bilingual text → philological reading → positions it grounds | passage node → `has_translation` + `grounds`/`contributes_to` → the debates/arguments citing it |
| **doxographical-synthesis** | "what did the Stoics hold about fate" (doctrine, low controversy) | doctrine statement + attested sources + minority dissent | school/person node → concept edges + passages; controversy graphs only where dissent edges exist |

### How the plan drives retrieval

The planner is **one LLM call** (cheap tier — Gemini Flash / Fireworks small, not K2.7) that emits a typed `ResearchPlan`:

```json
{
  "shape": "survey-of-debates",
  "scope_filter": {"period_in": ["Presocratic","Classical","Hellenistic","Imperial","LateAntiquity"], "exclude_period": ["Medieval","Modern"]},
  "seed_intent": ["free will", "fate", "moral responsibility", "the will"],
  "controversy_budget": {"min": 3, "max": 6},
  "retrieval_dag": [
    {"step":"enter_debates", "tool":"query_controversies", "args":{"about":"free will antiquity","limit":6}},
    {"step":"expand_positions", "depends_on":"enter_debates", "tool":"get_controversy_structure"},
    {"step":"ground_passages", "depends_on":"expand_positions", "tool":"read_passages", "pair_translations":true}
  ],
  "answer_skeleton": ["thesis","per-debate sections","cross-cutting tension","hedged outlook"]
}
```

The `shape` selects the `answer_skeleton` (replacing the fixed Definition/Textual-Basis/Counterpoint facets) **and** the `retrieval_dag` template (a DAG of graph-pattern fetches, research_sota #4 + #6 + #DAG). The skeleton is *adaptive* — `survey-of-debates` produces one section per surfaced controversy, `primary-text-exegesis` produces one section per passage; there is no fixed section count, which kills F6 and the F9 char-floor mismatch (the floor becomes "one grounded section per controversy/passage actually retrieved", computed from the dossier, not a hardcoded 10k chars).

**Routing precedes planning** (Adaptive-RAG, research_sota #4): a no-retrieval / single-controversy / multi-controversy regime is set by the same call, matching budget to difficulty. `ClassifyQueryType` (`graph_nodes.py`) is rewritten to emit `shape` + `regime` instead of the current `query_type`/`complexity`.

---

## 2. Argument-structure-first VECTORLESS retrieval

This is where "0 edges" is killed at the root. Three changes: a new retrieval primitive, a dual-channel loop, and a relational system prompt.

### 2a. New tool: `query_controversies` + `get_controversy_structure`

The registry today is entity/passage-centric (8 tools, none debate-aware — F3). Add two **relational** tools (vectorless: pure KG traversal + lexical match on labels):

- **`query_controversies(about, period_filter, limit)`** → returns `debate`/`controversy`/`position` nodes matching the topic, ranked by *dialectical degree* (count of incoming `participates_in`/`contributes_to` + count of `opposes`/`critiques`/`responds_to` edges in their neighborhood). This is the missing "enter via debate nodes" affordance (kg_affordances §8 step 1). Implemented as a SQL query over `kg_nodes WHERE type IN ('debate','controversy','position')` joined to an edge-degree subquery — no model call, no embeddings.

- **`get_controversy_structure(debate_id)`** → returns a fully-expanded **Controversy Graph** object in one call:
  ```
  {
    debate: {id,label,description},
    participants: [{node_id, label, type, side?}],            # via participates_in / contributes_to
    positions: [{node_id, label, held_by, page_ref, base_strength}],  # scholar_position_* / scholarly_argument_*
    dialectical_edges: [{src, relation: opposes|critiques|responds_to|supports, dst}],
    contested_passages: [{passage_id, en_id, work, locus}]    # via contributes_to / grounds from passages
  }
  ```
  This is the single primitive that the synthesis consumes. It traverses exactly the edges kg_affordances §2/§5 enumerated (244 critiques + 57 responds_to + 11 opposes + supports), and **keeps `relation` + `direction`** — the literal F1 fix, now structural because the tool's return type *is* the edge set.

Both register in `tools.py`; `scholarly_agent.py:640`'s dead `query_scholarly_consensus` ref is repointed to `query_controversies`.

### 2b. Dual-channel retrieval (research_sota #2)

For every sub-claim the agent issues the question in **two shapes**:
- **Relational channel** (new, primary for debate/comparison shapes): the agent names the *edge pattern* to fetch (`debate → positions → opposes`), executed by `get_controversy_structure`.
- **Lexical/lemmatic channel** (existing): `search_nodes` + `search_passages` (ts_rank + lemmatic) for entities and primary text the relational channel didn't reach.

The relational channel surfaces the structure lexical search misses — exactly the "0 edges → garbage" failure. The agent runs both and merges via the existing RRF, but the **Controversy Graph is the spine** the lexical hits attach to (a stray passage hit becomes a `contested_passage` on the nearest controversy, or a standalone exegesis unit).

### 2c. How it stops being edge-blind — the four structural locks

1. **Ingestion (F1):** `evidence_collector._ingest_get_neighbors` (`evidence_collector.py:178-192`) keeps `relation`+`direction`; a new `edges: list[EdgeRecord]` and `controversy_graphs: list[ControversyGraph]` container is added to `RAGState` (`state.py`) and `populate_state` writes them. Edges can no longer be silently dropped.
2. **Tool surface (F3):** the two relational tools exist and the planner's DAG *requires* them for debate/comparison/genealogy/transmission shapes.
3. **System prompt (F3):** `NATIVE_SYSTEM_PROMPT_TEMPLATE` (`react_loop.py:566-600`) is rewritten to instruct: *"You are mapping a scholarly controversy. First enter via `query_controversies`; for each, call `get_controversy_structure` to get who-opposes-whom; only then read the passages each side contests. Never write a position without its holder and page reference."* Search-R1-style interleaving (research_sota #sec): the agent emits relational fetches inside its reasoning trace.
4. **Context pack (F2):** `_build_context_pack` (`graph_nodes.py:3377-3484`) gains a `## Controversy Graphs` layer that serializes each `ControversyGraph` (positions with holders + page refs, the dialectical edges as `A —opposes→ B` lines, the contested passages). `ContextPack` in `state.py` gets a `controversy_graphs` field. The synthesis prompt now *structurally cannot* be edge-blind — the edges are a top-level section.

---

## 3. Evidence dossier assembly

The dossier is **a list of Controversy Graphs plus a pool of standalone exegesis units**, each fully grounded. Structure:

```
ScholarDossier:
  controversies: list[ControversyGraph]      # the spine (see §2a)
  exegesis_units: list[ExegesisUnit]         # passages not bound to a controversy
  genealogy_spine: list[GenealogyLink]?      # only for concept-genealogy shape
  provenance: ProvenanceLedger               # built incrementally, see §4

ControversyGraph (enriched from §2a):
  ... + positions now carry full text:
  positions: [{
     node_id, label,
     held_by: {scholar, publication, page_ref},   # "Bobzien 1998, p. 280"
     stance_summary,                               # untruncated description
     base_strength: float,                         # DF-QuAD seed (see below)
     grounds_in: [passage_ref]                     # which primary text it reads
  }]
  contested_passages: [{
     passage_id, original_text,                    # FULL, untruncated, polytonic diacritics
     en_id, english_text,                          # FULL English from the _en pair
     work, locus, cts_urn,
     contested_by: [position_node_id, ...]         # which positions read it differently
  }]
```

### Non-negotiables (each fixes a named affordance gap, kg_affordances §7/§9)

- **Untruncated.** `read_passages` returns full text; the dossier never truncates (kills F5's `truncate_text(...,220)` and the A-RAG "read full chunks on demand" principle, research_sota #3). The 220-char paste sites (`graph_nodes.py:4192,4211,4308,4401`) are deleted with `_derive_claim_ledger_fallback`.
- **Bilingual pairing.** Every `contested_passage` is fetched *with* its `_en` counterpart via the `has_translation`/`translation_of` edges (2,953 pairs, kg_affordances §4) — original for verbatim quotation, English for the model to reason over. `read_passages` gains a `pair_translations=true` mode that resolves `passage_X → passage_X_en` automatically.
- **Page-grounded positions.** Each modern position carries `held_by.page_ref` (e.g. "Sharples 1983, p. 22", "Bobzien 1998, p. 280") pulled from the `scholar_position_*`/`scholarly_argument_*`/`publication` node metadata. A position with no page ref is flagged `provenance:weak` and the completeness critic (§5) is told to seek one.
- **Provenance, built as we go.** Each object records *how it was retrieved* (which tool, which edge traversed, confidence). This becomes the ledger byproduct (§4).

### Subagent isolation (research_sota #6)

For multi-controversy shapes, each controversy is populated by a **retrieval subagent** (sonnet/opus tier per the memory note, never the main loop) that does the messy `get_controversy_structure` + `read_passages` work and returns *only* the compact `ControversyGraph` (a few k tokens). The lead model receives clean dossiers, keeping K2.7's 262k context uncluttered for reasoning, not for raw retrieval scratch.

---

## 4. Dialectical scholarly SYNTHESIS — the core

This is the module that **replaces the facet template** (`_render_answer_fallback` `graph_nodes.py:3575-3733` is deleted; `RenderGroundedAnswer` `graph_nodes.py:5501` is rewritten; `DraftClaimLedger` `graph_nodes.py:5189-5429` is *inverted*, see §4d).

### 4a. Pre-synthesis: deterministic gradual semantics on the controversy graph (ArgLLMs / DF-QuAD, research_sota #5)

Before the model writes a word, run a **deterministic** DF-QuAD pass over each `ControversyGraph`:
- seed each position's `base_strength` from graph signal (citation count of its publication, number of grounding passages, recency) — *not* from the model, so it is traceable and contestable;
- propagate `supports` (raises) and `opposes`/`critiques`/`refutes` (lowers) into a final per-position strength;
- the result is **dialectic-as-data**: "Frede's Epictetus-thesis is attacked by Bobzien, Dihle, Irwin, Blackson; supported by Kahn-adjacent" → a strength ordering the model *reports*, never invents.

This is the load-bearing mechanism for "attribute, never assert": the verdict is a function of the edge structure, the model narrates the structure, and because every position has a holder + page ref, no position is ever stated as fact. It directly serves success criteria (a)/(c).

### 4b. The synthesis prompt (replacing `RENDER_ANSWER_PROMPT` `graph_nodes.py:580-680`)

The new prompt is **dossier-driven, not facet-driven**, and its instructions are *reasoning steps*, not a template. Sketch (Kimi K2.7, reasoning model — the `reasoning_content` phase does the weighing before prose):

```
SYSTEM:
You are a historian of ancient philosophy writing for a scholarly audience.
You will receive a DOSSIER of CONTROVERSY GRAPHS and EXEGESIS UNITS, fully
grounded. Write a single, coherent scholarly essay that answers the QUESTION.

ABSOLUTE RULES:
- Attribute every interpretive position to its holder with a page reference,
  exactly as given in the dossier (e.g. "Bobzien (1998, p. 280) argues..."). 
  Modern labels — "libertarian", "compatibilism", "the will", "indeterminist"
  — may ONLY appear inside an attributed position. NEVER assert them as
  historical fact in your own voice.
- Quote primary text in the ORIGINAL language (verbatim, with diacritics) AND
  give the English. Quote ONLY text present in the dossier. Inventing or
  completing Greek/Latin is academic fraud — if it is not in the dossier, do
  not quote it; paraphrase in English instead.
- Represent disagreement faithfully. Where the dossier's gradual-semantics
  strengths show a position is heavily attacked, say so and hedge accordingly.
  Do not adjudicate disputes the field has not settled.
- Cite as you write: every attributed position and every primary quotation
  carries its source id inline ⟦node_id⟧ / ⟦passage_id⟧ at the point of use.

REASONING STEPS (think before writing):
1. THESIS: From the controversies, state what genuine scholarly question the
   user is really asking and what the honest answer-shape is.
2. MAP THE FAULT LINES: For each ControversyGraph, identify the contested
   claim, the opposing camps (from opposes/critiques edges), and who holds
   what (held_by). Note the DF-QuAD strength ordering.
3. GROUND: For each fault line, identify the primary passage(s) each side
   reads, and how their readings differ.
4. COUNTER-EVIDENCE: For each position you report, name the strongest attack
   on it that the dossier contains. A controversy with no reported counter is
   a failure of this step.
5. HEDGE & STRUCTURE: Choose an essay structure that fits the QUESTION
   (per-debate sections for a survey; chronological spine for a genealogy;
   point-by-point for a comparison). Conclude with what remains open, not a
   false verdict.

Then WRITE the essay following the answer_skeleton from the plan.
```

The prompt **adapts structure to shape** (skeleton from §1), mandates **counter-evidence per claim** (DF-QuAD attacks), forces **inline cite-as-you-write** (research_sota #8), and bans assertion of labels (anti-anachronism, enforced again at the gate §5). The Bobzien⟂Frede example that is currently *hardcoded* in the prompt (F7, `graph_nodes.py:673-677`) is removed — the real controversy graphs replace it.

### 4c. Why this is genuine scholar-grade prose, not a ledger render

- It reasons over **relations** (the fault lines), so it can say "Frede dates the will to Epictetus; Bobzien denies there was a free-will problem to have a will *about*; Dihle pushes it to Augustine — the dispute is unsettled" — a sentence the facet template structurally cannot produce.
- It grounds in **bilingual primary text**, quoting `τὸ ἐφ᾽ ἡμῖν` from `passage_alex_fat_12` *and* its English, with the locus.
- It **hedges from the data** (DF-QuAD strengths), not from a canned "Counterpoint and Nuance" header.
- Structure is **chosen by the model for the question**, not stamped from facets.

### 4d. Provenance ledger as byproduct (reversing F8)

Today: ledger → prose (`build_render_prompt` reads `state.claim_ledger`). Inverted: **prose → ledger**. The synthesis emits prose with inline `⟦node_id⟧`/`⟦passage_id⟧` markers (cite-as-you-write). A deterministic post-pass walks the finished prose, harvests every marker, and *reconstructs* the `ProvenanceLedger` (claim span → cited source → resolved node/passage). The ledger is now a faithful audit of what was actually written, not the thing that wrote it. `DraftClaimLedger` is repurposed from "generate claims to render" into "extract claims from rendered prose for verification" — same module, reversed dataflow. Each extracted claim is tagged `assertion | attributed-position | interpretation` (Claim-Level Auditability, research_sota #8) so the verifier can apply different rules per type.

---

## 5. Scholar-grade verification loop

Three referees, run after synthesis, gated by an **iterate condition** (research_sota #1, #7). Each operates over the dossier + the extracted claim ledger, **not free memory** (CoVe's load-bearing trick).

### 5a. Adversarial citation referee (CitationVerifierV2, NLI-style)

Existing `citation_verifier_v2.py` (JSON bug now fixed). For a sample of `assertion`/`attributed-position`/quotation claims: does the cited passage/node **entail** the sentence? (ALCE NLI, research_sota #8). REJECTED/MISSING claims are not deleted wholesale — **RARR-edit** the offending span only (preserve the rest, research_sota #7). Quotation claims get an exact-substring check against the original passage text (zero-tolerance for invented Greek/Latin — the integrity policy).

### 5b. Completeness critic (NEW — fixes F11)

A focused LLM call: *"Here are the controversy graphs the retrieval surfaced: [list of debate ids + their opposes edges]. Here is the answer. Which surfaced controversy, opposing position, or `opposes` edge did the answer fail to address?"* Because the dossier *holds* the graph's real debates (§3), this critic can name the specific miss ("you covered discovery-of-will but dropped the Amand⟂Ramelli transmission dispute"). Its output is a **gap list** that becomes the next retrieval/synthesis query (research_sota #1 Query Expansion).

### 5c. Anti-anachronism gate (NEW — fixes F11)

Two-stage, mostly deterministic:
- **Structural (cheap, deterministic):** scan the prose for the modern-label lexicon (`libertarian`, `compatibilism`, `incompatibilism`, `hard/soft determinism`, `the will` as a faculty, `free will problem`). Any occurrence **outside** an attributed-position span (per the §4d claim tags) is a gate failure → RARR-edit to attribute or remove. This is exactly the project's "always attributed" rule (Phase 11/12 in memory), now machine-enforced.
- **Semantic (LLM, only on flagged spans):** confirm the attribution is correct (the label is genuinely the scholar's, not pinned to the wrong holder).

### 5d. Iterate condition

```
Accept iff:
  citation_referee.unsupported == 0  (after RARR edits)
  AND completeness_critic.gap_list == []  (or all gaps marked "graph has no evidence")
  AND anachronism_gate.violations == 0
  AND every reported controversy has ≥1 counter-evidence span (§4b step 4)
Else: form a targeted expansion query from (gap_list ∪ unsupported_claims),
  re-enter retrieval (§2) for ONLY the missing structure, rebuild the affected
  ControversyGraph, re-synthesize. Cap at 2 expansion rounds (budget §6).
```

This is the Draft→Verify→Expand loop (research_sota #1) that "only stops when evidence is sufficient" — the structural cure for the trigger garbage. It replaces the current single 3-call sufficiency round (F9) and the silent template fallback (F4/F7): there is **no template fallback**; on hard failure after 2 rounds the system returns the best grounded partial answer *with an explicit "the graph does not hold evidence on X" note*, never a node-paste.

---

## 6. K2.7 integration + budgets

### Model tiering (reconciling the goal doc with model_resolution.md)

| Stage | Tier | Default model | Rationale |
|---|---|---|---|
| Planner / router (§1) | cheap | Fireworks small / Gemini Flash | classification, latency-sensitive |
| Retrieval subagents (§3) | mid | sonnet (per memory note) | tool-heavy, isolated context |
| Gradual-semantics (§4a) | none | deterministic code | no model |
| **Dialectical synthesis (§4)** | **quality** | **`kimi-k2.7-code-highspeed` (Moonshot)** | best scholarly prose + reasoning_content weighing (model_resolution.md) |
| Verification referees (§5) | mid | sonnet / Fireworks K2p6 | focused, short, isolated |

**Synthesis config (single point, reversible):**
```python
SCHOLAR_SYNTH_MODEL   = env("SCHOLAR_SYNTH_MODEL", "kimi-k2.7-code-highspeed")
SCHOLAR_SYNTH_THINK   = env("SCHOLAR_SYNTH_THINK", "kimi-k2.7-code")  # hard queries
SCHOLAR_SYNTH_FALLBACK = ["kimi-k2.6",
                          "accounts/fireworks/models/kimi-k2p6",
                          "gemini-3.1-pro-preview"]
```
Wiring in `llm_service.py` (the F12 fix): add the Moonshot provider with `base_url=https://api.moonshot.ai/v1`, `env_key=MOONSHOT_API_KEY`, and **clamp `temperature=1.0` for the KIMI provider** in `_openai_compatible_payload` (Moonshot rejects any other value — model_resolution.md (c)). `reasoning_content` is already parsed. The K2.7→future swap is a one-line env change.

> **Tension acknowledged:** the goal doc says "do NOT use Moonshot direct; Fireworks-only." `model_resolution.md` empirically established that K2.7 *exists only on Moonshot* and is materially better for this exact task. I default to Moonshot **for the synthesis stage only**, gated behind `SCHOLAR_SYNTH_MODEL` with a Fireworks fallback, so the studio's Fireworks-first posture is one env var away and the architecture stays model-agnostic. If Romain wants strict Fireworks, set `SCHOLAR_SYNTH_MODEL=accounts/fireworks/models/kimi-k2p6` and the pipeline is unchanged. **This is the one choice to confirm.**

### Budgets (reconciling with latency work, F9)

- **Token budget:** synthesis `max_tokens=8000` (model_resolution.md: ≥5000 needed because `reasoning_content` eats the budget; 8000 safe). Critically, **the char-floor that demanded ~10–15k chars is removed** (F9/F10) — the adaptive skeleton (§1) sets the floor to "one grounded section per surfaced controversy/passage," computed from the dossier, so the token cap and the length requirement can no longer contradict. This single change dissolves the F9 "physically can't reach the floor → fallback" trap.
- **Tool budget:** raise COMPLEX `MAX_TOOL_CALLS` (`react_loop.py:91-115`) but make it *adaptive to controversy count* from the plan (survey-of-6-debates gets more `get_controversy_structure` calls than a single exegesis). Subagent isolation (§3) keeps per-agent budgets small.
- **Latency:** K2.7-highspeed (~55s) for synthesis; subagents run in parallel (one per controversy). Verification referees are short/parallel. The 2-round expansion cap bounds worst case. Streaming render keeps the SSE path (the UI path); the streaming token cap (`scholarly_agent.py:147-164`) is raised to 8000 to match the blocking path (F9 fix — the two paths must agree).

---

## 7. Migration plan + G2 measurement

### Staged migration (each stage independently shippable, behind a flag)

`SCHOLAR_RAG=true` gates the whole new path; default off until the eval clears it.

| Stage | Change | Files | Risk |
|---|---|---|---|
| **S0 — edge survival** | keep `relation`+`direction`; add `edges`/`controversy_graphs` to state | `evidence_collector.py:178-192,102-139`; `state.py` | low; structural prerequisite |
| **S1 — relational tools** | `query_controversies`, `get_controversy_structure`; register; repoint dead ref | `agents/tools/` (2 new), `tools.py`, `scholarly_agent.py:640` | low; additive |
| **S2 — controversy graph in pack** | `## Controversy Graphs` layer; `ContextPack.controversy_graphs` | `graph_nodes.py:3377-3484`; `state.py` | low |
| **S3 — planner** | shape classifier + ResearchPlan + retrieval DAG; delete facet picker | rewrite `ClassifyQueryType`; remove `_default_research_facets` `1082-1271` | med |
| **S4 — dossier** | ScholarDossier = controversy graphs + exegesis; bilingual pairing; page refs; subagents | `_build_scholarly_dossier` `1512`; `read_passages` pair mode | med |
| **S5 — synthesis core** | DF-QuAD pass + new prompt; delete facet template + 220-char pastes; invert ledger | `RenderGroundedAnswer` `5501`; delete `_render_answer_fallback` `3575-3733`, `_derive_claim_ledger_fallback` `4169+`; invert `DraftClaimLedger` `5189-5429` | high; the heart |
| **S6 — verification loop** | completeness critic + anachronism gate + RARR edit + iterate condition | new stages near `_run_citation_verifier_v2` `729-869`; `citation_verifier_v2.py` | med |
| **S7 — model wiring** | Moonshot provider, temp clamp, `SCHOLAR_SYNTH_*` config, fallback chain | `llm_service.py:106-113`, `_openai_compatible_payload` | low |
| **S8 — budgets** | adaptive floor, token-cap reconciliation, streaming cap = blocking cap | `graph_nodes.py:3987-3993`; `scholarly_agent.py:147-164` | low |

Stages S0–S2 are safe to ship immediately (edges start surviving even before the new synthesis). S5 is the cutover; keep the old path behind `SCHOLAR_RAG=false` for one release for A/B.

### Measurement by the G2 eval (`tests/eval/run_eval.py`)

The harness already computes **citation P/R/F1** (`eval_lib/scoring.py:citation_prf`), entity/work recall, keyword hit rate, and (with `ELEUTHERIA_EVAL_JUDGE=1`) adversarial `gold_claims` judging via CitationVerifierV2, plus the `must_not_appear.jsonl` fabrication scan. Concretely:

1. **Baseline capture** (old path): `python tests/eval/run_eval.py --output data/goals/g6/baseline_template.json` against the current template pipeline.
2. **New-path capture:** same with `SCHOLAR_RAG=true` → `--output data/goals/g6/scholar_rag.json`.
3. **Compare:** `python tests/eval/run_eval.py --compare baseline_template.json scholar_rag.json`.
4. **Add survey/comparison cases to `queries.yaml`** — the harness today is entity/concept-author heavy and has no debate-survey case. Add the trigger question and its kin with `query_type: school-debate`, `expected_entities` = the debate nodes + scholar positions (kg_affordances §8 lists the exact IDs: `debate_discovery_of_will`, `scholar_position_frede_will_originates_epictetus`, etc.), and `gold_claims` asserting the fault lines. This is what makes the eval *able to see* the improvement — without these cases the harness can't reward edge usage.
5. **New metrics to add to `run_eval.py`:** (a) **edge-usage count** (number of `opposes`/`critiques`/`responds_to` edges referenced in the answer's ledger — must be >0, success criterion b); (b) **attribution rate** (fraction of modern-label occurrences that are inside an attributed span — anachronism gate, success criterion c); (c) **counter-evidence coverage** (fraction of reported controversies with a reported attack). These three operationalize G6 success criteria (b)/(c)/(e) that the current harness doesn't capture.

**Success bar (on the trigger question + new debate cases):** citation-F1 up vs baseline; edge-usage >0; attribution rate = 1.0; counter-evidence coverage = 1.0; zero `must_not_appear` hits; qualitative scholar rubric (thesis present, ≥3 real graph debates enumerated — discovery-of-will, Alexander-libertarian, Carneadean-transmission, Stoic-compatibilism — each attributed + page-grounded, genuine prose with no repetition/truncation). Old-vs-new on the exact trigger question is the headline gate.
