from collections.abc import AsyncGenerator

import asyncpg

from auth.config import auth_conf
from shared_lib import AsyncpgPostgresConnector

__all__ = ("db_client", "get_transaction_connection")


db_client = AsyncpgPostgresConnector(dsn=auth_conf.get_db_url)


async def get_transaction_connection() -> AsyncGenerator[asyncpg.Connection, None]:
    async with db_client.acquire() as conn:
        async with conn.transaction():
            yield conn
