#!/usr/bin/env python3
"""
Qdrant Vector Database Service for Ancient Free Will Database

Adapted from Sematika MVP implementation with enhancements for:
- Knowledge Graph embeddings (3072 dimensions)
- Text embeddings (3072 dimensions) 
- Multi-modal semantic search
- HNSW optimization for maximum performance

Author: Romain Girardi
Date: 2025-01-17
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional
from uuid import NAMESPACE_DNS, uuid5

from qdrant_client import AsyncQdrantClient, models
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

_log = logging.getLogger(__name__)

# HNSW configuration optimized for 3072-dimensional embeddings
HNSW_SPACE = "cosine"
HNSW_CONSTRUCTION_EF = 400  # Higher for better index quality with high dimensions
HNSW_M = 32  # Higher connectivity for high-dimensional vectors
HNSW_SEARCH_EF = 200  # Higher query-time quality
BATCH_SIZE = 50  # Smaller batches for high-dimensional vectors


class AncientFreeWillQdrantService:
    """Qdrant vector database service optimized for Ancient Free Will Database."""

    def __init__(
        self,
        host: str = None,
        port: int = None,
        collection_name: str = "ancient_free_will_vectors",
        vector_size: int = None,
    ) -> None:
        """Initialize Qdrant service for Ancient Free Will Database.

        Args:
            host: Qdrant host (defaults to environment variable)
            port: Qdrant HTTP port (defaults to environment variable)
            collection_name: Collection name
            vector_size: Vector dimension (defaults to environment variable)
        """
        self.host = host or os.getenv('QDRANT_HOST', 'localhost')
        self.port = port or int(os.getenv('QDRANT_HTTP_PORT', '6333'))
        self.collection_name = collection_name
        self.vector_size = vector_size or int(os.getenv('EMBEDDING_DIMENSIONS', '3072'))
        self.client: Optional[AsyncQdrantClient] = None

    async def initialize(self) -> None:
        """Initialize Qdrant client and ensure collection exists."""
        if self.client:
            _log.warning("Qdrant client already initialized")
            return

        try:
            self.client = AsyncQdrantClient(host=self.host, port=self.port, timeout=60.0)

            # Check if collection exists
            collections = await self.client.get_collections()
            collection_exists = any(
                c.name == self.collection_name for c in collections.collections
            )

            if not collection_exists:
                # Create collection with optimized HNSW configuration for 3072 dimensions
                await self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=self.vector_size,
                        distance=models.Distance.COSINE,
                    ),
                    hnsw_config=models.HnswConfigDiff(
                        m=HNSW_M,
                        ef_construct=HNSW_CONSTRUCTION_EF,
                    ),
                    optimizers_config=models.OptimizersConfigDiff(
                        indexing_threshold=10000,  # Lower threshold for high dimensions
                    ),
                )
                _log.info(
                    f"Created Qdrant collection: {self.collection_name} "
                    f"(dim={self.vector_size}, HNSW: M={HNSW_M}, ef={HNSW_CONSTRUCTION_EF})"
                )

            # Get collection info
            collection_info = await self.client.get_collection(self.collection_name)
            doc_count = collection_info.points_count

            _log.info(
                f"Qdrant initialized: {self.host}:{self.port}/{self.collection_name} "
                f"({doc_count} vectors)"
            )

        except Exception as e:
            _log.error(f"Failed to initialize Qdrant: {e}")
            raise

    async def close(self) -> None:
        """Close Qdrant client."""
        if self.client:
            await self.client.close()
            self.client = None
            _log.info("Qdrant client closed")

    async def add_knowledge_graph_node(
        self,
        node_id: str,
        embedding: List[float],
        node_type: str,
        label: str,
        text_representation: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Add Knowledge Graph node embedding.

        Args:
            node_id: Node ID from Knowledge Graph
            embedding: 3072-dimensional embedding vector
            node_type: Type of node (person, work, concept, argument)
            label: Node label
            text_representation: Text used for embedding generation
            metadata: Optional additional metadata

        Returns:
            Success status
        """
        if not self.client:
            _log.error("Qdrant client not initialized")
            return False

        try:
            # Generate deterministic UUID for node
            node_uuid = str(uuid5(NAMESPACE_DNS, f"kg_node_{node_id}"))

            # Build payload
            payload = {
                "node_id": node_id,
                "node_type": node_type,
                "label": label,
                "text_representation": text_representation,
                "source": "knowledge_graph",
                **(metadata or {}),
            }

            # Create point
            point = models.PointStruct(
                id=node_uuid,
                vector=embedding,
                payload=payload,
            )

            # Upload point
            await self.client.upsert(
                collection_name=self.collection_name,
                points=[point],
            )

            _log.info(f"Added KG node: {node_id} ({node_type})")
            return True

        except Exception as e:
            _log.error(f"Failed to add KG node {node_id}: {e}")
            return False

    async def add_knowledge_graph_edge(
        self,
        edge_id: str,
        embedding: List[float],
        source_id: str,
        target_id: str,
        relation: str,
        description: str,
        text_representation: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Add Knowledge Graph edge embedding.

        Args:
            edge_id: Edge ID from Knowledge Graph
            embedding: 3072-dimensional embedding vector
            source_id: Source node ID
            target_id: Target node ID
            relation: Relationship type
            description: Edge description
            text_representation: Text used for embedding generation
            metadata: Optional additional metadata

        Returns:
            Success status
        """
        if not self.client:
            _log.error("Qdrant client not initialized")
            return False

        try:
            # Generate deterministic UUID for edge
            edge_uuid = str(uuid5(NAMESPACE_DNS, f"kg_edge_{edge_id}"))

            # Build payload
            payload = {
                "edge_id": edge_id,
                "source_id": source_id,
                "target_id": target_id,
                "relation": relation,
                "description": description,
                "text_representation": text_representation,
                "source": "knowledge_graph",
                **(metadata or {}),
            }

            # Create point
            point = models.PointStruct(
                id=edge_uuid,
                vector=embedding,
                payload=payload,
            )

            # Upload point
            await self.client.upsert(
                collection_name=self.collection_name,
                points=[point],
            )

            _log.info(f"Added KG edge: {edge_id} ({relation})")
            return True

        except Exception as e:
            _log.error(f"Failed to add KG edge {edge_id}: {e}")
            return False

    async def add_text_embedding(
        self,
        text_id: str,
        embedding: List[float],
        title: str,
        author: str,
        category: str,
        language: str,
        text_length: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Add text embedding from PostgreSQL.

        Args:
            text_id: Text ID from PostgreSQL
            embedding: 3072-dimensional embedding vector
            title: Text title
            author: Text author
            category: Text category
            language: Text language
            text_length: Text length in characters
            metadata: Optional additional metadata

        Returns:
            Success status
        """
        if not self.client:
            _log.error("Qdrant client not initialized")
            return False

        try:
            # Generate deterministic UUID for text
            text_uuid = str(uuid5(NAMESPACE_DNS, f"text_{text_id}"))

            # Build payload
            payload = {
                "text_id": text_id,
                "title": title,
                "author": author,
                "category": category,
                "language": language,
                "text_length": text_length,
                "source": "postgresql",
                **(metadata or {}),
            }

            # Create point
            point = models.PointStruct(
                id=text_uuid,
                vector=embedding,
                payload=payload,
            )

            # Upload point
            await self.client.upsert(
                collection_name=self.collection_name,
                points=[point],
            )

            _log.info(f"Added text embedding: {text_id} ({title})")
            return True

        except Exception as e:
            _log.error(f"Failed to add text embedding {text_id}: {e}")
            return False

    async def search_semantic(
        self,
        query_embedding: List[float],
        top_k: int = 50,
        min_score: float = 0.0,
        source_filter: Optional[str] = None,
        node_type_filter: Optional[str] = None,
        category_filter: Optional[str] = None,
        language_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Semantic search with advanced filtering.

        Args:
            query_embedding: Query vector (3072 dimensions)
            top_k: Results count
            min_score: Minimum similarity score (0-1)
            source_filter: Filter by source (knowledge_graph, postgresql)
            node_type_filter: Filter by node type (person, work, concept, argument)
            category_filter: Filter by text category
            language_filter: Filter by language (grc, lat)

        Returns:
            Search results with scores and metadata
        """
        if not self.client:
            _log.error("Qdrant client not initialized")
            return []

        try:
            # Build filter conditions
            conditions = []
            
            if source_filter:
                conditions.append(
                    models.FieldCondition(
                        key="source",
                        match=models.MatchValue(value=source_filter),
                    )
                )
                
            if node_type_filter:
                conditions.append(
                    models.FieldCondition(
                        key="node_type",
                        match=models.MatchValue(value=node_type_filter),
                    )
                )
                
            if category_filter:
                conditions.append(
                    models.FieldCondition(
                        key="category",
                        match=models.MatchValue(value=category_filter),
                    )
                )
                
            if language_filter:
                conditions.append(
                    models.FieldCondition(
                        key="language",
                        match=models.MatchValue(value=language_filter),
                    )
                )

            # Create filter if conditions exist
            query_filter = None
            if conditions:
                query_filter = models.Filter(must=conditions)

            # Search
            results = await self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k,
                query_filter=query_filter,
                score_threshold=min_score if min_score > 0 else None,
                with_payload=True,
                with_vectors=False,
            )

            # Format results
            formatted = []
            for hit in results:
                formatted.append(
                    {
                        "id": hit.id,
                        "score": float(hit.score),
                        "metadata": hit.payload,
                    }
                )

            return formatted

        except Exception as e:
            _log.error(f"Semantic search failed: {e}")
            return []

    async def search_cross_modal(
        self,
        query_embedding: List[float],
        top_k: int = 20,
        min_score: float = 0.0,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Cross-modal search across Knowledge Graph and texts.

        Args:
            query_embedding: Query vector (3072 dimensions)
            top_k: Results count per modality
            min_score: Minimum similarity score (0-1)

        Returns:
            Dictionary with results from each modality
        """
        results = {
            "knowledge_graph_nodes": [],
            "knowledge_graph_edges": [],
            "texts": [],
        }

        try:
            # Search Knowledge Graph nodes
            kg_node_results = await self.search_semantic(
                query_embedding=query_embedding,
                top_k=top_k,
                min_score=min_score,
                source_filter="knowledge_graph",
                node_type_filter="person",  # Start with persons
            )
            results["knowledge_graph_nodes"].extend(kg_node_results)

            # Search Knowledge Graph edges
            kg_edge_results = await self.search_semantic(
                query_embedding=query_embedding,
                top_k=top_k,
                min_score=min_score,
                source_filter="knowledge_graph",
            )
            # Filter for edges (no node_type filter)
            edge_results = [r for r in kg_edge_results if "edge_id" in r["metadata"]]
            results["knowledge_graph_edges"].extend(edge_results)

            # Search texts
            text_results = await self.search_semantic(
                query_embedding=query_embedding,
                top_k=top_k,
                min_score=min_score,
                source_filter="postgresql",
            )
            results["texts"].extend(text_results)

            return results

        except Exception as e:
            _log.error(f"Cross-modal search failed: {e}")
            return results

    async def get_stats(self) -> Dict[str, Any]:
        """Get database statistics.

        Returns:
            Statistics dictionary
        """
        if not self.client:
            return {"error": "Client not initialized"}

        try:
            collection_info = await self.client.get_collection(self.collection_name)

            # Count by source
            kg_nodes = 0
            kg_edges = 0
            texts = 0

            # Scroll through all points to count by source
            offset = None
            while True:
                results = await self.client.scroll(
                    collection_name=self.collection_name,
                    limit=100,
                    offset=offset,
                    with_payload=True,
                    with_vectors=False,
                )
                points, offset = results

                if not points:
                    break

                for point in points:
                    source = point.payload.get("source")
                    if source == "knowledge_graph":
                        if "node_id" in point.payload:
                            kg_nodes += 1
                        elif "edge_id" in point.payload:
                            kg_edges += 1
                    elif source == "postgresql":
                        texts += 1

                if offset is None:
                    break

            return {
                "total_vectors": collection_info.points_count,
                "knowledge_graph_nodes": kg_nodes,
                "knowledge_graph_edges": kg_edges,
                "text_embeddings": texts,
                "vector_size": collection_info.config.params.vectors.size,
                "hnsw_config": {
                    "space": "cosine",
                    "m": collection_info.config.hnsw_config.m,
                    "ef_construct": collection_info.config.hnsw_config.ef_construct,
                },
                "host": self.host,
                "port": self.port,
                "collection": self.collection_name,
            }

        except Exception as e:
            _log.error(f"Stats failed: {e}")
            return {"error": str(e)}

    async def health_check(self) -> bool:
        """Check Qdrant health.

        Returns:
            True if Qdrant is healthy
        """
        if not self.client:
            return False

        try:
            await self.client.get_collections()
            return True
        except Exception as e:
            _log.error(f"Health check failed: {e}")
            return False


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_qdrant_service: Optional[AncientFreeWillQdrantService] = None


async def get_qdrant_service(
    collection_name: str = "ancient_free_will_vectors",
    vector_size: int = None,
) -> AncientFreeWillQdrantService:
    """Get or create singleton QdrantService instance.

    Args:
        collection_name: Collection name
        vector_size: Vector dimension (defaults to environment variable)

    Returns:
        AncientFreeWillQdrantService instance
    """
    global _qdrant_service

    if _qdrant_service is None:
        _qdrant_service = AncientFreeWillQdrantService(
            collection_name=collection_name,
            vector_size=vector_size,
        )
        await _qdrant_service.initialize()

    return _qdrant_service


async def close_qdrant_service() -> None:
    """Close singleton QdrantService instance."""
    global _qdrant_service

    if _qdrant_service:
        await _qdrant_service.close()
        _qdrant_service = None
