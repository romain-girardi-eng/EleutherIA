# Scholar-RAG — Implementation Blueprint (G6)

> Maps `ARCHITECTURE.md` onto the exact files + functions to change/add in this codebase,
> in dependency order, each step small + independently reviewable. Everything ships behind
> `SCHOLAR_RAG=true` (default off until M5 passes eval). Package root for all paths below:
> `graphrag/src/eleutheria_graphrag/`.

All line numbers are from the failure-map trace and verified against the live tree
(2026-06-16). The reference draft of the core synthesis function is in
`data/goals/g6/reference_synthesis.py` (blueprint artifact, NOT applied).

---

## Step list (dependency-ordered; each = one reviewable PR)

### Step 0 — M0a: Reachability probe (GATE on the whole edifice — must pass before M4)
**New:** `tests/g6/test_reachability_probe.py` (offline DB probe, not in CI gate).
Probe asserts the highest-risk assumption: that `find_debates` → `build_controversy_frame`
can surface the 11 `opposes` edges from real debate/position nodes within 2 hops.
- Query `kg_edges` for `relation IN ('opposes','critiques')` incident on `debate_*` /
  `scholar_position_*` / `scholarly_argument_*` / `argument_cafma_*` nodes.
- Confirm the two known empty debate nodes (`debate_origins_notion_of_will_modern_paradigm`
  = no out-edges; `debate_carneadean_antiastrology_tradition` = 0 grounded passages) and
  that their fault lines are reachable via the position/argument fallback (§2.2 fallback).
- **Output:** a one-page `data/goals/g6/reachability_report.json` listing, per headline
  debate, the seed node, the reachable opposing positions, and the grounding passages.
**If a fault line is NOT reachable, the fallback in M1 must be widened before M4.**

### Step 1 — M0b: Edge survival at ingestion (the literal F1 fix)
**Files:** `agents/state.py`, `agents/evidence_collector.py:102-139,161-176,178-192`.
- `state.py`: add `DIALECTICAL_RELATIONS` set, `DialecticalEdge` pydantic model, and
  `RAGState.dialectical_edges: list[DialecticalEdge]` (default empty).
- `evidence_collector.py`: in `_ingest_get_neighbors` (L178-192), for every edge whose
  `relation ∈ DIALECTICAL_RELATIONS`, append a `DialecticalEdge` retaining BOTH endpoints
  + `relation` + `direction` (today only `edge_node_id` survives; `relation`/`direction`
  are dropped — `EdgeSummary` already carries them per `tools/get_neighbors.py:107-116`).
- Apply the SAME retention in `_ingest_explore_subgraph` (L161-176) — subgraph results
  carry edge lists too (judge #1).
- `populate_state` (L102-139): write `state.dialectical_edges = self.dialectical_edges`.
**Acceptance:** after a `get_neighbors` call on a debate node, `state.dialectical_edges`
is non-empty. Makes "0 edges used" physically impossible. **Low risk, structural prereq.**

### Step 2 — M1: Relational retrieval tools + debate-first prompt
**New files:** `agents/tools/find_debates.py`, `agents/tools/build_controversy_frame.py`.
**Edit:** `agents/tools.py` (`build_tool_registry`), `agents/tool_schemas.py`
(`build_tool_function_schemas`), `agents/react_loop.py:566-600`, `scholarly_agent.py:640`.
- **Tool A `find_debates(topic, period_filter?, limit?)`** — the SQL in ARCHITECTURE §2.2
  (ts_rank + incoming-dialectical-edge degree, `ORDER BY lex + 0.15*least(degree,40)`,
  `WHERE n.type IN ('debate','controversy','position')`). Returns
  `[{debate_id, label, summary, participant_ids, opposing_pairs, grounded_passage_count, degree}]`,
  most-contested-first. **Pure SQL/KG adjacency — no embeddings.**
- **Tool B `build_controversy_frame(seed_id)`** — accepts a `debate` OR `scholar_position_*`
  node; traverses one hop of dialectical edges both directions; pulls grounding
  (`created_by`/`advanced_in` → publication; `cites_primary_source`/`evidenced_by` →
  passage) and contested passages auto-paired with `_en` via `has_translation`. Returns a
  `ControversyFrame`. **Carries the empty-debate-node fallback** (lexical-match participants
  → hop via `argument_*`/`argument_cafma_*` → re-seed on position nodes → merge back).
- Register both in `build_tool_registry`; add JSON schemas in `build_tool_function_schemas`.
- Repoint the dead `tools.get("query_scholarly_consensus")` (`scholarly_agent.py:640`,
  currently returns `None`) → `find_debates`.
- Rewrite `NATIVE_SYSTEM_PROMPT_TEMPLATE` (`react_loop.py:566-600`) to the debate-first,
  shape-aware text in ARCHITECTURE §2.4 (FIRST move = `find_debates`, THEN
  `build_controversy_frame`; never start with entity descriptions; a debate is real only
  if you can name two sides + the edge; always fetch `_en` alongside original).
**Acceptance:** on the trigger question the agent calls `find_debates` first and returns
≥3 debate ids with non-empty `opposing_pairs`. **Medium risk.**

### Step 3 — M2: Question→shape planner (replaces facet picker)
**Files:** `agents/state.py` (`AnswerShape`, `GraphPattern`, `ResearchPlan` models),
new `PlanResearch` node in `agents/graph_nodes.py`; delete `_default_research_facets`
(`graph_nodes.py:1082-1271`) usage.
- Add the six shapes + `factual_lookup` short-circuit (ARCHITECTURE §1 table).
- `PlanResearch`: one cheap Fireworks `kimi-k2p6` JSON-mode call (`max_tokens≈1500`) given
  the inventory header (counts of debate nodes + `opposes` edge shape) → emits a typed
  `ResearchPlan` (DAG of `GraphPattern`, not fixed section titles). Default-when-ambiguous
  = `survey_of_debates` (the failing trigger lands here).
- `ClassifyQueryType` stays for back-compat budget math (`query_type`/`complexity`) but no
  longer picks facets. `factual_lookup` short-circuits to a single `get_node_detail`.
**Acceptance:** trigger question → `primary_shape == survey_of_debates`; "when did
Chrysippus die" → `factual_lookup`. **Medium risk.**

### Step 4 — M3: `ControversyMap` dossier + context-pack edge layer
**Files:** `agents/state.py` (the §3.1 models), `agents/graph_nodes.py:3377-3484`
(`_build_context_pack`), `agents/evidence_collector.py`.
- Add `PassageRef`, `GroundedPosition`, `DialecticalLink`, `FrameCompleteness`,
  `ControversyFrame`, `ControversyMap` to `state.py` (verbatim §3.1).
- Frame assembly: `build_controversy_frame` (M1) emits `ControversyFrame`s; assemble into
  a `ControversyMap` ordered by `incident_edge_count` desc (RAW count — **no score**, no
  DF-QuAD, no `base_strength`/`contestedness`).
- `_en` join + page-grounding: every `contested_passage` is original+`_en` via
  `has_translation`; `page_grounding` read off `scholar_position_*`/`scholarly_argument_*`
  node metadata; absent → `None` (never invented).
- `_build_context_pack`: add a top-level `## Controversy Frames` layer serialising each
  frame (positions w/ holder+page; `A —critiques→ B` link lines; contested passages
  original+English). Add `ContextPack.controversy_frames` field.
- For heavy shapes (≥3 frames, survey/transmission): each frame build runs as an isolated
  Fireworks `kimi-k2p6` subagent returning only a distilled `ControversyFrame` (§3.3 —
  latency/quality lever, not load-bearing).
**Acceptance:** `ControversyMap` for the trigger has ≥3 frames each with ≥2 positions, a
dialectical link, ≥1 bilingual contested passage. **Medium risk.**

### Step 5 — M4: Dialectical synthesis — the cutover (HIGH risk, the heart)
**Files:** `agents/graph_nodes.py` — replace `RENDER_ANSWER_PROMPT` (L580-680) with
`DIALECTICAL_SYNTHESIS_PROMPT`; new `DialecticalSynthesis` node replacing the
`DraftClaimLedger → build_render_prompt → RenderGroundedAnswer → _render_answer_fallback`
chain. Reference: `data/goals/g6/reference_synthesis.py`.
- **Add** `DIALECTICAL_SYNTHESIS_SYSTEM` + `DIALECTICAL_SYNTHESIS_TEMPLATE` (the actual
  prompt — see below), `serialize_controversy_map`, `synthesize_dialectical`.
- **Cite-as-you-write:** model emits `[P_*: …]`, `[edge: …]`, `[passage_*: …]` inline,
  ids drawn from the map → resolvable by construction.
- **`build_provenance_ledger`** deterministic post-pass parses markers → `ClaimLedgerItem[]`,
  tagging each `assertion | attributed_position | interpretation`. **Demote**
  `DraftClaimLedger` (L5189-5429) from generative pre-step to this parser; **delete**
  `build_render_prompt`'s `ledger_json` input (L5471-5497).
- **DELETE:** `_render_answer_fallback` facet template (L3575-3733); the 220-char
  `_derive_claim_ledger_fallback` pastes (L4169+, incl. L4192/4211/4308/4401 + facet claim
  region L4250-4380); the hardcoded Bobzien⟂Frede example in the old prompt (L673-677).
- **Replace** `_render_answer_fallback` with the prose-stated **degraded mode**
  (`synthesize_degraded`) + **content gate** (`passes_content_gate`) replacing the
  ~10k-char floor (L3987-3993). Route the inadequate-band branch (L5757-5759,
  `scholarly_agent.py:1615-1618`) to degraded mode, **never** to a paste.
**Acceptance:** trigger question produces non-repeating prose with ≥3 fault lines, >0
edge markers, every position attributed+page-grounded; `0` occurrences of
`"frames the issue as"`. **High risk — keep old path behind flag one release for A/B.**

### Step 6 — M5: Scholar-grade verification loop
**Files:** `services/citation_verifier_v2.py`, `agents/scholarly_agent.py:729-869`
(alongside `_run_citation_verifier_v2`).
- **CitationVerifierV2 (extended):** fed the map; NLI-style entailment per `[passage_*]`/
  `[P_*]` marker (does the cited entry entail the sentence?); markers not resolving to the
  map → hard-reject; quotation claims → exact-substring check vs. original passage text;
  cap raised from 8 to ALL attributed-position claims on the synthesis path.
- **Completeness critic (new):** denominator = the frames `find_debates`/
  `build_controversy_frame` actually returned (graph-real, NOT planner hints).
  `fault_line_coverage = |narrated| / |in map|`. Any map frame absent from the answer →
  targeted `build_controversy_frame` expansion re-entering retrieval.
- **Anti-anachronism gate (new, F11):** deterministic scan for the MEMORY lexicon
  (`ANACHRONISTIC_LEXICON` in reference_synthesis) outside an `attributed_position` span →
  fail; LLM confirms attribution on flagged spans; RARR span-edit the offending sentence.
- **Iterate condition (§5.4):** ACCEPT iff referee 0-unsupported AND completeness complete
  (or gaps marked "graph has no evidence") AND anachronism 0-unattributed AND every fault
  line has ≥1 counter-evidence span. REJECT → query-expansion (frame the missed debate) →
  RARR-edit affected spans → re-verify. Cap at `N_max` per budget tier; hard failure →
  degraded mode (never a template).
**Acceptance:** an answer missing a real debate or asserting an unattributed "compatibilism"
is REJECTED and repaired. **Medium risk.**

### Step 7 — M6: K2.7 provider wiring + budget/quality-tier reconciliation
**Files:** `services/llm_service.py:106-113,467-505`, `agents/scholarly_agent.py:147-164`,
`opencode.json`, `agents/repl.py`, `llm_pricing.py`.
- **`PROVIDER_CONFIGS[ModelProvider.KIMI]` (L106-113)** → resolved ids from
  `model_resolution.md`:
  ```python
  ModelProvider.KIMI: {
      "base_url": "https://api.moonshot.ai/v1",
      "model": "kimi-k2.7-code-highspeed",      # primary synthesis (was "kimi-latest")
      "thinking_model": "kimi-k2.7-code",         # deep tier (was "kimi-latest")
      "env_key": "MOONSHOT_API_KEY",
      "base_url_env": "MOONSHOT_BASE_URL",
      "model_env": "MOONSHOT_MODEL",              # ADD — overridable
      "thinking_model_env": "MOONSHOT_THINKING_MODEL",  # ADD
      "rate_limit": 20,
  }
  ```
- **KIMI temperature clamp (mandatory)** in `_openai_compatible_payload` — insert right
  after the `payload` dict is built (L500-505):
  ```python
  if provider == ModelProvider.KIMI:
      payload["temperature"] = 1.0   # Moonshot 400s on any other value
  ```
- **`SCHOLAR_SYNTHESIS_MODEL` resolver (new in `llm_service.py`):**
  `resolve_scholar_synthesis_model()` reads env `SCHOLAR_SYNTHESIS_MODEL`
  (default `fireworks:kimi-k2p6`; opt-in `moonshot:kimi-k2.7-code-highspeed`) → returns
  `(ModelProvider, model_id)`. `generate()`/`stream()` gain `model_override` +
  `provider_override` params (thread through to `config["model"]`).
- **Fallback chain (synthesis):** `kimi-k2.7-code-highspeed → kimi-k2.6 (Moonshot) →
  fireworks/kimi-k2p6 → gemini-3.1-pro-preview`.
- **Budgets (§6):** delete the char-floor (`graph_nodes.py:3987-3993`) — replaced by the
  content gate (M4). Raise `_stream_render_max_tokens` default (`scholarly_agent.py:147-164`)
  to **8000** to match the blocking path (≥5000 mandatory — reasoning eats budget).
  `_tool_call_budget` (`react_loop.py:91-115`) raised to **45** for survey/transmission.
  Stream `reasoning_content` as a "thinking…" heartbeat; raise `_await_with_heartbeat` /
  `_stream_render` `max_wait` for the synthesis call (highspeed ~55s, code ~95s).
- **`opencode.json`, `repl.py`, `llm_pricing.py`:** add the K2.7 model ids + pricing rows.
**Acceptance:** with `SCHOLAR_SYNTHESIS_MODEL=moonshot:kimi-k2.7-code-highspeed`, a
synthesis call returns non-empty `content` (temp=1, max_tokens=8000). **Low risk.**

### Step 8 — M7: Flip default + delete dead code
**Files:** flag removal across the above.
- Remove `_inject_passage_quotations` (`scholarly_agent.py:939-1033`, F10) — passages now
  cited inline via the map.
- Delete the old facet-template path and `SCHOLAR_RAG` flag after one A/B release.

---

## The synthesis prompt (the actual design)

Replaces `RENDER_ANSWER_PROMPT` (`graph_nodes.py:580-680`). Full reference in
`reference_synthesis.py`; the load-bearing text:

**System role (`DIALECTICAL_SYNTHESIS_SYSTEM`):**

> You are a historian of ancient philosophy writing for a specialist audience
> (Cambridge-Companion register). You reason DIALECTICALLY over a CONTROVERSY MAP: a
> structured record of contending scholarly positions and the primary texts they fight
> over. You attribute every interpretive claim to a named scholar with a page reference.
> You ground every claim about an ancient author in a quoted primary passage. You hedge
> where the evidence underdetermines the question. You never adjudicate a dispute the field
> has not settled. Modern categories — "libertarian free will", "compatibilism",
> "incompatibilism", "hard/soft determinism", "the will" as a faculty, "the free-will
> problem", "indeterminist" — are scholarly CHARACTERISATIONS. They may appear ONLY inside
> an attributed position ("what Bobzien terms…", "on Frede's reading…"), NEVER asserted in
> your own voice as ancient fact. You never write Greek or Latin that is not present
> verbatim in the provided passages; if a phrase is not in the map, paraphrase it in
> English. You quote contested primary text in the original AND English at the point the
> scholars argue over it. CITE AS YOU WRITE — every interpretive sentence carries an inline
> marker drawn from the map: `[P_<id>: <holder>, <pub+page>]`, `[edge: <relation>
> P_<from>->P_<to>]`, `[passage_<id>: <author>, <ref>]`. Use only ids that appear in the
> map; never invent one.

**User template (`DIALECTICAL_SYNTHESIS_TEMPLATE`)** — the serialised `ControversyMap`
(`## QUESTION`, `## FRAME f… POSITIONS / DIALECTIC (A --opposes--> B) / CONTESTED PRIMARY
TEXT (GR + EN, untruncated)`, `## COVERAGE GAPS`) followed by:

> **REASON** (private scratch, drives `reasoning_content`):
> 1. THESIS SELECTION — state the *shape* of the answer (which fault lines dominate), not a
>    doctrinal verdict.
> 2. MAP THE FAULT LINES — per frame name ≥2 opposing positions + the opposing edge; flag a
>    one-sided frame as incomplete.
> 3. LOCATE THE PRIMARY ANCHOR — per position find its dossier passage; if none, mark
>    "interpretation without surfaced primary grounding" and hedge harder.
> 4. WEIGH, DON'T DECIDE — AND DETECT TALKING-PAST — note genuine conflict vs. talking past
>    (different object of choice, different dating of "the will", different sense of the
>    term); note `responds_to` chains; **do not pick a winner.**
> 5. CHECK ANACHRONISM — voice every modern label as "what X calls…", never "the Stoics
>    held compatibilism."
> 6. PLAN STRUCTURE FROM THE FRAMES PRESENT — one movement per fault line (survey),
>    chronological (genealogy), point-by-point (comparison). Never a fixed template.
>
> **WRITE** (drives `content`): open with a thesis sentence answering the actual question;
> one movement per fault line with adaptive headings derived from frame titles; inline
> citation per interpretive sentence as written; quote contested text original+English
> where argued over; hedge with the field's markers; close with what remains genuinely open.

**Function signature** (live `DialecticalSynthesis.run` body):
```python
async def synthesize_dialectical(
    state: RAGState,
    cmap: ControversyMap,
    llm: LLMService,
    *,
    max_tokens: int = 8000,      # >=5000 mandatory (reasoning eats the budget)
    budget_tier: str = "standard",
) -> SynthesisResult:            # {prose, reasoning_trace, model_used, ledger}
```
Input = the `ControversyMap` dossier (frames + exegesis units + coverage gaps, fully
grounded, full bilingual passages, page-grounded positions, `incident_edge_count` order).
Output = prose + `reasoning_content` trace + ledger (parsed from prose by
`build_provenance_ledger`). No facet template, no pre-built ledger feeds it.

---

## Eval plan (G2 harness, old-vs-new)

**Harness:** `tests/eval/run_eval.py` (+ `eval_lib/scoring.py:citation_prf`,
`must_not_appear.jsonl`), driven by `tests/eval/queries.yaml`.

1. **Add G2 gold cases to `queries.yaml`** — the trigger + kin, with `expected_entities` =
   exact node ids: `debate_origins_notion_of_will_modern_paradigm`,
   `scholar_position_frede_will_originates_epictetus`,
   `scholar_position_dihle_will_christian_innovation`,
   `scholar_position_bobzien_no_free_will_problem_ancients`,
   `scholarly_argument_amand_de_mendieta_carneades_anti_fatalist_moral__0`,
   `scholarly_argument_ramelli_origen_s_knowledge_of_alexande_0`,
   `debate_carneadean_antiastrology_tradition`; plus `gold_claims` asserting the fault lines.
   Reuse existing q001–q003 (Aristotle voluntary; Chrysippus fate; Epictetus prohairesis)
   as `concept_genealogy`/`doxographical_synthesis` regression anchors.
2. **Trigger question:** *"What are the big open debates today about free will in
   antiquity?"* → must enumerate: discovery-of-will (Bobzien⟂Frede⟂Dihle); Stoic
   compatibilism (Cic. Fat. 39–43, cylinder); Alexander libertarian? (Sharples 1983 p.22);
   Carneadean transmission (Amand⟂Ramelli).
3. **Baseline capture** (old path) → `data/goals/g6/baseline_template.json`.
   **New-path capture** (`SCHOLAR_RAG=true`) → `data/goals/g6/scholar_rag.json`. Compare.
4. **Add 5 metrics to `run_eval.py`:** (a) edge-use count (distinct dialectical edges in
   the ledger, must be >0); (b) attribution rate (modern-label occurrences inside an
   attributed span); (c) counter-evidence coverage (fault lines with a reported attack);
   (d) fault-line coverage (completeness critic's ratio); (e) non-repetition (n-gram
   self-overlap — catches "same node 4×").
5. **Anti-template regression fixture (snapshot test):** on the trigger question assert ≥3
   distinct fault lines, >0 `opposes`/`critiques` edges in the map, and **0 occurrences of
   `"frames the issue as"`** — so the template can never silently return.

**Old-vs-new acceptance bar (trigger question):**

| Criterion | Old path (baseline) | New path (must pass) |
|---|---|---|
| Enumerates the 4 real live debates | ✗ (generic facets) | ✓ all 4 named |
| Dialectical edges used | 0 | ≥3 `opposes`/`critiques` |
| Positions attributed + page-grounded | ✗ | ✓ every position |
| Non-repetition (n-gram self-overlap) | high (node 4×) | low (genuine prose) |
| `must_not_appear` hits | — | 0 |
| `"frames the issue as"` occurrences | present | 0 |
| All three referees pass | n/a | ✓ |
| Fault-line coverage | — | complete (or gaps prose-stated) |

The win is only *visible* once the debate-survey cases exist (the harness is structurally
blind to relational improvement until then — graft from P2 §7).
