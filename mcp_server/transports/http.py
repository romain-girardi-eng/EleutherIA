"""HTTP/SSE transport entrypoint.

Run with::

    MCP_API_TOKEN=<secret> python -m mcp_server.transports.http \\
        --host 0.0.0.0 --port 8020

For remote agents (sst/opencode on the the platform host, browser-based
clients). All requests must carry ``Authorization: Bearer <token>``;
the server refuses to start without ``MCP_API_TOKEN`` set, so an
unauthenticated MCP endpoint never goes online by accident.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from mcp_server.server import mcp

logger = logging.getLogger(__name__)


class BearerAuthMiddleware(BaseHTTPMiddleware):
    """Reject any request whose ``Authorization`` header is missing or wrong.

    Health-check routes (``/health`` and ``/livez``) are allowed through so
    container orchestrators can probe without leaking the token.
    """

    def __init__(self, app, token: str) -> None:  # type: ignore[no-untyped-def]
        super().__init__(app)
        self._token = token

    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        if request.url.path in {"/health", "/livez"}:
            return await call_next(request)
        provided = request.headers.get("authorization", "")
        expected = f"Bearer {self._token}"
        if provided != expected:
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        return await call_next(request)


async def _healthz(_: Request) -> Response:
    return JSONResponse({"status": "ok"})


def main() -> None:
    parser = argparse.ArgumentParser(description="EleutherIA MCP HTTP/SSE server")
    parser.add_argument("--host", default=os.getenv("MCP_HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(os.getenv("MCP_PORT", "8020")))
    parser.add_argument(
        "--transport",
        default=os.getenv("MCP_TRANSPORT", "sse"),
        choices=["sse", "streamable-http"],
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    token = os.getenv("MCP_API_TOKEN", "").strip()
    if not token:
        sys.stderr.write(
            "FATAL: MCP_API_TOKEN must be set before starting the HTTP transport.\n"
            "Refusing to run unauthenticated.\n"
        )
        sys.exit(2)

    # Configure FastMCP's bind address before pulling its ASGI app.
    mcp.settings.host = args.host
    mcp.settings.port = args.port

    app = mcp.sse_app() if args.transport == "sse" else mcp.streamable_http_app()

    app.add_middleware(BearerAuthMiddleware, token=token)
    app.add_route("/health", _healthz, methods=["GET"])
    app.add_route("/livez", _healthz, methods=["GET"])

    import uvicorn

    logger.info("Starting MCP %s server on %s:%d", args.transport, args.host, args.port)
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
