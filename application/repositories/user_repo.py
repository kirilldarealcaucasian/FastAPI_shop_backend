from typing import Protocol, Type

from sqlalchemy import and_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from application.models import Book, BookOrderAssoc, Order, User
from .orm_entity_repo import OrmEntityRepository
from ..repositories.orm_entity_repo import OrmEntityRepoInterface
from ..exceptions import DBError, NotFoundError
from ..types import Id


class UserInterface(Protocol):
    async def get_by_id(self, session: AsyncSession, id: Id) -> User | None: ...

    async def get_user_by_order_id(
        self, session: AsyncSession, order_id: int
    ) -> User: ...

    async def get_user_with_orders(
        self, session: AsyncSession, user_id: int
    ) -> User: ...


class CombinedUserInterface(UserInterface, OrmEntityRepoInterface, Protocol): ...


class UserRepository(OrmEntityRepository):
    @property
    def model(self) -> Type[User]:
        return User

    async def get_by_id(self, session: AsyncSession, id: int) -> User:
        stmt = select(User).where(User.id == id)

        try:
            user: User | None = (await session.scalars(stmt)).one_or_none()
        except SQLAlchemyError as e:
            raise DBError(traceback=str(e)) from e
        if user is None:
            raise NotFoundError(entity="User")
        return user

    async def get_user_with_orders(self, session: AsyncSession, user_id: int) -> User:
        stmt = (
            select(User, Order.user_id)
            .join_from(User, Order, Order.user_id == User.id, isouter=True)
            .where(and_(User.id == user_id, Order.user_id == user_id))
            .options(
                joinedload(User.orders),
                joinedload(User.orders)
                .joinedload(Order.order_details)
                .joinedload(BookOrderAssoc.book)
                .joinedload(Book.categories),
                joinedload(User.orders)
                .joinedload(Order.order_details)
                .joinedload(BookOrderAssoc.book)
                .joinedload(Book.authors),
            )
        )
        try:
            user_with_orders = (
                (await session.execute(stmt)).unique().scalar_one_or_none()
            )
        except SQLAlchemyError as e:
            raise DBError(traceback=str(e)) from e
        if not user_with_orders:
            raise NotFoundError(entity="User")

        return user_with_orders

    async def get_user_by_order_id(
        self,
        session: AsyncSession,
        order_id: int,
    ) -> User | None:
        stmt = (
            select(User, Order)
            .join_from(User, Order, User.id == Order.user_id, isouter=True)
            .where(Order.id == order_id)
        )

        user: User | None = (await session.execute(stmt)).scalar_one_or_none()
        return user
