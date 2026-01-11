from typing import Protocol, Type, cast

from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from application.models import BookOrderAssoc
from application.schemas import BookOrderPrimaryIdentifier
from application.schemas.domain_model_schemas import BookOrderAssocS
from core import OrmEntityRepository
from core.base_repos import OrmEntityRepoInterface
from core.entity_base_service import Id
from core.exceptions.storage_exceptions import DBError, DuplicateError


class BookOrderAssocRepoInterface(Protocol):
    async def create_many(
        self, session: AsyncSession, domain_models: list[BookOrderAssocS]
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
        self, session: AsyncSession, domain_models: list[BookOrderAssocS]
    ) -> None:
        to_add: list[BookOrderAssoc] = [
            BookOrderAssoc(**obj.model_dump(exclude_unset=True, exclude_none=True))
            for obj in domain_models
        ]

        try:
            session.add_all(to_add)
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
