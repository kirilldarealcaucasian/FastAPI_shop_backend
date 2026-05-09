from auth.config import auth_conf
from shared_lib import KafkaConnector, KafkaPublisher

kafka_connector = KafkaConnector(host=auth_conf.KAFKA_HOST, port=auth_conf.KAFKA_PORT)
kafka_publisher = KafkaPublisher(connector=kafka_connector)

__all__ = (
    "kafka_connector",
    "kafka_publisher",
)
