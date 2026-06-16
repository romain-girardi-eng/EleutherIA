# Scholar-RAG — Authoritative Architecture (G6)

> **Status:** single authoritative spec. Synthesised from design proposals #1/#2/#3 and the two
> adversarial judgments. Spine = **Proposal #1** (the *Controversy Object as a tri-purpose typed
> structure*); amputations and grafts applied per both judges' unanimous instructions. This document
> supersedes the three proposals for implementation.

---

## Headline design

**Scholar-RAG is a vectorless, agentic, *edge-first* graph-RAG whose retrieval, synthesis, and
verification are all organised around one typed intermediate object — the `ControversyMap` — that is
simultaneously (1) the retrieval target, (2) the synthesis context, and (3) the verification oracle.**

The `ControversyMap` is a set of **`ControversyFrame`s**: each frame is one scholarly fault line —
its contending positions (each attributed to a named holder with a page reference), the *flat,
star-tolerant* dialectical links between them (`opposes / critiques / responds_to / refutes /
contrasts_with / agrees_with / supports`), and the contested primary passages (original + English,
untruncated) the positions fight over. The retrieval phase's explicit goal is to *populate frames*,
not collect nodes. The synthesis phase's explicit input is *frames*, not a node list. The verification
phase checks the answer *against the frames* — giving the completeness critic a real denominator (fault
lines retrieved vs. fault lines narrated).

This one object structurally kills the trigger failure ("same truncated description pasted 4×, 0 edges,
not answering the question"): a frame **has no rows except positions and the edges between them**, so
the synthesis prompt is *structurally unable* to be edge-blind, and the deterministic facet template
has nothing left to do — section structure comes from `frames`, claims come from `positions`, grounding
comes from `contested_passages`. The template is **deleted, not patched**. The provenance ledger is
**reconstructed from the finished prose** (cite-as-you-write), reversing today's ledger→prose
dependency.

**The three decisions that distinguish this spec from any single proposal** (both judges, unanimous):

1. **No gradual-semantics numbers.** DF-QuAD / `base_strength` / `contestedness` scalars are *removed*
   (P1's only fidelity hazard, P2's load-bearing liability). On a graph with **11 `opposes` edges
   total**, a propagated `0.62 vs 0.38` strength is false precision — itself an anachronistic
   assertion, antithetical to "attribute, never assert." We keep only the *bipolar structure* as (a) a
   retrieval shape and (b) an internal completeness signal (*attackers but no surfaced defender ⇒
   incomplete frame ⇒ expand*). Fault lines are ordered by **raw incident dialectical-edge count**, not
   a computed score. **No strength scalar ever reaches the prose.** (Graft from P3 §0.2.)

2. **Flat, star-tolerant links — not pro/con tagging.** The 244 `critiques` edges are *star-shaped*
   (Bobzien critiques Long, Sedley, and Frede simultaneously — a star, not a pole). P1's
   `{pro|con|neutral}` bipolarisation would mislabel them. We adopt P3's flat
   `DialecticalLink{relation, from_holder, to_holder, gloss}`: it represents both a two-sided opposition
   *and* a one-to-many critique honestly. (Graft from P3 §3.2 / judge #2.)

3. **Reachability is verified before anything is built.** The single highest-risk unverified assumption
   shared by all three proposals — that the `opposes`/`critiques` fault-line edges are reachable from
   debate nodes in ≤2 hops — is *false for two of the four headline debates*
   (`debate_origins_notion_of_will_modern_paradigm` has **no out-edges**;
   `debate_carneadean_antiastrology_tradition` has **0 grounded passages**). The fault-line edges hang
   off the `scholar_position_*` nodes, not the debate node. Stage 0 is a **graph-reachability probe**;
   `build_controversy_frame` carries an explicit **empty-debate-node fallback** (lexical-match
   participants, hop via `argument_*` / `argument_cafma_*` clusters and `contributes_to` arguments).
   Without this, the winner's own showcase trigger returns two empty frames. (The fallback all three
   proposals missed; both judges flag it as non-negotiable.)

**Hard constraints honoured throughout:** vectorless (every retrieval is ts_rank + lemmatic + tree-nav
+ KG adjacency + `has_translation` join — *no embeddings anywhere*); agentic (model-driven ReAct
escalation, anaphora-chained hops, draft→verify→expand loop — not a fixed algorithm); attributed-
not-asserted (every modern label lives only inside an attributed `Position`; an anti-anachronism gate
enforces it on the prose); zero fabrication (Greek/Latin quoted only verbatim from retrieved passages;
exact-substring check in the citation referee).

---

## Model wiring (K2.7, the two-tier seam)

Two roles, one swap-point. The goal doc's "do NOT use Moonshot direct / Fireworks-first" line and
`model_resolution.md`'s "K2.7 exists only on Moonshot and is the best synthesis prose engine" are **not
in conflict — they are two different roles.** (Resolution adopted from P1, the goal-compliant default;
both judges rank P1's reconciliation safest on a *hard constraint*.)

| Role | Default model | Why |
|------|--------------|-----|
| Planner (shape classify) | Fireworks `kimi-k2p6`, JSON-mode | cheap, fast, JSON proven on Fireworks |
| ReAct retrieval (tool-calling) | Fireworks `kimi-k2p6` | tool-calling documented Fireworks-only (`llm_service.py:873-874`) |
| Retrieval subagents | Fireworks `kimi-k2p6` (cheap tier per MEMORY) | tool-heavy, isolated context |
| **Dialectical synthesis** | **`SCHOLAR_SYNTHESIS_MODEL` (default `fireworks:kimi-k2p6`)** | the one swap-point |
| Verification referees | Fireworks `kimi-k2p6` | focused, short, isolated |

- **Default ships Fireworks** (`SCHOLAR_SYNTHESIS_MODEL=fireworks:kimi-k2p6`) — honours the goal's hard
  "do NOT use Moonshot direct" for the default deployment.
- **One-line swap** to `fireworks:kimi-k2p7` the day it lands on Fireworks.
- **Opt-in Moonshot** for operators who accept Moonshot-direct for the synthesis call only:
  `SCHOLAR_SYNTHESIS_MODEL=moonshot:kimi-k2.7-code-highspeed`
  (`thinking_model=kimi-k2.7-code` for the `deep` tier). `model_resolution.md` proves this is the best
  scholarly prose engine; it is documented opt-in, never the default.
- **KIMI temperature clamp (mandatory):** in `_openai_compatible_payload`,
  `if provider == ModelProvider.KIMI: payload["temperature"] = 1.0` — Moonshot 400s on any other value.
- **`reasoning_content`** is already parsed; it is an *advantage* for dialectic (the model weighs before
  writing). Synthesis `max_tokens = 8000` (≥5000 required: reasoning eats the budget).
- **Fallback chain** (synthesis): `kimi-k2.7-code-highspeed → kimi-k2.6 (Moonshot) →
  fireworks/kimi-k2p6 → gemini-3.1-pro-preview`.
- **Swap touch-points** (exactly the four the goal names + one resolver): `opencode.json`,
  `services/llm_service.py` (provider config + temp clamp), `repl.py`, `llm_pricing.py`, plus the new
  `SCHOLAR_SYNTHESIS_MODEL` resolver.

---

## 1. Question → scholarly-answer-shape planner

Replaces the keyword facet picker (`_default_research_facets`, `graph_nodes.py:1082-1271`). One cheap
LLM call (Fireworks `kimi-k2p6`, JSON-mode, `max_tokens≈1500`) classifies the question into **one
primary + optional secondary shape** and emits a typed `ResearchPlan` — a *retrieval program* (a small
DAG of graph patterns), not a fixed list of section titles.

### The six shapes (+ one short-circuit)

| Shape | Trigger (intent) | Graph-entry pattern | Adaptive answer skeleton |
|-------|------------------|---------------------|--------------------------|
| `survey_of_debates` | "open debates / controversies / what's contested about X" | `find_debates` → positions → `opposes`/`critiques` fault lines → contested passages | one movement **per fault line** |
| `concept_genealogy` | "origin/emergence/history of X", "who invented the will" | concept → `precedes`/`influenced_by` chain + the meta-debate node about the dating | chronological, **dating dispute foregrounded** |
| `transmission_trace` | "did A know B", "source of A's argument", "how X reached Y" | `participates_in` chain + `cites_primary_source` + rival-source `opposes` | source-stemma + the scholarly dispute over it |
| `position_comparison` | "X vs Y on Z", "did A agree with B" | two anchors → `opposes`/`contrasts_with`/`agrees_with` between them → grounding each side | symmetric point-by-point |
| `primary_text_exegesis` | a locus is named ("what does Cic. Fat. 41 say") | passage → `_en` pair → `discusses`/`interprets` from reception → `critiques` among interpreters | quote-first, philological, interpretation-history |
| `doxographical_synthesis` | "what did the Stoics hold about fate" | school/person cluster → `member_of` → doctrine concepts → `critiques` from rivals | doctrine + ancient counter-positions |
| `factual_lookup` (short-circuit) | "when did Chrysippus die" | single `get_node_detail` | 2-sentence answer, no synthesis loop |

The classifier is given the **inventory header** (counts of debate nodes, the `opposes` edge-list
shape) so it knows the graph *has* a disagreement layer to target. Default when ambiguous:
`survey_of_debates` (the failing trigger lands here; it currently mis-routes to
Definition/Textual-Basis/Counterpoint — F6).

### The plan object (`ResearchPlan`, new, in `state.py`)

```python
class GraphPattern(BaseModel):
    intent: str                 # "find fault lines in discovery-of-will debate"
    entry: Literal["debate","concept","person","passage","school","position"]
    seed_query: str             # lexical/lemmatic seed to locate entry nodes
    edge_program: list[str]     # ordered relations to walk: ["participates_in","opposes",...]
    depth: int = 2
    want_bilingual: bool = True

class ResearchPlan(BaseModel):
    primary_shape: AnswerShape
    secondary_shape: AnswerShape | None
    patterns: list[GraphPattern]      # the DAG (3-6 patterns), executed in topological order
    answer_skeleton: list[str]        # adaptive HINTS the synthesiser may override — never a hard template
    budget_tier: Literal["quick","standard","deep"]
```

- `patterns` are **fully-typed up front** (P1's named `edge_program` — the inspectable audit surface
  judge #2 preferred over P3's hints-only design): the plan can be diffed against the graph before
  retrieval runs.
- `answer_skeleton` is a *hint*; the synthesiser shapes prose to the question — never a fixed template.
- This is Adaptive-RAG routing generalised from 3 regimes to 6 scholarly shapes (research §4), emitting
  a DAG not a flat list (research §6).

**Implementation:** new node `PlanResearch` replaces `ClassifyQueryType`'s template role; `query_type`/
`complexity` stay for back-compat budget math but no longer pick facets.

---

## 2. Argument-structure-first VECTORLESS retrieval (how it stops being edge-blind)

Four structural locks kill F1/F2/F3. Edges survive ingestion; the prompt gets an edge slot; the agent
gets debate-first tools and a debate-first system prompt.

### 2.1 Lock 1 — edges survive ingestion (the literal F1 fix)

`evidence_collector._ingest_get_neighbors` (`evidence_collector.py:178-192`) currently keeps only
`edge_node_id` and **drops `relation` + `direction`** — though `EdgeSummary` already carries them
(`get_neighbors.py:107-116`). Add a first-class typed edge store:

```python
# state.py — new container on RAGState
DIALECTICAL_RELATIONS = {
    "opposes","critiques","responds_to","refutes","contrasts_with","agrees_with","supports",
    "participates_in","contributes_to","has_position","advanced_in","engages_with","interprets",
}

class DialecticalEdge(BaseModel):
    source_id: str; relation: str; target_id: str; direction: str; weight: float | None
    source_label: str; target_label: str; source_type: str; target_type: str

# RAGState gets:  dialectical_edges: list[DialecticalEdge] = field(default_factory=list)
```

`_ingest_get_neighbors` appends a `DialecticalEdge` for every edge whose `relation ∈
DIALECTICAL_RELATIONS`, **retaining both endpoints**. Apply the **same retention in
`_ingest_explore_subgraph`** (subgraph results carry edge lists too — judge #1's explicit point) and in
the new debate tools. `populate_state` (`evidence_collector.py:102-139`) writes `dialectical_edges`.
This alone makes "0 edges used" physically impossible.

### 2.2 Lock 2 — two new relational tools (the debate affordance F3 lacks)

The current 8 tools are entity-centric. Add two, registered in `tools.py`, surfaced in the ReAct
registry and system prompt. Both are **pure SQL / KG adjacency / tree-nav / `has_translation` join — no
embeddings.**

**Tool A — `find_debates(topic, period_filter?, limit?)`** — the missing relational entry point.

- **Concrete vectorless ranking (grafted from P2 §2a — the only proposal that specified it):**
  ```sql
  SELECT n.id, n.label, n.description,
         (incoming_dialectical_edge_count) AS degree,
         ts_rank(to_tsvector(n.label || ' ' || n.description), plainto_tsquery(:topic)) AS lex
  FROM kg_nodes n
  LEFT JOIN (
      SELECT target_id, count(*) AS incoming_dialectical_edge_count
      FROM kg_edges
      WHERE relation IN ('participates_in','contributes_to','has_position',
                         'opposes','critiques','responds_to')
      GROUP BY target_id
  ) d ON d.target_id = n.id
  WHERE n.type IN ('debate','controversy','position')
    AND (:period_filter IS NULL OR n.period = ANY(:period_filter))
  ORDER BY (lex + 0.15 * least(degree, 40)) DESC
  LIMIT :limit;
  ```
- Returns `[{debate_id, label, summary, participant_ids, opposing_pairs, grounded_passage_count,
  degree}]`, ranked **most-contested-first** so the model sees live fault lines up top.
- `period_filter` excludes Medieval/Modern debate nodes when the question is about antiquity.
- Exposes the 33 `debate`/`controversy`/`position` nodes + 312 dialectical edges the facet template
  never touched. Repoints the dead `query_scholarly_consensus` ref (`scholarly_agent.py:640`).

**Tool B — `build_controversy_frame(seed_id)`** — the dossier-unit retriever (the novel core).

- Accepts a `debate` node **OR** a `scholar_position_*` node (critical: the fault-line `opposes` edges
  hang off the *position* nodes, not the debate node — judge #2's secondary attack on P2/P3's
  one-call-from-debate assumption).
- Traverses **one hop of dialectical edges in both directions** to assemble the bipolar/star frame:
  `{anchor, positions[], links[]}`. For each position, pulls grounding
  (`scholar_position → created_by/advanced_in → publication`; `→ cites_primary_source → passage`) and
  the contested primary passages (`debate ←contributes_to← passage`; `position →evidenced_by→
  passage`), each **auto-paired with its `_en` translation** via `has_translation`.
- Returns a fully-formed `ControversyFrame` (§3.2). One call → one ready-to-synthesise unit.

**The empty-debate-node fallback (non-negotiable, all three missed it).** When the seed is a debate
node with **no dialectical out-edges or 0 grounded passages** — true for
`debate_origins_notion_of_will_modern_paradigm` and `debate_carneadean_antiastrology_tradition`:
1. Resolve participants by **lexical-matching the debate label/description** against `scholar_*` and
   `scholar_position_*` nodes.
2. **Hop via the `argument_*` / `argument_cafma_*` clusters**: pull the `contributes_to` arguments
   pointing *at* the debate, then for each argument follow its `opposes`/`critiques`/`advanced_in`
   edges to recover the fault line.
3. For `origins_notion_of_will`: the `opposes` edges live on
   `scholar_position_frede_will_originates_epictetus` ↔ `scholar_position_dihle_will_christian_innovation`
   etc. — `build_controversy_frame` **re-seeds on those position nodes** and merges the result back
   under the debate.
4. For `carneadean`: the dispute edge is
   `scholarly_argument_amand_de_mendieta_* OPPOSES scholarly_argument_ramelli_*`; recover it via the
   `participates_in` chain + the `argument_cafma_*` cluster; ground in `passage_eusebius_praep_ev_6_6_5`.

This fallback is what makes the trigger question's f1 (Frede/Dihle) and f4 (Amand/Ramelli) frames
non-empty on the *real* graph.

### 2.3 Lock 3 — the context pack gets an edge layer (F2 fix)

`_build_context_pack` (`graph_nodes.py:3377-3484`) today has exactly three layers (`## KG Metadata`,
`## Work Sections`, `## Evidence Bundles`) and **no edge slot**. Add a top-level `## Controversy
Frames` layer serialising each `ControversyFrame` — positions (holder + page), the dialectical links as
`A —critiques→ B` lines, the contested passages. `ContextPack` in `state.py` gets a `controversy_frames`
field. The synthesis prompt now **structurally cannot** be edge-blind.

### 2.4 Lock 4 — debate-first system prompt + dual-channel, coarse→fine escalation

Rewrite `NATIVE_SYSTEM_PROMPT_TEMPLATE` (`react_loop.py:566-600`) to be debate-first and shape-aware:

> "This knowledge graph encodes scholarly **disagreement** as edges (`opposes`, `critiques`,
> `responds_to`, `refutes`, `contrasts_with`). For any question about debates, controversies, origins,
> or comparisons, your FIRST move is `find_debates`, THEN `build_controversy_frame` on each fault line —
> do **not** start by reading entity descriptions. A debate is real only if you can name the *two sides*
> and the *edge* between them. For every position you surface, retrieve its grounding (publication +
> primary passage) before reporting it; always fetch the `_en` translation alongside the original. Never
> write a position without its holder and page; never paraphrase a position you have not located via an
> edge; never assert a modern label ('libertarian', 'compatibilism', 'the will') as historical fact."

- **Dual-channel (research §2):** per frame, run the **relational channel**
  (`build_controversy_frame`, `get_neighbors` filtered to dialectical relations) AND the
  **lexical/lemmatic channel** (`search_nodes`, `search_passages`, tree-nav) for grounding the
  structural channel can't supply. Merge via the existing RRF; the `ControversyFrame` is the spine
  lexical hits attach to.
- **Coarse→fine ladder, model picks the rung (research §3, A-RAG):**
  `find_debates`/`search_nodes` → `build_controversy_frame`/`get_neighbors` → `get_node_detail` →
  `read_passages` (full, bilingual). **Never truncate at a tool boundary** — read deep only on demand.
- **Anaphora-chained hops (kept from P1 §2.4 — the most genuinely agentic mechanism, both judges):**
  `build_controversy_frame` returns node IDs the model binds into the next call ("map
  `frede_position`" → returns its four `opposes` edges → "map `dihle_position`"…). This keeps the
  design honest to "model-driven, not a fixed program."

---

## 3. Evidence dossier — the `ControversyMap`

The dossier is **not** the old `ScholarlyDossier` of generic facets. It is a single typed
`ControversyMap`: a list of `ControversyFrame`s + a pool of standalone exegesis units, each fully
grounded.

### 3.1 Models (new pydantic in `state.py`)

```python
class PassageRef(BaseModel):
    passage_id: str; work: str; author: str; canonical_ref: str; cts_urn: str | None
    original_text: str            # FULL, untruncated, polytonic diacritics preserved
    english_text: str | None      # the _en counterpart, auto-joined via has_translation
    language: str

class GroundedPosition(BaseModel):
    position_id: str              # scholar_position_* / scholarly_argument_* / ancient person/arg
    holder: str                   # "Michael Frede" — always a HOLDER, never asserted as truth
    holder_node_id: str
    holder_type: Literal["modern_scholar","ancient_author","school"]
    claim: str                    # the scholar's thesis in ONE attributed sentence
    publication: str | None       # "Frede 2011, A Free Will, pp. 153–174"
    publication_node_id: str | None
    page_grounding: str | None    # page/locus if present in node metadata; else None (never invented)
    primary_support: list[str]    # PassageRef ids this position cites

class DialecticalLink(BaseModel):           # FLAT and STAR-TOLERANT (not pro/con)
    relation: str                 # opposes | critiques | responds_to | refutes | agrees_with | ...
    from_id: str; to_id: str
    from_holder: str; to_holder: str
    gloss: str | None             # one-line scholarly gloss of the disagreement

class FrameCompleteness(BaseModel):
    has_two_sides: bool           # ≥1 position with ≥1 attacker
    has_orphan_attack: bool       # an attacker with no surfaced defender ⇒ expand (internal signal only)
    has_primary_grounding: bool   # ≥1 contested passage
    incident_edge_count: int      # raw count — drives ordering (NO score)

class ControversyFrame(BaseModel):
    frame_id: str
    debate_node_id: str | None
    title: str                    # "When did a notion of 'the will' emerge?"
    period: str
    positions: list[GroundedPosition]
    links: list[DialecticalLink]
    contested_passages: list[PassageRef]
    completeness: FrameCompleteness

class ControversyMap(BaseModel):
    question_frame: str
    shape: AnswerShape
    frames: list[ControversyFrame]            # ordered by incident_edge_count desc
    exegesis_units: list[PassageRef]          # passages not bound to a frame
    coverage_gaps: list[str]                  # planned patterns retrieval under-filled
    provenance: dict[str, PassageRef]         # full untruncated bilingual passages, by id
```

### 3.2 Non-negotiables (each fixes a named failure)

- **Untruncated (F5).** The 220-char `truncate_text` calls (`graph_nodes.py:4192/4211/4308/4401`) are
  **deleted, not relocated**. `original_text`/`english_text` are full strings. K2.x 262k context makes
  truncation unnecessary even for a 4-frame survey × ~8 passages.
- **Bilingual (affordance §4).** Every `contested_passage` is an original+`_en` pair via
  `has_translation` (2,953 pairs, 0 currently used). Enforces the project citation rule (*original +
  English, never French*) structurally. `read_passages` gains a `pair_translations=true` mode.
- **Page-grounded.** `page_grounding` reads the publication/page already on `scholar_position_*` /
  `scholarly_argument_*` nodes (e.g. "Sharples 1983, p. 22", "Frede 2011, pp. 153–174"). Absent →
  `None`, cite work-level only — **never invent a page**.
- **Provenance.** Every field carries its source node id; this *is* the ledger substrate (§4.4).
- **No strength scalar.** `FrameCompleteness` carries booleans + a raw `incident_edge_count` for
  ordering. There is **no DF-QuAD pass, no `base_strength`, no `contestedness` float.** (Amputation 1.)

### 3.3 Subagent distillation (research §6, optional — for the heavy shapes)

For `survey_of_debates` / `transmission_trace` with ≥3 frames, each `build_controversy_frame` + drill
runs as an **isolated retrieval subagent** (Fireworks `kimi-k2p6`, cheap tier per MEMORY) that does the
messy multi-call retrieval and returns **only** a distilled `ControversyFrame` (~1–2k tokens). The lead
synthesiser never sees raw tool chatter — it sees a clean `ControversyMap`. Single-frame shapes
(`position_comparison`, `primary_text_exegesis`) build inline. This is a latency/quality lever, not
load-bearing for correctness.

---

## 4. Dialectical scholarly synthesis — the core

One LLM call (`SCHOLAR_SYNTHESIS_MODEL`, `reasoning_content` enabled) over the `ControversyMap`,
replacing the entire `DraftClaimLedger → build_render_prompt → RenderGroundedAnswer →
_render_answer_fallback` chain. Prose comes **from reasoning over the map**, with cite-as-you-write — no
intermediate mechanical ledger feeds the prose.

### 4.1 Why it structurally replaces the template (F4/F6/F7/F8)

The facet template existed because the pipeline had *no relational object to reason over*. The
`ControversyMap` *is* that object: section structure comes from `frames`, claims from `positions`,
grounding from `contested_passages`. The template's three jobs are now data on the map → it is deleted.
The hardcoded Bobzien⟂Frede example in `RENDER_ANSWER_PROMPT` (`graph_nodes.py:673-677`, F7) is removed
— the *real* frames replace it. The inadequate-band branch (`graph_nodes.py:5757-5759`,
`scholarly_agent.py:1615-1618`) routes to the **prose-stated degraded mode** (§4.5), **never** to a
deterministic paste.

### 4.2 The synthesis prompt (the actual design)

Replaces `RENDER_ANSWER_PROMPT` (`graph_nodes.py:580-680`) with `DIALECTICAL_SYNTHESIS_PROMPT`.

**System role:**

> You are a historian of ancient philosophy writing for a specialist audience (Cambridge-Companion
> register). You reason **dialectically** over a CONTROVERSY MAP: a structured record of contending
> scholarly positions and the primary texts they fight over. You attribute every interpretive claim to a
> named scholar with a page reference; you ground every claim about an ancient author in a quoted
> primary passage; you hedge where the evidence underdetermines the question; you never adjudicate a
> dispute the field has not settled. Modern categories — "libertarian free will", "compatibilism", "the
> will" as a faculty, "indeterminist" — are scholarly characterisations and may appear ONLY inside an
> attributed position, NEVER asserted in your own voice as ancient fact. You never write Greek or Latin
> that is not present verbatim in the provided passages; if it is not in the map, paraphrase in English
> instead.

**Input blocks (the `ControversyMap`, serialised as structured markdown — edges explicit):**

```
## QUESTION  ⟨question_frame⟩   (detected shape: survey_of_debates)

## FRAME f1 — "When did a notion of 'the will' emerge?" (period: Imperial–Late Antiquity)
POSITIONS:
  [P_dihle]   Albrecht Dihle (Dihle 1982, Theory of Will, pp. 123–144):
              a discrete concept of will is a Christian innovation, crystallised in Augustine.
  [P_frede]   Michael Frede (Frede 2011, A Free Will, pp. 153–174):
              the notion originates earlier, with Epictetus and the late Stoa.
  [P_bobzien] Susanne Bobzien (Bobzien 1998, "The Inadvertent Conception"):
              there is no free-will *problem* in the ancients in the modern sense at all.
DIALECTIC (flat links, star-tolerant):
  P_frede   --opposes-->   P_dihle        (Frede dates emergence earlier than Augustine)
  P_frede   --opposes-->   P_bobzien      (Frede: will in Epictetus; Bobzien: no such problem)
  irwin_arg --opposes-->   P_frede        (Irwin: Aristotle may already have it)
  Fürst     --critiques--> P_dihle
CONTESTED PRIMARY TEXT:
  [passage_alex_fat_12] Alexander, De Fato 12 —
    GR: Ἀναιρουμένου δὲ ὡς ἐδείχθη τοῦ βουλεύσασθαι...
    EN: Since deliberation is abolished on their account...

## FRAME f2 … (Stoic compatibilism — Cic. Fat. 39–43, cylinder analogy) …
## FRAME f3 … (Alexander libertarian? — Sharples 1983 p.22) …
## FRAME f4 … (Carneadean transmission — Amand ⟂ Ramelli) …

## COVERAGE GAPS  ⟨frames the planner named but retrieval under-filled⟩
```

**Reasoning steps the prompt mandates (drive `reasoning_content`):**

1. **Thesis selection.** From the frames, state the *shape* of the answer (e.g. "the liveliest current
   disputes are not about whether the ancients were free, but about whether they had the concept at
   all, and when it emerged — these fault lines dominate"), NOT a doctrinal verdict.
2. **Map the fault lines.** Per frame: name the ≥2 opposing positions and the edge that opposes them. A
   frame with only one position is incomplete — flag it (feeds §5).
3. **Locate the primary anchor.** Per position, find the dossier passage it argues over. If none, mark
   *interpretation without surfaced primary grounding* and hedge harder.
4. **Weigh, don't decide — and detect talking-past (NON-NEGOTIABLE graft from P3 §4.2 / judge #1+#2).**
   Note where positions **genuinely conflict vs. talk past each other** — different `object_of_choice`,
   different dating of "the will", different sense of the term. The Frede⟂Dihle dispute is
   *substantially terminological* (they disagree about what "will" denotes); narrating it as a flat
   contradiction is a fidelity failure. Note who has `responds_to` whom (reply chains). **Do not pick a
   winner.**
5. **Check anachronism.** Flag every modern label; ensure it is voiced as *"what X calls…"*, never *"the
   Stoics held compatibilism."*
6. **Plan structure.** Choose the answer's movements **from the frames present**, not a fixed template —
   one movement per fault line for `survey_of_debates`; chronological for `concept_genealogy`;
   point-by-point for `position_comparison`.

**Writing instructions (drive `content`):**

- Open with a **thesis sentence** that answers the actual question.
- One movement per fault line; **adaptive headings derived from frame titles**, never
  `Definition/Textual Basis/Counterpoint`.
- Every interpretive sentence carries an **inline citation as it is written** (§4.3).
- Quote contested primary text in **original + English** at the point the scholars argue over it.
- **Hedge with the field's own markers** ("Bobzien argues…, though Frede contends…"; "the evidence
  underdetermines whether…").
- Close with what remains **genuinely open**.

### 4.3 Cite-as-you-write (research §8) — the inversion of F8

The model emits citations **inline during generation**, drawing ids from the map it was given:

```
Frede argues that a notion of the will is already operative in Epictetus
[P_frede: Frede 2011, pp. 153–174], a dating Dihle rejects in favour of an Augustinian
origin [P_dihle: Dihle 1982] — the two positions stand in direct opposition
[edge: opposes P_frede→P_dihle]. Yet the dispute is partly terminological: the Stoic texts
both invoke, such as Alexander's report that abolishing deliberation abolishes τὸ ἐφ' ἡμῖν
[passage_alex_fat_12: Alexander, De Fato 12], do not settle what "will" must denote…
```

Markers `[P_*: …]`, `[edge: …]`, `[passage_*: …]` are **resolvable against the map** because every id
came from it. This makes "uses edges (>0)" and "attributes each position with a citation" satisfied *by
construction*.

### 4.4 Provenance ledger as byproduct (reverses F8)

A **deterministic** post-pass (`build_provenance_ledger`) parses the inline markers out of the finished
prose and resolves each to its map entry, emitting the `ClaimLedgerItem[]` the UI reference map and
`ProgrammaticVerify` expect. Each extracted claim is tagged `assertion | attributed_position |
interpretation` (research §8) so the referee applies type-specific rules. `DraftClaimLedger`
(`graph_nodes.py:5189-5429`) is **demoted** from a generative pre-step to this post-synthesis parser;
`build_render_prompt`'s `ledger_json` input (`graph_nodes.py:5471-5497`) is **deleted** — the prompt is
built from the `ControversyMap`, not the ledger. The prose is the source of truth; the ledger is its
index.

### 4.5 Degraded mode — a reasoned hedge, never a template (graft from P3 §4.5)

`_render_answer_fallback` (the facet template, `graph_nodes.py:3575-3733`) and
`_derive_claim_ledger_fallback` (the 220-char paste, `graph_nodes.py:4169+`) are **deleted**. When
synthesis genuinely fails or frames are thin, the degraded mode is a **shorter reasoned answer over
whatever frames did assemble, explicitly stating its coverage limit in prose**: *"The graph holds rich
material on the discovery-of-will debate; coverage of the Carneadean-transmission dispute was thin in
this run."* This is a real scholar's hedge — more faithful than P1/P2's "re-synthesise with a tightened
prompt" (which can loop) and never a node-paste. `_classify_render_quality`'s ~10k-char floor (F7/F9) is
replaced by a **content gate**: "does the answer name ≥1 fault line with both sides + ≥1 primary
citation?" A correct 600-word debate survey now passes instead of being thrown away for the template.

---

## 5. Scholar-grade verification loop

Three referees + an iterate condition, run after synthesis. All operate **against the
`ControversyMap`, not free memory** (CoVe's load-bearing trick, research §7). Any rejection triggers
**targeted re-retrieval + RARR span-edit** (research §7) — not wholesale regeneration.

### 5.1 Adversarial citation referee (CitationVerifierV2, extended)

Reuse `citation_verifier_v2.py` (JSON bug now fixed), fed the map. Because cite-as-you-write attaches
ids:
- Every `[passage_*]`/`[P_*]` marker is checked via **NLI-style entailment** — does the cited map
  passage/node actually entail the sentence's claim? (research §8, ALCE).
- Markers that don't resolve to the map (a hallucinated id) are **hard-rejected**.
- **Quotation claims get an exact-substring check** against the original passage text — zero tolerance
  for invented Greek/Latin (the integrity policy).
- Cap raised from 8 to **all attributed-position claims** on the synthesis path (these are
  load-bearing). REJECTED → mark the span for RARR edit.

### 5.2 Completeness critic — with a real denominator (P1's unique strength, kept)

The verification *oracle*. The denominator is **graph-real: the set of frames `find_debates` /
`build_controversy_frame` actually returned** — NOT the planner's hints (judge #2's correction of P3's
hand-wavy denominator). Mechanical set-diff:

```
fault_line_coverage = |fault lines narrated (parsed from [edge:]/frame markers)|
                      / |fault lines in the ControversyMap|
```

Any frame in the map but absent from the answer → a concrete gap → a targeted expansion query
("`build_controversy_frame` on `debate_carneadean_antiastrology_tradition`") that re-enters retrieval.
This is why the map-as-oracle matters: completeness has a denominator, and the anti-template regression
test (§7) is a one-line assertion.

### 5.3 Anti-anachronism gate (new — F11)

Deterministic + LLM hybrid, operating on the §4.4 claim tags:
- **Structural (cheap, deterministic):** scan prose for the MEMORY-flagged lexicon (`libertarian`,
  `compatibilism`, `incompatibilism`, `hard/soft determinism`, `the will` as a faculty, `free will
  problem`, `invention of the will`). Any occurrence **outside** an `attributed_position` span → gate
  failure.
- **Semantic (LLM, only on flagged spans):** confirm the attribution is correct (the label is genuinely
  *that* scholar's, not pinned to the wrong holder).
- Violation → **RARR-edit the offending span**: "the Stoics were compatibilists" → "the Stoics held
  what modern scholars term compatibilism." Operationalises the Phase-11/12 anachronism audits as a
  runtime gate.

### 5.4 Iterate condition

```
draft → {citation referee, completeness critic, anachronism gate} → verdict
  ACCEPT iff:  citation referee: 0 unsupported (after RARR edits)
           AND completeness: fault_line_coverage complete (or gaps marked "graph has no evidence")
           AND anachronism gate: 0 unattributed-label spans
           AND every reported fault line has ≥1 counter-evidence span (§4.2 step 4)
  REJECT → Query Expansion: turn each gap into a targeted retrieval (build_controversy_frame on the
           missed debate / read the missing passage) → augment the map → RARR-edit only affected spans
           → re-verify.
  Cap at N_max expansion rounds (budget tier). On hard failure → §4.5 degraded mode (prose-stated
  coverage limit), NEVER a template.
```

The loop stops only when evidence is **sufficient + complete** (research §1) — the literal cure for "0
edges, garbage answer."

---

## 6. Budgets (reconciling the latency bugs F9/F10)

| Tier | Tool calls | Synthesis `max_tokens` | Verify rounds | When |
|------|-----------|------------------------|---------------|------|
| `quick` | 12 | 6,000 | 0 | single-shape, well-grounded |
| `standard` | 24 | 8,000 | 1 | default |
| `deep` | 45 | 8,000 | 2 | `survey_of_debates` / `transmission_trace` cross-period |

- **Char-floor removed (F9/F10).** The ~10–15k-char floor (`graph_nodes.py:3987-3993`) collided with
  the 8k-token cap (`scholarly_agent.py:147-164`), forcing mechanical fallback. The floor is *deleted*;
  the §4.5 **content gate** replaces it (completeness against the map, not length). A correct short
  survey is no longer rejected.
- **Token caps reconciled.** Streaming render cap (`scholarly_agent.py:147-164`) raised to **8000** to
  match the blocking path — the two paths must agree. ≥5000 is mandatory (reasoning eats the budget).
- **Tool-call cap shape-aware.** `_tool_call_budget` (`react_loop.py:91-115`) raised to 45 for
  survey/transmission so a Bobzien⟂Frede + origins + Alexander + Carneadean survey can fetch its
  `build_controversy_frame` + bilingual `read_passages` calls. The **real stop condition is the
  completeness critic**, not a blunt count.
- **Reasoning is a feature, not a stall.** `_await_with_heartbeat` / `_stream_render` `max_wait` raised
  for the synthesis call (K2.7-highspeed ~55s, K2.7-code ~95s) and the heartbeat **streams
  `reasoning_content` as a "thinking…" trace** so the UI shows progress instead of abandoning to
  fallback (F9).
- **`_inject_passage_quotations` deleted (F10).** Passages are now *in* the synthesis via the map,
  cited inline — no post-hoc raw-dump bolting.
- **Cost control.** Only 1 synthesis + ≤2 expansion rounds touch the synthesis tier; everything else
  stays on cheap Fireworks `kimi-k2p6`. Subagent distillation keeps the synthesis call's *input* small
  despite deep retrieval.

---

## 7. Migration plan + G2 measurement

### 7.1 Staged migration — each stage independently shippable, behind `SCHOLAR_RAG=true` (default off until M5 passes eval)

| Stage | Change | Files | Risk |
|-------|--------|-------|------|
| **M0 — Reachability probe + edge survival** | **FIRST: probe that `find_debates`→frame surfaces the 11 `opposes` edges on real debate nodes** (highest-risk assumption). Then: keep `relation`+`direction`; add `DialecticalEdge`/`dialectical_edges` to state; retain edges in `_ingest_explore_subgraph` too | `evidence_collector.py:178-192,102-139`; `state.py` | low; structural prerequisite |
| **M1 — Relational tools** | `find_debates` (SQL ranking) + `build_controversy_frame` (with empty-node fallback); register; debate-first system prompt; repoint dead `query_scholarly_consensus`; auto-bilingual pairing | `agents/tools/*`, `tools.py`, `react_loop.py:566-600`, `scholarly_agent.py:640` | medium |
| **M2 — Planner** | `ResearchPlan` + `PlanResearch` node (6 shapes + `factual_lookup`); delete facet picker | `state.py`, `graph_nodes.py:1082-1271` | medium |
| **M3 — `ControversyMap` dossier** | frame assembly + `_en` join + page-grounding; `## Controversy Frames` layer in context pack; `ContextPack.controversy_frames` | `state.py`, `graph_nodes.py:3377-3484`, `evidence_collector.py` | medium |
| **M4 — Dialectical synthesis (the cutover)** | `DialecticalSynthesis` node + `DIALECTICAL_SYNTHESIS_PROMPT` (cite-as-you-write, "weigh-don't-decide"); `build_provenance_ledger` post-pass; **delete** facet template + 220-char pastes + char floor; invert `DraftClaimLedger`; prose-stated degraded mode | `graph_nodes.py:580-680,3575-3733,4169+,5189-5429,5471-5497` | **high** (the heart) |
| **M5 — Verification loop** | extend referee (NLI + marker-resolve + substring); completeness critic (graph-real denominator) + anachronism gate + RARR edit + iterate | `citation_verifier_v2.py`, `scholarly_agent.py:729-869` | medium |
| **M6 — K2.7 wiring + budgets** | `SCHOLAR_SYNTHESIS_MODEL` resolver, KIMI temp=1 clamp, fallback chain; streaming cap = blocking cap; reasoning heartbeat | `llm_service.py:106-113`, `scholarly_agent.py:147-164,1486,1569`, `opencode.json`, `repl.py`, `llm_pricing.py` | low |
| **M7 — Flip default, delete dead code** | remove `_inject_passage_quotations` (F10); delete old template path; flag removal | flag removal | low |

M0+M1 alone make edges visible (validate "edges > 0" early). **M0's reachability probe must pass before
M4** — it is the gate on the whole edifice. M4 is the irreversible core; keep the old path behind the
flag for one release for A/B, then delete.

### 7.2 Measurement — G2 eval harness, old-vs-new (graft from P2 §7, the only proposal that made the eval *able to see* the win)

The existing harness (`tests/eval/run_eval.py`, `eval_lib/scoring.py:citation_prf`,
`must_not_appear.jsonl`) is **structurally blind to relational improvement** until debate-survey cases
exist. Concretely:

1. **Add the missing cases to `queries.yaml`** — the trigger question + kin, with
   `expected_entities` = the exact debate/position node IDs from the affordance inventory
   (`debate_discovery_of_will`, `scholar_position_frede_will_originates_epictetus`,
   `scholar_position_dihle_will_christian_innovation`,
   `scholar_position_bobzien_no_free_will_problem_ancients`,
   `scholarly_argument_amand_de_mendieta_carneades_anti_fatalist_moral__0`,
   `scholarly_argument_ramelli_origen_s_knowledge_of_alexande_0`, …) and `gold_claims` asserting the
   fault lines. Without these the harness can't reward edge usage.
2. **Baseline capture** (old path) → `data/goals/g6/baseline_template.json`.
3. **New-path capture** (`SCHOLAR_RAG=true`) → `data/goals/g6/scholar_rag.json`; compare.
4. **Add three new metrics to `run_eval.py`:** (a) **edge-use count** — distinct dialectical edges
   referenced in the answer's ledger (must be >0, criterion b); (b) **attribution rate** — fraction of
   modern-label occurrences inside an attributed span (anachronism gate, criterion c); (c)
   **counter-evidence coverage** — fraction of reported fault lines with a reported attack. Plus
   **fault-line coverage** (the completeness critic's own ratio) and **non-repetition** (n-gram
   self-overlap, catching "same node 4×").
5. **Anti-template regression fixture (P1's best test, kept):** on the trigger question, assert the new
   path produces ≥3 distinct fault lines, >0 `opposes`/`critiques` edges in the map, and **0
   occurrences of the `"frames the issue as"` template string** — so the template can *never silently
   return*. Frozen as a snapshot test.

**Success bar on the trigger question** ("big open debates today about free will in antiquity"),
old-vs-new: enumerates the real live debates (discovery-of-will Bobzien⟂Frede⟂Dihle; Stoic
compatibilism; Alexander libertarian — Sharples; Carneadean transmission — Amand⟂Ramelli); uses ≥3
`opposes`/`critiques` edges; every position attributed + page-grounded; genuine non-repeating prose;
all three referees pass; zero `must_not_appear` hits.

---

## Appendix — how each failure (F1–F12) is killed

| F | Failure | Killed by |
|---|---------|-----------|
| F1 | edges discarded at ingestion | §2.1 `DialecticalEdge` store; `_ingest_get_neighbors` + `_ingest_explore_subgraph` keep relation+direction |
| F2 | no edge slot in prompt | §2.3 `## Controversy Frames` layer; edges are first-class in the map |
| F3 | no debate retrieval affordance | §2.2 `find_debates` + `build_controversy_frame` (+ empty-node fallback) |
| F4 | facet template IS the answer | §4.1 template deleted; inadequate-band → reasoned degraded mode (§4.5), never paste |
| F5 | 220-char node-paste claims | §3.2 truncations deleted; full bilingual provenance |
| F6 | question-shape-blind facets | §1 six-shape planner emits graph patterns, not fixed sections |
| F7 | real synthesis overridden by gates | §4.1 synthesis is the path; §4.5 char-floor → content gate; hardcoded example removed |
| F8 | ledger→prose dependency | §4.4 ledger extracted from prose as byproduct |
| F9 | latency caps force mechanical synthesis | §6 tiered budgets; floor removed; caps reconciled; reasoning heartbeat |
| F10 | post-hoc passage dumping | §6 `_inject_passage_quotations` removed; passages cited inline |
| F11 | verify audits citations only | §5.2 completeness critic (graph-real denominator) + §5.3 anachronism gate |
| F12 | K2.7 not wired | §K2.7 `SCHOLAR_SYNTHESIS_MODEL`, one-line swap, temp clamp |
