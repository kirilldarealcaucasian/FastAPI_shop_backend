from dataclasses import dataclass

from loguru import logger
from redis.asyncio import Redis
from redis.exceptions import RedisError

from events_collector.kafka import KafkaPublisher
from events_collector.schemas import BookEventRequest


@dataclass(slots=True)
class EventsCollectorService:
    redis_con: Redis | None
    kafka_publisher: KafkaPublisher
    kafka_topic: str
    history_limit: int = 200

    @property
    def normalized_history_limit(self) -> int:
        return max(50, min(self.history_limit, 200))

    @staticmethod
    def build_history_key(session_id: str) -> str:
        return f"events:history:{session_id}"

    async def collect_book_event(self, event: BookEventRequest) -> None:
        await self._send_to_kafka(event=event)
        await self._append_to_redis_history(
            session_id=event.session_id,
            event_item_json=event.model_dump_json(
                include={"book_id", "event", "ts", "weight"},
            ),
        )

    async def _send_to_kafka(self, event: BookEventRequest) -> None:
        message = event.model_dump_json().encode("utf-8")
        await self.kafka_publisher.send_message(topic=self.kafka_topic, message=message)

    async def _append_to_redis_history(
        self,
        session_id: str,
        event_item_json: str,
    ) -> None:
        if self.redis_con is None:
            return

        key = self.build_history_key(session_id=session_id)
        try:
            await self.redis_con.lpush(
                key,
                event_item_json,
            )
            await self.redis_con.ltrim(key, 0, self.normalized_history_limit - 1)
        except RedisError as exc:
            logger.opt(exception=exc).warning("failed to append event to redis history")
