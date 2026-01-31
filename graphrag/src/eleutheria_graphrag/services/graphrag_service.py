"""
GraphRAG Service - Graph-based Retrieval-Augmented Generation.

5-stage pipeline:
1. Semantic search (Qdrant) - find relevant starting nodes
2. Graph traversal - expand to connected nodes
3. Context building - aggregate descriptions + passages
4. LLM synthesis - generate answer
5. Citation extraction - track sources
"""

import logging
import re
from collections import deque
from collections.abc import AsyncIterator
from typing import Any

from eleutheria_graphrag.services.llm_service import LLMService, ModelProvider

logger = logging.getLogger(__name__)

# Academic system prompt for scholarly answers
SYSTEM_PROMPT = """You are a scholarly assistant specializing in ancient philosophy,
particularly debates about free will, fate, and moral responsibility in Greco-Roman thought.

Guidelines:
- Ground your answers in the provided context from the knowledge graph
- Cite specific ancient sources when available using [1], [2] notation
- Distinguish between ancient primary sources and modern scholarly interpretations
- Use proper Greek/Latin terminology with transliteration when appropriate
- Acknowledge scholarly debates and different interpretations
- Be precise about historical periods and philosophical schools

Important: Only use information from the provided context. If the context doesn't
contain enough information to answer, say so clearly."""


class GraphRAGService:
    """
    GraphRAG service combining semantic search, graph traversal, and LLM synthesis.

    Usage:
        graphrag = GraphRAGService(db_service, qdrant_service)
        await graphrag.load_kg()

        result = await graphrag.query("What did Stoics believe about fate?")
        print(result["answer"])
    """

    def __init__(
        self,
        db_service: Any,
        qdrant_service: Any,
        llm_service: LLMService | None = None,
    ) -> None:
        """
        Initialize GraphRAG service.

        Args:
            db_service: Database service (eleutheria_database.DatabaseService)
            qdrant_service: Qdrant service (eleutheria_kg.QdrantService)
            llm_service: Optional LLM service (creates default if not provided)
        """
        self.db = db_service
        self.qdrant = qdrant_service
        self.llm = llm_service or LLMService(preferred_provider=ModelProvider.KIMI)

        # Knowledge graph data
        self.kg_data: dict[str, Any] | None = None
        self.node_lookup: dict[str, dict[str, Any]] = {}
        self.outgoing_edges: dict[str, list[dict[str, Any]]] = {}
        self.incoming_edges: dict[str, list[dict[str, Any]]] = {}

        self._kg_loaded = False

    async def load_kg(self) -> None:
        """Load knowledge graph from database."""
        if self._kg_loaded:
            return

        logger.info("Loading knowledge graph from database...")

        # Load nodes
        nodes = await self.db.fetch("""
            SELECT
                node_id as id,
                label,
                type,
                description,
                period,
                school,
                role,
                metadata
            FROM free_will.kg_nodes
        """)

        # Load edges
        edges = await self.db.fetch("""
            SELECT
                source_id as source,
                target_id as target,
                relation,
                description,
                weight
            FROM free_will.kg_edges
        """)

        self.kg_data = {"nodes": nodes, "edges": edges}

        # Build lookup indices
        self.node_lookup = {node["id"]: node for node in nodes}

        for edge in edges:
            source = edge["source"]
            target = edge["target"]

            if source not in self.outgoing_edges:
                self.outgoing_edges[source] = []
            self.outgoing_edges[source].append(edge)

            if target not in self.incoming_edges:
                self.incoming_edges[target] = []
            self.incoming_edges[target].append(edge)

        self._kg_loaded = True
        logger.info(f"Loaded {len(nodes)} nodes and {len(edges)} edges")

    async def query(
        self,
        question: str,
        semantic_k: int = 10,
        graph_depth: int = 2,
        max_context_nodes: int = 30,
        include_passages: bool = True,
    ) -> dict[str, Any]:
        """
        Execute GraphRAG query pipeline.

        Args:
            question: User question
            semantic_k: Number of nodes from semantic search
            graph_depth: BFS traversal depth
            max_context_nodes: Maximum nodes in context
            include_passages: Whether to include ancient passages

        Returns:
            Dictionary with answer, citations, and metadata
        """
        if not self._kg_loaded:
            await self.load_kg()

        # Stage 1: Semantic search
        query_embedding = await self._get_embedding(question)
        seed_nodes = await self.qdrant.search_nodes(query_embedding, limit=semantic_k)
        seed_ids = [n["id"] for n in seed_nodes if n["id"] in self.node_lookup]

        logger.info(f"Semantic search found {len(seed_ids)} seed nodes")

        # Stage 2: Graph traversal (BFS)
        expanded_ids = self._bfs_expand(seed_ids, depth=graph_depth)
        logger.info(f"Graph traversal expanded to {len(expanded_ids)} nodes")

        # Limit to max context
        context_ids = list(expanded_ids)[:max_context_nodes]

        # Stage 3: Context building
        context = self._build_context(context_ids, seed_ids)

        # Add passages if requested
        passages = []
        if include_passages:
            passages = await self._fetch_relevant_passages(context_ids)
            if passages:
                context += "\n\n## Ancient Passages\n"
                for i, p in enumerate(passages[:10], 1):
                    context += f"\n[P{i}] {p['author']}, {p['title']} {p['canonical_ref']}:\n"
                    context += f'"{p["text_content"][:500]}..."\n'

        # Stage 4: LLM synthesis
        prompt = f"""Based on the following knowledge graph context about ancient philosophy,
answer this question: {question}

## Knowledge Graph Context
{context}

Provide a scholarly answer with citations to the sources above using [1], [2] notation."""

        answer = await self.llm.generate(prompt, system_prompt=SYSTEM_PROMPT)

        # Stage 5: Citation extraction
        citations = self._extract_citations(answer, context_ids, passages)

        return {
            "answer": answer,
            "question": question,
            "citations": citations,
            "seed_nodes": seed_ids,
            "context_nodes": context_ids,
            "passages_used": len(passages),
        }

    async def query_stream(
        self,
        question: str,
        semantic_k: int = 10,
        graph_depth: int = 2,
        max_context_nodes: int = 30,
    ) -> AsyncIterator[str]:
        """
        Execute GraphRAG query with streaming response.

        Yields text chunks as they're generated.
        """
        if not self._kg_loaded:
            await self.load_kg()

        # Stages 1-3 same as non-streaming
        query_embedding = await self._get_embedding(question)
        seed_nodes = await self.qdrant.search_nodes(query_embedding, limit=semantic_k)
        seed_ids = [n["id"] for n in seed_nodes if n["id"] in self.node_lookup]

        expanded_ids = self._bfs_expand(seed_ids, depth=graph_depth)
        context_ids = list(expanded_ids)[:max_context_nodes]
        context = self._build_context(context_ids, seed_ids)

        prompt = f"""Based on the following knowledge graph context about ancient philosophy,
answer this question: {question}

## Knowledge Graph Context
{context}

Provide a scholarly answer with citations to the sources above using [1], [2] notation."""

        # Stage 4: Streaming LLM synthesis
        async for chunk in self.llm.stream(prompt, system_prompt=SYSTEM_PROMPT):
            yield chunk

    def _bfs_expand(
        self,
        seed_ids: list[str],
        depth: int = 2,
    ) -> set[str]:
        """Expand seed nodes via BFS traversal."""
        visited = set(seed_ids)
        queue = deque([(node_id, 0) for node_id in seed_ids])

        while queue:
            node_id, current_depth = queue.popleft()

            if current_depth >= depth:
                continue

            # Outgoing edges
            for edge in self.outgoing_edges.get(node_id, []):
                target = edge["target"]
                if target not in visited and target in self.node_lookup:
                    visited.add(target)
                    queue.append((target, current_depth + 1))

            # Incoming edges
            for edge in self.incoming_edges.get(node_id, []):
                source = edge["source"]
                if source not in visited and source in self.node_lookup:
                    visited.add(source)
                    queue.append((source, current_depth + 1))

        return visited

    def _build_context(
        self,
        node_ids: list[str],
        seed_ids: list[str],
    ) -> str:
        """Build context string from nodes."""
        context_parts = []

        # Prioritize seed nodes
        for node_id in seed_ids:
            if node_id in self.node_lookup:
                node = self.node_lookup[node_id]
                context_parts.append(self._format_node(node, is_seed=True))

        # Add other nodes
        for node_id in node_ids:
            if node_id not in seed_ids and node_id in self.node_lookup:
                node = self.node_lookup[node_id]
                context_parts.append(self._format_node(node, is_seed=False))

        return "\n\n".join(context_parts)

    def _format_node(self, node: dict[str, Any], is_seed: bool = False) -> str:
        """Format a node for context."""
        marker = "[SEED] " if is_seed else ""
        parts = [f"{marker}**{node.get('label', node['id'])}** ({node.get('type', 'Unknown')})"]

        if node.get("period"):
            parts.append(f"Period: {node['period']}")
        if node.get("school"):
            parts.append(f"School: {node['school']}")
        if node.get("description"):
            parts.append(node["description"][:500])

        return "\n".join(parts)

    async def _fetch_relevant_passages(
        self,
        node_ids: list[str],
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Fetch passages linked to context nodes."""
        if not node_ids:
            return []

        # Get passages via citation links
        placeholders = ", ".join(f"${i+1}" for i in range(len(node_ids)))
        passages = await self.db.fetch(f"""
            SELECT DISTINCT
                p.passage_id,
                p.text_content,
                p.canonical_ref,
                w.title,
                w.author,
                pc.confidence
            FROM free_will.passage_citations pc
            JOIN free_will.passages p ON pc.passage_id = p.passage_id
            JOIN free_will.ancient_works w ON p.work_id = w.work_id
            WHERE pc.kg_node_id IN ({placeholders})
            ORDER BY pc.confidence DESC
            LIMIT {limit}
        """, *node_ids)

        return passages

    async def _get_embedding(self, text: str) -> list[float]:
        """Get embedding for text using Gemini."""
        import os

        import google.generativeai as genai

        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY required for embeddings")

        genai.configure(api_key=api_key)
        result = genai.embed_content(
            model="models/gemini-embedding-001",
            content=text,
        )
        return result["embedding"]

    def _extract_citations(
        self,
        answer: str,
        node_ids: list[str],
        passages: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Extract and resolve citations from answer."""
        citations = []

        # Find [1], [2], etc. in answer
        citation_refs = re.findall(r'\[(\d+)\]', answer)

        # Map to nodes (simplified - could be enhanced)
        for _i, ref in enumerate(set(citation_refs)):
            ref_num = int(ref)
            if ref_num <= len(node_ids):
                node_id = node_ids[ref_num - 1]
                if node_id in self.node_lookup:
                    node = self.node_lookup[node_id]
                    citations.append({
                        "ref": ref,
                        "type": "node",
                        "id": node_id,
                        "label": node.get("label", node_id),
                    })

        # Also check for passage refs [P1], [P2]
        passage_refs = re.findall(r'\[P(\d+)\]', answer)
        for ref in set(passage_refs):
            ref_num = int(ref)
            if ref_num <= len(passages):
                p = passages[ref_num - 1]
                citations.append({
                    "ref": f"P{ref}",
                    "type": "passage",
                    "id": str(p["passage_id"]),
                    "label": f"{p['author']}, {p['title']} {p['canonical_ref']}",
                })

        return citations

    async def close(self) -> None:
        """Close resources."""
        await self.llm.close()
