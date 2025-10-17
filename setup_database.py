#!/usr/bin/env python3
"""
PostgreSQL Setup for Ancient Free Will Database

This script sets up a comprehensive PostgreSQL database containing 289 ancient
philosophical and theological works relevant to free will debates, including
full-text search capabilities, linguistic analysis, and semantic search.

Author: Romain Girardi
Date: 2025-01-17
"""

import asyncio
import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

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

# File paths
KG_PATH = Path("/Users/romaingirardi/Documents/Ancient Free Will Database/ancient_free_will_database.json")
SQLITE_DB_PATH = Path("/Users/romaingirardi/SematikaData/library.db")


class AncientFreeWillDatabaseSetup:
    """Handles the complete setup of the Ancient Free Will Database PostgreSQL instance."""
    
    def __init__(self):
        self.pg_conn: Optional[asyncpg.Connection] = None
        self.sqlite_conn: Optional[sqlite3.Connection] = None
        
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
            self.pg_conn = await asyncpg.connect(**DB_CONFIG)
            self.sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
            logger.info("Database connections established successfully")
        except Exception as e:
            logger.error(f"Failed to establish database connections: {e}")
            raise
            
    async def close(self) -> None:
        """Close database connections."""
        if self.pg_conn:
            await self.pg_conn.close()
        if self.sqlite_conn:
            self.sqlite_conn.close()
        logger.info("Database connections closed")
        
    async def create_schema(self) -> None:
        """Create the PostgreSQL schema and tables."""
        logger.info("Creating PostgreSQL schema...")
        
        schema_sql = """
        -- Drop existing schema if it exists
        DROP SCHEMA IF EXISTS free_will CASCADE;
        CREATE SCHEMA free_will;
        
        -- Main texts table
        CREATE TABLE free_will.texts (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            kg_work_id TEXT UNIQUE,
            title TEXT NOT NULL,
            author TEXT,
            category TEXT,
            raw_text TEXT NOT NULL,
            normalized_text TEXT,
            tei_xml TEXT,
            lemmas JSONB,
            pos_tags JSONB,
            named_entities JSONB,
            embedding BYTEA,
            embedding_model TEXT,
            embedding_dimensions INTEGER,
            embedding_hash TEXT,
            embedding_created_at TIMESTAMP WITH TIME ZONE,
            language TEXT DEFAULT 'grc',
            date_created TEXT,
            source TEXT,
            notes TEXT,
            metadata JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Text divisions table
        CREATE TABLE free_will.text_divisions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            text_id UUID NOT NULL,
            parent_id UUID,
            type TEXT NOT NULL,
            subtype TEXT,
            n TEXT,
            full_reference TEXT,
            heading TEXT,
            language TEXT,
            speaker TEXT,
            char_position INTEGER,
            char_length INTEGER,
            xml_id TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (text_id) REFERENCES free_will.texts(id) ON DELETE CASCADE,
            FOREIGN KEY (parent_id) REFERENCES free_will.text_divisions(id) ON DELETE CASCADE
        );
        
        -- Text sections table
        CREATE TABLE free_will.text_sections (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            text_id UUID NOT NULL,
            division_id UUID,
            type TEXT NOT NULL,
            subtype TEXT,
            n TEXT,
            content TEXT NOT NULL,
            language TEXT,
            speaker TEXT,
            char_position INTEGER,
            xml_id TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (text_id) REFERENCES free_will.texts(id) ON DELETE CASCADE,
            FOREIGN KEY (division_id) REFERENCES free_will.text_divisions(id) ON DELETE CASCADE
        );
        
        -- Create indexes for performance
        CREATE INDEX idx_texts_title ON free_will.texts (title);
        CREATE INDEX idx_texts_author ON free_will.texts (author);
        CREATE INDEX idx_texts_category ON free_will.texts (category);
        CREATE INDEX idx_texts_kg_work_id ON free_will.texts (kg_work_id);
        CREATE INDEX idx_texts_language ON free_will.texts (language);
        CREATE INDEX idx_text_divisions_text_id ON free_will.text_divisions (text_id);
        CREATE INDEX idx_text_sections_text_id ON free_will.text_sections (text_id);
        CREATE INDEX idx_text_sections_division_id ON free_will.text_sections (division_id);
        
        -- Full-text search indexes
        CREATE INDEX idx_texts_fts_greek ON free_will.texts 
            USING gin(to_tsvector('greek', raw_text)) WHERE language = 'grc';
        CREATE INDEX idx_texts_fts_latin ON free_will.texts 
            USING gin(to_tsvector('simple', raw_text)) WHERE language = 'lat';
        """
        
        await self.pg_conn.execute(schema_sql)
        logger.info("PostgreSQL schema created successfully")
        
    async def create_search_functions(self) -> None:
        """Create PostgreSQL search functions."""
        logger.info("Creating search functions...")
        
        functions_sql = """
        -- Greek full-text search function
        CREATE OR REPLACE FUNCTION free_will.search_greek_texts(
            query_text TEXT,
            result_limit INTEGER DEFAULT 10
        )
        RETURNS TABLE(
            id UUID,
            title TEXT,
            author TEXT,
            category TEXT,
            language TEXT,
            rank REAL,
            snippet TEXT
        ) AS $$
        BEGIN
            RETURN QUERY
            SELECT 
                t.id,
                t.title,
                t.author,
                t.category,
                t.language,
                ts_rank(to_tsvector('greek', t.raw_text), plainto_tsquery('greek', query_text)) as rank,
                ts_headline('greek', t.raw_text, plainto_tsquery('greek', query_text), 
                           'MaxWords=30, MinWords=5, MaxFragments=2') as snippet
            FROM free_will.texts t
            WHERE to_tsvector('greek', t.raw_text) @@ plainto_tsquery('greek', query_text)
            ORDER BY rank DESC
            LIMIT result_limit;
        END;
        $$ LANGUAGE plpgsql;
        
        -- Category-based search function
        CREATE OR REPLACE FUNCTION free_will.search_by_category(
            category_name TEXT,
            result_limit INTEGER DEFAULT 10
        )
        RETURNS TABLE(
            id UUID,
            title TEXT,
            author TEXT,
            category TEXT,
            language TEXT,
            text_length INTEGER
        ) AS $$
        BEGIN
            RETURN QUERY
            SELECT 
                t.id,
                t.title,
                t.author,
                t.category,
                t.language,
                LENGTH(t.raw_text) as text_length
            FROM free_will.texts t
            WHERE t.category = category_name
            ORDER BY text_length DESC
            LIMIT result_limit;
        END;
        $$ LANGUAGE plpgsql;
        
        -- Author-based search function
        CREATE OR REPLACE FUNCTION free_will.search_by_author(
            author_name TEXT,
            result_limit INTEGER DEFAULT 10
        )
        RETURNS TABLE(
            id UUID,
            title TEXT,
            author TEXT,
            category TEXT,
            language TEXT,
            text_length INTEGER
        ) AS $$
        BEGIN
            RETURN QUERY
            SELECT 
                t.id,
                t.title,
                t.author,
                t.category,
                t.language,
                LENGTH(t.raw_text) as text_length
            FROM free_will.texts t
            WHERE t.author ILIKE '%' || author_name || '%'
            ORDER BY text_length DESC
            LIMIT result_limit;
        END;
        $$ LANGUAGE plpgsql;
        
        -- New Testament specific search function
        CREATE OR REPLACE FUNCTION free_will.search_new_testament(
            query_text TEXT,
            result_limit INTEGER DEFAULT 10
        )
        RETURNS TABLE(
            id UUID,
            title TEXT,
            author TEXT,
            language TEXT,
            rank REAL,
            snippet TEXT
        ) AS $$
        BEGIN
            RETURN QUERY
            SELECT 
                t.id,
                t.title,
                t.author,
                t.language,
                ts_rank(to_tsvector('greek', t.raw_text), plainto_tsquery('greek', query_text)) as rank,
                ts_headline('greek', t.raw_text, plainto_tsquery('greek', query_text), 
                           'MaxWords=30, MinWords=5, MaxFragments=2') as snippet
            FROM free_will.texts t
            WHERE t.category = 'new_testament'
            AND to_tsvector('greek', t.raw_text) @@ plainto_tsquery('greek', query_text)
            ORDER BY rank DESC
            LIMIT result_limit;
        END;
        $$ LANGUAGE plpgsql;
        """
        
        await self.pg_conn.execute(functions_sql)
        logger.info("Search functions created successfully")
        
    def load_kg_works(self) -> Dict[str, Dict]:
        """Load work nodes from the Knowledge Graph."""
        logger.info("Loading Knowledge Graph works...")
        
        with open(KG_PATH, 'r', encoding='utf-8') as f:
            kg_data = json.load(f)
        
        works = {}
        for node in kg_data.get('nodes', []):
            if node.get('type') == 'work':
                works[node['label'].lower()] = {
                    'id': node['id'],
                    'label': node['label'],
                    'sources': node.get('ancient_sources', [])
                }
        
        logger.info(f"Loaded {len(works)} works from Knowledge Graph")
        return works
        
    def load_sematika_works(self) -> Dict[str, Dict]:
        """Load works from the Sematika MVP SQLite database."""
        logger.info("Loading Sematika MVP works...")
        
        cursor = self.sqlite_conn.cursor()
        cursor.execute("""
            SELECT id, title, author, raw_text, normalized_text, tei_xml, 
                   lemmas, pos_tags, named_entities, embedding, embedding_model,
                   embedding_dimensions, embedding_hash, embedding_created_at,
                   language, date_created, source, notes, metadata
            FROM texts
        """)
        
        works = {}
        for row in cursor.fetchall():
            (text_id, title, author, raw_text, normalized_text, tei_xml,
             lemmas, pos_tags, named_entities, embedding, embedding_model,
             embedding_dimensions, embedding_hash, embedding_created_at,
             language, date_created, source, notes, metadata) = row
            
            if title:
                works[title.lower()] = {
                    'id': text_id,
                    'title': title,
                    'author': author,
                    'raw_text': raw_text,
                    'normalized_text': normalized_text,
                    'tei_xml': tei_xml,
                    'lemmas': json.loads(lemmas) if lemmas else None,
                    'pos_tags': json.loads(pos_tags) if pos_tags else None,
                    'named_entities': json.loads(named_entities) if named_entities else None,
                    'embedding': embedding,
                    'embedding_model': embedding_model,
                    'embedding_dimensions': embedding_dimensions,
                    'embedding_hash': embedding_hash,
                    'embedding_created_at': embedding_created_at,
                    'language': language,
                    'date_created': date_created,
                    'source': source,
                    'notes': notes,
                    'metadata': json.loads(metadata) if metadata else None
                }
        
        logger.info(f"Loaded {len(works)} works from Sematika MVP")
        return works
        
    def categorize_text(self, title: str, author: str) -> str:
        """Categorize a text based on its title and author."""
        title_lower = title.lower()
        author_lower = author.lower() if author else ""
        
        # New Testament
        if any(nt in title_lower for nt in ['matthew', 'mark', 'luke', 'john', 'acts', 'romans', 
                                          'corinthians', 'galatians', 'ephesians', 'philippians',
                                          'colossians', 'thessalonians', 'timothy', 'titus', 
                                          'philemon', 'hebrews', 'james', 'peter', 'jude', 
                                          'revelation', 'apocalypse']):
            return 'new_testament'
            
        # 2nd Century Apologists
        if any(ap in author_lower for ap in ['justin', 'tatian', 'athenagoras', 'theophilus']):
            return 'apologists_2nd_century'
            
        # Origen
        if 'origen' in author_lower or 'origenes' in author_lower:
            return 'origen_works'
            
        # Clement of Alexandria
        if 'clement' in author_lower and 'alexandria' in author_lower:
            return 'clement_works'
            
        # Tertullian
        if 'tertullian' in author_lower:
            return 'tertullian_works'
            
        # Irenaeus
        if 'irenaeus' in author_lower:
            return 'irenaeus_works'
            
        # Original philosophical works
        return 'original_works'
        
    async def migrate_data(self) -> None:
        """Migrate data from SQLite to PostgreSQL."""
        logger.info("Starting data migration...")
        
        kg_works = self.load_kg_works()
        sematika_works = self.load_sematika_works()
        
        # Find matching works
        matched_works = {}
        for kg_label, kg_data in kg_works.items():
            if kg_label in sematika_works:
                matched_works[kg_data['id']] = sematika_works[kg_label]
            else:
                # Try partial matching
                for sematika_label, sematika_data in sematika_works.items():
                    if (kg_label in sematika_label or sematika_label in kg_label or
                        any(word in sematika_label for word in kg_label.split() if len(word) > 3)):
                        matched_works[kg_data['id']] = sematika_data
                        break
        
        logger.info(f"Found {len(matched_works)} matching works to migrate")
        
        # Migrate texts
        migrated_count = 0
        for kg_work_id, text_data in matched_works.items():
            try:
                category = self.categorize_text(text_data['title'], text_data['author'])
                
                # Handle embedding_created_at conversion
                embedding_created_at = None
                if text_data['embedding_created_at']:
                    try:
                        embedding_created_at = datetime.fromisoformat(
                            text_data['embedding_created_at'].replace('Z', '+00:00')
                        )
                    except (ValueError, AttributeError):
                        embedding_created_at = None
                
                # Insert text
                text_id = await self.pg_conn.fetchval("""
                    INSERT INTO free_will.texts (
                        kg_work_id, title, author, category, raw_text, normalized_text,
                        tei_xml, lemmas, pos_tags, named_entities, embedding,
                        embedding_model, embedding_dimensions, embedding_hash,
                        embedding_created_at, language, date_created, source, notes, metadata
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20)
                    RETURNING id
                """, 
                kg_work_id, text_data['title'], text_data['author'], category,
                text_data['raw_text'], text_data['normalized_text'], text_data['tei_xml'],
                json.dumps(text_data['lemmas']) if text_data['lemmas'] else None,
                json.dumps(text_data['pos_tags']) if text_data['pos_tags'] else None,
                json.dumps(text_data['named_entities']) if text_data['named_entities'] else None,
                text_data['embedding'], text_data['embedding_model'], 
                text_data['embedding_dimensions'], text_data['embedding_hash'],
                embedding_created_at, text_data['language'], text_data['date_created'],
                text_data['source'], text_data['notes'], 
                json.dumps(text_data['metadata']) if text_data['metadata'] else None
                )
                
                # Migrate divisions
                await self._migrate_divisions(text_id, text_data['id'])
                
                # Migrate sections
                await self._migrate_sections(text_id, text_data['id'])
                
                migrated_count += 1
                if migrated_count % 50 == 0:
                    logger.info(f"Migrated {migrated_count} texts...")
                    
            except Exception as e:
                logger.error(f"Error migrating text '{text_data['title']}': {e}")
                
        logger.info(f"Migration completed. Migrated {migrated_count} texts.")
        
    async def _migrate_divisions(self, new_text_id: str, old_text_id: str) -> None:
        """Migrate text divisions."""
        cursor = self.sqlite_conn.cursor()
        cursor.execute("""
            SELECT id, parent_id, type, subtype, n, full_reference, heading,
                   language, speaker, char_position, char_length, xml_id
            FROM text_divisions WHERE text_id = ?
        """, (old_text_id,))
        
        divisions = cursor.fetchall()
        division_id_map = {}
        
        # Insert divisions
        for div_row in divisions:
            (div_id, parent_id, type, subtype, n, full_reference, heading,
             language, speaker, char_position, char_length, xml_id) = div_row
            
            new_div_id = await self.pg_conn.fetchval("""
                INSERT INTO free_will.text_divisions (
                    text_id, parent_id, type, subtype, n, full_reference,
                    heading, language, speaker, char_position, char_length, xml_id
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                RETURNING id
            """, 
            new_text_id, None, type, subtype, n, full_reference, heading,
            language, speaker, char_position, char_length, xml_id
            )
            
            division_id_map[div_id] = new_div_id
            
        # Update parent relationships
        for div_row in divisions:
            (div_id, parent_id, _, _, _, _, _, _, _, _, _, _) = div_row
            if parent_id and parent_id in division_id_map:
                await self.pg_conn.execute("""
                    UPDATE free_will.text_divisions 
                    SET parent_id = $1 WHERE id = $2
                """, division_id_map[parent_id], division_id_map[div_id])
                
    async def _migrate_sections(self, new_text_id: str, old_text_id: str) -> None:
        """Migrate text sections."""
        cursor = self.sqlite_conn.cursor()
        cursor.execute("""
            SELECT id, division_id, type, subtype, n, content,
                   language, speaker, char_position, xml_id
            FROM text_sections WHERE text_id = ?
        """, (old_text_id,))
        
        sections = cursor.fetchall()
        
        for sec_row in sections:
            (sec_id, division_id, type, subtype, n, content,
             language, speaker, char_position, xml_id) = sec_row
            
            await self.pg_conn.execute("""
                INSERT INTO free_will.text_sections (
                    text_id, division_id, type, subtype, n, content,
                    language, speaker, char_position, xml_id
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """, 
            new_text_id, division_id, type, subtype, n, content,
            language, speaker, char_position, xml_id
            )
            
    async def create_summary_view(self) -> None:
        """Create a summary view for quick database overview."""
        logger.info("Creating summary view...")
        
        view_sql = """
        CREATE OR REPLACE VIEW free_will.database_summary AS
        SELECT 
            category,
            COUNT(*) as text_count,
            SUM(LENGTH(raw_text)) as total_characters,
            AVG(LENGTH(raw_text)) as avg_text_length,
            COUNT(CASE WHEN lemmas IS NOT NULL THEN 1 END) as texts_with_lemmas,
            COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) as texts_with_embeddings,
            COUNT(CASE WHEN tei_xml IS NOT NULL THEN 1 END) as texts_with_tei_xml
        FROM free_will.texts
        GROUP BY category
        ORDER BY text_count DESC;
        """
        
        await self.pg_conn.execute(view_sql)
        logger.info("Summary view created successfully")
        
    async def run_setup(self) -> None:
        """Run the complete database setup."""
        logger.info("Starting Ancient Free Will Database setup...")
        
        try:
            await self.create_schema()
            await self.create_search_functions()
            await self.migrate_data()
            await self.create_summary_view()
            
            # Display final statistics
            stats = await self.pg_conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_texts,
                    SUM(LENGTH(raw_text)) as total_characters,
                    COUNT(DISTINCT category) as categories,
                    COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) as texts_with_embeddings
                FROM free_will.texts
            """)
            
            logger.info("=" * 60)
            logger.info("SETUP COMPLETED SUCCESSFULLY!")
            logger.info("=" * 60)
            logger.info(f"Total texts: {stats['total_texts']:,}")
            logger.info(f"Total characters: {stats['total_characters'] or 0:,}")
            logger.info(f"Categories: {stats['categories']}")
            logger.info(f"Texts with embeddings: {stats['texts_with_embeddings']}")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Setup failed: {e}")
            raise


async def main():
    """Main function to run the database setup."""
    async with AncientFreeWillDatabaseSetup() as setup:
        await setup.run_setup()


if __name__ == "__main__":
    asyncio.run(main())
