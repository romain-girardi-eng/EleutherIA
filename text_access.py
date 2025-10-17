#!/usr/bin/env python3
"""
Text Access and Export Utility for Ancient Free Will Database

This script provides utilities for accessing, searching, and exporting texts
from the Ancient Free Will Database PostgreSQL implementation.

Author: Romain Girardi
Date: 2025-01-17
"""

import asyncio
import logging
from pathlib import Path
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


class TextAccessor:
    """Provides access and export functionality for texts in the database."""
    
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
            
    async def list_texts(self, limit: int = 20) -> None:
        """List texts in the database."""
        logger.info(f"\n📚 DATABASE TEXTS (showing first {limit}):")
        logger.info("=" * 80)
        
        texts = await self.conn.fetch("""
            SELECT title, author, category, language, LENGTH(raw_text) as text_length
            FROM free_will.texts 
            ORDER BY text_length DESC
            LIMIT $1
        """, limit)
        
        for i, text in enumerate(texts, 1):
            logger.info(f"{i:2d}. {text['title']}")
            logger.info(f"     Author: {text['author']}")
            logger.info(f"     Category: {text['category']} | Language: {text['language']}")
            logger.info(f"     Length: {text['text_length']:,} characters")
            logger.info("")
            
    async def search_texts(self, query: str, limit: int = 10) -> None:
        """Search texts by title or author."""
        logger.info(f"\n🔍 SEARCHING FOR: '{query}'")
        logger.info("=" * 60)
        
        results = await self.conn.fetch("""
            SELECT title, author, category, language, LENGTH(raw_text) as text_length
            FROM free_will.texts 
            WHERE title ILIKE $1 OR author ILIKE $1
            ORDER BY text_length DESC
            LIMIT $2
        """, f"%{query}%", limit)
        
        if not results:
            logger.info("No texts found matching your query.")
            return
            
        for i, text in enumerate(results, 1):
            logger.info(f"{i}. {text['title']} by {text['author']}")
            logger.info(f"   Category: {text['category']} | Language: {text['language']}")
            logger.info(f"   Length: {text['text_length']:,} characters")
            logger.info("")
            
    async def get_text_content(self, title: str) -> Optional[dict]:
        """Get the full content of a specific text."""
        logger.info(f"\n📖 GETTING TEXT: '{title}'")
        logger.info("=" * 60)
        
        text = await self.conn.fetchrow("""
            SELECT title, author, category, language, raw_text, LENGTH(raw_text) as text_length
            FROM free_will.texts 
            WHERE title ILIKE $1
            LIMIT 1
        """, f"%{title}%")
        
        if not text:
            logger.info(f"Text '{title}' not found.")
            return None
            
        logger.info(f"Title: {text['title']}")
        logger.info(f"Author: {text['author']}")
        logger.info(f"Category: {text['category']}")
        logger.info(f"Language: {text['language']}")
        logger.info(f"Length: {text['text_length']:,} characters")
        logger.info("")
        logger.info("Content preview (first 500 characters):")
        logger.info("-" * 60)
        preview = text['raw_text'][:500] + "..." if len(text['raw_text']) > 500 else text['raw_text']
        logger.info(preview)
        logger.info("-" * 60)
        
        return dict(text)
        
    async def export_text_to_file(self, title: str, output_dir: str = "exported_texts") -> bool:
        """Export a text to a file."""
        logger.info(f"\n💾 EXPORTING TEXT: '{title}'")
        logger.info("=" * 60)
        
        text = await self.get_text_content(title)
        if not text:
            return False
            
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Create filename
        safe_title = "".join(c for c in text['title'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_author = "".join(c for c in text['author'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"{safe_title}_by_{safe_author}.txt"
        filepath = output_path / filename
        
        # Write text to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"Title: {text['title']}\n")
            f.write(f"Author: {text['author']}\n")
            f.write(f"Category: {text['category']}\n")
            f.write(f"Language: {text['language']}\n")
            f.write(f"Length: {text['text_length']:,} characters\n")
            f.write("=" * 80 + "\n\n")
            f.write(text['raw_text'])
        
        logger.info(f"✅ Text exported to: {filepath}")
        logger.info(f"   File size: {filepath.stat().st_size:,} bytes")
        return True
        
    async def export_multiple_texts(self, category: Optional[str] = None, 
                                 author: Optional[str] = None, limit: int = 5) -> None:
        """Export multiple texts based on criteria."""
        logger.info(f"\n📦 EXPORTING MULTIPLE TEXTS")
        logger.info("=" * 60)
        
        # Build query based on criteria
        where_clauses = []
        params = []
        
        if category:
            where_clauses.append("category = $" + str(len(params) + 1))
            params.append(category)
            
        if author:
            where_clauses.append("author ILIKE $" + str(len(params) + 1))
            params.append(f"%{author}%")
            
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        params.append(limit)
        
        query = f"""
            SELECT title, author, category, language, raw_text, LENGTH(raw_text) as text_length
            FROM free_will.texts 
            WHERE {where_sql}
            ORDER BY text_length DESC
            LIMIT ${len(params)}
        """
        
        texts = await self.conn.fetch(query, *params)
        
        if not texts:
            logger.info("No texts found matching your criteria.")
            return
            
        logger.info(f"Found {len(texts)} texts to export:")
        for text in texts:
            logger.info(f"  • {text['title']} by {text['author']}")
            
        logger.info("\nExporting...")
        
        for text in texts:
            await self.export_text_to_file(text['title'])
            
    async def show_database_info(self) -> None:
        """Show database storage information."""
        logger.info("\n🗄️ DATABASE STORAGE INFORMATION")
        logger.info("=" * 60)
        
        # Database size
        db_size = await self.conn.fetchval("""
            SELECT pg_size_pretty(pg_database_size('ancient_free_will_db'))
        """)
        
        logger.info(f"Database size: {db_size}")
        
        # Table sizes
        table_sizes = await self.conn.fetch("""
            SELECT 
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
            FROM pg_tables 
            WHERE schemaname = 'free_will'
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
        """)
        
        logger.info(f"\nTable sizes:")
        for table in table_sizes:
            logger.info(f"  {table['tablename']}: {table['size']}")
            
        # Text statistics
        stats = await self.conn.fetchrow("""
            SELECT 
                COUNT(*) as total_texts,
                SUM(LENGTH(raw_text)) as total_chars,
                AVG(LENGTH(raw_text)) as avg_length,
                MAX(LENGTH(raw_text)) as max_length,
                MIN(LENGTH(raw_text)) as min_length
            FROM free_will.texts
        """)
        
        logger.info(f"\nText statistics:")
        logger.info(f"  Total texts: {stats['total_texts']:,}")
        logger.info(f"  Total characters: {stats['total_chars']:,}")
        logger.info(f"  Average length: {stats['avg_length']:,.0f} characters")
        logger.info(f"  Longest text: {stats['max_length']:,} characters")
        logger.info(f"  Shortest text: {stats['min_length']:,} characters")


async def main():
    """Main function demonstrating text access capabilities."""
    async with TextAccessor() as accessor:
        # Show database info
        await accessor.show_database_info()
        
        # List some texts
        await accessor.list_texts(10)
        
        # Search for specific texts
        await accessor.search_texts("Republic")
        await accessor.search_texts("Origen")
        
        # Get a specific text
        await accessor.get_text_content("Republic")
        
        # Export a text
        await accessor.export_text_to_file("Republic")
        
        # Export multiple texts from a category
        await accessor.export_multiple_texts(category="new_testament", limit=3)


if __name__ == "__main__":
    asyncio.run(main())
