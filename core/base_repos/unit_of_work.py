from typing import Protocol

from core.exceptions import DBError
from sqlalchemy.exc import SQLAlchemyError

__all__ = (
    "AbstractUnitOfWork",
    "SqlAlchemyUnitOfWork"
)

from logger import logger


class AbstractUnitOfWork(Protocol):

    def __init__(self):
        ...

    async def __aenter__(self):
        ...

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        ...

    async def add(self, obj, orm_model):
        ...

    async def update(self, obj, orm_model):
        ...

    async def delete(self, obj, orm_model):
        ...

    async def commit(self):
        ...

    async def rollback(self):
        ...


class SqlAlchemyUnitOfWork:
    """Allows to perform operations transactionally"""

    def __init__(self):
        from infrastructure.postgres import db_client
        self._session = db_client.async_session()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            extra = {"exc_type": exc_type, "exc_val": exc_val, "exc_tb": exc_tb}
            logger.error("An error occurred in UnitOfWork", extra=extra)
            await self._session.rollback()
            exc_value = " ".join([str(exc_type), str(exc_val), str(exc_tb)])
            raise DBError(traceback=exc_value)

        self._session.expire_all()
        await self._session.aclose()

    def add(self, obj, orm_model):
        data = obj.model_dump(
            exclude_unset=True,
            exclude_none=True
        )
        to_add = orm_model(**data)
        self._session.add(to_add)

    async def update(self, obj, orm_model):
        data = obj.model_dump(
            exclude_unset=True,
            exclude_none=True
        )
        to_update = orm_model(**data)
        await self._session.merge(to_update)

    async def delete(
            self,
            orm_obj
    ):
        merged_obj = await self._session.merge(orm_obj)
        if merged_obj not in self._session:
            await self._session.add(merged_obj)
        await self._session.delete(merged_obj)

    async def commit(self):
        try:
            await self._session.commit()
        except SQLAlchemyError as e:
            logger.error("Failed to commit the session", exc_info=True)
            raise DBError(traceback=str(e))

    async def rollback(self):
        await self._session.rollback()
