#!/usr/bin/env python3
"""
Re-embed KG nodes into Qdrant vector database.

Finds KG nodes that are not yet in Qdrant and embeds them using Gemini,
then upserts into the kg_nodes_gemini collection.

Usage:
    set -a; source .env; set +a

    # Check status (how many nodes are missing from Qdrant)
    python scripts/reembed_kg_nodes.py --status

    # Embed all missing KG nodes (dry run)
    python scripts/reembed_kg_nodes.py --dry-run

    # Embed all missing KG nodes
    python scripts/reembed_kg_nodes.py --confirm

    # Embed only specific types
    python scripts/reembed_kg_nodes.py --types passage,person,work --confirm
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import time

import psycopg2

SCHEMA = "free_will"
COLLECTION_KG = "kg_nodes_gemini"
EMBEDDING_DIM = 3072
BATCH_SIZE = 50  # Gemini can batch embed
RATE_LIMIT_DELAY = 0.3  # seconds between batches


def get_db_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        print("ERROR: DATABASE_URL not set.")
        sys.exit(1)
    return url


def get_qdrant_client():
    from qdrant_client import QdrantClient

    host = os.environ.get("QDRANT_HOST", "localhost")
    port = int(os.environ.get("QDRANT_HTTP_PORT", "6333"))
    api_key = os.environ.get("QDRANT_API_KEY")

    if api_key:
        return QdrantClient(url=f"https://{host}", api_key=api_key, check_compatibility=False)
    else:
        return QdrantClient(host=host, port=port, check_compatibility=False)


def embed_texts(texts: list[str], api_key: str) -> list[list[float]]:
    """Embed texts using Gemini embedding API."""
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    result = genai.embed_content(
        model="models/gemini-embedding-001",
        content=texts,
    )
    return result["embedding"]


def build_embed_text(node: dict) -> str:
    """Build the text to embed for a KG node."""
    parts = []
    if node.get("label"):
        parts.append(node["label"])
    if node.get("type"):
        parts.append(f"[{node['type']}]")
    if node.get("description"):
        # Truncate very long descriptions
        desc = node["description"]
        if len(desc) > 8000:
            desc = desc[:8000] + "..."
        parts.append(desc)
    return " ".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(description="Re-embed KG nodes into Qdrant")
    parser.add_argument("--status", action="store_true", help="Show embedding status")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be embedded")
    parser.add_argument("--confirm", action="store_true", help="Actually embed and upsert")
    parser.add_argument("--types", help="Comma-separated node types to embed (default: all)")
    parser.add_argument("--db-url", help="Database URL")
    args = parser.parse_args()

    db_url = args.db_url or get_db_url()
    gemini_key = os.environ.get("GEMINI_API_KEY", "")

    # Connect to DB
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute(f"SET search_path TO {SCHEMA}")

    # Connect to Qdrant
    qdrant = get_qdrant_client()

    # Check collection exists
    try:
        info = qdrant.get_collection(COLLECTION_KG)
        qdrant_count = info.points_count
        print(f"Qdrant collection '{COLLECTION_KG}': {qdrant_count:,} points")
    except Exception as e:
        print(f"Collection '{COLLECTION_KG}' not found: {e}")
        if args.confirm:
            from qdrant_client.http.models import Distance, VectorParams
            qdrant.create_collection(
                collection_name=COLLECTION_KG,
                vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
            )
            print(f"Created collection '{COLLECTION_KG}'")
            qdrant_count = 0
        else:
            print("Use --confirm to create it.")
            return

    # Get existing point IDs from Qdrant
    # We use a deterministic ID based on node_id hash
    # First, get all node_ids from DB
    type_filter = ""
    params: list = []
    if args.types:
        types = args.types.split(",")
        placeholders = ",".join(["%s"] * len(types))
        type_filter = f"AND type IN ({placeholders})"
        params = types

    cur.execute(f"""
        SELECT node_id, label, type, description, period,
               metadata->>'language' as lang,
               metadata->>'author' as author
        FROM kg_nodes
        WHERE description IS NOT NULL AND description != ''
        {type_filter}
        ORDER BY node_id
    """, params)
    all_nodes = cur.fetchall()
    print(f"DB nodes with descriptions: {len(all_nodes):,}")

    # Check which are already in Qdrant by scrolling through existing points
    existing_node_ids: set[str] = set()
    offset = None
    while True:
        points, next_offset = qdrant.scroll(
            collection_name=COLLECTION_KG,
            limit=1000,
            offset=offset,
            with_payload=["id"],
        )
        for p in points:
            if p.payload and "id" in p.payload:
                existing_node_ids.add(p.payload["id"])
        if next_offset is None:
            break
        offset = next_offset

    print(f"Already in Qdrant: {len(existing_node_ids):,}")

    # Find missing nodes
    missing = []
    for row in all_nodes:
        node_id = row[0]
        if node_id not in existing_node_ids:
            missing.append({
                "node_id": node_id,
                "label": row[1],
                "type": row[2],
                "description": row[3],
                "period": row[4],
                "language": row[5],
                "author": row[6],
            })

    print(f"Missing from Qdrant: {len(missing):,}")

    if args.status:
        # Show breakdown by type
        from collections import Counter
        type_counts = Counter(n["type"] for n in missing)
        print("\nMissing by type:")
        for t, c in type_counts.most_common():
            print(f"  {t:25s} {c:>6,}")
        return

    if not missing:
        print("All nodes are already embedded!")
        return

    if args.dry_run:
        print(f"\nDRY RUN: Would embed {len(missing):,} nodes in {len(missing)//BATCH_SIZE + 1} batches")
        for n in missing[:5]:
            text = build_embed_text(n)
            print(f"  {n['node_id']:55s} [{n['type']:10s}] {len(text):>5} chars")
        return

    if not args.confirm:
        print("Use --confirm to embed, --dry-run to preview, or --status for breakdown.")
        return

    if not gemini_key:
        print("ERROR: GEMINI_API_KEY not set.")
        sys.exit(1)

    # Embed in batches
    import google.generativeai as genai
    from qdrant_client.http.models import PointStruct

    genai.configure(api_key=gemini_key)

    total_embedded = 0
    for i in range(0, len(missing), BATCH_SIZE):
        batch = missing[i:i + BATCH_SIZE]
        texts = [build_embed_text(n) for n in batch]

        try:
            result = genai.embed_content(
                model="models/gemini-embedding-001",
                content=texts,
            )
            embeddings = result["embedding"]
        except Exception as e:
            print(f"  ERROR embedding batch {i//BATCH_SIZE + 1}: {e}")
            if "429" in str(e):
                print("  Rate limited. Waiting 60s...")
                time.sleep(60)
                continue
            raise

        # Build Qdrant points
        points = []
        for _j, (node, embedding) in enumerate(zip(batch, embeddings, strict=False)):
            # Use deterministic numeric ID from node_id hash
            point_id = int(hashlib.md5(node["node_id"].encode()).hexdigest()[:16], 16)
            points.append(PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "id": node["node_id"],
                    "label": node["label"],
                    "type": node["type"],
                    "description": (node["description"] or "")[:2000],
                    "period": node["period"],
                    "language": node.get("language"),
                    "author": node.get("author"),
                },
            ))

        qdrant.upsert(collection_name=COLLECTION_KG, points=points)
        total_embedded += len(points)
        print(f"  Batch {i//BATCH_SIZE + 1}/{len(missing)//BATCH_SIZE + 1}: "
              f"embedded {len(points)} nodes (total: {total_embedded:,})")

        if i + BATCH_SIZE < len(missing):
            time.sleep(RATE_LIMIT_DELAY)

    print(f"\nDone! Embedded {total_embedded:,} nodes into {COLLECTION_KG}")
    conn.close()


if __name__ == "__main__":
    main()
