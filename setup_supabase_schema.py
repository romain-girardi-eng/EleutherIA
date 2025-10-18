#!/usr/bin/env python3
"""
Supabase Schema Setup for Ancient Free Will Database

This script creates just the database schema on Supabase PostgreSQL
without requiring data migration from SQLite.

Author: Romain Girardi
Date: 2025-10-18
"""

import asyncio
import logging
import os
from dotenv import load_dotenv
import asyncpg

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Supabase configuration from environment
POSTGRES_HOST = os.getenv('POSTGRES_HOST')
POSTGRES_PORT = int(os.getenv('POSTGRES_PORT'))
POSTGRES_DB = os.getenv('POSTGRES_DB')
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
POSTGRES_SSLMODE = os.getenv('POSTGRES_SSLMODE', 'require')


async def setup_schema():
    """Create the free_will schema and tables on Supabase."""
    logger.info("🚀 Starting Supabase Schema Setup")
    logger.info("="*80)
    logger.info(f"Connecting to: {POSTGRES_HOST}:{POSTGRES_PORT}")
    logger.info("="*80)

    try:
        # Connect to Supabase
        conn = await asyncpg.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            ssl=POSTGRES_SSLMODE,
            statement_cache_size=0  # Required for pgbouncer transaction mode
        )
        logger.info("✅ Connected to Supabase PostgreSQL")

        # Create schema
        schema_sql = """
        -- Create free_will schema if it doesn't exist
        CREATE SCHEMA IF NOT EXISTS free_will;

        -- Main texts table
        CREATE TABLE IF NOT EXISTS free_will.texts (
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
        CREATE TABLE IF NOT EXISTS free_will.text_divisions (
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
        CREATE TABLE IF NOT EXISTS free_will.text_sections (
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
        CREATE INDEX IF NOT EXISTS idx_texts_title ON free_will.texts (title);
        CREATE INDEX IF NOT EXISTS idx_texts_author ON free_will.texts (author);
        CREATE INDEX IF NOT EXISTS idx_texts_category ON free_will.texts (category);
        CREATE INDEX IF NOT EXISTS idx_texts_kg_work_id ON free_will.texts (kg_work_id);
        CREATE INDEX IF NOT EXISTS idx_texts_language ON free_will.texts (language);
        CREATE INDEX IF NOT EXISTS idx_text_divisions_text_id ON free_will.text_divisions (text_id);
        CREATE INDEX IF NOT EXISTS idx_text_sections_text_id ON free_will.text_sections (text_id);
        CREATE INDEX IF NOT EXISTS idx_text_sections_division_id ON free_will.text_sections (division_id);

        -- Full-text search indexes
        CREATE INDEX IF NOT EXISTS idx_texts_fts_greek ON free_will.texts
            USING gin(to_tsvector('greek', raw_text)) WHERE language = 'grc';
        CREATE INDEX IF NOT EXISTS idx_texts_fts_latin ON free_will.texts
            USING gin(to_tsvector('simple', raw_text)) WHERE language = 'lat';
        """

        await conn.execute(schema_sql)
        logger.info("✅ Schema and tables created successfully")

        # Check existing data
        count = await conn.fetchval("SELECT COUNT(*) FROM free_will.texts")
        logger.info(f"📊 Current text count: {count}")

        await conn.close()
        logger.info("="*80)
        logger.info("🎉 SUPABASE SCHEMA SETUP COMPLETE!")
        logger.info("="*80)

    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(setup_schema())
