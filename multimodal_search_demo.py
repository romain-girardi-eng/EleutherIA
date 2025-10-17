#!/usr/bin/env python3
"""
Comprehensive Multi-Modal Semantic Search Demo for Ancient Free Will Database

This script demonstrates the complete multi-modal search capabilities:
1. Knowledge Graph semantic search (GraphRAG)
2. PostgreSQL full-text search with linguistic analysis
3. Vector Database semantic search with Gemini embeddings
4. Cross-modal similarity and integration

Author: Romain Girardi
Date: 2025-01-17
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import asyncpg
import numpy as np
import google.generativeai as genai

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# File paths
KG_PATH = Path("/Users/romaingirardi/Documents/Ancient Free Will Database/ancient_free_will_database.json")
KG_EMBEDDINGS_PATH = Path("/Users/romaingirardi/Documents/Ancient Free Will Database/kg_embeddings.json")

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'ancient_free_will_db',
    'user': 'free_will_user',
    'password': 'free_will_password'
}

# Gemini configuration
GEMINI_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSIONS = 3072  # Maximum Gemini embedding dimensions


class MultiModalSemanticSearch:
    """Comprehensive multi-modal semantic search across KG, PostgreSQL, and Vector DB."""
    
    def __init__(self):
        self.conn: Optional[asyncpg.Connection] = None
        self.kg_data: Optional[Dict] = None
        self.kg_embeddings: Optional[Dict] = None
        self.genai_client = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
        
    async def connect(self) -> None:
        """Establish database connection."""
        try:
            self.conn = await asyncpg.connect(**DB_CONFIG)
            logger.info("Connected to Ancient Free Will Database")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
            
    async def close(self) -> None:
        """Close database connection."""
        if self.conn:
            await self.conn.close()
            logger.info("Disconnected from database")
            
    def load_knowledge_graph(self) -> Dict:
        """Load Knowledge Graph data."""
        logger.info("Loading Knowledge Graph...")
        
        with open(KG_PATH, 'r', encoding='utf-8') as f:
            kg_data = json.load(f)
            
        logger.info(f"Loaded KG: {len(kg_data.get('nodes', []))} nodes, {len(kg_data.get('edges', []))} edges")
        return kg_data
        
    def load_kg_embeddings(self) -> Dict:
        """Load Knowledge Graph embeddings."""
        logger.info("Loading Knowledge Graph embeddings...")
        
        if not KG_EMBEDDINGS_PATH.exists():
            logger.warning("KG embeddings file not found. Run generate_kg_embeddings.py first.")
            return {}
            
        with open(KG_EMBEDDINGS_PATH, 'r', encoding='utf-8') as f:
            embeddings_data = json.load(f)
            
        logger.info(f"Loaded KG embeddings: {embeddings_data['metadata']['total_embeddings']} embeddings")
        return embeddings_data
        
    def configure_gemini(self) -> None:
        """Configure Gemini API for embedding generation."""
        try:
            import os
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                logger.warning("Gemini API key not found. Semantic search will be limited.")
                return
                
            genai.configure(api_key=api_key)
            self.genai_client = genai.GenerativeModel('gemini-pro')
            logger.info("Gemini API configured successfully")
        except Exception as e:
            logger.warning(f"Failed to configure Gemini: {e}")
            
    def generate_query_embedding(self, query_text: str) -> Optional[List[float]]:
        """Generate embedding for query text."""
        if not self.genai_client:
            return None
            
        try:
            result = genai.embed_content(
                model=GEMINI_MODEL,
                content=query_text,
                task_type="retrieval_query",
                output_dimensionality=3072
            )
            return result['embedding']
        except Exception as e:
            logger.error(f"Error generating query embedding: {e}")
            return None
            
    async def kg_semantic_search(self, query_text: str, node_type: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Search Knowledge Graph using semantic similarity."""
        logger.info(f"🔍 Knowledge Graph semantic search: '{query_text}'")
        
        # Generate query embedding
        query_embedding = self.generate_query_embedding(query_text)
        if not query_embedding:
            logger.warning("Could not generate query embedding. Using text similarity.")
            # Fallback to text similarity
            return await self.kg_text_similarity_search(query_text, node_type, limit)
            
        # Get node embeddings from database
        query = """
        SELECT node_id, node_type, label, text_representation, embedding
        FROM free_will.kg_node_embeddings
        WHERE ($1::TEXT IS NULL OR node_type = $1)
        ORDER BY node_id
        """
        
        rows = await self.conn.fetch(query, node_type)
        
        similarities = []
        query_vector = np.array(query_embedding, dtype=np.float32)
        
        for row in rows:
            # Convert embedding bytes back to numpy array
            node_vector = np.frombuffer(row['embedding'], dtype=np.float32)
            
            # Calculate cosine similarity
            similarity = np.dot(query_vector, node_vector) / (
                np.linalg.norm(query_vector) * np.linalg.norm(node_vector)
            )
            
            similarities.append({
                'node_id': row['node_id'],
                'node_type': row['node_type'],
                'label': row['label'],
                'text_representation': row['text_representation'],
                'similarity': float(similarity),
                'source': 'kg_semantic'
            })
            
        # Sort by similarity and return top results
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return similarities[:limit]
        
    async def kg_text_similarity_search(self, query_text: str, node_type: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Fallback text similarity search for Knowledge Graph."""
        query = """
        SELECT node_id, node_type, label, text_representation,
               similarity(text_representation, $1) as similarity
        FROM free_will.kg_node_embeddings
        WHERE ($2::TEXT IS NULL OR node_type = $2)
        AND similarity(text_representation, $1) > 0.1
        ORDER BY similarity DESC
        LIMIT $3
        """
        
        rows = await self.conn.fetch(query, query_text, node_type, limit)
        
        return [{
            'node_id': row['node_id'],
            'node_type': row['node_type'],
            'label': row['label'],
            'text_representation': row['text_representation'],
            'similarity': float(row['similarity']),
            'source': 'kg_text_similarity'
        } for row in rows]
        
    async def postgresql_fulltext_search(self, query_text: str, language: str = 'greek', limit: int = 10) -> List[Dict]:
        """Search PostgreSQL database using full-text search."""
        logger.info(f"🗄️ PostgreSQL full-text search: '{query_text}' (language: {language})")
        
        query = """
        SELECT id, title, author, category, language, LENGTH(raw_text) as text_length,
               ts_headline($1, raw_text, plainto_tsquery($1, $2)) as snippet,
               ts_rank(to_tsvector($1, raw_text), plainto_tsquery($1, $2)) as rank
        FROM free_will.texts
        WHERE to_tsvector($1, raw_text) @@ plainto_tsquery($1, $2)
        ORDER BY rank DESC
        LIMIT $3
        """
        
        rows = await self.conn.fetch(query, language, query_text, limit)
        
        return [{
            'id': row['id'],
            'title': row['title'],
            'author': row['author'],
            'category': row['category'],
            'language': row['language'],
            'text_length': row['text_length'],
            'snippet': row['snippet'],
            'rank': float(row['rank']),
            'source': 'postgresql_fts'
        } for row in rows]
        
    async def vector_db_semantic_search(self, query_text: str, limit: int = 10) -> List[Dict]:
        """Search Vector Database using semantic similarity."""
        logger.info(f"🔍 Vector Database semantic search: '{query_text}'")
        
        # Generate query embedding
        query_embedding = self.generate_query_embedding(query_text)
        if not query_embedding:
            logger.warning("Could not generate query embedding for vector search.")
            return []
            
        # Get text embeddings from database
        query = """
        SELECT id, title, author, category, language, LENGTH(raw_text) as text_length, embedding
        FROM free_will.texts
        WHERE embedding IS NOT NULL
        ORDER BY id
        """
        
        rows = await self.conn.fetch(query)
        
        similarities = []
        query_vector = np.array(query_embedding, dtype=np.float32)
        
        for row in rows:
            # Convert embedding bytes back to numpy array
            text_vector = np.frombuffer(row['embedding'], dtype=np.float32)
            
            # Calculate cosine similarity
            similarity = np.dot(query_vector, text_vector) / (
                np.linalg.norm(query_vector) * np.linalg.norm(text_vector)
            )
            
            similarities.append({
                'id': row['id'],
                'title': row['title'],
                'author': row['author'],
                'category': row['category'],
                'language': row['language'],
                'text_length': row['text_length'],
                'similarity': float(similarity),
                'source': 'vector_db_semantic'
            })
            
        # Sort by similarity and return top results
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return similarities[:limit]
        
    async def cross_modal_search(self, query_text: str, limit: int = 10) -> Dict[str, List[Dict]]:
        """Perform cross-modal search across all three systems."""
        logger.info(f"🔄 Cross-modal search: '{query_text}'")
        
        results = {}
        
        # Knowledge Graph semantic search
        results['knowledge_graph'] = await self.kg_semantic_search(query_text, limit=limit)
        
        # PostgreSQL full-text search (Greek)
        results['postgresql_greek'] = await self.postgresql_fulltext_search(query_text, 'greek', limit)
        
        # PostgreSQL full-text search (Latin)
        results['postgresql_latin'] = await self.postgresql_fulltext_search(query_text, 'latin', limit)
        
        # Vector Database semantic search
        results['vector_database'] = await self.vector_db_semantic_search(query_text, limit)
        
        return results
        
    async def demonstrate_search_capabilities(self) -> None:
        """Demonstrate comprehensive search capabilities."""
        logger.info("🚀 MULTI-MODAL SEMANTIC SEARCH DEMONSTRATION")
        logger.info("=" * 80)
        
        # Load data
        self.kg_data = self.load_knowledge_graph()
        self.kg_embeddings = self.load_kg_embeddings()
        self.configure_gemini()
        
        # Test queries
        test_queries = [
            "ἐφ ἡμῖν",  # Greek: "in our power"
            "liberum arbitrium",  # Latin: "free will"
            "voluntary action and moral responsibility",
            "fate and determinism",
            "Aristotle ethics",
            "Stoic philosophy",
            "Christian free will"
        ]
        
        for i, query in enumerate(test_queries, 1):
            logger.info(f"\n🔍 TEST QUERY {i}: '{query}'")
            logger.info("-" * 60)
            
            try:
                # Perform cross-modal search
                results = await self.cross_modal_search(query, limit=5)
                
                # Display results
                for modality, modality_results in results.items():
                    logger.info(f"\n📊 {modality.upper()} RESULTS ({len(modality_results)} found):")
                    
                    for j, result in enumerate(modality_results, 1):
                        if 'similarity' in result:
                            logger.info(f"  {j}. {result.get('label', result.get('title', 'Unknown'))} "
                                      f"(similarity: {result['similarity']:.3f})")
                        elif 'rank' in result:
                            logger.info(f"  {j}. {result.get('title', 'Unknown')} "
                                      f"(rank: {result['rank']:.3f})")
                        else:
                            logger.info(f"  {j}. {result.get('label', result.get('title', 'Unknown'))}")
                            
                        # Show snippet or text representation
                        if 'snippet' in result and result['snippet']:
                            snippet = result['snippet'][:100] + "..." if len(result['snippet']) > 100 else result['snippet']
                            logger.info(f"     Snippet: {snippet}")
                        elif 'text_representation' in result:
                            text_repr = result['text_representation'][:100] + "..." if len(result['text_representation']) > 100 else result['text_representation']
                            logger.info(f"     Description: {text_repr}")
                            
            except Exception as e:
                logger.error(f"Error processing query '{query}': {e}")
                
        logger.info("\n" + "=" * 80)
        logger.info("✅ MULTI-MODAL SEARCH DEMONSTRATION COMPLETED")
        logger.info("=" * 80)
        
    async def get_system_statistics(self) -> Dict:
        """Get comprehensive system statistics."""
        logger.info("📊 Gathering system statistics...")
        
        stats = {}
        
        # Knowledge Graph statistics
        if self.kg_data:
            stats['knowledge_graph'] = {
                'total_nodes': len(self.kg_data.get('nodes', [])),
                'total_edges': len(self.kg_data.get('edges', [])),
                'node_types': {}
            }
            
            # Count node types
            for node in self.kg_data.get('nodes', []):
                node_type = node.get('type', 'unknown')
                stats['knowledge_graph']['node_types'][node_type] = \
                    stats['knowledge_graph']['node_types'].get(node_type, 0) + 1
                    
        # Database statistics
        db_stats = await self.conn.fetch("""
            SELECT 
                COUNT(*) as total_texts,
                COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) as texts_with_embeddings,
                COUNT(CASE WHEN lemmas IS NOT NULL THEN 1 END) as texts_with_lemmas,
                SUM(LENGTH(raw_text)) as total_characters,
                COUNT(DISTINCT language) as languages,
                COUNT(DISTINCT category) as categories
            FROM free_will.texts
        """)
        
        stats['postgresql'] = dict(db_stats[0])
        
        # KG embeddings statistics
        kg_emb_stats = await self.conn.fetch("""
            SELECT 
                (SELECT COUNT(*) FROM free_will.kg_node_embeddings) as node_embeddings,
                (SELECT COUNT(*) FROM free_will.kg_edge_embeddings) as edge_embeddings
        """)
        
        stats['kg_embeddings'] = dict(kg_emb_stats[0])
        
        return stats
        
    async def display_system_overview(self) -> None:
        """Display comprehensive system overview."""
        logger.info("🎯 ANCIENT FREE WILL DATABASE - SYSTEM OVERVIEW")
        logger.info("=" * 80)
        
        stats = await self.get_system_statistics()
        
        # Knowledge Graph
        if 'knowledge_graph' in stats:
            kg_stats = stats['knowledge_graph']
            logger.info(f"🧠 KNOWLEDGE GRAPH (GraphRAG):")
            logger.info(f"   • Total nodes: {kg_stats['total_nodes']}")
            logger.info(f"   • Total edges: {kg_stats['total_edges']}")
            logger.info(f"   • Node types: {kg_stats['node_types']}")
            
        # PostgreSQL
        if 'postgresql' in stats:
            pg_stats = stats['postgresql']
            logger.info(f"\n🗄️ POSTGRESQL DATABASE:")
            logger.info(f"   • Total texts: {pg_stats['total_texts']}")
            logger.info(f"   • Texts with embeddings: {pg_stats['texts_with_embeddings']}")
            logger.info(f"   • Texts with lemmas: {pg_stats['texts_with_lemmas']}")
            logger.info(f"   • Total characters: {pg_stats['total_characters']:,}")
            logger.info(f"   • Languages: {pg_stats['languages']}")
            logger.info(f"   • Categories: {pg_stats['categories']}")
            
        # KG Embeddings
        if 'kg_embeddings' in stats:
            kg_emb_stats = stats['kg_embeddings']
            logger.info(f"\n🔍 VECTOR DATABASE:")
            logger.info(f"   • KG node embeddings: {kg_emb_stats['node_embeddings']}")
            logger.info(f"   • KG edge embeddings: {kg_emb_stats['edge_embeddings']}")
            logger.info(f"   • Text embeddings: {stats['postgresql']['texts_with_embeddings']}")
            
        logger.info("\n" + "=" * 80)
        logger.info("🚀 ELEUTHERIA - The Ancient Free Will Database:")
        logger.info("   Where Knowledge Graphs meet Full-Text Search meets Semantic AI!")
        logger.info("=" * 80)


async def main():
    """Main function to run the comprehensive search demonstration."""
    async with MultiModalSemanticSearch() as searcher:
        await searcher.display_system_overview()
        await searcher.demonstrate_search_capabilities()


if __name__ == "__main__":
    asyncio.run(main())
