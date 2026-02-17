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
# System prompts
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are a scholarly assistant specializing in ancient philosophy, \
particularly debates about free will, fate, and moral responsibility \
in Greco-Roman thought.

Guidelines:
- Ground your answers in the provided context from the knowledge graph
- Cite specific ancient sources when available using [1], [2] notation
- For passages, use [P1], [P2] notation
- Distinguish between ancient primary sources and modern scholarly interpretations
- Use proper Greek/Latin terminology with transliteration when appropriate
- Acknowledge scholarly debates and different interpretations
- Be precise about historical periods and philosophical schools

Important: Only use information from the provided context. If the context \
doesn't contain enough information to answer, say so clearly."""

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

INSTRUCTION: Ground your answer in primary ancient sources first. \
Secondary scholarship provides interpretive context but is not authoritative \
for what the ancient authors actually said. Cite sources using [1], [2] for \
knowledge graph nodes and [P1], [P2] for passages."""


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
    ) -> Synthesize:
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

        return Synthesize()


# ---------------------------------------------------------------------------
# 3. HybridRetrieve (medium queries)
# ---------------------------------------------------------------------------


@dataclass
class HybridRetrieve(BaseNode[RAGState, Deps, ScholarlyAnswer]):
    """Medium-complexity path: semantic + hybrid search, optional reranking,
    single-pass graph expansion, then synthesize."""

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> Synthesize:
        question = ctx.state.question
        logger.info("Hybrid retrieval for: %s", question[:80])

        # 1. Semantic search on KG nodes
        embedding = await _get_embedding(ctx.deps, question)
        node_hits = await ctx.deps.qdrant.search_nodes(embedding, limit=10)

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
            evidence = Evidence(
                id=node_id,
                label=node.get("label", node_id),
                type=node.get("type", ""),
                layer=layer,
                source=EvidenceSource.SEMANTIC_SEARCH,
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
                    description=p.get("text_content", "")[:800],
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

        return Synthesize()


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
                    description=p.get("text_content", "")[:800],
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
    ) -> SearchPrimarySources | SearchSecondarySources:
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
            logger.info("Max iterations reached, proceeding to secondary sources")
            return SearchSecondarySources()

        # Quick heuristic: if we have passages, likely sufficient
        if passage_count >= 3 and primary_count >= 5:
            state.sufficiency_score = 0.8
            return SearchSecondarySources()

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
                return SearchSecondarySources()

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
            return SearchSecondarySources()


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

Provide a scholarly answer with citations to the sources above \
using [1], [2] notation for nodes and [P1], [P2] for passages."""

        answer = await ctx.deps.llm.generate(prompt, system_prompt=SYSTEM_PROMPT)
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
    """

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> End[ScholarlyAnswer]:
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
                        verified=False,
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
                        verified=False,
                    )
                )

        # Full verification if verifier is available
        if ctx.deps.verifier:
            citations = await ctx.deps.verifier.verify_citations(
                answer=answer,
                citations=citations,
                evidence=all_evidence,
            )

        state.citations = citations

        return End(
            ScholarlyAnswer(
                answer=answer,
                question=state.question,
                complexity=state.complexity,
                citations=citations,
                seed_nodes=state.seed_node_ids,
                context_nodes=state.context_node_ids,
                passages_used=state.passages_used,
                iterations=state.iteration or 1,
                sub_queries=state.sub_queries,
                metadata=state.metadata,
            )
        )


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
            parts.append(f'[P{passage_idx}] {ev.label}:\n"{text[:600]}"')
        else:
            node_idx += 1
            header = f"[{node_idx}] **{ev.label}** ({ev.type})"
            extras = []
            if ev.period:
                extras.append(f"Period: {ev.period}")
            if ev.school:
                extras.append(f"School: {ev.school}")
            if ev.description:
                extras.append(ev.description[:500])
            parts.append(header + "\n" + "\n".join(extras))

    return "\n\n".join(parts)


def _build_hierarchical_context(state: RAGState) -> str:
    """Build context with clear primary/secondary layering."""
    sections: list[str] = []

    # Primary Ancient Sources
    primary_nodes = [e for e in state.primary_evidence if e.type != "passage"]
    primary_passages = [e for e in state.primary_evidence if e.type == "passage"]

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
                extras.append(ev.description[:500])
            section += "\n" + header + "\n" + "\n".join(extras) + "\n"

        for i, ev in enumerate(primary_passages, 1):
            text = ev.text_content or ev.description
            section += f'\n[P{i}] {ev.label}:\n"{text[:600]}"\n'
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
                extras.append(ev.description[:400])
            section += "\n" + header + "\n" + "\n".join(extras) + "\n"
        sections.append(section)

    return "\n\n".join(sections)
