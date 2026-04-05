from asyncio import current_task
from typing import AsyncGenerator

from loguru import logger
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_scoped_session,
    async_sessionmaker,
    create_async_engine,
)


class SqlalchemyPostgresConnector:
    """SQLAlchemy async engine/session connector used by marketplace-backend."""

    def __init__(self, url: str, echo: bool = False):
        self._url = url
        self._echo = echo
        self.engine = None
        self.async_session = None

    def connect(self) -> None:
        try:
            self.engine = create_async_engine(
                url=self._url,
                echo=self._echo,
                pool_size=3,
                max_overflow=3,
                pool_timeout=30,
                pool_recycle=1800,
                pool_pre_ping=True,
            )
            logger.info(f"Successful db connection via: {self._url}")
        except SQLAlchemyError:
            logger.error(
                "DB connection error: Error while connecting to db",
                extra={"url": self._url},
                exc_info=True,
            )
            return

        self.async_session = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    async def disconnect(self) -> None:
        if self.engine:
            await self.engine.dispose()
            logger.info("DB connection closed")
        else:
            logger.warning("Attempted to disconnect from db, but no connection found.")

    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        if not self.async_session:
            raise RuntimeError(
                "Postgres connector is not connected. Call connect() before using."
            )
        async with self.async_session() as session:
            yield session

    async def get_scoped_session_dependency(self) -> AsyncGenerator[AsyncSession, None]:
        if not self.async_session:
            raise RuntimeError(
                "Postgres connector is not connected. Call connect() before using."
            )

        scoped_factory = async_scoped_session(
            session_factory=self.async_session,
            scopefunc=current_task,
        )
        try:
            async with scoped_factory() as session:
                yield session
        finally:
            await scoped_factory.remove()
