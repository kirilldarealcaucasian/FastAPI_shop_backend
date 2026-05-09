import re
from pathlib import Path

from loguru import logger
from shared_lib import AsyncpgPostgresConnector

from .config import settings


def _safe_ident(name: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        raise ValueError(f"Invalid SQL identifier: {name}")
    return name


BASE_DIR = Path(__file__).resolve().parent.parent
MIGRATION_PATH = BASE_DIR / "migration.sql"
DB_SCHEMA = _safe_ident(settings.DB_SCHEMA)
postgres_connector = AsyncpgPostgresConnector(dsn=settings.db_url)


async def connect_db() -> None:
    logger.info("Connecting event-saver database", extra={"schema": DB_SCHEMA})
    await postgres_connector.connect()
    await run_migration()
    logger.info("event-saver database connected", extra={"schema": DB_SCHEMA})


async def disconnect_db() -> None:
    logger.info("Disconnecting event-saver database")
    await postgres_connector.disconnect()
    logger.info("event-saver database disconnected")


async def run_migration() -> None:
    sql = MIGRATION_PATH.read_text(encoding="utf-8")

    logger.info("Applying event-saver migration", extra={"path": str(MIGRATION_PATH)})
    async with postgres_connector.acquire() as conn:
        async with conn.transaction():
            await conn.execute(sql)
    logger.info("event-saver migration applied", extra={"path": str(MIGRATION_PATH)})
