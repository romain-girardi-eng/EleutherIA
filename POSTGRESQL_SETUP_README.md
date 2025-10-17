# Ancient Free Will Database - PostgreSQL Setup

This directory contains the PostgreSQL setup for the Ancient Free Will Database project, which extracts only the free-will related texts from the Sematika MVP database.

## Overview

The Ancient Free Will Database contains 48 works related to ancient debates on free will, fate, and moral responsibility. This PostgreSQL setup identifies and imports only the texts that are available in both the Knowledge Graph and the Sematika MVP database.

## Identified Overlaps

From the comparison between the Ancient Free Will Database and Sematika MVP database, we found **68 potential matches** across **48 works** in the KG and **4,420 works** in Sematika MVP.

### Key Free-Will Related Works Available:

#### Ancient Philosophical Works
- **De Fato (On Fate)** - Cicero, Pseudo-Plutarch, Alexander of Aphrodisias
- **Nicomachean Ethics** - Aristotle
- **De Interpretatione** - Aristotle  
- **Metaphysics Book Theta** - Aristotle
- **De Rerum Natura** - Lucretius
- **Republic** - Plato
- **Laws** - Plato

#### Patristic Works
- **De Libero Arbitrio** - Augustine
- **Confessiones** - Augustine
- **Consolation of Philosophy Book V** - Boethius

#### Biblical Texts (Relevant to Free Will Discussions)
- Genesis, Deuteronomy, Exodus
- Job, Proverbs, Ecclesiastes
- Wisdom of Sirach (Ecclesiasticus)

## Setup Instructions

### Prerequisites

1. **Docker and Docker Compose** installed
2. **Python 3.8+** with pip
3. **Sematika MVP database** accessible at `/Users/romaingirardi/SematikaData/library.db`

### Quick Start

1. **Start PostgreSQL with Docker Compose:**
   ```bash
   docker-compose up -d
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the setup script:**
   ```bash
   python setup_postgresql.py
   ```

### Manual Setup (Alternative)

If you prefer to set up PostgreSQL manually:

1. **Install PostgreSQL 15+**
2. **Create database and user:**
   ```sql
   CREATE DATABASE ancient_free_will_db;
   CREATE USER free_will_user WITH PASSWORD 'free_will_password';
   GRANT ALL PRIVILEGES ON DATABASE ancient_free_will_db TO free_will_user;
   ```

3. **Run the setup script with custom connection parameters:**
   ```python
   setup = FreeWillPostgresSetup(
       host="localhost",
       port=5432,
       database="ancient_free_will_db",
       user="free_will_user",
       password="free_will_password"
   )
   ```

## Database Schema

The PostgreSQL database uses the following structure:

### Tables

- **`free_will.texts`** - Main texts table with metadata and embeddings
- **`free_will.text_divisions`** - Hierarchical text structure (books, chapters, sections)
- **`free_will.text_sections`** - Individual text segments (paragraphs, lines, verses)

### Key Features

- **KG Integration**: Links to Ancient Free Will Database work IDs
- **Embeddings Support**: Stores vector embeddings for semantic search
- **Hierarchical Structure**: Supports complex text organization
- **Metadata Preservation**: Maintains all original Sematika MVP metadata
- **Performance Optimized**: Includes indexes for fast queries

## Accessing the Database

### Connection Details

- **Host**: localhost
- **Port**: 5432
- **Database**: ancient_free_will_db
- **User**: free_will_user
- **Password**: free_will_password

### PgAdmin Web Interface

Access the web interface at: http://localhost:8080

- **Email**: admin@ancientfreewill.org
- **Password**: admin123

### Python Connection Example

```python
import asyncpg

async def connect_to_db():
    conn = await asyncpg.connect(
        host="localhost",
        port=5432,
        database="ancient_free_will_db",
        user="free_will_user",
        password="free_will_password"
    )
    
    # Query example
    texts = await conn.fetch("SELECT title, author FROM free_will.texts LIMIT 10")
    for text in texts:
        print(f"{text['title']} by {text['author']}")
    
    await conn.close()
```

## Query Examples

### Basic Queries

```sql
-- Get all texts
SELECT title, author, language FROM free_will.texts ORDER BY title;

-- Get texts by author
SELECT title, date_created FROM free_will.texts WHERE author = 'Aristotle';

-- Get texts with embeddings
SELECT title, embedding_model FROM free_will.texts WHERE embedding IS NOT NULL;

-- Get summary statistics
SELECT 
    COUNT(*) as total_texts,
    COUNT(DISTINCT author) as unique_authors,
    COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) as texts_with_embeddings
FROM free_will.texts;
```

### Advanced Queries

```sql
-- Get texts by Ancient Free Will Database work ID
SELECT t.title, t.author, t.kg_work_id 
FROM free_will.texts t 
WHERE t.kg_work_id IS NOT NULL;

-- Get texts by language
SELECT language, COUNT(*) as count 
FROM free_will.texts 
GROUP BY language 
ORDER BY count DESC;

-- Get longest texts
SELECT title, author, LENGTH(raw_text) as text_length 
FROM free_will.texts 
ORDER BY text_length DESC 
LIMIT 10;
```

## Files Description

- **`compare_works.py`** - Script to compare works between KG and Sematika MVP
- **`setup_postgresql.py`** - Main setup script for PostgreSQL database
- **`docker-compose.yml`** - Docker Compose configuration for PostgreSQL and PgAdmin
- **`init.sql`** - Database initialization script
- **`requirements.txt`** - Python dependencies
- **`README.md`** - This documentation

## Troubleshooting

### Common Issues

1. **Connection refused**: Ensure PostgreSQL is running (`docker-compose ps`)
2. **Permission denied**: Check database user permissions
3. **Sematika database not found**: Verify path `/Users/romaingirardi/SematikaData/library.db`
4. **Import errors**: Check Sematika database integrity

### Logs

Check Docker logs:
```bash
docker-compose logs postgres
docker-compose logs pgadmin
```

### Reset Database

To start fresh:
```bash
docker-compose down -v
docker-compose up -d
python setup_postgresql.py
```

## Next Steps

1. **Semantic Search**: Implement vector similarity search using embeddings
2. **API Development**: Create REST API for text access
3. **Visualization**: Build web interface for exploring texts
4. **Integration**: Connect with Ancient Free Will Database visualization tools

## License

This PostgreSQL setup is part of the Ancient Free Will Database project and follows the same CC BY 4.0 license.
