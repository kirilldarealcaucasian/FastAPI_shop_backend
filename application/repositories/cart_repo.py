from uuid import UUID
from sqlalchemy import select, delete, and_
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from application import Book
from application.models import CartItem, ShoppingSession
from core import OrmEntityRepository
from core.base_repos import OrmEntityRepoInterface
from typing import Protocol, Union
from application.schemas.domain_model_schemas import BookS
from core.exceptions import NotFoundError, DBError
from logger import logger


class CartRepositoryInterface(Protocol):
    async def get_cart_by_session_id(
            self,
            session: AsyncSession,
            cart_session_id: UUID
    ) -> list[CartItem]:
        ...

    async def get_cart_by_user_id(
            self,
            session: AsyncSession,
            user_id: int | str,
    ) -> list[CartItem]:
        ...

    async def add_book_to_cart_by_session_id(
            self,
            session_id: str,
            domain_model: BookS
    ) -> None:
        ...

    async def delete_book_from_cart_by_session_id(
            self,
            session: AsyncSession,
            session_id: UUID,
            book_id: UUID,
    ):
        ...

    async def delete_cart_by_shopping_session_id(
            self,
            session: AsyncSession,
            shopping_session_id: UUID
    ) -> None:
        pass


CombinedCartRepositoryInterface = Union[CartRepositoryInterface, OrmEntityRepoInterface]


class CartRepository(OrmEntityRepository):
    model: CartItem = CartItem

    async def get_cart_by_session_id(
            self,
            session: AsyncSession,
            cart_session_id: UUID
    ) -> list[CartItem]:

        # load Cart with books
        stmt = select(CartItem).join_from(
            CartItem, ShoppingSession, CartItem.session_id == ShoppingSession.id
        ).where(ShoppingSession.id == str(cart_session_id)).options(
            selectinload(CartItem.book).selectinload(Book.authors),
            selectinload(CartItem.book).selectinload(Book.categories),
        )

        try:
            cart = (await session.scalars(stmt)).all()
        except SQLAlchemyError as e:
            raise DBError(str(e))

        if not cart:
            raise NotFoundError(entity="Cart")

        return list(cart)

    async def get_cart_by_user_id(
            self,
            session: AsyncSession,
            user_id: int
    ) -> list[CartItem]:
        stmt = select(CartItem).join(CartItem.shopping_session).options(
            selectinload(CartItem.book).selectinload(Book.authors),
            selectinload(CartItem.book).selectinload(Book.categories),
        ).where(ShoppingSession.user_id == user_id)

        try:
            cart = (await session.scalars(stmt)).all()
        except SQLAlchemyError as e:
            logger.error("query error: failed to perform select query", exc_info=True)
            raise DBError(str(e))

        if not cart:
            raise NotFoundError()

        return list(cart)

    async def delete_book_from_cart_by_session_id(
            self,
            session: AsyncSession,
            session_id: UUID,
            book_id: UUID,
    ) -> None:
        stmt = delete(self.model).where(
            and_(self.model.session_id == session_id, self.model.book_id == book_id))

        try:
            res = await session.execute(stmt)
            await super().commit(session)
            if res.rowcount == 0:
                raise NotFoundError()
        except (SQLAlchemyError, IntegrityError) as e:
            raise DBError(traceback=str(e))

    async def delete_cart_by_shopping_session_id(
            self,
            session: AsyncSession,
            shopping_session_id: UUID
    ) -> None:
        stmt = select(self.model).where(self.model.session_id == str(shopping_session_id))
        obj: Union[ShoppingSession, None] = (await session.execute(stmt)).one_or_none()

        if not obj:
            raise NotFoundError(entity="Cart")

        await session.delete(obj)
        await session.commit()

        try:
            await session.execute(stmt)
        except SQLAlchemyError as e:
            raise DBError(traceback=str(e))
        await session.commit()
