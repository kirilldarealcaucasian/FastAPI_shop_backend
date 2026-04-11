import json
from collections.abc import Sequence

from aiokafka import AIOKafkaConsumer
from loguru import logger
from pydantic import ValidationError

from .config import settings
from .db import save_events
from .schemas import BookInteractionEvent


def _decode_message(raw: bytes | None) -> dict:
    if raw is None:
        return {}
    return json.loads(raw.decode("utf-8"))


def _resolve_actor_id(payload: dict) -> dict:
    resolved_payload = payload.copy()

    actor_id = resolved_payload.get("actor_id")
    if actor_id is not None:
        return resolved_payload

    user_id = resolved_payload.get("user_id")
    if user_id is not None:
        resolved_payload["actor_id"] = int(user_id)
    return resolved_payload


def _parse_records(messages: Sequence) -> list[dict]:
    rows: list[dict] = []
    for message in messages:
        try:
            payload = _decode_message(message.value)
            payload = _resolve_actor_id(payload)
            event = BookInteractionEvent.model_validate(payload)
            rows.append(event.to_record())
        except (
            json.JSONDecodeError,
            TypeError,
            ValueError,
            ValidationError,
        ) as exc:
            logger.warning(
                "Skipping malformed event",
                extra={"offset": message.offset, "error": str(exc)},
            )
    return rows


async def consume_forever() -> None:
    consumer = AIOKafkaConsumer(
        settings.KAFKA_TOPIC,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id=settings.KAFKA_GROUP_ID,
        auto_offset_reset=settings.KAFKA_AUTO_OFFSET_RESET,
        enable_auto_commit=False,
    )
    await consumer.start()
    logger.info(
        "Kafka consumer started",
        extra={
            "topic": settings.KAFKA_TOPIC,
            "group_id": settings.KAFKA_GROUP_ID,
            "bootstrap": settings.KAFKA_BOOTSTRAP_SERVERS,
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

            rows = _parse_records(messages)
            if rows:
                await save_events(rows=rows)

            await consumer.commit()
    finally:
        await consumer.stop()
        logger.info("Kafka consumer stopped")
