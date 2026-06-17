# EleutherIA MCP Server

MCP (Model Context Protocol) server exposing EleutherIA's GraphRAG tools so external
agents — Claude Desktop, Cursor, sst/opencode, future orchestrators — can call them
over stdio or HTTP/SSE.

Wraps the 7 in-process ReAct agent tools with no logic reimplementation:

| MCP tool | Wraps | Purpose |
|---|---|---|
| `search_passages` | `SearchPassagesTool` | Full-text + lemmatic search across 69k ancient passages |
| `search_nodes` | `SearchNodesTool` | KG node lookup by label / description / type / period |
| `read_passages` | `ReadPassagesTool` | Pull passages linked to a KG node (+ English translation) |
| `read_work_section` | `ReadWorkSectionTool` | Navigate the hierarchical TOC of an ancient work |
| `get_node_detail` | `GetNodeDetailTool` | Full metadata + neighbor / passage counts for one node |
| `get_neighbors` | `GetNeighborsTool` | Immediate graph edges from a node (filterable by relation) |
| `explore_subgraph` | `ExploreSubgraphTool` | PPR-based subgraph discovery from seed nodes |

## Architecture

```
                +--------------------+
  agent  --->   |  MCP server (this) |  ----> Deps (asyncpg pool + KG snapshot)
 (stdio/HTTP)   |  FastMCP            |             |
                +--------------------+              |
                                                    v
                                          Postgres / Supabase
                                          KG JSONL snapshot
```

The MCP server is a thin adapter. The actual retrieval logic lives in
`graphrag/src/eleutheria_graphrag/agents/tools/*.py` and is unchanged.

## Run locally (stdio)

```bash
cd [local-path]
.venv-py314/bin/pip install -e mcp_server/
DATABASE_URL=postgresql://... \
ELEUTHERIA_KG_SNAPSHOT_DIR=data/kg \
python -m mcp_server.transports.stdio
```

No auth is needed for stdio — the parent agent owns the subprocess.

## Run as HTTP/SSE service

```bash
MCP_API_TOKEN=$(openssl rand -hex 32) \
DATABASE_URL=postgresql://... \
python -m mcp_server.transports.http --host 0.0.0.0 --port 8020
```

Server refuses to start without `MCP_API_TOKEN`. All requests must carry
`Authorization: Bearer <token>` — exception: `/health` and `/livez` are unauthenticated
so orchestrators can probe.

Default transport is SSE. Switch to streamable HTTP with `--transport streamable-http`.

## Claude Desktop integration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "eleutheria": {
      "command": "[local-path]",
      "args": ["-m", "mcp_server.transports.stdio"],
      "env": {
        "DATABASE_URL": "postgresql://...",
        "ELEUTHERIA_KG_SNAPSHOT_DIR": "[local-path]"
      }
    }
  }
}
```

## sst/opencode integration

Once `mcp.free-will.app` is exposed, point opencode at the SSE endpoint:

```jsonc
// opencode.json
{
  "mcp": {
    "eleutheria": {
      "type": "sse",
      "url": "https://mcp.free-will.app/sse",
      "headers": {
        "Authorization": "Bearer ${MCP_API_TOKEN}"
      }
    }
  }
}
```

Until DNS is up, target the host directly: `http://localhost:8020/sse` on the
deploy host, or expose via a Cloudflare tunnel.

## Test against the live deployment

Use the official MCP inspector:

```bash
npx @modelcontextprotocol/inspector \
  --header "Authorization: Bearer $MCP_API_TOKEN" \
  https://mcp.free-will.app/sse
```

Or curl-probe the auth + health endpoints:

```bash
curl -i https://mcp.free-will.app/health
curl -i -H "Authorization: Bearer $MCP_API_TOKEN" https://mcp.free-will.app/sse
```

## Tests

```bash
cd [local-path]
.venv-py314/bin/pytest mcp_server/tests/ --no-cov -q
```

Tests stub the global `DepsContainer` so no live Postgres is required.

## Compose integration

`deploy/production/docker-compose.yml` defines `eleutheria-mcp` under the `mcp` profile.
It stays opt-in until explicitly enabled:

```bash
docker compose --profile mcp up -d eleutheria-mcp
```
