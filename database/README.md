# eleutheria-database

Ancient Greek/Latin texts corpus for the EleutherIA knowledge graph.

## Installation

```bash
pip install eleutheria-database
```

For development:
```bash
pip install eleutheria-database[dev]
```

For FastAPI integration:
```bash
pip install eleutheria-database[api]
```

## Quick Start

```python
from eleutheria_database import DatabaseService

# Connect to database
db = DatabaseService()
await db.connect()

# Fetch ancient works
works = await db.fetch("""
    SELECT work_id, title, author, language
    FROM free_will.ancient_works
    WHERE language = 'grc'
    LIMIT 10
""")

# Fetch passages with CTS URN
passages = await db.fetch("""
    SELECT p.passage_id, p.text_content, p.cts_urn, w.title
    FROM free_will.passages p
    JOIN free_will.ancient_works w ON p.work_id = w.work_id
    WHERE w.author = 'Chrysippus'
""")

# Clean up
await db.close()
```

## Features

- **487 ancient works** with CTS URN support
- **69,277 passages** with hierarchical structure (book/chapter/section)
- **Full-text search** via PostgreSQL GIN indexes
- **Lemmatization data** for Greek and Latin texts
- **Passage citations** linking to knowledge graph nodes

## Database Schema

Core tables:
- `ancient_works` - Canonical works with metadata
- `passages` - Hierarchical text units
- `passage_citations` - Links to KG nodes
- `passage_relationships` - Inter-passage references

See [schema/](schema/) for the full PostgreSQL schema.

## Supabase Rebuild From KG Snapshot

If the managed Supabase project has to be recreated, use the bootstrap script
from the repository root:

```bash
export SUPABASE_DATABASE_URL='postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT_REF.supabase.co:5432/postgres?sslmode=require'

uv run --with asyncpg \
  python database/scripts/bootstrap_supabase.py \
  --replace-data
```

The script applies the canonical schema, public RPC wrappers, REST compatibility
columns for Cloudflare, and imports `data/kg/nodes.jsonl` + `data/kg/edges.jsonl`
into `kg_nodes`, `kg_edges`, derived `ancient_works`, `passages`, and
`passage_citations`.

Use `--dry-run` first to inspect the recovered row counts without connecting to
PostgreSQL.

Security constraints:

- keep `SUPABASE_DATABASE_URL` local or in CI secrets only;
- prefer a direct/session-pooler DSN for bootstrap, not the transaction pooler;
- never use a Supabase service-role API key for this script;
- runtime services should use their own `DATABASE_URL` and Cloudflare should use
  the anon API key unless a server-only admin route explicitly needs RLS bypass.

## API Routes (Optional)

If installed with `[api]`:

```python
from fastapi import FastAPI
from eleutheria_database.api import router as database_router

app = FastAPI()
app.include_router(database_router, prefix="/api/database")
```

Endpoints:
- `GET /works` - List ancient works
- `GET /works/{work_id}` - Get work details
- `GET /works/{work_id}/passages` - Get passages for a work
- `GET /passages/{passage_id}` - Get passage details
- `GET /search` - Full-text search

## Configuration

Environment variables:
```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=eleutheria
POSTGRES_USER=postgres
POSTGRES_PASSWORD=secret
DB_POOL_MIN_SIZE=5
DB_POOL_MAX_SIZE=15
```

## License

CC BY 4.0
