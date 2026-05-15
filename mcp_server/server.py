"""FastMCP server assembly for EleutherIA's GraphRAG surface."""

from __future__ import annotations

import logging

from mcp.server.fastmcp import FastMCP

from mcp_server.tools import (
    register_consensus,
    register_kg,
    register_read,
    register_search,
)

logger = logging.getLogger(__name__)

INSTRUCTIONS = """
EleutherIA exposes a curated set of read-only retrieval tools over a
knowledge graph of ancient philosophy (Greco-Roman + Early Christian)
and a corpus of 487 ancient works / 69k passages.

Typical agent flow:
  1) search_nodes(query) to locate persons / concepts / arguments.
  2) get_node_detail(node_id) for the full description.
  3) get_neighbors / explore_subgraph to traverse the KG.
  4) read_passages(node_id) for the actual ancient-text evidence.
  5) search_passages / read_work_section for direct corpus access.

Hard rule: do not fabricate ancient Greek or Latin. If a passage is
not returned by these tools, treat it as non-existent and answer in
English instead.
""".strip()


def build_server(name: str = "eleutheria-graphrag") -> FastMCP:
    """Build the FastMCP server with every EleutherIA tool registered."""
    mcp = FastMCP(name=name, instructions=INSTRUCTIONS)
    register_search(mcp)
    register_read(mcp)
    register_kg(mcp)
    register_consensus(mcp)
    return mcp


# Module-level singleton so transports can ``from mcp_server.server import mcp``.
mcp = build_server()
