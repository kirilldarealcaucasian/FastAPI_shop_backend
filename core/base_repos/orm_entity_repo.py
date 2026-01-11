from typing import Generic, Protocol, Sequence, Type, TypeAlias, TypeVar, Union
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from application.models.models import Base, BaseWithoutId
from core.exceptions.storage_exceptions import (ConflictError, DBError,
                                                DuplicateError, NotFoundError)

Id: TypeAlias = int | UUID
BaseT_co = TypeVar(
    "BaseT_co", bound=Union[DeclarativeBase, Base, BaseWithoutId], covariant=True
)
OrmModelT = TypeVar(
    "OrmModelT",
)


__all__ = ("OrmEntityRepository",)


class OrmEntityRepoInterface(Protocol, Generic[OrmModelT]):
    @property
    def model(self) -> Type[OrmModelT]:
        raise NotImplementedError

    async def create(
        self,
        session: AsyncSession,
        orm_model: OrmModelT,
    ) -> OrmModelT: ...

    async def get_all(
        self,
        session: AsyncSession,
        page: int = 0,
        limit: int = 5,
        **filters,
    ) -> list[OrmModelT]: ...

    async def update(
        self,
        orm_model: OrmModelT,
        instance_id: int | UUID,
        session: AsyncSession,
    ) -> OrmModelT: ...

    async def delete(
        self,
        session: AsyncSession,
        instance_id: Id,
    ) -> None: ...

    async def get_by_id(
        self,
        session: AsyncSession,
        id: Id,
    ) -> OrmModelT | None: ...

    async def commit(self, session: AsyncSession): ...


class OrmEntityRepository(Generic[OrmModelT]):
    """model is assigned in the child repo"""

    @property
    def model(self) -> Type[OrmModelT]: ...

    async def create(
        self,
        session: AsyncSession,
        orm_model: OrmModelT,
    ) -> OrmModelT:
        session.add(orm_model)
        try:
            await session.commit()
            await session.refresh(orm_model)
        except IntegrityError as e:
            raise DuplicateError(entity=self.model.__name__, traceback=str(e)) from e
        except SQLAlchemyError as e:
            raise DBError(str(e)) from e
        return orm_model

    async def get_all(
        self,
        session: AsyncSession,
        page: int = 0,
        limit: int = 5,
        **filters,
    ) -> list[OrmModelT]:
        stmt = select(self.model).filter_by(**filters).offset(page * limit).limit(limit)
        try:
            orm_models: Sequence = (await session.scalars(stmt)).all()
        except SQLAlchemyError as e:
            raise DBError(traceback=str(e)) from e
        return list(orm_models)

    async def update(
        self,
        orm_model: OrmModelT,
        instance_id: int | UUID,
        session: AsyncSession,
    ) -> OrmModelT:
        res: list[OrmModelT] = await self.get_all(
            session=session, id=instance_id
        )  # check existence of the entity

        if len(res) == 0:
            raise NotFoundError(entity=self.model.__name__)

        try:
            session.add(orm_model)
            await session.commit()
            await session.refresh(orm_model)
        except IntegrityError as e:
            raise ConflictError(entity=self.model, traceback=str(e)) from e
        except SQLAlchemyError as e:
            raise DBError(str(e)) from e
        return orm_model

    async def delete(
        self,
        session: AsyncSession,
        instance_id: Id,
    ) -> None:
        data: list[OrmModelT] = await self.get_all(session=session, id=instance_id)

        if len(data) == 0:
            raise NotFoundError(entity=self.model.__name__)

        try:
            await session.delete(data[0])
        except SQLAlchemyError as e:
            raise DBError(str(e)) from e

    async def commit(self, session: AsyncSession):
        try:
            await session.commit()
        except SQLAlchemyError as e:
            raise DBError(traceback=str(e)) from e
