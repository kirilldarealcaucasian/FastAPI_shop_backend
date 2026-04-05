import re
from collections.abc import AsyncIterator
from datetime import UTC, date, datetime, time, timedelta
from typing import Any

from shared_lib import AsyncpgPostgresConnector

from .config import settings


postgres_connector = AsyncpgPostgresConnector(dsn=settings.db_url)


def _safe_ident(name: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        raise ValueError(f"Invalid SQL identifier: {name}")
    return name


async def connect_db() -> None:
    await postgres_connector.connect()


async def disconnect_db() -> None:
    await postgres_connector.disconnect()


def target_date_window(lookback_days: int) -> tuple[date, datetime, datetime]:
    target_date = datetime.now(tz=UTC).date() - timedelta(days=max(1, lookback_days))
    start_dt = datetime.combine(target_date, time.min)
    end_dt = start_dt + timedelta(days=1)
    return target_date, start_dt, end_dt


async def iter_aggregated_features(
    target_start: datetime,
    target_end: datetime,
    batch_size: int,
) -> AsyncIterator[list[dict[str, Any]]]:
    schema = _safe_ident(settings.DB_SCHEMA)

    query = f"""
    SELECT
        CASE
            WHEN user_id IS NOT NULL THEN 'u:' || user_id::text
            ELSE 's:' || session_id::text
        END AS subject_key,
        item_id::bigint AS item_id,
        COUNT(*) FILTER (WHERE lower(event_type) = 'view')::int AS view_cnt,
        COUNT(*) FILTER (
            WHERE lower(event_type) IN ('long_view', 'long-view', 'longview')
        )::int AS long_view_cnt,
        COUNT(*) FILTER (WHERE lower(event_type) = 'cart')::int AS cart_cnt,
        COUNT(*) FILTER (WHERE lower(event_type) = 'purchase')::int AS purchase_cnt,
        COALESCE(SUM(event_weight), 0)::real AS weight,
        MIN(event_timestamp) AS first_event_ts,
        MAX(event_timestamp) AS last_event_ts,
        DATE(event_timestamp) AS event_date
    FROM {schema}.interaction_events
    WHERE event_timestamp >= $1
      AND event_timestamp < $2
    GROUP BY
        CASE
            WHEN user_id IS NOT NULL THEN 'u:' || user_id::text
            ELSE 's:' || session_id::text
        END,
        item_id,
        DATE(event_timestamp)
    ORDER BY subject_key, item_id
    """

    normalized_batch_size = max(1, int(batch_size))

    async with postgres_connector.acquire() as conn:
        async with conn.transaction():
            statement = await conn.prepare(query)
            cursor = statement.cursor(
                target_start,
                target_end,
                prefetch=normalized_batch_size,
            )
            batch: list[dict[str, Any]] = []

            async for row in cursor:
                batch.append(dict(row))
                if len(batch) >= normalized_batch_size:
                    yield batch
                    batch = []

            if batch:
                yield batch
