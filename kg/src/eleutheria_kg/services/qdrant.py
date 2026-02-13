"""
Qdrant Service - Vector database for semantic search.

Provides vector similarity search for knowledge graph nodes and text embeddings.
"""

import logging
import os
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models

logger = logging.getLogger(__name__)

# Configuration from environment
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_HTTP_PORT", "6333"))
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "3072"))


class QdrantService:
    """
    Manages Qdrant vector database connections and searches.

    Supports both local Qdrant instances and Qdrant Cloud.
    """

    def __init__(self) -> None:
        self.client: QdrantClient | None = None

    async def connect(self) -> None:
        """
        Connect to Qdrant.

        Uses QDRANT_API_KEY for cloud connections, otherwise connects locally.
        """
        try:
            if QDRANT_API_KEY:
                # Cloud connection with API key and HTTPS
                logger.info(f"Connecting to Qdrant Cloud at {QDRANT_HOST}")
                self.client = QdrantClient(
                    url=f"https://{QDRANT_HOST}",
                    api_key=QDRANT_API_KEY,
                    check_compatibility=False,
                )
            else:
                # Local connection with HTTP
                logger.info(
                    f"Connecting to local Qdrant at {QDRANT_HOST}:{QDRANT_PORT}"
                )
                self.client = QdrantClient(
                    host=QDRANT_HOST,
                    port=QDRANT_PORT,
                    check_compatibility=False,
                )

            # Verify connection
            collections = self.client.get_collections()
            logger.info(
                f"Connected to Qdrant - {len(collections.collections)} collections"
            )

        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise

    async def close(self) -> None:
        """Close Qdrant connection."""
        if self.client:
            self.client.close()
            logger.info("Qdrant connection closed")

    def is_connected(self) -> bool:
        """Check if Qdrant is connected."""
        return self.client is not None

    async def search_nodes(
        self,
        query_vector: list[float],
        limit: int = 10,
        score_threshold: float | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search KG nodes by vector similarity.

        Args:
            query_vector: Query embedding (3072 dimensions)
            limit: Maximum results
            score_threshold: Minimum similarity score

        Returns:
            List of matching nodes with scores
        """
        if not self.client:
            raise RuntimeError("Qdrant not connected")

        try:
            search_result = self.client.search(
                collection_name="kg_nodes_gemini",
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
            )

            results = []
            for hit in search_result:
                payload = hit.payload or {}
                results.append(
                    {
                        "id": payload.get("id"),
                        "score": hit.score,
                        "payload": payload,
                    }
                )

            return results

        except Exception as e:
            logger.error(f"Error searching kg_nodes_gemini: {e}")
            raise

    async def search_texts(
        self,
        query_vector: list[float],
        limit: int = 10,
        filters: dict[str, Any] | None = None,
        score_threshold: float | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search text embeddings by vector similarity.

        Args:
            query_vector: Query embedding
            limit: Maximum results
            filters: Optional field filters
            score_threshold: Minimum similarity score

        Returns:
            List of matching text passages with scores
        """
        if not self.client:
            raise RuntimeError("Qdrant not connected")

        try:
            qdrant_filter = None
            if filters:
                qdrant_filter = models.Filter(
                    must=[
                        models.FieldCondition(
                            key=key, match=models.MatchValue(value=value)
                        )
                        for key, value in filters.items()
                    ]
                )

            search_result = self.client.search(
                collection_name="text_embeddings",
                query_vector=query_vector,
                limit=limit,
                query_filter=qdrant_filter,
                score_threshold=score_threshold,
            )

            results = []
            for hit in search_result:
                payload = hit.payload or {}
                results.append(
                    {
                        "id": str(hit.id),
                        "score": hit.score,
                        "passage_id": payload.get("passage_id"),
                        "work_id": payload.get("work_id"),
                        "text_content": payload.get("text_content", ""),
                        "author": payload.get("author"),
                        "title": payload.get("title"),
                        "canonical_ref": payload.get("canonical_ref"),
                    }
                )

            return results

        except Exception as e:
            logger.error(f"Error searching text_embeddings: {e}")
            raise

    async def search_edges(
        self,
        query_vector: list[float],
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Search KG edges by vector similarity.

        Args:
            query_vector: Query embedding
            limit: Maximum results

        Returns:
            List of matching edges with scores
        """
        if not self.client:
            raise RuntimeError("Qdrant not connected")

        try:
            search_result = self.client.search(
                collection_name="kg_edges",
                query_vector=query_vector,
                limit=limit,
            )

            results = []
            for hit in search_result:
                payload = hit.payload or {}
                results.append(
                    {
                        "id": str(hit.id),
                        "score": hit.score,
                        "source": payload.get("source"),
                        "target": payload.get("target"),
                        "relation": payload.get("relation"),
                        "description": payload.get("description"),
                    }
                )

            return results

        except Exception as e:
            logger.error(f"Error searching kg_edges: {e}")
            raise

    async def search_contextual_passages(
        self,
        query_vector: list[float],
        limit: int = 10,
        filters: dict[str, Any] | None = None,
        score_threshold: float | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search contextual passage embeddings by vector similarity.

        Uses the ``passages_contextual`` collection which contains
        passages re-embedded with author/work/period context headers.
        Falls back to ``text_embeddings`` if contextual collection
        does not exist.

        Args:
            query_vector: Query embedding
            limit: Maximum results
            filters: Optional field filters
            score_threshold: Minimum similarity score

        Returns:
            List of matching text passages with scores
        """
        if not self.client:
            raise RuntimeError("Qdrant not connected")

        collection = "passages_contextual"
        try:
            self.client.get_collection(collection)
        except Exception:
            # Fall back to standard text_embeddings
            return await self.search_texts(
                query_vector,
                limit,
                filters,
                score_threshold,
            )

        try:
            qdrant_filter = None
            if filters:
                qdrant_filter = models.Filter(
                    must=[
                        models.FieldCondition(
                            key=key, match=models.MatchValue(value=value)
                        )
                        for key, value in filters.items()
                    ]
                )

            search_result = self.client.search(
                collection_name=collection,
                query_vector=query_vector,
                limit=limit,
                query_filter=qdrant_filter,
                score_threshold=score_threshold,
            )

            results = []
            for hit in search_result:
                payload = hit.payload or {}
                results.append(
                    {
                        "id": str(hit.id),
                        "score": hit.score,
                        "passage_id": payload.get("passage_id"),
                        "text_content": payload.get("text_content", ""),
                        "author": payload.get("author"),
                        "title": payload.get("title"),
                        "canonical_ref": payload.get("canonical_ref"),
                        "period": payload.get("period"),
                        "contextual_text": payload.get("contextual_text", ""),
                    }
                )

            return results

        except Exception as e:
            logger.error(f"Error searching {collection}: {e}")
            # Fall back to standard collection
            return await self.search_texts(
                query_vector,
                limit,
                filters,
                score_threshold,
            )

    async def get_collection_info(self, collection_name: str) -> dict[str, Any]:
        """Get information about a collection."""
        if not self.client:
            raise RuntimeError("Qdrant not connected")

        info = self.client.get_collection(collection_name)
        return {
            "name": collection_name,
            "vectors_count": info.vectors_count,
            "points_count": info.points_count,
            "status": str(info.status),
        }
