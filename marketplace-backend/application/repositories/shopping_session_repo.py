from typing import Protocol, Type
from uuid import UUID

from sqlalchemy import and_, delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from ..models import Book, CartItem, ShoppingSession
from .orm_entity_repo import OrmEntityRepoInterface, OrmEntityRepository
from ..types import Id
from shared_lib.exceptions import DBError, NotFoundError


class ShoppingSessionRepoInterface(Protocol):
    async def get_by_id(self, session: AsyncSession, id: Id) -> ShoppingSession: ...

    async def get_shopping_session_with_details(
        self, session: AsyncSession, id: UUID  # noqa
    ) -> ShoppingSession: ...


class CombinedShoppingSessionRepositoryInterface(
    ShoppingSessionRepoInterface, OrmEntityRepoInterface, Protocol
): ...


class ShoppingSessionRepository(OrmEntityRepository):
    @property
    def model(self) -> Type[ShoppingSession]:
        return ShoppingSession

    async def get_by_id(
        self, session: AsyncSession, id: UUID  # noqa
    ) -> ShoppingSession:
        stmt = (
            select(ShoppingSession)
            .options(joinedload(ShoppingSession.user))
            .where(ShoppingSession.id == str(id))
        )

        try:
            res = (await session.execute(stmt)).scalar_one_or_none()
        except SQLAlchemyError as e:
            raise DBError(traceback=str(e))

        if not res:
            raise NotFoundError(entity=self.model.__name__)

        return res

    async def get_shopping_session_with_details(
        self, session: AsyncSession, id: UUID  # noqa
    ) -> ShoppingSession:
        stmt = (
            select(ShoppingSession)
            .join_from(
                ShoppingSession, CartItem, ShoppingSession.id == CartItem.session_id
            )
            .options(
                selectinload(ShoppingSession.user),
                selectinload(ShoppingSession.cart_items).selectinload(CartItem.book),
                selectinload(ShoppingSession.cart_items)
                .selectinload(CartItem.book)
                .selectinload(Book.authors),
                selectinload(ShoppingSession.cart_items)
                .selectinload(CartItem.book)
                .selectinload(Book.categories),
            )
            .where(and_(ShoppingSession.id == str(id), CartItem.session_id == str(id)))
        )

        try:
            res = (await session.execute(stmt)).scalar_one_or_none()
        except SQLAlchemyError as e:
            raise DBError(traceback=str(e))

        if not res:
            raise NotFoundError(entity=self.model.__name__)

        return res

    async def delete(self, session: AsyncSession, instance_id: Id) -> None:
        stmt = delete(ShoppingSession).where(ShoppingSession.id == str(instance_id))
        try:
            await session.execute(stmt)
        except SQLAlchemyError as e:
            raise DBError(traceback=str(e))

        await super().commit(session=session)
