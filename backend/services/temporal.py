"""Temporal client factory for the EleutherIA backend.

Used from request handlers and the CLI to dispatch workflows onto the platform's
Temporal cluster. The connection is cached per-process: Temporal's
`Client.connect()` opens a long-lived gRPC channel and there's no benefit to
opening a new one per request.

Environment:
    TEMPORAL_HOST (default: temporal:7233)
"""

from __future__ import annotations

import asyncio
import logging
import os

from temporalio.client import Client

logger = logging.getLogger(__name__)

_client: Client | None = None
_lock = asyncio.Lock()


async def get_temporal_client() -> Client:
    """Return a process-wide Temporal client, connecting on first call.

    Re-entrant under asyncio: the lock ensures only one connect happens even
    if several requests race on cold start.
    """
    global _client
    if _client is not None:
        return _client

    async with _lock:
        if _client is None:
            address = os.environ.get("TEMPORAL_HOST", "temporal:7233")
            logger.info(f"Opening Temporal client at {address}")
            _client = await Client.connect(address)
    return _client


async def close_temporal_client() -> None:
    """Drop the cached client. Mostly useful for tests; production keeps the
    connection alive for the lifetime of the process."""
    global _client
    _client = None


__all__ = ["get_temporal_client", "close_temporal_client"]
