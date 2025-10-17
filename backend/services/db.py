#!/usr/bin/env python3
"""
Database Service - PostgreSQL connection management
"""

import asyncpg
import logging
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'ancient_free_will_db',
    'user': 'free_will_user',
    'password': 'free_will_password'
}


class DatabaseService:
    """Manages PostgreSQL database connections and queries"""

    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> None:
        """Establish connection pool to PostgreSQL"""
        try:
            self.pool = await asyncpg.create_pool(
                **DB_CONFIG,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            logger.info("PostgreSQL connection pool created")

        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise

    async def close(self) -> None:
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("PostgreSQL connection pool closed")

    def is_connected(self) -> bool:
        """Check if connection pool is active"""
        return self.pool is not None and not self.pool._closed

    @asynccontextmanager
    async def connection(self):
        """Get a connection from the pool"""
        if not self.pool:
            raise RuntimeError("Database not connected")

        async with self.pool.acquire() as conn:
            yield conn

    async def fetch(self, query: str, *args) -> List[Dict[str, Any]]:
        """Execute query and fetch all results"""
        async with self.connection() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]

    async def fetchrow(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """Execute query and fetch single result"""
        async with self.connection() as conn:
            row = await conn.fetchrow(query, *args)
            return dict(row) if row else None

    async def fetchval(self, query: str, *args) -> Any:
        """Execute query and fetch single value"""
        async with self.connection() as conn:
            return await conn.fetchval(query, *args)

    async def execute(self, query: str, *args) -> str:
        """Execute query without returning results"""
        async with self.connection() as conn:
            return await conn.execute(query, *args)
