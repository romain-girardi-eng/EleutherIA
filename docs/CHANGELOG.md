# Changelog

All notable changes to EleutherIA will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [5.0.0] - 2026-02-20

### Changed
- **GraphRAG: PageIndex V3** — Replaced 13-stage HiRAG V2 pipeline with direct retrieval architecture
  - 2 LLM calls instead of 10+ (1 embedding + 1 synthesis)
  - `passage_citations` table as primary retrieval signal (curated KG-to-passage links)
  - No context truncation — leverages Gemini's ~1M token context window
  - Full ancient text passages with CTS URNs in LLM context
- Bundle size reduced from 628 KiB to 606 KiB

### Removed
- HyDE (Hypothetical Document Embeddings)
- CRAG (Corrective RAG) validation
- Self-RAG evaluation
- LLM reranking
- Query expansion
- Sufficiency loop
- Evidence layering
- Weighted graph traversal
- Pipeline config selection

### Fixed
- SSE line-splitting bug in Cloudflare LLM streaming (TCP buffer handling)
- Context truncation destroying Greek diacritics and corrupting passage text
- `charset=utf-8` added to SSE Content-Type header

## [2.0.0] - 2025-01-30

### Added
- Complete repository reorganization into 3 independent pip-installable packages:
  - `eleutheria-database`: Ancient texts corpus (189 works, 16,968 passages)
  - `eleutheria-kg`: Knowledge graph framework (2,193 nodes, 8,616 edges)
  - `eleutheria-graphrag`: Graph-based RAG for scholarly Q&A
- FAIR compliance with `codemeta.json` and `CITATION.cff`
- Simplified documentation structure (7 folders max)
- Root Makefile for all common operations
- Docker Compose for local deployment

### Changed
- Consolidated 4 GraphRAG services into 1 unified service
- Consolidated 3 hybrid search services into 1
- Restructured docs/ from 55+ folders to 7 organized folders
- Removed Cloudflare Workers from public repo (stays in private development repo)

### Removed
- Obsolete JSON backup files (~100MB savings)
- Duplicate service implementations
- Debug pages and components from frontend
- 167 one-off scripts (archived in private repo)

## [1.0.0] - 2024-12-01

### Added
- Initial public release
- Knowledge graph with 2,193 nodes and 8,616 edges
- 189 ancient Greek/Latin works with 16,968 passages
- GraphRAG Q&A with citation grounding
- Hybrid search (full-text + lemmatic + semantic)
- Interactive Cytoscape.js visualization
- Complete lemmatization for Latin texts
- FastAPI backend with PostgreSQL + Qdrant
- React frontend with TypeScript

### Technical
- 15 node types, 32 relation types
- 3072-dimensional Gemini embeddings
- RRF fusion for search result ranking
- JWT authentication with rate limiting
