# G6 — Current-Pipeline Failure Map (Scholar-RAG)

Trace of the live `react`-mode path from query → retrieval → ledger → render → verification, with every
failure mode pinned to `file:line`. The trigger ("What are the big open debates today about free will in
antiquity?" → same truncated node description pasted 4× under a rigid template, 0 edges, not answering the
question) is reproduced by the chain of failures below.

Files traced:
- `agents/scholarly_agent.py` (facade / orchestration / streaming)
- `agents/react_loop.py` (ReAct retrieval)
- `agents/evidence_collector.py` (tool-result → state bridge)
- `agents/graph_nodes.py` (dossier, claim ledger, render, fallback template, classifier, verify)
- `agents/state.py` (RAGState containers)
- `services/llm_service.py` (provider/model resolution)
- `services/citation_verifier_v2.py` (adversarial referee)

---

## End-to-end path (react mode — the production default, `AGENT_MODE="react"` at `scholarly_agent.py:277`)

1. `ScholarlyAgent.query` / `query_stream` → `_run_react` / `_stream_react`
2. `ClassifyQueryType` (deterministic) → sets `query_type`, `complexity`
3. `NativeAgentLoop.run` (`react_loop.py:662`) — model-driven tool calls (8 tools), evidence accumulated in
   `EvidenceCollector`, then `populate_state(state)`
4. `_post_loop_quality_phase` — rerank (off), sufficiency continuation (≤1 round), counter-evidence hunt (deep only)
5. `DraftClaimLedger.run` (`graph_nodes.py:5189`) — LLM claim ledger → fallbacks
6. `RenderGroundedAnswer.run` (`graph_nodes.py:5501`) / `_stream_render` (`scholarly_agent.py:1485`) — LLM prose,
   else `_render_answer_fallback` (`graph_nodes.py:3575`) — **the facet template**
7. `ProgrammaticVerify` → `_inject_passage_quotations` → text verifier → CitationVerifierV2

The synthesis is NOT a single LLM call over a relational dossier. It is: deterministic dossier build →
deterministic-or-LLM claim ledger → LLM render that is **silently replaced by a deterministic template**
whenever quality gates trip. Edges are discarded before any of this.

---

## RANKED FAILURE MODES

### F1 — Edge-blindness at ingestion: `get_neighbors` relations are thrown away (ROOT of "0 edges")
**`evidence_collector.py:178-192` (`_ingest_get_neighbors`)**
`get_neighbors` returns `EdgeSummary{edge_node_id, relation, direction, label, type}`
(`tools/get_neighbors.py:15-20`, confirmed `relation` + `direction` are populated at L111-112). The collector
keeps **only `edge_node_id`** as a bare `Evidence(source=GRAPH_TRAVERSAL)` and **drops `relation` and
`direction` entirely**. So `opposes` / `critiques` / `responds_to` / `advanced_in` never enter state. There is
no edge container on the path: `populate_state` (`evidence_collector.py:102-139`) writes
`primary_evidence`, `secondary_evidence`, `evidence_bundles`, `seed_node_ids`, `context_node_ids` — **no edge
list**. The only relational data that survives is `inferred_edges` from `infer_transitive`
(`evidence_collector.py:271-285`), which is an ontology transitive-closure helper, not the disagreement layer.
→ This is the literal cause of "0 edges used". Fix here first.

### F2 — Context pack has no edge/relation/debate section: synthesis prompt is structurally edge-blind
**`graph_nodes.py:3377-3484` (`_build_context_pack`)**
The packed prompt contains exactly three layers: `## KG Metadata` (compact node lines, L3448-3449),
`## Work Sections` (L3450-3451), `## Evidence Bundles` (full passage text, L3452-3467). There is **no edges
layer, no debate-node layer, no opposes/critiques layer**. Even if F1 were fixed, the render LLM would still
never see relations because the pack has no slot for them. `ContextPack` in `state.py` likewise has no edge
field.

### F3 — Retrieval has no debate/controversy/disagreement affordance
**`agents/tools/` (8 tools only)** + **`react_loop.py:566-600` (`NATIVE_SYSTEM_PROMPT_TEMPLATE`)**
The registry is: `search_nodes, explore_subgraph, get_neighbors, get_node_detail, read_passages,
search_passages, read_work_section, infer_transitive`. **No `query_scholarly_consensus` / debate tool exists**
— `scholarly_agent.py:640` fetches it via `tools.get("query_scholarly_consensus")` and silently gets `None`.
The ontology HAS `debate` and `controversy` node types (`node_types.json:240,486`) with `positions` and
participants, but nothing retrieves them as first-class objects. The native system prompt (L571-599) tells the
agent to "search for philosophers/concepts/works", "read passages", "verify attributions" — it **never
mentions debates, opposing positions, or `opposes`/`critiques` edges**. So on a "what are the open debates"
question the agent retrieves entity nodes + passages, not the relational debate structure the graph holds.
→ The disagreement layer (G5 substrate) is invisible to both the tools and the planner.

### F4 — The facet template IS the answer when the LLM render trips a gate (the trigger garbage)
**`graph_nodes.py:3575-3733` (`_render_answer_fallback`)**
When the LLM render is empty or classified `inadequate`, the answer becomes this deterministic template:
one `### {facet.title}` section per dossier facet, each filled by pasting claim text + truncated quotes.
With generic facets (`Definition` / `Textual Basis` / `Counterpoint and Nuance`, from `_default_research_facets`
`graph_nodes.py:1175-1262`) and a metadata-only claim ledger, the **same lead node is distributed across
sections** (L3593-3611 explicitly shuffles `_general` claims into empty facets), so every section restates the
same node. This is the observed "same description pasted 4× under Definition/Textual-Basis/Counterpoint".

### F5 — The 220-char truncation that produces "frames the issue as <truncated desc>"
**`graph_nodes.py:4308`** (and siblings `4192`, `4211`, `4401`):
```
claim_text = f"{facet.title}: {metadata_node.label} frames the issue as {summary}."
```
where `summary = truncate_text(metadata_node.description, 220)`. This is `_derive_claim_ledger_fallback`
(`graph_nodes.py:4169+`). When the LLM ledger is empty/rejected (F8), these mechanical claims fill the ledger;
F4 then pastes them under each header. The 220-char cut mangles mid-sentence node descriptions into the
quoted "frames the issue as …". The same pattern: SPECIFIC_ENTITY at L4192, non-entity at L4211, last-ditch at
L4401. These are edge-blind ("frames the issue") because no relation is available (F1/F2).

### F6 — Generic, question-shape-blind facet template replaces a real research plan
**`graph_nodes.py:1082-1271` (`_default_research_facets`)** + **`_build_scholarly_dossier` (`graph_nodes.py:1512`)**
Facets are picked by keyword buckets and `query_type` only (`Definition`/`Textual Basis`,
`Points of Agreement`/`Divergence`, `Counterpoint and Nuance`, etc.). There is **no "survey-of-debates"
shape**: a question literally asking for open debates is routed to `Definition` + `Textual Basis` +
`Counterpoint` because none of its terms hit the doctrinal/fate/agency buckets. The facets then drive both the
ledger (F8) and the fallback sections (F4). This is the fixed template the goal's planner (G6 §1) replaces.

### F7 — A real LLM synthesis EXISTS but is overridden by quality gates / fallback
**`RenderGroundedAnswer.run` `graph_nodes.py:5541-5554`** runs `RENDER_ANSWER_PROMPT` (`graph_nodes.py:580-680`)
— a genuine Cambridge-Companion-style synthesis call. It is NOT bypassed by default, but it is **silently
discarded** in three ways:
- **Quality-gate override:** `_classify_render_quality` (`graph_nodes.py:4043-4106`) demands `min_chars`
  (often 10 k+, `_render_requirements` `graph_nodes.py:3987-3993`), `required_sections`, `required_quote_blocks`,
  and ≥4 inline citations/section. If unmet → band `inadequate` → `rendered = _render_answer_fallback(state)`
  (`graph_nodes.py:5757-5759`, streaming `scholarly_agent.py:1615-1618`). A correct-but-short debate survey is
  thrown away for the template.
- **Edge-blind prompt:** `RENDER_ANSWER_PROMPT` (L598-651) mandates **per-passage exegesis** ("for EACH major
  passage … quote … philological analysis"). The only "debate" content (Bobzien⟂Frede, L673-677) is a
  **hardcoded illustrative example**, not retrieved data. The dossier/evidence packet it receives carry no
  edges (F2), so the model cannot enumerate the graph's real debates even when it runs.
- **Exception fallback:** any LLM error → `_render_answer_fallback` (`graph_nodes.py:5798-5800`).

### F8 — Ledger-as-prose dependency (prose is downstream of a mechanical ledger, not of reasoning)
**`DraftClaimLedger.run` `graph_nodes.py:5189-5429`** + **`build_render_prompt` `graph_nodes.py:5471-5497`**
The render prompt is built FROM `state.claim_ledger` (`ledger_json`, reference_map keyed by claim text,
`graph_nodes.py:5471-5488`). The ledger is built first, by: deterministic-quote shortcut (L5213), else LLM
JSON ledger (L5277), else `_salvage_claim_ledger` (L5352), else `_derive_claim_ledger_fallback`
(F5, L5415). LLM ledger items are **dropped unless their `evidence_ids` resolve to a packed ref**
(L5315-5319) — and since edges are never packed (F1/F2), no relational claim can survive. So the prose is a
function of the (edge-blind, often mechanical) ledger, exactly the inverted dependency G6 §6 wants reversed
(ledger should be a byproduct of synthesis, not its input).

### F9 — Latency caps force premature/mechanical synthesis on exactly the hard queries
- **`MAX_TOOL_CALLS` / `_tool_call_budget` (`react_loop.py:91-115`)**: COMPLEX caps at 30 tool calls; a
  cross-period debate survey (Stoic Bobzien⟂Frede + origins-of-will + Alexander + Carneadean transmission)
  needs many `get_neighbors` + `read_passages`; hitting the cap (`react_loop.py:724-743`) truncates coverage so
  the ledger/render starve and fall to F4/F5.
- **`ELEUTHERIA_RENDER_MAX_TOKENS` (`scholarly_agent.py:147-164`)**: streaming render is capped at **8000**
  completion tokens (down from 16 k). `_render_requirements` simultaneously demands ~10–15 k **chars** across
  6–10 sections (`graph_nodes.py:3987-3993`). The token cap can make the render physically unable to reach the
  char floor the SAME pipeline requires → `inadequate` band → F4 fallback. The blocking node uses 16 k
  (`graph_nodes.py:5550`) but the public/streaming path uses 8 k — the path users actually hit is the one that
  starves.
- **`_await_with_heartbeat` max_wait / `_stream_render` max_wait=240 (`scholarly_agent.py:1486,1569`)**: a
  stalled reasoning model is abandoned mid-render → empty `chunks` → fallback (`scholarly_agent.py:1614-1618`).
- **Sufficiency continuation is a single 3-call round (`scholarly_agent.py:177-184,555-621`)** — too small to
  repair a debate-survey coverage gap.

### F10 — Post-hoc deterministic patching masks, not fixes, the failure
**`_inject_passage_quotations` (`scholarly_agent.py:939-1033`)** appends a `## Primary Textual Evidence` block
of raw bundle dumps when <2 Greek blockquotes are present. On a fallback-template answer this bolts passage
dumps onto already-broken prose, increasing the *appearance* of grounding without making the answer address
the question. It is deterministic (no reasoning) and edge-blind.

### F11 — Verification audits citations, never completeness or anachronism
**`citation_verifier_v2.py`** + **`scholarly_agent.py:729-869`**: the v2 referee checks whether sampled
citations support their surrounding sentence (≤8 claims, `_verifier_v2_max_claims`), downgrading REJECTED/
MISSING. There is **no completeness critic** ("which graph debate did the answer miss?") and **no
anti-anachronism gate** ("libertarian"/"compatibilism" asserted as fact). So an answer that misses every real
debate and asserts modern labels passes verification cleanly. `ProgrammaticVerify` only resolves ref markers.

### F12 — Model-resolution gap: K2.7 is not wired
**`llm_service.py:106-113`**: the Moonshot/Kimi provider config pins `model="kimi-latest"` /
`thinking_model="kimi-latest"`; primary is Fireworks `accounts/fireworks/models/kimi-k2p6`
(`llm_service.py:75`). The G6 target model **Kimi K2.7 via Moonshot** is not present — `kimi-latest` is an
alias of unknown version and tool-calling is documented as Fireworks-only (`llm_service.py:873-874`). The
exact K2.7 Moonshot id/params must be resolved and wired before the dialectical-synthesis stage can use it.

---

## EXACT CODE LOCATIONS TO CHANGE (for the blueprint)

| # | Concern | Location |
|---|---------|----------|
| 1 | Keep edge `relation`+`direction` (kill 0-edges) | `evidence_collector.py:178-192`; add edge store in `evidence_collector.py:102-139` + `state.py` `RAGState`/`ContextPack` |
| 2 | Add an edges/debate layer to the packed prompt | `_build_context_pack` `graph_nodes.py:3447-3469` (+ `ContextPack` in `state.py`) |
| 3 | Add a debate/disagreement retrieval tool + teach the planner to use it | `agents/tools/` (new tool) + register in `tools.py`; `react_loop.py:566-600` system prompt; `scholarly_agent.py:640` (dead `query_scholarly_consensus` ref) |
| 4 | Replace fixed facet template with question→shape planner | `_default_research_facets` `graph_nodes.py:1082-1271`; `_build_scholarly_dossier` `graph_nodes.py:1512` |
| 5 | Kill the 220-char node-paste claims | `graph_nodes.py:4192,4211,4308,4401` (`_derive_claim_ledger_fallback`) |
| 6 | Reverse ledger→prose: make ledger a byproduct of synthesis | `DraftClaimLedger` `graph_nodes.py:5189-5429`; `build_render_prompt` `graph_nodes.py:5471-5497` |
| 7 | Stop the silent template-fallback override of good prose | `_classify_render_quality` `graph_nodes.py:4043-4106`; render fallback `graph_nodes.py:5757-5759` + `scholarly_agent.py:1615-1618` |
| 8 | Replace facet-template fallback with a reasoned degraded mode | `_render_answer_fallback` `graph_nodes.py:3575-3733` |
| 9 | Make the synthesis prompt edge-aware (use real debates, not hardcoded example) | `RENDER_ANSWER_PROMPT` `graph_nodes.py:580-680`; `_scholarly_dossier_payload` `graph_nodes.py:1652-1693` |
| 10 | Reconcile token cap vs char floor on the streaming path | `_stream_render_max_tokens` `scholarly_agent.py:147-164` vs `_render_requirements` `graph_nodes.py:3987-3993` |
| 11 | Add completeness critic + anti-anachronism gate to verification | new stage alongside `_run_citation_verifier_v2` `scholarly_agent.py:729-869`; `citation_verifier_v2.py` |
| 12 | Resolve + wire Kimi K2.7 (Moonshot) | `llm_service.py:106-113` |

## One-line root cause
The pipeline **discards edges at ingestion (F1)**, has **no edge slot in the prompt (F2)** and **no debate
tool/shape (F3/F6)**, so the genuine LLM synthesis (F7) is both edge-blind and **silently replaced by a
deterministic facet template (F4) whose claims are 220-char node-description pastes (F5)** whenever the
length/section gates (F9) trip — which is exactly when a relational "open debates" question is asked.
