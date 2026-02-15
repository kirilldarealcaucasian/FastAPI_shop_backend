from typing import Protocol, Type, cast

from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..models import BookOrderAssoc
from ..types import BookOrderPrimaryIdentifier
from .orm_entity_repo import OrmEntityRepoInterface, OrmEntityRepository
from ..types import Id
from ..exceptions.storage_exceptions import DBError, DuplicateError


class BookOrderAssocRepoInterface(Protocol):
    async def create_many(
        self, session: AsyncSession, orm_models: list[BookOrderAssoc]
    ) -> None: ...

    async def get_by_id(
        self, session: AsyncSession, id: Id
    ) -> BookOrderAssoc | None: ...


class CombinedBookOrderAssocRepoInterface(
    BookOrderAssocRepoInterface, OrmEntityRepoInterface, Protocol
):
    pass


class BookOrderAssocRepository(OrmEntityRepository[BookOrderAssoc]):
    @property
    def model(self) -> Type[BookOrderAssoc]:
        return BookOrderAssoc

    async def create_many(
        self, session: AsyncSession, orm_models: list[BookOrderAssoc]
    ) -> None:
        try:
            session.add_all(orm_models)
            await session.commit()
        except IntegrityError as e:
            raise DuplicateError(entity=self.model.__name__, traceback=str(e)) from e
        except SQLAlchemyError as e:
            raise DBError(str(e)) from e

    async def get_by_id(self, session: AsyncSession, id: Id) -> BookOrderAssoc | None:
        book_order_id = cast(BookOrderPrimaryIdentifier, id)
        stmt = (
            select(BookOrderAssoc)
            .where(
                and_(
                    BookOrderAssoc.order_id == book_order_id.order_id,
                    BookOrderAssoc.book_id == book_order_id.book_id,
                )
            )
            .options(joinedload(BookOrderAssoc.order))
        )
        book_order: BookOrderAssoc | None = (
            await session.execute(stmt)
        ).scalar_one_or_none()

        return book_order
