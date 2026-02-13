#!/usr/bin/env python3
"""
Precompute KG data for Cloudflare KV upload.

Phase 6 offline script that:
1. Loads KG nodes and edges from PostgreSQL (free_will schema)
2. Computes PageRank scores using networkx
3. Generates 3-level community hierarchy using Leiden algorithm
4. Generates placeholder community summaries
5. Exports JSON files for Cloudflare KV upload
6. Optionally uploads to KV via wrangler CLI

Usage:
    python scripts/precompute_kg_data.py
    python scripts/precompute_kg_data.py --output-dir ./kv_data
    python scripts/precompute_kg_data.py --upload-kv
    python scripts/precompute_kg_data.py --upload-kv --kv-namespace-id 9506f86aab4845818bd7644508d504e6
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import asyncpg
import igraph as ig
import leidenalg
import networkx as nx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Default KV namespace ID from wrangler.toml (TEXT_CACHE)
DEFAULT_KV_NAMESPACE_ID = "9506f86aab4845818bd7644508d504e6"


# ------------------------------------------------------------------
# Database helpers
# ------------------------------------------------------------------

async def get_connection(database_url: str) -> asyncpg.Connection:
    """Create an asyncpg connection with free_will search_path."""
    conn = await asyncpg.connect(database_url)
    await conn.execute("SET search_path = free_will, public;")
    return conn


async def load_nodes(conn: asyncpg.Connection) -> list[dict[str, Any]]:
    """Load all KG nodes from PostgreSQL."""
    rows = await conn.fetch(
        """
        SELECT
            node_id,
            label,
            type,
            description,
            period,
            school,
            role,
            metadata
        FROM kg_nodes
        ORDER BY node_id
        """
    )
    nodes = []
    for row in rows:
        node = dict(row)
        # asyncpg returns JSONB as dict already, but ensure serialisability
        if node["metadata"] is not None and not isinstance(node["metadata"], dict):
            node["metadata"] = json.loads(node["metadata"])
        nodes.append(node)
    logger.info("Loaded %d nodes from kg_nodes", len(nodes))
    return nodes


async def load_edges(conn: asyncpg.Connection) -> list[dict[str, Any]]:
    """Load all KG edges from PostgreSQL."""
    rows = await conn.fetch(
        """
        SELECT
            edge_id::text AS edge_id,
            source_id,
            target_id,
            relation,
            description,
            weight,
            metadata
        FROM kg_edges
        ORDER BY source_id, target_id
        """
    )
    edges = []
    for row in rows:
        edge = dict(row)
        if edge["metadata"] is not None and not isinstance(edge["metadata"], dict):
            edge["metadata"] = json.loads(edge["metadata"])
        edges.append(edge)
    logger.info("Loaded %d edges from kg_edges", len(edges))
    return edges


# ------------------------------------------------------------------
# NetworkX graph construction
# ------------------------------------------------------------------

def build_networkx_graph(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> nx.DiGraph:
    """Build a NetworkX directed graph from nodes and edges."""
    G = nx.DiGraph()
    for node in nodes:
        G.add_node(
            node["node_id"],
            label=node["label"],
            type=node["type"],
            period=node.get("period"),
            school=node.get("school"),
        )
    for edge in edges:
        G.add_edge(
            edge["source_id"],
            edge["target_id"],
            relation=edge["relation"],
            weight=edge.get("weight", 1.0),
        )
    logger.info(
        "Built NetworkX graph: %d nodes, %d edges",
        G.number_of_nodes(),
        G.number_of_edges(),
    )
    return G


# ------------------------------------------------------------------
# PageRank computation
# ------------------------------------------------------------------

def compute_pagerank(G: nx.DiGraph, alpha: float = 0.85) -> dict[str, float]:
    """Compute PageRank scores for all nodes."""
    logger.info("Computing PageRank (alpha=%.2f) ...", alpha)
    scores = nx.pagerank(G, alpha=alpha, weight="weight")
    # Sort descending by score
    sorted_scores = dict(
        sorted(scores.items(), key=lambda item: item[1], reverse=True)
    )
    top_5 = list(sorted_scores.items())[:5]
    logger.info(
        "PageRank computed. Top 5: %s",
        ", ".join(f"{nid}={score:.6f}" for nid, score in top_5),
    )
    return sorted_scores


# ------------------------------------------------------------------
# Leiden community detection (3-level hierarchy)
# ------------------------------------------------------------------

def _nx_to_igraph(G: nx.DiGraph) -> tuple[ig.Graph, list[str]]:
    """Convert NetworkX directed graph to igraph (undirected for community detection)."""
    # Map node IDs to integer indices
    node_list = list(G.nodes())
    node_index = {nid: i for i, nid in enumerate(node_list)}

    ig_edges = []
    ig_weights = []
    for u, v, data in G.edges(data=True):
        ig_edges.append((node_index[u], node_index[v]))
        ig_weights.append(data.get("weight", 1.0))

    # Create undirected igraph for Leiden (community detection works on undirected)
    ig_graph = ig.Graph(n=len(node_list), edges=ig_edges, directed=False)
    ig_graph.es["weight"] = ig_weights

    # Attach node attributes
    ig_graph.vs["name"] = node_list
    for i, nid in enumerate(node_list):
        nx_attrs = G.nodes[nid]
        ig_graph.vs[i]["label"] = nx_attrs.get("label", nid)
        ig_graph.vs[i]["type"] = nx_attrs.get("type", "Unknown")

    return ig_graph, node_list


def compute_leiden_communities(
    G: nx.DiGraph,
    resolutions: tuple[float, float, float] = (0.5, 1.0, 2.0),
) -> dict[str, Any]:
    """
    Compute 3-level Leiden community hierarchy.

    Each resolution produces a different granularity:
      - Level 0 (low resolution): coarse, few large communities
      - Level 1 (default resolution): balanced communities
      - Level 2 (high resolution): fine-grained, many small communities
    """
    ig_graph, node_list = _nx_to_igraph(G)

    hierarchy: dict[str, Any] = {
        "levels": [],
        "node_assignments": {},  # node_id -> [level0_id, level1_id, level2_id]
    }

    # Initialize node assignments
    for nid in node_list:
        hierarchy["node_assignments"][nid] = [None, None, None]

    for level, resolution in enumerate(resolutions):
        logger.info(
            "Running Leiden (level %d, resolution=%.2f) ...", level, resolution
        )
        partition = leidenalg.find_partition(
            ig_graph,
            leidenalg.RBConfigurationVertexPartition,
            resolution_parameter=resolution,
            weights="weight",
            seed=42,
        )

        communities: list[dict[str, Any]] = []
        for comm_id, members in enumerate(partition):
            member_ids = [node_list[m] for m in members]
            # Determine dominant type and period for summary
            type_counts: dict[str, int] = {}
            period_counts: dict[str, int] = {}
            for m in members:
                ntype = ig_graph.vs[m]["type"]
                type_counts[ntype] = type_counts.get(ntype, 0) + 1
                period = G.nodes[ig_graph.vs[m]["name"]].get("period")
                if period:
                    period_counts[period] = period_counts.get(period, 0) + 1

            dominant_type = max(type_counts, key=type_counts.get) if type_counts else "Unknown"
            dominant_period = max(period_counts, key=period_counts.get) if period_counts else None

            # Placeholder community summary (no LLM call)
            summary = (
                f"Community {comm_id} at level {level} "
                f"({len(member_ids)} nodes, primarily {dominant_type} nodes"
            )
            if dominant_period:
                summary += f", {dominant_period} period"
            summary += "). Summary pending LLM generation."

            communities.append(
                {
                    "community_id": comm_id,
                    "level": level,
                    "resolution": resolution,
                    "node_count": len(member_ids),
                    "node_ids": member_ids,
                    "dominant_type": dominant_type,
                    "dominant_period": dominant_period,
                    "summary": summary,
                }
            )

            # Record per-node assignment
            for nid in member_ids:
                hierarchy["node_assignments"][nid][level] = comm_id

        hierarchy["levels"].append(
            {
                "level": level,
                "resolution": resolution,
                "num_communities": len(communities),
                "modularity": partition.modularity,
                "communities": communities,
            }
        )

        logger.info(
            "Level %d: %d communities (modularity=%.4f)",
            level,
            len(communities),
            partition.modularity,
        )

    return hierarchy


# ------------------------------------------------------------------
# Build output JSON payloads
# ------------------------------------------------------------------

def build_pagerank_output(
    scores: dict[str, float],
    G: nx.DiGraph,
) -> dict[str, Any]:
    """Build the pagerank_scores.json payload."""
    now = datetime.now(timezone.utc).isoformat()
    entries = []
    for node_id, score in scores.items():
        attrs = G.nodes.get(node_id, {})
        entries.append(
            {
                "node_id": node_id,
                "score": round(score, 8),
                "label": attrs.get("label", node_id),
                "type": attrs.get("type", "Unknown"),
            }
        )
    return {
        "generated_at": now,
        "algorithm": "pagerank",
        "alpha": 0.85,
        "total_nodes": len(entries),
        "scores": entries,
    }


def build_nodes_index(
    nodes: list[dict[str, Any]],
    pagerank_scores: dict[str, float],
    community_hierarchy: dict[str, Any],
) -> dict[str, Any]:
    """Build the kg_nodes_index.json payload (enriched node data for KV)."""
    now = datetime.now(timezone.utc).isoformat()
    node_assignments = community_hierarchy.get("node_assignments", {})
    indexed_nodes = []
    for node in nodes:
        nid = node["node_id"]
        indexed_nodes.append(
            {
                "node_id": nid,
                "label": node["label"],
                "type": node["type"],
                "description": node.get("description"),
                "period": node.get("period"),
                "school": node.get("school"),
                "role": node.get("role"),
                "pagerank": round(pagerank_scores.get(nid, 0.0), 8),
                "communities": node_assignments.get(nid, [None, None, None]),
            }
        )
    # Sort by pagerank descending for convenient top-k access
    indexed_nodes.sort(key=lambda n: n["pagerank"], reverse=True)
    return {
        "generated_at": now,
        "total_nodes": len(indexed_nodes),
        "nodes": indexed_nodes,
    }


def build_edges_index(edges: list[dict[str, Any]]) -> dict[str, Any]:
    """Build the kg_edges_index.json payload."""
    now = datetime.now(timezone.utc).isoformat()
    # Build adjacency lists for fast lookup
    adjacency: dict[str, list[dict[str, Any]]] = {}
    for edge in edges:
        src = edge["source_id"]
        entry = {
            "target_id": edge["target_id"],
            "relation": edge["relation"],
            "weight": edge.get("weight", 1.0),
            "description": edge.get("description"),
        }
        adjacency.setdefault(src, []).append(entry)

    return {
        "generated_at": now,
        "total_edges": len(edges),
        "total_source_nodes": len(adjacency),
        "adjacency": adjacency,
    }


# ------------------------------------------------------------------
# File I/O
# ------------------------------------------------------------------

def write_json(data: dict[str, Any], path: Path) -> None:
    """Write a JSON file with compact but readable formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    size_kb = path.stat().st_size / 1024
    logger.info("Wrote %s (%.1f KB)", path, size_kb)


# ------------------------------------------------------------------
# Wrangler KV upload
# ------------------------------------------------------------------

def upload_to_kv(
    json_files: dict[str, Path],
    namespace_id: str,
) -> None:
    """Upload JSON files to Cloudflare KV using wrangler CLI."""
    logger.info("Uploading %d files to KV namespace %s ...", len(json_files), namespace_id)

    for key_name, file_path in json_files.items():
        if not file_path.exists():
            logger.warning("Skipping %s: file not found at %s", key_name, file_path)
            continue

        value = file_path.read_text(encoding="utf-8")
        logger.info("Uploading key '%s' (%d bytes) ...", key_name, len(value))

        try:
            result = subprocess.run(
                [
                    "wrangler",
                    "kv:key",
                    "put",
                    "--namespace-id",
                    namespace_id,
                    key_name,
                    value,
                ],
                capture_output=True,
                text=True,
                check=True,
                timeout=60,
            )
            logger.info("Uploaded '%s': %s", key_name, result.stdout.strip())
        except FileNotFoundError:
            logger.error(
                "wrangler CLI not found. Install with: npm install -g wrangler"
            )
            sys.exit(1)
        except subprocess.CalledProcessError as e:
            logger.error("Failed to upload '%s': %s", key_name, e.stderr.strip())
            sys.exit(1)
        except subprocess.TimeoutExpired:
            logger.error("Timeout uploading '%s'", key_name)
            sys.exit(1)

    logger.info("All KV uploads complete.")


# ------------------------------------------------------------------
# Main pipeline
# ------------------------------------------------------------------

async def run(args: argparse.Namespace) -> None:
    """Execute the full precomputation pipeline."""
    database_url = args.database_url or os.environ.get("DATABASE_URL")
    if not database_url:
        logger.error(
            "DATABASE_URL not set. Provide --database-url or set the DATABASE_URL "
            "environment variable."
        )
        sys.exit(1)

    output_dir = Path(args.output_dir)

    # ---- Step 1: Load data from PostgreSQL ----
    logger.info("Connecting to PostgreSQL ...")
    conn = await get_connection(database_url)
    try:
        nodes = await load_nodes(conn)
        edges = await load_edges(conn)
    finally:
        await conn.close()

    if not nodes:
        logger.error("No nodes found in kg_nodes. Aborting.")
        sys.exit(1)

    # ---- Step 2: Build graph ----
    G = build_networkx_graph(nodes, edges)

    # ---- Step 3: Compute PageRank ----
    pagerank_scores = compute_pagerank(G)

    # ---- Step 4: Compute Leiden communities (3 levels) ----
    community_hierarchy = compute_leiden_communities(G)

    # ---- Step 5: Build output payloads ----
    pagerank_output = build_pagerank_output(pagerank_scores, G)
    nodes_index = build_nodes_index(nodes, pagerank_scores, community_hierarchy)
    edges_index = build_edges_index(edges)

    # Include community data in the nodes index
    nodes_index["community_hierarchy"] = {
        "levels": [
            {
                "level": lvl["level"],
                "resolution": lvl["resolution"],
                "num_communities": lvl["num_communities"],
                "modularity": lvl["modularity"],
                "communities": [
                    {
                        "community_id": c["community_id"],
                        "node_count": c["node_count"],
                        "dominant_type": c["dominant_type"],
                        "dominant_period": c["dominant_period"],
                        "summary": c["summary"],
                    }
                    for c in lvl["communities"]
                ],
            }
            for lvl in community_hierarchy["levels"]
        ],
    }

    # ---- Step 6: Write JSON files ----
    pagerank_path = output_dir / "pagerank_scores.json"
    nodes_path = output_dir / "kg_nodes_index.json"
    edges_path = output_dir / "kg_edges_index.json"

    write_json(pagerank_output, pagerank_path)
    write_json(nodes_index, nodes_path)
    write_json(edges_index, edges_path)

    logger.info(
        "Precomputation complete: %d nodes, %d edges, %d community levels",
        len(nodes),
        len(edges),
        len(community_hierarchy["levels"]),
    )

    # ---- Step 7 (optional): Upload to KV ----
    if args.upload_kv:
        namespace_id = args.kv_namespace_id or DEFAULT_KV_NAMESPACE_ID
        upload_to_kv(
            {
                "kg:pagerank": pagerank_path,
                "kg:nodes_index": nodes_path,
                "kg:edges_index": edges_path,
            },
            namespace_id=namespace_id,
        )


# ------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Precompute KG data (PageRank, Leiden communities) for Cloudflare KV.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/precompute_kg_data.py
  python scripts/precompute_kg_data.py --output-dir ./kv_data
  python scripts/precompute_kg_data.py --upload-kv
  python scripts/precompute_kg_data.py --upload-kv --kv-namespace-id <id>
  DATABASE_URL=postgresql://... python scripts/precompute_kg_data.py
        """,
    )
    parser.add_argument(
        "--database-url",
        type=str,
        default=None,
        help="PostgreSQL connection URL (default: $DATABASE_URL env var)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./kv_data",
        help="Directory for output JSON files (default: ./kv_data)",
    )
    parser.add_argument(
        "--upload-kv",
        action="store_true",
        default=False,
        help="Upload output files to Cloudflare KV via wrangler CLI",
    )
    parser.add_argument(
        "--kv-namespace-id",
        type=str,
        default=None,
        help=f"KV namespace ID for upload (default: {DEFAULT_KV_NAMESPACE_ID})",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
