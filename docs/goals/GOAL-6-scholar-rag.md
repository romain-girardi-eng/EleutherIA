# G6 — Invent "Scholar-RAG": a vectorless agentic graph-RAG that researches like a scholar

**Trigger (2026-06-16):** a live GraphRAG answer to "What are the big open debates today about free will
in antiquity?" was garbage — the same truncated node description pasted 4× under a rigid
Definition/Textual-Basis/Counterpoint template, 0 edges used, not answering the question. Romain: invent the
absolute-best architecture for this use case; it doesn't exist as a named paradigm, so build it.

**Root cause (confirmed in code):** the "synthesis" is a DETERMINISTIC claim-ledger template
(`graph_nodes.py` L1105/1179/1249 facet titles; L4308 `claim = f"{facet.title}: {label} frames the issue as
{truncate_text(node.description,220)}"`). Edge-blind, truncating, non-reasoning. The agentic VECTORLESS
retrieval (ReAct + 8 tools, PPR/`explore_subgraph`, lemmatic, tree-nav) is the RIGHT paradigm and stays.

**Hard constraints:** **vectorless** (no embeddings — keep ts_rank + lemmatic + tree + KG traversal);
**agentic** (model-driven iterative retrieval, not fixed algorithms); **reasons like a scholar** (weighs
primary text vs reception, attributes positions, represents disagreement, hedges, full provenance, zero
fabrication/anachronism). **STACK = Fireworks AI + opencode as configured in the platform** (`opencode.json`
provider=fireworks, `FIREWORKS_API_KEY`, ctx 256k/out 64k; `.opencode/agent/*` deep-research agents; MCP
`eleutheria`; `services/llm_service.py` default fireworks). Do NOT use Moonshot direct. **Model: Kimi K2.7
via Fireworks WHEN AVAILABLE** — Fireworks currently has only `kimi-k2p6`/`k2p5` (no k2p7 yet, 404), so keep
`accounts/fireworks/models/kimi-k2p6` now and make the K2.7 swap a one-line change at the same config points
(`opencode.json`, `llm_service.py`, `repl.py`, `llm_pricing.py`). Architecture is model-agnostic.

## The architecture to build ("Scholar-RAG")
1. **Question→scholarly-shape planner** — classify into an answer shape (survey-of-debates, concept-genealogy,
   transmission-trace, position-comparison, primary-text-exegesis, doxographical-synthesis) → a research plan
   naming the graph patterns to fetch. Replaces the fixed facet template.
2. **Argument-structure-first retrieval (novel)** — retrieve the RELATIONAL scholarship: `debate`/`controversy`
   nodes → participants → `opposes`/`critiques`/`responds_to`/`advanced_in` edges → contested passages.
   Fix the "0 edges" failure. The G5 disagreement layer is the substrate.
3. **Evidence dossier** — per sub-claim: full primary passages (original+English, untruncated), page-grounded
   modern positions, disagreement edges, confidence/provenance.
4. **Dialectical scholarly synthesis (K2.7)** — genuine reasoning over the dossier: thesis, attributed
   positions, primary grounding, counter-evidence, hedged conclusions, adaptive structure, inline citations.
   Prose from reasoning, NOT from templating the ledger.
5. **Scholar-grade verification loop** — adversarial citation referee (CitationVerifierV2, JSON bug now fixed)
   + completeness critic ("which graph debate did it miss?") + anti-anachronism gate → iterate.
6. **Provenance ledger as a byproduct** of synthesis (reverse the current ledger→prose dependency).

## Anti-goals
No vector store / embeddings. No fixed answer template. No truncated node-description pasting. No asserting
modern labels as fact ("invention of the will", "libertarian", "compatibilism" stay attributed).

## Success criteria
On the exact "open debates" question, the new answer (a) enumerates the real live debates the graph holds
(Stoic free will Bobzien⟂Frede; origins-of-the-will; Alexander libertarian; Carneadean transmission), (b) uses
edges (>0), (c) attributes each position with a citation, (d) is genuine prose (no repetition/template/
truncation), (e) verified (every claim traces to evidence). Measured by the G2 eval harness (citation-F1 +
faithfulness, now that the verifier parses) + a scholar-grade qualitative rubric, old-vs-new.

## Workflow phases
Research (web SOTA of agentic/deep-research/dialectical RAG — NOT vector GraphRAG; current-failure map; KG
affordance inventory; K2.7 model resolution) → Invent/Design (judge panel of full architectures → one spec) →
Blueprint (files to change, the synthesis module replacing the template, edge-first retrieval, K2.7 wiring,
self-critique loop, eval plan) → Implement (staged) → Verify (G2 eval + old-vs-new on the trigger question).
