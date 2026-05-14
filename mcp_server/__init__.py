"""MCP server exposing EleutherIA's GraphRAG tools.

Wraps the existing in-process agent tools (search_passages, search_nodes,
read_passages, get_node_detail, explore_subgraph, read_work_section,
get_neighbors) as Model Context Protocol tools so external agents
(Claude Desktop, Cursor, sst/opencode, etc.) can call them over stdio
or HTTP/SSE.
"""

from mcp_server.server import build_server

__all__ = ["build_server"]
