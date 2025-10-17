#!/usr/bin/env python3
"""
Qdrant Service - Vector database connection and search
"""

import logging
import os
from typing import List, Dict, Optional, Any
from qdrant_client import QdrantClient
from qdrant_client.http import models
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Qdrant configuration from environment
QDRANT_HOST = os.getenv('QDRANT_HOST', 'localhost')
QDRANT_PORT = int(os.getenv('QDRANT_HTTP_PORT', '6333'))
EMBEDDING_DIMENSIONS = int(os.getenv('EMBEDDING_DIMENSIONS', '3072'))


class QdrantService:
    """Manages Qdrant vector database connections and searches"""

    def __init__(self):
        self.client: Optional[QdrantClient] = None

    async def connect(self) -> None:
        """Connect to Qdrant with proper error handling"""
        try:
            logger.info(f"Connecting to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}")
            self.client = QdrantClient(
                host=QDRANT_HOST, 
                port=QDRANT_PORT,
                check_compatibility=False  # Suppress version warnings
            )

            # Verify connection
            collections = self.client.get_collections()
            logger.info(f"✅ Connected to Qdrant - {len(collections.collections)} collections available")
            
            # Log available collections
            for collection in collections.collections:
                logger.debug(f"   - {collection.name}")

        except Exception as e:
            logger.error(f"❌ Failed to connect to Qdrant: {e}")
            raise

    async def close(self) -> None:
        """Close Qdrant connection"""
        if self.client:
            self.client.close()
            logger.info("Qdrant connection closed")

    def is_connected(self) -> bool:
        """Check if Qdrant is connected"""
        return self.client is not None

    async def search_nodes(
        self,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Search KG nodes by vector similarity"""
        if not self.client:
            raise RuntimeError("Qdrant not connected")

        try:
            # Search without filter first, then filter in Python
            search_result = self.client.search(
                collection_name="ancient_free_will_vectors",
                query_vector=query_vector,
                limit=limit * 3,  # Get more to ensure we have enough KG nodes
                score_threshold=score_threshold
            )

            # Filter results to only include KG nodes and limit to requested amount
            kg_results = []
            for hit in search_result:
                if 'node_id' in hit.payload:
                    kg_results.append({
                        'id': hit.id,
                        'score': hit.score,
                        'payload': hit.payload
                    })
                    if len(kg_results) >= limit:
                        break

            logger.info(f"Found {len(kg_results)} KG nodes out of {len(search_result)} total results")
            return kg_results

        except Exception as e:
            logger.error(f"Error searching kg_nodes: {e}")
            raise

    async def search_texts(
        self,
        query_vector: List[float],
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        score_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Search text embeddings by vector similarity"""
        if not self.client:
            raise RuntimeError("Qdrant not connected")

        try:
            # Build filter if provided
            qdrant_filter = None
            if filters:
                qdrant_filter = models.Filter(
                    must=[
                        models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=value)
                        )
                        for key, value in filters.items()
                    ]
                )

            search_result = self.client.search(
                collection_name="text_embeddings",
                query_vector=query_vector,
                limit=limit,
                query_filter=qdrant_filter,
                score_threshold=score_threshold
            )

            return [
                {
                    'id': hit.id,
                    'score': hit.score,
                    'payload': hit.payload
                }
                for hit in search_result
            ]

        except Exception as e:
            logger.error(f"Error searching text_embeddings: {e}")
            raise

    async def search_edges(
        self,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Search KG edges by vector similarity"""
        if not self.client:
            raise RuntimeError("Qdrant not connected")

        try:
            search_result = self.client.search(
                collection_name="kg_edges",
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold
            )

            return [
                {
                    'id': hit.id,
                    'score': hit.score,
                    'payload': hit.payload
                }
                for hit in search_result
            ]

        except Exception as e:
            logger.error(f"Error searching kg_edges: {e}")
            raise

    async def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get information about a collection"""
        if not self.client:
            raise RuntimeError("Qdrant not connected")

        try:
            info = self.client.get_collection(collection_name)
            return {
                'name': collection_name,
                'points_count': info.points_count,
                'vectors_count': info.vectors_count,
                'status': info.status
            }

        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            raise
