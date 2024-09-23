from uuid import UUID
from sqlalchemy import select, delete, and_
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from application.models import CartItem, ShoppingSession, Book
from application.schemas import CartPrimaryIdentifier
from application.schemas.domain_model_schemas import CartItemS
from core import OrmEntityRepository
from core.base_repos import OrmEntityRepoInterface
from typing import Protocol, Union, TypeAlias, Optional
from core.exceptions import NotFoundError, DBError
from infrastructure.postgres import db_client
from logger import logger
from datetime import datetime


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
            user_id: int,
    ) -> list[CartItem]:
        ...

    async def get_by_id(
            self,
            session: AsyncSession,
            id: CartPrimaryIdentifier
    ) -> CartItem:
        ...

    async def delete_book_from_cart_by_session_id(
            self,
            session: AsyncSession,
            session_id: UUID,
            book_id: UUID,
    ) -> None:
        ...

    async def delete_cart_by_shopping_session_id(
            self,
            session: AsyncSession,
            shopping_session_id: UUID
    ) -> None:
        ...

    async def delete_expired_carts(
            self,
    ) -> None:
        ...


class CombinedCartRepositoryInterface(
    CartRepositoryInterface,
    OrmEntityRepoInterface,
    Protocol
):
    pass


Id: TypeAlias = Optional[Union[str, int, UUID]]


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
            selectinload(CartItem.shopping_session)
        )

        try:
            cart = (await session.scalars(stmt)).all()
        except SQLAlchemyError as e:
            raise DBError(str(e))

        if not cart:
            raise NotFoundError(entity="Cart")

        return list(cart)

    async def get_by_id(self, session: AsyncSession, id: CartPrimaryIdentifier) -> CartItem:
        stmt = select(CartItem).where(
            and_(
                CartItem.book_id == str(id.book_id),
                CartItem.session_id == str(id.session_id)
            )
        ).options(
            joinedload(CartItem.shopping_session)
        )

        try:
            cart_item: Union[CartItem, None] = (await session.scalars(stmt)).one_or_none()
        except SQLAlchemyError as e:
            raise DBError(traceback=str(e))

        return cart_item

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

    async def create(
            self,
            session: AsyncSession,
            domain_model: CartItemS,
    ) -> CartPrimaryIdentifier:

        cart_item_domain_model: CartItemS = await super().create(
            session=session,
            domain_model=domain_model
        )

        res = CartPrimaryIdentifier(
            book_id=cart_item_domain_model.book_id,
            session_id=cart_item_domain_model.session_id
        )

        return res

    async def delete_expired_carts(self) -> None:
        async with db_client.async_session() as session:
            now = datetime.now()
            stmt = select(CartItem).join_from(
                CartItem, ShoppingSession, CartItem.session_id == ShoppingSession.id
            ).where(ShoppingSession.expiration_time <= now)

            try:
                cart_items = (await session.scalars(stmt)).all()
            except SQLAlchemyError as e:
                logger.error("failed to retrieve expired carts", exc_info=True)
                raise DBError(traceback=str(e))
            session_ids = []
            for item in cart_items:
                session_ids.append(item.session_id)

            try:
                delete_stmt = delete(ShoppingSession).where(ShoppingSession.id.in_(session_ids))
            except SQLAlchemyError as e:
                logger.error("failed to delete expired carts", exc_info=True)
                raise DBError(traceback=str(e))
            await session.execute(delete_stmt)
            await session.commit()
