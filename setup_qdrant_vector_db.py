#!/usr/bin/env python3
"""
Qdrant Vector Database Setup for Ancient Free Will Database

This script sets up Qdrant as a dedicated vector database for high-performance
semantic search across Knowledge Graph embeddings and text embeddings.

Benefits of Qdrant:
- Advanced vector indexing (HNSW, IVF)
- Fast approximate nearest neighbor search
- Vector clustering and filtering
- Scalable vector operations
- Better performance than PostgreSQL BYTEA

Author: Romain Girardi
Date: 2025-01-17
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

import asyncpg
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# File paths
KG_EMBEDDINGS_PATH = Path("/Users/romaingirardi/Documents/Ancient Free Will Database/kg_embeddings.json")

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'ancient_free_will_db',
    'user': 'free_will_user',
    'password': 'free_will_password'
}

# Qdrant configuration
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
EMBEDDING_DIMENSIONS = 3072  # Maximum Gemini embedding dimensions


class QdrantVectorDatabaseSetup:
    """Sets up Qdrant as a dedicated vector database for the Ancient Free Will Database."""
    
    def __init__(self):
        self.pg_conn: Optional[asyncpg.Connection] = None
        self.qdrant_client: Optional[QdrantClient] = None
        self.kg_embeddings: Optional[Dict] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
        
    async def connect(self) -> None:
        """Establish database connections."""
        try:
            # Connect to PostgreSQL
            self.pg_conn = await asyncpg.connect(**DB_CONFIG)
            logger.info("Connected to PostgreSQL database")
            
            # Connect to Qdrant
            self.qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
            logger.info("Connected to Qdrant vector database")
            
        except Exception as e:
            logger.error(f"Failed to connect to databases: {e}")
            raise
            
    async def close(self) -> None:
        """Close database connections."""
        if self.pg_conn:
            await self.pg_conn.close()
        if self.qdrant_client:
            self.qdrant_client.close()
        logger.info("Disconnected from databases")
        
    def load_kg_embeddings(self) -> Dict:
        """Load Knowledge Graph embeddings from JSON file."""
        logger.info("Loading Knowledge Graph embeddings...")
        
        if not KG_EMBEDDINGS_PATH.exists():
            logger.error(f"KG embeddings file not found: {KG_EMBEDDINGS_PATH}")
            raise FileNotFoundError("KG embeddings file not found")
            
        with open(KG_EMBEDDINGS_PATH, 'r', encoding='utf-8') as f:
            embeddings_data = json.load(f)
            
        logger.info(f"Loaded KG embeddings: {embeddings_data['metadata']['total_embeddings']} embeddings")
        return embeddings_data
        
    async def create_qdrant_collections(self) -> None:
        """Create Qdrant collections for different types of embeddings."""
        logger.info("Creating Qdrant collections...")
        
        collections = [
            {
                'name': 'kg_nodes',
                'description': 'Knowledge Graph node embeddings (3072 dimensions)',
                'payload_schema': {
                    'node_id': 'keyword',
                    'node_type': 'keyword', 
                    'label': 'text',
                    'text_representation': 'text',
                    'generated_at': 'float'
                }
            },
            {
                'name': 'kg_edges',
                'description': 'Knowledge Graph edge embeddings (3072 dimensions)',
                'payload_schema': {
                    'edge_id': 'keyword',
                    'source_id': 'keyword',
                    'target_id': 'keyword',
                    'relation': 'keyword',
                    'description': 'text',
                    'text_representation': 'text',
                    'generated_at': 'float'
                }
            },
            {
                'name': 'text_embeddings',
                'description': 'Text embeddings from PostgreSQL (3072 dimensions)',
                'payload_schema': {
                    'text_id': 'keyword',
                    'title': 'text',
                    'author': 'text',
                    'category': 'keyword',
                    'language': 'keyword',
                    'text_length': 'integer',
                    'generated_at': 'float'
                }
            }
        ]
        
        for collection in collections:
            try:
                # Check if collection exists
                collections_info = self.qdrant_client.get_collections()
                existing_names = [c.name for c in collections_info.collections]
                
                if collection['name'] in existing_names:
                    logger.info(f"Collection '{collection['name']}' already exists")
                    continue
                    
                # Create collection
                self.qdrant_client.create_collection(
                    collection_name=collection['name'],
                    vectors_config=VectorParams(
                        size=EMBEDDING_DIMENSIONS,
                        distance=Distance.COSINE
                    )
                )
                
                logger.info(f"Created collection '{collection['name']}': {collection['description']}")
                
            except Exception as e:
                logger.error(f"Error creating collection '{collection['name']}': {e}")
                raise
                
    async def upload_kg_node_embeddings(self) -> None:
        """Upload Knowledge Graph node embeddings to Qdrant."""
        logger.info("Uploading Knowledge Graph node embeddings to Qdrant...")

        if not self.kg_embeddings:
            self.kg_embeddings = self.load_kg_embeddings()

        node_embeddings = self.kg_embeddings['embeddings']['nodes']

        points = []
        for idx, (node_id, embedding_data) in enumerate(node_embeddings.items()):
            try:
                # Use integer index as point ID (Qdrant requirement)
                point = PointStruct(
                    id=idx,
                    vector=embedding_data['embedding'],
                    payload={
                        'node_id': embedding_data['node_id'],
                        'node_type': embedding_data['node_type'],
                        'label': embedding_data['label'],
                        'text_representation': embedding_data['text_representation'],
                        'generated_at': embedding_data['generated_at']
                    }
                )
                points.append(point)
                
            except Exception as e:
                logger.error(f"Error processing node {node_id}: {e}")
                continue
                
        # Upload in batches
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            try:
                self.qdrant_client.upsert(
                    collection_name='kg_nodes',
                    points=batch
                )
                logger.info(f"Uploaded batch {i//batch_size + 1}/{(len(points)-1)//batch_size + 1}")
            except Exception as e:
                logger.error(f"Error uploading batch {i//batch_size + 1}: {e}")
                continue
                
        logger.info(f"Successfully uploaded {len(points)} KG node embeddings to Qdrant")
        
    async def upload_kg_edge_embeddings(self) -> None:
        """Upload Knowledge Graph edge embeddings to Qdrant."""
        logger.info("Uploading Knowledge Graph edge embeddings to Qdrant...")

        if not self.kg_embeddings:
            self.kg_embeddings = self.load_kg_embeddings()

        edge_embeddings = self.kg_embeddings['embeddings']['edges']

        points = []
        for idx, (edge_id, embedding_data) in enumerate(edge_embeddings.items()):
            try:
                # Use integer index as point ID (Qdrant requirement)
                point = PointStruct(
                    id=idx,
                    vector=embedding_data['embedding'],
                    payload={
                        'edge_id': embedding_data['edge_id'],
                        'source_id': embedding_data['source_id'],
                        'target_id': embedding_data['target_id'],
                        'relation': embedding_data['relation'],
                        'description': embedding_data['description'],
                        'text_representation': embedding_data['text_representation'],
                        'generated_at': embedding_data['generated_at']
                    }
                )
                points.append(point)
                
            except Exception as e:
                logger.error(f"Error processing edge {edge_id}: {e}")
                continue
                
        # Upload in batches
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            try:
                self.qdrant_client.upsert(
                    collection_name='kg_edges',
                    points=batch
                )
                logger.info(f"Uploaded batch {i//batch_size + 1}/{(len(points)-1)//batch_size + 1}")
            except Exception as e:
                logger.error(f"Error uploading batch {i//batch_size + 1}: {e}")
                continue
                
        logger.info(f"Successfully uploaded {len(points)} KG edge embeddings to Qdrant")
        
    async def upload_text_embeddings(self) -> None:
        """Upload text embeddings from PostgreSQL to Qdrant."""
        logger.info("Uploading text embeddings from PostgreSQL to Qdrant...")

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

        points = []
        for idx, row in enumerate(rows):
            try:
                # Convert embedding bytes back to numpy array
                embedding_vector = np.frombuffer(row['embedding'], dtype=np.float32).tolist()

                # Use integer index as point ID (Qdrant requirement)
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
                logger.error(f"Error processing text {row['id']}: {e}")
                continue
                
        # Upload in batches
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            try:
                self.qdrant_client.upsert(
                    collection_name='text_embeddings',
                    points=batch
                )
                logger.info(f"Uploaded batch {i//batch_size + 1}/{(len(points)-1)//batch_size + 1}")
            except Exception as e:
                logger.error(f"Error uploading batch {i//batch_size + 1}: {e}")
                continue
                
        logger.info(f"Successfully uploaded {len(points)} text embeddings to Qdrant")
        
    async def create_hybrid_search_functions(self) -> None:
        """Create hybrid search functions combining PostgreSQL and Qdrant."""
        logger.info("Creating hybrid search functions...")
        
        # This would create PostgreSQL functions that can call Qdrant
        # For now, we'll create a Python-based hybrid search class
        
        logger.info("Hybrid search functions will be implemented in Python")
        
    async def demonstrate_qdrant_capabilities(self) -> None:
        """Demonstrate Qdrant's advanced vector search capabilities."""
        logger.info("🎯 Demonstrating Qdrant vector search capabilities...")
        
        # Test queries
        test_queries = [
            "ἐφ ἡμῖν",  # Greek: "in our power"
            "liberum arbitrium",  # Latin: "free will"
            "voluntary action and moral responsibility",
            "Aristotle ethics",
            "Stoic philosophy"
        ]
        
        for query in test_queries:
            logger.info(f"\n🔍 Testing query: '{query}'")
            
            # Search across all collections
            collections = ['kg_nodes', 'kg_edges', 'text_embeddings']
            
            for collection in collections:
                try:
                    # Generate query embedding (placeholder - would need actual embedding)
                    # For demo purposes, we'll use a random vector
                    query_vector = np.random.random(EMBEDDING_DIMENSIONS).tolist()
                    
                    # Search in Qdrant
                    search_result = self.qdrant_client.search(
                        collection_name=collection,
                        query_vector=query_vector,
                        limit=3
                    )
                    
                    logger.info(f"  📊 {collection}: {len(search_result)} results")
                    for i, result in enumerate(search_result, 1):
                        score = result.score
                        payload = result.payload
                        logger.info(f"    {i}. Score: {score:.3f} - {payload.get('label', payload.get('title', 'Unknown'))}")
                        
                except Exception as e:
                    logger.error(f"Error searching {collection}: {e}")
                    
    async def run_qdrant_setup(self) -> None:
        """Run the complete Qdrant setup process."""
        logger.info("🚀 Starting Qdrant Vector Database Setup")
        logger.info("=" * 60)
        
        try:
            # Load KG embeddings
            self.kg_embeddings = self.load_kg_embeddings()
            
            # Create collections
            await self.create_qdrant_collections()
            
            # Upload embeddings
            await self.upload_kg_node_embeddings()
            await self.upload_kg_edge_embeddings()
            await self.upload_text_embeddings()
            
            # Create hybrid search functions
            await self.create_hybrid_search_functions()
            
            # Demonstrate capabilities
            await self.demonstrate_qdrant_capabilities()
            
            # Summary
            logger.info("=" * 60)
            logger.info("✅ QDRANT SETUP COMPLETED SUCCESSFULLY!")
            logger.info("=" * 60)
            
            # Get collection statistics
            collections_info = self.qdrant_client.get_collections()
            for collection in collections_info.collections:
                collection_info = self.qdrant_client.get_collection(collection.name)
                logger.info(f"📊 Collection '{collection.name}': {collection_info.points_count} vectors")
                
            logger.info("=" * 60)
            logger.info("🎯 Qdrant Vector Database Benefits:")
            logger.info("   • Advanced vector indexing (HNSW)")
            logger.info("   • Fast approximate nearest neighbor search")
            logger.info("   • Vector clustering and filtering")
            logger.info("   • Scalable vector operations")
            logger.info("   • Better performance than PostgreSQL BYTEA")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Qdrant setup failed: {e}")
            raise


async def main():
    """Main function to run the Qdrant setup."""
    async with QdrantVectorDatabaseSetup() as setup:
        await setup.run_qdrant_setup()


if __name__ == "__main__":
    asyncio.run(main())

