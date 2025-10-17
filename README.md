# Ancient Free Will Database - Comprehensive Multi-Modal System

A revolutionary **triple-threat** digital humanities platform combining:

1. **🧠 Knowledge Graph (KG)** with GraphRAG capabilities - 465 nodes, 745 edges
2. **🗄️ PostgreSQL Database** with full-text search and linguistic analysis - 289 texts, 35M+ characters  
3. **🔍 Vector Database** for semantic search with Gemini embeddings - 285 texts with embeddings

This comprehensive system enables unprecedented research across ancient philosophical and theological works relevant to free will debates, spanning from Aristotle (4th c. BCE) through Augustine (5th c. CE).

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

## 📊 System Overview

### 🧠 Knowledge Graph (GraphRAG)
- **Nodes:** 465 (persons, works, concepts, arguments)
- **Edges:** 745 (relationships, citations, influences)
- **Coverage:** 8 historical phases from Aristotle to Boethius
- **GraphRAG:** Advanced retrieval-augmented generation capabilities
- **Format:** JSON with comprehensive metadata and citations

### 🗄️ PostgreSQL Database
- **Total Works:** 289 texts
- **Total Characters:** 35+ million characters
- **Languages:** Greek (225 texts), Latin (64 texts)
- **Categories:** New Testament, Apologists, Origen, Clement, Tertullian, Irenaeus, Original Works
- **Metadata:** 285 texts with embeddings, 109 with lemmas, 289 with TEI XML

### 🔍 Vector Database (Semantic Search)
- **Embeddings:** 285 texts with Gemini embeddings
- **Dimensions:** 768-3072 depending on model
- **Search Types:** Semantic similarity, concept clustering, cross-lingual search
- **Integration:** Seamless with PostgreSQL and Knowledge Graph

## 🔍 Multi-Modal Search Capabilities

### 🧠 Knowledge Graph Search (GraphRAG)
```python
# GraphRAG queries for complex relationships
# Find all works that discuss "eph' hêmin" concept
kg_query = {
    "concept": "eph' hêmin",
    "relationships": ["discusses", "influences", "critiques"],
    "time_period": "4th_c_BCE_to_6th_c_CE"
}

# Semantic traversal of philosophical influences
traversal_path = "Aristotle -> Nicomachean Ethics -> Stoic compatibilism -> Christian libertarianism"
```

### 🗄️ PostgreSQL Full-Text Search
```sql
-- Greek philosophical concepts
SELECT title, author, rank, snippet
FROM free_will.search_greek_texts('ἐφ ἡμῖν', 10);

-- Latin concepts  
SELECT title, author, rank, snippet
FROM free_will.search_greek_texts('libero arbitrio', 10);

-- Category-based search
SELECT title, author, text_length
FROM free_will.search_by_category('new_testament', 10);

-- Author-specific search
SELECT title, author, category, text_length
FROM free_will.search_by_author('Aristotle', 10);
```

### 🔍 Vector Database Semantic Search
```python
# Semantic similarity search
similar_texts = vector_search(
    query_text="voluntary action and moral responsibility",
    similarity_threshold=0.8,
    max_results=10
)

# Cross-lingual semantic search
cross_lingual_results = semantic_search(
    greek_query="ἐφ ἡμῖν",
    latin_query="in nostra potestate",
    embedding_model="gemini-embedding-001"
)

# Concept clustering
concept_clusters = cluster_embeddings(
    texts_with_embeddings=285,
    clustering_algorithm="hierarchical",
    n_clusters=20
)
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

## 🔗 Multi-Modal Integration

The system provides seamless integration across all three components:

### 🧠 Knowledge Graph ↔ PostgreSQL
- **`kg_work_id`** fields link PostgreSQL texts to Knowledge Graph works
- **Bidirectional queries** enable graph traversal from text content
- **Citation mapping** connects ancient sources to full-text passages

### 🗄️ PostgreSQL ↔ Vector Database  
- **Embedding storage** in PostgreSQL BYTEA columns
- **Hybrid search** combining full-text and semantic similarity
- **Metadata enrichment** with linguistic analysis (lemmas, POS tags)

### 🧠 Knowledge Graph ↔ Vector Database
- **Concept embeddings** for graph node similarity
- **Semantic clustering** of philosophical concepts
- **Cross-modal retrieval** from graph structure to semantic content

### 🔄 Unified Research Workflow
```python
# Example: Multi-modal research query
def comprehensive_research(query):
    # 1. GraphRAG: Find related concepts and influences
    kg_results = graphrag_search(query)
    
    # 2. PostgreSQL: Full-text search in related works
    text_results = fulltext_search(kg_results.work_ids)
    
    # 3. Vector DB: Semantic similarity in found texts
    semantic_results = vector_search(text_results.content)
    
    # 4. Integration: Combine insights across all modalities
    return integrated_results(kg_results, text_results, semantic_results)
```

## 📈 Performance Features

### 🧠 Knowledge Graph Performance
- **Graph traversal optimization** for complex relationship queries
- **GraphRAG caching** for frequently accessed concept paths
- **Node indexing** for fast concept and person lookups
- **Edge weighting** for influence strength calculations

### 🗄️ PostgreSQL Performance  
- **GIN Indexes** for full-text search in Greek and Latin
- **JSONB Indexes** for metadata queries
- **B-tree Indexes** for categorical and temporal queries
- **Connection Pooling** for high performance
- **Async Operations** for scalability

### 🔍 Vector Database Performance
- **Vector Indexes** for semantic similarity search
- **Embedding compression** for storage optimization
- **Batch processing** for large-scale similarity calculations
- **GPU acceleration** for embedding generation

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

## 🏆 Revolutionary Achievement

This **triple-threat system** represents the most comprehensive digital collection of ancient free will debates, combining:

- **🧠 Knowledge Graph (GraphRAG)**: 465 nodes, 745 edges mapping philosophical relationships
- **🗄️ PostgreSQL Database**: 289 texts, 35M+ characters with full-text search  
- **🔍 Vector Database**: 285 texts with Gemini embeddings for semantic search

Spanning from Aristotle (4th c. BCE) through Augustine (5th c. CE), this multi-modal platform enables unprecedented research across Greek and Latin philosophical and theological literature with advanced AI-powered capabilities.

**EleutherIA** - The Ancient Free Will Database: Where Knowledge Graphs meet Full-Text Search meets Semantic AI! 🚀