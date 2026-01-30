# Changelog

All notable changes to EleutherIA will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
