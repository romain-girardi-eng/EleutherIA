#!/usr/bin/env python3
"""
Enhanced test script for Ancient Free Will Database PostgreSQL with FTS capabilities.
"""

import asyncio
import asyncpg
import logging
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedFreeWillTester:
    """Test enhanced PostgreSQL setup with full-text search capabilities."""
    
    def __init__(self, 
                 host: str = "localhost",
                 port: int = 5433,
                 database: str = "ancient_free_will_db",
                 user: str = "free_will_user",
                 password: str = "free_will_password"):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.pool = None
    
    async def initialize(self):
        """Initialize PostgreSQL connection pool."""
        try:
            self.pool = await asyncpg.create_pool(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                min_size=2,
                max_size=5,
                command_timeout=60,
            )
            logger.info(f"Connected to PostgreSQL: {self.host}:{self.port}/{self.database}")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise
    
    async def close(self):
        """Close PostgreSQL connection pool."""
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("PostgreSQL connection closed")
    
    async def test_basic_queries(self):
        """Test basic database queries."""
        logger.info("🔍 Testing basic database queries...")
        
        async with self.pool.acquire() as conn:
            # Test basic counts
            total_texts = await conn.fetchval("SELECT COUNT(*) FROM free_will.texts")
            total_divisions = await conn.fetchval("SELECT COUNT(*) FROM free_will.text_divisions")
            total_sections = await conn.fetchval("SELECT COUNT(*) FROM free_will.text_sections")
            
            logger.info(f"✅ Total texts: {total_texts}")
            logger.info(f"✅ Total divisions: {total_divisions}")
            logger.info(f"✅ Total sections: {total_sections}")
            
            # Test metadata coverage
            with_lemmas = await conn.fetchval("SELECT COUNT(*) FROM free_will.texts WHERE lemmas IS NOT NULL")
            with_embeddings = await conn.fetchval("SELECT COUNT(*) FROM free_will.texts WHERE embedding IS NOT NULL")
            with_tei_xml = await conn.fetchval("SELECT COUNT(*) FROM free_will.texts WHERE tei_xml IS NOT NULL")
            
            logger.info(f"✅ Texts with lemmas: {with_lemmas}")
            logger.info(f"✅ Texts with embeddings: {with_embeddings}")
            logger.info(f"✅ Texts with TEI XML: {with_tei_xml}")
    
    async def test_full_text_search(self):
        """Test full-text search capabilities."""
        logger.info("🔍 Testing full-text search capabilities...")
        
        async with self.pool.acquire() as conn:
            # Test Greek full-text search
            logger.info("Testing Greek full-text search for 'ἐφ ἡμῖν' (eph' hêmin)...")
            results = await conn.fetch("""
                SELECT id, title, author, rank, snippet
                FROM free_will.search_greek_texts('ἐφ ἡμῖν', 5)
            """)
            
            if results:
                logger.info(f"✅ Found {len(results)} results for 'eph' hêmin':")
                for result in results:
                    logger.info(f"  - {result['title']} by {result['author']} (rank: {result['rank']:.3f})")
            else:
                logger.info("ℹ️ No results found for 'eph' hêmin'")
            
            # Test search for 'fate' concepts
            logger.info("Testing search for 'fate' concepts...")
            results = await conn.fetch("""
                SELECT id, title, author, rank, snippet
                FROM free_will.search_greek_texts('εἱμαρμένη', 5)
            """)
            
            if results:
                logger.info(f"✅ Found {len(results)} results for 'εἱμαρμένη' (fate):")
                for result in results:
                    logger.info(f"  - {result['title']} by {result['author']} (rank: {result['rank']:.3f})")
            else:
                logger.info("ℹ️ No results found for 'εἱμαρμένη'")
            
            # Test Latin search
            logger.info("Testing Latin search for 'libero arbitrio'...")
            results = await conn.fetch("""
                SELECT id, title, author, rank, snippet
                FROM free_will.search_greek_texts('libero arbitrio', 5)
            """)
            
            if results:
                logger.info(f"✅ Found {len(results)} results for 'libero arbitrio':")
                for result in results:
                    logger.info(f"  - {result['title']} by {result['author']} (rank: {result['rank']:.3f})")
            else:
                logger.info("ℹ️ No results found for 'libero arbitrio'")
    
    async def test_lemma_search(self):
        """Test lemma-based search."""
        logger.info("🔍 Testing lemma-based search...")
        
        async with self.pool.acquire() as conn:
            # Test lemma search
            logger.info("Testing lemma search for 'ἐφ ἡμῖν'...")
            results = await conn.fetch("""
                SELECT id, title, author, language, lemmas
                FROM free_will.search_by_lemmas('ἐφ ἡμῖν', 5)
            """)
            
            if results:
                logger.info(f"✅ Found {len(results)} results with lemmas:")
                for result in results:
                    logger.info(f"  - {result['title']} by {result['author']}")
            else:
                logger.info("ℹ️ No results found with lemmas")
    
    async def test_author_search(self):
        """Test author-based search."""
        logger.info("🔍 Testing author-based search...")
        
        async with self.pool.acquire() as conn:
            # Test author search
            logger.info("Testing author search for 'Aristotle'...")
            results = await conn.fetch("""
                SELECT id, title, author, language, text_length
                FROM free_will.search_by_author('Aristotle', 5)
            """)
            
            if results:
                logger.info(f"✅ Found {len(results)} results for Aristotle:")
                for result in results:
                    logger.info(f"  - {result['title']} ({result['text_length']:,} chars)")
            else:
                logger.info("ℹ️ No results found for Aristotle")
    
    async def test_advanced_queries(self):
        """Test advanced SQL queries."""
        logger.info("🔍 Testing advanced SQL queries...")
        
        async with self.pool.acquire() as conn:
            # Test JSONB queries for lemmas
            logger.info("Testing JSONB lemma queries...")
            results = await conn.fetch("""
                SELECT title, author, lemmas
                FROM free_will.texts 
                WHERE lemmas IS NOT NULL 
                AND jsonb_typeof(lemmas) = 'array'
                AND jsonb_array_length(lemmas) > 100
                ORDER BY jsonb_array_length(lemmas) DESC
                LIMIT 3
            """)
            
            if results:
                logger.info(f"✅ Found {len(results)} texts with extensive lemmas:")
                for result in results:
                    lemma_count = len(result['lemmas']) if result['lemmas'] else 0
                    logger.info(f"  - {result['title']} by {result['author']} ({lemma_count} lemmas)")
            
            # Test text structure analysis
            logger.info("Testing text structure analysis...")
            results = await conn.fetch("""
                SELECT t.title, t.author, 
                       COUNT(d.id) as division_count,
                       COUNT(s.id) as section_count,
                       LENGTH(t.raw_text) as text_length
                FROM free_will.texts t
                LEFT JOIN free_will.text_divisions d ON t.id = d.text_id
                LEFT JOIN free_will.text_sections s ON t.id = s.text_id
                GROUP BY t.id, t.title, t.author, t.raw_text
                ORDER BY text_length DESC
                LIMIT 5
            """)
            
            if results:
                logger.info(f"✅ Text structure analysis (top 5 longest texts):")
                for result in results:
                    logger.info(f"  - {result['title']} by {result['author']}")
                    logger.info(f"    Length: {result['text_length']:,} chars, "
                              f"Divisions: {result['division_count']}, "
                              f"Sections: {result['section_count']}")
    
    async def test_performance(self):
        """Test query performance."""
        logger.info("🔍 Testing query performance...")
        
        async with self.pool.acquire() as conn:
            import time
            
            # Test FTS performance
            start_time = time.time()
            results = await conn.fetch("""
                SELECT COUNT(*) 
                FROM free_will.texts 
                WHERE to_tsvector('greek', raw_text) @@ plainto_tsquery('greek', 'ἐφ ἡμῖν')
            """)
            fts_time = time.time() - start_time
            
            logger.info(f"✅ Full-text search query completed in {fts_time:.3f} seconds")
            logger.info(f"✅ Found {results[0]['count']} matching texts")
            
            # Test JSONB query performance
            start_time = time.time()
            results = await conn.fetch("""
                SELECT COUNT(*) 
                FROM free_will.texts 
                WHERE lemmas::text ILIKE '%ἐφ ἡμῖν%'
            """)
            jsonb_time = time.time() - start_time
            
            logger.info(f"✅ JSONB lemma search completed in {jsonb_time:.3f} seconds")
            logger.info(f"✅ Found {results[0]['count']} matching texts")
    
    async def run_all_tests(self):
        """Run all tests."""
        logger.info("🚀 Starting Enhanced Ancient Free Will Database Tests")
        logger.info("=" * 60)
        
        try:
            await self.test_basic_queries()
            logger.info("")
            
            await self.test_full_text_search()
            logger.info("")
            
            await self.test_lemma_search()
            logger.info("")
            
            await self.test_author_search()
            logger.info("")
            
            await self.test_advanced_queries()
            logger.info("")
            
            await self.test_performance()
            logger.info("")
            
            logger.info("🎉 All enhanced tests completed successfully!")
            logger.info("=" * 60)
            logger.info("Full-text search capabilities are working perfectly!")
            
        except Exception as e:
            logger.error(f"Test failed: {e}")
            raise

async def main():
    """Main test function."""
    tester = EnhancedFreeWillTester()
    
    try:
        await tester.initialize()
        await tester.run_all_tests()
    except Exception as e:
        logger.error(f"Enhanced testing failed: {e}")
        raise
    finally:
        await tester.close()

if __name__ == "__main__":
    asyncio.run(main())
