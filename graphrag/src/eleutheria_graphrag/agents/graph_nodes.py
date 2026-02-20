"""
pydantic-graph FSM nodes for the agentic scholarly RAG pipeline.

Each node represents a stage in the pipeline.  The ``run()`` method
returns either the *next* node to transition to or ``End(answer)``
to terminate the graph with a ``ScholarlyAnswer``.

Node graph
----------
::

    ClassifyComplexity
     ├─ simple  → DirectKGLookup → VerifyCitations → End
     ├─ medium  → HybridRetrieve → Synthesize → VerifyCitations → End
     └─ complex → DecomposeQuery → SearchPrimarySources
                                      ↕ (loop)
                                   EvaluateSufficiency
                                      ↓ (sufficient)
                                   SearchSecondarySources
                                      ↓
                                   SynthesizeWithHierarchy
                                      ↓
                                   VerifyCitations → End
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from dataclasses import dataclass
from typing import Any

from pydantic_graph import BaseNode, End, GraphRunContext

from eleutheria_graphrag.agents.dependencies import Deps
from eleutheria_graphrag.agents.text_utils import truncate_json, truncate_text
from eleutheria_graphrag.agents.state import (
    Citation,
    Evidence,
    EvidenceLayer,
    EvidenceSource,
    QueryComplexity,
    RAGState,
    ScholarlyAnswer,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Context budget constants (sized for Gemini 3.1 Pro ~1M token window)
# ---------------------------------------------------------------------------

MAX_PASSAGE_DESCRIPTION = 2000  # Evidence.description for passages
MAX_PASSAGE_IN_CONTEXT = 4000  # Full passage text in context builder
MAX_NODE_DESC_IN_CONTEXT = 2000  # Node description in context builder
MAX_SECONDARY_DESC_IN_CONTEXT = 1200  # Secondary evidence descriptions
MAX_TREE_JSON = 15000  # Tree index JSON for LLM navigation
MAX_CRAG_CONTEXT = 12000  # Context for CRAG validation
MAX_ANSWER_FOR_EVAL = 8000  # raw_answer for SelfRAG/Refine
MAX_CONTEXT_FOR_REFINE = 20000  # accumulated_context for RefineSynthesis

# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are a scholarly assistant specializing in ancient philosophy, \
particularly debates about free will, fate, and moral responsibility \
in Greco-Roman thought.

Guidelines:
- Ground your answers EXCLUSIVELY in the provided context from the knowledge graph
- Cite specific ancient sources using [1], [2] notation for KG nodes
- For passages, use [P1], [P2] notation and QUOTE the original Greek/Latin text verbatim
- When a passage contains ancient Greek or Latin text, reproduce it EXACTLY as provided — \
do NOT paraphrase, reconstruct, or generate any ancient language text yourself
- NEVER fabricate, compose, or approximate Greek or Latin text — only quote what appears \
in the provided passages. If no passage text is available, describe the content in English
- Include CTS URNs where available in citations
- Distinguish between ancient primary sources and modern scholarly interpretations
- Use proper transliteration for Greek/Latin terms when discussing concepts
- Acknowledge scholarly debates and different interpretations
- Be precise about historical periods, dates, and philosophical schools
- Ensure all dates, names, and titles are accurate based on the provided context

CRITICAL: This is an academic resource held to the highest scholarly standards. \
If the context doesn't contain enough information, say so clearly. \
Never fill gaps with generated content that looks like ancient source material."""

CLASSIFY_PROMPT = """\
Classify the following scholarly question about ancient philosophy \
into one of three complexity tiers.  Return a JSON object with keys \
"complexity" (one of "simple", "medium", "complex") and "reason" (brief explanation).

Classification criteria:
- **simple**: Single-entity factual lookup (who, what, when). \
  E.g. "Who was Chrysippus?" or "What school did Epictetus belong to?"
- **medium**: Requires combining information about one topic from \
  multiple sources. E.g. "What did the Stoics believe about fate?"
- **complex**: Multi-hop, comparative, or requires distinguishing \
  primary sources from modern scholarship. \
  E.g. "How did Stoic fate evolve from Chrysippus to Epictetus, \
  and how do Bobzien and Frede disagree about this?"

Question: {question}

Respond ONLY with valid JSON."""

DECOMPOSE_PROMPT = """\
Decompose the following complex scholarly question about ancient philosophy \
into 2-4 simpler sub-questions that can each be answered independently \
and then combined.  Return a JSON array of strings.

Question: {question}

Respond ONLY with a valid JSON array of strings."""

SUFFICIENCY_PROMPT = """\
Given the following question and retrieved evidence, assess whether \
there is sufficient primary-source evidence to answer the question.

Question: {question}

Evidence summary:
- Primary ancient sources found: {primary_count}
- Passages with ancient text: {passage_count}
- Key nodes: {node_summary}

Return a JSON object:
{{"score": <float 0.0-1.0>, "sufficient": <bool>, "reason": "<brief explanation>", \
"refinement": "<optional refined search query if insufficient>"}}

Respond ONLY with valid JSON."""

HIERARCHICAL_SYNTHESIS_PROMPT = """\
Based on the following evidence about ancient philosophy, \
answer this question: {question}

{context}

INSTRUCTIONS:
1. Ground your answer in primary ancient sources first. \
Secondary scholarship provides interpretive context but is not authoritative \
for what the ancient authors actually said.
2. Cite sources using [1], [2] for knowledge graph nodes and [P1], [P2] for passages.
3. When citing passages that contain Greek or Latin text, QUOTE the original text \
exactly as provided — e.g. [P1]: "τῆς αὐτεξουσίου ἡμῶν κρίσεως". \
NEVER generate or approximate Greek/Latin text not found in the passages above.
4. Include CTS URNs from the passage metadata when available.
5. Ensure all biographical dates, work titles, and historical details are accurate \
based solely on the provided context.
6. If insufficient ancient source material is available, state this explicitly \
rather than generating plausible-sounding content."""


# ---------------------------------------------------------------------------
# Edge-type relevance categories for intent-based traversal
# ---------------------------------------------------------------------------

ARGUMENTATIVE_EDGES = {
    "argues_for",
    "argues_against",
    "refutes",
    "responds_to",
}
INTELLECTUAL_EDGES = {
    "influences",
    "influenced_by",
    "taught_by",
    "teaches",
}
DOCTRINAL_EDGES = {
    "holds_position",
    "endorses",
    "rejects",
}
SEMANTIC_EDGES = {
    "discusses",
    "discussed_in",
    "defines",
    "related_to",
    "contrasts_with",
}
AUTHORSHIP_EDGES = {"wrote", "authored_by"}
TEXTUAL_EDGES = {"preserves", "preserved_in", "contains", "part_of"}
HERMENEUTIC_EDGES = {"interprets", "interpreted_by"}

PRIMARY_EDGE_CATEGORIES = (
    ARGUMENTATIVE_EDGES
    | INTELLECTUAL_EDGES
    | DOCTRINAL_EDGES
    | SEMANTIC_EDGES
    | AUTHORSHIP_EDGES
    | TEXTUAL_EDGES
)
SECONDARY_EDGE_CATEGORIES = HERMENEUTIC_EDGES

# Node types that belong to the primary (ancient) layer
PRIMARY_NODE_TYPES = {
    "Person",
    "Concept",
    "Argument",
    "Work",
    "School",
    "Passage",
    "Debate",
    "Position",
    "Event",
    "Institution",
    "Text_Fragment",
    "Term",
    "Source_Collection",
    "Doctrine",
}
SECONDARY_NODE_TYPES = {"Modern_Interpretation"}

# Database schema prefix (used in SQL queries for passage lookups)
DB_SCHEMA = os.getenv("ELEUTHERIA_DB_SCHEMA", "free_will")


# ---------------------------------------------------------------------------
# Helper: parse JSON from LLM output (tolerant of markdown fences)
# ---------------------------------------------------------------------------


def _parse_json(text: str) -> Any:
    """Extract JSON from LLM output, stripping markdown code fences."""
    text = text.strip()
    # Remove ```json ... ``` wrappers
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        text = match.group(1).strip()
    return json.loads(text)


def _is_primary_node(node: dict[str, Any]) -> bool:
    """Check if a KG node belongs to the primary (ancient) layer."""
    if node.get("role") == "modern_scholar":
        return False
    return node.get("type") != "Modern_Interpretation"


# ---------------------------------------------------------------------------
# 1. ClassifyComplexity
# ---------------------------------------------------------------------------


@dataclass
class ClassifyComplexity(BaseNode[RAGState, Deps, ScholarlyAnswer]):
    """Classify query complexity and route to the appropriate sub-pipeline."""

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> DirectKGLookup | HybridRetrieve | DecomposeQuery:
        question = ctx.state.question
        logger.info("Classifying query complexity: %s", question[:80])

        prompt = CLASSIFY_PROMPT.format(question=question)
        classification_reason = ""
        try:
            raw = await ctx.deps.llm.generate(
                prompt,
                temperature=0.0,
                max_tokens=256,
            )
            result = _parse_json(raw)
            complexity = QueryComplexity(result.get("complexity", "medium"))
            classification_reason = result.get("reason", "")
        except Exception:
            logger.warning("Classification failed, defaulting to medium")
            complexity = QueryComplexity.MEDIUM

        ctx.state.complexity = complexity
        ctx.state.metadata["classification_reason"] = classification_reason
        logger.info("Query classified as: %s", complexity.value)

        if complexity == QueryComplexity.SIMPLE:
            return DirectKGLookup()
        elif complexity == QueryComplexity.COMPLEX:
            return DecomposeQuery()
        else:
            return HybridRetrieve()


# ---------------------------------------------------------------------------
# 2. DirectKGLookup (simple queries)
# ---------------------------------------------------------------------------


@dataclass
class DirectKGLookup(BaseNode[RAGState, Deps, ScholarlyAnswer]):
    """Fast path for simple factual lookups — semantic search + format."""

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> TreeReasoningRetrieve:
        question = ctx.state.question
        logger.info("Direct KG lookup for: %s", question[:80])

        # Semantic search
        embedding = await _get_embedding(ctx.deps, question)
        results = await ctx.deps.qdrant.search_nodes(embedding, limit=5)

        for hit in results:
            node_id = hit.get("id")
            if not node_id or node_id not in ctx.deps.node_lookup:
                continue
            node = ctx.deps.node_lookup[node_id]
            ctx.state.primary_evidence.append(
                Evidence(
                    id=node_id,
                    label=node.get("label", node_id),
                    type=node.get("type", ""),
                    layer=EvidenceLayer.PRIMARY
                    if _is_primary_node(node)
                    else EvidenceLayer.SECONDARY,
                    source=EvidenceSource.SEMANTIC_SEARCH,
                    description=node.get("description", ""),
                    score=hit.get("score", 0.0),
                    period=node.get("period"),
                    school=node.get("school"),
                    role=node.get("role"),
                )
            )
            ctx.state.seed_node_ids.append(node_id)
            ctx.state.context_node_ids.append(node_id)

        # Build simple context
        ctx.state.accumulated_context = _build_context_from_evidence(
            ctx.state.primary_evidence,
        )

        return TreeReasoningRetrieve()


# ---------------------------------------------------------------------------
# 3. HybridRetrieve (medium queries)
# ---------------------------------------------------------------------------


@dataclass
class HybridRetrieve(BaseNode[RAGState, Deps, ScholarlyAnswer]):
    """Medium-complexity path: semantic + hybrid search, optional HyDE,
    optional reranking, single-pass graph expansion, then tree reasoning."""

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> TreeReasoningRetrieve:
        question = ctx.state.question
        config = ctx.state.pipeline_config
        logger.info("Hybrid retrieval for: %s", question[:80])

        # 1. Run standard semantic search and (optionally) HyDE in parallel
        embedding_coro = _get_embedding(ctx.deps, question)
        if config.use_hyde and ctx.deps.hyde:
            standard_emb, hyde_results = await asyncio.gather(
                embedding_coro,
                ctx.deps.hyde.search_nodes(question, limit=10),
            )
        else:
            standard_emb = await embedding_coro
            hyde_results = []

        node_hits = await ctx.deps.qdrant.search_nodes(standard_emb, limit=10)

        # If HyDE returned results, RRF-fuse with standard hits
        if hyde_results and ctx.deps.hyde:
            node_hits = ctx.deps.hyde.rrf_fusion(node_hits, hyde_results, k=60)

        seed_ids: list[str] = []
        for hit in node_hits:
            node_id = hit.get("id")
            if not node_id or node_id not in ctx.deps.node_lookup:
                continue
            node = ctx.deps.node_lookup[node_id]
            layer = (
                EvidenceLayer.PRIMARY
                if _is_primary_node(node)
                else EvidenceLayer.SECONDARY
            )
            source = (
                EvidenceSource.HYDE_SEARCH
                if hit.get("_hyde")
                else EvidenceSource.SEMANTIC_SEARCH
            )
            evidence = Evidence(
                id=node_id,
                label=node.get("label", node_id),
                type=node.get("type", ""),
                layer=layer,
                source=source,
                description=node.get("description", ""),
                score=hit.get("score", 0.0),
                period=node.get("period"),
                school=node.get("school"),
                role=node.get("role"),
            )
            if layer == EvidenceLayer.PRIMARY:
                ctx.state.primary_evidence.append(evidence)
            else:
                ctx.state.secondary_evidence.append(evidence)
            seed_ids.append(node_id)

        ctx.state.seed_node_ids = seed_ids

        # 2. Graph expansion (weighted if available, else BFS)
        expanded_ids = _expand_graph(ctx.deps, seed_ids, depth=2)
        for nid in expanded_ids:
            if nid in ctx.deps.node_lookup and nid not in seed_ids:
                node = ctx.deps.node_lookup[nid]
                layer = (
                    EvidenceLayer.PRIMARY
                    if _is_primary_node(node)
                    else EvidenceLayer.SECONDARY
                )
                evidence = Evidence(
                    id=nid,
                    label=node.get("label", nid),
                    type=node.get("type", ""),
                    layer=layer,
                    source=EvidenceSource.GRAPH_TRAVERSAL,
                    description=node.get("description", ""),
                    period=node.get("period"),
                    school=node.get("school"),
                    role=node.get("role"),
                )
                if layer == EvidenceLayer.PRIMARY:
                    ctx.state.primary_evidence.append(evidence)
                else:
                    ctx.state.secondary_evidence.append(evidence)

        ctx.state.context_node_ids = list({e.id for e in ctx.state.all_evidence()})

        # 3. Fetch passages
        passages = await _fetch_passages(ctx.deps, ctx.state.context_node_ids)
        for p in passages:
            ctx.state.primary_evidence.append(
                Evidence(
                    id=str(p["passage_id"]),
                    label=f"{p['author']}, {p['title']} {p['canonical_ref']}",
                    type="passage",
                    layer=EvidenceLayer.PRIMARY,
                    source=EvidenceSource.PASSAGE_CITATION,
                    description=truncate_text(
                        p.get("text_content", ""), MAX_PASSAGE_DESCRIPTION
                    ),
                    passage_id=str(p["passage_id"]),
                    canonical_ref=p.get("canonical_ref"),
                    author=p.get("author"),
                    work_title=p.get("title"),
                    text_content=p.get("text_content"),
                    confidence=p.get("confidence"),
                )
            )
        ctx.state.passages_used = len(passages)

        # 4. Rerank if available
        if ctx.deps.reranker:
            all_evidence = ctx.state.primary_evidence + ctx.state.secondary_evidence
            reranked = await ctx.deps.reranker.rerank(question, all_evidence)
            # Separate back into primary/secondary
            ctx.state.primary_evidence = [
                e for e in reranked if e.layer == EvidenceLayer.PRIMARY
            ]
            ctx.state.secondary_evidence = [
                e for e in reranked if e.layer == EvidenceLayer.SECONDARY
            ]

        # 5. Build context
        ctx.state.accumulated_context = _build_hierarchical_context(ctx.state)

        return TreeReasoningRetrieve()


# ---------------------------------------------------------------------------
# 4. DecomposeQuery (complex queries — entry)
# ---------------------------------------------------------------------------


@dataclass
class DecomposeQuery(BaseNode[RAGState, Deps, ScholarlyAnswer]):
    """Decompose a complex multi-hop question into sub-queries."""

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> SearchPrimarySources:
        question = ctx.state.question
        logger.info("Decomposing complex query: %s", question[:80])

        prompt = DECOMPOSE_PROMPT.format(question=question)
        try:
            raw = await ctx.deps.llm.generate(
                prompt,
                temperature=0.0,
                max_tokens=512,
            )
            sub_queries = _parse_json(raw)
            if isinstance(sub_queries, list):
                ctx.state.sub_queries = [str(q) for q in sub_queries]
        except Exception:
            logger.warning("Decomposition failed, using original question")
            ctx.state.sub_queries = [question]

        if not ctx.state.sub_queries:
            ctx.state.sub_queries = [question]

        logger.info("Sub-queries: %s", ctx.state.sub_queries)
        return SearchPrimarySources()


# ---------------------------------------------------------------------------
# 5. SearchPrimarySources
# ---------------------------------------------------------------------------


@dataclass
class SearchPrimarySources(BaseNode[RAGState, Deps, ScholarlyAnswer]):
    """Retrieve primary ancient sources for all sub-queries.

    Uses semantic search on KG nodes, weighted graph traversal,
    and passage fetching.  Only follows primary-layer edges.
    """

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> EvaluateSufficiency:
        ctx.state.iteration += 1
        queries = ctx.state.sub_queries or [ctx.state.question]
        logger.info(
            "SearchPrimarySources iteration=%d queries=%d",
            ctx.state.iteration,
            len(queries),
        )

        existing_ids = ctx.state.primary_node_ids()

        for query in queries:
            # Semantic search
            embedding = await _get_embedding(ctx.deps, query)
            hits = await ctx.deps.qdrant.search_nodes(embedding, limit=10)

            seed_ids: list[str] = []
            for hit in hits:
                node_id = hit.get("id")
                if (
                    not node_id
                    or node_id not in ctx.deps.node_lookup
                    or node_id in existing_ids
                ):
                    continue
                node = ctx.deps.node_lookup[node_id]
                if not _is_primary_node(node):
                    continue
                ctx.state.primary_evidence.append(
                    Evidence(
                        id=node_id,
                        label=node.get("label", node_id),
                        type=node.get("type", ""),
                        layer=EvidenceLayer.PRIMARY,
                        source=EvidenceSource.SEMANTIC_SEARCH,
                        description=node.get("description", ""),
                        score=hit.get("score", 0.0),
                        period=node.get("period"),
                        school=node.get("school"),
                        role=node.get("role"),
                    )
                )
                seed_ids.append(node_id)
                existing_ids.add(node_id)

            ctx.state.seed_node_ids.extend(seed_ids)

            # Weighted graph expansion (primary edges only)
            if ctx.deps.traversal:
                expanded = ctx.deps.traversal.expand(
                    seed_ids=seed_ids,
                    edge_filter=PRIMARY_EDGE_CATEGORIES,
                    max_nodes=20,
                    score_threshold=0.1,
                )
            else:
                expanded = _expand_graph(ctx.deps, seed_ids, depth=2)

            for nid in expanded:
                if nid in existing_ids or nid not in ctx.deps.node_lookup:
                    continue
                node = ctx.deps.node_lookup[nid]
                if not _is_primary_node(node):
                    continue
                ctx.state.primary_evidence.append(
                    Evidence(
                        id=nid,
                        label=node.get("label", nid),
                        type=node.get("type", ""),
                        layer=EvidenceLayer.PRIMARY,
                        source=EvidenceSource.GRAPH_TRAVERSAL,
                        description=node.get("description", ""),
                        period=node.get("period"),
                        school=node.get("school"),
                        role=node.get("role"),
                    )
                )
                existing_ids.add(nid)

        # Fetch passages linked to primary evidence
        primary_ids = [e.id for e in ctx.state.primary_evidence if e.type != "passage"]
        passages = await _fetch_passages(ctx.deps, primary_ids)
        for p in passages:
            pid = str(p["passage_id"])
            if pid in existing_ids:
                continue
            ctx.state.primary_evidence.append(
                Evidence(
                    id=pid,
                    label=f"{p['author']}, {p['title']} {p['canonical_ref']}",
                    type="passage",
                    layer=EvidenceLayer.PRIMARY,
                    source=EvidenceSource.PASSAGE_CITATION,
                    description=truncate_text(
                        p.get("text_content", ""), MAX_PASSAGE_DESCRIPTION
                    ),
                    passage_id=pid,
                    canonical_ref=p.get("canonical_ref"),
                    author=p.get("author"),
                    work_title=p.get("title"),
                    text_content=p.get("text_content"),
                    confidence=p.get("confidence"),
                )
            )
            existing_ids.add(pid)

        ctx.state.passages_used = sum(
            1 for e in ctx.state.primary_evidence if e.type == "passage"
        )
        ctx.state.context_node_ids = list(existing_ids)

        # Rerank primary evidence if reranker available
        if ctx.deps.reranker:
            ctx.state.primary_evidence = await ctx.deps.reranker.rerank(
                ctx.state.question,
                ctx.state.primary_evidence,
            )

        return EvaluateSufficiency()


# ---------------------------------------------------------------------------
# 6. EvaluateSufficiency
# ---------------------------------------------------------------------------


@dataclass
class EvaluateSufficiency(BaseNode[RAGState, Deps, ScholarlyAnswer]):
    """Check if primary evidence is sufficient to answer the question.

    If not, refine queries and loop back to SearchPrimarySources
    (up to max_iterations).
    """

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> SearchPrimarySources | TreeReasoningRetrieve:
        state = ctx.state
        primary_count = len(state.primary_evidence)
        passage_count = sum(1 for e in state.primary_evidence if e.type == "passage")
        node_summary = ", ".join(
            e.label for e in state.primary_evidence[:8] if e.type != "passage"
        )

        logger.info(
            "EvaluateSufficiency: primary=%d passages=%d iter=%d/%d",
            primary_count,
            passage_count,
            state.iteration,
            state.max_iterations,
        )

        # Hard sufficiency: enough iterations → proceed
        if state.iteration >= state.max_iterations:
            logger.info("Max iterations reached, proceeding to tree reasoning")
            return TreeReasoningRetrieve()

        # Quick heuristic: if we have passages, likely sufficient
        if passage_count >= 3 and primary_count >= 5:
            state.sufficiency_score = 0.8
            return TreeReasoningRetrieve()

        # Ask LLM for sufficiency assessment
        prompt = SUFFICIENCY_PROMPT.format(
            question=state.question,
            primary_count=primary_count,
            passage_count=passage_count,
            node_summary=node_summary or "(none)",
        )
        try:
            raw = await ctx.deps.llm.generate(
                prompt,
                temperature=0.0,
                max_tokens=256,
            )
            result = _parse_json(raw)
            state.sufficiency_score = float(result.get("score", 0.5))
            sufficient = result.get("sufficient", False)

            if sufficient or state.sufficiency_score >= 0.6:
                logger.info("Evidence sufficient (score=%.2f)", state.sufficiency_score)
                return TreeReasoningRetrieve()

            # Refine sub-queries and loop back
            refinement = result.get("refinement", "")
            if refinement:
                state.sub_queries = [refinement]
            logger.info(
                "Evidence insufficient (score=%.2f), refining",
                state.sufficiency_score,
            )
            return SearchPrimarySources()

        except Exception:
            logger.warning("Sufficiency check failed, proceeding")
            return TreeReasoningRetrieve()


# ---------------------------------------------------------------------------
# 7. SearchSecondarySources
# ---------------------------------------------------------------------------


@dataclass
class SearchSecondarySources(BaseNode[RAGState, Deps, ScholarlyAnswer]):
    """Retrieve modern scholarly interpretations linked to primary evidence.

    Follows hermeneutic edges and looks for Modern_Interpretation nodes.
    """

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> SynthesizeWithHierarchy:
        logger.info("Searching secondary (modern) sources")
        primary_ids = [e.id for e in ctx.state.primary_evidence if e.type != "passage"]
        existing_ids = ctx.state.all_node_ids()

        for node_id in primary_ids[:20]:
            # Follow hermeneutic edges from primary nodes
            for edge in ctx.deps.outgoing_edges.get(node_id, []):
                if edge.get("relation") not in HERMENEUTIC_EDGES | {"interpreted_by"}:
                    continue
                target = edge["target"]
                if target in existing_ids or target not in ctx.deps.node_lookup:
                    continue
                node = ctx.deps.node_lookup[target]
                ctx.state.secondary_evidence.append(
                    Evidence(
                        id=target,
                        label=node.get("label", target),
                        type=node.get("type", ""),
                        layer=EvidenceLayer.SECONDARY,
                        source=EvidenceSource.GRAPH_TRAVERSAL,
                        description=node.get("description", ""),
                        period=node.get("period"),
                        school=node.get("school"),
                        role=node.get("role"),
                    )
                )
                existing_ids.add(target)

            for edge in ctx.deps.incoming_edges.get(node_id, []):
                if edge.get("relation") not in HERMENEUTIC_EDGES | {"interprets"}:
                    continue
                source = edge["source"]
                if source in existing_ids or source not in ctx.deps.node_lookup:
                    continue
                node = ctx.deps.node_lookup[source]
                ctx.state.secondary_evidence.append(
                    Evidence(
                        id=source,
                        label=node.get("label", source),
                        type=node.get("type", ""),
                        layer=EvidenceLayer.SECONDARY,
                        source=EvidenceSource.GRAPH_TRAVERSAL,
                        description=node.get("description", ""),
                        period=node.get("period"),
                        school=node.get("school"),
                        role=node.get("role"),
                    )
                )
                existing_ids.add(source)

        # Also look for Modern_Interpretation nodes via semantic search
        embedding = await _get_embedding(ctx.deps, ctx.state.question)
        hits = await ctx.deps.qdrant.search_nodes(embedding, limit=5)
        for hit in hits:
            nid = hit.get("id")
            if not nid or nid in existing_ids or nid not in ctx.deps.node_lookup:
                continue
            node = ctx.deps.node_lookup[nid]
            if (
                node.get("type") != "Modern_Interpretation"
                and node.get("role") != "modern_scholar"
            ):
                continue
            ctx.state.secondary_evidence.append(
                Evidence(
                    id=nid,
                    label=node.get("label", nid),
                    type=node.get("type", ""),
                    layer=EvidenceLayer.SECONDARY,
                    source=EvidenceSource.SEMANTIC_SEARCH,
                    description=node.get("description", ""),
                    score=hit.get("score", 0.0),
                    period=node.get("period"),
                    school=node.get("school"),
                    role=node.get("role"),
                )
            )
            existing_ids.add(nid)

        ctx.state.context_node_ids = list(existing_ids)

        logger.info(
            "Secondary search found %d modern sources",
            len(ctx.state.secondary_evidence),
        )

        return SynthesizeWithHierarchy()


# ---------------------------------------------------------------------------
# 8. Synthesize (medium-path single-pass synthesis)
# ---------------------------------------------------------------------------


@dataclass
class Synthesize(BaseNode[RAGState, Deps, ScholarlyAnswer]):
    """Single-pass LLM synthesis for simple/medium queries."""

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> VerifyCitations:
        question = ctx.state.question
        context = ctx.state.accumulated_context

        if not context:
            context = _build_context_from_evidence(
                ctx.state.primary_evidence + ctx.state.secondary_evidence,
            )
            ctx.state.accumulated_context = context

        prompt = f"""\
Based on the following knowledge graph context about ancient philosophy, \
answer this question: {question}

## Knowledge Graph Context
{context}

INSTRUCTIONS:
1. Provide a scholarly answer grounded EXCLUSIVELY in the sources above.
2. Cite sources using [1], [2] for nodes and [P1], [P2] for passages.
3. When citing passages that contain Greek or Latin text, QUOTE the original text \
exactly as provided. NEVER generate or approximate Greek/Latin text.
4. Include CTS URNs from passage metadata when available.
5. If insufficient source material is available, state this explicitly."""

        answer = await ctx.deps.llm.generate(
            prompt, system_prompt=SYSTEM_PROMPT, max_tokens=4096
        )
        ctx.state.raw_answer = answer

        return VerifyCitations()


# ---------------------------------------------------------------------------
# 9. SynthesizeWithHierarchy (complex-path layered synthesis)
# ---------------------------------------------------------------------------


@dataclass
class SynthesizeWithHierarchy(BaseNode[RAGState, Deps, ScholarlyAnswer]):
    """Hierarchical synthesis with primary/secondary source distinction."""

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> VerifyCitations:
        context = _build_hierarchical_context(ctx.state)
        ctx.state.accumulated_context = context

        prompt = HIERARCHICAL_SYNTHESIS_PROMPT.format(
            question=ctx.state.question,
            context=context,
        )

        answer = await ctx.deps.llm.generate(
            prompt,
            system_prompt=SYSTEM_PROMPT,
            max_tokens=4096,
        )
        ctx.state.raw_answer = answer

        return VerifyCitations()


# ---------------------------------------------------------------------------
# 10. VerifyCitations
# ---------------------------------------------------------------------------


@dataclass
class VerifyCitations(BaseNode[RAGState, Deps, ScholarlyAnswer]):
    """Extract citations from the answer and verify against actual DB content.

    If a CitationVerifier is available, runs the full verification loop.
    Otherwise, falls back to positional regex extraction (legacy behaviour).

    Fail-closed: any verification error marks citations as verified=False
    (never silently marks unverified citations as verified).
    """

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> SelfRAGEvaluate:
        state = ctx.state
        answer = state.raw_answer

        # Extract citations using regex
        all_evidence = state.primary_evidence + state.secondary_evidence
        node_evidence = [e for e in all_evidence if e.type != "passage"]
        passage_evidence = [e for e in all_evidence if e.type == "passage"]

        citations: list[Citation] = []

        # [1], [2], ... → map to node evidence by position
        node_refs = re.findall(r"\[(\d+)\]", answer)
        for ref in sorted(set(node_refs), key=int):
            ref_num = int(ref)
            if ref_num <= len(node_evidence):
                ev = node_evidence[ref_num - 1]
                citations.append(
                    Citation(
                        ref=ref,
                        type="node",
                        id=ev.id,
                        label=ev.label,
                        layer=ev.layer,
                        confidence=ev.confidence,
                        verified=False,  # fail-closed: default unverified
                    )
                )

        # [P1], [P2], ... → map to passage evidence by position
        passage_refs = re.findall(r"\[P(\d+)\]", answer)
        for ref in sorted(set(passage_refs), key=int):
            ref_num = int(ref)
            if ref_num <= len(passage_evidence):
                ev = passage_evidence[ref_num - 1]
                citations.append(
                    Citation(
                        ref=f"P{ref}",
                        type="passage",
                        id=ev.id,
                        label=ev.label,
                        layer=ev.layer,
                        confidence=ev.confidence,
                        verified=False,  # fail-closed: default unverified
                    )
                )

        # Full verification if verifier is available — fail-closed on error
        if ctx.deps.verifier:
            try:
                citations = await ctx.deps.verifier.verify_citations(
                    answer=answer,
                    citations=citations,
                    evidence=all_evidence,
                )
            except Exception:
                logger.warning("Citation verification failed — marking all unverified")
                for c in citations:
                    c.verified = False

        state.citations = citations

        return SelfRAGEvaluate()


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


async def _get_embedding(_deps: Deps, text: str) -> list[float]:
    """Get embedding via Gemini embedding API.

    Runs the synchronous ``genai.embed_content`` in a thread pool
    to avoid blocking the event loop.
    """
    import google.generativeai as genai

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY required for embeddings")

    genai.configure(api_key=api_key)

    def _embed() -> list[float]:
        result = genai.embed_content(
            model="models/gemini-embedding-001",
            content=text,
        )
        return result["embedding"]

    return await asyncio.to_thread(_embed)


def _expand_graph(
    deps: Deps,
    seed_ids: list[str],
    depth: int = 2,
) -> set[str]:
    """Fallback BFS expansion (when WeightedTraversal is unavailable)."""
    from collections import deque

    visited = set(seed_ids)
    queue = deque([(nid, 0) for nid in seed_ids])

    while queue:
        node_id, d = queue.popleft()
        if d >= depth:
            continue
        for edge in deps.outgoing_edges.get(node_id, []):
            target = edge["target"]
            if target not in visited and target in deps.node_lookup:
                visited.add(target)
                queue.append((target, d + 1))
        for edge in deps.incoming_edges.get(node_id, []):
            source = edge["source"]
            if source not in visited and source in deps.node_lookup:
                visited.add(source)
                queue.append((source, d + 1))

    return visited


async def _fetch_passages(
    deps: Deps,
    node_ids: list[str],
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Fetch passages linked to nodes via passage_citations table."""
    if not node_ids:
        return []

    placeholders = ", ".join(f"${i + 1}" for i in range(len(node_ids)))
    passages: list[dict[str, Any]] = await deps.db.fetch(
        f"""
        SELECT DISTINCT
            p.passage_id,
            p.text_content,
            p.canonical_ref,
            w.title,
            w.author,
            pc.confidence
        FROM {DB_SCHEMA}.passage_citations pc
        JOIN {DB_SCHEMA}.passages p ON pc.passage_id = p.passage_id
        JOIN {DB_SCHEMA}.ancient_works w ON p.work_id = w.work_id
        WHERE pc.kg_node_id IN ({placeholders})
        ORDER BY pc.confidence DESC
        LIMIT {limit}
        """,
        *node_ids,
    )
    return passages


def _build_context_from_evidence(evidence: list[Evidence]) -> str:
    """Build a plain context string from evidence items."""
    parts: list[str] = []
    node_idx = 0
    passage_idx = 0

    for ev in evidence:
        if ev.type == "passage":
            passage_idx += 1
            text = ev.text_content or ev.description
            ref_parts = [f"[P{passage_idx}] {ev.label}"]
            if ev.canonical_ref:
                ref_parts.append(f"(ref: {ev.canonical_ref})")
            if ev.cts_urn:
                ref_parts.append(f"[{ev.cts_urn}]")
            header = " ".join(ref_parts)
            parts.append(
                f'{header}:\n"{truncate_text(text, MAX_PASSAGE_IN_CONTEXT)}"'
            )
        else:
            node_idx += 1
            header = f"[{node_idx}] **{ev.label}** ({ev.type})"
            extras = []
            if ev.period:
                extras.append(f"Period: {ev.period}")
            if ev.school:
                extras.append(f"School: {ev.school}")
            if ev.description:
                extras.append(
                    truncate_text(ev.description, MAX_NODE_DESC_IN_CONTEXT)
                )
            parts.append(header + "\n" + "\n".join(extras))

    return "\n\n".join(parts)


def _build_hierarchical_context(state: RAGState) -> str:
    """Build context with clear primary/secondary layering."""
    sections: list[str] = []

    # Primary Ancient Sources (sorted by relevance score to mitigate "lost in the middle")
    primary_nodes = sorted(
        [e for e in state.primary_evidence if e.type != "passage"],
        key=lambda e: e.score,
        reverse=True,
    )
    primary_passages = sorted(
        [e for e in state.primary_evidence if e.type == "passage"],
        key=lambda e: e.confidence or e.score,
        reverse=True,
    )

    if primary_nodes or primary_passages:
        section = "## Primary Ancient Sources (authoritative)\n"
        for idx, ev in enumerate(primary_nodes, 1):
            header = f"[{idx}] **{ev.label}** ({ev.type})"
            extras = []
            if ev.period:
                extras.append(f"Period: {ev.period}")
            if ev.school:
                extras.append(f"School: {ev.school}")
            if ev.description:
                extras.append(
                    truncate_text(ev.description, MAX_NODE_DESC_IN_CONTEXT)
                )
            section += "\n" + header + "\n" + "\n".join(extras) + "\n"

        for i, ev in enumerate(primary_passages, 1):
            text = ev.text_content or ev.description
            ref_parts = [f"[P{i}] {ev.label}"]
            if ev.canonical_ref:
                ref_parts.append(f"(ref: {ev.canonical_ref})")
            if ev.cts_urn:
                ref_parts.append(f"[{ev.cts_urn}]")
            header = " ".join(ref_parts)
            section += (
                f'\n{header}:\n'
                f'"{truncate_text(text, MAX_PASSAGE_IN_CONTEXT)}"\n'
            )
        sections.append(section)

    # Secondary Modern Scholarship
    if state.secondary_evidence:
        section = "## Modern Scholarly Interpretations (commentary)\n"
        for ev in state.secondary_evidence:
            header = f"**{ev.label}** ({ev.type})"
            extras = []
            if ev.role:
                extras.append(f"Role: {ev.role}")
            if ev.description:
                extras.append(
                    truncate_text(ev.description, MAX_SECONDARY_DESC_IN_CONTEXT)
                )
            section += "\n" + header + "\n" + "\n".join(extras) + "\n"
        sections.append(section)

    return "\n\n".join(sections)


# ===========================================================================
# NEW NODES (SOTA Agentic Pipeline v2)
# ===========================================================================

# ---------------------------------------------------------------------------
# Prompts for new nodes
# ---------------------------------------------------------------------------

CLASSIFY_QUERY_TYPE_PROMPT = """\
Classify the following scholarly question about ancient philosophy \
into one of five query types.

Classification criteria:
- **specific_entity**: Single-entity factual lookup (who, what, when). \
  E.g. "Who was Chrysippus?" or "What school did Epictetus belong to?"
- **global_abstract**: Requires combining information about one broad topic \
  from multiple sources. E.g. "What did the Stoics believe about fate?"
- **multi_hop**: Requires tracing chains of influence, transmission, or \
  argument across multiple philosophers or time periods. \
  E.g. "How did Stoic fate evolve from Chrysippus to Epictetus?"
- **comparative**: Requires explicit comparison between schools, philosophers, \
  or positions. E.g. "How did Stoics and Epicureans differ on free will?"
- **temporal**: Temporal traces, dialectical analysis, or questions that don't \
  fit the above categories.

Return ONLY valid JSON:
{{"query_type": "<one of the five values>", "confidence": <float 0-1>, "reason": "<brief explanation>"}}

Question: {question}"""

EXPAND_QUERY_PROMPT = """\
You are an expert classicist. Analyze this research question about \
ancient philosophy and identify relevant terms.

Question: "{question}"

Return ONLY valid JSON with these fields:
- greek_terms: list of objects with "greek", "transliteration", "translation"
- latin_terms: list of objects with "latin", "translation"
- philosophers: list of philosopher names (strings)
- concepts: list of philosophical concept names (strings)
- schools: list of philosophical school names (strings)
- periods: list of historical period names (strings)

Keep all lists concise (2-5 items max). Return only terms directly relevant to the question."""

TREE_REASONING_PROMPT = """\
You are a scholar of ancient philosophy navigating document indices \
to find passages that answer a specific question.

QUESTION: {question}

DOCUMENT INDICES:
{tree_indices_json}

For each document, examine the section summaries and reason about \
which sections are most likely to contain information that answers the question.

Return ONLY valid JSON:
{{"selected_nodes": [{{"work_id": "...", "node_id": "...", "reason": "...", "priority": 1}}], \
"reasoning": "..."}}

Priority: 1=must-read, 2=important, 3=supplementary."""

CRAG_VALIDATE_PROMPT = """\
You are a scholarly validation system for ancient philosophy research.

TASK: Evaluate if the retrieved context can adequately answer the research question.

RESEARCH QUESTION: "{question}"

RETRIEVED CONTEXT:
\"\"\"{context}\"\"\"

Return ONLY valid JSON:
{{"relevance": <0-100>, "completeness": <0-100>, "confidence": <0-100>, \
"missing": ["..."], "suggestions": ["search query 1", ...]}}"""

SELF_RAG_EVALUATE_PROMPT = """\
You are a scholarly quality evaluator for ancient philosophy research.

TASK: Evaluate this answer's quality and reliability.

RESEARCH QUESTION: "{question}"

GENERATED ANSWER:
\"\"\"{answer}\"\"\"

SOURCES CITED: {source_count} sources

Evaluate on 0-100 scale (relevance, grounding, completeness, confidence).
Pay special attention to GROUNDING — any claim not supported by cited evidence \
should lower the grounding score significantly.

Return ONLY valid JSON:
{{"relevance": <0-100>, "grounding": <0-100>, "completeness": <0-100>, \
"confidence": <0-100>, "caveats": ["..."], "improvements": ["..."]}}"""

REFINE_SYNTHESIS_PROMPT = """\
You are refining a scholarly answer based on quality feedback.

ORIGINAL QUESTION: "{question}"

ORIGINAL ANSWER:
\"\"\"{raw_answer}\"\"\"

QUALITY ISSUES:
- Caveats: {caveats}
- Improvements: {improvements}
- Grounding score: {grounding}/100
- Completeness score: {completeness}/100

AVAILABLE CONTEXT:
\"\"\"{context}\"\"\"

TASK: Rewrite the answer to address the identified issues. \
If a claim cannot be grounded in the evidence, remove it or state \
"The available sources do not address this point." \
Maintain scholarly register.

Write the improved answer directly."""

# Keyword heuristic for query classification fallback
_KEYWORD_PATTERNS = {
    "compare": "comparative",
    "differ": "comparative",
    " vs ": "comparative",
    "versus": "comparative",
    "trace": "multi_hop",
    "influence": "multi_hop",
    "through": "multi_hop",
    "evolution": "multi_hop",
    "who was": "specific_entity",
    "what is": "specific_entity",
    "define": "specific_entity",
    "when did": "specific_entity",
    "what school": "specific_entity",
}

# Static fallback expansion dictionary (matches TypeScript COMMON_GREEK_TERMS)
_STATIC_GREEK_TERMS = {
    "free will": {
        "greek": "τὸ ἐφ' ἡμῖν",
        "transliteration": "to eph' hēmin",
        "translation": "what is in our power",
    },
    "in our power": {
        "greek": "τὸ ἐφ' ἡμῖν",
        "transliteration": "to eph' hēmin",
        "translation": "what is in our power",
    },
    "self-determination": {
        "greek": "αὐτεξούσιον",
        "transliteration": "autexousion",
        "translation": "self-determination",
    },
    "fate": {
        "greek": "εἱμαρμένη",
        "transliteration": "heimarmenē",
        "translation": "fate/destiny",
    },
    "destiny": {
        "greek": "εἱμαρμένη",
        "transliteration": "heimarmenē",
        "translation": "fate/destiny",
    },
    "assent": {
        "greek": "συγκατάθεσις",
        "transliteration": "synkatathesis",
        "translation": "assent",
    },
    "moral choice": {
        "greek": "προαίρεσις",
        "transliteration": "prohairesis",
        "translation": "moral choice",
    },
    "swerve": {
        "greek": "παρέγκλισις",
        "transliteration": "parenklisis",
        "translation": "swerve/clinamen",
    },
    "necessity": {
        "greek": "ἀνάγκη",
        "transliteration": "anankē",
        "translation": "necessity",
    },
    "possibility": {
        "greek": "δυνατόν",
        "transliteration": "dynaton",
        "translation": "possibility",
    },
    "cause": {"greek": "αἰτία", "transliteration": "aitia", "translation": "cause"},
    "impression": {
        "greek": "φαντασία",
        "transliteration": "phantasia",
        "translation": "impression/appearance",
    },
}

_STATIC_PHILOSOPHERS = [
    "Chrysippus",
    "Epictetus",
    "Epicurus",
    "Aristotle",
    "Plato",
    "Alexander of Aphrodisias",
    "Cicero",
    "Seneca",
    "Marcus Aurelius",
    "Augustine",
    "Origen",
    "Cleanthes",
    "Carneades",
]


# ---------------------------------------------------------------------------
# 11. ClassifyQueryType (replaces ClassifyComplexity as the new entry point)
# ---------------------------------------------------------------------------


@dataclass
class ClassifyQueryType(BaseNode[RAGState, Deps, ScholarlyAnswer]):
    """Classify query into 5-type taxonomy and configure pipeline."""

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> ExpandQuery:
        from eleutheria_graphrag.agents.pipeline_config import (
            QueryType,
            get_pipeline_config,
            query_type_to_complexity,
        )

        question = ctx.state.question
        logger.info("Classifying query type: %s", question[:80])

        query_type = QueryType.GLOBAL_ABSTRACT  # default
        confidence = 0.5
        reason = ""

        # Try LLM classification
        prompt = CLASSIFY_QUERY_TYPE_PROMPT.format(question=question)
        try:
            raw = await ctx.deps.llm.generate(prompt, temperature=0.0, max_tokens=256)
            result = _parse_json(raw)
            query_type = QueryType(result.get("query_type", "global_abstract"))
            confidence = float(result.get("confidence", 0.5))
            reason = result.get("reason", "")
        except Exception:
            logger.warning("LLM classification failed, using keyword heuristic")
            # Keyword fallback
            q_lower = question.lower()
            for keyword, qt_value in _KEYWORD_PATTERNS.items():
                if keyword in q_lower:
                    query_type = QueryType(qt_value)
                    break

        # Set state
        ctx.state.query_type = query_type
        ctx.state.pipeline_config = get_pipeline_config(query_type)
        ctx.state.complexity = query_type_to_complexity(query_type)
        ctx.state.metadata["query_type"] = query_type.value
        ctx.state.metadata["classification_confidence"] = confidence
        ctx.state.metadata["classification_reason"] = reason

        logger.info("Query type: %s (confidence=%.2f)", query_type.value, confidence)
        return ExpandQuery()


# ---------------------------------------------------------------------------
# 12. ExpandQuery
# ---------------------------------------------------------------------------


@dataclass
class ExpandQuery(BaseNode[RAGState, Deps, ScholarlyAnswer]):
    """Philological query expansion with Greek/Latin terms, then routing."""

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> DirectKGLookup | HybridRetrieve | DecomposeQuery:
        from eleutheria_graphrag.agents.pipeline_config import QueryType

        question = ctx.state.question
        config = ctx.state.pipeline_config
        query_type = ctx.state.query_type

        # --- Build expanded query ---
        if config.use_expansion:
            expansion = await self._expand(ctx.deps.llm, question)
            ctx.state.expansion_terms = expansion
            ctx.state.expanded_query = self._build_expanded_query(question, expansion)
            logger.info("Expanded query: %s", ctx.state.expanded_query[:120])
        else:
            ctx.state.expanded_query = question

        # --- Route based on query type ---
        if query_type == QueryType.SPECIFIC_ENTITY:
            return DirectKGLookup()
        elif query_type in (QueryType.MULTI_HOP, QueryType.TEMPORAL):
            return DecomposeQuery()
        else:
            # GLOBAL_ABSTRACT, COMPARATIVE
            return HybridRetrieve()

    async def _expand(self, llm: Any, question: str) -> Any:
        """Try LLM expansion, fall back to static dictionary."""
        from eleutheria_graphrag.agents.structured_models import (
            ExpansionTerms,
        )

        try:
            prompt = EXPAND_QUERY_PROMPT.format(question=question)
            raw = await llm.generate(prompt, temperature=0.0, max_tokens=1024)
            data = _parse_json(raw)
            return ExpansionTerms.model_validate(data)
        except Exception:
            logger.warning("LLM expansion failed, using static dictionary")
            return self._static_expand(question)

    @staticmethod
    def _static_expand(question: str) -> Any:
        """Fallback: match known Greek terms and philosopher names."""
        from eleutheria_graphrag.agents.structured_models import (
            ExpansionTerms,
            GreekTerm,
        )

        q_lower = question.lower()
        greek_terms = []
        for trigger, term in _STATIC_GREEK_TERMS.items():
            if trigger in q_lower:
                greek_terms.append(GreekTerm(**term))
        philosophers = [p for p in _STATIC_PHILOSOPHERS if p.lower() in q_lower]
        return ExpansionTerms(
            greek_terms=greek_terms[:5], philosophers=philosophers[:5]
        )

    @staticmethod
    def _build_expanded_query(question: str, expansion: Any) -> str:
        """Build expanded query string with transliterations."""
        extras = []
        for term in getattr(expansion, "greek_terms", [])[:3]:
            extras.append(term.transliteration)
        for p in getattr(expansion, "philosophers", [])[:3]:
            extras.append(p)
        if extras:
            return f"{question} ({', '.join(extras)})"
        return question


# ---------------------------------------------------------------------------
# 13. TreeReasoningRetrieve (PageIndex-inspired)
# ---------------------------------------------------------------------------


@dataclass
class TreeReasoningRetrieve(BaseNode[RAGState, Deps, ScholarlyAnswer]):
    """Navigate pre-built tree indices to extract high-precision passages."""

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> CRAGValidate:
        config = ctx.state.pipeline_config
        if not config.use_tree_reasoning or ctx.deps.tree_index is None:
            logger.info("TreeReasoningRetrieve: disabled or no service, passthrough")
            return CRAGValidate()

        # Extract unique work IDs from current evidence
        work_ids = list(
            {
                e.work_title
                for e in ctx.state.all_evidence()
                if e.work_title and e.type == "passage"
            }
        )
        if not work_ids:
            # Fall back to top node labels as work IDs
            work_ids = [
                e.id
                for e in sorted(
                    ctx.state.primary_evidence, key=lambda x: x.score, reverse=True
                )[:5]
                if e.type != "passage"
            ]

        # Load tree indices
        try:
            indices = await ctx.deps.tree_index.load_indices(work_ids[:5])
        except Exception:
            logger.warning("TreeReasoningRetrieve: failed to load indices")
            return CRAGValidate()

        if not indices:
            return CRAGValidate()

        # Build tree JSON for LLM navigation
        tree_json = truncate_json(
            [idx.model_dump() for idx in indices], MAX_TREE_JSON
        )

        # LLM navigates the tree
        prompt = TREE_REASONING_PROMPT.format(
            question=ctx.state.question,
            tree_indices_json=tree_json,
        )
        try:
            raw = await ctx.deps.llm.generate(prompt, temperature=0.0, max_tokens=1024)
            nav_data = _parse_json(raw)
            selected_nodes = nav_data.get("selected_nodes", [])
        except Exception:
            logger.warning("TreeReasoningRetrieve: LLM navigation failed")
            return CRAGValidate()

        # Extract passages for priority 1 and 2 nodes
        existing_passages = sum(
            1 for e in ctx.state.primary_evidence if e.type == "passage"
        )
        for sel in selected_nodes:
            priority = sel.get("priority", 3)
            if priority == 3 and existing_passages >= 10:
                continue
            work_id = sel.get("work_id", "")
            node_id = sel.get("node_id", "")
            matching_idx = next(
                (idx for idx in indices if idx.work_id == work_id), None
            )
            if not matching_idx:
                continue
            try:
                passages = await ctx.deps.tree_index.extract_passages(
                    matching_idx, [node_id]
                )
            except Exception:
                continue
            for p in passages:
                pid = str(p.get("passage_id", p.get("canonical_ref", "")))
                existing_ids = ctx.state.all_node_ids()
                if pid in existing_ids:
                    continue
                ctx.state.primary_evidence.append(
                    Evidence(
                        id=pid,
                        label=f"{p.get('author', '')}, {p.get('title', '')} {p.get('canonical_ref', '')}",
                        type="passage",
                        layer=EvidenceLayer.PRIMARY,
                        source=EvidenceSource.TREE_REASONING,
                        description=truncate_text(
                            p.get("text_content", ""), MAX_PASSAGE_DESCRIPTION
                        ),
                        passage_id=pid,
                        canonical_ref=p.get("canonical_ref"),
                        author=p.get("author"),
                        work_title=p.get("title"),
                        text_content=p.get("text_content"),
                    )
                )
                existing_passages += 1

        logger.info(
            "TreeReasoningRetrieve: added passages, total primary=%d",
            len(ctx.state.primary_evidence),
        )
        return CRAGValidate()


# ---------------------------------------------------------------------------
# 14. CRAGValidate
# ---------------------------------------------------------------------------


@dataclass
class CRAGValidate(BaseNode[RAGState, Deps, ScholarlyAnswer]):
    """Corrective RAG — validate retrieval quality, trigger secondary if needed."""

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> DualRerank:
        config = ctx.state.pipeline_config
        if not config.use_crag:
            logger.info("CRAGValidate: disabled, passthrough")
            return DualRerank()

        # Build context summary for CRAG evaluation
        all_ev = ctx.state.all_evidence()
        context = truncate_text(
            _build_context_from_evidence(all_ev[:20]), MAX_CRAG_CONTEXT
        )
        primary_count = len(
            [e for e in ctx.state.primary_evidence if e.type != "passage"]
        )

        prompt = CRAG_VALIDATE_PROMPT.format(
            question=ctx.state.question,
            context=context or "(no context retrieved)",
        )
        try:
            from eleutheria_graphrag.agents.structured_models import CRAGValidation

            raw = await ctx.deps.llm.generate(prompt, temperature=0.0, max_tokens=512)
            data = _parse_json(raw)
            crag = CRAGValidation.model_validate(data)
        except Exception:
            logger.warning("CRAGValidate: validation failed, proceeding")
            return DualRerank()

        ctx.state.crag_validation = crag
        logger.info(
            "CRAG: relevance=%d completeness=%d confidence=%d",
            crag.relevance,
            crag.completeness,
            crag.confidence,
        )

        # Evidence insufficiency gate
        if crag.confidence < 30 and primary_count < 3:
            ctx.state.insufficient_evidence = True
            ctx.state.metadata["insufficiency_reason"] = (
                f"CRAG confidence {crag.confidence}/100 with only "
                f"{primary_count} primary sources."
            )
            logger.warning("CRAGValidate: evidence insufficient gate triggered")
            return DualRerank()

        # Secondary retrieval if confidence < 60
        if crag.confidence < 60:
            logger.info("CRAGValidate: confidence low, running secondary retrieval")
            existing_ids = ctx.state.all_node_ids()
            search_queries = (crag.missing[:3] + crag.suggestions[:2])[:5]
            for sq in search_queries:
                if not sq:
                    continue
                try:
                    embedding = await _get_embedding(ctx.deps, sq)
                    hits = await ctx.deps.qdrant.search_nodes(embedding, limit=5)
                    for hit in hits:
                        nid = hit.get("id")
                        if not nid or nid in existing_ids:
                            continue
                        if nid not in ctx.deps.node_lookup:
                            continue
                        node = ctx.deps.node_lookup[nid]
                        ev = Evidence(
                            id=nid,
                            label=node.get("label", nid),
                            type=node.get("type", ""),
                            layer=EvidenceLayer.PRIMARY
                            if _is_primary_node(node)
                            else EvidenceLayer.SECONDARY,
                            source=EvidenceSource.CRAG_SECONDARY,
                            description=node.get("description", ""),
                            score=hit.get("score", 0.0) * 0.85,  # discount
                            period=node.get("period"),
                            school=node.get("school"),
                            role=node.get("role"),
                        )
                        if ev.layer == EvidenceLayer.PRIMARY:
                            ctx.state.primary_evidence.append(ev)
                        else:
                            ctx.state.secondary_evidence.append(ev)
                        existing_ids.add(nid)
                except Exception:
                    continue

        return DualRerank()


# ---------------------------------------------------------------------------
# 15. DualRerank
# ---------------------------------------------------------------------------


@dataclass
class DualRerank(BaseNode[RAGState, Deps, ScholarlyAnswer]):
    """Two-stage reranking: cross-encoder (existing) + LLM scholarly scoring."""

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> FetchPassagesAndLayer:
        config = ctx.state.pipeline_config
        if not config.use_reranking:
            logger.info("DualRerank: disabled, passthrough")
            return FetchPassagesAndLayer()

        question = ctx.state.question
        all_evidence = ctx.state.all_evidence()
        eligible = [e for e in all_evidence if len(e.description or e.label) >= 20]

        if not eligible:
            return FetchPassagesAndLayer()

        # Stage 1: cross-encoder (existing RerankerService)
        if ctx.deps.reranker:
            try:
                reranked = await ctx.deps.reranker.rerank(question, eligible, top_k=20)
            except Exception:
                reranked = eligible[:20]
        else:
            reranked = eligible[:20]

        # Stage 2: LLM scholarly reranking
        if ctx.deps.llm_reranker:
            try:
                reranked = await ctx.deps.llm_reranker.rerank(
                    question, reranked, top_k=15
                )
            except Exception:
                reranked = reranked[:15]
        else:
            reranked = reranked[:15]

        # Update state
        ctx.state.primary_evidence = [
            e for e in reranked if e.layer == EvidenceLayer.PRIMARY
        ]
        ctx.state.secondary_evidence = [
            e for e in reranked if e.layer == EvidenceLayer.SECONDARY
        ]

        logger.info(
            "DualRerank: primary=%d secondary=%d",
            len(ctx.state.primary_evidence),
            len(ctx.state.secondary_evidence),
        )
        return FetchPassagesAndLayer()


# ---------------------------------------------------------------------------
# 16. FetchPassagesAndLayer
# ---------------------------------------------------------------------------


@dataclass
class FetchPassagesAndLayer(BaseNode[RAGState, Deps, ScholarlyAnswer]):
    """Convergence point: fetch passages, layer evidence, route to synthesis."""

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> Synthesize | SearchSecondarySources:
        from eleutheria_graphrag.agents.pipeline_config import QueryType

        # Fetch passages for all non-passage node IDs
        node_ids = [e.id for e in ctx.state.all_evidence() if e.type != "passage"]
        passages = await _fetch_passages(ctx.deps, node_ids)
        existing_ids = ctx.state.all_node_ids()
        for p in passages:
            pid = str(p["passage_id"])
            if pid in existing_ids:
                continue
            ctx.state.primary_evidence.append(
                Evidence(
                    id=pid,
                    label=f"{p['author']}, {p['title']} {p['canonical_ref']}",
                    type="passage",
                    layer=EvidenceLayer.PRIMARY,
                    source=EvidenceSource.PASSAGE_CITATION,
                    description=truncate_text(
                        p.get("text_content", ""), MAX_PASSAGE_DESCRIPTION
                    ),
                    passage_id=pid,
                    canonical_ref=p.get("canonical_ref"),
                    author=p.get("author"),
                    work_title=p.get("title"),
                    text_content=p.get("text_content"),
                    confidence=p.get("confidence"),
                )
            )
            existing_ids.add(pid)

        ctx.state.passages_used = sum(
            1 for e in ctx.state.primary_evidence if e.type == "passage"
        )
        ctx.state.context_node_ids = list(ctx.state.all_node_ids())
        ctx.state.accumulated_context = _build_hierarchical_context(ctx.state)

        # Route by query type
        qt = ctx.state.query_type
        if qt in (QueryType.SPECIFIC_ENTITY, QueryType.GLOBAL_ABSTRACT):
            return Synthesize()
        return SearchSecondarySources()


# ---------------------------------------------------------------------------
# 17. SelfRAGEvaluate
# ---------------------------------------------------------------------------


@dataclass
class SelfRAGEvaluate(BaseNode[RAGState, Deps, ScholarlyAnswer]):
    """Post-generation quality evaluation with refinement trigger."""

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> End[ScholarlyAnswer] | RefineSynthesis:
        config = ctx.state.pipeline_config
        state = ctx.state

        # Build final answer
        def _make_answer() -> ScholarlyAnswer:
            return ScholarlyAnswer(
                answer=state.raw_answer,
                question=state.question,
                complexity=state.complexity,
                query_type=state.query_type,
                citations=state.citations,
                seed_nodes=state.seed_node_ids,
                context_nodes=state.context_node_ids,
                passages_used=state.passages_used,
                iterations=state.iteration or 1,
                sub_queries=state.sub_queries,
                quality_badge=state.quality_badge,
                self_rag_evaluation=state.self_rag_evaluation,
                crag_validation=state.crag_validation,
                insufficient_evidence=state.insufficient_evidence,
                metadata=state.metadata,
            )

        if not config.use_self_rag:
            return End(_make_answer())

        # Evaluate answer quality
        source_count = len(state.citations)
        prompt = SELF_RAG_EVALUATE_PROMPT.format(
            question=state.question,
            answer=truncate_text(state.raw_answer, MAX_ANSWER_FOR_EVAL),
            source_count=source_count,
        )
        try:
            from eleutheria_graphrag.agents.structured_models import SelfRAGEvaluation

            raw = await ctx.deps.llm.generate(prompt, temperature=0.0, max_tokens=512)
            data = _parse_json(raw)
            evaluation = SelfRAGEvaluation.model_validate(data)
        except Exception:
            logger.warning("SelfRAGEvaluate: evaluation failed, returning answer")
            return End(_make_answer())

        state.self_rag_evaluation = evaluation

        # Assign quality badge
        if evaluation.confidence >= 80:
            state.quality_badge = "High"
        elif evaluation.confidence >= 60:
            state.quality_badge = "Medium"
        else:
            state.quality_badge = "Low"

        logger.info(
            "SelfRAG: confidence=%d badge=%s",
            evaluation.confidence,
            state.quality_badge,
        )

        # Decide: refine or finalize
        if (
            evaluation.confidence >= 60
            or state.self_rag_iterations >= state.max_self_rag_iterations
        ):
            return End(_make_answer())

        return RefineSynthesis()


# ---------------------------------------------------------------------------
# 18. RefineSynthesis
# ---------------------------------------------------------------------------


@dataclass
class RefineSynthesis(BaseNode[RAGState, Deps, ScholarlyAnswer]):
    """Re-synthesize answer incorporating Self-RAG feedback."""

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> VerifyCitations:
        state = ctx.state
        state.self_rag_iterations += 1

        evaluation = state.self_rag_evaluation
        caveats = getattr(evaluation, "caveats", []) if evaluation else []
        improvements = getattr(evaluation, "improvements", []) if evaluation else []
        grounding = getattr(evaluation, "grounding", 0) if evaluation else 0
        completeness = getattr(evaluation, "completeness", 0) if evaluation else 0

        prompt = REFINE_SYNTHESIS_PROMPT.format(
            question=state.question,
            raw_answer=truncate_text(state.raw_answer, MAX_ANSWER_FOR_EVAL),
            caveats=caveats,
            improvements=improvements,
            grounding=grounding,
            completeness=completeness,
            context=truncate_text(
                state.accumulated_context, MAX_CONTEXT_FOR_REFINE
            ),
        )

        try:
            refined = await ctx.deps.llm.generate(
                prompt,
                system_prompt=SYSTEM_PROMPT,
                max_tokens=4096,
            )
            state.raw_answer = refined
        except Exception:
            logger.warning(
                "RefineSynthesis: generation failed, keeping original answer"
            )

        logger.info("RefineSynthesis: iteration=%d", state.self_rag_iterations)
        return VerifyCitations()
