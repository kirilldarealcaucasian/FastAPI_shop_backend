from loguru import logger
from redis.asyncio import Redis, from_url
from redis.exceptions import RedisError


class RedisConnector:
    """Creates and reuses a connection to redis-server."""

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.reconnect_retrials = 3
        self.__connection: Redis | None = None

    @property
    def connection(self) -> Redis | None:
        return self.__connection

    @connection.setter
    def connection(self, con: Redis) -> None:
        if not self.__connection:
            self.__connection = con

    async def connect(self) -> Redis | None:
        if self.__connection:
            return self.__connection

        redis_con = from_url(
            f"redis://{self.host}:{self.port}",
            decode_responses=True,
        )
        try:
            if self.reconnect_retrials == 0:
                raise TypeError
            self.reconnect_retrials -= 1
            await redis_con.ping()
            logger.info(f"connected to redis on redis://{self.host}:{self.port}")
            self.connection = redis_con
            return redis_con
        except (TypeError, RedisError):
            logger.error(
                f"failed to connect redis on redis://{self.host}:{self.port}",
                exc_info=True,
            )
            return None

    async def disconnect(self) -> None:
        if self.__connection:
            await self.__connection.close()
            self.__connection = None
            logger.info(f"redis connection closed on redis://{self.host}:{self.port}")

    async def get_redis_connection_dependency(self) -> Redis | None:
        redis_con = self.connection
        if redis_con is None:
            return await self.connect()
        return redis_con
