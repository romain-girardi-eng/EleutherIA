#!/usr/bin/env python3
"""
EXPANDED PostgreSQL setup for Ancient Free Will Database with ALL major works.
This includes New Testament, 2nd century Apologists, Origen, Clement, Tertullian, etc.
"""

import json
import sqlite3
import asyncpg
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Set, Tuple
from datetime import datetime
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# EXPANDED Free-will related works - now including ALL major ancient philosophical and theological works
EXPANDED_FREE_WILL_WORKS = {
    # Original works from Knowledge Graph
    'work_de_fato_pseudo_plutarch_a8c6d4e2': ['9a3e9455-66ef-4dae-9bf6-c05cd132ded6', 'c5d2a102-79f7-4c7b-92dd-f85e097ef1b9', '1e95f89b-41b6-40b9-a769-e0011a5c0df7', '87dca007-e515-463b-8b0a-48b1d94a2206'],
    'work_de_fato_cicero_44bce_b9c4e5d2': ['9a3e9455-66ef-4dae-9bf6-c05cd132ded6', 'c5d2a102-79f7-4c7b-92dd-f85e097ef1b9', '1e95f89b-41b6-40b9-a769-e0011a5c0df7', '87dca007-e515-463b-8b0a-48b1d94a2206'],
    'work_de_fato_alexander_c200ce_o6p7q8r9': ['9a3e9455-66ef-4dae-9bf6-c05cd132ded6', 'c5d2a102-79f7-4c7b-92dd-f85e097ef1b9', 'b53b25d9-4fbf-4bae-a50a-ab1999e9227c', '1e95f89b-41b6-40b9-a769-e0011a5c0df7', '87dca007-e515-463b-8b0a-48b1d94a2206'],
    'work_nicomachean_ethics_aristotle_c350bce_d3e5f7b9': ['f02c8dc5-67f0-4fd6-a633-dc57ea84941e'],
    'work_de_interpretatione_aristotle_c350bce_e4f6g8h0': ['6b529db4-e6b3-4533-bbc1-061a33484ee7'],
    'work_metaphysics_theta_aristotle_c350bce_f5g7h9i1': ['1b55d6b6-e753-4a44-8702-e26976ac24b6'],
    'work_de_rerum_natura_lucretius_50sbce_l2m3n4o5': ['4c8c1daa-233b-47b5-9978-9630ae810966', '9f7d946e-27ff-49ef-be06-f88dc372ff56'],
    'work_republic_plato_c380bce_c3d4e5f6': ['c4b00273-b729-4cca-9ebf-b63f2868452b', 'cb72a4be-c9ef-4fb1-aeac-f132ba117456'],
    'work_laws_plato_c350bce_d4e5f6g7': ['f735b268-82c4-4176-980a-dbb34d690d83', '370dd185-98dd-40b2-84a9-b9f3823f0ca0'],
    'work_de_libero_arbitrio': ['6a8e9d3f-7f2b-4bf9-b528-0e5b2f64183a', '01c64fc3-78b1-4123-bb92-e950f1a7df72'],
    'work_confessions': ['06db87e3-6345-43c9-a5ed-eda9ae26b207', '05d2f90f-e951-4da4-9f63-4c9d57e9c92e'],
    'work_genesis_u1v2w3x4': ['00ed6784-e922-4ad9-bfca-238b303885c6', '74c3fec4-538b-479f-9949-de01ba3fc8cb', 'dadff9b9-9730-4101-8aac-81081bb65c50'],
    'work_deuteronomy_y5z6a7b8': ['dbd7eae2-47cf-48e4-bdf7-82ed4d2222ad'],
    'work_exodus_c9d0e1f2': ['3888b128-6003-4b2b-afbf-e897664a74d5', '57be8e98-bb33-4fdf-ae9b-1628a041db91', '6962982d-3070-4e30-a4cd-01f22c0c8263'],
    'work_job_o1p2q3r4': ['fa83f192-1873-4e42-8776-1fd6096ad741', '4feba4c2-7539-445e-8187-d0f44fcc50e5', 'cc491358-0670-4bc5-9651-a25598a5bb37'],
    'work_proverbs_s5t6u7v8': ['e60a0adb-118b-440c-8590-7a3473afbec0'],
    'work_ecclesiastes_w9x0y1z2': ['db21bb49-3da4-46ee-aab0-5fe5279ead32', '5186f353-9e3a-4b88-b7b1-1ae8ee9a9797'],
    'work_sirach_a3b4c5d6': ['d3097d01-733a-4ee3-8702-c70f14ad2e19', 'b29d8b54-0ba9-4fa3-95d1-424a3f24a798', '6fdfcf9f-87e0-4ddc-8852-aa1f68197b7c'],
    
    # NEW: All New Testament works (crucial for early Christian free will debates)
    'new_testament_gospels': [],  # Will be populated dynamically
    'new_testament_pauline_epistles': [],  # Will be populated dynamically
    'new_testament_catholic_epistles': [],  # Will be populated dynamically
    'new_testament_acts_revelation': [],  # Will be populated dynamically
    
    # NEW: 2nd Century Apologists (crucial for early Christian philosophy)
    'justin_martyr_apologies': [],  # Will be populated dynamically
    'tatian_oratio_ad_graecos': [],  # Will be populated dynamically
    'athenagoras_works': [],  # Will be populated dynamically
    'theophilus_ad_autolycum': [],  # Will be populated dynamically
    
    # NEW: Major Early Christian Theologians
    'origen_works': [],  # Will be populated dynamically
    'clement_of_alexandria_works': [],  # Will be populated dynamically
    'tertullian_works': [],  # Will be populated dynamically
    'irenaeus_works': [],  # Will be populated dynamically
}

class ExpandedFreeWillPostgresSetup:
    """Expanded PostgreSQL setup with ALL major ancient philosophical and theological works."""
    
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
                min_size=5,
                max_size=10,
                command_timeout=60,
            )
            logger.info(f"PostgreSQL pool initialized: {self.host}:{self.port}/{self.database}")
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL pool: {e}")
            raise
    
    async def close(self):
        """Close PostgreSQL connection pool."""
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("PostgreSQL pool closed")
    
    def discover_all_relevant_works(self) -> Dict[str, List[str]]:
        """Discover all relevant works from Sematika MVP database."""
        db_path = "/Users/romaingirardi/SematikaData/library.db"
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all texts
        cursor.execute("SELECT id, title, author, language FROM texts")
        all_texts = cursor.fetchall()
        
        # Categories for free-will related works
        categories = {
            'new_testament': [],
            'apologists_2nd_century': [],
            'origen_works': [],
            'clement_works': [],
            'tertullian_works': [],
            'irenaeus_works': [],
            'original_works': []  # Keep original works
        }
        
        # Keywords for free-will related content
        free_will_keywords = [
            'fate', 'fatum', 'εἱμαρμένη', 'heimarmenê',
            'free will', 'libero arbitrio', 'ἐφ ἡμῖν', 'eph\' hêmin',
            'necessity', 'necessitas', 'ἀνάγκη', 'anankê',
            'choice', 'προαίρεσις', 'prohairesis',
            'voluntary', 'ἑκούσιον', 'hekousion',
            'involuntary', 'ἀκούσιον', 'akousion',
            'virtue', 'virtus', 'ἀρετή', 'aretê',
            'vice', 'vitium', 'κακία', 'kakia',
            'will', 'voluntas', 'αὐτεξούσιον', 'autexousion',
            'deliberation', 'βούλευσις', 'bouleusis',
            'responsibility', 'moral', 'ethics'
        ]
        
        for text_id, title, author, language in all_texts:
            title_lower = title.lower() if title else ""
            author_lower = author.lower() if author else ""
            
            # New Testament works
            if author == "New Testament" or "testament" in title_lower:
                categories['new_testament'].append(text_id)
            
            # 2nd Century Apologists
            elif any(apologist in author_lower for apologist in ['justin', 'tatian', 'athenagoras', 'theophilus']):
                categories['apologists_2nd_century'].append(text_id)
            
            # Origen
            elif 'origen' in author_lower:
                categories['origen_works'].append(text_id)
            
            # Clement of Alexandria
            elif 'clement' in author_lower and 'alexandria' in author_lower:
                categories['clement_works'].append(text_id)
            
            # Tertullian
            elif 'tertullian' in author_lower:
                categories['tertullian_works'].append(text_id)
            
            # Irenaeus
            elif 'irenaeus' in author_lower:
                categories['irenaeus_works'].append(text_id)
            
            # Check for free-will related keywords in title
            elif any(keyword in title_lower for keyword in free_will_keywords):
                categories['original_works'].append(text_id)
            
            # Original works from Knowledge Graph (keep existing)
            elif text_id in [id for ids in EXPANDED_FREE_WILL_WORKS.values() for id in ids]:
                categories['original_works'].append(text_id)
        
        conn.close()
        
        # Log discoveries
        logger.info("🔍 DISCOVERED WORKS FOR EXPANDED FREE-WILL DATABASE:")
        logger.info("=" * 60)
        for category, works in categories.items():
            logger.info(f"{category}: {len(works)} works")
        
        return categories
    
    async def create_expanded_schema(self):
        """Create expanded database schema."""
        async with self.pool.acquire() as conn:
            # Drop existing schema to recreate with expanded data
            await conn.execute("DROP SCHEMA IF EXISTS free_will CASCADE")
            
            await conn.execute("""
                -- Create expanded schema for Ancient Free Will Database
                CREATE SCHEMA free_will;
                
                -- Enhanced texts table with ALL metadata
                CREATE TABLE free_will.texts (
                    id TEXT PRIMARY KEY,
                    kg_work_id TEXT, -- Link to Ancient Free Will Database work ID
                    category TEXT, -- Category: 'new_testament', 'apologists', 'origen', etc.
                    file_id TEXT,
                    title TEXT NOT NULL,
                    author TEXT,
                    raw_text TEXT NOT NULL,
                    normalized_text TEXT,
                    
                    -- TEI XML and linguistic analysis
                    tei_xml TEXT,
                    lemmas JSONB, -- JSON array of lemmas
                    pos_tags JSONB, -- JSON array of POS tags
                    named_entities JSONB, -- JSON array of named entities
                    
                    -- Embeddings
                    embedding BYTEA,
                    embedding_model TEXT,
                    embedding_dimensions INTEGER,
                    embedding_hash TEXT,
                    embedding_created_at TIMESTAMP,
                    
                    -- Metadata
                    language TEXT DEFAULT 'grc',
                    date_created TEXT,
                    source TEXT,
                    notes TEXT,
                    metadata JSONB,
                    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Text divisions (books, chapters, sections)
                CREATE TABLE IF NOT EXISTS free_will.text_divisions (
                    id TEXT PRIMARY KEY,
                    text_id TEXT NOT NULL,
                    parent_id TEXT,
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (text_id) REFERENCES free_will.texts(id) ON DELETE CASCADE,
                    FOREIGN KEY (parent_id) REFERENCES free_will.text_divisions(id) ON DELETE CASCADE
                );
                
                -- Text sections (paragraphs, lines, verses)
                CREATE TABLE IF NOT EXISTS free_will.text_sections (
                    id TEXT PRIMARY KEY,
                    text_id TEXT NOT NULL,
                    division_id TEXT,
                    type TEXT NOT NULL,
                    subtype TEXT,
                    n TEXT,
                    content TEXT NOT NULL,
                    language TEXT,
                    speaker TEXT,
                    char_position INTEGER,
                    xml_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (text_id) REFERENCES free_will.texts(id) ON DELETE CASCADE,
                    FOREIGN KEY (division_id) REFERENCES free_will.text_divisions(id) ON DELETE CASCADE
                );
                
                -- Page breaks (Stephanus, Bekker numbers, etc.)
                CREATE TABLE IF NOT EXISTS free_will.text_page_breaks (
                    id TEXT PRIMARY KEY,
                    text_id TEXT NOT NULL,
                    n TEXT NOT NULL,
                    edition TEXT,
                    unit TEXT,
                    char_position INTEGER,
                    division_id TEXT,
                    section_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (text_id) REFERENCES free_will.texts(id) ON DELETE CASCADE,
                    FOREIGN KEY (division_id) REFERENCES free_will.text_divisions(id) ON DELETE SET NULL,
                    FOREIGN KEY (section_id) REFERENCES free_will.text_sections(id) ON DELETE SET NULL
                );
                
                -- Milestones (alternative numbering systems)
                CREATE TABLE IF NOT EXISTS free_will.text_milestones (
                    id TEXT PRIMARY KEY,
                    text_id TEXT NOT NULL,
                    unit TEXT NOT NULL,
                    n TEXT NOT NULL,
                    char_position INTEGER,
                    division_id TEXT,
                    section_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (text_id) REFERENCES free_will.texts(id) ON DELETE CASCADE,
                    FOREIGN KEY (division_id) REFERENCES free_will.text_divisions(id) ON DELETE SET NULL,
                    FOREIGN KEY (section_id) REFERENCES free_will.text_sections(id) ON DELETE SET NULL
                );
                
                -- Citation systems
                CREATE TABLE IF NOT EXISTS free_will.text_citation_systems (
                    id TEXT PRIMARY KEY,
                    text_id TEXT NOT NULL,
                    system_name TEXT NOT NULL,
                    system_type TEXT NOT NULL,
                    description TEXT,
                    is_primary BOOLEAN DEFAULT FALSE,
                    pattern TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (text_id) REFERENCES free_will.texts(id) ON DELETE CASCADE
                );
                
                -- Text apparatus (variants)
                CREATE TABLE IF NOT EXISTS free_will.text_apparatus (
                    id TEXT PRIMARY KEY,
                    text_id TEXT NOT NULL,
                    lemma TEXT NOT NULL,
                    reading TEXT,
                    witness TEXT,
                    type TEXT,
                    char_position INTEGER,
                    section_id TEXT,
                    note TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (text_id) REFERENCES free_will.texts(id) ON DELETE CASCADE,
                    FOREIGN KEY (section_id) REFERENCES free_will.text_sections(id) ON DELETE SET NULL
                );
                
                -- Text notes and commentary
                CREATE TABLE IF NOT EXISTS free_will.text_notes (
                    id TEXT PRIMARY KEY,
                    text_id TEXT NOT NULL,
                    note_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    target_id TEXT,
                    target_type TEXT,
                    char_position INTEGER,
                    author TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (text_id) REFERENCES free_will.texts(id) ON DELETE CASCADE
                );
                
                -- Create indexes for better performance
                CREATE INDEX IF NOT EXISTS idx_texts_category ON free_will.texts(category);
                CREATE INDEX IF NOT EXISTS idx_texts_kg_work_id ON free_will.texts(kg_work_id);
                CREATE INDEX IF NOT EXISTS idx_texts_author ON free_will.texts(author);
                CREATE INDEX IF NOT EXISTS idx_texts_title ON free_will.texts(title);
                CREATE INDEX IF NOT EXISTS idx_texts_language ON free_will.texts(language);
                CREATE INDEX IF NOT EXISTS idx_text_divisions_text_id ON free_will.text_divisions(text_id);
                CREATE INDEX IF NOT EXISTS idx_text_sections_text_id ON free_will.text_sections(text_id);
                CREATE INDEX IF NOT EXISTS idx_text_sections_division_id ON free_will.text_sections(division_id);
                CREATE INDEX IF NOT EXISTS idx_text_page_breaks_text_id ON free_will.text_page_breaks(text_id);
                CREATE INDEX IF NOT EXISTS idx_text_milestones_text_id ON free_will.text_milestones(text_id);
                
                -- Create GIN indexes for JSONB columns
                CREATE INDEX IF NOT EXISTS idx_texts_lemmas_gin ON free_will.texts USING GIN (lemmas);
                CREATE INDEX IF NOT EXISTS idx_texts_pos_tags_gin ON free_will.texts USING GIN (pos_tags);
                CREATE INDEX IF NOT EXISTS idx_texts_named_entities_gin ON free_will.texts USING GIN (named_entities);
                CREATE INDEX IF NOT EXISTS idx_texts_metadata_gin ON free_will.texts USING GIN (metadata);
            """)
            
            # Create full-text search indexes
            await conn.execute("""
                -- Create full-text search indexes for Greek and Latin texts
                CREATE INDEX IF NOT EXISTS idx_texts_raw_text_fts 
                ON free_will.texts USING GIN (to_tsvector('greek', raw_text));
                
                CREATE INDEX IF NOT EXISTS idx_texts_normalized_text_fts 
                ON free_will.texts USING GIN (to_tsvector('greek', normalized_text));
                
                CREATE INDEX IF NOT EXISTS idx_text_sections_content_fts 
                ON free_will.text_sections USING GIN (to_tsvector('greek', content));
                
                -- Create full-text search indexes for titles and authors
                CREATE INDEX IF NOT EXISTS idx_texts_title_fts 
                ON free_will.texts USING GIN (to_tsvector('simple', title));
                
                CREATE INDEX IF NOT EXISTS idx_texts_author_fts 
                ON free_will.texts USING GIN (to_tsvector('simple', author));
            """)
            
            logger.info("Expanded database schema created successfully")
    
    def load_all_sematika_data(self) -> Dict[str, Dict]:
        """Load all data from Sematika MVP SQLite database."""
        db_path = "/Users/romaingirardi/SematikaData/library.db"
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all texts with their metadata
        cursor.execute("""
            SELECT id, file_id, title, author, raw_text, normalized_text, tei_xml,
                   lemmas, pos_tags, named_entities, language, date_created, 
                   source, notes, metadata, embedding, embedding_model, 
                   embedding_dimensions, embedding_hash, embedding_created_at
            FROM texts
        """)
        texts = cursor.fetchall()
        
        result = {}
        for row in texts:
            text_id, file_id, title, author, raw_text, normalized_text, tei_xml, \
            lemmas, pos_tags, named_entities, language, date_created, source, \
            notes, metadata, embedding, embedding_model, embedding_dimensions, \
            embedding_hash, embedding_created_at = row
            
            result[text_id] = {
                'file_id': file_id,
                'title': title or '',
                'author': author or '',
                'raw_text': raw_text or '',
                'normalized_text': normalized_text or '',
                'tei_xml': tei_xml,
                'lemmas': lemmas,
                'pos_tags': pos_tags,
                'named_entities': named_entities,
                'language': language or 'grc',
                'date_created': date_created or '',
                'source': source or '',
                'notes': notes or '',
                'metadata': metadata or '{}',
                'embedding': embedding,
                'embedding_model': embedding_model or '',
                'embedding_dimensions': embedding_dimensions or 0,
                'embedding_hash': embedding_hash or '',
                'embedding_created_at': embedding_created_at
            }
        
        conn.close()
        return result
    
    def load_all_sematika_divisions(self) -> Dict[str, List[Dict]]:
        """Load text divisions from Sematika MVP database."""
        db_path = "/Users/romaingirardi/SematikaData/library.db"
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, text_id, parent_id, type, subtype, n, full_reference,
                   heading, language, speaker, char_position, char_length, xml_id
            FROM text_divisions
        """)
        divisions = cursor.fetchall()
        
        result = {}
        for row in divisions:
            div_id, text_id, parent_id, type_, subtype, n, full_reference, \
            heading, language, speaker, char_position, char_length, xml_id = row
            
            if text_id not in result:
                result[text_id] = []
            
            result[text_id].append({
                'id': div_id,
                'parent_id': parent_id,
                'type': type_,
                'subtype': subtype,
                'n': n,
                'full_reference': full_reference,
                'heading': heading,
                'language': language,
                'speaker': speaker,
                'char_position': char_position,
                'char_length': char_length,
                'xml_id': xml_id
            })
        
        conn.close()
        return result
    
    def load_all_sematika_sections(self) -> Dict[str, List[Dict]]:
        """Load text sections from Sematika MVP database."""
        db_path = "/Users/romaingirardi/SematikaData/library.db"
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, text_id, division_id, type, subtype, n, content,
                   language, speaker, char_position, xml_id
            FROM text_sections
        """)
        sections = cursor.fetchall()
        
        result = {}
        for row in sections:
            sec_id, text_id, division_id, type_, subtype, n, content, \
            language, speaker, char_position, xml_id = row
            
            if text_id not in result:
                result[text_id] = []
            
            result[text_id].append({
                'id': sec_id,
                'division_id': division_id,
                'type': type_,
                'subtype': subtype,
                'n': n,
                'content': content,
                'language': language,
                'speaker': speaker,
                'char_position': char_position,
                'xml_id': xml_id
            })
        
        conn.close()
        return result
    
    async def import_expanded_data(self):
        """Import ALL relevant free-will related data."""
        logger.info("Loading expanded data from Sematika MVP database...")
        
        # Discover all relevant works
        categories = self.discover_all_relevant_works()
        
        # Load all data
        texts_data = self.load_all_sematika_data()
        divisions_data = self.load_all_sematika_divisions()
        sections_data = self.load_all_sematika_sections()
        
        # Collect all text IDs that are free-will related
        all_free_will_text_ids = set()
        for category_works in categories.values():
            all_free_will_text_ids.update(category_works)
        
        logger.info(f"Found {len(all_free_will_text_ids)} total free-will related texts to import")
        
        async with self.pool.acquire() as conn:
            # Clear existing data
            await conn.execute("DELETE FROM free_will.text_sections")
            await conn.execute("DELETE FROM free_will.text_divisions")
            await conn.execute("DELETE FROM free_will.texts")
            
            imported_count = 0
            for text_id in all_free_will_text_ids:
                if text_id in texts_data:
                    text_data = texts_data[text_id]
                    
                    # Determine category
                    category = 'original_works'  # default
                    for cat_name, cat_works in categories.items():
                        if text_id in cat_works:
                            category = cat_name
                            break
                    
                    # Find the corresponding KG work ID (if any)
                    kg_work_id = None
                    for kg_id, sematika_ids in EXPANDED_FREE_WILL_WORKS.items():
                        if text_id in sematika_ids:
                            kg_work_id = kg_id
                            break
                    
                    # Convert datetime string to datetime object if needed
                    embedding_created_at = None
                    if text_data['embedding_created_at']:
                        try:
                            embedding_created_at = datetime.fromisoformat(text_data['embedding_created_at'].replace('Z', '+00:00'))
                        except (ValueError, TypeError):
                            embedding_created_at = None
                    
                    # Insert expanded text data
                    await conn.execute("""
                        INSERT INTO free_will.texts (
                            id, kg_work_id, category, file_id, title, author, raw_text, normalized_text,
                            tei_xml, lemmas, pos_tags, named_entities, language, date_created,
                            source, notes, metadata, embedding, embedding_model,
                            embedding_dimensions, embedding_hash, embedding_created_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22)
                    """, 
                        text_id,
                        kg_work_id,
                        category,
                        text_data['file_id'],
                        text_data['title'],
                        text_data['author'],
                        text_data['raw_text'],
                        text_data['normalized_text'],
                        text_data['tei_xml'],
                        text_data['lemmas'],
                        text_data['pos_tags'],
                        text_data['named_entities'],
                        text_data['language'],
                        text_data['date_created'],
                        text_data['source'],
                        text_data['notes'],
                        text_data['metadata'],
                        text_data['embedding'],
                        text_data['embedding_model'],
                        text_data['embedding_dimensions'],
                        text_data['embedding_hash'],
                        embedding_created_at
                    )
                    
                    # Import divisions
                    if text_id in divisions_data:
                        for div_data in divisions_data[text_id]:
                            await conn.execute("""
                                INSERT INTO free_will.text_divisions (
                                    id, text_id, parent_id, type, subtype, n, full_reference,
                                    heading, language, speaker, char_position, char_length, xml_id
                                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                            """, 
                                div_data['id'], text_id, div_data['parent_id'], div_data['type'],
                                div_data['subtype'], div_data['n'], div_data['full_reference'],
                                div_data['heading'], div_data['language'], div_data['speaker'],
                                div_data['char_position'], div_data['char_length'], div_data['xml_id']
                            )
                    
                    # Import sections
                    if text_id in sections_data:
                        for sec_data in sections_data[text_id]:
                            await conn.execute("""
                                INSERT INTO free_will.text_sections (
                                    id, text_id, division_id, type, subtype, n, content,
                                    language, speaker, char_position, xml_id
                                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                            """, 
                                sec_data['id'], text_id, sec_data['division_id'], sec_data['type'],
                                sec_data['subtype'], sec_data['n'], sec_data['content'],
                                sec_data['language'], sec_data['speaker'], sec_data['char_position'],
                                sec_data['xml_id']
                            )
                    
                    imported_count += 1
                    if imported_count % 50 == 0:  # Log progress every 50 texts
                        logger.info(f"Imported {imported_count} texts...")
        
        logger.info(f"Successfully imported {imported_count} expanded free-will related texts")
    
    async def create_expanded_fts_functions(self):
        """Create expanded full-text search functions."""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                -- Create function for Greek full-text search
                CREATE OR REPLACE FUNCTION free_will.search_greek_texts(
                    search_query TEXT,
                    limit_count INTEGER DEFAULT 10
                )
                RETURNS TABLE (
                    id TEXT,
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
                        ts_rank(to_tsvector('greek', t.raw_text), plainto_tsquery('greek', search_query)) as rank,
                        ts_headline('greek', t.raw_text, plainto_tsquery('greek', search_query), 
                                   'MaxWords=50, MinWords=10, MaxFragments=3') as snippet
                    FROM free_will.texts t
                    WHERE to_tsvector('greek', t.raw_text) @@ plainto_tsquery('greek', search_query)
                    ORDER BY rank DESC
                    LIMIT limit_count;
                END;
                $$ LANGUAGE plpgsql;
                
                -- Create function for category-based search
                CREATE OR REPLACE FUNCTION free_will.search_by_category(
                    category_query TEXT,
                    limit_count INTEGER DEFAULT 10
                )
                RETURNS TABLE (
                    id TEXT,
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
                    WHERE t.category = category_query
                    ORDER BY text_length DESC
                    LIMIT limit_count;
                END;
                $$ LANGUAGE plpgsql;
                
                -- Create function for New Testament search
                CREATE OR REPLACE FUNCTION free_will.search_new_testament(
                    search_query TEXT,
                    limit_count INTEGER DEFAULT 10
                )
                RETURNS TABLE (
                    id TEXT,
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
                        ts_rank(to_tsvector('greek', t.raw_text), plainto_tsquery('greek', search_query)) as rank,
                        ts_headline('greek', t.raw_text, plainto_tsquery('greek', search_query), 
                                   'MaxWords=50, MinWords=10, MaxFragments=3') as snippet
                    FROM free_will.texts t
                    WHERE t.category = 'new_testament'
                    AND to_tsvector('greek', t.raw_text) @@ plainto_tsquery('greek', search_query)
                    ORDER BY rank DESC
                    LIMIT limit_count;
                END;
                $$ LANGUAGE plpgsql;
            """)
            logger.info("Expanded full-text search functions created successfully")
    
    async def generate_expanded_report(self):
        """Generate expanded report of imported data."""
        async with self.pool.acquire() as conn:
            # Get total counts
            total_texts = await conn.fetchval("SELECT COUNT(*) FROM free_will.texts")
            total_divisions = await conn.fetchval("SELECT COUNT(*) FROM free_will.text_divisions")
            total_sections = await conn.fetchval("SELECT COUNT(*) FROM free_will.text_sections")
            
            # Get texts with different types of metadata
            with_lemmas = await conn.fetchval("SELECT COUNT(*) FROM free_will.texts WHERE lemmas IS NOT NULL")
            with_pos_tags = await conn.fetchval("SELECT COUNT(*) FROM free_will.texts WHERE pos_tags IS NOT NULL")
            with_named_entities = await conn.fetchval("SELECT COUNT(*) FROM free_will.texts WHERE named_entities IS NOT NULL")
            with_embeddings = await conn.fetchval("SELECT COUNT(*) FROM free_will.texts WHERE embedding IS NOT NULL")
            with_tei_xml = await conn.fetchval("SELECT COUNT(*) FROM free_will.texts WHERE tei_xml IS NOT NULL")
            
            # Get texts by category
            categories = await conn.fetch("""
                SELECT category, COUNT(*) as count 
                FROM free_will.texts 
                GROUP BY category 
                ORDER BY count DESC
            """)
            
            # Get texts by language
            languages = await conn.fetch("""
                SELECT language, COUNT(*) as count 
                FROM free_will.texts 
                GROUP BY language 
                ORDER BY count DESC
            """)
            
            # Get texts by author
            authors = await conn.fetch("""
                SELECT author, COUNT(*) as count 
                FROM free_will.texts 
                WHERE author IS NOT NULL AND author != ''
                GROUP BY author 
                ORDER BY count DESC
                LIMIT 15
            """)
            
            logger.info("=" * 80)
            logger.info("EXPANDED ANCIENT FREE WILL DATABASE - POSTGRESQL SETUP REPORT")
            logger.info("=" * 80)
            logger.info(f"Total texts imported: {total_texts}")
            logger.info(f"Total divisions: {total_divisions}")
            logger.info(f"Total sections: {total_sections}")
            logger.info("")
            logger.info("Metadata Coverage:")
            logger.info(f"  Texts with lemmas: {with_lemmas}")
            logger.info(f"  Texts with POS tags: {with_pos_tags}")
            logger.info(f"  Texts with named entities: {with_named_entities}")
            logger.info(f"  Texts with embeddings: {with_embeddings}")
            logger.info(f"  Texts with TEI XML: {with_tei_xml}")
            logger.info("")
            logger.info("Texts by Category:")
            for category in categories:
                logger.info(f"  {category['category']}: {category['count']}")
            logger.info("")
            logger.info("Texts by Language:")
            for language in languages:
                logger.info(f"  {language['language']}: {language['count']}")
            logger.info("")
            logger.info("Top Authors:")
            for author in authors:
                logger.info(f"  {author['author']}: {author['count']}")
            logger.info("=" * 80)

async def main():
    """Main expanded setup function."""
    setup = ExpandedFreeWillPostgresSetup()
    
    try:
        await setup.initialize()
        await setup.create_expanded_schema()
        await setup.import_expanded_data()
        await setup.create_expanded_fts_functions()
        await setup.generate_expanded_report()
        
        logger.info("Expanded PostgreSQL setup completed successfully!")
        logger.info("Now includes New Testament, Apologists, Origen, Clement, Tertullian, and more!")
        
    except Exception as e:
        logger.error(f"Expanded setup failed: {e}")
        raise
    finally:
        await setup.close()

if __name__ == "__main__":
    asyncio.run(main())
