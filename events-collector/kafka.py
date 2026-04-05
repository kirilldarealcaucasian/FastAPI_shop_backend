from dataclasses import dataclass

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError
from loguru import logger


class KafkaConnector:
    kafka = None

    def __new__(cls, *args, **kwargs):
        if cls.kafka is None:
            instance = super().__new__(cls)
            cls.kafka = instance
        return cls.kafka

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.reconnect_retrials = 3
        self.__producer: AIOKafkaProducer | None = None

    @property
    def producer(self) -> AIOKafkaProducer | None:
        return self.__producer

    @producer.setter
    def producer(self, producer: AIOKafkaProducer):
        if not self.__producer:
            self.__producer = producer

    async def connect(self) -> AIOKafkaProducer | None:
        if self.__producer:
            return self.__producer

        producer = AIOKafkaProducer(
            bootstrap_servers=f"{self.host}:{self.port}",
        )
        try:
            if self.reconnect_retrials == 0:
                raise TypeError
            self.reconnect_retrials -= 1
            await producer.start()
            logger.info(f"connected to kafka on {self.host}:{self.port}")
            self.producer = producer
            return producer
        except (TypeError, KafkaError):
            logger.error(
                f"failed to connect kafka on {self.host}:{self.port}",
                exc_info=True,
            )
            return None

    async def disconnect(self) -> None:
        if self.__producer:
            await self.__producer.stop()
            self.__producer = None
            logger.info(f"kafka connection closed on {self.host}:{self.port}")


@dataclass
class KafkaPublisher:
    connector: KafkaConnector

    async def send_message(self, topic: str, message: bytes) -> None:
        producer = self.connector.producer or await self.connector.connect()
        if producer is None:
            return
        try:
            await producer.send_and_wait(topic=topic, value=message)
        except KafkaError as exc:
            logger.opt(exception=exc).warning("failed to publish message to kafka")
