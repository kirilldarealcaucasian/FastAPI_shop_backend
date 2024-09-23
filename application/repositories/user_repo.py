from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError

from core import OrmEntityRepository

from application.models import User, Order, BookOrderAssoc, Book
from typing import Protocol, Union

from core.base_repos import OrmEntityRepoInterface
from core.exceptions import DBError, NotFoundError


class UserInterface(Protocol):
    async def get_by_id(
            self,
            session: AsyncSession,
            user_id: int
    ) -> User:
        ...

    async def get_user_by_order_id(
            self,
            session: AsyncSession,
            order_id: int
    ) -> User:
        ...

    async def get_user_with_orders(
            self,
            session: AsyncSession,
            user_id: int
    ) -> User:
        ...


class CombinedUserInterface(UserInterface, OrmEntityRepoInterface, Protocol):
    ...


class UserRepository(OrmEntityRepository):
    model: User = User

    async def get_by_id(
            self,
            session: AsyncSession,
            id: int
    ) -> User:
        stmt = select(User).where(User.id == id)

        try:
            user: Union[User, None] = (await session.scalars(stmt)).one_or_none()
        except SQLAlchemyError as e:
            raise DBError(traceback=str(e))

        return user

    async def get_user_with_orders(
            self,
            session: AsyncSession,
            user_id: int
    ) -> User:
        stmt = select(User, Order.user_id).join_from(
            User, Order, Order.user_id == User.id,
            isouter=True
        ).where(and_(User.id == user_id, Order.user_id == user_id)).options(
            joinedload(User.orders),
            joinedload(User.orders).joinedload(Order.order_details).joinedload(BookOrderAssoc.book).joinedload(
                Book.categories),
            joinedload(User.orders).joinedload(Order.order_details).joinedload(BookOrderAssoc.book).joinedload(
                Book.authors),
        )
        try:
            user_with_orders = (await session.execute(stmt)).unique().scalar_one_or_none()
        except SQLAlchemyError as e:
            raise DBError(traceback=str(e))

        if not user_with_orders:
            raise NotFoundError(entity="User")

        return user_with_orders

    async def get_user_by_order_id(
            self,
            session: AsyncSession,
            order_id: int,
    ) -> User:
        stmt = select(User, Order).join_from(
            User, Order, User.id == Order.user_id, isouter=True
        ).where(Order.id == order_id)

        user: Union[User, None] = (await session.execute(stmt)).scalar_one_or_none()
        return user
