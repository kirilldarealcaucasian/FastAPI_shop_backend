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

    actor_mapping_query = f"""
        INSERT INTO {settings.DB_SCHEMA}.user_index_map (actor_type, user_id, session_id)
        SELECT t.actor_type, t.user_id, t.session_id
        FROM UNNEST($1::SMALLINT[], $2::INT[], $3::UUID[]) AS t(actor_type, user_id, session_id)
        WHERE NOT EXISTS (
            SELECT 1
            FROM {settings.DB_SCHEMA}.user_index_map uim
            WHERE uim.actor_type = t.actor_type
              AND uim.user_id IS NOT DISTINCT FROM t.user_id
              AND uim.session_id IS NOT DISTINCT FROM t.session_id
        )
    """
    item_mapping_query = f"""
        INSERT INTO {settings.DB_SCHEMA}.item_index_map (item_id)
        SELECT item_id
        FROM UNNEST($1::BIGINT[]) AS t(item_id)
        ON CONFLICT (item_id) DO NOTHING
    """
    actor_mappings = {
        (
            1,
            int(row["actor_id"]),
            None,
        )
        for row in rows
        if row.get("actor_id") is not None
    }
    actor_mappings |= {
        (
            2,
            None,
            row["session_id"],
        )
        for row in rows
        if row.get("actor_id") is None and row.get("session_id") is not None
    }

    actor_types = [mapping[0] for mapping in actor_mappings]
    user_ids = [mapping[1] for mapping in actor_mappings]
    session_ids = [mapping[2] for mapping in actor_mappings]
    item_ids = list({int(row["item_id"]) for row in rows})
    event_records = [
        (
            row["actor_id"],
            row["item_id"],
            row["event_type"],
            row["event_weight"],
            row["event_timestamp"],
        )
        for row in rows
    ]

    async with postgres_connector.acquire() as conn:
        async with conn.transaction():
            if actor_mappings:
                await conn.execute(
                    actor_mapping_query, actor_types, user_ids, session_ids
                )
            if item_ids:
                await conn.execute(item_mapping_query, item_ids)
            await conn.copy_records_to_table(
                "interaction_events",
                schema_name=settings.DB_SCHEMA,
                records=event_records,
                columns=(
                    "actor_id",
                    "item_id",
                    "event_type",
                    "event_weight",
                    "event_timestamp",
                ),
            )
