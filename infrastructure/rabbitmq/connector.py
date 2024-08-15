import pika
from pika.adapters.blocking_connection import BlockingChannel, BlockingConnection
from pika.exceptions import AMQPError

from core.config import settings
from logger import logger
from dataclasses import dataclass, field


# __all__ = ("rabbit_connector",)


@dataclass
class RabbitConnector:
    # sets up connection to rabbitMQ

    host: str
    user: str
    password: str
    port: int
    creds: dict = field(init=False)
    _rabbit_con: BlockingConnection = field(init=False, default=None)
    _rabbit_chan: BlockingChannel = field(init=False, default=None)

    def __post_init__(self):
        self.creds = {
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "password": self.password
                         }

    @property
    def rabbit_con(self):
        return self._rabbit_con

    @property
    def rabbit_chan(self):
        return self._rabbit_chan

    @rabbit_con.setter
    def rabbit_con(self, v: BlockingConnection):
        self._rabbit_con = v

    @rabbit_chan.setter
    def rabbit_chan(self, v: BlockingChannel):
        self._rabbit_chan = v

    def create_connection(self) -> None:
        con_params = pika.ConnectionParameters(
            host=self.host,
            port=self.port,
            heartbeat=120,
            connection_attempts=10,
            retry_delay=5,
            credentials=pika.PlainCredentials(self.user, self.password)
        )
        try:
            self.rabbit_con = pika.BlockingConnection(con_params)
            logger.info("Connection has been created, CON: ", self.rabbit_con)
        except BaseException as e:
            raise logger.error(
                "unable to create RabbitMQ connection",
                exc_info=True,
                extra=self.creds
            )

    def create_chan(self) -> None:
        # creates a channel using pre-created connection
        if self.rabbit_con is None:
            raise ValueError("There is no connection created")

        try:
            self.rabbit_chan: BlockingChannel = self.rabbit_con.channel()
            logger.info("Channel has been created, CHAN: ", self.rabbit_chan)
        except BaseException as e:
            raise logger.error(
                "unable to create RabbitMQ channel",
                exc_info=True,
                extra=self.creds
            )

    def create_queue(
            self,
            q_name: str,
            is_passive: bool, is_durable: bool,
            is_exclusive: bool, is_auto_delete: bool,
    ) -> None:
        # creates a queue using pre-created channel
        chan = self.rabbit_chan
        if self.rabbit_chan is None:
            raise ValueError("There is no channel created")
        try:
            _ = chan.queue_declare(
                queue=q_name,
                passive=is_passive,
                durable=is_durable,
                exclusive=is_exclusive,
                auto_delete=is_auto_delete
            )
            logger.info(f"Queue {q_name} has been created")
        except AMQPError as e:
            raise logger.error(
                "unable to create queue",
                exc_info=True,
                extra=self.creds
            )

    def close_chan(self) -> None:
        if chan := self.rabbit_chan is None:
            raise ValueError("No rabbit channel specified")
        try:
            chan.close()
        except AMQPError as e:
            logger.error("Failed to close channel", extra=self.creds)

    def close_con(self) -> None:
        if con := self.rabbit_con is None:
            raise ValueError("No rabbit connectionq specified")
        try:
            con.close()
        except AMQPError as e:
            logger.error("Failed to close connection", extra=self.creds)


# rabbit_connector = RabbitConnector(
#     host=settings.Rabbit_HOST,
#     user=settings.RABBIT_USER,
#     password=settings.RABBIT_PASSWORD,
#     port=settings.Rabbit_PORT
# )
#
# rabbit_connector.create_connection()
# rabbit_connector.create_chan()
#
# rabbit_connector.create_queue(
#     q_name="logs_q",
#     is_passive=False,
#     is_durable=True,
#     is_exclusive=False,
#     is_auto_delete=False,
# )






