#!/usr/bin/env python3
"""
Comprehensive search demo for Ancient Free Will Database PostgreSQL implementation.
Demonstrates full-text search, lemma search, semantic search, and category-based queries.
"""

import asyncio
import asyncpg
import json
from typing import List, Dict, Any

# Database connection details
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'ancient_free_will_db',
    'user': 'free_will_user',
    'password': 'free_will_password'
}

class AncientFreeWillSearchDemo:
    """Comprehensive search demonstration for Ancient Free Will Database."""
    
    def __init__(self):
        self.conn = None
    
    async def connect(self):
        """Connect to PostgreSQL database."""
        self.conn = await asyncpg.connect(**DB_CONFIG)
        print("✅ Connected to Ancient Free Will Database PostgreSQL")
    
    async def disconnect(self):
        """Disconnect from database."""
        if self.conn:
            await self.conn.close()
            print("✅ Disconnected from database")
    
    async def demo_full_text_search(self):
        """Demonstrate full-text search capabilities."""
        print("\n" + "="*80)
        print("🔍 FULL-TEXT SEARCH DEMONSTRATION")
        print("="*80)
        
        # Greek philosophical concepts
        greek_queries = [
            "ἐφ ἡμῖν",  # "in our power"
            "εἱμαρμένη",  # "fate"
            "προαίρεσις",  # "choice"
            "ἑκούσιον",  # "voluntary"
            "ἀρετή"  # "virtue"
        ]
        
        for query in greek_queries:
            print(f"\n📖 Searching for: {query}")
            print("-" * 50)
            
            results = await self.conn.fetch("""
                SELECT title, author, category, rank, snippet
                FROM free_will.search_greek_texts($1, 3)
            """, query)
            
            for i, result in enumerate(results, 1):
                print(f"{i}. {result['title']} by {result['author']}")
                print(f"   Category: {result['category']}")
                print(f"   Relevance: {result['rank']:.3f}")
                print(f"   Context: {result['snippet'][:150]}...")
                print()
    
    async def demo_category_search(self):
        """Demonstrate category-based search."""
        print("\n" + "="*80)
        print("📚 CATEGORY-BASED SEARCH DEMONSTRATION")
        print("="*80)
        
        categories = [
            "new_testament",
            "apologists_2nd_century", 
            "origen_works",
            "clement_works",
            "tertullian_works"
        ]
        
        for category in categories:
            print(f"\n📖 Category: {category.replace('_', ' ').title()}")
            print("-" * 50)
            
            results = await self.conn.fetch("""
                SELECT title, author, language, text_length
                FROM free_will.search_by_category($1, 5)
            """, category)
            
            for i, result in enumerate(results, 1):
                print(f"{i}. {result['title']} by {result['author']}")
                print(f"   Language: {result['language']} | Length: {result['text_length']:,} chars")
                print()
    
    async def demo_author_search(self):
        """Demonstrate author-based search."""
        print("\n" + "="*80)
        print("👤 AUTHOR-BASED SEARCH DEMONSTRATION")
        print("="*80)
        
        authors = [
            "Aristotle",
            "Plato", 
            "Origenes",
            "Tertullian",
            "Augustine"
        ]
        
        for author in authors:
            print(f"\n📖 Author: {author}")
            print("-" * 50)
            
            results = await self.conn.fetch("""
                SELECT title, author, category, language, LENGTH(raw_text) as text_length
                FROM free_will.texts 
                WHERE author ILIKE $1
                ORDER BY text_length DESC
                LIMIT 3
            """, f"%{author}%")
            
            for i, result in enumerate(results, 1):
                print(f"{i}. {result['title']}")
                print(f"   Category: {result['category']} | Language: {result['language']}")
                print(f"   Length: {result['text_length']:,} chars")
                print()
    
    async def demo_lemma_search(self):
        """Demonstrate lemma-based search."""
        print("\n" + "="*80)
        print("🔤 LEMMA-BASED SEARCH DEMONSTRATION")
        print("="*80)
        
        # Check which texts have lemmas
        lemma_count = await self.conn.fetchval("""
            SELECT COUNT(*) FROM free_will.texts WHERE lemmas IS NOT NULL
        """)
        
        print(f"📊 Texts with lemmas: {lemma_count}")
        
        if lemma_count > 0:
            # Find texts with specific lemmas
            results = await self.conn.fetch("""
                SELECT title, author, language, lemmas
                FROM free_will.texts 
                WHERE lemmas IS NOT NULL 
                AND lemmas::text ILIKE '%ἐφ%'
                LIMIT 5
            """)
            
            print(f"\n📖 Texts containing 'ἐφ' in lemmas:")
            print("-" * 50)
            
            for i, result in enumerate(results, 1):
                print(f"{i}. {result['title']} by {result['author']}")
                print(f"   Language: {result['language']}")
                # Show first few lemmas
                if result['lemmas']:
                    lemmas_preview = str(result['lemmas'])[:100] + "..." if len(str(result['lemmas'])) > 100 else str(result['lemmas'])
                    print(f"   Lemmas: {lemmas_preview}")
                print()
    
    async def demo_embedding_search(self):
        """Demonstrate semantic search with embeddings."""
        print("\n" + "="*80)
        print("🧠 SEMANTIC SEARCH WITH EMBEDDINGS DEMONSTRATION")
        print("="*80)
        
        # Check which texts have embeddings
        embedding_count = await self.conn.fetchval("""
            SELECT COUNT(*) FROM free_will.texts WHERE embedding IS NOT NULL
        """)
        
        print(f"📊 Texts with embeddings: {embedding_count}")
        
        if embedding_count > 0:
            # Get a sample embedding for demonstration
            sample_embedding = await self.conn.fetchval("""
                SELECT embedding FROM free_will.texts 
                WHERE embedding IS NOT NULL 
                LIMIT 1
            """)
            
            if sample_embedding:
                print(f"\n📖 Sample embedding found (dimensions: {len(sample_embedding)})")
                print("Note: Full semantic similarity search requires vector operations")
                print("This would typically involve:")
                print("1. Converting search query to embedding using Gemini")
                print("2. Computing cosine similarity with stored embeddings")
                print("3. Ranking results by similarity score")
    
    async def demo_new_testament_search(self):
        """Demonstrate New Testament specific search."""
        print("\n" + "="*80)
        print("📖 NEW TESTAMENT SEARCH DEMONSTRATION")
        print("="*80)
        
        nt_queries = [
            "grace",
            "faith", 
            "will",
            "choice",
            "sin"
        ]
        
        for query in nt_queries:
            print(f"\n📖 Searching New Testament for: {query}")
            print("-" * 50)
            
            results = await self.conn.fetch("""
                SELECT title, author, language, rank, snippet
                FROM free_will.search_new_testament($1, 3)
            """, query)
            
            for i, result in enumerate(results, 1):
                print(f"{i}. {result['title']} by {result['author']}")
                print(f"   Language: {result['language']} | Relevance: {result['rank']:.3f}")
                print(f"   Context: {result['snippet'][:150]}...")
                print()
    
    async def demo_database_statistics(self):
        """Show comprehensive database statistics."""
        print("\n" + "="*80)
        print("📊 DATABASE STATISTICS")
        print("="*80)
        
        # Total counts
        total_texts = await self.conn.fetchval("SELECT COUNT(*) FROM free_will.texts")
        total_divisions = await self.conn.fetchval("SELECT COUNT(*) FROM free_will.text_divisions")
        total_sections = await self.conn.fetchval("SELECT COUNT(*) FROM free_will.text_sections")
        
        print(f"📚 Total texts: {total_texts:,}")
        print(f"📑 Total divisions: {total_divisions:,}")
        print(f"📄 Total sections: {total_sections:,}")
        
        # Metadata coverage
        with_lemmas = await self.conn.fetchval("SELECT COUNT(*) FROM free_will.texts WHERE lemmas IS NOT NULL")
        with_pos_tags = await self.conn.fetchval("SELECT COUNT(*) FROM free_will.texts WHERE pos_tags IS NOT NULL")
        with_embeddings = await self.conn.fetchval("SELECT COUNT(*) FROM free_will.texts WHERE embedding IS NOT NULL")
        with_tei_xml = await self.conn.fetchval("SELECT COUNT(*) FROM free_will.texts WHERE tei_xml IS NOT NULL")
        
        print(f"\n🔍 Metadata Coverage:")
        print(f"   Texts with lemmas: {with_lemmas}")
        print(f"   Texts with POS tags: {with_pos_tags}")
        print(f"   Texts with embeddings: {with_embeddings}")
        print(f"   Texts with TEI XML: {with_tei_xml}")
        
        # Language distribution
        languages = await self.conn.fetch("""
            SELECT language, COUNT(*) as count
            FROM free_will.texts 
            GROUP BY language 
            ORDER BY count DESC
        """)
        
        print(f"\n🌍 Language Distribution:")
        for lang in languages:
            print(f"   {lang['language']}: {lang['count']} texts")
        
        # Category distribution
        categories = await self.conn.fetch("""
            SELECT category, COUNT(*) as count
            FROM free_will.texts 
            GROUP BY category 
            ORDER BY count DESC
        """)
        
        print(f"\n📚 Category Distribution:")
        for cat in categories:
            print(f"   {cat['category']}: {cat['count']} texts")
        
        # Top authors by text count
        authors = await self.conn.fetch("""
            SELECT author, COUNT(*) as work_count, SUM(LENGTH(raw_text)) as total_chars
            FROM free_will.texts 
            WHERE author IS NOT NULL AND author != ''
            GROUP BY author
            ORDER BY work_count DESC
            LIMIT 10
        """)
        
        print(f"\n👤 Top Authors by Work Count:")
        for author in authors:
            print(f"   {author['author']}: {author['work_count']} works, {author['total_chars']:,} chars")
    
    async def run_comprehensive_demo(self):
        """Run all demonstration functions."""
        print("🚀 ANCIENT FREE WILL DATABASE - COMPREHENSIVE SEARCH DEMO")
        print("="*80)
        print("This demo showcases the full-text search capabilities of the")
        print("Ancient Free Will Database PostgreSQL implementation.")
        print("="*80)
        
        await self.connect()
        
        try:
            await self.demo_database_statistics()
            await self.demo_full_text_search()
            await self.demo_category_search()
            await self.demo_author_search()
            await self.demo_lemma_search()
            await self.demo_embedding_search()
            await self.demo_new_testament_search()
            
            print("\n" + "="*80)
            print("✅ COMPREHENSIVE SEARCH DEMO COMPLETED")
            print("="*80)
            print("The Ancient Free Will Database PostgreSQL implementation")
            print("provides powerful search capabilities across 289 ancient")
            print("philosophical and theological works with:")
            print("• Full-text search in Greek and Latin")
            print("• Lemma-based linguistic search")
            print("• Semantic search with Gemini embeddings")
            print("• Category-based filtering")
            print("• Author-specific queries")
            print("="*80)
            
        finally:
            await self.disconnect()

async def main():
    """Main function to run the comprehensive search demo."""
    demo = AncientFreeWillSearchDemo()
    await demo.run_comprehensive_demo()

if __name__ == "__main__":
    asyncio.run(main())
