from shared_lib import RedisConnector

from events_collector.events_collector_service import EventsCollectorService
from events_collector.kafka import KafkaConnector, KafkaPublisher
from events_collector.settings import settings

redis_client = RedisConnector(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
kafka_connector = KafkaConnector(host=settings.KAFKA_HOST, port=settings.KAFKA_PORT)
kafka_publisher = KafkaPublisher(connector=kafka_connector)


def get_events_collector_service() -> EventsCollectorService:
    return EventsCollectorService(
        redis_con=redis_client.connection,
        kafka_publisher=kafka_publisher,
        kafka_topic=settings.KAFKA_EVENTS_TOPIC,
        history_limit=settings.EVENTS_HISTORY_LIMIT,
    )


__all__ = (
    "get_events_collector_service",
    "kafka_connector",
    "kafka_publisher",
    "redis_client",
)
