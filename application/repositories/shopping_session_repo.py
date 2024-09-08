from uuid import UUID

from sqlalchemy import select, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.exc import SQLAlchemyError
from typing import Protocol

from application import Book
from core import OrmEntityRepository
from application.models import ShoppingSession, CartItem
from core.base_repos import OrmEntityRepoInterface
from core.exceptions import NotFoundError, DBError


class ShoppingSessionRepoInterface(Protocol):
    async def get_by_id(
            self,
            session: AsyncSession,
            id: UUID # noqa
    ) -> ShoppingSession:
        ...

    async def get_shopping_session_with_details(
            self,
            session: AsyncSession,
            id: UUID  # noqa
    ) -> ShoppingSession:
        ...


class CombinedShoppingSessionRepositoryInterface(
    OrmEntityRepoInterface,
    ShoppingSessionRepoInterface,
    Protocol
):
    pass


class ShoppingSessionRepository(OrmEntityRepository):
    model: ShoppingSession = ShoppingSession

    async def get_by_id(
        self,
        session: AsyncSession,
        id: UUID  # noqa
    ) -> ShoppingSession:
        stmt = select(ShoppingSession).\
            options(
          joinedload(ShoppingSession.user)
        ).where(
            ShoppingSession.id == str(id)
        )

        try:
            res = (await session.execute(stmt)).scalar_one_or_none()
        except SQLAlchemyError as e:
            raise DBError(traceback=str(e))

        if not res:
            raise NotFoundError(entity=self.model.__name__)

        return res

    async def get_shopping_session_with_details(
            self,
            session: AsyncSession,
            id: UUID  # noqa
    ) -> ShoppingSession:
        stmt = select(ShoppingSession).join_from(
            ShoppingSession, CartItem, ShoppingSession.id == CartItem.session_id
        ).options(
            selectinload(ShoppingSession.user),
            selectinload(ShoppingSession.cart_items).selectinload(CartItem.book),
            selectinload(ShoppingSession.cart_items).selectinload(CartItem.book).selectinload(Book.authors),
            selectinload(ShoppingSession.cart_items).selectinload(CartItem.book).selectinload(Book.categories),
        ).\
            where(
            and_(
                ShoppingSession.id == str(id),
                CartItem.session_id == str(id)
            )
        )

        try:
            # res = (await session.execute(stmt)).scalar_one_or_none()
            res = (await session.scalars(stmt)).all()
        except SQLAlchemyError as e:
            raise DBError(traceback=str(e))

        if not res:
            raise NotFoundError(entity=self.model.__name__)

        return res

    async def delete(
            self,
            session: AsyncSession,
            instance_id: int | str | UUID
    ) -> None:
        stmt = delete(ShoppingSession).where(ShoppingSession.id == str(instance_id))
        try:
            await session.execute(stmt)
            await super().commit(session=session)
        except SQLAlchemyError as e:
            raise DBError(traceback=str(e))
