#!/usr/bin/env python3
"""
Re-embed KG nodes into Qdrant vector database.

Finds KG nodes that are not yet in Qdrant and embeds them using Gemini,
then upserts into the configured Qdrant collection.

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

    # Rebuild the dual-vector collection used by the Cloudflare worker
    python scripts/reembed_kg_nodes.py --collection kg_nodes_dual --vector-name gemini --recreate --confirm
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import time
from types import SimpleNamespace
from urllib.parse import urlparse

import httpx
import psycopg2

SCHEMA = "free_will"
COLLECTION_KG = os.environ.get("KG_EMBED_COLLECTION", "kg_nodes_gemini")
VECTOR_NAME = os.environ.get("QDRANT_VECTOR_NAME", "").strip()
QDRANT_PROXY_URL = os.environ.get("QDRANT_PROXY_URL", "").strip().rstrip("/")
QDRANT_PROXY_KEY = os.environ.get("QDRANT_PROXY_KEY", "").strip()
EMBEDDING_MODEL = os.environ.get(
    "GEMINI_EMBEDDING_MODEL",
    "models/gemini-embedding-001",
)
EMBEDDING_DIM = int(os.environ.get("EMBEDDING_DIMENSIONS", "3072"))
BATCH_SIZE = int(os.environ.get("EMBEDDING_BATCH_SIZE", "50"))
RATE_LIMIT_DELAY = 0.3  # minimum seconds between batches
EMBEDDING_TPM_LIMIT = int(os.environ.get("GEMINI_EMBEDDING_TPM_LIMIT", "30000"))
EMBEDDING_RPM_LIMIT = int(os.environ.get("GEMINI_EMBEDDING_RPM_LIMIT", "100"))
EMBEDDING_RPD_LIMIT = int(os.environ.get("GEMINI_EMBEDDING_RPD_LIMIT", "1000"))
EMBEDDING_BATCH_TOKEN_LIMIT = int(
    os.environ.get("GEMINI_EMBEDDING_BATCH_TOKEN_LIMIT", "24000")
)


def get_db_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        print("ERROR: DATABASE_URL not set.")
        sys.exit(1)
    return url


def get_qdrant_client():
    from qdrant_client import QdrantClient

    port = int(os.environ.get("QDRANT_HTTP_PORT", "6333"))
    api_key = os.environ.get("QDRANT_API_KEY")
    qdrant_url = os.environ.get("QDRANT_URL", "").strip()
    host = os.environ.get("QDRANT_HOST", "").strip()
    localhost_url = qdrant_url.lower().startswith("http://localhost") or qdrant_url.lower().startswith(
        "http://127.0.0.1"
    )

    if localhost_url and host and host != "localhost" and api_key:
        parsed = urlparse(host if "://" in host else f"https://{host}")
        return QdrantClient(
            url=f"{parsed.scheme}://{parsed.netloc}",
            api_key=api_key,
            check_compatibility=False,
        )

    if qdrant_url:
        return QdrantClient(url=qdrant_url.rstrip("/"), api_key=api_key, check_compatibility=False)

    if host:
        parsed = urlparse(host if "://" in host else f"https://{host}")
        if parsed.scheme and parsed.netloc:
            return QdrantClient(
                url=f"{parsed.scheme}://{parsed.netloc}",
                api_key=api_key,
                check_compatibility=False,
            )

    return QdrantClient(host="localhost", port=port, api_key=api_key, check_compatibility=False)


class QdrantProxyClient:
    """Upload points to production Qdrant through the authenticated Cloudflare admin API."""

    def __init__(self, base_url: str, ingest_key: str) -> None:
        if not base_url or not ingest_key:
            raise ValueError("QDRANT_PROXY_URL and QDRANT_PROXY_KEY are required for proxy mode.")
        self.base_url = base_url
        self.ingest_key = ingest_key
        self.client = httpx.Client(timeout=120.0)

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "X-Admin-Ingest-Key": self.ingest_key,
        }

    def get_collection(self, collection_name: str):
        response = self.client.get(f"{self.base_url}/info", headers=self.headers)
        response.raise_for_status()
        data = response.json()
        for collection in data.get("collections", []):
            if collection.get("name") == collection_name:
                return SimpleNamespace(points_count=collection.get("points_count", 0))
        raise RuntimeError(f"Collection '{collection_name}' not found via proxy.")

    def recreate_collection(self, collection_name: str, embedding_dim: int, vector_name: str) -> None:
        payload: dict[str, object] = {
            "collection_name": collection_name,
            "dimensions": embedding_dim,
        }
        if vector_name:
            payload["vector_name"] = vector_name
        response = self.client.post(
            f"{self.base_url}/recreate-collection",
            json=payload,
            headers=self.headers,
        )
        response.raise_for_status()

    def upsert(self, collection_name: str, points: list[dict[str, object]]) -> None:
        response = self.client.post(
            f"{self.base_url}/upload-batch",
            json={
                "collection_name": collection_name,
                "points": points,
            },
            headers=self.headers,
        )
        response.raise_for_status()


def get_qdrant_proxy_client() -> QdrantProxyClient | None:
    if QDRANT_PROXY_URL and QDRANT_PROXY_KEY:
        return QdrantProxyClient(QDRANT_PROXY_URL, QDRANT_PROXY_KEY)
    return None


def build_vectors_config(embedding_dim: int, vector_name: str):
    from qdrant_client.http.models import Distance, VectorParams

    if vector_name:
        return {vector_name: VectorParams(size=embedding_dim, distance=Distance.COSINE)}
    return VectorParams(size=embedding_dim, distance=Distance.COSINE)


def embed_texts(texts: list[str], api_key: str) -> list[list[float]]:
    """Embed texts using Gemini embedding API."""
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    result = genai.embed_content(
        model=EMBEDDING_MODEL,
        content=texts,
        task_type="retrieval_document",
    )
    return result["embedding"]


def build_embed_text(node: dict) -> str:
    """Build the text to embed for a KG node."""
    parts = []
    if node.get("label"):
        parts.append(node["label"])
    if node.get("type"):
        parts.append(f"[{node['type']}]")
    if node.get("author"):
        parts.append(f"Author: {node['author']}")
    if node.get("period"):
        parts.append(f"Period: {node['period']}")
    if node.get("language"):
        parts.append(f"Language: {node['language']}")
    if node.get("description"):
        # Truncate very long descriptions
        desc = node["description"]
        if len(desc) > 8000:
            desc = desc[:8000] + "..."
        parts.append(desc)
    return " ".join(part.strip() for part in parts if part and part.strip())


def estimate_tokens(text: str) -> int:
    """Cheap token estimate for Gemini rate-limit pacing."""
    return max(1, len(text) // 4)


def batch_nodes(nodes: list[dict]) -> list[list[dict]]:
    """Split nodes into batches constrained by both count and token budget."""
    batches: list[list[dict]] = []
    current_batch: list[dict] = []
    current_tokens = 0

    for node in nodes:
        node_tokens = int(node["token_estimate"])
        would_exceed_count = len(current_batch) >= BATCH_SIZE
        would_exceed_tokens = current_batch and (current_tokens + node_tokens > EMBEDDING_BATCH_TOKEN_LIMIT)

        if would_exceed_count or would_exceed_tokens:
            batches.append(current_batch)
            current_batch = []
            current_tokens = 0

        current_batch.append(node)
        current_tokens += node_tokens

    if current_batch:
        batches.append(current_batch)

    return batches


def main() -> None:
    parser = argparse.ArgumentParser(description="Re-embed KG nodes into Qdrant")
    parser.add_argument("--status", action="store_true", help="Show embedding status")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be embedded")
    parser.add_argument("--confirm", action="store_true", help="Actually embed and upsert")
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Delete and recreate the Qdrant collection before re-embedding all nodes",
    )
    parser.add_argument("--types", help="Comma-separated node types to embed (default: all)")
    parser.add_argument("--db-url", help="Database URL")
    parser.add_argument(
        "--collection",
        default=COLLECTION_KG,
        help=f"Qdrant collection name (default: {COLLECTION_KG})",
    )
    parser.add_argument(
        "--vector-name",
        default=VECTOR_NAME,
        help="Named vector to upsert/search within the collection (default: single-vector collection)",
    )
    args = parser.parse_args()

    db_url = args.db_url or get_db_url()
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    collection_name = args.collection
    vector_name = args.vector_name.strip()

    # Connect to DB
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute(f"SET search_path TO {SCHEMA}")

    # Connect to Qdrant
    qdrant_proxy = get_qdrant_proxy_client()
    qdrant = None if qdrant_proxy else get_qdrant_client()

    # Check collection exists
    try:
        info = (qdrant_proxy or qdrant).get_collection(collection_name)
        qdrant_count = info.points_count
        print(f"Qdrant collection '{collection_name}': {qdrant_count:,} points")
        if args.recreate:
            if not args.confirm:
                print("Use --confirm with --recreate to rebuild the collection.")
                return
            if qdrant_proxy:
                qdrant_proxy.recreate_collection(collection_name, EMBEDDING_DIM, vector_name)
            else:
                qdrant.delete_collection(collection_name)
                qdrant.create_collection(
                    collection_name=collection_name,
                    vectors_config=build_vectors_config(EMBEDDING_DIM, vector_name),
                )
            vector_label = f", named vector '{vector_name}'" if vector_name else ""
            print(f"Recreated collection '{collection_name}' ({EMBEDDING_DIM}d{vector_label})")
            qdrant_count = 0
    except Exception as e:
        print(f"Collection '{collection_name}' not found: {e}")
        if args.confirm:
            if qdrant_proxy:
                qdrant_proxy.recreate_collection(collection_name, EMBEDDING_DIM, vector_name)
            else:
                qdrant.create_collection(
                    collection_name=collection_name,
                    vectors_config=build_vectors_config(EMBEDDING_DIM, vector_name),
                )
            vector_label = f", named vector '{vector_name}'" if vector_name else ""
            print(f"Created collection '{collection_name}' ({EMBEDDING_DIM}d{vector_label})")
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
        WHERE COALESCE(label, '') != '' OR COALESCE(description, '') != ''
        {type_filter}
        ORDER BY node_id
    """, params)
    all_nodes = cur.fetchall()
    print(f"DB nodes with label or description: {len(all_nodes):,}")

    # Check which are already in Qdrant by scrolling through existing points
    existing_node_ids: set[str] = set()
    if qdrant_proxy and args.confirm and not args.recreate:
        print("ERROR: Proxy mode requires --recreate for a full deterministic rebuild.")
        sys.exit(1)

    if not args.recreate and not qdrant_proxy:
        offset = None
        while True:
            points, next_offset = qdrant.scroll(
                collection_name=collection_name,
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

    if qdrant_proxy and not args.recreate:
        print(
            "Already in Qdrant: unknown (proxy mode does not scroll existing ids; "
            "use --recreate for production rebuilds)"
        )
    else:
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
    for node in missing:
        embed_text = build_embed_text(node)
        node["embed_text"] = embed_text
        node["token_estimate"] = estimate_tokens(embed_text)

    total_chars = sum(len(node["embed_text"]) for node in missing)
    approx_tokens = sum(int(node["token_estimate"]) for node in missing)
    prepared_batches = batch_nodes(missing)
    estimated_requests = len(prepared_batches)
    print(f"Approx embedding workload: {approx_tokens:,} tokens (~{total_chars:,} chars)")
    print(
        f"Estimated requests: {estimated_requests:,} "
        f"(max {BATCH_SIZE} texts / {EMBEDDING_BATCH_TOKEN_LIMIT:,} tokens per batch, "
        f"target <= {EMBEDDING_RPD_LIMIT:,} per day)"
    )
    if estimated_requests > EMBEDDING_RPD_LIMIT:
        print(
            "WARNING: Estimated request count exceeds configured daily free-tier cap. "
            "Reduce batch size only if needed, or split the run across days."
        )

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
            print(f"  {n['node_id']:55s} [{n['type']:10s}] {len(n['embed_text']):>5} chars")
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
    previous_batch_finished_at = 0.0
    for batch_index, batch in enumerate(prepared_batches, start=1):
        texts = [str(n["embed_text"]) for n in batch]
        batch_tokens = sum(int(n["token_estimate"]) for n in batch)
        min_interval = max(
            RATE_LIMIT_DELAY,
            (60.0 * batch_tokens) / max(1, EMBEDDING_TPM_LIMIT),
            60.0 / max(1, EMBEDDING_RPM_LIMIT),
        )
        now = time.time()
        if previous_batch_finished_at:
            elapsed = now - previous_batch_finished_at
            if elapsed < min_interval:
                sleep_for = min_interval - elapsed
                print(
                    f"  Sleeping {sleep_for:.1f}s to stay under ~{EMBEDDING_TPM_LIMIT:,} TPM "
                    f"(batch ≈ {batch_tokens:,} tokens)"
                )
                time.sleep(sleep_for)

        while True:
            try:
                result = genai.embed_content(
                    model=EMBEDDING_MODEL,
                    content=texts,
                    task_type="retrieval_document",
                )
                embeddings = result["embedding"]
                break
            except Exception as e:
                print(f"  ERROR embedding batch {batch_index}: {e}")
                if "429" in str(e):
                    print("  Rate limited. Waiting 60s before retrying the same batch...")
                    time.sleep(60)
                    continue
                raise

        # Build Qdrant points
        points: list[PointStruct] | list[dict[str, object]] = []
        for _j, (node, embedding) in enumerate(zip(batch, embeddings, strict=False)):
            # Use deterministic numeric ID from node_id hash
            point_id = int(hashlib.md5(node["node_id"].encode()).hexdigest()[:16], 16)
            payload = {
                "id": node["node_id"],
                "label": node["label"],
                "type": node["type"],
                "description": (node["description"] or "")[:2000],
                "period": node["period"],
                "language": node.get("language"),
                "author": node.get("author"),
            }
            vector_payload = {vector_name: embedding} if vector_name else embedding
            if qdrant_proxy:
                points.append(
                    {
                        "id": point_id,
                        "vector": vector_payload,
                        "payload": payload,
                    }
                )
            else:
                points.append(
                    PointStruct(
                        id=point_id,
                        vector=vector_payload,
                        payload=payload,
                    )
                )

        if qdrant_proxy:
            qdrant_proxy.upsert(
                collection_name=collection_name,
                points=points,
            )
        else:
            qdrant.upsert(collection_name=collection_name, points=points)
        total_embedded += len(points)
        previous_batch_finished_at = time.time()
        print(f"  Batch {batch_index}/{len(prepared_batches)}: "
              f"embedded {len(points)} nodes (total: {total_embedded:,})")

    print(f"\nDone! Embedded {total_embedded:,} nodes into {collection_name}")
    conn.close()


if __name__ == "__main__":
    main()
