import json
from collections.abc import Sequence
from dataclasses import dataclass

from aiokafka import AIOKafkaConsumer
from loguru import logger
from pydantic import ValidationError
from shared_lib.recommendations.models import BookEventMessage, UserSessionLinkMessage

from .config import settings
from .processor import link_user_sessions, save_events


@dataclass(slots=True)
class ParsedMessages:
    book_events: list[BookEventMessage]
    user_session_links: list[UserSessionLinkMessage]
    malformed_count: int = 0
    unexpected_topic_count: int = 0


def _decode_message(raw: bytes | None) -> dict:
    if raw is None:
        return {}
    return json.loads(raw.decode("utf-8"))


def _parse_messages(
    messages: Sequence,
) -> ParsedMessages:
    events: list[BookEventMessage] = []
    links: list[UserSessionLinkMessage] = []
    malformed_count = 0
    unexpected_topic_count = 0
    for message in messages:
        try:
            payload = _decode_message(message.value)
            if message.topic == settings.KAFKA_BOOK_EVENTS_TOPIC:
                events.append(BookEventMessage.model_validate(payload))
            elif message.topic == settings.KAFKA_AUTH_EVENTS_TOPIC:
                links.append(UserSessionLinkMessage.model_validate(payload))
            else:
                unexpected_topic_count += 1
                logger.warning(
                    "Skipping message from unexpected topic",
                    extra={
                        "topic": message.topic,
                        "partition": message.partition,
                        "offset": message.offset,
                    },
                )
        except (
            json.JSONDecodeError,
            TypeError,
            ValueError,
            ValidationError,
        ) as exc:
            malformed_count += 1
            logger.warning(
                "Skipping malformed event",
                extra={
                    "topic": message.topic,
                    "partition": message.partition,
                    "offset": message.offset,
                    "error": str(exc),
                },
            )
    return ParsedMessages(
        book_events=events,
        user_session_links=links,
        malformed_count=malformed_count,
        unexpected_topic_count=unexpected_topic_count,
    )


def _records_metadata(records_map: dict) -> dict:
    topic_counts: dict[str, int] = {}
    offset_ranges: dict[str, str] = {}

    for topic_partition, records in records_map.items():
        if not records:
            continue

        topic_counts[topic_partition.topic] = topic_counts.get(
            topic_partition.topic, 0
        ) + len(records)
        offset_ranges[f"{topic_partition.topic}:{topic_partition.partition}"] = (
            f"{records[0].offset}-{records[-1].offset}"
        )

    return {
        "topic_counts": topic_counts,
        "offset_ranges": offset_ranges,
    }


async def consume_forever() -> None:
    consumer = AIOKafkaConsumer(
        settings.KAFKA_BOOK_EVENTS_TOPIC,
        settings.KAFKA_AUTH_EVENTS_TOPIC,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id=settings.KAFKA_GROUP_ID,
        auto_offset_reset=settings.KAFKA_AUTO_OFFSET_RESET,
        enable_auto_commit=False,
    )
    await consumer.start()
    logger.info(
        "Kafka consumer started",
        extra={
            "topics": (
                settings.KAFKA_BOOK_EVENTS_TOPIC,
                settings.KAFKA_AUTH_EVENTS_TOPIC,
            ),
            "group_id": settings.KAFKA_GROUP_ID,
            "bootstrap": settings.KAFKA_BOOTSTRAP_SERVERS,
            "auto_offset_reset": settings.KAFKA_AUTO_OFFSET_RESET,
            "batch_size": settings.KAFKA_BATCH_SIZE,
        },
    )

    try:
        while True:
            records_map = await consumer.getmany(
                timeout_ms=1000,
                max_records=settings.KAFKA_BATCH_SIZE,
            )
            messages = [msg for records in records_map.values() for msg in records]

            if not messages:
                continue

            logger.info(
                "Kafka messages received",
                extra={
                    "message_count": len(messages),
                    **_records_metadata(records_map),
                },
            )
            parsed_messages = _parse_messages(messages)
            logger.info(
                "Kafka messages parsed",
                extra={
                    "book_event_count": len(parsed_messages.book_events),
                    "user_session_link_count": len(parsed_messages.user_session_links),
                    "malformed_count": parsed_messages.malformed_count,
                    "unexpected_topic_count": parsed_messages.unexpected_topic_count,
                },
            )
            try:
                if parsed_messages.book_events:
                    await save_events(events=parsed_messages.book_events)
                if parsed_messages.user_session_links:
                    await link_user_sessions(links=parsed_messages.user_session_links)
            except Exception:
                logger.exception(
                    "Failed to process Kafka batch",
                    extra={
                        "message_count": len(messages),
                        "book_event_count": len(parsed_messages.book_events),
                        "user_session_link_count": len(
                            parsed_messages.user_session_links,
                        ),
                    },
                )
                raise

            await consumer.commit()
            logger.info(
                "Kafka offsets committed",
                extra={"message_count": len(messages)},
            )
    finally:
        await consumer.stop()
        logger.info("Kafka consumer stopped")
