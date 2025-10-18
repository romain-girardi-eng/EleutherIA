#!/usr/bin/env python3
"""
GraphRAG Service - Graph-based Retrieval-Augmented Generation
Combines semantic search, graph traversal, and LLM synthesis
"""

import logging
import json
import os
from typing import List, Dict, Any, Set, Optional, Tuple
from pathlib import Path
from collections import defaultdict, deque

import google.generativeai as genai
from dotenv import load_dotenv

from services.qdrant_service import QdrantService
from services.db import DatabaseService
from services.llm_service import LLMService, ModelProvider

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Configure Gemini with proper error handling
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY environment variable not set!")
    raise ValueError("GEMINI_API_KEY environment variable is required")

genai.configure(api_key=GEMINI_API_KEY)

# Path to KG database
# In Docker: /app/services/graphrag_service.py -> /app/ancient_free_will_database.json
# Locally: backend/services/graphrag_service.py -> ancient_free_will_database.json
KG_PATH = Path(__file__).parent.parent / "ancient_free_will_database.json"


class GraphRAGService:
    """
    Complete GraphRAG pipeline:
    1. Semantic search (Qdrant) - find relevant starting nodes
    2. Graph traversal - expand to connected nodes
    3. Context building - create rich context with citations
    4. LLM synthesis - generate answer with Gemini
    5. Citation extraction - track sources used
    """

    def __init__(self, qdrant_service: QdrantService, db_service: DatabaseService, llm_service: Optional[LLMService] = None) -> None:
        """Initialize GraphRAG service with proper error handling"""
        self.qdrant = qdrant_service
        self.db = db_service
        self.llm_service = llm_service or LLMService(preferred_provider=ModelProvider.OLLAMA)
        self.kg_data: Optional[Dict[str, Any]] = None
        self._load_kg()

    def _load_kg(self) -> None:
        """Load Knowledge Graph data with proper error handling"""
        try:
            if not KG_PATH.exists():
                raise FileNotFoundError(f"Knowledge Graph file not found: {KG_PATH}")
                
            with open(KG_PATH, 'r', encoding='utf-8') as f:
                self.kg_data = json.load(f)
                
            if not isinstance(self.kg_data, dict) or 'nodes' not in self.kg_data or 'edges' not in self.kg_data:
                raise ValueError("Invalid Knowledge Graph format: missing 'nodes' or 'edges' keys")
                
            logger.info(f"✅ Loaded KG: {len(self.kg_data['nodes'])} nodes, {len(self.kg_data['edges'])} edges")
            
        except FileNotFoundError as e:
            logger.error(f"❌ Knowledge Graph file not found: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON in Knowledge Graph file: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Error loading Knowledge Graph: {e}")
            raise

    def _get_node_by_id(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get node by ID"""
        if not self.kg_data:
            return None

        for node in self.kg_data['nodes']:
            if node['id'] == node_id:
                return node
        return None

    async def semantic_search_nodes(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Step 1: Semantic search to find relevant starting nodes
        Uses Qdrant vector similarity with proper error handling
        """
        logger.info(f"🔍 GraphRAG Step 1: Semantic search for '{query}'")

        try:
            if not query.strip():
                logger.warning("Empty query provided for semantic search")
                return []

            # Generate query embedding with proper error handling
            logger.debug("Generating query embedding with Gemini...")
            result = genai.embed_content(
                model="models/gemini-embedding-001",
                content=query,
                output_dimensionality=3072
            )
            
            if 'embedding' not in result:
                logger.error("No embedding returned from Gemini API")
                return []
                
            query_vector = result['embedding']
            logger.debug(f"Generated embedding: {len(query_vector)} dimensions")

            # Search in Qdrant with proper error handling
            logger.debug(f"Searching Qdrant for {limit} nodes...")
            search_results = await self.qdrant.search_nodes(
                query_vector=query_vector,
                limit=limit
            )

            if not search_results:
                logger.warning("No results returned from Qdrant search")
                return []

            # Enrich with full node data
            enriched_results = []
            for result in search_results:
                try:
                    payload = result.get('payload', {})
                    node_id = payload.get('node_id')
                    
                    if not node_id:
                        logger.warning(f"No node_id found in payload: {payload.keys()}")
                        continue
                        
                    node = self._get_node_by_id(node_id)
                    if node:
                        enriched_results.append({
                            **node,
                            'semantic_score': result.get('score', 0.0)
                        })
                    else:
                        logger.warning(f"Node {node_id} not found in Knowledge Graph")
                        
                except Exception as e:
                    logger.warning(f"Error processing search result: {e}")
                    continue

            logger.info(f"✅ Found {len(enriched_results)} relevant nodes from {len(search_results)} search results")
            return enriched_results

        except Exception as e:
            logger.error(f"❌ Error in semantic search: {e}", exc_info=True)
            return []

    def graph_traversal_bfs(
        self,
        starting_nodes: List[Dict[str, Any]],
        max_depth: int = 2,
        max_nodes: int = 50
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Step 2: Graph traversal using Breadth-First Search
        Expands from starting nodes to connected nodes

        Returns:
            Tuple of (expanded_nodes, traversed_edges)
        """
        logger.info(f"GraphRAG Step 2: Graph traversal (depth={max_depth}, max_nodes={max_nodes})")

        if not self.kg_data:
            return [], []

        # Initialize
        visited_node_ids = set()
        queue = deque()
        expanded_nodes = []
        traversed_edges = []

        # Build adjacency lists for fast lookup
        outgoing_edges = defaultdict(list)  # node_id -> list of edges where node is source
        incoming_edges = defaultdict(list)  # node_id -> list of edges where node is target

        for edge in self.kg_data['edges']:
            outgoing_edges[edge['source']].append(edge)
            incoming_edges[edge['target']].append(edge)

        # Add starting nodes to queue
        for node in starting_nodes:
            node_id = node['id']
            if node_id not in visited_node_ids:
                queue.append((node, 0))  # (node, depth)
                visited_node_ids.add(node_id)

        # BFS traversal
        while queue and len(expanded_nodes) < max_nodes:
            current_node, depth = queue.popleft()
            expanded_nodes.append(current_node)

            # Don't expand beyond max depth
            if depth >= max_depth:
                continue

            node_id = current_node['id']

            # Explore outgoing edges (node -> target)
            for edge in outgoing_edges[node_id]:
                target_id = edge['target']
                if target_id not in visited_node_ids:
                    target_node = self._get_node_by_id(target_id)
                    if target_node and len(expanded_nodes) < max_nodes:
                        queue.append((target_node, depth + 1))
                        visited_node_ids.add(target_id)
                        traversed_edges.append(edge)

            # Explore incoming edges (source -> node)
            for edge in incoming_edges[node_id]:
                source_id = edge['source']
                if source_id not in visited_node_ids:
                    source_node = self._get_node_by_id(source_id)
                    if source_node and len(expanded_nodes) < max_nodes:
                        queue.append((source_node, depth + 1))
                        visited_node_ids.add(source_id)
                        traversed_edges.append(edge)

        logger.info(f"Expanded to {len(expanded_nodes)} nodes via {len(traversed_edges)} edges")
        return expanded_nodes, traversed_edges

    def extract_citations(
        self,
        nodes: List[Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """
        Step 3: Extract citations from nodes
        Returns ancient sources and modern scholarship
        """
        logger.info("GraphRAG Step 3: Extracting citations")

        ancient_sources = set()
        modern_scholarship = set()

        for node in nodes:
            # Extract ancient sources
            if 'ancient_sources' in node and node['ancient_sources']:
                if isinstance(node['ancient_sources'], list):
                    ancient_sources.update(node['ancient_sources'])

            # Extract modern scholarship
            if 'modern_scholarship' in node and node['modern_scholarship']:
                if isinstance(node['modern_scholarship'], list):
                    modern_scholarship.update(node['modern_scholarship'])

        citations = {
            'ancient_sources': sorted(list(ancient_sources)),
            'modern_scholarship': sorted(list(modern_scholarship))
        }

        logger.info(f"Extracted {len(citations['ancient_sources'])} ancient sources, "
                   f"{len(citations['modern_scholarship'])} modern scholarship")

        return citations

    def build_context(
        self,
        nodes: List[Dict[str, Any]],
        max_context_length: int = 15
    ) -> str:
        """
        Step 4: Build context string for LLM
        Prioritizes by node type and includes key information
        """
        logger.info("GraphRAG Step 4: Building context")

        # Prioritize node types
        type_priority = {
            'person': 1,
            'argument': 2,
            'concept': 3,
            'work': 4,
            'debate': 5,
            'controversy': 6,
            'school': 7,
            'reformulation': 8,
            'event': 9,
            'group': 10,
            'argument_framework': 11
        }

        # Sort nodes by priority
        sorted_nodes = sorted(
            nodes,
            key=lambda n: (type_priority.get(n.get('type', 'unknown'), 99), n.get('label', ''))
        )

        # Limit context
        sorted_nodes = sorted_nodes[:max_context_length]

        # Build context
        context_parts = ["# Ancient Philosophy Knowledge Base\n"]

        for node in sorted_nodes:
            node_type = node.get('type', 'unknown')
            label = node.get('label', 'Unknown')

            context_parts.append(f"\n## {label} ({node_type})")

            # Add description
            if 'description' in node and node['description']:
                context_parts.append(f"{node['description']}")

            # Add period and school for persons
            if node_type == 'person':
                if 'period' in node and node['period']:
                    context_parts.append(f"**Period:** {node['period']}")
                if 'school' in node and node['school']:
                    context_parts.append(f"**School:** {node['school']}")
                if 'dates' in node and node['dates']:
                    context_parts.append(f"**Dates:** {node['dates']}")

            # Add position for arguments
            if node_type == 'argument' and 'position_on_free_will' in node:
                context_parts.append(f"**Position:** {node['position_on_free_will']}")

            # Add sources (first 2)
            if 'ancient_sources' in node and node['ancient_sources']:
                sources = node['ancient_sources'][:2]
                if sources:
                    context_parts.append(f"**Sources:** {'; '.join(sources)}")

            context_parts.append("")  # Empty line

        context = "\n".join(context_parts)
        logger.info(f"Built context: {len(context)} characters, {len(sorted_nodes)} nodes")

        return context

    async def synthesize_answer(
        self,
        query: str,
        context: str,
        temperature: float = 0.7,
        provider: Optional[ModelProvider] = None
    ) -> str:
        """
        Step 5: Generate answer using unified LLM service
        Uses context from Knowledge Graph to ground the answer
        """
        logger.info("GraphRAG Step 5: Synthesizing answer with unified LLM service")

        system_prompt = """You are a scholar of ancient philosophy specializing in debates about free will, determinism, and moral responsibility.

Your task is to answer questions using ONLY the provided Knowledge Base from the Ancient Free Will Database.

CRITICAL RULES:
1. ONLY use information from the provided Knowledge Base
2. ALWAYS cite your sources using the node labels (e.g., "According to Aristotle (person)...")
3. If the Knowledge Base doesn't contain enough information, say so explicitly
4. DO NOT add information from outside the Knowledge Base
5. Be precise and academic in your language
6. When discussing arguments, mention the key ancient sources
7. Acknowledge nuances and complexities in ancient debates

Format your answer clearly with:
- Direct answer to the question
- Supporting evidence from the Knowledge Base
- Relevant ancient sources (cite them!)
- Any important caveats or limitations"""

        user_prompt = f"""Knowledge Base:
{context}

Question: {query}

Answer (with citations):"""

        try:
            logger.info(f"🤖 Generating answer with unified LLM service")
            
            result = await self.llm_service.generate_response(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=2000,
                provider=provider
            )
            
            if result.get("response"):
                answer = result["response"]
                provider_used = result.get("provider", "unknown")
                logger.info(f"✅ Generated answer with {provider_used}: {len(answer)} characters")
                
                # Add provider info to the answer for transparency
                if provider_used == "ollama":
                    answer = f"[Generated with local Mistral 7B]\n\n{answer}"
                elif provider_used == "gemini":
                    answer = f"[Generated with Gemini 2.0 Flash]\n\n{answer}"
                
                return answer
            else:
                logger.error(f"❌ Empty response from LLM service: {result}")
                return "I apologize, but I was unable to generate a response. Please try rephrasing your question."

        except Exception as e:
            logger.error(f"❌ Error generating answer: {e}")
            return f"I encountered an error while generating an answer: {str(e)}"

    def create_reasoning_path(
        self,
        starting_nodes: List[Dict[str, Any]],
        expanded_nodes: List[Dict[str, Any]],
        traversed_edges: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Step 6: Create reasoning path visualization data
        Shows which nodes were used and how they're connected
        """
        logger.info("GraphRAG Step 6: Creating reasoning path")

        # Extract node IDs
        starting_ids = set(n['id'] for n in starting_nodes)
        expanded_ids = set(n['id'] for n in expanded_nodes)

        # Build reasoning path
        reasoning_path = {
            'starting_nodes': [
                {
                    'id': node['id'],
                    'label': node.get('label', ''),
                    'type': node.get('type', ''),
                    'reason': 'Semantically relevant to query'
                }
                for node in starting_nodes
            ],
            'expanded_nodes': [
                {
                    'id': node['id'],
                    'label': node.get('label', ''),
                    'type': node.get('type', ''),
                    'reason': 'Connected via graph traversal'
                }
                for node in expanded_nodes
                if node['id'] not in starting_ids
            ],
            'traversed_edges': [
                {
                    'source': edge['source'],
                    'target': edge['target'],
                    'relation': edge.get('relation', ''),
                    'description': edge.get('description', '')
                }
                for edge in traversed_edges
            ],
            'total_nodes': len(expanded_ids),
            'total_edges': len(traversed_edges)
        }

        logger.info(f"Reasoning path: {len(starting_ids)} starting → {len(expanded_ids)} total nodes")

        return reasoning_path

    async def answer_question(
        self,
        query: str,
        semantic_k: int = 10,
        graph_depth: int = 2,
        max_context: int = 15,
        temperature: float = 0.7,
        deep_mode: bool = False
    ) -> Dict[str, Any]:
        """
        Complete GraphRAG pipeline to answer a question

        Args:
            query: User's question
            semantic_k: Number of nodes to retrieve via semantic search
            graph_depth: Depth of graph traversal (1-3 recommended)
            max_context: Maximum nodes to include in LLM context
            temperature: LLM temperature (0.0-1.0)
            deep_mode: Include PostgreSQL full-text search results

        Returns:
            Dictionary with answer, citations, reasoning path, and metadata
        """
        logger.info(f"='*80")
        logger.info(f"GraphRAG Pipeline: '{query}'")
        logger.info(f"='*80")

        try:
            # Step 1: Semantic search
            starting_nodes = await self.semantic_search_nodes(
                query=query,
                limit=semantic_k
            )

            if not starting_nodes:
                return {
                    'query': query,
                    'answer': 'I could not find any relevant information in the Knowledge Graph to answer this question.',
                    'citations': {'ancient_sources': [], 'modern_scholarship': []},
                    'reasoning_path': {},
                    'nodes_used': 0,
                    'success': False
                }

            # Step 2: Graph traversal
            expanded_nodes, traversed_edges = self.graph_traversal_bfs(
                starting_nodes=starting_nodes,
                max_depth=graph_depth,
                max_nodes=50
            )

            # Step 3: Extract citations
            citations = self.extract_citations(expanded_nodes)

            # Step 4: Build context
            context = self.build_context(
                nodes=expanded_nodes,
                max_context_length=max_context
            )

            # Step 5: Synthesize answer
            answer = await self.synthesize_answer(
                query=query,
                context=context,
                temperature=temperature
            )

            # Step 6: Create reasoning path
            reasoning_path = self.create_reasoning_path(
                starting_nodes=starting_nodes,
                expanded_nodes=expanded_nodes,
                traversed_edges=traversed_edges
            )

            # Build response
            response = {
                'query': query,
                'answer': answer,
                'citations': citations,
                'reasoning_path': reasoning_path,
                'nodes_used': len(expanded_nodes),
                'edges_traversed': len(traversed_edges),
                'parameters': {
                    'semantic_k': semantic_k,
                    'graph_depth': graph_depth,
                    'max_context': max_context,
                    'temperature': temperature,
                    'deep_mode': deep_mode
                },
                'success': True
            }

            logger.info("="*80)
            logger.info("✅ GraphRAG Pipeline Complete")
            logger.info(f"   Answer length: {len(answer)} chars")
            logger.info(f"   Nodes used: {len(expanded_nodes)}")
            logger.info(f"   Ancient sources: {len(citations['ancient_sources'])}")
            logger.info(f"   Modern scholarship: {len(citations['modern_scholarship'])}")
            logger.info("="*80)

            return response

        except Exception as e:
            logger.error(f"Error in GraphRAG pipeline: {e}", exc_info=True)
            return {
                'query': query,
                'answer': f'Error processing question: {str(e)}',
                'citations': {'ancient_sources': [], 'modern_scholarship': []},
                'reasoning_path': {},
                'nodes_used': 0,
                'success': False,
                'error': str(e)
            }
