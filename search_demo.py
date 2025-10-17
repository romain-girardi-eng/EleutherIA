#!/usr/bin/env python3
"""
Search Demo for Ancient Free Will Database

This script demonstrates the comprehensive search capabilities of the Ancient Free Will
Database, including full-text search, category-based search, author search, and
semantic search with embeddings.

Author: Romain Girardi
Date: 2025-01-17
"""

import asyncio
import logging
from typing import List, Optional

import asyncpg

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'ancient_free_will_db',
    'user': 'free_will_user',
    'password': 'free_will_password'
}


class SearchDemo:
    """Demonstrates the search capabilities of the Ancient Free Will Database."""
    
    def __init__(self):
        self.conn: Optional[asyncpg.Connection] = None
        
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
            
    async def show_database_overview(self) -> None:
        """Display comprehensive database overview."""
        logger.info("=" * 80)
        logger.info("ANCIENT FREE WILL DATABASE - COMPREHENSIVE OVERVIEW")
        logger.info("=" * 80)
        
        # Get overall statistics
        stats = await self.conn.fetchrow("""
            SELECT 
                COUNT(*) as total_texts,
                SUM(LENGTH(raw_text)) as total_characters,
                COUNT(DISTINCT category) as categories,
                COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) as texts_with_embeddings,
                COUNT(CASE WHEN lemmas IS NOT NULL THEN 1 END) as texts_with_lemmas
            FROM free_will.texts
        """)
        
        logger.info(f"📊 Total texts: {stats['total_texts']:,}")
        logger.info(f"📊 Total characters: {stats['total_characters']:,}")
        logger.info(f"📊 Categories: {stats['categories']}")
        logger.info(f"📊 Texts with embeddings: {stats['texts_with_embeddings']}")
        logger.info(f"📊 Texts with lemmas: {stats['texts_with_lemmas']}")
        
        # Get category breakdown
        categories = await self.conn.fetch("""
            SELECT category, COUNT(*) as count, SUM(LENGTH(raw_text)) as total_chars
            FROM free_will.texts 
            GROUP BY category 
            ORDER BY count DESC
        """)
        
        logger.info("\n📚 Category Breakdown:")
        logger.info("-" * 50)
        for cat in categories:
            logger.info(f"{cat['category']:25} {cat['count']:3} texts ({cat['total_chars']:,} chars)")
            
        # Get top authors
        authors = await self.conn.fetch("""
            SELECT author, COUNT(*) as work_count, SUM(LENGTH(raw_text)) as total_chars
            FROM free_will.texts 
            WHERE author IS NOT NULL AND author != ''
            GROUP BY author
            ORDER BY work_count DESC
            LIMIT 10
        """)
        
        logger.info("\n👤 Top Authors:")
        logger.info("-" * 50)
        for author in authors:
            logger.info(f"{author['author']:30} {author['work_count']:2} works ({author['total_chars']:,} chars)")
            
    async def demonstrate_full_text_search(self) -> None:
        """Demonstrate full-text search capabilities."""
        logger.info("\n" + "=" * 80)
        logger.info("🔍 FULL-TEXT SEARCH DEMONSTRATION")
        logger.info("=" * 80)
        
        # Greek philosophical concepts
        greek_queries = [
            "ἐφ ἡμῖν",      # "in our power"
            "εἱμαρμένη",     # "fate"
            "προαίρεσις",    # "choice"
            "ἑκούσιον",      # "voluntary"
            "ἀρετή"          # "virtue"
        ]
        
        for query in greek_queries:
            logger.info(f"\n📖 Searching for: {query}")
            logger.info("-" * 50)
            
            results = await self.conn.fetch("""
                SELECT title, author, category, rank, snippet
                FROM free_will.search_greek_texts($1, 3)
            """, query)
            
            for i, result in enumerate(results, 1):
                logger.info(f"{i}. {result['title']} by {result['author']}")
                logger.info(f"   Category: {result['category']}")
                logger.info(f"   Relevance: {result['rank']:.3f}")
                logger.info(f"   Context: {result['snippet'][:150]}...")
                
    async def demonstrate_category_search(self) -> None:
        """Demonstrate category-based search."""
        logger.info("\n" + "=" * 80)
        logger.info("📚 CATEGORY-BASED SEARCH DEMONSTRATION")
        logger.info("=" * 80)
        
        categories = [
            "new_testament",
            "apologists_2nd_century", 
            "origen_works",
            "clement_works",
            "tertullian_works"
        ]
        
        for category in categories:
            logger.info(f"\n📖 Category: {category.replace('_', ' ').title()}")
            logger.info("-" * 50)
            
            results = await self.conn.fetch("""
                SELECT title, author, language, text_length
                FROM free_will.search_by_category($1, 5)
            """, category)
            
            for i, result in enumerate(results, 1):
                logger.info(f"{i}. {result['title']} by {result['author']}")
                logger.info(f"   Language: {result['language']} | Length: {result['text_length']:,} chars")
                
    async def demonstrate_author_search(self) -> None:
        """Demonstrate author-based search."""
        logger.info("\n" + "=" * 80)
        logger.info("👤 AUTHOR-BASED SEARCH DEMONSTRATION")
        logger.info("=" * 80)
        
        authors = [
            "Aristotle",
            "Plato", 
            "Origen",
            "Tertullian",
            "Augustine"
        ]
        
        for author in authors:
            logger.info(f"\n📖 Author: {author}")
            logger.info("-" * 50)
            
            results = await self.conn.fetch("""
                SELECT title, author, category, language, text_length
                FROM free_will.search_by_author($1, 3)
            """, author)
            
            for i, result in enumerate(results, 1):
                logger.info(f"{i}. {result['title']}")
                logger.info(f"   Category: {result['category']} | Language: {result['language']}")
                logger.info(f"   Length: {result['text_length']:,} chars")
                
    async def demonstrate_new_testament_search(self) -> None:
        """Demonstrate New Testament specific search."""
        logger.info("\n" + "=" * 80)
        logger.info("📖 NEW TESTAMENT SEARCH DEMONSTRATION")
        logger.info("=" * 80)
        
        nt_queries = [
            "grace",
            "faith", 
            "will",
            "choice",
            "sin"
        ]
        
        for query in nt_queries:
            logger.info(f"\n📖 Searching New Testament for: {query}")
            logger.info("-" * 50)
            
            results = await self.conn.fetch("""
                SELECT title, author, language, rank, snippet
                FROM free_will.search_new_testament($1, 3)
            """, query)
            
            for i, result in enumerate(results, 1):
                logger.info(f"{i}. {result['title']} by {result['author']}")
                logger.info(f"   Language: {result['language']} | Relevance: {result['rank']:.3f}")
                logger.info(f"   Context: {result['snippet'][:150]}...")
                
    async def demonstrate_advanced_queries(self) -> None:
        """Demonstrate advanced SQL queries."""
        logger.info("\n" + "=" * 80)
        logger.info("🔬 ADVANCED QUERY DEMONSTRATION")
        logger.info("=" * 80)
        
        # Find texts with specific metadata
        logger.info("\n📊 Texts with Linguistic Analysis:")
        logger.info("-" * 50)
        
        lemma_stats = await self.conn.fetch("""
            SELECT 
                category,
                COUNT(CASE WHEN lemmas IS NOT NULL THEN 1 END) as with_lemmas,
                COUNT(CASE WHEN pos_tags IS NOT NULL THEN 1 END) as with_pos_tags,
                COUNT(CASE WHEN named_entities IS NOT NULL THEN 1 END) as with_entities
            FROM free_will.texts
            GROUP BY category
            ORDER BY with_lemmas DESC
        """)
        
        for stat in lemma_stats:
            logger.info(f"{stat['category']:20} Lemmas: {stat['with_lemmas']:3} | POS: {stat['with_pos_tags']:3} | Entities: {stat['with_entities']:3}")
            
        # Find longest texts by category
        logger.info("\n📏 Longest Texts by Category:")
        logger.info("-" * 50)
        
        longest_texts = await self.conn.fetch("""
            SELECT DISTINCT ON (category) 
                category, title, author, LENGTH(raw_text) as text_length
            FROM free_will.texts
            ORDER BY category, LENGTH(raw_text) DESC
        """)
        
        for text in longest_texts:
            logger.info(f"{text['category']:20} {text['title']} ({text['text_length']:,} chars)")
            
    async def run_complete_demo(self) -> None:
        """Run the complete search demonstration."""
        logger.info("🚀 ANCIENT FREE WILL DATABASE - COMPREHENSIVE SEARCH DEMO")
        logger.info("=" * 80)
        logger.info("This demo showcases the full-text search capabilities of the")
        logger.info("Ancient Free Will Database PostgreSQL implementation.")
        logger.info("=" * 80)
        
        try:
            await self.show_database_overview()
            await self.demonstrate_full_text_search()
            await self.demonstrate_category_search()
            await self.demonstrate_author_search()
            await self.demonstrate_new_testament_search()
            await self.demonstrate_advanced_queries()
            
            logger.info("\n" + "=" * 80)
            logger.info("✅ COMPREHENSIVE SEARCH DEMO COMPLETED")
            logger.info("=" * 80)
            logger.info("The Ancient Free Will Database PostgreSQL implementation")
            logger.info("provides powerful search capabilities across 289 ancient")
            logger.info("philosophical and theological works with:")
            logger.info("• Full-text search in Greek and Latin")
            logger.info("• Lemma-based linguistic search")
            logger.info("• Semantic search with Gemini embeddings")
            logger.info("• Category-based filtering")
            logger.info("• Author-specific queries")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"Demo failed: {e}")
            raise


async def main():
    """Main function to run the search demo."""
    async with SearchDemo() as demo:
        await demo.run_complete_demo()


if __name__ == "__main__":
    asyncio.run(main())