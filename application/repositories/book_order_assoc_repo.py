from typing import Protocol, Union

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from application.schemas import BookOrderPrimaryIdentifier
from application.schemas.domain_model_schemas import BookOrderAssocS
from core import OrmEntityRepository
from application.models import BookOrderAssoc
from core.base_repos import OrmEntityRepoInterface
from core.exceptions import DBError


class BookOrderAssocRepoInterface(Protocol):
    async def create_many(
            self,
            session: AsyncSession,
            domain_models: list[BookOrderAssocS]
    ) -> None:
        ...

    async def get_by_id(
            self,
            session: AsyncSession,
            id: BookOrderPrimaryIdentifier
    ) -> BookOrderAssoc:
        ...


CombinedBookOrderAssocRepoInterface = Union[BookOrderAssocRepoInterface, OrmEntityRepoInterface]


class BookOrderAssocRepository(OrmEntityRepository):
    model = BookOrderAssoc

    async def create_many(
            self,
            session: AsyncSession,
            domain_models: list[BookOrderAssocS]
    ) -> None:
        try:
            to_add: list[BookOrderAssoc] = [BookOrderAssoc(
                **obj.model_dump(exclude_unset=True, exclude_none=True)
            ) for obj in domain_models]
        except Exception as e:
            raise DBError(traceback=str(e))

        session.add_all(to_add)

    async def get_by_id(
            self,
            session: AsyncSession,
            id: BookOrderPrimaryIdentifier
    ) -> BookOrderAssoc:
        stmt = select(BookOrderAssoc).where(
            and_(
                BookOrderAssoc.order_id == id.order_id,
                BookOrderAssoc.book_id == str(id.book_id)
            )
        ).options(
            joinedload(BookOrderAssoc.order)
        )

        book_order: Union[BookOrderAssoc, None] = (
            await session.execute(stmt)
        ).scalar_one_or_none()

        return book_order
