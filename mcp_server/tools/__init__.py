"""MCP tool registrations for EleutherIA's GraphRAG surface."""

from mcp_server.tools.consensus import register as register_consensus
from mcp_server.tools.kg import register as register_kg
from mcp_server.tools.read import register as register_read
from mcp_server.tools.search import register as register_search

__all__ = [
    "register_consensus",
    "register_kg",
    "register_read",
    "register_search",
]
