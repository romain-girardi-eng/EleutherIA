#!/usr/bin/env python3
"""
Test Suite for Ancient Free Will Database PostgreSQL Implementation

This script provides comprehensive testing of the database setup, including
connection tests, data integrity checks, and search functionality validation.

Author: Romain Girardi
Date: 2025-01-17
"""

import asyncio
import logging
from typing import Dict, List, Optional

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


class DatabaseTester:
    """Comprehensive test suite for the Ancient Free Will Database."""
    
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
            logger.info("Database connection established successfully")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
            
    async def close(self) -> None:
        """Close database connection."""
        if self.conn:
            await self.conn.close()
            logger.info("Database connection closed")
            
    async def test_connection(self) -> bool:
        """Test basic database connection."""
        logger.info("Testing database connection...")
        
        try:
            result = await self.conn.fetchval("SELECT 1")
            if result == 1:
                logger.info("✅ Database connection test passed")
                return True
            else:
                logger.error("❌ Database connection test failed")
                return False
        except Exception as e:
            logger.error(f"❌ Database connection test failed: {e}")
            return False
            
    async def test_schema(self) -> bool:
        """Test database schema existence."""
        logger.info("Testing database schema...")
        
        try:
            # Check schema exists
            schema_exists = await self.conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM pg_namespace WHERE nspname = 'free_will'
                )
            """)
            
            if not schema_exists:
                logger.error("❌ Schema 'free_will' does not exist")
                return False
                
            # Check tables exist
            tables = await self.conn.fetch("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'free_will'
                ORDER BY tablename
            """)
            
            expected_tables = {'texts', 'text_divisions', 'text_sections'}
            actual_tables = {row['tablename'] for row in tables}
            
            if expected_tables.issubset(actual_tables):
                logger.info("✅ Database schema test passed")
                logger.info(f"Found tables: {', '.join(sorted(actual_tables))}")
                return True
            else:
                missing = expected_tables - actual_tables
                logger.error(f"❌ Missing tables: {', '.join(missing)}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Database schema test failed: {e}")
            return False
            
    async def test_data_integrity(self) -> bool:
        """Test data integrity and completeness."""
        logger.info("Testing data integrity...")
        
        try:
            # Get basic statistics
            stats = await self.conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_texts,
                    COUNT(DISTINCT category) as categories,
                    COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) as texts_with_embeddings,
                    COUNT(CASE WHEN lemmas IS NOT NULL THEN 1 END) as texts_with_lemmas,
                    COUNT(CASE WHEN tei_xml IS NOT NULL THEN 1 END) as texts_with_tei_xml,
                    SUM(LENGTH(raw_text)) as total_characters
                FROM free_will.texts
            """)
            
            logger.info("Database Statistics:")
            logger.info(f"  Total texts: {stats['total_texts']:,}")
            logger.info(f"  Categories: {stats['categories']}")
            logger.info(f"  Texts with embeddings: {stats['texts_with_embeddings']}")
            logger.info(f"  Texts with lemmas: {stats['texts_with_lemmas']}")
            logger.info(f"  Texts with TEI XML: {stats['texts_with_tei_xml']}")
            logger.info(f"  Total characters: {stats['total_characters']:,}")
            
            # Check for minimum expected data
            if stats['total_texts'] < 100:
                logger.error("❌ Insufficient texts in database")
                return False
                
            if stats['categories'] < 5:
                logger.error("❌ Insufficient categories in database")
                return False
                
            logger.info("✅ Data integrity test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Data integrity test failed: {e}")
            return False
            
    async def test_search_functions(self) -> bool:
        """Test search function functionality."""
        logger.info("Testing search functions...")
        
        try:
            # Test Greek full-text search
            greek_results = await self.conn.fetch("""
                SELECT COUNT(*) as count
                FROM free_will.search_greek_texts('ἐφ ἡμῖν', 5)
            """)
            
            if greek_results[0]['count'] > 0:
                logger.info("✅ Greek full-text search test passed")
            else:
                logger.warning("⚠️ No results for Greek search 'ἐφ ἡμῖν'")
                
            # Test category search
            category_results = await self.conn.fetch("""
                SELECT COUNT(*) as count
                FROM free_will.search_by_category('new_testament', 5)
            """)
            
            if category_results[0]['count'] > 0:
                logger.info("✅ Category search test passed")
            else:
                logger.warning("⚠️ No results for New Testament category search")
                
            # Test author search
            author_results = await self.conn.fetch("""
                SELECT COUNT(*) as count
                FROM free_will.search_by_author('Aristotle', 5)
            """)
            
            if author_results[0]['count'] > 0:
                logger.info("✅ Author search test passed")
            else:
                logger.warning("⚠️ No results for Aristotle author search")
                
            logger.info("✅ Search functions test completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Search functions test failed: {e}")
            return False
            
    async def test_performance(self) -> bool:
        """Test database performance."""
        logger.info("Testing database performance...")
        
        try:
            import time
            
            # Test full-text search performance
            start_time = time.time()
            await self.conn.fetch("""
                SELECT title, author, rank
                FROM free_will.search_greek_texts('ἀρετή', 10)
            """)
            search_time = time.time() - start_time
            
            if search_time < 1.0:  # Should complete in under 1 second
                logger.info(f"✅ Full-text search performance test passed ({search_time:.3f}s)")
            else:
                logger.warning(f"⚠️ Full-text search slower than expected ({search_time:.3f}s)")
                
            # Test complex query performance
            start_time = time.time()
            await self.conn.fetch("""
                SELECT category, COUNT(*) as count, AVG(LENGTH(raw_text)) as avg_length
                FROM free_will.texts
                GROUP BY category
                ORDER BY count DESC
            """)
            query_time = time.time() - start_time
            
            if query_time < 0.5:  # Should complete in under 0.5 seconds
                logger.info(f"✅ Complex query performance test passed ({query_time:.3f}s)")
            else:
                logger.warning(f"⚠️ Complex query slower than expected ({query_time:.3f}s)")
                
            logger.info("✅ Performance test completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Performance test failed: {e}")
            return False
            
    async def test_data_relationships(self) -> bool:
        """Test data relationships and foreign keys."""
        logger.info("Testing data relationships...")
        
        try:
            # Test text-division relationships
            orphaned_divisions = await self.conn.fetchval("""
                SELECT COUNT(*)
                FROM free_will.text_divisions td
                LEFT JOIN free_will.texts t ON td.text_id = t.id
                WHERE t.id IS NULL
            """)
            
            if orphaned_divisions == 0:
                logger.info("✅ Text-division relationships test passed")
            else:
                logger.error(f"❌ Found {orphaned_divisions} orphaned divisions")
                return False
                
            # Test text-section relationships
            orphaned_sections = await self.conn.fetchval("""
                SELECT COUNT(*)
                FROM free_will.text_sections ts
                LEFT JOIN free_will.texts t ON ts.text_id = t.id
                WHERE t.id IS NULL
            """)
            
            if orphaned_sections == 0:
                logger.info("✅ Text-section relationships test passed")
            else:
                logger.error(f"❌ Found {orphaned_sections} orphaned sections")
                return False
                
            logger.info("✅ Data relationships test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Data relationships test failed: {e}")
            return False
            
    async def run_all_tests(self) -> bool:
        """Run all tests and return overall success."""
        logger.info("Starting comprehensive database tests...")
        logger.info("=" * 60)
        
        tests = [
            ("Connection", self.test_connection),
            ("Schema", self.test_schema),
            ("Data Integrity", self.test_data_integrity),
            ("Search Functions", self.test_search_functions),
            ("Performance", self.test_performance),
            ("Data Relationships", self.test_data_relationships)
        ]
        
        results = []
        for test_name, test_func in tests:
            logger.info(f"\n--- {test_name} Test ---")
            try:
                result = await test_func()
                results.append((test_name, result))
            except Exception as e:
                logger.error(f"❌ {test_name} test failed with exception: {e}")
                results.append((test_name, False))
                
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("TEST SUMMARY")
        logger.info("=" * 60)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASSED" if result else "❌ FAILED"
            logger.info(f"{test_name:20} {status}")
            if result:
                passed += 1
                
        logger.info("=" * 60)
        logger.info(f"Overall Result: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("🎉 ALL TESTS PASSED! Database is ready for use.")
        else:
            logger.warning(f"⚠️ {total - passed} tests failed. Please review the issues above.")
            
        return passed == total


async def main():
    """Main function to run the test suite."""
    async with DatabaseTester() as tester:
        success = await tester.run_all_tests()
        return success


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
