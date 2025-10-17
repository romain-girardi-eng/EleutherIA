# Ancient Free Will Database - PostgreSQL Full-Text Search Documentation

## 🚀 Overview

The Ancient Free Will Database PostgreSQL implementation provides **comprehensive full-text search capabilities** across 289 ancient philosophical and theological works, with advanced linguistic analysis and semantic search using Gemini embeddings.

## 📊 Database Statistics

- **Total Works:** 289 texts
- **Total Divisions:** 36,864 structural divisions
- **Total Sections:** 144,485 text sections
- **Languages:** 225 Greek texts, 64 Latin texts
- **Metadata Coverage:** 109 texts with lemmas, 285 with embeddings, 289 with TEI XML

## 🔍 Search Capabilities

### 1. **Full-Text Search (FTS)**
PostgreSQL's native full-text search with Greek and Latin language support:

```sql
-- Greek full-text search
SELECT title, author, rank, snippet
FROM free_will.search_greek_texts('ἐφ ἡμῖν', 10);

-- Latin full-text search  
SELECT title, author, rank, snippet
FROM free_will.search_greek_texts('libero arbitrio', 10);
```

### 2. **Lemma-Based Search**
Search through linguistic analysis data:

```sql
-- Search by lemmas
SELECT title, author, lemmas
FROM free_will.search_by_lemmas('προαίρεσις', 10);

-- Advanced lemma queries
SELECT title, author, lemmas
FROM free_will.texts 
WHERE lemmas::text ILIKE '%ἐφ ἡμῖν%'
AND jsonb_typeof(lemmas) = 'array';
```

### 3. **Semantic Search with Gemini Embeddings**
Vector similarity search using Gemini embeddings:

```sql
-- Find semantically similar texts
SELECT title, author, 
       1 - (embedding <=> $1::vector) as similarity
FROM free_will.texts 
WHERE embedding IS NOT NULL
ORDER BY similarity DESC
LIMIT 10;
```

### 4. **Category-Based Search**
Search within specific categories:

```sql
-- New Testament search
SELECT title, author, rank, snippet
FROM free_will.search_new_testament('grace', 10);

-- Search by category
SELECT title, author, text_length
FROM free_will.search_by_category('origen_works', 10);
```

## 📚 Complete Text Collection

### **New Testament (57 works)**
Complete canonical texts with full-text search:

- **Gospels:** Matthew, Mark, Luke, John (multiple versions)
- **Pauline Epistles:** Romans, Corinthians, Galatians, Ephesians, Philippians, Colossians, Thessalonians, Timothy, Titus, Philemon
- **Catholic Epistles:** James, Peter, John, Jude
- **Acts of the Apostles**
- **Revelation**
- **Total:** 1.8M+ characters

### **2nd Century Apologists (13 works)**
Early Christian philosophical defenses:

- **Justin Martyr:** Apologia I & II, Dialogue with Trypho
- **Tatian:** Oratio ad Graecos
- **Athenagoras:** Supplicatio pro Christianis, De Resurrectione Mortuorum
- **Theophilus:** Ad Autolycum (Libri Tres)
- **Total:** 580K+ characters

### **Origen (48 works)**
Systematic theology and biblical commentary:

- **Commentary on John** (1.6M characters)
- **Contra Celsum** (1M+ characters)
- **Commentary on Matthew** (multiple versions)
- **Homilies:** Luke, Jeremiah, Psalms, Genesis, Exodus
- **Philocalia**
- **Selecta in Psalmos**
- **Total:** 8.7M+ characters

### **Clement of Alexandria (9 works)**
Alexandrian theological synthesis:

- **Paedagogus** (400K characters)
- **Protrepticus** (multiple versions)
- **Stromata** (Books 7-8)
- **Quis Dives Salvetur**
- **Excerpta ex Theodoto**
- **Eclogae propheticae**
- **Total:** 1.1M+ characters

### **Tertullian (99 works)**
Latin theological treatises:

- **Adversus Marcionem** (multiple versions, 773K+ chars)
- **De Anima** (multiple versions)
- **De Carnis Resurrectione**
- **Ad Nationes Libri Duo**
- **De Praescriptionibus Hereticorum**
- **De Spectaculis**
- **Total:** 8.3M+ characters

### **Irenaeus (2 works)**
Anti-Gnostic theology:

- **Adversus Haereses** (209K characters)
- **Fragmenta Synodicae Epistulae**

### **Original Philosophical Works (61 works)**
Core ancient philosophical texts:

- **Aristotle:** Nicomachean Ethics, De Interpretatione, Metaphysics
- **Plato:** Republic, Laws (multiple versions)
- **Lucretius:** De Rerum Natura (Latin & Greek)
- **Cicero:** De Fato (Latin & Greek)
- **Alexander of Aphrodisias:** De fato
- **Plutarch:** De fato, Περὶ εἱμαρμένης
- **Augustine:** Confessiones (Latin & Greek)
- **Methodius:** De Libero Arbitrio (multiple versions)
- **Seneca:** Epistulae, De Beneficiis, De Clementia
- **Biblical Texts:** Genesis, Exodus, Deuteronomy, Job, Proverbs, Ecclesiastes, Ecclesiasticus (Septuagint & Vulgate)

## 🛠️ Database Schema

### **Core Tables**

#### `free_will.texts`
Main text storage with full metadata:
- **id:** Unique text identifier
- **kg_work_id:** Link to Knowledge Graph work ID
- **category:** Text category (new_testament, apologists_2nd_century, origen_works, etc.)
- **title, author:** Text metadata
- **raw_text, normalized_text:** Full text content
- **tei_xml:** Structured markup
- **lemmas, pos_tags, named_entities:** Linguistic analysis (JSONB)
- **embedding:** Gemini vector embeddings (BYTEA)
- **embedding_model, embedding_dimensions:** Embedding metadata
- **language:** Text language (grc, lat)
- **metadata:** Additional metadata (JSONB)

#### `free_will.text_divisions`
Structural divisions (books, chapters, sections):
- **id, text_id, parent_id:** Hierarchical structure
- **type, subtype:** Division types (book, chapter, section)
- **n, full_reference:** Canonical references
- **heading:** Division titles
- **char_position, char_length:** Text positioning

#### `free_will.text_sections`
Text sections (paragraphs, lines, verses):
- **id, text_id, division_id:** Relationships
- **type, subtype:** Section types (paragraph, line, verse)
- **content:** Actual text content
- **char_position:** Text positioning

### **Search Functions**

#### `free_will.search_greek_texts(query, limit)`
Full-text search with relevance ranking:
- Returns: id, title, author, category, language, rank, snippet
- Supports Greek and Latin queries
- Uses PostgreSQL's `ts_rank` for relevance scoring

#### `free_will.search_by_lemmas(query, limit)`
Lemma-based search:
- Returns: id, title, author, language, lemmas
- Searches through linguistic analysis data

#### `free_will.search_by_author(query, limit)`
Author-based search:
- Returns: id, title, author, language, text_length
- Ordered by text length (longest first)

#### `free_will.search_new_testament(query, limit)`
New Testament specific search:
- Returns: id, title, author, language, rank, snippet
- Limited to New Testament texts only

#### `free_will.search_by_category(category, limit)`
Category-based search:
- Returns: id, title, author, category, language, text_length
- Categories: new_testament, apologists_2nd_century, origen_works, clement_works, tertullian_works, irenaeus_works, original_works

## 🔧 Setup and Usage

### **Connection Details**
- **Host:** localhost
- **Port:** 5433
- **Database:** ancient_free_will_db
- **User:** free_will_user
- **Password:** free_will_password

### **Quick Start**
```bash
# Start PostgreSQL with Docker
docker-compose up -d

# Run expanded setup
python3 setup_expanded_postgresql.py

# Test search capabilities
python3 search_demo.py
```

### **Python Usage Example**
```python
import asyncio
import asyncpg

async def search_example():
    conn = await asyncpg.connect(
        host='localhost',
        port=5433,
        database='ancient_free_will_db',
        user='free_will_user',
        password='free_will_password'
    )
    
    # Full-text search
    results = await conn.fetch("""
        SELECT title, author, rank, snippet
        FROM free_will.search_greek_texts('ἐφ ἡμῖν', 5)
    """)
    
    for result in results:
        print(f"{result['title']} by {result['author']}")
        print(f"Relevance: {result['rank']:.3f}")
        print(f"Context: {result['snippet'][:200]}...")
        print()
    
    await conn.close()

asyncio.run(search_example())
```

## 🎯 Key Search Terms

### **Greek Philosophical Concepts**
- **ἐφ ἡμῖν** (eph' hêmin) - "in our power"
- **εἱμαρμένη** (heimarmenê) - "fate"
- **αὐτεξούσιον** (autexousion) - "self-determining power"
- **προαίρεσις** (prohairesis) - "choice"
- **βούλευσις** (bouleusis) - "deliberation"
- **ἑκούσιον** (hekousion) - "voluntary"
- **ἀκούσιον** (akousion) - "involuntary"
- **ἀρετή** (aretê) - "virtue"
- **κακία** (kakia) - "vice"
- **ἀνάγκη** (anankê) - "necessity"

### **Latin Philosophical Concepts**
- **libero arbitrio** - "free will"
- **fatum** - "fate"
- **necessitas** - "necessity"
- **voluntas** - "will"
- **virtus** - "virtue"
- **vitium** - "vice"
- **providentia** - "providence"
- **peccatum** - "sin"
- **gratia** - "grace"

## 📈 Performance Features

- **GIN Indexes:** Full-text search indexes for Greek and Latin
- **JSONB Indexes:** GIN indexes for lemmas, POS tags, named entities
- **Vector Indexes:** For semantic similarity search
- **Category Indexes:** For efficient category-based queries
- **Connection Pooling:** AsyncPG connection pool for high performance

## 🔗 Integration with Knowledge Graph

Each text includes a `kg_work_id` field linking to the Ancient Free Will Database Knowledge Graph, enabling seamless integration between:
- **Structured knowledge** (Knowledge Graph)
- **Full-text content** (PostgreSQL database)
- **Linguistic analysis** (lemmas, POS tags)
- **Semantic search** (Gemini embeddings)

This creates a comprehensive research platform combining graph-based relationships with powerful text search capabilities.

## 📝 Citation and Attribution

All texts maintain proper attribution and source information, with links to:
- Original manuscripts and editions
- Modern scholarly references
- Linguistic analysis sources
- Embedding generation metadata

---

*This database represents the most comprehensive digital collection of ancient free will debates, spanning from Aristotle (4th c. BCE) through Augustine (5th c. CE), with full-text search capabilities across Greek and Latin philosophical and theological literature.*
