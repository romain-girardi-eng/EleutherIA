#!/usr/bin/env python3
"""
GraphRAG query example.

Prerequisites:
    pip install eleutheria-graphrag[llm]

    Set environment variables:
    - Database and Qdrant connection vars
    - MOONSHOT_API_KEY or GEMINI_API_KEY
"""

import asyncio
import os


async def main() -> None:
    # Environment setup
    os.environ.setdefault("POSTGRES_HOST", "localhost")
    os.environ.setdefault("POSTGRES_USER", "eleutheria")
    os.environ.setdefault("POSTGRES_PASSWORD", "eleutheria")
    os.environ.setdefault("POSTGRES_DB", "eleutheria")
    os.environ.setdefault("QDRANT_HOST", "localhost")

    from eleutheria_database import DatabaseService
    from eleutheria_graphrag import GraphRAGService
    from eleutheria_kg import QdrantService

    # Connect services
    db = DatabaseService()
    qdrant = QdrantService()
    await db.connect()
    await qdrant.connect()

    # Initialize GraphRAG
    graphrag = GraphRAGService(db, qdrant)
    await graphrag.load_kg()

    print("GraphRAG initialized")
    print(f"  KG nodes: {len(graphrag.node_lookup)}")

    # Ask a question
    question = "What did Chrysippus believe about fate and human responsibility?"
    print(f"\nQuestion: {question}\n")

    result = await graphrag.query(
        question=question,
        semantic_k=10,
        graph_depth=2,
        include_passages=True,
    )

    print("Answer:")
    print(result["answer"])

    print("\nCitations:")
    for citation in result["citations"]:
        print(f"  [{citation['ref']}] {citation['label']}")

    print("\nMetadata:")
    print(f"  Seed nodes: {len(result['seed_nodes'])}")
    print(f"  Context nodes: {len(result['context_nodes'])}")
    print(f"  Passages used: {result['passages_used']}")

    # Clean up
    await graphrag.close()
    await db.close()
    await qdrant.close()


if __name__ == "__main__":
    asyncio.run(main())
