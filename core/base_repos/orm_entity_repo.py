from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from core.exceptions.storage_exceptions import (
    DuplicateError,
    DBError, NotFoundError
)
from sqlalchemy.exc import NoSuchTableError, NoReferenceError
from typing import TypeVar, TypeAlias, Optional, Union, Protocol
from application.schemas.domain_model_schemas import \
    (
    AuthorS,
    BookS,
    BookOrderAssocS,
    CartItemS,
    CategoryS,
    OrderS,
    PaymentDetailS,
    PublisherS,
    ShoppingSessionS
)

DomainModelDataT = TypeVar(
    "DomainModelDataT",
    AuthorS, BookS, BookOrderAssocS,
    CartItemS, CategoryS, OrderS,
    PaymentDetailS, PublisherS, ShoppingSessionS
)

Id: TypeAlias = Optional[Union[str, int, UUID]]
DomainModelDataT = TypeVar("DomainModelDataT",)

__all__ = (
    "OrmEntityRepoInterface",
    "OrmEntityRepository",
)

class OrmEntityRepoInterface(Protocol):

    async def create(
            self,
            domain_model: DomainModelDataT,
            session: AsyncSession
    ):
        ...

    async def get_all(
            self,
            session: AsyncSession,
            **filters,
    ):
        ...


    async def update(
            self,
            domain_model: DomainModelDataT,
            instance_id: int | UUID,
            session: AsyncSession,
    ):
        ...

    async def delete(
            self,
            session: AsyncSession,
            instance_id: int,
    ):
        ...

    async def commit(self, session: AsyncSession):
        ...


class OrmEntityRepository:
    model = None

    async def create(
            self,
            session: AsyncSession,
            domain_model: DomainModelDataT,
    ) -> Id:
        from logger import logger

        to_add = None

        try:
            to_add = self.model(**domain_model.model_dump(exclude_unset=True))
        except Exception as e:
            raise DBError(
                traceback=str(e)
            )
        try:
            session.add(to_add)
            await session.commit()
        except NoSuchTableError as e:
            raise DBError(
                traceback=str(e)
            )
        except IntegrityError as e:
            raise DuplicateError(
                entity=self.model.__name__,
                traceback=str(e)
            )

        except NoReferenceError as e:
            raise DBError(
                traceback=str(e)
            )
        added_entity_id = to_add.id
        logger.info(f"added {self.model}: {added_entity_id}")
        return added_entity_id

    async def get_all(
            self,
            session: AsyncSession,
            page: int = 0,
            limit: int = 5,
            **filters
    ) -> list:
        stmt = select(self.model).filter_by(**filters).offset(page * limit).limit(limit)
        try:
            domain_models: list | [] = (await session.scalars(stmt)).all()
        except NoSuchTableError as e:
            raise DBError(
                traceback=str(e)
            )

        if not domain_models or domain_models is None:
            return []

        return list(domain_models)

    async def update(
            self,
            domain_model: DomainModelDataT,
            instance_id: str | int | UUID,
            session: AsyncSession,
    ) -> model:
        res = await self.get_all(session=session, id=instance_id)  # check existence of the entity

        if not res:
            raise NotFoundError(entity=self.model.__name__)

        try:
            to_update: dict = domain_model.model_dump(exclude_unset=True, exclude_none=True)
        except Exception as e:
            raise DBError(
                traceback=str(e)
            )

        try:
            stmt = update(self.model).where(self.model.id == instance_id).values(**to_update)
            await session.execute(stmt)
            await session.commit()
        except (IntegrityError, NoReferenceError, TypeError) as e:
            raise DBError(
                traceback=str(e)
            )
        session.expire_all()
        updated_entity: list = await self.get_all(session=session, id=instance_id)
        if not updated_entity:
            raise DBError(
                traceback="Entity wasn't found after update operation"
            )
        return updated_entity[0]

    async def delete(
            self,
            session: AsyncSession,
            instance_id: int | str,
    ) -> None:
        instance = await self.get_all(session=session, id=instance_id)

        if not instance:
            raise NotFoundError(entity=self.model.__name__)

        instance = instance[0]
        await session.delete(instance)

    async def commit(self, session: AsyncSession):
        from logger import logger
        try:
            await session.commit()
        except SQLAlchemyError as e:
            logger.error("Error while committing session", exc_info=True)
            raise DBError(traceback=str(e))
