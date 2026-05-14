"""stdio transport entrypoint.

Run with::

    python -m mcp_server.transports.stdio

stdio is for local agent subprocesses (Claude Desktop, Cursor, etc.).
No auth — the parent process owns the subprocess.
"""

from __future__ import annotations

import logging

from mcp_server.server import mcp


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    mcp.run("stdio")


if __name__ == "__main__":
    main()
