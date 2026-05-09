from collections.abc import Sequence
from datetime import datetime

from loguru import logger
from shared_lib.recommendations.models import BookEventMessage, UserSessionLinkMessage

from .db import DB_SCHEMA, postgres_connector
from .sql import INSERT_ITEM_MAPPINGS, INSERT_SESSION_MAPPINGS, LINK_USER_SESSIONS

insert_session_mappings_sql = INSERT_SESSION_MAPPINGS.format(schema=DB_SCHEMA)
insert_item_mappings_sql = INSERT_ITEM_MAPPINGS.format(schema=DB_SCHEMA)
link_user_sessions_sql = LINK_USER_SESSIONS.format(schema=DB_SCHEMA)


def _event_type_counts(events: Sequence[BookEventMessage]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for event in events:
        event_type = event.event.value
        counts[event_type] = counts.get(event_type, 0) + 1
    return counts


async def save_events(events: Sequence[BookEventMessage]) -> None:
    if not events:
        return

    session_expiration_by_id = {
        event.session_id: event.session_expiration_time for event in events
    }
    session_ids = list(session_expiration_by_id)
    session_expiration_times = list(session_expiration_by_id.values())
    item_ids = list({event.book_id for event in events})
    event_records = [
        (
            event.user_id,
            event.book_id,
            event.event.value,
            event.weight,
            datetime.fromtimestamp(event.ts),
        )
        for event in events
    ]

    logger.info(
        "Saving book events",
        extra={
            "event_count": len(events),
            "session_count": len(session_ids),
            "item_count": len(item_ids),
            "event_type_counts": _event_type_counts(events),
            "anonymous_event_count": sum(event.user_id is None for event in events),
            "earliest_event_ts": min(record[4] for record in event_records),
            "latest_event_ts": max(record[4] for record in event_records),
            "latest_session_expiration_time": max(session_expiration_times),
        },
    )

    async with postgres_connector.acquire() as conn:
        async with conn.transaction():
            if session_ids:
                logger.debug(
                    "Inserting event session mappings",
                    extra={"session_count": len(session_ids)},
                )
                await conn.execute(
                    insert_session_mappings_sql,
                    session_ids,
                    session_expiration_times,
                )
            if item_ids:
                logger.debug(
                    "Inserting item mappings",
                    extra={"item_count": len(item_ids)},
                )
                await conn.execute(insert_item_mappings_sql, item_ids)
            logger.debug(
                "Copying interaction events",
                extra={"event_count": len(event_records), "schema": DB_SCHEMA},
            )
            await conn.copy_records_to_table(
                "interaction_events",
                schema_name=DB_SCHEMA,
                records=event_records,
                columns=(
                    "actor_id",
                    "item_id",
                    "event_type",
                    "event_weight",
                    "event_timestamp",
                ),
            )
    logger.info(
        "Book events saved",
        extra={
            "event_count": len(events),
            "session_count": len(session_ids),
            "item_count": len(item_ids),
        },
    )


async def link_user_sessions(links: Sequence[UserSessionLinkMessage]) -> None:
    if not links:
        return

    user_ids = [link.user_id for link in links]
    session_ids = [link.session_id for link in links]
    session_expiration_times = [link.session_expiration_time for link in links]

    logger.info(
        "Linking user sessions",
        extra={
            "link_count": len(links),
            "user_count": len(set(user_ids)),
            "session_count": len(set(session_ids)),
            "latest_session_expiration_time": max(session_expiration_times),
        },
    )

    async with postgres_connector.acquire() as conn:
        async with conn.transaction():
            logger.debug(
                "Updating linked user session mappings",
                extra={"link_count": len(links), "schema": DB_SCHEMA},
            )
            await conn.execute(
                link_user_sessions_sql,
                user_ids,
                session_ids,
                session_expiration_times,
            )
    logger.info("User sessions linked", extra={"link_count": len(links)})


__all__ = (
    "link_user_sessions",
    "save_events",
)
