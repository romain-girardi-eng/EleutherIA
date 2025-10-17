# Ancient Free Will Database - PostgreSQL Implementation

A comprehensive PostgreSQL database containing 289 ancient philosophical and theological works relevant to free will debates, with advanced full-text search capabilities, linguistic analysis, and semantic search using Gemini embeddings.

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.8+
- Access to Sematika MVP SQLite database

### Installation

1. **Clone and navigate to the project:**
   ```bash
   cd "/Users/romaingirardi/Documents/Ancient Free Will Database"
   ```

2. **Run the automated setup:**
   ```bash
   ./setup.sh
   ```

This will:
- Start PostgreSQL and PgAdmin with Docker Compose
- Install Python dependencies
- Set up the database schema
- Migrate texts from Sematika MVP
- Run comprehensive tests
- Demonstrate search capabilities

## 📊 Database Overview

- **Total Works:** 289 texts
- **Total Characters:** 35+ million characters
- **Languages:** Greek (225 texts), Latin (64 texts)
- **Categories:** New Testament, Apologists, Origen, Clement, Tertullian, Irenaeus, Original Works
- **Metadata:** 285 texts with embeddings, 109 with lemmas, 289 with TEI XML

## 🔍 Search Capabilities

### Full-Text Search
```sql
-- Greek philosophical concepts
SELECT title, author, rank, snippet
FROM free_will.search_greek_texts('ἐφ ἡμῖν', 10);

-- Latin concepts
SELECT title, author, rank, snippet
FROM free_will.search_greek_texts('libero arbitrio', 10);
```

### Category-Based Search
```sql
-- New Testament texts
SELECT title, author, text_length
FROM free_will.search_by_category('new_testament', 10);

-- Origen's works
SELECT title, author, text_length
FROM free_will.search_by_category('origen_works', 10);
```

### Author Search
```sql
-- All works by Aristotle
SELECT title, author, category, text_length
FROM free_will.search_by_author('Aristotle', 10);
```

## 🛠️ Available Scripts

### Core Scripts
- **`setup_database.py`** - Complete database setup and migration
- **`test_database.py`** - Comprehensive test suite
- **`search_demo.py`** - Search capabilities demonstration
- **`text_access.py`** - Text access and export utilities

### Usage Examples

**Setup Database:**
```bash
python3 setup_database.py
```

**Run Tests:**
```bash
python3 test_database.py
```

**Search Demo:**
```bash
python3 search_demo.py
```

**Export Texts:**
```bash
python3 text_access.py
```

## 📚 Text Categories

### New Testament (57 works)
Complete canonical texts including Gospels, Pauline Epistles, Catholic Epistles, Acts, and Revelation.

### 2nd Century Apologists (13 works)
Early Christian philosophical defenses by Justin Martyr, Tatian, Athenagoras, and Theophilus.

### Origen (48 works)
Systematic theology and biblical commentary, including Commentary on John (1.6M chars) and Contra Celsum (1M+ chars).

### Clement of Alexandria (9 works)
Alexandrian theological synthesis including Paedagogus and Stromata.

### Tertullian (99 works)
Latin theological treatises including Adversus Marcionem (773K+ chars).

### Irenaeus (2 works)
Anti-Gnostic theology including Adversus Haereses.

### Original Philosophical Works (61 works)
Core ancient philosophical texts by Aristotle, Plato, Lucretius, Cicero, Augustine, Seneca, and others.

## 🔧 Database Schema

### Core Tables
- **`free_will.texts`** - Main text storage with metadata
- **`free_will.text_divisions`** - Structural divisions (books, chapters)
- **`free_will.text_sections`** - Text sections (paragraphs, lines)

### Search Functions
- **`search_greek_texts(query, limit)`** - Full-text search with relevance ranking
- **`search_by_category(category, limit)`** - Category-based search
- **`search_by_author(author, limit)`** - Author-specific search
- **`search_new_testament(query, limit)`** - New Testament specific search

## 🌐 Web Interface

Access PgAdmin for visual database management:
- **URL:** http://localhost:8080
- **Email:** admin@ancientfreewill.org
- **Password:** admin123

## 📖 Documentation

- **`POSTGRESQL_FULL_TEXT_SEARCH_DOCUMENTATION.md`** - Comprehensive search documentation
- **`WHERE_ARE_THE_TEXTS_STORED.md`** - Database storage explanation
- **`POSTGRESQL_SETUP_README.md`** - Setup and usage guide

## 🔗 Integration

The database integrates with the Ancient Free Will Database Knowledge Graph through `kg_work_id` fields, enabling seamless research across:
- Structured knowledge (Knowledge Graph)
- Full-text content (PostgreSQL database)
- Linguistic analysis (lemmas, POS tags)
- Semantic search (Gemini embeddings)

## 📈 Performance Features

- **GIN Indexes** for full-text search in Greek and Latin
- **JSONB Indexes** for metadata queries
- **Vector Indexes** for semantic similarity search
- **Connection Pooling** for high performance
- **Async Operations** for scalability

## 🎯 Key Search Terms

### Greek Philosophical Concepts
- **ἐφ ἡμῖν** (eph' hêmin) - "in our power"
- **εἱμαρμένη** (heimarmenê) - "fate"
- **αὐτεξούσιον** (autexousion) - "self-determining power"
- **προαίρεσις** (prohairesis) - "choice"
- **ἑκούσιον** (hekousion) - "voluntary"

### Latin Philosophical Concepts
- **libero arbitrio** - "free will"
- **fatum** - "fate"
- **voluntas** - "will"
- **virtus** - "virtue"
- **gratia** - "grace"

## 📝 Citation and Attribution

All texts maintain proper attribution and source information, with links to original manuscripts, modern scholarly references, and linguistic analysis sources.

---

*This database represents the most comprehensive digital collection of ancient free will debates, spanning from Aristotle (4th c. BCE) through Augustine (5th c. CE), with full-text search capabilities across Greek and Latin philosophical and theological literature.*