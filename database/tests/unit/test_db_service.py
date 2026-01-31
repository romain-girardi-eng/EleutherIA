"""Tests for DatabaseService."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from eleutheria_database.services.db import DatabaseService


class TestDatabaseService:
    """Tests for DatabaseService class."""

    def test_init(self):
        """Test initialization."""
        db = DatabaseService()
        assert db.pool is None
        assert db._acquire_timeout is None

    def test_is_connected_no_pool(self):
        """Test is_connected when pool is None."""
        db = DatabaseService()
        assert db.is_connected() is False

    @pytest.mark.asyncio
    async def test_connection_without_connect(self):
        """Test that using connection without connect raises error."""
        db = DatabaseService()
        with pytest.raises(RuntimeError, match="Database not connected"):
            async with db.connection():
                pass

    @pytest.mark.asyncio
    async def test_connect_success(self):
        """Test successful connection."""
        db = DatabaseService()

        mock_pool = MagicMock()
        mock_pool._closed = False

        with (
            patch("asyncpg.create_pool", new_callable=AsyncMock, return_value=mock_pool),
            patch.dict("os.environ", {
                "POSTGRES_HOST": "localhost",
                "POSTGRES_PORT": "5432",
                "POSTGRES_DB": "test",
                "POSTGRES_USER": "test",
                "POSTGRES_PASSWORD": "test",
            }),
        ):
            await db.connect()

        assert db.pool is not None
        assert db.is_connected() is True

    @pytest.mark.asyncio
    async def test_close(self):
        """Test closing connection pool."""
        db = DatabaseService()
        mock_pool = AsyncMock()
        db.pool = mock_pool

        await db.close()
        mock_pool.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch(self):
        """Test fetch method."""
        db = DatabaseService()

        mock_row = {"id": 1, "name": "test"}
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[MagicMock(**mock_row)])

        mock_pool = MagicMock()
        mock_pool.acquire = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_conn)))
        db.pool = mock_pool
        db._acquire_timeout = 10

        # Mock the context manager properly
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

        result = await db.fetch("SELECT * FROM test")
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_fetchrow(self):
        """Test fetchrow method."""
        db = DatabaseService()

        mock_row = MagicMock()
        mock_row.__iter__ = lambda _self: iter([("id", 1), ("name", "test")])
        mock_row.keys = lambda: ["id", "name"]
        mock_row.__getitem__ = lambda _self, key: {"id": 1, "name": "test"}[key]

        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value=mock_row)

        mock_pool = MagicMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
        db.pool = mock_pool
        db._acquire_timeout = 10

        result = await db.fetchrow("SELECT * FROM test WHERE id = $1", 1)
        assert result is not None

    @pytest.mark.asyncio
    async def test_fetchrow_no_result(self):
        """Test fetchrow when no result."""
        db = DatabaseService()

        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value=None)

        mock_pool = MagicMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
        db.pool = mock_pool
        db._acquire_timeout = 10

        result = await db.fetchrow("SELECT * FROM test WHERE id = $1", 999)
        assert result is None

    @pytest.mark.asyncio
    async def test_fetchval(self):
        """Test fetchval method."""
        db = DatabaseService()

        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value=42)

        mock_pool = MagicMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
        db.pool = mock_pool
        db._acquire_timeout = 10

        result = await db.fetchval("SELECT COUNT(*) FROM test")
        assert result == 42

    @pytest.mark.asyncio
    async def test_execute(self):
        """Test execute method."""
        db = DatabaseService()

        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value="INSERT 0 1")

        mock_pool = MagicMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
        db.pool = mock_pool
        db._acquire_timeout = 10

        result = await db.execute("INSERT INTO test VALUES ($1)", "value")
        assert result == "INSERT 0 1"


class TestDatabaseServiceEnvironment:
    """Tests for environment-based configuration."""

    @pytest.mark.asyncio
    async def test_ssl_mode_configuration(self):
        """Test SSL mode is configured when env var is set."""
        db = DatabaseService()

        with patch("asyncpg.create_pool", new_callable=AsyncMock) as mock_create_pool:
            mock_create_pool.return_value = MagicMock(_closed=False)

            with patch.dict("os.environ", {
                "POSTGRES_HOST": "cloud.example.com",
                "POSTGRES_SSLMODE": "require",
            }):
                await db.connect()

            # Verify SSL was passed to create_pool
            call_kwargs = mock_create_pool.call_args.kwargs
            assert call_kwargs.get("ssl") == "require"

    @pytest.mark.asyncio
    async def test_pool_size_configuration(self):
        """Test pool size configuration from environment."""
        db = DatabaseService()

        with patch("asyncpg.create_pool", new_callable=AsyncMock) as mock_create_pool:
            mock_create_pool.return_value = MagicMock(_closed=False)

            with patch.dict("os.environ", {
                "DB_POOL_MIN_SIZE": "10",
                "DB_POOL_MAX_SIZE": "50",
            }):
                await db.connect()

            call_kwargs = mock_create_pool.call_args.kwargs
            assert call_kwargs["min_size"] == 10
            assert call_kwargs["max_size"] == 50
