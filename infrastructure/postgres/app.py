from asyncio import current_task
from typing import AsyncGenerator

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_scoped_session,
    async_sessionmaker,
    create_async_engine,
)
from ...application.settings import settings
from loguru import logger


class PostgresClient:
    def __init__(self, url, echo: bool = False):
        self._url = url
        self._echo = echo

    def connect(self):
        try:
            self.engine = create_async_engine(
                url=self._url,
                echo=self._echo,
                pool_size=3,  # TODO: SET to normal amount later: (3 only for local testing) persistent connections
                max_overflow=3,  # extra temporary connections
                pool_timeout=30,  # seconds to wait for a free conn
                pool_recycle=1800,  # recycle stale conns (seconds)
                pool_pre_ping=True,  # test connection before using
            )
            logger.info(f"Successful db connection via: {self._url}")
        except SQLAlchemyError:
            extra = {"url": self._url}
            logger.error(
                "DB connection error: Error while connecting to db",
                extra=extra,
                exc_info=True,
            )

        self.async_session = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    async def disconnect(self):
        if self.engine:
            await self.engine.dispose()
            logger.info("DB connection closed")
        else:
            logger.warning("Attempted to disconnect from db, but no connection found.")

    async def get_async_session(self) -> AsyncGenerator[AsyncSession]:
        if not self.async_session:
            raise RuntimeError(
                "PostgresClient is not connected. Call connect() before using."
            )
        async with self.async_session() as session:
            yield session

    async def get_scoped_session_dependency(self) -> AsyncGenerator[AsyncSession, None]:
        scoped_factory = async_scoped_session(
            session_factory=self.async_session, scopefunc=current_task
        )
        try:
            async with scoped_factory() as s:
                yield s
        finally:
            await scoped_factory.remove()


# client to access db
db_client = PostgresClient(url=settings.get_db_url, echo=False)
