# Agentic GraphRAG — Literature Review (2024-2026)

Companion to `2026-03-31-agentic-retrieval-design.md`. Full research on state-of-the-art techniques.

## Papers Reviewed

| Paper | Venue | Key Technique | Adopted? |
|-------|-------|---------------|----------|
| Microsoft GraphRAG | arXiv 2024 | Community clustering, local/global search | Concept only (we have curated KG) |
| DRIFT Search | Microsoft 2025 | Follow-up question generation from community reports | Yes — agent decomposes broad queries |
| LazyGraphRAG | Microsoft 2025 | Defer LLM to query time, iterative deepening | Yes — core principle |
| Think-on-Graph 2.0 | ICLR 2024 | Alternating KG traversal + document retrieval | Yes — primary pattern |
| Paths-over-Graph | ACM Web 2025 | Multi-stage path pruning | Yes — metadata-first exploration |
| Graph-Constrained Reasoning | ICML 2025 | KG-Trie constrained decoding | Principle only (grounding constraint) |
| Debate-on-Graph | AAAI 2025 | Sufficiency checking, early stopping | Yes — after every 2-3 tools |
| FiDeLiS | ACL 2025 | Deductive verification beam search | Principle only (step verification) |
| Self-RAG | ICLR 2024 | Reflection tokens for retrieval control | Yes — 4 reflection dimensions in prompt |
| CRAG | ICLR 2024 | Retrieval quality assessment + correction | Yes — self-correction behavior |
| Adaptive-RAG | NAACL 2024 | Query complexity routing | Yes — ClassifyQueryType sets budget |
| FLARE | EMNLP 2023 | Low-confidence token triggers retrieval | Future — synthesis-time retrieval |
| IRCoT | ACL 2023 | Interleave reasoning + retrieval | Yes — core ReAct pattern |
| HopRAG | ACL 2025 | Passage graph with retrieve-reason-prune | Yes — get_neighbors prune pattern |
| HippoRAG | NeurIPS 2024 | Personalized PageRank from seeds | Yes — explore_subgraph tool |
| LightRAG | EMNLP 2025 | Dual-level (entity + topic) retrieval | Yes — multi-granularity tools |
| StructRAG | ICLR 2025 | Hybrid structure routing | Concept (query-type routing) |
| RoboData | Wikidata 2025 | FSM with free-form exploration state | Yes — hybrid architecture |
| Graf von Data | CEUR-WS 2025 | 3-action ReAct (search/describe/query) | Yes — visible trace |

## Key Design Principles Extracted

1. **Interleave reasoning and retrieval** (IRCoT) — each tool call informed by reasoning
2. **Periodic sufficiency checks** (DoG) — after 2-3 tools, "do I have enough?"
3. **Retrieve-reason-prune** (HopRAG, PoG) — metadata first, detail only for relevant items
4. **Multi-level granularity** (LightRAG) — entity-level AND topic-level tools
5. **Self-correction** (CRAG) — if retrieval returns noise, try different strategy
6. **Grounding constraint** (GCR) — synthesis can only cite retrieved evidence
7. **Token budget management** (Google Cloud) — summarize when approaching 50%
8. **Visible trace** (GvD) — full audit trail for scholarly transparency
9. **PPR for broad exploration** (HippoRAG) — single-step graph-aware seed expansion
10. **Iterative deepening** (LazyGraphRAG) — start broad, deepen only on promising paths
