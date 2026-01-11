from dataclasses import dataclass

from infrastructure.rabbitmq.connector import RabbitConnector, rabbit_connector

__all__ = ("rabbit_publisher", "RabbitPublisher")


@dataclass
class RabbitPublisher:
    # sets up interaction with RabbitMQ
    rabbit_connector: RabbitConnector

    def send_message_basic_publish(self, message: bytes, routing_key: str) -> None:
        self.rabbit_connector.rabbit_chan.basic_publish(
            exchange="", routing_key=routing_key, body=message, mandatory=True
        )


rabbit_publisher = RabbitPublisher(rabbit_connector=rabbit_connector)
