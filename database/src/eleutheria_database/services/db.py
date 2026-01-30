"""
Database Service - PostgreSQL connection management for EleutherIA.

This module provides async connection pooling and query execution
for the ancient texts corpus.
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import Any

import asyncpg

logger = logging.getLogger(__name__)


class DatabaseService:
    """
    Manages PostgreSQL database connections and queries.

    Usage:
        db = DatabaseService()
        await db.connect()

        works = await db.fetch("SELECT * FROM free_will.ancient_works LIMIT 10")

        await db.close()
    """

    def __init__(self) -> None:
        self.pool: asyncpg.Pool | None = None
        self._acquire_timeout: float | None = None

    async def connect(self) -> None:
        """
        Establish connection pool to PostgreSQL.

        Configuration via environment variables:
            POSTGRES_HOST: Database host (default: localhost)
            POSTGRES_PORT: Database port (default: 5432)
            POSTGRES_DB: Database name (default: postgres)
            POSTGRES_USER: Username (default: postgres)
            POSTGRES_PASSWORD: Password (default: empty)
            POSTGRES_SSLMODE: SSL mode for cloud databases
            DB_POOL_MIN_SIZE: Minimum pool size (default: 5)
            DB_POOL_MAX_SIZE: Maximum pool size (default: 15)
            DB_POOL_ACQUIRE_TIMEOUT: Connection acquire timeout (default: 10)
        """
        try:
            min_pool_size = int(os.getenv("DB_POOL_MIN_SIZE", "5"))
            max_pool_size = int(os.getenv("DB_POOL_MAX_SIZE", "15"))
            acquire_timeout = float(os.getenv("DB_POOL_ACQUIRE_TIMEOUT", "10"))
            self._acquire_timeout = acquire_timeout

            db_config: dict[str, Any] = {
                "host": os.getenv("POSTGRES_HOST", "localhost"),
                "port": int(os.getenv("POSTGRES_PORT", "5432")),
                "database": os.getenv("POSTGRES_DB", "postgres"),
                "user": os.getenv("POSTGRES_USER", "postgres"),
                "password": os.getenv("POSTGRES_PASSWORD", ""),
                "min_size": min_pool_size,
                "max_size": max_pool_size,
                "command_timeout": 60,
                "statement_cache_size": 0,  # Disable for pgbouncer compatibility
                "timeout": acquire_timeout,
            }

            # Add SSL for cloud databases
            ssl_mode = os.getenv("POSTGRES_SSLMODE")
            if ssl_mode:
                db_config["ssl"] = ssl_mode

            self.pool = await asyncpg.create_pool(**db_config)
            logger.info(
                "PostgreSQL connection pool created",
                extra={
                    "min_size": min_pool_size,
                    "max_size": max_pool_size,
                    "acquire_timeout": acquire_timeout,
                },
            )

        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise

    async def close(self) -> None:
        """Close connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("PostgreSQL connection pool closed")

    def is_connected(self) -> bool:
        """Check if connection pool is active."""
        return self.pool is not None and not self.pool._closed

    @asynccontextmanager
    async def connection(self):
        """
        Get a connection from the pool.

        Usage:
            async with db.connection() as conn:
                result = await conn.fetch("SELECT * FROM ...")
        """
        if not self.pool:
            raise RuntimeError("Database not connected. Call connect() first.")

        acquire_kwargs: dict[str, Any] = {}
        if self._acquire_timeout is not None:
            acquire_kwargs["timeout"] = self._acquire_timeout

        async with self.pool.acquire(**acquire_kwargs) as conn:
            yield conn

    async def fetch(self, query: str, *args: Any) -> list[dict[str, Any]]:
        """
        Execute query and fetch all results.

        Args:
            query: SQL query string
            *args: Query parameters

        Returns:
            List of rows as dictionaries
        """
        async with self.connection() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]

    async def fetchrow(self, query: str, *args: Any) -> dict[str, Any] | None:
        """
        Execute query and fetch single result.

        Args:
            query: SQL query string
            *args: Query parameters

        Returns:
            Single row as dictionary, or None if no results
        """
        async with self.connection() as conn:
            row = await conn.fetchrow(query, *args)
            return dict(row) if row else None

    async def fetchval(self, query: str, *args: Any) -> Any:
        """
        Execute query and fetch single value.

        Args:
            query: SQL query string
            *args: Query parameters

        Returns:
            Single value from first column of first row
        """
        async with self.connection() as conn:
            return await conn.fetchval(query, *args)

    async def execute(self, query: str, *args: Any) -> str:
        """
        Execute query without returning results.

        Args:
            query: SQL query string
            *args: Query parameters

        Returns:
            Command status string
        """
        async with self.connection() as conn:
            result = await conn.execute(query, *args)
            return str(result) if result else ""
