from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, async_scoped_session, AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from typing_extensions import AsyncGenerator

from asyncio import current_task
from logger import logger
from core.config import settings


class PostgresClient:
    def __init__(self, url, echo: bool = False):
        try:
            self.engine = create_async_engine(url=url, echo=echo)
            logger.info(f"Successful db connection via: {url}")
        except SQLAlchemyError:
            extra = {"url": url}
            logger.error("DB connection error: Error while connecting to db", extra=extra, exc_info=True)

        self.async_session = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False
        )

    async def get_scoped_session_dependency(self) -> AsyncGenerator[AsyncSession, None]:
        scoped_factory = async_scoped_session(
            session_factory=self.async_session,
            scopefunc=current_task
        )
        try:
            async with scoped_factory() as s:
                yield s
        except BaseException as e:
            logger.error("failed to create scope session", exc_info=True)
        finally:
            await scoped_factory.remove()


db_client = PostgresClient(
    url=settings.get_db_url,
    echo=False
)
