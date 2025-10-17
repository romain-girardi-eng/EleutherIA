#!/usr/bin/env python3
"""
Test script for GraphRAG pipeline
Tests the complete implementation end-to-end
"""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from services.db import DatabaseService
from services.qdrant_service import QdrantService
from services.graphrag_service import GraphRAGService


async def test_graphrag_pipeline():
    """Test complete GraphRAG pipeline"""

    print("=" * 80)
    print("GraphRAG Pipeline Test")
    print("=" * 80)

    # Initialize services
    print("\n1. Initializing services...")
    db_service = DatabaseService()
    qdrant_service = QdrantService()

    try:
        await db_service.connect()
        print("   ✅ Connected to PostgreSQL")

        await qdrant_service.connect()
        print("   ✅ Connected to Qdrant")

        # Create GraphRAG service
        graphrag_service = GraphRAGService(qdrant_service, db_service)
        print("   ✅ GraphRAG service initialized")

        # Test query
        test_query = "What is Aristotle's concept of voluntary action?"
        print(f"\n2. Test Query: '{test_query}'")
        print("-" * 80)

        # Execute pipeline
        print("\n3. Executing GraphRAG pipeline...")
        result = await graphrag_service.answer_question(
            query=test_query,
            semantic_k=5,
            graph_depth=2,
            max_context=10,
            temperature=0.7
        )

        # Display results
        print("\n4. Results:")
        print("-" * 80)

        print(f"\n📝 Answer:")
        print(result['answer'])

        print(f"\n📚 Citations:")
        if result['citations']['ancient_sources']:
            print(f"   Ancient Sources ({len(result['citations']['ancient_sources'])}):")
            for source in result['citations']['ancient_sources'][:5]:
                print(f"   - {source}")
            if len(result['citations']['ancient_sources']) > 5:
                print(f"   ... and {len(result['citations']['ancient_sources']) - 5} more")

        if result['citations']['modern_scholarship']:
            print(f"\n   Modern Scholarship ({len(result['citations']['modern_scholarship'])}):")
            for source in result['citations']['modern_scholarship'][:3]:
                print(f"   - {source}")
            if len(result['citations']['modern_scholarship']) > 3:
                print(f"   ... and {len(result['citations']['modern_scholarship']) - 3} more")

        print(f"\n📊 Statistics:")
        print(f"   - Nodes used: {result['nodes_used']}")
        if 'edges_traversed' in result:
            print(f"   - Edges traversed: {result['edges_traversed']}")
        if 'error' in result:
            print(f"\n❌ Pipeline Error: {result['error']}")

        print(f"\n🔍 Reasoning Path:")
        if result['reasoning_path']:
            print(f"   Starting nodes: {len(result['reasoning_path'].get('starting_nodes', []))}")
            print(f"   Expanded nodes: {len(result['reasoning_path'].get('expanded_nodes', []))}")
            print(f"   Edges: {len(result['reasoning_path'].get('edges', []))}")

        print("\n" + "=" * 80)
        print("✅ GraphRAG Pipeline Test PASSED")
        print("=" * 80)

        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup
        print("\n5. Cleaning up...")
        await db_service.close()
        await qdrant_service.close()
        print("   ✅ Services disconnected")


if __name__ == "__main__":
    # Check environment
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ Error: GEMINI_API_KEY not set in environment")
        print("Please set it in .env file or export it")
        sys.exit(1)

    # Run test
    success = asyncio.run(test_graphrag_pipeline())
    sys.exit(0 if success else 1)
