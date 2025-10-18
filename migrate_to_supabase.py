#!/usr/bin/env python3
"""
Migrate Data to Supabase PostgreSQL

This script migrates ancient philosophical texts with embeddings from the
local Sematika SQLite database to Supabase PostgreSQL.

Author: Romain Girardi
Date: 2025-10-18
"""

import asyncio
import json
import logging
import sqlite3
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
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

# File paths
KG_PATH = Path("/Users/romaingirardi/Documents/Ancient Free Will Database/ancient_free_will_database.json")
SQLITE_DB_PATH = Path("/Users/romaingirardi/SematikaData/library.db")


class SupabaseMigration:
    """Migrates data from SQLite to Supabase PostgreSQL."""

    def __init__(self):
        self.pg_conn: Optional[asyncpg.Connection] = None
        self.sqlite_conn: Optional[sqlite3.Connection] = None

    async def connect(self) -> None:
        """Establish database connections."""
        try:
            self.pg_conn = await asyncpg.connect(
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                database=POSTGRES_DB,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
                ssl=POSTGRES_SSLMODE,
                statement_cache_size=0  # Required for pgbouncer transaction mode
            )
            self.sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
            logger.info("✅ Database connections established")
        except Exception as e:
            logger.error(f"❌ Failed to establish database connections: {e}")
            raise

    async def close(self) -> None:
        """Close database connections."""
        if self.pg_conn:
            await self.pg_conn.close()
        if self.sqlite_conn:
            self.sqlite_conn.close()
        logger.info("Connections closed")

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
        """Load works with embeddings from the Sematika MVP SQLite database."""
        logger.info("Loading Sematika MVP works with embeddings...")

        cursor = self.sqlite_conn.cursor()
        cursor.execute("""
            SELECT id, title, author, raw_text, normalized_text, tei_xml,
                   lemmas, pos_tags, named_entities, embedding, embedding_model,
                   embedding_dimensions, embedding_hash, embedding_created_at,
                   language, date_created, source, notes, metadata
            FROM texts
            WHERE embedding IS NOT NULL
        """)

        works = {}
        for row in cursor.fetchall():
            (text_id, title, author, raw_text, normalized_text, tei_xml,
             lemmas, pos_tags, named_entities, embedding, embedding_model,
             embedding_dimensions, embedding_hash, embedding_created_at,
             language, date_created, source, notes, metadata) = row

            if title and raw_text:
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

        logger.info(f"Loaded {len(works)} works with embeddings from Sematika")
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
        """Migrate data from SQLite to Supabase PostgreSQL."""
        logger.info("Starting data migration to Supabase...")

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

        logger.info(f"Found {len(matched_works)} matching works with embeddings to migrate")

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
                    ON CONFLICT (kg_work_id) DO NOTHING
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

                if text_id:
                    migrated_count += 1
                    if migrated_count % 10 == 0:
                        logger.info(f"Migrated {migrated_count} texts...")

            except Exception as e:
                logger.error(f"Error migrating text '{text_data['title']}': {e}")

        logger.info(f"✅ Migration completed. Migrated {migrated_count} texts with embeddings.")

    async def run(self) -> None:
        """Run the complete migration process."""
        logger.info("🚀 Starting Supabase Migration")
        logger.info("="*80)
        logger.info(f"PostgreSQL: {POSTGRES_HOST}:{POSTGRES_PORT}")
        logger.info("="*80)

        try:
            await self.connect()
            await self.migrate_data()

            # Display final statistics
            stats = await self.pg_conn.fetchrow("""
                SELECT
                    COUNT(*) as total_texts,
                    SUM(LENGTH(raw_text)) as total_characters,
                    COUNT(DISTINCT category) as categories,
                    COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) as texts_with_embeddings
                FROM free_will.texts
            """)

            logger.info("="*80)
            logger.info("🎉 MIGRATION COMPLETED SUCCESSFULLY!")
            logger.info("="*80)
            logger.info(f"Total texts: {stats['total_texts']:,}")
            logger.info(f"Total characters: {stats['total_characters'] or 0:,}")
            logger.info(f"Categories: {stats['categories']}")
            logger.info(f"Texts with embeddings: {stats['texts_with_embeddings']}")
            logger.info("="*80)

        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            raise
        finally:
            await self.close()


async def main():
    """Main function."""
    migration = SupabaseMigration()
    await migration.run()


if __name__ == "__main__":
    asyncio.run(main())
