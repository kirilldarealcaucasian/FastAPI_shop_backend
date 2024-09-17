from typing import Union

import aioredis
from aioredis import RedisError, Connection

from core.config import settings
from logger import logger


class RedisConnector:
    """Creates connection to redis-server"""
    redis = None

    def __new__(cls, *args, **kwargs):
        if cls.redis is None:
            instance = super().__new__(cls)
            cls.redis = instance
        return cls.redis

    def __init__(self, host: str | int, port: int):
        self.host = host
        self.port = port
        self.reconnect_retrials = 3
        self.__connection: Union[Connection, None] = None

    @property
    def connection(self) -> Union[Connection, None]:
        return self.__connection

    @connection.setter
    def connection(self, con: Connection):
        if not self.__connection:
            self.__connection = con

    async def connect(self) -> Union[Connection, None]:
        """Creates or retrieves a connection to redis-server"""
        if self.__connection:
            return self.__connection

        redis_con = await aioredis.from_url(
            f"redis://{self.host}:{self.port}",
            decode_responses=True
            )
        try:
            if self.reconnect_retrials == 0:
                raise TypeError  # manually raise this error so that the
                # exception scenario took action
            self.reconnect_retrials -= 1
            pong = await redis_con.ping()
            if pong == b'PONG':
                logger.info(f"Successful connection to redis on redis://{self.host}:{self.port}")
            self.connection = redis_con
            return redis_con
        except (TypeError, RedisError):
            extra = {
                "redis_host": self.host,
                "redis_port": self.port
            }
            logger.error(
                f"Connection to redis on redis://{self.host}:{self.port} hasn't been established",
                extra=extra,
                exc_info=True
                )
            return None

    async def get_redis_connection_dependency(self) -> Connection:
        redis_con = self.connection
        if redis_con is None:
            return await redis_client.connect()
        return redis_con


redis_client = RedisConnector(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT
)










