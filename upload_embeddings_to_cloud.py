#!/usr/bin/env python3
"""
Upload Text Embeddings to Qdrant Cloud

This script uploads existing text embeddings from Supabase PostgreSQL
to Qdrant Cloud for production deployment.

Author: Romain Girardi
Date: 2025-10-18
"""

import asyncio
import logging
import os
import sys
from typing import Optional

import asyncpg
import numpy as np
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration from environment variables
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', 5432))
POSTGRES_DB = os.getenv('POSTGRES_DB', 'postgres')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', '')

QDRANT_HOST = os.getenv('QDRANT_HOST', 'localhost')
QDRANT_HTTP_PORT = int(os.getenv('QDRANT_HTTP_PORT', 6333))
QDRANT_API_KEY = os.getenv('QDRANT_API_KEY', None)

EMBEDDING_DIMENSIONS = int(os.getenv('EMBEDDING_DIMENSIONS', 3072))


class CloudEmbeddingsUploader:
    """Uploads text embeddings from Supabase to Qdrant Cloud."""

    def __init__(self):
        self.pg_conn: Optional[asyncpg.Connection] = None
        self.qdrant_client: Optional[QdrantClient] = None

    async def connect_postgres(self) -> None:
        """Connect to Supabase PostgreSQL."""
        try:
            # Add SSL for cloud databases like Supabase
            ssl_mode = os.getenv('POSTGRES_SSLMODE', 'require')

            self.pg_conn = await asyncpg.connect(
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                database=POSTGRES_DB,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
                ssl=ssl_mode,
                statement_cache_size=0  # Required for pgbouncer transaction mode
            )
            logger.info(f"✅ Connected to PostgreSQL at {POSTGRES_HOST}:{POSTGRES_PORT}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to PostgreSQL: {e}")
            raise

    def connect_qdrant(self) -> None:
        """Connect to Qdrant Cloud."""
        try:
            if QDRANT_API_KEY:
                # Cloud connection with API key
                self.qdrant_client = QdrantClient(
                    url=f"https://{QDRANT_HOST}:{QDRANT_HTTP_PORT}",
                    api_key=QDRANT_API_KEY
                )
            else:
                # Local connection
                self.qdrant_client = QdrantClient(
                    host=QDRANT_HOST,
                    port=QDRANT_HTTP_PORT
                )
            logger.info(f"✅ Connected to Qdrant at {QDRANT_HOST}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Qdrant: {e}")
            raise

    async def create_collection(self) -> None:
        """Create text_embeddings collection in Qdrant if it doesn't exist."""
        try:
            collections_info = self.qdrant_client.get_collections()
            existing_names = [c.name for c in collections_info.collections]

            if 'text_embeddings' in existing_names:
                logger.info("Collection 'text_embeddings' already exists - deleting and recreating...")
                self.qdrant_client.delete_collection('text_embeddings')
                logger.info("Deleted existing collection")

            # Create collection
            self.qdrant_client.create_collection(
                collection_name='text_embeddings',
                vectors_config=VectorParams(
                    size=EMBEDDING_DIMENSIONS,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"✅ Created collection 'text_embeddings' ({EMBEDDING_DIMENSIONS} dimensions, Cosine distance)")

        except Exception as e:
            logger.error(f"❌ Error creating collection: {e}")
            raise

    async def upload_embeddings(self) -> None:
        """Upload text embeddings from PostgreSQL to Qdrant."""
        logger.info("📤 Uploading text embeddings from PostgreSQL to Qdrant Cloud...")

        # Get text embeddings from PostgreSQL
        query = """
        SELECT id, title, author, category, language,
               LENGTH(COALESCE(raw_text, '')) as text_length,
               embedding, embedding_created_at
        FROM free_will.texts
        WHERE embedding IS NOT NULL
        ORDER BY id
        """

        rows = await self.pg_conn.fetch(query)
        logger.info(f"Found {len(rows)} texts with embeddings in PostgreSQL")

        if len(rows) == 0:
            logger.warning("⚠️  No embeddings found in PostgreSQL!")
            logger.warning("   Did you run the database setup script?")
            return

        points = []
        for idx, row in enumerate(rows):
            try:
                # Convert embedding bytes to list
                embedding_vector = np.frombuffer(row['embedding'], dtype=np.float32).tolist()

                # Create Qdrant point
                point = PointStruct(
                    id=idx,
                    vector=embedding_vector,
                    payload={
                        'text_id': str(row['id']),
                        'title': row['title'],
                        'author': row['author'],
                        'category': row['category'],
                        'language': row['language'],
                        'text_length': row['text_length'],
                        'generated_at': row['embedding_created_at'].timestamp() if row['embedding_created_at'] else None
                    }
                )
                points.append(point)

            except Exception as e:
                logger.error(f"❌ Error processing text {row['id']}: {e}")
                continue

        # Upload in batches
        batch_size = 100
        total_batches = (len(points) - 1) // batch_size + 1

        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            batch_num = i // batch_size + 1

            try:
                self.qdrant_client.upsert(
                    collection_name='text_embeddings',
                    points=batch
                )
                logger.info(f"✅ Uploaded batch {batch_num}/{total_batches} ({len(batch)} embeddings)")
            except Exception as e:
                logger.error(f"❌ Error uploading batch {batch_num}: {e}")
                continue

        logger.info(f"✅ Successfully uploaded {len(points)} text embeddings to Qdrant Cloud")

    async def verify_upload(self) -> None:
        """Verify embeddings were uploaded correctly."""
        logger.info("🔍 Verifying upload...")

        try:
            collection_info = self.qdrant_client.get_collection('text_embeddings')
            logger.info(f"✅ Collection 'text_embeddings': {collection_info.points_count} vectors")

            if collection_info.points_count > 0:
                logger.info("✅ Upload verification successful!")
            else:
                logger.warning("⚠️  Collection is empty!")

        except Exception as e:
            logger.error(f"❌ Verification failed: {e}")

    async def run(self) -> None:
        """Run the complete upload process."""
        logger.info("🚀 Starting Cloud Embeddings Upload")
        logger.info("=" * 80)
        logger.info(f"PostgreSQL: {POSTGRES_HOST}:{POSTGRES_PORT}")
        logger.info(f"Qdrant: {QDRANT_HOST}:{QDRANT_HTTP_PORT}")
        logger.info(f"Embedding dimensions: {EMBEDDING_DIMENSIONS}")
        logger.info("=" * 80)

        try:
            # Connect
            await self.connect_postgres()
            self.connect_qdrant()

            # Create collection
            await self.create_collection()

            # Upload embeddings
            await self.upload_embeddings()

            # Verify
            await self.verify_upload()

            logger.info("=" * 80)
            logger.info("🎉 CLOUD EMBEDDINGS UPLOAD SUCCESSFUL!")
            logger.info("=" * 80)

        except Exception as e:
            logger.error(f"❌ Upload failed: {e}")
            raise
        finally:
            # Cleanup
            if self.pg_conn:
                await self.pg_conn.close()
            if self.qdrant_client:
                self.qdrant_client.close()


async def main():
    """Main function."""
    uploader = CloudEmbeddingsUploader()
    await uploader.run()


if __name__ == "__main__":
    asyncio.run(main())
