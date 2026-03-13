"""Qdrant Service - Vector database for semantic search."""

import logging
import os
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models

logger = logging.getLogger(__name__)

EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "3072"))


def _resolve_qdrant_connection() -> dict[str, Any]:
    """Prefer cloud settings over a stale localhost QDRANT_URL."""
    qdrant_url = os.getenv("QDRANT_URL", "").strip()
    qdrant_host = os.getenv("QDRANT_HOST", "localhost").strip()
    qdrant_port = int(os.getenv("QDRANT_HTTP_PORT", "6333"))
    qdrant_api_key = os.getenv("QDRANT_API_KEY", "").strip() or None

    localhost_url = qdrant_url.lower().startswith("http://localhost") or qdrant_url.lower().startswith(
        "http://127.0.0.1"
    )
    if localhost_url and qdrant_host and qdrant_host != "localhost" and qdrant_api_key:
        return {
            "mode": "cloud",
            "url": f"https://{qdrant_host}",
            "api_key": qdrant_api_key,
            "host": qdrant_host,
            "port": qdrant_port,
        }

    if qdrant_url:
        return {
            "mode": "url",
            "url": qdrant_url,
            "api_key": qdrant_api_key,
            "host": qdrant_host,
            "port": qdrant_port,
        }

    if qdrant_api_key:
        return {
            "mode": "cloud",
            "url": f"https://{qdrant_host}",
            "api_key": qdrant_api_key,
            "host": qdrant_host,
            "port": qdrant_port,
        }

    return {
        "mode": "local",
        "url": None,
        "api_key": None,
        "host": qdrant_host,
        "port": qdrant_port,
    }


class QdrantService:
    """
    Manages Qdrant vector database connections and searches.

    Supports both local Qdrant instances and Qdrant Cloud.
    """

    def __init__(self) -> None:
        self.client: QdrantClient | None = None
        self._connected = False

    async def connect(self) -> None:
        """
        Connect to Qdrant.

        Uses QDRANT_API_KEY for cloud connections, otherwise connects locally.
        """
        try:
            config = _resolve_qdrant_connection()

            if config["mode"] == "url":
                logger.info(f"Connecting to Qdrant via QDRANT_URL at {config['url']}")
                self.client = QdrantClient(
                    url=config["url"],
                    api_key=config["api_key"],
                    check_compatibility=False,
                )
            elif config["mode"] == "cloud":
                # Cloud connection with API key and HTTPS
                logger.info(f"Connecting to Qdrant Cloud at {config['host']}")
                self.client = QdrantClient(
                    url=config["url"],
                    api_key=config["api_key"],
                    check_compatibility=False,
                )
            else:
                # Local connection with HTTP
                logger.info(
                    f"Connecting to local Qdrant at {config['host']}:{config['port']}"
                )
                self.client = QdrantClient(
                    host=config["host"],
                    port=config["port"],
                    check_compatibility=False,
                )

            # Verify connection
            collections = self.client.get_collections()
            self._connected = True
            logger.info(
                f"Connected to Qdrant - {len(collections.collections)} collections"
            )

        except Exception as e:
            self._connected = False
            self.client = None
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise

    async def close(self) -> None:
        """Close Qdrant connection."""
        if self.client:
            self.client.close()
            self.client = None
        self._connected = False
        logger.info("Qdrant connection closed")

    def is_connected(self) -> bool:
        """Check if Qdrant is connected."""
        return self._connected

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
            deduped: dict[str, dict[str, Any]] = {}

            def add_hits(search_result: Any) -> None:
                for hit in search_result:
                    payload = hit.payload or {}
                    key = str(payload.get("id") or payload.get("node_id") or hit.id)
                    if key in deduped:
                        continue
                    deduped[key] = {
                        "id": payload.get("id"),
                        "score": hit.score,
                        "payload": payload,
                    }

            # Prefer the production collection used by the Cloudflare worker.
            try:
                named_hits = self.client.search(
                    collection_name="kg_nodes_dual",
                    query_vector=models.NamedVector(name="gemini", vector=query_vector),
                    limit=limit,
                    score_threshold=score_threshold,
                )
                add_hits(named_hits)
            except Exception as dual_exc:
                logger.warning(f"Error searching kg_nodes_dual: {dual_exc}")

            if len(deduped) < limit:
                try:
                    legacy_hits = self.client.search(
                        collection_name="kg_nodes_gemini",
                        query_vector=query_vector,
                        limit=limit,
                        score_threshold=score_threshold,
                    )
                    add_hits(legacy_hits)
                except Exception as legacy_exc:
                    logger.warning(f"Error searching kg_nodes_gemini: {legacy_exc}")

            if len(deduped) < limit:
                try:
                    historical_hits = self.client.search(
                        collection_name="ancient_free_will_vectors",
                        query_vector=query_vector,
                        limit=limit * 3,
                        score_threshold=score_threshold,
                    )
                    filtered = [
                        hit for hit in historical_hits if (hit.payload or {}).get("node_id")
                    ]
                    add_hits(filtered)
                except Exception as historical_exc:
                    logger.warning(
                        f"Error searching ancient_free_will_vectors: {historical_exc}"
                    )

            return list(deduped.values())[:limit]

        except Exception as e:
            logger.error(f"Error searching KG node collections: {e}")
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
