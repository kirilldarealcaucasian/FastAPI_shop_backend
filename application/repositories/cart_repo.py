from datetime import datetime
from typing import Protocol, Type, cast
from uuid import UUID

from sqlalchemy import CursorResult, and_, delete, select, text, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from application.models import Book, CartItem, ShoppingSession
from application.schemas import CartPrimaryIdentifier
from core import OrmEntityRepository
from core.base_repos import OrmEntityRepoInterface
from core.entity_base_service import Id
from core.exceptions import DBError, NotFoundError
from core.exceptions.storage_exceptions import ConflictError
from infrastructure.postgres import db_client


class CartRepositoryInterface(Protocol):
    async def get_cart_by_session_id(
        self, session: AsyncSession, cart_session_id: UUID
    ) -> list[CartItem]: ...

    async def get_cart_by_user_id(
        self,
        session: AsyncSession,
        user_id: int,
    ) -> list[CartItem]: ...

    async def get_by_id(self, session: AsyncSession, id: Id) -> CartItem | None: ...

    async def delete_all_books_from_cart(
        self, session: AsyncSession, session_id: UUID, book_id: int  # noqa: W291
    ): ...

    async def delete_some_books_from_cart(
        self, session: AsyncSession, session_id: UUID, book_id: int, quantity: int
    ): ...

    async def delete_cart_by_shopping_session_id(
        self, session: AsyncSession, shopping_session_id: UUID
    ) -> None: ...

    async def delete_expired_carts(
        self,
    ) -> None: ...

    async def create_or_update_book_in_cart(
        self, session: AsyncSession, book_id: int, session_id: UUID, quantity: int
    ): ...


class CombinedCartRepositoryInterface(
    CartRepositoryInterface, OrmEntityRepoInterface, Protocol
): ...


class CartRepository(OrmEntityRepository[CartItem]):
    @property
    def model(self) -> Type[CartItem]:
        return CartItem

    async def get_cart_by_session_id(
        self, session: AsyncSession, cart_session_id: UUID
    ) -> list[CartItem]:

        # load Cart with books
        stmt = (
            select(CartItem)
            .join_from(
                CartItem, ShoppingSession, CartItem.session_id == ShoppingSession.id
            )
            .where(ShoppingSession.id == str(cart_session_id))
            .options(
                selectinload(CartItem.book).selectinload(Book.authors),
                selectinload(CartItem.book).selectinload(Book.categories),
                selectinload(CartItem.shopping_session),
            )
        )

        try:
            cart = (await session.scalars(stmt)).all()
        except SQLAlchemyError as e:
            raise DBError(str(e)) from e

        if not cart:
            raise NotFoundError(entity="Cart")

        return list(cart)

    async def get_by_id(
        self, session: AsyncSession, id: CartPrimaryIdentifier
    ) -> CartItem | None:
        stmt = (
            select(CartItem)
            .where(
                and_(
                    CartItem.book_id == str(id.book_id),
                    CartItem.session_id == str(id.session_id),
                )
            )
            .options(joinedload(CartItem.shopping_session))
        )

        try:
            cart_item: CartItem | None = (await session.scalars(stmt)).one_or_none()
        except SQLAlchemyError as e:
            raise DBError(traceback=str(e)) from e

        return cart_item

    async def get_cart_by_user_id(
        self, session: AsyncSession, user_id: int
    ) -> list[CartItem]:
        stmt = (
            select(CartItem)
            .join(CartItem.shopping_session)
            .options(
                selectinload(CartItem.book).selectinload(Book.authors),
                selectinload(CartItem.book).selectinload(Book.categories),
            )
            .where(ShoppingSession.user_id == user_id)
        )

        try:
            cart = (await session.scalars(stmt)).all()
        except SQLAlchemyError as e:
            raise DBError(str(e)) from e

        if not cart:
            raise NotFoundError()

        return list(cart)

    async def delete_all_books_from_cart(
        self, session: AsyncSession, session_id: UUID, book_id: int  # noqa: W291
    ):
        stmt = delete(self.model).where(
            and_(self.model.session_id == session_id, self.model.book_id == book_id)
        )

        try:
            res = cast(CursorResult, await session.execute(stmt))
            await super().commit(session)
            if res.rowcount == 0:
                raise NotFoundError()
        except (SQLAlchemyError, IntegrityError) as e:
            if isinstance(e, IntegrityError):
                raise ConflictError(entity=self.model, traceback=str(e)) from e
            raise DBError(traceback=str(e)) from e

    async def delete_some_books_from_cart(
        self, session: AsyncSession, session_id: UUID, book_id: int, quantity: int
    ):
        stmt = (
            update(self.model)
            .where(
                and_(self.model.session_id == session_id, self.model.book_id == book_id)
            )
            .values(quantity=self.model.quantity - quantity)
        )

        try:
            await session.execute(stmt)
            await super().commit(session)
        except (SQLAlchemyError, IntegrityError) as e:
            if isinstance(e, IntegrityError):
                raise ConflictError(entity="Cart", traceback=str(e))
            raise DBError(traceback=str(e)) from e

    async def delete_cart_by_shopping_session_id(
        self, session: AsyncSession, shopping_session_id: UUID
    ) -> None:
        stmt = select(self.model).where(
            self.model.session_id == str(shopping_session_id)
        )
        obj: CartItem | None = (await session.execute(stmt)).scalars().one_or_none()
        if not obj:
            raise NotFoundError(entity="Cart")

        await session.delete(obj)
        await session.commit()

        try:
            await session.execute(stmt)
        except SQLAlchemyError as e:
            raise DBError(traceback=str(e)) from e
        await session.commit()

    async def create(
        self,
        session: AsyncSession,
        orm_model: CartItem,
    ) -> CartItem:
        return await super().create(session=session, orm_model=orm_model)

    async def delete_expired_carts(self) -> None:
        async with db_client.async_session() as session:
            now = datetime.now()
            stmt = (
                select(CartItem)
                .join_from(
                    CartItem, ShoppingSession, CartItem.session_id == ShoppingSession.id
                )
                .where(ShoppingSession.expiration_time <= now)
            )

            try:
                cart_items = (await session.scalars(stmt)).all()
            except SQLAlchemyError as e:
                raise DBError(traceback=str(e)) from e
            session_ids = []
            for item in cart_items:
                session_ids.append(item.session_id)

            try:
                delete_stmt = delete(ShoppingSession).where(
                    ShoppingSession.id.in_(session_ids)
                )
            except SQLAlchemyError as e:
                raise DBError(traceback=str(e)) from e
            await session.execute(delete_stmt)
            await session.commit()

    async def create_or_update_book_in_cart(
        self,
        session: AsyncSession,
        book_id: int,
        session_id: UUID,  # noqa: W291
        quantity: int,
    ):
        stmt = """
                SELECT 1
                FROM cart_items 
                WHERE session_id = :session_id
                FOR UPDATE;

                WITH update_cart AS (
                    UPDATE cart_items 
                    SET quantity = quantity + :qty
                    WHERE session_id = :session_id and book_id = :book_id
                    RETURNING 1
                )  
                   
                INSERT INTO cart_items (session_id, book_id, quantity)
                SELECT :session_id, :book_id, :qty
                WHERE NOT EXISTS (
                    SELECT 1 FROM update_cart
                );
            """  # type: ignore  # noqa: W291, W293
        await session.execute(
            text(stmt), {"qty": quantity, "session_id": session_id, "book_id": book_id}
        )
