# G6 Scholar-RAG — SOTA Building Blocks (web research)

> Scope: cutting-edge **agentic / deep-research / dialectical / claim-grounded** RAG mechanisms
> relevant to a **vectorless, agentic, scholarly-reasoning** KG system.
> EXPLICITLY EXCLUDED: vector GraphRAG (Microsoft community summaries, LightRAG, HippoRAG
> embeddings, Self-RAG's vector retriever) — we keep ts_rank + lemmatic + tree + KG traversal.
> Date: 2026-06-16.

Each mechanism below is harvested as a reusable *building block*, not a vendor pitch, with a
one-line "→ apply" for a vectorless scholarly KG.

---

## Top 8 mechanisms (ranked, the ones worth stealing)

### 1. Reflection-routing loop: Draft → Verify-sufficiency → Expand (GraphSearch, 2509.22009)
GraphSearch splits the workflow into an **Iterative-Retrieval phase** (Query Decomposition →
Context Refinement → Query Grounding) and a **Reflection-Routing phase** (Logic Drafting →
Evidence Verification → Query Expansion). The loop's *driver* is **Evidence Verification**:
it draws a coherent reasoning chain, **explicitly exposes the gaps**, returns Accept/Reject;
Reject triggers **Query Expansion** that generates new sub-queries *targeted at the missing
evidence*, which re-enter retrieval. Iterate until Accept or budget hit. This is the exact cure
for the "0 edges, garbage answer" failure: the loop only stops when evidence is sufficient.
→ **Apply:** make the synthesis call itself emit a *gap list* ("which graph debate/edge did I
not cover?") that becomes the next retrieval query — replace the one-shot deterministic render
with a draft→verify→expand loop over the KG.

### 2. Dual-channel retrieval: relational queries ≠ semantic queries (GraphSearch)
Same question is issued **twice in different shapes**: a *semantic* query over text chunks AND a
*relational* query formulated as **subject–predicate–object triples** retrieved directly as
subgraphs, enabling multi-hop reasoning "with reduced reliance on textual co-occurrence." The
relational channel is what surfaces structure that lexical search misses.
→ **Apply:** for every sub-claim, run BOTH the existing lexical/lemmatic channel AND a
**relational channel** that asks the model to name the edge pattern to fetch
(`debate → participants → opposes/critiques/responds_to → contested passage`). This is the
"argument-structure-first retrieval" the goal wants, with literature backing.

### 3. Hierarchical retrieval interfaces, model picks the granularity (A-RAG, 2602.03442)
Core thesis: *don't pre-bake a retrieval algorithm or a fixed workflow* — **expose retrieval as
tiered tools** (keyword/lexical, semantic, chunk-read) and let the agent choose granularity and
when to drill down, coarse-to-fine. Outperforms fixed pipelines with **comparable or fewer
retrieved tokens** because the model only reads deep when it decides it needs to. Validates the
vectorless-agentic bet: the win is from *model-driven retrieval decisions*, not a smarter index.
→ **Apply:** keep the 8-tool ReAct surface but layer it coarse→fine
(`search_nodes` → `get_node_detail` → `explore_subgraph` → `read_passages` full-text), and let
Kimi decide when to escalate from a node label to the untruncated passage. Never truncate at the
tool boundary — A-RAG reads full chunks only on demand.

### 4. Query-complexity routing before you retrieve (Adaptive-RAG, 2403.14403)
A lightweight classifier routes each query to one of three regimes: **no-retrieval / single-step /
multi-step iterative**. Matches cost to difficulty; "emerging best practice" for production.
→ **Apply:** this is the goal's **Question→scholarly-shape planner**. Replace the generic 3-class
router with a *scholarly-shape* classifier (survey-of-debates, concept-genealogy,
transmission-trace, position-comparison, primary-text-exegesis, doxographical-synthesis) →
each shape names the graph patterns + retrieval depth to fetch. Routing decides the *plan*, not
just the budget.

### 5. Argument framework with gradual semantics — represent disagreement, never assert (ArgLLMs, 2405.02079)
For a contested claim, build a **bipolar argumentation framework**: supporting + attacking
arguments (recursively, depth/width configurable), give each a base strength τ∈[0,1], then run a
**deterministic gradual-semantics algorithm (DF-QuAD)** to propagate support/attack into a final
strength. The verdict is *faithfully determined by the structure*, fully traceable, and
**contestable** (raising a supporter's score monotonically raises the claim; adding an attacker
lowers it). It is dialectic-as-data, not prose opinion.
→ **Apply:** the *ideal* substrate for "attribute positions, never assert." Model
Bobzien⟂Frede etc. as a bipolar framework over the G5 disagreement edges
(`opposes/critiques/responds_to`); the synthesis reports the structure + strengths + who-holds-
what, and stays hedged because no single position is asserted as fact. Directly serves success
criterion (a)/(c).

### 6. Lead-agent + subagents with context isolation & distillation (Anthropic/OpenAI deep research)
Convergent frontier pattern: a **lead agent** holds the plan; **subagents** each explore deeply
(tens of thousands of tokens) but return only a **distilled 1–2k-token summary**. Separation of
concerns: messy retrieval context stays in the subagent; the lead synthesizes clean dossiers.
Four pillars: detailed system prompt + planning tool (todo list) + subagents + persistent
file/memory. Plan = a DAG of sub-tasks, not reactive step-by-step.
→ **Apply:** per scholarly sub-claim (or per debate node), spawn a retrieval subagent that
returns a compact **evidence dossier** (full primary passage orig+EN, page-grounded modern
position, disagreement edges, confidence). Lead model does dialectical synthesis over clean
dossiers — matches the goal's Evidence-dossier + Dialectical-synthesis split, and keeps Kimi's
context uncluttered. (Memory note: subagents = sonnet/opus tier; main loop only orchestrates.)

### 7. Chain-of-Verification — independent verification questions (CoVe) + adversarial referee
After a draft, the model **plans verification questions**, then **answers each one in isolation**
(the load-bearing trick: short focused questions don't replay the long-answer's hallucinations),
then regenerates a corrected final. Pairs with **Self-Refine** (iterative critique→fix) and a
**completeness critic**. RARR adds the post-hoc complement: retrieve attribution for each claim,
**edit unsupported spans while preserving the rest**.
→ **Apply:** the goal's "scholar-grade verification loop." Per claim, generate isolated checks —
*does passage X actually say this? is this modern label attributed not asserted? is there an
anachronism?* — answered against the dossier, not free memory. Adversarial citation referee
(CitationVerifierV2) + completeness critic ("which graph debate did it miss?") + anti-anachronism
gate → iterate. RARR-style: don't regenerate wholesale, *edit* the unsupported sentence.

### 8. Claim-level decomposition + in-generation citation (ALCE / cite-as-you-write / claim-auditability)
Two attribution paradigms: **post-generation** (write, then retrieve sources per claim) vs
**in-generation / cite-as-you-write** (model decides mid-inference it needs evidence, retrieves
live, cites inline). ALCE scores **citation precision + recall via NLI** (does the cited source
*entail* the sentence?). Claim-Level Auditability (2602.13855) decomposes a report into discrete
**auditable claims**, separating *assertions from interpretations*, each linked to evidence, and
flags claims that extrapolate beyond source.
→ **Apply:** invert the current ledger→prose dependency: synthesize prose with **inline
cite-as-you-write** (every attributed position carries a passage_id / scholar-citation as it's
written), then the **provenance ledger falls out as a byproduct**. Verify with NLI-style
entailment: each sentence's cited passage must actually support it (citation-F1 in the G2 eval).
Decompose answer into claims, tag each `assertion | attributed-position | interpretation`.

---

## Secondary mechanisms (supporting, not in top 8)

- **Search-R1 (2503.09516)** — interleave `<think>`/`<search>` tokens; model autonomously emits
  search queries mid-reasoning, retrieval is a first-class reasoning action (RL-trained, but the
  *prompt-level interleaving pattern* is reusable without RL). → Lets Kimi call KG tools inside a
  reasoning trace rather than in a rigid retrieve-then-read phase.
- **Self-RAG reflection tokens** — model emits markers signaling "retrieve now" / "this is
  unsupported," triggering verification or more retrieval. (Use the *control signal* idea; skip
  its vector retriever — excluded.) → Inline self-flags that drive the verify/expand loop.
- **Query Grounding (GraphSearch module 2/3)** — accumulate intermediate answers and *instantiate
  later sub-queries with resolved references* (anaphora resolution across hops). → Chain KG hops:
  "find Bobzien's position" → "find who *responds to that*" with the resolved node bound in.
- **Context Refinement (GraphSearch)** — keep only the most informative evidence before drafting,
  to fight context dilution. → Dossier pruning before synthesis.
- **Multi-persona debate (2412.04629) / MArgE (2508.02584)** — generate opposing personas to
  widen perspective coverage and reduce confirmation bias; mesh argumentative evidence from
  multiple sources. → Optional generator for the bipolar framework when the graph is thin on one
  side of a debate (but never fabricate ancient text — personas argue *about* attested evidence).
- **DAG planning over reactive prompting (deep-research survey 2508.12752)** — plan sub-tasks as a
  DAG up front. → The scholarly-shape planner emits a small DAG of retrievals, not a flat list.

---

## Synthesis: how these compose into Scholar-RAG

1. **Plan** — Adaptive-RAG routing → scholarly-shape classifier → DAG of graph patterns (#4, #6).
2. **Retrieve** — dual-channel (relational + lexical), hierarchical coarse→fine tools, subagent
   per sub-claim returning a distilled dossier (#2, #3, #6); Search-R1-style interleaving (#sec).
3. **Represent disagreement** — bipolar argument framework over G5 edges, gradual-semantics
   strengths, positions attributed not asserted (#5).
4. **Synthesize** — dialectical prose with **cite-as-you-write**; provenance ledger as byproduct
   (#8). Draft exposes its own gaps (#1).
5. **Verify** — CoVe isolated checks + completeness critic + anti-anachronism gate + NLI citation
   referee; RARR-edit unsupported spans; loop via Query Expansion until Accept (#1, #7, #8).

This is a vectorless instantiation: every "retrieval" is a KG traversal / lexical-lemmatic /
tree-nav call; no embeddings anywhere in the chain.

---

## Sources

- Search-R1 — https://arxiv.org/abs/2503.09516 ; https://github.com/PeterGriffinJin/Search-R1
- GraphSearch — https://arxiv.org/abs/2509.22009 ; https://github.com/DataArcTech/GraphSearch
- A-RAG (hierarchical retrieval interfaces) — https://huggingface.co/papers/2602.03442 ; https://github.com/Ayanami0730/arag
- Adaptive-RAG — https://arxiv.org/html/2403.14403
- ArgLLMs (argumentative claim verification) — https://arxiv.org/html/2405.02079
- Deep research patterns (Anthropic/OpenAI) — https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents ; survey https://arxiv.org/pdf/2508.12752
- Claim-Level Auditability for Deep Research Agents — https://arxiv.org/pdf/2602.13855
- ALCE (cite + NLI eval) — https://www.semanticscholar.org/paper/e7c97e953849f1a8e5d85ceb4cfcc0a5d54d2365 ; attribution survey https://arxiv.org/html/2508.15396v1 ; RARR via same survey
- Chain-of-Verification (CoVe) — https://learnprompting.org/docs/advanced/self_criticism/chain_of_verification
- Self-RAG (reflection-token control idea only; vector retriever excluded) — https://medium.com/@shaikh-vasim/self-rag-...
- Multi-persona debate — https://arxiv.org/abs/2412.04629 ; MArgE — https://arxiv.org/pdf/2508.02584
