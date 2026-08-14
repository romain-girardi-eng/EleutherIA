#!/usr/bin/env python3
"""
Basic example of using EleutherIA packages.

Prerequisites:
    pip install eleutheria-database eleutheria-kg eleutheria-graphrag[llm]

    Set environment variables:
    - POSTGRES_HOST, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
    - CODEX_PROXY_API_KEY, CLAUDE_PROXY_API_KEY or GEMINI_API_KEY
"""

import asyncio
import os


async def main() -> None:
    # Set up environment for local development
    os.environ.setdefault("POSTGRES_HOST", "localhost")
    os.environ.setdefault("POSTGRES_USER", "eleutheria")
    os.environ.setdefault("POSTGRES_PASSWORD", "eleutheria")
    os.environ.setdefault("POSTGRES_DB", "eleutheria")

    from eleutheria_database import DatabaseService

    # Connect to database
    db = DatabaseService()
    await db.connect()
    print("Connected to PostgreSQL")

    # Example 1: Query ancient works
    print("\n=== Ancient Works ===")
    works = await db.fetch("""
        SELECT title, author, language, period
        FROM free_will.ancient_works
        WHERE school = 'Stoic'
        LIMIT 5
    """)
    for work in works:
        print(f"  - {work['title']} by {work['author']} ({work['period']})")

    # Example 2: Search passages
    print("\n=== Search: 'fate' ===")
    passages = await db.fetch("""
        SELECT
            p.text_content,
            w.title,
            w.author,
            ts_rank(to_tsvector('simple', p.text_content),
                    plainto_tsquery('simple', 'fate')) as rank
        FROM free_will.passages p
        JOIN free_will.ancient_works w ON p.work_id = w.work_id
        WHERE to_tsvector('simple', p.text_content) @@ plainto_tsquery('simple', 'fate')
        ORDER BY rank DESC
        LIMIT 3
    """)
    for p in passages:
        print(f"  - {p['author']}, {p['title']}")
        print(f"    {p['text_content'][:100]}...")

    # Example 3: KG statistics
    print("\n=== Knowledge Graph ===")
    stats = await db.fetchrow("""
        SELECT
            (SELECT COUNT(*) FROM free_will.kg_nodes) as nodes,
            (SELECT COUNT(*) FROM free_will.kg_edges) as edges
    """)
    if stats:
        print(f"  Nodes: {stats['nodes']}")
        print(f"  Edges: {stats['edges']}")

    # Clean up
    await db.close()
    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
