#!/usr/bin/env python3
"""
Hybrid Search Service - Combines full-text, lemmatic, and semantic search
Uses Reciprocal Rank Fusion (RRF) to merge results
"""

import logging
from typing import List, Dict, Any, Optional
from collections import defaultdict
import google.generativeai as genai
import os
from dotenv import load_dotenv

from services.db import DatabaseService
from services.qdrant_service import QdrantService

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Configure Gemini for embeddings
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    logger.info("✅ Gemini configured for hybrid search embeddings")
else:
    logger.warning("⚠️ GEMINI_API_KEY not found - semantic search will fail")


class HybridSearchService:
    """Implements hybrid search using RRF to combine multiple search modes"""

    def __init__(self, db_service: DatabaseService, qdrant_service: QdrantService):
        self.db = db_service
        self.qdrant = qdrant_service

    async def generate_query_embedding(self, query: str) -> List[float]:
        """Generate embedding for search query using Gemini (3072 dimensions)"""
        try:
            # Reconfigure API key before each call to ensure it's set
            if GEMINI_API_KEY:
                genai.configure(api_key=GEMINI_API_KEY)

            result = genai.embed_content(
                model="models/gemini-embedding-001",
                content=query
            )
            return result['embedding']

        except Exception as e:
            logger.error(f"Error generating query embedding: {e}")
            raise

    async def fulltext_search(
        self,
        query: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Full-text search using PostgreSQL ts_rank"""
        try:
            sql = """
            SELECT
                id, title, author, category, language,
                ts_rank(search_vector, plainto_tsquery('simple', $1)) as rank,
                ts_headline('simple', normalized_text, plainto_tsquery('simple', $1),
                           'MaxWords=50, MinWords=20') as snippet
            FROM free_will.texts
            WHERE search_vector @@ plainto_tsquery('simple', $1)
            ORDER BY rank DESC
            LIMIT $2
            """

            results = await self.db.fetch(sql, query, limit)
            return results

        except Exception as e:
            logger.error(f"Error in fulltext_search: {e}")
            return []

    async def lemmatic_search(
        self,
        query: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Lemmatic search using existing lemmas in JSONB column"""
        try:
            # Search across the 109 texts that have lemmas
            sql = """
            SELECT
                id, title, author, category, language, lemmas,
                1.0 as rank
            FROM free_will.texts
            WHERE lemmas IS NOT NULL
            AND lemmas::text ILIKE $1
            LIMIT $2
            """

            # Add wildcards for partial matching
            search_pattern = f"%{query}%"
            results = await self.db.fetch(sql, search_pattern, limit)

            return results

        except Exception as e:
            logger.error(f"Error in lemmatic_search: {e}")
            return []

    async def semantic_search(
        self,
        query: str,
        limit: int = 50,
        collection: str = "text_embeddings"
    ) -> List[Dict[str, Any]]:
        """Semantic search using Qdrant vector similarity"""
        try:
            # Generate query embedding
            query_vector = await self.generate_query_embedding(query)

            # Search in Qdrant
            if collection == "text_embeddings":
                results = await self.qdrant.search_texts(
                    query_vector=query_vector,
                    limit=limit
                )
            elif collection == "kg_nodes":
                results = await self.qdrant.search_nodes(
                    query_vector=query_vector,
                    limit=limit
                )
            else:
                results = await self.qdrant.search_edges(
                    query_vector=query_vector,
                    limit=limit
                )

            return results

        except Exception as e:
            logger.error(f"Error in semantic_search: {e}")
            return []

    def reciprocal_rank_fusion(
        self,
        results_lists: List[List[Dict[str, Any]]],
        id_key: str = 'id',
        k: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Combine multiple ranked lists using Reciprocal Rank Fusion (RRF)

        RRF Formula: score(item) = Σ 1/(k + rank_i) for all lists i

        Args:
            results_lists: List of result lists to combine
            id_key: Key to use for identifying unique items
            k: Constant (typically 60) to prevent high ranks from dominating
        """
        scores = defaultdict(float)
        items = {}

        # Calculate RRF scores
        for results in results_lists:
            for rank, item in enumerate(results, start=1):
                item_id = item[id_key]
                scores[item_id] += 1 / (k + rank)

                # Store the item (use first occurrence)
                if item_id not in items:
                    items[item_id] = item

        # Sort by RRF score
        sorted_items = sorted(
            scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Build final results with scores
        final_results = []
        for item_id, score in sorted_items:
            item = items[item_id].copy()
            item['rrf_score'] = score
            final_results.append(item)

        return final_results

    async def hybrid_search(
        self,
        query: str,
        limit: int = 10,
        enable_fulltext: bool = True,
        enable_lemmatic: bool = True,
        enable_semantic: bool = True,
        collection: str = "text_embeddings"
    ) -> Dict[str, Any]:
        """
        Perform hybrid search combining multiple search modes

        Args:
            query: Search query
            limit: Number of results to return
            enable_fulltext: Enable full-text search
            enable_lemmatic: Enable lemmatic search
            enable_semantic: Enable semantic search
            collection: Qdrant collection to search (text_embeddings or kg_nodes)

        Returns:
            Dictionary with combined results and individual search results
        """
        logger.info(f"Hybrid search: query='{query}', modes={enable_fulltext}/{enable_lemmatic}/{enable_semantic}")

        # Collect results from enabled search modes
        results_lists = []

        # Full-text search
        fulltext_results = []
        if enable_fulltext:
            fulltext_results = await self.fulltext_search(query, limit=50)
            if fulltext_results:
                results_lists.append(fulltext_results)
                logger.info(f"Full-text search: {len(fulltext_results)} results")

        # Lemmatic search
        lemmatic_results = []
        if enable_lemmatic:
            lemmatic_results = await self.lemmatic_search(query, limit=50)
            if lemmatic_results:
                results_lists.append(lemmatic_results)
                logger.info(f"Lemmatic search: {len(lemmatic_results)} results")

        # Semantic search
        semantic_results = []
        if enable_semantic:
            semantic_results = await self.semantic_search(query, limit=50, collection=collection)
            if semantic_results:
                results_lists.append(semantic_results)
                logger.info(f"Semantic search: {len(semantic_results)} results")

        # Combine using RRF
        if not results_lists:
            return {
                'combined_results': [],
                'fulltext_results': [],
                'lemmatic_results': [],
                'semantic_results': [],
                'total_found': 0
            }

        combined_results = self.reciprocal_rank_fusion(results_lists, id_key='id', k=60)

        # Limit final results
        combined_results = combined_results[:limit]

        logger.info(f"Hybrid search complete: {len(combined_results)} combined results")

        return {
            'combined_results': combined_results,
            'fulltext_results': fulltext_results[:limit],
            'lemmatic_results': lemmatic_results[:limit],
            'semantic_results': semantic_results[:limit],
            'total_found': len(combined_results)
        }

    async def search_knowledge_graph(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search Knowledge Graph nodes using semantic search"""
        try:
            results = await self.semantic_search(
                query=query,
                limit=limit,
                collection="kg_nodes"
            )

            return results

        except Exception as e:
            logger.error(f"Error searching knowledge graph: {e}")
            return []
