from dataclasses import dataclass
from logger import logger
from infrastructure.rabbitmq.connector import RabbitConnector, rabbit_connector


__all__ = ("rabbit_publisher", "RabbitPublisher")


@dataclass
class RabbitPublisher:
    # sets up interaction with RabbitMQ
    rabbit_connector: RabbitConnector

    def send_message_basic_publish(self, message: bytes, routing_key: str):
        try:
            self.rabbit_connector.rabbit_chan.basic_publish(
                exchange="",
                routing_key=routing_key,
                body=message,
                mandatory=True
            )
        except Exception:
            logger.error(
                "Failed to publish a message",
                extra=self.rabbit_connector.creds
            )
            return


rabbit_publisher = RabbitPublisher(
    rabbit_connector=rabbit_connector
)
