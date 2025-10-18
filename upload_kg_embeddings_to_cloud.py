#!/usr/bin/env python3
"""
Upload Knowledge Graph Embeddings to Qdrant Cloud

This script uploads KG node and edge embeddings from kg_embeddings.json
to Qdrant Cloud for production deployment.

Author: Romain Girardi
Date: 2025-10-18
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Optional, List, Dict, Any

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from tqdm import tqdm

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration from environment variables
QDRANT_HOST = os.getenv('QDRANT_HOST')
QDRANT_API_KEY = os.getenv('QDRANT_API_KEY')
EMBEDDING_DIMENSIONS = int(os.getenv('EMBEDDING_DIMENSIONS', 3072))

# File path
KG_EMBEDDINGS_PATH = Path("kg_embeddings.json")


class KGEmbeddingsUploader:
    """Uploads KG embeddings from JSON to Qdrant Cloud."""

    def __init__(self):
        self.qdrant_client: Optional[QdrantClient] = None
        self.kg_embeddings: Optional[Dict[str, Any]] = None

    def connect_qdrant(self) -> None:
        """Connect to Qdrant Cloud."""
        try:
            if not QDRANT_HOST or not QDRANT_API_KEY:
                raise ValueError("QDRANT_HOST and QDRANT_API_KEY must be set in .env")

            # Cloud connection with API key
            self.qdrant_client = QdrantClient(
                url=f"https://{QDRANT_HOST}",
                api_key=QDRANT_API_KEY,
                check_compatibility=False
            )

            # Verify connection
            collections = self.qdrant_client.get_collections()
            logger.info(f"✅ Connected to Qdrant Cloud at {QDRANT_HOST}")
            logger.info(f"   Found {len(collections.collections)} existing collections")

        except Exception as e:
            logger.error(f"❌ Failed to connect to Qdrant: {e}")
            raise

    def load_kg_embeddings(self) -> Dict[str, Any]:
        """Load KG embeddings from JSON file."""
        try:
            if not KG_EMBEDDINGS_PATH.exists():
                raise FileNotFoundError(f"KG embeddings file not found: {KG_EMBEDDINGS_PATH}")

            logger.info(f"📖 Loading KG embeddings from {KG_EMBEDDINGS_PATH}...")
            with open(KG_EMBEDDINGS_PATH, 'r', encoding='utf-8') as f:
                embeddings_data = json.load(f)

            total_embeddings = embeddings_data.get('metadata', {}).get('total_embeddings', 0)
            logger.info(f"✅ Loaded {total_embeddings} embeddings")

            return embeddings_data

        except Exception as e:
            logger.error(f"❌ Error loading embeddings: {e}")
            raise

    def create_collection(self) -> None:
        """Create ancient_free_will_vectors collection in Qdrant if it doesn't exist."""
        try:
            collections_info = self.qdrant_client.get_collections()
            existing_names = [c.name for c in collections_info.collections]

            if 'ancient_free_will_vectors' in existing_names:
                logger.info("⚠️  Collection 'ancient_free_will_vectors' already exists")
                response = input("Do you want to DELETE and recreate it? (yes/no): ")
                if response.lower() == 'yes':
                    self.qdrant_client.delete_collection('ancient_free_will_vectors')
                    logger.info("🗑️  Deleted existing collection")
                else:
                    logger.info("Keeping existing collection - will upsert points")
                    return

            # Create collection
            self.qdrant_client.create_collection(
                collection_name='ancient_free_will_vectors',
                vectors_config=VectorParams(
                    size=EMBEDDING_DIMENSIONS,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"✅ Created collection 'ancient_free_will_vectors' ({EMBEDDING_DIMENSIONS}D, Cosine)")

        except Exception as e:
            logger.error(f"❌ Error creating collection: {e}")
            raise

    def upload_node_embeddings(self) -> int:
        """Upload KG node embeddings to Qdrant."""
        logger.info("\n🧠 Uploading KG node embeddings...")

        node_embeddings = self.kg_embeddings['embeddings']['nodes']
        logger.info(f"Found {len(node_embeddings)} node embeddings")

        points = []
        point_id = 0

        # Prepare points
        for node_id, embedding_data in tqdm(node_embeddings.items(), desc="Preparing nodes"):
            try:
                point = PointStruct(
                    id=point_id,
                    vector=embedding_data['embedding'],
                    payload={
                        'node_id': embedding_data['node_id'],
                        'node_type': embedding_data['node_type'],
                        'label': embedding_data['label'],
                        'text_representation': embedding_data['text_representation'],
                        'embedding_model': embedding_data.get('embedding_model'),
                        'embedding_dimensions': embedding_data.get('embedding_dimensions'),
                        'data_type': 'kg_node'  # Distinguish from edges
                    }
                )
                points.append(point)
                point_id += 1

            except Exception as e:
                logger.error(f"❌ Error preparing node {node_id}: {e}")
                continue

        # Upload in batches
        batch_size = 100
        total_batches = (len(points) - 1) // batch_size + 1

        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            batch_num = i // batch_size + 1

            try:
                self.qdrant_client.upsert(
                    collection_name='ancient_free_will_vectors',
                    points=batch
                )
                logger.info(f"✅ Uploaded node batch {batch_num}/{total_batches} ({len(batch)} nodes)")
            except Exception as e:
                logger.error(f"❌ Error uploading node batch {batch_num}: {e}")
                continue

        logger.info(f"✅ Successfully uploaded {len(points)} node embeddings")
        return len(points)

    def upload_edge_embeddings(self, start_id: int) -> int:
        """Upload KG edge embeddings to Qdrant."""
        logger.info("\n🔗 Uploading KG edge embeddings...")

        edge_embeddings = self.kg_embeddings['embeddings']['edges']
        logger.info(f"Found {len(edge_embeddings)} edge embeddings")

        points = []
        point_id = start_id

        # Prepare points
        for edge_id, embedding_data in tqdm(edge_embeddings.items(), desc="Preparing edges"):
            try:
                point = PointStruct(
                    id=point_id,
                    vector=embedding_data['embedding'],
                    payload={
                        'edge_id': embedding_data['edge_id'],
                        'source_id': embedding_data['source_id'],
                        'target_id': embedding_data['target_id'],
                        'relation': embedding_data['relation'],
                        'description': embedding_data.get('description', ''),
                        'text_representation': embedding_data['text_representation'],
                        'embedding_model': embedding_data.get('embedding_model'),
                        'embedding_dimensions': embedding_data.get('embedding_dimensions'),
                        'data_type': 'kg_edge'  # Distinguish from nodes
                    }
                )
                points.append(point)
                point_id += 1

            except Exception as e:
                logger.error(f"❌ Error preparing edge {edge_id}: {e}")
                continue

        # Upload in batches
        batch_size = 100
        total_batches = (len(points) - 1) // batch_size + 1

        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            batch_num = i // batch_size + 1

            try:
                self.qdrant_client.upsert(
                    collection_name='ancient_free_will_vectors',
                    points=batch
                )
                logger.info(f"✅ Uploaded edge batch {batch_num}/{total_batches} ({len(batch)} edges)")
            except Exception as e:
                logger.error(f"❌ Error uploading edge batch {batch_num}: {e}")
                continue

        logger.info(f"✅ Successfully uploaded {len(points)} edge embeddings")
        return len(points)

    def verify_upload(self) -> None:
        """Verify embeddings were uploaded correctly."""
        logger.info("\n🔍 Verifying upload...")

        try:
            collection_info = self.qdrant_client.get_collection('ancient_free_will_vectors')
            logger.info(f"✅ Collection 'ancient_free_will_vectors': {collection_info.points_count} vectors")

            if collection_info.points_count > 0:
                logger.info("✅ Upload verification successful!")
            else:
                logger.warning("⚠️  Collection is empty!")

        except Exception as e:
            logger.error(f"❌ Verification failed: {e}")

    def run(self) -> None:
        """Run the complete upload process."""
        logger.info("🚀 Starting KG Embeddings Upload to Qdrant Cloud")
        logger.info("=" * 80)
        logger.info(f"Qdrant: {QDRANT_HOST}")
        logger.info(f"Embedding dimensions: {EMBEDDING_DIMENSIONS}")
        logger.info("=" * 80)

        try:
            # Load embeddings
            self.kg_embeddings = self.load_kg_embeddings()

            # Connect to Qdrant
            self.connect_qdrant()

            # Create collection
            self.create_collection()

            # Upload embeddings
            nodes_uploaded = self.upload_node_embeddings()
            edges_uploaded = self.upload_edge_embeddings(start_id=nodes_uploaded)

            # Verify
            self.verify_upload()

            # Success summary
            logger.info("=" * 80)
            logger.info("🎉 KG EMBEDDINGS UPLOAD SUCCESSFUL!")
            logger.info("=" * 80)
            logger.info(f"📊 Node embeddings uploaded: {nodes_uploaded}")
            logger.info(f"📊 Edge embeddings uploaded: {edges_uploaded}")
            logger.info(f"📊 Total vectors: {nodes_uploaded + edges_uploaded}")
            logger.info("=" * 80)
            logger.info("✅ GraphRAG is now ready to use!")
            logger.info("=" * 80)

        except Exception as e:
            logger.error(f"❌ Upload failed: {e}")
            raise
        finally:
            # Cleanup
            if self.qdrant_client:
                self.qdrant_client.close()


def main():
    """Main function."""
    uploader = KGEmbeddingsUploader()
    uploader.run()


if __name__ == "__main__":
    main()
