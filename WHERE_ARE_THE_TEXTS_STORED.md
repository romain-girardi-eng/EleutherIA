# 📚 WHERE ARE THE TEXTS STORED? - Complete Multi-Modal Guide

## 🎯 **The Ancient Free Will Database is a TRIPLE-THREAT System:**

### 🧠 **Knowledge Graph (GraphRAG)** - `ancient_free_will_database.json`
- **465 nodes** (persons, works, concepts, arguments)
- **745 edges** (relationships, influences, citations)
- **GraphRAG capabilities** for complex philosophical relationship queries
- **13MB JSON file** with comprehensive metadata

### 🗄️ **PostgreSQL Database** - `ancient_free_will_db` (localhost:5433)
- **289 texts** with full content and metadata
- **35+ million characters** of ancient Greek and Latin
- **Full-text search** with linguistic analysis
- **Structured storage** with divisions and sections

### 🔍 **Vector Database** - Integrated with PostgreSQL
- **285 texts** with Gemini embeddings
- **Semantic search** capabilities
- **Cross-lingual similarity** matching
- **Concept clustering** and analysis

### **Database Location:**
- **Host:** localhost
- **Port:** 5433  
- **Database:** ancient_free_will_db
- **Schema:** free_will
- **User:** free_will_user
- **Password:** free_will_password

### **Storage Statistics:**
- **Database size:** 296 MB
- **Total texts:** 289 works
- **Total characters:** 35,214,668 characters
- **Average text length:** 121,850 characters
- **Longest text:** 1,608,474 characters (Origen's Commentary on John)
- **Shortest text:** 870 characters

## 📊 **Table Structure:**

### **Main Tables:**
1. **`free_will.texts`** (183 MB) - Main text storage
2. **`free_will.text_sections`** (93 MB) - Text sections/paragraphs  
3. **`free_will.text_divisions`** (12 MB) - Structural divisions (books, chapters)
4. **`free_will.text_milestones`** (24 KB) - Page breaks, milestones
5. **`free_will.text_page_breaks`** (24 KB) - Stephanus, Bekker numbers
6. **`free_will.text_citation_systems`** (16 KB) - Citation systems
7. **`free_will.text_apparatus`** (16 KB) - Critical apparatus
8. **`free_will.text_notes`** (16 KB) - Notes and commentary

## 🔍 **How to Access the Texts:**

### **1. Direct Database Query:**
```sql
-- Get a specific text
SELECT title, author, raw_text 
FROM free_will.texts 
WHERE title ILIKE '%Republic%' 
LIMIT 1;

-- Search texts by content
SELECT title, author, 
       ts_headline('greek', raw_text, plainto_tsquery('greek', 'ἐφ ἡμῖν')) as context
FROM free_will.texts 
WHERE to_tsvector('greek', raw_text) @@ plainto_tsquery('greek', 'ἐφ ἡμῖν')
LIMIT 5;
```

### **2. Python Script Access:**
```python
import asyncio
import asyncpg

async def get_text():
    conn = await asyncpg.connect(
        host='localhost', port=5433,
        database='ancient_free_will_db',
        user='free_will_user', 
        password='free_will_password'
    )
    
    # Get text content
    text = await conn.fetchrow("""
        SELECT title, author, raw_text, LENGTH(raw_text) as text_length
        FROM free_will.texts 
        WHERE title ILIKE '%Republic%'
        LIMIT 1
    """)
    
    print(f"Title: {text['title']}")
    print(f"Author: {text['author']}")
    print(f"Length: {text['text_length']:,} characters")
    print(f"Content: {text['raw_text'][:500]}...")
    
    await conn.close()

asyncio.run(get_text())
```

### **3. Export Text to File:**
```python
# Export a text to a file
text = await conn.fetchrow("SELECT title, author, raw_text FROM free_will.texts WHERE title = 'Republic'")

with open("Republic_by_Plato.txt", "w", encoding="utf-8") as f:
    f.write(f"Title: {text['title']}\n")
    f.write(f"Author: {text['author']}\n")
    f.write("=" * 80 + "\n\n")
    f.write(text['raw_text'])
```

## 📖 **Sample Texts Available:**

### **Top 10 Longest Texts:**
1. **Commentarii In Evangelium Joannis** by Origenes (1,608,474 chars)
2. **Contra Celsum** by Origenes (1,044,592 chars)  
3. **Pseudo-Augustini Quaestiones** by Ambrosiaster (915,631 chars)
4. **Epistulae, Ad Lucilium** by Seneca (866,013 chars)
5. **Confessiones** by Augustine (831,042 chars)
6. **Commentarium In Evangelium Matthaei** by Origenes (782,135 chars)
7. **Adversus Marcionem** by Tertullian (773,665 chars)
8. **Laws** by Plato (771,537 chars)
9. **Commentariorum Series In Evangelium Matthaei** by Origenes (699,057 chars)
10. **Selecta in Psalmos** by Origenes (660,661 chars)

### **Categories Available:**
- **New Testament (57 works)** - Complete canonical texts
- **2nd Century Apologists (13 works)** - Justin Martyr, Tatian, Athenagoras, Theophilus
- **Origen (48 works)** - Systematic theology and biblical commentary
- **Clement of Alexandria (9 works)** - Alexandrian theological synthesis
- **Tertullian (99 works)** - Latin theological treatises
- **Irenaeus (2 works)** - Anti-Gnostic theology
- **Original Philosophical Works (61 works)** - Aristotle, Plato, Lucretius, Cicero, Augustine, Seneca

## 🛠️ **Available Scripts:**

### **1. Text Access Demo:**
```bash
python3 text_access_demo.py
```
- Lists all texts
- Searches by title/author
- Shows text content
- Exports texts to files

### **2. Comprehensive Search Demo:**
```bash
python3 comprehensive_search_demo.py
```
- Full-text search in Greek and Latin
- Category-based search
- Author-specific queries
- Lemma-based search
- Semantic search with embeddings

### **3. Database Connection Test:**
```bash
python3 test_enhanced_postgresql.py
```
- Tests database connection
- Shows database statistics
- Verifies data integrity

## 🔧 **Database Management:**

### **Start/Stop Database:**
```bash
# Start PostgreSQL with Docker
docker-compose up -d

# Stop PostgreSQL
docker-compose down

# Check status
docker-compose ps
```

### **Access PgAdmin Web Interface:**
- **URL:** http://localhost:8080
- **Email:** admin@ancientfreewill.org
- **Password:** admin123

### **Direct Database Access:**
```bash
# Connect with psql
psql -h localhost -p 5433 -U free_will_user -d ancient_free_will_db

# Or with Docker
docker exec -it ancient_free_will_postgres psql -U free_will_user -d ancient_free_will_db
```

## 📁 **File System vs Database:**

### **❌ NOT stored as files:**
- The texts are NOT individual text files
- They are NOT in a folder structure
- They are NOT accessible via file system

### **✅ Stored in database:**
- All texts are in PostgreSQL tables
- Access via SQL queries or Python scripts
- Full-text search capabilities
- Structured metadata and annotations
- Vector embeddings for semantic search

## 🎯 **Key Points:**

### 🧠 **Knowledge Graph Access:**
1. **465 nodes** with philosophical concepts and relationships
2. **GraphRAG queries** for complex relationship traversal
3. **JSON format** with comprehensive metadata and citations
4. **13MB file** containing the complete knowledge structure

### 🗄️ **PostgreSQL Access:**
1. **289 texts** stored in database tables with full content
2. **SQL queries** for full-text search in Greek and Latin
3. **Structured metadata**: lemmas, POS tags, embeddings, TEI XML
4. **Database size**: 296 MB with 35+ million characters

### 🔍 **Vector Database Access:**
1. **285 texts** with Gemini embeddings for semantic search
2. **Cross-lingual similarity** matching across Greek and Latin
3. **Concept clustering** and philosophical analysis
4. **Integrated storage** within PostgreSQL BYTEA columns

### 🔄 **Multi-Modal Integration:**
- **`kg_work_id`** fields link all three systems
- **Bidirectional queries** across Knowledge Graph and PostgreSQL
- **Semantic enrichment** of graph nodes with text embeddings
- **Unified research workflow** combining all three modalities

**EleutherIA** - The Ancient Free Will Database: Where Knowledge Graphs meet Full-Text Search meets Semantic AI! 🚀
