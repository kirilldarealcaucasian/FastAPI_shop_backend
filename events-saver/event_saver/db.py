import re
from collections.abc import Sequence
from pathlib import Path

from shared_lib import AsyncpgPostgresConnector

from .config import settings


def _safe_ident(name: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        raise ValueError(f"Invalid SQL identifier: {name}")
    return name


postgres_connector = AsyncpgPostgresConnector(dsn=settings.db_url)
MIGRATION_PATH = Path(__file__).resolve().parent.parent / "migration.sql"
EVENTS_SCHEMA = "events"


async def connect_db() -> None:
    await postgres_connector.connect()
    await run_migration()


async def disconnect_db() -> None:
    await postgres_connector.disconnect()


async def run_migration() -> None:
    _ = _safe_ident(settings.DB_SCHEMA)
    sql = MIGRATION_PATH.read_text(encoding="utf-8")

    async with postgres_connector.acquire() as conn:
        async with conn.transaction():
            await conn.execute(sql)


async def save_events(rows: Sequence[dict]) -> None:
    if not rows:
        return

    schema = EVENTS_SCHEMA
    query = (
        f"INSERT INTO {schema}.interaction_events "
        "(session_id, user_id, item_id, event_type, event_weight, event_timestamp) "
        "VALUES ($1, $2, $3, $4, $5, $6)"
    )

    args = [
        (
            row.get("session_id"),
            row.get("user_id"),
            row.get("item_id"),
            row.get("event_type"),
            row.get("event_weight"),
            row.get("event_timestamp"),
        )
        for row in rows
    ]

    async with postgres_connector.acquire() as conn:
        async with conn.transaction():
            await conn.executemany(query, args)
