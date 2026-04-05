from contextlib import asynccontextmanager
from typing import AsyncGenerator

import asyncpg
from loguru import logger


class AsyncpgPostgresConnector:
    """Lightweight asyncpg pool connector used by events-oriented services."""

    def __init__(self, dsn: str, min_size: int = 1, max_size: int = 10):
        self._dsn = dsn
        self._min_size = min_size
        self._max_size = max_size
        self._pool: asyncpg.Pool | None = None

    @property
    def pool(self) -> asyncpg.Pool | None:
        return self._pool

    async def connect(self) -> asyncpg.Pool | None:
        if self._pool is not None:
            return self._pool
        try:
            self._pool = await asyncpg.create_pool(
                dsn=self._dsn,
                min_size=self._min_size,
                max_size=self._max_size,
            )
            logger.info("Successful asyncpg pool connection")
            return self._pool
        except Exception:
            logger.error(
                "DB connection error: Error while connecting to postgres via asyncpg",
                extra={"dsn": self._dsn},
                exc_info=True,
            )
            return None

    async def disconnect(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None
            logger.info("asyncpg pool closed")

    @asynccontextmanager
    async def acquire(self) -> AsyncGenerator[asyncpg.Connection, None]:
        pool = self._pool or await self.connect()
        if pool is None:
            raise RuntimeError("Postgres connector is not connected.")
        async with pool.acquire() as connection:
            yield connection
