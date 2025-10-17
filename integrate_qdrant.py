#!/usr/bin/env python3
"""
Qdrant Integration for Ancient Free Will Database

This script integrates Qdrant vector database with our Ancient Free Will Database,
adapting the proven Sematika MVP implementation for our multi-modal system.

Features:
- Knowledge Graph embeddings (465 nodes + 745 edges)
- Text embeddings (289 texts with 3072 dimensions)
- Cross-modal semantic search
- HNSW optimization for maximum performance

Author: Romain Girardi
Date: 2025-01-17
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

import asyncpg
import numpy as np
from qdrant_service import AncientFreeWillQdrantService

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


class QdrantIntegration:
    """Integrates Qdrant vector database with Ancient Free Will Database."""
    
    def __init__(self):
        self.pg_conn: Optional[asyncpg.Connection] = None
        self.qdrant_service: Optional[AncientFreeWillQdrantService] = None
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
            
            # Initialize Qdrant service
            self.qdrant_service = AncientFreeWillQdrantService(
                collection_name="ancient_free_will_vectors",
                vector_size=3072
            )
            await self.qdrant_service.initialize()
            logger.info("Connected to Qdrant vector database")
            
        except Exception as e:
            logger.error(f"Failed to connect to databases: {e}")
            raise
            
    async def close(self) -> None:
        """Close database connections."""
        if self.pg_conn:
            await self.pg_conn.close()
        if self.qdrant_service:
            await self.qdrant_service.close()
        logger.info("Disconnected from databases")
        
    def load_kg_embeddings(self) -> Dict:
        """Load Knowledge Graph embeddings from JSON file."""
        logger.info("Loading Knowledge Graph embeddings...")
        
        if not KG_EMBEDDINGS_PATH.exists():
            logger.error(f"KG embeddings file not found: {KG_EMBEDDINGS_PATH}")
            raise FileNotFoundError("KG embeddings file not found. Run generate_kg_embeddings.py first.")
            
        with open(KG_EMBEDDINGS_PATH, 'r', encoding='utf-8') as f:
            embeddings_data = json.load(f)
            
        logger.info(f"Loaded KG embeddings: {embeddings_data['metadata']['total_embeddings']} embeddings")
        return embeddings_data
        
    async def upload_knowledge_graph_embeddings(self) -> None:
        """Upload Knowledge Graph embeddings to Qdrant."""
        logger.info("🧠 Uploading Knowledge Graph embeddings to Qdrant...")
        
        if not self.kg_embeddings:
            self.kg_embeddings = self.load_kg_embeddings()
            
        # Upload node embeddings
        node_embeddings = self.kg_embeddings['embeddings']['nodes']
        logger.info(f"Uploading {len(node_embeddings)} KG node embeddings...")
        
        uploaded_nodes = 0
        for node_id, embedding_data in node_embeddings.items():
            try:
                success = await self.qdrant_service.add_knowledge_graph_node(
                    node_id=embedding_data['node_id'],
                    embedding=embedding_data['embedding'],
                    node_type=embedding_data['node_type'],
                    label=embedding_data['label'],
                    text_representation=embedding_data['text_representation'],
                    metadata={
                        'generated_at': embedding_data['generated_at'],
                        'embedding_model': embedding_data['embedding_model'],
                        'embedding_dimensions': embedding_data['embedding_dimensions']
                    }
                )
                
                if success:
                    uploaded_nodes += 1
                    
                if uploaded_nodes % 50 == 0:
                    logger.info(f"Uploaded {uploaded_nodes}/{len(node_embeddings)} KG node embeddings...")
                    
            except Exception as e:
                logger.error(f"Error uploading KG node {node_id}: {e}")
                continue
                
        logger.info(f"✅ Successfully uploaded {uploaded_nodes} KG node embeddings")
        
        # Upload edge embeddings
        edge_embeddings = self.kg_embeddings['embeddings']['edges']
        logger.info(f"Uploading {len(edge_embeddings)} KG edge embeddings...")
        
        uploaded_edges = 0
        for edge_id, embedding_data in edge_embeddings.items():
            try:
                success = await self.qdrant_service.add_knowledge_graph_edge(
                    edge_id=embedding_data['edge_id'],
                    embedding=embedding_data['embedding'],
                    source_id=embedding_data['source_id'],
                    target_id=embedding_data['target_id'],
                    relation=embedding_data['relation'],
                    description=embedding_data['description'],
                    text_representation=embedding_data['text_representation'],
                    metadata={
                        'generated_at': embedding_data['generated_at'],
                        'embedding_model': embedding_data['embedding_model'],
                        'embedding_dimensions': embedding_data['embedding_dimensions']
                    }
                )
                
                if success:
                    uploaded_edges += 1
                    
                if uploaded_edges % 50 == 0:
                    logger.info(f"Uploaded {uploaded_edges}/{len(edge_embeddings)} KG edge embeddings...")
                    
            except Exception as e:
                logger.error(f"Error uploading KG edge {edge_id}: {e}")
                continue
                
        logger.info(f"✅ Successfully uploaded {uploaded_edges} KG edge embeddings")
        
    async def upload_text_embeddings(self) -> None:
        """Upload text embeddings from PostgreSQL to Qdrant."""
        logger.info("📚 Uploading text embeddings from PostgreSQL to Qdrant...")
        
        # Get text embeddings from PostgreSQL
        query = """
        SELECT id, title, author, category, language, LENGTH(raw_text) as text_length, 
               embedding, embedding_created_at
        FROM free_will.texts
        WHERE embedding IS NOT NULL
        ORDER BY id
        """
        
        rows = await self.pg_conn.fetch(query)
        logger.info(f"Found {len(rows)} texts with embeddings in PostgreSQL")
        
        uploaded_texts = 0
        for row in rows:
            try:
                # Convert embedding bytes back to numpy array
                embedding_vector = np.frombuffer(row['embedding'], dtype=np.float32).tolist()
                
                success = await self.qdrant_service.add_text_embedding(
                    text_id=str(row['id']),
                    embedding=embedding_vector,
                    title=row['title'],
                    author=row['author'],
                    category=row['category'],
                    language=row['language'],
                    text_length=row['text_length'],
                    metadata={
                        'generated_at': row['embedding_created_at'].timestamp() if row['embedding_created_at'] else None,
                        'source': 'postgresql'
                    }
                )
                
                if success:
                    uploaded_texts += 1
                    
                if uploaded_texts % 50 == 0:
                    logger.info(f"Uploaded {uploaded_texts}/{len(rows)} text embeddings...")
                    
            except Exception as e:
                logger.error(f"Error uploading text {row['id']}: {e}")
                continue
                
        logger.info(f"✅ Successfully uploaded {uploaded_texts} text embeddings")
        
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
            
            try:
                # Generate a random query embedding for demo (would use actual embedding in production)
                query_embedding = np.random.random(3072).tolist()
                
                # Cross-modal search
                results = await self.qdrant_service.search_cross_modal(
                    query_embedding=query_embedding,
                    top_k=5,
                    min_score=0.0
                )
                
                # Display results
                for modality, modality_results in results.items():
                    logger.info(f"  📊 {modality}: {len(modality_results)} results")
                    for i, result in enumerate(modality_results[:3], 1):
                        score = result['score']
                        metadata = result['metadata']
                        label = metadata.get('label', metadata.get('title', 'Unknown'))
                        logger.info(f"    {i}. Score: {score:.3f} - {label}")
                        
            except Exception as e:
                logger.error(f"Error testing query '{query}': {e}")
                
    async def run_integration(self) -> None:
        """Run the complete Qdrant integration process."""
        logger.info("🚀 Starting Qdrant Integration for Ancient Free Will Database")
        logger.info("=" * 80)
        
        try:
            # Load KG embeddings
            self.kg_embeddings = self.load_kg_embeddings()
            
            # Upload embeddings to Qdrant
            await self.upload_knowledge_graph_embeddings()
            await self.upload_text_embeddings()
            
            # Demonstrate capabilities
            await self.demonstrate_qdrant_capabilities()
            
            # Get final statistics
            stats = await self.qdrant_service.get_stats()
            
            # Success summary
            logger.info("=" * 80)
            logger.info("✅ QDRANT INTEGRATION COMPLETED SUCCESSFULLY!")
            logger.info("=" * 80)
            logger.info(f"📊 Total vectors: {stats.get('total_vectors', 0)}")
            logger.info(f"🧠 Knowledge Graph nodes: {stats.get('knowledge_graph_nodes', 0)}")
            logger.info(f"🔗 Knowledge Graph edges: {stats.get('knowledge_graph_edges', 0)}")
            logger.info(f"📚 Text embeddings: {stats.get('text_embeddings', 0)}")
            logger.info(f"🎯 Vector dimensions: {stats.get('vector_size', 0)}")
            logger.info("=" * 80)
            logger.info("🚀 ELEUTHERIA - The Ancient Free Will Database:")
            logger.info("   Now with Qdrant Vector Database for maximum performance!")
            logger.info("   • HNSW indexing optimized for 3072-dimensional embeddings")
            logger.info("   • Cross-modal semantic search across KG and texts")
            logger.info("   • Production-grade vector database performance")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"Qdrant integration failed: {e}")
            raise


async def main():
    """Main function to run the Qdrant integration."""
    async with QdrantIntegration() as integration:
        await integration.run_integration()


if __name__ == "__main__":
    asyncio.run(main())

